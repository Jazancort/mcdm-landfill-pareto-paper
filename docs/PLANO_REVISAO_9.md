# Plano de Revisão para 9/10 — Omega/EJOR/C&OR
**Nota actual:** 6/10 (major revision)
**Alvo:** 9/10
**Referência:** f475928 | Criado: 2026-10-21

---

## Estimativa de impacto por fase

| Fase | Conteúdo | Esforço | Nota estimada após |
|---|---|---|---|
| F475 | Itens urgentes da revisão de f475928 | 2 dias | 6.5 (erros de afirmação corrigidos) |
| A | 20 erros factuais do PDF | 1 dia | 7.0 |
| G | Build check alargado + Figura 1 no pipeline | 1 dia | 7.0 (evita -0.5 futuro) |
| C | F8 matriz 2x2 completa + reframing para Resultados | 1-2 dias | 7.5 |
| D | Correcções científicas pontuais (§2.5-§2.9) | 2 dias | 7.8 |
| B | Métrica de regret de valor | 2-3 dias | 8.5 |
| E | Cortes estruturais + integração E6 | 2 dias | 8.5 |
| F | Segunda instância (Santiago) | semanas | 9.0-9.5 |

---

## Fase F475: Revisão de f475928 (URGENTE — afecta afirmações do artigo)

### F475-1: E1-V contra o factorial SAW/vec/opt por draw
**Risco: afirmação possivelmente falsa na §7.7**

**RESULTADO: 500/500 MATCH — draws são idênticos. §7.7 está CORRECTA.**
Commit de verificação: `scripts/test_e1_draws.py` (C:\tmp).

- [x] Executar o teste de coincidência — 500/500, §7.7 verificada por draw
- [x] TASKS.md pode ser actualizado de "via agregados" para "verificado por draw"

### F475-2: B=10,000 vs B=2,000 — inconsistência no texto
**FEITO: Opção B implementada — `\nbootEone{10,000}` adicionado a macros_structural.tex, texto da E1 actualizado (36e7f37).**

- [x] Implementar Opção B: `\nbootEone{10,000}`, texto na §7.7 diz agora "$B = \nbootEone$ replicates"
- [x] TASKS.md: registar que [3.8; 11.0] não corresponde a nenhuma configuração reproduzível

A §5.4 e a Tabela 6 dizem "2,000-replicate bootstrap intervals". O macro `\nboot` vale 2,000. O [4.0; 11.0] foi calculado com B=10,000 (diag_e1b_greedy.py).

- [ ] Decidir e implementar uma das duas opções coerentes:
  - **Opção A — Uniformizar para B=2,000:** recalcular com B=2,000 e default_rng(42) (não RandomState), que dá [3.8; 11.2]. Actualizar `\EonePtwoBootCILo{3.8}` e `\EonePtwoBootCIHi{11.2}`. O `\EonePtwoDiff{7.4}` (ponto) não muda.
  - **Opção B — Declarar B=10,000:** manter [4.0; 11.0] e acrescentar ao texto "95% paired bootstrap CI, B=10,000" com um macro `\nbootEone{10000}`, distinto de `\nboot{2000}`.
- [ ] Registar no TASKS.md que o [3.8; 11.0] publicado antes de f475928 não corresponde a nenhuma configuração reproduzível.
- [ ] Whichever option chosen: add a MUST_FAIL test for the abandoned value.

### F475-3: .gitattributes e hashes independentes do SO
**FEITO: a7bc796 — .gitattributes criado, 94 ficheiros convertidos para LF, 4 SHAs canónicos verificados.**

- [x] Criar `.gitattributes` com `*.csv -text`, `*.json -text`, `*.npy binary`, `*.log -text`
- [x] Executar `git add --renormalize .` e fazer commit
- [x] Verificar SHAs canónicos: amplitudes.json, e1_diag_bootstrap.csv, f8_per_draw.csv, e6_raw_prespec.csv — TODOS OK

