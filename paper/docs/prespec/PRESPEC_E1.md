# PRESPEC_E1.md — Pre-Specification for Experiment E1
# "Between-group vs within-group distortion in portfolio efficiency"
#
# WRITTEN BEFORE RUNNING. This commit precedes any E1 execution.
# Date: 2026-09-30
# Author: J. Azancort Neto
#
# Purpose: test the sufficient/necessary condition in the Extension of
# Proposition 1 by direct intervention on amplitudes.
#
# If E1 confirms the predictions, the article has a causal result, not
# a correlation. If it does not, the ceiling stays at ~8.

## 1. Theoretical basis

Extension of Proposition 1 (sketch, to be formalised in §6):

  Let the score normalisation be affine per column relative to min-max,
  n_j = a_j * n_j^mm + b_j, with a_j > 0.

  (i) SUFFICIENCY: if a_j is constant within each objective group G_g
      for all g, then optimal assembly produces a Pareto-efficient
      portfolio for any w, any instance, and any coupling constraint.
      Proof: the score is a positive scalarisation of the group
      objectives (Proposition 1 argument applied group-wise).

  (ii) NECESSITY: if there exist j, k in the same group with a_j ≠ a_k,
      there exist data for which the optimal portfolio is dominated.
      Construction: two portfolios equal on all other groups. The one
      with higher weight on the larger-amplitude criterion wins the score
      and loses on F_g. Formal proof follows with k=1, m=2.

Consequence: TV_B (between-group distortion) only displaces the choice
along the frontier. TV_W (within-group distortion) removes it from the
frontier. TV total mixes the two and orders efficiency loss poorly.

## 2. Experimental design

Instance: Fogo (m=1940, admissible m'=389, k=3, separation=10km).
Source of constants: fogo_constants.py (generated from main.tex tab:amplitude).

Groups (from fogo_constants.py):
  G1 = [perm, slope, roads]          indices [0,1,2]   W_G1=0.2950
  G2 = [rivers, aspect, coast, prot, wells] indices [3..7] W_G2=0.3560
  G3 = [urban, aero, cult]           indices [8,9,10]  W_G3=0.3490

Three amplitude cells:

| Cell | A_j description                     | TV    | TV_B   | TV_W   |
|------|-------------------------------------|-------|--------|--------|
| E1-B | A_j = Ā_g (constant within group)   | 0.2489 | 0.2489 | 0.0000 |
| E1-W | A_j = ρ_j/Ā_g × scale (between=0) | 0.1986 | 0.0000 | 0.1986 |
| E1-V | A_j = ρ_j (vector norm, published)  | 0.3146 | 0.2489 | 0.1986 |

Ā_g values (weighted mean within group):
  G1: Ā_G1 = 0.3731
  G2: Ā_G2 = 0.1458
  G3: Ā_G3 = 0.1157

E1-W rescale factor: 0.2024 (so weighted mean of E1-W Aj = weighted mean of E1-V Aj).

Score normalisation: applied to the full matrix (1940 sites);
objectives: fixed in min-max over admissible sites (389) — same as WP3.

Parameters: N=500 Dirichlet draws, κ=200, seed=42.

## 3. Pre-declared predictions

### P1 (Hard assertion — falsification closes the argument)
E1-B OPTIMAL = 100.0%.
Rationale: by sufficiency (i), constant Aj within groups means the
score is a positive scalarisation of the group objectives. Therefore
optimal assembly = Pareto-efficient. No exception.

This is an assertion, not a hypothesis. If P1 fails, there is a bug.

### P2 (Primary empirical prediction)
E1-W OPTIMAL ≈ E1-V OPTIMAL (within 5 pp).
Rationale: both E1-W and E1-V have TV_W = 0.1986. By the necessity
argument, within-group distortion is the operative channel for
efficiency loss in optimal assembly. Between-group distortion (TV_B)
only displaces the choice along the frontier — it does not move it off
the frontier. Therefore E1-W should reproduce the loss of E1-V in
optimal assembly.

Predicted E1-W OPTIMAL: ~57% (close to E1-V OPTIMAL = 56.8%).
Falsification criterion: if E1-W OPTIMAL > E1-B OPTIMAL - 10pp = 90%,
the within-group channel accounts for <10% of the loss, and the
decomposition does not support the causal claim.

### P3 (Secondary prediction)
E1-B GREEDY ≠ 100.0%.
Rationale: greedy assembly is not constrained to be Pareto-efficient
even under constant-Aj normalisation. Foreclosure (selecting
sub-optimal combinations under coupling constraints) affects greedy
but not optimal. E1-B should still show the greedy/optimal gap.

Predicted E1-B GREEDY: ~65% (similar to E1-V GREEDY = 54.0%,
but possibly higher since TV_W=0 removes misranking within groups).

## 4. Falsification criteria

| Prediction | Falsified if                              | Consequence |
|------------|-------------------------------------------|-------------|
| P1         | E1-B optimal < 100%                       | Bug in code |
| P2         | E1-W optimal > 90% (loss < 10pp)         | TV_W not the operative channel; max score ~8 |
| P2         | E1-W optimal < 45% (loss > 55pp from 100%) | E1-W introduces spurious effects; inspect Aj |
| P3         | E1-B greedy = 100%                        | No greedy/optimal gap; unexpected |

## 5. Connection to article structure

If P1 and P2 are confirmed:
  - The theorem (sufficiency+necessity) becomes the central result.
  - E1 provides causal evidence that TV_W governs efficiency loss.
  - The synthetic grid (WS2) replaces the current 3-point regression
    with a 4×4 grid in (s_B, s_W) space.
  - The article restructures around one thesis (§5 below).

If P2 is not confirmed:
  - The article retains its current structure.
  - The decomposition TV = (TV_B, TV_W) is reported as descriptive only.
  - Ceiling remains ~8.

## 6. Proposed thesis (conditional on E1 confirmation)

"Normalisation costs Pareto efficiency exactly through within-group
distortion. Between-group distortion only displaces the chosen portfolio
along the frontier. Optimal assembly amplifies within-group distortion;
greedy assembly is additionally subject to foreclosure."

## 7. Computation

Script: scripts/run_e1.py
Run on: Athena (~/scratch/mcdm-landfill-pareto)
Expected time: ~3 min (6 cells × 500 draws, greedy+optimal)

Output: results/e1_results.csv
Columns: cell, assembly, Q2, SE, n_draws
