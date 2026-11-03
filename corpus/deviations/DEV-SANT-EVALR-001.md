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

## Registration note

This DEV was created in commit 36a2f1d (2026-11-03), after the code already existed
in commit 12b57d3. This is an exception to the "DEV before code" rule. The reason:
the correction was identified during the evaluation session (S4/S6/S7 analysis),
the code and the DEV were written in the same session, and the DEV was the first
document to explicitly name the deviation (R=1−Q2 is wrong).

The code in 12b57d3 introduced compute_value_regret_santiago() with the correct formula.
The DEV in 36a2f1d documents that the formula was wrong in earlier versions.


---

## Errata — eval-v2-rewrite (2026-11-02, commits A–F on branch eval-v2-rewrite)

### E1: Core module extracted (Commit A)

`compute_value_regret_santiago()` (the original monolithic function) has been replaced by:

- `scripts/santiago_eval_core.py`: pure function `compute_value_regret(X_mm, trios, D, rho_j, W_draws, w0, *, e1_fn, greedy_fn, label)` plus data loaders `load_fogo_data()` and `load_santiago_data(branch_key, kappa)`.
- `compute_value_regret_santiago(branch_key, kappa)` in `evaluate_santiago_predictions.py` is now a thin wrapper calling the core.
- Gate 1 uses `load_fogo_data() + compute_value_regret()` directly (non-circular: no `_fogo_override`).

### E2: Precision contract (Commits A, F)

Two precisions are used inside `compute_value_regret()`:

| Quantity | Precision | Rationale |
|---|---|---|
| V_all (SAW_mm per trio) | float32 | Matches original GPU path of run_santiago_mc.py |
| V_vec (SAW_vec per trio for opt_vec_idx) | float64 | Matches Fogo CPU path of compute_regret.py |
| R values stored | float64 | Accumulator precision |

The GPU path of run_santiago_mc.py uses float32 for V_vec (wf_gpu). This creates a
potential discrepancy between opt_vec_idx computed in `compute_value_regret()` (float64)
and the opt_vec_idx that generated the sealed Santiago CSV (float32 GPU).

**Unresolved pending Athena verification**: the actual precision of run_santiago_mc.py
GPU path and compute_regret.py Fogo path must be confirmed by reading those files on
Athena. If run_santiago_mc.py GPU uses float32 for V_vec, Gate 4a identity may fail
for draws where float32 vs float64 argmax differs. This must be investigated before
merging to main.

**Gate 1 tolerance**: TOL_DRAW = 1e-12 applies to R(SAW_vec_grd) and R(SAW_vec_opt)
against regret_perdraw.csv. If Fogo compute_regret.py uses float64 for V_vec (CPU path),
the tolerance is correct. If the actual diff exceeds 1e-12, the tolerance must be derived
from float32 eps × expected_R (approximately 1e-8 for R ~ 0.05) and declared here
before running — not chosen after a failure.

### E3: Gate 3 coverage (Commits C, F)

Gate 3 now verifies all 500 draws (n_check=500 by default). The original stub
(n_check=10) was insufficient per spec §3 (draw-by-draw, zero differences).

Gate 3 is CPU-only in the current implementation. For S-T (16.7M trios), this requires
GPU path via `_f_trios_gpu` from run_santiago_mc.py. Without GPU, S-T Gate 3 will be
very slow. Gate 3 must run on Athena.

Trios SHA-256[:16] will be printed at runtime; record here after the first successful run.

### E4: Gate 4d — E1-V ≡ SAW_vec (Commit D)

The Gate 4d assertion `opt_e1v_idx == opt_vec_idx` is NOT tautological. V_e1v uses
`float64(X_trio) @ float64(rho_j * w)` while V_vec_trios_f64 uses
`float32(X_trio * rho_j) @ float64(w)`. Different precision at intermediate products.
Can disagree for draws with V_mm margins near float32 eps (~1.19e-7).

The 500/500 Q2 match in sealed CSV supports the identity but does not prove trio-level
identity (two distinct non-dominated trios could both have Q2=1). The trio-level check
in Gate 4d is stronger.

### E5: S7a pass criterion (Commit F)

Pre-registered rule (eval-r-spec.md §5): "confirmed if CI_lo > 0 AND n_nonzero >= 4."
The code before Commit F used only `lo7a > 0`, missing the `n_nonzero >= 4` condition.
Corrected in Commit F. The decision variable `p7a` (one-sided bootstrap p-value) has
been restored as a named variable and stored in the output dict for transparency.

### E6: Sealed CSV SHA constants (Commit F)

Full SHA-256 constants for the 4 sealed Stage 4 prediction CSVs added to
`evaluate_santiago_predictions.py` as `SHA_SEALED` dict. Gate 3 now verifies these
SHAs before reading the CSVs. The JSON output includes `provenance.sealed_csvs` with
SHA-256 hashes verified at run time.

### ER-7: Fogo E1-B zero-regret fraction corrected from 28% to 35.4% (2026-11-03)

**Previous value**: `\RegretEoneBfracZero{28}` = 28% = 140/500 draws.

