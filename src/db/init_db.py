import sqlite3
from pathlib import Path

from src.config import DB_PATH


def init_db(db_path: Path = DB_PATH) -> None:
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    schema_sql = schema_path.read_text()

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Initialized database at {DB_PATH}")
