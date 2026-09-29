# Plano de Revisão Editorial — Manuscrito MCDM Landfill

**Arquivo:** `main.tex` (Jazancort/mcdm-landfill-pareto)  
**Venue:** Omega (Elsevier, CAS-DC, coluna dupla)  
**Data:** 29 set 2026

> **Plano de reescrita estilística:** ver [`PLANO_ESTILO.md`](./PLANO_ESTILO.md) — cobre todas as violações de estilo (V1–V9), conversão dos ambientes de teorema, substituição de travessões e frases de efeito, reestruturação de seções, tabelas e figuras. Baseado no IEEE Access 2026. A seção 9 (figuras) está provisória até que `STYLE_GUIDE.md` e `study_design_extracted.html` sejam colados no documento.

---

## O que está errado e por quê

### 1. Voz e tom — o artigo não soa como você escreve

Seus dois artigos de referência têm um estilo reconhecível:

**IEEE Access 2026 (Fogo Island, NSGA-II):**
> "The urgency of addressing municipal solid waste management challenges is further emphasized by the United Nations 2030 Agenda..."
> "A pivotal modeling decision in this research is the rigorous justification of the fixed cardinality constraint of three facilities (k=3). This parameter is dictated by the unique geomorphological structure of Fogo Island..."

**Intervention Window (LLM, Springer):**
> "The central finding is that this interaction is not fixed: it begins positive, reverses sign near generation 5, and grows strongly negative by Gen 12; short-horizon factorial designs do not merely lack power to detect the late effect, they can return the inverted conclusion."
> "This limitation exposes three related gaps. First..."

**O padrão:** frases longas com subordinadas controladas, declarações causais explícitas ("This parameter is dictated by..."), voz ativa ("We demonstrate", "This implies"), transições numeradas ("First... Second... Third..."), sem linguagem de marketing, sem eufemismos.

**O que o manuscrito atual tem em vez disso:**

- Environments LaTeX expostos no texto corrido: `Remark 1`, `Corollary 0.1`, `Lemma 1` aparecem no PDF como texto formatado em negrito itálico, criando uma aparência de manual de matemática, não de artigo aplicado.
- Frases de efeito sem ancoragem: "The variable that the literature compares most is the variable that matters least" — boa em Introduction, mas repetida demais.
- Parágrafos curtos demais em seções que deviam ser contínuas (§7.2, §7.3 têm vários parágrafos de 2 linhas).

---

### 2. Remark / Corollary / Lemma expostos — o problema principal

O manuscrito usa `\begin{remark}`, `\begin{corollary}`, `\begin{lemma}` com numeração automática. No PDF ficam assim:

> **Remark 1** *(what the benchmark is, and is not)*. **F** *is a three-dimensional...*

Isso é estilo de livro de matemática pura (Rudin, Royden). Para Omega — que é OR/MS aplicado — e para o seu estilo habitual, essas proposições devem ser **integradas como parágrafos**, com negrito ou itálico apenas no nome do resultado, sem numeração automática destacada.

**Padrão correto para você:**

Em vez de:
```
\begin{remark}[what the benchmark is, and is not]
\label{rem:valuespace}
$\mathbf{F}$ is a three-dimensional partial value space...
\end{remark}
```

Use:
```
\paragraph{What the benchmark is, and is not.}
The value space $\mathbf{F}$ is three-dimensional but not a vector of
physically independent objectives: each component is an additive weighted
aggregate of normalised criteria.
```

Isso mantém a estrutura semântica sem o visual de "Remark 1".

**Regra:** substituir todos os `\begin{remark}`, `\begin{corollary}` soltos por `\paragraph{Título.}` com texto direto. Os Lemmas e Propositions que têm prova formal podem manter o ambiente, mas com formatação mais limpa (ver item 3).

---

### 3. Tabelas quebrando — diagnóstico e solução

As tabelas estão quebrando de duas formas:

**a) tab:amplitude quebrando no meio de uma coluna**

Causa: a tabela está em `\begin{table}` (coluna simples) mas tem 7 colunas — ela não cabe. Precisa de `\begin{table*}` (coluna dupla) com `\begin{tabular*}{\textwidth}{...}`.

