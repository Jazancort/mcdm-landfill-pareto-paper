# -*- coding: utf-8 -*-
"""
run_e1.py — Experiment E1: between-group vs within-group amplitude distortion.
Pre-specification: corpus/PRESPEC_E1.md (commit f6042f8)

Design:
  E1-B: A_j = Aj_bar_g  (constant within group)   TV_B=0.2489  TV_W=0
  E1-W: A_j = rho_j/Aj_bar_g × scale              TV_B=0       TV_W=0.1986
  E1-V: A_j = rho_j    (vector, published)         TV_B=0.2489  TV_W=0.1986

All cells use SAW, objectives fixed in min-max over admissible sites.
Non-dominated check is vectorised (O(n) per trio, not O(n^2) full frontier).

Groups (from main.tex tab:amplitude via fogo_constants.py):
  G1 = [perm(0), slope(1), roads(2)]  →  F1 (siting cost, minimise)
  G2 = [rivers(3), aspect(4), coast(5), prot(6), wells(7)]  →  F2 (env, minimise)
  G3 = [urban(8), aero(9), cult(10)]  →  F3 (social safety, maximise)
"""
import os, sys, time
import numpy as np
import pandas as pd
from scipy.stats import dirichlet as sp_dir

if 'MCDM_DATA_DIR' not in os.environ and os.path.exists('/home/julioazancort/scratch/mcdm'):
    os.environ['MCDM_DATA_DIR'] = '/home/julioazancort/scratch/mcdm'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcdm_experiment import (
    load_data, impute_nan, haversine_km,
    greedy_trio, COL, AHP_WEIGHTS, MIN_DIST_KM, _build_decision_matrix,
    _norm, INV, COST
)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

N_DRAWS = 500
KAPPA   = 200
SEED    = 42

print("=" * 70)
print("E1: Between-group vs within-group amplitude distortion")
print("Pre-specification: corpus/PRESPEC_E1.md (commit f6042f8)")
print("=" * 70)

# ── 1. Load data ──────────────────────────────────────────────────────────────
df_all, par, bcs = load_data()
df_imp    = impute_nan(df_all)
viable    = df_imp[COL["protected"]] > 0
df_via    = df_imp[viable].copy()
N_via     = len(df_via)
print(f"Viable sites: {N_via}")

D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
w_ahp = w_ahp / w_ahp.sum()
col_names = list(AHP_WEIGHTS.keys())
M = len(w_ahp)

X_via, benefit = _build_decision_matrix(df_via)
# X_via[:,j] is already benefit-oriented (_build_decision_matrix inverts cost cols)

# ── 2. Build viable trios ─────────────────────────────────────────────────────
t0 = time.time()
valid = D_via >= MIN_DIST_KM
trio_list = []
for i in range(N_via):
    for j2 in range(i + 1, N_via):
        if not valid[i, j2]: continue
        for k in range(j2 + 1, N_via):
            if not valid[i, k] or not valid[j2, k]: continue
            trio_list.append((i, j2, k))
trio_arr = np.array(trio_list, dtype=np.int32)
print(f"Viable trios: {len(trio_arr):,} (built in {time.time()-t0:.2f}s)")

# ── 3. Pre-compute FIXED min-max objectives for all trios ─────────────────────
# Groups: G1=siting cost (minimise), G2=env impact (minimise), G3=social (maximise)
# X_via already benefit-oriented: higher = better for all cols.
# For min-max norm: n_j = (x - x_min) / (x_max - x_min), then multiply by w_j.
# F1 and F2 are COST objectives in the original paper, but since X_via is already
# benefit-oriented (cost cols complemented), we compute site-level scores and
# then the dominance check uses the paper's convention:
#   trio dominated if exists another with F1<=, F2<=, F3>=, strictly better in one
# (F1 siting cost minimise means LOWER F1 is better for original criterion,
#  but since X_via[:,j] is inverted for cost, higher values = better, so
#  in terms of paper F_ell: F1 = sum w_j * n_j^mm for j in G1 where n_j^mm is
#  computed on the benefit-oriented column).
# The dominance check for the paper's objectives (cost/cost/benefit) becomes:
#   dominated if exists t' with F1_t'>=F1_t (better or equal siting: higher nn = less cost),
#   F2_t'>=F2_t, F3_t'>=F3_t, strictly better in one.
# So ALL three objectives are "higher = better" after benefit-orientation.

def minmax_col(col):
    lo, hi = col.min(), col.max()
    if hi == lo: return np.ones_like(col)
    return (col - lo) / (hi - lo)

