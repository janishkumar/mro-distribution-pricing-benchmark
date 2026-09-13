import logging
import sqlite3
from typing import Any

import requests

from src.config import DB_PATH, FRED_API_KEY, FRED_BASE_URL

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

HEADLINE_PPI_SERIES_ID = "PCU423700423700"
PRIMARY_SERVICES_PPI_SERIES_ID = "PCU4237004237001"
SECTORAL_OUTPUT_SERIES_ID = "IPUGN4237T300000000"

SERIES_TO_FETCH = [
    HEADLINE_PPI_SERIES_ID,
    PRIMARY_SERVICES_PPI_SERIES_ID,
    SECTORAL_OUTPUT_SERIES_ID,
]


def fetch_series_observations(series_id: str) -> dict[str, Any]:
    resp = requests.get(
        f"{FRED_BASE_URL}/series/observations",
        params={
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "observation_start": "2019-01-01",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def parse_observations(raw: dict[str, Any], series_id: str) -> list[tuple[str, str, float]]:
    rows = []
    for obs in raw.get("observations", []):
        if obs["value"] == ".":
            continue
        rows.append((series_id, obs["date"], float(obs["value"])))
    return rows


def load_rows(rows: list[tuple[str, str, float]], db_path=DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executemany(
            "INSERT OR REPLACE INTO ppi_monthly (series_id, date, value) VALUES (?, ?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def run() -> None:
    for series_id in SERIES_TO_FETCH:
        logger.info("Fetching FRED series %s", series_id)
        raw = fetch_series_observations(series_id)
        rows = parse_observations(raw, series_id)
        load_rows(rows)
        logger.info("Loaded %d observations for %s", len(rows), series_id)


if __name__ == "__main__":
    run()
