# -*- coding: utf-8 -*-
"""
wp3_mc.py — WP3: Monte Carlo evaluation of SAW under expanded normalisations.

Expands Table 3 (main.tex: tab:tvorder) from 3 levels (min-max, ranks, vector)
to 5 levels (min-max, max, ranks, vector, sum) plus Peldschus nonlinear.

Evaluation design:
  - Additive aggregation (SAW)
  - Space A' (389 viable sites, N_cand = 473, viable = protected > 0)
  - Trios: 1,944,653 viable combinations (min pairwise dist >= 10 km)
  - Reference: exact Pareto frontier on A' under drawn weights w ~ Dir(kappa * w_ahp)
  - kappa = 200, N_DRAWS = 500, seed = 42
  - Assemblies: greedy and optimal
  - Q2[A']: % non-dominated across 500 draws (average of greedy and optimal)

Outputs:
  - Table of TV, m_eff, l2, Q2_greedy, Q2_optimal, Q2_mean for each normalisation
  - Linear regression Q2 ~ TV (slope, SE, R2, df) for 3-level, 5-level, and all levels
  - CSV saved to results/wp3_mc_results.csv and results/wp3_summary.csv
"""
import os
import sys
import time
import numpy as np
import pandas as pd
from scipy import stats

# Path setup
if 'MCDM_DATA_DIR' not in os.environ and os.path.exists('/home/julioazancort/scratch/mcdm'):
    os.environ['MCDM_DATA_DIR'] = '/home/julioazancort/scratch/mcdm'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcdm_experiment import (
    load_data, impute_nan, haversine_km,
    greedy_trio, COL, AHP_WEIGHTS, MIN_DIST_KM, _build_decision_matrix, COST, INV, _norm
)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
if not os.path.exists(RESULTS_DIR):
    RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

print("=" * 70)
print("WP3: Monte Carlo Evaluation of SAW under Expanded Normalisations")
print("=" * 70)

# ─── 1. Load and prepare data ──────────────────────────────────────────────
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
N = len(df_via)
print(f"Viable sites N = {N}")

D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
M = len(w_ahp)

# Build decision matrix and benefit flags
X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j2, b in enumerate(benefit):
    if not b:
        X_adj[:, j2] = 1.0 - X_via[:, j2]

# Build raw criteria matrix (for exact amplitudes from raw data)
X_raw = np.zeros((N, M), dtype=np.float64)
for j, k in enumerate(col_names):
    col = COL[k]
    vals = df_via[col].values.astype(np.float64)
    if k == 'aspect':
        # Leeward favourable [90, 180]: c=1, else 0
        X_raw[:, j] = np.where((vals >= 90) & (vals <= 180), 1.0, 0.0)
    else:
        X_raw[:, j] = vals

# Build viable trios (10 km constraint)
t0 = time.time()
valid = D_via >= MIN_DIST_KM
trio_arr = []
for i in range(N):
    for j in range(i + 1, N):
        if not valid[i, j]:
            continue
        for k in range(j + 1, N):
            if not valid[i, k] or not valid[j, k]:
                continue
            trio_arr.append((i, j, k))
trio_arr = np.array(trio_arr, dtype=np.int32)
num_trios = len(trio_arr)
print(f"Viable trios: {num_trios:,} (built in {time.time() - t0:.2f}s)")

# ─── 2. Normalisation definitions & matrices ─────────────────────────────────
# Midranks scaled by N+1 (as in mc_18cells.py)
X_ranks = np.apply_along_axis(
    lambda c: pd.Series(c).rank(method="average").values / (N + 1), 0, X_adj
)

# Vector norms (as in mc_18cells.py)
norms_via = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)
X_vec_mc18 = X_adj / norms_via

# Vector norms from raw X (canonical Table 1 definition: rho_j = (max-min)/||x||_2)
norms_raw = np.maximum(np.sqrt((X_raw**2).sum(0)), 1e-12)
A_vec_raw = (X_raw.max(0) - X_raw.min(0)) / norms_raw
X_vec_raw = X_adj * A_vec_raw

# Max normalisation: A_j = 1 - min/max
# Oriented: V = const + A_j * X_adj
A_max = (X_raw.max(0) - X_raw.min(0)) / np.maximum(X_raw.max(0), 1e-12)
X_max = X_adj * A_max

# Sum normalisation: A_j = (max - min) / sum(x)
sums_raw = np.maximum(X_raw.sum(0), 1e-12)
A_sum = (X_raw.max(0) - X_raw.min(0)) / sums_raw
X_sum = X_adj * A_sum

# Peldschus nonlinear: (x / x_max)^2
# For benefit: (x / mx)^2; for cost: ((mx - x) / mx)^2
X_peld = np.zeros_like(X_raw)
for j in range(M):
    x = X_raw[:, j]
    mx = x.max()
    if benefit[j]:
        X_peld[:, j] = (x / mx)**2 if mx > 0 else 0.0
    else:
        X_peld[:, j] = ((mx - x) / mx)**2 if mx > 0 else 0.0

