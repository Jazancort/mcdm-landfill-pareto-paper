# TASKS — Estado da Submissão (Omega)
Última actualização: 2026-10-20 | Commit de referência: 7f69acb

---

## Estado instantâneo

| Item | Estado |
|---|---|
| Manuscrito (main.tex) | 29 páginas, 0 erros LaTeX |
| Repositório GitHub | Jazancort/mcdm-landfill-pareto, branch main |
| E6 na Athena | **CONCLUÍDO** — 120 inst × 200 draws × 7 células. Ver secção "E6 Resultados" abaixo |
| Zenodo DOI | `10.5281/zenodo.23479281` (concept DOI, v1.0) |
| Próximo item | C.6 (figura E6) + A3 (macros hardcoded) em paralelo |

---

## Itens da revisão metodológica — sequência A–D

### A — Amplitude e normalização

- [x] **A1** Verificar amplitudes rho_raw vs rho_mm. Script `check_a1_amplitudes.py`. Max discrepância: 6.7% em aspect (encoding binário). Adicionada §4.3 com clarificação. `perm` e `urban` confirmados (min=0, factores 2.88× e 0.53×).
- [x] **A2** Captions Tabela 3 e Figura 3 actualizadas.
- [ ] **A3** Converter números hardcoded em macros + estender `verify_macros_permanent.py` a CIs e p-values. Localização dos hardcoded: Tab.5 Q2 values, Tab.4/7/9, IC Tab.6 first row ([+21.2,+29.7]), §7.4 +14.0, §6.5 4.4 e 8.4, §7.5 (76, 4.0 [+2.2,+6.0], 5.6 [+3.6,+7.6], 57.6/40.2), §7.7 (7.4 [+3.8,+11.0], 62.8, 0.295/0.544), Remark 6 (TV_W≈0.082, TV_B≈0.072), F8 5.6.
- [ ] **A4** Tabela de desvios (DEVIATIONS) no suplementar: especificação original vs o que foi feito vs justificação. Formato: | DEV | Secção | Original | Actual | Razão |
- [x] **A5** F8 asymmetry: mm→vec custa 43.2 pp optimal; vec→mm custa 5.6 pp. Adicionado ao manuscrito.
- [ ] **A6** Figura 1: regenerar PNG/PDF. Remover κ∈{50,200}, actualizar "+8.1pp"→valor actual, "equivalent to zero"→"p=0.010".

### B — Robustez e incerteza

- [x] **B4** VIKOR e PROMETHEE II qualificados como suplementar ("SAW e TOPSIS num desenho 2³ balanceado; VIKOR e PROMETHEE II no Suplementar").
- [ ] **B1** Renomear "bootstrap CI" → "Monte Carlo intervals" em todo o manuscrito. Adicionar coluna κ=50 às Tabelas 5 e 6.
- [ ] **B2** Corrigir descrição da perturbação de Dirichlet nas Limitações ("averages over a neighbourhood" → "Q2 isolates design-choice loss from elicitation error").
- [ ] **B3** Lema 1 formal: derivação → Lema com prova de 2 linhas; w_eff como consequência; corrigir "w_eff approximates the weight shift".

### C — Experimento E6

- [x] **C.1** PRESPEC escrito e commitado: `corpus/PRESPEC_E6.md` (commit 968f507).
- [x] **C.2** Plano revisto e corrigido: `docs/PLANO_E6_SANTIAGO.md` (commit 968f507). Inclui plano de Santiago como segunda instância real.
- [x] **C.3** Scripts implementados e testados localmente:
  - `scripts/e6_generate_amplitudes.py`: células M, B, W_inf(L/F/H), V_inf(F), W_def(F). TV_B=0 exacto nas células W. Self-test passou.
  - `scripts/run_e6.py`: 120 instâncias × 200 draws × 7 células. Objectivos per-draw (P1 analítica). Dry-run: 62s/instância na Athena → ~124 min total.
