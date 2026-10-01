# PRESPEC_E4 — Reference-set mismatch as within-group re-weighting
#
# WRITTEN BEFORE RUNNING. This commit precedes any E4 execution.
# Date: 2026-10-01
# Author: J. Azancort Neto
#
# Purpose: test whether the reference-set mismatch (Mechanism 2 of
# Marco A) can be fully accounted for by Theorem thm:groupconst, i.e.
# whether it reduces to within-group re-weighting of the same form as E1.

## 1. Theoretical basis

In the 473/A' cell, the score is SAW with normalisation constants
computed over 473 sites, but selection and evaluation are restricted to
the 389 admissible sites (confirmed in mc_2cube_fixed.py line 173:
`sc4 = build_score_473(w, agg=agg_4)` with argmax over D_via).

Let r_j = range_389(j) / range_473(j) (tab:amprefset). For a SAW score
normalised over 473 sites but evaluated over 389:

  n_j^{473}(a) = (c_j(a) - min_473) / range_473(j)

This is an affine function of n_j^{389}(a) = (c_j(a) - min_389) / range_389(j):

  n_j^{473}(a) = b_j + r_j * n_j^{389}(a)

where r_j = range_389 / range_473 and b_j = (min_389 - min_473) / range_473.

The effective amplitude is A_j = r_j. Theorem thm:groupconst applies
directly: exact assembly is Pareto-efficient iff r_j is constant within
each group.

The mirror direction (389 score vs A evaluator) uses A_j = 1/r_j.

## 2. Design

