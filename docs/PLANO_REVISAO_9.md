# Plano de Revisão para 9/10 — Omega/EJOR/C&OR

**Nota actual:** 6/10 (major revision)
**Alvo:** 9/10
**Commit de referência:** f475928 | Criado: 2026-10-21 | Última actualização: 2026-10-21

---

## Estado resumido

| Fase | Conteúdo | Estado | Nota estimada após |
|---|---|---|---|
| F475 | Itens urgentes da revisão de f475928 | 4/6 feitos | 6.5 |
| A | 20 erros factuais do PDF | 5/20 feitos (A3-A7) | 7.0 depois de tudo |
| G | Build check alargado + Figura 1 no pipeline | 0/5 | 7.0 (evita -0.5 futuro) |
| C | F8 matriz 2x2 + reframing para Resultados | 0/6 | 7.5 |
| D | Correcções científicas pontuais | 0/6 | 7.8 |
| B | Métrica de regret de valor | 0/6 | 8.5 |
| E | Cortes estruturais + integração E6 | 0/10 | 8.5 |
| F | Segunda instância (Santiago) | 0/6 | 9.0-9.5 |

---

## LOG — O que foi encontrado e o que foi feito

Registo cronológico de descobertas, surpresas e decisões tomadas durante a execução.

### 2026-10-21 — Sessão inicial

**F475-1: Draws E1-V vs factorial — VERIFICADO**
Resultado: 500/500 match exacto. `e1_diag_bootstrap.csv` (e1v_opt_nd) e `mc_unified_raw.csv` (SAW/vector/optimal) têm sequências de draws idênticas draw a draw. Isto confirma que a §7.7 está correcta: "objectives, frontier, draws and feasible set are identical to the factorial". O argumento de probabilidade era forte: se draws fossem independentes, coincidência 284/284 seria p≈2.5%; match perfeito confirma mesma semente.

**F475-3: CRLF — resultado inesperado**
Ao verificar os SHAs, descobriu-se que os ficheiros no working tree tinham CRLF (Windows) mas os hashes registados no código eram LF (gerados na Athena). No entanto, depois de criar `.gitattributes` e converter 94 ficheiros para LF, o `git add -u` não detectou alterações nos CSVs/JSONs: a store do git já tinha as versões LF (da Athena). Ou seja, o problema era que o git estava a fazer checkout com CRLF (core.autocrlf=true) mas a guardar LF internamente. Com `-text` no `.gitattributes`, o working tree fica agora em LF.

Verificação final: os 4 SHAs canónicos (amplitudes.json, e1_diag_bootstrap.csv, f8_per_draw.csv, e6_raw_prespec.csv) batem com os valores LF registados. Isto fecha o problema de replicação.

**F475-4: Threshold errado na primeira tentativa**
A primeira implementação de `\RnkContinuousGainPct` usou threshold 0.985, que capturava urban (rho_rnk=0.9885) — resultado: 8 critérios em vez de 7. Ao inspeccionar os valores por critério (slope/roads/rivers/coast/protected/wells/aero = 0.9949, urban = 0.9885, cult = 0.9808), ficou claro que threshold 0.992 dá exactamente os 7 critérios sem tie mass. Corrigido antes do commit.

**A3: O erro era de conceito, não de cálculo**
`\FEightMMOptSE` (= SE = 1.0) estava a ser usado em L1150 onde o texto dizia "≈1.0 pp in the other direction". Mas o SE é o erro padrão da estimativa 94.4%, não a perda. A perda real é 100 - 94.4 = 5.6 pp. Foram criados dois macros distintos: `\FEightMMOptSE{1.0}` (já existia) e `\FEightMMOptLoss{5.6}` (novo). O hardcoded "5.6" na linha anterior (L1131) também foi substituído pelo macro.

**A4: Aero vs aspect — verificado no código**
Inspecção do `benefit` array via `_build_decision_matrix`: aspect é binário (min=0, max=1), aero tem valores contínuos com min > 0 (252.7 m). A lista "perm, urban, cult, aero, rivers" no §4.3 incluía aero incorrectamente e excluía aspect. Corrigido para "perm, aspect, urban, cult, rivers".