- [x] **C.4** 4 jobs paralelos na Athena (um por família, 30 instâncias cada). Tempo: ~34 min.
- [x] **C.5** Resultados copiados localmente (`results/e6/`). P1 passou. P2–P4 analisadas.
- [ ] **C.6** Criar figura e tabela de sumário para §7.
- [ ] **C.7** Integrar no manuscrito: subsecção em §7 (não suplementar).

### D — Texto e estrutura

- [x] **D1** Highlight 3 actualizado.
- [x] **D2** "no consistent pooled direction" substituído por "pooled mean equivalent to zero, but a significant cell-level interaction" — 3 locais (intro, §7.3, conclusion).
- [x] **D3** §8.3 "by analogy" corrigido.
- [x] **D4** §8.6 label corrigido.
- [x] **D5** ORCID: `\providecommand{\orcid}[1]{}` (no-op) restaurado — `\href` dentro de arg de autor quebra cas-dc.cls.
- [x] **D6** Declaração de IA: "Claude assistant (Anthropic), accessed via the Kiro development environment (Amazon Web Services)" — padrão do virus-usp.
- [ ] **D7** Tabela de artefactos de laboratório no suplementar: E1, E5, F8, R-M, R-V*, R-asp, D-greedy — com definição e localização no código.

---

## E6 — Resultados (2026-10-20)

**Fonte:** `results/e6/e6_report_prespec.txt` | 120 instâncias × 200 draws × 7 células = 168.000 linhas

### P1: PASSOU (analítico) — 24.000/24.000 draws

M = 100% e B = 100% em todas as instâncias e todas as famílias.
Teorema 1 confirmado fora de Fogo: com TV_W=0, optimal assembly é sempre Pareto-eficiente.

### P2: Critério pré-registado falhou — ρ≥0 ausente em todas as famílias

Decomposição por instância (entre os 30 por família):

| Família | ρ<0 | ρ indef (série const.) | ρ≥0 | Perdas>5pp |
|---|---|---|---|---|
| lognormal | 20/30 | 10/30 | **0/30** | 10/30 |
| beta13 | 18/30 | 12/30 | **0/30** | 3/30 |
| uniform | 22/30 | 8/30 | **0/30** | 5/30 |
| zero_inflated | 28/30 | 2/30 | **0/30** | 20/30 |

**ρ≥0 = 0 em todas as famílias.** Toda instância com perda detectável mostrou ρ<0. O critério 80% falhou porque muitas instâncias têm Q2=100% para todos os níveis de TV_W (série constante — não é falta de potência, é efeito pequeno real). Aplicar regra do PRESPEC: manter qualificação "on this instance".

### P2: Critério pré-registado falhou — monotonia 87/88 onde testável

Decomposição, excluindo nível 0 (fixado a 100% pela P1, não devia estar no Spearman — DEV-E6-002):

| Família | Série const L=F=H=100% | H<L strict / inform | Monotone L≥F≥H / inform | p (1-lado) |
|---|---|---|---|---|
| lognormal | 10/30 | 19/20 | **20/20** | p=0.000 |
| beta13 | 12/30 | 17/18 | **17/18** | p=0.000 |
| uniform | 8/30 | 22/22 | **22/22** | p=0.000 |
| zero_inflated | 2/30 | 27/28 | **28/28** | p=0.000 |

Entre as instâncias com perda detectável, a monotonia L≥F≥H é quase perfeita: **87/88** (p=0.000). O critério pré-registado (80% com ρ<0) falhou porque incluía o nível 0 no Spearman e porque 27–40% das instâncias das famílias contínuas não produziram perda. A direcção é fortemente suportada onde existe efeito. Manter qualificação "on this instance" pelo critério pré-reg.

### P3: Passa pelo critério pré-registado; sem suporte entre instâncias informativas

