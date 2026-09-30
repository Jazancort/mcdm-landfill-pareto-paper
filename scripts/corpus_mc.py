"""
corpus_mc.py
============
Monte Carlo Dirichlet experiment on each matrix in corpus_data.py.

For each matrix:
  1. Normalise under min-max, vector, and ranks.
  2. Enumerate all C(m,k) trios (k=3 pre-declared in PRESPEC.md).
  3. Build exact Pareto frontier: one group per criterion (most conservative).
  4. Draw N=3500 weight vectors from Dirichlet(kappa * w_0) where w_0 are
     the published weights.
  5. For each draw, compute SAW scores, run greedy and optimal assembly,
     check if selected trio is Pareto non-dominated.
  6. Report Q2_greedy, Q2_optimal, Q2_mean and binomial SE for each.

Output: results/corpus_mc_results.csv  (one row per matrix × normalisation)
"""
import sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
from scipy.stats import dirichlet as sp_dirichlet
from corpus_data import CORPUS
from corpus_amplitudes import normalise_minmax, normalise_vector, normalise_ranks

# ── Parameters (pre-declared in PRESPEC.md) ──────────────────────────────────
K_PORTFOLIO = 3          # portfolio size
KAPPA       = 200        # Dirichlet concentration
N_DRAWS     = 3500       # Monte Carlo draws
SEED        = 42
RNG         = np.random.default_rng(SEED)


# ── Pareto frontier (one objective per criterion, most conservative) ──────────
def pareto_frontier(X_mm, directions):
    """
    Return set of indices that are Pareto non-dominated.
    X_mm : normalised matrix (all columns benefit-oriented after min-max).
    directions : list of 'max'/'min' for raw criteria.
    After min-max with our convention, all columns are benefit (higher=better).
    """
    m = X_mm.shape[0]
    dominated = np.zeros(m, dtype=bool)
    for i in range(m):
        for j in range(m):
            if i == j:
                continue
            # j dominates i if j >= i on all criteria and > on at least one
            if np.all(X_mm[j] >= X_mm[i]) and np.any(X_mm[j] > X_mm[i]):
                dominated[i] = True
                break
    return set(np.where(~dominated)[0])


# ── Greedy assembly ───────────────────────────────────────────────────────────
def greedy_portfolio(scores, k):
    """Select top-k by descending SAW score."""
    return set(np.argsort(scores)[::-1][:k])


# ── Optimal assembly (exhaustive over C(m,k)) ────────────────────────────────
def optimal_portfolio(scores, k, all_trios):
    """Select trio with highest sum of scores."""
    best_trio = max(all_trios, key=lambda t: sum(scores[i] for i in t))
    return set(best_trio)


# ── SAW score under a normalisation ──────────────────────────────────────────
def saw_score(N, w):
    """N: (m x n) normalised matrix; w: (n,) weights. Returns (m,) scores."""
    return N @ w


# ── Single matrix experiment ──────────────────────────────────────────────────
def run_experiment(entry):
    X       = np.array(entry['matrix'], dtype=float)
    w0      = np.array(entry['weights'], dtype=float)
    w0      = w0 / w0.sum()
    dirs    = entry['directions']
    m, n    = X.shape
    k       = K_PORTFOLIO

    # Enumerate C(m, k) trios
    all_trios = list(itertools.combinations(range(m), k))

    # Build normalised matrices
    N_mm  = normalise_minmax(X, dirs)
    N_vec = normalise_vector(X, dirs)
    N_rnk = normalise_ranks(X, dirs)

    # Pareto frontier (computed once on min-max, which is group-free)
    frontier = pareto_frontier(N_mm, dirs)

    # Draw weight vectors
    alpha = KAPPA * w0
    W = sp_dirichlet.rvs(alpha, size=N_DRAWS, random_state=RNG)  # (N, n)

    results = {}
    for label, N in [('mm', N_mm), ('vec', N_vec), ('rnk', N_rnk)]:
        nd_greedy  = 0
        nd_optimal = 0
        for w_draw in W:
            scores = saw_score(N, w_draw)
            # Greedy
            trio_g = greedy_portfolio(scores, k)
            # Optimal
            trio_o = optimal_portfolio(scores, k, all_trios)
            # Check non-dominance
            if trio_g.issubset(frontier):
                nd_greedy += 1
            if trio_o.issubset(frontier):
                nd_optimal += 1

        q2g = nd_greedy  / N_DRAWS * 100
        q2o = nd_optimal / N_DRAWS * 100
        q2m = (q2g + q2o) / 2
        se_g = np.sqrt(q2g * (100 - q2g) / N_DRAWS)
        se_o = np.sqrt(q2o * (100 - q2o) / N_DRAWS)
        results[label] = {
            'Q2_greedy':  round(q2g, 2),
            'Q2_optimal': round(q2o, 2),
            'Q2_mean':    round(q2m, 2),
            'SE_greedy':  round(se_g, 2),
            'SE_optimal': round(se_o, 2),
            'n_frontier': len(frontier),
            'n_trios':    len(all_trios),
        }
    return results


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    rows = []
    for entry in CORPUS:
        key = entry['source_key']
        m, n = entry['m'], entry['n']
        n_trios = len(list(itertools.combinations(range(m), K_PORTFOLIO)))
        print(f"\n{key}  (m={m}, n={n}, C({m},{K_PORTFOLIO})={n_trios})  ...")
        res = run_experiment(entry)
        for norm, vals in res.items():
            print(f"  {norm:4s}  greedy={vals['Q2_greedy']:5.1f}%  optimal={vals['Q2_optimal']:5.1f}%  "
                  f"mean={vals['Q2_mean']:5.1f}%  |frontier|={vals['n_frontier']}")
            rows.append({
                'source_key':  key,
                'm': m, 'n': n,
                'norm':        norm,
                'Q2_greedy':   vals['Q2_greedy'],
                'Q2_optimal':  vals['Q2_optimal'],
                'Q2_mean':     vals['Q2_mean'],
                'SE_greedy':   vals['SE_greedy'],
                'SE_optimal':  vals['SE_optimal'],
                'n_frontier':  vals['n_frontier'],
                'n_trios':     vals['n_trios'],
            })

    df = pd.DataFrame(rows)
    out = os.path.join(os.path.dirname(__file__), '..', 'results', 'corpus_mc_results.csv')
    df.to_csv(out, index=False)
    print(f"\n{'='*60}")
    print(df.to_string(index=False))
    print(f"\nSaved to {out}")

    # H1 check: Q2_optimal(mm) >= Q2_optimal(vec) for each instance
    print("\n=== H1 check: Q2_optimal(mm) >= Q2_optimal(vec) ===")
    pivot = df.pivot_table(index='source_key', columns='norm',
                           values='Q2_optimal', aggfunc='first')
    violations = 0
    for key in pivot.index:
        mm  = pivot.loc[key, 'mm']
        vec = pivot.loc[key, 'vec']
        diff = mm - vec
        ok = '✓' if diff >= -2.5 else '✗ VIOLATION'
        if diff < -2.5:
            violations += 1
        print(f"  {ok}  {key}: mm={mm:.1f}  vec={vec:.1f}  diff={diff:+.1f} pp")
    print(f"\nH1 violations: {violations}/{len(pivot)} "
          f"({'FALSIFIED' if violations/len(pivot) >= 0.20 else 'SUPPORTED'})")


if __name__ == '__main__':
    main()
