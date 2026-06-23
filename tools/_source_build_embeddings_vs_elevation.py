"""Builder for embeddings_vs_elevation.ipynb.

Constructs a notebook that compares the final autoencoder embeddings (z1-z5)
with per-site elevation, to test for correlation. Run this script, then execute
the notebook with nbconvert.
"""
from pathlib import Path
import nbformat as nbf

HERE = Path(__file__).resolve().parent
NB_PATH = HERE / "embeddings_vs_elevation.ipynb"

nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip("\n")))


def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip("\n")))


md(r"""
# Model embeddings compared to elevation

This notebook tests whether the five latent dimensions of the final autoencoder
(z1 to z5) relate to terrain elevation. Each of the 14,191 sites has a 5-D
embedding from the model and a single elevation value in metres. The comparison
reports the Pearson and Spearman correlation of each latent dimension with
elevation, a multiple regression of elevation on all five dimensions, and a set
of plots (correlation bars, scatter against elevation, spatial maps, and the
regression fit).

The embeddings and the site metadata are loaded from the STEP 5 root. Elevation
is loaded from the STEP 4 auxiliary-head export and joined on `site_id`.
""")

code(r"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

# Plot style kept consistent with the thesis figures (serif, modest sizes).
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.dpi": 120,
    "savefig.bbox": "tight",
})

ROOT = Path(r"D:\University\Masters\Data\Enviromental Clustering\Clustering time series\Clustering Final Model Embeddings (STEP 5 - NEW)")
ELEV_CSV = Path(r"D:\University\Masters\Data\Enviromental Clustering\Clustering time series\Further Improvements of model (STEP 4 - NEW)\AUX Heads Group C simple\site_elevation.csv")
OUT_DIR = ROOT / "Model embeddings compared to elevation"
OUT_DIR.mkdir(exist_ok=True)

SPLITS = ["train", "val", "test"]
Z_COLS = ["z1", "z2", "z3", "z4", "z5"]
""")

md(r"""
## Recompute the 33 climate features from the raw data

The 33 cluster summary features are recomputed from the raw daily parquet files
using the shared AuxTargetComputer, the same routine used for the other feature
files. The recomputation picks up the corrected RH_mean, which now follows the
BIO1 monthly aggregation. The 19 parquet years are loaded one at a time so that
only a single year is held in memory at any moment. The result is cached to
site_features_33.csv, so the computation runs only once.
""")

code(r"""
import sys

AUX_DIR = Path(r"D:\University\Masters\Data\Enviromental Clustering\Clustering time series\Architecture Tuning (STEP 3 - NEW)\Phase 3")
PARQUET_DIR = Path(r"D:\University\Masters\Data\Enviromental Clustering\Data\5km Hex data\Parquet format")
FEATURES_CSV = OUT_DIR / "site_features_33.csv"

YEARS = list(range(2006, 2025))            # 19 parquet years
DAYS_PER_YEAR = 365
EXPECTED_T = len(YEARS) * DAYS_PER_YEAR    # 6935
PARQUET_COLS = {"tmax": 0, "tmin": 1, "rhmax": 2, "rhmin": 3, "u10_median": 4, "precip": 5}

if str(AUX_DIR) not in sys.path:
    sys.path.insert(0, str(AUX_DIR))
from aux_features import AuxTargetComputer, TARGET_NAMES
assert len(TARGET_NAMES) == 33, f"expected 33 features, got {len(TARGET_NAMES)}"


def load_env_year_by_year():
    # Assemble the (N, 6, T) raw tensor, reading one parquet year at a time so
    # that only a single year is held in memory at any moment.
    first = pd.read_parquet(PARQUET_DIR / f"FinalDataset_{YEARS[0]}_cleaned.parquet",
                            columns=["lat", "lon"])
    coords = first.drop_duplicates().sort_values(["lat", "lon"]).reset_index(drop=True)
    n_sites = len(coords)
    site_to_idx = {(la, lo): i for i, (la, lo) in
                   enumerate(zip(coords["lat"].to_numpy(), coords["lon"].to_numpy()))}
    env = np.zeros((n_sites, 6, EXPECTED_T), dtype=np.float32)
    print(f"sites {n_sites}, tensor {env.nbytes / 1024**3:.2f} GiB; loading {len(YEARS)} years")
    for yi, year in enumerate(YEARS):
        dfy = pd.read_parquet(PARQUET_DIR / f"FinalDataset_{year}_cleaned.parquet",
                              columns=["lat", "lon", "date"] + list(PARQUET_COLS))
        dfy = dfy.sort_values(["lat", "lon", "date"]).reset_index(drop=True)
        ys = yi * DAYS_PER_YEAR
        for (la, lo), g in dfy.groupby(["lat", "lon"], sort=False):
            i = site_to_idx.get((la, lo))
            if i is None:
                continue
            for col, ch in PARQUET_COLS.items():
                vals = g[col].to_numpy()[:DAYS_PER_YEAR]
                env[i, ch, ys:ys + len(vals)] = vals
        del dfy
        print(f"  loaded {year}")
    return env, coords