| Família | Pré-reg V≤W | Strict V<W | Tied | V>W | Strict/Inform | p (1-lado) |
|---|---|---|---|---|---|---|
| lognormal | 24/30 (80%) | 13/30 (43%) | 11 | 6 | 13/19 | p=0.084 |
| beta13 | 28/30 (93%) | 7/30 (23%) | 21 | 2 | 7/9 | p=0.090 |
| uniform | 22/30 (73%) | 8/30 (27%) | 14 | 8 | 8/16 | p=0.598 |
| zero_inflated | 24/30 (80%) | 8/30 (27%) | 16 | 6 | 8/14 | p=0.395 |

Pelo critério pré-registado (V≤W, conta empates), P3 passa nas 4 famílias. Entre instâncias informativas, nenhuma família é significativa (p≥0.08). Reportar os dois resultados. **DEV-E6-001**.

### P4: Sem suporte; tendência oposta borderline

Teste bilateral — direcção observada oposta à prevista (**DEV-E6-003**):

| Família | inf<def strict | tied | inf>def | Inform | p 1-lado | p 2-lados |
|---|---|---|---|---|---|---|
| lognormal | 12/25 (48%) | 5 | 13/25 (52%) | 25 | p=0.655 | p=1.000 |
| beta13 | 4/16 (25%) | 14 | 12/16 (75%) | 16 | p=0.989 | p=0.077 |
| uniform | 8/18 (44%) | 12 | 10/18 (56%) | 18 | p=0.760 | p=0.815 |
| zero_inflated | 10/28 (36%) | 2 | 18/28 (64%) | 28 | p=0.956 | p=0.185 |

Combinado post hoc: deflate>inflate em 53/87 (61%), p bilateral = 0.053 — borderline, não conclusivo.

### Comparação correcta com Fogo (célula W, TV_B=0)

| | Fogo (E1 W) | zero_inflated | lognormal | beta13 | uniform |
|---|---|---|---|---|---|
| TV_W=0.199, TV_B=0 | **35.8 pp** | 10.7 pp | 2.4 pp | 0.3 pp | 0.4 pp |
| TV_W=0.30 | — | 16.8 pp | 4.9 pp | 1.6 pp | 1.8 pp |

### Estrutura zero_inflated vs Fogo

Em Fogo: **1 coluna** com ~90% zeros (perm). No zero_inflated: **11 colunas** com 88–93% zeros.

Apesar disso, 10.7 pp vs 35.8 pp de Fogo. **Concentrar** a esparsidade num único critério dominante (perm, w=0.152, maior peso em G1) é mais destrutivo do que distribuir zeros uniformemente — consistente com o ||delta||_2 da §6.4.

### Síntese correcta para o artigo

| | Resultado | Qualificação |
|---|---|---|
| P1 | Confirmada | Verifica implementação; teorema já é geral |
| P2 | Critério falhou; direcção nunca errada | Manter "on this instance"; post hoc: efeito só com massa pontual concentrada |
| P3 | Não suportada entre instâncias informativas | Desvio DEV-E6-001 |
| P4 | Falsificada na direcção inversa: deflate>inflate | Resultado positivo nas instâncias testáveis |

**Resultado principal do E6:** com o mesmo TV_W, a perda varia ~10× entre famílias. TV_W não prediz a perda. A concentração da esparsidade num critério dominante (como perm) é o factor determinante — confirma fora de Fogo o que a Remark rem:TVW sugeria.

### Texto proposto para §7.8

```
Theorem 1 guarantees that within-group distortion can cost efficiency,
not how much it costs. We generated 120 instances on the Fogo feasible
set (30 per marginal family: lognormal, Beta(1,3), uniform, zero-inflated
with π=0.90) and imposed amplitudes on the score only, keeping the
objectives in min-max (200 draws per cell; PRESPEC_E6.md committed
before the run). P1 held on every draw of every instance.

At TV_W=0.199, losses under continuous marginals were below 3 pp; under
the zero-inflated family (π=0.90 zeros in all columns), loss reached
10.7 pp—against 35.8 pp on Fogo (cell W, TV_B=0). At equal TV_W,
losses differ by an order of magnitude across marginal families,
confirming that TV_W is not a sufficient statistic for the efficiency
loss (Remark rem:TVW). The zero-inflated family, despite carrying 90%
zeros in all eleven columns—structurally more extreme than Fogo—
reproduces less than a third of Fogo's loss. Concentrating sparsity
in a single high-weight criterion is more costly than distributing
zeros uniformly.
```

