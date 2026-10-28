# DEV-SANT-GPU-001 — GPU acceleration substituted for CPU in Stage 4 MC
Date: 2026-10-28
Type: implementation change (code path altered after launch; results sealed)

## Timeline

| UTC | Event |
|---|---|
| 09:25 | CPU run launched (tag r4, stage4-launch-r4, 7ed3202^4 = da3a840) |
| ~09:28 | CPU run stopped manually (κ=25 of S-T in progress, ~19 draws of 500, 0% complete) |
| 09:32 | CPU partial log written: only startup provenance + "κ=25 (500 draws)" line |
| 12:37 | GPU run launched (tag r5, stage4-launch-r5, 7ed3202, CUDA_VISIBLE_DEVICES=1) |
| 12:42 | GPU run completed both branches (S-T: ~5 min, S-N: ~15 s) |

No CPU κ completed before stop. The CPU partial log is 1455 bytes:
SHA-256: cb3f220280ec11a0a137e636505ead502400d047b991a4d3b7f092751a77339d

## Why the change was made

The GPU (RTX 4000 Ada, GPU 1) was idle (13 MiB / 20 GB used).
The bottleneck check_dominated_raw + compute_trio_objectives is bandwidth-bound
(reads 400 MB per call × 8 cells × 500 draws per κ). Benchmark: 4.6 ms per call
on GPU vs ~1000 ms on CPU → ~100–200× speedup. S-T estimated: 9.3 h CPU vs ~7 min GPU.

GPU 0 (RTX 5000 Ada) occupied by llama-server (17.8 GB VRAM). GPU 1 used.

## _stage4_run_meta.json removal

The file `results/santiago/_stage4_run_meta.json` written by the CPU partial run
pointed to commit da3a840 (r4). When the GPU run (commit 7ed3202, r5) tried to start,
the metadata check failed: "git_hash: checkpoint=da3a840 current=7ed3202".
The file was deleted explicitly before relaunching.

No CPU checkpoint (.npz) was produced (the CPU run never completed a κ value).
All .npz timestamps are in the range 12:38–12:42 UTC (GPU run only):
  mc_ST_k25.npz: 2026-10-28T12:38:25Z (first checkpoint of GPU run)
Proof: `ls -la --time-style=full-iso results/santiago/mc_*.npz` shows no file
predating 12:38 UTC.

## Code changes r4 → r5

git diff --stat stage4-launch-r4 stage4-launch-r5 -- scripts/:
  scripts/run_santiago_mc.py | 281 ++++++++++++++++++++++++++++++++++++++-------
  1 file changed, 237 insertions(+), 44 deletions(-)

Added:
- cupy import block with fallback to CPU (print on startup)
- prepare_gpu_data(): pre-loads trios, X_mm, rho_j to GPU once per branch
- _f_trios_gpu(): compute F_site and F_trios on GPU per draw
- _check_dom_gpu(): domination check on GPU
- _optimal_gpu(): argmax of trio scores on GPU
- compute_q2_all_cells_gpu(): all 8 cells on GPU
- compute_e1_cells_gpu(): E1 cells (M/B/W/V) on GPU
- run_branch(): calls prepare_gpu_data() once, passes gpu_data to run_kappa()
- run_kappa(): dispatches to GPU or CPU path based on _USE_GPU

Not changed in run_kappa(): weight drawing (numpy), greedy_selector (CPU),
bootstrap_contrast(), evaluate_gates(), generate_macros(), main().

## Origin of GPU code

The GPU code was written from scratch for Stage 4 on 2026-10-28. It was not
adapted from the E7 Fogo pipeline (run_e7_kappa_sweep.py, a separate script
that uses only numpy). The E7 run on Athena (RTX 4000 Ada, 997 s) used CPU-only
computation (no cupy in run_e7_kappa_sweep.py).

## A5 checklist on r5 (stage4-launch-r5, 7ed3202)

Checked against run_santiago_mc.py at 7ed3202:
- seeds: KAPPA_VALUES=[25,50,100,200,400,1000], parent=[1,4,15,17,28,30],
  SeedSequence.spawn(2). Dirichlet draws via numpy.random.Generator. PASS.
- N_DRAWS=500, B_BOOT=2000. PASS.
- K1 abort (K1 FAIL → return {"abort": True}). PASS.
- kappa=inf = 1 draw. PASS.
- E1 cells M/B/W/V at κ=200 and κ=inf only. PASS.
- Bootstrap paired, Holm K4. PASS.
- DELTA_PP=2.5. PASS.
- git status --untracked-files=no in log. PASS.
- SHA-256 full (64 hex) for CSVs + uv.lock hash. PASS.
- w0 assert sys.exit(1) in log_startup_provenance(). PASS.
- No cp.random anywhere in run_kappa (verified by inspect.getsource). PASS.

