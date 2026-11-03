# DEV-SANT-KINF-001 — κ=∞ run with 1 draw instead of 500
Date: 2026-10-29
Type: pre-data clarification (no Q2 value computed before this record)

## PRESPEC declaration (A5 §1)

PRESPEC_SANTIAGO_A5 §1 declares: "Draws: 500 per κ" including κ=∞.

## What changed

`scripts/run_santiago_mc.py` implements `n_draws_actual = 1 if kappa == "inf" else n_draws`.
For the full Stage 4 run (n_draws=500), κ=∞ uses 1 draw instead of 500.

## Justification

κ=∞ is the deterministic case: w = w₀ (the declared AHP weights, no randomness).
All 500 "draws" would be identical because the weights do not change. Running 500
copies of the same computation:
1. Does not add any statistical information (the result is a single number, not a
   distribution).
2. The 95% CI from 500 identical draws would be [value, value] (width = 0).
3. For K5 (sign check at κ=∞), the 1-draw result is the only unique result;
   repeating it 500 times changes nothing.
4. For K2 (E1-B optimal Q2 = 100% at κ=∞), 1 check is sufficient.

Running 1 draw saves ~160 minutes of Athena CPU time on the S-T branch.

## Pre-registration status

This is a clarification, not an amendment. The PRESPEC declared 500 draws because
the general notation applied to all κ without considering the deterministic case.
The intention of "500 draws" is to generate a distribution over weight uncertainty;
for κ=∞, there is no weight uncertainty. Running 1 draw is the only meaningful
interpretation of a deterministic point.

No criterion value, score, frontier, or Q2 has been computed for Santiago before
this clarification was written.

## Impact on predictions

K1, K2, K3, K4 only involve stochastic κ (except K2 which includes κ=∞).
For K2 at κ=∞: one check is sufficient (deterministic, no CI needed).
For K5: only sign direction at κ=∞; 1 draw gives the sign.
For K6: SAW–TOPSIS contrast at κ=∞; 1 draw gives the deterministic contrast.

No bootstrap CI is computed for κ=∞ (would be degenerate).
Results at κ=∞ are reported as a single descriptive value (no CI, no p-value).
