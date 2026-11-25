"""Reading CSV files into flight records and error messages."""

import csv
from pathlib import Path

from validator import to_record, validate_row


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    """Process the CSV files in the order given.

    Return (records, errors):
      records - valid flight records, in input order
      errors  - one message per invalid row, in input order, formatted as
                "<file name>:<line number>: <ERROR_CODE> | <free text>"
                (base file name only, no timestamp or level, no newline)

    Also performs the DUPLICATE_FLIGHT check across all the files.
    Does not write any files and does not log anything itself.
    """
    records: list[dict] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()

    for path_str in paths:
        file_name = Path(path_str).name
        with open(path_str, encoding="utf-8", newline="") as f:
            lines = f.read().splitlines()

        for line_no, raw_line in enumerate(lines, start=1):
            # Line 1 is the header; skip blank lines and '#' comments.
            if line_no == 1 or not raw_line.strip() or raw_line.lstrip().startswith("#"):
                continue

            fields = next(csv.reader([raw_line]))
            err = validate_row(fields, airports)
            if err is not None:
                errors.append(f"{file_name}:{line_no}: {err} | {raw_line}")
                continue

            record = to_record(fields)
            key = (record["flight_id"], record["departure_datetime"])
            if key in seen:
                errors.append(f"{file_name}:{line_no}: DUPLICATE_FLIGHT | {raw_line}")
                continue

            seen.add(key)
            records.append(record)

    return records, errors