**A6: Inversão G1 vs G2 — confirmado no código**
Grupos: G1 = {perm, slope, roads} com benefit=False; G2 = {rivers, aspect, coast, protected, wells} com benefit=True; G3 = {urban, aero, cult} com benefit=True. O texto dizia que "distance criteria in G1 AND G2 enter as 1-x̂_j". Mas G1 (roads) não precisa de inversão: farther from roads = worse = larger c_j sem inversão. G2 (rivers, coast, wells) precisa: closer to sensitive receptor = worse, mas mm-norm(distance) é maior quando mais longe, por isso é preciso 1-x̂_j para ter "larger c_j = worse". Texto reescrito para apontar apenas G2.

**A7: Total de draws estava errado**
O texto dizia "Seven cells yield 24,000 total draws" mas 24,000 é o número por célula (120 inst × 200 draws). O total real é 7 × 24,000 = 168,000. Adicionados `\EsixNperdraw{200}`, `\EsixNcells{7}`, `\EsixNdrawsTotal{168,000}` ao macros_e6.tex. A descrição das 7 células foi expandida para incluir V_inf_F (P3) e W_def_F (P4), que não estavam descritas. O "TV_W = 0.20" substituído por `\EsixTargetTVW{0.199}`.

---

## Dúvidas em aberto

Questões que surgiram durante a execução e precisam de resposta antes de continuar.

**A2 (§6.8 — valores shift): FEITO (f08f1f7)**
Os três valores raw (`TV=0.3146`, `‖δ‖₂=0.3127`, `‖δ‖∞=0.2859`) foram substituídos por macros shift (`\TVvec`, `\DeltaLtwoshift`, `\DeltaLinfshift`). Ao mesmo tempo, `\TVvec`, `\TVBvec`, `\TVWvec` foram actualizados para 4 dp (eram 3 dp) para manter precisão consistente com os outros macros de delta. A linha hardcoded `0.311` na Tabela amplitude também foi substituída por `\TVvec`.

**A8 (§7.8 P2 — ties/reversals): FEITO (ad3f5a0)**
"excluded" → "counted as failures". Confirmação: as 3 instâncias (2 ties + 1 reversal) eram contadas como falhas no Poisson-binomial test, daí 85/88. O texto "excluded" era incorrecto.

**A9 (§8.3 e Conclusão — "divides by 0.53x"): FEITO (ad3f5a0)**
As 2 ocorrências restantes (L2737, L3018) corrigidas para "scales another by a factor of \UrbanRatioVec". A ocorrência da Intro já tinha sido corrigida em F475-4.

**G1 (fig_F1_slope_weights — amplitudes hardcoded): FEITO (ad3f5a0)**
`fig_F1_slope_weights.py` actualizado para ler `rho_j` de `results/amplitudes/amplitudes.json`. Antes: `A["vec"]["perm"] = 0.583` hardcoded (e outros 10 critérios). Diferença crítica: a razão efectiva de perm era 2.88× com os valores antigos, agora é 2.86× (consistente com `\PermInflation`). A diferença não veio do rho_perm em si (0.583 era igual nos dois casos) mas dos rho_j dos outros critérios, que afectam o denominador S. As amplitudes de midranks continuam hardcoded (justificado: não estão no amplitudes.json pois usam uma fórmula heurística diferente, documentado no script).

**Dúvida D?-8 (nova): "Figura 1 (p. 7)" do revisor — qual figura era?**
O revisor cita "Figura 1 (p. 7)" com "perm: 2.88×", "Aggregation: +0.5 pp", "Assembly: −1.1 pp", "+34.6 pp full 2³". O main.tex actual tem 5 figuras, nenhuma com estes valores como anotações de texto. A fig_F1_slope_weights.py mostra o rácio de RANK (0.62×) como label de texto, não o rácio vec (2.86×). A fig_F2_interaction.py (lê de mc_18cells_raw.csv) existe mas não está incluída no main.tex. Hipótese mais provável: o revisor viu uma versão mais antiga do paper onde uma figura de interacção tinha estas anotações. A correcção de G1 endereça o problema de fundo (amplitudes hardcoded). Clarificar com o revisor se necessário.

**A10-A17 (múltiplos itens): FEITOS (8f82ce9, 8173421)**

A10: "linearly independent when n₀ ≠ n₁" — condição removida. Matematicamente: x e 1-x são sempre linearmente independentes se x não é constante.

