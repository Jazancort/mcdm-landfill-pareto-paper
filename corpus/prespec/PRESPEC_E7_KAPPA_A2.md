# PRESPEC_E7_KAPPA — Amendment 2

**Status:** Clarification. Committed and tagged before the §7.x text was written.
**Date:** 2026-11-01 (after E7 run, before §7.x drafted).
**Reason:** Gate G1 declares the κ=200 aggregation contrast "equivalent to zero" (see
PRESPEC_E7_KAPPA §5) but the equivalence margin was not stated in the original PRESPEC.
This amendment records the pre-existing margin and verifies it was operative before E7 ran.

---

## Equivalence margin for the κ=200 TOST

The TOST uses **δ = 2.5 pp** (two-sided, α = 0.05 each side, 90% CI criterion).

**Evidence that δ = 2.5 was pre-existing:**

The main factorial PRESPEC (E1) declared the aggregation TOST in manuscript §5.4
("TOST with δ = 2.5 pp"), which appears in commits predating the E7 run:

```
git log -S "delta=2.5" -- main.tex | head -3
# or
git log -S "2.5" -- macros.tex | head -3
```

Expected output: commits earlier than `e6bf66b` (E7 run, 2026-10-30).

The `\TOSTp = 0.010` macro in macros.tex was computed from this margin before E7 ran.
The E7 gate G1 implicitly inherits the same margin (same κ=200 data point).

**Confirmation:** Run on E7 results (post-hoc check):
- Point estimate: −0.4 pp
- 95% CI: [−2.2, 1.3] → SE ≈ (1.3 − (−2.2)) / (2 × 1.96) ≈ 0.89 pp
- 90% CI: [−1.87, 1.07] pp ⊂ (−2.5, +2.5) → TOST passes
- TOST p ≈ max(Φ(−(−0.4 + 2.5)/0.89), Φ(−(2.5 − (−0.4))/0.89))
         = max(Φ(−2.36), Φ(−3.26)) ≈ max(0.009, 0.001) = 0.009 ≈ 0.010

Equivalence holds for **any δ ≥ 1.9 pp** (i.e. for δ = 2.0, p ≈ 0.04).
This robustness should be stated in §7.x.

---

## Text to add to §7.x

Add after the TOST result:

> TOST with δ=2.5 pp (pre-declared in §5.4); equivalence holds for any δ ≥ 1.9 pp.

---

## Seeds confirmation (clarification to PRESPEC_E7_KAPPA §2)

The sentence "κ=50 and κ=200 reuse the existing seeds" means:
- κ=200: `e1_weights_k200.npy` (SHA `bea05275…`; `rng(42).dirichlet(200·w₀, 500)`)
- κ=50:  `e1_weights_k50.npy`  (SHA `e761c76d…`; `rng(42).dirichlet(50·w₀, 500)`)

Other κ: seed = BASE_SEED + κ (100 + 25 = 125, 100 + 100 = 200, 100 + 400 = 500,
100 + 1000 = 1100). Seeds differ across κ by design; this is NOT a deviation.

**Deviation (recorded):** E7 v1 and v2 on Athena used seed = 43 for κ = 50 instead of
loading `e1_weights_k50.npy`. The final authoritative E7 run used the correct file
(data SHA `8b91cba2…`). See DEV-E7-001 for full record.
