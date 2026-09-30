# Roadmap to 9.0 — Normalisation as Implicit Re-weighting

**Status do manuscrito:** commit 87bf3b9, 25 páginas, 0 erros. Pronto para circulação interna com coautores.
**Nota actual estimada:** 8.0 (Omega/EJOR tier)
**Nota alvo:** 9.0

---

## Diagnóstico: o que separa 8.0 de 9.0

| Défice | Nota actual | O que bloqueia |
|---|---|---|
| Validade externa: uma instância | C+ | "magnitudes específicas de um caso" |
| Dose-resposta ordinal, suporte vazio em 71% | B | "o canal repousa em três pontos" |
| Teoria é formalização de relação conhecida | B− | "incremento analítico modesto" |

O desenho empírico já está em A. O caminho para 9.0 é converter o caso em mecanismo medido e dar teoria ao achado empírico mais forte — que hoje não tem nenhuma.

---

## Workstream 1 — Corpus de matrizes publicadas ⭐ máxima prioridade

**O movimento retórico:** testar a recomendação de normalização vectorial nos próprios dados dos artigos que a recomendam.

**Fontes alvo** (já na bibliografia):
- Milani (2005), Chakraborty (2009), Vafaei (2018, 2022), Jahan (2015), Aytekin (2021)
- Alvo: 10–15 matrizes com pesos elicitados explícitos (AHP, BWM, SWARA ou equivalente)
- Critério de inclusão pré-declarado: matriz completa publicada + pesos + sentido dos critérios

**Porque é o item de maior retorno:**
1. Matrizes de 10–30 alternativas: `C(n,k)` enumera instantaneamente. Custo computacional ≈ zero.
2. Entrega simultaneamente: (a) validade externa real, (b) distribuição conjunta `(TV, m_eff)` em matrizes aplicadas — que §8.7 declara desconhecida —, (c) contribuição de survey com valor autónomo.
3. Demonstra que o mecanismo opera com e sem a restrição de separação espacial de Fogo.

**Protocolo:**

Para cada matriz:
1. Computar `A_j` sob min-max, vector e ranks; derivar `w_eff`, TV, `m_eff`, `||delta||_2`
2. Escolher `k=3` (ou `k=ceil(n/5)`, pré-declarado), enumerar `C(n,k)`
3. Construir a fronteira exacta sobre os grupos de objectivos declarados no artigo original
4. Perturbação Dirichlet, κ=200, N≥3500
5. Reportar Q2 por célula, **sempre desagregado por montagem** (não repetir o erro do estimand)

**Pré-especificação (escrever antes de ver resultados):**
- Hipótese primária: `Q2(min-max) ≥ Q2(vector)` sob SAW, montagem óptima, em cada instância
- Secundária: a perda ordena-se com `||delta||_2` entre instâncias (Spearman, IC bootstrap)
- Critério de falsificação: se a ordenação inverter em ≥20% das instâncias, o mecanismo é instância-dependente e o artigo assim o dirá

**Risco e mitigação:** algumas matrizes podem ter TV minúsculo (colunas homogéneas) → Q2 saturado. Não é falha — é informação sobre a distribuição de TV no mundo real, precisamente o que §8.7 pede. Reportar o histograma.

**Esforço:** 2–3 semanas.
**Ganho:** C+ → A−. Este item sozinho move a nota global para ~8.5.

---

## Workstream 2 — Coeficiente com suporte preenchido

**O que executar:** quatro células no caminho `A_j(t) = ρ_j^t`, `t ∈ {0.419, 0.513, 0.692, 0.868}`, produzindo `TV ∈ {0.12, 0.15, 0.21, 0.27}` com `m_eff` confinado a `[4.05, 5.00]`.

**Dimensionamento:** N=3500 por célula (SE binomial cai de 2.2 para 0.85 pp). A 3.5 sorteios/s, ~17 min por célula. Reexecutar também os níveis canónicos com o mesmo N — sem isso volta a ter tabelas de execuções diferentes.

