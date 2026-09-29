# -*- coding: utf-8 -*-
"""
WP4 — Synthetic instance grid, optimised (240 instances).

Key changes vs previous version:
  - OMP/MKL/OPENBLAS_NUM_THREADS=1 set at import time (no BLAS serialisation)
  - Unit test suite removed from worker startup (run separately with --test)
  - Criterion matrix C pre-computed once per instance: C[t,j] = sum_i∈t cj(i)
    Objectives: F = C @ Wg  (n_trios × 3) — 5× faster than fancy-index gather
  - Per-draw: dominance query O(n) instead of full Pareto front
    Q2 = is best trio dominated by any other? (vectorised check)
    Q3 = gap of best trio against its dominator set
  - Full Pareto front computed once per instance (nominal weights) for |F| reporting
  - Regression assert: argmax SAW ∈ F  via O(n) dominance check

Usage
-----
    # unit tests (run once, separately)
    uv run python scripts/wp4_synthetic.py --test

    # pilot (3 instances, verify correctness and timing)
    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \\
        uv run python scripts/wp4_synthetic.py --pilot --draws 200

    # full grid, 4 workers in parallel
    for W in 0 1 2 3; do
      OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \\
          uv run python scripts/wp4_synthetic.py \\
          --calibrate --draws 200 --worker $W --total-workers 4 &
    done
"""

import os
# Single-threaded BLAS — must be set before numpy import
os.environ.setdefault("OMP_NUM_THREADS",      "1")
os.environ.setdefault("MKL_NUM_THREADS",      "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS",  "1")

import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from itertools import product as iproduct

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent))
from pareto3d import pareto_front_3d, run_unit_tests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

W_AHP = np.array([
    0.177, 0.107, 0.107, 0.059,  # G1 siting
    0.059, 0.059, 0.069, 0.069,  # G2 impact
    0.107, 0.107, 0.080,          # G3 safety
], dtype=np.float64)
W_AHP /= W_AHP.sum()

M = len(W_AHP)
G1, G2, G3 = slice(0, 4), slice(4, 8), slice(8, 11)
GROUPS = [G1, G2, G3]
G_sizes = [4, 4, 3]

N_DRAWS = 500
KAPPA   = 50
SEED_BASE = 20260929
EPS = 1e-9


# ---------------------------------------------------------------------------
# Normalisations
# ---------------------------------------------------------------------------

def minmax_norm(X):
    lo, hi = X.min(0), X.max(0)
    return (X - lo) / np.where(hi > lo, hi - lo, 1.0)


def vector_norm(X):
    norms = np.sqrt((X ** 2).sum(0))
    return X / np.where(norms > 0, norms, 1.0)


def tv_from_norm(V, w, alpha=1.0):
    A = V.max(0) - V.min(0)
    num = (w ** alpha) * (A ** alpha)
    s = num.sum()
    if s < 1e-30:
        return 0.0
    w_eff = num / s
    return 0.5 * float(np.abs(w_eff - w).sum())


# ---------------------------------------------------------------------------
# Criterion generator
# ---------------------------------------------------------------------------

def generate_criteria(n, m, p0, shape, rng):
    X = np.zeros((n, m))
    for j in range(m):
        nz = ~(rng.random(n) < p0)
        k = int(nz.sum())
        if k == 0:
            continue
        if shape == 'normal':
            v = rng.normal(0.5, 0.2, k).clip(1e-6, 1.0)
        elif shape == 'lognormal':
            v = rng.lognormal(-0.7, 0.6, k)
            lo, hi = v.min(), v.max()
            v = (v - lo) / (hi - lo + 1e-12)
        elif shape == 'bimodal':
            h = k // 2
            v = np.concatenate([rng.normal(0.2, 0.07, h).clip(0, 1),
                                 rng.normal(0.8, 0.07, k - h).clip(0, 1)])
            rng.shuffle(v)
        X[nz, j] = v
    return X


# ---------------------------------------------------------------------------
# Fogo trio loader
# ---------------------------------------------------------------------------

def load_fogo_trios(data_dir):
    npy = data_dir / 'fogo_trios.npy'
    if npy.exists():
        trios = np.load(npy)
        print(f"Loaded {len(trios):,} trios from {npy}")
        return trios.astype(np.int32)
    raise FileNotFoundError(
        f"fogo_trios.npy not found at {npy}.\n"
        "Run: uv run python scripts/export_fogo_trios.py"
    )


# ---------------------------------------------------------------------------
# Pre-compute criterion sum matrix C  (n_trios × M)
# C[t, j] = sum_{i in t} V[i, j]
# Then F_group_ell(t; w) = sum_{j in G_ell} w_j * C[t, j]
# Vectorised: F = C @ Wg  where Wg[j, ell] = w_j if j in G_ell else 0
# ---------------------------------------------------------------------------