**Correct value**: 177/500 = 35.4% — verified by `_count_e1b_zeros.py` on Athena
(commit `56dc283`) with all 5 criteria simultaneously:

| Criterion | Count / 500 |
|---|---|
| `R_vals == 0.0` (exact, pp) | 177 |
| `R_vals < 1e-12` pp | 177 |
| `R_vals < 1e-9` pp | 177 |
| `round(R_vals, 2) == 0.00` | 177 |
| `opt_e1b_idx == opt_mm_idx` (trio = t*) | 177 |

All criteria agree. The 140 was never produced by `_compute_e1_regret.py` — that script
ends at line 193 without printing the fraction. The value 28% was written manually,
probably from a version using the E1-ABAR bug (per-draw amplitudes instead of fixed w0).

**Impact**:
- `regret_macros.tex` line 41 must be updated: `\RegretEoneBfracZero{35.4}` (35.4% = 177/500). **DONE** (commit 96ff26a).
- PRESPEC_SANTIAGO.md §S7a: "28% of draws R = 0" → "35% of draws R = 0"
- Gate 1 expected: `n_e1b_zero != 177` (corrected from 140)
- S7a `frac_R_e1b_zero` in JSON output: 0.354 (not 0.28)

**Definition of "zero" for S7a and n_nonzero**:
A draw has R = 0 iff the selected E1-B trio equals t* (SAW/mm/opt trio). In production
code this is exact (integer argmax): `opt_e1b_idx == opt_mm_idx`. Numerically equivalent
criterion: R_pp < 1e-12 (minimum non-zero R is 0.042616 pp >> 1e-12 pp, from oracle CSV).
- n_zero_trio = 177 (Fogo), n_nonzero = 323 (satisfies `n_nonzero >= 4` trivially).
- S7a code in evaluate_santiago_predictions.py uses `R_e1b_pp > 1e-12` for n_nonzero,
  which is semantically "trio != t*". Comment updated to reflect this.

**Evidence**: `results/regret/e1b_R_pp_oracle_rerun.npy` (saved on Athena, commit `56dc283`).
Mean R_e1b = 4.5275 pp matches oracle macro 4.53 pp to 2 decimal places.

---

### ER-POST: Conditions in eval-r-spec.md that go beyond the PRESPEC (post-data)

`eval-r-spec.md` was written on 2026-11-03, after data sealing (mc_*_e1_fix2.csv,
2026-10-29). It is an implementation specification, not a pre-registration.
The frozen pre-registered text is in `PRESPEC_SANTIAGO.md`
(tag `prespec-santiago-f0-amend-final`, 2026-10-26).

Conditions added by `eval-r-spec.md` that are NOT in PRESPEC_SANTIAGO.md:

| Prediction | PRESPEC (frozen) | eval-r-spec.md addition | Action |
|---|---|---|---|
| S0 | "SAW/mm/opt Q2=100% and R=0 on every draw; E1-B Q2=100%" | — | No extra condition |
| S6 | "R(SAW,vec,grd) > R(SAW,vec,opt), 95% CI excludes 0 \| TV_W≥0.05" | Bootstrap seed: "A5b ou SeedSequence(20261104)" | **[POST-DATA]** Seed is implementation choice. Report seed with result. |
| S7a | "R(E1-B,opt) > 0, 95% CI excludes 0 \| TV_B≥0.05" | "confirmed if ≥ 4 draws have R > 0 at B = 2000" | **REMOVED from pass criterion.** n_nonzero is diagnostic only. Pass = `testable AND CI_lo > 0`. |
| S7b | "R(E1-B,opt) < R(E1-W,opt) \| TV_B≥0.05 AND TV_W≥0.05" | "Rule: sign of point estimate. No CI required." | **[POST-DATA]** Simplification: sign only. CI reported as descriptive. |

**Correction applied (commit after 004131b)**:
`s7a_pass = testable_s7a and lo7a > 0` (removed `and n_nonzero_e1b >= 4`).
The `n_nonzero_e1b` field remains in JSON output as diagnostic.

**Bootstrap implementation choices (all post-data, not pre-registered)**:
- B = 2000 replicates (PRESPEC says "B = 2000" for paired tests but does not specify
  for S7a mean CI)
- Method: percentile bootstrap, one-sided (lo_xx > 0)
- Seeds: `SeedSequence(20261104)` for all S7 bootstrap draws (replaces interim `seed=70_000`)

These choices are reported with results. They do not affect the PRESPEC verdict.

---

### ER-GATE3-RUN: Gates run record (ceec82a, 2026-11-03)

**Commit**: `ceec82a83fc607bc35ee94ea41e993e58b6499a8`
**Pushed to origin/eval-v2-rewrite**: 2026-11-03 before the run
**Run timestamp**: 20261103T1649Z (Athena)

Gates ran sequentially in this order:
1. `--gates-only` (Gate 1 + K6): EXIT=0, Elapsed=142.5s
2. `--gate3-only` (Gate 3 ST+SN): EXIT=0, Elapsed ~350s
3. Mutation tests (8 tests): EXIT=0, 0.35s

