# MRO Distribution Pricing & Margin Benchmark (NAICS 4237)

HD Supply's Facilities Maintenance business sells into NAICS 4237
(Hardware, and Plumbing and Heating Equipment and Supplies Merchant
Wholesalers). Since HD Supply is a private Home Depot subsidiary and no
longer files its own financials, this project benchmarks the pricing
environment of its category using free public data — HD Supply is the
motivating example, not a data source:

- **FRED PPI, NAICS 4237** — monthly wholesale price index
- **FRED Sectoral Output, NAICS 4237** — annual nominal output, for price/volume decomposition
- **Census Monthly Wholesale Trade Survey, NAICS 4237** — monthly sales & inventories
- **SEC EDGAR XBRL (FAST, GWW, WCC, MSM, CNM)** — public MRO distributor margins as a proxy

No fabricated or synthetic data, and no HD Supply data of any kind — everything
here is public-industry and public-company data. See `docs/data_dictionary.md`
for field-level sourcing and known limitations, and
`docs/superpowers/plans/2026-09-12-mro-distribution-pricing-benchmark.md` for the
full build plan.

## Setup

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in `FRED_API_KEY` and `CENSUS_API_KEY`
   (both free, instant signup — see links in the plan doc).
3. `python -m src.db.init_db`
4. `python -m src.etl.fetch_fred`
5. `python -m src.etl.fetch_census`
6. `python -m src.etl.fetch_sec`
7. Open `data/mro_distribution_benchmark.db` from Power BI Desktop (SQLite ODBC connector).

## Findings

See [`memo/executive_memo.md`](memo/executive_memo.md) for the full write-up. Headline numbers from the live pipeline:

- Category nominal output grew 44.7% from 2019–2025; only 15.8 points of that was real volume growth, the rest (25.0 points) was price.
- Public MRO distributor peer margins did not track that price inflation — the two highest-margin peers (Fastenal, MSC Industrial) actually compressed over the same period.
- Current inventory-to-sales ratio (1.87) is near its 2019–2026 median, well off the 2023 peak — no category-wide oversupply signal right now.

Power BI dashboard: built and published as "MRO Distribution Pricing Benchmark Dashboard" (3 visuals — PPI trend, price/volume decomposition, inventory-to-sales ratio — backed by the `mro_distribution_pricing_benchmark` semantic model).
