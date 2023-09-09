import asyncio
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import AsyncIterator, Dict, List, Set, Tuple

import aiohttp

from ncaa_basketball.util import get_url

gamelist_url = (
    "https://data.ncaa.com/casablanca/scoreboard/basketball-men/{}/{}/scoreboard.json"
)

# gameinfo_url = "https://data.ncaa.com/casablanca/game/{}/gameInfo.json"
# boxscore_url = "https://data.ncaa.com/casablanca/game/{}/boxscore.json"
play_by_play_url = "https://data.ncaa.com/casablanca/game/{}/pbp.json"

foul_capture = re.compile(r".*?'s ?([^\)]+) \((.+) draws the foul\)")
player_capture = re.compile(r".*?(?:'s ?|-)(.+)")
alt_player_capture = re.compile(r".*? by (.+)")
player_sanitize = re.compile(r"(.+), (.+)")


# Get all game IDs between the two dates, inclusive.
async def get_game_list(
    session: aiohttp.ClientSession,
    division: str,
    start_date: date,
    end_date: date,
) -> Set[str]:
    games: Set[str] = set()

    delta = end_date - start_date

    # For each day between the inputs.
    for i in range(delta.days + 1):
        day = start_date + timedelta(days=i)

        data = json.loads(
            await get_url(
                session, gamelist_url.format(division, day.strftime("%Y/%m/%d"))
            )
        )

        gamelist = data.get("games", [])
        for game in gamelist:
            games.add(game["game"]["url"].removeprefix("/game/"))

    return games


# Get all game data for the given ID.
async def get_pbp_data(
    session: aiohttp.ClientSession, game_id: str
) -> AsyncIterator[List[Dict[str, str]]]:
    data = json.loads(await get_url(session, play_by_play_url.format(game_id)))

    game_data = dict()
    game_data["gameID"] = game_id

    for team in data.get("meta", {}).get("teams", {}):
        if team["homeTeam"] == "true":
            game_data["homeTeamID"] = team["id"]
            game_data["homeTeamName"] = team["shortName"]
        else:
            game_data["visitorTeamID"] = team["id"]
            game_data["visitorTeamName"] = team["shortName"]

    periods = data.get("periods", {})

    for period in periods:
        events = list()
        game_data["period"] = period["periodNumber"]
        for event in period["playStats"]:
            events.append(event | game_data)

        yield events


@dataclass
class EventPlayers:
    event: Dict[str, str]
    active_home_players: Set[str]
    active_away_players: Set[str]


def expand_pbp_data(events: List[Dict[str, str]], mirror: bool) -> List[Dict[str, str]]:
    working_list: List[EventPlayers] = list()
    active_home_players: Set[str] = set()
    active_away_players: Set[str] = set()

    previous_score = "0-0"

    for event in events:
        if event["score"]:
            previous_score = event["score"]
        else:
            event["score"] = previous_score

        event["homeScore"], event["visitorScore"] = event["score"].split("-")

        time = event["time"].split(":")
        event["timeSeconds"] = str(int(time[0]) * 60 + int(time[1]))

        if text := event["homeText"]:
            event["eventType"], event["shotMade"], with_player = get_event_type(text)
            if with_player:
                event["homePlayer"], event["visitorPlayer"] = get_player_from_event(
                    text, event["homeTeamName"]
                )
            event["isHomeEvent"] = "TRUE"
        elif text := event["visitorText"]:
            event["eventType"], event["shotMade"], with_player = get_event_type(text)
            if with_player:
                event["visitorPlayer"], event["homePlayer"] = get_player_from_event(
                    text, event["visitorTeamName"]
                )
            event["isHomeEvent"] = "FALSE"

        if player := event.get("homePlayer"):
            if "Subbing out" in event["homeText"]:
                active_home_players.discard(player)
            else:
                active_home_players.add(player)

        if player := event.get("visitorPlayer"):
            if "Subbing out" in event["visitorText"]:
                active_away_players.discard(player)
            else:
                active_away_players.add(player)

        working_list.append(
            EventPlayers(
                event,
                active_home_players.copy(),
                active_away_players.copy(),
            )
        )

    for event_player in reversed(working_list):
        event = event_player.event

        if player := event.get("homePlayer"):
            if "Subbing in" in event["homeText"]:
                active_home_players.discard(player)
            else:
                active_home_players.add(player)

        if player := event.get("visitorPlayer"):
            if "Subbing in" in event["visitorText"]:
                active_away_players.discard(player)
            else:
                active_away_players.add(player)

        event_player.active_home_players.update(active_home_players)
        event_player.active_away_players.update(active_away_players)

    results = list()
    for event_player in working_list:
        event = event_player.event

        # if (
        #    len(event_player.active_home_players) != 5
        #    or len(event_player.active_away_players) != 5
        # ):
        #    print(
        #        "WARNING: record does not have exactly 10 players: {}".format(
        #            event_player
        #        )
        #    )

        ordered_home_players = sorted(event_player.active_home_players)
        ordered_away_players = sorted(event_player.active_away_players)

        for i, player in enumerate(ordered_home_players, start=1):
            event[f"homePlayer{i}"] = player
        for i, player in enumerate(ordered_away_players, start=1):
            event[f"visitorPlayer{i}"] = player

        home_player_hash = hashlib.sha256()
        for player in ordered_home_players:
            home_player_hash.update(player.encode("utf-8"))
        event["homePlayerUID"] = home_player_hash.hexdigest()

        away_player_hash = hashlib.sha256()
        for player in ordered_away_players:
            away_player_hash.update(player.encode("utf-8"))
        event["visitorPlayerUID"] = away_player_hash.hexdigest()

        event["isMirroredEvent"] = "FALSE"
        results.append(event)

        if mirror:
            mirrored_event = dict()
            for k, v in event.items():
                if k.startswith("home"):
                    key = "visitor" + k.removeprefix("home")
                    mirrored_event[key] = v
                elif k.startswith("visitor"):
                    key = "home" + k.removeprefix("visitor")
                    mirrored_event[key] = v
                else:
                    mirrored_event[k] = v

            if mirrored_event.get("isHomeEvent") == "TRUE":
                mirrored_event["isHomeEvent"] = "FALSE"
            elif mirrored_event.get("isHomeEvent") == "FALSE":
                mirrored_event["isHomeEvent"] = "TRUE"

            mirrored_event["isMirroredEvent"] = "TRUE"
            results.append(mirrored_event)

    return results


