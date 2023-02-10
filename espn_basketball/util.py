import csv
from typing import Dict, List


def write_data_to_csv(data: List[Dict[str, str]], output_path: str):
    # Get all field names in the data dictionaries.
    fieldnames = list(set().union(*(d.keys() for d in data)))
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

        for row in data:
            writer.writerow(row)
