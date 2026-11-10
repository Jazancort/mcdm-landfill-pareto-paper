# Response Matrix — Ronda 10-2

> Gerado em sessão 10 (Ronda 10-2).
> Cada linha = uma questão de um dos três pareceres simulados (10-1).
> Colunas: ID, Revisor, Tipo, Questão, Acção, Ficheiro/Linha, Estado.

---

## Legenda

- **Tipo**: MAJOR / MINOR
- **Estado**: OPEN / IN-PROGRESS / DONE / JUSTIFIED (sem alteração, com justificação escrita)
- **Ficheiro/Linha**: caminho relativo à raiz do repositório de trabalho

---

## Reviewer 1 — OR / Combinatorial Optimisation

| ID | Tipo | Questão | Acção | Ficheiro / Linha | Estado |
|----|------|---------|-------|-----------------|--------|
| R1-M1 | MAJOR | Assembly reversal (min-max greedy > vector greedy) apresentado como resultado geral, mas §8 mostra que NÃO replica em Santiago (S2 NOT CONFIRMED em S-T; S6 NOT CONFIRMED em S-T). O abstract e a conclusão não qualificam o resultado a Fogo. | Qualificar "assembly reversal" com "on Fogo" em abstract (L~15), highlights (H4), §7 abertura, §9 Prática 2 e §10 conclusão. Adicionar ressalva "depends on the instance" em cada ocorrência. | `paper/manuscript/main.tex` L~15, L~1900, L~2190, L~2580 | OPEN |
| R1-M2 | MAJOR | O resultado principal do artigo é apresentado como "normalisation equivalence" (abstract H1), mas o resultado real é uma *diferença* de +25.4 pp. "Equivalence" sugere que as normalizações produzem o mesmo resultado, o que é o oposto do que se demonstra. | Substituir "equivalence" por "differential effect" ou "implicit re-weighting" em H1 e no abstract. Verificar que o título e a contribuição (i) usam linguagem consistente. | `paper/manuscript/main.tex` L~5 (highlights), L~10 (abstract) | OPEN |
| R1-M3 | MAJOR | Confusão entre prova matemática (Proposição 1: SAW/min-max/optimal = 100% para qualquer instância) e confirmação empírica (Q2 observado = 100% no Fogo). O texto usa "confirms" para ambos, mas são afirmações de natureza diferente. | Distinguir explicitamente: "Proposition 1 proves analytically that…; the experiment confirms the bound is tight on this instance." Verificar §6 (proposições) e §7 (resultados E1). | `paper/manuscript/main.tex` L~1200–1400 (§6), L~1600–1700 (§7 E1) | OPEN |
| R1-M4 | MAJOR | A medida de gap (Q2 = fracção de draws na fronteira de Pareto) não é comparada com alternativas (e.g., hypervolume indicator, gap to best). A escolha de Q2 não é justificada no contexto de portfolio selection. | Adicionar parágrafo em §4 ou §5 justificando Q2 como medida de eficiência de Pareto para portfolios discretos. Citar literatura de indicadores de qualidade de Pareto (e.g., Zitzler 1999). | `paper/manuscript/main.tex` L~800–900 (§4/§5) | OPEN |
| R1-m1 | MINOR | Tabela 2 (resultados factoriais): os IC de 95% não indicam o método de bootstrap (percentile, BCa, etc.). | Adicionar nota de rodapé à Tabela 2: "Bootstrap 95% CI: percentile method, B=10,000 paired draws, seed=42." | `paper/manuscript/main.tex` L~tabela factorial | OPEN |
| R1-m2 | MINOR | §3 (Problem Formulation): a definição de "feasible portfolio" usa "spatially non-overlapping" sem definir a métrica de sobreposição (buffer? centroid distance?). | Adicionar frase: "Two sites are considered overlapping if their 1-km buffer zones intersect (ok_matrix.npy, §A)." | `paper/manuscript/main.tex` L~600–700 (§3) | OPEN |
| R1-m3 | MINOR | A notação $w_j^{\text{eff}}$ (effective weight) é introduzida na §6 mas não aparece no glossário de notação (§3 ou Tabela de notação). | Adicionar $w_j^{\text{eff}}$ à tabela de notação com definição $w_j A_j / \sum_i w_i A_i$. | `paper/manuscript/main.tex` L~tabela notação | OPEN |
| R1-m4 | MINOR | "Weak dominance" vs "strict dominance": o artigo usa "Pareto-efficient" sem especificar se é dominância fraca ou estrita. Para portfolios com empates (350 tied zeros mencionados), a distinção importa. | Clarificar em §3: "A portfolio $p$ dominates $q$ if $f_k(p) \geq f_k(q)$ for all $k$ and $f_k(p) > f_k(q)$ for at least one $k$ (strict Pareto dominance)." | `paper/manuscript/main.tex` L~§3 definição Pareto | OPEN |

