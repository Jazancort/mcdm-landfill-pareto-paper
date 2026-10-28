# -*- coding: utf-8 -*-
"""
check_float64.py — Stability check: re-run 4 SAW cells of tab:factorial in float64
with dominance tolerance eps=1e-9, compare with wp3_summary.csv (float32, no eps).

Cells verified: min-max/greedy, min-max/optimal, vector/greedy, vector/optimal.
Same seed=42, kappa=200, N=500, space A' (389 sites).

Output: prints comparison table and asserts |diff| < 1 SE for each cell.
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

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
EPS  = 1e-9
N_DRAWS = 500
KAPPA   = 200
SEED    = 42

# Reference values from wp3_summary.csv (float32, no eps)
WP3_REF = {
    ("min-max", "greedy"):  65.8,
    ("min-max", "optimal"): 100.0,
    ("vector",  "greedy"):  54.0,
    ("vector",  "optimal"): 56.8,
}

print("=" * 70)
print("Float64 stability check: 4 SAW cells (min-max + vector, greedy + optimal)")
print(f"eps={EPS}, kappa={KAPPA}, N={N_DRAWS}, seed={SEED}")
print("=" * 70)

# ── Load data ──────────────────────────────────────────────────────────────────
df_all, par, bcs = load_data()
df_imp  = impute_nan(df_all)
viable  = df_imp[COL["protected"]] > 0
df_via  = df_imp[viable].copy()
N       = len(df_via)
assert N == 389
D_via   = haversine_km(df_via["latitude (degrees)"].values,
                       df_via["longitude (degrees)"].values)
w_ahp   = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
M = len(w_ahp)

# ── Score matrices ─────────────────────────────────────────────────────────────
X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b:
        X_adj[:, j] = 1.0 - X_via[:, j]

# min-max score: X_adj (already [0,1] benefit-oriented over 389)
X_mm = X_adj.copy()

# vector score: X_adj / norms (norms from X_via, same as WP3 X_vec_mc18)
norms_via = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)
X_vec = X_adj / norms_via

NORMS = {"min-max": X_mm, "vector": X_vec}

# ── Build trios ────────────────────────────────────────────────────────────────
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
print(f"Trios: {len(trio_arr):,}  (built in {time.time()-t0:.1f}s)")

# ── Group indices ──────────────────────────────────────────────────────────────
G1 = [col_names.index(c) for c in F1_CRIT]
G2 = [col_names.index(c) for c in F2_CRIT]
G3 = [col_names.index(c) for c in F3_CRIT]

# ── Per-site objective columns in FLOAT64 (replicate compute_objs_Ap exactly) ─
c64 = {}
for crit in col_names:
    col_key = COL[crit]
    x   = df_via[col_key].values.astype(np.float64)
    ref = df_via[col_key].values.astype(np.float64)
    if crit == "aspect":
        c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
    elif crit in INV:
        c = 1.0 - _norm(x, ref)
    elif crit in COST:
        c = _norm(x, ref)
    else:
        c = _norm(x, ref)
    c64[crit] = c.astype(np.float64)

# Trip columns: float64
trip64 = np.zeros((len(trio_arr), M), dtype=np.float64)
for j, crit in enumerate(col_names):
    cv = c64[crit]
    trip64[:, j] = cv[T0] + cv[T1] + cv[T2]

def compute_F64(w):
    """F1, F2, F3 for all trios in float64, weighted by w."""
    f1 = trip64[:, G1] @ w[G1]
    f2 = trip64[:, G2] @ w[G2]
    f3 = trip64[:, G3] @ w[G3]
    return f1, f2, f3

def is_dominated_eps(f1t, f2t, f3t, F1, F2, F3, eps=EPS):
    """Dominance with tolerance eps.
    Dominator must be at least eps better in one objective.
    Uses: F1 <= f1t+eps AND F2 <= f2t+eps AND F3 >= f3t-eps
    AND (F1 < f1t-eps OR F2 < f2t-eps OR F3 > f3t+eps)
    """
    weak_dom = (F1 <= f1t + eps) & (F2 <= f2t + eps) & (F3 >= f3t - eps)
    strict   = (F1 <  f1t - eps) | (F2 <  f2t - eps) | (F3 >  f3t + eps)
    return bool((weak_dom & strict).any())

def trio_f64_single(i, j, k, w):
    f1 = float(sum(c64[c][i]+c64[c][j]+c64[c][k] for c in F1_CRIT) * 0)  # placeholder
    f1 = float(np.array([c64[c][i]+c64[c][j]+c64[c][k] for c in F1_CRIT]) @ w[G1])
    f2 = float(np.array([c64[c][i]+c64[c][j]+c64[c][k] for c in F2_CRIT]) @ w[G2])
    f3 = float(np.array([c64[c][i]+c64[c][j]+c64[c][k] for c in F3_CRIT]) @ w[G3])
    return f1, f2, f3

# ── Monte Carlo ────────────────────────────────────────────────────────────────
rng = np.random.default_rng(SEED)
draws = rng.dirichlet(KAPPA * w_ahp, size=N_DRAWS)

results = {}
for nm, V in NORMS.items():
    nd_g = 0; nd_o = 0
    t0 = time.time()
    for draw_idx, w in enumerate(draws):
        F1d, F2d, F3d = compute_F64(w)

        # Greedy
        sc = (V * w).sum(1)
        ig, jg, kg = greedy_trio(sc, D_via)
        f1g, f2g, f3g = trio_f64_single(ig, jg, kg, w)
        if not is_dominated_eps(f1g, f2g, f3g, F1d, F2d, F3d):
            nd_g += 1

        # Optimal
        st = sc[T0] + sc[T1] + sc[T2]
        t_idx = int(st.argmax())
        f1o = float(trip64[t_idx, G1] @ w[G1])
        f2o = float(trip64[t_idx, G2] @ w[G2])
        f3o = float(trip64[t_idx, G3] @ w[G3])
        if not is_dominated_eps(f1o, f2o, f3o, F1d, F2d, F3d):
            nd_o += 1

        if (draw_idx + 1) % 100 == 0:
            print(f"  {nm} [{draw_idx+1}/500] grd={nd_g/(draw_idx+1)*100:.1f}% opt={nd_o/(draw_idx+1)*100:.1f}% ({time.time()-t0:.0f}s)")

    Q2g = nd_g / N_DRAWS * 100
    Q2o = nd_o / N_DRAWS * 100
    results[(nm, "greedy")]  = Q2g
    results[(nm, "optimal")] = Q2o
    print(f"  {nm}: greedy={Q2g:.2f}%  optimal={Q2o:.2f}%")

# ── Comparison table ───────────────────────────────────────────────────────────
print(f"\n{'='*70}")
print(f"{'Cell':<22} {'WP3 (f32,no-eps)':>18} {'f64+eps':>10} {'diff':>8} {'SE':>8} {'stable?':>10}")
print(f"{'-'*70}")
all_stable = True
for key, ref in WP3_REF.items():
    nm, asm = key
    q2 = results[key]
    diff = abs(q2 - ref)
    se = (ref * (100 - ref) / N_DRAWS) ** 0.5
    stable = diff < se  # within 1 SE
    flag = "OK" if stable else "CHANGED"
    if not stable:
        all_stable = False
    print(f"  SAW/{nm}/{asm:<10} {ref:>18.1f}% {q2:>10.2f}% {diff:>7.2f}pp {se:>7.2f}pp {flag:>10}")

print(f"\n{'STABLE' if all_stable else 'CHANGED — re-run all MC required'}")
if all_stable:
    print("Float32→float64 with eps=1e-9 does not change results by more than 1 SE.")
    print("Article numbers are safe. Record this in Supplementary Material.")

# Save
df_out = pd.DataFrame([
    {"norm": nm, "assembly": asm, "Q2_f64_eps": results[(nm,asm)], "Q2_wp3": WP3_REF[(nm,asm)],
     "diff_pp": results[(nm,asm)] - WP3_REF[(nm,asm)]}
    for nm, asm in [("min-max","greedy"),("min-max","optimal"),("vector","greedy"),("vector","optimal")]
])
out = os.path.join(RESULTS_DIR, "float64_check.csv")
df_out.to_csv(out, index=False)
print(f"\nSaved to {out}")