if FEATURES_CSV.exists():
    feat33 = pd.read_csv(FEATURES_CSV)
    FEATURES = [c for c in feat33.columns if c not in ("lat", "lon")]
    print(f"loaded cached features: {feat33.shape}")
else:
    env, coords = load_env_year_by_year()
    print("computing 33 features with AuxTargetComputer ...")
    feats = AuxTargetComputer()(env, verbose=False).numpy()
    del env
    FEATURES = list(TARGET_NAMES)
    feat33 = coords[["lat", "lon"]].copy()
    feat33[FEATURES] = feats
    feat33.to_csv(FEATURES_CSV, index=False)
    print(f"computed and saved {feat33.shape} to {FEATURES_CSV.name}")
""")

md(r"""
## Load the embeddings, metadata, and elevation

The three split embeddings stack in train, validation, test order. The matching
metadata files supply `site_id`, `lat`, and `lon` in the same row order, so the
embedding rows and metadata rows align directly. Elevation joins on `site_id`.
""")

code(r"""
zs = [np.load(ROOT / f"z_{s}.npy").astype(np.float64) for s in SPLITS]
metas = [pd.read_csv(ROOT / f"site_metadata_{s}.csv") for s in SPLITS]

z = np.vstack(zs)
meta = pd.concat(metas, ignore_index=True)
assert z.shape[0] == len(meta), "embedding rows do not match metadata rows"

df = meta[["site_id", "lat", "lon", "split"]].copy()
for i, c in enumerate(Z_COLS):
    df[c] = z[:, i]

elev = pd.read_csv(ELEV_CSV)        # columns: site_id, elevation_m
df = df.merge(elev, on="site_id", how="left")
assert df["elevation_m"].notna().all(), "some sites have no elevation"

elev_v = df["elevation_m"].values
print(f"sites: {len(df)}")
print(f"elevation range: {elev_v.min():.0f} to {elev_v.max():.0f} m  "
      f"(mean {elev_v.mean():.0f}, std {elev_v.std():.0f})")
df.head()
""")

md(r"""
## Correlation of each latent dimension with elevation

The Pearson coefficient measures the strength of a straight-line relationship.
The Spearman coefficient measures a monotonic relationship and is robust to a
non-linear but order-preserving link between a latent dimension and elevation.
""")

code(r"""
rows = []
for c in Z_COLS:
    zv = df[c].values
    r, rp = pearsonr(zv, elev_v)
    rho, rhop = spearmanr(zv, elev_v)
    rows.append({
        "dimension": c,
        "pearson_r": r, "pearson_p": rp,
        "spearman_rho": rho, "spearman_p": rhop,
    })
corr = pd.DataFrame(rows).set_index("dimension")
corr.round(4).to_csv(OUT_DIR / "elevation_correlations.csv")
print(corr.round(3))
corr.round(3)
""")

md(r"""
## Multiple regression of elevation on the five dimensions

A single dimension may capture only part of the elevation signal. Regressing
elevation on all five dimensions together reports how much of the elevation
variance the full embedding explains, given by the coefficient of determination
R squared. The multiple correlation R is the square root of R squared. The
predictors are standardised to zero mean and unit variance, so each coefficient
reads as the change in elevation in metres for a one standard-deviation change in
that dimension, holding the others fixed.
""")

code(r"""
X = df[Z_COLS].values
y = elev_v
Xs = StandardScaler().fit_transform(X)

reg = LinearRegression().fit(Xs, y)
r2 = reg.score(Xs, y)
mult_R = np.sqrt(r2)

print(f"elevation ~ z1..z5:  R^2 = {r2:.3f}   multiple R = {mult_R:.3f}")
print("standardised coefficients (metres per 1 SD of the dimension):")
print(pd.Series(reg.coef_, index=Z_COLS).round(1))
""")

md(r"""
## Correlation magnitudes per dimension

