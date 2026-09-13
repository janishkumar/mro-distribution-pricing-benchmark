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
