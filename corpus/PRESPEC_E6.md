# PRESPEC_E6 — Mechanism Generalisation: Score-Only Amplitude Manipulation
#
# WRITTEN BEFORE RUNNING. This commit must precede any E6 execution.
# Date: 2026-10-XX
# Author: J. Azancort Neto
#
# Purpose: test whether the TV_W channel (E1) generalises to synthetic instances
# with different marginal distributions, using score-only amplitude manipulation
# (objectives fixed in min-max throughout).
#
# Critical difference from E5:
# E5 imposed amplitudes on score and objectives jointly, making optimal assembly
# efficient by construction (Q2_opt = 100% always, per Proposition 1). E6 applies
# amplitudes to the score only. The manuscript (§8.6) states: "E5 imposes amplitudes
# on score and objectives jointly, so optimal assembly is efficient by construction
# and the grid does not test Theorem 1." E6 is designed to test Theorem 1.

## 1. Theoretical basis

Theorem 1 (thm:groupconst, manuscript): optimal assembly is Pareto-efficient for
any instance and any Dirichlet draw if and only if the score amplitudes A_j are
constant within each objective group. Equivalently, TV_W = 0 is sufficient for
efficiency.

E6 tests three empirical claims that are NOT consequences of Theorem 1:

P2: Q2_opt is monotone non-increasing in TV_W (not implied by the theorem).
P3: TV_B amplifies the within-group loss (replicates E1 finding in synthetic context).
P4: inflating the highest-weight criterion within a group costs more than deflating
    it at the same TV_W (Remark rem:TVW leaves this open).

None of P2–P4 follows from Theorem 1. The theorem is existential: it guarantees
Q2_opt = 100% when TV_W = 0 and gives no prediction on the level of loss when
TV_W > 0.

## 2. Experimental design

### 2.1 Spatial structure

Instance: Fogo geometry (fogo_trios.npy, k=3, κ=200, d_min=10km, N_adm=389).
Criterion columns are redrawn from synthetic distributions.
The trios and separation constraints are identical to the main study; only the
marginal distributions of the columns change.

Rationale: using Fogo's trios avoids constructing new GIS data. The spatial
structure is instrumental; the estimands concern amplitude structure.

### 2.2 Marginal distribution families

| Family | Specification | Rationale |
|---|---|---|
| Lognormal | LogN(μ=0, σ=1) | Positive-skewed, no point mass at 0 |
| Beta(1,3) | — | Right-skewed, mass near 0, no exact zeros |
| Uniform | U(0,1) | No concentration; expected low TV_W |
| Zero-inflated | π=0.90 zeros + LogN(μ=0, σ=1) for the remainder | Replicates perm's extreme structure (350/389 zeros) |

30 replicates per family (independent random seeds for column generation).
Total: 4 families × 30 replicates = 120 base instances.

Rationale for zero-inflated family: the three continuous families lack the
point mass at zero that produced the extreme amplitude ρ_perm = 0.583 in Fogo
(main criterion of the study). Without this family, the grid cannot reach
TV_W values comparable to the published instance.

### 2.3 Factors

| Factor | Levels | Notation |
|---|---|---|
| TV_W target | {0, 0.10, 0.199, 0.30} | tw |
| TV_B target | {0, 0.249} | tb |
| Direction | {inflate, deflate} for j* = argmax_{j∈G_g} w_j in each group | dir |

### 2.4 Seven cells per instance

| Cell | TV_B | TV_W | Direction | Purpose |
|---|---|---|---|---|
| M | 0 | 0 | — | P1 assertion |
| B | 0.249 | 0 | — | P1 assertion |
| W_inf(L) | 0 | 0.10 | inflate | P2 (low level) |
| W_inf(F) | 0 | 0.199 | inflate | P2 (Fogo level), P3, P4 |
| W_inf(H) | 0 | 0.30 | inflate | P2 (high level) |
| V_inf(F) | 0.249 | 0.199 | inflate | P3 (TV_B amplification) |
| W_def(F) | 0 | 0.199 | deflate | P4 (direction) |

### 2.5 TV_W definition (§6.4 of the manuscript)

TV_W = sum_g W_g * TV_{W,g}
TV_{W,g} = 0.5 * sum_{j in G_g} |w_j^eff / W_g^eff - w_j / W_g|

where w_j^eff = w_j * A_j / (sum_k w_k * A_k).

The target tw must be achieved under this definition, not under a simpler
approximation. s_W (scale factor for the deviation from 1) is calibrated by
bisection per instance.

### 2.6 Amplitude construction