**b) Tabelas ocupando página inteira com floats acumulados**

Causa: `[htbp]` sem `\FloatBarrier` entre seções pesadas. As 5 figuras novas + 7 tabelas estão acumulando.

**Correção imediata:**
```latex
% No preâmbulo já está:
\usepackage[section]{placeins}   % já adicionado ✓

% Verificar se tab:amplitude usa table* :
\begin{table*}[htbp]
\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcrrrrrr}
```

**c) Figura F5 com página inteira**

A F5 (binary amplitude) é pequena — coluna simples (COL1=90mm). Mas está em `figure[htbp]` depois de floats acumulados. Adicionar `\FloatBarrier` antes da seção §7 e usar `[!htbp]` nas figuras pequenas.

---

### 4. Figuras não seguem o STYLE_GUIDE

O STYLE_GUIDE do Intervention Window define:

```python
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 13,
    'axes.titlesize': 14,
    'legend.fontsize': 11,
    'lines.linewidth': 2.0,
    'lines.markersize': 6,
    'axes.spines.top': False,
    'axes.spines.right': False,
})
```

**O que as figuras atuais têm:**
- `fig_utils.py` define `font.size=8`, `axes.labelsize=9` — para Elsevier 90mm. Isso está correto para coluna simples Elsevier (6pt mínimo), mas a F5 renderiza com texto menor que o padrão do Intervention Window.
- As figuras usam `font.size=8` (correto para Elsevier) mas o STYLE_GUIDE usa `font.size=11`. O steering não cobre a especificidade Elsevier vs Springer.

**Não é erro — é diferença de venue.** Elsevier CAS-DC com 90mm de largura exige fonte 7-8pt para ser legível depois de redução a 50%. O Intervention Window (Springer, coluna mais larga) usa 11pt. As figuras atuais estão certas para Omega.

**Único ajuste necessário:** a legenda da F1 diz "Other criteria" mas o Intervention Window sempre usa direct labels quando há poucos elementos destacados. Para consistência com o seu estilo, substituir a legenda de "Other criteria" por uma nota em prosa na caption.

---

### 5. "Source study" ambíguo — clarificação editorial pendente

Em 3 locais o texto usa "source study" sem deixar claro se é Andrade (2015) ou AzancortNeto (2026). O manuscrito cita ambos em §3, mas o leitor que chega a §7.1 sem reler §3 fica sem saber qual.

**Solução (uma linha):** na primeira ocorrência em §7.1, substituir "source study" por "the GIS dataset of \citet{AzancortNeto2026}, which reproduces the AHP weights of \citet{Andrade2015}".

---

## Prioridades — O Que Fazer Agora

### Alta prioridade (antes de submeter)

| # | Item | Onde | Tempo |
|---|------|------|-------|
| 1 | Converter todos os `\begin{remark}` soltos em `\paragraph{}` | §3, §5, §6, §8 | 45 min |
| 2 | tab:amplitude: converter para `table*` com `tabular*{\textwidth}` | §6 | 15 min |
| 3 | Adicionar `\FloatBarrier` entre §6 e §7, e entre §7 e §8 | main.tex | 5 min |
| 4 | Clarificar "source study" na primeira ocorrência em §7.1 | §7 | 5 min |
| 5 | D2: instrumento legal cabo-verdiano (2 `\todo` ainda abertos) | §3, §7.5 | aberto |

### Média prioridade (melhoria de estilo)

| # | Item | Onde |
|---|------|------|
| 6 | Parágrafos de 2 linhas em §7.2 e §7.3 — fundir com o adjacente | §7 |
| 7 | Legenda da F1 "Other criteria" → nota em prosa na caption | scripts/fig_F1 |
| 8 | D1: acknowledgement Omega | `\tnotetext[1]` |

### Baixa prioridade (pós-submissão)

| # | Item |
|---|------|
| 9 | Supplementary S1 (histograma perm) e S2 (bootstrap distributions) |
| 10 | tab:amprefset fundir em tab:amplitude como coluna extra |

---

## Como Converter Remarks em Texto Corrido

Padrão para cada remark:

### ANTES (estilo manual de matemática):
```latex
\begin{remark}[what the benchmark is, and is not]
\label{rem:valuespace}
$\mathbf{F}$ is a three-dimensional partial value space, not a vector of
physically independent objectives...
\end{remark}
```

### DEPOIS (seu estilo):
```latex
\paragraph{What the benchmark is, and is not.}
\label{rem:valuespace}
The value space $\mathbf{F}$ is three-dimensional but not a vector of
physically independent objectives: each component is an additive weighted
aggregate of normalised criteria...
```

**Regras:**
- O `\label` fica no `\paragraph` — todas as `\ref{rem:...}` continuam funcionando.
- A frase de abertura fica em voz ativa ("The value space is...") em vez de itálico com negrito automático.
- As Propositions e o Lemma que têm provas formais podem manter o ambiente `\begin{proposition}` mas com `\noindent\textbf{Proposition X.}` manual se a numeração ficar estranha.

---

## Contagem de Remarks/Corollaries a Converter

```
rem:valuespace     — §3 (benchmark definition)
rem:scope          — §5 (scope of experiment)
rem:p2normalization — §6 (rank normalization)
cor:three          — §6 (three corollaries) → manter como corollary mas
                     reescrever o texto de abertura sem itálico automático
```

Lemma e Propositions: manter os ambientes (têm provas formais), mas verificar se a numeração não aparece como "Lemma 0.1" — isso é bug do template CAS-DC sem `\setcounter` correto.

---

## Verificação de Consistência Final

Antes de submeter, rodar:

```powershell
# Verificar todos os \todo restantes
Select-String -Path main.tex -Pattern "\\\\todo" | Select-Object LineNumber, Line

# Verificar se não há referências quebradas
pdflatex -interaction=nonstopmode main.tex 2>&1 | Select-String "undefined|multiply"

# Contar figuras e tabelas
$t = Get-Content main.tex -Raw
([regex]::Matches($t, '\\label\{fig:')).Count  # esperado: 6
([regex]::Matches($t, '\\label\{tab:')).Count  # esperado: 6-7
```

---

## Estado Actual do Manuscrito (29 set 2026)

| Secção | Conteúdo | Observação |
|--------|----------|------------|
| Abstract | ✅ ~215 palavras | OK |
| §1 Introduction | ✅ | OK |
| §2 Literature Review | ✅ 7 subsecções | OK |
| §3 Problem formulation | ✅ | F4 inserida ✓ |
| §4 Methods | ✅ | |
| §5 Experimental design | ✅ | |
| §6 Propositions | ✅ | F5 + F1 inseridas ✓; remarks a converter |
| §7 Results | ✅ | F3 + F2 inseridas ✓ |
| §8 Discussion | ✅ | |
| §9 Conclusion | ✅ | |
| Figuras | 5 figuras | F1-F5 geradas e inseridas ✓ |
| Tabelas | 7 tabelas | tab:amplitude quebra → converter para table* |
| `\todo` abertos | D1, D2 (×2) | bloqueantes para submissão |
| Abstract | ✅ | OK |
| Highlights | ✅ | OK |
| Keywords | ✅ | OK |

**Pendências reais antes de submeter:**

1. Converter remarks em `\paragraph{}` — visual mais limpo, mais próximo do seu estilo
2. tab:amplitude → table* — corrige o overflow visual
3. D2 — instrumento legal (ou reformular como limitação explícita)
4. D1 — acknowledgement Omega
5. "Source study" — clarificar uma vez

---

## Nota Sobre o STYLE_GUIDE vs Elsevier

O STYLE_GUIDE foi escrito para o Intervention Window (Springer, coluna ~84mm com fontes maiores). Para Omega (Elsevier CAS-DC, coluna 90mm), as figuras atuais seguem corretamente as especificações do steering `scientific-figures.md`:

```
Elsevier:
  Column widths: Single=90mm, Double=190mm
  Resolution: 300dpi
  Text size: Minimum 7pt
```

Os scripts `fig_utils.py` usam `font.size=8` — correto para 90mm. Não há conflito real com o STYLE_GUIDE do Intervention Window; são venues diferentes com requisitos diferentes. As paletas (Wong) e as regras de limpeza (sem spines, sem gradientes, sem sombras) são idênticas nos dois.