def get_event_type(event: str) -> Tuple[str, str, bool]:
    event = event.lower()
    shot_made = ""
    with_player = True

    if event.startswith("subbing"):
        event_type = "Sub"
    elif "turnover" in event or "steal" in event:
        event_type = "Turnover"
    elif "assist" in event:
        event_type = "Assist"
    elif "rebound" in event:
        event_type = "Rebound"
    elif "block" in event:
        event_type = "Block"
    elif event.startswith("end of"):
        event_type = "End of period"
        with_player = False
    elif event.startswith("free throw"):
        event_type = "Free throw"
        shot_made = "TRUE"
    elif event.startswith("layup"):
        event_type = "Layup"
        shot_made = "TRUE"
    elif event.startswith("2 pointer"):
        event_type = "2 pointer"
        shot_made = "TRUE"
    elif event.startswith("3 pointer"):
        event_type = "3 pointer"
        shot_made = "TRUE"
    elif event.startswith("jumper"):
        event_type = "Jumper"
        shot_made = "TRUE"
    elif event.startswith("slam dunk"):
        event_type = "Dunk"
        shot_made = "TRUE"
    elif "time out" in event or "timeout" in event:
        with_player = False
        if "short" in event or "30" in event:
            event_type = "Short timeout"
        elif "media" in event:
            event_type = "Media timeout"
        else:
            event_type = "Full timeout"
    elif "foul " in event:
        if "offensive" in event:
            event_type = "Offensive foul"
        elif "technical" in event:
            event_type = "Technical foul"
        else:
            event_type = "Personal foul"
    else:
        print("WARNING: Unknown event type: '{}'".format(event))
        event_type = ""

    if shot_made == "TRUE" and "missed" in event:
        shot_made = "FALSE"

    return (event_type, shot_made, with_player)


def get_player_from_event(event: str, team_name: str) -> Tuple[str, str]:
    fouled_player = ""
    remainder = event.split(sep=team_name, maxsplit=1)[-1]

    if capture := foul_capture.match(remainder):
        player = capture.group(1)
        fouled_player = capture.group(2)

    elif capture := player_capture.match(remainder):
        player = capture.group(1)

    elif capture := alt_player_capture.match(remainder):
        player = capture.group(1)

    else:
        # print("WARNING: no player match on '{}'. Team name '{}'".format(event, team_name))
        return ("", "")

    if player == team_name:
        # I found this a few times in poor data.
        # Eg: "Foul on Illinois'sIllinois"
        player = ""

    return (sanitize_name(player), sanitize_name(fouled_player))


def sanitize_name(name: str) -> str:
    name = name.strip()
    # Special case for  Viktor Rajković.
    name = name.replace("Ä\u0087", "ć")
    if not name or name == "team" or "shot clock" in name:
        return ""
    elif capture := player_sanitize.match(name):
        return "{} {}".format(capture.group(2), capture.group(1))
    else:
        return name


async def get_games_pbp(
    division: str, start_date: date, end_date: date, mirror: bool
) -> List[Dict[str, str]]:
    games_data: List[Dict[str, str]] = list()

    async def gather_game_data(game: str):
        data = get_pbp_data(session, game)
        async for period in data:
            games_data.extend(expand_pbp_data(period, mirror=mirror))

    async with aiohttp.ClientSession() as session:
        games = await get_game_list(session, division, start_date, end_date)

        # Run all game gathering tasks at the same time.
        tasks = [gather_game_data(game) for game in games]
        await asyncio.gather(*tasks)

    return games_data