A11: τ_b=0.960 e top-100=0.960 eram ambos 0.960 — flagged pelo revisor como suspeito. Calculados via TOPSIS/vec com 389 sites admissíveis e W=AHP normalised: τ_b=0.9191, top-100=0.9400. São distintos (delta=0.0209). A coincidência 0.960/0.960 no paper era erro de cópia — um valor foi copiado sobre o outro. Não foi encontrado nenhum script original que produza 0.960 para nenhum dos dois valores. Script canónico criado: `compute_aspect_polecoding.py`.

A12: "Within this scope, Q₂ ... for min-max, ranks and vector" — a frase anterior dizia que midranks estão fora do âmbito exacto, mas depois incluía ranks sem qualificação. Adicionado "(heuristic: ranks fall outside the exact scope)" ao valor de ranks.

A14: "For completeness, we recall the reference-set amplitude ratio." — opener vago que não conectava o parágrafo ao tópico anterior (aspect encoding mismatch). "Table holds the evaluator fixed" aparece APENAS UMA VEZ (não havia duplicado — verificado). Oponer substituído por "For completeness, we note that the reference-set amplitude ratio is a separate source of mismatch when the normalisation set differs."

A15: §8.6 tinha dois parágrafos com título "Gap measure and weak dominance". Fundidos num único parágrafo com o label. "Regulatory grounding" tinha apenas 1 frase — expandida para 2 para ser uma subsecção completa.

A16: "slope (dimensionless gradient)" — DATA_DICTIONARY.md confirma: slope é derivado com `gdaldem slope` em graus. Corrigido para "slope (degrees)". Adicionalmente, "aspect (degrees)" foi corrigido para "aspect (binary leeward indicator)" para reflectir que o papel usa a codificação binária, não o azimuth bruto.

A17: "|𝒯| up to several hundred candidates" — 𝒯 é o conjunto de trios (1.94M portfolios). "Several hundred" aplica-se a N (candidatos individuais). Corrigido para "$N$ up to several hundred".
Condição `n₀ ≠ n₁` removida. x e 1-x são sempre linearmente independentes quando x não é constante (ou seja, quando n₀ > 0 e n₁ > 0). A condição era redundante e matematicamente incorrecta como escrita.

**A11 (§6.9 — τ_b=0.960 = top-100=0.960): FEITO (8f82ce9)**
Verificação via `compute_aspect_polecoding.py` (TOPSIS/vec, 389 sites, W=AHP normalised):
- τ_b computado: 0.9191 → arredondado para `\AspectTauB{0.92}`
- Top-100 agreement: 0.9400 → `\AspectTopKAgree{0.94}`
- Os dois valores são distintos (delta=0.0209) — confirma que o 0.960/0.960 do paper era um erro de cópia.
- Script canónico criado em `scripts/compute_aspect_polecoding.py`.
- Não foi encontrado o script original que gerou 0.960 — indica que os valores foram inseridos manualmente.

**A17 (§2.3 — |𝒯| several hundred candidates): FEITO (8f82ce9)**
`($|\Tset|$ up to several hundred candidates)` → `($N$ up to several hundred)`. O `\Tset` no manuscrito é o conjunto de trios (1.94M portfolios), não o conjunto de candidatos individuais.

**A19 (referências diacríticos): NÃO ERA PROBLEMA**
refs.bib já tem os diacríticos correctos em Unicode: `Kadziński, Miłosz` e `Słowiński, Roman`. O Select-String no Windows tinha mostrado sem Unicode, induzindo em erro. Nenhuma alteração necessária.
Implementou-se `\nbootEone{10,000}` e actualizou-se a frase da §7.7 que reporta o IC do E1. Mas a Tabela 6 e a §5.4 mencionam "\nboot-replicate bootstrap" no contexto geral. Revisar se a tabela caption precisa de nota explicando que E1 usa B=10,000 separado, ou se a declaração geral B=2,000 é aceitável enquanto a E1 tem a sua própria nota.

**D?-3 (F475-5, pendente): Auditoria bidirecional ainda não implementada**
A regra "depois de cada substituição de literal, confirmar o contexto" não foi implementada no `audit_hardcoded.py`. Está na lista mas precisa de código. Impacto: substituições futuras podem colocar macros no lugar errado sem detecção automática.