The absolute Pearson and Spearman coefficients are plotted side by side so the
dimension that tracks elevation most strongly is easy to read off.
""")

code(r"""
fig, ax = plt.subplots(figsize=(6.5, 4))
xpos = np.arange(len(Z_COLS))
w = 0.38
ax.bar(xpos - w / 2, corr["pearson_r"].abs(), w, label="|Pearson r|", color="steelblue")
ax.bar(xpos + w / 2, corr["spearman_rho"].abs(), w, label="|Spearman rho|", color="darkorange")
ax.set_xticks(xpos)
ax.set_xticklabels(Z_COLS)
ax.set_ylabel("correlation magnitude with elevation")
ax.set_ylim(0, 1)
ax.legend()
fig.savefig(OUT_DIR / "elevation_correlation_bars.png", transparent=True, dpi=150)
plt.show()
""")

md(r"""
## Latent dimension against elevation

Each panel plots one latent dimension against elevation for all sites, with a
least-squares line and the Pearson coefficient in the title. Point opacity is
low so that dense regions are visible.
""")

code(r"""
# One separate transparent figure per latent dimension.
for c in Z_COLS:
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    ax.scatter(df[c], elev_v, s=5, alpha=0.12, color="steelblue", edgecolors="none")
    b1, b0 = np.polyfit(df[c], elev_v, 1)
    xs = np.array([df[c].min(), df[c].max()])
    ax.plot(xs, b0 + b1 * xs, color="firebrick", lw=1.5)
    r = corr.loc[c, "pearson_r"]
    ax.set_title(f"{c} vs elevation (r = {r:+.2f})")
    ax.set_xlabel(c)
    ax.set_ylabel("elevation (m)")
    fig.tight_layout()
    fig.savefig(OUT_DIR / f"elevation_vs_{c}.png", transparent=True, dpi=150)
    plt.show()
""")

md(r"""
## Spatial maps

The first panel maps elevation over longitude and latitude. The remaining panels
map each latent dimension over the same coordinates. A dimension that tracks
elevation shows a spatial pattern that matches the elevation panel.
""")

code(r"""
fig, axes = plt.subplots(2, 3, figsize=(14, 9))

ax = axes.flat[0]
sc = ax.scatter(df["lon"], df["lat"], c=elev_v, cmap="viridis", s=6)
ax.set_title("elevation (m)")
ax.set_xlabel("longitude")
ax.set_ylabel("latitude")
fig.colorbar(sc, ax=ax, shrink=0.8)

for ax, c in zip(axes.flat[1:], Z_COLS):
    sc = ax.scatter(df["lon"], df["lat"], c=df[c], cmap="coolwarm", s=6)
    ax.set_title(c)
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    fig.colorbar(sc, ax=ax, shrink=0.8)

fig.tight_layout()
fig.savefig(OUT_DIR / "elevation_and_z_maps.png", transparent=True, dpi=150)
plt.show()
""")

md(r"""
## Regression fit

The predicted elevation from the five-dimension regression is plotted against the
actual elevation. Points on the diagonal are predicted exactly. The spread around
the diagonal shows the part of the elevation signal the embedding does not carry.
""")

code(r"""
pred = reg.predict(Xs)
fig, ax = plt.subplots(figsize=(5.6, 5.6))
ax.scatter(y, pred, s=5, alpha=0.12, color="steelblue", edgecolors="none")
lims = [y.min(), y.max()]
ax.plot(lims, lims, color="firebrick", lw=1.2)
ax.set_xlabel("actual elevation (m)")
ax.set_ylabel("predicted elevation (m)")
ax.set_title(f"five-dimension fit to elevation (R^2 = {r2:.2f})")
fig.tight_layout()
fig.savefig(OUT_DIR / "elevation_regression_fit.png", transparent=True, dpi=150)
plt.show()
""")

md(r"""
## What the embedding encodes beyond elevation

Elevation is expected to dominate one or two latent axes, because elevation sets
temperature through the lapse rate and the encoder reads the temperature
channels. The question of interest is what the remaining axes carry. To answer
this, each latent dimension is correlated against 33 interpretable per-site
variables: the WorldClim-style bioclimatic set (BIO1 to BIO19, covering
temperature level, temperature seasonality, precipitation amount, and
precipitation seasonality), humidity variables (the mean annual relative humidity
RH_mean, the within-year RH range, the humidity seasonality, the warm-quarter
vapour-pressure deficit VPD, and the mean relative humidity of the wettest,
driest, warmest, and coldest quarters), and wind variables (the mean annual wind
speed, the wind seasonality, and the mean wind of the windiest, wettest, driest,
and warmest quarters). The quarter-based humidity and wind features follow the
same wettest, driest, warmest, and coldest quarter scheme as the bioclimatic
variables, so the numeric suffix marks a quarter and not an hour of the day.

