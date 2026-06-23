"""
build_region_overlay.py
========================
Builds the interactive-map assets for the Poster Website results section.

It reproduces the final K-means K = 8 labelling of all 14,191 sites exactly as
km_cluster_spatial_map.py does (training and validation use the saved labels, the
test sites are assigned by nearest training centroid in standardised space), then
rasterises a nearest-neighbour cluster fill in Web Mercator so the gaps between
sites are filled by the majority of their neighbours. The fill is written as a
semi-transparent PNG that lines up with Leaflet tiles, together with a small
JavaScript file giving the geographic bounds, centre and legend.

Outputs:
  ..\figures\region_overlay.png
  ..\js\region_overlay.js
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.cm as cm
from matplotlib.colors import Normalize, to_hex

BASE = Path(r"D:\University\Masters\Data\Enviromental Clustering\Clustering time series\Clustering Final Model Embeddings (STEP 5 - NEW)")
FIXK8 = BASE / "KMeans" / "Fix K 8"
SITE = Path(r"D:\University\Masters\Presentations\Poster Website")
OUT_PNG = SITE / "figures" / "region_overlay.png"
OUT_JS = SITE / "js" / "region_overlay.js"
K = 8

TAB10 = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
         "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]

R = 6378137.0


def merc(lon, lat):
    x = R * np.radians(lon)
    y = R * np.log(np.tan(np.pi / 4.0 + np.radians(lat) / 2.0))
    return x, y


def inv_merc(x, y):
    lon = np.degrees(x / R)
    lat = np.degrees(2.0 * np.arctan(np.exp(y / R)) - np.pi / 2.0)
    return lon, lat


def h2rgb(c):
    c = c.lstrip("#")
    return [int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)]


def rnd(x, dec):
    return int(round(float(x))) if dec == 0 else round(float(x), dec)


def get_cmap(name):
    try:
        return matplotlib.colormaps[name]
    except Exception:
        return cm.get_cmap(name)


def min_dec(vals, cap=3):
    """Fewest decimal places (0..cap) that keep all values distinct."""
    arr = np.asarray(vals, dtype=float)
    for d in range(0, cap + 1):
        if len(set(np.round(arr, d).tolist())) == arr.size:
            return d
    return cap


# --- labelling (identical recipe to km_cluster_spatial_map.py) -------------
z_train = np.load(BASE / "z_train.npy").astype(np.float64)
z_test = np.load(BASE / "z_test.npy").astype(np.float64)
mu = z_train.mean(axis=0)
sd = z_train.std(axis=0) + 1e-12
centroids = np.load(FIXK8 / "centroids.npy")


def nearest_centroid(z):
    zs = (z - mu) / sd
    d = ((zs[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
    return d.argmin(axis=1).astype(int)


lab_train = np.load(FIXK8 / "training_labels.npy").astype(int)
lab_val = np.load(FIXK8 / "validation_labels.npy").astype(int)
lab_test = nearest_centroid(z_test)

meta_train = pd.read_csv(BASE / "site_metadata_train.csv")
meta_val = pd.read_csv(BASE / "site_metadata_val.csv")
meta_test = pd.read_csv(BASE / "site_metadata_test.csv")

lat = np.concatenate([meta_train["lat"], meta_val["lat"], meta_test["lat"]]).astype(np.float64)
lon = np.concatenate([meta_train["lon"], meta_val["lon"], meta_test["lon"]]).astype(np.float64)
labels = np.concatenate([lab_train, lab_val, lab_test]).astype(int)
counts = np.bincount(labels, minlength=K).tolist()
print(f"sites: {len(labels)}   per-cluster: {counts}")

# --- rasterise a nearest-neighbour / majority fill in Web Mercator --------
sx, sy = merc(lon, lat)
xmin, xmax = sx.min(), sx.max()
ymin, ymax = sy.min(), sy.max()
padx = 0.02 * (xmax - xmin)
pady = 0.02 * (ymax - ymin)
xmin -= padx; xmax += padx; ymin -= pady; ymax += pady

Wpx = 1000
Hpx = int(round(Wpx * (ymax - ymin) / (xmax - xmin)))
print(f"raster: {Wpx} x {Hpx}")

gx = np.linspace(xmin, xmax, Wpx)
gy = np.linspace(ymax, ymin, Hpx)  # row 0 = north (top)
GX, GY = np.meshgrid(gx, gy)
pix = np.column_stack([GX.ravel(), GY.ravel()])

tree = cKDTree(np.column_stack([sx, sy]))
dnn, _ = tree.query(np.column_stack([sx, sy]), k=2)
med_nn = float(np.median(dnn[:, 1]))
thresh = 1.7 * med_nn
print(f"median nearest-neighbour spacing (mercator m): {med_nn:.0f}   fill threshold: {thresh:.0f}")

kk = 9
dist, idx = tree.query(pix, k=kk)
neigh = labels[idx]                       # (npix, kk)
votes = np.zeros((pix.shape[0], K), dtype=np.int16)
rows = np.arange(pix.shape[0])
for j in range(kk):
    votes[rows, neigh[:, j]] += 1
maj = votes.argmax(axis=1)
inside = dist[:, 0] <= thresh

rgb = np.array([h2rgb(c) for c in TAB10], dtype=np.uint8)
rgba = np.zeros((pix.shape[0], 4), dtype=np.uint8)
rgba[inside, :3] = rgb[maj[inside]]
rgba[inside, 3] = 205
img = rgba.reshape(Hpx, Wpx, 4)
OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
Image.fromarray(img, "RGBA").save(OUT_PNG)
print(f"wrote {OUT_PNG}  ({inside.sum()} filled pixels)")

# --- per-variable recoloured overlays (same region pixels) ----------------
# (name, csv column, label, unit, matplotlib colormap, low end of the colour ramp)
VARS = [
    ("temperature", "BIO1", "Temperature", "&deg;C", "RdYlBu_r", 0.0),
    ("precipitation", "BIO12", "Precipitation", "mm", "YlGnBu", 0.15),
    ("humidity", "RH_mean", "Humidity", "%", "BuGn", 0.15),
    ("wind", "WS_mean", "Wind", "m/s", "Purples", 0.15),
]
means = pd.read_csv(FIXK8 / "fixk8_cluster_feature_means.csv").set_index("ae_cluster").sort_index()
variables = {}
for name, col, label, unit, cmname, lo in VARS:
    vals = means[col].to_numpy(dtype=float)
    dec = min_dec(vals)
    vmin, vmax = float(vals.min()), float(vals.max())
    cmap = get_cmap(cmname)
    # Colour by rank, not by raw value, so regions with close means still get
    # clearly different shades. The ramp starts above 0 for sequential maps so
    # the lowest region is still visible over the satellite imagery.
    ranks = np.empty(K, dtype=int)
    ranks[np.argsort(vals)] = np.arange(K)
    pos = lo + (1.0 - lo) * (ranks / (K - 1))
    reg_rgb = (np.array([cmap(p)[:3] for p in pos]) * 255.0).astype(np.uint8)
    rgba_v = np.zeros((pix.shape[0], 4), dtype=np.uint8)
    rgba_v[inside, :3] = reg_rgb[maj[inside]]
    rgba_v[inside, 3] = 205
    out_v = SITE / "figures" / f"overlay_{name}.png"
    Image.fromarray(rgba_v.reshape(Hpx, Wpx, 4), "RGBA").save(out_v)
    stops = [to_hex(cmap(lo + (1.0 - lo) * (r / (K - 1)))) for r in range(K)]
    regions_v = [{"k": int(k), "value": rnd(vals[k], dec), "color": to_hex(cmap(pos[k]))} for k in range(K)]
    variables[name] = {"img": f"figures/overlay_{name}.png", "label": label, "unit": unit,
                       "vmin": rnd(vmin, dec), "vmax": rnd(vmax, dec), "stops": stops, "regions": regions_v}
    print(f"wrote {out_v}")

# --- bounds + legend ------------------------------------------------------
lon_sw, lat_sw = inv_merc(xmin, ymin)
lon_ne, lat_ne = inv_merc(xmax, ymax)
bounds = [[round(float(lat_sw), 5), round(float(lon_sw), 5)],
          [round(float(lat_ne), 5), round(float(lon_ne), 5)]]
center = [round(float(lat_sw + lat_ne) / 2.0, 5), round(float(lon_sw + lon_ne) / 2.0, 5)]
cent_lat = [round(float(lat[labels == k].mean()), 4) for k in range(K)]
cent_lon = [round(float(lon[labels == k].mean()), 4) for k in range(K)]
legend = [{"k": k, "color": TAB10[k], "name": f"Region {k + 1}", "n": int(counts[k]),
           "lat": cent_lat[k], "lon": cent_lon[k]} for k in range(K)]

data = {"img": "figures/region_overlay.png", "bounds": bounds, "center": center,
        "legend": legend, "variables": variables}
OUT_JS.parent.mkdir(parents=True, exist_ok=True)
OUT_JS.write_text("window.REGION_OVERLAY = " + json.dumps(data, indent=2) + ";\n", encoding="utf-8")
print(f"wrote {OUT_JS}")
print(f"bounds: {bounds}  center: {center}")
