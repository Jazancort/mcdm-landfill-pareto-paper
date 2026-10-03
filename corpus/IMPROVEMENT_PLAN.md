# Improvement Plan — MCDM Landfill Paper
**Status:** Plano fechado. Nenhuma expansão autorizada sem justificativa fundamental explícita do autor.
**Baseline:** commit `9dedfc7`, tag `v0.9-defensible`, ALL CHECKS PASSED.

---

## Rubrica operacional de chegada (6 critérios)

> **Indicador de chegada:** os 6 critérios abaixo são verificados em passe único sobre o PDF final, com evidência citada por linha. Nenhum critério pode ficar FAIL. Qualquer FAIL gera patch cirúrgico dentro da etapa corrente ou restrição explícita do claim — nunca nova linha de investigação.

| Critério | PASS objetivo | Limite honesto |
|---|---|---|
| **V — Rigor e validade formal** | Provas matemáticas sem ambiguidade; quantificadores explícitos e delimitados; sem contraexemplos no domínio declarado (incluindo notas de limitação sobre o operador gap sob dominância fraca). | Não extrapolar SAW/afim para TOPSIS, ranks ou métricas não afins. |
| **C — Demarcação da contribuição** | Tabela curta "contribuição × literatura mais próxima × Fogo prévio": novo vs. reuso explícito. | Não vender weighted-sum conhecido como teoria nova. |
| **E — Evidência independente controlada** | Um E6 prospectivo, congelado antes de rodar, com estimand claro e delineamento pré-registrado. | Generaliza só para a família sintética definida, não para "todos os casos reais". |
| **S — Rastreabilidade estatística** | IC/teste pareado com unidade correta (instância-base, não draw), seeds, hashes e exclusões documentados. p-valor não é selo de verdade; se direção fraca, o claim é reduzido. | Sem valores pré-fixados; estatísticas emergem dos dados reais. |
| **A — Reivindicações proporcionais** | Abstract, captions e conclusões dizem exatamente o que foi demonstrado/estimado; sem "all", "universal", "predicts" quando há só evidência limitada. | Sem "for any instance" para resultado single-instance. |
| **R — Reprodutibilidade ponta a ponta** | Execução autônoma por pessoa/agente independente, logs, README e tag final após revisão. | README e tag não bastam se números e claims não fecharem. |

---

## Quatro premissas conceituais corrigidas

Antes do plano, estas premissas são **corrigidas** em relação a versões anteriores de revisão:

1. **Quantificadores lógicos são preservados.** Não se deve banir *iff* ou *for any* quando formalmente delimitados (ex.: Teorema 1, equivalência sob transformações afins estritamente crescentes, cardinalidade fixa *k*, modelo de valor aditivo estritamente positivo). O que não pode é deixar dado empírico "provar" teorema.

2. **Termos científicos são qualificados, não censurados.** *Predict* é legítimo quando há fórmula/estimador especificado; *demonstrate* é legítimo para proposição provada ou exemplo empírico claramente delimitado. O conserto é qualificar conteúdo e escopo, não trocar palavras mecanicamente.

3. **Prefixos de label LaTeX não são erros per se.** `prop:`, `thm:`, `rem:` são convenções de chave de referência cruzada. O problema é chamar de Proposition algo que é remark/diagnóstico — o ajuste é no ambiente textual, não no prefixo.

4. **Estatísticas não são pré-fixadas.** p=0.003 e IC não são valores mandatórios; devem emergir do pareamento real por draw. Arredondamento legítimo (34.55 → 34.6) não precisa ser relitigado; "tolerância 0.15" como validação é que seria frágil.

---

## Inventário fechado de pendências

### Reparos de validade/integridade (sem estes, claims ficam frágeis)

