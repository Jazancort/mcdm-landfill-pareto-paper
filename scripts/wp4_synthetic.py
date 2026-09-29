# -*- coding: utf-8 -*-
"""
WP4 — Synthetic instance grid for external validity (132 instances).

Design
------
Grid: 11 levels of zero-mass p0 in {0, 0.05, ..., 0.50}  ×
      3 marginal shapes {normal, lognormal, bimodal}  ×
      4 replications  = 132 instances.

Each instance reuses the Fogo distance matrix (N=389 sites, ~1.94M trios)
and re-draws only the criterion columns, so the combinatorial structure
matches the real problem while marginal shapes are varied.

p0 extends to 0.95 in calibration mode (--calibrate flag) to sweep TV
in [0, 0.5] before committing to the full grid.

Outputs
-------
results/wp4_synthetic.csv   — one row per instance × normalisation
results/wp4_summary.csv     — mean Q2/Q3 by (p0, shape, normalisation)

Usage
-----
    # calibration (3 instances, measure TV range and time)
    uv run python scripts/wp4_synthetic.py --pilot

    # full grid
    uv run python scripts/wp4_synthetic.py
"""

import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from itertools import product as iproduct

sys.stdout.reconfigure(encoding='utf-8')

# ---------------------------------------------------------------------------
# Constants from paper
# ---------------------------------------------------------------------------

W_AHP = np.array([
    0.177,  # perm  (G1)
    0.107,  # slope (G1)
    0.107,  # road  (G1)
    0.059,  # urban (G1)
    0.059,  # water (G2)
    0.059,  # coast (G2)
    0.069,  # fault (G2)
    0.069,  # flood (G2)
    0.107,  # aspect(G3)
    0.107,  # elev  (G3)
    0.080,  # land  (G3)
], dtype=float)
W_AHP /= W_AHP.sum()

M = len(W_AHP)          # 11 criteria
K = 3                   # portfolio size
N_DRAWS = 500           # weight draws per cell (use 200 if time is tight)
KAPPA = 50              # Dirichlet concentration
SEED_BASE = 20260929
EPS = 1e-9

# Objective groups
G1 = slice(0, 4)
G2 = slice(4, 8)
G3 = slice(8, 11)
GROUPS = [G1, G2, G3]


# ---------------------------------------------------------------------------
# Pareto front — vectorised O(n^2), correct for 3 objectives
# ---------------------------------------------------------------------------

def pareto_front_correct(F: np.ndarray, eps: float = EPS) -> np.ndarray:
    """
    Return boolean mask of non-dominated rows of F (shape n×3), all maximised.

    Correct O(n^2) algorithm, safe for n up to ~50k.
    For n > 50k (e.g. Fogo's 1.94M trios) use pareto_front_large() instead.

    UNIT TEST: P1=(10,10,1), P2=(9,1,10), P3=(8,5,5) — all three non-dominated.
    """
    n = len(F)
    if n == 0:
        return np.zeros(0, dtype=bool)

    dominated = np.zeros(n, dtype=bool)
    chunk = 500

    for start in range(0, n, chunk):
        end = min(start + chunk, n)
        Fi = F[start:end, np.newaxis, :]  # (blk, 1, 3)
        Fj = F[np.newaxis, :, :]          # (1, n, 3)
        weak   = (Fj >= Fi - eps).all(axis=2)  # (blk, n)
        strict = (Fj >  Fi + eps).any(axis=2)  # (blk, n)
        dom    = weak & strict
        # remove self-dominance
        rows = np.arange(start, end)
        dom[rows - start, rows] = False
        dominated[start:end] = dom.any(axis=1)

    return ~dominated


