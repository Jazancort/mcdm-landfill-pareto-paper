"""
corpus_mc.py  (corrected)
==========================
Monte Carlo Dirichlet experiment on active corpus matrices.

Key corrections vs previous version:
1. Pareto frontier is computed over TRIOS, not over individual alternatives.
   F(trio) = group-level aggregate for each trio; frontier over the set
   of C(m,k) trio-vectors.
2. Without coupling constraints, optimal == greedy by separability theorem.
   We report Q2 without the greedy/optimal split — this is noted as scope.
3. Orientations are applied BEFORE within-group aggregation (complement
   cost criteria: x -> max+min-x so all group aggregates are benefit-oriented).

Scope: tests Mechanism 1 (amplitude identity → ordering TV → Q2) in isolation,
not the normalisation × assembly interaction (which requires coupling constraints).

Output: results/corpus_mc_results.csv
"""
import sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
from scipy.stats import dirichlet as sp_dirichlet
from corpus_data import CORPUS
from corpus_amplitudes import Aj_minmax, Aj_vector, Aj_ranks, compute_TV_meff

def normalise_minmax(X, directions):
    """Apply min-max normalisation to X; cost cols complemented."""
    m, n = X.shape
    N = np.zeros_like(X, dtype=float)
    for j in range(n):
        col = X[:, j].astype(float)
        lo, hi = col.min(), col.max()
        if hi == lo:
            N[:, j] = 1.0; continue
        if directions[j] == 'max':
            N[:, j] = (col - lo) / (hi - lo)
        else:
            N[:, j] = (hi - col) / (hi - lo)
    return N

def normalise_vector(X, directions):
    """Vector normalisation; cost cols complemented before norming."""
    m, n = X.shape
    N = np.zeros_like(X, dtype=float)
    for j in range(n):
        col = X[:, j].astype(float)
        if directions[j] != 'max':
            col = col.max() + col.min() - col
        norm_j = np.sqrt(np.sum(col**2))
        N[:, j] = col / norm_j if norm_j > 0 else 0.0
    return N

def normalise_ranks(X, directions):
    """Midrank/(m+1) normalisation; cost cols complemented."""
    m, n = X.shape
    N = np.zeros((m, n))
    for j in range(n):
        col = X[:, j].astype(float)
        if directions[j] != 'max':
            col = col.max() + col.min() - col
        vals, counts = np.unique(col, return_counts=True)
        midranks = np.zeros(m)
        i = 0
        while i < m:
            j_end = i
            while j_end < m and np.sort(col)[j_end] == np.sort(col)[i]:
                j_end += 1
            mr = (i + 1 + j_end) / 2.0
            for k2 in range(i, j_end):
                midranks[k2] = mr
            i = j_end
        # assign midranks to original positions
        sorted_idx = np.argsort(col)
        rank_col = np.zeros(m)
        for rank_pos, orig_pos in enumerate(sorted_idx):
            rank_col[orig_pos] = midranks[rank_pos]
        N[:, j] = rank_col / (m + 1)
    return N

# ── Parameters ────────────────────────────────────────────────────────────────
K_PORTFOLIO = 3
KAPPA       = 200
N_DRAWS     = 3500
SEED        = 42
RNG         = np.random.default_rng(SEED)


# ── Group-level aggregate: orient then sum ────────────────────────────────────
def group_aggregate(X_raw, group_indices, directions):
    """For each alternative, sum the group's criteria after orienting.
    Cost criteria are complemented (max+min-x) so the aggregate is benefit.
    X_raw: (m, n) original matrix; group_indices: list of column indices.
    Returns (m,) vector of group scores (higher = better).
    """
    m = X_raw.shape[0]
    agg = np.zeros(m)
    for j in group_indices:
        col = X_raw[:, j].astype(float)
        if directions[j] != 'max':
            col = col.max() + col.min() - col  # complement: now benefit
        agg += col
    return agg


def build_trio_objectives(X_raw, obj_groups, directions):
    """Build the objective matrix over all C(m,3) trios.
    Each trio gets a 3-vector (one aggregate per group).
    Returns: trio_list (list of tuples), obj_matrix (n_trios x 3).
    """
    m = X_raw.shape[0]
    G = [group_aggregate(X_raw, g, directions) for g in obj_groups]  # 3 x m
    G = np.array(G).T  # m x 3; each row = alternative's group scores

    trios = list(itertools.combinations(range(m), K_PORTFOLIO))
    trio_obj = np.zeros((len(trios), 3))
    for t_idx, trio in enumerate(trios):
        for g_idx in range(3):
            trio_obj[t_idx, g_idx] = sum(G[i, g_idx] for i in trio)
    return trios, trio_obj


