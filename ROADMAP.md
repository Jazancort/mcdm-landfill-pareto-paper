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

**Purpose:** produce Q2(t) vs TV(t) and TV_W(t) with discriminating signal.
Requires coupling constraints (greedy ≠ optimal) and frontier base rate < 5%.
Both conditions hold on the Fogo matrix.

**Design:**
- Path: A_j(t) = ρ_j^t, t ∈ {0, 0.419, 0.513, 0.692, 0.868, 1.0}
  → TV ∈ {0, 0.12, 0.15, 0.21, 0.27, 0.315}
- Objectives fixed in min-max (ONLY — see below).
- Score varies: mm / vec / rnk.
- 4 cells × N=3500 draws, Athena (~17 min/cell).

**REMOVED: "matched objectives" variant (objects casados)**
Rationale: in optimal assembly, objectives matched to score norm gives Q2=1
by Proposition 1 (exact positive scalarisation). This is a tautology, not a
finding. The variant was listed in the ROADMAP but is now removed.
Only the fixed-mm objective design produces discriminating signal.

**Prediction to declare BEFORE running (WS3 preliminary):**
The loss Q2(mm) - Q2(vec) should track TV_W(t), not TV(t), because:
  - TV_B causes between-group distortion → chooses a different point on the
    frontier → no Q2 loss in optimal assembly.
  - TV_W causes within-group distortion → breaks the Prop-1 scalarisation
    argument within each group → loss in optimal assembly.

TV_W(t) for the path A_j(t) = ρ_j^t should be computed from corpus_amplitudes.py
BEFORE running WS2. This is the pre-declared estimand.

## WS3 — TV_B / TV_W decomposition and foreclosure  [PENDING]

- Compute TV_B(t) and TV_W(t) along the A_j(t) path.
- Propose foreclosure/misalignment proposition: condition under which
  TV_W alone (not TV) determines Q2 loss in optimal assembly.
- If confirmed by WS2 data, add as corollary after rem:definitional in §6.

## WS4 — Article restructuring  [PENDING — after WS2 data]

- §8.7: insert amplitude table from WS1 corpus.
- §8.6: insert TV_W(t) prediction and WS2 regression.
- Corollary after rem:definitional: Extension of Prop. 1 (affine norms,
  multi-criterion groups → Q2=1 in optimal assembly).
- rem:scope: update to reference TV_W, not TV, as the operative measure.

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
