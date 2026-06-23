"""
build_timeseries.py
===================
Sample one location from the 2006 daily dataset and plot a one-year snippet of
the six climate variables the model reads, to show the reader the raw input.

Output: ..\figures\data_timeseries.png  (+ prints the sampled location)
"""
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

PATH = Path(r"D:\University\Masters\Data\Enviromental Clustering\Data\5km Hex data\Parquet format\FinalDataset_2006_cleaned.parquet")
OUT = Path(r"D:\University\Masters\Presentations\Poster Website\figures\data_timeseries.png")

plt.rcParams.update({"figure.facecolor": "white", "savefig.facecolor": "white",
                     "font.family": "serif", "font.serif": ["DejaVu Serif"],
                     "font.size": 11, "axes.unicode_minus": False})

# --- pick a forestry-belt location (Mpumalanga escarpment) -----------------
ll = pq.read_table(PATH, columns=["lat", "lon"]).to_pandas().drop_duplicates()
tlat, tlon = -25.5, 30.6
ll["d"] = (ll.lat - tlat) ** 2 + (ll.lon - tlon) ** 2
sel = ll.sort_values("d").iloc[0]
la, lo = float(sel.lat), float(sel.lon)
print("sampled location:", round(la, 4), round(lo, 4))

cols = ["date", "tmax", "tmin", "rhmax", "rhmin", "precip", "u10_median"]
df = pq.read_table(PATH, columns=cols, filters=[("lat", "=", la), ("lon", "=", lo)]).to_pandas()
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
print("days:", len(df), "from", df.date.min().date(), "to", df.date.max().date())

# (column, label, unit, colour, kind)
SPEC = [
    ("tmax",       "Max temp",  r"$^\circ$C",  "#61223B", "line"),
    ("tmin",       "Min temp",  r"$^\circ$C",  "#9C5A74", "line"),
    ("rhmax",      "Max RH",    "%",        "#1D9E75", "line"),
    ("rhmin",      "Min RH",    "%",        "#5FB89A", "line"),
    ("precip",     "Precip",    "mm",       "#185FA5", "bar"),
    ("u10_median", "Wind",      "m/s",      "#D85A30", "line"),
]

fig, axes = plt.subplots(len(SPEC), 1, figsize=(10, 8), sharex=True)
for ax, (col, label, unit, color, kind) in zip(axes, SPEC):
    if kind == "bar":
        ax.bar(df["date"], df[col], width=1.0, color=color, linewidth=0)
    else:
        ax.plot(df["date"], df[col], color=color, linewidth=1.3)
    ax.set_ylabel(f"{label}\n({unit})", rotation=0, ha="right", va="center", labelpad=12, fontsize=10)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.margins(x=0.01)
    ax.tick_params(labelsize=9)
    ax.grid(axis="y", color="0.9", linewidth=0.6)
axes[-1].xaxis.set_major_locator(mdates.MonthLocator())
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
fig.align_ylabels(axes)
fig.tight_layout(h_pad=0.4)
fig.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close(fig)
from PIL import Image
print("saved", OUT.name, Image.open(OUT).size)
