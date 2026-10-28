# PRESPEC_E7_KAPPA — Amendment 1

**Status:** POST HOC. Committed before any E7 run.  
**Reason:** Decomposition of existing κ=50 vs κ=200 results (descriptive) shows the change
in the aggregation contrast is driven mainly by SAW (+15.0 pp) rather than TOPSIS (−5.8 pp),
and SAW/min–max/greedy improves with TV ≡ 0 (+11.6 pp). The TV(2) mechanism alone cannot
explain the SAW side.

## Decomposition of the Δ = 20.8 pp shift (κ=50 − κ=200 in 3-cell Agg†)

|   | κ=200 | κ=50 | Δ |
|---|---|---|---|
| Mean SAW (mm/grd + vec/grd + vec/opt)/3 | 69.7 | 84.7 | +15.0 |
| Mean TOPSIS same cells | 70.1 | 64.3 | −5.8 |
| **Contrast (SAW − TOPSIS)** | **−0.4** | **+20.4** | **+20.8** |

SAW/mm/greedy rises 97.6 − 86.0 = +11.6 pp with TV ≡ 0. This cannot be caused by amplitude
distortion. Two candidate mechanisms:

1. **Frontier-size effect**: Draws with lower κ have higher variance, leading to draws with
   extreme group weights and consequently smaller |F(w)|. A smaller frontier is easier to hit.
2. **Group-weight concentration**: With lower κ, more draws have one dominant group weight.
   The score becomes approximately lexicographic, reducing the conflict between optimising the
   score and being Pareto-efficient.

## Additions to E7 design (before first E7 run)

A1. Per draw, record:
    - `|F(w)|` = size of exact Pareto frontier
    - `H(w) = Σ_g W_g(w)²` = group-weight concentration (Herfindahl index)

A2. Q2 mechanism models gain two additional regressions per cell:
    - `miss ~ log κ + log|F(w)|`
    - `miss ~ log κ + H(w)`
    Report attenuation of the log κ coefficient when each covariate is added.

A3. Report the aggregation contrast decomposed into SAW and TOPSIS components at every κ
    (point estimates + paired bootstrap CI).

## Pre-declared readings

| Outcome | Label |
|---|---|
| `log|F(w)|` coefficient CI excludes 0 AND attenuation ≥ 50% | "frontier-size effect" |
| `H(w)` coefficient CI excludes 0 AND attenuation ≥ 50% | "concentration effect" |
| Otherwise | "unexplained" |

Both can be active simultaneously. Each is reported as confirmed/not-supported/partial
independently, regardless of the other.

## Gates (same as PRESPEC_E7_KAPPA, plus)

G4. SAW/mm/greedy Q2 at κ=200 replicates to within 0.5 pp of 86.0% (gate for this cell).
G5. |F(w)| computation agrees with the exact-enumeration count at κ=200 seed=42.

## Multiplicity

Two additional models × 8 cells × 6 κ = 96 regressions, all unadjusted, all descriptive.