# Per-site group scores under min-max (using published w_ahp for fixed objectives)
f1_site = np.zeros(N_via, dtype=np.float32)
f2_site = np.zeros(N_via, dtype=np.float32)
f3_site = np.zeros(N_via, dtype=np.float32)
for j, k in enumerate(col_names):
    col = X_via[:, j].astype(float)
    nn  = minmax_col(col)
    if k in ("perm", "slope", "roads"):
        f1_site += (nn * w_ahp[j]).astype(np.float32)
    elif k in ("rivers", "aspect", "coast", "protected", "wells"):
        f2_site += (nn * w_ahp[j]).astype(np.float32)
    else:
        f3_site += (nn * w_ahp[j]).astype(np.float32)

# Pre-compute trio-level objectives (vectorised over all trios)
print("Pre-computing trio objectives...", end=" ", flush=True)
t0 = time.time()
T0, T1, T2 = trio_arr[:, 0], trio_arr[:, 1], trio_arr[:, 2]
F1_all = (f1_site[T0] + f1_site[T1] + f1_site[T2]).astype(np.float64)
F2_all = (f2_site[T0] + f2_site[T1] + f2_site[T2]).astype(np.float64)
F3_all = (f3_site[T0] + f3_site[T1] + f3_site[T2]).astype(np.float64)
print(f"done in {time.time()-t0:.2f}s")

# ── 4. Vector amplitudes (rho_j) — no double complement ──────────────────────
rho_j = np.zeros(M)
for j in range(M):
    col = X_via[:, j].astype(float)
    rng = col.max() - col.min()
    nrm = np.sqrt(np.sum(col**2))
    rho_j[j] = rng / nrm if nrm > 0 else 0.0

# Aj_bar_g
GROUPS = [[0, 1, 2], [3, 4, 5, 6, 7], [8, 9, 10]]
Aj_bar = np.zeros(M)
for g in GROUPS:
    wg = w_ahp[g]; Ajg = rho_j[g]
    Ajbar_g = np.dot(wg, Ajg) / wg.sum()
    for j in g:
        Aj_bar[j] = Ajbar_g

print(f"\nAj_bar_g: G1={Aj_bar[0]:.4f}  G2={Aj_bar[3]:.4f}  G3={Aj_bar[8]:.4f}")
print(f"Published: G1=0.3731  G2=0.1458  G3=0.1157")
assert abs(Aj_bar[0] - 0.3731) < 0.005, f"G1 mismatch: {Aj_bar[0]:.4f}"
assert abs(Aj_bar[3] - 0.1458) < 0.005, f"G2 mismatch: {Aj_bar[3]:.4f}"
assert abs(Aj_bar[8] - 0.1157) < 0.005, f"G3 mismatch: {Aj_bar[8]:.4f}"

Aj_E1B = Aj_bar.copy()
Aj_E1W_raw = rho_j / Aj_bar
scale_EW = np.dot(w_ahp, rho_j) / np.dot(w_ahp, Aj_E1W_raw)
Aj_E1W = Aj_E1W_raw * scale_EW
Aj_E1V = rho_j.copy()
print(f"E1-W rescale factor: {scale_EW:.4f}  (published: 0.2024)")
def build_N(X, Aj):
    """n_j = col / (range/Aj). X already benefit-oriented."""
    N_sc = np.zeros_like(X, dtype=float)
    for j in range(X.shape[1]):
        col = X[:, j].astype(float)
        rng = col.max() - col.min()
        if rng == 0: N_sc[:, j] = 1.0; continue
        N_sc[:, j] = col / (rng / Aj[j])
    return N_sc

print("\nBuilding score matrices...")
N_E1B = build_N(X_via, Aj_E1B)
N_E1W = build_N(X_via, Aj_E1W)
N_E1V = build_N(X_via, Aj_E1V)

# ── 6. Monte Carlo ────────────────────────────────────────────────────────────
CELLS = [("E1-B", N_E1B), ("E1-W", N_E1W), ("E1-V", N_E1V)]
rng   = np.random.default_rng(SEED)
# Pre-generate all draws
draw_weights = rng.dirichlet(KAPPA * w_ahp, size=N_DRAWS)

