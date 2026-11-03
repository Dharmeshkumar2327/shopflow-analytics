"""
EL step: land the raw CSV extracts into DuckDB's `raw` schema exactly as received.

Every column is loaded as VARCHAR on purpose - typing, cleaning and de-duplication
are the transformation layer's job (dbt staging models), not the loader's.

Usage:
    python scripts/load_raw.py                       # -> data/shopflow.duckdb
    DUCKDB_PATH=/tmp/x.duckdb python scripts/load_raw.py
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = Path(os.environ.get("DUCKDB_PATH", ROOT / "data" / "shopflow.duckdb"))


def main() -> None:
    files = sorted(RAW_DIR.glob("*.csv"))
    if not files:
        raise SystemExit(f"No CSVs in {RAW_DIR}. Run `python scripts/generate_data.py` first.")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(DB_PATH)) as con:
        con.execute("create schema if not exists raw")
        for csv_file in files:
            table = csv_file.stem
            path = csv_file.as_posix().replace("'", "''")
            con.execute(
                f"create or replace table raw.{table} as "
                f"select * from read_csv('{path}', header = true, all_varchar = true)"
            )
            rows = con.execute(f"select count(*) from raw.{table}").fetchone()[0]
            print(f"  raw.{table:<16} {rows:>8,} rows")
    print(f"Loaded {len(files)} tables into {DB_PATH}")


if __name__ == "__main__":
    main()
