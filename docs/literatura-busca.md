# Busca Sistemática de Literatura — Artigo A1

**Data:** 27/set/2026
**Objetivo:** mapear o estado da arte em 6 frentes para identificar lacunas que o artigo A1 pode preencher.

---

## SUMÁRIO EXECUTIVO

A busca de 6 frentes temáticas revela um padrão claro: **a lacuna central do artigo existe e não está coberta**. Os artigos encontrados comparam métodos MCDM entre si usando rankings e correlações. Nenhum deles benchmarkeia trios/portfólios de locais contra uma fronteira de Pareto exata com restrição de dispersão espacial. O efeito da normalização foi documentado em rankings de alternativas individuais, mas não em seleção de conjuntos.

**Conclusão preliminar:** a combinação de três elementos não aparece na literatura — (1) restrição espacial de dispersão, (2) fronteira exata como benchmark, (3) separação de normalização e agregação como fatores. A lacuna é real.

---

## FRENTE 1 — MCDM + Pareto consistency / benchmarking

### Artigo chave: Sałabun et al. (2020)
**Título:** Are MCDA Methods Benchmarkable? A Comparative Study of TOPSIS, VIKOR, COPRAS, and PROMETHEE II
**DOI:** 10.3390/sym12091549
**Periódico:** Symmetry (MDPI)
**Citações:** 438
**Resumo:** benchmarkeia 4 métodos (TOPSIS, VIKOR, COPRAS, PROMETHEE II) usando coeficientes de similaridade (WS e Spearman) variando número de atributos, alternativas, métodos de ponderação e técnicas de normalização. Mostra que a normalização e os pesos afetam os rankings.
**Relevância para o artigo:** define o estado da arte em benchmarking de MCDM. O artigo de Sałabun *não* usa fronteira de Pareto como benchmark externo, nem seleciona conjuntos. É o ponto de partida metodológico.
**Lacuna que abre:** os autores medem "similaridade entre rankings", não "qualidade da seleção de conjunto em relação ao ótimo de Pareto". Isso é exatamente o que o artigo propõe.

### Artigo relacionado: Paradowski & Salabun (2024)
**Título:** Enhancing Objective Decision-Making with Exhaustive Objective Ranking Solution (EORS)
**DOI:** 10.1109/cdc56724.2024.10886096
**Citações:** 4
**Resumo:** propõe ranking exaustivo de soluções. Usa IEEE CDC — mais teórico, menos aplicado.
**Relevância:** confirma tendência de benchmark objetivo, mas não usa Pareto de conjuntos.

### Artigo relacionado: Sumanto et al.
**Título:** Benchmarking Aggregation-Based MCDM Methods: A Comparative Analysis of Ranking Consistency, Stability, and Robustness
**DOI:** 10.67449/jodesma.v1i2.9
**Resumo:** benchmarkeia SAW, WASPAS, ARAS, COPRAS, MAIRCA. Usa Spearman, RSI, RRR. Foco em seleção de funcionário (n pequeno). Sem Pareto.
**Relevância:** confirma que benchmarking de MCDM sem Pareto externo é o padrão atual — o que reforça a lacuna.

### LACUNA IDENTIFICADA (Frente 1):
Nenhum artigo benchmarkeia métodos pelo desvio em relação à fronteira de Pareto exata. Todos usam similaridade entre rankings como métrica. A pergunta "o método seleciona conjuntos Pareto-ótimos?" não foi feita antes no contexto de localização de facilidades.

---

## FRENTE 2 — Normalização em MCDM: efeito nos rankings

### Artigo chave: Petrović et al. (2025)
**Título:** Comparative Investigation of Normalization Techniques and Their Influence on MCDM Ranking — A Case Study
**DOI:** 10.31181/smeor21202542
**Periódico:** Spectrum of Mechanical Engineering and Operational Research
**Citações:** 10
**Resumo:** aplica CRITIC+TOPSIS com diferentes normalizações (min-max, max, vector, etc.) para selecionar tecnologia de propulsão de ônibus. Usa Spearman para comparar rankings.
**Relevância:** confirma que o efeito da normalização no TOPSIS é documentado na literatura, mas em rankings de alternativas individuais.