---

## Reviewer 2 — MCDM / MAVT / Normalisation

| ID | Tipo | Questão | Acção | Ficheiro / Linha | Estado |
|----|------|---------|-------|-----------------|--------|
| R2-M1 | MAJOR | O benchmark SAW/min-max/optimal = 100% (Proposição 1) é usado como referência para medir a "perda" das outras células. Mas este benchmark é circular: min-max normaliza para [0,1] e o optimal assembly maximiza exactamente o score SAW. A proposição prova que o método é auto-consistente, não que é superior. | Adicionar parágrafo em §6 ou §9 reconhecendo a circularidade: "Proposition 1 establishes internal consistency of SAW/min-max/optimal, not external optimality. The Q2=100% result means this cell never selects a dominated portfolio, not that it selects the best portfolio by any external criterion." | `paper/manuscript/main.tex` L~§6 após Proposição 1, L~§9 limitações | OPEN |
| R2-M2 | MAJOR | A analogia entre TOPSIS e norma L2 (γ=2) é apresentada como justificação para o comportamento diferente do TOPSIS, mas não é derivada formalmente. A identidade $w_j^{\text{eff}} \propto w_j A_j$ é provada para SAW/min-max; para TOPSIS a relação é apenas sugerida. | Ou derivar formalmente a identidade para TOPSIS (ou mostrar que não se aplica), ou qualificar a afirmação como "conjectured" / "suggested by the data". | `paper/manuscript/main.tex` L~§6 identidade TOPSIS | OPEN |
| R2-M3 | MAJOR | Highlight 1 ("Min-max normalisation recovers the full Pareto frontier") é demasiado forte: é verdade apenas para SAW/optimal (Proposição 1). Para SAW/greedy é +25.4 pp (não 100%). Para TOPSIS/min-max/greedy é substancialmente menos. | Reformular H1: "SAW with min-max normalisation and optimal assembly always recovers the full Pareto frontier (Proposition 1); under greedy assembly, min-max recovers +25.4 pp more than vector normalisation." | `paper/manuscript/main.tex` L~highlights | OPEN |
| R2-M4 | MINOR | A identidade PROMETHEE–Borda mencionada na §2 (literatura) não é usada em nenhum resultado. Se não é relevante para os resultados, deve ser removida ou ligada explicitamente a uma contribuição. | Ou remover a referência à identidade PROMETHEE–Borda, ou adicionar frase: "A analogous identity holds for PROMETHEE (Brans & Mareschal, 1992), suggesting the amplitude distortion mechanism may generalise beyond SAW." | `paper/manuscript/main.tex` L~§2 literatura | OPEN |
| R2-m1 | MINOR | A Tabela 1 (decision matrix Fogo) não indica a fonte dos pesos $w_j$. O texto menciona AHP mas não cita o estudo de elicitação. | Adicionar nota de rodapé: "Weights elicited via AHP by [fonte]; see §A for full elicitation procedure." | `paper/manuscript/main.tex` L~Tabela 1 | OPEN |
| R2-m2 | MINOR | "Vector normalisation" é o termo usado no artigo, mas a literatura usa também "Euclidean normalisation" e "L2 normalisation". Uma nota de rodapé na primeira ocorrência evitaria confusão. | Adicionar nota: "Also called Euclidean or L2 normalisation in the literature." na primeira ocorrência de "vector normalisation". | `paper/manuscript/main.tex` L~primeira ocorrência "vector normalisation" | OPEN |
| R2-m3 | MINOR | A §9 (Discussion) menciona "anchoring bias" como limitação, mas não explica o mecanismo. Um leitor de MCDM esperaria uma referência a Tversky & Kahneman ou a literatura de elicitação de pesos. | Adicionar citação e frase explicativa: "Anchoring bias in weight elicitation (Tversky & Kahneman, 1974) may inflate the nominal weights of criteria with large natural ranges." | `paper/manuscript/main.tex` L~§9 limitações anchoring | OPEN |

