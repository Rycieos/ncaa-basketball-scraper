import asyncio
import json
import re
from datetime import date, timedelta
from typing import Any, Dict, Iterator, List, Set, Tuple

import aiohttp
from bs4 import BeautifulSoup

from ncaa_basketball.util import get_url

# Group 50 is Division I.
teamlist_url = "https://www.espn.com/mens-college-basketball/teams/_/group/50"

gamelist_url = (
    "https://www.espn.com/mens-college-basketball/scoreboard/_/date/{}/group/50"
)
gamestats_url = "https://www.espn.com/mens-college-basketball/matchup/_/gameId/{}"

playerlist_url = "https://www.espn.com/mens-college-basketball/team/roster/_/id/{}"
playerstats_url = "https://www.espn.com/mens-college-basketball/player/stats/_/id/{}"

script_regex = re.compile(r"window\['__espnfitt__'\]=({.+?});")

# Match a word with a "-" in it, and no digits.
multi_stat_re = re.compile(r"[^\s\d]+-[^\s\d]+")


# Download the page, and load the data as a HTML document.
async def get_data(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
    page = await get_url(session, url)
    document = BeautifulSoup(page, "html.parser")

    # Locate the specific object that contains all of the data, and capture it.
    scripts = document.find_all("script")
    for script in scripts:
        if capture := script_regex.search(script.text):
            data = capture.group(1)
            # Convert the text of the page into a data format Python understands.
            return json.loads(data)

    print("WARNING: found no data for URL {}".format(url))
    return dict()


# Get all game IDs between the two dates, inclusive.
async def get_game_list(
    session: aiohttp.ClientSession, start_date: date, end_date: date
) -> Set[str]:
    games: Set[str] = set()

    delta = end_date - start_date

    # For each day between the inputs.
    for i in range(delta.days + 1):
        day = start_date + timedelta(days=i)

        data = await get_data(session, gamelist_url.format(day.strftime("%Y%m%d")))

        gamelist = data["page"]["content"]["scoreboard"]["evts"]
        for game in gamelist:
            games.add(game["id"])

    return games


# Get all game data for the given ID.
async def get_game_data(session: aiohttp.ClientSession, game_id: str) -> Dict[str, str]:
    raw_data = (await get_data(session, gamestats_url.format(game_id)))["page"]
    game_data: Dict[str, str] = dict()
    game_data["GameID"] = game_id

    try:
        game_data["GameTitle"] = raw_data["meta"]["title"]

        # Save references to the parts of the data we care about.
        metadata = raw_data["content"]["gamepackage"]["gmStrp"]
        team_stats = raw_data["content"]["gamepackage"]["tmStats"]

        game_data["Game Date"] = metadata["dt"]
        game_data["hometeam Name"] = team_stats["home"]["t"]["dspNm"]
        game_data["hometeam ID"] = team_stats["home"]["t"]["id"]
        game_data["awayteam Name"] = team_stats["away"]["t"]["dspNm"]
        game_data["awayteam ID"] = team_stats["away"]["t"]["id"]
    except KeyError:
        return game_data

    for team in ["home", "away"]:
        for stat in team_stats[team]["s"].values():
            # If this is a compound stat (like shots made with shots attempted),
            # break it out into different fields.
            if "-" in stat["n"]:
                for n, d in zip(stat["n"].split("-"), stat["d"].split("-")):
                    game_data["{}team {}".format(team, n)] = d
            else:
                game_data["{}team {}".format(team, stat["l"])] = stat["d"]

    for team_data in metadata["tms"]:
        if team_data["isHome"]:
            game_data["hometeam Score"] = team_data.get("score")
        else:
            game_data["awayteam Score"] = team_data.get("score")

    return game_data


async def get_games_data(start_date: date, end_date: date) -> List[Dict[str, str]]:
    games_data: List[Dict[str, str]] = list()

    async def gather_game_data(game: str):
        games_data.append(await get_game_data(session, game))

    async with aiohttp.ClientSession() as session:
        games = await get_game_list(session, start_date, end_date)

        # Run all game gathering tasks at the same time.
        tasks = [gather_game_data(game) for game in games]
        await asyncio.gather(*tasks)

    return games_data


def split_stat(key: str, value: str) -> Iterator[Tuple[str, str]]:
    if multi_stat := multi_stat_re.search(key):
        full_stats: List[str] = list()

        sub_stats = multi_stat.group().split("-")
        for stat in sub_stats:
            full_stats.append(key.replace(multi_stat.group(), stat))

        return zip(full_stats, value.split("-"))

    return iter(())


async def get_player_data(
    session: aiohttp.ClientSession | None, player_id: str, group_filter: List[str] = []
) -> Dict[str, str]:
    if not session:
        async with aiohttp.ClientSession() as session:
            raw_data = await get_data(session, playerstats_url.format(player_id))
    else:
        raw_data = await get_data(session, playerstats_url.format(player_id))

    player_data: Dict[str, str] = dict()

    player_data["player ID"] = player_id

    metadata = raw_data["page"]["content"]["player"]["plyrHdr"]["ath"]
    player_stats = raw_data["page"]["content"]["player"]["stat"]

    player_data["birthplace"] = metadata.get("brthpl")
    player_data["position"] = metadata.get("pos")
    player_data["status"] = metadata.get("sts")
    player_data["class"] = metadata.get("exp")
    player_data["team name"] = metadata.get("tm")
    player_data["first name"] = metadata.get("fNm")
    player_data["last name"] = metadata.get("lNm")
    player_data["full name"] = metadata.get("dspNm")
    player_data["display number"] = metadata.get("dspNum")
    if team_id := metadata.get("tmUid"):
        player_data["team ID"] = team_id.split(":")[-1]
    if height_weight := metadata.get("htwt"):
        player_data["height"], player_data["weight"] = height_weight.split(",")

    for group in player_stats["tbl"]:
        prefix = group["ttl"]
        if group_filter and prefix not in group_filter:
            continue

        rows = group["row"] + [group["car"]]

        for index, column in enumerate(group["col"]):
            # First two entries are Season and Team, not stats.
            if index < 2:
                continue

            key = f"{prefix} {column['ttl']}"

            # Percentages can be derived from other fields.
            if "Percentage" in key:
                continue

            for row in rows:
                season = row[0]

                # If this is a compound stat (like shots made with shots attempted),
                # break it out into different fields.
                if "-" in key:
                    for sub_key, value in split_stat(key, row[index]):
                        player_data[f"{sub_key} {season}"] = value
                else:
                    player_data[f"{key} {season}"] = row[index]

    return player_data


async def get_team_list(session: aiohttp.ClientSession) -> Dict[str, Dict[str, str]]:
    teams: Dict[str, Dict[str, str]] = dict()

    data = await get_data(session, teamlist_url)

    columnlist = data["page"]["content"]["leagueTeams"]["columns"]
    grouplist = [group for column in columnlist for group in column["groups"]]

    for group in grouplist:
        group_name = group["nm"]

        for team in group["tms"]:
            teams[team["id"]] = {
                "name": team["n"],
                "group": group_name,
            }

    return teams


async def get_player_list(session: aiohttp.ClientSession, team: str) -> List[str]:
    players: List[str] = list()

    data = await get_data(session, playerlist_url.format(team))

    try:
        playerlist = data["page"]["content"]["roster"]["athletes"]
    except KeyError:
        return players

    for player in playerlist:
        players.append(player["id"])

    return players


async def get_league_players_data(group_filter: List[str] = []) -> List[Dict[str, str]]:
    players_data: List[Dict[str, str]] = list()

    async def gather_player_list(team: str):
        players.extend(await get_player_list(session, team))

    async def gather_player_data(player: str):
        players_data.append(await get_player_data(session, player, group_filter))

    async with aiohttp.ClientSession() as session:
        teams = await get_team_list(session)

        players: List[str] = list()

        # Run all player gathering tasks at the same time.
        tasks = [gather_player_list(team) for team in teams]
        await asyncio.gather(*tasks)

        tasks = [gather_player_data(player) for player in players]
        await asyncio.gather(*tasks)

    return players_data