Two views are produced. The raw correlation shows which variable each dimension
tracks. The partial correlation controlling for elevation removes the elevation
signal from both the dimension and the variable, so the residual correlation
shows the information each dimension carries that elevation does not.

The 33 features are the ones recomputed at the top of this notebook from the raw
daily data, and are joined to the embedding sites on rounded latitude and
longitude.
""")

code(r"""
# Features come from the recomputation cell above (feat33: lat, lon + 33 features).
feat = feat33.copy()
FEATURES = [c for c in feat.columns if c not in ("lat", "lon")]

# Join on rounded coordinates (the 5 km grid spacing is far larger than 1e-5 deg,
# so rounding to five decimals gives a unique, exact key on both sides).
for d in (df, feat):
    d["lat_r"] = np.round(d["lat"].values, 5)
    d["lon_r"] = np.round(d["lon"].values, 5)

merged = df.merge(feat.drop(columns=["lat", "lon"]), on=["lat_r", "lon_r"], how="left")
assert len(merged) == len(df), "coordinate join changed the row count"
assert merged[FEATURES].notna().all().all(), "some sites did not match a feature row"
print(f"matched {len(merged)} sites to {len(FEATURES)} interpretable features")
print("feature groups: BIO1-BIO19 (temperature and precipitation), "
      "RH/VPD (humidity), WS (wind)")
""")

md(r"""
### Correlation of each dimension with the interpretable features

The heatmap shows the Pearson correlation of every latent dimension with every
feature. A red cell is a positive correlation and a blue cell a negative one.
""")

code(r"""
Zc = merged[Z_COLS].values
Fc = merged[FEATURES].values
e = merged["elevation_m"].values

# Standardise columns so a matrix product gives Pearson correlations directly.
Zsd = (Zc - Zc.mean(0)) / Zc.std(0)
Fsd = (Fc - Fc.mean(0)) / Fc.std(0)
esd = (e - e.mean()) / e.std()

R = (Zsd.T @ Fsd) / len(merged)                 # 5 x 32 raw Pearson
Rdf = pd.DataFrame(R, index=Z_COLS, columns=FEATURES)
Rdf.round(3).to_csv(OUT_DIR / "z_feature_correlation.csv")

CAT_COLOR = {"temperature": "firebrick", "precipitation": "steelblue",
             "humidity": "seagreen", "wind": "goldenrod"}


def feat_category(f):
    if f.startswith("BIO"):
        return "temperature" if int(f[3:]) <= 11 else "precipitation"
    if f.startswith("RH") or f.startswith("VPD"):
        return "humidity"
    if f.startswith("WS"):
        return "wind"
    return "other"


cats_f = [feat_category(f) for f in FEATURES]
bounds_f = [k for k in range(1, len(FEATURES)) if cats_f[k] != cats_f[k - 1]]
edges_f = [0] + bounds_f + [len(FEATURES)]


def feature_blocks(ax):
    # Colour the feature (x-axis) labels by category, add white dividers between
    # the category blocks, and place a bold block label above each block.
    for lbl, f in zip(ax.get_xticklabels(), FEATURES):
        lbl.set_color(CAT_COLOR[feat_category(f)])
    for b in bounds_f:
        ax.axvline(b - 0.5, color="white", lw=2.5)
    for a, c in zip(edges_f[:-1], edges_f[1:]):
        mid = (a + c - 1) / 2.0
        cat = cats_f[a]
        ax.text(mid, -0.9, cat.upper(), va="bottom", ha="center",
                fontsize=9, fontweight="bold", color=CAT_COLOR[cat], clip_on=False)


