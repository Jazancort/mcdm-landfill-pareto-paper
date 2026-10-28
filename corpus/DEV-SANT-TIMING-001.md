# DEV-SANT-TIMING-001 — Timing run on Athena: what was computed and what was not recorded
Date: 2026-10-29
Type: pre-data transparency note (no Q2 values outside K1 were printed or saved)

## What happened

To measure per-draw timing before launching Stage 4 (PRESPEC §5: "timing medido"),
a test run was executed on Athena with `--timing` flag: 5 draws per κ, all κ values,
both branches, no results saved to disk.

Command: `uv run python -u scripts/run_santiago_mc.py --branch both --timing`
Commit: 0755358

## What the log showed (complete list)

For each branch and each κ value, the log printed ONLY:
1. Branch name, N_adm, n_trios, and trios-build time.
2. Per κ: total time for 5 draws (seconds) and K1 percentage: `K1(SAW/mm/opt)=100.0%`.
3. Timing summary: seconds/draw and estimated full run time.

No other Q2 values appeared in the log. No values for SAW_mm_grd, SAW_vec_grd,
SAW_vec_opt, TOPSIS_*, or any other cell were printed or written to disk.

The full timing log is archived at: results/santiago/timing_log_2026-10-29.txt

## What was computed in RAM (not recorded)

The --timing branch calls `compute_q2_all_cells()` which computes Q2 for all 8 cells
in memory. These values were computed (necessary for K1 extraction) but:
- Were never printed (only K1 was extracted from the result dict).
- Were never saved (timing_only=True skips the np.savez checkpoint call).
- Were discarded after each draw iteration.

The actual seeds from gen_santiago_seeds (parent seeds 1,4,15,17,28,30) were used
for the 5 stochastic draws per κ. Each κ consumed 5 draws from the child generators.

## Pre-registration implications

K1 = 100% at all κ for both branches is an implementation check, not a scientific
finding. It means the greedy/optimal trio-selection code is working correctly.
It does not reveal the direction or magnitude of normalisation effects (K3-K6,
S1-S7). This is the same type of check as the Fogo S0 regression gate.

The fact that Q2 for non-K1 cells was computed in RAM is similar to the situation
where a randomisation check reveals that the data structure is valid — it does not
reveal results of the randomised experiment.

## Seed state after timing run

The timing run consumed 5 draws per κ from the child generators. For the full Stage 4
run (500 draws per κ), the draws will start from draw 0 (not draw 5) because each
`get_branch_rngs(kappa)` call creates a NEW child generator by calling
`SeedSequence(parent_seed).spawn(2)`. The timing run's generators were ephemeral
(created in the timing_only run and then discarded). The full run starts fresh.

## Conclusion

The timing run qualifies as: "5 draws per κ per branch, only time and K1 recorded."
No scientific result from Stage 4 was seen or could have influenced any decision.
This note is recorded to make the information available for any reviewer who asks.
