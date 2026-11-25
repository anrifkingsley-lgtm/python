"""Flight Schedule Parser and Query Tool - command-line entry point.

Run from the project folder, for example:
    python flight_parser.py -i data/db.csv -a data/airports.txt
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import logging
from pathlib import Path
import sys

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

# TODO: fill in your details: plain ASCII, no spaces or underscores.
STUDENT_ID = "260ADB184"
FIRST_NAME = "anrifoudine"
LAST_NAME = "salim"

LOGGER_NAME = "flight_parser"


class _ParserError(Exception):
    """Raised when argparse reports a usage error."""


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _ParserError(message)


def _make_parser() -> _ArgumentParser:
    parser = _ArgumentParser(prog="flight_parser.py", add_help=True)
    parser.add_argument("-i", dest="csv_file")
    parser.add_argument("-d", dest="csv_dir")
    parser.add_argument("-j", dest="json_db")
    parser.add_argument("-a", dest="airports")
    parser.add_argument("-o", dest="out_db")
    parser.add_argument("-q", dest="query_file")
    parser.add_argument("-r", dest="out_dir", default=".")
    return parser


def _attach_handler(log_path: Path) -> tuple[logging.Logger, logging.FileHandler]:
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(handler)
    return logger, handler


def _detach_handler(logger: logging.Logger, handler: logging.FileHandler | None) -> None:
    if handler is not None:
        try:
            logger.removeHandler(handler)
        finally:
            handler.close()


def _read_json(path_str: str, label: str) -> object:
    path = Path(path_str)
    if not path.is_file():
        raise RuntimeError(f"{label} not found: {path_str}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"cannot read {label} '{path_str}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON in {label} '{path_str}': {exc.msg}") from exc


def _collect_csv_paths(args: argparse.Namespace) -> list[str]:
    if args.csv_file is not None:
        p = Path(args.csv_file)
        if not p.is_file():
            raise RuntimeError(f"CSV file not found: {args.csv_file}")
        try:
            p.open("r", encoding="utf-8").close()
        except OSError as exc:
            raise RuntimeError(f"cannot read CSV file '{args.csv_file}': {exc}") from exc
        return [str(p)]

    folder = Path(args.csv_dir)
    if not folder.is_dir():
        raise RuntimeError(f"folder not found: {args.csv_dir}")
    try:
        entries = list(folder.iterdir())
    except OSError as exc:
        raise RuntimeError(f"cannot read folder '{args.csv_dir}': {exc}") from exc

    csvs = sorted(e for e in entries if e.is_file() and e.name.endswith(".csv"))
    if not csvs:
        raise RuntimeError(f"no .csv files in folder: {args.csv_dir}")

    for csv_path in csvs:
        try:
            csv_path.open("r", encoding="utf-8").close()
        except OSError as exc:
            raise RuntimeError(f"cannot read CSV file '{csv_path}': {exc}") from exc

    return [str(p) for p in csvs]


def main(argv: list[str] | None = None) -> int:
    """Run the whole program and return the exit code (0, 1 or 2).

    argv is the argument list without the program name.
    None means use sys.argv[1:] (argparse does this for you).
    Do not call sys.exit() inside main(); return the code instead.
    """
    parser = _make_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 0
    except _ParserError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    sources = [s for s in (args.csv_file, args.csv_dir, args.json_db) if s is not None]
    if len(sources) != 1:
        print("Error: exactly one of -i, -d, or -j is required", file=sys.stderr)
        return 2

    from_json = args.json_db is not None
    if not from_json and not args.airports:
        print("Error: -a is required with -i or -d", file=sys.stderr)
        return 2
    if from_json and args.out_db is not None:
        print("Error: -o is not allowed with -j", file=sys.stderr)
        return 2

    logger = logging.getLogger(LOGGER_NAME)
    handler: logging.FileHandler | None = None

    try:
        if from_json:
            raw_db = _read_json(args.json_db, "JSON database")
            if not isinstance(raw_db, list) or not all(isinstance(x, dict) for x in raw_db):
                raise RuntimeError("JSON database must be a JSON array of objects")
            db = raw_db
        else:
            csv_paths = _collect_csv_paths(args)
            airports_path = Path(args.airports)
            if not airports_path.is_file():
                raise RuntimeError(f"airport file not found: {args.airports}")
            try:
                airports = load_airports(str(airports_path))
            except OSError as exc:
                raise RuntimeError(f"cannot read airport file '{args.airports}': {exc}") from exc

            out_db_path = Path(args.out_db) if args.out_db is not None else Path("db.json")
            if not out_db_path.parent.is_dir():
                raise RuntimeError(f"output folder does not exist: {out_db_path.parent}")

            logger, handler = _attach_handler(out_db_path.parent / "errors.log")
            db, errors = parse_files(csv_paths, airports)
            for msg in errors:
                logger.warning(msg)

            try:
                out_db_path.write_text(json.dumps(db, indent=2), encoding="utf-8")
            except OSError as exc:
                raise RuntimeError(f"cannot write database '{out_db_path}': {exc}") from exc

        if args.query_file is not None:
            resp_dir = Path(args.out_dir)
            if not resp_dir.is_dir():
                raise RuntimeError(f"response folder does not exist: {args.out_dir}")

            raw_queries = _read_json(args.query_file, "query file")
            if not isinstance(raw_queries, dict) and not (
                isinstance(raw_queries, list) and all(isinstance(x, dict) for x in raw_queries)
            ):
                raise RuntimeError("query file must contain a query object or an array of query objects")

            responses = run_queries(db, raw_queries)
            stamp = datetime.now().strftime("%Y%m%d_%H%M")
            resp_name = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{stamp}.json"
            try:
                (resp_dir / resp_name).write_text(json.dumps(responses, indent=2), encoding="utf-8")
            except OSError as exc:
                raise RuntimeError(f"cannot write response file '{resp_dir / resp_name}': {exc}") from exc

        return 0
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        _detach_handler(logger, handler)


if __name__ == "__main__":
    sys.exit(main())