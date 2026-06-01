# usajobs-tool-trends

An analysis of tool mentions in federal job postings from 2017 to 2026, using the [`loyoladatamining/usajobs`](https://huggingface.co/datasets/loyoladatamining/usajobs) dataset (~3M postings).

![Python vs BI tools in federal job postings](results/tool_trends.png)

## Data source

The dataset is queried directly from HuggingFace as monthly parquet files via DuckDB's `httpfs` extension — no local download required. The datasets-server API returns all parquet URLs:

```
https://datasets-server.huggingface.co/parquet?dataset=loyoladatamining/usajobs
```

Each file is queried with `read_parquet(url)` over HTTP. A HuggingFace token speeds things up but isn't required.

## Methodology

Tool mentions are counted with `regexp_matches` in DuckDB, one parquet file at a time. Python excludes snake and firearms contexts (Burmese python, Colt Python revolver, etc.). Tableau and Power BI are also counted as a combined deduplicated figure — a posting mentioning both counts once.

The chart uses a 3-month rolling average to smooth monthly noise.

## Running it

Pre-run results are in `results/` so you can go straight to the chart:

```bash
pip install -r requirements.txt
python make_chart.py
```

To re-run the full query against HuggingFace (~1 hour):

```bash
python fetch_data.py
python make_chart.py
```

Set `HF_TOKEN` in your environment or a `.env` file to authenticate.
