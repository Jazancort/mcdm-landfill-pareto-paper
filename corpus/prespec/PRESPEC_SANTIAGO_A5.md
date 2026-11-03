# PRESPEC_SANTIAGO — Amendment A5: weight-dispersion (κ) grid

```
Status:     pre-registered before any Santiago criterion value, score, frontier or Q2 exists.
Parent:     PRESPEC_SANTIAGO.md, frozen at tag prespec-santiago-f0-amend-final
            (commit 06fc1e76a3e33a2d6aaa069936cc6552918c6026).
Written:    2026-10-27
```

Motivation: the Fogo E7 sweep (PRESPEC_E7_KAPPA, A1–A2) showed that factorial contrasts
depend on κ. The parent document registers κ = 200 only. This amendment extends the
confirmatory scope to a κ grid. It does not modify any parent prediction S0–S7.

**Non-access declaration:**
As of the date of this commit, no criterion value, normalised score, amplitude, distance,
frontier, or Q2 for Santiago has been extracted, computed, or inspected in either branch
S-T or S-N. This amendment modifies parameter declarations only.

---

## 1. Fixed parameters (both branches S-T and S-N unless stated)

- **κ values:** {25, 50, 100, 200, 400, 1000} (stochastic) and κ = ∞ (deterministic: w = w0).
- **w0:** S-T = Fogo AHP weights (`fogo_constants.py`); S-N = Cabral (2012) leaf weights
  (PRESPEC_SANTIAGO.md Annex C).
- **Draws:** 500 per κ. Seed convention identical to PRESPEC_E7_KAPPA_A2
  (section "Seeds confirmation — clarification to PRESPEC_E7_KAPPA §2"):
  - κ = 200: S-T reuses `e1_weights_k200.npy` (seed 42; `rng(42).dirichlet(200·w0_Fogo, 500)`);
    S-N uses `rng(42).dirichlet(200·w0_Cabral, 500)` (independent stream, seed 42).
  - κ = 50: S-T reuses `e1_weights_k50.npy` (seed 42; `rng(42).dirichlet(50·w0_Fogo, 500)`);
    S-N generates fresh with seed 150 (`rng(150).dirichlet(50·w0_Cabral, 500)`).
  - Other κ (25, 100, 400, 1000): seed = BASE_SEED + κ, where BASE_SEED = 100.
    S-T reuses the E7 weight files where they exist; S-N generates fresh streams with the
    same BASE_SEED + κ rule applied to w0_Cabral.
  - The DEV-E7-001 error (seed 43 for κ = 50 in E7 v1/v2) must not repeat: verify seed
    loading before any Stage 4 run.
- **Portfolio:** k = 3 sites; d_min = 10 km (previously implicit in parent; fixed here).
- **Enumeration:** parent spacing rule unchanged — 1 km start; ±0.25 km steps;
  bounds 0.5–5 km; 10 000 ≤ |T| ≤ 50 000 000; abandonment rules unchanged.
  Spacing is determined from |T| alone before any weight draw is scored.
- **Cells:** the 2³ factorial (SAW/TOPSIS × mm/vec × greedy/opt) at every κ.
  E1 cells M, B, W, V at κ = 200 and κ = ∞ only (the parent pipeline κ and the limit).
- **Objectives:**
  - S-T: three group objectives F1–F3 (groups G1–G3, Fogo partition; PRESPEC_SANTIAGO §4.5).
    Frontier is 3-dimensional.
  - S-N: four group objectives F_A–F_D (groups A–D, Cabral partition; PRESPEC_SANTIAGO §5.6:
    A = {A1–A7}, B = {B1–B3}, C = {C1–C2}, D = {D1–D2}). Frontier is 4-dimensional.
  Theorem 1 and Proposition 1 hold for any criterion-to-group partition (proof unchanged).
- **Bootstrap:** B = 2000, paired by draw within κ. Equivalence margin Δ = 2.5 pp
  (TOST, α = 0.05 each side, 90% CI criterion; same as PRESPEC_E7_KAPPA_A2).
- **Assomada (A/A1):** primary P-C classification = Intermédia (two independent research
  summaries of Gomes 2007 agree; page in original thesis not yet confirmed due to SSL).
  SENS-6 activates if source verification yields Recente. This decision is fixed before
  data extraction and applies to both S-T (P-F rule unaffected) and S-N (B1 scoring).

---

## 2. Predictions (each tested separately in S-T and in S-N)

Parent predictions S0–S7 retain their original definitions at κ = 200 and are not
modified by this amendment.

**K1 — Implementation check (abort branch if failed)**
SAW/min–max/optimal attains Q2 = 100% at every κ (stochastic and deterministic).
This is a consequence of Proposition 1 (any weight draw gives an admissible score-optimal
portfolio on the frontier). Failure indicates a scoring or enumeration bug; abort before
reporting any other cell.

**K2 — Theorem 1 at κ = 200 and κ = ∞**
E1 cell B (between-group distortion only, TV_W = 0) attains Q2 = 100% under optimal
assembly at both κ = 200 and κ = ∞. These are the two κ values at which cell B is
computed. Failure at κ = 200 is a regression failure (covered by S0); failure at κ = ∞
is a new check added here.

