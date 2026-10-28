# -*- coding: utf-8 -*-
"""
check_self_dom.py — Test for self-dominance bug in float32 greedy pipeline.

Hypothesis: greedy is marked dominated only by itself because greedy_trio
returns indices in selection order (not sorted), while the frontier array
uses sorted indices. In float32, summing the same three values in different
order can differ by 1 ULP, causing the trio to dominate itself.

Test: for each draw, check if the ONLY dominator of the greedy trio is
the greedy trio itself (using its sorted-index entry in the frontier).

Expected count:
  min-max greedy: ~101 draws  (86.0 - 65.8 = 20.2pp * 500 = 101)
  vector  greedy: ~61  draws  (66.2 - 54.0 = 12.2pp * 500 = 61)
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
    if not b:
        X_adj[:, j] = 1.0 - X_via[:, j]

norms_via = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)
X_mm  = X_adj.copy()
X_vec = X_adj / norms_via

# Build trios
t0 = time.time()
valid = D_via >= MIN_DIST_KM
trio_list = []
for i in range(N):
    for j2 in range(i + 1, N):
        if not valid[i, j2]: continue
        for k in range(j2 + 1, N):
            if not valid[i, k] or not valid[j2, k]: continue
            trio_list.append((i, j2, k))
trio_arr = np.array(trio_list, dtype=np.int32)
T0, T1, T2 = trio_arr[:, 0], trio_arr[:, 1], trio_arr[:, 2]
assert len(trio_arr) == 1944653
print(f"Trios: {len(trio_arr):,} ({time.time()-t0:.1f}s)")

# Build lookup: sorted tuple -> index in trio_arr
print("Building trio lookup...", end=" ", flush=True)
trio_lookup = {(int(T0[i]),int(T1[i]),int(T2[i])): i for i in range(len(trio_arr))}
print("done")

# Group indices
G1 = [col_names.index(c) for c in F1_CRIT]
G2 = [col_names.index(c) for c in F2_CRIT]
G3 = [col_names.index(c) for c in F3_CRIT]

# compute_objs_Ap in float32 (ORIGINAL wp3_mc.py behaviour)
def compute_objs_f32(w):
    f1v = np.zeros(N, dtype=np.float32)
    f2v = np.zeros(N, dtype=np.float32)
    f3v = np.zeros(N, dtype=np.float32)
    for j, k in enumerate(col_names):
        col = COL[k]
        x   = df_via[col].values.astype(float)
        ref = df_via[col].values.astype(float)
        if k == "aspect":
            c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
        elif k in INV:
            c = 1.0 - _norm(x, ref)
        elif k in COST:
            c = _norm(x, ref)
        else:
            c = _norm(x, ref)
        c = c.astype(np.float32) * float(w[j])
        if k in F1_CRIT: f1v += c
        elif k in F2_CRIT: f2v += c
        else: f3v += c
    return f1v, f2v, f3v

rng = np.random.default_rng(SEED)
draws = rng.dirichlet(KAPPA * w_ahp, size=N_DRAWS)

print("\n" + "="*70)
print("Self-dominance test (float32 pipeline, original wp3_mc.py behaviour)")
print("="*70)

for nm, V in [("min-max", X_mm), ("vector", X_vec)]:
    nd_f32 = 0           # not-dominated in float32 (original)
    self_dom = 0         # dominated ONLY by itself
    other_dom = 0        # dominated by at least one other trio
    both = 0             # dominated by itself AND others

    for draw_idx, w in enumerate(draws):
        f1v, f2v, f3v = compute_objs_f32(w)
        F1 = (f1v[T0]+f1v[T1]+f1v[T2]).astype(np.float64)
        F2 = (f2v[T0]+f2v[T1]+f2v[T2]).astype(np.float64)
        F3 = (f3v[T0]+f3v[T1]+f3v[T2]).astype(np.float64)

        sc = (V * w).sum(1)
        ig, jg, kg = greedy_trio(sc, D_via)

        # Objectives via site indices directly (original order — NOT sorted)
        f1g_unsorted = float(f1v[ig] + f1v[jg] + f1v[kg])
        f2g_unsorted = float(f2v[ig] + f2v[jg] + f2v[kg])
        f3g_unsorted = float(f3v[ig] + f3v[jg] + f3v[kg])

        # Original dominance test (float32 frontier, no eps)
        dom_mask = ((F1 <= f1g_unsorted) & (F2 <= f2g_unsorted) & (F3 >= f3g_unsorted) &
                    ((F1 < f1g_unsorted) | (F2 < f2g_unsorted) | (F3 > f3g_unsorted)))

        n_dominators = int(dom_mask.sum())
        if n_dominators == 0:
            nd_f32 += 1
            continue

        # Find the greedy trio's own index in the sorted array
        key = tuple(sorted([ig, jg, kg]))
        self_idx = trio_lookup.get(key, -1)

        if self_idx < 0:
            other_dom += 1
            continue

        # Is the greedy trio itself a dominator?
        is_self = bool(dom_mask[self_idx])
        # Are there OTHER dominators besides self?
        dom_mask_no_self = dom_mask.copy()
        if self_idx >= 0:
            dom_mask_no_self[self_idx] = False
        has_other = bool(dom_mask_no_self.any())

        if is_self and not has_other:
            self_dom += 1   # PURE self-dominance: only dominator is itself
        elif is_self and has_other:
            both += 1       # self + other
        else:
            other_dom += 1  # only other dominators

    total_dominated = N_DRAWS - nd_f32
    print(f"\n{nm} greedy (float32 pipeline):")
    print(f"  Not dominated:        {nd_f32:4d} / {N_DRAWS}  = {nd_f32/N_DRAWS*100:.1f}%  (original Q2)")
    print(f"  Total dominated:      {total_dominated:4d}")
    print(f"  Pure self-dominance:  {self_dom:4d}  ({self_dom/N_DRAWS*100:.1f}%)")
    print(f"  Self + other:         {both:4d}  ({both/N_DRAWS*100:.1f}%)")
    print(f"  Other only:           {other_dom:4d}  ({other_dom/N_DRAWS*100:.1f}%)")
    print(f"  Corrected Q2 (no self-dom): {(nd_f32+self_dom)/N_DRAWS*100:.1f}%")
    print(f"  Expected corrected Q2: ~{nd_f32/N_DRAWS*100 + (total_dominated - other_dom - both)/N_DRAWS*100:.0f}%")

print("\nDone.")
