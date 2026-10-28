"""
corpus_mc.py  (corrected v3)
=============================
Monte Carlo Dirichlet experiment on active corpus matrices.

Design (declared before running, per PRESPEC.md §8):
  - Objectives F_g(T) = sum of N_mm[i,g_cols] for i in trio T, for each group g.
    Objectives are FIXED in min-max normalisation for all cells. This creates
    the score/objective mismatch that makes Q2 < 1 under vector and rank
    normalisation (Mechanism 1). If objectives were matched to the score
    normalisation, Q2 = 1 by Proposition 1 — a tautology (tested separately
    as regression assertion, NOT reported as a finding).
  - Score: SAW with the draw's normalisation (mm / vec / rnk).
  - Frontier: reconstructed per draw w from the set of C(m,3) trios.
  - k = 3 (portfolio size).
  - N = 3500 draws, kappa = 200.

Scope: tests Mechanism 1 (amplitude identity → ordering Q2(mm)>=Q2(vec)) in
independent matrices. Without coupling constraints, greedy == optimal by
separability. No assembly factor. Q2 values will be close to 100%; the
discriminating quantity is the ORDERING across normalisations and the MARGIN
relative to the frontier base rate.

Regression assertion (Proposition 1):
  When score normalisation matches objective normalisation (matched cell),
  Q2 must equal 100% exactly. Failure indicates a bug: wrong orientation,
  wrong group indices, or mismatched scale between score and objectives.
"""
import sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
from scipy.stats import dirichlet as sp_dirichlet
from corpus_data import CORPUS

# ─── Parameters ──────────────────────────────────────────────────────────────
K      = 3       # portfolio size
KAPPA  = 200     # Dirichlet concentration
N_DRAW = 3500
SEED   = 42
RNG    = np.random.default_rng(SEED)


# ─── Normalisation (benefit-oriented: higher = better after this) ─────────────
def norm_minmax(X, dirs):
    m, n = X.shape
    N = np.zeros_like(X, dtype=float)
    for j in range(n):
        col = X[:, j].astype(float)
        lo, hi = col.min(), col.max()
        if hi == lo:
            N[:, j] = 1.0; continue
        if dirs[j] == 'max':
            N[:, j] = (col - lo) / (hi - lo)
        else:
            N[:, j] = (hi - col) / (hi - lo)
    return N


def norm_vector(X, dirs):
    m, n = X.shape
    N = np.zeros_like(X, dtype=float)
    for j in range(n):
        col = X[:, j].astype(float)
        if dirs[j] != 'max':
            col = col.max() + col.min() - col  # complement
        norm_j = np.sqrt(np.sum(col**2))
        N[:, j] = col / norm_j if norm_j > 0 else 0.0
    return N


def norm_ranks(X, dirs):
    m, n = X.shape
    N = np.zeros((m, n))
    for j in range(n):
        col = X[:, j].astype(float)
        if dirs[j] != 'max':
            col = col.max() + col.min() - col
        order = np.argsort(col)
        # compute midranks
        ranks = np.zeros(m)
        i = 0
        while i < m:
            v = col[order[i]]
            j_end = i
            while j_end < m and col[order[j_end]] == v:
                j_end += 1
            mr = (i + 1 + j_end) / 2.0
            for k in range(i, j_end):
                ranks[order[k]] = mr
            i = j_end
        N[:, j] = ranks / (m + 1)
    return N


NORM_FNS = {'mm': norm_minmax, 'vec': norm_vector, 'rnk': norm_ranks}


