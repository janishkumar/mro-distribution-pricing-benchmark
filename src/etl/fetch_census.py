import logging
import sqlite3
from collections import defaultdict

import requests

from src.config import CENSUS_API_KEY, CENSUS_MWTS_URL, DB_PATH, NAICS_CODE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def fetch_mwts_raw() -> list[list[str]]:
    resp = requests.get(
        CENSUS_MWTS_URL,
        params={
            "get": "cell_value,data_type_code,time_slot_id",
            "category_code": NAICS_CODE,
            "time": "from 2019",
            "seasonally_adj": "no",
            "key": CENSUS_API_KEY,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def parse_mwts_response(raw: list[list[str]]) -> dict[tuple[str, str], dict[str, float]]:
    header, *data_rows = raw
    idx = {name: i for i, name in enumerate(header)}

    result: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for row in data_rows:
        data_type = row[idx["data_type_code"]]
        if data_type not in ("SM", "IM"):
            continue

        time_str = row[idx["time"]]  # "2024-01"
        date = f"{time_str}-01"
        category = row[idx["category_code"]]
        value = float(row[idx["cell_value"]])

        key = (category, date)
        if data_type == "SM":
            result[key]["sales"] = value
        elif data_type == "IM":
            result[key]["inventories"] = value

    return dict(result)


def load_rows(parsed: dict[tuple[str, str], dict[str, float]], db_path=DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        for (naics, date), values in parsed.items():
            conn.execute(
                """
                INSERT INTO census_wholesale_monthly (naics, date, sales, inventories)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(naics, date) DO UPDATE SET
                    sales = COALESCE(excluded.sales, sales),
                    inventories = COALESCE(excluded.inventories, inventories)
                """,
                (naics, date, values.get("sales"), values.get("inventories")),
            )
        conn.commit()
    finally:
        conn.close()


def run() -> None:
    logger.info("Fetching Census MWTS for NAICS %s", NAICS_CODE)
    raw = fetch_mwts_raw()
    parsed = parse_mwts_response(raw)
    load_rows(parsed)
    logger.info("Loaded %d month(s) of Census wholesale data", len(parsed))


if __name__ == "__main__":
    run()