**Variante crítica a incluir (duas condições por valor de t):**
- (i) Objectivos fixos em min-max → mede Mecanismo 1 + 2 conjuntamente
- (ii) Objectivos casados com `A_j(t)` → mede Mecanismo 1 isolado (Prop.1 garante Q2=1 na montagem óptima, logo a perda observada em greedy é foreclosure puro)

Esta é a **primeira separação limpa dos dois mecanismos em função de TV** — resolve a confusão que §7.7 admite nas células vectoriais da grade sintética.

**Ganho no desenho (com 4 corridas):**

| Métrica | Actual | Com 4 corridas |
|---|---|---|
| Alavancagem máx. | 0.935 | 0.622 |
| Fracção de S_xx num só ponto | 73.5% | 29.6% |
| VIF (TV, TV²) | 23.75 | 11.78 |
| SE(β₂) | 95.3 | 68.0 |

**Esforço:** 1 semana (implementação + ~4h de compute).
**Ganho:** B → A− em rigor inferencial.

---

## Workstream 3 — A proposição que falta ⭐ maior risco, maior retorno teórico

**O achado empírico mais forte — interacção normalização × montagem — não tem teoria.**

Formalizá-la eleva a contribuição de B− para A−: deixa de ser "formalizámos Choo" e passa a ser "explicámos um fenómeno que ninguém previu".

**Estrutura-alvo:** decompor a perda de Q2 em duas parcelas:

```
L(norm, assembly) = L_forec [combinatória] ⊕ L_mis [re-ponderação]
```

**Os dados já indicam a forma de ⊕:**
- Sob min-max (SAW): `L_mis = 0` por construção, logo `L_forec = 35.4 pp` (100.0 − 64.6)
- Sob vector, a montagem óptima só recupera 2.6 pp. Se as perdas fossem aditivas, o ganho seria ~35 pp. Não é: compõem-se sub-aditivamente, com saturação.

**A proposição a provar:**

> O ganho da montagem óptima sobre a greedy é limitado superiormente por uma função decrescente de `||delta||_2`: corrigir a foreclosure só tem valor na medida em que o alvo que se optimiza é o alvo correcto.

**Intuição do mecanismo:**
- A montagem óptima é (pela Prop.1) exactamente Pareto-eficiente em relação a `w_eff`. À medida que `w_eff` se afasta de `w`, `T*` permanece na fronteira de `w_eff` e desliza ao longo dela, divergindo da fronteira de `w` — a perda é ancorada e monótona no desvio.
- A greedy não tem garantia em `w_eff` nenhuma: a sua perda é dominada pela foreclosure, que é ortogonal à re-ponderação (nenhum `w` restaura um sítio já excluído). Logo o ganho da óptima é a parcela de foreclosure que sobrevive ao desvio — e satura.

**Bónus:** a mesma estrutura explica a anomalia Peldschus. A greedy é função descontínua do score (depende só da ordem), logo uma inclinação de amplitude de ordem 10⁻³ produz saltos discretos de sinal não determinado — valor esperado ≈ 0, variância > 0. A óptima é suave e degrada monotonicamente. Uma proposição que unifique a interacção e o desvio do Peldschus é uma contribuição genuína.

**Fallback se a prova não fechar:** enunciar como decomposição empírica com o limite superior verificado nas ≥10 instâncias do WS1, e deixar a forma fechada como conjectura explícita. Ainda mais forte do que o artigo tem hoje. Não forçar uma prova frágil.

**Esforço:** 2–4 semanas, com incerteza real.
**Ganho:** B− → A− se fechar; → B+ se ficar em conjectura verificada.

---

## Workstream 4 — Pipeline numérico

Não melhora o conteúdo, mas elimina a classe de erros que dominou estas rondas de revisão — todos eram detectáveis por aritmética sobre tabelas impressas.

**Componentes:**

1. **Macros `\newcommand` geradas por script** a partir dos CSV — todos os números do texto
2. **`make check`** que recomputa cada quantidade derivada e falha se divergir da macro. Em particular:
   - Identidade `Q2[A'] = (Q2_greedy + Q2_optimal) / 2` entre tab:tvorder e tab:factorial
   - Estimand correcto em comparações texto-vs-modelo (greedy SAW vs média sobre montagens)
