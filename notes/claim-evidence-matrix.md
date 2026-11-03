# H3 — Matriz afirmação → evidência

**Data:** 2026-10-02  
**Propósito:** cada frase do resumo e cada highlight aponta para uma tabela, macro ou teorema.

---

## Resumo — afirmações e evidências

| # | Afirmação no resumo | Evidência | Localização |
|---|---------------------|-----------|-------------|
| A1 | "normalisation is worth +25.4 pp of Pareto efficiency under greedy assembly" | `\NormGreedyContrast` | macros.tex L6 ← bootstrap_contrasts.log |
| A2 | "SAW–TOPSIS not significant pooled (+0.5 pp)" | `\AggContrast`, `\AggLo`, `\AggHi` | macros.tex L7–9 ← aggregation_strata.csv |
| A3 | "sign depends on cell (-8.4 to +4.4 pp)" | `\AggStratumMMgrd`, `\AggStratumVecopt` | macros.tex L101–105 ← aggregation_strata.csv |
| A4 | "Exact assembly gains +8.1 pp under min-max" | `\AsmMM` | macros.tex L13 ← bootstrap_contrasts.log |
| A5 | "loses 10.2 pp under vector" | `\AsmVec` | macros.tex L14 ← bootstrap_contrasts.log |
| A6 | "exact assembly is Pareto-efficient iff amplitudes constant within groups" | Theorem thm:groupconst | main.tex L1133 |
| A7 | "between-group distortion alone costs nothing; within-group 35.8 of 43.2 pp" | `\EoneWloss`, `\EoneVloss` | macros.tex L18–19 ← e1_results.csv |
| A8 | "criterion encoded inconsistently reduces Q2 from 100% to 24%" | `\RaspOptimal` | macros.tex L119 ← e4-audit/fourthcell_consistent.csv |
| A9 | "consistent encoding: greedy gain +11.8 pp CI[+8.8,+14.8]" | `\RefSetGreedyGain`, `\RoneTwoGrdCIlo`, `\RoneTwoGrdCIhi` | macros.tex L111–113 ← r1_decisions.json |

---

## Highlights — afirmações e evidências

| # | Highlight | Evidência | Localização |
|---|-----------|-----------|-------------|
| H1 | "Effective weight scales with w_j A_j; min-max alone preserves elicited weights" | Lemma (amplitude identity) | main.tex eq:weff |
| H2 | "Normalisation worth +25.4 pp; aggregation +0.5 pp pooled (sign cell-dependent)" | `\NormGreedyContrast`, `\AggContrast`, `\AggStratumMMgrd`, `\AggStratumVecopt` | macros.tex |
| H3 | "Exact assembly helps under min-max (+8.1 pp) but hurts under vector (-10.2 pp)" | `\AsmMM`, `\AsmVec` | macros.tex |
| H4 | "Between-group distortion costs nothing; within-group drives the loss" | E1 cells B and W, tab:e1 | main.tex tab:e1 |
| H5 | "Coding 100%→24%; consistent encoding greedy +11.8 pp, optimal 0 pp" | `\RaspOptimal`, `\RefSetGreedyGain`, R1-decisions | macros.tex + r1_decisions.json |

---

## Verificação

Todas as afirmações quantitativas do resumo e dos highlights têm:
- Uma macro LaTeX com nome descritivo
- A macro gerada por um script em commit identificado
- Nenhum número hardcoded na prosa (grep limpo em H1)

**Estado: PASS**
