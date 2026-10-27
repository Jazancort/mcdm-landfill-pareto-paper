# PRESPEC_E7_KAPPA — Sensitivity of factorial contrasts to weight-draw dispersion

**Status:** POST HOC. Motivated by Table 6 (κ=50 vs κ=200); results already seen for those two κ values.
Committed and tagged before any new E7 run. All E7 results are descriptive.

**Committed:** before any E7 run.
**SHA-256 verification:** record the SHA of this file in TASKS.md before running.

---

## 1. Questions

Q1. How do the six Table 6 contrasts vary with κ?
Q2. Is the κ-dependence of the aggregation contrast consistent with TOPSIS's
    approximately quadratic re-weighting (w_eff ∝ w²A², Remark 3)?

---

## 2. Design

- **Cells:** the 8 cells of the balanced 2³ (code path and commit identical to Table 5/6: `<hash before run>`).
- **Space:** A′, d_min = 10 km; frontier F(w) recomputed per draw (w_sc = w_ob = w_fr = w).
- **κ values:** {25, 50, 100, 200, 400, 1000}; plus w = w_AHP (κ → ∞) as a deterministic point.
- **Draws:** 500 draws per κ; within each κ, the same 500 draws are shared by all 8 cells (paired contrasts).
- **Seeds:** κ=50 and κ=200 reuse the existing seeds (gate checks). Other κ: seed = `<base> + κ`.
- **No weight floor.** Report min_j w_j per draw; flag draws with min_j w_j < 1e-4
  (relevant at κ=25, where κ·w_roads = 0.75 < 1).

---

## 3. Outcomes

- Per cell × κ: Q₂, Q₃, R (with SE).
- Per κ: the six Table 6 contrasts, 2,000-replicate paired percentile bootstrap, 95% CI.
- **Main display:** contrasts vs κ (log axis) with CI bands; κ=200 marked as primary.

---

## 4. Mechanism analysis (Q2)

For each draw, compute TV(1)(w) and TV(2)(w):

TV(2)(w) = ½ Σ_j |w_j² A_j² / Σ_k w_k² A_k² − w_j|

with A_j = 1 (min–max) and A_j = ρ_j (vector).

- **Model:** logistic regression of the TOPSIS miss indicator 1 − 1[M(w) ∈ F(w)]
  on log κ, fitted separately for the TOPSIS min–max and vector cells;
  then add TV(2)(w). Report the attenuation of the log κ coefficient (bootstrap CI).
- **Control:** SAW min–max greedy (TV(1) ≡ 0, so the loss is purely combinatorial).

**Pre-declared reading:**

| Label | Criterion |
|---|---|
| "consistent" | TV(2) coefficient > 0 with CI excluding 0 AND attenuation ≥ 50% |
| "not supported" | TV(2) coefficient CI includes 0 |
| "partial" | otherwise |

---

## 5. Gates (must pass before any reporting)

G1. κ=200 and κ=50 reproduce Tables 5–6 to the reported precision.
G2. SAW/min–max/optimal: Q₂ = 100% at every κ (Proposition 1).
G3. 500 valid draws per κ; any failure is reported as a deviation.

**Equivalence margin:** The aggregation contrast is declared equivalent to zero at κ=200 using
TOST with δ=2.5 pp (matching the pre-declared margin in §5.4 of the manuscript). The 90%
bootstrap CI must lie entirely within (−2.5, +2.5) pp.

---

## 6. Multiplicity and reporting

36 intervals (6 contrasts × 6 κ), unadjusted, descriptive. All results are
reported whatever their direction. Deviations are logged as DEV-E7-xxx.

---

## 7. Placement

New §7.x "Dependence on weight dispersion"; Table 5 gains κ=50 columns (main text);
full grid in the Supplement; macros auto-generated in `macros_e7.tex` with checker rules.

---

## 8. Cost

F(w) depends only on w and is shared by the 8 cells: 6 × 500 = 3,000 frontier
computations (κ=50 and κ=200 are reruns that serve as gates).
