<p align="center">
  <h1 align="center">Normalisation as Implicit Re-weighting in Multi-Criteria Portfolio Selection<br>Landfill Site Selection on Fogo Island, Cabo Verde</h1>
  <p align="center"><em>Closed Form and Cost Against an Exact Pareto Frontier</em></p>
  <p align="center">
    Replication package &middot; Omega (under review)
  </p>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white" alt="Python 3.11+"></a>
  <a href="https://numpy.org/"><img src="https://img.shields.io/badge/NumPy-1.26+-013243?logo=numpy&logoColor=white" alt="NumPy 1.26+"></a>
  <a href="https://scipy.org/"><img src="https://img.shields.io/badge/SciPy-1.13+-8CAAE6?logo=scipy&logoColor=white" alt="SciPy 1.13+"></a>
  <a href="https://doi.org/10.5281/zenodo.23676429"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.23676429.svg" alt="DOI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green" alt="License MIT"></a>
  <img src="https://img.shields.io/badge/Journal-Omega%20(Elsevier)-orange" alt="Omega">
</p>

---

## Overview

**How much does the choice of normalization and aggregation method matter in real MCDM problems?**

We study the sensitivity of SAW and TOPSIS rankings to methodological choices — normalization rule (min-max vs vector), aggregation operator (weighted sum vs vector norm), and assembly method (greedy vs optimal) — using a pre-registered Pareto-based Monte Carlo design on **473 candidate landfill sites** on Fogo Island, Cabo Verde.

<p align="center">
  <img src="https://raw.githubusercontent.com/Jazancort/mcdm-landfill-pareto-paper/main/paper/figs/final/fig_F4_map.png" width="700" alt="Study area: Fogo Island candidate sites">
  <br><sub>Fig. F4 — Fogo Island, Cabo Verde. Candidate sites (N=473) after feasibility screening. Site attributes include slope, aspect, proximity to roads, rivers, coastline, protected areas, wells, and the airport.</sub>
</p>

The key finding: **normalization is the dominant driver of Pareto attainment** — switching from min-max to vector normalization shifts Q2 retention by +29 to +33 pp regardless of all other choices. Aggregation and assembly have smaller, conditional effects.

---

## Main result: normalisation dominates

<p align="center">
  <img src="https://raw.githubusercontent.com/Jazancort/mcdm-landfill-pareto-paper/main/paper/figs/final/fig_F2_interaction.png" width="700" alt="Interaction: normalization × aggregation × assembly">
  <br><sub>Fig. F2 — Bootstrap contrasts (95% CI, N=4000 Monte Carlo draws, &kappa;=200) for the main factorial effects and pairwise interactions. Normalization dominates across all cells. The aggregation contrast is not robust to &kappa; (see Table 6).</sub>
</p>

Across 4000 Monte Carlo draws (κ=200, pre-registered), we observe:

- **Normalization (greedy):** +29.2 pp [+25.7, +33.0] — the largest and most consistent effect
- **Normalization (informative):** +33.2 pp [+29.4, +36.7] — significant across both κ values
- **Aggregation (min-max vs vector, κ=200):** −0.4 pp [−3.4, +2.8] — not significant
- **Assembly (exact, κ=200):** −10.2 pp [−13.0, −7.4] — significant but κ-sensitive

The aggregation and assembly contrasts depend on κ: at κ=50, aggregation reverses sign (+20.4 pp SIG) while assembly becomes non-significant. Pre-registration details in `paper/docs/prespec/`.

---

## Pareto frontier structure

<p align="center">
  <img src="https://raw.githubusercontent.com/Jazancort/mcdm-landfill-pareto-paper/main/paper/figs/final/fig_F3_pareto.png" width="700" alt="Pareto frontier: SAW vs TOPSIS under uncertainty">
  <br><sub>Fig. F3 — Pareto-optimal triples under the 2×2×2 factorial. Each point is one (normalization, aggregation, assembly) combination evaluated over the 473 candidate sites. The exact frontier dominates greedy solutions in 8/8 cells for SAW.</sub>
</p>

The Pareto frontier is computed exactly (not approximated): for each weight draw, we enumerate all non-dominated site triples and count how often a candidate appears. This gives **rank-robust site recommendations** that are stable across the entire uncertainty space.

---

## Aspect sensitivity (R-V analysis)

| Metric | Greedy | Optimal | Contrast |
|--------|--------|---------|----------|
| R-asp (aspect regret, %) | 15.8% | 15.6% | +0.2 pp (n.s.) |
| R-V (vector regret, %) | 6.4% | 6.2% | +0.2 pp (n.s.) |
| R-asp − R-V | **+9.4 pp** | **+9.4 pp** | **[+6.6, +12.4] SIG** |