### Artigo chave: Mukhametzyanov (2023)
**Título:** Rank Reversal in MCDM Models: Contribution of the Normalization
**DOI:** 10.1007/978-3-031-33837-3_6
**Periódico:** Springer ISOR series (capítulo de livro)
**Citações:** 4
**Resumo:** analisa formalmente como a normalização contribui para rank reversal em MCDM. Mostra que métodos diferentes de normalização produzem rank reversals distintos.
**Relevância direta:** o mecanismo que o artigo propõe (distorção de pesos efetivos por normalização vetorial) é consistente com este resultado. O artigo proposto vai além: quantifica a distorção com pesos efetivos e mostra que ela afeta a qualidade do conjunto, não apenas o ranking.

### Artigo chave: Ersoy (2022)
**Título:** The Influence of Statistical Normalization Techniques on Performance Ranking Results
**DOI:** 10.4018/ijban.298017
**Periódico:** International Journal of Business Analytics
**Citações:** 7
**Resumo:** compara 5 normalizações (max, min-max, sum, z-score, etc.) para método de Biswas e Saha. Conclui que max normalização é a mais consistente.
**Relevância:** mostra que efeito da normalização em MCDM é problema geral, não específico do TOPSIS.

### LACUNA IDENTIFICADA (Frente 2):
A literatura documenta rank reversal e inconsistência de rankings causados por normalização. Mas nenhum artigo: (a) quantifica a distorção em termos de pesos efetivos como o artigo propõe, nem (b) mostra que a normalização afeta a qualidade de conjuntos de localização. A P3 do artigo proposto é nova.

---

## FRENTE 3 — TOPSIS: normalização vetorial vs min-max

### Artigo chave: Shyur & Shih (2024)
**Título:** Resolving Rank Reversal in TOPSIS: A Comprehensive Analysis of Distance Metrics and Normalization Methods
**DOI:** 10.15388/24-infor576
**Periódico:** Informatica
**Citações:** 19
**Resumo:** análise matemática de min-max e max normalization + métricas Euclidiana, Manhattan e Chebyshev no TOPSIS. Explora quando rank reversal ocorre ao adicionar alternativas.
**Relevância:** é o paper de referência mais próximo do resultado P3 do artigo. Mas o foco é rank reversal de alternativas individuais, não qualidade de conjuntos.

### Artigo chave: Yang et al. (2022)
**Título:** Materials selection method using improved TOPSIS without rank reversal based on linear max-min normalization with absolute maximum and minimum values
**DOI:** 10.1088/2053-1591/ac2d6b
**Periódico:** Materials Research Express (IOP)
**Citações:** 24
**Resumo:** propõe TOPSIS melhorado com normalização max-min absoluta para eliminar rank reversal. As closeness values passam a ser absolutas (independentes do conjunto de alternativas).
**Relevância:** confirma que a comunidade sabe que normalização vetorial causa problemas. A solução proposta (valores absolutos) é diferente da solução min-max mas parte da mesma premissa.

### Artigo: Ni & Hu (2025)
**Título:** The Prediction of Rank Reversal in TOPSIS
**DOI:** 10.47577/eximia.v14i1.540
**Resumo:** analisa matematicamente quando rank reversal ocorre no TOPSIS com normalização linear. Propõe previsão analítica do rank reversal.
**Relevância:** confirma que o mecanismo de distorção no TOPSIS é um problema ativo.

### LACUNA IDENTIFICADA (Frente 3):
A literatura sabe que normalização no TOPSIS afeta rankings. Mas nenhum artigo: (a) atribui a causa a distorção de pesos efetivos por outliers em dados geoespaciais, nem (b) mostra que isso leva a seleção de conjuntos não Pareto-ótimos em localização de facilidades.