def pareto_frontier_trios(trio_obj):
    """Return set of non-dominated trio indices.
    trio_obj: (n_trios x 3), all objectives benefit-oriented (higher = better).
    """
    n = trio_obj.shape[0]
    dominated = np.zeros(n, dtype=bool)
    for i in range(n):
        if dominated[i]:
            continue
        for j in range(n):
            if i == j or dominated[j]:
                continue
            if np.all(trio_obj[j] >= trio_obj[i]) and np.any(trio_obj[j] > trio_obj[i]):
                dominated[i] = True
                break
    return set(np.where(~dominated)[0])


# ── SAW score ─────────────────────────────────────────────────────────────────
def saw_score(N, w):
    return N @ w


def top_k_trio(scores, k, trios):
    """Select trio with highest total SAW score (= greedy = optimal here)."""
    best = max(range(len(trios)), key=lambda t: sum(scores[i] for i in trios[t]))
    return best  # index into trios list


# ── Single matrix experiment ──────────────────────────────────────────────────
def run_experiment(entry):
    if not entry.get('active', True):
        return None

    X    = np.array(entry['matrix'], dtype=float)
    w0   = np.array(entry['weights'], dtype=float)
    w0   = w0 / w0.sum()
    dirs = entry['directions']
    og   = entry.get('obj_groups')
    m, n = X.shape

    if og is None:
        # Fallback: one group per criterion
        og = [[j] for j in range(n)]

    # Build trio-level Pareto frontier (once, on raw data)
    trios, trio_obj = build_trio_objectives(X, og, dirs)
    frontier = pareto_frontier_trios(trio_obj)
    n_trios    = len(trios)
    n_frontier = len(frontier)

    # Normalised matrices
    N_mm  = normalise_minmax(X, dirs)
    N_vec = normalise_vector(X, dirs)
    N_rnk = normalise_ranks(X, dirs)

    # Draw weights
    alpha = KAPPA * w0
    W = sp_dirichlet.rvs(alpha, size=N_DRAWS, random_state=RNG)

    results = {}
    for label, N in [('mm', N_mm), ('vec', N_vec), ('rnk', N_rnk)]:
        nd = 0
        for w_draw in W:
            scores  = saw_score(N, w_draw)
            t_idx   = top_k_trio(scores, K_PORTFOLIO, trios)
            if t_idx in frontier:
                nd += 1
        q2  = nd / N_DRAWS * 100
        se  = np.sqrt(q2 * (100 - q2) / N_DRAWS)
        results[label] = {
            'Q2':          round(q2, 2),
            'SE':          round(se, 2),
            'n_frontier':  n_frontier,
            'n_trios':     n_trios,
        }
    return results


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    rows = []
    for entry in CORPUS:
        key = entry['source_key']
        if not entry.get('active', True):
            print(f"\n{key}  INACTIVE — skipped")
            continue

        m, n    = entry['m'], entry['n']
        n_trios = len(list(itertools.combinations(range(m), K_PORTFOLIO)))
        print(f"\n{key}  (m={m}, n={n}, C({m},{K_PORTFOLIO})={n_trios}) ...")
        res = run_experiment(entry)
        if res is None:
            continue

        for norm, vals in res.items():
            print(f"  {norm:4s}  Q2={vals['Q2']:5.1f}%  SE={vals['SE']:.2f}  "
                  f"|frontier|={vals['n_frontier']}/{vals['n_trios']} trios")
            rows.append({
                'source_key':  key,
                'm': m, 'n': n,
                'norm':        norm,
                'Q2':          vals['Q2'],
                'SE':          vals['SE'],
                'n_frontier':  vals['n_frontier'],
                'n_trios':     vals['n_trios'],
            })

    if not rows:
        print("\nNo active instances — nothing to save.")
        return

    df = pd.DataFrame(rows)
    out = os.path.join(os.path.dirname(__file__), '..', 'results', 'corpus_mc_results.csv')
    df.to_csv(out, index=False)
    print(f"\n{'='*60}")
    print(df.to_string(index=False))
    print(f"\nSaved to {out}")

    # H1 check: Q2(mm) >= Q2(vec) for each active instance
    print("\n=== H1 check: Q2(mm) >= Q2(vec) ===")
    pivot = df.pivot_table(index='source_key', columns='norm', values='Q2', aggfunc='first')
    violations = 0
    for key in pivot.index:
        mm  = pivot.loc[key, 'mm']
        vec = pivot.loc[key, 'vec']
        diff = mm - vec
        ok = '✓' if diff >= -2.5 else '✗ VIOLATION'
        if diff < -2.5:
            violations += 1
        print(f"  {ok}  {key}: mm={mm:.1f}  vec={vec:.1f}  diff={diff:+.1f} pp")
    n_active = len(pivot)
    frac = violations / n_active if n_active > 0 else 0
    print(f"\nH1 violations: {violations}/{n_active} "
          f"({'FALSIFIED (>=20%)' if frac >= 0.20 else 'SUPPORTED'})")


if __name__ == '__main__':
    main()
