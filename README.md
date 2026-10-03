# mcdm-landfill-pareto

Replication repository for:
**"Normalisation as implicit re-weighting in MCDM portfolio selection: a factorial comparison on Fogo Island landfill siting"**

---

## Requirements

- Python ≥ 3.10 with [uv](https://github.com/astral-sh/uv) (`pip install uv`)
- XeLaTeX (TeX Live 2023+ or MiKTeX)
- Data files in `data/` and `results/` (included in repository)

---

## Reproduce in 3 steps

### Step 1 — Clone

```bash
git clone https://github.com/Jazancort/mcdm-landfill-pareto.git
cd mcdm-landfill-pareto
```

### Step 2 — Rerun the main Monte Carlo experiment (E1)

```bash
uv run python scripts/run_e1_v3.py
```

Expected output: `results/e1/mc_2cube_fixed_raw.csv`
Expected source hash: `ea5dfe07d12bd5ff`
Runtime: ~5–10 min on a modern laptop (500 draws × 8 cells).

### Step 3 — Verify all macro values against the manuscript

```bash
uv run python scripts/verify_macros_permanent.py
```

Expected output: `ALL CHECKS PASSED`
Expected hash: `ea5dfe07d12bd5ff` (mc_2cube_fixed_raw.csv)

If the hash matches and all checks pass, every number in the manuscript
is consistent with the data files.

---

## Build the PDF

```bash
# From the repository root
cp macros.tex /tmp/build/
cd /tmp/build/
xelatex main.tex && xelatex main.tex
```

On Windows (PowerShell):

```powershell
$repo = "path\to\mcdm-landfill-pareto"
Copy-Item "$repo\macros.tex" "C:\build\paper\macros.tex" -Force
xelatex -interaction=nonstopmode "$repo\main.tex"
```

---

## End-to-end pipeline (1 command)

Runs all validation steps and builds the PDF:

```bash
# Linux/macOS
bash -c "
  uv run python scripts/run_e1_v3.py &&
  uv run python scripts/verify_macros_permanent.py &&
  uv run python scripts/validate_e6.py &&
  uv run python scripts/check_consistency.py &&
  uv run python scripts/test_promethee_identity.py &&
  uv run python scripts/test_gap_counterexample.py &&
  xelatex -interaction=nonstopmode main.tex
"
```

```powershell
# Windows PowerShell
$repo = "path\to\mcdm-landfill-pareto"
cd $repo
uv run python scripts/run_e1_v3.py
uv run python scripts/verify_macros_permanent.py
uv run python scripts/validate_e6.py
uv run python scripts/check_consistency.py
uv run python scripts/test_promethee_identity.py
uv run python scripts/test_gap_counterexample.py
Copy-Item macros.tex C:\build\paper\macros.tex -Force
xelatex -interaction=nonstopmode main.tex
```

Expected final output: `main.pdf` with all checks passing (exit 0).
Note: `run_e1_v3.py` takes ~5–10 min on a modern CPU. The full E6 study (`run_e6_generator.py`, 45 instances × 200 draws) was run on an Athena server (NVIDIA RTX 4000 Ada) and took ~584 s; outputs are pre-committed in `results/e6/` for local validation without re-running.

---

## Key scripts

| Script | Purpose |
|--------|---------|
| `scripts/run_e1_v3.py` | Main E1 experiment (500 draws, 8 cells) |
| `scripts/verify_macros_permanent.py` | Audit all manuscript numbers against CSV sources |
| `scripts/check_consistency.py` | Cross-check LaTeX macros vs data files |
| `scripts/generate_macros.py` | Regenerate `macros.tex` from data |
| `scripts/test_promethee_identity.py` | Unit test: PROMETHEE II ≡ rank-weighted SAW |
| `scripts/test_gap_counterexample.py` | Unit test: gap=0 ≠ Pareto |

---

## Repository structure

```
data/           Raw spatial and attribute data (Fogo Island)
results/        Experiment outputs (CSV logs, cached draws)
  e1/           E1 Monte Carlo output
  e5/           E5 synthetic grid
scripts/        All Python scripts
corpus/         Internal notes and improvement plan
main.tex        Main manuscript
supplementary.tex  Supplementary material
macros.tex      Auto-generated numerical macros
```

---

## Versions

| Tag | Description |
|-----|-------------|
| `v0.9-defensible` | All primary claims verified; baseline before improvement plan |
| `v1.0-submission-candidate` | Final candidate (after E6 and one-pass review) |

---

## License

Data and code: MIT. Manuscript text: all rights reserved pending journal submission.