O git converte CRLF no Windows. Os SHA-256 registados no código e no README não se reproduzem num clone Linux/Mac.

- [ ] Confirmar que a diferença é só nos finais de linha:
  ```python
  import hashlib
  b = open("results/f8/f8_per_draw.csv","rb").read().replace(b"\r\n", b"\n")
  print(hashlib.sha256(b).hexdigest())  # deve bater com o hash registado
  ```
- [ ] Criar `.gitattributes` na raiz:
  ```
  *.csv   -text
  *.json  -text
  *.npy   binary
  *.log   -text
  ```
- [ ] Executar `git add --renormalize .` e fazer commit.
- [ ] Decidir e documentar no README: os hashes são calculados sobre bytes do Git (após renormalize) ou sobre bytes com `\n` (normalização explícita). Implementar a escolha nos scripts de verificação.
- [ ] Actualizar todos os SHA-256 registados após o renormalize.

### F475-4: Macro \RnkContinuousGainPct para os "12%"
**FEITO: 36e7f37 — \UrbanRatioVec, \AspectRatioVec, \RnkContinuousGainPct{12.1}, \DeltaLinfshift{0.2835}.**

- [x] Acrescentar `\RnkContinuousGainPct{12.1}` (threshold 0.992, 7 critérios)
- [x] Renomear `\UrbanInflation` → `\UrbanRatioVec`, `\AspectInflation` → `\AspectRatioVec`
- [x] Corrigir §6.2: "all others gain 12%" → "seven fully continuous criteria gain ≈\RnkContinuousGainPct%"
- [x] Acrescentar `\DeltaLtwoshift{0.3101}` e `\DeltaLinfshift{0.2835}` para §6.8 (A2)

Com S_rnk ≈ 0.8874: os sete critérios contínuos ficam em 0.995/0.8874 = 1.121 (+12.1%). Urban fica em 0.989/0.8874 = 1.115 (+11.5%). Cult fica em 0.981/0.8874 = 1.105 (+10.5%). A Tabela 2 já mostra 1.11 para urban e cult.

- [ ] Acrescentar ao `generate_macros_amplitudes.py` a computação de `\RnkContinuousGainPct` a partir do amplitudes.json (usando os 7 critérios contínuos sem empates).
- [ ] Corrigir §6.2: "all others gain 12%" → "the seven fully continuous criteria gain ≈\RnkContinuousGainPct%; urban and cult gain somewhat less (see Table 2)".
- [ ] Regenerar `macros_amplitudes.tex` e confirmar que o macro aparece.
- [ ] Renomear `\UrbanInflation` para `\UrbanRatioVec` (0.53 é uma deflação, não uma inflação). Fazer o mesmo com `\AspectInflation` → `\AspectRatioVec`. Actualizar todas as ocorrências no main.tex e regenerar.

### F475-5: Revisão do contexto de cada substituição de literal (anti-pattern)
**Risco: macro certo no sítio errado passa em todos os checks actuais**

As substituições de f475928 (1.77x, 0.53x, 0.51x) precisam de verificação de contexto.

- [ ] Executar `git show f475928 -- main.tex` e rever cada linha modificada.
- [ ] Para cada macro substituído, confirmar que a grandeza bate com o significado da frase em contexto (não só que o valor numérico é o certo).
- [ ] Implementar nova regra no `audit_hardcoded.py`: para cada macro definido nos .tex gerados, imprimir as linhas do main.tex onde é usado com 2 linhas de contexto antes e depois. Isto torna o audit bidirecional.

### F475-6: Erros 1-7 do PDF têm prioridade sobre tudo o resto
Ver secção Fase A abaixo. Os itens A1-A7 correspondem directamente aos erros 1-7 da revisão de f475928.

---

## Fase A: 20 Erros Factuais do PDF (1 dia)

Cada erro destes custa credibilidade se encontrado por um revisor antes de chegar aos resultados.