---

## FRENTE 4 — Multi-site / portfólio + MCDM + espacial

### Artigo relevante: Zhou et al. (2026)
**Título:** Multi-Source Geospatial Data-Driven Multi-Objective Spatial Optimization for Vertiport Location in Urban Air Mobility
**DOI:** 10.2139/ssrn.7216697
**Resumo:** localização de k vertiportos em Xangai usando multi-objetivo (NSGA-II) com fronteira de Pareto. Combina OSM + dados geoespaciais + MOOVLP.
**Relevância ALTA:** metodologicamente próximo. A diferença: este artigo usa apenas otimização (sem MCDM), e os objetivos não incluem restrição de dispersão entre pares. **Citar e diferenciar.**

### Artigo relevante: Ghorui (2026)
**Título:** Multi-Objective Optimization of Healthcare Facility Location in Urban Networks: Balancing Efficiency and Social Equity in Delhi
**DOI:** 10.2139/ssrn.6427779
**Resumo:** greedy heurístico + NSGA-II para localização de facilidades de saúde, com trade-off eficiência/equidade. Usa fronteira de Pareto.
**Relevância:** muito próximo metodologicamente. Mas: sem restrição de dispersão espacial, sem MCDM, sem comparação ranking vs portfólio ótimo.

### Artigo relevante: Bhattacharjee & Mukhopadhyay (2026)
**Título:** A Review of Advances in Multi-objective Optimization for Facility Location Problems
**DOI:** 10.1007/978-981-95-7908-2_7
**Periódico:** Springer (capítulo)
**Resumo:** review de avanços em otimização multi-objetivo para localização de facilidades.
**Relevância:** review de 2026 — confirmar se cobre MCDM vs Pareto ou apenas otimização pura.

### Artigo: Costa & Lourenço (2026)
**Título:** On the Selection of a Pareto Solution — A Robust Approach
**DOI:** 10.2139/ssrn.6478022
**Resumo:** usa vários MCDM + variação de pesos para selecionar uma solução da fronteira de Pareto. Usa Sum of Ranking Differences.
**Relevância:** o problema inverso: dado um conjunto Pareto, qual MCDM seleciona a melhor? O artigo propõe o problema direto: dado um ranking MCDM, o conjunto selecionado é Pareto-ótimo?

### LACUNA IDENTIFICADA (Frente 4):
Localização multi-facilidade com fronteira de Pareto existe (Zhou, Ghorui). Mas: nenhum combina (1) restrição de dispersão espacial entre pares + (2) comparação de rankings MCDM contra a fronteira + (3) separação de normalização e agregação como fatores explicativos.

---

## FRENTE 5 — Seleção de aterro: MCDM + GIS

### Artigo chave: Bechroune et al. (2024)
**Título:** GIS-MCDM integrated approach for suitable landfill site selection (Bejaia, Algeria)
**DOI:** 10.1007/s10661-024-13381-9
**Periódico:** Environmental Monitoring and Assessment (Springer)
**Citações:** 16
**Resumo:** AHP + sobreposição GIS, 14 critérios, mapa de aptidão. Seleciona 4 de 13 candidatos.
**Relevância:** típico artigo de aterro. Seleciona 1 local, sem otimização multi-objetivo, sem benchmark de Pareto.

### Artigo chave: Mozaffari et al. (2023)
**Título:** Integration of LCSA and GIS-based MCDM for sustainable landfill site selection
**DOI:** 10.1007/s10661-023-11112-0
**Periódico:** Environmental Monitoring and Assessment
**Citações:** 27
**Resumo:** integra Life Cycle Sustainability Assessment + MCDM-GIS. Análise de ciclo de vida + MCDM clássico.
**Relevância:** metodologicamente avançado dentro do paradigma atual. Ainda seleciona 1 local.