**D?-4 (Fase B, pré-análise): Onde estão os pesos w por draw?**
Para a métrica de regret R(t) = [V_w(t*) - V_w(t)] / range, preciso dos pesos w por draw. O `mc_unified_raw.csv` tem os portfolios seleccionados mas não os pesos. O `e1_diag_bootstrap.csv` tem as outcomes mas não os pesos. Os pesos são amostrados de uma Dirichlet — qual CSV guarda w_j para cada draw? Verificar `diag_e1b_greedy.py` e `run_e1.py` para perceber se o output inclui os pesos.

**D?-5 (A11, pendente): τ_b = 0.960 = top-100 = 0.960 — coincidência ou erro?**

**D?-6 (F8 Fase C): A fronteira F_mm existe algures?**
Para calcular a matriz 2×2 do F8, precisamos de F_mm (fronteira sob normalização min-max). A fronteira F_vec já existe em `results/f8/`. A F_mm pode ser calculada com a mesma pipeline mas usando scoring mm em vez de vec. Confirmar se `compute_f8_circularity.py` já tem infra para calcular F_mm, ou se é necessário novo código em `pareto_utils.py`.

**D?-7 (A16, pendente): Slope — graus ou gradiente adimensional?**
§4.1 diz "slope (dimensionless gradient)" mas pode ser graus. Verificar `fogo_constants.py` ou o CSV de origem. Impacto pequeno (nota de unidade) mas um revisor pode verificar.

---

## Fase F475: Revisão de f475928

### F475-1 — FEITO (commit: teste C:\tmp\test_e1_draws.py)
500/500 match. §7.7 está correcta. Nenhuma alteração ao manuscrito necessária.

### F475-2 — FEITO PARCIALMENTE (commit: 36e7f37)
Opção B implementada: `\nbootEone{10,000}` em macros_structural.tex; §7.7 diz agora "$B = \nbootEone$ replicates". Mas a §5.4 e a Tabela 6 continuam a usar `\nboot{2,000}` no contexto geral — ver D?-2 acima.

- [x] `\nbootEone{10,000}` adicionado a macros_structural.tex
- [x] Parágrafo da E1 actualizado com B=10,000 explícito
- [ ] Verificar se Tabela 6 / §5.4 precisam de nota sobre B distinto no E1
- [ ] Adicionar MUST_FAIL test para [3.8; 11.0] (não corresponde a nenhuma configuração)

### F475-3 — FEITO (commit: a7bc796)
`.gitattributes` criado, 94 ficheiros convertidos para LF, 4 SHAs canónicos verificados.

- [x] `.gitattributes`: `*.csv -text`, `*.json -text`, `*.npy binary`, `*.log -text`, `*.tex text eol=lf`, `*.py text eol=lf`
- [x] `git add --renormalize .` + commit
- [x] Verificar SHAs: amplitudes.json, e1_diag_bootstrap.csv, f8_per_draw.csv, e6_raw_prespec.csv — TODOS batem
- [ ] Documentar no README: hashes calculados sobre bytes LF (normalização `.replace(b"\r\n", b"\n")`)
- [ ] Actualizar scripts de verificação que calculam SHA para usar normalização LF

### F475-4 — FEITO (commit: 36e7f37)
`\RnkContinuousGainPct{12.1}`, `\UrbanRatioVec{0.53}`, `\AspectRatioVec{0.51}`, `\DeltaLtwoshift{0.3101}`, `\DeltaLinfshift{0.2835}` gerados e usados em main.tex.

- [x] `\RnkContinuousGainPct{12.1}` (threshold 0.992, exactamente 7 critérios)
- [x] `\UrbanRatioVec`, `\AspectRatioVec` (nomes correctos: são deflações, < 1)
- [x] `\DeltaLtwoshift` e `\DeltaLinfshift` para §6.8
- [x] main.tex: "divides by 0.53x" → "scales by a factor of \UrbanRatioVec"
- [x] main.tex: "all others gain 12%" → "seven fully continuous criteria gain ≈\RnkContinuousGainPct%"

### F475-5 — PENDENTE
Auditoria bidirecional: após cada substituição de literal, confirmar contexto. Ver D?-3.

- [ ] `git show f475928 -- main.tex` — rever linhas das substituições 1.77x/0.53x/0.51x
- [ ] Extender `audit_hardcoded.py` com modo inverso (macro → contexto onde aparece)