### Grupo 1: Números visivelmente errados (fazer primeiro)

- [ ] **A1** Figura 1 (p.7): regenerar a partir dos JSON. Identificar qual `fig_*.py` gera a "Figura 1" no main.tex (provavelmente `fig_F2_interaction.py` ou `fig_interaction.py`). Os valores actuais 2.88x, +0.5pp, -1.1pp, +34.6pp são antigos. Depois de regenerar, adicionar ao Makefile target `figures` e ao build_check.
- [ ] **A2** §6.8 (p.14): TV=0.3146, ‖δ‖₂=0.3127, ‖δ‖∞=0.2859 são valores raw. Com shift: TV=0.3113, ‖δ‖₂≈0.3101, ‖δ‖∞≈0.2832. Criar macros `\TVshift{0.3113}`, `\DeltaLtwoshift{0.3101}`, `\DeltaLinfshift{0.2832}` em `generate_macros_amplitudes.py` e substituir no §6.8.
- [ ] **A3** §5.4: "only ≈1.0 pp in the other direction (94.4% attainment)". Correcto: 100-94.4=5.6 pp. Verificar qual macro expandiu para 1.0 — suspeita em `\RawSensMaxDeltaQtwo`. Separar os conceitos: 5.6 pp é a perda de Q2; 94.4% é o attainment. Usar macros distintos para cada.
- [ ] **A4** §4.3: lista "perm, urban, cult, aero and rivers have min=0". Aero tem mínimo 252.7 m. Lista certa: perm, aspect, urban, cult, rivers. Os que divergem: slope, coast, wells, aero; roads e protected ficam abaixo de 0.3%. Confirmar com `compute_q2_raw_vs_shift.py` ou `fogo_constants.py`.
- [ ] **A5** §6.2/§6.7 eq.(20): ρ_j e v_j escritos com x_j (raw) em vez de x̃_j (shift). Contradiz eq.(9) e Tabela 2. Substituir x por x̃ nas duas ocorrências.
- [ ] **A7** §7.8: "Seven cells yield 24,000 total draws". Três níveis + duas baselines = cinco células. As células V_inf_F e W_def_F (P3 e P4) não estão descritas. Definir L (0.10), F (0.1986), H (0.30) na primeira ocorrência. Corrigir "TV_W ∈ {0.10, 0.20, 0.30}" — F=0.1986, não 0.20.

### Grupo 2: Erros de lógica ou notação

- [ ] **A6** §3.2: "distance criteria in G1 and G2 enter as 1-x̂ so that a short distance is a high cost". No G1 (perm, roads) distância curta = custo baixo. A inversão aplica-se ao G2. Verificar no código (`fogo_constants.py`, array `benefit`) e corrigir a frase.
- [ ] **A8** §7.8 P2: "two three-way ties and one reversal excluded". Não foram excluídos: contam como falhas, daí 85/88. Corrigir para "counted as failures".
- [ ] **A9** Intro/§8.3/Conclusão: "divides another by 0.53x" = multiplicar por 1.89. Substituir por "scales another by a factor of 0.53". Verificar todas as ocorrências (o reviewer encontrou pelo menos 3).
- [ ] **A10** §6.9: "linearly independent when n₀ ≠ n₁". x e 1-x são sempre linearmente independentes quando x não é constante. Remover a condição.
- [ ] **A11** §6.9: τ_b=0.960 e top-100=0.960 são iguais ao centésimo. Recalcular ambos a partir dos CSVs. Se coincidência real, adicionar "(coincidentally equal)" em nota. Se erro de cópia, corrigir.
- [ ] **A12** §6.1: frase sobre midranks "fora do âmbito exacto" imediatamente antes de afirmar Q₂ se aplica a min-max, ranks e vector. Reorganizar para que o âmbito exacto e a extensão heurística fiquem na ordem certa.
- [ ] **A13** Tabela 3 + §7.1: legenda menciona "blue diamonds" (estão na Figura 5, não na tabela) e "portfolios including excluded sites cannot lie on that frontier" (nenhum trio inclui sítios excluídos). Acrescentar coluna "∈ F" do teste de dominância. Verificar se os métodos com gap=0 são de facto eficientes.
- [ ] **A14** §7.5: "For completeness, we recall the reference-set amplitude ratio…" está deslocado. "Table 7 holds the evaluator fixed…" aparece duas vezes. Corrigir a posição e eliminar o duplicado.
- [ ] **A15** §8.6: dois parágrafos com o título "Gap measure and weak dominance"; "Regulatory grounding" com uma única frase. Fundir os dois gap-paragraphs; completar ou absorver "Regulatory grounding".
- [ ] **A16** §4.1: "slope (dimensionless gradient)". Confirmar: graus ou gradiente adimensional? Ver `fogo_constants.py` ou o CSV de origem.
- [ ] **A17** §2.3: "|𝒯| up to several hundred candidates". 𝒯 é o conjunto de trios (1.94M). O que tem "several hundred" é N. Corrigir para N.

