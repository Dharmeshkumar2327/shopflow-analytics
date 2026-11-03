# Shortcuts for macOS / Linux. On Windows use:  python pipeline.py
export DUCKDB_PATH := $(CURDIR)/data/shopflow.duckdb
DBT := cd transform && dbt

.PHONY: setup data load build test docs dashboard all clean

setup:          ## install dependencies
	pip install -r requirements.txt

data:           ## generate synthetic raw CSVs
	python scripts/generate_data.py

load:           ## land raw CSVs into DuckDB (raw schema)
	python scripts/load_raw.py

build:          ## seeds + models + snapshots + all tests, in DAG order
	$(DBT) build --profiles-dir .

test:           ## data tests + unit tests only
	$(DBT) test --profiles-dir .

docs:           ## generate and serve dbt docs (lineage graph) on :8080
	$(DBT) docs generate --profiles-dir . && dbt docs serve --profiles-dir . --port 8080

dashboard:      ## launch the Streamlit dashboard on :8501
	streamlit run dashboard/app.py

all: data load build

clean:
	rm -rf transform/target transform/logs data/*.duckdb