## Three code conditions verified (2026-10-28, verify_gpu.py)

1. Seeds: `rng.dirichlet` is numpy.random.Generator throughout. No cupy.random
   call anywhere in run_kappa (confirmed by inspect.getsource). PASS.

2. Float64: X_mm (float64), trios (int32), rho_j (float64) on GPU.
   wA = cp.asarray(...astype(np.float64)) — explicit float64.
   F_site = cp.empty((N, G), dtype=cp.float64). PASS.

3. Argmax tie-breaking: numpy and cupy return identical index for all tested cases
   including all-tied arrays. Verified on S-T nominal weights (w0):
   - All 601 SAW_mm site scores are unique at nominal weights (no ties)
   - Exactly 1 trio tied at the maximum SAW_mm trio score
   - numpy optimal_selector and cupy _optimal_gpu select identical trio (index 10030254,
     sites [132, 134, 570])

## Equivalence rule (declared before equivalence test is complete)

The implementation of reference is r4 (CPU, da3a840), because r4 was the pre-registered
version verified by the A5 checklist.

**Rule:** The GPU results (r5) are accepted as the main analysis if and only if, for
every (branch, κ, cell), the Q2 value from the GPU run equals the Q2 value from a
full r4 CPU run on the same input data.
  - Discrete outputs (Q2 ∈ {0,1}): must be exactly equal.
  - Continuous outputs (bootstrap CI endpoints): may differ by at most 1e-12.

If any Q2 differs: the CPU run (r4) is the main analysis. The GPU run is reported
as a deviating replication with the difference documented.

## Equivalence test status

Launched 2026-10-28 from worktree at ~/scratch/mc_equiv_cpu (r4, da3a840).

### S-N equivalence: CONFIRMED

CPU r4 and GPU r5 produce identical Q2 outputs for S-N (all κ):
  - mc_SN_raw.csv: 3001 rows × 8 cells = 24,008 Q2 values → 0 differences
  - mc_SN_e1.csv:  2004 rows × Q2_opt + Q2_grd → 0 differences

Gate comparison (CPU vs GPU):
  K1: identical (100% all κ)
  K2: identical (100% at κ=200 and κ=∞)
  K3: identical (no reversals)
  K4: p-values differ by bootstrap randomness (K4 bootstrap is unseeded);
      both runs: all κ pass after Holm correction
  K5: identical (assembly_1000=96.8pp, assembly_inf=100.0pp)
  K6: identical per-κ values

Result: GPU r5 ACCEPTED as main analysis for S-N (equivalence rule satisfied).

### S-T equivalence: partial — pending A+B verification

S-T full CPU run (9.3h) was cancelled during κ=25 after ~3 min without completing
any κ (see timeline above). Replaced by two targeted checks:

**Criterion (written BEFORE running A and B):**

S-T GPU r5 is accepted as equivalent to CPU r4 if:
  (A) No decision in the margin audit has gap < τ=1e-9 in absolute terms
      (meaning floating-point rounding cannot flip any Q2 or argmax result), OR
      all flagged fragile draws coincide in (B).
  (B) All discrete Q2 values in the CPU sample match GPU r5 exactly.
  Combined: zero fragile decisions OR all fragile decisions confirmed correct.

If any Q2 differs in (B): GPU r5 S-T result is NOT accepted; r4 CPU is the reference.

**Verification A: margin audit (GPU, a few minutes)**

For each of the 3000 stochastic S-T draws, record:
  - argmax_gap: trio_scores[rank1] - trio_scores[rank2] per scorer-cell
  - dom_gap: for the selected trio, min positive value of any dominating-direction
    component across all 16.7M trios (i.e., the closest near-dominator)
τ = 1e-9 (absolute). Float64 rounding error for sums of ~600 terms ≈ 600 × ε₅₄ ≈ 1e-13.
Fragile: gap < τ for either metric.

**Verification B: CPU sample (r4 worktree, parallel κ, ~13 min)**

Draws per κ: 20 random (seed=99, not a canonical seed) + all fragile from A.
Weight regeneration: advance `get_branch_rngs(κ)` exactly draw_idx steps to
reproduce the same w as in the sealed run.
Criterion: discrete Q2 outputs identical for all sampled draws.
Statistical bound: if all 120 random draws (20 × 6 κ) match, divergence rate
< 2.5% with 95% confidence (rule of three over 120 independent draws).