fig, ax = plt.subplots(figsize=(14, 3.8))
im = ax.imshow(R, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")
ax.set_xticks(np.arange(len(FEATURES)))
ax.set_xticklabels(FEATURES, rotation=90, fontsize=8)
ax.set_yticks(np.arange(len(Z_COLS)))
ax.set_yticklabels(Z_COLS)
feature_blocks(ax)
ax.set_title("Pearson correlation of latent dimensions with interpretable features", pad=26)
fig.colorbar(im, ax=ax, shrink=0.8, label="Pearson r")
fig.tight_layout()
fig.savefig(OUT_DIR / "z_feature_correlation.png", transparent=True, dpi=150)
plt.show()

print("Raw correlation, top 4 features per dimension:")
for zc in Z_COLS:
    top = Rdf.loc[zc].abs().sort_values(ascending=False).head(4)
    items = ", ".join(f"{f} ({Rdf.loc[zc, f]:+.2f})" for f in top.index)
    print(f"  {zc}: {items}")
""")

md(r"""
### Partial correlation controlling for elevation

Each cell is the correlation of a latent dimension with a feature after the
linear effect of elevation has been removed from both. A cell that stays strong
here marks information the dimension carries that elevation does not explain.
""")

code(r"""
rze = (Zsd.T @ esd) / len(merged)               # 5,  dimension vs elevation
rfe = (Fsd.T @ esd) / len(merged)               # 32, feature vs elevation

num = R - np.outer(rze, rfe)
den = np.sqrt(np.outer(1 - rze ** 2, 1 - rfe ** 2))
Rp = num / den                                  # partial correlation given elevation
Rpdf = pd.DataFrame(Rp, index=Z_COLS, columns=FEATURES)
Rpdf.round(3).to_csv(OUT_DIR / "z_feature_partial_correlation.csv")

fig, ax = plt.subplots(figsize=(14, 3.8))
im = ax.imshow(Rp, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")
ax.set_xticks(np.arange(len(FEATURES)))
ax.set_xticklabels(FEATURES, rotation=90, fontsize=8)
ax.set_yticks(np.arange(len(Z_COLS)))
ax.set_yticklabels(Z_COLS)
feature_blocks(ax)
ax.set_title("Partial correlation with features, controlling for elevation", pad=26)
fig.colorbar(im, ax=ax, shrink=0.8, label="partial r")
fig.tight_layout()
fig.savefig(OUT_DIR / "z_feature_partial_correlation.png", transparent=True, dpi=150)
plt.show()

print("Elevation-controlled correlation, top 4 features per dimension:")
for zc in Z_COLS:
    top = Rpdf.loc[zc].abs().sort_values(ascending=False).head(4)
    items = ", ".join(f"{f} ({Rpdf.loc[zc, f]:+.2f})" for f in top.index)
    print(f"  {zc}: {items}")
""")


md(r"""
## Approach A: how well the embedding retains each feature (random forest)

The Pearson correlations above are linear and pairwise, but the autoencoder is
non-linear. To capture non-linear encoding, a random forest regressor is fitted
for each of the 33 features, predicting the feature from the five latent
dimensions z1 to z5. The five dimensions are far fewer and much less collinear
than the 33 features, so the importance assigned to each dimension is stable. For
each feature the importances show which dimension carries that feature, and the
out-of-bag R^2 shows how well the embedding reconstructs the feature. The random
forest measures the strength of the relationship only, so the sign of the
relationship is still read from the Pearson correlation above.
""")

code(r"""
from sklearn.ensemble import RandomForestRegressor

A_IMP = OUT_DIR / "rf_feature_dim_importance.csv"
A_OOB = OUT_DIR / "rf_feature_oob_r2.csv"
if A_IMP.exists() and A_OOB.exists():
    imp = pd.read_csv(A_IMP, index_col=0)
    oob_r2 = pd.read_csv(A_OOB, index_col=0).iloc[:, 0]
    print("loaded cached Approach A results (delete the two csv files to retrain)")
else:
    X_rf = merged[Z_COLS].values
    imp_rows = []
    oob_rows = []
    for f in FEATURES:
        rf = RandomForestRegressor(n_estimators=300, random_state=0,
                                   oob_score=True, n_jobs=-1)
        rf.fit(X_rf, merged[f].values)
        imp_rows.append(rf.feature_importances_)
        oob_rows.append(rf.oob_score_)
    imp = pd.DataFrame(imp_rows, index=FEATURES, columns=Z_COLS)
    oob_r2 = pd.Series(oob_rows, index=FEATURES, name="oob_R2")
    imp.round(4).to_csv(A_IMP)
    oob_r2.round(4).to_csv(A_OOB)
    print("trained and saved Approach A results")

print(f"mean out-of-bag R^2 across the 33 features: {oob_r2.mean():.3f}")
print("dominant dimension per feature (random forest importance):")
dom = imp.idxmax(axis=1)
for d in Z_COLS:
    feats = imp.index[dom == d].tolist()
    print(f"  {d}: {', '.join(feats) if feats else '(none)'}")
""")

code(r"""
CAT_COLOR = {"temperature": "firebrick", "precipitation": "steelblue",
             "humidity": "seagreen", "wind": "goldenrod"}


def feat_category(f):
    if f.startswith("BIO"):
        return "temperature" if int(f[3:]) <= 11 else "precipitation"
    if f.startswith("RH") or f.startswith("VPD"):
        return "humidity"
    if f.startswith("WS"):
        return "wind"
    return "other"


cats = [feat_category(f) for f in FEATURES]
bounds = [k for k in range(1, len(FEATURES)) if cats[k] != cats[k - 1]]
edges = [0] + bounds + [len(FEATURES)]

fig, ax = plt.subplots(figsize=(8, 11))
im = ax.imshow(imp.values, cmap="viridis", aspect="auto", vmin=0, vmax=1)
ax.set_xticks(np.arange(len(Z_COLS)))
ax.set_xticklabels(Z_COLS)
ax.set_yticks(np.arange(len(FEATURES)))
ax.set_yticklabels(FEATURES, fontsize=7)
for lbl, f in zip(ax.get_yticklabels(), FEATURES):
    lbl.set_color(CAT_COLOR[feat_category(f)])
ax.set_xlabel("latent dimension")
ax.set_title("Approach A: dimension contributing most to each feature")
for i in range(len(FEATURES)):
    for j in range(len(Z_COLS)):
        v = imp.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                color="white" if v < 0.55 else "black", fontsize=6)
for b in bounds:
    ax.axhline(b - 0.5, color="white", lw=2.5)
for a, c in zip(edges[:-1], edges[1:]):
    mid = (a + c - 1) / 2.0
    cat = cats[a]
    ax.text(-0.34, mid, cat.upper(), rotation=90, va="center", ha="center",
            fontsize=10, fontweight="bold", color=CAT_COLOR[cat],
            transform=ax.get_yaxis_transform(), clip_on=False)
fig.colorbar(im, ax=ax, shrink=0.5, label="importance (fraction)")
fig.tight_layout()
fig.savefig(OUT_DIR / "rf_feature_dim_importance.png", transparent=True, dpi=150)
plt.show()
""")

code(r"""
# Feature category for colouring (temperature, precipitation, humidity, wind).
CAT_COLOR = {"temperature": "firebrick", "precipitation": "steelblue",
             "humidity": "seagreen", "wind": "goldenrod"}


def feat_category(f):
    if f.startswith("BIO"):
        return "temperature" if int(f[3:]) <= 11 else "precipitation"
    if f.startswith("RH") or f.startswith("VPD"):
        return "humidity"
    if f.startswith("WS"):
        return "wind"
    return "other"


# Approach A view: out-of-bag R^2 for recovering each feature from z1 to z5.
order = oob_r2.sort_values(ascending=True)
bar_colors = [CAT_COLOR[feat_category(f)] for f in order.index]
fig, ax = plt.subplots(figsize=(8, 9))
ax.barh(np.arange(len(order)), order.values, color=bar_colors)
ax.set_yticks(np.arange(len(order)))
ax.set_yticklabels(order.index, fontsize=8)
ax.set_xlim(0, 1)
ax.set_xlabel("out-of-bag $R^2$")
ax.set_title("Approach A: variance of each feature recovered from the five embeddings")
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in CAT_COLOR.values()]
ax.legend(handles, list(CAT_COLOR.keys()), loc="lower right", fontsize=9)
fig.tight_layout()
fig.savefig(OUT_DIR / "rfA_feature_oob_r2.png", transparent=True, dpi=150)
plt.show()
""")

md(r"""
## Approach B: physical meaning of each dimension (random forest)

