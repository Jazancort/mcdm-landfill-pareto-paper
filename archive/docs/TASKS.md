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
| Próximo item | Gate 1 full (unicidade dos trios, portfolio a 1e-12) + F8 passo 5 |

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
- [x] **C.7** Integrar no manuscrito: §7.8 adicionada com macros \\EsixPtwoMono, \\EsixPtwoLossyN, \\EsixPtwoPAll, etc. PDF: 30 páginas, exit 0.

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

### P2: Critério pré-registado falhou — ρ<0 presente em todas as famílias (mas 27–40% instâncias constantes)

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
| lognormal | 10/30 | 19/20 | **20/20** | p<0.001 |
| beta13 | 12/30 | 17/18 | **17/18** | p<0.001 |
| uniform | 8/30 | 22/22 | **22/22** | p<0.001 |
| zero_inflated | 2/30 | 27/28 | **28/28** | p<0.001 |

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

### Síntese final (números definitivos)

| | Resultado | Qualificação |
|---|---|---|
| P1 | Confirmada | Verifica implementação |
| P2 | Critério falhou; monotonia 87/88 onde testável (p=0.000) | Manter "on this instance"; DEV-E6-002 |
| P3 | Passa pelo critério pré-reg; sem suporte entre informativas | Reportar ambos; DEV-E6-001 |
| P4 | Sem suporte; tendência oposta borderline (53/87, p=0.053) | Não conclusivo; DEV-E6-003 |

**Resultado principal:** TV_W não prediz a magnitude da perda. A direcção é correcta onde há efeito (P2 corrigido: 87/88). A concentração da esparsidade importa, mas o E6 não isola esse factor.

### DEV-E6-005 — E6 cell F targeted TV_W = 0.199 (rho_raw) instead of 0.195 (rho_shift)

**Descoberta:** A corrida do E6 usou `TW_F = TV_W_VEC = 0.1986` como alvo de bissecção para a
célula W_inf_F. O valor correcto com rho_shift (a fórmula do código) é `TV_W = 0.1954`.

**Impacto:** As instâncias de W_inf_F foram bissectadas para TV_W ≈ 0.199 em vez de 0.195.
Diferença absoluta = 0.003 (1.6% relativo). L e H são fixos (0.10 e 0.30); só F muda.

**Corrida de sensibilidade (pendente):**

  - Alvo: `TW_F = 0.1954` (correcto)
  - Variável de ambiente: `E6_TARGET_TVW=0.1954 uv run python run_e6.py`
  - Output para: `results/e6/e6_raw_sensit_tvwF.csv`
  - Regra de decisão (a anotar antes de lançar):
    "Veredicto igual se P1-P4 derem a mesma conclusão (passa/falha) e o mesmo lado de p=0.05
    em todas as famílias e no All. Contagens podem diferir em ±2 por família."

**RESULTADO DA CORRIDA DE SENSIBILIDADE (executada 2026-10-xx, Athena):**

  Premissa DEV-E6-005 estava incompleta: TW_F entra em TRÊS células, não só W_inf_F.
  Células afectadas: W_inf_F (26/24000 draws Q2 diferente), V_inf_F (22/24000),
  W_def_F (41/24000). Células M, B, W_inf_L, W_inf_H idênticas bit-a-bit.
  tvw_achieved verificado localmente via bissecção determinística:
    W_inf_F: prespec=0.198600 sensit=0.195400 delta=+0.003200
    V_inf_F: prespec=0.198600 sensit=0.195400 delta=+0.003200
    W_def_F: prespec=0.198600 sensit=0.195400 delta=+0.003200

  CSV: results/e6/sensit/e6_raw_sensit_tvwF01954.csv
  SHA-256: 0a8dfc528140d8bfb63d85bd1b31c839ea2afc250e2c933e72bcbfa51ebb774a
  rows=168000, code_commit=14f93c3

  RESULTADO DA REGRA DE DECISÃO:
  - P1: IGUAL (48000/48000 em ambas)
  - P2 primário (Mono=85/88): IGUAL. NDistinct mudou 52->50 (2 instâncias passaram
    de 3 niveis a 2 com a mudança de W_def_F). Conclusão: inalterada.
  - P3: PreregN mudou 98->99 (+1). InfStrict inalterado (36/58 vs 36/57). p mudou
    0.043->0.031. Ambos abaixo de 0.05. Veredicto: inalterado.
  - P4: PREVISÃO FALHOU. p=0.053003 (principal) -> p=0.047525 (sensit).
    Cruza o limiar de 0.05. Pela regra "mesmo lado de p=0.05", o veredicto DIFERE.
    NOTA: a estimativa praticamente nao muda (53/87=0.609 vs 51/83=0.614).
    A proporcao rounded e 0.61 em ambos. So o p atravessa um limiar arbitrario por 0.005.
    INTERPRETACAO CORRECTA (conforme decisao 2026-10-xx):
      A corrida principal continua a ser a de referencia. O framing muda:
      o P4 deixa de ser "borderline nao conclusivo" e passa a ser "fragil":
      a proporcao e estavel mas o p atravessa 0.05 com a correccao de 0.003 no alvo.
      Texto §7.8 a usar: ver secao "Texto para §7.8" abaixo.

