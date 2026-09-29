# -*- coding: utf-8 -*-
"""
WP4 — Synthetic instance grid for external validity (132 instances).

Design
------
Grid: 11 levels of zero-mass p0 in {0, 0.05, ..., 0.50}  ×
      3 marginal shapes {normal, lognormal, bimodal}  ×
      4 replications  = 132 instances.

Each instance:
  - N=400 sites, m=11 criteria, k=3 sites per portfolio.
  - AHP weights from paper (Table 1).
  - Min-max and vector normalisation.
  - SAW aggregation (additive), optimal assembly (exhaustive trio enumeration
    subject to d_min = 10 km separation, approximated here by random spatial
    placement with rejection sampling).
  - Outputs: TV(α=1), Q2, Q3=E[gap].

Outputs
-------
results/wp4_synthetic.csv   — one row per instance × normalisation
results/wp4_summary.csv     — mean Q2/Q3 by (p0, shape, normalisation)

Usage
-----
    uv run python scripts/wp4_synthetic.py

Runtime: ~3–5 min on a single core (numpy-vectorised enumeration).
"""

import sys
import itertools
import numpy as np
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# ---------------------------------------------------------------------------
# Constants from paper
# ---------------------------------------------------------------------------

# AHP weights (Table 1, 11 criteria in order)
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
W_AHP /= W_AHP.sum()   # renormalise to exact 1

M = len(W_AHP)         # 11 criteria
K = 3                  # portfolio size
N_SITES = 40        # C(40,3)~10k trios; ~3s per instance at 500 draws
D_MIN_KM = 10.0        # separation constraint (km)
BOX_KM   = 50.0        # spatial domain side (km)
N_DRAWS = 500          # weight draws per cell
KAPPA = 50             # Dirichlet concentration
SEED_BASE = 20260929

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def amplitude(col: np.ndarray) -> float:
    """A_j = max - min of normalised column (min-max: always 1; vector: varies)."""
    return float(col.max() - col.min())


def total_variation(w_eff: np.ndarray, w: np.ndarray) -> float:
    return 0.5 * np.abs(w_eff - w).sum()


def minmax_norm(X: np.ndarray) -> np.ndarray:
    lo, hi = X.min(axis=0), X.max(axis=0)
    rng = np.where(hi > lo, hi - lo, 1.0)
    return (X - lo) / rng


def vector_norm(X: np.ndarray) -> np.ndarray:
    norms = np.sqrt((X ** 2).sum(axis=0))
    norms = np.where(norms > 0, norms, 1.0)
    return X / norms


def tv_alpha(w: np.ndarray, A: np.ndarray, alpha: float) -> float:
    num = (w ** alpha) * (A ** alpha)
    w_eff = num / num.sum()
    return total_variation(w_eff, w)


def saw_scores(V: np.ndarray, w: np.ndarray) -> np.ndarray:
    """SAW score for each site: shape (N,)."""
    return V @ w


def pareto_front(F: np.ndarray, eps: float = 1e-9):
    """
    Fast 3-objective Pareto filter using sort-and-sweep.
    Sort descending by F[:,0], then sweep tracking best F[:,1] and F[:,2].
    O(n log n) — handles 10k trios in <0.01s.
    All objectives maximised.
    """
    n = len(F)
    if n == 0:
        return np.zeros(0, dtype=bool)
    order = np.argsort(-F[:, 0])
    F_sorted = F[order]
    nd_sorted = np.ones(n, dtype=bool)
    best2 = -np.inf
    best3 = -np.inf
    for i in range(n):
        f1, f2, f3 = F_sorted[i, 0], F_sorted[i, 1], F_sorted[i, 2]
        if f2 > best2 - eps or f3 > best3 - eps:
            # update running bests
            if f2 > best2:
                best2 = f2
            if f3 > best3:
                best3 = f3
        else:
            nd_sorted[i] = False
    # map back to original order
    result = np.zeros(n, dtype=bool)
    result[order] = nd_sorted
    return result


def gap_score(f: np.ndarray, front: np.ndarray, R: np.ndarray) -> float:
    """
    Scale-free gap for a single portfolio f (shape 3,).
    front: (|F|, 3) non-dominated set.
    R: (3,) attainable range per objective.
    """
    if front.shape[0] == 0:
        return 0.0
    R_safe = np.where(R > 0, R, 1.0)
    # max over front members of min over objectives of (F'_l - f_l) / R_l
    diffs = (front - f[None, :]) / R_safe[None, :]  # (|F|, 3)
    per_member = diffs.min(axis=1)                   # (|F|,)
    return float(max(0.0, per_member.max()))


# ---------------------------------------------------------------------------
# Spatial placement with separation constraint
# ---------------------------------------------------------------------------