### Artigo chave: Armanuos et al. (2023)
**Título:** Landfill site selection using MCDM methods and GIS (Nile Delta, Egypt)
**DOI:** 10.1007/s10661-023-11946-8
**Periódico:** Environmental Monitoring and Assessment
**Citações:** 36
**Resumo:** AHP, RSW, SRS e Booleano. Combina resultados de 4 métodos. 11 critérios.
**Relevância:** compara 4 métodos mas usando mapa de aptidão, não ranking de candidatos individuais.

### Artigo chave: Jafarzadeh & Nasiri (2022)
**Título:** Sustainable landfill site selection for hazardous waste using GIS-based MCDM with G-number information
**DOI:** 10.1007/s10668-022-02400-9
**Periódico:** Environment, Development and Sustainability (Springer)
**Citações:** 13
**Resumo:** usa G-numbers (extensão dos intervalos) + AHP + GIS. Foco em incerteza.

### Artigo: Özkurt (2024)
**Título:** A MCDM approach to the facility location selection problem of sustainable solid waste management
**DOI:** 10.47743/pesd2024182006
**Resumo:** TOPSIS + EDAS para aterro na Turquia. Ambos convergem para o mesmo site. Análise de sensibilidade confirma robustez.
**Relevância:** comparação TOPSIS vs EDAS, mas sem benchmark externo.

### LACUNA IDENTIFICADA (Frente 5):
A literatura de aterros usa MCDM-GIS para selecionar 1 site. Nenhum artigo: (a) seleciona k sites com restrição de dispersão, (b) usa fronteira de Pareto exata como benchmark, (c) compara o efeito da normalização na qualidade da seleção de conjunto.

---

## FRENTE 6 — PROMETHEE II vs outros métodos

### Artigo chave: Sałabun et al. (2020)
(já citado na Frente 1 — inclui PROMETHEE II no benchmark)
**Relevância adicional:** PROMETHEE II é um dos 4 métodos benchmarkeados. Resultados mostram que PROMETHEE II é mais estável que TOPSIS sob variações de normalização.

### Artigo: Lassey (2025)
**Título:** Comparative Analysis of PROMETHEE, VIKOR and TOPSIS for Logistics Centre Location Selection
**DOI:** 10.21203/rs.3.rs-7870462/v1
**Resumo:** PROMETHEE II e VIKOR dão o mesmo ranking; TOPSIS discorda. Atribui a discordância à incapacidade do TOPSIS de considerar distâncias relativas de PIS e NIS.
**Relevância ALTA:** confirma a observação do artigo (TOPSIS diverge) e aponta a mesma direção. Mas a explicação é qualitativa, não quantitativa como a P3 proposta.

### Artigo: Gülmez (2025)
**Título:** A novel hybrid MCDM framework combining TOPSIS, PROMETHEE II, and VIKOR for peach drying method selection
**DOI:** 10.1016/j.crfs.2025.101034
**Citações:** 17
**Resumo:** combina os 3 métodos em framework híbrido. Foco em consenso.
**Relevância:** estratégia de combinar métodos é alternativa à nossa abordagem de entender por que divergem.

### LACUNA IDENTIFICADA (Frente 6):
A literatura já sabe que PROMETHEE e SAW tendem a convergir e TOPSIS diverge. Mas nenhum artigo: (a) deriva formalmente que PROMETHEE (critério usual) = SAW sobre postos (P2 do artigo), (b) usa essa derivação para explicar concordância, nem (c) testa no contexto de seleção de conjuntos.

---

## ANÁLISE DE LACUNAS CONSOLIDADA

### Matriz de lacunas

