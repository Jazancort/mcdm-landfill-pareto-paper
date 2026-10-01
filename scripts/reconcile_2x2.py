# -*- coding: utf-8 -*-
"""
reconcile_2x2.py — Reproduce exactly 64.6% and 100.0% from the old mc_2cube.

Grid: {ref=389, ref=473} × {float32 no-eps, float64 eps=1e-9}
Cell: SAW/min-max/greedy and SAW/min-max/optimal, alpha=200, N=500, seed=42.

Expected:
  Old mc_2cube (ref=473, float32): SAW/mm/greedy=64.6%, optimal=100.0%
  wp3_mc_fixed (ref=389, float64): SAW/mm/greedy=86.0%, optimal=100.0%
  explain_646 (ref=473, float64):  SAW/mm/greedy=58.8%, optimal=?

The question: can we reproduce 64.6% exactly? Which combination produces it?
"""
import os, sys, time
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
from pareto_utils import build_pareto_utils

EPS = 1e-9
N_DRAWS = 500
KAPPA   = 200
SEED    = 42

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable = df_imp[COL["protected"]] > 0
df_via = df_imp[viable].copy()
N = len(df_via)
assert N == 389
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
M = len(w_ahp)

X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b: X_adj[:, j] = 1.0 - X_via[:, j]

# SAW/min-max score (same for all variants)
# Score = (X_adj * w).sum(1) — identical regardless of ref

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
assert len(trio_arr) == 1944653

trio_lookup = {(int(T0[i]),int(T1[i]),int(T2[i])): i for i in range(len(trio_arr))}

rng = np.random.default_rng(SEED)
draws = rng.dirichlet(KAPPA * w_ahp, size=N_DRAWS)

def argmax_trio(sc):
    st = sc[T0]+sc[T1]+sc[T2]; return trio_arr[st.argmax()]

# ── Objective builders ────────────────────────────────────────────────────────
def build_objs(ref_df, dtype):
    """Build per-draw objectives. dtype=np.float32 or np.float64."""
    def compute(w):
        f1v = np.zeros(N, dtype=dtype)
        f2v = np.zeros(N, dtype=dtype)
        f3v = np.zeros(N, dtype=dtype)
        for j, k in enumerate(col_names):
            x   = df_via[COL[k]].values.astype(float)
            ref = ref_df[COL[k]].values.astype(float)
            if k == "aspect":  c = np.where((x>=90)&(x<=180), 0., 1.)
            elif k in INV:     c = 1. - _norm(x, ref)
            elif k in COST:    c = _norm(x, ref)
            else:              c = _norm(x, ref)
            c = (c * float(w[j])).astype(dtype)
            if k in F1_CRIT:   f1v += c
            elif k in F2_CRIT: f2v += c
            else:              f3v += c
        return f1v, f2v, f3v
    return compute

def dom_strict(f1t, f2t, f3t, F1, F2, F3):
    """No tolerance (original mc_2cube behaviour)."""
    return bool(((F1<=f1t)&(F2<=f2t)&(F3>=f3t)&((F1<f1t)|(F2<f2t)|(F3>f3t))).any())

def dom_eps(f1t, f2t, f3t, F1, F2, F3, eps=EPS):
    """With tolerance, excluding self via sorted-idx."""
    # For this test, we use the simple version without self-exclusion
    # to match the original script's behaviour more closely
    weak   = (F1<=f1t+eps)&(F2<=f2t+eps)&(F3>=f3t-eps)
    strict = (F1< f1t-eps)|(F2< f2t-eps)|(F3> f3t+eps)
    return bool((weak&strict).any())