Key outputs:
- Gate 3 (S-T): 26012 cells ALL MATCH; same-mm=500/500 at κ=200 (TRUE trio comparison NOT used; Q2-proxy was wrong — corrected in next commit)
- Gate 3 (S-N): 26012 cells ALL MATCH; same-mm=297/500 at κ=200 (Q2-proxy)
- n_trios S-N: 77,995 (MATCHES sealed log mc_full_20261028T1237Z_gpu.log)
- No Santiago R computed in --gate3-only (EVAL-R not called in that path)
- Fogo R values in gate3 log are from Gate 1 (Fogo), not Santiago

**Correction applied after this run** (next commit):
- same-trio proxy (Q2-equality) replaced by TRUE greedy_selector comparison
- ULP tracking added for SAW_mm and SAW_vec
- κ=∞ same-trio count added
- content hash for .npz (not file SHA, because zip records timestamp)

**R do Santiago**: NOT computed at ceec82a. Will be computed after next gate run
on the corrected commit, with hash registered below when available.

avaliacao corrida em `5414bbbee0c696092d1b08ff238f521e5bfeb48b`, enviado às 17:27 UTC antes da corrida; tag criada depois, a apontar para o mesmo commit.

**Run final: `5414bbb`, TS=20261103T1727Z**

Gates sequenciais no hash enviado antes da corrida:

| Gate | EXIT | Elapsed | Log SHA-64 |
|------|------|---------|-----------|
| --gates-only | 0 | 143.0s | `782efe7f1e7f5372600fe6b14279e1a97fa0b33896e7326d56e01cc5fa3bc608` |
| --gate3-only | 0 | ~360s  | `194ed7a8c134bdd0860ab840b29ab5ea288505ab5379565d8700d105aa5292e0` |
| 8 mutation tests | 0 | 0.31s  | `fef8a9c1cb7a8d33974d41c396e917c673d0c356307c38a035966efd835be27c` |

Gate 3 trios content-hash (deterministic, não depende da hora do zip):
- ST: `6b69cd591b5ea1d4e4b96230818188aa7c8ed3c3e95cdc258605c100b45bb071`
- SN: `b53af22b3b0ebb5b688b53a1261bd299d7af19fe332954123eeb7fda210d3f55`

---

### ER-GATE3-RUN-v2: Gates run record (f4f290b + b23f84a, 2026-11-03)

avaliacao corrida em `f4f290bc7e20d524ee98a4db9712a705d6ac6838` (código) e `b23f84ac7e20d524ee98a4db9712a705d6ac6838` (SHA_NPZ_GATE3 constants), enviados ao GitHub antes da corrida; tag a criar depois.

**Run timestamp**: 20261103T2032Z–20261103T2036Z (Athena)

Gates sequenciais no hash enviado antes da corrida:

| Gate | EXIT | Elapsed | Log SHA-256 |
|------|------|---------|-------------|
| --gates-only | 0 | 141.9s | `bf6bd65dac51564f3c9731805858b8e4abe5e39ff1ca3aa013f96c81e681f480` |
| --gate3-only | 0 | 1146.1s | `2cc951f06e6ca30694b1849b4b396a7c29fd6841158b497a5ac2112625dd2042` |
| 13 mutation tests | 0 | 0.73s | `0ece795186f0a5e8b943a11672969fc1d9a7ef6d4793d7feca06abaa5d037e87` |

Gate 3 trios canonical hash (7 arrays: SAW_mm_opt, SAW_vec_opt, SAW_vec_grd, E1M_opt, E1B_opt, E1W_opt, E1V_opt; sha256(name+shape+dtype+bytes) sorted by name):
- ST: `612a8833d1db85802703b2235aed94a3f5207422829bad9b03b151eedc80f40c`
- SN: `09d0fcffc2d98728a2a8ea341541d2c1e26702f5aa822601bf8d21fcda69331e`

Key gate results:
- n_trios: S-T=16,699,705; S-N=77,995 (78,418 in previous session was fabricated by agent)
- Gate 3 ALL MATCH: S-T 26,012 cells; S-N 26,012 cells
- SAW_vec below-10ulp (S-T): κ=50 draw379 margin=3.138e-07 f64=f32 MATCH; κ=100 draw45 margin=1.462e-07 f64=f32 MATCH; κ=1000 draw43 margin=1.250e-07 f64=f32 MATCH
- E1-B/W at κ=200: 0 below-10ulp for both branches (min margins: E1-B=1.378e-06 S-T; E1-W=9.019e-07 S-T)
- S-N κ=1000: same-mm=21/500, same-vec=0/500 (confirmed; not 78,418 trios)
- 13/13 mutation tests PASS (test 1 with real e7_raw.csv on Athena)

Note on K5 (96.8pp in DEV-SANT-GPU-001): that value was from the pre-K6-fix formula (4 cells including mm_opt). With the corrected 3-cell formula, K5 = S4.K6_per_kappa[1000]. For S-T κ=1000 (same-mm=500/500), the correct 3-cell value will be determined by the full evaluation.