### Grupo 3: Notação e referências

- [ ] **A18** Notação: (i) k=3 usado para tamanho do portfolio (§8.2) e número de objectivos (§8.6) — escolher um símbolo distinto; (ii) portfolios como t e T de forma inconsistente — uniformizar; (iii) §6.10 usa "N vs. N′" mas o resto usa "A vs. A′"; (iv) Q₂ e Q₃ referenciados mas Q₁ nunca definido — defini-lo ou remover as referências implícitas.
- [ ] **A19** Referências: "Kadziski" → Kadziński; "Sowiski" → Słowiński. Verificar outros autores com diacríticos.
- [ ] **A20** Code availability: afirma que o script "recomputes all primary quantitative claims and exits 0 on exact agreement". Com A1-A3 por corrigir, esta afirmação é falsa. Só actualizar depois de fechar A1-A3 e Fase G.

---

## Fase G: Build Check Alargado (1 dia, após Fase A)

- [ ] **G1** Identificar qual `fig_*.py` é a "Figure 1 (p.7)" no main.tex. Verificar se lê de JSON ou tem literais. Adicionar regeneração automática ao Makefile (target `figures`).
- [ ] **G2** Acrescentar ao `check_consistency.py`: verificação dos três valores TV/δ do §6.8 contra os macros gerados de shift. Deve falhar com valores raw actuais e passar com shift.
- [ ] **G3** Alargar `audit_hardcoded.py` para incluir `supplementary.tex` e todos os ficheiros `tab_*.tex`. Classificar os RESULT? restantes como justificados (comentário `# OK: <razão>`) ou pendentes. Objectivo: exit 0 com excepções documentadas.
- [ ] **G4** Adicionar `check_tab_amplitude.py` e `generate_macros_r1.py` ao Makefile `check` target.
- [ ] **G5** Após A1-A3 e G1-G3 fechados: actualizar a frase de Code availability (A20).

---

## Fase C: F8 Matriz 2x2 Completa + Reframing (1-2 dias)

O `f8_circularity.csv` actual só tem obj=vec × score=mm/vec (4 linhas). Faltam as 4 células com obj=mm.

**Matriz completa 2x2 × 2 montagens (8 células alvo):**

| | F_mm (fronteira) | F_vec (fronteira) |
|---|---|---|
| Score mm, opt | ~100% (Theorem 1 — só verificação) | ? (célula NOVA) |
| Score mm, greedy | ? (célula NOVA) | ? (célula NOVA) |
| Score vec, opt | 94.4% (existe) | 100% (existe) |
| Score vec, greedy | 72.4% (existe) | 100% (existe) |

