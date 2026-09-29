# -*- coding: utf-8 -*-
"""
WP4 — Synthetic instance grid for external validity (240 instances).

Design (--calibrate):
  20 levels of zero-mass p0 in {0, 0.05, ..., 0.95}  ×
  3 marginal shapes {normal, lognormal, bimodal}  ×
  4 replications  = 240 instances.

Each instance reuses the Fogo distance matrix (N=389 sites, ~1.94M trios)
and re-draws only the criterion columns, isolating marginal shape from
spatial structure.

Key safeguards:
  1. pareto_front_3d (staircase bisect, O(n log n)) — 4 unit tests before any run.
  2. Regression assert per instance: argmax Σs(a) must be in the frontier.
     Violates prop:p1 and aborts immediately if not.
  3. TV range check before full grid (--calibrate prints TV per cell).

Usage
-----
    # unit tests + pilot (3 instances)
    uv run python scripts/wp4_synthetic.py --pilot

    # calibrate: check TV range across p0 levels
    uv run python scripts/wp4_synthetic.py --calibrate --draws 50

    # full grid (4 workers in parallel)
    uv run python scripts/wp4_synthetic.py --draws 200 --worker 0 --total-workers 4
    uv run python scripts/wp4_synthetic.py --draws 200 --worker 1 --total-workers 4
    uv run python scripts/wp4_synthetic.py --draws 200 --worker 2 --total-workers 4
    uv run python scripts/wp4_synthetic.py --draws 200 --worker 3 --total-workers 4
"""

import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from itertools import product as iproduct

sys.stdout.reconfigure(encoding='utf-8')

# ---------------------------------------------------------------------------
# Import correct Pareto filter
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))
from pareto3d import pareto_front_3d, run_unit_tests

# ---------------------------------------------------------------------------
# Constants from paper
# ---------------------------------------------------------------------------

W_AHP = np.array([
    0.177,  # perm  (G1 siting)
    0.107,  # slope (G1)
    0.107,  # road  (G1)
    0.059,  # urban (G1)
    0.059,  # water (G2 impact)
    0.059,  # coast (G2)
    0.069,  # fault (G2)
    0.069,  # flood (G2)
    0.107,  # aspect(G3 safety)
    0.107,  # elev  (G3)
    0.080,  # land  (G3)
], dtype=float)
W_AHP /= W_AHP.sum()

M = len(W_AHP)
K = 3
N_DRAWS = 500
KAPPA = 50
SEED_BASE = 20260929
EPS = 1e-9

# Objective groups  G1=cost(min), G2=impact(min), G3=safety(max)
# After complementing cost/impact, all three are larger-is-better.
# The SAW score sum equals F1(eff)+F2(eff)+F3(eff) exactly (eq:scalarisation).
G1 = slice(0, 4)
G2 = slice(4, 8)
G3 = slice(8, 11)
GROUPS = [G1, G2, G3]


# ---------------------------------------------------------------------------
# Normalisations (larger-is-better output)
# ---------------------------------------------------------------------------

def minmax_norm(X: np.ndarray) -> np.ndarray:
    lo, hi = X.min(axis=0), X.max(axis=0)
    rng = np.where(hi > lo, hi - lo, 1.0)
    return (X - lo) / rng


def vector_norm(X: np.ndarray) -> np.ndarray:
    norms = np.sqrt((X ** 2).sum(axis=0))
    return X / np.where(norms > 0, norms, 1.0)


# ---------------------------------------------------------------------------
# TV helper
# ---------------------------------------------------------------------------

def total_variation(w_eff, w):
    return 0.5 * float(np.abs(w_eff - w).sum())


def tv_from_norm(V, w, alpha=1.0):
    A = V.max(axis=0) - V.min(axis=0)
    num = (w ** alpha) * (A ** alpha)
    s = num.sum()
    return total_variation(num / s, w) if s > 1e-30 else 0.0


# ---------------------------------------------------------------------------
# Criterion generator
# ---------------------------------------------------------------------------

def generate_criteria(n, m, p0, shape, rng):
    """Raw criterion matrix (n, m) with p0 mass at zero."""
    X = np.zeros((n, m), dtype=float)
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
        else:
            raise ValueError(shape)
        X[nz, j] = v
    return X


# ---------------------------------------------------------------------------
# Fogo trio index loader
# ---------------------------------------------------------------------------

def load_fogo_trios(data_dir: Path) -> np.ndarray:
    npy = data_dir / 'fogo_trios.npy'
    csv = data_dir / 'fogo_trios.csv'
    if npy.exists():
        trios = np.load(npy)
        print(f"Loaded {len(trios):,} Fogo trios from {npy}")
        return trios.astype(np.int32)
    if csv.exists():
        trios = pd.read_csv(csv, header=None).values.astype(np.int32)
        np.save(npy, trios)
        return trios
    raise FileNotFoundError(
        f"Fogo trio index not found at {npy}.\n"
        "Run: uv run python scripts/export_fogo_trios.py"
    )