| ID | Problema | Localização |
|---|---|---|
| I-1 | `tab:tvorder` caption ainda pode conter linguagem de predição universal — verificar e restringir ao domínio aditivo. | L1865 |
| I-2 | Iff "for any weights and any instance" em abstract/§1/conclusion: qualificar com "within additive aggregation under the fixed partial value model". | L116, L2667 |
| I-3 | Label `prop:exponent` → verificar que `\ref{prop:exponent}` em L969 aponta para o remark correcto após promoção. | L969, L1328 |
| I-4 | Confirmar que `\end{remark}...\begin{corollary}` compila sem overlap de numeração. | após L1328 |
| I-5 | Operator gap: documentar nas Limitations que gap=0 não implica Pareto sem condições (contraexemplo de dominância fraca). | Limitations §8.2 |
| I-6 | PROMETHEE-Borda identity: formalizar prova sem atribuição espúria a empates arbitrários; explicitar hipótese de ausência de empates ou comportamento sob empates. | §3.3 |

### Melhorias com ganho real rumo ao padrão

| ID | Melhoria | Justificação |
|---|---|---|
| G-1 | README com 3 passos executáveis (clone, rerun, verify_macros_permanent). | Critério R |
| G-2 | PHASES_STATUS: adicionar output completo do TOST (statistic, CI, p, n_draws, fonte CSV). | Critério S |
| G-3 | Tabela de contribuição × literatura: diferenciar novo vs. reuso. | Critério C |
| G-4 | Limitations: item gap/weak dominance consistente com R2. | Critério A |
| G-5 | E6 sintético pré-registrado (ver protocolo abaixo). | Critério E — único novo experimento autorizado |

### Cosméticos/irrelevantes (excluídos permanentemente)

- Reformulação estilística sem impacto em validade
- Referências adicionais sem gap identificado
- Alteração de ordem de secções
- Rerun de B1 (SKIP permanente)
- Qualquer experimento além de E6

---

## Plano definitivo — 5 etapas fixas

### Etapa 1 — Fundamento teórico, escopo e mapa de claims

| Campo | Conteúdo |
|---|---|
| **Tarefa** | (a) Criar tabela de definições: matrizes, pesos, referência, avaliador, viabilidade, grupos, cardinalidade, transformação admissível. (b) Manter como teorema apenas o demonstrável: compatibilidade sob transformação afim positiva no escopo declarado; hipóteses explícitas. (c) Rebaixar para remark/diagnóstico: complemento de gap sem condições, TOPSIS como analogia, PROMETHEE com empates. (d) Documentar contraexemplo de dominância fraca em Limitations. (e) Qualificar iff "for any instance" em L116/L2667. |
| **Dependências** | Nenhuma |
| **Entregável** | Mapa de claims (claim → modelo → prova/dado → secção); main.tex diff |
| **Evidência** | 100% dos teoremas com premissas explícitas; mapa sem declarações universais não provadas; grep "for any instance" = 0 sem qualificador de âmbito |
| **Critério de aceite** | check_consistency 0 failures; build 0 `??`; mapa commitado |
| **Condição de parada** | Nenhum item I-1 a I-6 pendente |

### Etapa 2 — Auditoria numérica e rastreabilidade estatística

| Campo | Conteúdo |
|---|---|
| **Tarefa** | (a) Consolidar base de dados por draw (E1, E4 corrigido, F8, E5) em CSV auditado. (b) Calcular TOST pareado com unidade correta (draw), B=2000 bootstrap, margem ±2.5pp; registrar statistic, CI, p, n_draws, fonte em PHASES_STATUS. (c) Criar provenance.csv com hash de cada ficheiro fonte. (d) Excluir exclusivamente runs com bugs de pipeline; preservar contrastes deliberados de incompatibilidade de codificação rotulados como exploratórios. |
| **Dependências** | Etapa 1 completa |
| **Entregável** | provenance.csv; PHASES_STATUS actualizado com TOST; verify_macros_permanent.py exit 0 |
| **Evidência** | Script de consistência exit 0; conferência automática entre CSV, macros LaTeX e PDF |
| **Critério de aceite** | p-value, CI e n_draws calculados a partir dos dados; nenhum valor pré-fixado; hashes coincidem |
| **Condição de parada** | Todos os claims numéricos rastreáveis a fonte com hash |

