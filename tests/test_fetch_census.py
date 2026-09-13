from src.etl.fetch_census import parse_mwts_response


def test_parse_mwts_response_splits_sales_and_inventories():
    raw = [
        ["cell_value", "time", "data_type_code", "category_code"],
        ["12345", "2024-01", "SM", "4237"],
        ["67890", "2024-01", "IM", "4237"],
        ["2.41", "2024-01", "IR", "4237"],
        ["5.0", "2024-01", "E_SM", "4237"],
    ]

    rows = parse_mwts_response(raw)

    assert rows == {("4237", "2024-01-01"): {"sales": 12345.0, "inventories": 67890.0}}
