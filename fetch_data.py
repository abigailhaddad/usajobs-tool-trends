#!/usr/bin/env python3
"""
Query the loyoladatamining/usajobs HuggingFace dataset directly via DuckDB —
no local download of the ~32GB parquet files.

For each monthly split (2017_01 through present) it counts job postings that
mention each tool, then writes two CSVs:

  results/tool_counts.csv   — per-tool counts per month
  results/bi_combined.csv   — deduplicated (Tableau OR Power BI) count per month

Authentication: set HF_TOKEN in a .env file or as an environment variable.
Without a token the queries still work but may be rate-limited.
"""

import csv
import json
import os
import re
import urllib.request

import duckdb

HF_PARQUET_API = "https://datasets-server.huggingface.co/parquet?dataset=loyoladatamining/usajobs"

PYTHON_EXCLUDE = r"(?i)\b(?:burmese|ball\s+python|rock\s+python|reticulated|constrictor|python\s+snake|invasive\s+snake|colt\s+python|python\s+revolver)\b"

TOOLS = {
    "python":  (r"(?i)\bpython\b",      PYTHON_EXCLUDE),
    "stata":   (r"(?i)\bstata\b",       None),
    "tableau": (r"(?i)\btableau\b",     None),
    "powerbi": (r"(?i)\bpower\s*bi\b",  None),
    "spss":    (r"(?i)\bSPSS\b",        None),
}


def load_hf_token():
    if os.environ.get("HF_TOKEN"):
        return os.environ["HF_TOKEN"]
    for path in [
        os.path.join(os.path.dirname(__file__), ".env"),
        os.path.expanduser("~/Documents/repos/opm/.env"),
    ]:
        path = os.path.normpath(path)
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    if line.strip().startswith("HF_TOKEN="):
                        return line.strip().split("=", 1)[1]
    return None


def get_parquet_files():
    req = urllib.request.Request(HF_PARQUET_API, headers={"User-Agent": "usajobs-tool-trends/1.0"})
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)
    by_split = {}
    for f in data.get("parquet_files", []):
        split = f["split"]
        if re.match(r"^\d{4}_\d{2}$", split):
            by_split.setdefault(split, []).append(f["url"])
    return dict(sorted(by_split.items()))


def build_tool_query(tools):
    filters = []
    for name, (match_pat, excl_pat) in tools.items():
        cond = f"regexp_matches(text, '{match_pat}')"
        if excl_pat:
            cond += f" AND NOT regexp_matches(text, '{excl_pat}')"
        filters.append(f"COUNT(*) FILTER (WHERE {cond}) AS {name}_count")
    counts = ",\n    ".join(filters)
    return f"SELECT COUNT(*) AS total,\n    {counts}\nFROM read_parquet(?)"


BI_QUERY = """
SELECT
    COUNT(*) FILTER (WHERE
        regexp_matches(text, '(?i)\\btableau\\b')
        OR regexp_matches(text, '(?i)\\bpower\\s*bi\\b')
    ) AS bi_count,
    COUNT(*) FILTER (WHERE
        regexp_matches(text, '(?i)\\btableau\\b')
        AND regexp_matches(text, '(?i)\\bpower\\s*bi\\b')
    ) AS both_count
FROM read_parquet(?)
"""


def main():
    base = os.path.dirname(__file__)
    os.makedirs(os.path.join(base, "results"), exist_ok=True)
    tool_path = os.path.join(base, "results", "tool_counts.csv")
    bi_path   = os.path.join(base, "results", "bi_combined.csv")

    print("Fetching parquet file list from HuggingFace...")
    splits = get_parquet_files()
    print(f"Found {len(splits)} monthly splits")

    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    token = load_hf_token()
    if token:
        con.execute("CREATE SECRET hf (TYPE HUGGINGFACE, TOKEN ?)", [token])
        print("HuggingFace token loaded.")
    else:
        print("No HF_TOKEN found — proceeding unauthenticated (may hit rate limits).")

    tool_names = list(TOOLS.keys())
    tool_query = build_tool_query(TOOLS)

    with open(tool_path, "w", newline="") as tf, open(bi_path, "w", newline="") as bf:
        tw = csv.DictWriter(tf, fieldnames=["split"] + [f"{t}_count" for t in tool_names] + ["total_postings"])
        bw = csv.DictWriter(bf, fieldnames=["split", "bi_count", "both_count"])
        tw.writeheader()
        bw.writeheader()

        for split, urls in splits.items():
            t_row = {"split": split, "total_postings": 0, **{f"{t}_count": 0 for t in tool_names}}
            b_row = {"split": split, "bi_count": 0, "both_count": 0}

            for url in urls:
                r = con.execute(tool_query, [url]).fetchone()
                t_row["total_postings"] += r[0]
                for i, t in enumerate(tool_names):
                    t_row[f"{t}_count"] += r[i + 1]

                r2 = con.execute(BI_QUERY, [url]).fetchone()
                b_row["bi_count"]   += r2[0]
                b_row["both_count"] += r2[1]

            tw.writerow(t_row)
            bw.writerow(b_row)
            tf.flush(); bf.flush()
            print(
                f"  {split}: python={t_row['python_count']:,}  tableau={t_row['tableau_count']:,}  "
                f"powerbi={t_row['powerbi_count']:,}  bi_combined={b_row['bi_count']:,}  "
                f"total={t_row['total_postings']:,}",
                flush=True,
            )

    print(f"\nDone. Results written to results/")


if __name__ == "__main__":
    main()
