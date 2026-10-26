# Replication Package — Pareto-Based MCDM for Landfill Site Selection (Fogo Island, Cabo Verde)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.PENDING.svg)](https://doi.org/10.5281/zenodo.PENDING)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Replication package for the Omega paper:

> Azancort Neto, J. L., *Comparing SAW and TOPSIS under normalization and aggregation uncertainty: a Pareto-based Monte Carlo study for landfill site selection on Fogo Island, Cabo Verde*. Under review at Omega (Elsevier).

---

## Repository Layout

```
.
├── paper/            LaTeX source to compile the manuscript
│   ├── main.tex
│   ├── supplementary.tex
│   ├── refs.bib
│   ├── macros*.tex   (auto-generated; do not edit by hand)
│   ├── cas-dc.cls    (Elsevier CAS double-column class)
│   └── figures/      compiled figures (PDF + PNG)
│
├── data/             input data files
│   ├── fogo_trios.npy          candidate site triples (N=473)
│   ├── asp_correct_473.npy     corrected geographic aspect values
│   ├── ok_matrix.npy           feasibility matrix
│   ├── idecv_ilhas.geojson     island boundaries (IDECV)
│   ├── fogo_boundary.geojson   Fogo Island boundary
│   ├── e1_v3_rerun_20261002.log provenance log for E1 rerun
│   └── literature/             extracted matrices from cited studies
│
├── src/              replication source code
│   ├── utils/        shared utilities (imported by experiments)
│   ├── experiments/  one script per main experiment (E1–E6, main MC)
│   ├── analysis/     bootstrap, macro generation, sensitivity, figures analysis
│   └── figures/      figure generation scripts
│
├── results/          pre-computed output files (CSV/JSON/NPY)
│   ├── e1/           E1 normalization experiment
│   ├── e2/           E2 grid search
│   ├── e4/           E4 star test
│   ├── e5/           E5 synthetic grid
│   ├── e6/           E6 Spearman decomposition
│   ├── f8/           F8 circularity analysis
│   ├── fourthcell/   main 2-cube Monte Carlo (mc_2cube_fixed_raw.csv)
│   ├── r1/           R1 residual analysis
│   ├── regret/       regret (R) analysis
│   ├── bootstrap_k50_k200.csv   bootstrap contrasts (κ=200 vs κ=50)
│   ├── raw_sensitivity_4cells.csv   κ sensitivity across 4 main cells
│   └── raw_sensitivity_q2.json      raw sensitivity output
│
├── prespec/          pre-registration documents (open-science transparency)
│   ├── PRESPEC.md          master pre-registration
│   ├── PRESPEC_E1.md … PRESPEC_E6.md  per-experiment specs
│   ├── PRESPEC_R1.md
│   ├── PRESPEC_SANTIAGO.md  Santiago Island replication plan
│   └── DEVIATIONS.md       documented deviations from pre-spec
│
├── docs/             documentation for replicators
│   ├── DATA_DICTIONARY.md
│   ├── MACRO_PROVENANCE.md
│   ├── contamination-note.md
│   └── provenance.csv
│
└── archive/          not needed for replication
    ├── scripts/      development and diagnostic scripts
    ├── docs/         internal planning documents
    └── results/      intermediate/diagnostic output files
```

---

## Requirements

```
Python >= 3.11
numpy
scipy
pandas
geopandas
matplotlib
```

Install with:

```bash
pip install numpy scipy pandas geopandas matplotlib
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install numpy scipy pandas geopandas matplotlib
```

---

## Reproducing the Results

### Step 1 — Main Monte Carlo (2-cube × 4th cell)

Generates `results/fourthcell/mc_2cube_fixed_raw.csv`, the primary dataset for
all statistical contrasts reported in Tables 5–9 of the paper.

```bash
uv run python src/experiments/run_fourthcell_consistent.py
```

Expected runtime on a modern CPU: approximately 30–60 minutes.
On GPU (NVIDIA RTX 4000 Ada): approximately 5–10 minutes.

### Step 2 — Bootstrap contrasts (κ=200 and κ=50)

Reads `results/fourthcell/mc_2cube_fixed_raw.csv` and produces
`results/bootstrap_k50_k200.csv`.

```bash
uv run python src/analysis/bootstrap_contrasts.py
```

### Step 3 — Individual experiments

Each experiment is self-contained:

```bash
uv run python src/experiments/run_e1_v3.py      # E1 normalization
uv run python src/experiments/run_e3_grid.py     # E3 grid
uv run python src/experiments/run_e4_vstar.py    # E4 star test
uv run python src/experiments/run_e5_grid.py     # E5 synthetic
uv run python src/experiments/run_e6.py          # E6 Spearman
```

### Step 4 — κ sensitivity curve

```bash
uv run python src/analysis/raw_sensitivity_4cells.py
```

### Step 5 — Regenerate LaTeX macros

After rerunning experiments, regenerate all macros:

```bash
uv run python src/analysis/generate_macros.py
uv run python src/analysis/generate_macros_amplitudes.py
uv run python src/analysis/generate_macros_e6.py
uv run python src/analysis/generate_macros_r1.py
uv run python src/analysis/generate_macros_f8.py
```

Macro files are written to `results/*/` and must be copied to `paper/` before
compiling.

### Step 6 — Regenerate figures

```bash
uv run python src/figures/fig_F1_slope_weights.py
uv run python src/figures/fig_F2_interaction.py
uv run python src/figures/fig_F3_pareto.py
uv run python src/figures/fig_F4_map.py
uv run python src/figures/fig_F5_binary_amplitude.py
uv run python src/figures/fig_E5_synthetic_grid.py
```

Figures are written to `paper/figures/`.

### Step 7 — Compile the paper

```bash
cd paper
make
```

Or manually:

```bash
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

---

## Input Data

| File | Description |
|---|---|
| `data/fogo_trios.npy` | 473 candidate site triples, each encoded as (site_id, weight_index, ...). Shape (473, …). |
| `data/asp_correct_473.npy` | Geographic aspect values (degrees, 0=North CW) for each of the 473 sites. |
| `data/ok_matrix.npy` | Boolean feasibility matrix for candidate site pairs. |
| `data/idecv_ilhas.geojson` | Official Cabo Verde island boundaries from IDECV. |
| `data/fogo_boundary.geojson` | Fogo Island boundary used for spatial clipping. |

For a full description of all fields, see `docs/DATA_DICTIONARY.md`.

---

## Pre-registration

All experiments were pre-registered before data analysis. Documents are in
`prespec/`. The master pre-registration (`PRESPEC.md`) was timestamped via a
git commit before the main Monte Carlo was run. Per-experiment pre-registrations
(`PRESPEC_E1.md` through `PRESPEC_E6.md`) document the exact parameters and
hypotheses for each sub-study.

Deviations from the pre-registered protocol are documented in
`prespec/DEVIATIONS.md`.

---

## Integrity Verification

To verify that the key data files match the values reported in the paper:

```bash
uv run python src/analysis/verify_macros_permanent.py
```

This script checks SHA-256 hashes of critical intermediate files against
hard-coded reference values and exits with code 0 on success.

---

## Citation

```bibtex
@article{AzancortNeto2026omega,
  author  = {Azancort Neto, Julio L.},
  title   = {Comparing {SAW} and {TOPSIS} under normalization and aggregation
             uncertainty: a {Pareto}-based {Monte Carlo} study for landfill
             site selection on {Fogo Island, Cabo Verde}},
  journal = {Omega},
  year    = {2026},
  note    = {Under review}
}
```

---

## License

MIT. See [LICENSE](LICENSE).
