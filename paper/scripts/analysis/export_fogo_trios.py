# -*- coding: utf-8 -*-
"""
Export Fogo admissible trio indices to data/fogo_trios.npy
for use by wp4_synthetic.py.

Reuses the same load_data() and haversine_km() from mcdm_experiment.py
to generate the identical N=389, ~1.94M trio index used in the main experiment.
"""
import sys
import os
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding='utf-8')

from mcdm_experiment import (
    load_data, impute_nan, haversine_km, COL, MIN_DIST_KM
)

DATA_DIR = Path(__file__).parent.parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
NPY_OUT = DATA_DIR / 'fogo_trios.npy'

print("Loading Fogo data...")
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
N = len(df_via)
print(f"  N_viable = {N}")

D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
valid = D_via >= MIN_DIST_KM

print("Enumerating admissible trios...")
trio_list = []
for i in range(N):
    for j in range(i+1, N):
        if not valid[i, j]:
            continue
        for k in range(j+1, N):
            if valid[i, k] and valid[j, k]:
                trio_list.append((i, j, k))

trio_arr = np.array(trio_list, dtype=np.int32)
print(f"  {len(trio_arr):,} admissible trios")

np.save(NPY_OUT, trio_arr)
print(f"Saved to {NPY_OUT}")

