#!/usr/bin/env python3

import argparse
import csv
import json
import requests
import sys
from bs4 import BeautifulSoup
from datetime import date, timedelta
from typing import Any, Dict, List, Set

# Group 50 is Division I.
gamelist_url = (
    "https://www.espn.com/mens-college-basketball/scoreboard/_/date/{}/group/50"
)
gamestats_url = "https://www.espn.com/mens-college-basketball/matchup/_/gameId/{}"

script_start = "window['__espnfitt__']="
script_end = ";"


# Download the page, and load the data as a HTML document.
def get_data(url: str) -> Dict[str, Any]:
    resp = requests.get(url)
    document = BeautifulSoup(resp.content, "html.parser")

    # Locate the specific object that contains all of the data, and capture it.
    scripts = document.find_all("script")
    for script in scripts:
        if script.text.startswith(script_start):
            data = script.text.removeprefix(script_start).removesuffix(script_end)
            break

    # Convert the text of the page into a data format Python understands.
    return json.loads(data)


# Get all game IDs between the two dates, inclusive.
def get_game_list(start_date: date, end_date: date) -> Set[str]:
    games: Set[str] = set()

    delta = end_date - start_date

    # For each day between the inputs.
    for i in range(delta.days + 1):
        day = start_date + timedelta(days=i)

        data = get_data(gamelist_url.format(day.strftime("%Y%m%d")))

        gamelist = data["page"]["content"]["scoreboard"]["evts"]
        for game in gamelist:
            games.add(game["id"])

    return games


# Get all game data for the given ID.
def get_game_data(game_id: str) -> Dict[str, str]:
    raw_data = get_data(gamestats_url.format(game_id))["page"]
    game_data: Dict[str, str] = dict()
    game_data["GameID"] = game_id

    game_data["GameTitle"] = raw_data["meta"]["title"]

    # Save references to the parts of the data we care about.
    metadata = raw_data["content"]["gamepackage"]["gmStrp"]
    team_stats = raw_data["content"]["gamepackage"]["tmStats"]

    game_data["Game Date"] = metadata["dt"]
    game_data["hometeam Name"] = team_stats["home"]["t"]["dspNm"]
    game_data["hometeam ID"] = team_stats["home"]["t"]["id"]
    game_data["awayteam Name"] = team_stats["away"]["t"]["dspNm"]
    game_data["awayteam ID"] = team_stats["away"]["t"]["id"]

    for team in ["home", "away"]:
        for stat in team_stats[team]["s"].values():
            # If this is a compound stat (like shots made with shots attempted),
            # break it out into different fields.
            if "-" in stat["n"]:
                for l, d in zip(stat["n"].split("-"), stat["d"].split("-")):
                    game_data["{}team {}".format(team, l)] = d
            else:
                game_data["{}team {}".format(team, stat["l"])] = stat["d"]

    for team in metadata["tms"]:
        if team["isHome"]:
            game_data["hometeam Score"] = team.get("score")
        else:
            game_data["awayteam Score"] = team.get("score")

    return game_data


def compile_data(start_date: date, end_date: date, output_path: str):
    games_data: List[Dict[str, str]] = list()
    for game in get_game_list(start_date, end_date):
        games_data.append(get_game_data(game))

    # Get all field names in the game data dictionaries.
    fieldnames = set().union(*(d.keys() for d in games_data))

    with open(output_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()

        for game_data in games_data:
            writer.writerow(game_data)


# Command line start point
def main(*argv: List[str]):
    parser = argparse.ArgumentParser(
        description="Fetch NCAA basketball game stats and write them to a CSV file."
    )

    parser.add_argument(
        "start_date",
        type=str,
        help="First date to fetch games from, in any ISO format. Eg: 2023-01-16.",
    )
    parser.add_argument(
        "end_date",
        type=str,
        help="Last date to fetch games from, inclusive.",
    )

    args = parser.parse_args(*argv)

    compile_data(
        date.fromisoformat(args.start_date),
        date.fromisoformat(args.end_date),
        "gamedata.csv",
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
