"""
compare_z_vs_grouppc1.py
========================

Relate the five autoencoder latent dimensions (z1..z5) to the four
interpretable climate gradients (group PC1 composites from
pc1_group_analysis.py), across all locations (train + validation + test).

Produces:
  z_vs_grouppc1_pearson.csv          5 x 4 Pearson r
  z_vs_grouppc1_spearman.csv         5 x 4 Spearman rho
  z_to_grouppc1_r2.csv               R^2 of (z1..z5 -> each group PC1) + best single z
  z_vs_grouppc1_correlation_heatmap.png
  z_latent_maps.png                  lat/lon maps of z1..z5 (+ cluster map)
  grouppc1_vs_bestz_maps.png         each group PC1 beside its best-matching latent

Latent sign is arbitrary (autoencoder), so correlation sign only marks
direction; in the side-by-side the latent is sign-aligned to the group for
visual comparison.
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

SCRIPT_DIR = Path(__file__).resolve().parent.parent   # analysis root (scripts/ is one level down)
BASE       = SCRIPT_DIR.parent

GROUPS = ["Temperature", "Precipitation", "Humidity", "Wind"]
MEANING = {"Temperature": "warm", "Precipitation": "wet",
           "Humidity": "humid", "Wind": "windy"}
ZDIMS  = [f"z{i}" for i in range(1, 6)]
K      = 8

plt.rcParams.update({
    "figure.facecolor":   "white",
    "savefig.facecolor":  "white",
    "font.family":        "serif",
    "font.serif":         ["DejaVu Serif"],
    "font.size":          10,
    "axes.unicode_minus": False,
})


def load_latents():
    frames = []
    for split, zname, mname in [("train", "z_train.npy", "site_metadata_train.csv"),
                                ("val",   "z_val.npy",   "site_metadata_val.csv"),
                                ("test",  "z_test.npy",  "site_metadata_test.csv")]:
        z = np.load(BASE / zname).astype(np.float64)
        m = pd.read_csv(BASE / mname).copy()
        for i in range(5):
            m[f"z{i+1}"] = z[:, i]
        frames.append(m)
    return pd.concat(frames, ignore_index=True)


def main():
    pc = pd.read_csv(SCRIPT_DIR / "site_pc1_scores.csv")     # lat,lon,split,cluster,4 groups
    zdf = load_latents()
    data = pc.merge(zdf[["lat", "lon", *ZDIMS]], on=["lat", "lon"],
                    how="left", validate="one_to_one")
    assert data[ZDIMS].notna().all().all(), "missing latents after merge"
    print(f"Sites: {len(data)}  (train {sum(data['split']=='train')}, "
          f"val {sum(data['split']=='val')}, test {sum(data['split']=='test')})")

    # standardised latents for plotting (correlation is scale-invariant)
    for z in ZDIMS:
        data[z + "_s"] = (data[z] - data[z].mean()) / data[z].std(ddof=0)

    # ---- correlations -----------------------------------------------------
    P = pd.DataFrame(index=ZDIMS, columns=GROUPS, dtype=float)
    S = pd.DataFrame(index=ZDIMS, columns=GROUPS, dtype=float)
    for z in ZDIMS:
        for g in GROUPS:
            P.loc[z, g] = pearsonr(data[z], data[g])[0]
            S.loc[z, g] = spearmanr(data[z], data[g])[0]
    P.to_csv(SCRIPT_DIR / "z_vs_grouppc1_pearson.csv")
    S.to_csv(SCRIPT_DIR / "z_vs_grouppc1_spearman.csv")

    print("\nPearson r  (latent z vs group PC1):")
    with pd.option_context("display.float_format", lambda v: f"{v:+.3f}"):
        print(P.to_string())

    # ---- multivariate R^2: z1..z5 -> each group PC1 -----------------------
    X = data[ZDIMS].to_numpy()
    r2_rows = []
    for g in GROUPS:
        y = data[g].to_numpy()
        r2 = LinearRegression().fit(X, y).score(X, y)
        best = P[g].abs().idxmax()
        r2_rows.append({"group": g, "R2_all_z": r2,
                        "best_single_z": best, "best_r": P.loc[best, g],
                        "best_single_r2": P.loc[best, g] ** 2})
    r2df = pd.DataFrame(r2_rows)
    r2df.to_csv(SCRIPT_DIR / "z_to_grouppc1_r2.csv", index=False)
    print("\nVariance of each group PC1 captured by the latents:")
    with pd.option_context("display.float_format", lambda v: f"{v:.3f}"):
        print(r2df.to_string(index=False))

    # ---- correlation heatmap ---------------------------------------------
    fig, ax = plt.subplots(figsize=(6.0, 5.5))
    A = P.to_numpy(dtype=float)
    norm = TwoSlopeNorm(vmin=-1, vcenter=0.0, vmax=1)
    im = ax.imshow(A, cmap="RdBu_r", norm=norm, aspect="auto")
    ax.set_xticks(range(len(GROUPS)))
    ax.set_xticklabels(GROUPS, rotation=20, ha="right")
    ax.set_yticks(range(len(ZDIMS)))
    ax.set_yticklabels(ZDIMS)
    for i in range(len(ZDIMS)):
        for j in range(len(GROUPS)):
            v = A[i, j]
            ax.text(j, i, f"{v:+.2f}", ha="center", va="center",
                    color="white" if abs(v) > 0.55 else "black", fontsize=10)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Pearson r")
    ax.set_title("Latent dimensions vs group PC1 gradients")
    fig.tight_layout()
    fig.savefig(SCRIPT_DIR / "z_vs_grouppc1_correlation_heatmap.png", dpi=200,
                bbox_inches="tight")
    plt.close(fig)

    # ---- latent maps ------------------------------------------------------
    def scatter(ax, vals, title, cbar_label, discrete=False):
        if discrete:
            sc = ax.scatter(data["lon"], data["lat"], c=vals, cmap="tab10",
                            s=6, alpha=0.9, edgecolor="none", vmin=0, vmax=9)
        else:
            m = float(np.abs(vals).max())
            sc = ax.scatter(data["lon"], data["lat"], c=vals, cmap="RdBu_r",
                            norm=TwoSlopeNorm(vmin=-m, vcenter=0.0, vmax=m),
                            s=6, alpha=0.9, edgecolor="none")
        ax.set_aspect("equal")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title(title)
        cbar = ax.figure.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label(cbar_label)

    fig, axes = plt.subplots(2, 3, figsize=(18, 13))
    for ax, z in zip(axes.ravel()[:5], ZDIMS):
        scatter(ax, data[z + "_s"].to_numpy(), f"{z} (standardised)", z)
    scatter(axes.ravel()[5], data["cluster"].to_numpy(),
            "KMeans K = 8 clusters", "cluster", discrete=True)
    fig.suptitle("Autoencoder latent dimensions across all locations "
                 "(train + validation + test)", fontsize=13)
    fig.tight_layout()
    fig.savefig(SCRIPT_DIR / "z_latent_maps.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # ---- group PC1 beside its best-matching latent ------------------------
    fig, axes = plt.subplots(len(GROUPS), 2, figsize=(13, 5.0 * len(GROUPS)))
    for row, g in enumerate(GROUPS):
        best = P[g].abs().idxmax()
        r = P.loc[best, g]
        scatter(axes[row, 0], data[g].to_numpy(),
                f"{g} PC1 (positive = {MEANING[g]})", "group PC1")
        z_aligned = data[best + "_s"].to_numpy() * np.sign(r)
        scatter(axes[row, 1], z_aligned,
                f"{best} (sign-aligned)  r = {r:+.2f}", best)
    fig.suptitle("Climate gradient vs its most-correlated latent dimension",
                 fontsize=13)
    fig.tight_layout()
    fig.savefig(SCRIPT_DIR / "grouppc1_vs_bestz_maps.png", dpi=200,
                bbox_inches="tight")
    plt.close(fig)

    print("\nwrote: z_vs_grouppc1_pearson.csv, z_vs_grouppc1_spearman.csv, "
          "z_to_grouppc1_r2.csv,")
    print("       z_vs_grouppc1_correlation_heatmap.png, z_latent_maps.png, "
          "grouppc1_vs_bestz_maps.png")
    print("\nDone.")


if __name__ == "__main__":
    main()
