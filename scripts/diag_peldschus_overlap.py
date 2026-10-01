# -*- coding: utf-8 -*-
"""
diag_peldschus_overlap.py — Two diagnostics:
  A) Peldschus greedy=99%: is it a tie-breaking artefact?
     - Fraction of draws where greedy == optimal under Peldschus
     - F1 percentile of greedy trios (same as E1-B diagnosis)
     - Sensitivity: perturb min-max scores by 1e-12 -> does Q2 change?
  B) Greedy trio overlap between normalisations (min-max, Peldschus, max, ranks, vector, sum)
     - Jaccard(greedy_i, greedy_j) per draw, averaged over 500 draws
     - Identifies whether greedy is nearly normalisation-invariant on this instance
"""
import os, sys, time
import numpy as np
import pandas as pd

if 'MCDM_DATA_DIR' not in os.environ and os.path.exists('/home/julioazancort/scratch/mcdm'):
    os.environ['MCDM_DATA_DIR'] = '/home/julioazancort/scratch/mcdm'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcdm_experiment import (
    load_data, impute_nan, haversine_km,
    greedy_trio, COL, AHP_WEIGHTS, MIN_DIST_KM,
    _build_decision_matrix, _norm, INV, COST,
    F1_CRIT, F2_CRIT, F3_CRIT,
)

EPS     = 1e-9
N_DRAWS = 500
KAPPA   = 200
SEED    = 42

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable = df_imp[COL["protected"]] > 0
df_via = df_imp[viable].copy()
N = len(df_via)
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
M = len(w_ahp)

X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b: X_adj[:, j] = 1.0 - X_via[:, j]

X_raw = np.zeros((N, M), dtype=np.float64)
for j, k in enumerate(col_names):
    vals = df_via[COL[k]].values.astype(np.float64)
    if k == 'aspect':
        X_raw[:, j] = np.where((vals >= 90) & (vals <= 180), 1.0, 0.0)
    else:
        X_raw[:, j] = vals

# ── Build trios and lookup ─────────────────────────────────────────────────────
valid = D_via >= MIN_DIST_KM
trio_list = []
for i in range(N):
    for j2 in range(i+1, N):
        if not valid[i, j2]: continue
        for k in range(j2+1, N):
            if not valid[i, k] or not valid[j2, k]: continue
            trio_list.append((i, j2, k))
trio_arr = np.array(trio_list, dtype=np.int32)
T0, T1, T2 = trio_arr[:,0], trio_arr[:,1], trio_arr[:,2]
print(f"Trios: {len(trio_arr):,}")

trio_lookup = {(int(T0[i]),int(T1[i]),int(T2[i])): i for i in range(len(trio_arr))}

# ── Normalisations ─────────────────────────────────────────────────────────────
norms_via = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)
X_mm  = X_adj.copy()
norms_raw = np.maximum(np.sqrt((X_raw**2).sum(0)), 1e-12)
A_max = (X_raw.max(0)-X_raw.min(0)) / np.maximum(X_raw.max(0), 1e-12)
X_max = X_adj * A_max
X_ranks = np.apply_along_axis(
    lambda c: pd.Series(c).rank(method="average").values / (N+1), 0, X_adj)
X_vec = X_adj / norms_via
sums_raw = np.maximum(X_raw.sum(0), 1e-12)
A_sum = (X_raw.max(0)-X_raw.min(0)) / sums_raw
X_sum = X_adj * A_sum
X_peld = np.zeros_like(X_raw)
for j in range(M):
    x = X_raw[:,j]; mx = x.max()
    if benefit[j]:
        X_peld[:,j] = (x/mx)**2 if mx > 0 else 0.
    else:
        X_peld[:,j] = ((mx-x)/mx)**2 if mx > 0 else 0.

NORMS = {
    "min-max": X_mm, "Peldschus": X_peld, "max": X_max,
    "ranks": X_ranks, "vector": X_vec, "sum": X_sum,
}

# Min-max perturbed (test tie-breaking)
rng_pert = np.random.default_rng(999)
X_mm_pert = X_mm + rng_pert.uniform(-1e-12, 1e-12, size=X_mm.shape)

# ── Objectives (float64) ──────────────────────────────────────────────────────
def compute_objs_f64(w):
    f1v = np.zeros(N, dtype=np.float64)
    f2v = np.zeros(N, dtype=np.float64)
    f3v = np.zeros(N, dtype=np.float64)
    for j, k in enumerate(col_names):
        x = df_via[COL[k]].values.astype(np.float64); ref = x
        if k == "aspect":    c = np.where((x>=90)&(x<=180), 0., 1.)
        elif k in INV:       c = 1. - _norm(x, ref)
        elif k in COST:      c = _norm(x, ref)
        else:                c = _norm(x, ref)
        c = c * float(w[j])
        if k in F1_CRIT:     f1v += c
        elif k in F2_CRIT:   f2v += c
        else:                f3v += c
    return f1v, f2v, f3v

def is_dominated_sorted(trio_tuple, F1, F2, F3, eps=EPS):
    key = tuple(sorted(trio_tuple))
    idx = trio_lookup.get(key, -1)
    if idx < 0: return False
    f1t, f2t, f3t = float(F1[idx]), float(F2[idx]), float(F3[idx])
    mask = np.ones(len(F1), dtype=bool); mask[idx] = False
    F1m, F2m, F3m = F1[mask], F2[mask], F3[mask]
    weak   = (F1m<=f1t+eps) & (F2m<=f2t+eps) & (F3m>=f3t-eps)
    strict = (F1m< f1t-eps) | (F2m< f2t-eps) | (F3m> f3t+eps)
    return bool((weak & strict).any())

