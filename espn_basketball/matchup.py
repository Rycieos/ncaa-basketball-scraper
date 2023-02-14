#!/usr/bin/env python3

import argparse
import asyncio
import sys
from datetime import date
from typing import List

import espn
import util


def compile_data(start_date: date, end_date: date, output_path: str):
    games_data = asyncio.run(espn.get_games_data(start_date, end_date))

    util.write_data_to_csv(games_data, output_path)


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