**Nota:** A corrida principal (TW_F=0.199, e6_raw_prespec.csv) mantém o papel de resultado
pré-registado. A corrida de sensibilidade é reportada numa frase na §7.8 e numa tabela
no suplemento.

| DEV | Previsão | Original | Actual | Razão |
|---|---|---|---|---|
| E6-001 | P3, P4 | Proporção sobre todas (empates contam) | Também reportar instâncias informativas + binomial | Empates a 100% enviesam os dois lados |
| E6-002 | P2 | Spearman sobre {0, L, F, H} | Também reportar Q2(H)<Q2(L) sem nível 0 | Nível 0 fixado a 100% pela P1 |
| E6-003 | P4 | Teste 1-lado (direcção prevista) | Teste 2-lados | Direcção observada oposta |
| E6-004 | Todas | — | 200 draws no E6 vs 500 no E1 | Custo computacional |

### Texto proposto para §7.8 (números finais confirmados)

```
P1 held on every draw of every instance. P2 failed its pre-specified
criterion in three of four families: 27--40% of instances under
continuous marginals showed no loss at any TV_W level. Among instances
with detectable loss, 85 of 88 showed the monotone ordering L $\geq$ F $\geq$ H
with H strictly below L (two three-way ties and one reversal counted as
failures; one-sided binomial with null = 1/6, p < 0.001; DEV-E6-002). P3 met
its pre-specified criterion in all four families, but most successes
were ties at 100%; among informative instances no family was significant
(one-sided binomial p >= 0.08; DEV-E6-001). P4 was not supported; the
observed trend runs counter to the prediction: in 53 of 87 instances with a
detectable directional difference (the remaining 33 pairs were within tolerance),
deflating the most heavily weighted criterion produced strictly larger losses
than inflating it -- the prediction was that inflating would be more costly
(p = 0.053, two-sided binomial on the 87 non-tied instances, post hoc; DEV-E6-003).

At TV_W = 0.199, the loss was 10.7 pp in the zero-inflated family and
below 3 pp otherwise, against 35.8 pp on Fogo. At equal TV_W, losses
differ by an order of magnitude across marginal families, confirming
that TV_W alone does not determine the cost (Remark rem:TVW). Point
masses are associated with larger losses. Whether concentrating sparsity
in a single high-weight criterion is more harmful than distributing it
uniformly is not tested here.
```

**Notas sobre os testes reportados no §7.8:**
### P2 — nula correcta (Poisson-binomial)

A contagem de 85 inclui três padrões:
- 52 com ordem estrita L > F > H (n_distinct=3, p_i=1/6)
- 33 com um empate (L=F ou F=H, n_distinct=2, p_i=1/3)
- 2 empates triplos (contados como falhas, p_i=0)

Usar null=1/6 uniformemente para os 88 seria anti-conservador (subestima sucessos esperados: 14.7 vs 20.0 correcto). O teste correcto é Poisson-binomial com p_i por instância.

Resultados (compute_e6_macro_stats, Poisson-binomial confirmado 2026-10-21):
- E[sucessos sob nula] = 20.00
- p (Poisson-binomial, one-sided) = 6.78e-55 → p < 0.001
- p (binomial null=1/6, anti-conservador) = 4.60e-62 (mais pequeno, anti-conservador confirmado)
- Sensitivity: 52/88 strictly distinct → p = 3.46e-19 → p < 0.001

Ambos p < 0.001. A conclusão não muda; a nula declarada passa a ser correcta.

Macros adicionados: `\EsixPtwoMono{fam}` (85 all, renomeado de Strict), `\EsixPtwoStrictOnly{fam}` (52 all) e `\EsixPtwoPAll` (Poisson-binomial). `\EsixPtwoStrict` é proibido em check_consistency.py.

### Consequências para main.tex

1. Abstract: substituir frase dos 35.8 pp (ver proposta da análise do revisor).
2. Contribuição (iv): manter "on Fogo" (regra do PRESPEC aplicada).
3. Remark rem:TVW: actualizar com resultado do E6 — direcção suportada, magnitude específica.
4. §7.7: adicionar "on Fogo; the synthetic test of §7.8 does not reproduce this amplification reliably."
5. §8.5 recomendação: "check for point masses before normalising."
6. Limitações: "The synthetic test draws criteria independently, without spatial correlation, and applies the zero-inflation to every criterion."

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

## F8 — circularity benchmark

**Script:** `scripts/compute_f8_circularity.py`  
**Resultados existentes:** `results/f8/f8_circularity.csv` (commit 43b8427, 02/10/2026)

### Resultados confirmados (N=500, KAPPA=200, SEED=42)

| obj_norm | score_norm | assembly | Q2 | SE |
|---|---|---|---|---|
### Resultados confirmados com código actual (N=500, KAPPA=200, SEED=42)

**Nova corrida: Athena, commit e678d32, `tmux f8`, 2026-10-21 09:07–09:25**

| obj_norm | score_norm | assembly | Q2 | SE | per-draw violations |
|---|---|---|---|---|---|
| vec | vec | optimal | **100.0** | 0.000 | **0/500** |
| vec | mm | optimal | **94.4** | 1.028 | 28/500 |
| vec | vec | greedy | **100.0** | 0.000 | **0/500** |
| vec | mm | greedy | **72.4** | 1.999 | 138/500 |

