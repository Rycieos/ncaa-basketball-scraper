import asyncio
import csv
from typing import Dict, List

import aiohttp


def write_data_to_csv(data: List[Dict[str, str]], output_path: str):
    # Get all field names in the data dictionaries.
    fieldnames = list(set().union(*(d.keys() for d in data)))
    fieldnames.sort()

    with open(output_path, "w", newline="", encoding="UTF-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        writer.writerows(data)


async def get_url(session: aiohttp.ClientSession, url: str) -> str:
    retries = 0
    while True:
        try:
            async with session.get(url) as resp:
                if resp.status >= 500:
                    resp.raise_for_status()
                return await resp.text()
        except aiohttp.ClientError as e:
            retries += 1
            if retries > 3:
                raise e
            await asyncio.sleep(1)
