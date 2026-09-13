# MRO Distribution Pricing & Margin Benchmark (NAICS 4237) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible ETL + SQLite + Power BI pipeline that benchmarks HD Supply's core MRO wholesale category (NAICS 4237) using only free federal and SEC data, and produce a one-page executive memo with 2-3 data-backed pricing/margin recommendations.

**Architecture:** Three independent Python ETL scripts (FRED, Census, SEC EDGAR) land raw data into a single SQLite database via a shared schema. A pure-Python analysis module computes the price/volume decomposition and inventory-to-sales ratio from that database. Power BI connects directly to the SQLite file (via ODBC) for the dashboard layer. No fabricated data anywhere — every number traces to one of the four documented sources.

**Tech Stack:** Python 3.11+, `requests`, `pandas`, `python-dotenv`, `pytest`, SQLite (stdlib `sqlite3`), Power BI Desktop.

---

## Before you start

You need two things the plan can't get for you:

1. **A free FRED API key** — https://fred.stlouisfed.org/docs/api/api_key.html (instant, no approval wait).
2. **A free Census API key** — https://api.census.gov/data/key_signup.html (instant).

SEC EDGAR needs no key, but SEC's fair-use policy requires every request to carry a `User-Agent` header with a real contact — this plan uses `kjanish28@gmail.com`.

Put both keys in `.env` (Task 0 creates `.env.example` — copy it to `.env` and fill in the real values; `.env` is gitignored, never commit it).

## Design note: FRED series IDs are discovered, not guessed

The PRD names `PCU423700423700` for the headline monthly PPI series — that one is used directly. For the PPI *sub-components* and the *annual sectoral output* series, this plan does **not** hardcode a guessed FRED series ID, because a wrong ID silently returns either an error or (worse) a plausible-looking but wrong series. Instead, Task 1 includes a discovery step that calls FRED's own search API and prints candidate series for you to eyeball and confirm before they're wired into the fetch script. This is slower by five minutes and correct, instead of fast and possibly wrong.

---

### Task 0: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/__init__.py`
- Create: `src/config.py`
- Create: `README.md`

- [ ] **Step 1: Create `requirements.txt`**

```
requests==2.32.3
pandas==2.2.3
python-dotenv==1.0.1
pytest==8.3.3
```

- [ ] **Step 2: Create `.gitignore`**

```
.env
__pycache__/
*.pyc
.pytest_cache/
data/*.db
data/raw/
.DS_Store
```

- [ ] **Step 3: Create `.env.example`**

```
FRED_API_KEY=
CENSUS_API_KEY=
```

- [ ] **Step 4: Create `src/__init__.py`** (empty file, makes `src` a package)

```python
```

- [ ] **Step 5: Create `src/config.py`**

```python
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "mro_distribution_benchmark.db"

FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY", "")

SEC_USER_AGENT = "MRO Distribution Pricing Benchmark kjanish28@gmail.com"

FRED_BASE_URL = "https://api.stlouisfed.org/fred"
CENSUS_MWTS_URL = "https://api.census.gov/data/timeseries/eits/mwts"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:0>10}.json"

NAICS_CODE = "4237"
COMP_TICKERS = ["FAST", "GWW", "WCC", "MSM", "CNM"]

DATA_DIR.mkdir(exist_ok=True)
```

- [ ] **Step 6: Create `README.md`**

```markdown
# MRO Distribution Pricing & Margin Benchmark (NAICS 4237)

HD Supply's Facilities Maintenance business sells into NAICS 4237
(Hardware, and Plumbing and Heating Equipment and Supplies Merchant
Wholesalers). Since HD Supply is a private Home Depot subsidiary and no
longer files its own financials, this project benchmarks its pricing
environment using free public data:

- **FRED PPI, NAICS 4237** — monthly wholesale price index
- **FRED Sectoral Output, NAICS 4237** — annual nominal output, for price/volume decomposition
- **Census Monthly Wholesale Trade Survey, NAICS 4237** — monthly sales & inventories
- **SEC EDGAR XBRL (FAST, GWW, WCC, MSM, CNM)** — public MRO distributor margins as a proxy

No fabricated or synthetic data. See `docs/data_dictionary.md` for field-level
sourcing and known limitations, and `docs/superpowers/plans/2026-09-12-mro-distribution-pricing-benchmark.md`
for the full build plan.

## Setup

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in `FRED_API_KEY` and `CENSUS_API_KEY`
   (both free, instant signup — see links in the plan doc).
3. `python -m src.db.init_db`
4. `python -m src.etl.fetch_fred`
5. `python -m src.etl.fetch_census`
6. `python -m src.etl.fetch_sec`
7. Open `data/mro_distribution_benchmark.db` from Power BI Desktop (SQLite ODBC connector).
```