**Theorem 1: 500/500 draws on frontier (0 violations)** — confirmado por `f8_per_draw.csv`, `n_draws(Q2 < 100) == 0` para vec/vec/opt. Idêntico ao log de `43b8427`.

Resultados guardados em `results/f8/f8_per_draw.csv` e `results/f8/f8_run_current.log`.

**Macros exactamente iguais ao CSV**: `\FEightVecOptQ{100.0}`, `\FEightMMOptQ{94.4}`, `\FEightVecGrdQ{100.0}`, `\FEightMMGrdQ{72.4}`.

### Arqueologia (2026-10-21)

- Commit `9cdceb4` (2026-10-02): versão buggy com injection approach → 89.4% para vec/opt (double-normalisation + aspect misclassification)
- Commit `4d0a98d`: fix para direct vec objectives; mini-run: 100%
- Commit `43b8427`: full run N=500 → 100.0% confirmado; macros corrigidos

### Scorer equivalence (passo 2, 2026-10-21)

`mm_saw`: diff = 0.00e+00 — IDÊNTICO entre F8 e scoring.py. `vec_saw`: divergência de 9.23e-02 esperada por design inicial (F8 usava L2(X_adj) vs scoring.py usa L2(X_via)).

**Fix (commit 4d01e06):** F8 corrigido para usar L2(X_via) = convenção do artigo (rho_j = 1/||X_via||, confirmado: perm=0.583, aspect=0.103, urban=0.107). TV_vec = 0.311 ≈ macro TVvec=0.315.

Diferença F8 vs artigo era APENAS em critérios COST (perm, slope, roads). INV, BENEFIT e aspect: idênticos. A versão anterior tinha rho_perm=0.052 vs artigo 0.583 (factor 11×). TV_vec(F8 antigo) = 0.184 vs artigo 0.311.

**Nova corrida com vec corrigido (v2, Athena, commit 4d01e06):** resultados IDÊNTICOS à corrida anterior:
- mm/opt: 94.4% SE=1.03 (472/500 on frontier)
- mm/grd: 72.4% SE=2.00 (362/500)
- vec/opt: 100.0% (500/500) ← Theorem 1 confirmado
- vec/grd: 100.0% (500/500)

Cenário D (confirmado): os resultados idênticos são esperados e corretos. A "correcção" mudou `X_adj_vec` que era código morto desde o início; o scoring real usava `C_vec_raw` que já calculava a fórmula correta. Não houve fronteira diferente (cenário B seria errado). Ver diagnóstico v2 abaixo.

**Diagnóstico v2 (sessão 2026-10-21):** os resultados idênticos eram suspeitos. Investigação confirmou
que `X_adj_vec = X_adj_mm / L2_via` (a linha "corrigida" em 4d01e06) era **código morto** — nunca usada
no scoring nem nos objectivos. O scoring usa `C_score_vec` construído de `C_vec_raw`, onde:
`C_vec_raw[:,j] = _mm_norm(x_j) / L2(_mm_norm(x_j)) = X_via_raw[:,j] / L2_via[j]` para colunas
não-aspect. Logo a fórmula correcta (ρ_j = 1/L2_via) estava no código desde o início.
Assertiva `np.allclose(L2_raw, L2_via)` adicionada ao script para confirmar em tempo de execução.
`X_adj_vec` marcado como "DIAGNOSTIC ONLY" no docstring. Resultados são genuínos, não de cache.

O TV=0.311 (F8) vs 0.315 (artigo) deve-se à coluna aspect: F8 usa encoding binário {0,1};
o artigo calcula ρ_j sobre os graus brutos (Fase 1.3, "6.7% discrepância" no DATA_DICTIONARY).

### Pendente (passo 5)

- Validar a **fronteira vectorial** (tamanho, não-dominância, completude exacta): o script usa `build_pareto_utils` internamente mas o resultado não foi verificado com um bloco independente ao estilo do validate_core.
- TV_W plausibility para 94.4% (mm/opt loss = 5.6 pp): calcular TV_W da razão de amplitudes mm/vec e comparar com E4 reference (\TVWrj = 0.082, loss = 0 pp; \TVWinvrj = 0.085, loss = 11.6 pp). Se TV_W(mm/vec) < 0.082, 5.6 pp é plausível.
- Script agora grava `results/f8/f8_per_draw.csv` (per-draw), necessário para a próxima corrida na Athena.
- Correr o script actualizado na Athena com `tmux new -s f8` para regenerar f8_per_draw.csv com o código corrigido.

### Pré-existente em main.tex

L1102: `— that the` (em-dash como separador em prosa). Pré-existente, não da sessão actual. Corrigir com a §7.8.

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
| e5cc06a | feat: run_e6 parallel mode (--family, --merge) |
| ce53f64 | results: E6 complete — P1 OK, P3 OK all families, P2 power-limited, P4 falsified |
| ac23f6b | results: E6 tie decomposition — P3 not supported, P4 reversed, zero_inflated structural note |
| 22d5d29 | docs: corrected E6 analysis — tie decomposition, P3 not supported, P4 reversed |
| 7446e47 | results: E6 final stats — P2 87/88 monotone (p=0.000), P4 bilateral corrected, DEV-E6-001-004 |
| 985999d | docs: E6 final numbers — P2 87/88 monotone, P4 bilateral, DEVs 001-004, §7.8 text |
| 0446f54 | docs: E6 synthesis + DEVs final — §7.8 text with corrected numbers |
| 7209993 | feat: Phase 0/1 — DATA_DICTIONARY.md + validate_core.py (7/7 quick checks PASS) |
| f958933 | fix: validate_core — remove duplicate Pareto block, portfolio check informational, 8/8 PASS |
| f5615bb | fix: validate_core — idx1/2/3 column detection, dual path for Pareto CSV |
| c48766a | fix: validate_core gate 1 — 15/15 PASS (trace, completeness, index remap, pareto A, portfolio) |
| b1bae3c | fix: validate_core path fallback for pareto_front_A.csv (results/ before scripts/results/) |

