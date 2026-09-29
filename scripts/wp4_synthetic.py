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

    Algorithm: for each point i, check whether any other point j dominates it,
    i.e. F[j] >= F[i] - eps for all objectives AND F[j] > F[i] + eps for at
    least one objective.

    Vectorised with chunked broadcasting to avoid O(n^2 * 3) memory blowup.
    For n=10k this takes ~0.05s; for n=100k use a sweep-tree instead.

    UNIT TEST (run with --test):
        P1 = (10, 10, 1), P2 = (9, 1, 10), P3 = (8, 5, 5)
        Expected non-dominated: P1, P2, P3 (all three).
        P3 is NOT dominated: P1 beats it on F1 and F2 but loses on F3;
        P2 beats it on F3 but loses on F2.
    """
    n = len(F)
    dominated = np.zeros(n, dtype=bool)
    chunk = 2000  # adjust for memory; ~200 MB peak at chunk=2000, n=10k

    for start in range(0, n, chunk):
        end = min(start + chunk, n)
        # Fi: (chunk, 1, 3)  Fj: (1, n, 3)
        Fi = F[start:end, np.newaxis, :]
        Fj = F[np.newaxis, :, :]
        # j weakly dominates i: Fj >= Fi for all obj
        weak = (Fj >= Fi - eps).all(axis=2)          # (chunk, n)
        # j strictly beats i in at least one obj
        strict = (Fj > Fi + eps).any(axis=2)         # (chunk, n)
        dominates_i = weak & strict                   # (chunk, n)
        # exclude self-dominance
        diag_idx = np.arange(start, end) - start
        dominates_i[diag_idx, start:end][
            np.arange(len(diag_idx)), np.arange(len(diag_idx))] = False
        dominated[start:end] = dominates_i.any(axis=1)

    return ~dominated


def run_unit_test():
    """Verify the Pareto filter on the documented counterexample."""
    F = np.array([[10, 10, 1],
                  [9,  1, 10],
                  [8,  5,  5]], dtype=float)
    nd = pareto_front_correct(F)
    assert nd.all(), (
        f"UNIT TEST FAILED: expected all 3 non-dominated, got {nd}. "
        "The sweep-based filter would mark P3 as dominated — "
        "pareto_front_correct must return [True, True, True]."
    )
    print("UNIT TEST PASSED: P1, P2, P3 all non-dominated (counterexample to sweep).")
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
    fogo_trios: (n_trios, 3) integer index array from the Fogo distance matrix.
    X_raw: (N, M) raw criterion values (new draw, same sites as Fogo).
    """
    rng = np.random.default_rng(seed)
    results = {}

    for norm_name, norm_fn in [('minmax', minmax_norm), ('vector', vector_norm)]:
        V = norm_fn(X_raw)  # (N, M)
        tv1 = tv_from_norm(V, w_ahp, alpha=1.0)
        tv2 = tv_from_norm(V, w_ahp, alpha=2.0)

        q2_list, q3_list = [], []

        for _ in range(n_draws):
            w = rng.dirichlet(kappa * w_ahp)
            w /= w.sum()

            # SAW scores and optimal assembly
            scores = V @ w
            trio_scores = scores[fogo_trios].sum(axis=1)  # (n_trios,)
            best_idx = int(trio_scores.argmax())
            best_trio = fogo_trios[best_idx]

            # Objective values for all trios
            site_obj = np.stack([V[:, g] @ w[g] for g in GROUPS], axis=1)  # (N,3)
            trio_obj = site_obj[fogo_trios].sum(axis=1)                      # (n_trios,3)

            # Pareto front — correct vectorised filter
            is_nd = pareto_front_correct(trio_obj)
            front = trio_obj[is_nd]
            R = trio_obj.max(axis=0) - trio_obj.min(axis=0)
            R = np.where(R > 0, R, 1.0)

            # Q2: is the best portfolio on the front?
            q2_list.append(float(is_nd[best_idx]))

            # Q3: normalised gap
            f_best = trio_obj[best_idx]
            if front.shape[0] == 0:
                q3_list.append(0.0)
            else:
                diffs = (front - f_best[np.newaxis, :]) / R[np.newaxis, :]
                per_member = diffs.min(axis=1)
                q3_list.append(float(max(0.0, per_member.max())))

        results[norm_name] = {
            'tv1': tv1, 'tv2': tv2,
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
    total = len(p0_levels) * len(shapes) * n_reps
    rows = []
    done = 0

    for p0, shape, rep in iproduct(p0_levels, shapes, range(n_reps)):
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
              f"Q3={res['minmax']['Q3']:.4f} | "
              f"vec tv1={res['vector']['tv1']:.3f} Q2={res['vector']['Q2']:.3f} "
              f"Q3={res['vector']['Q3']:.4f}")
        sys.stdout.flush()

    df = pd.DataFrame(rows)
    df.to_csv(out_dir / 'wp4_synthetic.csv', index=False)
    print(f"\nSaved {len(df)} rows to {out_dir/'wp4_synthetic.csv'}")

    summary = df.groupby(['p0', 'shape', 'norm'])[['Q2', 'Q3', 'tv1', 'tv2']].mean()
    summary.to_csv(out_dir / 'wp4_summary.csv')

    print("\n=== Summary by norm ===")
    print(df.groupby('norm')[['Q2', 'Q3', 'tv1']].mean().round(4).to_string())
    print("\n=== Q2 by (p0, norm) ===")
    print(df.groupby(['p0', 'norm'])['Q2'].mean().unstack('norm').round(3).to_string())
    print("\nCONCLUÍDO")


if __name__ == '__main__':
    main()
