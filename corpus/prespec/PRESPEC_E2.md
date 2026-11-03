# PRESPEC_E2.md — Pre-Specification for Experiment E2
# "TV_W^eff as predictor of optimal-assembly efficiency loss"
#
# WRITTEN BEFORE RUNNING. This commit precedes any E2 execution.
# Date: 2026-10-01
# Author: J. Azancort Neto
#
# Purpose: test whether the within-group weighted distortion under effective
# weights (TV_W^eff) predicts optimal-assembly Q2 loss across synthetic instances
# that vary independently in between-group distortion (s_B) and within-group
# distortion (s_W).
#
# E1 results that motivate this hypothesis (commit DEV-E1-004, 18e7a66):
#   E1-B optimal = 100.0%  (TV_B alone: no loss)
#   E1-W optimal = 64.2%   (TV_W alone: 35.8pp loss)
#   E1-V optimal = 56.8%   (TV_B + TV_W: 43.2pp loss)
#   Bootstrap E1-W vs E1-V: diff = +7.40pp, CI = [+3.80, +11.00]pp, p < 0.001
#   Interpretation: TV_B alone does not cause loss; it interacts with TV_W
#   to amplify it by 7.4pp. The interaction has a precise mechanism (see §2).

## 1. Theoretical basis

### 1.1 TV_W^eff — definition

Let Ā_g = Σ_{j∈g} w_j ρ_j / W_g be the weighted-mean amplitude of group g,
and let W_g^eff = W_g · Ā_g / Ā_global be the effective group weight (proportional
to amplitude × nominal weight). Define:

  TV_W^eff = Σ_g W_g^eff · TV_W,g

where TV_W,g = (1/2) Σ_{j∈g} w_j/W_g · |ρ_j - Ā_g| / Ā_g is the within-group
distortion of group g.

### 1.2 Motivation from E1

For the three E1 cells:

| Cell | TV_W^eff | Optimal loss |
|------|:--------:|:------------:|
| E1-B | 0.0000   | 0.0pp        |
| E1-W | 0.1987   | 35.8pp       |
| E1-V | 0.2335   | 43.2pp       |

Ratio TV_W^eff (E1-V / E1-W) = 1.175.
Ratio loss (E1-V / E1-W) = 43.2 / 35.8 = 1.207.

The two ratios are within 3% of each other — consistent with TV_W^eff being
the operative predictor and explaining the interaction (TV_B inflates W_g^eff
for the high-amplitude group G1, increasing TV_W^eff).

### 1.3 Hypothesis (pre-declared)

In optimal assembly, the Q2 loss (fraction not on the Pareto frontier) is
monotone increasing in TV_W^eff and approximately zero when TV_W^eff = 0.

Formally: E[1 - Q2_optimal] ≈ f(TV_W^eff) for some monotone f, with f(0) = 0.

Stronger form (the one that would bring the article to ~9):
  E[1 - Q2_optimal] ≈ β · TV_W^eff + ε
  i.e., the relationship is approximately linear over the tested range.

### 1.4 Null hypothesis (falsification criterion)

H0: TV_W^eff has no predictive power beyond TV_W alone.
Falsified if: the regression of loss on TV_W^eff has R² > R²(TV_W alone) + 0.10.

### 1.5 Relationship to the article structure

If the hypothesis is confirmed:
  - The article gains a pre-registered empirical law: loss ≈ β · TV_W^eff.
  - TV_W^eff explains why TV (total) orders the loss poorly.
  - The synthetic grid becomes the central evidence table.
  - The article restructures around: theorem (E1-B) + empirical law (grid E2).

If the hypothesis is not confirmed:
  - Report as negative: TV_W^eff does not simplify the prediction.
  - The article retains its current structure (TV as descriptive metric).

## 2. The mechanism that motivates TV_W^eff

When between-group distortion (TV_B > 0) is present, the effective group weight
W_g^eff differs from the nominal weight W_g. Specifically:

  W_g^eff = W_g · Ā_g / Ā_global

where Ā_g is the within-group mean amplitude and Ā_global is the global mean.
If group G1 has higher amplitude (Ā_G1 > Ā_global), W_G1^eff > W_G1.

This means that within-group distortion TV_W,G1 is applied with a larger
effective weight — amplifying the total within-group distortion. That is the
mechanism behind the 7.4pp interaction in E1.