Instance: Fogo (m=1940, admissible m'=389, k=3, separation=10km).
Score: SAW, constants from run_at_473_sites = mc_2cube_fixed.py line 106-121.
Evaluator: objectives and frontier over A' (389 sites), per draw,
  pareto_utils, eps=1e-9, kappa=200, N=1000.
Seed: 42 (declared before any run).

Groups and r_j values (to be computed from tab:amprefset before running;
the PRESPEC declares the structure, not the numerical values):
  G1 = [perm, slope, roads]         indices [0,1,2]
  G2 = [rivers, aspect, coast, prot, wells]  indices [3..7]
  G3 = [urban, aero, cult]          indices [8,9,10]

Four cells (direction 473 → A'):
  R-M: A_j = 1           (aligned control; identical to 389/A')
  R-B: A_j = rbar_g      (w-weighted mean of r_j within group g)
  R-W: A_j ∝ r_j/rbar_g  (group totals equalised; within-group only)
  R-V: A_j = r_j         (= the published 473/A' cell; tab:fourthcell row 1)

Four cells (direction 389 → A, mirror):
  R-M': A_j = 1
  R-B': A_j = 1/rbar_g
  R-W': A_j ∝ (1/r_j)/(1/rbar_g)
  R-V': A_j = 1/r_j       (= the published 389/A cell; tab:fourthcell row 3)

Unit of analysis: cell, paired bootstrap by draw (2000 replicates).

## 3. Pre-declared predictions

### P_E4_1 (Theorem — hard assertion)
R-B optimal Q2 = 100% on every draw, both directions.
R-B' optimal Q2 = 100% on every draw.
Rationale: if r_j = rbar_g within each group, Theorem thm:groupconst
applies. Failure = bug or theorem false (given the affine structure above).

### P_E4_2 (Regression test)
R-V optimal reproduces tab:fourthcell within 3 SE:
  Direction 473→A': Q2_opt ≈ 20.0% (tab:fourthcell row 1, optimal)
  Direction 389→A:  Q2_opt ≈ 95.0% (tab:fourthcell row 3, optimal)
Rationale: R-V is defined to reproduce the published cell exactly.
Failure = pipeline bug.

### P_E4_3
R-W optimal loss >= 50% of R-V optimal loss, in the 473→A' direction.
  Declared: (100% - Q2_opt[R-W]) >= 0.50 * (100% - Q2_opt[R-V])
Rationale: within-group distortion carries most of the loss (E1 result
extended to this direction). The exact fraction is unknown before running.

### P_E4_4 (exploratory, declared)
The 80 vs 5 pp asymmetry (tab:fourthcell) persists in R-W, i.e. the
473→A' direction has R-W loss > R-W' loss.
Rationale: asymmetry unexplained by TV, TV_B and TV_W in Marco A. If it
persists in R-W (within-group only), it is not explained by the theorem.

### P_E4_5 (exploratory, declared)
In the 473→A' direction, R-W optimal loss > E1-W optimal loss,
despite E4's TV_W being smaller than E1's TV_W (0.199).
  Declared: Q2_opt[R-W, 473→A'] < Q2_opt[E1-W] = 64.2%
Rationale: if the loss depends on which criterion carries the within-group
distortion (perm, with 350 tied zeros) rather than just the size of TV_W,
then E4's R-W (where the distortion falls on perm's group G1) should
incur a larger loss than E1-W (where TV_W = 0.199 is spread differently).
Confirmation would establish that the loss depends on the identity of the
distorted criterion, not just its magnitude — pointing to the next
theoretical result.

Inherited constraint: the asymmetry was unexplained by TV, TV_B and TV_W
(Marco A, §8.1). E4 tests whether it is explained by the affine structure.

## 4. Falsification criteria

| Prediction | Falsified if | Consequence |
|---|---|---|
| P_E4_1 | R-B optimal < 100% on any draw | Bug or theorem false for this class |
| P_E4_2 | |Q2 - tab| > 3 SE for either direction | Pipeline bug |
| P_E4_3 | R-W loss < 50% of R-V loss | Within-group distortion not dominant in this direction |
| P_E4_4 | R-W loss ≈ R-W' loss (symmetric) | Asymmetry explained by within-group component |

## 5. Connection to article structure

If P_E4_1 and P_E4_3 confirmed:
  - The reference-set mismatch reduces to within-group re-weighting.
  - "Mechanism 2" is an instance of Theorem thm:groupconst, not a separate phenomenon.
  - §8.1 replaces "Neither the magnitude nor the group structure accounts
    for this asymmetry" with a confirmed prediction and an explanation.
  - The article has two pre-registered confirmations in different situations.

If P_E4_1 confirmed but P_E4_3 not:
  - The theorem holds but within-group distortion is not the dominant channel here.
  - "Mechanism 2" remains distinct.

If P_E4_1 fails:
  - The affine structure assumed above does not hold for this cell (possible
    if min_389 < min_473 for some criterion, making b_j negative and the
    mapping non-affine on [0,1]). Redesign required.

## 6. Deviations from PRESPEC declared before running (DEV-E4)

### DEV-E4-001: alpha parameter clarification
Section 6 estimated "8 cells × 1000 draws × 2 alphas". The 2 alphas
refer to the Dirichlet concentration parameter values (alpha=50 and
alpha=200), following mc_2cube_fixed.py which uses ALPHAS = [50, 200].
The PRESPEC declares kappa=200 as the portfolio size; alpha is a separate
parameter governing weight uncertainty. Both alpha values are run; the
primary estimand uses alpha=200 (matching the main factorial).

### DEV-E4-003: kappa clarification (supersedes DEV-E4-001) and N_draws alignment
DEV-E4-001 misidentified kappa as the portfolio size. In this project kappa
is the Dirichlet concentration parameter (kappa ∈ {50, 200}); ALPHAS = [50, 200]
in mc_2cube_fixed.py line 39 are these two kappa values. Portfolio size is k = 3
(\kk in the manuscript, main.tex line 28). DEV-E4-001 is superseded.

N_draws: the PRESPEC (Section 7) declared N = 1000. mc_2cube_fixed.py uses
N_DRAWS = 500 (line 37), matching the main factorial and E1. E4 will use
N = 500 to enable paired-by-draw comparison with E1. Pairing strategy: the
weight matrix from E1 (500 × 11, kappa = 200, seed 42) is saved as
results/e1_weights_k200.npy before running E4; E4 loads this matrix directly
rather than regenerating from seed. This ensures identical weight vectors
regardless of RNG state.

SHA-256 of results/e1_weights_k200.npy:
  bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487
(generated by scripts/tvw_e4.py, commit d4e970b, 2026-10-01T19:35-03:00)

Feasibility check (A3): fogo_trios.npy indexes trios over df_via (max index 388,
confirmed 2026-10-01T19:36). The 84 excluded sites (dist_protected == 0) have no
positional index in df_via. Frontier trios cannot contain excluded sites by
construction; the same T is used in both directions. No DEV-E4-005 required.

### DEV-E4-002: mirror direction frontier
The design states "direction 389→A, mirror" but the frontier for space A
is defined over objectives computed on 473 sites (all candidates).
Clarification: for the 389→A direction, the evaluator uses:
  - Score: SAW with constants over 389 sites (range_389)
  - Objectives: computed on 473 sites (as in the published tab:fourthcell)
  - Frontier: space A (213 portfolios, objectives over 473 sites)
This is the published 389/A cell from tab:fourthcell (row 3: greedy=58.8%,
optimal=95.0%), confirmed as the regression test in P_E4_2.
The affine relation A_j = 1/r_j holds because: the 389-site score has
amplitude 1, while the A-evaluator uses 473-site objectives with
amplitude range_473/range_389 = 1/r_j relative to the score.

### DEV-E4-004: P_E4_5 restated (supersedes P_E4_5 text of commit ece6544)
Direction 473->A', cell R-W (A_j = r_j / rbar_g; TV_B = 0 by construction).
TV_W(R-W) = 0.0815, computed before running by scripts/tvw_e4.py
(commit d4e970b, 2026-10-01T19:35-03:00), using
TV_{W,g} = 0.5 * sum_{j in G_g} (w_j/W_g) * |A_j - 1|, the same definition
as \TVWvec in the manuscript.
Cross-check: same formula applied to E1-V amplitudes gives TV_W = 0.1986
(manuscript \TVWvec = 0.199). Factor-of-2 error in the ece6544 text corrected.

Reference: E1-W has TV_W = 0.199 and Q2_opt = 64.2% (loss 35.8 pp).
Declared: Q2_opt[R-W, 473->A'] < 64.2%, paired by draw (kappa = 200,
weight matrix from e1_weights_k200.npy, SHA-256 as in DEV-E4-003).

Rationale: within G1, E1-W inflates perm's within-group share by 1.563x
(rho_perm/Abar_G1 = 0.583/0.373 = 1.563x, computed by tvw_e4.py);
R-W deflates it by 0.788x (r_perm/rbar_G1 = 0.482/0.612 = 0.788x).
Despite TV_W(R-W) = 0.0815 < 0.199 = TV_W(E1-W), if R-W loses more than
E1-W (35.8 pp), the result is consistent with the hypothesis that loss
depends on the direction of distortion on the dominant zero-heavy criterion
(deflation more costly than inflation at comparable TV_W), not on TV_W alone.
"Consistent with" does not establish the hypothesis; it motivates a design
that controls inflation versus deflation at fixed TV_W.

Note: the P_E4_5 text in commit ece6544 used TV_W(R-W) = 0.163 (missing
factor 1/2) and A_perm factor = 2.88x (the full cell-V ratio, not the
within-group ratio). This DEV supersedes that text.

## 7. Computation

Script: scripts/run_e4.py (to be written)
Run on: Athena (~/scratch/mcdm-landfill-pareto)
Expected time: ~6 min (8 cells × 1000 draws × 2 alphas, greedy+optimal)
Output: results/e4_results.csv
Columns: cell, direction, assembly, Q2, SE, n_draws

## 8. Note on frontier asymmetry

tab:fourthcell rows use different frontiers:
  473/A' uses frontier A' (181 portfolios in 389 admissible)
  389/A  uses frontier A  (213 portfolios in 389 admissible)

This confounder is acknowledged. P_E4_3 and P_E4_4 compare cells within
the same direction (same frontier), so the confounder does not affect them.
P_E4_1 is unaffected (the frontier is always A', and B attains 100% of it).
