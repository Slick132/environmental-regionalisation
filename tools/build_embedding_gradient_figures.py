"""
build_embedding_gradient_figures.py
===================================

Regenerate the figures for the website section on the learned embeddings and
their relationship to elevation, at high resolution (300 dpi), with a white
background that matches the white figure cards on the site.

The plotting logic is taken from two analysis scripts and consolidated here so
the website figures can be rebuilt in one step:

  * compare_z_vs_grouppc1.py          (Analysing final clustering embeddings)
        -> spatial maps of the five latent dimensions z1..z5
  * _build_embeddings_vs_elevation.py (Model embeddings compared to elevation)
        -> correlation of z1..z5 with site elevation, the multiple regression
           of elevation on the five dimensions, and the regression fit plot

Inputs (read only, absolute paths to the STEP 5 / STEP 4 data roots):
  ROOT/z_{train,val,test}.npy             the 5-D embedding per split
  ROOT/site_metadata_{train,val,test}.csv site_id, lat, lon, split (same order)
  ELEV_CSV                                site_id, elevation_m

Outputs (written into the website figures/ folder):
  embedding_gradient_maps.png   z1..z5 (diverging) + elevation (viridis), 2x3
  elevation_recovery_fit.png    predicted vs actual elevation, with R^2
  elevation_correlation_bars.png  |Pearson| and |Spearman| of each z vs elevation

Run from anywhere:
  python build_embedding_gradient_figures.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
ROOT = Path(r"D:\University\Masters\Data\Enviromental Clustering\Clustering time series"
            r"\Clustering Final Model Embeddings (STEP 5 - NEW)")
ELEV_CSV = Path(r"D:\University\Masters\Data\Enviromental Clustering\Clustering time series"
                r"\Further Improvements of model (STEP 4 - NEW)\AUX Heads Group C simple"
                r"\site_elevation.csv")

# website/figures (this script lives in website/tools)
OUT_DIR = Path(__file__).resolve().parent.parent / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SPLITS = ["train", "val", "test"]
Z_COLS = ["z1", "z2", "z3", "z4", "z5"]
DPI = 300

plt.rcParams.update({
    "figure.facecolor":  "white",
    "savefig.facecolor": "white",
    "savefig.bbox":      "tight",
    "font.family":       "serif",
    "font.serif":        ["DejaVu Serif"],
    "font.size":         11,
    "axes.titlesize":    12,
    "axes.labelsize":    11,
    "axes.unicode_minus": False,
})


# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------
def load_data():
    """Stack the three splits and join elevation on site_id."""
    zs = [np.load(ROOT / f"z_{s}.npy").astype(np.float64) for s in SPLITS]
    metas = [pd.read_csv(ROOT / f"site_metadata_{s}.csv") for s in SPLITS]
    z = np.vstack(zs)
    meta = pd.concat(metas, ignore_index=True)
    assert z.shape[0] == len(meta), "embedding rows do not match metadata rows"

    df = meta[["site_id", "lat", "lon", "split"]].copy()
    for i, c in enumerate(Z_COLS):
        df[c] = z[:, i]

    elev = pd.read_csv(ELEV_CSV)
    elev_col = next(c for c in elev.columns
                    if c not in ("site_id", "lat", "lon") and
                    pd.api.types.is_numeric_dtype(elev[c]))
    df = df.merge(elev[["site_id", elev_col]], on="site_id", how="left")
    df = df.rename(columns={elev_col: "elevation_m"})
    assert df["elevation_m"].notna().all(), "some sites have no elevation"

    print(f"sites: {len(df)}  "
          f"(train {sum(df.split=='train')}, val {sum(df.split=='val')}, "
          f"test {sum(df.split=='test')})")
    e = df["elevation_m"].values
    print(f"elevation range: {e.min():.0f} to {e.max():.0f} m "
          f"(mean {e.mean():.0f}, std {e.std():.0f})")
    return df


def correlations(df):
    e = df["elevation_m"].values
    rows = []
    for c in Z_COLS:
        r, _ = pearsonr(df[c].values, e)
        rho, _ = spearmanr(df[c].values, e)
        rows.append({"dimension": c, "pearson_r": r, "spearman_rho": rho})
    corr = pd.DataFrame(rows).set_index("dimension")
    print("\ncorrelation of each dimension with elevation:")
    print(corr.round(3))
    return corr


def regression(df):
    X = df[Z_COLS].values
    y = df["elevation_m"].values
    Xs = StandardScaler().fit_transform(X)
    reg = LinearRegression().fit(Xs, y)
    r2 = reg.score(Xs, y)
    pred = reg.predict(Xs)
    print(f"\nelevation ~ z1..z5:  R^2 = {r2:.3f}   multiple R = {np.sqrt(r2):.3f}")
    return y, pred, r2


# ----------------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------------
def fig_gradient_maps(df):
    """z1..z5 as diverging maps, elevation as the sixth panel (viridis)."""
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))

    for ax, c in zip(axes.flat[:5], Z_COLS):
        v = (df[c].values - df[c].values.mean()) / df[c].values.std()
        m = float(np.abs(v).max())
        sc = ax.scatter(df["lon"], df["lat"], c=v, cmap="RdBu_r",
                        norm=TwoSlopeNorm(vmin=-m, vcenter=0.0, vmax=m),
                        s=6, alpha=0.9, edgecolors="none")
        ax.set_title(f"Learned dimension {c[1:]}  ({c}, standardised)")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_aspect("equal")
        cb = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
        cb.set_label(c)

    ax = axes.flat[5]
    sc = ax.scatter(df["lon"], df["lat"], c=df["elevation_m"].values,
                    cmap="viridis", s=6, alpha=0.9, edgecolors="none")
    ax.set_title("Elevation (metres, never given to the model)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal")
    cb = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("elevation (m)")

    fig.tight_layout()
    out = OUT_DIR / "embedding_gradient_maps.png"
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"wrote {out.name}")


def fig_recovery(y, pred, r2):
    fig, ax = plt.subplots(figsize=(6.2, 6.2))
    ax.scatter(y, pred, s=5, alpha=0.12, color="steelblue", edgecolors="none")
    lims = [float(y.min()), float(y.max())]
    ax.plot(lims, lims, color="firebrick", lw=1.3)
    ax.set_xlabel("actual elevation (m)")
    ax.set_ylabel("predicted elevation (m)")
    ax.set_title(f"Elevation predicted from the five numbers\n"
                 f"(multiple regression, $R^2$ = {r2:.2f})")
    ax.set_aspect("equal")
    fig.tight_layout()
    out = OUT_DIR / "elevation_recovery_fit.png"
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"wrote {out.name}")


def fig_corr_bars(corr):
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    xpos = np.arange(len(Z_COLS))
    w = 0.38
    ax.bar(xpos - w / 2, corr["pearson_r"].abs(), w,
           label="|Pearson r|", color="steelblue")
    ax.bar(xpos + w / 2, corr["spearman_rho"].abs(), w,
           label="|Spearman rho|", color="darkorange")
    ax.set_xticks(xpos)
    ax.set_xticklabels(Z_COLS)
    ax.set_ylabel("correlation magnitude with elevation")
    ax.set_ylim(0, 1)
    ax.legend()
    fig.tight_layout()
    out = OUT_DIR / "elevation_correlation_bars.png"
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"wrote {out.name}")


def main():
    df = load_data()
    corr = correlations(df)
    y, pred, r2 = regression(df)
    fig_gradient_maps(df)
    fig_recovery(y, pred, r2)
    fig_corr_bars(corr)
    print(f"\nall figures written to {OUT_DIR} at {DPI} dpi")


if __name__ == "__main__":
    main()