**K3 — Normalisation contrast never reverses sign (confirmatory)**
For no κ in the stochastic grid {25, 50, 100, 200, 400, 1000} is the 95% CI of the
greedy normalisation contrast (Q2(SAW, mm, greedy) − Q2(SAW, vec, greedy)) entirely
below zero. Evaluated per κ individually, without multiplicity adjustment (evaluating
each interval is strictly conservative for the overall "never reverses" claim). A single
κ with a CI entirely below zero falsifies K3.

**K4 — Normalisation is detectable at some κ (confirmatory)**
For at least one κ in the stochastic grid the greedy normalisation contrast is
significantly positive after Holm correction across the six stochastic κ values
(one-sided test: H0: contrast ≤ 0; reject if lower 95% CI bound > 0 after adjustment).

Note on K3/K4 relationship: K3 is a global claim (no reversal at any κ) and K4 is an
existence claim (detectable positive contrast at some κ). Both can be confirmed
simultaneously; confirming K3 does not imply K4.

**K5 — Descriptive check of the high-κ reading (descriptive)**
At κ = 1000 and κ = ∞ report:
(a) whether the vector-assembly effect (Q2(SAW, vec, opt) − Q2(SAW, vec, grd)) has the
    same sign in both cases;
(b) whether the pooled SAW–TOPSIS aggregation contrast (informative cells) has the same
    sign in both cases.
The Fogo E7 result was: assembly contrast at κ = 1000 ≈ −12 pp (same sign as κ = ∞),
aggregation contrast at κ = 1000 ≈ −6 pp (same sign as κ = ∞, near zero). K5 checks
whether these signs replicate in Santiago without predicting the magnitudes.
K5 is purely descriptive; no CI test, no confirmation criterion.

**K6 — SAW–TOPSIS aggregation contrast across κ (exploratory, descriptive only)**
Report the pooled SAW–TOPSIS contrast (mean of informative-cell Q2 values, SAW minus
TOPSIS) at each κ, with 95% CI from bootstrap. Report sign changes, monotonicity, and
TOST result at each κ. No directional prediction is made. K6 corresponds to the
aggregation row of the Fogo E7 table (§7.10); the sign reversal observed in Fogo was
unexplained theoretically and is registered here as exploratory only.

---

## 3. Multiplicity and reporting

- **Families for Holm correction:** {K3, K4} form one family per branch; Holm applies
  within K4 only (six κ values, one test per κ). K1 and K2 are implementation checks.
  K5 and K6 are descriptive (no adjustment).
- All K-predictions are reported whether confirmed or not, in a prediction table generated
  by script (output: `macros_santiago.tex`). No prediction may be dropped or redefined
  after Stage 3.
- Parent predictions S0–S7 retain their definitions at κ = 200.

---

## 4. Stage gates (no stage begins before the previous stage's commit is on the remote)

**Stage 1 — Regression:** the frozen pipeline (commit 94b5baf, PRESPEC_SANTIAGO §3) run
on Fogo reproduces Table 5 and passes all 22 E7 gates. SHA-256 verification against the
four reference files listed in PRESPEC_SANTIAGO §3 Common pipeline. Abort if any mismatch.

**Stage 2 — Data extraction:** extract all Santiago criterion values. Aspect computed via
`arctan2(−dx, dy)` from ASTER GDEM v3 (correct formula; `aspect_utils.py`; Rule 4b declared
in PRESPEC_SANTIAGO §3). Tolerance regression on 389 Fogo admissible sites: max|Δ| ≤ 1e−4°,
zero classification changes — same criterion as amend-final. Geotransform asserts required
(PRESPEC_SANTIAGO §3, step 4). Commit data files with SHA-256. No Q2, R, or portfolio
computed at this stage.

**Stage 3 — Deterministic descriptors:** compute A_j, w_eff, TV, TV_B, TV_W, m_eff, |T|,
and final spacing for each branch. Run unsaved timing estimate (one κ, both branches) to
project Stage 4 cost. Commit descriptor file before Stage 4. The conditional sign in K5
(sign(assembly effect at κ = 1000) vs sign at κ = ∞) is resolved here from the descriptors,
not from MC results.

**Stage 4 — Monte Carlo:** full κ grid on Athena; automated gates K1 and K2; full
prediction report generated by script. If cost exceeds Athena capacity, the only
permitted response is to invoke the pre-registered spacing rule (increase spacing in
0.25 km steps until |T| ≤ 50 000 000) and log as a deviation if spacing changes from
Stage 3 value. No post-data choice of spacing or κ subset is permitted.

---

## 5. Deviations

Any departure from §1–§4 after the commit of this amendment is logged as DEV-SANT-xxx
with date, reason, and expected direction of effect, before the affected analysis runs
where possible. Pre-declared contingencies C-1 through C-9 in the parent document are
not deviations; they are logged as contingency activations.

---

## Amendment changelog entry (to be added to PRESPEC_SANTIAGO.md §Amendment changelog)

| Tag | Commit | Date (UTC) | What was changed |
|---|---|---|---|
| `prespec-santiago-a5` | `475c3eb` | 2026-10-27 | κ grid {25,50,100,200,400,1000,∞}; predictions K1–K6; d_min = 10 km fixed; S-N objectives 4D confirmed; seed convention from E7_KAPPA_A2; Assomada rule fixed pre-data |
