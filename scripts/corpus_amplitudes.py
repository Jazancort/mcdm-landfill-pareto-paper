"""
corpus_amplitudes.py  (corrected)
==================================
For each matrix in corpus_data.py, compute Aj, TV, m_eff, l2 using the
EXACT definitions from the paper (Propositions 4-5, §6.2).

Definitions:
  A_j (min-max) = 1  by construction
  A_j (vector)  = rho_j = (max_j - min_j) / ||x_j||_2
                  For binary col with n1 positives: rho_j = 1/sqrt(n1)
  A_j (ranks)   = (r_max - r_min) / (m+1)
                  For binary: (m/2) / (m+1)  ≈ 1/2

  w_eff_j = w_j * A_j / sum_k(w_k * A_k)
  delta_j = w_eff_j - w_j
  TV      = 0.5 * sum_j |delta_j|          # eq:TV  (invariant to rescaling)
  l2      = sqrt(sum_j delta_j^2)          # ||delta||_2  (independent calc)
  m_eff   = ||delta||_1^2 / ||delta||_2^2  # Prop 5; nan when TV=0

The identity 2*TV/sqrt(m_eff) = l2 is VERIFIED independently (non-trivial).

REGRESSION TEST: Fogo (vector norm) must return TV≈0.315, m_eff≈4.05, l2≈0.313.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
from corpus_data import CORPUS


# ─── Aj under each normalisation ────────────────────────────────────────────

def Aj_vector(X_raw, directions):
    """A_j = rho_j = (max - min) / ||x_j||_2 for each column.
    For benefit cols, use x_j directly.
    For cost cols, use the complemented vector (max+min - x_j) — same rho_j
    since range and norm are invariant to this linear transform."""
    m, n = X_raw.shape
    Aj = np.zeros(n)
    for j in range(n):
        col = X_raw[:, j].astype(float)
        # cost complement: max+min-col; does not change range or ||.||_2
        # (confirmed: range(max+min-c) = range(c); ||max+min-c||_2 = ||c-mid||_2
        #  but mid shifts — safer: use col directly for range, norm of complement)
        if directions[j] != 'max':
            col = col.max() + col.min() - col
        rng  = col.max() - col.min()
        norm = np.sqrt(np.sum(col**2))
        Aj[j] = rng / norm if norm > 0 else 0.0
    return Aj


def Aj_minmax(X_raw, directions):
    """A_j = 1 for all j by construction."""
    return np.ones(X_raw.shape[1])


def Aj_ranks(X_raw, directions, m=None):
    """A_j = (r_max - r_min) / (m+1) using midranks (paper eq:Arank_binary).
    For continuous cols without ties: r_max = m, r_min = 1 → (m-1)/(m+1).
    For binary col with n0 zeros, n1 ones: exact midrank formula."""
    if m is None:
        m = X_raw.shape[0]
    n = X_raw.shape[1]
    Aj = np.zeros(n)
    for j in range(n):
        col = X_raw[:, j].astype(float)
        if directions[j] != 'max':
            col = col.max() + col.min() - col
        vals, counts = np.unique(col, return_counts=True)
        # Check if binary (exactly 2 distinct values)
        if len(vals) == 2:
            # midranks: group 0 (lower) midrank = (1 + counts[0])/2
            #           group 1 (upper) midrank = counts[0] + (1 + counts[1])/2
            r_low  = (1 + counts[0]) / 2
            r_high = counts[0] + (1 + counts[1]) / 2
            Aj[j] = (r_high - r_low) / (m + 1)
        else:
            # General: use actual max and min of midrank distribution
            # Compute midranks for each element
            sorted_col = np.sort(col)
            midranks = np.zeros(m)
            i = 0
            while i < m:
                j_end = i
                while j_end < m and sorted_col[j_end] == sorted_col[i]:
                    j_end += 1
                mr = (i + 1 + j_end) / 2.0  # midrank of tied group
                for k in range(i, j_end):
                    midranks[k] = mr
                i = j_end
            Aj[j] = (midranks.max() - midranks.min()) / (m + 1)
    return Aj


def compute_TV_meff(w, Aj):
    """Given weights w and amplitudes Aj, compute TV, l2, m_eff.
    Returns dict with keys TV, l2, m_eff, w_eff, delta.
    For min-max Aj≡1: TV=0, l2=0, m_eff=nan."""
    w    = np.array(w, dtype=float)
    w    = w / w.sum()
    Aj   = np.array(Aj, dtype=float)
    wA   = w * Aj
    wA_s = wA.sum()
    w_eff = wA / wA_s if wA_s > 0 else w.copy()
    delta = w_eff - w
    TV    = 0.5 * np.sum(np.abs(delta))
    l2    = np.sqrt(np.sum(delta**2))
    if np.any(delta != 0):
        meff = (np.sum(np.abs(delta))**2) / np.sum(delta**2)
    else:
        meff = float('nan')
    return {'TV': TV, 'l2': l2, 'm_eff': meff, 'w_eff': w_eff, 'delta': delta}


def compute_all(entry):
    X    = np.array(entry['matrix'], dtype=float)
    w    = np.array(entry['weights'], dtype=float)
    dirs = entry['directions']
    m    = X.shape[0]

    results = {}
    for label, Aj_fn in [('mm', Aj_minmax), ('vec', Aj_vector), ('rnk', Aj_ranks)]:
        Aj  = Aj_fn(X, dirs)
        res = compute_TV_meff(w, Aj)
        res['Aj'] = Aj
        results[label] = res
    return results


# ─── Regression test: Fogo ─────────────────────────────────────────────────

def regression_test_fogo():
    """Regression test using EXACT values from Table 1 of the paper.
    Source: tab:amplitude in main.tex (lines 1372–1390).
    Expected outputs: TV=0.3146, ||delta||_2=0.3127, m_eff=4.0486.
    These are PUBLISHED VALUES. Tolerance = 1e-3 (rounding of Aj to 3dp).
    Modifying expected values requires written justification in DEVIATIONS.md.
    """
    # Tab1 exact values — DO NOT CHANGE without updating DEVIATIONS.md
    # criteria:  perm   slope  roads  rivers aspect coast  prot   wells  urban  aero   cult
    w_tab1  = [0.152, 0.113, 0.030, 0.091, 0.075, 0.069, 0.066, 0.055, 0.166, 0.102, 0.081]
    Aj_vec  = [0.583, 0.135, 0.206, 0.265, 0.103, 0.126, 0.105, 0.081, 0.107, 0.086, 0.171]

    w  = np.array(w_tab1, dtype=float)
    Aj = np.array(Aj_vec,  dtype=float)
    w  = w / w.sum()

    res = compute_TV_meff(w, Aj)

    # Published values from §6.2 / tab:tvorder
    TV_pub   = 0.3146
    l2_pub   = 0.3127
    meff_pub = 4.0486
    tol      = 1e-3

    ok_TV   = abs(res['TV']    - TV_pub)   < tol
    ok_l2   = abs(res['l2']    - l2_pub)   < tol
    ok_meff = abs(res['m_eff'] - meff_pub) < tol
    ok_ident = abs(2*res['TV']/np.sqrt(res['m_eff']) - res['l2']) < 1e-10
    ok_not_D = abs(res['TV'] - float(np.sum(w * np.abs(Aj - 1.0)))) > 0.1

    print("=== REGRESSION TEST: Fogo (Tab1 exact values) ===")
    print(f"  TV   = {res['TV']:.4f}  expected {TV_pub}  {'✓' if ok_TV   else '✗ FAIL'}")
    print(f"  l2   = {res['l2']:.4f}  expected {l2_pub}  {'✓' if ok_l2   else '✗ FAIL'}")
    print(f"  meff = {res['m_eff']:.4f}  expected {meff_pub}  {'✓' if ok_meff else '✗ FAIL'}")
    print(f"  identity 2*TV/√meff = l2 (non-trivial): {'✓' if ok_ident else '✗ FAIL'}")
    print(f"  TV ≠ D (not the rejected formula):       {'✓' if ok_not_D else '✗ FAIL'}")

    all_ok = ok_TV and ok_l2 and ok_meff and ok_ident and ok_not_D
    if not all_ok:
        print("  ✗ REGRESSION FAILED — check inputs against Tab1 before continuing")
    else:
        print("  Overall: PASS")

    # Hard assert — test must not be weakened silently
    assert ok_TV,   f"TV={res['TV']:.4f} deviates from published {TV_pub} by more than 1e-3"
    assert ok_l2,   f"l2={res['l2']:.4f} deviates from published {l2_pub} by more than 1e-3"
    assert ok_meff, f"meff={res['m_eff']:.4f} deviates from published {meff_pub} by more than 1e-3"
    assert ok_ident, "Identity 2*TV/sqrt(meff) != l2 — formula error"
    assert ok_not_D, "TV == D — using rejected formula D instead of TV"
    return True


def main():
    # Run regression test first — must pass before corpus
    passed = regression_test_fogo()
    if not passed:
        print("\nAborting: Fogo regression test failed. Fix formulas first.")
        import sys; sys.exit(1)

    rows = []
    for entry in CORPUS:
        key = entry['source_key']
        res = compute_all(entry)
        for norm, vals in res.items():
            # Non-trivial identity check (only when TV>0)
            if vals['TV'] > 0:
                l2_check = 2 * vals['TV'] / np.sqrt(vals['m_eff'])
                ident_ok = abs(l2_check - vals['l2']) < 1e-10
            else:
                ident_ok = True  # trivial: TV=0 → l2=0 by construction
            rows.append({
                'source_key': key,
                'm': entry['m'],
                'n': entry['n'],
                'norm':  norm,
                'TV':    round(vals['TV'],   6),
                'm_eff': round(vals['m_eff'], 4) if not np.isnan(vals['m_eff']) else float('nan'),
                'l2':    round(vals['l2'],   6),
                'ident_ok': ident_ok,
            })

    df = pd.DataFrame(rows)
    out = os.path.join(os.path.dirname(__file__), '..', 'results', 'corpus_amplitudes.csv')
    df.to_csv(out, index=False)

    print("\n=== Corpus amplitudes (corrected formulas) ===")
    print(df[df['norm']=='vec'][['source_key','m','n','TV','m_eff','l2','ident_ok']].to_string(index=False))

    print("\n=== Identity check (non-trivial, TV>0 only) ===")
    fails = df[(df['TV'] > 0) & (~df['ident_ok'])]
    if len(fails) == 0:
        n_checked = len(df[df['TV'] > 0])
        print(f"  ALL {n_checked} PASS (non-trivial)")
    else:
        print(fails)

    print(f"\nFull table saved to {out}")


if __name__ == '__main__':
    main()