### F475-6 — PARCIALMENTE VIA FASE A
Os erros 1-7 do PDF correspondem a A1-A7. A3-A7 estão feitos. A1-A2 pendentes.

---

## Fase A: 20 Erros Factuais do PDF

### Grupo 1 — Números visivelmente errados

- [ ] **A1** Figura 1 (p.7): valores 2.88x, +0.5pp, -1.1pp, +34.6pp são antigos. Identificar qual `fig_*.py` gera a Figura 1 (provavelmente `fig_F2_interaction.py` ou `fig_interaction.py`). Regenerar a partir dos JSON. Adicionar ao Makefile target `figures` e ao build_check. Bloqueador: sem isto a afirmação de Code availability é falsa.

- [x] **A2** FEITO (f08f1f7): valores raw de §6.8 substituídos por macros (`\TVvec`, `\DeltaLtwoshift`, `\DeltaLinfshift`). `\TVvec`/`\TVBvec`/`\TVWvec` actualizados para 4 dp. Tabela amplitude: `0.311` hardcoded → `\TVvec`.

- [x] **A3** FEITO (6da59ed): `\FEightMMOptLoss{5.6}` criado. "≈1.0 pp in the other direction" → "≈\FEightMMOptLoss pp". Causa raiz: `\FEightMMOptSE` (SE=1.0) estava no lugar errado.

- [x] **A4** FEITO (6da59ed): `\texttt{aero}` → `\texttt{aspect}` em §4.3. Confirmado no código: aspect tem min=0 (binário), aero tem min=252.7 m.

- [x] **A5** FEITO (6da59ed): equação (weff_vec) corrigida de $x_j(a)$ para $\tilde{x}_j(a)$. Usa agora a notação shift, consistente com eq.(9) e Tabela 2.

### Grupo 2 — Erros de lógica ou notação

- [x] **A6** FEITO (6da59ed): §3.2 reformulado. Inversão $1-\hat{x}_j$ aplica-se ao G2 (proximidade a receptores sensíveis). G1 = {perm, slope, roads}: valores já denotam custo/severidade sem inversão.

- [x] **A7** FEITO (6da59ed): §7.8 expandido para descrever as 7 células. TV_W=0.20 → `\EsixTargetTVW{0.199}`. "24,000 total draws" → `\EsixNdrawsTotal{168,000}`. Adicionados `\EsixNperdraw{200}`, `\EsixNcells{7}`, `\EsixNdrawsTotal` ao macros_e6.tex.

- [x] **A8** FEITO (ad3f5a0): "excluded" → "counted as failures" em §7.8 P2.

- [x] **A9** FEITO (ad3f5a0): "divides another by 0.53x" → "scales another by a factor of \UrbanRatioVec" em §8.3 (L2737) e Conclusão (L3018). Intro já feita em F475-4.

- [x] **A10** FEITO (8f82ce9): "linearly independent when n₀ ≠ n₁" → condição removida. x e 1-x são sempre linearmente independentes quando x não é constante.

- [x] **A11** FEITO (8f82ce9): τ_b=0.960/top-100=0.960 → `\AspectTauB{0.92}` e `\AspectTopKAgree{0.94}`. Script canónico `compute_aspect_polecoding.py` criado. Verificado: nenhum script original encontrado para os valores 0.960 — era erro de cópia.

- [x] **A12** FEITO (8173421): §6.1 — "Within this scope, Q₂ ... for min-max, ranks and vector" agora qualifica ranks como "(heuristic: ranks fall outside the exact scope)". Mantém a informação mas assinala o âmbito.

- [x] **A13** FEITO (b8911a2): Tabela 3 (tab:canonical): (i) removido "blue diamonds" da caption; (ii) removida nota sobre sítios excluídos (nenhum portfolio na tabela inclui sítios excluídos — verificado); (iii) adicionada coluna "∈F" com valores do dominance test: SAW/mm/opt=yes, TOPSIS/mm/grd=yes, PROMETHEE/grd=yes, Source study=yes; restantes=no. Gap=0 ↔ ∈F coincidiu em todos os casos (confirmado via pareto_front_A.csv, df_all indices).

