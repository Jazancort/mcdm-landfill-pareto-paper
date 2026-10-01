# -*- coding: utf-8 -*-
"""
mc_2cube_fixed.py — mc_2cube_and_4thcell.py with three corrections:
  1. compute_objs_ref upgraded to float64 (was float32)
  2. is_nd_fn replaced by is_dominated from pareto_utils (sorted-idx + eps)
  3. All objectives for space A' use ref=df_via (389), never ref=df_imp (473)

Bug documented in explain_646_vs_658.py:
  mc_2cube used ref=473 for A' objectives: 58.8% vs correct 86.0% for mm/greedy.
  The tab:factorial values (64.6%, 54.2%) were from an older run that also had
  the self-dominance bug — combined effect produced values far from the truth.

All output structure is IDENTICAL to mc_2cube_and_4thcell.py.
The "fourth cell" (ref=473 method, A' evaluator) is now correctly computed
with per-draw objectives using ref=df_via.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

from mcdm_experiment import (
    load_data, impute_nan,
    haversine_km, greedy_trio, COL, AHP_WEIGHTS, MIN_DIST_KM,
    _build_decision_matrix, COST, _norm, INV,
    F1_CRIT, F2_CRIT, F3_CRIT,
)
from pareto_utils import build_pareto_utils

if 'MCDM_DATA_DIR' not in os.environ and os.path.exists('/home/julioazancort/scratch/mcdm'):
    os.environ['MCDM_DATA_DIR'] = '/home/julioazancort/scratch/mcdm'

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

EPS     = 1e-9
N_DRAWS = 500
SEED    = 42
ALPHAS  = [50, 200]

print("=" * 70)
print("mc_2cube_fixed: float64 + sorted-idx + ref=389 for all A' objectives")
print("=" * 70)

# ── Data ───────────────────────────────────────────────────────────────────────
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
N = len(df_via)
assert N == 389
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
M = len(w_ahp)

X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j2, b in enumerate(benefit):
    if not b: X_adj[:, j2] = 1.0 - X_via[:, j2]

# ── Trios ─────────────────────────────────────────────────────────────────────
t0 = time.time()
valid = D_via >= MIN_DIST_KM
trio_list = []
for i in range(N):
    for j in range(i+1, N):
        if not valid[i, j]: continue
        for k in range(j+1, N):
            if not valid[i, k] or not valid[j, k]: continue
            trio_list.append((i, j, k))
trio_arr = np.array(trio_list, dtype=np.int32)
T0, T1, T2 = trio_arr[:,0], trio_arr[:,1], trio_arr[:,2]
assert len(trio_arr) == 1944653
print(f"Trios: {len(trio_arr):,} ({time.time()-t0:.1f}s)")

# ── Pareto utilities (shared, from pareto_utils.py) ───────────────────────────
compute_objs_f64, is_dominated, trio_lookup = build_pareto_utils(
    df_via, col_names, trio_arr, eps=EPS
)

# ── Score functions (identical to mc_2cube_and_4thcell.py) ────────────────────
norms_via = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)

def saw_sc(w, norm="minmax"):
    if norm == "minmax":
        return (X_adj * w).sum(1)
    else:  # vector: X_adj/norms (benefit-adjusted), consistent with wp3_mc_fixed
        return ((X_adj / norms_via) * w).sum(1)

def topsis_sc(w, norm="minmax"):
    Xb = X_via if norm == "minmax" else X_via / norms_via
    V  = Xb * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp  = np.sqrt(((V - PIS)**2).sum(1))
    dn  = np.sqrt(((V - NIS)**2).sum(1))
    return np.where(dp + dn == 0, 0.5, dn / (dp + dn))

def argmax_trio_fn(sc):
    st = sc[T0] + sc[T1] + sc[T2]
    return trio_arr[st.argmax()]

# Score with 473-site normalisation (for fourth cell)
def build_score_473(w, agg="saw"):
    Xb473 = np.zeros((N, M), dtype=np.float64)
    for jj, crit in enumerate(col_names):
        col = COL[crit]
        x_via = df_via[col].values.astype(float)
        x_all = df_imp[col].values.astype(float)
        mn, mx = x_all.min(), x_all.max(); rng_c = mx - mn or 1.0
        Xb473[:, jj] = (x_via - mn) / rng_c
    Xadj473 = Xb473.copy()
    for jj, b in enumerate(benefit):
        if not b: Xadj473[:, jj] = 1.0 - Xb473[:, jj]
    if agg == "saw":
        return (Xadj473 * w).sum(1)
    else:
        V   = Xb473 * w
        PIS = np.where(benefit, V.max(0), V.min(0))
        NIS = np.where(benefit, V.min(0), V.max(0))
        dp  = np.sqrt(((V - PIS)**2).sum(1))
        dn  = np.sqrt(((V - NIS)**2).sum(1))
        return np.where(dp + dn == 0, 0.5, dn / (dp + dn))

# ── Cells ─────────────────────────────────────────────────────────────────────
CELLS_CUBE = [(agg, norm, mont)
              for agg  in ["saw", "topsis"]
              for norm in ["minmax", "vector"]
              for mont in ["greedy", "optimal"]]

CELLS_4TH = [("saw",    "minmax", "greedy"),
             ("saw",    "minmax", "optimal"),
             ("topsis", "minmax", "greedy"),
             ("topsis", "minmax", "optimal")]

print(f"Cells: {len(CELLS_CUBE)} cube + {len(CELLS_4TH)} fourth")
print(f"Draws: {N_DRAWS} × {len(ALPHAS)} alphas")

# ── Monte Carlo ────────────────────────────────────────────────────────────────
records   = []
records_4 = []
t_start   = time.time()

for alpha in ALPHAS:
    print(f"\n  alpha={alpha}")
    rng = np.random.default_rng(SEED)

    for draw in range(N_DRAWS):
        w = rng.dirichlet(alpha * w_ahp)

        # FIX: objectives for space A' always use ref=df_via (389 sites)
        f1v, f2v, f3v = compute_objs_f64(w)
        F1 = f1v[T0] + f1v[T1] + f1v[T2]
        F2 = f2v[T0] + f2v[T1] + f2v[T2]
        F3 = f3v[T0] + f3v[T1] + f3v[T2]

        for agg, norm, mont in CELLS_CUBE:
            sc = saw_sc(w, norm) if agg == "saw" else topsis_sc(w, norm)
            idx = greedy_trio(sc, D_via) if mont == "greedy" else argmax_trio_fn(sc)

            # Only Q2[A'] reported (single estimand, space A', ref=389)
            nd_Q2Ap = int(not is_dominated(idx, F1, F2, F3))

            records.append({
                "alpha": alpha, "draw": draw,
                "agg": agg, "norm": norm, "mont": mont,
                "nd_Q2Ap": nd_Q2Ap,
            })

        for agg_4, norm_4, mont_4 in CELLS_4TH:
            sc4 = build_score_473(w, agg=agg_4)
            idx4 = greedy_trio(sc4, D_via) if mont_4 == "greedy" else argmax_trio_fn(sc4)

            # FIX: evaluator is always A' with ref=389 (was ref=473)
            nd_Q2Ap4 = int(not is_dominated(idx4, F1, F2, F3))

            records_4.append({
                "alpha": alpha, "draw": draw,
                "agg": agg_4, "norm": norm_4, "mont": mont_4,
                "ref_method": 473, "nd_Q2Ap": nd_Q2Ap4,
            })

        if (draw + 1) % 100 == 0:
            elapsed = time.time() - t_start
            print(f"    [{draw+1}/{N_DRAWS}]  {elapsed:.0f}s")

df_cube = pd.DataFrame(records)
df_4th  = pd.DataFrame(records_4)
df_cube.to_csv(os.path.join(RESULTS_DIR, "mc_2cube_fixed_raw.csv"),    index=False)
df_4th.to_csv( os.path.join(RESULTS_DIR, "mc_4thcell_fixed_raw.csv"), index=False)

# ── Summary table (alpha=200) ──────────────────────────────────────────────────
print("\n" + "="*70)
print("2³ balanceado — Q2[A'], α=200 (FIXED: float64, sorted-idx, ref=389)")
print("="*70)
df200 = df_cube[df_cube.alpha == 200]
tbl = df200.groupby(["agg", "norm", "mont"]).agg(
    Q2Ap=("nd_Q2Ap", lambda x: 100*x.mean())
).reset_index()
print(tbl.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

print("\n" + "="*70)
print("Quarta casa — Q2[A'], α=200 (FIXED: ref=389 evaluator)")
print("="*70)
df200_4 = df_4th[df_4th.alpha == 200]
tbl4 = df200_4.groupby(["agg", "norm", "mont"]).agg(
    Q2Ap=("nd_Q2Ap", lambda x: 100*x.mean())
).reset_index()
print(tbl4.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

print(f"\nTotal time: {(time.time()-t_start)/60:.1f} min")
print("Done.")