# Dictionary of normalisations to evaluate
NORMS = {
    "min-max":     X_adj,
    "Peldschus":   X_peld,
    "max":         X_max,
    "ranks":       X_ranks,
    "vector":      X_vec_mc18,
    "vector_tab1": X_vec_raw,
    "sum":         X_sum,
}

# Compute theoretical Aj, TV, m_eff for each normalisation
print("\n=== Theoretical Distortion Metrics (TV, m_eff, l2) ===")
print(f"{'Normalisation':14s}  {'TV':8s}  {'m_eff':8s}  {'l2':8s}  {'Aj range':20s}")
print("-" * 65)

norm_metrics = {}
for nm, V in NORMS.items():
    A = V.max(0) - V.min(0)
    num = w_ahp * A
    s = num.sum()
    weff = num / s
    tv = 0.5 * float(np.abs(weff - w_ahp).sum())
    delta = weff - w_ahp
    sum_abs = np.abs(delta).sum()
    sum_sq = (delta**2).sum()
    meff = (sum_abs**2) / sum_sq if sum_sq > 1e-30 else float('inf')
    l2 = float(np.sqrt(sum_sq))
    norm_metrics[nm] = dict(tv=tv, meff=meff, l2=l2, A=A)
    meff_str = "N/A" if tv < 1e-8 else f"{meff:.3f}"
    print(f"{nm:14s}  {tv:8.5f}  {meff_str:>8s}  {l2:8.5f}  [{A.min():.4f}, {A.max():.4f}]")

# ─── 3. Objectives & Non-dominance helper functions ─────────────────────────
def compute_objs_Ap(w):
    """Compute per-site (f1, f2, f3) on A' using min-max on df_via."""
    f1v = np.zeros(N, dtype=np.float32)
    f2v = np.zeros(N, dtype=np.float32)
    f3v = np.zeros(N, dtype=np.float32)
    for j, k in enumerate(col_names):
        col = COL[k]
        x = df_via[col].values.astype(float)
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
        if k in ("perm", "slope", "roads"):
            f1v += c
        elif k in ("rivers", "aspect", "coast", "protected", "wells"):
            f2v += c
        else:
            f3v += c
    return f1v, f2v, f3v

def argmax_trio(sc):
    """Find trio maximizing sum of scores."""
    st = sc[trio_arr[:, 0]] + sc[trio_arr[:, 1]] + sc[trio_arr[:, 2]]
    return trio_arr[st.argmax()]

# ─── 4. Monte Carlo Execution ───────────────────────────────────────────────
KAPPA = 200
N_DRAWS = 500
SEED = 42

print(f"\n=== Running Monte Carlo: kappa={KAPPA}, N_DRAWS={N_DRAWS}, seed={SEED} ===")
rng = np.random.default_rng(SEED)

# Pre-generate weights
draw_weights = rng.dirichlet(KAPPA * w_ahp, size=N_DRAWS)

# Storage: list of dicts for each draw & condition
results_list = []
t_start = time.time()

for draw_idx in range(N_DRAWS):
    w = draw_weights[draw_idx]

    # Reference objectives on A' for this draw
    f1_v, f2_v, f3_v = compute_objs_Ap(w)
    F1 = f1_v[trio_arr[:, 0]] + f1_v[trio_arr[:, 1]] + f1_v[trio_arr[:, 2]]
    F2 = f2_v[trio_arr[:, 0]] + f2_v[trio_arr[:, 1]] + f2_v[trio_arr[:, 2]]
    F3 = f3_v[trio_arr[:, 0]] + f3_v[trio_arr[:, 1]] + f3_v[trio_arr[:, 2]]

    # For each normalisation, compute greedy and optimal trios
    # Cache trio non-dominance checks in this draw to avoid redundant checks
    trio_cache = {}

    for nm, V in NORMS.items():
        # Score vector for sites
        sc = (V * w).sum(axis=1)

        # 1. Greedy assembly
        trio_g = tuple(greedy_trio(sc, D_via))
        if trio_g not in trio_cache:
            ti, tj, tk = trio_g
            f1_t = f1_v[ti] + f1_v[tj] + f1_v[tk]
            f2_t = f2_v[ti] + f2_v[tj] + f2_v[tk]
            f3_t = f3_v[ti] + f3_v[tj] + f3_v[tk]
            # Dominated if exists another trio strictly better in at least one and >= in all
            # Siting cost F1 (lower better), environmental impact F2 (lower better), social safety F3 (higher better)
            dominated = bool(((F1 <= f1_t) & (F2 <= f2_t) & (F3 >= f3_t) &
                             ((F1 < f1_t) | (F2 < f2_t) | (F3 > f3_t))).any())
            trio_cache[trio_g] = int(not dominated)
        nd_g = trio_cache[trio_g]

        # 2. Optimal assembly
        trio_o = tuple(argmax_trio(sc))
        if trio_o not in trio_cache:
            ti, tj, tk = trio_o
            f1_t = f1_v[ti] + f1_v[tj] + f1_v[tk]
            f2_t = f2_v[ti] + f2_v[tj] + f2_v[tk]
            f3_t = f3_v[ti] + f3_v[tj] + f3_v[tk]
            dominated = bool(((F1 <= f1_t) & (F2 <= f2_t) & (F3 >= f3_t) &
                             ((F1 < f1_t) | (F2 < f2_t) | (F3 > f3_t))).any())
            trio_cache[trio_o] = int(not dominated)
        nd_o = trio_cache[trio_o]

        results_list.append({
            "draw": draw_idx,
            "norm": nm,
            "nd_greedy": nd_g,
            "nd_optimal": nd_o,
            "trio_g": str(trio_g),
            "trio_o": str(trio_o),
        })

    if (draw_idx + 1) % 50 == 0 or draw_idx == N_DRAWS - 1:
        elapsed = time.time() - t_start
        rate = (draw_idx + 1) / elapsed
        rem = (N_DRAWS - (draw_idx + 1)) / rate if rate > 0 else 0
        print(f"  Draw [{draw_idx + 1:3d}/{N_DRAWS}] - Elapsed: {elapsed:5.1f}s - "
              f"Rate: {rate:4.1f} draws/s - ETA: {rem:4.1f}s")