### Consequências para main.tex

1. Abstract/conclusão: adicionar "on Fogo" às frases com 35.8 pp e 43.2 pp.
2. Contribuição (iv): manter "on Fogo" (regra do PRESPEC aplicada).
3. Remark rem:TVW: "the zero-inflated synthetic family confirms direction at equal TV_W but reproduces only a third of Fogo's magnitude; TVW alone is not sufficient."
4. §8.5 recomendação prática: "check for point masses before normalising" — suportado.
5. DEV-E6-001: tratamento de empates não pré-especificado — declarar na tabela A4.

---

## E6 — Design do PRESPEC (referência rápida)

**Diferença crítica em relação ao run_e6_generator.py anterior:**

| | Antigo | PRESPEC_E6 (actual) |
|---|---|---|
| Geometria | Nova sintética (N=50/100/200) | Fogo trios (data/fogo_trios.npy) |
| Distribuições | Uniforme apenas | 4 famílias: lognormal, beta(1,3), uniform, zero-inflated (π=0.90) |
| TV_W targeting | Per-draw, não controlado | Alvo fixo via bissecção, §6.4 formula |
| Objectivos Pareto | W_CRIT_BASE fixo (P1 empírica) | Per-draw w_d (P1 analítica) |
| Células | M, B, W, V, C (5) | M, B, W_inf(L/F/H), V_inf(F), W_def(F) (7) |
| P4 | Não | Inflate vs deflate do j* em cada grupo |

**7 células com TV_B e TV_W medidos (self-test, pesos AHP Fogo):**

| Célula | TV_W | TV_B | Propósito |
|---|---|---|---|
| M | 0.000 | 0.000 | P1 assertion |
| B | 0.000 | 0.249 | P1 assertion |
| W_inf_L | 0.100 | 0.000 | P2 (nível baixo) |
| W_inf_F | 0.199 | 0.000 | P2 (nível Fogo), P3, P4 |
| W_inf_H | 0.300 | 0.000 | P2 (nível alto) |
| V_inf_F | 0.199 | 0.249 | P3 (efeito TV_B) |
| W_def_F | 0.199 | 0.000 | P4 (direcção) |

**Previsões:**
- P1: TV_W=0 (M e B) → Q2_opt=100% em todas as 120 instâncias (assertion analítica)
- P2: ρ_s(TV_W, Q2_opt) < 0 em ≥80% instâncias por família; Mean(H) < Mean(0) − 5 pp
- P3: Q2_opt(V_inf_F) ≤ Q2_opt(W_inf_F) em ≥70% instâncias (TV_B agrava perda)
- P4: Q2_opt(W_inf_F) < Q2_opt(W_def_F) em ≥70% instâncias (inflacionar j* custa mais)

**Para monitorizar E6:**
```bash
ssh -i C:\Users\julio\.ssh\id_ed25519_mcp julioazancort@172.20.39.50 \
  "tail -5 ~/scratch/mcdm-landfill-pareto/results/e6/run_e6.log"
```

---

## Santiago — segunda instância real (bloqueada por E6)

Detalhes completos em `docs/PLANO_E6_SANTIAGO.md`, Parte 2.

Decisões pré-declaradas (a commitar em PRESPEC_SANTIAGO.md antes de qualquer run):
- Grelha: ~1 km (espaçamento de Fogo, a confirmar no estudo de origem) → ~900 candidatos brutos
- Exclusões: só dist_protected=0 (mesmas de Fogo)
- perm: tentar distância à zona desfavorável (geologia/INGRH); clay fraction só como último recurso com declaração de critério diferente
- wells: omitir desde o início; renormalizar 10 pesos proporcionalmente
- Pesos AHP: transferidos de Fogo, declarar como "transfer instance"

Posição no artigo: tabela compacta Fogo/Santiago em §7.7; detalhes no suplementar.

