"""Quick diagnostic: confirm the eight K-means clusters are genuinely distinct,
both in the 5-D embedding and on each headline variable, and explain why two
regions can share a rounded humidity value."""
from pathlib import Path
from itertools import combinations
import numpy as np
import pandas as pd

BASE = Path(r"D:\University\Masters\Data\Enviromental Clustering\Clustering time series\Clustering Final Model Embeddings (STEP 5 - NEW)")
FIXK8 = BASE / "KMeans" / "Fix K 8"
K = 8

C = np.load(FIXK8 / "centroids.npy")  # 8 x 5, standardised embedding space
dists = sorted((float(np.linalg.norm(C[i] - C[j])), i, j) for i, j in combinations(range(K), 2))
print("5-D embedding centroid separation (standardised space):")
print(f"  closest pair : clusters {dists[0][1]} & {dists[0][2]}  distance = {dists[0][0]:.3f}")
print(f"  farthest pair: clusters {dists[-1][1]} & {dists[-1][2]}  distance = {dists[-1][0]:.3f}")
print(f"  every one of the {len(dists)} pairwise distances is > 0: {all(d[0] > 1e-6 for d in dists)}")

means = pd.read_csv(FIXK8 / "fixk8_cluster_feature_means.csv").set_index("ae_cluster").sort_index()
print("\nPer-variable distinctness of the eight cluster means:")
for col, label, unit in [("BIO1", "temperature", "C"), ("BIO12", "precipitation", "mm"),
                         ("RH_mean", "humidity", "%"), ("WS_mean", "wind", "m/s")]:
    v = means[col].to_numpy(float)
    s = np.sort(v)
    gap = float(np.diff(s).min())
    print(f"  {label:13s}: all 8 distinct = {len(set(np.round(v, 6))) == K}; smallest gap = {gap:.3f} {unit}")

rh = means["RH_mean"].to_numpy(float)
order = np.argsort(rh)
gaps = np.diff(np.sort(rh))
pi = int(np.argmin(gaps))
a, b = int(order[pi]), int(order[pi + 1])
print(f"\nThe two clusters closest in humidity are {a} & {b}: {rh[a]:.3f}% vs {rh[b]:.3f}% "
      f"(gap {abs(rh[a]-rh[b]):.3f} percentage points), yet they differ clearly elsewhere:")
for col, unit in [("BIO1", "C"), ("BIO12", "mm"), ("WS_mean", "m/s")]:
    print(f"  {col:8s}: {means.loc[a, col]:.2f} vs {means.loc[b, col]:.2f} {unit}")