# ---------------------------------------------------------------------------
# Instance evaluator
# ---------------------------------------------------------------------------

def evaluate_instance(fogo_trios, X_raw, w_ahp, n_draws, kappa, seed):
    """
    Evaluate one instance for both min-max and vector normalisation.
    Uses pareto_front_3d (correct O(n log n) staircase) pre-computed
    with nominal weights. Includes regression assert per draw.
    """
    rng = np.random.default_rng(seed)
    results = {}

    for norm_name, norm_fn in [('minmax', minmax_norm), ('vector', vector_norm)]:
        V = norm_fn(X_raw)
        tv1 = tv_from_norm(V, w_ahp, alpha=1.0)
        tv2 = tv_from_norm(V, w_ahp, alpha=2.0)

        # Pre-compute objectives and Pareto front with nominal weights (1×)
        site_obj_nom = np.stack([V[:, g] @ w_ahp[g] for g in GROUPS], axis=1)
        trio_obj_nom = site_obj_nom[fogo_trios].sum(axis=1)  # (n_trios, 3) larger-is-better

        is_nd = pareto_front_3d(trio_obj_nom)
        front_nom = trio_obj_nom[is_nd]
        R = trio_obj_nom.max(axis=0) - trio_obj_nom.min(axis=0)
        R = np.where(R > 0, R, 1.0)

        # Regression assert: SAW optimal trio must be on frontier (prop:p1)
        saw_scores = V @ w_ahp
        trio_saw = saw_scores[fogo_trios].sum(axis=1)
        best_nom = int(trio_saw.argmax())
        assert is_nd[best_nom], (
            f"REGRESSION FAILED [{norm_name}]: SAW optimal trio {best_nom} "
            f"is not on the nominal frontier. "
            f"This violates prop:p1 (Pareto consistency of optimal linear aggregation). "
            f"tv1={tv1:.4f}, |front|={is_nd.sum()}"
        )

        # MC draws
        q2_list, q3_list = [], []
        for _ in range(n_draws):
            w = rng.dirichlet(kappa * w_ahp)
            w /= w.sum()
            scores = V @ w
            trio_scores = scores[fogo_trios].sum(axis=1)
            best_idx = int(trio_scores.argmax())
            q2_list.append(float(is_nd[best_idx]))
            f_best = trio_obj_nom[best_idx]
            diffs = (front_nom - f_best[np.newaxis, :]) / R[np.newaxis, :]
            q3_list.append(float(max(0.0, diffs.min(axis=1).max())))

        results[norm_name] = {
            'tv1': tv1, 'tv2': tv2,
            'front_size': int(is_nd.sum()),
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
    parser.add_argument('--pilot', action='store_true')
    parser.add_argument('--calibrate', action='store_true',
                        help='p0 up to 0.95, report TV range')
    parser.add_argument('--draws', type=int, default=N_DRAWS)
    parser.add_argument('--worker', type=int, default=0)
    parser.add_argument('--total-workers', type=int, default=1)
    args = parser.parse_args()

    # Unit tests first — fail loud before any computation
    print("Running unit tests...")
    run_unit_tests(verbose=True)

    data_dir = Path(__file__).parent.parent / 'data'
    out_dir  = Path(__file__).parent.parent / 'results'
    out_dir.mkdir(exist_ok=True)

    fogo_trios = load_fogo_trios(data_dir)
    N_FOGO = int(fogo_trios.max()) + 1
    print(f"N_FOGO={N_FOGO}, n_trios={len(fogo_trios):,}")

    p0_levels = np.linspace(0, 0.95, 20) if args.calibrate else np.linspace(0, 0.50, 11)
    shapes = ['normal', 'lognormal', 'bimodal']
    n_reps = 4
    n_draws = args.draws

    all_jobs = list(iproduct(p0_levels, shapes, range(n_reps)))
    worker, n_workers = args.worker, args.total_workers
    my_jobs  = [j for i, j in enumerate(all_jobs) if i % n_workers == worker]
    suffix   = f'_w{worker}' if n_workers > 1 else ''

    if args.pilot:
        my_jobs = [(0.0,'normal',0),(0.25,'lognormal',0),(0.50,'bimodal',0),(0.90,'normal',0)]
        print(f"\n=== PILOT: {len(my_jobs)} instances, draws={n_draws} ===")

    print(f"Worker {worker}/{n_workers}: {len(my_jobs)} instances, draws={n_draws}")

    rows = []
    import time
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
        print(df.groupby('norm')[['Q2', 'Q3', 'tv1']].mean().round(4).to_string())
        print("\n=== Q2 and tv1 by (p0, norm) ===")
        pivot = df.groupby(['p0', 'norm'])[['Q2', 'tv1']].mean().unstack('norm')
        print(pivot.round(3).to_string())

    print(f"\nCONCLUÍDO worker={worker}")


if __name__ == '__main__':
    main()