def pareto_front_large(F: np.ndarray, eps: float = EPS) -> np.ndarray:
    """
    Correct Pareto filter for large n (e.g. 1.94M trios).

    Algorithm:
    1. Sort by F0 descending.
    2. For each point, check only against the current non-dominated
       'skyline' (points seen so far that are themselves non-dominated).
    3. The skyline grows slowly (O(n^{2/3}) expected for uniform 3D data),
       so the average cost per point is O(skyline_size), not O(n).

    Passes the same unit test as pareto_front_correct.
    """
    n = len(F)
    if n == 0:
        return np.zeros(0, dtype=bool)

    order = np.lexsort((-F[:, 2], -F[:, 1], -F[:, 0]))
    F_s = F[order]
    nd_s = np.ones(n, dtype=bool)

    # Skyline: list of indices (in sorted order) that are currently ND
    # Convert to numpy array periodically for fast vectorised checks
    sky_idx = []

    for i in range(n):
        fi = F_s[i]
        if not sky_idx:
            sky_idx.append(i)
            continue

        sky = F_s[sky_idx]            # (k, 3)
        # Does any skyline point dominate fi?
        weak   = (sky >= fi - eps).all(axis=1)
        strict = (sky >  fi + eps).any(axis=1)
        if (weak & strict).any():
            nd_s[i] = False
            continue

        # Does fi dominate any skyline point? Remove them.
        dom_by_fi = ((fi >= sky - eps).all(axis=1) &
                     (fi >  sky + eps).any(axis=1))
        if dom_by_fi.any():
            sky_idx = [j for j, d in zip(sky_idx, dom_by_fi) if not d]

        sky_idx.append(i)

    result = np.zeros(n, dtype=bool)
    result[order] = nd_s
    return result


def run_unit_test():
    """Verify both Pareto filters on the documented counterexample."""
    F = np.array([[10, 10, 1],
                  [9,  1, 10],
                  [8,  5,  5]], dtype=float)
    for fn, name in [(pareto_front_correct, 'pareto_front_correct'),
                     (pareto_front_large,   'pareto_front_large')]:
        nd = fn(F)
        assert nd.all(), (
            f"UNIT TEST FAILED ({name}): expected all 3 non-dominated, got {nd}. "
            "The sweep-based filter marks P3 as dominated — "
            "correct filter must return [True, True, True]."
        )
    print("UNIT TEST PASSED: P1, P2, P3 all non-dominated — "
          "both pareto_front_correct and pareto_front_large.")
    return True


# ---------------------------------------------------------------------------
# Normalisations
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

def total_variation(w_eff: np.ndarray, w: np.ndarray) -> float:
    return 0.5 * float(np.abs(w_eff - w).sum())


def tv_from_norm(V: np.ndarray, w: np.ndarray, alpha: float = 1.0) -> float:
    A = V.max(axis=0) - V.min(axis=0)
    num = (w ** alpha) * (A ** alpha)
    s = num.sum()
    if s < 1e-30:
        return 0.0
    return total_variation(num / s, w)


# ---------------------------------------------------------------------------
# Criterion generator
# ---------------------------------------------------------------------------

def generate_criteria(n: int, m: int, p0: float, shape: str,
                      rng: np.random.Generator) -> np.ndarray:
    """
    Raw criterion matrix (n, m) with p0 mass at zero, rest drawn from `shape`.
    Larger-is-better orientation (no complement needed here; normalisation handles it).
    """
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
# Instance evaluator — reuses Fogo trios
# ---------------------------------------------------------------------------