Groups (from fogo_constants.py, same as E1):
  G1 = [perm, slope, roads]          indices [0,1,2]   W_G1 = 0.295
  G2 = [rivers, aspect, coast, prot, wells] indices [3..7] W_G2 = 0.356
  G3 = [urban, aero, cult]           indices [8,9,10]  W_G3 = 0.349

In each group G_g, identify j* = argmax_{j in G_g} w_j (highest-weight criterion).

**Inflate (W_inf and V_inf cells)**:
  A_{j*} = 1 + delta_g       (delta_g > 0, calibrated so TV_W = tw)
  A_{j≠j*} = 1

**Deflate (W_def cell)**:
  A_{j*} = 1 - delta_g       (same delta_g as inflate; same TV_W)
  A_{j≠j*} = 1

Constraints:
  - A_j > 0 for all j (check before run; deflate may fail at tw=H for some families)
  - A_{j*} ≤ 3 for inflate (avoid extreme amplifications)
  - If constraints fail for a particular (instance, cell, tw): declare as DEV before run

**Between-group cell B** (TV_W = 0, TV_B = 0.249):
  A_j = Abar_g for all j in G_g
  where Abar_g are scaled per group so TV_B = 0.249 under the §6.4 formula.
  (Abar_g constant within group ⟹ TV_W = 0 exactly, Theorem 1 applies.)

**Score** (all cells except M):
  score(a) = sum_j w_j * A_j * n_j^mm(a)

**Objectives** (all cells, fixed throughout):
  F_g(a) = sum_{j in G_g} w_j * n_j^mm(a)     (no A_j factor)

This is the critical difference from E5: objectives are not distorted by A_j.

### 2.7 Parameters

N_draws = 200 per cell (±3.5 pp Monte Carlo SE at Q2=50%)
κ = 200 (Dirichlet concentration, same as main factorial)
seed = 42 (+ instance index for column generation)
k = 3 (portfolio size)
Spatial structure: fogo_trios.npy (1,944,653 feasible trios)

### 2.8 Scope declaration

E6 tests OPTIMAL assembly only.

Greedy assembly is not reported: synthetic columns are drawn independently
(no spatial autocorrelation), confounding the foreclosure effect with the
spatial structure of the instance. Greedy results from synthetic instances
are therefore not comparable with Fogo's greedy results. This is declared
before any run; greedy output may be saved but will not be reported in the
manuscript.

## 3. Pre-declared predictions

### P1 — Theorem 1 assertion (hard test, not a hypothesis)

For ALL 120 instances × ALL families, cells M and B (TV_W = 0):
  Q2_optimal = 100% on every draw.

P1 is an assertion, not a hypothesis. Failure on any instance indicates a bug
in the amplitude construction (A_j not affine within groups) or in the objective
computation (objectives not in min-max). P1 is verified before computing P2–P4.

### P2 — Monotonicity of Q2_opt in TV_W (primary empirical prediction)

For each instance × family, Q2_opt in the W_inf cells is monotone
non-increasing in tw:
  Q2_opt(tw=0) ≥ Q2_opt(tw=L) ≥ Q2_opt(tw=F) ≥ Q2_opt(tw=H).

**Confirmatory criteria (both required)**:
(a) Spearman ρ_s(TV_W, Q2_opt) < 0 in ≥ 80% of instances per family.
    [Note: ρ_s < 0 because Q2 decreases when TV_W increases.]
(b) Mean(Q2_opt(tw=H)) < Mean(Q2_opt(tw=0)) − 5 pp.

**Falsification**: ρ_s ≥ 0 in > 20% of instances within any family.

Rationale: if TV_W governs optimal-assembly efficiency loss (the main empirical
claim of the paper), then the relationship must be monotone beyond Fogo. Confirmed
on 120 instances across 4 distribution families, it extends the claim from "on
this instance" to "on Fogo and across [N] synthetic instances."

### P3 — Between-group amplification (replicates E1)

For each instance × family, at fixed TV_W = 0.199:
  Q2_opt(V_inf) ≤ Q2_opt(W_inf).

**Confirmatory criterion**: Q2_opt(V_inf) < Q2_opt(W_inf) in ≥ 70% of instances.

**Falsification**: Q2_opt(V_inf) > Q2_opt(W_inf) + 5 pp in > 30% of instances.

Rationale: E1 found W=64.2% vs V=56.8% (TV_B added 7.4 pp of loss). P3 tests
whether this amplification replicates in synthetic instances. P3 does NOT predict
that TV_B has no effect — it predicts that TV_B adds to the loss (consistent with
E1). A reversal (TV_B reduces loss) would be a new result and must be investigated.

