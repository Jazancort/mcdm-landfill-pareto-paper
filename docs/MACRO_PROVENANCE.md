# Macro Provenance

Every LaTeX macro in the manuscript must appear in one of the categories below.
Auto-generated macros: run the listed script and commit the output file.
Orphan macros: value derives from a source that cannot be recomputed automatically; source and rationale are documented here.

No macro should be edited by hand in an auto-generated file.

---

## Auto-generated files

### macros_amplitudes.tex

Script: `scripts/generate_macros_amplitudes.py`
Source: `results/amplitudes/amplitudes.json` (SHA-256 prefix in file header)
Regenerate: `uv run python scripts/generate_macros_amplitudes.py`

| Macro | Value | Source field |
|---|---|---|
| `\TVvec` | 0.311 | `TV_vec` |
| `\TVBvec` | 0.248 | `TV_B` |
| `\TVWvec` | 0.195 | `TV_W` |
| `\TValphaTwo` | 0.673 | `TV_alpha2` |
| `\DeltaTValphaTwo` | 0.362 | `DeltaTV_alpha2` |
| `\TValphaTwoMM` | 0.160 | `TV_alpha2_mm` |
| `\PermInflation` | 2.86 | `perm_inflation` |
| `\IntraGperm` | 1.56 | `IntraGperm` |
| `\RhoShiftMaxPct` | 4.1 | `RhoShiftMaxPct` |
| `\RhoShiftMaxCrit` | coast | `RhoShiftMaxCrit` |
| `\slopeOpt` | 139.4 | `slope_opt` (OLS on 3 normalisations) |
| `\RhoPerm` | 0.583 | `rho_perm` |
| `\RhoPermInverted` | 0.052 | `rho_perm_inv` |
| `\RhoAspect` | 0.103 | `rho_aspect` |
| `\RhoAspectFlipped` | 0.058 | `rho_asp_flip` |

CI check: `uv run python scripts/generate_macros_amplitudes.py && git diff --exit-code macros_amplitudes.tex`

### macros_e6.tex

Script: `scripts/generate_macros_e6.py`
Source: `results/e6/e6_raw_prespec.csv` (SHA-256 prefix in file header)
Regenerate: `uv run python scripts/generate_macros_e6.py`

Key macros: `\EsixTargetTVW` (from `target_tvw` column, pre-registered run = 0.1986), `\Esix*` family.

CI check: `uv run python scripts/generate_macros_e6.py && git diff --exit-code macros_e6.tex`

### results/r1/macros_r1.tex

Script: `scripts/generate_macros_r1.py`
Source: `results/r1/r1_decisions.json`, `results/r1/r1_aggregate.csv`
Regenerate: `uv run python scripts/generate_macros_r1.py`

Macros: `\Rone*`, `\Rasp*` included from `macros.tex` via `\input{results/r1/macros_r1}`.

---

## Manually maintained: macros.tex

These macros have no auto-generation script. Each entry documents its source.

| Macro | Source | Last audit |
|---|---|---|
| `\TVrnk` | 0.091 from midranks amplitude run (mc_unified.py); recomputable but not scripted | 2026-10-xx |
| `\NormMainEffect` | mc_unified.py C1 contrast (34.55 pp) | 2026-10-01 |
| `\NormGreedyContrast` | mc_unified.py C6 greedy-only (25.4 pp) | 2026-10-01 |
| `\AsmMain` | mc_unified.py C2 all4 (-1.05 pp) | 2026-10-01 |
| `\AsmMM` | mc_unified.py C4 within mm (8.1 pp) | 2026-10-01 |
| `\TOSTp` | TOST p=0.010 (delta=2.5pp, 3-cell) | 2026-10-01 |
| `\Qtwo*` | tab:tvorder and tab:factorial values from mc_2cube_fixed.py | 2026-10-01 |
| `\Qthree*` | q3_perdraw.py v2 output | 2026-10-19 |
| `\FEight*` | compute_f8_circularity.py | 2026-10-02 |
| `\EoneWloss`, `\EoneVloss` | run_e1.py output | 2026-10-01 |
| `\AspSpearman*` | amplitude_regression.py (aspect non-monotone analysis) | 2026-10-02 |
| `\Agg*` | aggregation_strata.py per-cell contrasts | 2026-10-02 |
| `\TVWrj`, `\TVWinvrj`, `\TVWrw` | tvw_e4.py (E4 TV_W patterns) | 2026-10-01 |
| `\RVstarOptimal`, `\RVprimeOptimal` | R1-2 result (consistent coding) | 2026-10-01 |
| `\RefSetGreedyGain` | R1-2 11.8pp improvement | 2026-10-01 |
| `\RaspOptimal` | R-asp result (24.0%) | 2026-10-02 |
| `\slopeFive`, `\SEfive`, `\dffive`, etc. | 5-level regression for supplementary | 2026-10-01 |

Note: `generate_macros.py` was designed to write `macros_auto.tex` but that file is not currently included in main.tex. The mc_unified contrasts in macros.tex were last verified by running the script and comparing manually.

---

## Forbidden values (check_consistency.py)

Values that must NOT appear in main.tex, enforced by `BAD_PHRASES` in `check_consistency.py`:

| Value | Reason |
|---|---|
| `& 0.135 & 0.995` | Tab2 stale rho_raw for slope |
| `& 0.126 & 0.995` | Tab2 stale rho_raw for coast |
| `& 0.081 & 0.995` | Tab2 stale rho_raw for wells |
| `& 0.086 & 0.995` | Tab2 stale rho_raw for aero |
| `& 0.590 & $+0.279$` | TV(2) with wrong def-(i) |
| `& 0.675 & $+0.360$` | TV(2) with rho_raw |
| `\TVvecNumerical` | Superseded by `\TVvec` |
| `\EsixPtwoStrict*` | Renamed to `\EsixPtwoMono*` |

---

## CI workflow

```bash
# Regenerate all auto-generated macro files:
uv run python scripts/generate_macros_amplitudes.py
uv run python scripts/generate_macros_e6.py
uv run python scripts/generate_macros_r1.py

# Verify no uncommitted changes in generated files:
git diff --exit-code macros_amplitudes.tex macros_e6.tex results/r1/macros_r1.tex

# Run consistency checks:
uv run python scripts/check_consistency.py
uv run python scripts/test_coding_consistency.py
```