def evaluate_instance(fogo_trios: np.ndarray,
                      X_raw: np.ndarray,
                      w_ahp: np.ndarray,
                      n_draws: int,
                      kappa: float,
                      seed: int) -> dict:
    """
    Evaluate one instance for both min-max and vector normalisation.

    Strategy: pre-compute the Pareto front once using the nominal AHP weights,
    then use it as a fixed reference for all Monte Carlo draws (same approach
    as mcdm_experiment.py). This is O(n) per draw instead of O(n * skyline).

    fogo_trios: (n_trios, 3) integer index array — Fogo spatial structure.
    X_raw: (N, M) raw criterion values (new draw, same sites as Fogo).
    """
    rng = np.random.default_rng(seed)
    results = {}

    for norm_name, norm_fn in [('minmax', minmax_norm), ('vector', vector_norm)]:
        V = norm_fn(X_raw)  # (N, M)
        tv1 = tv_from_norm(V, w_ahp, alpha=1.0)
        tv2 = tv_from_norm(V, w_ahp, alpha=2.0)

        # --- Pre-compute Pareto front with nominal weights (once per cell) ---
        site_obj_nom = np.stack([V[:, g] @ w_ahp[g] for g in GROUPS], axis=1)
        trio_obj_nom = site_obj_nom[fogo_trios].sum(axis=1)   # (n_trios, 3)

        # Use pareto_front_large for 1.94M trios (skyline-based, O(n*|front|))
        is_nd_nom = pareto_front_large(trio_obj_nom)
        front_nom = trio_obj_nom[is_nd_nom]                   # (~181, 3)
        R_nom = trio_obj_nom.max(axis=0) - trio_obj_nom.min(axis=0)
        R_nom = np.where(R_nom > 0, R_nom, 1.0)

        # --- Monte Carlo loop (O(n) per draw — no Pareto computation) ---
        q2_list, q3_list = [], []

        for _ in range(n_draws):
            w = rng.dirichlet(kappa * w_ahp)
            w /= w.sum()

            # SAW scores and optimal assembly
            scores = V @ w
            trio_scores = scores[fogo_trios].sum(axis=1)
            best_idx = int(trio_scores.argmax())

            # Q2: is the best trio on the nominal front?
            q2_list.append(float(is_nd_nom[best_idx]))

            # Q3: gap against nominal front
            f_best = trio_obj_nom[best_idx]
            diffs = (front_nom - f_best[np.newaxis, :]) / R_nom[np.newaxis, :]
            per_member = diffs.min(axis=1)
            q3_list.append(float(max(0.0, per_member.max())))

        results[norm_name] = {
            'tv1': tv1, 'tv2': tv2,
            'front_size': int(is_nd_nom.sum()),
            'Q2': float(np.mean(q2_list)),
            'Q3': float(np.mean(q3_list)),
            'Q2_se': float(np.std(q2_list) / np.sqrt(n_draws)),
            'Q3_se': float(np.std(q3_list) / np.sqrt(n_draws)),
        }

    return results


# ---------------------------------------------------------------------------
# Load Fogo distance-based trio index
# ---------------------------------------------------------------------------

def load_fogo_trios(data_dir: Path) -> np.ndarray:
    """
    Load the pre-computed admissible trio index for Fogo (N=389, ~1.94M trios).
    Expected file: data/fogo_trios.npy  (shape: n_trios x 3, int32)
    or data/fogo_trios.csv.

    If not found, raises FileNotFoundError with instructions.
    """
    npy_path = data_dir / 'fogo_trios.npy'
    csv_path = data_dir / 'fogo_trios.csv'

    if npy_path.exists():
        trios = np.load(npy_path)
        print(f"Loaded {len(trios):,} Fogo trios from {npy_path}")
        return trios.astype(np.int32)

    if csv_path.exists():
        trios = pd.read_csv(csv_path, header=None).values.astype(np.int32)
        print(f"Loaded {len(trios):,} Fogo trios from {csv_path}")
        np.save(npy_path, trios)  # cache for future runs
        return trios

    raise FileNotFoundError(
        f"Fogo trio index not found.\n"
        f"Expected: {npy_path} or {csv_path}\n"
        f"Generate it from the main experiment script:\n"
        f"  uv run python scripts/mcdm_experiment.py --export-trios data/fogo_trios.npy\n"
        f"or extract from the exhaustive enumeration CSV."
    )


