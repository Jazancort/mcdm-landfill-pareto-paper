# Changelog

All notable changes to the replication package are documented here.

## [v1.1] - 2026-10-28

### Added
- Full reorganization into a clean, Zenodo-ready structure mirroring the
  `llm-knowledge-collapse-replication` package layout.
- `paper/scripts/analysis/bootstrap_contrasts.py`: bootstrap contrasts for
  both κ=200 (primary) and κ=50 (robustness check), saved to
  `paper/results/bootstrap_k50_k200.csv`.
- `paper/results/bootstrap_k50_k200.csv`: 5 bootstrap contrasts at κ=200 and
  κ=50 for the four main factorial cells.
- `paper/docs/prespec/` directory consolidating all ten pre-registration documents.
- `paper/docs/contamination-note.md`: full history of the aspect convention correction.
- `paper/figs/src/` directory with all figure generation scripts.
- `archive/` directory for development scripts and internal planning documents.

### Changed
- κ-sensitivity qualified in abstract, highlights, introduction, §8.5, and §9:
  normalization contrasts are robust across both κ values; aggregation and assembly
  contrasts are reported conditionally on κ.
- Table 6 now shows two columns (κ=200 and κ=50) for the main bootstrap contrasts.
- `paper/scripts/utils/aspect_utils.py`: geographic azimuth convention enforced
  consistently across all scripts (`theta_geo = (270 - theta_nb) % 360`).

### Fixed
- R-V (vector regret): corrected from 19.6–20.0% (mixed convention) to 6.2–6.4%
  (geographic azimuth). R-asp − R-V contrast corrected from −4.4 pp (artefact) to
  +9.4 pp [+6.6, +12.4] (true value). Commits `61d4686` and `c3db083`.
- Cross-references to `sec:refset` corrected to `rem:nonmonotone` / `sec:alignment`.
- Remark 6 geometric explanation rewritten; p-value removed (it was a tautology
  given linear normalization applied to WNW aspect values).
- §6.7 derivation uses consistent notation (x̃ throughout).

---

## [v1.0] - 2026-10-26

Initial public release. Contains:
- LaTeX manuscript source (`paper/manuscript/`).
- All six pre-registered experiments (E1–E6) and the main 2-cube Monte Carlo.
- Pre-computed result files (`paper/results/`).
- Input data for Fogo Island (473 candidate sites).
- Ten pre-registration documents.
