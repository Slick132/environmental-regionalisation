"""
build_prototype_data.py
=======================

Export a small, downsampled per-site JSON for the embedding+elevation ANIMATION
prototypes (data/prototype_sites.json). Reuses the same 14,191-site join as
build_embedding_gradient_figures.py: z1..z5 from the embeddings, lat/lon from
the metadata, elevation from the STEP 4 auxiliary export.

Fields per site: lon, lat, elev, z1..z5, elev_hat (elevation predicted from the
five dimensions by the same multiple regression, R^2 ~ 0.87). Also ships a
Delaunay triangulation of the sampled points (for the relief animation), the
per-axis Spearman correlation with elevation, value ranges, and a z2 sign-flip
so positive z2 maps to high ground.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.spatial import Delaunay
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

ROOT = Path(r"D:\University\Masters\Data\Enviromental Clustering\Clustering time series"
            r"\Clustering Final Model Embeddings (STEP 5 - NEW)")
ELEV_CSV = Path(r"D:\University\Masters\Data\Enviromental Clustering\Clustering time series"
                r"\Further Improvements of model (STEP 4 - NEW)\AUX Heads Group C simple"
                r"\site_elevation.csv")
OUT = Path(__file__).resolve().parent.parent / "data"
OUT.mkdir(parents=True, exist_ok=True)

SPLITS = ["train", "val", "test"]
Z = ["z1", "z2", "z3", "z4", "z5"]
N_SAMPLE = 2500
SEED = 7

zs = [np.load(ROOT / f"z_{s}.npy").astype(np.float64) for s in SPLITS]
metas = [pd.read_csv(ROOT / f"site_metadata_{s}.csv") for s in SPLITS]
z = np.vstack(zs)
meta = pd.concat(metas, ignore_index=True)
df = meta[["site_id", "lat", "lon"]].copy()
for i, c in enumerate(Z):
    df[c] = z[:, i]

elev = pd.read_csv(ELEV_CSV)
elev_col = next(c for c in elev.columns
                if c not in ("site_id", "lat", "lon") and pd.api.types.is_numeric_dtype(elev[c]))
df = df.merge(elev[["site_id", elev_col]], on="site_id", how="left").rename(columns={elev_col: "elev"})
assert df["elev"].notna().all(), "some sites have no elevation"

# elevation predicted from z1..z5 (same regression as the figure script)
X = df[Z].values
y = df["elev"].values
Xs = StandardScaler().fit_transform(X)
reg = LinearRegression().fit(Xs, y)
df["elev_hat"] = reg.predict(Xs)
r2 = float(reg.score(Xs, y))

spear = {c: round(float(spearmanr(df[c], y)[0]), 3) for c in Z}
z2_flip = 1.0 if spear["z2"] >= 0 else -1.0

# downsample: a seeded random spatial sample, plus the 40 highest sites so peaks survive
rng = np.random.default_rng(SEED)
idx = rng.choice(len(df), size=min(N_SAMPLE, len(df)), replace=False)
top = np.argsort(df["elev"].values)[-40:]
idx = np.unique(np.concatenate([idx, top]))
sub = df.iloc[idx].reset_index(drop=True)

# Delaunay on lon/lat; drop long triangles that bridge concave gaps / the hull
pts = sub[["lon", "lat"]].values
tri = Delaunay(pts)
simp = tri.simplices


def elen(a, b):
    d = pts[a] - pts[b]
    return np.hypot(d[:, 0], d[:, 1])


maxedge = np.maximum.reduce([elen(simp[:, 0], simp[:, 1]),
                             elen(simp[:, 1], simp[:, 2]),
                             elen(simp[:, 2], simp[:, 0])])
simp = simp[maxedge <= np.median(maxedge) * 2.2]

cols = ["lon", "lat", "elev", "z1", "z2", "z3", "z4", "z5", "elev_hat"]
arr = sub[cols].to_numpy()
sites = [[round(float(v), 4) for v in r] for r in arr]

out = {
    "fields": cols,
    "bounds": {"lon": [float(sub.lon.min()), float(sub.lon.max())],
               "lat": [float(sub.lat.min()), float(sub.lat.max())]},
    "ranges": {c: [round(float(sub[c].min()), 4), round(float(sub[c].max()), 4)] for c in cols[2:]},
    "spearman": spear,
    "z2_flip": z2_flip,
    "r2": round(r2, 3),
    "n": len(sites),
    "tris": [[int(a), int(b), int(c)] for a, b, c in simp],
    "sites": sites,
}
(OUT / "prototype_sites.json").write_text(json.dumps(out), encoding="utf-8")
print(f"wrote {OUT / 'prototype_sites.json'}")
print(f"  sites={len(sites)} tris={len(simp)} r2={r2:.3f} spearman={spear} z2_flip={z2_flip}")