rows = []
for cell_name, N_sc in CELLS:
    print(f"\n--- {cell_name} ---")
    nd_greedy = 0; nd_optimal = 0
    t0 = time.time()

    for draw_idx, w_draw in enumerate(draw_weights):
        sc = N_sc @ w_draw

        # Greedy
        trio_g = tuple(greedy_trio(sc, D_via))
        ti, tj, tk = trio_g
        f1t = float(f1_site[ti] + f1_site[tj] + f1_site[tk])
        f2t = float(f2_site[ti] + f2_site[tj] + f2_site[tk])
        f3t = float(f3_site[ti] + f3_site[tj] + f3_site[tk])
        dominated_g = bool(((F1_all >= f1t) & (F2_all >= f2t) & (F3_all >= f3t) &
                            ((F1_all > f1t) | (F2_all > f2t) | (F3_all > f3t))).any())
        if not dominated_g:
            nd_greedy += 1

        # Optimal (argmax total score over all viable trios)
        st = sc[T0] + sc[T1] + sc[T2]
        t_idx_o = int(st.argmax())
        ti_o, tj_o, tk_o = int(T0[t_idx_o]), int(T1[t_idx_o]), int(T2[t_idx_o])
        f1o = float(f1_site[ti_o] + f1_site[tj_o] + f1_site[tk_o])
        f2o = float(f2_site[ti_o] + f2_site[tj_o] + f2_site[tk_o])
        f3o = float(f3_site[ti_o] + f3_site[tj_o] + f3_site[tk_o])
        dominated_o = bool(((F1_all >= f1o) & (F2_all >= f2o) & (F3_all >= f3o) &
                            ((F1_all > f1o) | (F2_all > f2o) | (F3_all > f3o))).any())
        if not dominated_o:
            nd_optimal += 1

        if (draw_idx + 1) % 100 == 0:
            elapsed = time.time() - t0
            print(f"  [{draw_idx+1}/{N_DRAWS}]  greedy={nd_greedy/(draw_idx+1)*100:.1f}%  "
                  f"optimal={nd_optimal/(draw_idx+1)*100:.1f}%  {elapsed:.0f}s elapsed")

    Q2g = nd_greedy  / N_DRAWS * 100
    Q2o = nd_optimal / N_DRAWS * 100
    SEg = (Q2g * (100 - Q2g) / N_DRAWS) ** 0.5
    SEo = (Q2o * (100 - Q2o) / N_DRAWS) ** 0.5
    print(f"  RESULT: greedy={Q2g:.2f}% (SE={SEg:.2f})  optimal={Q2o:.2f}% (SE={SEo:.2f})")
    rows += [
        {"cell": cell_name, "assembly": "greedy",  "Q2": Q2g, "SE": SEg, "n_draws": N_DRAWS},
        {"cell": cell_name, "assembly": "optimal", "Q2": Q2o, "SE": SEo, "n_draws": N_DRAWS},
    ]

# ── 7. Hard assertion P1 ──────────────────────────────────────────────────────
E1B_opt = next(r["Q2"] for r in rows if r["cell"]=="E1-B" and r["assembly"]=="optimal")
assert abs(E1B_opt - 100.0) < 1e-6, f"P1 FAIL: E1-B optimal={E1B_opt:.4f}% != 100%"
print(f"\n[P1] E1-B optimal = {E1B_opt:.2f}%  PASS (hard assertion)")

# ── 8. Save and report ────────────────────────────────────────────────────────
df = pd.DataFrame(rows)
out = os.path.join(RESULTS_DIR, "e1_results.csv")
df.to_csv(out, index=False)

print(f"\n{'='*70}")
print("RESULTS:")
print(df.to_string(index=False))

E1W_opt = next(r["Q2"] for r in rows if r["cell"]=="E1-W" and r["assembly"]=="optimal")
E1V_opt = next(r["Q2"] for r in rows if r["cell"]=="E1-V" and r["assembly"]=="optimal")
E1B_grd = next(r["Q2"] for r in rows if r["cell"]=="E1-B" and r["assembly"]=="greedy")

print(f"\nPrediction check:")
print(f"  P1 E1-B optimal=100%:           {'CONFIRMED' if abs(E1B_opt-100)<0.1 else 'FAILED'} ({E1B_opt:.2f}%)")
print(f"  P2 E1-W optimal ≈ E1-V optimal: |{E1W_opt:.1f}-{E1V_opt:.1f}|={abs(E1W_opt-E1V_opt):.1f}pp  {'CONFIRMED (<5pp)' if abs(E1W_opt-E1V_opt)<5 else 'PARTIAL' if abs(E1W_opt-E1V_opt)<15 else 'FAILED'}")
print(f"  P3 E1-B greedy<100%:            {'CONFIRMED' if E1B_grd<99 else 'UNEXPECTED'} ({E1B_grd:.2f}%)")
print(f"\nSaved to {out}")