| Dimensão | Estado da arte | O que falta |
|----------|---------------|-------------|
| Benchmark de MCDM | Similaridade entre rankings (Spearman, WS) | Desvio em relação a fronteira de Pareto exata |
| Normalização | Rank reversal documentado em alternativas individuais | Efeito em seleção de conjuntos + mecanismo de pesos efetivos |
| TOPSIS vs outros | TOPSIS diverge (documentado) | Por quê (pesos efetivos distorcidos por outliers) — quantificado |
| Multi-site + Pareto | Localização multi-facilidade com Pareto existe (sem MCDM) | Comparação MCDM vs Pareto com restrição de dispersão |
| Aterros | k=1, sem Pareto | k=3, fronteira exata, benchmark de métodos |
| PROMETHEE vs SAW | Convergência observada | Derivação formal como SAW sobre postos |

### O que o artigo propõe que ninguém fez

1. **Benchmark de conjuntos contra Pareto exata** com restrição espacial de dispersão — não existe na literatura.
2. **Mecanismo quantificado de distorção de normalização** (pesos efetivos) como causa de seleção de conjunto não Pareto-ótimo — não existe.
3. **Derivação formal PROMETHEE = SAW sobre postos** para explicar concordância — não foi publicada assim.
4. **Proposições P1–P4** formalizando quando ranking gera conjuntos Pareto-ótimos e quando não — não existe como corpo teórico.

### O que existe e precisa ser citado

| Paper | Por que citar |
|-------|---------------|
| Sałabun et al. (2020) Symmetry | Estado da arte em benchmarking MCDM |
| Shyur & Shih (2024) Informatica | Normalização e rank reversal no TOPSIS |
| Mukhametzyanov (2023) Springer | Normalização e rank reversal geral |
| Zhou et al. (2026) preprint | Multi-facilidade com Pareto (diferente: sem MCDM, sem dispersão) |
| Lassey (2025) preprint | PROMETHEE/VIKOR vs TOPSIS em localização |
| Bechroune et al. (2024) EMA | Aterro com MCDM-GIS (sem Pareto) |
| Armanuos et al. (2023) EMA | Aterro com múltiplos métodos |
| Costa & Lourenço (2026) preprint | Seleção de ponto Pareto via MCDM (problema inverso) |

---

## STRINGS DE BUSCA PARA SCOPUS / WEB OF SCIENCE

Rodar estas strings antes da submissão para confirmar que a lacuna não foi preenchida:

```
S1 (lacuna central):
("MCDM" OR "multi-criteria") AND ("Pareto front" OR "Pareto optimal") 
AND ("facility location" OR "site selection") AND ("benchmark" OR "comparison")
ANOS: 2020-2026

S2 (portfolio MCDM):
("MCDM" OR "TOPSIS" OR "VIKOR" OR "PROMETHEE") 
AND ("portfolio selection" OR "set selection" OR "subset selection")
AND ("spatial" OR "location" OR "facility")
ANOS: 2020-2026

S3 (normalização efeito em seleção):
("normalization" OR "normalisation") AND ("TOPSIS" OR "MCDM")
AND ("effective weight" OR "weight distortion") 
ANOS: 2020-2026

S4 (PROMETHEE = rank aggregation):
("PROMETHEE") AND ("rank" OR "Borda") AND ("equivalence" OR "linear")
ANOS: 2015-2026

S5 (greedy vs optimal MCDM):
("greedy" OR "sequential selection") AND ("MCDM" OR "multi-criteria")
AND ("Pareto" OR "dominated" OR "non-dominated")
ANOS: 2020-2026
```

---

## PRÓXIMOS PASSOS

1. Rodar S1–S5 no Scopus e Web of Science (30 min cada string).
2. Verificar `Bhattacharjee & Mukhopadhyay (2026)` (review completo de multi-objetivo em localização) — pode cobrir terreno próximo.
3. Verificar `Costa & Lourenço (2026)` (seleção de ponto Pareto via MCDM) — problema inverso, mas pode ser mal-interpretado como sobreposição.
4. Buscar citantes de Liesiö et al. (2007) EJOR (Robust Portfolio Modeling) para 2020–2026.

---

*Arquivo gerado automaticamente a partir das buscas de 27/set/2026.*
*Atualizar quando novas buscas forem realizadas no Scopus/WoS.*