---

## Gate 1 — diagnóstico técnico (sessão 2026-10-20+)

### Nota sobre o commit f5615bb — "EXPECTED estava errado"

O commit f5615bb adicionou detecção de colunas idx1/idx2/idx3 depois de um FAIL no portfolio check. A causa real não era EXPECTED errado: era uma convenção de índices. Os CSVs usam índices df_all (0–472); o fogo_trios.npy usa índices A' (0–388). A mapeação `pos_Ap[df_all_idx] = A'_idx` resolve. O portfolio {180,346,376} em A' é exactamente {184,430,460} em df_all — mesmos sítios físicos em dois sistemas de indexação. O EXPECTED não estava errado; o diagnóstico inicial estava.

### Causa do max_diff = 7.17e-08 em A'

- CSV dtype: float64. Float32 round-trip error = 9e-17. **Causa: float32 intermediate em space_aprime.py.**
- `space_aprime.py` casts os F por sítio para float32 antes de somar trios: `f1P = objs_P["f1"].values.astype(np.float32)`. O CSV armazena estes valores float32-precision como float64. validate_core usa float64 do princípio ao fim → 7e-8 = erro de quantização float32 (≈ F × 2^-23 ≈ 0.27 × 1.2e-7 ≈ 3e-8 por sítio).
- Confirmado: reprodução float32 → CSV: max diff = 9e-17 (match exacto). float64 vs CSV: max diff = 7e-8.
- **A nota anterior ("não-associatividade de ponto flutuante") estava errada.** O teste de round-trip float32 (resultado 9e-17) CONFIRMAVA a origem float32 — eu tirei a conclusão errada.
- A-norm (ref=473) vs CSV dá max_diff = 0.11 → CSV usa A'-norm. Não mudou.
- Impacto nos checks de gate: verificado com sweep completo (ver abaixo).

### A/A' — distinção correcta (nota de 2026-10-21)

Tanto o Pareto A como o Pareto A' usam os **mesmos 1.9M trios de A'-sítios (fogo_trios.npy)**. O que difere é apenas a referência de normalização:
- A' space: A'-sítios com A'-norm (ref=389) → 181 trios
- A space: A'-sítios com A-norm (ref=473) → 213 trios

**A distinção "espaço A" não significa "incluir os 84 sítios excluídos".** Os trios são sempre sobre os 389 admissíveis. A análise com 2.9M trios (473 sítios) era uma pergunta diferente — não corresponde ao que o manuscrito calcula.

Acção pendente: confirmar no main.tex que os 213 e 132 estão correctamente descritos como "A'-sítios com normalização A" (ver grep abaixo).

### Sweep de tolerâncias — Pareto A' (todos os 1.9M trios, float64)

**Argumento principal (igualdade de conjuntos):** os checks 8b (não-dominância) e 8c (completude exata) passaram em float64. O CSV foi gerado com float32. O facto de o mesmo conjunto de 181 trios ser tanto não-dominado como completo em float64 significa que o float32 e o float64 produziram a **mesma fronteira**. Não há margem a invocar — é uma igualdade directa.

### Sweep de tolerâncias — Pareto A' (todos os 1.9M trios, float64)

**Argumento principal (igualdade de conjuntos):** os checks 8b (não-dominância) e 8c (completude exata) passaram em float64. O CSV foi gerado com float32. O facto de o mesmo conjunto de 181 trios ser tanto não-dominado como completo em float64 significa que o float32 e o float64 produziram a **mesma fronteira**. Não há margem a invocar — é uma igualdade directa.

**Argumento secundário (ε-dominância):** o sweep abaixo confirma que a fronteira é estável sob ε-dominância para ε ≤ 1e-5. "ε-dominância" aqui: o dominador pode ser até ε pior num objectivo desde que seja mais de ε melhor noutro (ge relaxado, gt apertado). Não implica "margem > ε em todos os objectivos".

```
EPS      dom_within   escaped    tempo  (TODOS os 1.9M trios — confirmado 2026-10-21)
0        0            0          1.2s
1e-9     0            0          1.3s
1e-8     0            0          1.4s
1e-7     0            0          1.3s
1e-6     0            0          1.3s
1e-5     0            0          1.4s   ← confirmado em 2026-10-21 (não apenas 50k)
```

O Pareto A' float32 e o float64 são **IDÊNTICOS** sobre estes 1.9M trios. Gate definitivamente limpo.

### Completude em A — verificada (2026-10-21)

```
EPS      dom_within   escaped    tempo
0        0            0          1.7s
1e-9     0            0          1.6s
1e-7     0            0          1.6s
1e-6     0            0          1.6s
1e-5     2            0          1.6s   ← 2 pares ε-dominados mutuamente; escaped=0
```

Pareto A (213 trios, A-norm, sobre 1.9M A'-trios) está verificado. Completude (escaped=0) mantém-se a ε=1e-5. Não-dominância interna (8a) falha a ε=1e-5: 2 trios tornam-se ε-dominados, confirmados como não sendo o portfolio.

**Dois trios ε-dominados a eps=1e-5 em A (gap mínimo):**
- {42, 288, 376}: gap = 2.24e-06 (dominator: {203, 366, 376})
- {49, 237, 386}: gap = 6.99e-06 (dominator: {35, 260, 386})
- Portfolio {180, 346, 376}: NÃO está na lista — confirmado seguro.

F-values match float64 a 9.71e-17 (CSV foi gerado com float64, ao contrário do A' CSV que usa float32).

**Precisão mista:** A' CSV usa float32-precision, A CSV usa float64. A intersecção |A∩A'| = 132 compara fronteiras de precisões diferentes. Hoje as duas são idênticas em float64, mas o cast em space_aprime.py devia ser removido para eliminar a assimetria explicativa. Acção: regenerar pareto_front_Aprime.csv sem cast float32, confirmar 181/213/132 inalterados.

### DEV-G1-001 — FECHADO

Portfolio {184, 430, 460} está no Pareto A (confirmado). O pipeline (space_aprime.py) usa A'-trios para ambos A e A'. O check em validate_core está correcto. DEV-G1-001 fechado.

### Acções abertas para completar o Gate 1 formalmente

- [x] ~~Confirmar que o pipeline usou A'-trios para o portfolio (fechar DEV-G1-001)~~ ← FECHADO
- [ ] Adicionar comparação de F-values do portfolio a 1e-12 com os valores do manuscrito (Tab. 3)
- [x] ~~Calcular completude em A (opcional)~~ ← CALCULADA e LIMPA

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

---

## Previsões para a ida à Athena (escritas antes de lançar)

Data: 2026-10-21 | Commit: 7e9c79a

### E1 — por draw (corrida nova, output por draw)

| Verificação | Previsão |
|---|---|
| E1-V Q2_optimal | 56,8% |
| E1-V portfolios vs SAW/vec/opt, por draw, mesma seed | 500/500 idênticos |
| E1-W Q2_optimal | 64,2% (perda 35,8 pp) |
| Precisão | float64, eps=1e-9, N_DRAWS=500, seed=42 |

Se 500/500 bater: generate_macros_e1.py passa a ler o CSV por draw; log fica no arquivo.
Se E1-V < 500/500 ou Q2 diferir > 0,1 pp: re-examinar scoring path antes de publicar.

Nota: EoneWloss=35,8 não tem cruzamento independente (ao contrário de EoneVloss=43,2 que bate com o factorial). Esta é a única previsão unilateral — confirmada só pela corrida.

### E6 — corrida de sensibilidade

Parâmetros: E6_TARGET_TVW=0.1954, L=0.10, H=0.30, seeds iguais.

Regra de decisão (pré-registada):

| Critério | "Veredicto igual" |
|---|---|
| P1 | passa em ambas as corridas |
| P2 | mesmo resultado passa/falha; p do mesmo lado de 0,05; contagens ±2 por família |
| P3 | mesmo resultado passes/falha |
| P4 | mesmo resultado passa/falha; p do mesmo lado de 0,05 |

Se igual: uma frase na §7.8 + tabela suplementar com as duas corridas. Macros com prefixo \EsixSens.
Se diferente: discussão na §7.8; corrida principal continua a ser a pré-registada.

### F8 — passo 5

1. Tamanho da fronteira: verificar não-dominância e completude exacta (chunks).
2. Sweep de ε nos A' (1e-7 e 1e-5): 0 escaped em ambos.
3. Coincidência greedy = óptimo por draw: medida, não assumida.
   Previsão dedutiva: em vec/mm, draws com greedy ≠ óptimo tem de ser ≥ 110
   (derivação: mm tem 138 Q2=0 e vec tem 28 Q2=0; se fossem os mesmos 28, o mínimo seria 138-28=110).
   Se der menos, há bug.
   Em vec/vec: 100% em ambos (Proposição 1), coincidência trivial; não tem implicação.

### Sensibilidade raw

Método: células vec com pesos multiplicados por rho_shift/rho_raw para slope, coast, wells, aero (factor 1,02 a 1,04). Perm, aspect, rivers, protected, urban, aero, cult: factor 1 (min=0).
Previsão: Q2 muda poucos pp. Fronteira recalculada com pesos raw antes de comparar.

---

## Correcções ao diagnóstico do E1

- O E1 scoring usa `build_N` com `X_adj` (leeward=1 para aspect, benefício orientado).
  O `c_site` (leeward=0) é só para os objectivos F1/F2/F3, não para o score SAW.
  Diagnóstico anterior de "inconsistência de c_site" estava errado. Retirada a referência a DEV-E4-007 no contexto do E1.
- CSV e1_v3_results_DRYRUN_N10_DEV-E1-004.csv: dry-run de 10 draws, SE=15,8% confirma exactamente. Não é bug. Não é corrida inválida. É um ensaio curto compatível com 56,8% (P(X<=5, n=10, p=0.568) ≈ 22%).

---

## PRESPEC Santiago Phase 0 — registo de proveniência e erros corrigidos

### classify_pf.py — três ajustes para coincidir com T1

A regra P-F foi implementada em `scripts/classify_pf.py` e testada contra os 28 cod_forms
da T1 (Annex A do PRESPEC). Para que os 28/28 passassem, foram necessários três ajustes ao
código. Todos baseados exclusivamente no texto das legendas da camada IDECV; nenhum usou
dados espaciais, áreas, ou distribuição geográfica das formações.

| # | cod_form afectado | Ajuste | Justificação |
|---|---|---|---|
| 1 | CB | Adicionou verificação de conteúdo parentético nas cláusulas ignoradas por `_is_skip`. `CB` tem lit `"Formação dos Flamengos (Mantos, piroclastos, chaminés)"`: o prefixo "Formação" é ignorado como nome de formação, mas o conteúdo `(Mantos, piroclastos, chaminés)` revela carácter de lava → Baixa. Sem este ajuste, CB retornava NC (nenhum primeiro termo primário após ignorar a cláusula). | Apenas texto da legenda. |
| 2 | de | Adicionou `'duna'` (singular) a `_ALTA_PREFIXES` ao lado de `'dunas'` (plural). `de` tem lit `"Duna, eluviões (Quaternário)"`: o primeiro token é singular "Duna". Sem este ajuste, retornava NC. | Apenas texto da legenda. |
| 3 | dv | Adicionou `'depósitos de vertente'` a `_MEDIA_PREFIXES`. `dv` tem lit `"Depósitos de vertente (Quaternário)"`. Sem este ajuste, "Depósitos" não matchava nenhum prefixo e retornava NC. | Apenas texto da legenda. |

Impacto na partição S-T: o ajuste 1 (CB) é o único que afecta a partição Baixa/não-Baixa.
Os ajustes 2 e 3 afectam apenas sub-classificações dentro de não-Baixa (Média vs NC), que
são irrelevantes para o critério de distância em S-T. O assert em `check_consistency.py`
verifica a partição Baixa; avisos são gerados para divergências de sub-classe.

### Erros de proveniência corrigidos nesta fase (pré-tag)

| Erro | Causa verdadeira | Commit de correcção |
|---|---|---|
| "96/94 pode ser erro de coordenadas" | A causa era a amostragem (`np.round` vs `src.index`), não precisão das coordenadas. O floor1m+land grid com src.index dá exactamente 94/94. | 4561462 |
| "elevation_utm.tif não é o ficheiro que gerou o CSV" | O ficheiro gera o CSV correctamente; a causa dos valores errados era a amostragem, não o ficheiro de origem. | cf9a1e3 → 4561462 |

### R-asp — artigo pendente (não bloqueia a tag)

O critério R-asp no artigo (Tabela 7) usa o azimute verdadeiro no score contínuo. A
reflexão θ → (270°−θ) preserva o indicador binário [90°,180°] mas altera o valor
contínuo e portanto os macros `\RaspOptimal`, `\AspSpearman`, `\AspTopQuartile`, e os
valores 24.0%/20.0% da Tabela 7. Os números têm de ser recalculados com a fórmula
correcta `arctan2(-dx, dy)` antes da próxima revisão do artigo. Não bloqueia a tag
`prespec-santiago-f0`.

---

## PRESPEC Santiago Phase 0 — hash imutável

Tag: `prespec-santiago-f0`
Commit (HASH_F0): `5ead7f594e48241189c5b7396a1d6ddd9edafd5a`
Data: 2026-10-26
Tagger: Julio Azancort <julioazancortneto@gmail.com>

A partir deste commit o texto do Phase 0 é imutável.
Qualquer mudança a §3–§6 do PRESPEC é um DEV-S-### com data, razão e direcção esperada.
Phase 1 é appendada num commit separado; o texto do Phase 0 nunca é editado depois.

---

## Consequências do aspecto reflectido no artigo de Fogo

### O que é afectado (aspecto contínuo)

`run_e4_vstar.py` e `run_fourthcell_consistent.py` lêem `slope_aspect (degrees)` do CSV
publicado (convenção notebook: 270°−θ) e usam esses valores brutos como azimute contínuo.
Estes scripts calculam o R-asp.

Macros e secções do artigo que precisam de ser recalculados:

| Macro / local | Recalcular como |
|---|---|
| `\RaspOptimal` (24.0%) | `run_e4_vstar.py` com `asp_correct = (270 - asp_notebook) % 360` |
| `\AspGrd` (25.2%) | idem |
| `\AspSpearman` | `compute_aspect_polecoding.py` com aspecto corrigido |
| `\AspTopQuartile` | idem |
| Tabela 7: 24.0% e 20.0% | macros regenerados |
| Remark 5: exemplo 350° | fórmula correcta (350° notebook = 280° correcto = W-facing) |

### O que NÃO é afectado

O pipeline factorial (mcdm_experiment.py) binariza o aspecto: `c = 1.0 if asp in [90,180]`.
A binarização é invariante sob a reflexão ([90°,180°] mapeia para si próprio). Portanto:
- Q2 (SAW, TOPSIS, min-max, vector, greedy, optimal): CORRECTO
- R (regret, não-asp): CORRECTO
- E1, E6: CORRECTOS
- Teorema 1 e Proposição 1: CORRECTOS

### Caminho para corrigir

```python
# Em run_e4_vstar.py e run_fourthcell_consistent.py, antes de usar asp:
asp_notebook = df_imp[COL["aspect"]].values.astype(float)
asp_correct  = (270.0 - asp_notebook) % 360.0  # converter para azimute geográfico
```

### Outros itens do artigo pendentes

1. DATA_DICTIONARY.md: adicionar nota que `slope_aspect (degrees)` está em convenção notebook (270°−θ), não azimute geográfico. O hash do ficheiro não muda.
2. Renomear "leeward" para "SE-facing (90°–180°)" no artigo (ou acrescentar nota explicativa).
3. Registar limitação: o intervalo [90°,180°] não tem justificação encontrada na fonte.
4. Zenodo/OSF: fazer upload da série de tags f0, amend1–amend4b antes da Fase 1 de Santiago.

### Estado das tags prespec-santiago

| Tag | Commit | O que resolve |
|---|---|---|
| `prespec-santiago-f0`        | 5ead7f5 | Phase 0 base |
| `prespec-santiago-f0-amend1` | 648e54b | tolerância DEM; null Baixa; NFC; teste sintético |
| `prespec-santiago-f0-amend2` | f42f89e | nodata slope exclusão; leeward meteorológico; CRS assert |
| `prespec-santiago-f0-amend3` | fe2e362 | cone test oracle; geotransform assert; [90,180] fechado |
| `prespec-santiago-f0-amend4` | b20df70 | data 2026-10-26T15:05Z; Andrade2015 não inspeccionado; remove especulação caldera |
| `prespec-santiago-f0-amend4b`| 6143c88 | compute_edges WITH confirmado (hell.tif = slope nodata match) |

**Estado para Fase 1:** bloqueado por Zenodo/OSF. Pronto tecnicamente.

---

## Estado actual do Remark 5 / R-asp (ANTES do recálculo com fórmula correcta)

Registado em 2026-10-26 antes de qualquer recálculo. Valores com convenção notebook (270°−θ):

| Macro | Valor actual | O que mede |
|---|---|---|
| `\AspSpearman` | 0.018 | Spearman(azimute contínuo normalizado, indicador binário leeward) |
| `\AspSpearmanP` | 0.73 | p-value do Spearman (não correlacionado) |
| `\AspTopQuartile` | 98 | % dos sítios no quartil superior do aspecto contínuo com indicador 0 |
| `\RaspOptimal` | 24.0% | Q2 da célula R-asp (codificação mista: score contínuo, objectivos binários) |
| `\RaspLoss` | 76 | = 100 − 24.0 pp (custo da codificação) |

Texto da Remark 5 (linhas 2255–2263 do main.tex):
"Scoring aspect as a continuous azimuth while the objectives use a binary leeward
indicator introduces a non-monotone mismatch (ρ=0.018; all 98% top-quartile sites carry
indicator zero), reducing Q2 from 100% to 24.0% under SAW/min-max/optimal: 76 pp
through coding alone."

Após o recálculo, registar aqui se a conclusão muda ou não.

---

## R-asp recalculation record — resultado contra Remark 5 pré-existente

Registado em 2026-10-26. Remark 5 antes do recálculo (convenção notebook):
- Custo de discrepância: 76 pp (Q2 = 24.0%)
- Correlação: ρ = 0.018, p = 0.73 (não correlacionado)
- R1-6 (R-asp − R-V, opt): +4.0 pp [+2.2, +6.0]

Resultado com fórmula geográfica correcta (arctan2(-dx, dy)):
- Custo de discrepância: 84 pp (Q2 = 15.6%): aumentou 8 pp
- Correlação: ρ = -0.445, p < 0.001 (anti-correlacionado): mudou de sentido
- R1-6 (R-asp − R-V, opt): -4.4 pp [-7.2, -1.4]: inverteu o sinal

Controlo: células sem aspecto (RV_star_Aprime, RM_Aprime, RV_star_A, RM_A) são
idênticas bit a bit ao run anterior. R-V (20.0%, 19.6%) também não mudou — confirma
que só o caminho do aspecto contínuo foi alterado.

Comparação: os dois resultados são distintos numericamente. A conclusão central
(codificação inconsistente é destrutiva) mantém-se; a magnitude aumentou e a
correlação passou de ruído a anti-correlação significativa. Nenhum valor foi
escolhido pelo resultado favorável — o pré-registo da Remark 5 estava documentado
em TASKS.md antes do recálculo (ver secção anterior).

## V2 (ocean=nodata) max|Δ| no teste de codificação do mar

V1 (ocean=0 válido):  max|Δ| = 0.0000° em 7241 células costeiras (arredondamento
                                exacto a float64; valor medido: < 1×10⁻⁶°)
V2 (ocean=nodata):    max|Δ| = 0.0000° (ambas as variantes dão resultado idêntico
                                porque no código V2 preenche NaN com 0 antes de
                                convolucionar, reproduzindo efectivamente V1)

Conclusão real: as duas variantes são indistinguíveis com a implementação em Python
porque V2 substitui NaN por 0 antes da convolução. Para distingui-las formalmente
seria necessário implementar Horn com NaN verdadeiro (sem preenchimento). A conclusão
de que ocean=0 é a codificação correcta vem da contagem de células válidas
(11 696 622 células com valor 0 E válidas no hell.tif), não da comparação V1/V2.


---

## Clarificações pós-sessão (2026-10-28)

### AspSpearman — transformação validada contra DEM

`\AspSpearman` = −0.445 usa a transformação `(270 − θ_nb) % 360` para converter
o aspecto no CSV (convenção do notebook, 270°−θ) para azimute geográfico correcto
(arctan2(−dx, dy)). A transformação foi validada contra o DEM por cálculo directo
de arctan2(−dx, dy) sobre o raster: máximo Δ circular entre os dois métodos = 0.000107°
(< 1 × 10⁻⁴°), com 0 células planas. O Spearman ρ = −0.445 e todos os valores
derivados em Remark 5 (§6.7) usam o azimute transformado.

### κ = 50 no log de run_fourthcell_consistent.py

O log dizia "four cells, all with aspect binary (kappa=50)". Isso é correcto e não
contradiz o R-asp calculado com kappa=200. As quatro células do run_fourthcell
(RV_star, RM, em A e A') usam o indicador binário SE-facing. O indicador binário
é invariante sob a correcção de fórmula (ambas as convenções de aspecto produzem
o mesmo conjunto de 94 sites SE-facing, Δ simétrico = 0). Com coding binário,
o kappa = 50 e kappa = 200 produzem exactamente os mesmos trios-ótimos, porque
a fronteira de Pareto sobre a coluna binária não muda com o limiar de distância.
Apenas a célula R-asp usa aspecto contínuo, e essa é a que foi corrigida.


---

## Histórico completo do R1-6 (correcção de 2026-10-28)

A "inversão de sinal" registada na sessão anterior era um artefacto. O sinal correcto é POSITIVO (R-asp > R-V) em todos os três estados.

| Estado | R-asp | R-V | R-asp − R-V |
|---|---|---|---|
| As duas células reflectidas (original) | 24,0% | 20,0% | +4,0 pp |
| Convenções misturadas (commit intermédio) | 15,6% | 20,0% | −4,4 pp |
| As duas células geográficas (correcto) | 15,6% | 6,2% | +9,4 pp |

O estado intermédio ("−4,4 pp") foi causado por: R-asp usa (270−θ_nb)%360 (correcto) mas R-V ainda usava θ_nb directo (reflectido). A mistura de convenções inverteu o sinal. Com as duas células na convenção geográfica, o sinal é o mesmo do original (+), e a magnitude é maior.

O 9,4 pp igual para óptimo e greedy (15,6−6,2=9,4 e 15,8−6,4=9,4) é uma coincidência aritmética. Os intervalos de confiança são diferentes ([6,6;12,4] e [6,4;12,6]), confirmando bootstraps independentes.

## Inventário de scripts que usam slope_aspect (2026-10-28)

| Script | Como usa o aspecto | Convenção | Corrigido? | Resultados no artigo? |
|---|---|---|---|---|
| run_fourthcell_consistent.py | Contínuo (R-asp: 389-base; R-V: 473-base) via aspect_utils | Geográfica | SIM (2026-10-28) | SIM (RaspOptimal, RVoptimal, ResidualRef*) |
| run_e4_vstar.py | R-V*: binário (invariante); R-asp secundário: contínuo | R-V*: N/A; R-asp: notebook (não corrigido) | R-V*: N/A; R-asp: NÃO | R-V*: SIM (RVstarOptimal/Greedy). R-asp: NÃO usado no artigo |
| validate_core.py | Só contagem binária n1=94 | Notebook (mas check binário é invariante) | N/A | NÃO (diagnóstico) |
| check_aspect_impact.py | Só contagem binária n1=94 | Notebook (invariante) | N/A | NÃO |
| diag_p3.py | Lê raw; diagnóstico | Notebook | NÃO | NÃO |
| diag_r14.py | Lê raw; verifica estrutura binária | Notebook | NÃO | NÃO |
| _verify_amend3.py | Lê raw para oracle test | Notebook (intencional — testa θ_pub) | N/A | NÃO |
| compute_f8_circularity.py | Binário via _build_decision_matrix | N/A | N/A | SIM (FEight* macros) — SEGURO |
| run_e6.py | Binário via _build_decision_matrix | N/A | N/A | SIM (Esix* macros) — SEGURO |
| run_e1.py | Binário via _build_decision_matrix | N/A | N/A | SIM (E1 macros) — SEGURO |
| run_e5_grid.py | Grid sintético — sem Fogo aspect | N/A | N/A | SIM (E5 macros) — SEGURO |
| aggregation_strata.py | Sem aspecto | N/A | N/A | SIM (F1 macros) — SEGURO |
| generate_macros_amplitudes.py | Binário via _build_decision_matrix | N/A | N/A | SIM (amplitude macros) — SEGURO |

**Conclusão**: todos os resultados relevantes para o artigo usam aspecto binário (invariante) ou a convenção geográfica corrigida (via aspect_utils.py). O único script com a convenção errada (run_e4_vstar.py / R-asp secundário) não é citado no artigo.

**Prevenção**: aspect_utils.py criado como módulo centralizado. check_consistency.py deve proibir leituras directas de slope_aspect fora desse módulo.
