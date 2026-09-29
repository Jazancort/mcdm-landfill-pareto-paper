# Plano de reescrita estilística — artigo MCDM

**Referência de estilo:** Azancort Neto et al. (2026), IEEE Access 14, doi 10.1109/ACCESS.2026.3697915  
**Venue alvo:** Omega (Elsevier, template CAS-DC duas colunas)  
**Pendente:** reconciliar seção 9 (Figuras) com `STYLE_GUIDE.md` e `study_design_extracted.html` (não lidos — colar aqui quando disponíveis)

---

## 1. Regras extraídas do IEEE Access 2026

### 1.1 Pontuação

| Regra | Evidência no artigo de referência |
|---|---|
| Sem travessão duplo como aposto | Zero ocorrências em 22 páginas. Usa vírgula, dois-pontos ou frase nova |
| Aposto com vírgula + "namely" | "three conflicting objectives, namely implementation cost, environmental impact, and Social Safety" |
| Dois-pontos para explicação | "a structural flaw known as the compensatory effect, where a site with..." |
| Parênteses para qualificação curta | "(e.g., Social Safety)", "(landslides, volcanic activity)" |
| Frase nova em vez de aposto longo | "This mathematical collapse of the objective space masks critical trade-offs." |

### 1.2 Estrutura de seção

Toda seção abre com prosa de enquadramento antes de qualquer subseção, lista ou equação. Exemplo, §II do artigo de referência:

> "Landfill site selection for municipal solid waste management constitutes a spatially constrained and combinatorial decision problem in which environmental protection, economic viability, and Social Safety must be optimized simultaneously. \[…4 parágrafos…\] Each stage is described in detail in the following subsections, with explicit reference to this workflow."

Toda subseção abre com âncora ao workflow:

> "This subsection corresponds to Stage 1 of the workflow depicted in Figure 1, covering the acquisition and preprocessing of all geospatial datasets used in the analysis."

**Implicação para o draft:** o artigo MCDM precisa de uma Figura 1 de workflow e de uma frase de ancoragem em cada subseção. O draft actual não tem nenhuma das duas.

### 1.3 Resultados formais

O artigo de referência nunca usa `\newtheorem`. Resultados entram como:

- Equação numerada + prosa explicativa: "The problem is subject to the fixed cardinality constraint given in Eq. (6)"
- Subseção numerada com título descritivo: "1) CARDINALITY CONSTRAINT HANDLING"
- Bloco `Algorithm N` para procedimentos
- Lista numerada com lead-in em negrito: "1) Municipal Budget Constraints: Each landfill facility incurs..."

### 1.4 Registro

**Permitido:** Notably, Crucially, Critically, Furthermore, Specifically, However, Consequently.

**Ausente:** inversões retóricas, paralelismos de efeito, frases curtas isoladas para ênfase, meta-comentário sobre o próprio argumento.

---

## 2. Inventário de violações no draft actual

| # | Violação | Ocorrências | Gravidade |
|---|---|---|---|
| V1 | Travessão duplo `---` | ~23 | Alta |
| V2 | Ambientes `lemma`/`corollary`/`proposition`/`remark` | 6 ambientes, ~40 referências | Alta |
| V3 | Frases de efeito | 13 identificadas (§6) | Alta |
| V4 | Seções abrindo sem prosa | §3, §5, §6, §7 | Média |
| V5 | Sem figura de workflow | — | Média |
| V6 | Tabela `tab:amplitude` com 8 colunas (quebra) | — | Alta |
| V7 | `figure*` ocupando página inteira (F1, F3) | — | Alta |
| V8 | `\begin{proof}` | 4 | Alta |
| V9 | Meta-comentário ("We state this explicitly to make the constraint auditable" e similares) | ~5 | Média |

---

## 3. Reorganização: estrutura actual → alvo

O modelo IEEE Access de referência tem 4 seções numeradas (Introduction, Materials and Methods, Results and Discussion, Conclusion) com subseções A–H. O draft actual tem 9 seções. Proposta de colapso:

| Alvo | Conteúdo | Vem de |
|---|---|---|
| I. Introduction | motivação, lacuna, contribuições, roadmap | §1 |
| **II. Materials and Methods** | | |
| II-A | Related work and positioning | §2 (condensado de 7 para 3 subseções) |
| II-B | Study area, data and preprocessing | §4.1 |
| II-C | Spatial criteria and AHP weights | §4.2 |
| II-D | Problem formulation as portfolio selection | §3.1–3.2 |
| II-E | Reference set and optimality gap | §3.3 |
| II-F | Normalisation and effective weights | §6.1 + §6.2 (núcleo analítico) |
| II-G | Aggregation and assembly | §4.4–4.5 |
| II-H | Experimental design and validation | §5 |
| **III. Results and Discussion** | | |
| III-A | Base portfolios under nominal weights | §7.1 |
| III-B | Effective weights across normalisations | §7.2 |
| III-C | Factorial results | §7.3 |
| III-D | Normalisation and assembly interaction | §7.4 |
| III-E | Reference-set alignment | §7.5 |
| III-F | Positioning and implications | §8 (condensado) |
| III-G | Limitations | §8.6 |
| IV. Conclusion | | §9 |

