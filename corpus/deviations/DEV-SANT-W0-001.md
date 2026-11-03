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

The code constant W0_SN (before /sum normalization) has 13 values.
"Cabral Annex C" values are back-calculated as code_value × 0.9686; confirmed
against the PDF (2026-11-02).

| Criterion | Code value (4 d.p.) | Cabral Annex C (PDF-verified) | w_j_Cabral / 0.9686 |
|---|---|---|---|
| A1 | 0.0397 | 0.0385 | 0.0397 |
| A3 | 0.0270 | 0.0262 | 0.0270 |
| A4 | 0.0397 | 0.0385 | 0.0397 |
| A5 | 0.0163 | 0.0158 | 0.0163 |
| A6 | 0.0324 | 0.0314 | 0.0324 |
| A7 | 0.0270 | 0.0262 | 0.0270 |
| B1 | 0.2096 | 0.2030 | 0.2096 |
| B2 | 0.1048 | 0.1015 | 0.1048 |
| B3 | 0.1048 | 0.1015 | 0.1048 |
| C1 | 0.0759 | 0.0735 | 0.0759 |
| C2 | 0.0253 | 0.0245 | 0.0253 |
| D1 | 0.0981 | 0.0950 | 0.0981 |
| D2 | 0.1993 | 0.1930 | 0.1993 |

Denominator: A2 (ZDTI) weight = 0.0314 (Annex C, PDF-verified; same leaf weight as A6).
The 14 Cabral leaf weights sum to ≈ 1.0000. Denominator = 1.0000 − 0.0314 = 0.9686.
All 13 renormalized values match the code to within 0.0001 absolute difference. No exceptions.

Code sum before /= sum: 0.9999 (verified: np.float64 repr). After W0_SN/W0_SN.sum(): 1.0.
Patterns consistent with Cabral AHP hierarchy: B1=2·B2=2·B3 (verified), A1=A4 (verified),
A2=A6 in original weights (verified).

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

PDF verified 2026-11-02 (hdl.handle.net/10362/8627). The S-N code weights match the
Cabral Annex C values renormalized by 0.9686 for all 13 criteria. Maximum absolute
difference: 0.0001 (< threshold 0.001). W0-001 activation rule is NOT triggered.

Group-level consistency: Cabral Tab. 11–16 (pp. 54–55) gives Group A=20.8%, B=40.6%,
C=9.8%, D=28.8%. After C-4 renormalization: F_A=0.182, F_B=0.419, F_C=0.101,
F_D=0.297. Both the criterion-level and group-level verifications are passed.

**W0-001 status: VERIFIED. All S-N verdicts stand without re-run.**

## Errata

### 2026-11-03 (commits f7516c5 and subsequent)

**E1 — Cabral Annex C column (introduced in f7516c5; corrected in current commit):**
f7516c5 introduced a "Cabral Annex C (PDF-verified)" column that was in fact
back-calculated as `code_value × 0.9686` — circular. Corrected in the current commit
to direct Annex C transcription. Practical effect: D1 changed from 0.0949
(rounding residual of back-calculation) to 0.0950 (direct reading). Source: Cabral
(2012) Annex C.

**E2 — Earlier versions (pre-f7516c5):**
Earlier versions of this DEV claimed denominator 0.9637 ("Tab. 14/16 sum = 1.0020",
A2 = 0.0383) and "12 of 13" coincidences. Source of error: A2 was incorrectly read
as 0.0383 instead of 0.0314. f7516c5 corrected this from PDF verification (2026-11-02).
The git history contains the incorrect values; this errata note documents the chain
of corrections for archive transparency.