def make_coords(n: int, rng: np.random.Generator, box_km: float = BOX_KM):
    """Random (x,y) in km × km box."""
    return rng.uniform(0, box_km, size=(n, 2))


def admissible_trios(coords: np.ndarray, d_min: float):
    """
    Vectorised trio enumeration. Builds upper-triangle pair index,
    then filters valid triples using only admissible pairs.
    Fast: O(n^2) memory for pairs, much less for trios.
    """
    n = len(coords)
    diff = coords[:, None, :] - coords[None, :, :]
    dist = np.sqrt((diff**2).sum(axis=2))
    ok = dist >= d_min  # (n,n) bool

    # admissible pairs (upper triangle)
    pi, pj = np.where(np.triu(ok, k=1))  # shape (n_pairs,)

    # for each pair (i,j), find all k > j where (i,k) and (j,k) are ok
    trios = []
    for idx in range(len(pi)):
        i, j = int(pi[idx]), int(pj[idx])
        # candidates: k > j, ok[i,k] and ok[j,k]
        k_cands = np.where((np.arange(n) > j) & ok[i] & ok[j])[0]
        if len(k_cands):
            block = np.stack([
                np.full(len(k_cands), i),
                np.full(len(k_cands), j),
                k_cands
            ], axis=1)
            trios.append(block)

    if not trios:
        return np.empty((0, 3), dtype=np.int32)
    return np.concatenate(trios, axis=0).astype(np.int32)


# ---------------------------------------------------------------------------
# Criterion value generators
# ---------------------------------------------------------------------------

def generate_criteria(n: int, m: int, p0: float, shape: str,
                      rng: np.random.Generator) -> np.ndarray:
    """
    Generate raw criterion matrix X of shape (n, m), larger-is-better.

    p0    : probability of exact zero (sparse / binary-like mass)
    shape : 'normal' | 'lognormal' | 'bimodal'
    """
    X = np.zeros((n, m))
    for j in range(m):
        zero_mask = rng.random(n) < p0
        n_nonzero = int((~zero_mask).sum())

        if shape == 'normal':
            vals = rng.normal(0.5, 0.2, size=n_nonzero).clip(0, 1)
        elif shape == 'lognormal':
            vals = rng.lognormal(mean=-0.7, sigma=0.6, size=n_nonzero)
            vals = (vals - vals.min()) / max(vals.max() - vals.min(), 1e-9)
        elif shape == 'bimodal':
            half = n_nonzero // 2
            a = rng.normal(0.2, 0.07, size=half).clip(0, 1)
            b = rng.normal(0.8, 0.07, size=n_nonzero - half).clip(0, 1)
            vals = np.concatenate([a, b])
            rng.shuffle(vals)
        else:
            raise ValueError(f"Unknown shape: {shape}")

        col = np.zeros(n)
        col[~zero_mask] = vals
        X[:, j] = col

    return X


# ---------------------------------------------------------------------------
# Single-instance evaluation
# ---------------------------------------------------------------------------

def evaluate_instance(X: np.ndarray, w_ahp: np.ndarray,
                      coords: np.ndarray, d_min: float,
                      n_draws: int, kappa: float,
                      seed: int) -> dict:
    """
    Evaluate one synthetic instance for both min-max and vector normalisation.
    Returns dict with TV(α=1), TV(α=2), Q2, Q3 for each normalisation.
    """
    rng = np.random.default_rng(seed)
    trios = admissible_trios(coords, d_min)

    if len(trios) == 0:
        return None  # skip degenerate instances

    results = {}
    for norm_name, norm_fn in [('minmax', minmax_norm), ('vector', vector_norm)]:
        V = norm_fn(X)  # (N, M) normalised, larger-is-better

        # Amplitude
        A = np.array([amplitude(V[:, j]) for j in range(V.shape[1])])
        num1 = w_ahp * A
        w_eff1 = num1 / num1.sum()
        tv1 = total_variation(w_eff1, w_ahp)
        tv2 = tv_alpha(w_ahp, A, alpha=2.0)

        # Objective groups (same as paper: G1=0..3, G2=4..7, G3=8..10)
        G = [slice(0, 4), slice(4, 8), slice(8, 11)]

        # Monte Carlo loop
        q2_list, q3_list = [], []

        for _ in range(n_draws):
            w_draw = rng.dirichlet(kappa * w_ahp)
            w_draw /= w_draw.sum()

            # SAW scores
            scores = V @ w_draw  # (N,)

            # Optimal assembly: rank all trios by sum of scores, pick best
            trio_scores = scores[trios].sum(axis=1)  # (n_trios,)
            best_trio_idx = np.argmax(trio_scores)
            best_trio = trios[best_trio_idx]

            # Portfolio objectives F_l = sum_site sum_j in Gl w_j*v_j(i)
            def F_l(sites, g):
                return sum(V[s, g] @ w_draw[g] for s in sites)

            f_best = np.array([F_l(best_trio, g) for g in G])

            # Enumerate objectives for ALL trios (vectorised)
            # F_l(T) = sum_{i in T} sum_{j in Gl} w_j * V[i,j]
            # = sum_{i in T} (V[i, Gl] @ w[Gl])
            site_obj = np.stack([V[:, g] @ w_draw[g] for g in G], axis=1)  # (N,3)
            trio_obj = site_obj[trios].sum(axis=1)  # (n_trios, 3)

            # Pareto front (all maximised)
            is_nd = pareto_front(trio_obj)
            front = trio_obj[is_nd]
            R = trio_obj.max(axis=0) - trio_obj.min(axis=0)

            # Q2: is best_trio on the front?
            on_front = is_nd[best_trio_idx]
            q2_list.append(float(on_front))

            # Q3: gap
            g_val = gap_score(f_best, front, R)
            q3_list.append(g_val)

        results[norm_name] = {
            'tv1': tv1,
            'tv2': tv2,
            'Q2': float(np.mean(q2_list)),
            'Q3': float(np.mean(q3_list)),
            'Q2_se': float(np.std(q2_list) / np.sqrt(n_draws)),
            'Q3_se': float(np.std(q3_list) / np.sqrt(n_draws)),
        }

    return results


