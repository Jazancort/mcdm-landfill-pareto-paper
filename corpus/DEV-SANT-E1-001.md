# DEV-SANT-E1-001: E1 cells evaluated against amplitude-specific frontier instead of mm-frontier

```
Status:      OPEN — corrective run not yet executed
Type:        Implementation error (post-PRESPEC, pre-data; undocumented)
Discovered:  2026-10-29 (after seeing all E1 cells at 100% in both branches)
Written:     2026-10-29
```

## What happened

Commit `67a71b8` (2026-10-28 07:36:33), message:
"fix(stage4): greedy/optimal selectors corrected; Q2 uses mm frontier for all 8 cells; E1 uses amplitude-specific frontier"

The commit explicitly set the E1 cells to use their own amplitude-specific Pareto frontier
for the Q2 and R computations, instead of the mm-frontier used in the Fogo E1 experiment.

Affected code in `run_santiago_mc.py` (CPU path):

```python
# WRONG (committed version)
F_e1_trios = compute_trio_objectives(F_e1_site, trios)  # E1-specific frontier
q2_opt = 0 if check_dominated_raw(F_e1_trios, F_e1_trios[tidx_opt]) else 1
```

Same pattern in GPU path (`compute_e1_cells_gpu`):

```python
# WRONG (committed version)
F_site_gpu, F_e1_trios_gpu = _f_trios_gpu(...)
q2_opt = 0 if _check_dom_gpu(F_e1_trios_gpu, F_e1_trios_gpu[tidx]) else 1
```

## Why this is wrong (PRESPEC evidence)

**PRESPEC_SANTIAGO.md lines 274–278 (literal):**

> "E1 cells M, B, W, V (definitions as Fogo §7.7, with Santiago's own rho_j and groups)."
>
> "**Frontier:** exact enumeration; dominance tolerance eps = 1e-9; `validate_core` checks pass
> (non-dominance and completeness) before any Q2."

One frontier is defined for all metrics. No E1-specific frontier is mentioned in
PRESPEC_SANTIAGO.md, PRESPEC_SANTIAGO_A5.md, A5a, A5b, or in any DEV file (grep confirmed).

"Definitions as Fogo §7.7" references the Fogo E1 experiment, which used mm-frontier.
Confirmed by `results/e1/e1_macros.tex` (auto-generated from Fogo data):

```
QtwoEoneWOpt = 64.2%   (against mm-frontier; not 100%)
QtwoEoneVOpt = 56.8%   (against mm-frontier; equal to QtwovecOptimal = 56.8%)
```

S3a predicts "E1-W optimal < 100% and E1-V optimal < 100%". Against amplitude-specific
frontier, the argmax is always on its own frontier (Theorem 1), so Q2_opt = 100% trivially.
This makes S3a non-falsifiable under the committed code; it is a real empirical prediction
only against the mm-frontier.

**The decision was not documented.** Commit `67a71b8` was made after `prespec-santiago-a5`
(tag, 2026-10-27) and before `stage4-launch-r3` (09:13, 2026-10-28), during pre-launch
code iteration. No DEV was filed. The phrase "amplitude-specific frontier" does not appear
in any PRESPEC or DEV file.

## Why this was not detected

- The K2 gate (E1-B optimal Q2 = 100%) PASSED. Under amplitude-specific frontier, K2 passes
  trivially for all cells by Theorem 1, not just E1-B. The PRESPEC intent is that K2 tests
  whether E1-B is on the mm-frontier (which it is, because TV_W = 0 means E1-B group
  objectives are a positive rescaling of mm group objectives — same Pareto set). Against
  amplitude-specific frontier, K2 is vacuous.
- The CPU/GPU equivalence validation (DEV-SANT-GPU-001) compared the 8 main cells only.
  E1 cells were not part of the A+B comparison.
- The error was discovered only after observing that all four E1 cells (M, B, W, V) showed
  Q2_opt = 100% in both branches, which is impossible under mm-frontier for E1-W and E1-V
  (Fogo: 64.2% and 56.8% respectively).

## Effect on sealed files

- `mc_ST_raw.csv` (SHA 123a5421) and `mc_SN_raw.csv` (SHA dbfa2f00): **not affected**.
  These contain the 8 factorial cells, which use mm-frontier correctly.
- `mc_ST_e1.csv` (SHA c074d3d0) and `mc_SN_e1.csv` (SHA 20b991c4): **affected**.
  Q2_opt = 100% for all E1 cells in both branches is an artefact of the wrong frontier.