- [ ] **Step 7: Commit**

```bash
git add requirements.txt .gitignore .env.example src/__init__.py src/config.py README.md
git commit -m "chore: scaffold project structure and config"
```

---

### Task 1: SQLite schema and database init

**Files:**
- Create: `src/db/__init__.py`
- Create: `src/db/schema.sql`
- Create: `src/db/init_db.py`
- Test: `tests/test_init_db.py`

- [ ] **Step 1: Create `src/db/__init__.py`** (empty)

```python
```

- [ ] **Step 2: Create `src/db/schema.sql`**

```sql
-- Holds both the monthly PPI series and the annual sectoral-output series
-- from FRED. They share the same (series_id, date, value) shape; annual
-- rows are keyed at date = '<year>-01-01'. Distinguish them by series_id.
CREATE TABLE IF NOT EXISTS ppi_monthly (
    series_id TEXT NOT NULL,
    date TEXT NOT NULL,
    value REAL,
    PRIMARY KEY (series_id, date)
);

CREATE TABLE IF NOT EXISTS census_wholesale_monthly (
    naics TEXT NOT NULL,
    date TEXT NOT NULL,
    sales REAL,
    inventories REAL,
    PRIMARY KEY (naics, date)
);

CREATE TABLE IF NOT EXISTS comp_margins_quarterly (
    ticker TEXT NOT NULL,
    cik TEXT NOT NULL,
    quarter TEXT NOT NULL,
    period_end TEXT NOT NULL,
    revenue REAL,
    gross_profit REAL,
    gross_margin_pct REAL,
    revenue_tag TEXT,
    cost_tag TEXT,
    PRIMARY KEY (ticker, quarter)
);
```

- [ ] **Step 3: Write the failing test**

```python
# tests/test_init_db.py
import sqlite3

from src.db.init_db import init_db


def test_init_db_creates_all_tables(tmp_path):
    db_path = tmp_path / "test.db"

    init_db(db_path)

    conn = sqlite3.connect(db_path)
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()

    assert {"ppi_monthly", "census_wholesale_monthly", "comp_margins_quarterly"} <= tables
```

- [ ] **Step 4: Run test to verify it fails**

Run: `pytest tests/test_init_db.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.db.init_db'`

- [ ] **Step 5: Create `src/db/init_db.py`**

```python
import sqlite3
from pathlib import Path

from src.config import DB_PATH


def init_db(db_path: Path = DB_PATH) -> None:
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    schema_sql = schema_path.read_text()

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Initialized database at {DB_PATH}")
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_init_db.py -v`
Expected: PASS

- [ ] **Step 7: Run it for real to create the working database**

Run: `python -m src.db.init_db`
Expected: `Initialized database at .../data/mro_distribution_benchmark.db`

- [ ] **Step 8: Commit**

```bash
git add src/db/__init__.py src/db/schema.sql src/db/init_db.py tests/test_init_db.py
git commit -m "feat: add SQLite schema and db init"
```

---

### Task 2: FRED series discovery

Run this once, by hand, before writing the real fetch script — its job is to find the correct FRED series IDs for the PPI sub-components and the annual sectoral output series, so Task 3 doesn't hardcode a guess.

**Files:**
- Create: `scripts/discover_fred_series.py`

- [ ] **Step 1: Create `scripts/discover_fred_series.py`**

```python
import requests

from src.config import FRED_API_KEY, FRED_BASE_URL


def search_series(search_text: str) -> None:
    resp = requests.get(
        f"{FRED_BASE_URL}/series/search",
        params={
            "search_text": search_text,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "limit": 20,
        },
        timeout=30,
    )
    resp.raise_for_status()
    for s in resp.json().get("seriess", []):
        print(f"{s['id']:>20}  {s['title']}  (freq={s['frequency_short']}, units={s['units_short']})")


if __name__ == "__main__":
    print("--- PPI sub-components, NAICS 4237 ---")
    search_series("PPI industry 4237")
    print()
    print("--- Sectoral output, NAICS 4237 ---")
    search_series("sectoral output 4237")
```

- [ ] **Step 2: Run it and record the results**