---

## Reviewer 3 — GIS / Environmental / Waste Management

| ID | Tipo | Questão | Acção | Ficheiro / Linha | Estado |
|----|------|---------|-------|-----------------|--------|
| R3-M1 | MAJOR | As recomendações práticas (§10, Práticas 1–5) não reflectem os resultados de Santiago. Prática 2 ("use min-max for greedy assembly") e Prática 5 ("assembly matters") são apresentadas como gerais, mas §8 mostra que assembly reversal NÃO replica em S-T e S-N. | Qualificar Práticas 2 e 5 com "on Fogo" e "instance-dependent". Adicionar Prática 6: "Replicate on the target instance before generalising normalisation recommendations." | `paper/manuscript/main.tex` L~§10 Práticas 2, 5 | OPEN |
| R3-M2 | MAJOR | A discrepância entre a área S-N de 387 km² (GIS) e 395 km² (Cabral 2012) não é explicada no texto. Para um leitor de GIS/ambiente, esta diferença (~2%) levanta questões sobre a delimitação da área de estudo. | Adicionar frase em §8.1: "The S-N study area covers the three southern concelhos (~387 km² by GIS measurement of the IDECV boundary polygon; Cabral (2012) reports approximately 395 km², a ~2% difference attributable to projection and polygon resolution)." | `paper/manuscript/santiago.tex` L~38 (§8.1) | OPEN |
| R3-m1 | MINOR | A Figura 1 (mapa de Fogo) não indica a escala nem o sistema de coordenadas (UTM zone). Para replicação, o EPSG é necessário. | Adicionar à legenda da Figura 1: "Coordinate system: UTM Zone 26N (EPSG:32626). Scale bar: 10 km." | `paper/manuscript/main.tex` L~Figura 1 legenda | OPEN |
| R3-m2 | MINOR | O critério ZDTI (zona de distância a infraestruturas) é mencionado mas a sua definição operacional (buffer de quantos metros?) não aparece no corpo principal. | Adicionar frase em §3 ou §A: "ZDTI: distance to existing road network, buffered at 500 m (see §A for full criterion definitions)." | `paper/manuscript/main.tex` L~§3 ou suplementar §A | OPEN |
| R3-m3 | MINOR | A §8 não discute se os resultados de Santiago têm implicações para a política de gestão de resíduos em Cabo Verde. O artigo é metodológico, mas uma frase de implicação aplicada aumentaria o impacto para leitores de waste management. | Adicionar frase final em §8.5 (síntese): "For practitioners in small island developing states, these results suggest that the choice of normalisation method is a first-order decision that should be made explicit and justified before site selection." | `paper/manuscript/santiago.tex` L~§8.5 síntese | OPEN |

---

## Resumo por Estado

