# PRESPEC_E3.md — Pre-Specification for Experiment E3
# "Dose-response of optimal-assembly loss under the power-law amplitude model"
#
# WRITTEN BEFORE RUNNING. This commit must precede any E3 execution.
# Author: J. Azancort Neto
#
# Context: E2 used a stochastic generator (linear interpolation + uniform
# perturbations) that differs from the power-law formula discussed in the
# E2 motivating text. E3 uses the deterministic power-law generator, which:
#   (a) is fully reproducible (no random amplitude seed needed),
#   (b) has four corners that recover E1 cells exactly (regression tests),
#   (c) reaches TV_W^eff ≈ 0.23, covering the Fogo regime.
#
# Known falsified predictions at the time of writing this PRESPEC:
#   P2 of E1: |E1-W − E1-V| < 5pp in optimal. FALSIFIED (7.4pp, CI=[+3.80,+11.00]).
#   P3 of E2: |residual_E1| < 5pp for E1-W and E1-V. FALSIFIED (+9.6pp and +12.2pp).
#   The E2 grid (stochastic generator, TV_W^eff ≤ 0.068) does not cover the
#   Fogo regime and is moved to Supplementary Material.

## 1. Theoretical basis

### 1.1 Power-law generator

For each (s_B, s_W) cell, the amplitude of criterion j in group g is:

  A_j = Ā_g(s_B)^{1 - s_W} · ρ_j^{s_W}

where:
  ρ_j  = actual Fogo amplitude of criterion j (range of unnormalised column j)
  Ā_g(s_B) = global_mean + s_B · (Ā_g^{Fogo} - global_mean)
            = (1-s_B)·global_mean + s_B·Ā_g^{Fogo}

This is equivalent to A_j = Ā_g(s_B) · (ρ_j/Ā_g^{Fogo})^{s_W} · (correction)
where the correction renormalises to preserve Σ_g W_g·Ā_g = global_mean.

More precisely:
  step 1: compute Ā_g(s_B) by linear interpolation in group means
  step 2: within each group, set A_j ∝ Ā_g(s_B) · (ρ_j/Ā_g^{Fogo})^{s_W}
  step 3: renormalise within each group so Σ_{j∈g} w_j/W_g · A_j = Ā_g(s_B)

The generator is DETERMINISTIC: no random seed, no replicate dimension.

### 1.2 Corner recovery (regression assertions)

The four corners of the 5×5 grid recover the four E1 cells exactly:

  (s_B=0, s_W=0): A_j = global_mean for all j → E1-M (all amplitudes equal)
  (s_B=1, s_W=0): A_j = Ā_g^{Fogo} for all j in group g → E1-B (within-group flat)
  (s_B=0, s_W=1): A_j = ρ_j · (global_mean/Ā_g^{Fogo}) → E1-W (TV_B=0, within-group = Fogo)
  (s_B=1, s_W=1): A_j = ρ_j → E1-V (actual Fogo amplitudes)

ASSERTION: TV_W^eff at (0,1) must equal TV_W^eff(E1-W) = 0.1987 ± 1e-6.
ASSERTION: Q2_optimal at (0,0) must equal 100.0% (all 1000 draws).
ASSERTION: Q2_optimal at (1,0) must equal 100.0% (all 1000 draws).
ASSERTION: Q2_optimal at (0,1) must equal E1-W optimal = 64.2% ± 2pp (sampling).
ASSERTION: Q2_optimal at (1,1) must equal E1-V optimal = 56.8% ± 2pp (sampling).

### 1.3 TV_W^eff values at key grid points (pre-computed, verified)

From the power-law generator with Fogo data:
  (s_B=0, s_W=0):   TV_W^eff = 0.000
  (s_B=0, s_W=0.25): TV_W^eff ≈ 0.050 (to be confirmed by script assertion)
  (s_B=0, s_W=0.5):  TV_W^eff ≈ 0.100 (to be confirmed)
  (s_B=0, s_W=0.75): TV_W^eff ≈ 0.150 (to be confirmed)
  (s_B=0, s_W=1.0):  TV_W^eff = 0.1987 (= E1-W, assertion)
  (s_B=1, s_W=1.0):  TV_W^eff = 0.2335 (= E1-V, assertion)

The grid covers TV_W^eff ∈ [0, 0.234] by construction, spanning the full Fogo regime.

## 2. Experimental design

### 2.1 Grid

  s_B ∈ {0.0, 0.25, 0.5, 0.75, 1.0}   — 5 levels
  s_W ∈ {0.0, 0.25, 0.5, 0.75, 1.0}   — 5 levels

Total: 5 × 5 = 25 cells. NO random replicates (generator is deterministic).

For each (s_B, s_W):
  - Compute A_j via power-law generator (deterministic, no seed needed)
  - Keep the Fogo dataset (389 sites, 1,944,653 trios) fixed
  - Score: SAW/min-max with the generated amplitudes
  - N_DRAWS = 1000, κ = 200, seed = 42

### 2.2 Outcomes

For each cell, compute:
  - Q2_optimal, Q2_greedy (fraction of draws on the Pareto frontier)
  - TV_W^eff, TV_W (per-group and total), TV_B, TV_total
  - loss_optimal = 100 - Q2_optimal

### 2.3 Models to fit (pre-specified)

