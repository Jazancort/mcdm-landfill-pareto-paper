# PRESPEC_E5 — Expanded Synthetic Grid for Generalisation (F4)

**Written:** 2026-10-02 (before results; E2/E3 results already known but E5 uses
different N, geometry and group structure — new estimands not contaminated by E2/E3)  
**Classification:** Pre-specified exploratory (estimands fixed before new runs)  
**Git:** to be committed before any E5 run is launched

---

## Research question

Is the relationship between within-group amplitude variation (TV_W) and greedy-assembly
Pareto efficiency (Q2_mm_greedy) monotonic and consistent across instances that differ
in:
1. Number of sites (N)
2. Spatial geometry
3. Group weight structure

This tests whether the Fogo result is a property of the mechanism (as the amplitude
identity predicts) or an artefact of the specific instance.

---

## Estimands (primary, fixed before results)

| ID | Estimand | Interpretation |
|----|----------|----------------|
| E5-P1 | slope dQ2_greedy/dTV_W across instances | Is TV_W a consistent predictor? |
| E5-P2 | Q2_mm_optimal = 100% on all instances | Regression invariant (Prop1) |
| E5-P3 | Fraction of instances where TV_W predicts >50% of Q2 variance | Generalisability metric |

**Stop/fail rule:** if slope CI includes 0 in >30% of N×geometry strata, conclude
TV_W is not a robust predictor and revise the narrative (TV_W is an instance-specific
observation, not a generalisable mechanism indicator).

---

## Design

### Factors

| Factor | Levels | Rationale |
|--------|--------|-----------|
| N (sites) | 50, 100, 200, 389 | Tests if mechanism holds at smaller instances |
| geometry | uniform, clustered, grid | Different spatial constraints on feasible trios |
| s_B (between-group) | 0.0, 0.5, 1.0 | Between-group amplitude variation |
| s_W (within-group) | 0.0, 0.25, 0.5, 0.75, 1.0 | Within-group amplitude variation |
| replicates | 3 per cell | Independent random seeds for site positions |

**Total instances:** 4 × 3 × 3 × 5 × 3 = 540

### Parameters

- N_draws = 200 per instance (±2.2pp Monte Carlo SE at Q2=50%)
- κ = 200 (consistent with main factorial)
- seed_base = 100 (+ instance index, deterministic)
- d_min: scaled proportionally to bounding box (10 km for N=389, adjusted for N<389)
- Group weights: W_G1=0.295, W_G2=0.356, W_G3=0.349 (same as AHP)
- 3 criteria per group (same M=9 structure, simplified from M=11)

### Site generation

```python
# Uniform: random uniform in [0, bbox] × [0, bbox]
# Clustered: 3 cluster centres, sites drawn from Gaussian(centre, sigma)
# Grid: regular grid with small jitter
# bbox set so median nearest-neighbour distance ≈ d_min/2
```

### Amplitude generator

Same power-law as E3:
```
A_j = Ag_bar(s_B) * (rho_j / Agbar_ref)^s_W
```
where rho_j = range(column_j) / ||column_j||_2 for each synthetic instance,
and Agbar_ref is the within-group mean amplitude.

---

## Regression model

Primary analysis: linear mixed model

```
Q2_greedy ~ TV_W + TV_B + log(N) + geometry + (1 | replicate)
```

Coefficient of TV_W is E5-P1. CI from bootstrap over instances (not draws).

---

## Output

- `results/e5/e5_grid_results.csv` — one row per instance
- `results/e5/e5_summary.csv` — aggregated by (N, geometry, s_B, s_W)
- Figure: Q2_greedy vs TV_W, coloured by N, faceted by geometry

---

## Decision rules

| Rule | Condition | Decision |
|------|-----------|----------|
| E5-R1 | All Q2_mm_optimal = 100% | Regression passes; proceed |
| E5-R2 | slope(TV_W) CI excludes 0 in ≥70% strata | TV_W is robust predictor |
| E5-R3 | slope(TV_W) CI includes 0 in >30% strata | TV_W not robust; revise narrative |
| E5-R4 | Any instance where Q2_mm_optimal < 99% | Pipeline bug; abort and debug |

---

## What E5 does NOT test

- TOPSIS vs SAW (not the question here)
- Real-world instance validity beyond Fogo
- Whether min-max is "better" in general

---

**Commit this file before launching any E5 run.**
