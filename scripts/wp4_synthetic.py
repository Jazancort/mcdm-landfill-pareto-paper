# -*- coding: utf-8 -*-
"""
WP4 v5 — Synthetic instance grid (240 instances, ~36 min with 4 workers).

Design
------
Factors:
  N_SPARSE ∈ {0,1,2,3,4}   — number of sparse criteria (highest-weight first)
  P0_SPARSE ∈ {0.5,0.75,0.9,0.95} — zero-mass fraction on sparse criteria
  SHAPE ∈ {lognormal, bimodal}
  6 replications
  = 5×4×2×6 = 240 instances

Four cells per instance (parallel to article factorial):
  (1) SAW · min-max · optimal   → Q2=1 always (regression test)
  (2) SAW · min-max · greedy    → combinatorial loss only
  (3) SAW · vector  · greedy    → combinatorial + re-weighting
  (4) SAW · vector  · optimal   → re-weighting only (wsc≠wob)

Objectives F_ℓ always use min-max normalisation (§8.5 recommendation).
Score uses the cell's own normalisation.

Correctness safeguards:
  - pareto_front_3d (4-test staircase): run once with --test
  - Regression assert: cell (1) must give Q2=1.000 on every instance
  - greedy derived from fogo_trios — no distance matrix needed
"""

import os
os.environ.setdefault("OMP_NUM_THREADS",      "1")
os.environ.setdefault("MKL_NUM_THREADS",      "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS",  "1")

import sys, argparse, time
import numpy as np
import pandas as pd
from pathlib import Path
from itertools import product as iproduct

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent))
from pareto3d import pareto_front_3d, run_unit_tests

# ---------------------------------------------------------------------------
# Constants — weights from mcdm_experiment.py (Table 7, IEEE Access 2026)
# Order: perm, slope, roads, rivers, aspect, coast, protected, wells,
#        urban, aero, cult
# G1=siting efficiency (F1): perm,slope,roads,rivers (indices 0-3)
# G2=environmental integrity (F2): aspect,coast,protected,wells (indices 4-7)
# G3=social safety (F3): urban,aero,cult (indices 8-10)
# ---------------------------------------------------------------------------
W_AHP = np.array([
    0.152, 0.113, 0.030, 0.091,   # G1: perm, slope, roads, rivers
    0.075, 0.069, 0.066, 0.055,   # G2: aspect, coast, protected, wells
    0.166, 0.102, 0.081,           # G3: urban, aero, cult
], dtype=np.float32)
assert abs(float(W_AHP.sum()) - 1.0) < 1e-5, "weights must sum to 1"

# Criteria sorted by weight descending — sparse applied to highest-weight first
# Correct order: urban(0.166), perm(0.152), slope(0.113), aero(0.102), ...
SPARSE_ORDER = np.argsort(-W_AHP)

M = len(W_AHP)
G1, G2, G3 = slice(0, 4), slice(4, 8), slice(8, 11)
GROUPS = [G1, G2, G3]

N_DRAWS   = 200
KAPPA     = 50
SEED_BASE = 20261001
EPS       = np.float32(1e-6)
BATCH     = 20


# ---------------------------------------------------------------------------
# Normalisations (float32 output)
# ---------------------------------------------------------------------------
def minmax_norm(X):
    lo, hi = X.min(0), X.max(0)
    return ((X - lo) / np.where(hi > lo, hi - lo, 1.0)).astype(np.float32)

def vector_norm(X):
    norms = np.sqrt((X ** 2).sum(0))
    return (X / np.where(norms > 0, norms, 1.0)).astype(np.float32)

def tv_from_norm(V, w, alpha=1.0):
    A = V.max(0) - V.min(0)
    num = (w ** alpha) * (A ** alpha)
    s = num.sum()
    if s < 1e-30: return 0.0
    return 0.5 * float(np.abs(num / s - w).sum())


# ---------------------------------------------------------------------------
# Criterion generator — sparse on N_SPARSE highest-weight criteria
# ---------------------------------------------------------------------------
def generate_criteria(n, m, n_sparse, p0_sparse, shape, rng):
    """
    Generate (n, m) criterion matrix.
    The n_sparse criteria with highest AHP weights get zero-mass p0_sparse;
    the remaining criteria are drawn from a continuous uniform-ish distribution.
    """
    X = np.zeros((n, m), dtype=np.float32)
    sparse_set = set(SPARSE_ORDER[:n_sparse].tolist())

    for j in range(m):
        p0 = p0_sparse if j in sparse_set else 0.0
        nz = ~(rng.random(n) < p0)
        k  = int(nz.sum())
        if k == 0:
            continue
        if j in sparse_set:
            # Sparse: lognormal or bimodal tail
            if shape == 'lognormal':
                v = rng.lognormal(-0.7, 0.6, k)
                lo, hi = v.min(), v.max()
                v = (v - lo) / (hi - lo + 1e-12)
            else:  # bimodal
                h = k // 2
                v = np.concatenate([rng.normal(0.2, 0.07, h).clip(0, 1),
                                     rng.normal(0.8, 0.07, k-h).clip(0, 1)])
                rng.shuffle(v)
        else:
            # Continuous: normal (like geographic distances)
            v = rng.normal(0.5, 0.2, k).clip(1e-6, 1.0)
        X[nz, j] = v.astype(np.float32)
    return X


