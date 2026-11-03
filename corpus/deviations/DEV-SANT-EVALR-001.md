# DEV-SANT-EVALR-001 — S6/S7: value regret replaces R = 1 − Q2
Date: 2026-11-03 (written after commit 12b57d3; code already exists)
Type: post-data implementation correction (discovered during S4/S6/S7 analysis)
Affects: S6, S7a, S7b predictions; S0 completeness check

## Original implementation (commits up to 12b57d3)

evaluate_santiago_predictions.py computed "regret" as:

    R_j = 1 − Q2_j   (fraction of draws where cell j's portfolio is NOT on the frontier)

This was inherited from the r4 pipeline description ("fraction of non-efficient draws").
It is NOT the value regret that the PRESPEC S6/S7 refer to.

Under this definition:
    S6: R_grd − R_opt = (1−Q2_grd) − (1−Q2_opt) = Q2_opt − Q2_grd
This is the NEGATIVE of the S2 test (Q2_grd − Q2_opt).
S6 with R=1−Q2 and S2 are identical tests with opposite sign conventions.
They cannot both be meaningful predictions at the same time.

## Corrected definition (commit fd64eeb, 2026-11-03)

Value regret per PRESPEC EVAL-R spec (notes/eval-r-spec.md):

    R(t; w) = max(0, V_mm(t*; w) − V_mm(t; w)) / max(V_mm(t*; w) − V_min(T; w), 1e-12)

where:
    V_mm(t; w) = SAW/min-max score = (X_adj[i0] + X_adj[i1] + X_adj[i2]) @ w
    t*(w)      = SAW/mm/optimal trio (Proposition 1: always on frontier, V_mm = v_max)
    V_min(T;w) = min V_mm over ALL feasible trios T

R = 0 ↔ selected trio is t* (exact, integer comparison).
R in [0, 1] by construction.
Report in pp: multiply by 100.

## Why the correction matters for S6 and S7

Under value regret:
    S6: R(SAW,vec,grd) vs R(SAW,vec,opt) — how much value the two assembly modes LOSE
        relative to the mm-optimal. These are different quantities from Q2.
    S7a: R(E1-B, opt) > 0 — does the E1-B optimal trio lose value vs the mm-optimal?
    S7b: R(E1-B, opt) < R(E1-W, opt) — ordering of value losses.

Under R=1−Q2, S7a would test whether E1-B ever fails to be Q2-efficient, which is
the K2 check (Theorem 1). Since K2 always passes (100% for E1-B), R=1−Q2 would give
R=0 always → S7a never confirmed. This contradicts the Fogo reference (R_E1B=4.53pp).

## Scale

R is dimensionless in [0, 1] internally. The script reports R × 100 (percentage points).
The Fogo oracle is: R(SAW,vec,grd)=6.63 pp, R(SAW,vec,opt)=5.27 pp, R(E1-B,opt)=4.53 pp.

## Bootstrap for S6/S7

Paired bootstrap, B = 2000, percentile method, seed 20261104.
S6: test CI of R_grd − R_opt (pp) vs 0 at κ=200. Confirmed if CI_lo > 0.
S7b: sign of estimate R_E1B_mean − R_E1W_mean. No CI required for verdict.
IC [0.95; 1.74] (from Fogo _compute_e1_regret.py, seed 55) is INFORMATIVE only,
not a gate — it depends on the bootstrap seed and may differ between runs.

## Direction of effect

Under value regret, S6 and S2 are no longer mirror tests:
- S2 asks: does greedy Q2 exceed optimal Q2 (frontier attainment)?
- S6 asks: does greedy value regret exceed optimal value regret?
For S-T: both zero (greedy = optimal in every draw at κ≥100).
For S-N: S2 not confirmed (optimal Q2 >> greedy Q2); S6 direction depends on EVAL-R.

## Gate 1 (non-circular)

Gate 1 runs compute_value_regret_santiago() on Fogo data and compares against
the SHA-verified oracle files (regret_aggregate.csv, regret_macros.tex).
On Windows: SHA-only check. Must pass with full re-computation on Athena before tag.

## History

- Commit 12b57d3 (2026-11-03): added compute_value_regret_santiago() with correct formula;
  but S6/S7 still marked "PENDING EVAL-R" in evaluate_branch().
- Commit fd64eeb (2026-11-03): removed PENDING; S6/S7 use value regret; raise if unavailable.
- Commit current: gate_1 rewritten to be non-circular; gate_3 stub added;
  assert_regression expanded; DEV-SANT-EVALR-001 created.