- [ ] **C1** Estender `compute_f8_circularity.py` para calcular as 4 células em falta. A fronteira mm (F_mm) é o conjunto de trios não-dominados quando o scoring usa min-max — calcular ou carregar de `results/`. A lógica de `on_frontier` precisa de aceitar F_mm como argumento alternativo.
- [ ] **C2** Com a matriz completa, criar nova tabela no manuscrito (Tabela 8 ou §7.x) com as 8 células.
- [ ] **C3** Mover o F8 da §5.4 (Métodos) para nova §7.x (Resultados). Título sugerido: "Cross-model alignment: attainment when scoring and frontier normalisations differ".
- [ ] **C4** Reenquadrar o destaque: "custo de desalinhamento entre modelo de score e modelo de valor" em vez de "efeito da normalização". Defensável nos dois sentidos, elimina a circularidade do benchmark.
- [ ] **C5** Corrigir §5.4 para apenas referenciar §7.x.
- [ ] **C6** Acrescentar as 8 células ao `check_consistency.py` e ao `generate_macros_f8.py`.

---

## Fase D: Correcções Científicas Pontuais (2 dias)

- [ ] **D1** Convenção de orientação vec (§4.3): acrescentar parágrafo a justificar que se segue a convenção dos manuais de TOPSIS (normalizar x bruto antes de tratar o sentido). Computar como sensibilidade: ρ_perm com orientação antes da normalização = `\RhoPermInverted` = 0.052 (macro já existe). Adicionar ao suplemento uma tabela com os valores vec nas duas convenções. Mostrar que o ranking dos 389 sítios não muda além de X posições.

- [ ] **D2** Confirmações vs regressões: reformular E1-P1, E6-P1, F8-vec/opt como "implementation consistency checks — they cannot fail without a bug". Dizer explicitamente: "P1 is a structural consequence of Theorem 1 (ii)⇒(i) and cannot fail; P2 and P3 are the empirically falsifiable predictions."

- [ ] **D3** Agregação "equivalente a zero": remover o TOST do destaque e do abstract. Substituir por: "The aggregation effect is cell-dependent, ranging from -8.4 to +4.4 pp; it does not have a stable sign." Retirar "aggregation is downstream", "the least consequential factor" e "the answer is not about the aggregation methods".

- [ ] **D4** TV_B + TV_W não é uma decomposição: substituir "decomposition" por "components" ou "indices". Acrescentar a inequação correcta: TV ≤ TV_B + Σ_g W_g^eff · TV_{W,g}. Justificar em uma frase por que W_g nominal foi escolhido (é o que faz TV_W(W) = TV_W(V)).

- [ ] **D5** Novidade teórica: reformular para três contribuições centrais: (i) medição contra a fronteira exacta de 1.94M portfolios, (ii) condição necessária e suficiente para nulidade do custo, (iii) evidência de que é a componente entre grupos que determina o custo. Mover contribuição (v) PROMETHEE-Borda para o suplemento.

- [ ] **D6** Incerteza no factorial: acrescentar colunas SE e IC a pelo menos as células principais da Tabela 5. Verificar explicitamente que os sítios 41, 385, 429 (com imputação) não pertencem a F′ — acrescentar frase confirmando.

---

## Fase B: Métrica de Regret de Valor (2-3 dias)

Esta é a correcção de maior impacto individual. Q₂ mede pertença à fronteira de Pareto. O argumento normativo do artigo é sobre distorção de preferências. As duas coisas são diferentes e um revisor de Omega vai notar exactamente isso.

**Definição formal:**

```
R(t) = [V_w(t*_w) - V_w(t)] / [max_{s∈F} V_w(s) - min_{s∈F} V_w(s)]
```

onde V_w é a escalarização SAW/mm com os pesos nominais w, t*_w é o portfolio óptimo SAW/mm, e F é a fronteira exacta. R(t)=0 significa que t é tão bom quanto o óptimo SAW/mm; R(t)=1 significa que t é o pior ponto da fronteira sob w.