# ---------------------------------------------------------------------------
# Main grid
# ---------------------------------------------------------------------------

def main():
    out_dir = Path('results')
    out_dir.mkdir(exist_ok=True)

    # Grid definition
    p0_levels = np.linspace(0, 0.50, 11)   # 11 levels: 0, 0.05, ..., 0.50
    shapes = ['normal', 'lognormal', 'bimodal']
    n_reps = 4
    # 11 × 3 × 4 = 132 instances

    rows = []
    total = len(p0_levels) * len(shapes) * n_reps
    done = 0

    for p0, shape, rep in itertools.product(p0_levels, shapes, range(n_reps)):
        done += 1
        seed = SEED_BASE + int(p0 * 1000) * 10000 + shapes.index(shape) * 100 + rep
        rng_inst = np.random.default_rng(seed)

        X = generate_criteria(N_SITES, M, p0, shape, rng_inst)
        coords = make_coords(N_SITES, rng_inst)

        res = evaluate_instance(X, W_AHP, coords, D_MIN_KM,
                                N_DRAWS, KAPPA, seed + 1)

        pct = 100 * done / total
        if res is None:
            print(f"[{done}/{total}] {pct:.1f}% | SKIP p0={p0:.2f} {shape} rep{rep}")
            sys.stdout.flush()
            continue

        for norm_name, vals in res.items():
            rows.append({
                'p0': round(p0, 3),
                'shape': shape,
                'rep': rep,
                'norm': norm_name,
                'tv1': vals['tv1'],
                'tv2': vals['tv2'],
                'Q2': vals['Q2'],
                'Q3': vals['Q3'],
                'Q2_se': vals['Q2_se'],
                'Q3_se': vals['Q3_se'],
            })

        print(f"[{done}/{total}] {pct:.1f}% | p0={p0:.2f} {shape} rep{rep} "
              f"| mm Q2={res['minmax']['Q2']:.3f} Q3={res['minmax']['Q3']:.4f}"
              f"| vec Q2={res['vector']['Q2']:.3f} Q3={res['vector']['Q3']:.4f}")
        sys.stdout.flush()

    df = pd.DataFrame(rows)
    df.to_csv(out_dir / 'wp4_synthetic.csv', index=False)
    print(f"\nSaved {len(df)} rows to {out_dir/'wp4_synthetic.csv'}")

    # Summary: mean Q2/Q3 by (p0, shape, norm)
    summary = df.groupby(['p0', 'shape', 'norm'])[['Q2', 'Q3', 'tv1', 'tv2']].mean()
    summary.to_csv(out_dir / 'wp4_summary.csv')
    print(f"Saved summary to {out_dir/'wp4_summary.csv'}")

    # Quick report
    print("\n=== Summary by norm (all p0 and shapes) ===")
    print(df.groupby('norm')[['Q2', 'Q3', 'tv1']].mean().round(4).to_string())
    print("\n=== Q2 by (p0, norm), averaged over shapes and reps ===")
    pivot = df.groupby(['p0', 'norm'])['Q2'].mean().unstack('norm')
    print(pivot.round(3).to_string())
    print("\nCONCLUÍDO")


if __name__ == '__main__':
    main()
