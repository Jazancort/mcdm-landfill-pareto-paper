# -*- coding: utf-8 -*-
"""
diagnose_q2_rates.py  --  Compute exact Q2 rates for mc_2cube vs scoring.py
at kappa=200 and kappa=50, using the same canonical draws (e1_weights_k*.npy).

Output:
  Q2 rates (%) for each scorer at each kappa for SAW/vec greedy and optimal.
  This resolves whether Gate G1 passing at k=200 is an exact match or a
  coincidence within the 0.5% gate tolerance.

Also prints the fraction of draws where:
  (a) both scorers agree (same portfolio)
  (b) both non-dominated (nd=1)
  (c) only scoring.py non-dominated
  (d) only mc_2cube non-dominated
  (e) both dominated (nd=0)
"""
import os, sys, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

if "MCDM_DATA_DIR" not in os.environ:
    for candidate in [
        "/home/julioazancort/scratch/mcdm",
        str(ROOT / "data"),
    ]:
        if os.path.exists(candidate):
            os.environ["MCDM_DATA_DIR"] = candidate
            break

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS,
    haversine_km, MIN_DIST_KM, _build_decision_matrix,
    greedy_trio,
)
from pareto_utils import build_pareto_utils
from scoring import make_scorers

print("Loading data...", flush=True)
df_all, _, _ = load_data()
df_imp  = impute_nan(df_all)
df_via  = df_imp[df_imp[COL["protected"]] > 0].copy()
N       = len(df_via)
assert N == 389

w_ahp     = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
D         = haversine_km(df_via["latitude (degrees)"].values,
                         df_via["longitude (degrees)"].values)
valid     = D >= MIN_DIST_KM
trios     = np.array(
    [(i, j, k)
     for i in range(N) for j in range(i+1, N) if valid[i, j]
     for k in range(j+1, N) if valid[i, k] and valid[j, k]],
    dtype=np.int32,
)
T0, T1, T2 = trios[:,0], trios[:,1], trios[:,2]
print(f"Trios: {len(trios):,}", flush=True)

compute_objs, is_dominated, _ = build_pareto_utils(df_via, col_names, trios)
X_via, benefit = _build_decision_matrix(df_via)
X_adj  = X_via.copy()
for j, b in enumerate(benefit):
    if not b: X_adj[:,j] = 1.0 - X_via[:,j]
norms_via = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)
saw_new, _ = make_scorers(X_via, X_adj, norms_via, benefit)

def saw_old(w, norm="vector"):
    return ((X_via / norms_via) * w).sum(1)

def argmax_trio_fn(sc):
    st = sc[T0] + sc[T1] + sc[T2]
    return tuple(map(int, trios[int(st.argmax())]))

