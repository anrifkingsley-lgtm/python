"""Running queries against the flight database."""

from datetime import datetime
import math
import re

RECORD_KEYS = {
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
    "price",
}
ALLOWED_KEYS = RECORD_KEYS | {"min_price", "sort_by", "order", "limit"}
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
DATETIME_FMT = "%Y-%m-%d %H:%M"


def _valid_datetime(value: object) -> bool:
    if not isinstance(value, str) or not DATETIME_RE.fullmatch(value):
        return False
    try:
        dt = datetime.strptime(value, DATETIME_FMT)
    except ValueError:
        return False
    return dt.strftime(DATETIME_FMT) == value


def _valid_number(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def _valid_limit(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= 0


def _is_valid_query(query: object) -> bool:
    if not isinstance(query, dict):
        return False
    if not set(query.keys()).issubset(ALLOWED_KEYS):
        return False
    if "order" in query and "sort_by" not in query:
        return False

    for key in ("flight_id", "origin", "destination"):
        if key in query and not isinstance(query[key], str):
            return False

    for key in ("departure_datetime", "arrival_datetime"):
        if key in query and not _valid_datetime(query[key]):
            return False

    for key in ("price", "min_price"):
        if key in query and not _valid_number(query[key]):
            return False

    if "sort_by" in query and (
        not isinstance(query["sort_by"], str) or query["sort_by"] not in RECORD_KEYS
    ):
        return False

    if "order" in query and (
        not isinstance(query["order"], str) or query["order"] not in ("asc", "desc")
    ):
        return False

    if "limit" in query and not _valid_limit(query["limit"]):
        return False

    return True


def _matches(record: dict, query: dict) -> bool:
    if "flight_id" in query and record.get("flight_id") != query["flight_id"]:
        return False
    if "origin" in query and record.get("origin") != query["origin"]:
        return False
    if "destination" in query and record.get("destination") != query["destination"]:
        return False
    if "departure_datetime" in query and record.get("departure_datetime", "") < query["departure_datetime"]:
        return False
    if "arrival_datetime" in query and record.get("arrival_datetime", "") > query["arrival_datetime"]:
        return False
    if "price" in query and record.get("price", math.inf) > query["price"]:
        return False
    if "min_price" in query and record.get("price", -math.inf) < query["min_price"]:
        return False
    return True


def run_query(db: list[dict], query: dict) -> dict:
    """Return one response entry for one query object.

    Valid query:   {"query": query, "matches": [...]}
    Invalid query: {"query": query, "error": "INVALID_QUERY", "matches": []}
    """
    if not _is_valid_query(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}

    matches = [dict(row) for row in db if _matches(row, query)]

    if "sort_by" in query:
        sort_key = query["sort_by"]
        reverse = query.get("order", "asc") == "desc"
        matches = sorted(matches, key=lambda r: r[sort_key], reverse=reverse)

    if "limit" in query:
        matches = matches[: query["limit"]]

    return {"query": query, "matches": matches}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Accept one query object or a list of them; always return a list."""
    items = [queries] if isinstance(queries, dict) else list(queries)
    return [run_query(db, q) for q in items]