def dom_eps_noself(f1t, f2t, f3t, F1, F2, F3, trio_tuple, eps=EPS):
    """With tolerance + self-exclusion (pareto_utils behaviour)."""
    key = tuple(sorted(trio_tuple))
    idx = trio_lookup.get(key, -1)
    if idx < 0: return dom_eps(f1t, f2t, f3t, F1, F2, F3, eps)
    f1t2, f2t2, f3t2 = float(F1[idx]), float(F2[idx]), float(F3[idx])
    mask = np.ones(len(F1), dtype=bool); mask[idx] = False
    weak   = (F1[mask]<=f1t2+eps)&(F2[mask]<=f2t2+eps)&(F3[mask]>=f3t2-eps)
    strict = (F1[mask]< f1t2-eps)|(F2[mask]< f2t2-eps)|(F3[mask]> f3t2+eps)
    return bool((weak&strict).any())

# ── Four variants ─────────────────────────────────────────────────────────────
variants = [
    ("ref=389, f32, strict",  build_objs(df_via,  np.float32), dom_strict,     False),
    ("ref=473, f32, strict",  build_objs(df_imp,  np.float32), dom_strict,     False),
    ("ref=389, f64, eps+nself", build_objs(df_via, np.float64), dom_eps_noself, True),
    ("ref=473, f64, eps",     build_objs(df_imp,  np.float64), dom_eps,        False),
]

print("="*75)
print("Reconciliation: {ref} × {dtype/eps} — SAW/min-max, alpha=200, N=500, seed=42")
print(f"{'Variant':<32} {'Greedy':>8} {'Optimal':>8}  Target comparison")
print("-"*75)

for label, compute_fn, dom_fn, use_noself in variants:
    nd_g = 0; nd_o = 0
    for w in draws:
        f1v, f2v, f3v = compute_fn(w)
        F1 = (f1v[T0]+f1v[T1]+f1v[T2]).astype(np.float64)
        F2 = (f2v[T0]+f2v[T1]+f2v[T2]).astype(np.float64)
        F3 = (f3v[T0]+f3v[T1]+f3v[T2]).astype(np.float64)
        sc = (X_adj * w).sum(1)

        # Greedy
        trio_g = greedy_trio(sc, D_via)
        ig, jg, kg = trio_g
        f1t = float(f1v[ig]+f1v[jg]+f1v[kg])
        f2t = float(f2v[ig]+f2v[jg]+f2v[kg])
        f3t = float(f3v[ig]+f3v[jg]+f3v[kg])
        if use_noself:
            dom = dom_fn(f1t, f2t, f3t, F1, F2, F3, trio_g)
        else:
            dom = dom_fn(f1t, f2t, f3t, F1, F2, F3)
        if not dom: nd_g += 1

        # Optimal
        trio_o = tuple(argmax_trio(sc))
        ti, tj, tk = trio_o
        f1o = float(f1v[ti]+f1v[tj]+f1v[tk])
        f2o = float(f2v[ti]+f2v[tj]+f2v[tk])
        f3o = float(f3v[ti]+f3v[tj]+f3v[tk])
        if use_noself:
            dom_o = dom_fn(f1o, f2o, f3o, F1, F2, F3, trio_o)
        else:
            dom_o = dom_fn(f1o, f2o, f3o, F1, F2, F3)
        if not dom_o: nd_o += 1

    q2g = nd_g/N_DRAWS*100
    q2o = nd_o/N_DRAWS*100
    target = ""
    if "ref=389" in label and "f32" in label: target = "<- should match wp3_mc old (65.8%) or factorial old?"
    if "ref=473" in label and "f32" in label: target = "<- target: 64.6% / 100.0% (old mc_2cube)"
    if "ref=389" in label and "f64" in label: target = "<- should match 86.0% / 100.0%"
    if "ref=473" in label and "f64" in label: target = "<- should match 58.8% / ? (explain_646)"
    print(f"  {label:<32} {q2g:>7.2f}% {q2o:>7.2f}%  {target}")

print()
print("If ref=473/f32/strict gives 64.6%/100.0%, the explanation is:")
print("  mc_2cube used ref=473 for objectives AND float32 AND no-eps")
print("  The score (X_adj * w) uses 389-site normalisation regardless of ref")
print("  SAW/mm/optimal=100% is possible with ref=473 if the SAW argmax")
print("  happens to always be on the 473-ref frontier")
