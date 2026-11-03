# DEV-SANT-K6-001 — K6 (SAW–TOPSIS aggregation contrast): 4-cell vs 3-cell definition
Date: 2026-11-03
Type: post-data implementation discrepancy (discovered during S4 analysis, 2026-11-03)
Discovered by: user analysis of Santiago S4 table, verified against Fogo E7 scripts

## PRESPEC declaration

PRESPEC_SANTIAGO_A5 §3 (K6) states:

> "Report the pooled SAW–TOPSIS contrast (mean of **informative-cell** Q2 values,
>  SAW minus TOPSIS) at each κ, with 95% CI from bootstrap."
> "K6 corresponds to the aggregation row of the Fogo E7 table (§7.10)"

The Fogo E7 reference (run_e7_kappa_sweep.py, line 344):

```python
"Agg_pooled3": (1/3)*((C("saw","minmax","greedy")  - C("topsis","minmax","greedy"))
                     +(C("saw","vector","greedy")   - C("topsis","vector","greedy"))
                     +(C("saw","vector","optimal")  - C("topsis","vector","optimal")))
```

The "3" in Agg_pooled3 refers to three cells: mm_grd, vec_grd, vec_opt.
The cell mm_opt is excluded because SAW_mm_opt = 100% in all draws (Proposition 1),
making its SAW-TOPSIS contrast a mechanical consequence of the theorem rather than
an informative measure.

## What the Santiago script computed

run_santiago_mc.py (lines 1341–1345):

```python
saw_mean    = grp[["SAW_mm_grd","SAW_mm_opt","SAW_vec_grd","SAW_vec_opt"]].values.mean() * 100
topsis_mean = grp[["TOPSIS_mm_grd","TOPSIS_mm_opt","TOPSIS_vec_grd","TOPSIS_vec_opt"]].values.mean() * 100
k6_info[kappa] = round(saw_mean - topsis_mean, 2)
```

This uses all 4 cells, including mm_opt.

## Verification that Agg_pooled3 ≡ 3 cells (mm_grd, vec_grd, vec_opt)

At κ = 200, Fogo (from regret_aggregate.csv, S4 cells):
- SAW_mm_grd − TOPSIS_mm_grd = −8.4 pp
- SAW_vec_grd − TOPSIS_vec_grd = +2.8 pp
- SAW_vec_opt − TOPSIS_vec_opt = +4.4 pp
- Agg_pooled3 = (−8.4 + 2.8 + 4.4) / 3 = **−0.4 pp** ← matches E7 table entry

With 4 cells (including SAW_mm_opt ≈ 100% > TOPSIS_mm_opt):
- 4-cell mean would be (−8.4 + 3.4 + 2.8 + 4.4) / 4 = +0.55 pp ← does NOT match

## Direction of effect

Excluding mm_opt reduces the SAW contribution by removing a cell where SAW = 100%
by construction. Effect on K6:

- S-T: including mm_opt inflates saw_mean because SAW_mm_opt ≈ 100% at all κ.
  4-cell K6 underestimates |Agg_pooled3| when TOPSIS_mm_opt < 100%.
- S-N at high κ: SAW_mm_opt ≈ 100% but greedy cells fall heavily, making the
  difference between 3-cell and 4-cell versions larger as κ increases.

## Corrected K6 values (user computation, 2026-11-03; to be confirmed by eval script)

S-T:
| κ   | 4-cell (log) | 3-cell (corrected) |
|-----|-------------|-------------------|
| 25  | +19.5       | +22.1             |
| 50  | +23.0       | +26.4             |
| 100 | +19.7       | +23.9             |
| 200 | +20.5       | +26.2             |
| 400 | +18.5       | +23.8             |
| 1000| +18.5       | +24.1             |

S-N:
| κ   | 4-cell (log) | 3-cell (corrected) |
|-----|-------------|-------------------|
| 25  | +5.9        | +7.5              |
| 50  | +3.7        | +4.7              |
| 100 | −1.7        | −2.6              |
| 200 | −8.7        | −11.9             |
| 400 | −16.9       | −22.5             |
| 1000| −27.4       | −36.5             |

Fogo (E7, Agg_pooled3):
| κ   | 3-cell       |
|-----|-------------|
| 25  | +21.1       |
| 200 | −0.4        |
| 1000| −9.0        |

The qualitative pattern (positive S-T, sign reversal in S-N) is unchanged. The
magnitude changes, and the Fogo comparison now uses the same definition in both cases.

## K5 implication

