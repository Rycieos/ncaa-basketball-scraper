#!/usr/bin/env python3

import argparse
import asyncio
from datetime import date

import ncaa_basketball.ncaa as ncaa
import ncaa_basketball.util as util


def compile_data(
    division: str, start_date: date, end_date: date, output_path: str, mirror: bool
):
    games_data = asyncio.run(
        ncaa.get_games_pbp(division, start_date, end_date, mirror=mirror)
    )

    util.write_data_to_csv(games_data, output_path)


# Command line start point
def main():
    parser = argparse.ArgumentParser(
        description="Fetch NCAA basketball play by play data and write them to a CSV."
    )

    parser.add_argument(
        "division",
        type=str,
        help="Division to lookup games in. Eg: d3.",
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
    parser.add_argument(
        "--mirror",
        action="store_true",
        help="Create a mirror record for each event with the home and visitor teams switched.",
    )

    args = parser.parse_args()

    compile_data(
        args.division,
        date.fromisoformat(args.start_date),
        date.fromisoformat(args.end_date),
        "play_by_play.csv",
        mirror=args.mirror,
    )


if __name__ == "__main__":
    main()
