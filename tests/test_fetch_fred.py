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
