# -*- coding: utf-8 -*-
"""
wp3_mc_fixed.py — wp3_mc.py with three corrections:
  1. compute_objs_Ap upgraded to float64 (was float32)
  2. Trio objectives taken from F1[sorted_idx] (prevents self-dominance)
  3. Dominance test uses eps=1e-9 (was strict ==)
  4. Sensitivity analysis: eps in {0, 1e-12, 1e-9, 1e-6}

Bug documented in:
  - check_self_dom.py: min-max 101/500 pure self-dom, vector 61/500
  - check_float64.py: min-max greedy 65.8%->86.0%, vector 54.0%->66.2%

All other logic is IDENTICAL to wp3_mc.py (same normalisations, same MC params).
"""
import os, sys, time
import numpy as np
import pandas as pd
from scipy import stats

if 'MCDM_DATA_DIR' not in os.environ and os.path.exists('/home/julioazancort/scratch/mcdm'):
    os.environ['MCDM_DATA_DIR'] = '/home/julioazancort/scratch/mcdm'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcdm_experiment import (
    load_data, impute_nan, haversine_km,
    greedy_trio, COL, AHP_WEIGHTS, MIN_DIST_KM,
    _build_decision_matrix, _norm, INV, COST,
)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

EPS     = 1e-9   # dominance tolerance
N_DRAWS = 500
KAPPA   = 200
SEED    = 42

print("=" * 70)
print("WP3 MC Fixed: float64 + sorted-index objectives + eps=1e-9")
print(f"eps={EPS}, kappa={KAPPA}, N={N_DRAWS}, seed={SEED}")
print("=" * 70)

# ── Data (identical to wp3_mc.py) ─────────────────────────────────────────────
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
for j2, b in enumerate(benefit):
    if not b:
        X_adj[:, j2] = 1.0 - X_via[:, j2]

# Raw criteria matrix (for exact amplitudes — identical to wp3_mc.py)
X_raw = np.zeros((N, M), dtype=np.float64)
for j, k in enumerate(col_names):
    col = COL[k]
    vals = df_via[col].values.astype(np.float64)
    if k == 'aspect':
        X_raw[:, j] = np.where((vals >= 90) & (vals <= 180), 1.0, 0.0)
    else:
        X_raw[:, j] = vals

# ── Trios ─────────────────────────────────────────────────────────────────────
t0 = time.time()
valid = D_via >= MIN_DIST_KM
trio_list = []
for i in range(N):
    for j in range(i + 1, N):
        if not valid[i, j]: continue
        for k in range(j + 1, N):
            if not valid[i, k] or not valid[j, k]: continue
            trio_list.append((i, j, k))
trio_arr = np.array(trio_list, dtype=np.int32)
T0, T1, T2 = trio_arr[:, 0], trio_arr[:, 1], trio_arr[:, 2]
assert len(trio_arr) == 1944653
print(f"Viable trios: {len(trio_arr):,} ({time.time()-t0:.1f}s)")

# ── FIX 1: Sorted-index lookup (prevents self-dominance) ─────────────────────
# greedy_trio returns indices in selection order; trio_arr has them sorted.
# Using the sorted index avoids float rounding differences when summing.
print("Building sorted trio lookup...", end=" ", flush=True)
trio_lookup = {(int(T0[i]), int(T1[i]), int(T2[i])): i for i in range(len(trio_arr))}
print("done")

# ── Normalisations (identical to wp3_mc.py) ───────────────────────────────────
X_ranks = np.apply_along_axis(
    lambda c: pd.Series(c).rank(method="average").values / (N + 1), 0, X_adj
)
norms_via = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)
X_vec_mc18 = X_adj / norms_via

norms_raw = np.maximum(np.sqrt((X_raw**2).sum(0)), 1e-12)
A_vec_raw = (X_raw.max(0) - X_raw.min(0)) / norms_raw
X_vec_raw = X_adj * A_vec_raw

A_max = (X_raw.max(0) - X_raw.min(0)) / np.maximum(X_raw.max(0), 1e-12)
X_max = X_adj * A_max

sums_raw = np.maximum(X_raw.sum(0), 1e-12)
A_sum = (X_raw.max(0) - X_raw.min(0)) / sums_raw
X_sum = X_adj * A_sum

X_peld = np.zeros_like(X_raw)
for j in range(M):
    x = X_raw[:, j]; mx = x.max()
    if benefit[j]:
        X_peld[:, j] = (x / mx)**2 if mx > 0 else 0.0
    else:
        X_peld[:, j] = ((mx - x) / mx)**2 if mx > 0 else 0.0

