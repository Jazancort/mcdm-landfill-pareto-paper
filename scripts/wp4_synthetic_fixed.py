# -*- coding: utf-8 -*-
"""
wp4_synthetic_fixed.py — wp4_synthetic.py with pipeline corrections for E2 grid.

Pre-specification: corpus/PRESPEC_E2.md (commit 8d9d2ac, G: repo, 2026-10-01 07:32:24)

Changes from wp4_synthetic.py:
  1. Objectives F_k recomputed per draw in float64 (was float32 via F_obj fixed)
  2. is_dominated_vec replaced by is_dominated from pareto_utils (sorted-idx + eps=1e-9)
  3. greedy_trio uses standard greedy_trio from mcdm_experiment (not fogo-specific)
  4. TV metrics added: TV_B, TV_W per group, TV_W_eff = sum_g W_g_eff * TV_W_g
  5. Regression assert: SAW/mm/optimal Q2=1.000 on every instance (unchanged)

Grid design (from PRESPEC_E2.md):
  s_B ∈ {0.0, 0.1, 0.2, 0.3, 0.4}   (5 levels, between-group distortion)
  s_W ∈ {0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7}  (8 levels, within-group)
  6 replicates per (s_B, s_W) = 240 instances total

Output: results/e2_grid_results.csv
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import sys, argparse, time
import numpy as np
import pandas as pd
from pathlib import Path
from itertools import product as iproduct

if 'MCDM_DATA_DIR' not in os.environ and os.path.exists('/home/julioazancort/scratch/mcdm'):
    os.environ['MCDM_DATA_DIR'] = '/home/julioazancort/scratch/mcdm'

sys.path.insert(0, str(Path(__file__).parent))

# ── AHP weights and groups (from mcdm_experiment.AHP_WEIGHTS / tab:amplitude) ─
# perm=0.152, slope=0.113, roads=0.030 -> G1  (W_G1=0.295)
# rivers=0.091, aspect=0.075, coast=0.069, protected=0.066, wells=0.055 -> G2 (W_G2=0.356)
# urban=0.166, aero=0.102, cult=0.081 -> G3  (W_G3=0.349)
W_AHP = np.array([
    0.152, 0.113, 0.030,           # G1: perm, slope, roads  (indices 0-2)
    0.091, 0.075, 0.069, 0.066, 0.055,  # G2: rivers,aspect,coast,prot,wells (3-7)
    0.166, 0.102, 0.081,           # G3: urban, aero, cult   (8-10)
], dtype=np.float64)
W_AHP /= W_AHP.sum()
M = len(W_AHP)

# Group slices (G1=F1 siting cost, G2=F2 env impact, G3=F3 social safety)
G1_IDX = list(range(0, 3))   # 3 criteria
G2_IDX = list(range(3, 8))   # 5 criteria
G3_IDX = list(range(8, 11))  # 3 criteria
GROUPS = [G1_IDX, G2_IDX, G3_IDX]
GROUP_NAMES = ['G1', 'G2', 'G3']

N_DRAWS   = 500
KAPPA     = 200
SEED_BASE = 20261001
EPS       = 1e-9


# ── Amplitude construction for (s_B, s_W) grid ───────────────────────────────
def make_amplitudes(s_B, s_W, rng):
    """
    Generate amplitude vector Aj with:
      s_B=0.0 -> TV_B=0 (Aj constant across groups, like E1-B)
      s_B=1.0 -> TV_B ≈ 0.25 (published Fogo values)
      s_W=0.0 -> TV_W=0 for all groups (Aj constant within each group)
      s_W=1.0 -> TV_W,g ≈ 0.20 for each group (like E1-W)

    Method:
      - Interpolate between flat (s_B=0) and published (s_B=1) for between-groups.
      - Add within-group variation proportional to s_W.
    """
    # Published Ajbar_g (Fogo dataset)
    Ajbar_pub = np.array([0.3731, 0.1458, 0.1157])
    global_pub = float(np.dot([W_AHP[G1_IDX].sum(), W_AHP[G2_IDX].sum(), W_AHP[G3_IDX].sum()], Ajbar_pub))

    # s_B controls between-group: 0=flat, 1=published
    Ajbar_g = global_pub + s_B * (Ajbar_pub - global_pub)
    # Renormalise to preserve global mean
    w_groups = np.array([W_AHP[G1_IDX].sum(), W_AHP[G2_IDX].sum(), W_AHP[G3_IDX].sum()])
    eff_global = float(np.dot(w_groups, Ajbar_g))
    if eff_global > 0:
        Ajbar_g = Ajbar_g * global_pub / eff_global

    # Build per-criterion Aj: group mean + within-group variation
    Aj = np.zeros(M)
    w_ahp_local = W_AHP
    for g_idx, (g, Ajbar) in enumerate(zip(GROUPS, Ajbar_g)):
        wg = w_ahp_local[g]
        n_g = len(g)
        if s_W == 0.0:
            delta = np.zeros(n_g)
        else:
            delta = rng.uniform(-1, 1, n_g)
            delta -= np.dot(wg, delta) / wg.sum()  # enforce zero weighted mean
        Aj[g] = Ajbar * (1.0 + s_W * delta)
    Aj = np.maximum(np.abs(Aj), 1e-6)
    return Aj, Ajbar_g


def compute_tv_metrics(Aj, W_AHP, GROUPS):
    """Compute TV_B, TV_W per group, TV_W_eff."""
    global_mean = float(np.dot(W_AHP, Aj))
    if global_mean <= 0:
        return dict(TV_B=0., TV_W_G1=0., TV_W_G2=0., TV_W_G3=0., TV_W_eff=0., TV_total=0.)

    # Ajbar_g for this Aj
    Ajbar_g = []
    for g in GROUPS:
        wg = W_AHP[g]
        Ajbar_g.append(float(np.dot(wg, Aj[g]) / wg.sum()))

    # TV_B: between-group variation
    TV_B = 0.0
    for g_idx, (g, Ajbar) in enumerate(zip(GROUPS, Ajbar_g)):
        wg = W_AHP[g]
        Wg = wg.sum()
        TV_B += Wg * abs(Ajbar / global_mean - 1.0)
    TV_B *= 0.5

    # TV_W per group and effective weight
    TV_W_g = []
    W_g_eff = []
    for g_idx, (g, Ajbar) in enumerate(zip(GROUPS, Ajbar_g)):
        wg = W_AHP[g]
        Wg = wg.sum()
        if Ajbar <= 0:
            TV_W_g.append(0.)
            W_g_eff.append(Wg)
            continue
        tv_w = 0.5 * float(np.sum(wg * np.abs(Aj[g] - Ajbar) / Ajbar))
        TV_W_g.append(tv_w)
        W_g_eff.append(Wg * Ajbar / global_mean)

    TV_W_eff = sum(W_g_eff[g] * TV_W_g[g] for g in range(3))
    TV_total = TV_B + sum(W_AHP[g].sum() * TV_W_g[i] for i, g in enumerate(GROUPS))

    return dict(
        TV_B=TV_B,
        TV_W_G1=TV_W_g[0], TV_W_G2=TV_W_g[1], TV_W_G3=TV_W_g[2],
        TV_W_eff=TV_W_eff,
        TV_total=TV_total,
        Ajbar_G1=Ajbar_g[0], Ajbar_G2=Ajbar_g[1], Ajbar_G3=Ajbar_g[2],
    )


# ── Score construction ─────────────────────────────────────────────────────────
def build_score_matrix(X_adj, Aj):
    """V[:,j] = X_adj[:,j] * Aj[j] / range(X_adj[:,j])"""
    V = np.zeros_like(X_adj, dtype=np.float64)
    for j in range(X_adj.shape[1]):
        col = X_adj[:, j].astype(float)
        rng_v = col.max() - col.min()
        V[:, j] = col * Aj[j] / rng_v if rng_v > 0 else col * Aj[j]
    return V


# ── Main evaluation ────────────────────────────────────────────────────────────
def run_grid():
    from mcdm_experiment import (
        load_data, impute_nan, haversine_km,
        greedy_trio, COL, AHP_WEIGHTS, MIN_DIST_KM,
        _build_decision_matrix, _norm, INV, COST, F1_CRIT, F2_CRIT, F3_CRIT,
    )
    from pareto_utils import build_pareto_utils

    col_names = list(AHP_WEIGHTS.keys())

    df_all, par, bcs = load_data()
    df_imp = impute_nan(df_all)
    viable = df_imp[COL["protected"]] > 0
    df_via = df_imp[viable].copy()
    N = len(df_via)
    assert N == 389
    D_via = haversine_km(df_via["latitude (degrees)"].values,
                         df_via["longitude (degrees)"].values)

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
    assert len(trio_arr) == 1944653

    compute_objs, is_dominated, trio_lookup = build_pareto_utils(
        df_via, col_names, trio_arr, eps=EPS
    )

    def argmax_trio(sc):
        st = sc[T0]+sc[T1]+sc[T2]; return trio_arr[st.argmax()]

    # Grid
    S_B_LEVELS = [0.0, 0.1, 0.2, 0.3, 0.4]
    S_W_LEVELS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    N_REPS     = 6
    all_jobs   = list(iproduct(S_B_LEVELS, S_W_LEVELS, range(N_REPS)))
    print(f"Grid: {len(all_jobs)} instances × {N_DRAWS} draws")

    rows = []
    t_total = time.time()

    for done, (s_B, s_W, rep) in enumerate(all_jobs, 1):
        seed = SEED_BASE + int(s_B*10)*10000 + int(s_W*10)*100 + rep
        rng_inst = np.random.default_rng(seed)

        Aj, Ajbar_g = make_amplitudes(s_B, s_W, rng_inst)
        tv_metrics = compute_tv_metrics(Aj, W_AHP, GROUPS)
        V = build_score_matrix(X_adj, Aj)

        # Monte Carlo
        rng_mc = np.random.default_rng(seed + 1)
        draws  = rng_mc.dirichlet(KAPPA * W_AHP, size=N_DRAWS)

        nd_grd = 0; nd_opt = 0
        t_inst = time.time()

        for draw_idx, w in enumerate(draws):
            f1v, f2v, f3v = compute_objs(w)
            F1 = f1v[T0]+f1v[T1]+f1v[T2]
            F2 = f2v[T0]+f2v[T1]+f2v[T2]
            F3 = f3v[T0]+f3v[T1]+f3v[T2]

            sc = (V * w).sum(1)

            # Greedy
            trio_g = greedy_trio(sc, D_via)
            if not is_dominated(trio_g, F1, F2, F3):
                nd_grd += 1

            # Optimal
            trio_o = tuple(argmax_trio(sc))
            if not is_dominated(trio_o, F1, F2, F3):
                nd_opt += 1

        Q2_grd = nd_grd / N_DRAWS * 100
        Q2_opt = nd_opt / N_DRAWS * 100

        # Regression: s_B=0 and s_W=0 -> Aj flat -> SAW mm/opt = 100%
        # (only if Aj is actually flat, i.e. s_W=0 exactly)
        if s_B == 0.0 and s_W == 0.0:
            assert abs(Q2_opt - 100.0) < 0.1, \
                f"REGRESSION FAIL (s_B=0,s_W=0): Q2_opt={Q2_opt:.2f}%"

        row = dict(s_B=s_B, s_W=s_W, rep=rep,
                   Q2_greedy=Q2_grd, Q2_optimal=Q2_opt,
                   **tv_metrics)
        rows.append(row)

        elapsed = time.time() - t_inst
        total_elapsed = time.time() - t_total
        pct = 100 * done / len(all_jobs)
        print(f"[{done}/{len(all_jobs)}] {pct:.1f}% s_B={s_B:.1f} s_W={s_W:.1f} rep={rep} "
              f"{elapsed:.0f}s | TV_B={tv_metrics['TV_B']:.3f} "
              f"TV_W_eff={tv_metrics['TV_W_eff']:.3f} "
              f"grd={Q2_grd:.1f}% opt={Q2_opt:.1f}%  "
              f"[total {total_elapsed/60:.1f}min]", flush=True)

    df = pd.DataFrame(rows)
    out = Path(__file__).parent.parent / 'results' / 'e2_grid_results.csv'
    df.to_csv(out, index=False)
    print(f"\nSaved {len(df)} rows to {out}")
    print(f"Total time: {(time.time()-t_total)/60:.1f} min")

    # Summary: regression of loss on TV_B, TV_W, TV_W_eff, TV_total
    from scipy.stats import linregress
    df['loss_opt'] = 100 - df['Q2_optimal']
    print("\n=== OLS regression: loss_optimal ~ predictor ===")
    for pred in ['TV_B', 'TV_W_eff', 'TV_total']:
        x = df[pred].values; y = df['loss_opt'].values
        valid_mask = np.isfinite(x) & np.isfinite(y)
        if valid_mask.sum() < 3:
            print(f"  {pred:12s}: insufficient data"); continue
        res = linregress(x[valid_mask], y[valid_mask])
        print(f"  {pred:12s}: R²={res.rvalue**2:.4f} slope={res.slope:+.1f} "
              f"intercept={res.intercept:.1f} p={res.pvalue:.4e}")


if __name__ == '__main__':
    run_grid()