- [x] **A18** FEITO (b8911a2): (i) §6.10 "N vs. N′" → "A vs. A′"; (ii) §8.6 "$k=3$ minimisation objectives" → "three minimisation objectives" (k=portfolio size, não objectivos); (iii) §5.1: nota adicionada explicando subscripts Q₂, Q₃; (iv) t/T inconsistency verificada — não existe na versão actual.

- [x] **A19** FEITO: refs.bib já tem diacríticos correctos em Unicode (Kadziński, Słowiński). O Select-String não mostrava Unicode — não havia problema.

- [ ] **A20** Code availability: afirmação falsa enquanto A1 não fechado. Actualizar por último.

---

## Fase G: Build Check Alargado

- [x] **G1** FEITO (ad3f5a0): `fig_F1_slope_weights.py` lê `rho_j` de `amplitudes.json`. Perm: 2.88× → 2.86×.
- [x] **G2** FEITO (f09ad63): 9 novos BAD_PHRASES em `check_consistency.py` (§6.8 raw, tau_b copy-paste, blue-diamonds, divides-by-0.53). `aspect_polecoding.json` verificado. 23 regression cases.
- [x] **G3** FEITO PARCIAL (9ef2ebc): `audit_hardcoded.py` — suporte `% OK:`, DESIGN_EXACT alargado. main.tex: 90→48 RESULT?. TOPSIS Q₂ e NormGreedyContrastLo/Hi agora como macros. 208 no supplementary deferred.
- [ ] **G4** Adicionar `check_tab_amplitude.py` e `generate_macros_r1.py` ao Makefile `check`.
- [ ] **G5** Actualizar Code availability (A20) depois de A1 fechado.o para ler `rho_j` de `amplitudes.json`. Perm: 2.88× → 2.86×. Amplitudes de midranks mantêm-se hardcoded (documentadas no script: usam fórmula de rank não disponível no JSON).
- [ ] **G2** `check_consistency.py`: verificar os três valores de §6.8 contra macros shift.
- [ ] **G3** Alargar `audit_hardcoded.py` a supplementary.tex e tab_*.tex. Objectivo: exit 0 com excepções documentadas.
- [ ] **G4** Adicionar `check_tab_amplitude.py` e `generate_macros_r1.py` ao Makefile `check`.
- [ ] **G5** Depois de A1-A3 e G1-G3: actualizar Code availability (A20).

---

## Fase C: F8 Matriz 2x2 Completa

O `f8_circularity.csv` actual tem só 4 linhas (obj=vec × score=mm/vec). Faltam as 4 células obj=mm.

| | F_mm | F_vec |
|---|---|---|
| Score mm, opt | ~100% (Theorem 1) | ? |
| Score mm, greedy | ? | ? |
| Score vec, opt | 94.4% | 100% |
| Score vec, greedy | 72.4% | 100% |

Ver D?-6 sobre como obter F_mm.

- [ ] **C1** Estender `compute_f8_circularity.py` para F_mm.
- [ ] **C2** Criar nova tabela no manuscrito com as 8 células.
- [ ] **C3** Mover F8 da §5.4 (Métodos) para §7.x (Resultados).
- [ ] **C4** Reenquadrar o destaque: "custo de desalinhamento" em vez de "efeito da normalização".
- [ ] **C5** §5.4 passa a referenciar §7.x.
- [ ] **C6** Acrescentar as 8 células ao `check_consistency.py` e `generate_macros_f8.py`.

---

## Fase D: Correcções Científicas Pontuais

- [ ] **D1** Convenção de orientação vec (§4.3): justificar explicitamente a convenção TOPSIS. Sensibilidade: `\RhoPermInverted=0.052` já existe. Tabela no suplemento com as duas convenções.
- [ ] **D2** E1-P1, E6-P1, F8-vec/opt: reformular como "implementation consistency checks", não como falsificações empíricas.
- [ ] **D3** Agregação: remover TOST do destaque. "cell-dependent, ranging from -8.4 to +4.4 pp; no stable sign".
- [ ] **D4** TV_B + TV_W: "decomposition" → "components" ou "indices". Acrescentar inequação com W_g^eff.
- [ ] **D5** Novidade teórica: reduzir para 3 contribuições. Contribuição (v) PROMETHEE-Borda → suplemento.
- [ ] **D6** Incerteza no factorial: SE e IC na Tabela 5. Confirmar sítios 41, 385, 429 ∉ F′.