TV_W^eff = Σ_g W_g^eff · TV_W,g captures this amplification by construction.

## 3. Experimental design

### 3.1 Instance generation

Synthetic instances varying amplitude structure over a 2D grid (s_B, s_W):

  s_B ∈ {0.0, 0.1, 0.2, 0.3, 0.4}   — controls between-group distortion
  s_W ∈ {0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7}  — controls within-group distortion

Total: 5 × 8 = 40 (s_B, s_W) combinations × 6 random amplitude instantiations
= 240 instances.

For each (s_B, s_W, replicate):
  - Generate 11 amplitudes Ā_j with TV_B ≈ s_B and TV_W ≈ s_W
  - Keep the Fogo dataset (389 sites, 1,944,653 trios) fixed
  - Score: SAW with the generated amplitudes (same as E1 cells)
  - N_DRAWS = 500, κ = 200, seed = 42, same as WP3

### 3.2 Outcomes

For each instance, compute:
  - Q2_optimal: fraction of draws where optimal selection is on the frontier
  - Q2_greedy: fraction where greedy selection is on the frontier
  - TV_B, TV_W (for groups G1/G2/G3 separately)
  - TV_W^eff = Σ_g W_g^eff · TV_W,g (requires knowing Ā_g for each instance)
  - TV_total = TV_B + TV_W (for comparison)

### 3.3 Models to fit (pre-specified, do not select after seeing data)

All models are OLS on Q2_loss_optimal = 1 - Q2_optimal:

  M1: loss ~ TV_total                    (baseline, current article)
  M2: loss ~ TV_W                        (within-group only)
  M3: loss ~ TV_W^eff                    (pre-registered hypothesis)
  M4: loss ~ TV_W + TV_B                 (additive decomposition)
  M5: loss ~ TV_W^eff + I(TV_B > 0)     (threshold interaction)

Report R² for all five. Primary comparison: M3 vs M1 (TV_W^eff vs TV_total).

### 3.4 Pre-declared predictions

P_E2_1 (Primary): R²(M3) > R²(M1) + 0.10
  Rationale: TV_W^eff incorporates the interaction that TV_total misses.

P_E2_2 (Secondary): The M3 intercept is approximately zero.
  Rationale: when TV_W^eff = 0 (i.e., TV_W = 0 for all groups), loss = 0.
  Falsification: if intercept > 5pp with p < 0.05.

P_E2_3 (Secondary): The E1 cells lie on the M3 regression line (residual < 5pp).
  Rationale: E1 used the Fogo instance — the model should be consistent.

## 4. Connection to E1 results

The E1 results already support TV_W^eff as the operative predictor.
The grid E2 tests whether this generalises across amplitude configurations.
If it does, the article can claim:

  "The efficiency loss of optimal assembly equals approximately β · TV_W^eff,
   where TV_W^eff is the within-group distortion weighted by effective group weights.
   This was pre-specified (PRESPEC_E2.md, commit [HASH]) and confirmed across
   240 synthetic instances of the Fogo Island dataset."

## 5. Computation

Script: scripts/wp4_synthetic_fixed.py (to be written after this PRESPEC commit)
Run on: Athena (~/scratch/mcdm-landfill-pareto)
Expected time: ~4 hours (240 instances × 500 draws × greedy+optimal)

Output: results/e2_grid_results.csv
Columns: s_B, s_W, replicate, Q2_optimal, Q2_greedy, TV_B, TV_W, TV_W_eff, TV_total

## 6. Falsification criteria

| Prediction | Falsified if | Consequence |
|------------|--------------|-------------|
| P_E2_1 | R²(M3) < R²(M1) + 0.10 | TV_W^eff adds no predictive value; retain current article structure |
| P_E2_2 | Intercept > 5pp (p<0.05) | Loss exists even with TV_W^eff=0; mechanism is incomplete |
| P_E2_3 | |residual_E1| > 5pp for any E1 cell | Fogo instance is atypical; generalisation fails |

## 7. Note on PRESPEC_E1 error

PRESPEC_E1.md (commit f6042f8) mentions "1940 sites". The correct count is
473 candidate sites and 389 admissible sites (protected > 0). This typographic
error does not affect the experiment design or results. To be corrected in a
DEV entry (this file serves as the correction record).
