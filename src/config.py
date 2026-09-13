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