def argmax_trio_arr(sc):
    st = sc[T0]+sc[T1]+sc[T2]; return trio_arr[st.argmax()]

# ── Monte Carlo ───────────────────────────────────────────────────────────────
rng = np.random.default_rng(SEED)
draws = rng.dirichlet(KAPPA * w_ahp, size=N_DRAWS)

# Storage: greedy trio per norm per draw (as sorted tuple), nd flags
greedy_trios = {nm: [] for nm in list(NORMS.keys()) + ["mm_pert"]}
nd_flags     = {nm: [] for nm in list(NORMS.keys()) + ["mm_pert"]}
peld_eq_opt  = []     # Peldschus: greedy == optimal?
peld_f1_pctile = []   # Peldschus: F1 percentile of greedy

t0 = time.time()
for draw_idx, w in enumerate(draws):
    f1v, f2v, f3v = compute_objs_f64(w)
    F1 = f1v[T0]+f1v[T1]+f1v[T2]
    F2 = f2v[T0]+f2v[T1]+f2v[T2]
    F3 = f3v[T0]+f3v[T1]+f3v[T2]

    for nm, V in list(NORMS.items()) + [("mm_pert", X_mm_pert)]:
        sc = (V * w).sum(1)
        trio_g = greedy_trio(sc, D_via)
        key    = tuple(sorted(trio_g))
        greedy_trios[nm].append(key)
        nd = not is_dominated_sorted(trio_g, F1, F2, F3)
        nd_flags[nm].append(int(nd))

    # Peldschus extra
    sc_p = (X_peld * w).sum(1)
    trio_g_p = greedy_trio(sc_p, D_via)
    trio_o_p = tuple(argmax_trio_arr(sc_p))
    peld_eq_opt.append(int(tuple(sorted(trio_g_p)) == trio_o_p))

    key_p = tuple(sorted(trio_g_p))
    idx_p = trio_lookup.get(key_p, -1)
    if idx_p >= 0:
        peld_f1_pctile.append(float(np.mean(F1 <= F1[idx_p])))
    else:
        peld_f1_pctile.append(float('nan'))

    if (draw_idx+1) % 100 == 0:
        print(f"  [{draw_idx+1}/{N_DRAWS}]  {time.time()-t0:.0f}s")

print()

# ── A) Peldschus diagnosis ────────────────────────────────────────────────────
print("="*70)
print("A) PELDSCHUS greedy=99% DIAGNOSIS")
print("="*70)

q2_peld = np.mean(nd_flags["Peldschus"])*100
q2_mm   = np.mean(nd_flags["min-max"])*100
q2_mm_pert = np.mean(nd_flags["mm_pert"])*100
eq_opt  = np.mean(peld_eq_opt)*100
f1_med  = np.nanmedian(peld_f1_pctile)*100

print(f"Peldschus greedy Q2   = {q2_peld:.2f}%")
print(f"min-max   greedy Q2   = {q2_mm:.2f}%")
print(f"min-max pert (1e-12)  = {q2_mm_pert:.2f}%  (tie-break test)")
print(f"  -> If mm_pert != mm: tie-breaking in min-max is suppressing Q2")
print(f"     diff = {q2_mm_pert-q2_mm:+.2f}pp")
print(f"Peldschus: greedy==optimal fraction = {eq_opt:.1f}%")
print(f"Peldschus: median F1 percentile of greedy = {f1_med:.1f}%")
print()
if abs(q2_mm_pert - q2_mm) > 1.0:
    print("CONCLUSION: min-max Q2 is sensitive to tie-breaking (diff > 1pp).")
    print("  Peldschus breaks ties differently -> higher Q2 is a tie-break artefact.")
else:
    print("CONCLUSION: min-max Q2 invariant to perturbation -> NOT a tie-break artefact.")

# ── B) Greedy overlap between normalisations ──────────────────────────────────
print()
print("="*70)
print("B) GREEDY TRIO OVERLAP BETWEEN NORMALISATIONS (Jaccard, 500 draws)")
print("="*70)

nms = list(NORMS.keys())
# Jaccard: |A ∩ B| / |A ∪ B| for two sets of 3 sites
def jaccard_trios(t1, t2):
    s1, s2 = set(t1), set(t2)
    return len(s1 & s2) / len(s1 | s2)

overlap = np.zeros((len(nms), len(nms)))
for draw_idx in range(N_DRAWS):
    for i, ni in enumerate(nms):
        for j, nj in enumerate(nms):
            overlap[i, j] += jaccard_trios(
                greedy_trios[ni][draw_idx],
                greedy_trios[nj][draw_idx]
            )
overlap /= N_DRAWS

# Same trio exactly (Jaccard=1)
same = overlap == 1.0  # diagonal always 1

print(f"{'':>14s}", end="")
for nm in nms: print(f"  {nm[:7]:>7s}", end="")
print()
print("-" * (14 + 9*len(nms)))
for i, ni in enumerate(nms):
    print(f"  {ni:12s}", end="")
    for j, nj in enumerate(nms):
        print(f"  {overlap[i,j]:7.3f}", end="")
    print()

# Exact same trio
print("\nFraction of draws with IDENTICAL greedy trio:")
for i, ni in enumerate(nms):
    for j, nj in enumerate(nms):
        if j > i:
            exact = np.mean([1 if greedy_trios[ni][d]==greedy_trios[nj][d] else 0
                             for d in range(N_DRAWS)])*100
            if exact > 50:
                print(f"  {ni} vs {nj}: {exact:.1f}% identical")

print("\nDone.")
