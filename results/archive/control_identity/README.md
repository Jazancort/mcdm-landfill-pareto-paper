# results/archive/control_identity/

These files were produced by early versions of raw_sensitivity.py that contained
an algebraic identity in the SAW scoring. The identity arose because the scale
factor rho_shift/rho_raw was applied symmetrically, causing it to cancel.

## Files

### _raw_sensitivity_athena.csv (SHA: 928625fe)
Single-cell version (only SAW/optimal). Structure: draw, best_shift, best_raw, same.
All 500 draws give same=1 (SAW raw = SAW shift, trivially, by identity).
Produced before the four-cell script existed.

### raw_sensitivity_N500.csv (SHA: b2746e53)
Single-cell version, N=500 draws. Same algebraic identity issue.

## Why these are NOT sensitivity results

A true sensitivity test computes the score difference between shift and raw
normalisation. These files show 500/500 same because the score was computed
as X_adj / norms_raw * w * scale where scale = norms_shift / norms_raw, causing
the norms_raw to cancel out. The result was trivially identical, not empirically robust.

## Correct result

See results/raw_sensitivity_4cells.csv (SHA: 9aee31af). Uses the corrected
formula saw_raw_fn = (X_adj / norms_raw * w).sum(1) without the scale factor.
Result: 488/500 SAW optimal, 489/500 SAW greedy, 487/500 TOPSIS optimal.