def build_C(V, trios):
    """Build criterion sum matrix C (n_trios, M) in float32."""
    n_trios, M = len(trios), V.shape[1]
    i0, i1, i2 = trios[:, 0], trios[:, 1], trios[:, 2]
    C = (V[i0] + V[i1] + V[i2]).astype(np.float32)  # (n_trios, M)
    return C


def build_Wg(w):
    """Build weight-group matrix Wg (M, 3) from weight vector w."""
    Wg = np.zeros((M, 3), dtype=np.float64)
    for ell, g in enumerate(GROUPS):
        Wg[g, ell] = w[g]
    return Wg


def objectives_from_C(C, w):
    """F = C @ Wg  shape (n_trios, 3), all objectives larger-is-better."""
    Wg = build_Wg(w)
    return (C @ Wg).astype(np.float32)          # (n_trios, 3)


# ---------------------------------------------------------------------------
# O(n) dominance query — is point p dominated by any row in F?
# ---------------------------------------------------------------------------

def is_dominated(F, p_idx, eps=EPS):
    """
    True if F[p_idx] is dominated by any other row of F.
    Vectorised: O(n) with numpy broadcasting in chunks.
    """
    p = F[p_idx]
    chunk = 50_000
    n = len(F)
    for start in range(0, n, chunk):
        end = min(start + chunk, n)
        Fj = F[start:end]
        dom = ((Fj >= p - eps).all(axis=1) &
               (Fj > p + eps).any(axis=1))
        # exclude self
        if start <= p_idx < end:
            dom[p_idx - start] = False
        if dom.any():
            return True
    return False


def gap_from_F(F, p_idx, R, eps=EPS):
    """
    Scale-free gap of F[p_idx] against its dominator set.
    gap = max(0, max_{j dominates p} min_ell (F[j,ell] - F[p,ell]) / R[ell])
    O(n), vectorised.
    """
    p = F[p_idx]
    chunk = 50_000
    n = len(F)
    best_gap = 0.0
    for start in range(0, n, chunk):
        end = min(start + chunk, n)
        Fj = F[start:end]
        dom = ((Fj >= p - eps).all(axis=1) &
               (Fj > p + eps).any(axis=1))
        if start <= p_idx < end:
            dom[p_idx - start] = False
        if dom.any():
            diffs = (Fj[dom] - p[np.newaxis, :]) / R[np.newaxis, :]
            best_gap = max(best_gap, float(diffs.min(axis=1).max()))
    return best_gap


# ---------------------------------------------------------------------------
# Instance evaluator
# ---------------------------------------------------------------------------