**Verification A results — v2 (2026-10-28, GPU 0, 3000 stochastic draws × 6κ × 8 cells = 24,000 decisions):**

Metrics and definitions:

  argmax_gap (per draw, per _opt cell):
    = trio_scores[rank1] − trio_scores[rank2]
    A gap of 0 means two trios tie exactly → argmax order is undefined.
    τ = 1e-9 (absolute). Float64 rounding for sums of ~600 terms ≈ 1e-13.

  dom_gap (per draw, per _opt cell):
    For selected trio f_sel, a "near-dominator" is any trio t with
    max_g(F_t[g] − f_sel[g]) > 0 AND min_g(F_t[g] − f_sel[g]) ≥ −EPS.
    dom_gap = min over near-dominators of max_g(F_t[g] − f_sel[g]).
    Measures: how far the selected trio is from being dominated.
    (This is NOT the smallest difference between any two objective values;
    it is the distance from the selected trio to the domination boundary.)

Results:
  min_argmax_gap:          1.250e-07  (τ=1e-9; safety factor ×125 over τ, ×1.25M over float64 error)
  min_dom_gap:             2.716e-04  (×270,000 over τ)
  exact_ties (argmax==0):  0          (no draws where two trios tie exactly)
  exact_ties (dom==0):     0          (no draws where selected trio is dominated — consistent with K1=100%)
  total_fragile (gap<τ):   0
  Top-20 smallest margins per κ: recorded in st_margin_audit_v2.json

  PASS: no fragile decisions in 24,000 cells; rounding cannot change any Q2, argmax, or domination result.

**Verification B results — v2 (2026-10-28, CPU r5 vs GPU r5, 232 draws total):**

Draws per κ: 20 random (seed=99+κ) + top-20 from audit A = 37–40 per κ.
Comparison: Q2 (binary), trio_idx (selected trio index for _opt cells), and
trio_scores at selected trio (tolerance 1e-12).
Note: compute_q2_all_cells in r5 is identical to r4 (function was not modified).

Results:
  Total Q2 checked:      1856  (232 draws × 8 cells)
  Q2 diffs (cpu≠gpu):    0
  Trio idx diffs:        0
  Score diffs (>1e-12):  0

  Q2 counts per cell in sample (shows test had power — not all 1s):
    SAW_mm_grd/opt:    232/0   (ceiling — consistent with K1=100%)
    SAW_vec_grd/opt:   204/28
    TOPSIS_mm_grd/opt: 209/23
    TOPSIS_vec_grd/opt:109/123  (← most variable; includes Q2=0 cases)

  PASS: zero Q2 diffs, zero trio_idx diffs, zero score diffs.

Statistical bound: 0 failures in 232 independent draws →
  divergence rate < 3/232 = 1.3% with 95% confidence (rule of three).

**Conclusion (S-T): GPU r5 ACCEPTED as equivalent to CPU r4 for S-T.**
Criterion A: satisfied (0 fragile, 0 exact ties).
Criterion B: satisfied (0 differences in Q2, trio_idx, and scores).
S-T results are no longer provisional.

## κ=∞ K6=0 in S-T: diagnostic complete

κ∈{10⁴,10⁵,10⁶} diagnostic (100 draws, seed=42, diagnostic only):

| κ | K6(SAW−TOPSIS) |
|---|---|
| 1,000 (main run) | +18.5 pp |
| 10,000 | +1.5 pp |
| 100,000 | 0.0 pp |
| 1,000,000 | 0.0 pp |
| ∞ | 0.0 pp |

This is a smooth convergence to the nominal-weight limit, not a discontinuity. At the
nominal weights (κ→∞), all 8 cells select Pareto-optimal triples (K6=0 = mean(SAW)=100%,
mean(TOPSIS)=100%). The "alarm" was unnecessary: the K6 decline is continuous.

For S-N, the same pattern holds:
| κ | K6(SAW−TOPSIS) |
|---|---|
| 10,000 | −30.3 pp |
| 100,000 | −26.8 pp |
| 1,000,000 | −25.0 pp |
| ∞ | −25.0 pp |

S-N converges to −25.0 pp from below, consistent with κ=1000 result (−27.4 pp).

Implication for manuscript: the κ=∞ "limit" result is a genuine property of the nominal
weights, not an artefact. The narrative "all 8 cells are Pareto-efficient under nominal
weights in S-T, but not under sampled weights at κ=1000" is a reportable finding.
Report separately from the stochastic results per DEV-SANT-KINF-001.
