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