Vector normalization systematically reduces regret by 9.4 pp compared to aspect normalization (geographic azimuth convention), confirming the normalization dominance finding from the main factorial.

---

## Study design

<p align="center">
  <img src="https://raw.githubusercontent.com/Jazancort/mcdm-landfill-pareto-paper/main/paper/figs/final/fig_F1_slope_weights.png" width="700" alt="Criteria weight sampling and slope distribution">
  <br><sub>Fig. F1 — Weight sampling scheme and slope distribution across the 473 candidate sites. Weights are drawn from a Dirichlet distribution with uniform concentration (&kappa;=200 primary, &kappa;=50 robustness check).</sub>
</p>

| Experiment | Description | N draws | Purpose |
|-----------|-------------|---------|---------|
| E1 | Normalization comparison (SAW only) | 4000 | Main normalization effect |
| E2 | Grid search over κ | 100/cell | Concentration sensitivity |
| E4 | Star test (v-star sites) | 1000 | Extreme-weight validation |
| E5 | Synthetic grid (monotone profiles) | 100×100 | Theoretical boundary |
| E6 | Spearman decomposition | 500 | Rank correlation structure |
| Main MC | 2-cube (norm×agg) × 4th cell (assembly) | 4000 | Full factorial |

**Total: 6 pre-registered experiments + main factorial**, all completed on a standard CPU (< 60 min). GPU not required.

---

## Reproducing the results (v1.1)

### 1. Install dependencies

```bash
pip install numpy scipy pandas geopandas matplotlib
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install numpy scipy pandas geopandas matplotlib
```

### 2. Run the main Monte Carlo experiment

Generates `paper/results/fourthcell/mc_2cube_fixed_raw.csv` — the primary dataset for all contrasts in Tables 5–9.

```bash
cd paper
uv run python scripts/experiments/run_fourthcell_consistent.py
```

Expected runtime: 30–60 min on CPU.

### 3. Compute bootstrap contrasts (κ=200 and κ=50)

```bash
uv run python scripts/analysis/bootstrap_contrasts.py
```

Reads `results/fourthcell/mc_2cube_fixed_raw.csv`, writes `results/bootstrap_k50_k200.csv`.

### 4. Run individual experiments

```bash
uv run python scripts/experiments/run_e1_v3.py      # E1 normalization
uv run python scripts/experiments/run_e3_grid.py     # E2/E3 grid
uv run python scripts/experiments/run_e4_vstar.py    # E4 star test
uv run python scripts/experiments/run_e5_grid.py     # E5 synthetic
uv run python scripts/experiments/run_e6.py          # E6 Spearman
```

### 5. Regenerate LaTeX macros

```bash
uv run python scripts/analysis/generate_macros.py
uv run python scripts/analysis/generate_macros_e6.py
uv run python scripts/analysis/generate_macros_r1.py
```

Macro files are written to `results/*/` and must be copied to `manuscript/` before compiling.

### 6. Regenerate figures

```bash
uv run python figs/src/fig_F1_slope_weights.py
uv run python figs/src/fig_F2_interaction.py
uv run python figs/src/fig_F3_pareto.py
uv run python figs/src/fig_F4_map.py
uv run python figs/src/fig_F5_binary_amplitude.py
```

Figures are written to `figs/final/` at 300 dpi.

### 7. Compile the manuscript

