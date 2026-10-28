# ROADMAP — "Normalisation as Implicit Re-weighting"
# Target: Omega/Elsevier submission  |  Last updated: 2026-09-30

## WS0 — Pipeline numérico  [COMPLETE]

- `scripts/generate_macros.py` → `macros.tex` (17 macros)
- `scripts/check_consistency.py` → 17 assertions, exit 1 on failure
- `Makefile`: `make all` = macros + check + paper
- Commit: 7edc288

## WS1 — Corpus de amplitude  [IN PROGRESS]

**Primary deliverable:** table of (TV, m_eff, ||delta||_2, TV_B, TV_W) for 7+
published real-world matrices. Answers §8.7.

**Status:**
- Fogo regression: PASS (TV=0.3146, l2=0.3127, m_eff=4.0486, counterfactual TV_W=0)
- 7 matrices in corpus_data.py; 3 active (m≥8, multi-crit groups)
- corpus_amplitudes.py: TV/m_eff/l2/TV_B/TV_W implemented and verified
- corpus_mc.py: Prop1 assertion passes; Q2≈100% (tautology, not reported)
- PRESPEC.md v2: H1/H2 withdrawn, scope = amplitude table

**Remaining:**
- Extract 5-7 more instances with m≥8 and published hierarchy
- Report: amplitude table in §8.7; note TV_B/TV_W decomposition

**NOT a corpus deliverable:** Q2 with discrimination. See WS2.

## WS2 — Caminho A_j(t) em Fogo  [PENDING]

**Purpose:** produce Q2(t) with discriminating signal. Requires coupling
constraints (greedy ≠ optimal) and frontier base rate < 5%. Both hold on Fogo.

**Design (only one objective variant — matched-obj removed):**
Objectives fixed in min-max for all cells. The "matched objectives" variant
(objectives in the same norm as the score) gives Q2=1 by Proposition 1 in
optimal assembly — a tautology, removed from the design.

Path: A_j(t) = ρ_j^t, t ∈ {0, 0.419, 0.513, 0.692, 0.868, 1.0}
→ TV ∈ {0, 0.12, 0.15, 0.21, 0.27, 0.315}

N=3500 draws per cell, Athena (~17 min/cell).

**TV_W(t) along the path (computed with correct groups from fogo_constants.py):**

| t     | TV     | TV_B   | TV_W   | m_eff  |
|-------|--------|--------|--------|--------|
| 0.000 | 0.0000 | 0.0000 | 0.0000 | —      |
| 0.419 | 0.1199 | 0.0910 | 0.0848 | 4.500  |
| 0.513 | 0.1502 | 0.1146 | 0.1038 | 4.429  |
| 0.692 | 0.2099 | 0.1622 | 0.1395 | 4.290  |
| 0.868 | 0.2699 | 0.2113 | 0.1737 | 4.152  |
| 1.000 | 0.3146 | 0.2489 | 0.1986 | 4.049  |

**Pre-declared prediction (BEFORE running WS2):**
The efficiency loss Q2(mm) − Q2(vec) in OPTIMAL assembly is monotone
in TV_W(t) (Spearman ρ > 0 across the 5 non-zero t levels). Falsified if ρ ≤ 0.

The loss in GREEDY assembly is not covered by this prediction (foreclosure
is not determined by TV_W alone).

**Statistical design (from e351d79 ROADMAP):**
N=3500 per cell (SE ≈ 0.85 pp). With 4 new levels + canonical level (N=3500):
  - Max leverage: 0.622 (vs 0.935 with 3 points)
  - S_xx fraction on single point: 29.6% (vs 73.5%)
  - VIF(TV, TV²): 11.78 (vs 23.75)
  - SE(β₂): 68.0 (vs 95.3)

## WS3 — Decomposição foreclosure/misalignment  [PENDING]

From e351d79 ROADMAP (preserved):

The empirical result — normalisation × assembly interaction — has no theory.
Target proposition: decompose Q2 loss as L(norm, assembly) = L_forec ⊕ L_mis.
The gain from optimal assembly is bounded above by a decreasing function of
||delta||_2: fixing foreclosure only helps insofar as the target being optimised
is the correct target.

If proof does not close: state as verified empirical decomposition across WS1
instances with the upper bound confirmed numerically. More valuable than the
paper has today.

With correct TV_W(t) table:
- Pre-declare: L_optimal tracks TV_W(t), not TV(t)
- Pre-declare: L_greedy − L_optimal tracks TV_B(t) (between-group component)

These are the WS2 estimands. Run WS2, then check.

## WS4 — Pipeline numérico  [COMPLETE as WS0 above]

## WS5 — Reestruturação  [PENDING — after WS2 data]

From e351d79: promote the normalisation × assembly interaction. Currently §7.4.
With WS3 proposition: becomes the second pillar of the article.

- §8.7: insert amplitude table from WS1 corpus.
- §8.6: insert TV_W(t) prediction and WS2 regression.
- Corollary after rem:definitional: Extension of Prop. 1 (affine norms,
  multi-criterion groups → Q2=1 in optimal assembly).
- Title: consider bringing assembly into title (stronger claim than normalisation alone).
- Highlights: replace first highlight (Lemma) with the interaction finding.
- Abstract: +29.8 vs +2.2 pp in second sentence, not penultimate.

## Commit history (recent)

| Commit  | Description |
|---------|-------------|
| 87bf3b9 | §7.7 estimand corrected; §8.6 lower bound removed |
| 9d30fde | tab:tvorder canonical; §7.2/§8.6 bloco WP3 |
| 15072f4 | Weitendorf = min-max; Peldschus paired t |
| 7edc288 | WS4 pipeline: generate_macros, check_consistency, Makefile |
| e351d79 | ROADMAP v1 |
| f0e90b5 | corpus_amplitudes TV/meff/l2 correct; Fogo PASS; m≥8 |
| 5c07bf5 | Frontier over trios (bug: X_raw vs N_mm — diagnosed) |
| 0eb1218 | Prop1 assert; objectives fixed mm; PRESPEC §6 |
| current | PRESPEC v2; DEV-002-005; TV_B/TV_W; 2a/2b resolved |