Unit of analysis: 25 cells (the only unit; no replicate dimension).

  M1: loss_optimal ~ TV_total
  M2: loss_optimal ~ TV_W     (= Σ_g W_g · TV_W,g)
  M3: loss_optimal ~ TV_W^eff (pre-registered hypothesis)
  M4: loss_optimal ~ TV_W + TV_B
  M5: loss_optimal ~ TV_W^eff + I(TV_B > 0)

## 3. Pre-declared predictions

### P_E3_1 (Primary): TV_W^eff ranks loss better than TV_W
R²(M3) > R²(M2) + 0.05 on the 20 cells with s_W > 0.
Rationale: when s_B > 0, W_g^eff ≠ W_g, and TV_W^eff captures the amplification
that TV_W misses. This is the test that E2 could not perform (TV_B ≤ 0.10 in E2
kept W_g^eff ≈ W_g, making M2 ≈ M3).

Falsification: if R²(M3) ≤ R²(M2) + 0.05 on 20-cell subset.

### P_E3_2 (Primary): Monotonicity within each s_B slice
For each fixed s_B, the sequence Q2_optimal(s_B, 0), Q2_optimal(s_B, 0.25), ...,
Q2_optimal(s_B, 1.0) is non-increasing (Spearman ρ > 0 between s_W and loss).
Tested per-row for each of the 5 s_B values.
Falsified if Spearman ρ ≤ 0 for any s_B row.

### P_E3_3 (Primary): Interaction — fixed s_W, loss grows with s_B
For each s_W > 0, loss_optimal is non-decreasing in s_B (Spearman ρ > 0 per column).
This is the direct test of the interaction that motivated TV_W^eff.
Falsified if Spearman ρ ≤ 0 in at least 2 of the 4 columns (s_W ∈ {0.25,0.50,0.75,1.0}).

### P_E3_4 (Secondary): Zero loss when TV_W^eff = 0
All cells with s_W = 0 have Q2_optimal = 100.0% (Proposition 1).
Hard assertion — not statistical. Falsified if any cell with s_W=0 gives < 100%.

### P_E3_5 (Secondary): R²(M3) > 0.80 on 20-cell subset (s_W > 0)
If the relationship is approximately linear over the full range [0, 0.234],
R²(M3) should be high. Falsified if R²(M3) < 0.80 (indicating non-linearity).

## 4. Connection to prior experiments

E1 provides the four corners with exact known values.
E2 (Supplementary) tested a different generator over a smaller range.
E3 is the pre-registered test of the power-law relationship over the full Fogo regime.

The falsification chain:
  - P2 of E1 (falsified): TV_B interacts with TV_W — the 7.4pp amplification is established.
  - P_E3_3: tests whether this interaction is monotone in s_B — the dose-response of interaction.
  - P_E3_1: tests whether TV_W^eff captures the amplification better than TV_W.

If P_E3_1 and P_E3_3 are confirmed, the article can claim:
  "The efficiency loss is a monotone increasing function of TV_W^eff,
   which incorporates the amplification of within-group distortion by between-group
   differences in effective group weights. This was pre-registered (PRESPEC_E3.md,
   commit [HASH]) and confirmed across 25 deterministic instances spanning the
   full amplitude range of the Fogo dataset."

## 5. Computation

Script: scripts/run_e3_grid.py (to be written after this PRESPEC commit)
Run on: Athena (~/scratch/mcdm-landfill-pareto)
Expected time: ~25 × time(E1 one cell) ≈ 25 × ~10min ≈ 4 hours
Pipeline: pareto_utils.py (float64, eps=1e-9, sorted-idx, self-exclusion)

Output: results/e3_grid_results.csv
Columns: s_B, s_W, Q2_optimal, Q2_greedy, TV_B, TV_W_G1, TV_W_G2, TV_W_G3,
         TV_W_eff, TV_W_total, TV_total, Ajbar_G1, Ajbar_G2, Ajbar_G3

## 6. Falsification criteria summary

| Prediction | Falsified if | Consequence |
|---|---|---|
| P_E3_1 | R²(M3) ≤ R²(M2)+0.05 (20 cells s_W>0) | TV_W^eff offers no advantage over TV_W in full range |
| P_E3_2 | Spearman ρ(s_W, loss) ≤ 0 for any s_B | Loss not monotone; TV_W^eff not a valid predictor |
| P_E3_3 | Spearman ρ(s_B, loss) ≤ 0 in ≥2 of 4 columns | TV_B does not amplify loss; interaction mechanism fails |
| P_E3_4 | Any cell with s_W=0 has Q2_optimal < 100% | Pipeline bug or Proposition 1 violated |
| P_E3_5 | R²(M3) < 0.80 (20 cells s_W>0) | Non-linear relationship; linear law not supported |

## 7. Notes

### Relationship to E2
E2 (Supplementary) used stochastic generator (DEV-E2-005). P_E2_3 was falsified
(E1 cells had residuals 9-12pp above M3 line), confirming that the E2 grid did
not cover the Fogo regime. E3 addresses this by design.

### Relationship to E1
E3 is the "filling-in" of the 2D space of which E1 provided the four corners.
The four corner assertions are regression tests: if they fail, the generator is wrong.

### No random replicates
The power-law generator is deterministic. Variability comes only from the N_DRAWS=1000
Monte Carlo draws over w. With N=1000 per cell, the Monte Carlo error on Q2 is
≤ 1.6pp (2σ for binomial with p=0.5). This is smaller than any prediction margin.