Run: `python scripts/discover_fred_series.py`

Read the printed list. Confirm `PCU423700423700` appears under the first search (it should — it's the series named directly in the PRD). Pick the annual sectoral-output series ID from the second search's output — look for one with `freq=A` (annual) and units in dollars. Write both the confirmed headline ID and the chosen sectoral-output ID down; Task 3 uses them directly.

- [ ] **Step 3: Commit**

```bash
git add scripts/discover_fred_series.py
git commit -m "chore: add FRED series discovery script"
```

---

### Task 3: FRED ETL (PPI + sectoral output)

**Files:**
- Create: `src/etl/__init__.py`
- Create: `src/etl/fetch_fred.py`
- Test: `tests/test_fetch_fred.py`

- [ ] **Step 1: Write the failing test for the pure parsing function**

```python
# tests/test_fetch_fred.py
from src.etl.fetch_fred import parse_observations


def test_parse_observations_converts_and_drops_missing():
    raw = {
        "observations": [
            {"date": "2024-01-01", "value": "123.4"},
            {"date": "2024-02-01", "value": "."},  # FRED's missing-value marker
            {"date": "2024-03-01", "value": "125.0"},
        ]
    }

    rows = parse_observations(raw, series_id="PCU423700423700")

    assert rows == [
        ("PCU423700423700", "2024-01-01", 123.4),
        ("PCU423700423700", "2024-03-01", 125.0),
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fetch_fred.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.etl.fetch_fred'`

- [ ] **Step 3: Create `src/etl/__init__.py`** (empty)

```python
```

- [ ] **Step 4: Create `src/etl/fetch_fred.py`**

Fill in `SECTORAL_OUTPUT_SERIES_ID` with the ID you recorded from Task 2, Step 2, before running this for real.

```python
import logging
import sqlite3
from typing import Any

import requests

from src.config import DB_PATH, FRED_API_KEY, FRED_BASE_URL

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

HEADLINE_PPI_SERIES_ID = "PCU423700423700"
# Fill this in from Task 2's discovery output before running for real.
SECTORAL_OUTPUT_SERIES_ID = "REPLACE_ME"

SERIES_TO_FETCH = [HEADLINE_PPI_SERIES_ID, SECTORAL_OUTPUT_SERIES_ID]


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
    if SECTORAL_OUTPUT_SERIES_ID == "REPLACE_ME":
        raise RuntimeError(
            "Set SECTORAL_OUTPUT_SERIES_ID from scripts/discover_fred_series.py output first."
        )
    for series_id in SERIES_TO_FETCH:
        logger.info("Fetching FRED series %s", series_id)
        raw = fetch_series_observations(series_id)
        rows = parse_observations(raw, series_id)
        load_rows(rows)
        logger.info("Loaded %d observations for %s", len(rows), series_id)


if __name__ == "__main__":
    run()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_fetch_fred.py -v`
Expected: PASS

- [ ] **Step 6: Set `SECTORAL_OUTPUT_SERIES_ID`, then run for real**

Edit the constant with the ID from Task 2, then:

Run: `python -m src.etl.fetch_fred`
Expected: two `Loaded N observations for <series_id>` log lines, N > 0

- [ ] **Step 7: Commit**

```bash
git add src/etl/__init__.py src/etl/fetch_fred.py tests/test_fetch_fred.py
git commit -m "feat: add FRED PPI and sectoral output ETL"
```

---

### Task 4: Census MWTS ETL

The Monthly Wholesale Trade Survey is published through Census's Economic Indicators Time Series API. Confirm the exact variable names before writing the loader, since Census's EITS parameter names vary by dataset.

**Files:**
- Create: `src/etl/fetch_census.py`
- Test: `tests/test_fetch_census.py`

- [ ] **Step 1: Confirm the API's variable names**

Run: `curl -s "https://api.census.gov/data/timeseries/eits/mwts/variables.json" | python -m json.tool | head -60`

Look for the variable names for category code, data type code (sales vs. inventories), and seasonal adjustment. Adjust `params` in Step 4 below to match exactly what this prints — the census API rejects requests with unrecognized parameter names, so this step is not optional.

- [ ] **Step 2: Write the failing test for the pure parsing function**

```python
# tests/test_fetch_census.py
from src.etl.fetch_census import parse_mwts_response


def test_parse_mwts_response_splits_sales_and_inventories():
    raw = [
        ["cell_value", "time", "data_type_code", "category_code"],
        ["12345", "2024-01", "SM", "4237"],
        ["67890", "2024-01", "IM", "4237"],
    ]

    rows = parse_mwts_response(raw)

    assert rows == {("4237", "2024-01-01"): {"sales": 12345.0, "inventories": 67890.0}}
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_fetch_census.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.etl.fetch_census'`

- [ ] **Step 4: Create `src/etl/fetch_census.py`**

```python
import logging
import sqlite3
from collections import defaultdict
from typing import Any

import requests

from src.config import CENSUS_API_KEY, CENSUS_MWTS_URL, DB_PATH, NAICS_CODE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def fetch_mwts_raw() -> list[list[str]]:
    resp = requests.get(
        CENSUS_MWTS_URL,
        params={
            "get": "cell_value,data_type_code",
            "category_code": NAICS_CODE,
            "time": "from 2019",
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
        time_str = row[idx["time"]]  # "2024-01"
        date = f"{time_str}-01"
        category = row[idx["category_code"]]
        data_type = row[idx["data_type_code"]]
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_fetch_census.py -v`
Expected: PASS

- [ ] **Step 6: Run for real, fixing param names if the API rejects the request**

Run: `python -m src.etl.fetch_census`
Expected: `Loaded N month(s) of Census wholesale data`, N > 0. If you get a 400, re-check Step 1's variable names and adjust `fetch_mwts_raw`'s `params` dict to match.

- [ ] **Step 7: Commit**

```bash
git add src/etl/fetch_census.py tests/test_fetch_census.py
git commit -m "feat: add Census MWTS ETL"
```

---

### Task 5: SEC EDGAR comp margins ETL

Public companies use different XBRL tags for cost of goods sold (some tag `GrossProfit` directly, others only tag `Revenues` and `CostOfGoodsAndServicesSold`). This script tries a fallback chain per company and records which tag it used, so the limitation is visible in the data itself rather than hidden.

**Files:**
- Create: `src/etl/fetch_sec.py`
- Test: `tests/test_fetch_sec.py`

- [ ] **Step 1: Write the failing test for the pure margin-calc function**

```python
# tests/test_fetch_sec.py
from src.etl.fetch_sec import compute_margin, resolve_cik


def test_compute_margin_basic():
    assert compute_margin(revenue=1000.0, gross_profit=290.0) == 29.0


def test_compute_margin_zero_revenue_returns_none():
    assert compute_margin(revenue=0.0, gross_profit=100.0) is None


def test_resolve_cik_matches_ticker_case_insensitively():
    tickers_json = {
        "0": {"cik_str": 815556, "ticker": "FAST", "title": "FASTENAL CO"},
        "1": {"cik_str": 277135, "ticker": "GWW", "title": "GRAINGER W W INC"},
    }

    assert resolve_cik(tickers_json, "fast") == 815556
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fetch_sec.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.etl.fetch_sec'`

- [ ] **Step 3: Create `src/etl/fetch_sec.py`**

```python
import logging
import sqlite3
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

REVENUE_TAGS = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"]
GROSS_PROFIT_TAGS = ["GrossProfit"]
COST_TAGS = ["CostOfGoodsAndServicesSold", "CostOfRevenue"]


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


def _find_first_available_tag(facts: dict[str, Any], candidate_tags: list[str]) -> str | None:
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    for tag in candidate_tags:
        if tag in us_gaap:
            return tag
    return None


def _quarterly_values(facts: dict[str, Any], tag: str) -> dict[str, dict[str, Any]]:
    units = facts["facts"]["us-gaap"][tag]["units"]
    usd_entries = units.get("USD", [])
    by_quarter = {}
    for entry in usd_entries:
        if entry.get("form", "").startswith("10-Q") and entry.get("fp") in ("Q1", "Q2", "Q3", "Q4"):
            key = f"{entry['fy']}{entry['fp']}"
            by_quarter[key] = entry
    return by_quarter


def compute_margin(revenue: float, gross_profit: float) -> float | None:
    if revenue == 0:
        return None
    return round(gross_profit / revenue * 100, 2)


def build_rows_for_ticker(ticker: str, cik: int, facts: dict[str, Any]) -> list[tuple]:
    revenue_tag = _find_first_available_tag(facts, REVENUE_TAGS)
    gross_profit_tag = _find_first_available_tag(facts, GROSS_PROFIT_TAGS)
    cost_tag = _find_first_available_tag(facts, COST_TAGS)

    if revenue_tag is None:
        logger.warning("No revenue tag found for %s, skipping", ticker)
        return []

    revenues = _quarterly_values(facts, revenue_tag)
    rows = []

    if gross_profit_tag is not None:
        gross_profits = _quarterly_values(facts, gross_profit_tag)
        quarters = set(revenues) & set(gross_profits)
        for q in quarters:
            rev = revenues[q]["val"]
            gp = gross_profits[q]["val"]
            rows.append(
                (
                    ticker, str(cik), q, revenues[q]["end"],
                    rev, gp, compute_margin(rev, gp), revenue_tag, gross_profit_tag,
                )
            )
    elif cost_tag is not None:
        costs = _quarterly_values(facts, cost_tag)
        quarters = set(revenues) & set(costs)
        for q in quarters:
            rev = revenues[q]["val"]
            cost = costs[q]["val"]
            gp = rev - cost
            rows.append(
                (
                    ticker, str(cik), q, revenues[q]["end"],
                    rev, gp, compute_margin(rev, gp), revenue_tag, cost_tag,
                )
            )
    else:
        logger.warning("No gross-profit or cost tag found for %s, skipping", ticker)

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_fetch_sec.py -v`
Expected: PASS

- [ ] **Step 5: Run for real**

Run: `python -m src.etl.fetch_sec`
Expected: one `Loaded N quarter(s) for <ticker>` line per ticker, N > 0 for each. If a ticker is skipped, note it — that's a real limitation to document, not a bug to silently patch over.

- [ ] **Step 6: Commit**

```bash
git add src/etl/fetch_sec.py tests/test_fetch_sec.py
git commit -m "feat: add SEC EDGAR comp margins ETL"
```

---

### Task 6: Price/volume decomposition + inventory-to-sales analysis

Pure-math module, fully unit-testable without touching the database or any API.

**Files:**
- Create: `src/analysis/__init__.py`
- Create: `src/analysis/decomposition.py`
- Test: `tests/test_decomposition.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_decomposition.py
from src.analysis.decomposition import decompose_growth, inventory_to_sales_ratio


def test_decompose_growth_all_price_no_volume():
    # Nominal doubled, price doubled -> all price, zero real growth.
    result = decompose_growth(
        nominal_start=100.0, nominal_end=200.0,
        price_index_start=100.0, price_index_end=200.0,
    )
    assert result["nominal_growth_pct"] == 100.0
    assert result["price_growth_pct"] == 100.0
    assert abs(result["volume_growth_pct"]) < 1e-9


def test_decompose_growth_mixed():
    # Nominal +21%, price +10% -> real (volume) growth = 1.21/1.10 - 1 = 10%.
    result = decompose_growth(
        nominal_start=100.0, nominal_end=121.0,
        price_index_start=100.0, price_index_end=110.0,
    )
    assert result["nominal_growth_pct"] == 21.0
    assert result["price_growth_pct"] == 10.0
    assert abs(result["volume_growth_pct"] - 10.0) < 1e-9


def test_inventory_to_sales_ratio():
    assert inventory_to_sales_ratio(inventories=300.0, sales=150.0) == 2.0


def test_inventory_to_sales_ratio_zero_sales_returns_none():
    assert inventory_to_sales_ratio(inventories=300.0, sales=0.0) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_decomposition.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.analysis.decomposition'`

- [ ] **Step 3: Create `src/analysis/__init__.py`** (empty)

```python
```

- [ ] **Step 4: Create `src/analysis/decomposition.py`**

```python
def decompose_growth(
    nominal_start: float,
    nominal_end: float,
    price_index_start: float,
    price_index_end: float,
) -> dict[str, float]:
    """Split nominal growth into price-driven and volume-driven components.

    Deflates the ending nominal value to starting-period dollars using the
    price index ratio, then compares that real value to the nominal start.
    """
    nominal_growth = nominal_end / nominal_start - 1
    price_growth = price_index_end / price_index_start - 1

    real_end = nominal_end / (price_index_end / price_index_start)
    volume_growth = real_end / nominal_start - 1

    return {
        "nominal_growth_pct": round(nominal_growth * 100, 4),
        "price_growth_pct": round(price_growth * 100, 4),
        "volume_growth_pct": round(volume_growth * 100, 4),
    }


def inventory_to_sales_ratio(inventories: float, sales: float) -> float | None:
    if sales == 0:
        return None
    return round(inventories / sales, 4)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_decomposition.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/analysis/__init__.py src/analysis/decomposition.py tests/test_decomposition.py
git commit -m "feat: add price/volume decomposition and inventory-to-sales analysis"
```

---

### Task 7: Wire decomposition to the real database and print a findings summary

**Files:**
- Create: `src/analysis/report.py`
- Test: `tests/test_report.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_report.py
import sqlite3

from src.analysis.report import load_annual_price_volume, load_latest_inventory_to_sales
from src.db.init_db import init_db


def test_load_annual_price_volume_uses_january_average_price(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)

    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT INTO ppi_monthly (series_id, date, value) VALUES (?, ?, ?)",
        [
            ("PCU423700423700", "2019-01-01", 100.0),
            ("PCU423700423700", "2023-01-01", 115.0),
            ("SECTORAL_OUTPUT_ID", "2019-01-01", 5000.0),
            ("SECTORAL_OUTPUT_ID", "2023-01-01", 6200.0),
        ],
    )
    conn.commit()
    conn.close()

    result = load_annual_price_volume(
        db_path,
        ppi_series_id="PCU423700423700",
        output_series_id="SECTORAL_OUTPUT_ID",
        start_year=2019,
        end_year=2023,
    )

    assert result["nominal_growth_pct"] == 24.0
    assert result["price_growth_pct"] == 15.0


def test_load_latest_inventory_to_sales(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO census_wholesale_monthly (naics, date, sales, inventories) VALUES (?, ?, ?, ?)",
        ("4237", "2024-06-01", 1000.0, 2500.0),
    )
    conn.commit()
    conn.close()

    ratio = load_latest_inventory_to_sales(db_path, naics="4237")

    assert ratio == 2.5
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_report.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.analysis.report'`

- [ ] **Step 3: Create `src/analysis/report.py`**

```python
import sqlite3

from src.analysis.decomposition import decompose_growth, inventory_to_sales_ratio
from src.config import DB_PATH


def load_annual_price_volume(
    db_path,
    ppi_series_id: str,
    output_series_id: str,
    start_year: int,
    end_year: int,
) -> dict[str, float]:
    conn = sqlite3.connect(db_path)
    try:
        price_start = conn.execute(
            "SELECT value FROM ppi_monthly WHERE series_id = ? AND date = ?",
            (ppi_series_id, f"{start_year}-01-01"),
        ).fetchone()[0]
        price_end = conn.execute(
            "SELECT value FROM ppi_monthly WHERE series_id = ? AND date = ?",
            (ppi_series_id, f"{end_year}-01-01"),
        ).fetchone()[0]
        output_start = conn.execute(
            "SELECT value FROM ppi_monthly WHERE series_id = ? AND date = ?",
            (output_series_id, f"{start_year}-01-01"),
        ).fetchone()[0]
        output_end = conn.execute(
            "SELECT value FROM ppi_monthly WHERE series_id = ? AND date = ?",
            (output_series_id, f"{end_year}-01-01"),
        ).fetchone()[0]
    finally:
        conn.close()

    return decompose_growth(
        nominal_start=output_start,
        nominal_end=output_end,
        price_index_start=price_start,
        price_index_end=price_end,
    )


def load_latest_inventory_to_sales(db_path, naics: str) -> float | None:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT sales, inventories FROM census_wholesale_monthly "
            "WHERE naics = ? ORDER BY date DESC LIMIT 1",
            (naics,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    sales, inventories = row
    return inventory_to_sales_ratio(inventories, sales)


if __name__ == "__main__":
    from src.etl.fetch_fred import HEADLINE_PPI_SERIES_ID, SECTORAL_OUTPUT_SERIES_ID

    result = load_annual_price_volume(
        DB_PATH,
        ppi_series_id=HEADLINE_PPI_SERIES_ID,
        output_series_id=SECTORAL_OUTPUT_SERIES_ID,
        start_year=2019,
        end_year=2023,
    )
    print("Price/volume decomposition, 2019-2023:", result)

    ratio = load_latest_inventory_to_sales(DB_PATH, naics="4237")
    print("Latest inventory-to-sales ratio:", ratio)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_report.py -v`
Expected: PASS

- [ ] **Step 5: Run against the real database**

Run: `python -m src.analysis.report`
Expected: printed decomposition dict and a numeric inventory-to-sales ratio (adjust `start_year`/`end_year` in the `__main__` block if 2019 or 2023 data isn't present yet).

- [ ] **Step 6: Commit**

```bash
git add src/analysis/report.py tests/test_report.py
git commit -m "feat: wire price/volume decomposition to live database"
```

---

### Task 8: Data dictionary

**Files:**
- Create: `docs/data_dictionary.md`

- [ ] **Step 1: Create `docs/data_dictionary.md`**

```markdown
# Data Dictionary

## `ppi_monthly`
| Column | Type | Description |
|---|---|---|
| series_id | TEXT | FRED series ID. `PCU423700423700` = headline monthly PPI for NAICS 4237. The annual sectoral-output series (ID confirmed via `scripts/discover_fred_series.py`) is also stored here, keyed at `date = 'YYYY-01-01'`. |
| date | TEXT | Observation date (YYYY-MM-DD). Monthly for PPI, annual (Jan 1) for sectoral output. |
| value | REAL | Index value (PPI) or nominal dollar output (sectoral output), per FRED's native units. |

**Limitation:** NAICS 4237 is a national aggregate covering all hardware/plumbing/heating wholesalers, not HD Supply specifically — it's a proxy, not a direct measurement of HD Supply's own pricing.

## `census_wholesale_monthly`
| Column | Type | Description |
|---|---|---|
| naics | TEXT | NAICS code, always `4237` in this project. |
| date | TEXT | First of the survey month (YYYY-MM-01). |
| sales | REAL | Monthly wholesale sales, NAICS 4237, from Census MWTS. |
| inventories | REAL | End-of-month inventories, NAICS 4237, from Census MWTS. |

**Limitation:** Census MWTS and FRED's PPI use different collection methodologies and survey samples; they may not reconcile precisely at the monthly level.

## `comp_margins_quarterly`
| Column | Type | Description |
|---|---|---|
| ticker | TEXT | Public MRO distributor ticker (FAST, GWW, WCC, MSM, CNM). |
| cik | TEXT | SEC Central Index Key, resolved from SEC's ticker directory. |
| quarter | TEXT | Fiscal year + fiscal period concatenated, e.g. `2024Q1`, as reported by the company (fiscal quarters don't always align to calendar quarters). |
| period_end | TEXT | Period end date reported in the XBRL filing. |
| revenue | REAL | Quarterly revenue, USD. |
| gross_profit | REAL | Quarterly gross profit, USD — either the company's own `GrossProfit` tag, or `revenue - cost` when only a cost tag is available. |
| gross_margin_pct | REAL | `gross_profit / revenue * 100`. |
| revenue_tag | TEXT | Which XBRL us-gaap tag was actually used for revenue, for traceability. |
| cost_tag | TEXT | Which XBRL us-gaap tag was used for gross profit or cost, for traceability. |

**Limitation:** these five public comps sell a broader product mix than HD Supply's multifamily/hospitality-focused Facilities Maintenance business — their margins are directional context, not an exact stand-in for HD Supply's own margins. Different companies also use different XBRL tags for cost of goods sold (see `revenue_tag`/`cost_tag` columns), so cross-company margin comparisons carry some tagging-convention noise.
```

- [ ] **Step 2: Commit**

```bash
git add docs/data_dictionary.md
git commit -m "docs: add data dictionary with sourcing and limitations"
```

---

### Task 9: Power BI dashboard (manual — no code)

Not scriptable or testable the way the Python tasks are; this is a checklist to follow by hand in Power BI Desktop.

- [ ] **Step 1: Get Data → ODBC → point at `data/mro_distribution_benchmark.db`** (requires a SQLite ODBC driver installed — e.g. the one from http://www.ch-werner.de/sqliteodbc/ on Windows, or `brew install sqliteodbc` on Mac, then a matching System DSN).
- [ ] **Step 2: Load all three tables** (`ppi_monthly`, `census_wholesale_monthly`, `comp_margins_quarterly`).
- [ ] **Step 3: Build a line chart** — PPI value over time, filtered to `series_id = 'PCU423700423700'`, x-axis = date.
- [ ] **Step 4: Build a price/volume decomposition visual** — two bars (or a waterfall) per year showing `price_growth_pct` vs `volume_growth_pct` from Task 7's output (paste the computed yearly figures into a small manual table, since decomposition is a derived calculation, not a raw table Power BI can aggregate on its own).
- [ ] **Step 5: Build an inventory-to-sales ratio line chart** — computed measure `inventories / sales`, x-axis = date, from `census_wholesale_monthly`.
- [ ] **Step 6: Build a peer margin panel** — line or bar chart of `gross_margin_pct` by `ticker` over `quarter`, from `comp_margins_quarterly`.
- [ ] **Step 7: Add a text box citing all four sources by name** (FRED PPI, FRED Sectoral Output, Census MWTS, SEC EDGAR) with the as-of date of the last pull.
- [ ] **Step 8: Save as `dashboard/mro_distribution_benchmark.pbix`** and commit it.

```bash
git add dashboard/mro_distribution_benchmark.pbix
git commit -m "feat: add Power BI dashboard"
```

---

### Task 10: Executive memo

**Files:**
- Create: `memo/executive_memo.md`

- [ ] **Step 1: Create `memo/executive_memo.md`** using the real numbers Task 7 printed (replace every `[X]` placeholder with the actual computed value before this is considered done — a memo with placeholders left in is not finished)

```markdown
# MRO Distribution Pricing & Margin Benchmark — Executive Summary

**Category:** NAICS 4237 (Hardware, and Plumbing and Heating Equipment and Supplies Merchant Wholesalers)
**Period:** 2019–[latest year with data]
**Sources:** FRED PPI & Sectoral Output (NAICS 4237), Census Monthly Wholesale Trade Survey (NAICS 4237), SEC EDGAR XBRL (FAST, GWW, WCC, MSM, CNM)

## Findings

1. Category-wide wholesale prices (PPI, NAICS 4237) rose [X]% from 2019 to [latest year], against [X]% nominal output growth — implying [X]% of category growth was price-driven and [X]% was real volume growth.
2. The latest inventory-to-sales ratio for NAICS 4237 is [X], [above/below/in line with] [comparison point, e.g. the 2019 baseline] — [one sentence on what that signals about distributor demand/oversupply].
3. Public MRO distributor peers (FAST, GWW, WCC, MSM, CNM) show gross margins ranging [X]%–[X]% over the period, [trending up/down/flat] against the category's price trend — [one sentence on whether margin expansion tracked or lagged the pricing environment].

## Recommendations

1. [Specific, data-backed recommendation tied to finding 1 — e.g. "review pricing in the plumbing/heating subcategory specifically if its input inflation is outpacing the category average and outpacing peer margin realization."]
2. [Specific recommendation tied to finding 2 or 3.]
3. [Optional third recommendation.]

## Known Limitations

- NAICS 4237 is a national aggregate, not HD Supply-specific — a proxy, not a direct measurement.
- Public comps sell a broader product mix than HD Supply's multifamily/hospitality focus — their margins are directional, not exact.
- PPI and Census MWTS use different collection methodologies and may not perfectly reconcile month to month.
```

- [ ] **Step 2: Commit**

```bash
git add memo/executive_memo.md
git commit -m "docs: add executive memo with findings and recommendations"
```

---

### Task 11: Final README pass and push to GitHub

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a "Findings" section to `README.md`** linking to `memo/executive_memo.md` and `dashboard/mro_distribution_benchmark.pbix`, so a hiring manager can find the output without running any code.

- [ ] **Step 2: Create the GitHub repo and push** (ask before running — this is a repo-creation + push action)

```bash
gh repo create mro-distribution-pricing-benchmark --public --source=. --remote=origin
git push -u origin main
```

- [ ] **Step 3: Commit the README update before or as part of the push**

```bash
git add README.md
git commit -m "docs: link findings in README"
```

---

## Self-review notes

- **Spec coverage:** all four PRD data sources (FRED PPI, FRED sectoral output, Census MWTS, SEC EDGAR comps) have a dedicated ETL task (3, 4, 5); the three-table SQLite schema matches the PRD's "Data model" section exactly (Task 1); price/volume decomposition and inventory-to-sales are both implemented and tested (Task 6-7); Power BI dashboard covers all four PRD-specified visuals (Task 9); executive memo and README/GitHub delivery are covered (Task 10-11); known limitations are documented in the data dictionary and the memo itself, as the PRD explicitly requires.
- **Stretch goal (SEC full-text MD&A pull) is intentionally excluded from this plan** — the PRD marks it "only if time allows"; add it as a follow-on task after Task 11 if there's time left.
- **Placeholder scan:** the only bracketed placeholders left (`[X]`, `REPLACE_ME`) are in Task 10's memo template and Task 3's series-ID constant — both are flagged inline as required fill-ins before the task is done, not vague hand-waving.