### Etapa 3 — E6: estudo sintético independente controlado

| Campo | Conteúdo |
|---|---|
| **Tarefa** | Executar protocolo pré-registrado (ver secção abaixo). Congelar gerador e sementes **antes** da execução. |
| **Dependências** | Etapas 1 e 2 completas |
| **Entregável** | Script E6 versionado; relatório com estimativas pontuais e IC hierárquico; figuras; entry em PHASES_STATUS |
| **Evidência** | M, B, C atingem Q2=100% em todas as 45 instâncias (garantia matemática verificada como teste de regressão); W e V reportam estimativa ± IC sem significância forçada |
| **Critério de aceite** | Protocolo não modificado após execução; conclusões condicionadas à família sintética definida; nenhum claim de generalização para "todos os casos reais" |
| **Condição de parada** | Relatório gerado sem ajustes post hoc; entrada em PHASES_STATUS |

### Etapa 4 — Integração editorial e reprodutibilidade

| Campo | Conteúdo |
|---|---|
| **Tarefa** | (a) Incorporar E6 no manuscrito; (b) actualizar abstract ≤ 250 palavras; (c) README com pipeline em 1 comando; (d) supplementary 0 `??`; (e) tabela de contribuição × literatura (G-3). |
| **Dependências** | Etapas 1, 2 e 3 completas |
| **Entregável** | main.pdf + suppl_wrapper.pdf sem `??`; README executável; abstract word count ≤ 250 |
| **Evidência** | Build limpo; pipeline end-to-end em ambiente isolado bem-sucedido; word count verificado por script |
| **Critério de aceite** | 100% macros injetadas automaticamente; zero intervenção manual no pipeline |
| **Condição de parada** | Build limpo + pipeline isolado |

### Etapa 5 — One-pass review, congelamento e tag

| Campo | Conteúdo |
|---|---|
| **Tarefa** | Leitura linear do PDF (não do TeX) nas secções: Abstract, §1 contributions, Theorem 1, §7 Results opening, §8.1, Limitations, Conclusion — auditar rubrica V/C/E/S/A/R critério a critério. |
| **Dependências** | Etapas 1–4 completas |
| **Entregável** | Checklist rubrica (6 critérios, PASS/FAIL com evidência citada por linha de PDF); tag `v1.0-submission-candidate` |
| **Evidência** | Cada critério com citação de linha do PDF; qualquer FAIL → patch cirúrgico ou restrição de claim dentro desta etapa |
| **Critério de aceite** | Todos 6 PASS; `git status` limpo; zero pendências |
| **Condição de parada** | Checklist commitado em PHASES_STATUS; tag no GitHub |

---

## Protocolo E6 — detalhes congelados

### Delineamento

- **45 instâncias-base independentes:** 3 tamanhos N ∈ {50, 100, 200} × 3 geometrias (uniforme, agrupada, grade) × 5 sementes espaciais.
- **Medidas repetidas sobre cada instância-base:** 5 tratamentos de score (M, B, W, V, C) × 200 sorteios Dirichlet (κ=200).
- **Fixos em todas as células:** k=3, 11 critérios em 3 grupos (3, 5, 3), matriz de atributos brutos, orientações custo/benefício, conjunto viável T sob d_min (garantir ≥1 trio viável; registrar incompletudes no greedy).
- **Gerador, domínio espacial, marginais e sementes** arquivados antes da execução — sem ajustes post hoc.

### Avaliador fixo e células de score

A fronteira de Pareto e as funções parciais de valor dos objectivos mantêm-se em escala min-max (z), com os mesmos pesos w por draw e mesmo T. Apenas a função de score é manipulada:

| Condição | Definição |
|---|---|
| **M** | A_j = 1 (controle alinhado) |
| **B** | A_j = ρ̄_g(w) = Σ_{j∈G_g} w_j ρ_j / W_g por draw (between-group) |
| **W** | A_j = ρ_j / ρ̄_g(w) (within-group; distorção estritamente interna ao grupo) |
| **V** | A_j = ρ_j (amplitudes vetoriais completas) |
| **C** | Amplitudes de V, mas pesos w'_j ∝ w_j / ρ_j (recupera score min-max por compensação analítica exata) |

Colunas com ρ_j ≤ 0 tratadas por regra pré-especificada documentada antes da execução.

Sob montagem ótima, M, B e C atingem Q2=100% por garantia matemática — são testes de regressão/consistência, não evidência empírica nova. W e V são estimandos empíricos livres.

### Estimandos e inferência

- **Estimando primário:** perda within = Q2[M, opt] − Q2[W, opt].
- **Estimandos secundários:** V − W; contraste ótimo vs. greedy em M e V; correção C vs. V.
- **Inferência:** bootstrap hierárquico pareado no nível das 45 instâncias-base (evita pseudorreplicação de 45.000 amostras); reportar estimativa pontual e IC.
- **Sem significância forçada:** conclusões reportam magnitude e IC independentemente de p; se direção fraca, o claim é reduzido, não o protocolo expandido.
- **m_eff** permanece puramente descritivo — não ortogonalizado.

### Precisão sobre exclusões

A exclusão da Etapa 2 aplica-se **exclusivamente** a runs com bugs de pipeline. Os contrastes deliberados de incompatibilidade de codificação (aspecto contínuo vs. binário) são preservados integralmente e rotulados como análises exploratórias.

---

## Escopo congelado

**Incluído neste plano:** I-1 a I-6, G-1 a G-5, E6.

**Fora de escopo — permanentemente:**

- B1 (SKIP confirmado — sem rerun)
- Qualquer experimento além de E6
- Extensão a outros casos de estudo reais
- Comparação com métodos fora do factorial existente
- Revisão bibliográfica adicional sem gap identificado
- Alterações de estilo sem impacto em validade
- Reabertura de R0–R5 sem evidência nova e específica que invalide a resolução anterior

---

## Regra de risco à integridade

Se qualquer etapa revelar que um claim central não pode ser sustentado com a evidência disponível: **retirar ou restringir o claim**. Não criar nova etapa de investigação. Se a restrição tornar o claim inútil, declarar **BLOCKED** e exigir decisão explícita do autor sobre manter/remover a contribuição afectada.

---

## Primeira tarefa acionável imediata

**Etapa 1, item (e):** localizar L116 e L2667 (iff "for any weights and any instance"), adicionar qualificador "within additive aggregation under the fixed partial value model". Depois localizar L1865 (`tab:tvorder` caption) e remover linguagem de predição universal. Build + check_consistency. Nenhum dado novo necessário.


---

## Checklist de execução — itens atómicos

> Cada item é uma sessão de trabalho independente.
> Solicite um ID por vez. O item só fecha quando diff, validação semântica e build estiverem confirmados.
> Status: `[ ]` pendente · `[x]` concluído · `[~]` bloqueado

---

### Bloco I — Reparos de integridade
*(sem estes, claims ficam frágeis)*

| ID | Tarefa | Status |
|----|--------|--------|
| I-1 | `tab:tvorder` caption: verificar se ainda contém "predicted distortion" ou linguagem de predição universal; restringir ao domínio aditivo de Fogo se necessário. | [x] |
| I-2 | `iff "for any weights and any instance"` em L116 e L2667 (abstract + conclusion): adicionar qualificador explícito de âmbito — "within additive aggregation under the fixed partial value model". | [x] |
| I-3 | Label `prop:exponent` vs `rem:exponent`: verificar que `\ref{prop:exponent}` em L969 resolve correctamente após a promoção a remark; corrigir se necessário. | [x] |
| I-4 | Confirmar no PDF compilado que `\end{remark}…\begin{corollary}` produz numeração correcta sem overlap. | [x] |
| I-5 | Limitations §8.2: adicionar nota explícita de que gap=0 não implica Pareto sem condições; fornecer o contraexemplo de dominância fraca. | [ ] |
| I-6 | PROMETHEE-Borda identity §3.3: explicitar hipótese de ausência de empates (ou comportamento sob empates) para que a identidade não seja atribuída a empates arbitrários. | [ ] |