- [ ] **B1** Criar `scripts/compute_regret.py`. Inputs: `results/f8/f8_per_draw.csv` (portfolio seleccionado por método × draw), `scoring.py` (já tem `saw_sc`), pesos w por draw (verificar em `results/e1/` ou `results/unified/`). Output: `results/regret/regret_per_draw.csv` com colunas (method, norm, assembly, draw, R_value).
- [ ] **B2** Verificar que `saw_sc(w, norm='minmax')` de `scoring.py` computa V_w directamente. Confirmar que os pesos w por draw estão nos CSVs de saída do E1/factorial (verificar qual CSV contém os pesos por draw).
- [ ] **B3** Agregar R por método × célula: média e IC 95% bootstrap. Acrescentar como nova coluna à Tabela 5 ou como Tabela 5b.
- [ ] **B4** Verificar a hipótese central: um portfolio com Q₂=100% pode ter R > 0. Espera-se que TOPSIS/mm/opt tenha R > 0 mesmo com Q₂=100% quando avaliado sob os pesos nominais w. Reportar este contraste explicitamente.
- [ ] **B5** Reformular §7.2 e abstract para distinguir: "Q₂ testa eficiência de Pareto; R(t) testa custo preferencial (quão longe o portfolio está do óptimo sob w)". O argumento normativo do artigo depende de R, não de Q₂.
- [ ] **B6** Definir R formalmente no manuscrito (nova §5.5 ou como extensão da §5.1). Acrescentar `compute_regret.py` ao Makefile e ao `check_consistency.py`.

---

## Fase E: Cortes Estruturais (2 dias)

- [ ] **E1** Mover §6.5 (expoente α) e §6.6 para o suplemento. Tabela 1 vai junto. No corpo, manter só uma frase de ligação.
- [ ] **E2** Reduzir §7.5 a um Remark de 3-4 frases: "scoring with a different model than the one used to construct the frontier gives different results — verify coding consistency before comparing methods". O resultado +11.8 pp pode aparecer como nota de rodapé.
- [ ] **E3** Fundir §6.7 com §6.2 (redundantes na descrição da eq. vec).
- [ ] **E4** Completar §7.8: definir explicitamente as cinco células e os labels L (0.10), F (0.1986), H (0.30). Descrever V_inf_F e W_def_F. Corrigir "TV_W = 0.199" para o valor exacto. Confirmar "seven cells" vs "five cells".
- [ ] **E5** Criar uma tabela de orientação de critérios (uma só): critério, unidade, sentido no score, sentido em F_g, momento da inversão. Substituir as três descrições redundantes em §3.2, §4.1 e §4.3 por referência a esta tabela.
- [ ] **E6** Resolver inconsistências de notação (A18): fixar símbolo para tamanho do portfolio (p ou k), uniformizar t/T, padronizar A/A′ vs N/N′, definir Q₁ ou remover referências implícitas.
- [ ] **E7** Integrar E6 na §8 (Discussão) e na Conclusão. O E6 mostra que marginais contínuas reduzem a perda 10×. Acrescentar 1-2 parágrafos na Discussão.
- [ ] **E8** Corrigir §7.6: "no choice of w restores a site greedy has already excluded" → "given the score, no reweighting restores an excluded site from the greedy portfolio".
- [ ] **E9** Abstract e Introdução: "473 sites enumerate 1,944,653 portfolios". A enumeração é sobre os 389 sítios. Tornar inequívoco: "389 candidate sites yield 1,944,653 feasible portfolios of size three".
- [ ] **E10** Declaração de IA: rever segundo a política actual da Elsevier. Se algum texto gerado por LLM entrou editado no manuscrito, declarar. Rever a frase existente em `\aiDeclaration`.

---

## Fase F: Segunda Instância (semanas — obrigatória para 9/10)

Uma única instância adversarial é o maior limite para uma nota acima de 8.5. Os IC reflectem apenas incerteza sobre pesos, não variação entre instâncias. O E6 já existe como evidência sintética, mas um revisor de Omega vai pedir uma instância real.

