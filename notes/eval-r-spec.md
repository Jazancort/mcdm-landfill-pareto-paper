# EVAL-R Specification

> **NOTA DE PRÉ-REGISTO**: Este documento é uma especificação de implementação escrita
> em 2026-11-03, DEPOIS dos dados estarem selados (mc_ST_e1_fix2.csv e mc_SN_e1_fix2.csv,
> commits em 2026-10-29). NÃO é um pré-registo. O texto pré-registado é
> `PRESPEC_SANTIAGO.md` (tag `prespec-santiago-f0-amend-final`, 2026-10-26).
>
> Qualquer condição neste documento que VAI ALÉM do texto congelado do PRESPEC
> está identificada com `[POST-DATA]`. Essas condições são escolhas de implementação,
> não compromisos pré-registados. Ver tabela em DEV-SANT-EVALR-001.md §ER-POST.

Pre-commit: 2026-11-03 (tagged predictions-eval-v2)
Governing text: PRESPEC_SANTIAGO.md §6 (frozen tag prespec-santiago-f0-amend-final)

## 1. Metric

```
R(t; w) = max(0, V_mm(t*; w) - V_mm(t; w)) / max(V_mm(t*; w) - V_min(T; w), 1e-12)
```

- `V_mm(t; w)` = SAW/min-max score of trio t under weight draw w
  = `(X_adj[i0] + X_adj[i1] + X_adj[i2]) @ w`
- `t*(w)` = SAW/mm/optimal trio (argmax V_mm over all feasible T; Proposition 1: on frontier)
- `V_min(T; w)` = min V_mm over ALL feasible trios T (computed by batched GPU pass)
- `R = 0` iff the chosen trio is t* (exact: same integer index, not floating-point equality)
- Result in pp: multiply by 100

Denominator uses the global minimum over T (not min over 8 cells), consistent with
`results/regret/regret_perdraw.csv` from `scripts/compute_regret.py`.

## 2. Cells computed at κ = 200

| Cell           | Used for | Note |
|----------------|----------|------|
| SAW/mm/opt     | S0 assert | R = 0 in every draw by construction |
| SAW/vec/grd    | S6       | greedy under vector normalisation |
| SAW/vec/opt    | S6       | optimal under vector normalisation |
| E1-B/opt       | S7a, S7b | E1-B weights: w_j^B = Ā_g (group avg of sampled w) |
| E1-W/opt       | S7b      | E1-W weights: per-criterion, removes between-group signal |

E1-B and E1-W weights via `get_e1_amplitudes(rho_j, groups, w)` from run_santiago_mc.py.

Other κ values are descriptive (no inference). κ = ∞ reported separately (1 draw).

## 3. Implementation

Function: `compute_value_regret_santiago(branch_key, kappa=200)`
in `scripts/evaluate_santiago_predictions.py`.

Imports from `run_santiago_mc.py` and `gen_santiago_seeds.py` without modification.
Seeded via `get_branch_rngs(kappa)` — canonical seeds from A5b.
GPU (cupy) required for S-T (16.7M trios). CPU feasible for S-N (78K trios).

## 4. Gates (abort if any fail)

### Gate 1: Fogo oracle
Runs BEFORE any Santiago computation. Same code on `results/unified/mc_unified_raw.csv`
must reproduce (tolerance ≤ 0.1 pp):

| Quantity                  | Expected   |
|---------------------------|-----------|
| R(SAW, vec, grd)          | 6.63 pp   |
| R(SAW, vec, opt)          | 5.27 pp   |
| Difference grd − opt      | 1.36 pp   |
| R(E1-B, opt) mean         | 4.53 pp   |
| R(E1-B, opt) median       | 5.50 pp   |
| Fraction R(E1-B) = 0      | 28%       |
| R(E1-W, opt) mean         | 6.47 pp   |

If seed 55 from `_compute_e1_regret.py` is used, IC [0.95; 1.74] must also match.

### Gate 2: K6 Fogo reproduction
Function `gate_k6_fogo()` in `evaluate_santiago_predictions.py`.
Agg_pooled3 (3-cell formula) on Fogo mc_unified_raw.csv must give:

| κ    | Expected |
|------|---------|
| 25   | +21.1 pp |
| 50   | +20.4 pp |
| 100  | +9.3 pp  |
| 200  | -0.4 pp  |
| 400  | -5.7 pp  |
| 1000 | -9.0 pp  |

Tolerance: ≤ 0.1 pp. Aborts if any κ fails.

### Gate 3: Q2 regression
All 8 main cells and 4 E1 cells at κ = 200 must reproduce the sealed CSV values
draw-by-draw (exact binary match, zero differences).

### Gate 4: Built-in asserts in EVAL-R
a. `R(SAW_mm_opt) = 0` in every draw (Proposition 1). Exact comparison, not threshold.
b. When `trio_grd == trio_opt` in a draw, `R_grd == R_opt` exactly.
c. `R(E1-V)` ≡ `R(SAW_vec)` draw-by-draw (E1-V = full TV, same as SAW_vec).
d. `0 ≤ R ≤ 1 + 1e-9` in every draw (tolerance for floating-point).

## 5. Inference rules

### S6: R(SAW, vec, grd) > R(SAW, vec, opt)
- Bootstrap: B = 2000, percentil emparelhado (pared by draw), semente A5b se existir,
  senão 20261104.
- Test at κ = 200 only. Result: CI of (R_grd − R_opt). Confirmed if CI_lo > 0.
- Condition: TV_W ≥ 0.05.
- Secondary test (Fogo diff = 1.36 pp < δ = 2.5 pp).
- For S-T: if n_same_trio_sawvec = 500/500, the diff is 0 in every draw → NOT CONFIRMED
  by construction (report exact count, not "consistent with zero").

### S7a: R(E1-B, opt) > 0
- Bootstrap CI of mean R(E1-B_opt) vs 0. Confirmed if CI_lo > 0.
- Condition: TV_B ≥ 0.05.
- Always report: fraction of draws with R = 0.
- **[POST-DATA]** Low-risk note: "confirmed if ≥ 4 draws have R > 0 at B = 2000."
  This is a diagnostic note, not part of the PRESPEC pass criterion.
  The PRESPEC criterion is: testable AND CI_lo > 0.

### S7b: R(E1-B, opt) < R(E1-W, opt)
- Rule: sign of the point estimate (R_E1B_mean < R_E1W_mean). No IC required.
- CI reported as descriptive only.
- Condition: TV_B ≥ 0.05 AND TV_W ≥ 0.05.
- Fogo reference: 4.53 pp < 6.47 pp.

## 6. Reporting

Per ramo (κ = 200):
- mean, median, fraction R = 0, IC bootstrap, for each cell.
- Exact count of same-trio draws (SAW_vec grd == opt), by κ.
- For S-T at κ = 200: if count = 500/500, S6 and S2+S6 joint are "not confirmed by
  construction; greedy and exact assembly selected identical trio in all draws."

## 7. Provenance in output JSON

```json
{
  "script": "evaluate_santiago_predictions.py",
  "git_commit": "<SHA at run time>",
  "repo_clean": true,
  "sealed_csvs": {
    "mc_ST_raw.csv": "<sha256>",
    "mc_SN_raw.csv": "<sha256>",
    "mc_ST_e1_fix2.csv": "<sha256>",
    "mc_SN_e1_fix2.csv": "<sha256>"
  },
  "tag": "predictions-eval-v2"
}
```

## 8. Regression against manual cross-check (seed 20261103)

Point estimates and discordant-draw counts must match exactly.
IC may differ (different seeds). Verdicts must match.
