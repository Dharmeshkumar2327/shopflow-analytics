"""
One-command, cross-platform pipeline (works on Windows, macOS and Linux - no `make` needed).

    python pipeline.py            # generate -> load -> dbt build -> docs
    python pipeline.py --skip-generate
    python pipeline.py --dashboard   # ...and then open the Streamlit dashboard
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRANSFORM = ROOT / "transform"
DB_PATH = ROOT / "data" / "shopflow.duckdb"


def run(cmd: list[str], cwd: Path = ROOT) -> None:
    print(f"\n>>> {' '.join(cmd)}")
    env = {**os.environ, "DUCKDB_PATH": str(DB_PATH)}
    result = subprocess.run(cmd, cwd=cwd, env=env)
    if result.returncode != 0:
        sys.exit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-generate", action="store_true", help="reuse existing data/raw CSVs")
    parser.add_argument("--customers", type=int, default=10000)
    parser.add_argument("--dashboard", action="store_true", help="launch the dashboard at the end")
    args = parser.parse_args()

    py = sys.executable
    if not args.skip_generate:
        run([py, "scripts/generate_data.py", "--customers", str(args.customers)])
    run([py, "scripts/load_raw.py"])
    dbt = [shutil.which("dbt") or "dbt"]
    run(dbt + ["build", "--profiles-dir", "."], cwd=TRANSFORM)   # seeds, models, snapshots, all tests
    run(dbt + ["docs", "generate", "--profiles-dir", "."], cwd=TRANSFORM)
    print(f"\nWarehouse ready: {DB_PATH}")
    print("Browse lineage & docs:  cd transform && dbt docs serve --profiles-dir .")
    if args.dashboard:
        run([py, "-m", "streamlit", "run", "dashboard/app.py"])
    else:
        print("Launch the dashboard:   streamlit run dashboard/app.py")


if __name__ == "__main__":
    main()
