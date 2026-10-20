# mcdm-landfill-pareto

**Normalisation as implicit re-weighting in MCDM portfolio selection:
a factorial comparison on Fogo Island landfill siting**

Julio L. Azancort Neto — under review at *Omega*

---

## What this repository contains

| Path | Contents |
|---|---|
| `main.tex` | Article source (XeLaTeX, Elsevier CAS double-column) |
| `macros.tex` | All numeric macros — auto-generated, single source of truth |
| `refs.bib` | Bibliography (BibTeX) |
| `supplementary.tex` | Supplementary material |
| `figures/` | All figures in PDF (vector) and PNG (raster) |
| `scripts/` | Python scripts for every computation in the paper |
| `results/unified/` | **Canonical results** from `mc_unified.py` (seed=42) |
| `results/e1/` | E1 per-draw data: Q2, Q3, gap |
| `results/f8/` | F8 benchmark circularity |
| `data/` | Pre-built trios and matrices |
| `cas-dc.cls`, `cas-common.sty` | Elsevier CAS class files |

---

## Import into Overleaf

1. On GitHub, click **Code > Download ZIP**
2. In Overleaf, click **New Project > Upload Project** and select the ZIP
3. Set compiler to **XeLaTeX** and main file to `main.tex`
4. Click **Recompile**

All figure files (`figures/*.pdf`) and class files (`cas-dc.cls`) are included.

---

## Reproduce from scratch

### Requirements

- Python 3.12 with [uv](https://github.com/astral-sh/uv): `pip install uv`
- XeLaTeX (TeX Live 2023+ or MiKTeX)
- MCDM data files (set `MCDM_DATA_DIR`; see below)

### Step 1 — Clone

```bash
git clone https://github.com/Jazancort/mcdm-landfill-pareto.git
cd mcdm-landfill-pareto
```

### Step 2 — Set data path

The spatial dataset is obtained from [Azancort Neto (2026)](https://zenodo.org/records/17704387).
After downloading, set the environment variable:

```bash
# Linux / Athena
export MCDM_DATA_DIR=/path/to/mcdm_data

# Windows
$env:MCDM_DATA_DIR = "C:\path\to\mcdm_data"
```

### Step 3 — Run the unified MC experiment

```bash
uv run python scripts/mc_unified.py
```

This single script runs the complete analysis:
the balanced 2³ factorial (500 draws, kappa=200, seed=42),
Q3 gap computation, all bootstrap contrasts, TOST, and macro generation.

Outputs written to `results/unified/`:

| File | Contents |
|---|---|
| `mc_unified_raw.csv` | 4 000 rows: 8 cells × 500 draws (portfolios, Q2, gap) |
| `mc_unified_contrasts.csv` | Bootstrap CIs for 11 contrasts |
| `mc_unified_q3.csv` | Q3, frac\_gap0, conditional gap per cell |
| `mc_unified_macros.tex` | All numeric macros (copy into `macros.tex`) |

Expected output:

```
Assertao frac_gap0>=Q2: PASSOU em todas as 8 celulas.
TOST: mean=-0.40pp  90%CI=[-1.9,+1.1]  p=0.010
CONCLUIDO.
```

Runtime: ~4 min on GPU (Athena), ~9 min on laptop.

### Step 4 — Verify macros

```bash
uv run python scripts/verify_macros_permanent.py
```

Expected: `ALL CHECKS PASSED`

### Step 5 — Build the PDF

```bash
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

Or with the Makefile:

```bash
make
```

---

## Key scripts

| Script | Role |
|---|---|
| `scripts/mc_unified.py` | **Canonical**: factorial + Q3 + bootstrap + macros |
| `scripts/scoring.py` | Shared SAW/TOPSIS scoring (single source of truth) |
| `scripts/q3_perdraw.py` | Q3 per draw with assertions |
| `scripts/mcdm_experiment.py` | Core MCDM module (scores, data loading) |
| `scripts/pareto_utils.py` | Pareto dominance utilities |
| `scripts/verify_macros_permanent.py` | CI: verify all macros vs raw data |
| `scripts/compute_f8_circularity.py` | F8 benchmark robustness |
| `scripts/run_e1_v3.py` | E1 intervention experiment |

---

## Assertions and reproducibility

The repository guarantees exact reproducibility of every number in the manuscript:

- `mc_unified.py` uses a fixed seed (`SEED=42`, `B=10_000`) and asserts `q2==1 => gap==0` on all 8 cells.
- `verify_macros_permanent.py` cross-checks the manuscript macros against the raw CSV.
- All bootstrap CIs, TOST p-value, Q3 values, and conditional gaps derive from a single run.

---

## Replication DOI

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23479281.svg)](https://doi.org/10.5281/zenodo.23479281)

---

## Citation

```bibtex
@article{AzancortNeto2026_omega,
  author  = {Azancort Neto, Julio L.},
  title   = {Normalisation as implicit re-weighting in {MCDM} portfolio selection:
             a factorial comparison on {F}ogo {I}sland landfill siting},
  journal = {Omega},
  year    = {2026},
  note    = {Under review}
}
```