Approach A predicts each feature from the five dimensions and measures how much of
the feature the embedding retains. Approach B reverses the direction to label each
dimension. A random forest regressor is fitted for each latent dimension,
predicting the dimension from the 33 features, and the feature importances show
which physical variables define that dimension. The 33 features are collinear, so
the importance is split among correlated features and is read as a group-level
indication, for example a cluster of temperature features, rather than a single
exact driver. The out-of-bag R^2 shows how well the features reproduce the
dimension.
""")

code(r"""
from sklearn.ensemble import RandomForestRegressor

B_IMP = OUT_DIR / "rfB_dim_from_features_importance.csv"
B_OOB = OUT_DIR / "rfB_dim_oob_r2.csv"
if B_IMP.exists() and B_OOB.exists():
    impB = pd.read_csv(B_IMP, index_col=0)
    oobB = pd.read_csv(B_OOB, index_col=0).iloc[:, 0]
    print("loaded cached Approach B results (delete the two csv files to retrain)")
else:
    impB_rows = []
    oobB_vals = []
    for d in Z_COLS:
        rfb = RandomForestRegressor(n_estimators=300, random_state=0,
                                    oob_score=True, n_jobs=-1)
        rfb.fit(merged[FEATURES].values, merged[d].values)
        impB_rows.append(rfb.feature_importances_)
        oobB_vals.append(rfb.oob_score_)
    impB = pd.DataFrame(impB_rows, index=Z_COLS, columns=FEATURES)
    oobB = pd.Series(oobB_vals, index=Z_COLS, name="oob_R2")
    impB.round(4).to_csv(B_IMP)
    oobB.round(4).to_csv(B_OOB)
    print("trained and saved Approach B results")