# ---------------------------------------------------------------------------
# Fogo trio loader (int16)
# ---------------------------------------------------------------------------
def load_fogo_trios(data_dir):
    npy = data_dir / 'fogo_trios.npy'
    if not npy.exists():
        raise FileNotFoundError(f"fogo_trios.npy not found at {npy}")
    trios = np.load(npy).astype(np.int16)
    print(f"Loaded {len(trios):,} trios ({trios.nbytes/1e6:.1f} MB int16)")
    return trios


# ---------------------------------------------------------------------------
# Compatibility matrix from trios (no distance matrix needed)
# ok[u,v] = True iff d(u,v) >= d_min AND there exists w compatible with both
# ---------------------------------------------------------------------------
def load_ok_matrix(data_dir, trios_i16, N):
    """Load pre-computed ok_matrix.npy or build and save if missing."""
    npy = data_dir / 'ok_matrix.npy'
    if npy.exists():
        ok = np.load(npy)
        print(f"Loaded ok_matrix from {npy.name} ({ok.nbytes/1024:.0f} KB)")
        return ok
    print("Building compatibility matrix from trios...")
    ok = np.zeros((N, N), dtype=bool)
    t = trios_i16.astype(np.int32)
    for a, b in ((0, 1), (0, 2), (1, 2)):
        ok[t[:, a], t[:, b]] = True
        ok[t[:, b], t[:, a]] = True
    np.save(npy, ok)
    print(f"Saved ok_matrix: {ok.nbytes/1024:.0f} KB")
    return ok


# ---------------------------------------------------------------------------
# Greedy assembly
# ---------------------------------------------------------------------------
def greedy_trio_idx(site_scores, ok, trios_i16):
    """
    Greedy: pick sites in descending score order, keep if compatible with all chosen.
    Returns the index of the resulting trio in fogo_trios, or -1 if not found.
    """
    order = np.argsort(-site_scores)
    chosen = []
    for s in order:
        si = int(s)
        if all(ok[si, c] for c in chosen):
            chosen.append(si)
            if len(chosen) == 3:
                break
    if len(chosen) < 3:
        return -1
    c0, c1, c2 = np.int16(sorted(chosen))
    mask = (trios_i16[:, 0] == c0) & (trios_i16[:, 1] == c1) & (trios_i16[:, 2] == c2)
    idx = np.where(mask)[0]
    return int(idx[0]) if len(idx) > 0 else -1


# ---------------------------------------------------------------------------
# C matrix, Wg, dominance query
# ---------------------------------------------------------------------------
def build_C(V_f32, trios_i16):
    t = trios_i16.astype(np.int32)
    return (V_f32[t[:, 0]] + V_f32[t[:, 1]] + V_f32[t[:, 2]])  # (n,M) float32

def build_Wg(w_f32):
    Wg = np.zeros((M, 3), dtype=np.float32)
    for ell, g in enumerate(GROUPS):
        Wg[g, ell] = w_f32[g]
    return Wg

def is_dominated_vec(F_f32, best_idx):
    p = F_f32[best_idx]
    for s in range(0, len(F_f32), 100_000):
        e = min(s + 100_000, len(F_f32))
        Fj = F_f32[s:e]
        dom = (Fj >= p - EPS).all(1) & (Fj > p + EPS).any(1)
        if s <= best_idx < e:
            dom[best_idx - s] = False
        if dom.any():
            return True
    return False

def gap_vec(F_f32, best_idx, R_f32):
    p = F_f32[best_idx]
    best_gap = 0.0
    for s in range(0, len(F_f32), 100_000):
        e = min(s + 100_000, len(F_f32))
        Fj = F_f32[s:e]
        dom = (Fj >= p - EPS).all(1) & (Fj > p + EPS).any(1)
        if s <= best_idx < e:
            dom[best_idx - s] = False
        if dom.any():
            diffs = (Fj[dom] - p) / R_f32
            best_gap = max(best_gap, float(diffs.min(1).max()))
    return best_gap


