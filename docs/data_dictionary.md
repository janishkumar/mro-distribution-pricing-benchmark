# Data Dictionary

## `ppi_monthly`
| Column | Type | Description |
|---|---|---|
| series_id | TEXT | FRED series ID. `PCU423700423700` = headline monthly PPI for NAICS 4237 (Index May 2019=100, monthly, since 2009-02). `PCU4237004237001` = "primary wholesaler services" sub-component (the closest available narrower cut — FRED does not publish a hardware-vs-plumbing/heating split within NAICS 4237). `IPUGN4237T300000000` = nominal sectoral output, annual, $ millions, stored at `date = 'YYYY-01-01'`. |
| date | TEXT | Observation date (YYYY-MM-DD). Monthly for the two PPI series, annual (Jan 1) for sectoral output. |
| value | REAL | Index value (PPI series) or nominal dollar output in millions (sectoral output series), per FRED's native units. |

**Limitation:** NAICS 4237 is a national aggregate covering all hardware/plumbing/heating wholesalers, not HD Supply specifically — it's a proxy, not a direct measurement of HD Supply's own pricing. FRED's series catalog for this NAICS code does not offer a clean hardware-vs-plumbing/heating product split; the available sub-component divides "primary wholesaler services" from "all other goods," a different cut than product category.

## `census_wholesale_monthly`
| Column | Type | Description |
|---|---|---|
| naics | TEXT | NAICS code, always `4237` in this project. |
| date | TEXT | First of the survey month (YYYY-MM-01). |
| sales | REAL | Monthly wholesale sales, NAICS 4237, $ millions, not seasonally adjusted (`seasonally_adj=no`, matching the PPI series' NSA convention), from Census's Monthly Wholesale Trade Survey via the EITS API. |
| inventories | REAL | End-of-month inventories, NAICS 4237, $ millions, not seasonally adjusted, same source. |

**Limitation:** Census MWTS and FRED's PPI use different collection methodologies and survey samples; they may not reconcile precisely at the monthly level. Census's EITS API also publishes a pre-computed inventory/sales ratio (`data_type_code=IR`) and margin-of-error fields (`E_SM`, `E_IM`, `E_IR`) that this project does not currently store — the ratio is instead recomputed from `sales`/`inventories` in `src/analysis/decomposition.py` for transparency.

## `comp_margins_quarterly`
| Column | Type | Description |
|---|---|---|
| ticker | TEXT | Public MRO distributor ticker (FAST, GWW, WCC, MSM, CNM). |
| cik | TEXT | SEC Central Index Key, resolved live from SEC's ticker directory (`company_tickers.json`), not hardcoded. |
| quarter | TEXT | Calendar quarter derived from the reporting period's own end date (`YYYYQN`), not from SEC's self-reported `fy`/`fp` fields — those reflect the fiscal year of the *filing*, which drifts from the actual period for some companies. |
| period_end | TEXT | Period end date reported in the XBRL filing. |
| revenue | REAL | Quarterly revenue, USD, merged across multiple XBRL tags (see revenue_tag). |
| gross_profit | REAL | Quarterly gross profit, USD — either the company's own `GrossProfit` tag, or `revenue - cost` when only a cost tag overlaps that quarter. |
| gross_margin_pct | REAL | `gross_profit / revenue * 100`. |
| revenue_tag | TEXT | Which XBRL us-gaap tag supplied that quarter's revenue figure, for traceability. |
| cost_tag | TEXT | Which XBRL us-gaap tag supplied that quarter's gross-profit or cost figure, for traceability. |

**Limitation:** these five public comps sell a broader product mix than HD Supply's multifamily/hospitality-focused Facilities Maintenance business — their margins are directional context, not an exact stand-in for HD Supply's own margins.

**Two real data-quality issues found and handled, documented here rather than hidden:**
1. Companies change XBRL revenue tags over time (e.g. GWW's `Revenues` tag has essentially one usable quarter; its real multi-year history is under `RevenueFromContractWithCustomerExcludingAssessedTax` post-2018 and `SalesRevenueNet` pre-2018). `revenue_tag` is merged across all three candidate tags per quarter rather than stopping at the first one found, and records which tag actually supplied each row.
2. Some companies (e.g. WCC) only disclose quarterly figures inside a 10-K's "selected quarterly financial data" footnote (`form=10-K`, `fp=FY`), not as a standalone 10-Q filing. Quarter extraction filters on the reporting period's actual duration (~90 days) rather than the filing type, so this data isn't silently dropped. When the same quarter is reported in more than one filing (a restatement), the most recently filed value is kept.