def compute_q2_both(W, kappa):
    n = len(W)
    nd_new_g = nd_new_o = 0
    nd_old_g = nd_old_o = 0
    # contingency for greedy: (new_nd, old_nd) counts
    cont_g = {(0,0): 0, (0,1): 0, (1,0): 0, (1,1): 0}
    cont_o = {(0,0): 0, (0,1): 0, (1,0): 0, (1,1): 0}
    same_g = same_o = 0

    t0 = time.time()
    for d, w in enumerate(W):
        f1, f2, f3 = compute_objs(w)
        F1 = f1[T0]+f1[T1]+f1[T2]
        F2 = f2[T0]+f2[T1]+f2[T2]
        F3 = f3[T0]+f3[T1]+f3[T2]

        sc_new = saw_new(w, "vector")
        sc_old = saw_old(w, "vector")

        # greedy
        t_new_g = tuple(map(int, greedy_trio(sc_new, D)))
        t_old_g = tuple(map(int, greedy_trio(sc_old, D)))
        n1_g = int(not is_dominated(t_new_g, F1, F2, F3))
        n2_g = int(not is_dominated(t_old_g, F1, F2, F3))
        nd_new_g += n1_g
        nd_old_g += n2_g
        cont_g[(n1_g, n2_g)] += 1
        if t_new_g == t_old_g: same_g += 1

        # optimal
        t_new_o = argmax_trio_fn(sc_new)
        t_old_o = argmax_trio_fn(sc_old)
        n1_o = int(not is_dominated(t_new_o, F1, F2, F3))
        n2_o = int(not is_dominated(t_old_o, F1, F2, F3))
        nd_new_o += n1_o
        nd_old_o += n2_o
        cont_o[(n1_o, n2_o)] += 1
        if t_new_o == t_old_o: same_o += 1

        if (d+1) % 100 == 0:
            print(f"  k={kappa} draw {d+1}/{n}  {time.time()-t0:.0f}s", flush=True)

    print()
    print(f"=== k={kappa}: Q2 rates ===")
    print(f"  SAW/vec GREEDY:  scoring.py = {nd_new_g/n*100:.2f}%   mc_2cube = {nd_old_g/n*100:.2f}%   diff = {(nd_new_g-nd_old_g)/n*100:+.2f}pp")
    print(f"  SAW/vec OPTIMAL: scoring.py = {nd_new_o/n*100:.2f}%   mc_2cube = {nd_old_o/n*100:.2f}%   diff = {(nd_new_o-nd_old_o)/n*100:+.2f}pp")
    print()
    print(f"  Greedy  same portfolio: {same_g}/{n}  ({same_g/n*100:.1f}%)")
    print(f"  Optimal same portfolio: {same_o}/{n}  ({same_o/n*100:.1f}%)")
    print()
    print(f"  Greedy  (new_nd, old_nd) contingency:")
    print(f"    both nd=1: {cont_g[(1,1)]:5d}  only scoring.py: {cont_g[(1,0)]:5d}")
    print(f"    only mc_2cube: {cont_g[(0,1)]:5d}  both nd=0: {cont_g[(0,0)]:5d}")
    print(f"  Optimal (new_nd, old_nd) contingency:")
    print(f"    both nd=1: {cont_o[(1,1)]:5d}  only scoring.py: {cont_o[(1,0)]:5d}")
    print(f"    only mc_2cube: {cont_o[(0,1)]:5d}  both nd=0: {cont_o[(0,0)]:5d}")
    return nd_new_g/n*100, nd_new_o/n*100, nd_old_g/n*100, nd_old_o/n*100

# Load weight matrices
W200 = np.load(ROOT / "results" / "e1" / "e1_weights_k200.npy")
W50  = np.load(ROOT / "results" / "e1" / "e1_weights_k50.npy")
print(f"Loaded W200={W200.shape}, W50={W50.shape}", flush=True)

r = {}
r["new_g_200"], r["new_o_200"], r["old_g_200"], r["old_o_200"] = compute_q2_both(W200, 200)
r["new_g_50"],  r["new_o_50"],  r["old_g_50"],  r["old_o_50"]  = compute_q2_both(W50,  50)

print()
print("="*60)
print("FINAL TABLE: Q2 rates for SAW/vec")
print("="*60)
print(f"{'':25}  {'greedy':>8}  {'optimal':>8}")
print(f"{'k=200  scoring.py':25}  {r['new_g_200']:8.2f}  {r['new_o_200']:8.2f}")
print(f"{'k=200  mc_2cube':25}  {r['old_g_200']:8.2f}  {r['old_o_200']:8.2f}")
print(f"{'k=200  diff (new-old) pp':25}  {r['new_g_200']-r['old_g_200']:+8.2f}  {r['new_o_200']-r['old_o_200']:+8.2f}")
print()
print(f"{'k=50   scoring.py':25}  {r['new_g_50']:8.2f}  {r['new_o_50']:8.2f}")
print(f"{'k=50   mc_2cube':25}  {r['old_g_50']:8.2f}  {r['old_o_50']:8.2f}")
print(f"{'k=50   diff (new-old) pp':25}  {r['new_g_50']-r['old_g_50']:+8.2f}  {r['new_o_50']-r['old_o_50']:+8.2f}")
print()
print("Table 5 (from mc_2cube): k=200 SAW/vec greedy=66.2  opt=56.8")
print("                         k=50  SAW/vec greedy=77.0  opt=79.4")
print()
print("Correct values from scoring.py:")
print(f"  k=200 SAW/vec greedy={r['new_g_200']:.1f}%  opt={r['new_o_200']:.1f}%")
print(f"  k=50  SAW/vec greedy={r['new_g_50']:.1f}%   opt={r['new_o_50']:.1f}%")