df_raw = pd.DataFrame(results_list)
raw_path = os.path.join(RESULTS_DIR, "wp3_mc_results.csv")
df_raw.to_csv(raw_path, index=False)
print(f"\nRaw results saved to {raw_path}")

# ─── 5. Summary & Regression Analysis ────────────────────────────────────────
summary_rows = []
for nm in NORMS.keys():
    sub = df_raw[df_raw["norm"] == nm]
    pct_g = 100.0 * sub["nd_greedy"].mean()
    pct_o = 100.0 * sub["nd_optimal"].mean()
    pct_mean = (pct_g + pct_o) / 2.0
    tv = norm_metrics[nm]["tv"]
    meff = norm_metrics[nm]["meff"]
    l2 = norm_metrics[nm]["l2"]
    summary_rows.append({
        "norm": nm,
        "TV": tv,
        "m_eff": meff,
        "l2": l2,
        "Q2_greedy": pct_g,
        "Q2_optimal": pct_o,
        "Q2_mean": pct_mean,
    })

df_sum = pd.DataFrame(summary_rows)
sum_path = os.path.join(RESULTS_DIR, "wp3_summary.csv")
df_sum.to_csv(sum_path, index=False)

print("\n" + "=" * 70)
print("WP3 SUMMARY TABLE: SAW under Expanded Normalisations (kappa=200, space A')")
print("=" * 70)
print(f"{'Normalisation':14s}  {'TV':7s}  {'m_eff':7s}  {'Greedy':8s}  {'Optimal':8s}  {'Q2[A\']':8s}")
print("-" * 70)
for _, r in df_sum.iterrows():
    me_str = "N/A" if r['TV'] < 1e-6 else f"{r['m_eff']:7.3f}"
    print(f"{r['norm']:14s}  {r['TV']:7.4f}  {me_str:>7s}  "
          f"{r['Q2_greedy']:7.1f}%  {r['Q2_optimal']:7.1f}%  {r['Q2_mean']:7.1f}%")

# ─── 6. Linear Regression Models ─────────────────────────────────────────────
def fit_regression(norms_subset, label):
    sub = df_sum[df_sum["norm"].isin(norms_subset)].copy()
    sub = sub.sort_values("TV")
    x = sub["TV"].values
    y = sub["Q2_mean"].values
    n = len(x)
    res = stats.linregress(x, y)
    
    # Residual standard error and SE of slope
    y_pred = res.intercept + res.slope * x
    residuals = y - y_pred
    df_resid = n - 2
    s_err = np.sqrt((residuals**2).sum() / df_resid) if df_resid > 0 else 0.0
    sxx = ((x - x.mean())**2).sum()
    se_slope = s_err / np.sqrt(sxx) if sxx > 0 else 0.0

    print(f"\n--- OLS Regression: {label} (n={n}, df={df_resid}) ---")
    print(f"  Levels: {list(sub['norm'])}")
    print(f"  TV values: {[round(v, 4) for v in x]}")
    print(f"  Q2 means:  {[round(v, 2) for v in y]}")
    print(f"  Slope:     {res.slope:+.2f} pp/unit TV")
    print(f"  SE(slope): {se_slope:.2f} pp (res. stderr = {res.stderr:.2f} pp)")
    print(f"  Intercept: {res.intercept:.2f}%")
    print(f"  R^2:       {res.rvalue**2:.4f}")
    if df_resid > 0:
        print(f"  p-value:   {res.pvalue:.4e}")
    return res, se_slope

# (a) Original 3 levels (verification of Table 3)
fit_regression(["min-max", "ranks", "vector"], "Original 3 levels (Table 3)")

# (b) Five canonical levels (min-max, max, ranks, vector, sum)
fit_regression(["min-max", "max", "ranks", "vector", "sum"], "Five levels (WP3 target)")

# (c) All 6 levels (including Peldschus)
fit_regression(["min-max", "Peldschus", "max", "ranks", "vector", "sum"], "Six levels (with Peldschus)")

print("\n" + "=" * 70)
print("WP3 Monte Carlo completed successfully!")
print("=" * 70)
