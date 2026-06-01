#!/usr/bin/env python3
"""
Read results/tool_counts.csv and results/bi_combined.csv and produce
a chart of Python vs combined BI tools (Tableau + Power BI deduplicated)
in federal job postings over time.

Saves to results/tool_trends.png and opens it.
"""

import csv
import os
import subprocess
import sys
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

BASE = os.path.dirname(__file__)

tool_path = os.path.join(BASE, "results", "tool_counts.csv")
bi_path   = os.path.join(BASE, "results", "bi_combined.csv")

python_by_split = {}
with open(tool_path) as f:
    for row in csv.DictReader(f):
        python_by_split[row["split"]] = int(row["python_count"])

splits, python_c, bi_c = [], [], []
with open(bi_path) as f:
    for row in csv.DictReader(f):
        y, m = row["split"].split("_")
        splits.append(datetime(int(y), int(m), 1))
        python_c.append(python_by_split.get(row["split"], 0))
        bi_c.append(int(row["bi_count"]))


def rolling(vals, n=3):
    return [sum(vals[max(0, i - n + 1):i + 1]) / min(i + 1, n) for i in range(len(vals))]


fig, ax = plt.subplots(figsize=(13, 6))
fig.patch.set_facecolor("#0f1117")
ax.set_facecolor("#0f1117")

PY_COLOR = "#4c9be8"
BI_COLOR = "#e8d44c"

for spine in ax.spines.values():
    spine.set_edgecolor("#444")
ax.tick_params(colors="#aaa", labelsize=10)

ax.plot(splits, rolling(python_c), color=PY_COLOR, lw=2.8, zorder=3)
ax.plot(splits, rolling(bi_c),     color=BI_COLOR, lw=2.8, zorder=3)

ax.legend(
    handles=[
        plt.Line2D([0], [0], color=PY_COLOR, lw=2.8, label="Python"),
        plt.Line2D([0], [0], color=BI_COLOR, lw=2.8, label="Tableau + Power BI (deduplicated)"),
    ],
    loc="upper left",
    framealpha=0.25,
    facecolor="#1a1a2e",
    edgecolor="#555",
    labelcolor="white",
    fontsize=10,
)

doge_start = datetime(2025, 1, 1)
ax.axvline(doge_start, color="#ff4444", lw=1, alpha=0.5, linestyle="--", zorder=1)
ax.text(doge_start, ax.get_ylim()[1] * 0.97, "  Jan 2025", color="#ff6666", fontsize=9, va="top")

ax.set_xlim(splits[0], splits[-1])
ax.set_ylim(0)
ax.yaxis.set_major_locator(ticker.MultipleLocator(25))
ax.grid(axis="y", color="#333", linewidth=0.7, zorder=0)
ax.grid(axis="x", color="#2a2a2a", linewidth=0.5, zorder=0)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

ax.set_title("Python vs BI tools in federal job postings (2017–2026)",
             color="white", fontsize=14, fontweight="bold", pad=14)
ax.set_ylabel("Job postings mentioning tool (3-month avg)", color="#aaa", fontsize=11)

fig.tight_layout()
out = os.path.join(BASE, "results", "tool_trends.png")
fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"Saved to {out}")

if sys.platform == "darwin":
    subprocess.run(["open", out])
elif sys.platform.startswith("linux"):
    subprocess.run(["xdg-open", out])