A5 §3 K5 (b) reads: "whether the pooled SAW–TOPSIS aggregation contrast (informative cells)
has the same sign in both cases." The parenthetical "(informative cells)" refers to
Agg_pooled3. The K5 (b) check in the evaluation script must also use 3 cells.

## Fix

The sealed CSV files contain all 8 cells per draw. No MC re-run is required.

Fix in evaluate_santiago_predictions.py (to be applied before tag predictions-eval-v2):

```python
# K6: 3 informative cells (mm_grd, vec_grd, vec_opt) — matches Fogo Agg_pooled3
for kappa, grp in df8.groupby("kappa"):
    saw_3inf    = grp[["SAW_mm_grd",    "SAW_vec_grd",    "SAW_vec_opt"]].values.mean() * 100
    topsis_3inf = grp[["TOPSIS_mm_grd", "TOPSIS_vec_grd", "TOPSIS_vec_opt"]].values.mean() * 100
    k6_info[kappa] = round(saw_3inf - topsis_3inf, 2)
```

Same fix for K5 (b).

## Reporting

In §7: the 4-cell values from the MC log (run_santiago_mc.py output) are superseded
by the 3-cell values. The 4-cell version is not reported. The comparison between
Santiago and Fogo uses Agg_pooled3 in both cases.

## Source

PRESPEC_SANTIAGO_A5 §3 K6: "corresponds to the aggregation row of the Fogo E7 table (§7.10)"
Fogo E7: run_e7_kappa_sweep.py line 344 (Agg_pooled3 = 3-cell mean)
Santiago MC: run_santiago_mc.py lines 1341–1345 (4-cell mean — WRONG)

## A5 citation (confirms 3-cell interpretation)

PRESPEC_SANTIAGO_A5 §3 K6 (verbatim):

> "Report the **pooled SAW–TOPSIS contrast (mean of informative-cell Q2 values**, SAW minus
>  TOPSIS) at each κ, with 95% CI from bootstrap. Report sign changes, monotonicity, and
>  TOST result at each κ. No directional prediction is made. **K6 corresponds to the
>  aggregation row of the Fogo E7 table (§7.10)**; the sign reversal observed in Fogo was
>  unexplained theoretically and is registered here as exploratory only."

"Informative-cell" = cells where the SAW Q2 is not 100% by theorem. SAW_mm_opt = 100% by
Proposition 1 in every draw. Including it would inflate saw_mean mechanically. The A5 phrase
"informative cells" unambiguously refers to Agg_pooled3 (3 cells). This is an implementation
error, not an ambiguity.

## Gate: reproduce Fogo Agg_pooled3 values

Before reporting any Santiago K6 value, the evaluation script must reproduce the 6 Fogo
reference values using the same 3-cell formula on the Fogo mc_unified_raw.csv:

| κ   | Expected Agg_pooled3 |
|-----|---------------------|
| 25  | +21.1 pp            |
| 50  | +20.4 pp            |
| 100 | +9.3 pp             |
| 200 | −0.4 pp             |
| 400 | −5.7 pp             |
| 1000| −9.0 pp             |

Tolerance: ≤ 0.1 pp (one half-unit in the reported decimal). Abort if any value fails.

## K5(b): same fix required

K5 (b): "whether the pooled SAW–TOPSIS aggregation contrast (informative cells) has the
same sign in both cases" (A5 §3 K5).

With 3-cell formula, κ=∞ values (one draw each):
- S-T: (0 + 0 + 0)/3 = 0.0 pp → sign indeterminate (zero)
- S-N: (SAW_mm_grd − TOPSIS_mm_grd + SAW_vec_grd − TOPSIS_vec_grd + SAW_vec_opt − TOPSIS_vec_opt)/3

At κ=∞, S-N greedy cells: SAW_mm_grd=0 (user verified), SAW_vec_grd=0.
SAW_vec_opt=1, TOPSIS_vec_opt=1 → vec_opt diff = 0.
Then Agg_pooled3 ≈ (−100 + −25 + 0)/3 = −41.7 pp. User computed −33.3; verify.

K5(b) sign consistent in S-N (both κ=1000 and κ=∞ are negative). S-T sign is indeterminate
at κ=∞ (zero result). Report as: "consistent where defined (S-N); undefined at κ=∞ S-T."

## Log note: 4-cell values sealed

The MC log (run_santiago_mc.py output) contains the 4-cell K6 values. These are not reported
in the paper. The log is not modified. The table in §7 uses the 3-cell (Agg_pooled3) values,
computed in evaluate_santiago_predictions.py from the sealed CSV cells.