---

## Fase B: Métrica de Regret de Valor

O maior impacto individual. Q₂ mede pertença à fronteira de Pareto; o argumento normativo do artigo é sobre distorção de preferências. Sem esta métrica, um revisor pode dizer que a métrica principal contradiz a tese.

**Definição:**
```
R(t) = [V_w(t*_w) - V_w(t)] / [max_{s∈F} V_w(s) - min_{s∈F} V_w(s)]
```

Ver D?-4 antes de começar (localizar pesos w por draw).

- [ ] **B1** Criar `scripts/compute_regret.py`.
- [ ] **B2** Localizar pesos w por draw nos CSVs (ver D?-4).
- [ ] **B3** Agregar R por método × célula. Acrescentar à Tabela 5 ou como Tabela 5b.
- [ ] **B4** Verificar: TOPSIS/mm/opt tem R > 0 mesmo com Q₂=100%?
- [ ] **B5** Reformular §7.2 e abstract: Q₂ ≠ R.
- [ ] **B6** Definir R formalmente no manuscrito (§5.5 ou extensão de §5.1).

---

## Fase E: Cortes Estruturais

- [ ] **E1** Mover §6.5 (expoente α) e §6.6 para suplemento.
- [ ] **E2** §7.5 → Remark de 3-4 frases.
- [ ] **E3** Fundir §6.7 com §6.2.
- [ ] **E4** §7.8: já actualizado com 7 células (A7). Confirmar que está completo.
- [ ] **E5** Tabela única de orientação de critérios (substitui as 3 descrições em §3.2, §4.1, §4.3).
- [ ] **E6** Resolver notação inconsistente (A18).
- [ ] **E7** Integrar E6 na §8 (Discussão) e na Conclusão.
- [ ] **E8** §7.6: "no choice of w restores..." → "given the score, no reweighting restores...".
- [ ] **E9** Abstract/Intro: "473 sites enumerate 1,944,653" → "389 candidate sites yield 1,944,653 feasible portfolios of size three".
- [ ] **E10** Declaração de IA: rever segundo política Elsevier.

---

## Fase F: Segunda Instância (obrigatória para 9/10)

Uma única instância adversarial limita a nota a ≈8.5. Sem segunda instância não há resposta forte a "works on how many instances?".

- [ ] **F1** Santiago de Cabo Verde como candidato principal. Ver `docs/PLANO_E6_SANTIAGO.md`.
- [ ] **F2** Commitar `PRESPEC_SANTIAGO.md` ANTES de qualquer análise.
- [ ] **F3** Replicar pipeline: `fogo_constants.py` equivalente, fronteira, amplitudes, factorial.
- [ ] **F4** Confirmar: critério mais concentrado amplifica acima do seu peso nominal.
- [ ] **F5** Reportar como E7 com protocolo igual ao E1.
- [ ] **F6** Actualizar frase de generalização.

---

## Sequência de execução

```
Agora (esta sessão):
  A2 — substituir valores raw de §6.8 pelos macros shift já gerados
  A8, A9 — erros pequenos de texto
  G1 — identificar e regenerar Figura 1

Próxima sessão:
  A10-A17 — erros restantes
  F475-5 — auditoria bidirecional
  G2-G4 — build check
  C1-C6 — F8 2x2

Depois:
  B — regret metric (requer D?-4 respondida)
  D — correcções científicas
  E — cortes estruturais
  F — Santiago (semanas)
```

---

## Bloqueadores por patamar

**Para "minor revision" plausível (7.5):** F475 + A + G + C + D2 + D3 + D4.

**Para 8.0-8.5:** Tudo acima + B (regret) + E (cortes). O regret metric é o item de maior impacto isolado.

**Para 9.0:** Fase F obrigatória.

---

## Regras de processo

1. Após cada substituição de literal por macro: verificar o contexto onde o macro ficou (modo inverso do audit).
2. SHAs de CSV/JSON: calcular após `.replace(b"\r\n", b"\n")`. Documentar no README.
3. Nenhum script de verificação anuncia "ALL PASS" com erros conhecidos no PDF.
4. Qualquer nova substituição de literal no main.tex: adicionar MUST_FAIL test para o valor antigo.
5. Antes de implementar a Fase B: resolver D?-4 (localizar pesos w por draw).