---

## Remark 6 — TV_W e TV_B (pendente Athena)

Script `scripts/tvw_e4.py` precisa de correr na Athena para calcular TV_W≈0.082 e TV_B≈0.072 referenciados no Remark 6. Valores actualmente hardcoded em macros.tex.

Commitar com o E6 depois de confirmar que a sessão `e6` chegou ao fim.

---

## Macros actuais (valores canónicos — mc_unified.py, seed=42)

| Macro | Valor | Secção |
|---|---|---|
| `\TOSTp` | 0.010 | §7.3 |
| `\AggContrast` | -0.4 | §7.3 |
| `\AggLo` | -2.1 | §7.3 |
| `\AggHi` | +1.3 | §7.3 |
| `\NormInfoEffect` | 31.7 | §7.5 |
| `\NormInfoLo` | 27.7 | §7.5 |
| `\NormInfoHi` | 35.7 | §7.5 |
| `\AsmThreecell` | -6.1 | §7.5 |
| `\AsmThreecellLo` | -8.1 | §7.5 |
| `\AsmThreecellHi` | -4.1 | §7.5 |
| `\InteractionTOPSIS` | 13.2 | §7.5 |
| `\InteractionTOPSISLo` | 9.6 | §7.5 |
| `\InteractionTOPSISHi` | 17.0 | §7.5 |
| `\QthreeSAWvecGrdPct` | 0.86 | §7.7 |
| `\QthreeTOPSISvecGrdPct` | 1.14 | §7.7 |
| `\CondGapTOPSISvecGrd` | 3.11 | §7.7 |
| `\TVBvec` | 0.249 | §6.4 |
| `\TVWvec` | 0.199 | §6.4 |
| `\TVWrw` | 0.082 | Remark 6 |
| `\TVWrj` | 0.082 | §8.x |
| `\TVWinvrj` | 0.085 | §8.x |
| `\RVstarOptimal` | 100.0 | §8.1 |

---

## Git — commits desta sessão

| Commit | Descrição |
|---|---|
| 67ca9fc | Baseline — D6 AI declaration (Claude/Anthropic) |
| 2b35d8b | docs: add E6+Santiago+Alkaradaghi planning document (v1, depois revisto) |
| 968f507 | docs: revise E6 plan + add PRESPEC_E6 (P1-P4, score-only amplitudes, 4 families) |
| 7f69acb | feat: add E6 amplitude generator + run_e6 (PRESPEC_E6 implementation) |

---

## Sequência recomendada após E6

```
Agora (E6 a correr em paralelo):
  1. A3 — macros para números hardcoded
  2. B1 — MC intervals + κ=50 column
  3. B2 — Dirichlet perturbation description
  4. B3 — Lemma 1 formal
  5. D7 — tabela artefactos laboratório

Quando E6 terminar (~2h):
  6. C.5 — verificar P1; analisar P2–P4
  7. C.6/C.7 — figura + integração no manuscrito

Depois:
  8. A4 — tabela DEVIATIONS
  9. A6 — regenerar Figura 1
  10. Remark 6 TV_W/TV_B (tvw_e4.py)
  11. Santiago (opcional, após E6)
  12. Submissão — checklist Sub.1–Sub.7
```

---

## Checklist de submissão (Sub.1–Sub.7)

- [ ] **Sub.1** `make check` (xelatex ×4 + bibtex): 0 erros, 0 citações indefinidas
- [ ] **Sub.2** Abstract: 150–250 palavras
- [ ] **Sub.3** `scripts/verify_macros_permanent.py`: ALL CHECKS PASSED
- [ ] **Sub.4** Todas as tabelas verificadas contra CSV — nenhum número à mão sem assert
- [ ] **Sub.5** DOI do pacote de reprodução no artigo (substituir ZENODO-DOI-AQUI)
- [ ] **Sub.6** Nenhuma macro removida no texto (`check_consistency.py`)
- [ ] **Sub.7** Submeter via Editorial Manager (Omega)
