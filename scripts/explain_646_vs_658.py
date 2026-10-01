# -*- coding: utf-8 -*-
"""
explain_646_vs_658.py — Identify why mc_2cube_and_4thcell gives 64.6% for
SAW/min-max/greedy while wp3_mc gives 65.8% for the same cell.

Differences between the two scripts (to test one by one):
  D1: mc_2cube uses compute_objs_ref(w, df_imp) — ref=473 sites
      wp3_mc   uses compute_objs_Ap(w)          — ref=389 sites
  D2: mc_2cube SAW vector uses X_via/norms (NOT benefit-adjusted X_adj)
      wp3_mc   uses X_adj/norms (benefit-adjusted)
  D3: mc_2cube uses KAPPA from ALPHAS=[50,200] but checks only alpha=200
      wp3_mc   uses single KAPPA=200 — same
  D4: mc_2cube computes F1/F2/F3 arrays per-draw using compute_objs_ref
      wp3_mc   does the same with compute_objs_Ap — ref difference (D1)

For SAW/min-max specifically, score is (X_adj * w).sum(1) in both — identical.
The only candidate is D1: reference for objectives (473 vs 389).
"""
import os, sys
import numpy as np

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
trio_lookup = {(int(T0[i]),int(T1[i]),int(T2[i])): i for i in range(len(trio_arr))}

def compute_objs(w, ref_df):
    """Generalised: ref_df can be df_via (389) or df_imp (473)."""
    f1v = np.zeros(N, dtype=np.float64)
    f2v = np.zeros(N, dtype=np.float64)
    f3v = np.zeros(N, dtype=np.float64)
    for j, k in enumerate(col_names):
        x   = df_via[COL[k]].values.astype(np.float64)
        ref = ref_df[COL[k]].values.astype(np.float64)
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
    F1m,F2m,F3m = F1[mask],F2[mask],F3[mask]
    weak   = (F1m<=f1t+eps)&(F2m<=f2t+eps)&(F3m>=f3t-eps)
    strict = (F1m< f1t-eps)|(F2m< f2t-eps)|(F3m> f3t+eps)
    return bool((weak&strict).any())

rng = np.random.default_rng(SEED)
draws = rng.dirichlet(KAPPA * w_ahp, size=N_DRAWS)

nd_ref389 = 0   # wp3_mc style: ref=389
nd_ref473 = 0   # mc_2cube style: ref=473
nd_agree  = 0   # both agree on same result

for w in draws:
    f1_389, f2_389, f3_389 = compute_objs(w, df_via)   # ref=389
    f1_473, f2_473, f3_473 = compute_objs(w, df_imp)   # ref=473

    F1_389 = f1_389[T0]+f1_389[T1]+f1_389[T2]
    F2_389 = f2_389[T0]+f2_389[T1]+f2_389[T2]
    F3_389 = f3_389[T0]+f3_389[T1]+f3_389[T2]

    F1_473 = f1_473[T0]+f1_473[T1]+f1_473[T2]
    F2_473 = f2_473[T0]+f2_473[T1]+f2_473[T2]
    F3_473 = f3_473[T0]+f3_473[T1]+f3_473[T2]

    sc = (X_adj * w).sum(1)
    trio_g = greedy_trio(sc, D_via)

    r389 = int(not is_dominated_sorted(trio_g, F1_389, F2_389, F3_389))
    r473 = int(not is_dominated_sorted(trio_g, F1_473, F2_473, F3_473))

    nd_ref389 += r389
    nd_ref473 += r473
    if r389 == r473: nd_agree += 1

print("="*60)
print("SAW/min-max/greedy: ref=389 vs ref=473")
print("="*60)
print(f"ref=389 (wp3_mc style):      {nd_ref389/N_DRAWS*100:.2f}%  (should match 86.0%)")
print(f"ref=473 (mc_2cube style):    {nd_ref473/N_DRAWS*100:.2f}%  (should match ~64.6%)")
print(f"Agreement between the two:   {nd_agree/N_DRAWS*100:.1f}%")
print()
diff = nd_ref389/N_DRAWS*100 - nd_ref473/N_DRAWS*100
print(f"Difference: {diff:+.2f}pp")
if abs(diff) > 1.0:
    print("CONCLUSION: The 64.6 vs 65.8 discrepancy is explained by the")
    print("  reference set for objectives (473 vs 389 sites).")
    print("  The CORRECT estimand for space A' is ref=389.")
    print("  mc_2cube uses ref=473 — it measures dominance in the WRONG space.")
else:
    print("CONCLUSION: Reference set (389 vs 473) does NOT explain the discrepancy.")
    print("  Another cause must be identified.")
print("\nDone.")
