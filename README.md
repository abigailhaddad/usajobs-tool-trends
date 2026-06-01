# usajobs-tool-trends

How often do federal job postings mention Python, Tableau, and Power BI — and how has that changed from 2017 to 2026?

Uses the [`loyoladatamining/usajobs`](https://huggingface.co/datasets/loyoladatamining/usajobs) HuggingFace dataset (~3M federal job postings). Queries parquet files directly via DuckDB — no 32GB local download needed.

![Python vs BI tools in federal job postings](results/tool_trends.png)

## What it shows

- Python and BI tools (Tableau + Power BI combined) grew in lockstep through 2017–2024
- Power BI barely existed in federal job postings before 2019, then overtook Tableau around 2022–23
- Everything collapsed after January 2025 with the broader federal hiring freeze

## Quick start

```bash
pip install -r requirements.txt

# Option A: skip the query, use pre-run results
python make_chart.py

# Option B: re-run the full query against HuggingFace (~1 hour)
python fetch_data.py
python make_chart.py
```

## Authentication

The queries work without a token but may hit rate limits. To authenticate, set `HF_TOKEN` in your environment or in a `.env` file:

```
HF_TOKEN=hf_...
```

## How the querying works

DuckDB's `httpfs` extension lets you query remote parquet files directly:

```python
import duckdb

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute("CREATE SECRET hf (TYPE HUGGINGFACE, TOKEN ?)", [token])

count = con.execute("""
    SELECT COUNT(*) FROM read_parquet(?)
    WHERE regexp_matches(text, '(?i)\\bpython\\b')
""", [parquet_url]).fetchone()[0]
```

The HuggingFace datasets-server API returns all parquet URLs for a dataset:

```
https://datasets-server.huggingface.co/parquet?dataset=loyoladatamining/usajobs
```

## Files

| File | Description |
|------|-------------|
| `fetch_data.py` | Queries HuggingFace parquet files, writes `results/tool_counts.csv` and `results/bi_combined.csv` |
| `make_chart.py` | Reads results CSVs, produces `results/tool_trends.png` |
| `results/tool_counts.csv` | Pre-run counts for Python, Stata, Tableau, Power BI, SPSS by month |
| `results/bi_combined.csv` | Pre-run deduplicated (Tableau OR Power BI) count by month |