K2 in the sealed log: PASSED vacuously (not a real test under the committed code).
The K2 pass does not validate Theorem 1 for Santiago in the sealed run.

Affected verdicts from `santiago_predictions.json`: S3a, S3b, S7a, S7b are invalid.
Unaffected: S0, S1, S2, S4, S5, K1, K3, K4, K5, K6.

## Correction

The correct code checks the E1 portfolio's mm-group objectives against the mm-frontier.
`F_mm_trios` and `F_mm_site` are already available per draw in both CPU and GPU paths
(used for the 8 main cells). The correction:

1. Select the E1-optimal portfolio using the E1 score (unchanged).
2. Evaluate that portfolio's mm-group objectives (A_j = 1) against F_mm_trios.

CPU path fix:

```python
# CORRECT
tidx_opt = optimal_selector(sc_opt, trios)
trio_opt = trios[tidx_opt]
f_mm_opt = (F_mm_site[trio_opt[0]] +
            F_mm_site[trio_opt[1]] +
            F_mm_site[trio_opt[2]])
q2_opt = 0 if check_dominated_raw(F_mm_trios, f_mm_opt) else 1

trio_grd = greedy_selector(sc_opt, data["D"])
f_mm_grd = (F_mm_site[trio_grd[0]] +
            F_mm_site[trio_grd[1]] +
            F_mm_site[trio_grd[2]])
q2_grd = 0 if check_dominated_raw(F_mm_trios, f_mm_grd) else 1
```

GPU path: select trio using E1 GPU score; then look up that trio's mm-objectives
from `F_mm_site_gpu` (already computed in the GPU path) and check against the
mm Pareto frontier.

## Acceptance criteria for the corrective run

Santiago proceeds only if all three gates pass in sequence:

**Gate 1 — Fogo regression (exact to half the last decimal place):**
Apply corrected code to Fogo data with Fogo E1 weights (e1_weights_k200.npy,
SHA bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487).

Required results (from e1_macros.tex):

| Cell | Q2_opt |
|------|--------|
| E1-M | 100.0% |
| E1-B | 100.0% |
| E1-W | 64.2%  |
| E1-V | 56.8%  |

E1-V must equal QtwovecOptimal (56.8%) exactly, since E1-V uses A_j = rho_j
(same as vec normalization).

**Gate 2 — Internal consistency (Santiago, exact):**

- E1-M opt = 100.0% (mm normalization, by Proposition 1).
- E1-B opt = 100.0% (Proposition 1: TV_W = 0; this is now a real check).
- E1-V opt at kappa=200 must equal SAW_vec_opt from the sealed mc_ST_raw.csv / mc_SN_raw.csv
  draw-for-draw.

**Gate 3 — Main cells SHA preserved:**
Full Stage 4 run with corrected code. mc_ST_raw.csv and mc_SN_raw.csv must have
the same SHA-256 as the sealed files (SHA 123a5421 and dbfa2f00 respectively).
This proves the correction does not affect the 8 main cells.

## Reporting

Both runs are reported in the manuscript.

The sealed run: "The initial Stage 4 run (tag stage4-results-sealed) contained an
implementation error in the E1 cell computation (DEV-SANT-E1-001): E1 portfolios were
evaluated against an amplitude-specific Pareto frontier rather than the mm-frontier
used in the Fogo E1 experiment. Under this error, all four E1 cells reported Q2_opt = 100%
trivially (Theorem 1). Results for S3a, S3b, S7a, S7b from the sealed run are invalid.
The corrective run (tag stage4-e1fix-sealed) is the primary result for these predictions."

The 8 main cells and K1–K6 are unchanged and are cited from the original sealed run.

## Tags

- `stage4-results-sealed`: original run (E1 values invalid for S3a, S3b, S7a, S7b)
- `stage4-e1fix-sealed`: corrective run (to be created after gates pass)

## Expected direction (declared before corrective run)

Based on Fogo analogy. Not predictions; direction only.

- E1-W opt: expected below 100% (Fogo: 64.2% at kappa=200)
- E1-V opt: expected below 100% (Fogo: 56.8% at kappa=200)
- E1-V opt < E1-W opt: expected (Fogo: 56.8% < 64.2%)
- S3a: expected to confirm
- S3b: expected to confirm

No magnitude predictions are made for Santiago.
