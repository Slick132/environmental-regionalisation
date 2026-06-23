"""
build_koppen_overlay.py
=======================
Builds the interactive Koppen-Geiger map overlay for the Poster Website, the
rule-based baseline shown next to the learned regions. It rasterises the
per-site Koppen class into a nearest-neighbour fill in Web Mercator (the same
method build_region_overlay.py uses for the learned regions) so the overlay
lines up with the Esri satellite tiles, and writes a small JavaScript file with
the geographic bounds, centre and a legend giving each class code, its plain
meaning and its site count.

Colours follow the updated Koppen-Geiger scheme of Peel, Finlayson and McMahon
(2007), the same reference the classification itself follows.

Outputs:
  ..\figures\koppen_overlay.png
  ..\js\koppen_overlay.js
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from PIL import Image

KG_CSV = Path(r"D:\University\Masters\Data\Environmetal Gradient\Koppen Geiger classification results Forestry Comp\Koppen_Geiger_Classification_Results_5km_fixed066THreshold.csv")
SITE = Path(r"D:\University\Masters\Presentations\Poster Website")
OUT_PNG = SITE / "figures" / "koppen_overlay.png"
OUT_JS = SITE / "js" / "koppen_overlay.js"

# Updated Koppen-Geiger colours (Peel et al., 2007) and plain-language meanings.
KG = {
    "Aw":  ("#46AAFA", "Tropical savanna, dry winter"),
    "BWh": ("#FF0000", "Hot desert"),
    "BSh": ("#F5A500", "Hot semi-arid steppe"),
    "BSk": ("#FFDC64", "Cold semi-arid steppe"),
    "Cwa": ("#96FF00", "Humid subtropical, dry winter, hot summer"),
    "Cwb": ("#64C800", "Subtropical highland, dry winter, warm summer"),
    "Cfa": ("#C8FF50", "Humid subtropical, no dry season, hot summer"),
    "Cfb": ("#64FF50", "Oceanic, no dry season, warm summer"),
}

R = 6378137.0


def merc(lon, lat):
    return R * np.radians(lon), R * np.log(np.tan(np.pi / 4.0 + np.radians(lat) / 2.0))


def inv_merc(x, y):
    return np.degrees(x / R), np.degrees(2.0 * np.arctan(np.exp(y / R)) - np.pi / 2.0)


def h2rgb(c):
    c = c.lstrip("#")
    return [int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)]


# --- data ------------------------------------------------------------------
df = pd.read_csv(KG_CSV)
df = df[df["Koppen_Code"].isin(KG.keys())].copy()
codes = sorted(df["Koppen_Code"].unique().tolist())
missing = [c for c in codes if c not in KG]
assert not missing, f"unmapped Koppen codes: {missing}"
code_to_idx = {c: i for i, c in enumerate(codes)}
lat = df["lat"].to_numpy(np.float64)
lon = df["lon"].to_numpy(np.float64)
labels = df["Koppen_Code"].map(code_to_idx).to_numpy()
counts = {c: int((df["Koppen_Code"] == c).sum()) for c in codes}
print(f"sites: {len(df)}   classes: {counts}")

# --- rasterise a nearest-neighbour / majority fill in Web Mercator ---------
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
gy = np.linspace(ymax, ymin, Hpx)
GX, GY = np.meshgrid(gx, gy)
pix = np.column_stack([GX.ravel(), GY.ravel()])

tree = cKDTree(np.column_stack([sx, sy]))
dnn, _ = tree.query(np.column_stack([sx, sy]), k=2)
med_nn = float(np.median(dnn[:, 1]))
thresh = 1.7 * med_nn

kk = 9
dist, idx = tree.query(pix, k=kk)
neigh = labels[idx]
votes = np.zeros((pix.shape[0], len(codes)), dtype=np.int16)
rows = np.arange(pix.shape[0])
for j in range(kk):
    votes[rows, neigh[:, j]] += 1
maj = votes.argmax(axis=1)
inside = dist[:, 0] <= thresh

rgb = np.array([h2rgb(KG[c][0]) for c in codes], dtype=np.uint8)
rgba = np.zeros((pix.shape[0], 4), dtype=np.uint8)
rgba[inside, :3] = rgb[maj[inside]]
rgba[inside, 3] = 205
img = rgba.reshape(Hpx, Wpx, 4)
OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
Image.fromarray(img, "RGBA").save(OUT_PNG)
print(f"wrote {OUT_PNG}  ({int(inside.sum())} filled pixels)")

# --- bounds + legend -------------------------------------------------------
lon_sw, lat_sw = inv_merc(xmin, ymin)
lon_ne, lat_ne = inv_merc(xmax, ymax)
bounds = [[round(float(lat_sw), 5), round(float(lon_sw), 5)],
          [round(float(lat_ne), 5), round(float(lon_ne), 5)]]
center = [round(float(lat_sw + lat_ne) / 2.0, 5), round(float(lon_sw + lon_ne) / 2.0, 5)]

legend = [{"code": c, "name": KG[c][1], "color": KG[c][0], "n": counts[c]}
          for c in sorted(codes, key=lambda k: -counts[k])]

data = {"img": "figures/koppen_overlay.png", "bounds": bounds, "center": center, "legend": legend}
OUT_JS.parent.mkdir(parents=True, exist_ok=True)
OUT_JS.write_text("window.KOPPEN_OVERLAY = " + json.dumps(data, indent=2) + ";\n", encoding="utf-8")
print(f"wrote {OUT_JS}")
print(f"bounds: {bounds}  center: {center}")