NORMS = {
    "min-max":     X_adj,
    "Peldschus":   X_peld,
    "max":         X_max,
    "ranks":       X_ranks,
    "vector":      X_vec_mc18,
    "vector_tab1": X_vec_raw,
    "sum":         X_sum,
}

# TV metrics (identical to wp3_mc.py)
print(f"\n{'Normalisation':14s}  {'TV':8s}  {'m_eff':8s}  {'Greedy_f32':12s}  {'Optimal_f32':12s}")
print("-" * 65)
norm_metrics = {}
for nm, V in NORMS.items():
    A = V.max(0) - V.min(0)
    num = w_ahp * A; s = num.sum()
    weff = num / s
    tv = 0.5 * float(np.abs(weff - w_ahp).sum())
    delta = weff - w_ahp
    sum_abs = np.abs(delta).sum(); sum_sq = (delta**2).sum()
    meff = (sum_abs**2) / sum_sq if sum_sq > 1e-30 else float('inf')
    l2 = float(np.sqrt(sum_sq))
    norm_metrics[nm] = dict(tv=tv, meff=meff, l2=l2, A=A)

# Old values from wp3_summary.csv for comparison
OLD_VALUES = {
    "min-max": (65.8, 100.0), "Peldschus": (73.2, 100.0), "max": (66.4, 100.0),
    "ranks": (66.0, 88.2), "vector": (54.0, 56.8), "vector_tab1": (54.4, 57.8),
    "sum": (70.0, 76.2),
}

# ── FIX 2: compute_objs_Ap in FLOAT64 ────────────────────────────────────────
def compute_objs_Ap_f64(w):
    """Compute per-site (f1, f2, f3) on A'. FLOAT64 (was float32)."""
    f1v = np.zeros(N, dtype=np.float64)
    f2v = np.zeros(N, dtype=np.float64)
    f3v = np.zeros(N, dtype=np.float64)
    for j, k in enumerate(col_names):
        col = COL[k]
        x   = df_via[col].values.astype(np.float64)
        ref = df_via[col].values.astype(np.float64)
        if k == "aspect":
            c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
        elif k in INV:
            c = 1.0 - _norm(x, ref)
        elif k in COST:
            c = _norm(x, ref)
        else:
            c = _norm(x, ref)
        c = c * float(w[j])
        if k in ("perm", "slope", "roads"):       f1v += c
        elif k in ("rivers", "aspect", "coast",
                   "protected", "wells"):          f2v += c
        else:                                      f3v += c
    return f1v, f2v, f3v

def argmax_trio(sc):
    st = sc[T0] + sc[T1] + sc[T2]
    return trio_arr[st.argmax()]

# ── FIX 3: dominance with eps + sorted-index objectives ──────────────────────
def is_dominated_sorted(trio_tuple, F1, F2, F3, eps=EPS):
    """
    Look up the trio by sorted tuple -> array index.
    Use F1[idx], F2[idx], F3[idx] as objectives (same arithmetic as frontier).
    Then exclude the trio itself from the dominator set.
    """
    key = tuple(sorted(trio_tuple))
    idx = trio_lookup.get(key, -1)
    if idx < 0:
        # Fallback: compute directly (should not happen)
        i, j, k = trio_tuple
        f1t = F1.flat[0]  # dummy — should not reach here
        return False
    f1t = float(F1[idx])
    f2t = float(F2[idx])
    f3t = float(F3[idx])
    # Exclude self from dominator test
    mask = np.ones(len(F1), dtype=bool)
    mask[idx] = False
    F1m, F2m, F3m = F1[mask], F2[mask], F3[mask]
    weak   = (F1m <= f1t + eps) & (F2m <= f2t + eps) & (F3m >= f3t - eps)
    strict = (F1m <  f1t - eps) | (F2m <  f2t - eps) | (F3m >  f3t + eps)
    return bool((weak & strict).any())

# ── Monte Carlo ────────────────────────────────────────────────────────────────
print(f"\n=== Running Monte Carlo: kappa={KAPPA}, N={N_DRAWS}, seed={SEED} ===")
rng = np.random.default_rng(SEED)
draw_weights = rng.dirichlet(KAPPA * w_ahp, size=N_DRAWS)

results_list = []
t_start = time.time()