```
OPEN        : 18  (R1-M1, R1-M2, R1-M3, R1-M4, R1-m1–m4,
                   R2-M1, R2-M2, R2-M3, R2-M4, R2-m1–m3,
                   R3-M1, R3-M2, R3-m1–m3)
IN-PROGRESS :  0
DONE        :  0
JUSTIFIED   :  0

MAJOR em aberto: 9  (R1-M1, R1-M2, R1-M3, R1-M4, R2-M1, R2-M2, R2-M3, R3-M1, R3-M2)
MINOR em aberto: 9  (R1-m1–m4, R2-m1–m3, R3-m1–m3)
```

---

## Prioridade de Resolução

As MAJOR issues estão agrupadas por bloco de trabalho (ver `session-state.md`):

| Bloco | Issues MAJOR |
|-------|-------------|
| BLOCO 2 (texto Fogo §4, §6, §7) | R1-M3, R1-M4, R2-M2 |
| BLOCO 3 (discussão e limitações) | R1-M1, R2-M1, R3-M1 |
| BLOCO 4 (moldura: abstract, highlights, conclusão) | R1-M2, R2-M3 |
| §8.1 (área S-N) | R3-M2 |

> Nenhuma MAJOR pode ficar OPEN no momento da submissão (critério C9).

---

## Red Team — Ronda 10-3

> Cada afirmação do abstract, highlights e conclusão com evidência, força e acção.
> Força: **Demonstrado** (prova ou dado verificado) / **Sugerido** (tendência, sem prova) / **Exploratório** (post hoc, sem pré-registo).

### Abstract

| ID | Afirmação | Evidência | Força | Acção |
|----|-----------|-----------|-------|-------|
| A1 | "we enumerate all $\Ntrios$ three-site portfolios…and compute the exact Pareto frontier" | `verify_macros_permanent.py` ALL PASS; `\Ntrios` macro verificada | **Demonstrado** | OK |
| A2 | "effective weights are proportional to nominal weight times column amplitude" | Lemma 1 (prova matemática, §6.1) | **Demonstrado** (analítico) | OK |
| A3 | "exact assembly is Pareto-efficient on all instances if and only if amplitudes are constant within each objective group" | Theorem 1 (§6.3, prova matemática) | **Demonstrado** (analítico) | OK |
| A4 | "Normalisation shifts greedy Pareto attainment by $\NormSigMin$--$\NormSigMax$~pp wherever detectable" | `\NormSigMin`, `\NormSigMax` macros; Table 3 contrasts | **Demonstrado** (Fogo, $\kappa=25$–$400$) | Qualificar: "on Fogo" — ver R1-M1, R3-M1 |
| A5 | "The pooled SAW–TOPSIS contrast reverses sign, from $\AggKtwentyfive$~pp at $\kappa=25$ to $\AggKthousand$~pp at $\kappa=1000$" | Macros E7; Fig. kappa sweep | **Demonstrado** (Fogo) | Qualificar: "on Fogo" — ver R1-M1 |
| A6 | "equivalent to zero at $\kappa=200$ (TOST $p=\TOSTp$)" | `\TOSTp` macro; `check_inference_table.py` ALL PASS | **Demonstrado** | OK |
| A7 | "Under vector normalisation, exact assembly goes from $+\AsmVecSAWKtwentyfiveMag$~pp (SAW) at $\kappa=25$ to $-\AsmVecSAWKthousandMag$~pp at $\kappa=1000$" | Macros E7; Table 3 | **Demonstrado** (Fogo) | Qualificar: "on Fogo" — ver R1-M1 |
| A8 | "between-group distortion never moves the portfolio off the frontier but costs $\RegretEoneB$~pp of value regret" | Table E1; `\RegretEoneB` macro; E1 pre-spec | **Demonstrado** (Fogo + Theorem 1) | OK — "never" coberto por Theorem 1 |
| A9 | "within-group distortion reduces frontier attainment by $\EoneWloss$~pp" | Table E1; `\EoneWloss` macro | **Demonstrado** (Fogo, E1) | OK |
| A10 | "a criterion encoded inconsistently…reduces attainment from $100\%$ to $\RaspOptimal\%$" | Table coding 2×2; `\RaspOptimal` macro | **Exploratório** (post hoc) | Adicionar "(exploratory)" no abstract |

