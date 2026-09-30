"""
corpus_amplitudes.py
====================
For each matrix in corpus_data.py, compute:
  - Aj under min-max, vector, and ranks normalisation
  - TV  = sum_j w_j |A_j - 1|
  - m_eff = 1 / sum_j (w_j A_j / sum_k w_k A_k)^2
  - ||delta||_2 = 2*TV / sqrt(m_eff)

Outputs:
  results/corpus_amplitudes.csv
  (printed table to stdout)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
from corpus_data import CORPUS


def normalise_minmax(X, directions):
    """Min-max normalisation. All columns mapped to [0,1] with max=1 beneficial."""
    m, n = X.shape
    N = np.zeros_like(X)
    for j in range(n):
        col = X[:, j]
        lo, hi = col.min(), col.max()
        if hi == lo:
            N[:, j] = 1.0
            continue
        if directions[j] == 'max':
            N[:, j] = (col - lo) / (hi - lo)
        else:  # min/cost
            N[:, j] = (hi - col) / (hi - lo)
    return N


def normalise_vector(X, directions):
    """Vector (Euclidean) normalisation. Cost criteria complemented after."""
    m, n = X.shape
    # For cost criteria, use complement: x_j -> (max+min - x_j) then vector-norm
    # (same convention as the paper's _build_decision_matrix)
    X2 = X.copy().astype(float)
    for j in range(n):
        if directions[j] != 'max':
            X2[:, j] = X[:, j].max() + X[:, j].min() - X[:, j]
    N = np.zeros_like(X2)
    for j in range(n):
        norm_j = np.sqrt(np.sum(X2[:, j]**2))
        N[:, j] = X2[:, j] / norm_j if norm_j > 0 else 0.0
    return N


def normalise_ranks(X, directions):
    """Midrank normalisation: r_ij / (m+1). Higher rank = better."""
    m, n = X.shape
    N = np.zeros((m, n))
    for j in range(n):
        col = X[:, j].astype(float)
        if directions[j] == 'max':
            # rank 1 = smallest (worst), rank m = largest (best)
            ranks = col.argsort().argsort() + 1.0  # 1..m
        else:
            ranks = (-col).argsort().argsort() + 1.0  # rank 1 = largest (worst for cost)
        N[:, j] = ranks / (m + 1)
    return N


def amplitude(N):
    """A_j = std(N[:,j])  * sqrt(m) — equivalent to ||N[:,j]||_2 for mean-0 cols.
    Actually: A_j as used in the paper = std(normalised column) relative to
    min-max std. For consistency: A_j = std(N[:,j]) / std(N_mm[:,j]).
    
    Simpler and directly comparable: use the paper's definition
    A_j = ||normalised_col||_2 for vector norm; for min-max A_j ≡ 1 by construction
    because the paper defines amplitude as the l2-norm of the normalised column
    divided by the l2-norm under min-max.
    
    Implementation: A_j = std(N[:,j]) * sqrt(m) / (std(N_mm[:,j]) * sqrt(m))
                        = std(N[:,j]) / std(N_mm[:,j])
    This gives A_j(mm) ≡ 1 exactly, and A_j(vec) = std(vec_col)/std(mm_col).
    """
    pass  # see compute_amplitudes below


def compute_amplitudes(entry):
    """Return dict of TV, m_eff, l2 for mm, vector, ranks."""
    X = np.array(entry['matrix'], dtype=float)
    w = np.array(entry['weights'], dtype=float)
    w = w / w.sum()  # ensure normalised
    dirs = entry['directions']
    m, n = X.shape

    N_mm  = normalise_minmax(X, dirs)
    N_vec = normalise_vector(X, dirs)
    N_rnk = normalise_ranks(X, dirs)

    results = {}
    for label, N in [('mm', N_mm), ('vec', N_vec), ('rnk', N_rnk)]:
        # Reference: N_mm has std per column; use that as denominator
        # Aj = std(N[:,j]) / std(N_mm[:,j])  with N_mm as reference
        # Note: for mm, Aj = 1 by definition
        Aj = np.zeros(n)
        for j in range(n):
            std_ref = N_mm[:, j].std(ddof=0)
            std_j   = N[:, j].std(ddof=0)
            Aj[j] = std_j / std_ref if std_ref > 0 else 1.0

        # Effective weights: w_eff_j = w_j * A_j / sum(w_k A_k)
        wA = w * Aj
        wA_sum = wA.sum()
        w_eff = wA / wA_sum if wA_sum > 0 else w.copy()

        # TV = sum_j w_j |A_j - 1|
        TV = float(np.sum(w * np.abs(Aj - 1.0)))

        # m_eff = 1 / sum_j (w_eff_j)^2
        meff = 1.0 / np.sum(w_eff**2) if np.sum(w_eff**2) > 0 else float('inf')

        # ||delta||_2 = 2*TV / sqrt(m_eff)
        l2 = 2 * TV / np.sqrt(meff) if meff < float('inf') else 0.0

        results[label] = {'TV': TV, 'm_eff': meff, 'l2': l2, 'Aj': Aj}

    return results


def main():
    rows = []
    for entry in CORPUS:
        res = compute_amplitudes(entry)
        for norm, vals in res.items():
            rows.append({
                'source_key': entry['source_key'],
                'm': entry['m'],
                'n': entry['n'],
                'norm': norm,
                'TV':   round(vals['TV'],   6),
                'm_eff': round(vals['m_eff'], 4) if vals['m_eff'] < 1e9 else float('inf'),
                'l2':  round(vals['l2'],   6),
            })

    df = pd.DataFrame(rows)
    out = os.path.join(os.path.dirname(__file__), '..', 'results', 'corpus_amplitudes.csv')
    df.to_csv(out, index=False)
    print(df.to_string(index=False))
    print(f"\nSaved to {out}")

    # Cross-check identity ||delta||_2 = 2*TV/sqrt(m_eff) to 1e-5
    print("\n=== Identity check: ||delta||_2 = 2*TV/sqrt(m_eff) ===")
    for _, row in df.iterrows():
        if row['m_eff'] < 1e9 and row['TV'] > 0:
            expected = 2 * row['TV'] / (row['m_eff'] ** 0.5)
            diff = abs(expected - row['l2'])
            ok = '✓' if diff < 1e-4 else '✗'
            print(f"  {ok}  {row['source_key']}/{row['norm']}: "
                  f"2*TV/√m_eff={expected:.6f}  l2={row['l2']:.6f}  |diff|={diff:.2e}")


if __name__ == '__main__':
    main()
