#!/usr/bin/env python3

import argparse
import asyncio
import csv
import sys
from datetime import date
from typing import Dict, List

import espn


def compile_data(start_date: date, end_date: date, output_path: str):
    games_data = asyncio.run(espn.get_games_data(start_date, end_date))

    # Get all field names in the game data dictionaries.
    fieldnames = list(set().union(*(d.keys() for d in games_data)))
    fieldnames.sort()

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