### Highlights

| ID | Afirmação | Evidência | Força | Acção |
|----|-----------|-----------|-------|-------|
| H1 | "Normalisation re-weights criteria: effective weight is proportional to $w_jA_j$" | Lemma 1 (analítico) | **Demonstrado** | OK |
| H2 | "Exact assembly stays Pareto-efficient iff amplitudes are group-constant" | Theorem 1 (analítico) | **Demonstrado** | OK |
| H3 | "Normalisation shifts greedy Pareto attainment by $\NormSigMin$--$\NormSigMax$~pp wherever detectable" | Macros E7 + Table 3 | **Demonstrado** (Fogo) | Qualificar: "on Fogo" — ver R2-M3 |
| H4 | "SAW–TOPSIS contrast reverses sign as weight dispersion falls: $\AggKtwentyfive$ to $\AggKthousand$~pp" | Macros E7 | **Demonstrado** (Fogo) | Qualificar: "on Fogo" — ver R1-M1 |
| H5 | "Criterion coded differently in score and objectives alone costs $\RaspLoss$~pp" | Table coding 2×2; `\RaspLoss` macro | **Exploratório** (post hoc) | Adicionar "(exploratory)" |

### Conclusão (§10)

| ID | Afirmação | Evidência | Força | Acção |
|----|-----------|-----------|-------|-------|
| C1 | "min–max is the unique weight-preserving choice among the three standard families" | Lemma 1 + §6.2 (analítico) | **Demonstrado** | OK |
| C2 | "exact assembly is Pareto-efficient for every instance if and only if amplitudes are constant within each objective group" | Theorem 1 (analítico) | **Demonstrado** | OK |
| C3 | "between-group distortion alone never moved the portfolio off the frontier but cost $\RegretEoneB$~pp" | Table E1; E1 pre-spec | **Demonstrado** (Fogo + Theorem 1) | OK |
| C4 | "within-group distortion alone cost $\EoneWloss$~pp of frontier attainment" | Table E1 | **Demonstrado** (Fogo) | OK |
| C5 | "The prediction that the two components would not interact (P2) was not confirmed" | E1 bootstrap CI; `\EonePtwoDiff` macro | **Demonstrado** (ponto estimado > 5 pp; CI inclui valores abaixo) | OK — texto já qualifica |
| C6 | "normalisation shifted greedy attainment by $\NormSigMin$--$\NormSigMax$~pp wherever the effect was distinguishable from zero, never significantly in favour of vector normalisation" | Table 3; macros E7 | **Demonstrado** (Fogo, $\kappa=25$–$400$) | Qualificar: "on Fogo" |
| C7 | "The preferred aggregation operator reversed: SAW led by $\AggKtwentyfive$~pp at $\kappa=25$…equivalent to zero at $\kappa=200$…reached $\AggKthousand$~pp at $\kappa=1000$" | Macros E7; Fig. kappa | **Demonstrado** (Fogo) | Qualificar: "on Fogo" |
| C8 | "Under vector normalisation, exact assembly gained $+\AsmVecSAWKtwentyfiveMag$~pp (SAW) at $\kappa=25$…lost $\AsmVecSAWKthousandMag$~pp at $\kappa=1000$" | Macros E7 | **Demonstrado** (Fogo) | Qualificar: "on Fogo" |
| C9 | "$\EsixPtwoMonoAll$ of $\EsixPtwoLossyNAll$ informative instances followed the predicted ordering in $\mathrm{TV}_W$" | E6 results; macros E6 | **Demonstrado** (E6 synthetic) | OK |
| C10 | "directional prediction P4 was not supported" | E6 results; `\EsixPfourP{All}` macro | **Demonstrado** | OK |
| C11 | "a criterion encoded differently…reduced $Q_2$ from $100\%$ to $\RaspOptimal\%$ under optimal assembly" | Table coding 2×2 | **Exploratório** (post hoc) | Já marcado no corpo §7.8; OK |
| C12 | "normalisation…shifts attainment in the same direction wherever its effect is detectable ($\kappa\le400$)" | Table 3 + E7 | **Demonstrado** (Fogo) | Qualificar: "on Fogo" |
| C13 | "the aggregation operator…matters in a direction that depends on the uncertainty of the weights" | E7 kappa sweep | **Demonstrado** (Fogo) | Qualificar: "on Fogo" |