for draw_idx in range(N_DRAWS):
    w = draw_weights[draw_idx]

    f1v, f2v, f3v = compute_objs_Ap_f64(w)
    F1 = f1v[T0] + f1v[T1] + f1v[T2]
    F2 = f2v[T0] + f2v[T1] + f2v[T2]
    F3 = f3v[T0] + f3v[T1] + f3v[T2]

    trio_cache = {}

    for nm, V in NORMS.items():
        sc = (V * w).sum(axis=1)

        # Greedy
        trio_g = tuple(greedy_trio(sc, D_via))
        if trio_g not in trio_cache:
            trio_cache[trio_g] = int(not is_dominated_sorted(trio_g, F1, F2, F3))
        nd_g = trio_cache[trio_g]

        # Optimal (argmax_trio always returns sorted)
        trio_o_arr = argmax_trio(sc)
        trio_o = tuple(trio_o_arr)
        if trio_o not in trio_cache:
            trio_cache[trio_o] = int(not is_dominated_sorted(trio_o, F1, F2, F3))
        nd_o = trio_cache[trio_o]

        results_list.append({
            "draw": draw_idx, "norm": nm,
            "nd_greedy": nd_g, "nd_optimal": nd_o,
        })

    trio_cache.clear()

    if (draw_idx + 1) % 50 == 0 or draw_idx == N_DRAWS - 1:
        elapsed = time.time() - t_start
        print(f"  [{draw_idx+1:3d}/{N_DRAWS}]  {elapsed:.0f}s")

df_raw = pd.DataFrame(results_list)
df_raw.to_csv(os.path.join(RESULTS_DIR, "wp3_mc_fixed_raw.csv"), index=False)

# ── Summary table ─────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print(f"{'Norm':14s}  {'TV':7s}  {'Greedy_NEW':12s}  {'Greedy_OLD':12s}  {'Δ greedy':10s}  {'Opt_NEW':10s}  {'Opt_OLD':10s}")
print("-" * 80)
summary_rows = []
for nm in NORMS.keys():
    sub = df_raw[df_raw["norm"] == nm]
    pct_g = 100.0 * sub["nd_greedy"].mean()
    pct_o = 100.0 * sub["nd_optimal"].mean()
    tv = norm_metrics[nm]["tv"]
    meff = norm_metrics[nm]["meff"]
    l2 = norm_metrics[nm]["l2"]
    old_g, old_o = OLD_VALUES.get(nm, (None, None))
    delta_g = pct_g - old_g if old_g is not None else float('nan')
    summary_rows.append({
        "norm": nm, "TV": tv, "m_eff": meff, "l2": l2,
        "Q2_greedy": pct_g, "Q2_optimal": pct_o,
        "Q2_mean": (pct_g + pct_o) / 2.0,
        "Q2_greedy_old": old_g, "delta_greedy": delta_g,
    })
    print(f"  {nm:14s}  {tv:7.4f}  {pct_g:10.2f}%  {old_g if old_g else 'N/A':>10}  "
          f"{delta_g:+8.1f}pp  {pct_o:8.2f}%  {old_o if old_o else 'N/A':>8}")

df_sum = pd.DataFrame(summary_rows)
df_sum.to_csv(os.path.join(RESULTS_DIR, "wp3_summary_fixed.csv"), index=False)

# ── Sensitivity analysis: eps in {0, 1e-12, 1e-9, 1e-6} ─────────────────────
print("\n" + "=" * 70)
print("SENSITIVITY ANALYSIS: eps × norm (min-max and vector, greedy only)")
print("Only varies eps — same float64, same sorted-index objectives")
print("=" * 70)

EPS_VALUES = [0, 1e-12, 1e-9, 1e-6]
print(f"{'eps':>12s}  {'mm_greedy':>12s}  {'vec_greedy':>12s}")
print("-" * 40)

for eps_test in EPS_VALUES:
    counts = {"min-max": 0, "vector": 0}
    rng2 = np.random.default_rng(SEED)
    draws2 = rng2.dirichlet(KAPPA * w_ahp, size=N_DRAWS)
    for w in draws2:
        f1v, f2v, f3v = compute_objs_Ap_f64(w)
        F1 = f1v[T0] + f1v[T1] + f1v[T2]
        F2 = f2v[T0] + f2v[T1] + f2v[T2]
        F3 = f3v[T0] + f3v[T1] + f3v[T2]
        for nm in ("min-max", "vector"):
            V = NORMS[nm]
            sc = (V * w).sum(1)
            trio_g = tuple(greedy_trio(sc, D_via))
            if not is_dominated_sorted(trio_g, F1, F2, F3, eps=eps_test):
                counts[nm] += 1
    mm_q2  = counts["min-max"] / N_DRAWS * 100
    vec_q2 = counts["vector"]  / N_DRAWS * 100
    stable = "OK" if (abs(mm_q2-86.0)<1.0 and abs(vec_q2-66.2)<1.5) else "CHANGED"
    print(f"  {eps_test:>10.2e}  {mm_q2:>10.2f}%  {vec_q2:>10.2f}%  {stable}")

print("\nExpected: all eps values give approximately 86.0% and 66.2% (invariant).")
print("If eps=1e-6 changes results, real ties exist and need explicit handling.")
print("\nDone.")