# ---------------------------------------------------------------------------
# Instance evaluator — 4 cells
# ---------------------------------------------------------------------------
def evaluate_instance(fogo_trios, ok, X_raw, w_ahp, n_draws, kappa, seed):
    rng = np.random.default_rng(seed)
    w_f32 = w_ahp.astype(np.float32)

    # Objectives always use min-max normalisation
    V_mm = minmax_norm(X_raw)
    C_mm = build_C(V_mm, fogo_trios)          # (n_trios, M) float32
    Wg_nom = build_Wg(w_f32)
    F_obj = (C_mm @ Wg_nom).astype(np.float32)  # (n_trios, 3) — objective space

    # Pareto front (nominal weights, min-max objectives) — once
    is_nd = pareto_front_3d(F_obj.astype(float))
    front_size = int(is_nd.sum())
    R = (F_obj.max(0) - F_obj.min(0)).astype(np.float32)
    R = np.where(R > 0, R, np.float32(1.0))

    # TV for each score normalisation
    tv_mm = tv_from_norm(V_mm, w_f32)
    V_vec = vector_norm(X_raw)
    tv_vec = tv_from_norm(V_vec, w_f32)
    C_vec  = build_C(V_vec, fogo_trios)

    # Regression assert: SAW/mm/optimal must give Q2=1
    saw_nom = C_mm @ w_f32
    best_nom = int(saw_nom.argmax())
    assert is_nd[best_nom], (
        f"REGRESSION [mm/optimal]: tv_mm={tv_mm:.4f}, |F|={front_size}"
    )

    # Weight draws
    W_draws = rng.dirichlet(kappa * w_f32.astype(float), n_draws).astype(np.float32)
    W_draws /= W_draws.sum(1, keepdims=True)

    # Pre-calculate SAW for optimal assembly
    SAW_mm  = C_mm  @ W_draws.T  # (n_trios, n_draws)
    SAW_vec = C_vec @ W_draws.T  # (n_trios, n_draws)

    # Pre-calculate site scores for greedy assembly (389, n_draws)
    site_scores_mm  = V_mm  @ W_draws.T
    site_scores_vec = V_vec @ W_draws.T

    cell_q2 = {'mm_opt': [], 'mm_grd': [], 'vec_grd': [], 'vec_opt': []}
    cell_q3 = {'mm_opt': [], 'mm_grd': [], 'vec_grd': [], 'vec_opt': []}

    for k in range(n_draws):
        w_k = W_draws[k]

        # Evaluate in objective space (min-max objectives, w of draw)
        Wg_k = build_Wg(w_k)
        F_k  = (C_mm @ Wg_k).astype(np.float32)   # always min-max objectives
        R_k  = (F_k.max(0) - F_k.min(0)).astype(np.float32)
        R_k  = np.where(R_k > 0, R_k, np.float32(1.0))

        idx_mm_opt  = int(SAW_mm[:, k].argmax())
        idx_mm_grd  = greedy_trio_idx(site_scores_mm[:, k], ok, fogo_trios)
        idx_vec_grd = greedy_trio_idx(site_scores_vec[:, k], ok, fogo_trios)
        idx_vec_opt = int(SAW_vec[:, k].argmax())

        draw_indices = {
            'mm_opt':  idx_mm_opt,
            'mm_grd':  idx_mm_grd,
            'vec_grd': idx_vec_grd,
            'vec_opt': idx_vec_opt,
        }

        # Cache dominance queries for this draw so identical trio choices
        # across cells don't scan 1.94M rows multiple times
        dom_cache = {}
        gap_cache = {}

        for cell_name, best_idx in draw_indices.items():
            if best_idx < 0:
                continue
            if best_idx not in dom_cache:
                dom = is_dominated_vec(F_k, best_idx)
                dom_cache[best_idx] = dom
                gap_cache[best_idx] = gap_vec(F_k, best_idx, R_k) if dom else 0.0

            cell_q2[cell_name].append(float(not dom_cache[best_idx]))
            cell_q3[cell_name].append(gap_cache[best_idx])

    results = {'tv_mm': tv_mm, 'tv_vec': tv_vec, 'front_size': front_size}
    for cell_name in ['mm_opt', 'mm_grd', 'vec_grd', 'vec_opt']:
        q2_list = cell_q2[cell_name]
        q3_list = cell_q3[cell_name]
        nd = len(q2_list)
        results[f'Q2_{cell_name}']    = float(np.mean(q2_list)) if nd else float('nan')
        results[f'Q3_{cell_name}']    = float(np.mean(q3_list)) if nd else float('nan')
        results[f'Q2_se_{cell_name}'] = float(np.std(q2_list)/np.sqrt(nd)) if nd > 1 else float('nan')

    del C_mm, C_vec, SAW_mm, SAW_vec
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test',         action='store_true')
    parser.add_argument('--calibrate',    action='store_true',
                        help='12 instances; check TV range and Q2 signal before full grid')
    parser.add_argument('--draws',        type=int, default=N_DRAWS)
    parser.add_argument('--worker',       type=int, default=0)
    parser.add_argument('--total-workers',type=int, default=1)
    args = parser.parse_args()

    if args.test:
        run_unit_tests(verbose=True)
        print("All tests passed.")
        return

    print(f"BLAS: OMP={os.environ.get('OMP_NUM_THREADS')} "
          f"MKL={os.environ.get('MKL_NUM_THREADS')} "
          f"OPENBLAS={os.environ.get('OPENBLAS_NUM_THREADS')}")

    data_dir = Path(__file__).parent.parent / 'data'
    out_dir  = Path(__file__).parent.parent / 'results'
    out_dir.mkdir(exist_ok=True)

    fogo_trios = load_fogo_trios(data_dir)
    N_FOGO = int(fogo_trios.astype(np.int32).max()) + 1
    print(f"N_FOGO={N_FOGO}, n_trios={len(fogo_trios):,}")

    ok = load_ok_matrix(data_dir, fogo_trios, N_FOGO)

    # Grid factors
    N_SPARSE_LEVELS = [0, 1, 2, 3, 4]
    P0_LEVELS       = [0.50, 0.75, 0.90, 0.95]
    SHAPES          = ['lognormal', 'bimodal']
    N_REPS          = 6

    all_jobs = list(iproduct(N_SPARSE_LEVELS, P0_LEVELS, SHAPES, range(N_REPS)))
    worker, n_workers = args.worker, args.total_workers

    if args.calibrate:
        # 12 instances: vary N_SPARSE and P0, 1 shape, 1 rep
        cal_jobs = [(ns, p0, 'lognormal', 0)
                    for ns in [0, 2, 4] for p0 in [0.50, 0.75, 0.90, 0.95]]
        my_jobs = cal_jobs
        suffix  = '_calibrate'
        print(f"\n=== CALIBRATE: {len(my_jobs)} instances, draws={args.draws} ===")
    else:
        my_jobs = [j for i, j in enumerate(all_jobs) if i % n_workers == worker]
        suffix  = f'_w{worker}' if n_workers > 1 else ''

    print(f"Worker {worker}/{n_workers}: {len(my_jobs)} instances")

    rows = []
    for done, (n_sp, p0, shape, rep) in enumerate(my_jobs, 1):
        seed = SEED_BASE + n_sp * 100000 + int(p0 * 1000) * 100 + \
               SHAPES.index(shape) * 10 + rep
        rng_inst = np.random.default_rng(seed)
        X = generate_criteria(N_FOGO, M, n_sp, p0, shape, rng_inst)

        t0 = time.time()
        res = evaluate_instance(fogo_trios, ok, X, W_AHP, args.draws, KAPPA, seed + 1)
        dt = time.time() - t0

        rows.append({'n_sparse': n_sp, 'p0': p0, 'shape': shape, 'rep': rep, **res})

        pct = 100 * done / len(my_jobs)
        print(f"[{done}/{len(my_jobs)}] {pct:.1f}% n_sp={n_sp} p0={p0:.2f} {shape} "
              f"rep{rep} {dt:.0f}s | "
              f"tv_mm={res['tv_mm']:.3f} tv_vec={res['tv_vec']:.3f} "
              f"|F|={res['front_size']} | "
              f"mm/opt={res.get('Q2_mm_opt',0):.3f} "
              f"mm/grd={res.get('Q2_mm_grd',0):.3f} "
              f"vec/grd={res.get('Q2_vec_grd',0):.3f} "
              f"vec/opt={res.get('Q2_vec_opt',0):.3f}")
        sys.stdout.flush()

    df = pd.DataFrame(rows)
    csv_out = out_dir / f'wp4_synthetic{suffix}.csv'
    df.to_csv(csv_out, index=False)
    print(f"\nSaved {len(df)} rows to {csv_out}")

    if args.calibrate or n_workers == 1:
        print("\n=== TV range achieved ===")
        print(df[['n_sparse','p0','tv_mm','tv_vec']].groupby(
            ['n_sparse','p0']).mean().round(3).to_string())
        print("\n=== Q2 by cell (mean) ===")
        q2_cols = [c for c in df.columns if c.startswith('Q2_')]
        print(df[q2_cols].mean().round(3).to_string())
        print("\n=== Regression check: mm/opt must be 1.000 ===")
        bad = df[df['Q2_mm_opt'] < 0.999]
        if len(bad):
            print(f"WARNING: {len(bad)} instances with Q2_mm_opt < 1")
            print(bad[['n_sparse','p0','shape','rep','Q2_mm_opt']].to_string())
        else:
            print("OK — all instances Q2_mm_opt = 1.000")

    print(f"\nCONCLUÍDO worker={worker}")


if __name__ == '__main__':
    main()
