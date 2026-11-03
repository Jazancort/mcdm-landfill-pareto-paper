# DEV-FOGO-E1B-001 — E1-B zero-regret fraction: 28% → 35.4%
Date: 2026-11-03
Type: post-data errata for published Fogo result (fraction of draws where R=0)
Affects: regret_macros.tex, manuscript §S7a, archive/results/regret/regret_macros.tex

## Problem

`\RegretEoneBfracZero{28}` in `results/regret/regret_macros.tex` states that 28%
of Fogo weight draws give R(E1-B, opt) = 0. This value is WRONG.

## Root cause

**Commit `1f68ba91` (2026-10-25 20:00)**: Introduced `_compute_e1_regret.py` with
old R denominator (range over 8 cells only). Under that definition, mean R was 72 pp,
median 67 pp, fraction R=0 was 28% (140/500 draws). The macro was written manually.

**Commit `5da02ab` (2026-10-25 20:10, 10 minutes later)**: Fixed R denominator to
range over ALL 1.94M trios. Mean became 4.53 pp, median 5.50 pp. The macros for
mean and median were regenerated, but `\RegretEoneBfracZero` was NOT updated because
`_compute_e1_regret.py` does not print or compute the fraction.

The macro stayed at 28% for all subsequent commits.

## Correct value

Using `diagnostics/e1_oracle_per_draw.py` (commit d9fcbd2, SHA-verified
`_compute_e1_regret.py`), with V_range from `regret_perdraw.csv` (same as oracle):

| Criterion | Count / 500 |
|---|---|
| R_pp == 0.0 exact (batch V_max vs sequential V_sel) | 101 |
| R_pp < 1e-9 | 177 |
| round(R_pp, 2) == 0.00 | 177 |
| opt_e1b_idx == opt_mm_idx (trio == t*) | **177** |

The 101 vs 177 split is a floating-point batch vs sequential V_max artifact
(max |diff| = 8.5e-14 in R fraction). The semantic criterion (same trio as t*)
gives **177/500 = 35.4%**, confirmed by:
- `diagnostics/_count_e1b_zeros.py` (sequential V_all, all 5 criteria = 177)
- `diagnostics/e1_oracle_per_draw.py` (oracle CSV with trio_eq_tstar column)

Smallest R among 323 draws where trio != t*: **0.042616 pp** (>> 1e-12 pp).
The gap between "trio is t*" and "trio is not t*" is clear and unambiguous.

76 draws with 0 < R < 1e-9 (batch artifact): ALL have trio == t* (confirmed by
`e1_oracle_per_draw.py` output: `trio==t* in ALL: True`).

## Required corrections

**STATUS: APPLIED** (commit after 8de8dd8, branch eval-v2-rewrite)

1. `results/regret/regret_macros.tex`: **DONE** — `\RegretEoneBfracZero{35.4}` + new `\RegretEoneBfracZeroN{177}`
2. `archive/results/regret/regret_macros.tex`: **DONE** — same correction
3. `scripts/compute_regret.py`: **DONE** — now generates E1 section from oracle CSV (fraction no longer hardcoded)
4. Manuscript `src/main.tex` and `paper/manuscript/main.tex`:
   Lines 2439/2441/2457/2459 use `\RegretEoneBfracZero` macro — **updates automatically** via macro.
5. Zenodo/preprint: errata note required if 28% appears in a published version.

## Definition of "zero" (for S7a and related)

A draw has R=0 iff the selected trio equals t* (SAW/mm/optimal trio). This is
the semantically correct definition. Numerical threshold R < 1e-12 gives the same
177/500 result because the minimum non-zero R is 0.042616 pp >> 1e-12 pp.

## Evidence files (commit d9fcbd2, Athena)

- `results/regret/e1_oracle_per_draw.csv`
  SHA-256: 913396cea6a6288836783c9bc02a5f7a898b70643dd2788a5d0780b42155b56c
- `results/regret/e1b_R_pp_oracle_rerun.npy`
  (backup from diagnostics/_count_e1b_zeros.py)
