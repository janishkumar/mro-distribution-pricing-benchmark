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
        end_year=2025,
    )
    print("Price/volume decomposition, 2019-2025:", result)

    ratio = load_latest_inventory_to_sales(DB_PATH, naics="4237")
    print("Latest inventory-to-sales ratio:", ratio)
