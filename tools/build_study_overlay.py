"""
build_study_overlay.py
======================
Build a transparent hexagon overlay of the study area (the 14,191 sampled 5 km
hex locations) for the data section's Leaflet satellite map. Rendered in Web
Mercator so it lines up with the map tiles, exactly like build_region_overlay.py.

Output: ..\figures\study_area_overlay.png  (+ prints the geographic bounds)
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
from matplotlib.collections import PatchCollection

BASE = Path(r"D:\University\Masters\Data\Enviromental Clustering\Clustering time series\Clustering Final Model Embeddings (STEP 5 - NEW)")
OUT = Path(r"D:\University\Masters\Presentations\Poster Website\figures\study_area_overlay.png")
R = 6378137.0

def merc(lon, lat):
    return R * np.radians(lon), R * np.log(np.tan(np.pi/4.0 + np.radians(lat)/2.0))
def inv_merc(x, y):
    return np.degrees(x/R), np.degrees(2.0*np.arctan(np.exp(y/R)) - np.pi/2.0)

lat = np.concatenate([pd.read_csv(BASE/f"site_metadata_{s}.csv")["lat"] for s in ("train","val","test")]).astype(float)
lon = np.concatenate([pd.read_csv(BASE/f"site_metadata_{s}.csv")["lon"] for s in ("train","val","test")]).astype(float)
print("sites:", len(lat))

sx, sy = merc(lon, lat)
xmin, xmax, ymin, ymax = sx.min(), sx.max(), sy.min(), sy.max()
padx, pady = 0.02*(xmax-xmin), 0.02*(ymax-ymin)
xmin -= padx; xmax += padx; ymin -= pady; ymax += pady

med_nn = float(np.median(cKDTree(np.column_stack([sx, sy])).query(np.column_stack([sx, sy]), k=2)[0][:, 1]))
radius = med_nn / np.sqrt(3) * 1.06   # centre-to-vertex; slight overlap to close gaps
print("median nn (mercator m):", round(med_nn), "hex radius:", round(radius))

Wpx = 1700
Hpx = int(round(Wpx * (ymax-ymin)/(xmax-xmin)))
fig = plt.figure(figsize=(Wpx/200.0, Hpx/200.0), dpi=200)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
patches = [RegularPolygon((x, y), numVertices=6, radius=radius, orientation=0.0) for x, y in zip(sx, sy)]
pc = PatchCollection(patches, facecolor="#61223B", edgecolor="#3A1422", linewidth=0.15, alpha=0.5)
ax.add_collection(pc)
fig.savefig(OUT, transparent=True, dpi=200)
plt.close(fig)

lon_sw, lat_sw = inv_merc(xmin, ymin)
lon_ne, lat_ne = inv_merc(xmax, ymax)
from PIL import Image
print("saved", OUT.name, Image.open(OUT).size)
print("BOUNDS_SW_NE", round(float(lat_sw),5), round(float(lon_sw),5), round(float(lat_ne),5), round(float(lon_ne),5))
print("CENTER", round(float(lat_sw+lat_ne)/2,5), round(float(lon_sw+lon_ne)/2,5))
