# -*- coding: utf-8 -*-
"""
run_e1.py v2 — Experiment E1: between-group vs within-group amplitude distortion.
Pre-specification: corpus/PRESPEC_E1.md (commit f6042f8, repo G:)
Invalid run: DEV-E1-001 (commit 380ee1a, Athena) — fixed objectives bug.

Design:
  E1-B: A_j = Aj_bar_g  (constant within group)   TV_B=0.2489  TV_W=0
  E1-W: A_j = rho_j/Aj_bar_g × scale              TV_B=0       TV_W=0.1986
  E1-V: A_j = rho_j    (vector, published)         TV_B=0.2489  TV_W=0.1986

All cells use SAW with amplitude-normalised scores.
Objectives F_l(t; w) recomputed each draw with w_draw — SAME estimand as WP3.

REGRESSION (must pass before E1-B/E1-W are interpreted):
  R1: E1-V greedy  reproduces WP3 SAW/vector/greedy  (54.0 ± 3*SE)
  R2: E1-V optimal reproduces WP3 SAW/vector/optimal (56.8 ± 3*SE)
  R3: E1-B optimal = 100.0% exactly (P1 hard assertion)
  R4: frontier size varies across draws (objectives are not fixed)

Groups (from fogo_constants.py / main.tex tab:amplitude):
  G1 = [perm(0), slope(1), roads(2)]                          -> F1 (siting cost)
  G2 = [rivers(3), aspect(4), coast(5), prot(6), wells(7)]    -> F2 (env)
  G3 = [urban(8), aero(9), cult(10)]                          -> F3 (social safety)
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
os.makedirs(RESULTS_DIR, exist_ok=True)

N_DRAWS = 500
KAPPA   = 200
SEED    = 42

# Reference values from WP3 (wp3_summary.csv, alpha=200, SAW/vector)
WP3_VEC_GREEDY  = 54.0
WP3_VEC_OPTIMAL = 56.8

print("=" * 70)
print("E1 v2: Between-group vs within-group amplitude distortion")
print("Pre-specification: corpus/PRESPEC_E1.md (commit f6042f8)")
print("=" * 70)

# ── 1. Load data ───────────────────────────────────────────────────────────────
df_all, par, bcs = load_data()
df_imp    = impute_nan(df_all)           # 473 sites — normalisation reference
viable    = df_imp[COL["protected"]] > 0
df_via    = df_imp[viable].copy()        # 389 admissible sites (space A')
N_via     = len(df_via)
print(f"Reference sites: {len(df_imp)}   Admissible sites: {N_via}")
assert len(df_imp) == 473, f"Expected 473 reference sites, got {len(df_imp)}"
assert N_via == 389, f"Expected 389 admissible sites, got {N_via}"

D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
w_ahp = w_ahp / w_ahp.sum()
col_names = list(AHP_WEIGHTS.keys())
M = len(w_ahp)

# ── 2. Build viable trios ──────────────────────────────────────────────────────
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
T0, T1, T2 = trio_arr[:, 0], trio_arr[:, 1], trio_arr[:, 2]
print(f"Viable trios: {len(trio_arr):,} (built in {time.time()-t0:.2f}s)")
assert len(trio_arr) == 1944653, f"Expected 1,944,653 trios, got {len(trio_arr):,}"

# ── 3. Per-site objective column values (389-site normalised — same as WP3) ───
# WP3 (wp3_mc.py::compute_objs_Ap) uses df_via as reference for objectives.
# Normalisation over 389 sites, NOT 473. This matches the estimand that produces
# the reference values (54.0%/56.8%) in wp3_summary.csv.
print("Building per-site objective columns (389-site reference, as WP3)...", end=" ", flush=True)
c_site = {}  # crit -> np.float32 array (N_via,)
for crit in col_names:
    col_key = COL[crit] if crit in COL else crit
    x   = df_via[col_key].values.astype(float)
    ref = df_via[col_key].values.astype(float)   # 389-site reference (same as WP3)
    if crit == "aspect":
        c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
    elif crit in INV:
        c = 1.0 - _norm(x, ref)
    elif crit in COST:
        c = _norm(x, ref)
    else:
        c = _norm(x, ref)
    c_site[crit] = c.astype(np.float64)
print("done")

# Group index lists
G1_idx = [col_names.index(c) for c in F1_CRIT]
G2_idx = [col_names.index(c) for c in F2_CRIT]
G3_idx = [col_names.index(c) for c in F3_CRIT]

# Per-trio column sums: trip_col[trio_idx, j] = c_site[j][T0] + c_site[j][T1] + c_site[j][T2]
print("Pre-computing trio column sums...", end=" ", flush=True)
t0 = time.time()
trip_col = np.zeros((len(trio_arr), M), dtype=np.float64)
for j, crit in enumerate(col_names):
    cv = c_site[crit]
    trip_col[:, j] = cv[T0] + cv[T1] + cv[T2]
print(f"done in {time.time()-t0:.2f}s")

# ── Reference frontier per draw (recomputed with w_draw — same as WP3) ────────
# WP3 computes F1,F2,F3 per draw with w_draw and uses them for dominance test.
# This ensures w_ob = w_fr = w_draw (coherence condition from rem:coherence).

def compute_trio_F(w):
    """F1, F2, F3 for all trios with weight vector w (389-site normalised).
    F1,F2 cost-type (lower=better), F3 benefit (higher=better)."""
    f1 = (trip_col[:, G1_idx] @ w[G1_idx]).astype(np.float64)
    f2 = (trip_col[:, G2_idx] @ w[G2_idx]).astype(np.float64)
    f3 = (trip_col[:, G3_idx] @ w[G3_idx]).astype(np.float64)
    return f1, f2, f3

def trio_F_single(i, j, k, w):
    """F1,F2,F3 for a single trio."""
    f1 = float(np.array([c_site[c][i]+c_site[c][j]+c_site[c][k]
                         for c in F1_CRIT], dtype=np.float64) @ w[G1_idx])
    f2 = float(np.array([c_site[c][i]+c_site[c][j]+c_site[c][k]
                         for c in F2_CRIT], dtype=np.float64) @ w[G2_idx])
    f3 = float(np.array([c_site[c][i]+c_site[c][j]+c_site[c][k]
                         for c in F3_CRIT], dtype=np.float64) @ w[G3_idx])
    return f1, f2, f3

def is_dominated(f1t, f2t, f3t, F1, F2, F3):
    """True if (f1t,f2t,f3t) is dominated."""
    return bool(((F1 <= f1t) & (F2 <= f2t) & (F3 >= f3t) &
                 ((F1 < f1t) | (F2 < f2t) | (F3 > f3t))).any())

# R4: verify objectives vary with w — compute with w_ahp and a perturbed w
_F1_nom, _F2_nom, _F3_nom = compute_trio_F(w_ahp)
_w_test = w_ahp.copy(); _w_test[0] *= 1.1; _w_test /= _w_test.sum()
_F1_tst, _F2_tst, _F3_tst = compute_trio_F(_w_test)
_r4_proxy = float(np.abs(_F1_nom - _F1_tst).max()) > 1e-8
print(f"R4 proxy: objectives change with w perturbation: {_r4_proxy}")
print(f"Reference frontier (w_ahp): F1=[{_F1_nom.min():.4f},{_F1_nom.max():.4f}]  "
      f"F2=[{_F2_nom.min():.4f},{_F2_nom.max():.4f}]  "
      f"F3=[{_F3_nom.min():.4f},{_F3_nom.max():.4f}]")

# ── 4. Amplitude vectors ───────────────────────────────────────────────────────
X_via, benefit = _build_decision_matrix(df_via)   # normalised over 389

rho_j = np.zeros(M)
for j in range(M):
    col = X_via[:, j].astype(float)
    rng_val = col.max() - col.min()
    nrm = np.sqrt(np.sum(col**2))
    rho_j[j] = rng_val / nrm if nrm > 0 else 0.0

# Aj_bar_g = weighted mean of rho within group
GROUPS = [G1_idx, G2_idx, G3_idx]
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

# ── ASSERTION: TV_B(E1-W) = 0 ────────────────────────────────────────────────
# TV_B measures between-group amplitude variation.
# For E1-W: A_j = rho_j / Aj_bar_g * scale.
# Weighted mean within group g: sum_{j in g} w_j * A_j^W / W_g
#   = scale * sum_{j in g} w_j * rho_j / Aj_bar_g / W_g
#   = scale * Aj_bar_g * W_g / Aj_bar_g / W_g  (by definition of Aj_bar_g)
#   = scale   (constant, same for all groups)
# Therefore TV_B(E1-W) = 0: the amplitude mean is identical across all groups.
# Correct assertion: weighted mean amplitude per group must be constant across groups.
means_W = []
for g_idx, g_name in zip(GROUPS, ["G1", "G2", "G3"]):
    wg = w_ahp[g_idx]
    Wg = wg.sum()
    mean_g = float(np.dot(wg, Aj_E1W[g_idx])) / Wg
    means_W.append(mean_g)
for i, g_name in enumerate(["G1", "G2", "G3"]):
    assert abs(means_W[i] - means_W[0]) < 1e-10, \
        f"TV_B(E1-W) FAIL: mean_g({g_name})={means_W[i]:.8f} != mean_g(G1)={means_W[0]:.8f}"
print(f"[TV_B assertion] E1-W group amplitude means all equal {means_W[0]:.6f}: PASS")

# Build amplitude-normalised score matrices (SAW with A_j amplitudes)
# n_j(x) = x / (range_j / A_j).  X_adj: benefit-oriented over 389.
X_adj = X_via.copy()
for j, is_ben in enumerate(benefit):
    if not is_ben:
        X_adj[:, j] = 1.0 - X_via[:, j]

def build_N(Aj):
    """n_j = col / (range/Aj). X_adj already benefit-oriented over 389."""
    N_sc = np.zeros((N_via, M), dtype=np.float64)
    for j in range(M):
        col = X_adj[:, j].astype(float)
        rng_v = col.max() - col.min()
        if rng_v == 0:
            N_sc[:, j] = 1.0
        else:
            N_sc[:, j] = col / (rng_v / Aj[j])
    return N_sc

print("\nBuilding score matrices...")
N_E1V = build_N(Aj_E1V)
N_E1B = build_N(Aj_E1B)
N_E1W = build_N(Aj_E1W)

# ── 5. Monte Carlo ─────────────────────────────────────────────────────────────
CELLS = [("E1-V", N_E1V), ("E1-B", N_E1B), ("E1-W", N_E1W)]
rng_mc = np.random.default_rng(SEED)
draw_weights = rng_mc.dirichlet(KAPPA * w_ahp, size=N_DRAWS)

rows = []
frontier_sizes_EIV = []   # for R4: frontier variability check

for cell_name, N_sc in CELLS:
    print(f"\n--- {cell_name} ---")
    nd_greedy = 0; nd_optimal = 0
    t0 = time.time()

    for draw_idx, w_draw in enumerate(draw_weights):
        # Per-draw objectives (F1,F2,F3 recomputed with w_draw — same as WP3)
        F1d, F2d, F3d = compute_trio_F(w_draw)

        # ── Greedy ──────────────────────────────────────────────────────────
        sc = N_sc @ w_draw
        i_g, j_g, k_g = greedy_trio(sc, D_via)
        f1g, f2g, f3g = trio_F_single(i_g, j_g, k_g, w_draw)
        if not is_dominated(f1g, f2g, f3g, F1d, F2d, F3d):
            nd_greedy += 1

        # ── Optimal (argmax total SAW score) ─────────────────────────────────
        st = sc[T0] + sc[T1] + sc[T2]
        t_idx_o = int(st.argmax())
        f1o = float(trip_col[t_idx_o, G1_idx] @ w_draw[G1_idx])
        f2o = float(trip_col[t_idx_o, G2_idx] @ w_draw[G2_idx])
        f3o = float(trip_col[t_idx_o, G3_idx] @ w_draw[G3_idx])
        if not is_dominated(f1o, f2o, f3o, F1d, F2d, F3d):
            nd_optimal += 1

        # R4 proxy: track which optimal trio is selected (should vary across draws)
        if cell_name == "E1-V":
            frontier_sizes_EIV.append(t_idx_o)

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

# ── 6. Regression assertions ───────────────────────────────────────────────────
print(f"\n{'='*70}")
print("REGRESSION ASSERTIONS")
print(f"{'='*70}")

def get(cell, asm):
    return next(r["Q2"] for r in rows if r["cell"]==cell and r["assembly"]==asm)

E1V_g = get("E1-V", "greedy");  E1V_o = get("E1-V", "optimal")
E1B_g = get("E1-B", "greedy");  E1B_o = get("E1-B", "optimal")
E1W_g = get("E1-W", "greedy");  E1W_o = get("E1-W", "optimal")

SE_ref = (WP3_VEC_GREEDY * (100 - WP3_VEC_GREEDY) / N_DRAWS) ** 0.5

r1_ok = abs(E1V_g - WP3_VEC_GREEDY)  < 3 * SE_ref
r2_ok = abs(E1V_o - WP3_VEC_OPTIMAL) < 3 * SE_ref
r3_ok = abs(E1B_o - 100.0) < 1e-6
r4_ok = len(set(frontier_sizes_EIV)) > 1

print(f"R1 E1-V greedy  = {E1V_g:.2f}%  (WP3={WP3_VEC_GREEDY}%, "
      f"|diff|={abs(E1V_g-WP3_VEC_GREEDY):.1f}pp, 3*SE={3*SE_ref:.1f}pp): "
      f"{'PASS' if r1_ok else 'FAIL'}")
print(f"R2 E1-V optimal = {E1V_o:.2f}%  (WP3={WP3_VEC_OPTIMAL}%, "
      f"|diff|={abs(E1V_o-WP3_VEC_OPTIMAL):.1f}pp, 3*SE={3*SE_ref:.1f}pp): "
      f"{'PASS' if r2_ok else 'FAIL'}")
print(f"R3 E1-B optimal = {E1B_o:.2f}% (must be 100.0%): {'PASS' if r3_ok else 'FAIL'}")
print(f"R4 optimal trio varies across draws "
      f"({len(set(frontier_sizes_EIV))} distinct indices out of {len(frontier_sizes_EIV)}): "
      f"{'PASS' if r4_ok else 'FAIL'}")

assert r3_ok, f"P1 FAIL: E1-B optimal={E1B_o:.4f}% != 100%"
assert r1_ok, f"R1 FAIL: E1-V greedy={E1V_g:.2f}% vs WP3={WP3_VEC_GREEDY}% (diff={abs(E1V_g-WP3_VEC_GREEDY):.1f}pp > 3*SE={3*SE_ref:.1f}pp)"
assert r2_ok, f"R2 FAIL: E1-V optimal={E1V_o:.2f}% vs WP3={WP3_VEC_OPTIMAL}% (diff={abs(E1V_o-WP3_VEC_OPTIMAL):.1f}pp > 3*SE={3*SE_ref:.1f}pp)"
assert r4_ok, "R4 FAIL: optimal trio index never changes — selection does not vary with w_draw"

print("\n[REGRESSION PASS] Pipeline reproduces WP3 control cell.")

# ── 7. Prediction check ────────────────────────────────────────────────────────
print(f"\n{'='*70}")
print("PREDICTION CHECK (pre-spec: corpus/PRESPEC_E1.md commit f6042f8)")
print(f"{'='*70}")
print(f"P1 E1-B optimal=100%:               {'CONFIRMED' if abs(E1B_o-100)<0.1 else 'FAILED'} ({E1B_o:.2f}%)")
p2_diff = abs(E1W_o - E1V_o)
print(f"P2 E1-W optimal approx E1-V:        |{E1W_o:.1f}-{E1V_o:.1f}|={p2_diff:.1f}pp  "
      f"{'CONFIRMED (<5pp)' if p2_diff<5 else 'PARTIAL (5-15pp)' if p2_diff<15 else 'FAILED (>15pp)'}")
print(f"P3 E1-B greedy<100%:                {'CONFIRMED' if E1B_g<99 else 'UNEXPECTED'} ({E1B_g:.2f}%)")

# ── 8. Save ────────────────────────────────────────────────────────────────────
df_out = pd.DataFrame(rows)
out = os.path.join(RESULTS_DIR, "e1_results.csv")
df_out.to_csv(out, index=False)

print(f"\n{'='*70}")
print("RESULTS:")
print(df_out.to_string(index=False))
print(f"\nSaved to {out}")