print("Approach B - out-of-bag R^2 predicting each dimension from the 33 features:")
print(oobB.round(3))
print("top features per dimension:")
for d in Z_COLS:
    top = impB.loc[d].sort_values(ascending=False).head(5)
    print(f"  {d}: " + ", ".join(f"{f} ({v:.2f})" for f, v in top.items()))
""")

code(r"""
catsB = [feat_category(f) for f in FEATURES]
boundsB = [k for k in range(1, len(FEATURES)) if catsB[k] != catsB[k - 1]]
edgesB = [0] + boundsB + [len(FEATURES)]

fig, ax = plt.subplots(figsize=(14, 3.8))
im = ax.imshow(impB.values, cmap="magma", aspect="auto", vmin=0)
ax.set_yticks(np.arange(len(Z_COLS)))
ax.set_yticklabels(Z_COLS)
ax.set_xticks(np.arange(len(FEATURES)))
ax.set_xticklabels(FEATURES, rotation=90, fontsize=8)
for lbl, f in zip(ax.get_xticklabels(), FEATURES):
    lbl.set_color(CAT_COLOR[feat_category(f)])
for b in boundsB:
    ax.axvline(b - 0.5, color="white", lw=2.5)
for a, c in zip(edgesB[:-1], edgesB[1:]):
    mid = (a + c - 1) / 2.0
    cat = catsB[a]
    ax.text(mid, -0.9, cat.upper(), va="bottom", ha="center",
            fontsize=9, fontweight="bold", color=CAT_COLOR[cat], clip_on=False)
ax.set_title("Approach B: feature importance for predicting each embedding dimension", pad=26)
fig.colorbar(im, ax=ax, shrink=0.8, label="importance")
fig.tight_layout()
fig.savefig(OUT_DIR / "rfB_dim_from_features_importance.png", transparent=True, dpi=150)
plt.show()
""")

code(r"""
fig, axes = plt.subplots(1, len(Z_COLS), figsize=(18, 5))
for ax, d in zip(axes, Z_COLS):
    top = impB.loc[d].sort_values(ascending=False).head(8)[::-1]
    colors = [CAT_COLOR[feat_category(f)] for f in top.index]
    ax.barh(np.arange(len(top)), top.values, color=colors)
    ax.set_yticks(np.arange(len(top)))
    ax.set_yticklabels(top.index, fontsize=8)
    ax.set_title(f"{d}  (OOB $R^2$ = {oobB[d]:.2f})")
    ax.set_xlabel("importance")
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in CAT_COLOR.values()]
fig.legend(handles, list(CAT_COLOR.keys()), loc="upper right", ncol=4, fontsize=9)
fig.suptitle("Approach B: top features defining each embedding dimension")
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(OUT_DIR / "rfB_top_features_per_dim.png", transparent=True, dpi=150)
plt.show()
""")

md(r"""
## Elevation-controlled random forest (non-linear residual)

Approach A predicts each feature from the five dimensions without controlling for
elevation, so it is the non-linear counterpart of the raw Pearson correlation.
This final view is the elevation-controlled counterpart, and it removes the
elevation effect non-linearly. The analysis follows three steps. First, a random
forest predicts each feature from elevation alone, so the model captures both the
linear and the non-linear part of the elevation effect. Second, the residual is
the actual feature minus the predicted feature, which is the variance the elevation
model cannot explain. Third, a second random forest predicts the residual from the
five latent dimensions, and the dimension importances show which dimension carries
the elevation-free part of each feature.

The residual has to be formed carefully. A random forest is a powerful learner and
can memorise the training data, so using the same data to train the elevation model
and to predict it would drive the residual towards noise and erase the real signal.
The residual is therefore formed from out-of-bag predictions: each site is predicted
only by the trees that did not see that site during training, which gives an
unbiased residual. The importances of the second random forest are averaged over
three random seeds, and at this sample size (14,191 sites, five predictors) the
rankings do not depend on the seed.
""")

code(r"""
from sklearn.ensemble import RandomForestRegressor

