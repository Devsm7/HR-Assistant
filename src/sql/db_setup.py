"""
db_setup.py - One-time setup: loads HR CSV into a local SQLite database.

Run with:
    conda run -n ai_base python -m src.sql.db_setup
"""

from pathlib import Path
import sqlite3
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH     = PROJECT_ROOT / "dataset" / "hr_Employee_data_decoded.csv"
DB_PATH      = PROJECT_ROOT / "hr.db"
TABLE_NAME   = "employees"


def setup_db() -> None:
    print(f"Loading CSV from: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    # Drop the unnamed index column if present
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])

    print(f"Rows: {len(df)}  |  Columns: {len(df.columns)}")

    conn = sqlite3.connect(DB_PATH)
    df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
    conn.close()

    print(f"Database saved to: {DB_PATH}")
    print(f"Table '{TABLE_NAME}' created with {len(df)} rows.")


if __name__ == "__main__":
    setup_db()