```bash
cd manuscript
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

Or `make` if the Makefile is configured for your LaTeX installation.

---

## Repository structure

```
.
├── README.md
├── CHANGELOG.md           <- version history
├── .zenodo.json           <- Zenodo metadata (auto-read on release)
│
├── paper/                 <- replication package
│   ├── data/
│   │   ├── fogo_trios.npy              <- 473 candidate site triples
│   │   ├── asp_correct_473.npy         <- corrected geographic aspect values
│   │   ├── ok_matrix.npy               <- feasibility matrix
│   │   ├── idecv_ilhas.geojson         <- island boundaries (IDECV)
│   │   ├── fogo_boundary.geojson       <- Fogo Island boundary
│   │   ├── e1_v3_rerun_20261002.log    <- provenance log for E1 rerun
│   │   └── literature/                 <- extracted matrices from cited studies
│   │
│   ├── manuscript/
│   │   ├── main.tex                    <- LaTeX source
│   │   ├── supplementary.tex
│   │   ├── refs.bib
│   │   ├── macros*.tex                 <- auto-generated macros (do not edit)
│   │   └── cas-dc.cls                  <- Elsevier CAS double-column class
│   │
│   ├── figs/
│   │   ├── final/                      <- compiled figures (PDF + PNG, 300 dpi)
│   │   │   ├── fig_F1_slope_weights.*
│   │   │   ├── fig_F2_interaction.*
│   │   │   ├── fig_F3_pareto.*
│   │   │   ├── fig_F4_map.*
│   │   │   └── fig_F5_binary_amplitude.*
│   │   └── src/                        <- figure generation scripts
│   │       ├── fig_F1_slope_weights.py
│   │       ├── fig_F2_interaction.py
│   │       └── ...
│   │
│   ├── scripts/
│   │   ├── experiments/                <- one script per experiment
│   │   │   ├── run_e1_v3.py            <- E1 normalization
│   │   │   ├── run_e4_vstar.py         <- E4 star test
│   │   │   ├── run_e5_grid.py          <- E5 synthetic
│   │   │   ├── run_e6.py               <- E6 Spearman
│   │   │   └── run_fourthcell_consistent.py  <- main 2-cube Monte Carlo
│   │   ├── analysis/                   <- bootstrap, macros, sensitivity
│   │   │   ├── bootstrap_contrasts.py
│   │   │   ├── generate_macros.py
│   │   │   ├── compute_regret.py
│   │   │   └── ...
│   │   └── utils/                      <- shared utilities
│   │       ├── aspect_utils.py         <- geographic aspect convention
│   │       ├── pareto_utils.py
│   │       ├── scoring.py
│   │       └── ...
│   │
│   ├── results/                        <- pre-computed output files
│   │   ├── fourthcell/
│   │   │   └── mc_2cube_fixed_raw.csv  <- main experiment output (4000 draws)
│   │   ├── bootstrap_k50_k200.csv      <- bootstrap contrasts (kappa=200 vs kappa=50)
│   │   ├── raw_sensitivity_4cells.csv  <- kappa sensitivity
│   │   └── e1/ e2/ e4/ e5/ e6/ f8/ r1/ regret/
│   │
│   └── docs/
│       ├── DATA_DICTIONARY.md          <- field definitions for all data files
│       ├── MACRO_PROVENANCE.md         <- which script generates each macro
│       ├── contamination-note.md       <- aspect convention correction history
│       ├── provenance.csv              <- script-to-result traceability
│       └── prespec/                    <- pre-registration documents
│           ├── PRESPEC.md              <- master pre-registration
│           ├── PRESPEC_E1.md .. PRESPEC_E6.md
│           ├── PRESPEC_R1.md
│           ├── PRESPEC_SANTIAGO.md     <- Santiago Island replication plan
│           └── DEVIATIONS.md           <- documented protocol deviations
│
└── archive/                            <- development artifacts (not needed for replication)
    ├── scripts/                        <- diagnostic and one-off scripts
    ├── docs/                           <- internal planning documents
    └── results/                        <- intermediate and diagnostic outputs
```

---

## Data integrity

The aspect convention used throughout is **geographic azimuth** (0° = North, clockwise). The conversion from the DEM notebook convention is `θ_geo = (270 − θ_nb) % 360`, implemented in `paper/scripts/utils/aspect_utils.py`. An earlier version of the analysis used a mixed convention; the correction is documented in `paper/docs/contamination-note.md` and in commit `c3db083` of the working repository.

To verify that the key intermediate files match the values reported in the manuscript:

```bash
cd paper
uv run python scripts/analysis/verify_macros_permanent.py
```

---

## Pre-registration

All six sub-experiments and the main factorial were pre-registered before data analysis. The master document (`paper/docs/prespec/PRESPEC.md`) was timestamped via a git commit on 2026-09-30, before the main Monte Carlo was run. Deviations from the pre-registered protocol are documented in `paper/docs/prespec/DEVIATIONS.md`.

---

## Zenodo archive

| DOI type | Link | Resolves to |
|----------|------|-------------|
| **Concept** (always latest) | [10.5281/zenodo.23676429](https://doi.org/10.5281/zenodo.23676429) | Latest release |
| **Version v1.1** (this submission) | [10.5281/zenodo.23676429](https://doi.org/10.5281/zenodo.23676429) | This exact snapshot |

---

## Citation

```bibtex
@article{AzancortNeto2026omega,
  author  = {Azancort Neto, Julio L.},
  title   = {Comparing {SAW} and {TOPSIS} under normalization and aggregation
             uncertainty: a {Pareto}-based {Monte Carlo} study for landfill
             site selection on {Fogo Island, Cabo Verde}},
  journal = {Omega},
  note    = {Under review},
  year    = {2026},
  doi     = {10.5281/zenodo.23676429}
}
```

---

## License

| Component | License |
|-----------|---------|
| Scripts and figures | **MIT** — see [LICENSE](LICENSE) |
| Manuscript LaTeX source | Provided for review; all rights reserved pending publication |
| Geographic data (IDECV) | Public domain (Cabo Verde government) |
