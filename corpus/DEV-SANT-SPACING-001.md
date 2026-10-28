# DEV-SANT-SPACING-001 — S-N grid spacing corrected from 1250 m to 1000 m
Date: 2026-10-29
Type: pipeline correction — spacing rule applied per-branch (no criterion values involved)

## PRESPEC declaration (§3 Common pipeline)

PRESPEC_SANTIAGO §3 declares the spacing algorithm:

> "Start at initial spacing (default 1 000 m).
>  If n_trios(N_cand) > trio_limit: increase by 0.25 km steps until n_trios ≤ limit
>  or spacing > 5 000 m. If 5 000 m is reached: branch abandoned."
>
> "The trio limit (50 000 000) applies to n_trios(N_cand)."

The algorithm is defined once in the Common pipeline section and applies to
each branch independently (S-T and S-N use different boundaries and produce
different candidate counts).

## What happened

Stage 3a (commit b9650cd) applied the spacing rule to S-T only. The S-T grid at
1 km gave n_trios_Ncand = 76,124,767 (> 50M), triggering the increase to 1.25 km.

The S-N branch was not checked independently. Instead, GRID_SPACING = 1250.0 (a
single global constant in santiago_extract.py) was used for both S-T and S-N.
The S-N extraction at 1.25 km was committed at ebf7dfe without verifying that the
spacing rule required 1.25 km for S-N.

## Verified n_trios_Ncand for S-N at both spacings

Computed from S-N boundary geometry only (no criterion values), using the
tr(A³)/6 formula (same algorithm as santiago_grid.py), d_min = 10 km:

| Spacing | N_cand | n_trios(N_cand) | Decision |
|---------|--------|-----------------|----------|
| 1000 m  | 387    | 1,146,955       | ACCEPT (well below 50M limit) |
| 1250 m  | 249    | 305,584         | ACCEPT (but wrong — rule gives 1000 m) |

Both spacings are within the acceptable range. The PRESPEC rule gives 1000 m
for S-N because n_trios_Ncand = 1,146,955 at 1000 m is below the 50M limit.

## Correction

S-N extraction re-run at 1000 m (commit following this DEV file).
df_santiago_sn.csv, extract_report_sn.json, and stage3b_descriptors.json
updated with the corrected N_cand=387, N_adm≥100 (verified post-extraction).

GRID_SPACING_SN = 1000.0 in santiago_extract.py (was: GRID_SPACING = 1250.0 global).
GRID_SPACING_ST = 1250.0 unchanged (spacing rule correctly triggered at 1 km for S-T).

## No criterion-value bias

The spacing decision is purely geometric: it depends only on the boundary geometry
and the trio limit, not on any criterion value or MCDM result. Applying the rule
correctly after having seen S-N descriptors at 1.25 km introduces no criterion-value-
dependent arbitrariness. The PRESPEC spacing rule is mechanical.

## Official S-T spacing record (Stage 3a, for completeness)

| Spacing | N_cand | n_trios(N_cand) | Decision |
|---------|--------|-----------------|----------|
| 1000 m  | 1001   | 76,124,767      | OVER (> 50M) — trigger +0.25 km |
| 1250 m  | 650    | 21,112,677      | ACCEPT |

Source: TASKS_REVISION.md Stage 3a section, commit b9650cd.

## Impact on predictions

The S-N branch changes: different N_cand, N_adm, and descriptors at 1000 m.
The predictions in PRESPEC_SANTIAGO_A5 §6 are unchanged in structure; their
conditions (TV ≥ 0.05, TV_B ≥ 0.05, TV_W ≥ 0.05, point_mass < 0.5) are
re-evaluated on the corrected S-N data in Stage 3b.