- [ ] **F1** Confirmar Santiago de Cabo Verde como candidato (ver `docs/PLANO_E6_SANTIAGO.md` para decisões pré-declaradas). Alternativa: qualquer instância pública com ≥8 critérios e ≥100 candidatos.
- [ ] **F2** Commitar `PRESPEC_SANTIAGO.md` ANTES de correr qualquer análise (pré-especificação obrigatória): (a) instância, (b) previsão para ordenação de normalizações por Q₂, (c) asserção de regressão SAW/mm/opt=100%.
- [ ] **F3** Replicar o pipeline completo: `fogo_constants.py` equivalente, enumeração da fronteira, amplitudes, factorial com as mesmas células do E1.
- [ ] **F4** Verificar se o padrão se confirma: o critério com distribuição mais concentrada amplifica acima do seu peso nominal.
- [ ] **F5** Reportar como Experimento E7 (§7.x) com o mesmo protocolo do E1. Registar desvios explicitamente.
- [ ] **F6** Actualizar a frase de generalização: de "single adversarial instance" para "two instances with qualitatively different marginal distributions; the pattern holds in both".

**Nota técnica:** `run_473A_correct.py` e `pareto_utils.py` são o núcleo da enumeração. Com ~200-400 candidatos e k=3, o tempo de computação será similar ao Fogo (minutos na Athena). Usar `tmux new -s santiago`.

---

## Sequência de execução

```
Semana 1:
  F475-1 (teste draws E1 por draw) — primeira coisa a fazer
  F475-2 (decidir B=2000 vs B=10000 e implementar)
  F475-3 (.gitattributes e renormalize)
  A1-A7 (erros visíveis do PDF)

Semana 2:
  A8-A20 (erros restantes do PDF)
  F475-4 (\RnkContinuousGainPct, renomear \UrbanInflation)
  F475-5 (audit bidirecional)
  G1-G5 (build check alargado)

Semana 3:
  C1-C6 (F8 2x2 completo + reframing)
  D2, D3, D4 (reformulações textuais rápidas)

Semana 4:
  B1-B6 (regret metric — código + tabela + texto)
  D1, D5, D6

Semana 5:
  E1-E10 (cortes estruturais + integração E6)
  A20 e G5 (code availability — última a actualizar)

Semanas 6+:
  F1-F6 (segunda instância — Santiago)
```

---

## O que bloqueia cada patamar

**Para "minor revision" plausível (7.5):**
F475 + A + G + C + D2 + D3 + D4.
Só texto e extensão do F8. Sem nova computação intensiva.

**Para 8.0-8.5 (sem segunda instância):**
Tudo acima mais B (regret) e E (cortes).
O regret metric é o que mais sobe a nota. Um revisor que vê que o artigo tem uma métrica coerente com o argumento normativo aceita o paper como contribuição clara.

**Para 9.0:**
Fase F praticamente obrigatória. Um revisor de Omega vai perguntar "works on how many instances?" — e "one, adversarial" é uma resposta fraca para uma afirmação de generalidade sobre normalização MCDM.

---

## Regras de processo (novas — derivadas de f475928)

1. Após cada substituição de literal por macro: correr `audit_hardcoded.py` no modo inverso — para cada macro, imprimir o contexto onde foi expandido e confirmar que a grandeza bate com o significado da frase.
2. Os SHA-256 de CSVs e JSONs são sempre calculados após normalização para `\n` (usando `.replace(b"\r\n", b"\n")`). Documentar isto no README.
3. Nenhum script de verificação (`check_consistency.py`, `verify_macros_permanent.py`) pode anunciar "ALL PASS" enquanto houver erros conhecidos no PDF.
4. Qualquer nova substituição de literal no main.tex precisa de um MUST_FAIL test no `check_consistency.py` para o valor antigo.
