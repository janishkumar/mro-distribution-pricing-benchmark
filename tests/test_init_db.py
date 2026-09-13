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