def load_fogo_N(data_dir: Path) -> int:
    """Infer number of Fogo sites from trio index."""
    trios = load_fogo_trios(data_dir)
    return int(trios.max()) + 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pilot', action='store_true',
                        help='Run 3 pilot instances only (measure time and TV range)')
    parser.add_argument('--calibrate', action='store_true',
                        help='Extend p0 to 0.95 to check TV coverage')
    parser.add_argument('--draws', type=int, default=N_DRAWS)
    parser.add_argument('--worker', type=int, default=0,
                        help='Worker index (0-based). Use with --total-workers.')
    parser.add_argument('--total-workers', type=int, default=1,
                        help='Total number of parallel workers.')
    args = parser.parse_args()

    # --- Unit test first, always ---
    run_unit_test()

    data_dir = Path('data')
    out_dir  = Path('results')
    out_dir.mkdir(exist_ok=True)

    # Load Fogo structure
    try:
        fogo_trios = load_fogo_trios(data_dir)
    except FileNotFoundError as e:
        print(f"\nERROR: {e}\n")
        sys.exit(1)

    N_FOGO = int(fogo_trios.max()) + 1
    print(f"N_FOGO={N_FOGO}, n_trios={len(fogo_trios):,}")

    # Grid
    if args.calibrate:
        p0_levels = np.linspace(0, 0.95, 20)
    else:
        p0_levels = np.linspace(0, 0.50, 11)

    shapes = ['normal', 'lognormal', 'bimodal']
    n_reps = 4
    n_draws = args.draws

    if args.pilot:
        # 3 pilot instances: p0=0, 0.25, 0.5; shape=normal; rep=0
        pilot_grid = [(0.0, 'normal', 0), (0.25, 'lognormal', 0), (0.50, 'bimodal', 0)]
        print(f"\n=== PILOT: {len(pilot_grid)} instances, draws={n_draws} ===")
        import time
        for p0, shape, rep in pilot_grid:
            seed = SEED_BASE + int(p0 * 1000) * 10000 + shapes.index(shape) * 100 + rep
            rng_inst = np.random.default_rng(seed)
            X = generate_criteria(N_FOGO, M, p0, shape, rng_inst)
            t0 = time.time()
            res = evaluate_instance(fogo_trios, X, W_AHP, n_draws, KAPPA, seed + 1)
            dt = time.time() - t0
            print(f"p0={p0:.2f} {shape}: {dt:.1f}s | "
                  f"mm tv1={res['minmax']['tv1']:.3f} Q2={res['minmax']['Q2']:.3f} | "
                  f"vec tv1={res['vector']['tv1']:.3f} Q2={res['vector']['Q2']:.3f}")
        print("\nPilot done. Estimated total grid time: "
              f"~{dt * len(p0_levels) * len(shapes) * n_reps / 60:.0f} min")
        return

    # Full grid
    all_jobs = list(iproduct(p0_levels, shapes, range(n_reps)))
    total = len(all_jobs)

    # Slice for this worker
    worker      = args.worker
    n_workers   = args.total_workers
    my_jobs     = [j for i, j in enumerate(all_jobs) if i % n_workers == worker]
    out_suffix  = f'_w{worker}' if n_workers > 1 else ''

    print(f"Worker {worker}/{n_workers}: {len(my_jobs)}/{total} instances")

    rows = []
    done = 0

    for p0, shape, rep in my_jobs:
        done += 1
        seed = SEED_BASE + int(round(p0 * 1000)) * 10000 + shapes.index(shape) * 100 + rep
        rng_inst = np.random.default_rng(seed)

        X = generate_criteria(N_FOGO, M, p0, shape, rng_inst)
        res = evaluate_instance(fogo_trios, X, W_AHP, n_draws, KAPPA, seed + 1)

        for norm_name, vals in res.items():
            rows.append({'p0': round(p0, 3), 'shape': shape, 'rep': rep,
                         'norm': norm_name, **vals})

        pct = 100 * done / total
        print(f"[{done}/{total}] {pct:.1f}% | p0={p0:.2f} {shape} rep{rep} | "
              f"mm tv1={res['minmax']['tv1']:.3f} Q2={res['minmax']['Q2']:.3f} "
              f"Q3={res['minmax']['Q3']:.4f} |F|={res['minmax']['front_size']} | "
              f"vec tv1={res['vector']['tv1']:.3f} Q2={res['vector']['Q2']:.3f} "
              f"Q3={res['vector']['Q3']:.4f} |F|={res['vector']['front_size']}")
        sys.stdout.flush()

    df = pd.DataFrame(rows)
    csv_out = out_dir / f'wp4_synthetic{out_suffix}.csv'
    df.to_csv(csv_out, index=False)
    print(f"\nSaved {len(df)} rows to {csv_out}")

    summary = df.groupby(['p0', 'shape', 'norm'])[['Q2', 'Q3', 'tv1', 'tv2']].mean()
    summary_out = out_dir / f'wp4_summary{out_suffix}.csv'
    summary.to_csv(summary_out)

    if n_workers == 1:
        print("\n=== Summary by norm ===")
        print(df.groupby('norm')[['Q2', 'Q3', 'tv1']].mean().round(4).to_string())
        print("\n=== Q2 by (p0, norm) ===")
        print(df.groupby(['p0', 'norm'])['Q2'].mean().unstack('norm').round(3).to_string())
    print(f"\nCONCLUÍDO worker={worker}")


if __name__ == '__main__':
    main()
