#!/usr/bin/env python3

import argparse
import asyncio
import sys
from typing import List

import espn
import util


# Command line start point
def main(*argv: List[str]):
    parser = argparse.ArgumentParser(
        description="Fetch NCAA basketball player stats and write them to a CSV file."
    )

    parser.add_argument(
        "player",
        type=str,
        help="Player ID to get stats for.",
    )

    args = parser.parse_args(*argv)

    player_data = asyncio.run(espn.get_player_data(args.player))

    util.write_data_to_csv([player_data], "playerdata.csv")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