def evaluate_instance(fogo_trios, X_raw, w_ahp, n_draws, kappa, seed):
    rng = np.random.default_rng(seed)
    results = {}

    for norm_name, norm_fn in [('minmax', minmax_norm), ('vector', vector_norm)]:
        V = norm_fn(X_raw)                          # (N, M)
        tv1 = tv_from_norm(V, w_ahp, alpha=1.0)
        tv2 = tv_from_norm(V, w_ahp, alpha=2.0)

        # --- Pre-compute C once per normalisation ---
        C = build_C(V, fogo_trios)                  # (n_trios, M) float32

        # --- Nominal objectives and full Pareto front (for |F| and regression) ---
        F_nom = objectives_from_C(C, w_ahp)         # (n_trios, 3) float32
        is_nd_nom = pareto_front_3d(F_nom.astype(float))
        front_size = int(is_nd_nom.sum())

        # Regression assert: SAW optimal trio must be on nominal frontier (prop:p1)
        saw_scores = V @ w_ahp
        i0, i1, i2 = fogo_trios[:, 0], fogo_trios[:, 1], fogo_trios[:, 2]
        trio_saw = saw_scores[i0] + saw_scores[i1] + saw_scores[i2]
        best_nom = int(trio_saw.argmax())
        assert is_nd_nom[best_nom], (
            f"REGRESSION [{norm_name}]: SAW optimal not on nominal frontier. "
            f"tv1={tv1:.4f}, |F|={front_size}"
        )

        R = F_nom.max(axis=0) - F_nom.min(axis=0)
        R = np.where(R > 0, R, 1.0).astype(np.float32)

        # --- Monte Carlo: per-draw dominance query against NOMINAL front ---
        # Q2 = is the best trio (by perturbed weights) in the NOMINAL Pareto front?
        # This matches the original definition: Q2 = Pr[M(w) ∈ F(w_nom)]
        # Note: we cannot use per-draw frontier (that would trivially give Q2=1
        # for SAW by prop:p1). Instead we use the nominal frontier as the
        # reference — consistent with the paper's experimental design.
        q2_list, q3_list = [], []
        for _ in range(n_draws):
            w = rng.dirichlet(kappa * w_ahp)
            w /= w.sum()

            # Best trio by SAW with perturbed weights (sum over all criteria)
            saw_w = C @ w                             # (n_trios,) — SAW scores
            best_idx = int(saw_w.argmax())

            # Q2: is best_idx in the NOMINAL Pareto front?
            q2_list.append(float(is_nd_nom[best_idx]))

            # Q3: gap of best_idx against nominal front
            f_best = F_nom[best_idx]
            if not is_nd_nom[best_idx]:
                diffs = (F_nom[is_nd_nom] - f_best[np.newaxis, :]) / R[np.newaxis, :]
                q3_list.append(float(max(0.0, diffs.min(axis=1).max())))
            else:
                q3_list.append(0.0)

        results[norm_name] = {
            'tv1': tv1, 'tv2': tv2,
            'front_size': front_size,
            'Q2': float(np.mean(q2_list)),
            'Q3': float(np.mean(q3_list)),
            'Q2_se': float(np.std(q2_list) / np.sqrt(n_draws)),
            'Q3_se': float(np.std(q3_list) / np.sqrt(n_draws)),
        }

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test',      action='store_true', help='Run unit tests and exit')
    parser.add_argument('--pilot',     action='store_true', help='3 pilot instances')
    parser.add_argument('--calibrate', action='store_true', help='p0 up to 0.95')
    parser.add_argument('--draws',     type=int, default=N_DRAWS)
    parser.add_argument('--worker',       type=int, default=0)
    parser.add_argument('--total-workers',type=int, default=1)
    args = parser.parse_args()

    if args.test:
        run_unit_tests(verbose=True)
        print("All unit tests passed.")
        return

    # In worker mode, skip full unit suite — regression assert protects each instance
    print(f"BLAS threads: OMP={os.environ.get('OMP_NUM_THREADS','?')} "
          f"MKL={os.environ.get('MKL_NUM_THREADS','?')} "
          f"OPENBLAS={os.environ.get('OPENBLAS_NUM_THREADS','?')}")

    data_dir = Path(__file__).parent.parent / 'data'
    out_dir  = Path(__file__).parent.parent / 'results'
    out_dir.mkdir(exist_ok=True)

    fogo_trios = load_fogo_trios(data_dir)
    N_FOGO = int(fogo_trios.max()) + 1
    print(f"N_FOGO={N_FOGO}, n_trios={len(fogo_trios):,}")

    p0_levels = np.linspace(0, 0.95, 20) if args.calibrate else np.linspace(0, 0.50, 11)
    shapes    = ['normal', 'lognormal', 'bimodal']
    n_reps    = 4
    n_draws   = args.draws

    all_jobs = list(iproduct(p0_levels, shapes, range(n_reps)))
    worker, n_workers = args.worker, args.total_workers
    my_jobs  = [j for i, j in enumerate(all_jobs) if i % n_workers == worker]
    suffix   = f'_w{worker}' if n_workers > 1 else ''

    if args.pilot:
        my_jobs = [(0.0,'normal',0),(0.25,'lognormal',0),(0.50,'bimodal',0),(0.90,'normal',0)]
        print(f"\n=== PILOT: {len(my_jobs)} instances, draws={n_draws} ===")

    print(f"Worker {worker}/{n_workers}: {len(my_jobs)} instances, draws={n_draws}")

    import time
    rows = []
    for done, (p0, shape, rep) in enumerate(my_jobs, 1):
        seed = SEED_BASE + int(round(p0 * 1000)) * 10000 + shapes.index(shape) * 100 + rep
        rng_inst = np.random.default_rng(seed)
        X = generate_criteria(N_FOGO, M, p0, shape, rng_inst)
        t0 = time.time()
        res = evaluate_instance(fogo_trios, X, W_AHP, n_draws, KAPPA, seed + 1)
        dt = time.time() - t0

        for norm_name, vals in res.items():
            rows.append({'p0': round(p0, 3), 'shape': shape, 'rep': rep,
                         'norm': norm_name, **vals})

        pct = 100 * done / len(my_jobs)
        print(f"[{done}/{len(my_jobs)}] {pct:.1f}% p0={p0:.2f} {shape} rep{rep} {dt:.0f}s | "
              f"mm tv1={res['minmax']['tv1']:.3f} Q2={res['minmax']['Q2']:.3f} "
              f"|F|={res['minmax']['front_size']} | "
              f"vec tv1={res['vector']['tv1']:.3f} Q2={res['vector']['Q2']:.3f} "
              f"|F|={res['vector']['front_size']}")
        sys.stdout.flush()

    df = pd.DataFrame(rows)
    csv_out = out_dir / f'wp4_synthetic{suffix}.csv'
    df.to_csv(csv_out, index=False)
    print(f"\nSaved {len(df)} rows to {csv_out}")

    if n_workers == 1 or args.pilot:
        print("\n=== Summary by norm ===")
        print(df.groupby('norm')[['Q2','Q3','tv1']].mean().round(4).to_string())
        print("\n=== Q2 and tv1 by (p0, norm) ===")
        pivot = df.groupby(['p0','norm'])[['Q2','tv1']].mean().unstack('norm')
        print(pivot.round(3).to_string())

    print(f"\nCONCLUÍDO worker={worker}")


if __name__ == '__main__':
    main()