C_IMP = OUT_DIR / "rfC_elevation_controlled_importance.csv"
C_OOB = OUT_DIR / "rfC_elevation_controlled_oob_r2.csv"
if C_IMP.exists() and C_OOB.exists():
    impC = pd.read_csv(C_IMP, index_col=0)
    oobC = pd.read_csv(C_OOB, index_col=0).iloc[:, 0]
    print("loaded cached elevation-controlled results (delete the two csv files to retrain)")
else:
    elev_col = merged["elevation_m"].values.reshape(-1, 1)
    Xz_c = merged[Z_COLS].values
    impC_rows = []
    oobC_vals = []
    for f in FEATURES:
        y = merged[f].values
        # Remove elevation non-linearly with a random forest, and form the residual
        # from out-of-bag predictions so that overfitting the elevation model does not
        # drive the residual to noise. Each site is predicted only by the trees that
        # did not see that site during training.
        rf_elev = RandomForestRegressor(n_estimators=300, random_state=0,
                                        oob_score=True, n_jobs=-1)
        rf_elev.fit(elev_col, y)
        resid = y - rf_elev.oob_prediction_
        seed_imp = []
        seed_oob = []
        for seed in (0, 1, 2):
            rf = RandomForestRegressor(n_estimators=300, random_state=seed,
                                       oob_score=True, n_jobs=-1)
            rf.fit(Xz_c, resid)
            seed_imp.append(rf.feature_importances_)
            seed_oob.append(rf.oob_score_)
        impC_rows.append(np.mean(seed_imp, axis=0))
        oobC_vals.append(float(np.mean(seed_oob)))
    impC = pd.DataFrame(impC_rows, index=FEATURES, columns=Z_COLS)
    oobC = pd.Series(oobC_vals, index=FEATURES, name="oob_R2")
    impC.round(4).to_csv(C_IMP)
    oobC.round(4).to_csv(C_OOB)
    print("trained and saved elevation-controlled results")

print(f"mean residual out-of-bag R^2 across features: {oobC.mean():.3f}")
print("dominant dimension per feature (elevation-controlled):")
domC = impC.idxmax(axis=1)
for d in Z_COLS:
    feats = impC.index[domC == d].tolist()
    print(f"  {d}: {', '.join(feats) if feats else '(none)'}")

domA = imp.idxmax(axis=1)
changed = [f for f in FEATURES if domA[f] != domC[f]]
print(f"\ndominant dimension changed after controlling for elevation: "
      f"{len(changed)}/{len(FEATURES)} features")
for f in changed:
    print(f"  {f}: {domA[f]} -> {domC[f]}")
""")

code(r"""
catsC = [feat_category(f) for f in FEATURES]
boundsC = [k for k in range(1, len(FEATURES)) if catsC[k] != catsC[k - 1]]
edgesC = [0] + boundsC + [len(FEATURES)]

fig, ax = plt.subplots(figsize=(8, 11))
im = ax.imshow(impC.values, cmap="viridis", aspect="auto", vmin=0, vmax=1)
ax.set_xticks(np.arange(len(Z_COLS)))
ax.set_xticklabels(Z_COLS)
ax.set_yticks(np.arange(len(FEATURES)))
ax.set_yticklabels(FEATURES, fontsize=7)
for lbl, f in zip(ax.get_yticklabels(), FEATURES):
    lbl.set_color(CAT_COLOR[feat_category(f)])
ax.set_xlabel("latent dimension")
ax.set_title("Elevation-controlled RF: dimension predicting each feature's elevation-free part")
for i in range(len(FEATURES)):
    for j in range(len(Z_COLS)):
        v = impC.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                color="white" if v < 0.55 else "black", fontsize=6)
for b in boundsC:
    ax.axhline(b - 0.5, color="white", lw=2.5)
for a, c in zip(edgesC[:-1], edgesC[1:]):
    mid = (a + c - 1) / 2.0
    cat = catsC[a]
    ax.text(-0.34, mid, cat.upper(), rotation=90, va="center", ha="center",
            fontsize=10, fontweight="bold", color=CAT_COLOR[cat],
            transform=ax.get_yaxis_transform(), clip_on=False)
fig.colorbar(im, ax=ax, shrink=0.5, label="importance (fraction)")
fig.tight_layout()
fig.savefig(OUT_DIR / "rfC_elevation_controlled_importance.png", transparent=True, dpi=150)
plt.show()
""")

nb["cells"] = cells
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nb.metadata["language_info"] = {"name": "python"}

nbf.write(nb, NB_PATH)
print(f"wrote {NB_PATH}")
print(f"{len(cells)} cells")
