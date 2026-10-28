# -*- coding: utf-8 -*-
"""
_f8_coincidence.py  -- vec/vec AND vec/mm trio-level coincidence for 500 draws.

For each draw, records both greedy and optimal trio indices.
Coincidence = draws where greedy_trio_idx == optimal_trio_idx.

Uses same seed/kappa/N as F8 run (SEED=42, KAPPA=200, N=500).

Run:
    uv run python scripts/_f8_coincidence.py
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import dirichlet as sp_dirichlet

ROOT = Path(__file__).parent.parent

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, haversine_km, MIN_DIST_KM,
    _build_decision_matrix
)

N_DRAWS = 500
KAPPA   = 200
SEED    = 42
EPS     = 1e-9

t0 = time.time()
print("Loading data...", flush=True)
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL['protected']] > 0].copy()
N = len(df_via)
assert N == 389
col_names = list(AHP_WEIGHTS.keys())
w_ahp = np.array(list(AHP_WEIGHTS.values()))
X_raw, benefit = _build_decision_matrix(df_via)

print("Building trios...", flush=True)
try:
    trios = np.load(ROOT / 'data' / 'fogo_trios.npy')
    print(f"  Loaded fogo_trios.npy: {len(trios):,}", flush=True)
except FileNotFoundError:
    D = haversine_km(df_via['latitude (degrees)'].values,
                     df_via['longitude (degrees)'].values)
    valid = D >= MIN_DIST_KM
    trios_list = [(i, j, k)
                  for i in range(N) for j in range(i+1, N) if valid[i, j]
                  for k in range(j+1, N) if valid[i, k] and valid[j, k]]
    trios = np.array(trios_list, dtype=np.int32)
    print(f"  Built: {len(trios):,}", flush=True)

assert len(trios) == 1944653
T0, T1, T2 = trios[:, 0], trios[:, 1], trios[:, 2]
T = len(trios)
print(f"Trios: {T:,}  t={time.time()-t0:.1f}s", flush=True)

# Benefit-adjusted matrices for mm scoring
X_adj_mm = X_raw.copy()
for j, b in enumerate(benefit):
    if not b:
        X_adj_mm[:, j] = 1.0 - X_raw[:, j]

# Vec norms (L2 of raw columns = L2_via)
norms_via = np.maximum(np.sqrt((X_raw**2).sum(0)), 1e-12)
X_adj_vec = X_adj_mm / norms_via  # vec-normalised benefit-adjusted

# Vec objectives: same as vec scoring (aligned for Proposition 1)
# F1 = -(G1 contrib), F2 = -(G2 contrib), F3 = +(G3 contrib)
from mcdm_experiment import F1_CRIT, F2_CRIT, F3_CRIT
G1 = [col_names.index(c) for c in F1_CRIT]
G2 = [col_names.index(c) for c in F2_CRIT]
G3 = [col_names.index(c) for c in F3_CRIT]

def compute_objs_vec(w):
    """Per-trio vec objectives (F1 min, F2 min, F3 max)."""
    score = (X_adj_vec * w).sum(1)   # per-site scalar (= SAW/vec score per site)
    # Objectives = group-level sums, oriented for minimisation/maximisation
    f1 = -(X_adj_vec[:, G1] * w[G1]).sum(1)
    f2 = -(X_adj_vec[:, G2] * w[G2]).sum(1)
    f3 =  (X_adj_vec[:, G3] * w[G3]).sum(1)
    F1 = f1[T0] + f1[T1] + f1[T2]
    F2 = f2[T0] + f2[T1] + f2[T2]
    F3 = f3[T0] + f3[T1] + f3[T2]
    return F1, F2, F3, score

def compute_objs_mm(w):
    f1 = -(X_adj_mm[:, G1] * w[G1]).sum(1)
    f2 = -(X_adj_mm[:, G2] * w[G2]).sum(1)
    f3 =  (X_adj_mm[:, G3] * w[G3]).sum(1)
    F1 = f1[T0] + f1[T1] + f1[T2]
    F2 = f2[T0] + f2[T1] + f2[T2]
    F3 = f3[T0] + f3[T1] + f3[T2]
    return F1, F2, F3

from mcdm_experiment import greedy_trio
# Distance matrix (for greedy constraint)
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)

# Dirichlet draws (same as F8 run)
rng = np.random.default_rng(SEED)
W_DRAWS = sp_dirichlet.rvs(KAPPA * w_ahp, size=N_DRAWS, random_state=rng)

print(f"\nRunning {N_DRAWS} draws x 2 combos (vec/vec + vec/mm) ...", flush=True)

records = []
t_start = time.time()
for d, w in enumerate(W_DRAWS):
    # Vec objectives
    F1v, F2v, F3v, score_vec = compute_objs_vec(w)

    # vec/vec — optimal: argmax of score_vec over trios
    trio_scores_vec = score_vec[T0] + score_vec[T1] + score_vec[T2]
    vv_opt_idx = int(trio_scores_vec.argmax())
    vv_opt_trio = tuple(trios[vv_opt_idx])

    # vec/vec — greedy: site-greedy with vec score and distance constraint
    vv_grd_trio = tuple(greedy_trio(score_vec, D_via))
    vv_grd_score = score_vec[vv_grd_trio[0]] + score_vec[vv_grd_trio[1]] + score_vec[vv_grd_trio[2]]
    vv_opt_score = trio_scores_vec[vv_opt_idx]

    # mm scoring
    score_mm = (X_adj_mm * w).sum(1)
    trio_scores_mm = score_mm[T0] + score_mm[T1] + score_mm[T2]
    vm_opt_trio = tuple(trios[trio_scores_mm.argmax()])
    vm_grd_trio = tuple(greedy_trio(score_mm, D_via))

    records.append({
        'draw': d,
        'vv_opt_trio': str(vv_opt_trio),
        'vv_grd_trio': str(vv_grd_trio),
        'vm_opt_trio': str(vm_opt_trio),
        'vm_grd_trio': str(vm_grd_trio),
        'vv_same': int(vv_opt_trio == vv_grd_trio),
        'vm_same': int(vm_opt_trio == vm_grd_trio),
        'vv_opt_score': float(vv_opt_score),
        'vv_grd_score': float(vv_grd_score),
    })

    if (d + 1) % 50 == 0:
        elapsed = time.time() - t_start
        eta = elapsed / (d + 1) * (N_DRAWS - d - 1)
        print(f"  [{d+1}/{N_DRAWS}]  vv_same={sum(r['vv_same'] for r in records)}/{d+1}"
              f"  vm_same={sum(r['vm_same'] for r in records)}/{d+1}"
              f"  eta={eta:.0f}s", flush=True)

df = pd.DataFrame(records)
out = ROOT / 'results' / 'f8' / 'f8_coincidence.csv'
df.to_csv(out, index=False)
import hashlib
sha = hashlib.sha256(out.read_bytes()).hexdigest()

print(f"\n{'='*60}")
print("F8 TRIO COINCIDENCE RESULTS")
print(f"{'='*60}")
vv_coinc = int(df['vv_same'].sum())
vm_coinc = int(df['vm_same'].sum())
print(f"vec/vec  greedy == optimal: {vv_coinc}/{N_DRAWS}")
print(f"vec/mm   greedy == optimal: {vm_coinc}/{N_DRAWS}")
print()
print(f"Saved: {out}")
print(f"SHA-256: {sha}")
print("DONE")
