from src.etl.fetch_sec import (
    compute_margin,
    resolve_cik,
    _merged_quarterly_values,
    _quarter_key,
    _quarterly_values,
)


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


def test_quarter_key_from_end_date():
    assert _quarter_key("2024-03-31") == "2024Q1"
    assert _quarter_key("2024-12-31") == "2024Q4"


def test_quarterly_values_accepts_quarter_length_entries_regardless_of_form():
    # WCC-style case: quarterly figures disclosed inside a 10-K's "selected
    # quarterly data" footnote, tagged form=10-K/fp=FY, not form=10-Q.
    facts = {
        "facts": {
            "us-gaap": {
                "GrossProfit": {
                    "units": {
                        "USD": [
                            {
                                "start": "2019-01-01", "end": "2019-03-31",
                                "val": 100.0, "form": "10-K", "fp": "FY", "filed": "2021-03-01",
                            },
                            {
                                # A full-year entry (365 days) must be excluded.
                                "start": "2019-01-01", "end": "2019-12-31",
                                "val": 900.0, "form": "10-K", "fp": "FY", "filed": "2021-03-01",
                            },
                        ]
                    }
                }
            }
        }
    }

    result = _quarterly_values(facts, "GrossProfit")

    assert result == {
        "2019Q1": {
            "start": "2019-01-01", "end": "2019-03-31",
            "val": 100.0, "form": "10-K", "fp": "FY", "filed": "2021-03-01",
        }
    }


def test_quarterly_values_prefers_most_recently_filed_on_conflict():
    facts = {
        "facts": {
            "us-gaap": {
                "GrossProfit": {
                    "units": {
                        "USD": [
                            {
                                "start": "2019-01-01", "end": "2019-03-31",
                                "val": 100.0, "form": "10-K", "fp": "FY", "filed": "2020-01-01",
                            },
                            {
                                # Restated in a later filing -- should win.
                                "start": "2019-01-01", "end": "2019-03-31",
                                "val": 105.0, "form": "10-K", "fp": "FY", "filed": "2021-06-01",
                            },
                        ]
                    }
                }
            }
        }
    }

    result = _quarterly_values(facts, "GrossProfit")

    assert result["2019Q1"]["val"] == 105.0


def test_merged_quarterly_values_combines_tags_and_tracks_source_tag():
    facts = {
        "facts": {
            "us-gaap": {
                "TagA": {
                    "units": {
                        "USD": [
                            {"start": "2019-01-01", "end": "2019-03-31", "val": 100.0, "filed": "2019-05-01"},
                        ]
                    }
                },
                "TagB": {
                    "units": {
                        "USD": [
                            {"start": "2019-04-01", "end": "2019-06-30", "val": 200.0, "filed": "2019-08-01"},
                        ]
                    }
                },
            }
        }
    }

    merged = _merged_quarterly_values(facts, ["TagA", "TagB"])

    assert merged["2019Q1"]["tag"] == "TagA"
    assert merged["2019Q1"]["entry"]["val"] == 100.0
    assert merged["2019Q2"]["tag"] == "TagB"
    assert merged["2019Q2"]["entry"]["val"] == 200.0