**Ganho:** o núcleo analítico (Lema de Amplitude) passa de seção separada (§6) para II-F, dentro de Methods — que é onde o artigo de referência coloca toda a formalização matemática (Eqs. 1–26).

> **Nota de venue:** Omega é Elsevier e não usa numeração romana. Manter `\section{...}` com a mesma granularidade. Se preferir a estrutura Elsevier padrão (Introduction / Related work / Methods / Results / Discussion / Conclusion), o mapeamento muda — decisão do autor.

---

## 4. Conversão dos ambientes de teorema

Remover do preâmbulo: `\newtheorem{proposition}`, `{corollary}`, `{lemma}`, `{remark}` e `amsthm`.

| Actual | Alvo | Label novo |
|---|---|---|
| `lemma:amplitude` | Subseção II-F1, "Effective weights under column normalisation". Resultado como Eq. (11). Prova vira parágrafo "Derivation." | `eq:weff` |
| `cor:three` | Subseção II-F2, "Amplitude under the three standard normalisations". Lista numerada 1)–3) com lead-in em negrito | `eq:Amm`, `eq:Avec`, `eq:Arank` |
| `prop:p1` | Subseção II-F3, "Pareto consistency of optimal additive aggregation". Eq. + derivação em prosa | `eq:paretocons` |
| `prop:p2` | Subseção II-F4, "Equivalence of PROMETHEE II and rank-weighted aggregation". Eq. (identidade) | `eq:p2identity` (mantém) |
| `prop:p3` | Absorvido em II-F2, item 2) | — |
| `rem:pooling` | Parágrafo em III-C começando "Averaging $Q_2$ across all aggregation families…" | — |
| `rem:scope` | Parágrafo em II-F1 | — |
| `rem:valuespace` | Parágrafo em II-D | — |
| `rem:coherence` | Parágrafo em II-H | — |
| `rem:p2normalization` | Parágrafo em II-F4 | — |

**Substituição de referências no texto:**
- `Lemma~\ref{lem:amplitude}` → `Eq.~\eqref{eq:weff}`
- `Corollary~\ref{cor:three}(iii)` → `Eq.~\eqref{eq:Arank}`
- `Proposition~\ref{prop:p1}` → `Eq.~\eqref{eq:paretocons}`

São ~40 substituições; fazer com `sed` e conferir cada uma.

**Formato das derivações — modelo do artigo de referência (§II-G-2):**

> "2. Optimality Gap ($\delta_m$): Measures the absolute deviation between the extreme solutions found by NSGA-II and the global optima for each isolated objective $m$: \[Eq. 16\] where $\delta_m \approx 0$ confirms convergence to the single-objective global optimum."

Aplicado ao Lema de Amplitude:

> The effective weight of criterion $j$ is obtained as follows. For any two alternatives $i$ and $i'$, the score difference is $s(i) - s(i') = \sum_j w_j [n_j(x_{ij}) - n_j(x_{i'j})]$. The maximum absolute contribution of criterion $j$ to this difference, taken over all pairs, is $w_j A_j$. The share of total score variation attributable to criterion $j$ is therefore given in Eq. (11): \[equação\] Equality $w^{\mathrm{eff}} = w$ holds for all $w$ if and only if $A_j$ is constant across criteria, since the renormalisation cancels any common factor.

---

## 5. Frases de efeito: lista completa e substituições

| Local | Actual | Substituir por |
|---|---|---|
| Abstract | "which establishes that methods differ, but not that any is worse" | "These statistics establish that rankings diverge, without establishing which ranking is closer to the decision maker's objectives." |
| Abstract | "We supply an external standard." | "This study introduces an external reference standard." |
| §1 ¶1 | "and defeats the purpose of a distributed network" | "reducing the operational redundancy that motivates a distributed configuration" |
| §1 ¶2 | "Practice, however, is organised around rankings." | "Applied practice, however, relies predominantly on ranking procedures." |
| §1 ¶4 | "The answer is not about the aggregation methods." | "The results indicate that the aggregation operator is not the decisive factor." |
| §1 ¶4 | "The variable that the literature compares most is the variable that matters least." | **Cortar.** O parágrafo já reporta os três efeitos; a inversão não acrescenta informação. |
| §1 ¶5 | "without any of this appearing in the analyst's report" | "This redistribution is not reported by standard MCDM implementations." |
| §7.4 | "solves the wrong problem exactly" | "maximises the score exactly with respect to $w^{\mathrm{eff}}$ rather than $w$" |
| §7.4 | "it fails for its own reasons, but it does not optimise the distortion" | "Greedy assembly is partly insulated from this effect, since it does not maximise the distorted score globally." |
| §7.5 | "The gap is the signature of Mechanism 2." | "The residual is attributed to the second mechanism." |
| §8.1 | "Mismatch is a specification error that removes the theoretical warrant for optimising at all." | "Mismatch is a specification error: the Pareto-consistency guarantee of Eq. (X) does not apply." |
| §8.1 | "nothing in a standard TOPSIS or SAW report reveals that" | "Standard TOPSIS and SAW implementations do not report the effective weights, so this redistribution remains undocumented." |
| §9 | "Fogo Island quantifies the mechanism; it does not estimate how large it typically is." | "The Fogo Island instance quantifies the mechanism for this dataset. Estimating its typical magnitude across contexts requires additional instances." |
| §9 | "the ranking of design choices is not the one the literature's emphasis would suggest" | "the relative importance of the design choices differs from the emphasis observed in the applied literature" |
| §8.5 | "in decreasing order of cost to ignore" | "ordered by the magnitude of the effect observed" |
| §7.3 | "is not an inconclusive comparison; it is what the lemma predicts" | "is consistent with the prediction of Eq. (11): both aggregations operate on a matrix whose effective weights are already fixed." |

---

## 6. Regra de substituição de travessões

Três padrões, três tratamentos:

**(a) Aposto explicativo → vírgula + "namely", ou dois-pontos**

```
antes:  three group-level objectives --- siting cost, environmental
        impact and social safety
depois: three group-level objectives, namely siting cost, environmental
        impact, and social safety
```

**(b) Aposto interrompendo a frase → parênteses, ou frase nova**

```
antes:  costs up to 80 pp of Pareto efficiency --- far more than the
        re-weighting alone predicts
depois: costs up to 80 pp of Pareto efficiency. This exceeds the loss
        predicted by re-weighting alone.
```

**(c) Ênfase → cortar o travessão, reordenar**

```
antes:  the established upgrade path \citep{...} --- pays only when
depois: The established upgrade path \citep{...} yields a gain only when
```

**Localizações aproximadas no `main.tex`:** abstract ×1; §1 ×9; §2 ×1; §6 ×5; §7 ×4; §8 ×2; §9 ×4.

---

## 7. Prosa de abertura a escrever

Cada uma destas seções hoje começa directamente com subseção, lista ou equação. Precisa de 1–3 parágrafos de enquadramento antes.

| Seção | Conteúdo da abertura |
|---|---|
| II (Materials and Methods) | O problema como seleção de conjunto sob restrição espacial; por que métodos compensatórios são inadequados; referência à Figura 1 de workflow; frase de fechamento "Each stage is described in detail in the following subsections" |
| II-D | Por que a formulação é de portfólio e não de ranking |
| II-F | Que a normalização determina os pesos operativos, e que isto será formalizado nas subseções seguintes |
| II-H | O que o desenho experimental precisa controlar e por quê |
| III | Síntese do que a seção reporta, com roteiro das subseções (modelo: "The remainder of this section is structured as follows: Section III-A analyzes…") |

Cada subseção precisa de âncora à Figura 1: "This subsection corresponds to Stage N of the workflow in Figure 1…"

---

## 8. Tabelas

| Tabela | Problema | Correção |
|---|---|---|
| `tab:amplitude` | 8 colunas, quebra em coluna dupla | Dividir em duas: T1 = critério, grupo, $w_j$, direcção, objectivo (referência); T2 = critério, $A^{mm}$, $A^{vec}$, $A^{rank}$, dois factores. T2 como `table*` se necessário |
| `tab:canonical` | 7 colunas | Abreviar cabeçalhos ($F_1$/$F_2$/$F_3$ sem unidade), remover coluna "Assembly" fundindo com "Method" |
| `tab:amprefset` | "remaining 5" agrupado | Listar os 5 nominalmente ou mover para Suplementar |
| Todas | Sem nota de rodapé explicativa | Adicionar notas onde houver abreviação (modelo: "Note: Score 1 denotes minimum suitability; Score 3 denotes maximum suitability.") |
| Todas | `[t]` | Usar `[!t]` e `\small` onde necessário; nunca deixar tabela sozinha em página |

**Contagem final alvo:** 5 tabelas no corpo, 2 no Suplementar.

---

## 9. Figuras — COMPLETO

> ✅ Seção fechada. Fontes lidas: `STYLE_GUIDE.md` (Intervention Window, `figures/src/`) e `study_design_extracted.html` (Intervention Window, `figures/src/`).

### 9.1 Dois tipos de figura — duas ferramentas

| Tipo | Ferramenta | Quando usar |
|---|---|---|
| **Gráfico de dados** | Python + matplotlib | Linhas, barras, scatter, box plots — dados quantitativos |
| **Diagrama de escrita** | HTML + CSS → screenshot PNG | Workflow, fluxograma, comparação qualitativa, design de estudo |

**Regra absoluta:** nunca matplotlib para diagramas de escrita; nunca HTML para gráficos de dados.

### 9.2 rcParams obrigatórios (já implementados em `fig_utils.py`)

```python
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 11,
    'axes.labelsize': 13,
    'axes.titlesize': 14,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'axes.linewidth': 1.0,
    'lines.linewidth': 2.0,
    'lines.markersize': 6,
    'axes.spines.top': False,
    'axes.spines.right': False,
})
```

> **Nota de venue:** o `fig_utils.py` actual usa `font.size=11` (Intervention Window), compatível com Elsevier CAS-DC 90mm após redução a 50% (resulta em ~5.5pt — no limite mas aceitável). O mínimo Elsevier é 6pt; se a Omega pedir revisão de tamanho de fonte, baixar para 9pt.

### 9.3 Paleta semântica (já implementada)

```python
C_BASELINE  = "#C0392B"   # red-brown — perm / vector baselines
C_TREATMENT = "#2980B9"   # blue — min-max / treatment
C_ORANGE    = "#E67E22"   # orange — vector (segunda condição)
C_GREEN     = "#009E73"   # green — ranks
C_GRAY      = "#7F8C8D"   # gray — neutral / other criteria
```

**Regra de ouro (adaptada do STYLE_GUIDE):** não usar a mesma cor para significados diferentes em figuras adjacentes. No contexto MCDM: azul = min-max, vermelho/marrom = vector, verde = ranks, cinza = outras.

### 9.4 Padrão de legenda

Sempre abaixo, horizontal, sem frame:

```python
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12),
          ncol=N, frameon=False)
plt.subplots_adjust(bottom=0.18)
```

Para 2 curvas bem separadas verticalmente: preferir **direct labels** ao final de cada linha (na cor da linha), sem `ax.legend()`.

### 9.5 Figura 1 — Workflow do estudo (a criar)

**Tipo:** diagrama de escrita → HTML + CSS.  
**Referência canónica:** `study_design_extracted.html` (Intervention Window).

Estrutura do HTML (baseada no template lido):

```
┌─────────────────────────────────────────────────────────────────┐
│  MÉTODO                                                          │
│  ┌──────────┐  →  ┌──────────┐  →  ┌──────────┐  →  ┌──────┐ │
│  │ Stage 1  │     │ Stage 2  │     │ Stage 3  │     │  …   │ │
│  │ Dataset  │     │ Criteria │     │ Portfolio│     │      │ │
│  │ & Exclu- │     │ & AHP    │     │ Formula- │     │      │ │
│  │ sion     │     │ Weights  │     │ tion     │     │      │ │
│  └──────────┘     └──────────┘     └──────────┘     └──────┘ │
└─────────────────────────────────────────────────────────────────┘
```

Tokens CSS obrigatórios do STYLE_GUIDE (diagramas de escrita):

| Elemento | Valor |
|---|---|
| Fonte | `'Source Serif 4', Georgia, serif` |
| Fundo da página | `#ffffff` |
| Card histórico/neutro | bg `#f3f5f7`, borda `#b7bec6` |
| Card primary | bg `#e7f0f9`, borda `2.5px solid #1d4e89` |
| Border-radius dos cards | `12px` |
| Número do estágio | círculo `38px`, fundo `#1d4e89` (primary) ou `#9aa3ad` (neutro) |
| Separador interno | `height: 1px; background: #d9dee3` |
| Seta sólida | `background: #2c3742`, ponta `border-left: 12px solid #2c3742` |
| Largura total | `1840px` |
| Padding | `40px 44px 34px` |

**Conteúdo dos estágios para o artigo MCDM:**

| Estágio | Título | Conteúdo (bullets) |
|---|---|---|
| 1 | Dataset & Exclusion | 473 candidate sites; 84 excluded (D2); 389 admissible (N=389) |
| 2 | Criteria & AHP Weights | 13 spatial criteria; 3 groups; AHP weights from Andrade (2015) |
| 3 | Portfolio Formulation | k=3 facilities; d_min=10 km; 1,944,653 feasible triples |
| 4 | Normalisation | Min-max / Vector / Ranks; Amplitude Lemma |
| 5 | Assembly | Greedy / Optimal (exact enumeration) |
| 6 | Pareto Reference | 181-portfolio Pareto frontier; Q2 optimality gap |

**Fluxo de geração:**
1. Criar `scripts/fig_workflow.html` seguindo o template do STYLE_GUIDE
2. Abrir no Chrome → F12 → Ctrl+Shift+P → "Capture full size screenshot"
3. Guardar como `figures/fig_workflow.png`
4. Inserir no main.tex como `figure*` (largura dupla)

### 9.6 Plano de figuras (actualizado)

| # | Conteúdo | Largura | Tipo | Status |
|---|---|---|---|---|
| 1 | Workflow do estudo, 6 estágios | Dupla | HTML/CSS | **A criar** |
| 2 | Mapa de Fogo: 389 admissíveis, trio BCS, raios 10 km | Simples | matplotlib | Existe (F4) ✓ |
| 3 | Pesos efectivos: 3 painéis (a)(b)(c) mm/vec/rank | Dupla | matplotlib | Existe (F1) ✓ |
| 4 | Interação normalização × montagem, 3 retas com IC | Simples | matplotlib | Existe (F2) ✓ |
| 5 | Projeções 2D fronteira de Pareto, painéis (a)(b)(c) | Dupla | matplotlib | Existe (F3) ✓ |
| 6 | $A_j^{rank}$ binário vs. $n_1$ | Simples | matplotlib | Existe (F5); candidata a Suplementar |

### 9.7 Correcções técnicas para evitar página cheia

```latex
% No preâmbulo (já está placeins; adicionar os dois renewcommands):
\renewcommand{\topfraction}{0.9}
\renewcommand{\floatpagefraction}{0.8}

% Em todas as \includegraphics de figure* (F1, F3):
\includegraphics[width=\textwidth]{figures/fig_F1_slope_weights}
% Nunca 0.92\textwidth sem height= explícito

% \FloatBarrier já presente via placeins[section]
% Adicionar manualmente entre §6 e §7 se persistir acumulação
```

### 9.8 Regras de caption (padrão do IEEE Access 2026)

- Caption descreve **o que a figura mostra** (elementos, cores, eixos, painéis)
- Corpo do texto diz **o que a figura significa** (interpretação)
- Painéis múltiplos: referenciar (a), (b), (c) na caption
- 40–70 palavras para figuras simples; até 100 para multi-painel
- Símbolo e abreviatura não-óbvios definidos na caption

---

## 10. Ordem de execução

| Etapa | Tarefa | Custo estimado |
|---|---|---|
| 1 | Colar `STYLE_GUIDE.md` e `study_design_extracted.html` para fechar a seção 9 | — |
| 2 | Converter ambientes de teorema (seção 4): preâmbulo, 6 ambientes, ~40 refs | 2 h |
| 3 | Eliminar travessões (seção 6): 23 ocorrências | 1 h |
| 4 | Substituir frases de efeito (seção 5): 16 trechos | 1,5 h |
| 5 | Reestruturar seções (seção 3): colapso 9 → 4 | 3 h |
| 6 | Escrever prosa de abertura (seção 7): 5 blocos | 2,5 h |
| 7 | Criar Figura 1 (workflow) | 1,5 h |
| 8 | Refazer tabelas (seção 8) | 1,5 h |
| 9 | Ajustar floats, compilar, verificar quebras | 1 h |
| 10 | Passada final: ler em voz alta procurando registro fora do padrão | 1,5 h |

**Total: ~16 h.** Etapas 2–4 são mecânicas e independentes entre si. A etapa 5 depende da decisão sobre numeração romana vs. estrutura Elsevier padrão.

---

## 11. Pendências herdadas (não estilísticas)

Continuam abertas do plano anterior e **não são resolvidas por esta reescrita:**

| # | Pendência |
|---|---|
| D1 | `\tnotetext[1]` com `\todo` vazio no título (acknowledgement Omega) |
| D2 | Base legal cabo-verdiana para os 84 sites excluídos (2 `\todo` no texto, §3 e §7.5) |
| D3 | "source study" ambíguo entre `Andrade2015` (pesos AHP) e `AzancortNeto2026` (dataset) — definir um termo fixo e usar consistentemente |
| D4 | `Yang2015SMAAPO` — verificar autores via Crossref |