# ─── Group objectives (weighted, on mm-normalised matrix) ───────────────────
def build_group_scores_mm(N_mm, w, obj_groups):
    """G[i, g] = sum_{j in g} w_j * N_mm[i, j]  — weighted group scores.
    N_mm is benefit-oriented. w must be normalised (sum=1).
    Returns (m x K_g) matrix; higher = better in each group.

    Objectives are weighted to match the article definition F_g(a) = Σ w_j n_j(a).
    Without weights, the Pareto frontier does not depend on w_draw and the
    condition w_ob = w_fr (§5.1) cannot be tested. See 2b in audit notes.
    """
    m = N_mm.shape[0]
    K_g = len(obj_groups)
    G = np.zeros((m, K_g))
    for g, cols in enumerate(obj_groups):
        for j in cols:
            G[:, g] += w[j] * N_mm[:, j]
    return G


def trio_objectives(G, trios):
    """F[t, g] = sum_{i in trio t} G[i, g].  Higher = better."""
    n_trios = len(trios)
    K_g = G.shape[1]
    F = np.zeros((n_trios, K_g))
    for t_idx, trio in enumerate(trios):
        for i in trio:
            F[t_idx] += G[i]
    return F


def pareto_nd(F):
    """Indices of non-dominated rows of F (higher = better in all cols)."""
    n = F.shape[0]
    dominated = np.zeros(n, dtype=bool)
    for i in range(n):
        if dominated[i]:
            continue
        # vectorised check: any row j that dominates i
        ge = np.all(F >= F[i], axis=1)   # j >= i on all objectives
        gt = np.any(F >  F[i], axis=1)   # j >  i on at least one
        strictly = ge & gt
        strictly[i] = False
        if np.any(strictly):
            dominated[i] = True
    return set(np.where(~dominated)[0])


# ─── SAW score ────────────────────────────────────────────────────────────────
def top_trio_by_score(scores, trios):
    """Return index (into trios) of the trio with highest total SAW score."""
    trio_scores = [scores[list(t)].sum() for t in trios]
    return int(np.argmax(trio_scores))


# ─── Proposition 1 regression assertion ──────────────────────────────────────
def assert_matched_q2(entry, trios, F_pub, norm_label='mm'):
    """When score norm matches objective norm (both built with same w), Q2 must be 1.
    Uses published weights for the deterministic check.
    F_pub must have been built with the SAME norm as norm_label and the published w.
    """
    X    = np.array(entry['matrix'], dtype=float)
    w    = np.array(entry['weights'], dtype=float); w /= w.sum()
    dirs = entry['directions']
    N    = NORM_FNS[norm_label](X, dirs)
    scores = N @ w
    frontier = pareto_nd(F_pub)
    t_idx = top_trio_by_score(scores, trios)
    in_f  = t_idx in frontier
    assert in_f, (
        f"Proposition 1 violation: {entry['source_key']} norm={norm_label} "
        f"published weights — top trio {trios[t_idx]} NOT in frontier of "
        f"{len(frontier)}/{len(trios)} trios. Bug in orientation, grouping, or weighting."
    )