3. **Hash de execução em cada legenda de tabela** — torna impossível ligar tabelas de execuções diferentes sem o ver
4. **Teste de estimand** — verifica que cada comparação usa o mesmo estimand em ambos os lados

**Esforço:** 3–5 dias.
**Ganho:** C+ → A em execução; evita que os WS1–3 introduzam novos desalinhamentos.

---

## Workstream 5 — Reestruturação

**Promover a interacção.** Hoje está em §7.4, enterrada. É a única afirmação simultaneamente analítica, contraintuitiva e accionável: programação inteira sobre um score mal normalizado optimiza o desvio exactamente. Com a Proposição do WS3 por trás, torna-se o segundo pilar do artigo.

**Mudanças concretas:**
- **Título:** considerar trazer a montagem. O actual vende "normalisation as implicit re-weighting" — que é a parte mais fraca (Choo). A parte forte é o custo medido contra uma fronteira exacta e a interacção com a optimização.
- **Highlights:** substituir o primeiro (o Lema, que é restatement) pelo resultado da interacção.
- **Resumo:** os +29.8 vs +2.2 pp merecem estar na segunda frase, não na penúltima.
- **Figura nova:** decomposição foreclosure/misalignment ao longo do caminho `A_j(t)`, com as duas variantes de objectivo. Seria a figura mais informativa do artigo.

**Esforço:** 1 semana.
**Ganho:** meia nota de percepção editorial — desproporcional ao custo.

---

## Sequência e calendário

| Fase | Semanas | Conteúdo | Nota projectada |
|---|---|---|---|
| 0 | 1 | WS4 (pipeline) | 8.0 |
| 1 | 2–4 | WS1 (corpus de matrizes reais) | 8.5 |
| 2 | 1 | WS2 (caminho `A_j(t)`, N=3500, duas variantes) | 8.7 |
| 3 | 2–4 | WS3 (proposição foreclosure–misalignment) | 9.0 se fechar; 8.8 se conjectura |
| 4 | 1 | WS5 (reestruturação) + recompilação total | 9.0 |

**Total:** 7–11 semanas.

**Nota:** a Fase 0 (WS4) é pré-requisito. Sem o pipeline, as fases seguintes reintroduzem inconsistências.

---

## Disciplina de escopo: o que não fazer

| Acção | Razão |
|---|---|
| Adicionar famílias de normalização | Aglomeram-se em TV≈0 ou saltam para ≥0.31; Weitendorf = min-max; trabalho sem retorno |
| Estender a métodos outranking com funções não-lineares | Declarado correctamente como aberto; abrir essa frente dilui |
| Refazer a grade sintética | WS1 (matrizes reais) domina-a em todas as dimensões; a grade pode ficar ou ir para Material Suplementar |
| Aumentar κ ou adicionar níveis de κ | A incerteza de peso não é o gargalo; o suporte de TV é |

---

## O que não chega a 10 (e provavelmente não deve)

O Lema da amplitude continua a ser Choo com álgebra. Um 10 exigiria um resultado de unicidade axiomática — min-max como a única normalização preservadora de pesos numa classe ampla e caracterizada, não apenas entre as três padrão. É um teorema plausível e ao alcance, mas é outro artigo.

---

## Estado actual do manuscrito (pré-WS0)

| Item | Estado |
|---|---|
| tab:tvorder ↔ tab:factorial aritmética | ✓ (82.3 = (64.6+100.0)/2) |
| §7.2 slope=−86.7, R²=0.994, diagnósticos 3-level | ✓ |
| §7.7 comparador correcto (10.4 pp greedy SAW) | ✓ |
| §8.6 bloco WP3 unificado, −93.0 SE=6.8 df=3 | ✓ |
| §8.6 "lower bound" removido | ✓ |
| rem:scope canónico (82.3/76.5/55.5) | ✓ |
| Peldschus rotulado como suplementar, t=3.34 p=0.0009 | ✓ |
| Conclusão τ_b=0.550 com estimand correcto | ✓ |
| Weitendorf: uma ocorrência, identidade algébrica | ✓ |
| 26.8 pp em ambas as ocorrências | ✓ |
| 0 erros xelatex, 25 páginas | ✓ |
| último commit | 87bf3b9 |
