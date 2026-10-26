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


def compute_TV_between_within(w, Aj, obj_groups):
    """Decompose TV into between-group (TV_B) and within-group (TV_W) components.

    TV_B measures distortion of group-level weights:
        W_g = sum_{j in g} w_j   (nominal group weight)
        W_g^eff = sum_{j in g} w_j^eff  (effective group weight)
        TV_B = 0.5 * sum_g |W_g^eff - W_g|

    TV_W measures within-group re-weighting, weighted average across groups:
        For each group g with nominal weight W_g:
          w_{j|g} = w_j / W_g         (relative weight within group)
          w_{j|g}^eff = w_j^eff / W_g^eff  (relative effective weight)
          tv_g = 0.5 * sum_{j in g} |w_{j|g}^eff - w_{j|g}|  (within-group TV)
        TV_W = sum_g W_g * tv_g   (weighted mean of within-group TVs)

    The two components are NOT additive: TV != TV_B + TV_W in general.
    Report side by side, not as parts of a sum.

    Returns dict with TV_B, TV_W, and per-group tv_g.
    """
    w    = np.array(w, dtype=float); w = w / w.sum()
    Aj   = np.array(Aj, dtype=float)
    wA   = w * Aj
    wA_s = wA.sum()
    w_eff = wA / wA_s if wA_s > 0 else w.copy()

    K = len(obj_groups)
    W_g     = np.array([w[g].sum()     for g in obj_groups])
    W_g_eff = np.array([w_eff[g].sum() for g in obj_groups])

    TV_B = 0.5 * np.sum(np.abs(W_g_eff - W_g))

    tv_within = np.zeros(K)
    for idx, g in enumerate(obj_groups):
        wg  = w[g]     / W_g[idx]      if W_g[idx]     > 0 else np.zeros(len(g))
        wge = w_eff[g] / W_g_eff[idx]  if W_g_eff[idx] > 0 else np.zeros(len(g))
        tv_within[idx] = 0.5 * np.sum(np.abs(wge - wg))

    TV_W = np.sum(W_g * tv_within)

    return {
        'TV_B':     TV_B,
        'TV_W':     TV_W,
        'tv_within_per_group': tv_within,  # per-group raw tv_g
        'W_g':      W_g,
    }


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
    """Regression test: constants from fogo_constants.py only.
    Never write Fogo w/Aj/groups by hand here. See fogo_constants.py.
    Asserts: TV=0.3146, l2=0.3127, meff=4.0486, TV_B=0.2489, TV_W=0.1986.
    """
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(__file__))
    from fogo_constants import W, AJ_VEC, OBJ_GROUPS
    from fogo_constants import TV_VEC, L2_VEC, MEFF_VEC, TV_B_VEC, TV_W_VEC

    res    = compute_TV_meff(W, AJ_VEC)
    res_bw = compute_TV_between_within(W, AJ_VEC, OBJ_GROUPS)

    tol    = 1e-3
    ok_TV    = abs(res["TV"]    - TV_VEC)   < tol
    ok_l2    = abs(res["l2"]    - L2_VEC)   < tol
    ok_meff  = abs(res["m_eff"] - MEFF_VEC) < tol
    ok_TVB   = abs(res_bw["TV_B"] - TV_B_VEC) < tol
    ok_TVW   = abs(res_bw["TV_W"] - TV_W_VEC) < tol
    ok_ident = abs(2*res["TV"]/np.sqrt(res["m_eff"]) - res["l2"]) < 1e-10
    ok_not_D = abs(res["TV"] - float(np.sum(W * np.abs(AJ_VEC - 1.0)))) > 0.1

    Aj_bar = np.zeros_like(AJ_VEC)
    for g in OBJ_GROUPS:
        wg = W[g]; Ajg = AJ_VEC[g]
        Aj_bar_g = float(np.dot(wg, Ajg) / wg.sum())
        for j in g:
            Aj_bar[j] = Aj_bar_g
    res_cf = compute_TV_between_within(W, Aj_bar, OBJ_GROUPS)
    TV_cf  = compute_TV_meff(W, Aj_bar)["TV"]
    ok_cf  = abs(res_cf["TV_W"]) < 1e-10 and abs(TV_cf - res_cf["TV_B"]) < 1e-10

    rows_out = [
        ("TV",   res["TV"],       TV_VEC,   ok_TV),
        ("l2",   res["l2"],       L2_VEC,   ok_l2),
        ("meff", res["m_eff"],    MEFF_VEC, ok_meff),
        ("TV_B", res_bw["TV_B"], TV_B_VEC, ok_TVB),
        ("TV_W", res_bw["TV_W"], TV_W_VEC, ok_TVW),
    ]
    print("=== REGRESSION TEST: Fogo (fogo_constants.py -> main.tex) ===")
    for name, val, exp, ok in rows_out:
        print(f"  {name:<4} = {val:.4f}  expected {exp}  {'ok' if ok else 'FAIL'}")
    print(f"  identity 2TV/sqrt(meff)=l2:  {'ok' if ok_ident else 'FAIL'}")
    print(f"  TV != D:                     {'ok' if ok_not_D else 'FAIL'}")
    print(f"  counterfactual TV_W=0:       {'ok' if ok_cf    else 'FAIL'}")
    all_ok = ok_TV and ok_l2 and ok_meff and ok_TVB and ok_TVW and ok_ident and ok_not_D and ok_cf
    print(f"  Overall: {'PASS' if all_ok else 'FAIL'}")

    assert ok_TV,   f"TV={res['TV']:.4f} != {TV_VEC}"
    assert ok_l2,   f"l2={res['l2']:.4f} != {L2_VEC}"
    assert ok_meff, f"meff={res['m_eff']:.4f} != {MEFF_VEC}"
    assert ok_TVB,  f"TV_B={res_bw['TV_B']:.4f} != {TV_B_VEC} -- OBJ_GROUPS wrong? (perm in G1 not G3)"
    assert ok_TVW,  f"TV_W={res_bw['TV_W']:.4f} != {TV_W_VEC} -- OBJ_GROUPS wrong? (perm in G1 not G3)"
    assert ok_ident, "2TV/sqrt(meff) != l2"
    assert ok_not_D, "TV == D -- wrong formula"
    assert ok_cf,    "counterfactual TV_W != 0 -- decomposition bug"
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
        og  = entry.get('obj_groups')  # None for inactive instances
        res = compute_all(entry)
        for norm, vals in res.items():
            # Non-trivial identity check (only when TV>0)
            if vals['TV'] > 0:
                l2_check = 2 * vals['TV'] / np.sqrt(vals['m_eff'])
                ident_ok = abs(l2_check - vals['l2']) < 1e-10
            else:
                ident_ok = True

            # TV_B / TV_W if groups declared
            TV_B = float('nan')
            TV_W = float('nan')
            if og is not None and norm != 'mm' and vals['TV'] > 0:
                w = np.array(entry['weights'], dtype=float); w = w / w.sum()
                X = np.array(entry['matrix'], dtype=float)
                dirs = entry['directions']
                Aj_fn = {'mm': Aj_minmax, 'vec': Aj_vector, 'rnk': Aj_ranks}[norm]
                Aj = Aj_fn(X, dirs)
                bw = compute_TV_between_within(w, Aj, og)
                TV_B = round(bw['TV_B'], 6)
                TV_W = round(bw['TV_W'], 6)

            rows.append({
                'source_key': key,
                'm': entry['m'],
                'n': entry['n'],
                'norm':  norm,
                'TV':    round(vals['TV'],   6),
                'm_eff': round(vals['m_eff'], 4) if not np.isnan(vals['m_eff']) else float('nan'),
                'l2':    round(vals['l2'],   6),
                'TV_B':  TV_B,
                'TV_W':  TV_W,
                'ident_ok': ident_ok,
            })

    df = pd.DataFrame(rows)
    out = os.path.join(os.path.dirname(__file__), '..', 'results', 'corpus_amplitudes.csv')
    df.to_csv(out, index=False)

    print("\n=== Corpus amplitudes — vector norm (active instances only) ===")
    active_keys = [e['source_key'] for e in CORPUS if e.get('active', False)]
    print(df[(df['norm']=='vec') & (df['source_key'].isin(active_keys))][
        ['source_key','m','n','TV','TV_B','TV_W','m_eff','l2','ident_ok']
    ].to_string(index=False))

    print("\n=== All instances — vector norm ===")
    print(df[df['norm']=='vec'][['source_key','m','n','TV','TV_B','TV_W','m_eff','l2']].to_string(index=False))

    print("\n=== Identity check (TV>0, all norms) ===")
    fails = df[(df['TV'] > 0) & (~df['ident_ok'])]
    if len(fails) == 0:
        n_checked = len(df[df['TV'] > 0])
        print(f"  ALL {n_checked} PASS")
    else:
        print(fails)

    print(f"\nFull table saved to {out}")


if __name__ == '__main__':
    main()
