# diagnostics/ — Diagnostic scripts for Gate 1 E1 oracle

## e1_oracle_per_draw.py

Generates `results/regret/e1_oracle_per_draw.csv` with per-draw E1 results.
SHA-verifies `_compute_e1_regret.py` before running. Used by Gate 1.

Run on Athena:
```bash
MCDM_DATA_DIR=/home/julioazancort/scratch/mcdm \
.venv/bin/python3 diagnostics/e1_oracle_per_draw.py
```

## _count_e1b_zeros.py

Counts R(E1-B_opt)==0 with 5 criteria. Confirms 177/500 = 35.4%.

## Key findings (2026-11-03)

| Criterion | Count / 500 |
|---|---|
| R_pp == 0.0 exact (V_range from CSV batch) | 101 |
| round(R_pp, 2) == 0.00 | 177 |
| opt_e1b_idx == opt_mm_idx (trio == t*) | 177 |

The 101 vs 177 split is a floating-point batch vs sequential V_max artifact
(|diff| ≤ 8.5e-14 in R fraction). Semantically, 177 is correct: it counts
draws where E1-B selects the same trio as SAW/mm/optimal (t*).

The 28% (140/500) in regret_macros.tex comes from commit 1f68ba91 (25 Oct 2026,
old R denominator, mean=72pp). After 5da02ab fixed the denominator (mean→4.53pp),
the fraction was NOT updated because _compute_e1_regret.py does not compute it.
This is documented in DEV-FOGO-E1B-001 and DEV-SANT-EVALR-001 ER-7.
