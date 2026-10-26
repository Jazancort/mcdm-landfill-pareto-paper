# -*- coding: utf-8 -*-
"""
_diag_f8_c1.py -- diagnose the C1 vec score vs canonical vec score.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pathlib import Path

ROOT = Path(__file__).parent.parent

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, haversine_km, MIN_DIST_KM,
    _build_decision_matrix, F1_CRIT, F2_CRIT, INV as INV_SET, _norm as _mm_norm
)
from scoring import make_scorers

df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL['protected']] > 0].copy()
N = len(df_via)
col_names = list(AHP_WEIGHTS.keys())

D = haversine_km(df_via['latitude (degrees)'].values, df_via['longitude (degrees)'].values)
valid = D >= MIN_DIST_KM
trios_list = [(i,j,k) for i in range(N) for j in range(i+1,N) if valid[i,j]
              for k in range(j+1,N) if valid[i,k] and valid[j,k]]
trios = np.array(trios_list, dtype=np.int32)
T0, T1, T2 = trios[:,0], trios[:,1], trios[:,2]
print("trios:", len(trios))

# Canonical score
X_via_raw, benefit_flags = _build_decision_matrix(df_via)
X_adj = X_via_raw.copy()
for j, b in enumerate(benefit_flags):
    if not b:
        X_adj[:, j] = 1.0 - X_via_raw[:, j]
norms_via = np.array([max(float(np.sqrt((X_via_raw[:,j]**2).sum())), 1e-12)
                      for j in range(len(col_names))])
saw_sc, _ = make_scorers(X_via_raw, X_adj, norms_via, benefit_flags)

def canonical_opt(w):
    sc = saw_sc(w, norm='vector')
    return trios[int(np.argmax(sc[T0]+sc[T1]+sc[T2]))]

# C1 score
f1_set = set(F1_CRIT); f2_set = set(F2_CRIT)
C_vec_raw = np.zeros((N, len(col_names)))
L2_c1 = np.zeros(len(col_names))
for j, k in enumerate(col_names):
    x = df_via[COL[k]].values.astype(float)
    if k == "aspect":
        c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
    else:
        c = _mm_norm(x, x)
    L2_c1[j] = max(float(np.sqrt((c**2).sum())), 1e-12)
    C_vec_raw[:, j] = c / L2_c1[j]

sign_obj = np.array([-1.0 if k in (f1_set|f2_set) else 1.0 for k in col_names])
C_score_vec = np.zeros((N, len(col_names)))
for j, k in enumerate(col_names):
    if k == "aspect":
        x = df_via[COL[k]].values.astype(float)
        C_score_vec[:, j] = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
    elif k in INV_SET:
        C_score_vec[:, j] = 1.0 - C_vec_raw[:, j]
    else:
        C_score_vec[:, j] = C_vec_raw[:, j]

def c1_opt(w):
    sc = (C_score_vec * (w * sign_obj)).sum(axis=1)
    return trios[int(np.argmax(sc[T0]+sc[T1]+sc[T2]))]

# rho_j comparison
print("\nrho_j comparison:")
print(f"  {'crit':12s}  {'rho_can':>10s}  {'rho_C1':>8s}  status")
for j, k in enumerate(col_names):
    rho_can = 1.0/norms_via[j]
    col = C_score_vec[:, j]
    rho_c1 = float(col.max() - col.min())
    status = "OK" if abs(rho_can - rho_c1) < 0.002 else "MISMATCH"
    print(f"  {k:12s}  {rho_can:10.4f}  {rho_c1:8.4f}  {status}")

# Draw-by-draw check
W = np.load(ROOT / "results/e1/e1_weights_k200.npy")
mis = 0
for di, w in enumerate(W):
    tc = canonical_opt(w)
    t1 = c1_opt(w)
    if set(tc) != set(t1):
        mis += 1
        if mis <= 5:
            print(f"  draw {di}: can={sorted(tc)} c1={sorted(t1)}")

print(f"\nMismatches: {mis}/{len(W)}")
if mis == 0:
    print("Portfolios IDENTICAL -> bug is in FRONTIER, not score")
else:
    print("Portfolios DIFFER -> bug is in SCORE")
