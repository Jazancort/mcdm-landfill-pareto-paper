# DEV-SANT-W0-001 — S-N weight vector w₀ numerical verification
Date: 2026-10-28 (written after Stage 4 GPU run completed; see §Timing note below)
Type: post-run numerical verification (no prediction involved)

## Timing note

This DEV was written on 2026-10-28 AFTER the Stage 4 GPU run was sealed
(stage4-results-sealed tag, 2026-10-28T12:42Z). The question of whether the
S-N weights match PRESPEC §5.6 (Cabral 2012 Annex C) was raised in a pre-launch
review but the DEV was not published before the run. This file therefore does NOT
constitute a pre-data declaration. It is a post-run numerical audit.

The w₀ question does not involve a prediction: it is a reproducibility check on
whether the code uses the correct input weights. The S-N predictions (K1-K6) are
not affected by which party declared the check before or after the run.

## PRESPEC declaration

PRESPEC_SANTIAGO §5.6: "Cabral (2012) AHP leaf weights (Annex C)." No numerical
values are listed in the PRESPEC; the source is declared, not the values themselves.
Under C-4 (ZDTI omitted), the 14 Cabral weights are renormalized over 13 criteria
(see DEV-SANT-ZDTI-001).

## S-N code weights (W0_SN in run_santiago_mc.py)

The code constant W0_SN (before /sum normalization) has 13 values:

| Criterion | Code value (4 d.p.) | Cabral rounded (Tab.14/16) | w_j_Cabral / 0.9637 |
|---|---|---|---|
| A1 | 0.0397 | 0.0383 | 0.0397 |
| A3 | 0.0270 | 0.0260 | 0.0270 |
| A4 | 0.0397 | 0.0383 | 0.0397 |
| A5 | 0.0163 | 0.0157 | 0.0163 |
| A6 | 0.0324 | 0.0313 | 0.0325 (*) |
| A7 | 0.0270 | 0.0260 | 0.0270 |
| B1 | 0.2096 | 0.2020 | 0.2096 |
| B2 | 0.1048 | 0.1010 | 0.1048 |
| B3 | 0.1048 | 0.1010 | 0.1048 |
| C1 | 0.0759 | 0.0731 | 0.0759 |
| C2 | 0.0253 | 0.0244 | 0.0253 |
| D1 | 0.0981 | 0.0945 | 0.0981 |
| D2 | 0.1993 | 0.1921 | 0.1993 |

Denominator: 14 Cabral rounded weights sum to 1.0020, so denominator = 1.0020 − 0.0383 = 0.9637.
(*) A6 exception: 0.0313/0.9637 = 0.0325 (renormalized expected), code has 0.0324.
Difference = 0.0001 on renormalized weights (sum=1). This is within the bound below (§Threshold).

Code sum before /= sum: 0.9999 (verified: np.float64 repr). After W0_SN/W0_SN.sum(): 1.0.
Patterns consistent with Cabral AHP hierarchy: B1=2·B2=2·B3 (verified), A1=A4 (verified).

**Note:** An earlier version of this DEV claimed the A6 discrepancy indicates the code used
higher-precision ("unrounded") Cabral source values. That claim is not supported: the code
sum is 0.9999, consistent with 4-decimal-place input. The A6 difference may reflect rounding
of the source values during manual transcription, not a difference in precision. The claim is
retracted. The pending PDF verification (§Conclusion) remains the correct resolution path.

## Threshold (fixed before PDF verification — 2026-11-02)

The acceptability threshold for weight discrepancies is:

  **|w_code - w_renorm| ≤ 0.001** (absolute, on renormalized weights summing to 1)

Basis: Dirichlet SD at κ=25 for a weight of 0.03 is ~0.034 (much larger).
The threshold 0.001 is 34× below the sampling noise at the most concentrated κ,
and 170× below the sampling noise at the least concentrated κ=25.
Any difference below 0.001 is operationally indistinguishable from noise.

Current maximum: A6, difference = 0.0001. This is within the ≤ 0.001 bound.

**Activation rule for W0-001:** if the PDF verification finds any criterion with
|w_Cabral_renorm - w_code| > 0.001 (on sum-1 renormalized weights), the S-N branch
must be re-run with the corrected w0 before reporting predictions.

## S-T code weights (W0_ST in run_santiago_mc.py)

W0_ST derives from the 10-criterion Fogo AHP (published in main paper Tab. 1)
after removing wells (C-2) and renormalizing. Verified:

All 10 values match `Tab1_11crit.remove(wells).renorm()` to within |diff| < 5e-7.
Confirmed by numeric test on 2026-10-28 (verify_gpu.py, Athena).

## Conclusion

The S-N code weights match the Cabral rounded values renormalized by 0.9637 for 12 of 13
criteria, and for A6 the difference (0.0001) is within the 0.001 threshold fixed above.
The comparison above is against our own transcription (the DEV table), not the published
Cabral (2012) table: this is acknowledged. Independent verification is pending.

The weights cannot be independently verified against the published Cabral (2012) table
until the dissertation PDF is obtained (hdl.handle.net/10362/8627). The numerical
patterns (B1=2·B2=2·B3, A1=A4) are consistent with the declared Cabral AHP source.
All S-N verdicts are provisional until that verification is complete (W0-001 rule above).
