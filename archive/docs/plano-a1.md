# Plano: transformar o trabalho num artigo A1

**Arquivo criado em:** 27/set/2026
**Diretório do projeto:** `G:\Faculdade\Estudo\Mestrado\2022.1\Trabalhos\Multicriterio\03-latex\paper - Comparison between MCDM Methods for Landfill Site Selection\`
**Status geral:** Em andamento — base empírica sólida, experimento fatorial e teoria pendentes.

---

## Status rápido

| Item | Status |
|------|--------|
| Dataset Ilha do Fogo (473 candidatos, 389 viáveis) | ✅ Confirmado |
| Fronteira exata (213 trios) | ✅ Reproduzida com diff < 1e-9 |
| 4 métodos (SAW, TOPSIS, VIKOR, PROMETHEE) | ✅ Implementados e rodados |
| TOPSIS min-max como variante | ✅ {184,227,460} — Pareto-ótimo |
| PROMETHEE ótimo | ✅ {51,233,345} — mesmo do greedy |
| Gap normalizado pela amplitude da fronteira | ✅ Calculado |
| Taxa de base (91/389 = 23.4%) | ✅ Calculada |
| Pesos efetivos (mecanismo vetorial identificado) | ✅ perm: 0.152→0.549 |
| Proposições P1–P4 | ⬜ Redigir com provas |
| Monte Carlo nos pesos (Dirichlet, 500 sorteios) | ✅ Implementado v3 (corrigido, 4/4 PASS) |
| Espaço de avaliação B (não aditivo) | ✅ Implementado v2 (validado PASS vs brute force N=80) |
| Proposições P1–P4 | ✅ P1 confirmada (Q2 100%), P2-P4 confirmadas. P3 reformulada (rivers, não perm). |
| Decomposição de variância preliminar (Fogo) | ✅ Calculada em diag_r9.py |
| Importância w×std nas 3 normalizações | ✅ Calculada em diag_r9.py |
| Mais instâncias (outras ilhas) | ⬜ Verificar dados OSM |
| Instâncias sintéticas (gerador) | ⬜ Implementar |
| Experimento fatorial completo | ⬜ Depende de mais instâncias |
| Busca sistemática (lacuna vs portfólios) | ⬜ Esta semana |
| MILP ε-restrito para instâncias maiores | ⬜ Mês 2 |
| Análise estatística (ANOVA / Friedman) | ⬜ Mês 4 |
| Redação completa do manuscrito novo | ⬜ Mês 5 |
| Pacote de reprodutibilidade | ⬜ Mês 6 |

---

## 1. Diagnóstico: o que um revisor A1 vai cobrar

| O que será cobrado | Situação atual | O que fazer |
|---|---|---|
| Contribuição que se generaliza | 1 instância | Várias instâncias reais e sintéticas (§5) |
| Explicação dos resultados, não só descrição | Resultados empíricos soltos | Proposições formais P1–P4 (§3) |
| Avaliação que não favoreça nenhum método | Espaço aditivo favorece SAW e PROMETHEE por construção | Segundo espaço de avaliação B, não aditivo (§4) |
| Robustez | 1 vetor de pesos | Monte Carlo nos pesos + variação de k e d_min (§6) |
| Conclusões com força estatística | Tabelas por método | Desenho fatorial + decomposição da variância (§6) |
| Posicionamento na literatura | Apenas MCDM aplicado a aterros | Incluir literatura de seleção de portfólios (§2) |
| Reprodutibilidade | Scripts locais | Pacote aberto com dados, código e gerador de instâncias |

---

## 2. Pergunta central e contribuições

**Pergunta central:** quando um ranking MCDM é usado para escolher k locais com restrição de dispersão, quanto se perde em relação à fronteira de Pareto exata? E o que explica essa perda: a normalização, a agregação ou a forma de montar o conjunto?

**C1 — Teórica:** proposições que explicam quando um ranking gera conjuntos Pareto-ótimos e quando não gera.

**C2 — Empírica:** benchmark em várias instâncias contra fronteiras exatas, com a importância de cada fator quantificada (decomposição da variância).

**C3 — Prática:** recomendações para quem usa MCDM na escolha de múltiplos locais + benchmark aberto (dados + código).

**Risco de posicionamento** ⚠️: escolher os k primeiros de um ranking em vez de otimizar o conjunto é tema conhecido em decisão de portfólios (ex.: Liesiö, Mild & Salo, EJOR 2007; Mavrotas et al.). Um revisor de EJOR ou Omega vai levantar isso. A novidade possível está na combinação: restrição espacial de dispersão + fronteira exata + separação entre normalização e agregação. **Fazer busca sistemática antes de redigir.**

Strings sugeridas para Scopus/WoS:
- `"ranking-based selection" AND "portfolio" AND ("Pareto" OR "multi-objective")`
- `"MCDM" AND "Pareto consistency" AND "facility location"`
- `"top-k selection" AND ("facility location" OR "site selection") AND "Pareto"`

---

## 3. Proposições a redigir com provas

### P1 — SAW/PROMETHEE no espaço aditivo são Pareto-consistentes
**Enunciado:** se o score do método é uma escalarização coerente com os sentidos dos objetivos (S = -f1 - f2 + f3 com os mesmos pesos), o conjunto ótimo pelo score é Pareto-ótimo no espaço A.

**Condição necessária:** o score deve ter os sinais corretos. SAW clássico (maximiza f1+f2+f3) NÃO é coerente porque maximiza custo e impacto. O score coerente é S1 = -f1-f2+f3.

**Evidência em Fogo:** SAW_s1 ótimo = 100% não dominado em Q2 com qualquer vetor de pesos plausível (500 sorteios, α=200). P1 confirmada numericamente.

**Evidência errada (removida):** "PROMETHEE ótimo in_front=True" — P1 não cobre PROMETHEE (scores são postos, não valores min-max).

**Nota:** "f1+f2+f3 = S1 = SAW-473" estava errado. SAW-473 maximiza f1+f2+f3, que não é Pareto-coerente. S1 = -f1-f2+f3.

**Status:** ✅ Confirmada numericamente (Q2). ⬜ Escrever prova formal com sinais corretos.

---

### P2 — PROMETHEE II (critério usual) é SAW sobre postos
**Enunciado:** com o critério usual (P(d)=1 se d>0, 0 se d≤0) e usando postos médios para empates:
$$\phi(a) = \sum_j w_j \cdot \frac{2\,r_j(a) - n - 1}{n - 1}$$

O fluxo líquido é uma soma ponderada linear dos postos de cada critério.

**Evidência em Fogo:** concordância SAW–PROMETHEE r_w=0.923. Greedy e ótimo do PROMETHEE convergem para o mesmo trio.

**Status:** ✅ Prova algébrica em propositions.tex. **Nota:** verificar derivação com postos médios para o aspect binário (0/1 nos 389 viáveis — as 84 excluídas são por `dist_protected=0`, não por aspect).

---

### P3 — Normalização vetorial distorce pesos efetivos via critérios com cauda longa
**Enunciado:** no TOPSIS vetorial, o peso efetivo do critério j é proporcional a $w_j \cdot \text{std}(r_{ij})$ onde $r_{ij} = x_{ij}/\|x_j\|$. Critérios com distribuição de cauda longa (outliers) ganham peso desproporcional.

**Critério inflado: rivers (não perm):** rivers tem vec/mm = 2.40× na métrica w×std. Perm tem vec/mm = 0.47× (reduz, não infla). O mecanismo: distâncias de rios têm outliers grandes (maioria perto de rios, poucos muito longes), que dominam a norma vetorial.

**Achado adicional:** aspect binário tem mm_norm=0.148 (2º maior) porque variável 0/1 maximiza o desvio padrão na normalização min-max. Min-max não é "pesos nominais" para critérios binários.

**Evidência em Fogo:** TOPSIS-VN ótimo tem gap_norm=0.024, dominado. TOPSIS-MM greedy tem gap_norm=0.000 (na fronteira). MC Q1: TOPSIS-VN greedy 1% não-dominado; TOPSIS-MM 40%.

**Status:** ✅ Calculado em diag_r9.py. ⬜ Atualizar propositions.tex (P3 usa perm incorretamente). ⬜ Equação do peso efetivo a reescrever com rivers como exemplo.

---

### P4 — Guloso sob dispersão pode sair dominado mesmo com score linear
**Enunciado:** mesmo quando o score garante Pareto-consistência do ótimo (P1), o guloso pode selecionar um conjunto dominado.

**Evidência em Fogo:** SAW greedy = {184,279,320}, gap_norm=0.032. SAW_s1 ótimo na fronteira.

**Status:** ✅ Verificada. Contraexemplo documentado.

---

## 4. Segundo espaço de avaliação B v2 — IMPLEMENTADO

**Definição v2 (B v1 descartado por circularidade):**
- B1 = f1(T) = soma custo (aditivo, âncora)
- B2 = max_i f2(i) = pior impacto ambiental (gargalo, não aditivo — P1 não se aplica)
- B3 = min_i f3(i) = gargalo de segurança (não aditivo)

**Fronteira B v2:** 108 trios, A∩B=33. Algoritmo: `paretoset`, validado vs brute force N=80.

**Resultado:** apenas TOPSIS-MM greedy {184,227,460} na fronteira B — posição de extremo de segurança, não vantagem metodológica.

**Status:** ✅ Calculado e salvo em pareto_front_B_v2.csv. ⬜ Rodar MC Q2 no espaço B. ⬜ Rodar MC no espaço B.

---

## 5. Mais instâncias

### 5.1 Instâncias reais (outras ilhas)
Pipeline do IEEE usa OSM + DEM ASTER + camadas de exclusão. Candidatas:

| Ilha | País | Pop. aprox. | Verificar antes |
|------|------|------------|-----------------|
| Santiago (Cabo Verde) | Cabo Verde | ~300k | Áreas protegidas, geologia |
| Santo Antão | Cabo Verde | ~50k | Áreas protegidas, geologia |
| São Tomé | S. Tomé e Príncipe | ~200k | OSM coverage, geologia |
| Outras ilhas dos SIDS | — | — | OSM quality |

**Critério de inclusão:** camadas de áreas protegidas + geologia (permeabilidade) disponíveis. Sem elas, a instância fica incompleta.

**Status:** ⬜ Verificar OSM coverage e camadas de exclusão para pelo menos 3 ilhas.

### 5.2 Instâncias sintéticas (gerador)
Controlar:
- correlação entre critérios
- grau de agrupamento espacial
- proporção de critérios binários
- N (de ~100 a 1000+)

Permite testar por que a perda acontece, variando um fator de cada vez.

**Status:** ⬜ Implementar gerador em Python. ⬜ Validar que as fronteiras sintéticas são reproduzíveis.

### 5.3 Castanhal (descartado por enquanto)
7 alternativas é muito pouco. Só entra se os dados forem verificados no PDF de Sousa (2022) e mesmo assim apenas como exemplo pedagógico, não como instância de benchmark.

---

## 6. Desenho experimental fatorial

| Fator | Níveis |
|-------|--------|
| Normalização | min-max, vetorial, postos, soma, escore-z |
| Agregação | linear (SAW), distância ao ideal (TOPSIS), compromisso (VIKOR), outranking (PROMETHEE usual e com função em V) |
| Montagem do conjunto | guloso, ótimo, variante portfólio |
| Pesos | Monte Carlo Dirichlet(α·w_AHP), α ∈ {50, 200}; 500 sorteios; semente fixa |
| k e d_min | k ∈ {2, 3, 4, 5}; dois ou três limiares de distância |
| Instância e espaço | todas as instâncias; espaços A e B |

**Métricas:**
- taxa de conjuntos não dominados
- gap_norm (pela amplitude ideal–nadir)
- fração dos viáveis que dominam o conjunto escolhido
- Jaccard@k comparado com a taxa de base

**Análise estatística:**
- Decomposição da variância do gap por fator: η² de ANOVA ou modelo de efeitos mistos (instância como efeito aleatório). Sustenta "a normalização explica X% da variação".
- Comparações entre métodos ao longo das instâncias: Friedman + Nemenyi, ou equivalentes bayesianos, com tamanhos de efeito.

**Status:** ⬜ Depende de mais instâncias (§5) e do espaço B (§4).

---

## 7. O que sai do artigo

- Experimento de 2022 (ranqueamento de critérios): fica no máximo como parágrafo de contexto histórico na Introdução.
- AHP como método de ranqueamento: passa a servir apenas para derivar os pesos, com CR=0.056 informado.
- Tabelas 2–6 atuais do main.tex: saem.

**Decisão registrada:** este é um artigo novo. O main.tex atual pode servir como ponto de partida para a redação, mas não como estrutura a preservar.

---

## 8. Estrutura do manuscrito

1. **Introdução:** o problema da escolha de múltiplos locais com restrição de dispersão; a lacuna entre ranking e fronteira exata; contribuições C1–C3.
2. **Literatura:** MCDM na localização de aterros; análise de decisão de portfólios; comparações entre MCDM e otimização multiobjetivo; efeitos da normalização.
3. **Formulação e proposições:** definições formais; P1–P4 com provas.
4. **Desenho experimental:** instâncias; fatores; como calcular fronteiras exatas (enumeração e MILP ε-restrito); métricas.
5. **Resultados:** Fogo como caso ilustrativo; benchmark completo; decomposição da variância.
6. **Discussão:** implicações práticas; limitações; quando vale a pena usar otimização em vez de ranking.
7. **Conclusão** + declaração de dados abertos.

**Título possível:** "Normalization matters more than method: benchmarking MCDM rankings against an exact Pareto front for multi-site landfill selection"

---

## 9. Periódicos-alvo

| Perfil | Candidatos A1 |
|--------|--------------|
| Metodológico, com teoria e benchmark | European Journal of Operational Research (EJOR), Omega, Computers & Operations Research (COR), Decision Support Systems (DSS) |
| Metodológico aplicado | Expert Systems with Applications (ESWA) |
| Aplicado com componente metodológico | Waste Management, Journal of Environmental Management, Journal of Cleaner Production |

**Nota sobre Qualis:** verificar a classificação vigente na Plataforma Sucupira antes de submeter. A lista de estratos muda entre ciclos. Não confiar em memória.

**Recomendação:** se P1–P4 ficarem formalmente sólidas e o benchmark for multinstância, mirar EJOR, Omega ou DSS. Se o foco ficar no aterro, mirar Waste Management ou JEM.

---

## 10. Riscos e mitigações

| Risco | Mitigação |
|-------|-----------|
| Sobreposição com o artigo IEEE Access (mesmos dados de Fogo) | Citar explicitamente; não repetir figuras nem tabelas; declarar na carta ao editor; contribuição é outra (benchmark de métodos, não otimização) |
| Resultados não se generalizam | O artigo passa a responder "em que condições" — continua publicável |
| Revisores de portfólios apontarem falta de novidade | Busca sistemática antes de escrever + comparação explícita com Robust Portfolio Modeling (Liesiö et al. 2007) |
| Pesos inferidos (Andrade & Barbosa 2015) | Obter o PDF; no Monte Carlo, o vetor exato pesa menos |
| Dados OSM incompletos em outras ilhas | Documentar qualidade por instância; manter sintéticas como controle |
| Afirmar mais do que os dados mostram | Cada afirmação ligada a um número calculado no código |
| Circularidade P1 (espaço A favorece lineares) | Espaço B obrigatório — resultado só é forte se valer nos dois espaços |

---

## 11. Cronograma aproximado (5–6 meses)

| Mês | Entrega | Critério para seguir |
|-----|---------|----------------------|
| 1 | Busca sistemática + P1–P4 escritas e verificadas em Fogo + Monte Carlo em Fogo | Lacuna confirmada; efeito da normalização aparece com pesos variando |
| 2 | Espaço B + MILP ε-restrito validado contra enumeração de Fogo | MILP reproduz os 213 trios |
| 3 | ≥3 instâncias reais + gerador sintético | Dados de exclusão disponíveis nas ilhas escolhidas |
| 4 | Experimento fatorial completo + análise estatística | — |
| 5 | Redação completa | — |
| 6 | Revisão interna + pacote de reprodutibilidade + submissão | — |

---

## 12. O que fazer esta semana

- [ ] **Busca sistemática** (Scopus + WoS) sobre ranking vs portfólio e consistência de Pareto em MCDM. Decide se a novidade se sustenta.
- [ ] **Escrever P1–P4** com provas e verificar cada uma nos números de Fogo.
- [ ] **Rodar Monte Carlo de pesos** em Fogo (Dirichlet, α ∈ {50,200}, 500 sorteios, semente fixa). Primeira indicação de que o efeito da normalização não depende de um vetor.
- [ ] **Registrar no log** a decisão de fazer artigo novo, com experimento de 2022 fora do escopo.

---

## Arquivos relevantes

```
scripts/
  mcdm_experiment.py       ← implementação principal (701 linhas)
  diag2.py                 ← diagnósticos round 7 (taxa de base, pesos efetivos, etc.)
  results/
    mcdm_rankings.csv
    mcdm_trios.csv
    mcdm_concordance.csv

Dados GIS (leitura apenas):
  results_cache/df_real_data_cached.csv          ← 473 linhas, 13 colunas
  New code/results/.../exhaustive_search_pareto.csv  ← 213 trios
```