### Síntese 10-3

```
AFIRMAÇÕES SEM EVIDÊNCIA SUFICIENTE : 0
AFIRMAÇÕES QUE GENERALIZAM SEM RESSALVA: 10
  A4, A5, A7, H3, H4, C6, C7, C8, C12, C13
  → Todas têm evidência em Fogo; falta qualificação "on Fogo"
  → Santiago replica normalização (A4/H3) mas NÃO replica assembly reversal (A5/H4/C7)
  → Acção: Blocos 3/4 (já planeados em session-state.md)
AFIRMAÇÕES POST HOC SEM RÓTULO NO ABSTRACT/HIGHLIGHTS: 2
  A10, H5 — coding inconsistency
  → Acção: Bloco 4 (abstract + highlights)
AFIRMAÇÕES ANALÍTICAS CORRECTAS: 7  (A1–A3, H1–H2, C1–C2)
AFIRMAÇÕES EMPIRICAMENTE CORRECTAS E BEM QUALIFICADAS: 9  (A6, A8–A9, C3–C5, C9–C11)
```

---

## Varredura de Linguagem Universal — Ronda 10-4

> Varredura de `always`, `never`, `in general`, `the method`, `any instance`, `all instances`,
> `universally`, `in every case`, `regardless`, `for any`, `invariably` em main.tex + santiago.tex.

### Ocorrências problemáticas (sem ressalva "on Fogo" ou "instance-dependent")

| # | Secção | Texto (resumido) | Problema | Acção | Já mapeado |
|---|--------|-----------------|----------|-------|------------|
| 1 | §9 Prática 2 | "under vector normalisation exact assembly loses X pp (SAW) and X pp (TOPSIS) at κ=200, a loss that grows as the weight draws concentrate" | Assembly reversal NÃO replica em S-T (S2 NOT CONFIRMED) | Adicionar "on Fogo" | R1-M1 / R3-M1 (Bloco 3) |
| 2 | §10 conclusão | "never significantly in favour of vector normalisation" | "never" sem qualificação de instância | "on Fogo, never significantly…" | C6 (Bloco 4) |
| 3 | §10 conclusão | "shifts attainment in the same direction wherever its effect is detectable (κ≤400)" | Sem qualificação "on Fogo" | "on Fogo, shifts attainment…" | C12 (Bloco 4) |
| 4 | §10 conclusão | "matters in a direction that depends on the uncertainty of the weights" | Sem qualificação "on Fogo" | "on Fogo, matters in a direction…" | C13 (Bloco 4) |

### Ocorrências correctas (analíticas ou já qualificadas): 29

Todas as ocorrências de `always`/`never`/`for any`/`all instances` em contexto analítico
(Lemma 1, Theorem 1, Prop. 1, Corollary 1) são correctas — o escopo é declarado
("In any additive aggregation", "for every set of sites", etc.).
Ocorrências empíricas já qualificadas: "On Fogo", "on this instance",
"The analytic results hold for any instance; the magnitudes do not" (§9 limitações).

### Conclusão 10-4

```
OCORRÊNCIAS PROBLEMÁTICAS: 4  (todas já mapeadas nos Blocos 3/4)
OCORRÊNCIAS NOVAS (não mapeadas anteriormente): 0
ACÇÃO NECESSÁRIA: nenhuma nova — Blocos 3/4 cobrem todas as correcções
```
