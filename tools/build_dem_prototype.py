"""
build_dem_prototype.py
======================

Rasterise the 14,191 site elevations into a smoothed DEM for the standalone 3D
terrain prototype: a grayscale displacement map and a hypsometric colour drape.
Both are written to prototypes/assets/ with the study-area shape cut out
(transparent outside the data hull).

  dem_gray.png   red channel = normalised elevation (three.js displacementMap)
  dem_color.png  hypsometric tint (three.js colour map), green-brown-white ramp

The grid is a simple lon/lat raster (good enough for a look-and-feel prototype);
elevation is linearly interpolated, nearest-filled, then lightly smoothed.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"D:\University\Masters\Data\Enviromental Clustering\Clustering time series"
            r"\Clustering Final Model Embeddings (STEP 5 - NEW)")
ELEV_CSV = Path(r"D:\University\Masters\Data\Enviromental Clustering\Clustering time series"
                r"\Further Improvements of model (STEP 4 - NEW)\AUX Heads Group C simple"
                r"\site_elevation.csv")
OUT = Path(__file__).resolve().parent.parent / "prototypes" / "assets"
OUT.mkdir(parents=True, exist_ok=True)

SPLITS = ["train", "val", "test"]
W = H = 768

metas = [pd.read_csv(ROOT / f"site_metadata_{s}.csv") for s in SPLITS]
meta = pd.concat(metas, ignore_index=True)
elev = pd.read_csv(ELEV_CSV)
elev_col = next(c for c in elev.columns
                if c not in ("site_id", "lat", "lon") and pd.api.types.is_numeric_dtype(elev[c]))
df = meta[["site_id", "lat", "lon"]].merge(elev[["site_id", elev_col]], on="site_id", how="left") \
    .rename(columns={elev_col: "elev"}).dropna(subset=["elev"])

lon = df.lon.values
lat = df.lat.values
e = df.elev.values

lon0, lon1 = lon.min(), lon.max()
lat0, lat1 = lat.min(), lat.max()
padx = (lon1 - lon0) * 0.02
pady = (lat1 - lat0) * 0.02
lon0, lon1 = lon0 - padx, lon1 + padx
lat0, lat1 = lat0 - pady, lat1 + pady

gx = np.linspace(lon0, lon1, W)
gy = np.linspace(lat1, lat0, H)          # north (top) to south (bottom)
GX, GY = np.meshgrid(gx, gy)

grid = griddata((lon, lat), e, (GX, GY), method="linear")
nn = griddata((lon, lat), e, (GX, GY), method="nearest")
m = np.isnan(grid)
grid[m] = nn[m]
grid = gaussian_filter(grid, sigma=2.0)

# data hull: keep grid cells within ~1.8 median site spacings of a real site
tree = cKDTree(np.c_[lon, lat])
md = np.median(tree.query(np.c_[lon, lat], k=2)[0][:, 1])
dist, _ = tree.query(np.c_[GX.ravel(), GY.ravel()], k=1)
inside = (dist.reshape(H, W) <= md * 1.8)
inside = gaussian_filter(inside.astype(float), sigma=1.0) > 0.5
alpha = inside.astype(float)

emin, emax = np.percentile(grid[inside], [0.5, 99.5])
gn = np.clip((grid - emin) / (emax - emin), 0.0, 1.0)
gn_flat = gn * alpha                       # flat (0) outside the hull

# grayscale displacement (R=G=B=gn), alpha = hull
gray = np.dstack([gn_flat, gn_flat, gn_flat, alpha])
plt.imsave(OUT / "dem_gray.png", gray)

# hypsometric drape: terrain colormap but skip the blue (water) low end
cmap = plt.get_cmap("terrain")
rgb = cmap(0.25 + gn * 0.75)[:, :, :3]
color = np.dstack([rgb, alpha])
plt.imsave(OUT / "dem_color.png", color)

print(f"wrote {OUT / 'dem_gray.png'} and dem_color.png  ({W}x{H})")
print(f"  elevation display range {emin:.0f}..{emax:.0f} m, hull cells {int(inside.sum())}")