---

### Bloco G — Melhorias de qualidade
*(ganho real rumo à rubrica)*

| ID | Tarefa | Status |
|----|--------|--------|
| G-1 | Criar `README.md` com: pré-requisitos, 3 passos executáveis (clone → rerun → verify), hash esperado do `verify_macros_permanent.py`. | [ ] |
| G-2 | `PHASES_STATUS`: adicionar entrada TOST com statistic, CI, p, n_draws e fonte CSV — calculados dos dados reais, não pré-fixados. | [ ] |
| G-3 | Criar tabela de contribuição × literatura: para cada contribuição i–v, indicar o antecedente mais próximo, o que é novo e o que é reuso. | [ ] |
| G-4 | Limitations: confirmar que o item gap/weak dominance está consistente com a resolução R2 (gap=0 ≠ Pareto without conditions). | [ ] |

---

### Bloco E — Experimento sintético E6
*(único novo experimento autorizado — critério E da rubrica)*

| ID | Tarefa | Status |
|----|--------|--------|
| E6-A | Escrever e commitar o script gerador de instâncias (45 bases: 3×N × 3×geometria × 5×semente); congelar sementes e parâmetros **antes** de qualquer execução. | [ ] |
| E6-B | Implementar as 5 condições de score (M, B, W, V, C) com as fórmulas exactas do protocolo; testar que M=B=C atingem Q2=100% como regressão. | [ ] |
| E6-C | Executar E6 completo (45 instâncias × 5 condições × 200 draws); gerar relatório com estimativas pontuais e IC hierárquico por bootstrap. | [ ] |
| E6-D | Validar resultados: M/B/C = 100% em todas as instâncias; W e V com IC documentado; nenhum ajuste post hoc; entrada em PHASES_STATUS. | [ ] |

---

### Bloco W — Integração editorial
*(depois de E6 concluído)*

| ID | Tarefa | Status |
|----|--------|--------|
| W-1 | Incorporar E6 no manuscrito: secção de resultados + captions das tabelas/figuras do E6. | [ ] |
| W-2 | Actualizar abstract ≤ 250 palavras; confirmar que as 5 contribuições do §1 mapeiam 1-para-1 com os resultados. | [ ] |
| W-3 | README: adicionar pipeline end-to-end em 1 comando (gera tabelas, macros e PDF sem intervenção manual). | [ ] |
| W-4 | Build supplementary limpo: 0 `??`, secção S4b archived sem warnings. | [ ] |

---

### Bloco F — One-pass final e congelamento
*(só depois de I + G + E + W completos)*

| ID | Tarefa | Status |
|----|--------|--------|
| F-1 | Leitura linear do PDF: auditar rubrica V/C/E/S/A/R critério a critério com citação de linha; qualquer FAIL → patch cirúrgico dentro desta sessão. | [ ] |
| F-2 | Commit final limpo + tag `v1.0-submission-candidate` no GitHub. | [ ] |

---

### Ordem de execução sugerida

```
I-1 → I-2 → I-3 → I-4 → I-5 → I-6
      ↓
G-1 → G-2 → G-3 → G-4
      ↓
E6-A → E6-B → E6-C → E6-D
      ↓
W-1 → W-2 → W-3 → W-4
      ↓
F-1 → F-2
```

**Total: 18 itens atómicos.**
Para executar: diga o ID (ex: `faz I-1`) e o item será executado, diff mostrado, validado semanticamente e confirmado antes de fechar.