# ─── Main experiment per entry ────────────────────────────────────────────────
def run_entry(entry):
    if not entry.get('active', False):
        return None

    key  = entry['source_key']
    X    = np.array(entry['matrix'], dtype=float)
    w0   = np.array(entry['weights'], dtype=float); w0 /= w0.sum()
    dirs = entry['directions']
    og   = entry.get('obj_groups') or [[j] for j in range(X.shape[1])]
    m, n = X.shape

    # Fixed min-max normalisation for objectives
    N_mm = norm_minmax(X, dirs)
    G_mm_pub = build_group_scores_mm(N_mm, w0, og)   # weighted with published w

    # All trios (fixed)
    trios   = list(itertools.combinations(range(m), K))
    n_trios = len(trios)

    # Frontier with published weights (for Prop1 regression check)
    F_mm_pub = trio_objectives(G_mm_pub, trios)

    # --- Proposition 1 regression: one matched cell per norm (correct F) ---
    prop1_results = {}
    for match_label in ['mm', 'vec', 'rnk']:
        N_match  = NORM_FNS[match_label](X, dirs)
        G_match  = build_group_scores_mm(N_match, w0, og)   # objectives in SAME norm
        F_match  = trio_objectives(G_match, trios)
        frontier = pareto_nd(F_match)
        scores   = N_match @ w0
        t_idx    = top_trio_by_score(scores, trios)
        in_f     = t_idx in frontier
        prop1_results[match_label] = in_f
        status   = "PASS" if in_f else "FAIL (BUG)"
        print(f"  [Prop1 matched] {key}  {match_label} ... {status}")
        assert in_f, (
            f"Prop1 violation: {key} matched={match_label} — "
            f"top trio NOT in frontier (objectives and score both in {match_label}). Bug."
        )

    # --- Three targeted mutations — each MUST trigger (potency check) --------
    # Mutation A: invert direction of one group (G1 criteria get cost sense)
    # Expected: Q2 collapses because frontier is built with reversed objectives
    print(f"  [Mut-A] {key}  invert G1 direction ...", end='', flush=True)
    dirs_mut_A = list(dirs)
    for j in og[0]:                          # invert G1 criteria
        dirs_mut_A[j] = 'min' if dirs[j] == 'max' else 'max'
    N_mut_A  = norm_minmax(X, dirs_mut_A)
    G_mut_A  = build_group_scores_mm(N_mut_A, w0, og)
    F_mut_A  = trio_objectives(G_mut_A, trios)
    fr_mut_A = pareto_nd(F_mut_A)
    scores_A = norm_minmax(X, dirs) @ w0    # score uses ORIGINAL direction
    t_A      = top_trio_by_score(scores_A, trios)
    mut_A_triggered = t_A not in fr_mut_A
    print(f" {'TRIGGERED' if mut_A_triggered else 'NOT TRIGGERED'}")

    # Mutation B: permute weights within G1 (w_j reshuffled, total W_G1 unchanged)
    print(f"  [Mut-B] {key}  permute weights in G1 ...", end='', flush=True)
    w_mut_B = w0.copy()
    g1 = og[0]
    if len(g1) > 1:
        perm = np.roll(np.arange(len(g1)), 1)      # cyclic shift
        w_mut_B[g1] = w0[g1][perm]
    G_mm_B  = build_group_scores_mm(N_mm, w0, og)       # objectives with original w
    F_mm_B  = trio_objectives(G_mm_B, trios)
    fr_mm_B = pareto_nd(F_mm_B)
    # Score uses permuted weights → different top trio
    scores_B = N_mm @ w_mut_B
    t_B = top_trio_by_score(scores_B, trios)
    mut_B_triggered = t_B not in fr_mm_B
    print(f" {'TRIGGERED' if mut_B_triggered else 'NOT TRIGGERED (no power — base rate too high?)'}")

    # Mutation C: uniform w_fr vs published w_sc (mismatched weights)
    print(f"  [Mut-C] {key}  uniform w_fr vs published w_sc ...", end='', flush=True)
    w_unif = np.ones(n) / n
    G_unif = build_group_scores_mm(N_mm, w_unif, og)   # frontier with uniform w
    F_unif = trio_objectives(G_unif, trios)
    fr_unif = pareto_nd(F_unif)
    scores_C = N_mm @ w0                               # score with published w
    t_C = top_trio_by_score(scores_C, trios)
    mut_C_triggered = t_C not in fr_unif
    print(f" {'TRIGGERED' if mut_C_triggered else 'NOT TRIGGERED (no power — base rate too high?)'}")

    mut_power = {'A_invert': mut_A_triggered, 'B_permute': mut_B_triggered, 'C_uniform': mut_C_triggered}
    n_triggered = sum(mut_power.values())
    print(f"  [Mutation power] {n_triggered}/3 mutations triggered "
          f"({'adequate' if n_triggered >= 2 else 'LOW — assertions may not protect this instance'})")

    # --- Monte Carlo: objectives fixed in mm, weighted with w_draw per draw ---
    # Frontier IS w_draw-dependent because objectives are weighted.
    # w_ob = w_fr = w_draw (same draw weights for both score and objectives).
    results = {}
    for norm_label, norm_fn in NORM_FNS.items():
        nd = 0
        alpha = KAPPA * w0
        W = sp_dirichlet.rvs(alpha, size=N_DRAW, random_state=RNG)

        for w_draw in W:
            N_score   = norm_fn(X, dirs)
            scores    = N_score @ w_draw
            # Frontier rebuilt with w_draw: objectives are weighted mm,
            # so the frontier changes with w_draw. Condition w_ob=w_fr holds.
            G_draw    = build_group_scores_mm(N_mm, w_draw, og)
            F_draw    = trio_objectives(G_draw, trios)
            frontier  = pareto_nd(F_draw)
            t_idx     = top_trio_by_score(scores, trios)
            if t_idx in frontier:
                nd += 1

        q2 = nd / N_DRAW * 100.0
        se = np.sqrt(q2 * (100.0 - q2) / N_DRAW)
        frontier_pub = pareto_nd(F_mm_pub)
        results[norm_label] = {
            'Q2':         round(q2, 2),
            'SE':         round(se, 2),
            'n_frontier': len(frontier_pub),
            'n_trios':    n_trios,
            'base_rate':  round(len(frontier_pub) / n_trios * 100, 1),
        }
    return results


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    rows = []
    for entry in CORPUS:
        key = entry['source_key']
        if not entry.get('active', False):
            print(f"\n{key}  INACTIVE")
            continue

        m, n = entry['m'], entry['n']
        n_trios = len(list(itertools.combinations(range(m), K)))
        print(f"\n{'='*60}")
        print(f"{key}  m={m}  n={n}  C({m},{K})={n_trios}")
        res = run_entry(entry)
        if res is None:
            continue

        for norm, vals in res.items():
            print(f"  {norm:4s}  Q2={vals['Q2']:6.2f}%  SE={vals['SE']:.2f}  "
                  f"|frontier|={vals['n_frontier']}/{vals['n_trios']}  "
                  f"base={vals['base_rate']:.1f}%")
            rows.append({
                'source_key': key,
                'm': m, 'n': n,
                'norm': norm,
                'Q2': vals['Q2'],
                'SE': vals['SE'],
                'n_frontier': vals['n_frontier'],
                'n_trios': vals['n_trios'],
                'base_rate': vals['base_rate'],
            })

    if not rows:
        print("\nNo active instances. Set active=True in corpus_data.py.")
        return

    df = pd.DataFrame(rows)
    out = os.path.join(os.path.dirname(__file__), '..', 'results', 'corpus_mc_results.csv')
    df.to_csv(out, index=False)

    print(f"\n{'='*60}")
    print("Summary:")
    print(df.to_string(index=False))

    # H1: Q2(mm) >= Q2(vec) per instance
    print(f"\n{'='*60}")
    print("H1 check: Q2(mm) >= Q2(vec)")
    pivot = df.pivot_table(index='source_key', columns='norm', values='Q2', aggfunc='first')
    violations = 0
    for key in pivot.index:
        mm  = pivot.loc[key, 'mm']
        vec = pivot.loc[key, 'vec']
        diff = mm - vec
        # tolerance: 3*SE ≈ 0.5 pp for N=3500
        ok = diff >= -1.5
        mark = '✓' if ok else '✗ VIOLATION'
        if not ok:
            violations += 1
        print(f"  {mark}  {key}: mm={mm:.2f}%  vec={vec:.2f}%  diff={diff:+.2f}pp")

    n_active = len(pivot)
    print(f"\nH1 violations: {violations}/{n_active} "
          f"({'FALSIFIED' if violations / n_active >= 0.20 else 'SUPPORTED'})")
    print(f"Saved to {out}")


if __name__ == '__main__':
    main()
