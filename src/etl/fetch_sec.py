import logging
import sqlite3
from datetime import date
from typing import Any

import requests

from src.config import (
    COMP_TICKERS,
    DB_PATH,
    SEC_COMPANYFACTS_URL,
    SEC_TICKERS_URL,
    SEC_USER_AGENT,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": SEC_USER_AGENT}

# Ordered newest-convention first; a company may use different tags across
# its history (e.g. GWW's "Revenues" tag has one usable quarter, its real
# history is under "RevenueFromContractWithCustomerExcludingAssessedTax"
# post-2018 and "SalesRevenueNet" pre-2018). All are merged, not just the
# first one found.
REVENUE_TAGS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
]
GROSS_PROFIT_TAGS = ["GrossProfit"]
COST_TAGS = ["CostOfGoodsAndServicesSold", "CostOfRevenue"]

MIN_QUARTER_DAYS = 80
MAX_QUARTER_DAYS = 100


def fetch_tickers_json() -> dict[str, Any]:
    resp = requests.get(SEC_TICKERS_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def resolve_cik(tickers_json: dict[str, Any], ticker: str) -> int | None:
    ticker_upper = ticker.upper()
    for entry in tickers_json.values():
        if entry["ticker"].upper() == ticker_upper:
            return entry["cik_str"]
    return None


def fetch_companyfacts(cik: int) -> dict[str, Any]:
    url = SEC_COMPANYFACTS_URL.format(cik=cik)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _parse_date(s: str) -> date:
    y, m, d = map(int, s.split("-"))
    return date(y, m, d)


def _quarter_key(end: str) -> str:
    end_date = _parse_date(end)
    q = (end_date.month - 1) // 3 + 1
    return f"{end_date.year}Q{q}"


def _quarterly_values(facts: dict[str, Any], tag: str) -> dict[str, dict[str, Any]]:
    """Pull quarter-length (~3 month) USD entries for a tag, keyed by the
    calendar quarter the period *end* date falls in.

    Deliberately does not filter on form/fp: some companies (e.g. WCC) only
    disclose quarterly figures inside a 10-K's "selected quarterly data"
    footnote, tagged form=10-K/fp=FY, not form=10-Q. Filtering by the
    period's actual duration instead of the filing type catches those.
    When multiple filings report the same quarter (restatements), the most
    recently filed value wins.
    """
    units = facts["facts"]["us-gaap"][tag]["units"]
    usd_entries = units.get("USD", [])

    by_quarter: dict[str, dict[str, Any]] = {}
    for entry in usd_entries:
        start, end = entry.get("start"), entry.get("end")
        if not start or not end:
            continue
        duration_days = (_parse_date(end) - _parse_date(start)).days
        if not (MIN_QUARTER_DAYS <= duration_days <= MAX_QUARTER_DAYS):
            continue

        key = _quarter_key(end)
        existing = by_quarter.get(key)
        if existing is None or entry.get("filed", "") >= existing.get("filed", ""):
            by_quarter[key] = entry

    return by_quarter


def _merged_quarterly_values(facts: dict[str, Any], candidate_tags: list[str]) -> dict[str, dict[str, Any]]:
    """Merge quarterly data across multiple candidate XBRL tags for the same
    concept, keeping the most recently filed entry per quarter and tracking
    which tag supplied it.
    """
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    merged: dict[str, dict[str, Any]] = {}

    for tag in candidate_tags:
        if tag not in us_gaap:
            continue
        for key, entry in _quarterly_values(facts, tag).items():
            existing = merged.get(key)
            if existing is None or entry.get("filed", "") > existing["entry"].get("filed", ""):
                merged[key] = {"entry": entry, "tag": tag}

    return merged


def compute_margin(revenue: float, gross_profit: float) -> float | None:
    if revenue == 0:
        return None
    return round(gross_profit / revenue * 100, 2)


def build_rows_for_ticker(ticker: str, cik: int, facts: dict[str, Any]) -> list[tuple]:
    revenues = _merged_quarterly_values(facts, REVENUE_TAGS)
    gross_profits = _merged_quarterly_values(facts, GROSS_PROFIT_TAGS)
    costs = _merged_quarterly_values(facts, COST_TAGS)

    if not revenues:
        logger.warning("No revenue data found for %s, skipping", ticker)
        return []

    rows = []
    quarters_with_gp = set(revenues) & set(gross_profits)
    quarters_with_cost_only = (set(revenues) & set(costs)) - quarters_with_gp

    for q in quarters_with_gp:
        rev = revenues[q]["entry"]["val"]
        gp = gross_profits[q]["entry"]["val"]
        rows.append(
            (
                ticker, str(cik), q, revenues[q]["entry"]["end"],
                rev, gp, compute_margin(rev, gp),
                revenues[q]["tag"], gross_profits[q]["tag"],
            )
        )

    for q in quarters_with_cost_only:
        rev = revenues[q]["entry"]["val"]
        cost = costs[q]["entry"]["val"]
        gp = rev - cost
        rows.append(
            (
                ticker, str(cik), q, revenues[q]["entry"]["end"],
                rev, gp, compute_margin(rev, gp),
                revenues[q]["tag"], costs[q]["tag"],
            )
        )

    if not rows:
        logger.warning("No gross-profit or cost data overlapped with revenue for %s, skipping", ticker)

    return rows


def load_rows(rows: list[tuple], db_path=DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executemany(
            """
            INSERT OR REPLACE INTO comp_margins_quarterly
            (ticker, cik, quarter, period_end, revenue, gross_profit, gross_margin_pct, revenue_tag, cost_tag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def run() -> None:
    tickers_json = fetch_tickers_json()
    for ticker in COMP_TICKERS:
        cik = resolve_cik(tickers_json, ticker)
        if cik is None:
            logger.warning("Could not resolve CIK for %s, skipping", ticker)
            continue
        logger.info("Fetching SEC company facts for %s (CIK %s)", ticker, cik)
        facts = fetch_companyfacts(cik)
        rows = build_rows_for_ticker(ticker, cik, facts)
        load_rows(rows)
        logger.info("Loaded %d quarter(s) for %s", len(rows), ticker)


if __name__ == "__main__":
    run()