### P4 — Direction of within-group distortion (tests Remark rem:TVW)

For each instance × family, at TV_W = 0.199 and TV_B = 0:
  Q2_opt(W_inf) < Q2_opt(W_def).

**Confirmatory criterion**: Q2_opt(W_inf) < Q2_opt(W_def) in ≥ 70% of instances.

**Falsification**: Q2_opt(W_inf) > Q2_opt(W_def) in > 30% of instances.

Rationale: Remark rem:TVW (manuscript) states that TV_W > 0 is not sufficient for
efficiency loss without further conditions. P4 tests whether the direction of
distortion on the highest-weight criterion within each group matters at fixed TV_W.
There is no analytic prediction for P4; it is declared prospectively and is
exploratory in the sense of Nosek et al. (2018) (registered exploratory).

## 4. What P2–P4 do not claim

P2–P4 are empirical. None follows from Theorem 1.

The theorem is existential: it guarantees Q2_opt = 100% when TV_W = 0, for any
instance and any coupling constraint. It does not imply:
  - that Q2_opt is monotone in TV_W for TV_W > 0;
  - that TV_B amplifies the within-group loss;
  - that direction matters at fixed TV_W.

If P2–P4 are confirmed, the manuscript should read "on Fogo and across [N]
synthetic instances with four marginal families," not "in general." The qualifier
"on this instance" is removed only for the specific claims supported by P2–P4.

## 5. Falsification criteria and consequences

| Prediction | Falsified if | Consequence |
|---|---|---|
| P1 | Q2_opt < 100% on any M or B cell | Bug — abort, diagnose |
| P2(a) | ρ_s ≥ 0 in > 20% of instances in any family | TV_W not a consistent predictor; keep "on this instance" |
| P2(b) | Mean(H) ≥ Mean(0) − 5 pp | Effect too small to report as consistent finding |
| P3 | V_inf > W_inf + 5 pp in > 30% of instances | TV_B reduces loss in some distributions; report as new result |
| P4 | W_inf > W_def in > 30% of instances | Direction does not matter; Remark rem:TVW remains unresolved |

## 6. Connection to manuscript structure

If P1 confirmed (expected):
  - Confirm Theorem 1 holds on synthetic instances; include in §7.

If P1 + P2 confirmed:
  - Change "on this instance" to "on Fogo and across [N] synthetic instances"
    for claims about TV_W governing optimal-assembly loss.
  - Add Figure: Q2_opt vs TV_W by family (4 panels).

If P1 + P2 + P3 confirmed:
  - "The between-group amplification from E1 replicates across synthetic families."
  - Adds credibility to the §7.5 interaction result.

If P1 + P2 + P4 confirmed:
  - Partially resolves Remark rem:TVW: direction matters.
  - Add to §7 or Discussion.

## 7. Deviations from this PRESPEC

Any deviation must be logged in corpus/DEVIATIONS.md with DEV-E6-NNN identifier,
date, and justification. Expected deviations:

| Expected DEV | Description |
|---|---|
| DEV-E6-001 | Deflate constraint (A_{j*} > 0) fails for some cells at tw=H |
| DEV-E6-002 | Inflate constraint (A_{j*} ≤ 3) fails for zero-inflated family |
| DEV-E6-003 | Timing exceeds estimate; N_draws reduced from 200 to 100 |

## 8. Output

```
results/e6/e6_instances.csv
  columns: family, replicate, cell, Q2_optimal, SE, TV_W_actual, TV_B_actual

results/e6/e6_summary.csv
  by (family, cell): mean_Q2_opt, sd_Q2_opt, fraction_confirming_P2, fraction_confirming_P3, fraction_confirming_P4

results/e6/e6_p2_spearman.csv
  by (family, replicate): rho_s, p_value
```

Figures:
  fig_e6a: Q2_opt vs tw level, 4 panels (one per family); y=100 dashed line (P1/P2)
  fig_e6b: Q2_opt(W_inf) vs Q2_opt(W_def) scatter, one point per instance (P4)

## 9. Computation

Scripts:
  scripts/e6_generate_amplitudes.py — constructs A_j vectors for all 7 cells
  scripts/run_e6.py — runs 7 cells × N_draws × 120 instances

Run on: Athena (~/scratch/mcdm-landfill-pareto)
Timing: verify with 1 instance × 7 cells × 200 draws BEFORE submitting full job.
Expected total: ~4h (to verify; 120 × 7 × 200 = 168,000 draw-cell evaluations).
Output: results/e6/

Commit this file before launching any E6 run. The commit hash is the timestamp
of the pre-registration.
