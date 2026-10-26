# Marco A: blocos para o main.tex

Regras para o agente:

- Não alterar texto nem números destes blocos.
- Editar de baixo para cima.
- Fazer um commit por passo.
- Se um bloco não encaixar no contexto, parar e mostrar as linhas em causa.

---

## 0. Valores confirmados e macros

Valores numéricos (todos do pipeline corrigido):

| Tabela | Célula | Novo |
|--------|--------|------|
| tab:factorial | SAW mm greedy / óptima | 86.0 / 100.0 |
| tab:factorial | SAW vec greedy / óptima | 66.2 / 56.8 |
| tab:factorial | TOPSIS mm greedy / óptima | 94.4 / 96.6 |
| tab:factorial | TOPSIS vec greedy / óptima | 63.4 / 52.4 |
| tab:tvorder | (greedy / óptima) min–max | 86.0 / 100.0 |
| tab:tvorder | midranks | 86.0 / 88.2 |
| tab:tvorder | vector | 66.2 / 56.8 |
| tab:fourthcell | (SAW, greedy / óptima) 473/A | 84.6 / 100.0 |
| tab:fourthcell | 473/A′ | 19.6 / 20.0 |
| tab:fourthcell | 389/A | 58.8 / 95.0 |
| tab:fourthcell | 389/A′ | 86.0 / 100.0 |

O macros.tex gerado tem de conter exactamente estes valores:

```latex
\newcommand{\NormGreedyContrast}{25.4}   % bootstrap_contrasts C6
\newcommand{\NormMainEffect}{34.6}       % C1
\newcommand{\AggContrast}{0.6}           % C3
\newcommand{\AggLo}{-0.9}
\newcommand{\AggHi}{+2.0}
\newcommand{\TOSTp}{0.003}               % tost_25pp, delta=2.5
\newcommand{\AsmMain}{-1.1}              % C2
\newcommand{\AsmMainLo}{-2.6}
\newcommand{\AsmMainHi}{+0.5}
\newcommand{\AsmMM}{8.1}                 % C4
\newcommand{\AsmVec}{10.2}               % C5, magnitude (sign in text)
\newcommand{\EoneWloss}{35.8}            % e1_v3_results
\newcommand{\EoneVloss}{43.2}
\newcommand{\TVBvec}{0.249}              % corpus_amplitudes, perm in G1
\newcommand{\TVWvec}{0.199}
\newcommand{\slopeOpt}{137.7}            % 3 levels, optimal only
\newcommand{\MechOnePredAdmiss}{14.7}    % slopeOpt * 0.107
\newcommand{\MechOneShare}{18}           % 14.7 / 80
\newcommand{\MismatchRatioHi}{5.4}       % 80 / 14.7
\newcommand{\MismatchRatioLo}{0.34}      % 5 / 14.7
```

Os `\TVBvec` e `\TVWvec` saem com os grupos `[[0,1,2],[3,4,5,6,7],[8,9,10]]`, com asserções 0.2489 e 0.1986. Não usar os valores do E3 (0.064).

---

## 1. Resumo (substitui as linhas 96–137)

```latex
\begin{abstract}
Multi-site facility siting is a portfolio problem: several locations must
be chosen jointly, subject to a minimum separation between them.
Practice relies on multi-criteria rankings read top-down, and the
methodological literature compares such rankings by their agreement with
one another, which establishes that methods differ but not that any is
worse.
We supply an optimality benchmark that is internal to the value model but
external to the ranking.
For $\Ncand$ candidate sites on Fogo Island, Cape Verde, we enumerate all
$\Ntrios$ three-site portfolios under a $\dmin$~km separation constraint
and compute the exact Pareto frontier over siting cost, environmental
impact and social safety.
Crossing aggregation, normalisation and assembly, we find that
normalisation is worth $+\NormGreedyContrast$ percentage points of Pareto
efficiency under greedy assembly, whereas the choice between SAW and
TOPSIS is equivalent to zero ($+\AggContrast$~pp, equivalence margin
$\pm2.5$~pp).
Exact assembly has no average effect: it gains $+\AsmMM$~pp under
min--max normalisation and loses $\AsmVec$~pp under vector
normalisation, because it maximises exactly a score whose operative
weights the normalisation has already moved.
We characterise the mechanism analytically.
In additive aggregation the effective weight of a criterion is
proportional to $w_jA_j$, where $A_j$ is the amplitude of the normalised
column; when amplitudes are constant within each objective group, exact
assembly is Pareto-efficient for any weights, so distortion between
groups only relocates the choice along the frontier.
A pre-registered intervention on Fogo confirms this: between-group
distortion alone costs nothing, while within-group distortion alone
accounts for $\EoneWloss$ of the $\EoneVloss$~pp lost under vector
normalisation.
Vector normalisation multiplies one criterion's weight by $2.88\times$
in our data, every binary criterion loses half its weight in rank space,
and normalising over inadmissible alternatives costs up to $80$~pp of
Pareto efficiency.
\end{abstract}
```

---

## 2. Destaques (substituem as linhas 139–149)

```latex
\begin{highlights}
\item Effective weight scales with $w_jA_j$; min--max alone preserves
  elicited weights
\item Normalisation is worth $+\NormGreedyContrast$~pp of Pareto
  efficiency; aggregation $+\AggContrast$~pp
\item Exact assembly helps under min--max ($+\AsmMM$~pp) but hurts under
  vector ($-\AsmVec$~pp)
\item Between-group distortion costs nothing; within-group distortion
  drives the loss
\item Normalising over inadmissible sites costs up to $80$~pp of Pareto
  efficiency
\end{highlights}
```

---

## 3. Introdução

### 3a. Substitui o parágrafo das linhas 202–209

```latex
The answer is not about the aggregation methods.
Choosing between SAW and TOPSIS is worth $+\AggContrast$~pp
($95\%$ CI $[\AggLo,\,\AggHi]$), equivalent to zero within the
pre-specified margin of $\pm2.5$~pp.
Normalisation is worth $+\NormGreedyContrast$~pp under greedy assembly,
and $+\NormMainEffect$~pp across the full $2^3$ factorial, which includes
a cell fixed at $100\%$ by construction.
Exact assembly, the established upgrade over reading a ranking top-down,
has no average effect ($\AsmMain$~pp, $95\%$ CI $[\AsmMainLo,\,\AsmMainHi]$).
```

### 3b. Substitui o parágrafo da linha 233

```latex
The mechanism also explains why exact assembly has no average effect.
Exact optimisation of an additive score is guaranteed to yield a
Pareto-efficient portfolio under the weights that score encodes.
When the score encodes $w^{\mathrm{eff}}\neq w$, exact optimisation
solves the wrong problem exactly: replacing greedy with optimal assembly
gains $+\AsmMM$~pp under min--max normalisation and loses $\AsmVec$~pp
under vector normalisation, and the loss appears under both SAW and
TOPSIS.
We sharpen this into a structural result.
If the normalised amplitudes are constant within each objective group,
exact assembly remains Pareto-efficient whatever the distortion between
groups (Proposition~\ref{prop:groupconst}); only distortion within a
group can move the optimum off the frontier.
A pre-registered intervention that manipulates the two components
separately confirms the prediction on Fogo
(Section~\ref{sec:e1}).
Adding integer programming on top of a ranking
\citep{BransMareschal1992,Mavrotas2006,VetscheraDeAlmeida2012}
therefore pays only when the normalisation respects the grouping of the
objectives.
```

### 3c. Contribuições (iii) e (iv) — substituem os antigos itens

```latex
  \item A factorial decomposition showing that normalisation dominates the
    choice of aggregation operator, and that exact assembly has no
    average effect because its sign depends on the normalisation.
  \item A sufficient condition for exact assembly to remain
    Pareto-efficient under normalisation (group-constant amplitudes,
    Proposition~\ref{prop:groupconst}), a decomposition of the weight
    deviation into between-group and within-group components, and a
    pre-registered intervention showing that the second carries the loss.
```

---

## 4. Nova proposição (inserir antes da linha 1173)

Mudar também a linha 965: "three propositions" → "four propositions".

```latex
\subsection{Which part of the distortion costs efficiency}
\label{sec:groupconst}

Proposition~\ref{prop:p1:stmt} requires the score and the objectives to
share a normalisation.
The next result relaxes this to a condition on how amplitudes vary
across criteria.

\begin{proposition}[Group-constant amplitudes preserve Pareto consistency]
\label{prop:groupconst}
Let every normalised column be a strictly increasing affine function of
its oriented min--max partial value, $n_j=b_j+A_j\,\tilde c_j$ with
$A_j>0$, where $\tilde c_j=1-c_j$ for $j\in G_1\cup G_2$ and
$\tilde c_j=c_j$ for $j\in G_3$, and let the objectives
\eqref{eq:F1}--\eqref{eq:F3} be built on min--max with the same weights
$w>0$.
If $A_j=\bar A_g$ for every $j\in G_g$, $g=1,2,3$, then
$T^{*}=\argmax_{T\in\Tset}\sum_{a\in T}s(a)$ belongs to $\Fset(w)$, for
every $w$ and every feasible set $\Tset$.
\end{proposition}

\begin{proof}
Summing $s(a)=\sum_j w_j n_j(a)$ over a portfolio of fixed size $\kk$
gives
$\sum_{a\in T}s(a)=C-\bar A_1F_1(T)-\bar A_2F_2(T)+\bar A_3F_3(T)$,
where $C$ does not depend on $T$.
Maximising the score is therefore a strictly positive scalarisation of
the three objectives in their own senses, and the argument of
Proposition~\ref{prop:p1:stmt} applies unchanged.
\end{proof}

Vector normalisation has this affine form with $A_j=\rho_j$, so the
proposition applies to it whenever $\rho_j$ is constant within groups.
The condition suggests splitting the deviation
$\delta=w^{\mathrm{eff}}-w$ into two parts.
With group totals $W_g=\sum_{j\in G_g}w_j$ and
$W_g^{\mathrm{eff}}=\sum_{j\in G_g}w_j^{\mathrm{eff}}$, the
\emph{between-group} distortion is
$\mathrm{TV}_B=\tfrac12\sum_g|W_g^{\mathrm{eff}}-W_g|$, and the
\emph{within-group} distortion is
$\mathrm{TV}_W=\sum_g W_g\,\mathrm{TV}_{W,g}$ with
$\mathrm{TV}_{W,g}=\tfrac12\sum_{j\in G_g}
|w_j^{\mathrm{eff}}/W_g^{\mathrm{eff}}-w_j/W_g|$.
Under group-constant amplitudes $\mathrm{TV}_W=0$, whatever the value of
$\mathrm{TV}_B$.
The proposition therefore predicts that between-group distortion alone
relocates the optimum along the frontier without leaving it.
We do not claim the converse in general; Section~\ref{sec:e1} tests it
on Fogo.
Using the amplitudes of Table~\ref{tab:amplitude}, vector normalisation
gives $\mathrm{TV}_B=\TVBvec$ and $\mathrm{TV}_W=\TVWvec$.
```

---

## 4b. rem:scope (linhas 1010–1015)

```latex
Within that scope the prediction is borne out: under optimal assembly,
$Q_2[\mathcal{A}']$ at $\kappa=200$ is $100.0\%$, $88.2\%$ and
$56.8\%$ for min--max, ranks and vector normalisation respectively,
against predicted distortions $\mathrm{TV}=0$, $0.091$ and $0.315$,
a strictly monotone ordering (Table~\ref{tab:tvorder}).
```

---

## 4c. rem:meff_reading (cerca da linha 1476)

```latex
Neither is redundant: the Euclidean norm~\eqref{eq:l2fact} is their
ratio, and in a synthetic grid reported in the Supplementary Material it
tracks efficiency loss better than $\mathrm{TV}$ alone.
```

---

## 5.1 sec:lemmaconf (substitui tab:tvorder e todo o texto até ao fim da subsecção)

```latex
\begin{table}[!t]
\centering
\caption{Predicted distortion and observed performance under additive
  aggregation (SAW), $\kappa=200$, space~$A'$, $\ndraws$ draws.
  $\mathrm{TV}$ is computed from the amplitudes of
  Table~\ref{tab:amplitude}.}
\label{tab:tvorder}
\begin{tabular}{lcccc}
\toprule
Normalisation & $A_j$ & $\mathrm{TV}$ & greedy & optimal \\
\midrule
min--max & $\equiv 1$                        & 0.000 & 86.0\% & 100.0\% \\
midranks & $(r_j^{\max}-r_j^{\min})/(N{+}1)$ & 0.091 & 86.0\% &  88.2\% \\
vector   & $\rho_j$                          & 0.315 & 66.2\% &  56.8\% \\
\bottomrule
\end{tabular}
\end{table}

Under optimal assembly, the setting in which the amplitude identity is
the only source of loss, efficiency falls strictly with $\mathrm{TV}$.
A least-squares line through the three levels has slope
$-\slopeOpt$~pp per unit of total variation; with three levels and
\textit{vector} carrying most of the regressor variance, we report the
ordering and decline to treat the slope as a predictive coefficient.
Under greedy assembly the ordering is weak: min--max and midranks tie at
$86.0\%$, because a myopic rule commits to the same leading sites under
both.
The empirical ordering corroborates the analytic claim of
Section~\ref{sec:three_norms}; it is not its foundation.
Further families (max, Peldschus, sum) are reported in the
Supplementary Material.
```

---

## 5.2 sec:factorial (substitui as duas tabelas e o parágrafo TOST)

O rem:pooling mantém-se, mas sem a frase "pooling it inflates the vector average by~$5.9$~pp".

```latex
\begin{table}[!t]
\centering
\caption{$Q_2[A']$ for the balanced $2^3$ design ($\kappa=200$,
  $\ndraws$ draws). The SAW/min--max/optimal cell is fixed at $100\%$ by
  Proposition~\ref{prop:p1:stmt}.}
\label{tab:factorial}
\begin{tabular}{llc}
\toprule
Aggregation & Normalisation, assembly & $Q_2[A']$ \\
\midrule
\multirow{4}{*}{SAW}
 & min--max, greedy  & 86.0\% \\
 & min--max, optimal & \textbf{100.0\%} \\
 & vector, greedy    & 66.2\% \\
 & vector, optimal   & 56.8\% \\
\midrule
\multirow{4}{*}{TOPSIS}
 & min--max, greedy  & 94.4\% \\
 & min--max, optimal & 96.6\% \\
 & vector, greedy    & 63.4\% \\
 & vector, optimal   & 52.4\% \\
\bottomrule
\end{tabular}
\end{table}

\begin{table}[!t]
\centering
\caption{Contrasts in percentage points of $Q_2[A']$ ($\kappa=200$;
  $\nboot$ bootstrap replicates paired by draw).}
\label{tab:effects}
\begin{tabular}{lrc}
\toprule
Contrast & Effect & 95\% CI \\
\midrule
Normalisation, greedy only (min--max $-$ vector) & $+25.4$ & $[+21.2,\,+29.8]$ \\
Normalisation, full factorial                    & $+34.6$ & $[+30.7,\,+38.4]$ \\
Aggregation (SAW $-$ TOPSIS)                     & $+0.6$  & $[-0.9,\,+2.0]$ \\
Assembly (optimal $-$ greedy)                    & $-1.1$  & $[-2.6,\,+0.5]$ \\
\midrule
Assembly within min--max                         & $+8.1$  & $[+6.2,\,+10.1]$ \\
Assembly within vector                           & $-10.2$ & $[-13.1,\,-7.4]$ \\
\bottomrule
\end{tabular}
\end{table}

The aggregation contrast of $+\AggContrast$~pp ($95\%$ CI
$[\AggLo,\,\AggHi]$) is equivalent to zero within the pre-specified
margin $\delta=2.5$~pp (TOST, $p=\TOSTp$).
Both aggregations operate on a decision matrix whose effective weights
the normalisation has already fixed, so replacing one operator with the
other cannot recover the distortion.
We report the greedy-only contrast as the headline normalisation effect
because the full-factorial contrast includes the SAW/min--max/optimal
cell, which attains $100\%$ by construction.
```

---

## 5.3 sec:interaction (substitui a subsecção inteira, linhas 1846–1903, incluindo figura F2)

```latex
\subsection{Exact assembly: no average effect, opposite signs}
\label{sec:interaction}

Averaged over the factorial, replacing greedy with optimal assembly is
worth $\AsmMain$~pp ($95\%$ CI $[\AsmMainLo,\,\AsmMainHi]$).
The average conceals two regimes of opposite sign
(Table~\ref{tab:assembly}).

\begin{table}[!t]
\centering
\caption{Optimal minus greedy assembly, $Q_2[A']$ in percentage points,
  paired by draw ($\kappa=200$, $\ndraws$ draws).}
\label{tab:assembly}
\begin{tabular}{llrc}
\toprule
Aggregation & Normalisation & Difference & 95\% CI \\
\midrule
SAW    & min--max & $+14.0$ & $[+11.0,\,+17.2]$ \\
SAW    & vector   & $-9.4$  & $[-12.4,\,-6.4]$ \\
TOPSIS & min--max & $+2.2$  & $[+0.2,\,+4.2]$ \\
TOPSIS & vector   & $-11.0$ & $[-14.4,\,-7.8]$ \\
\bottomrule
\end{tabular}
\end{table}

Under min--max, exact assembly helps; under vector normalisation it is
significantly worse than reading the ranking top-down, for both
aggregations.
Optimal assembly maximises $\sum_{i\in t}s(i)$ exactly and, by
Proposition~\ref{prop:p1:stmt}, attains the frontier \emph{under the
weights the score encodes}.
When the score encodes $w^{\mathrm{eff}}\neq w$, it pursues the
trade-offs of $w^{\mathrm{eff}}$ exactly, which under vector
normalisation inflate \textit{perm} by $2.88\times$.
Greedy assembly is myopic and, on this evidence, less exposed to the
distortion it does not optimise.
The last sentence is an interpretation; Section~\ref{sec:e1} isolates
the part of the distortion responsible.
```

---

## 5.4 sec:e1 (inserir antes da antiga linha 2028)

```latex
\subsection{Isolating within-group distortion: a pre-registered intervention}
\label{sec:e1}

Proposition~\ref{prop:groupconst} predicts that between-group distortion
alone leaves exact assembly on the frontier.
We test this by intervening on the amplitudes directly.
Four score matrices differ only in $A_j$; objectives, frontier, draws and
feasible set are identical to the factorial ($\kappa=200$, $\ndraws$
draws, space $A'$).
\textbf{M} sets $A_j\equiv1$.
\textbf{B} sets $A_j=\bar A_g$, the weighted mean of $\rho_j$ within
the group of $j$, which reproduces the between-group distortion of
vector normalisation with none within groups.
\textbf{W} sets $A_j\propto\rho_j/\bar A_g$, which equalises group
totals while leaving within-group shares exactly as under vector
normalisation.
\textbf{V} sets $A_j=\rho_j$.
The four cells form a $2\times2$ design in the presence of each
component (Table~\ref{tab:e1}).
Three predictions were committed to the repository before any run
(Supplementary Material): (P1)~cell~B attains $Q_2=100\%$ under optimal
assembly; (P2)~cells~W and~V differ by less than $5$~pp under optimal
assembly; (P3)~cell~B under greedy assembly performs close to min--max.

\begin{table}[!t]
\centering
\caption{Intervention on amplitudes, SAW, $\kappa=200$, $\ndraws$ draws,
  space $A'$. $\mathrm{TV}_B$ and $\mathrm{TV}_W$ as in
  Section~\ref{sec:groupconst}. Loss is relative to cell~M under optimal
  assembly.}
\label{tab:e1}
\begin{tabular}{lccccc}
\toprule
Cell & $\mathrm{TV}_B$ & $\mathrm{TV}_W$ & greedy & optimal & loss \\
\midrule
M (min--max)     & 0       & 0       & 86.0\%  & 100.0\% & --- \\
B (between only) & \TVBvec & 0       & 100.0\% & 100.0\% & 0.0 \\
W (within only)  & 0       & \TVWvec & 64.0\%  & 64.2\%  & 35.8 \\
V (vector)       & \TVBvec & \TVWvec & 66.2\%  & 56.8\%  & 43.2 \\
\bottomrule
\end{tabular}
\end{table}

P1 is confirmed: cell~B reaches the frontier on every draw.
Within-group distortion alone costs $\EoneWloss$~pp; the full vector
distortion costs $\EoneVloss$~pp.
P2 is falsified at the pre-specified margin: W exceeds V by
$+7.4$~pp ($95\%$ paired bootstrap CI $[+3.8,\,+11.0]$).
Between-group distortion, harmless on its own, therefore amplifies the
within-group component.
A plausible reading, which we have not tested, is that within-group
distortion matters in proportion to the weight its group carries in
the score, and that vector normalisation raises the weight of $G_1$,
the group of \textit{perm}, from $0.295$ to $0.544$.
P3 is also falsified: cell~B under greedy assembly reaches $100\%$.
A post hoc diagnosis attributes this to the amplitudes of cell~B, which
give $F_1$ roughly $2.5$ times the weight of the other groups; the score
becomes nearly lexicographic in siting cost, greedy and optimal choices
coincide in $62.8\%$ of draws, and the median greedy portfolio lies at
the $0.8$th percentile of $F_1$.
The proposition says nothing about greedy assembly, and we do not treat
this result as evidence for it.
```

**Nota:** tabela com seis colunas `{lccccc}`.

---

## 5.5 sec:refset (linhas 1904–1992) — substituições pontuais

### Frase do Mecanismo 1

```latex
The observed cost (Table~\ref{tab:fourthcell}: $100\%\to20\%$,
a loss of $80$~pp under optimal assembly) far exceeds what
Mechanism~1 predicts: $\mathrm{TV}=0.107$ implies
$\approx\MechOnePredAdmiss$~pp under optimal assembly, about
$\MechOneShare\%$ of the observed loss.
The gap is the signature of Mechanism~2.
```

### Frase do assembly vector

```latex
Under vector normalisation, exact assembly optimises a score that is
misaligned with the evaluator, which is why it loses $\AsmVec$~pp to
greedy assembly (Section~\ref{sec:interaction}).
```

### Corpo da tab:fourthcell

```latex
$\Ncand$ & $A$  & 84.6\% & \textbf{100.0\%} \\
$\Ncand$ & $A'$ & 19.6\% &  20.0\% \\
$\Nvia$  & $A$  & 58.8\% &  95.0\% \\
$\Nvia$  & $A'$ & 86.0\% & \textbf{100.0\%} \\
```

---

## 5.6 sec:greedy (linha 2000)

"reaching only $64.6\%$." → "reaching $86.0\%$."

---

## 6. Discussão

### 6a. §8.1 primeiro mecanismo

Substituir desde "Within Fogo the ordering is monotone…" até "…of which TV is one of two factors.":

```latex
Within Fogo the ordering is monotone in $\mathrm{TV}$ under optimal
assembly (Table~\ref{tab:tvorder}), but Section~\ref{sec:e1} shows that
$\mathrm{TV}$ conflates two components with different consequences:
between-group distortion alone costs nothing, and within-group
distortion carries the loss.
```

### 6b. §8.1 segundo mecanismo

"the near-absence of any gain from exact assembly under vector normalisation ($+2.2$~pp, interval containing zero)" →

```latex
the loss from exact assembly under vector normalisation
($-\AsmVec$~pp relative to greedy)
```

### 6c. Practice, segundo ponto

Substituir a frase "+29.8 … +2.2":

```latex
Integer programming on a mismatched score optimises the mismatch:
exact assembly gains $+\AsmMM$~pp under min--max and loses $\AsmVec$~pp
to greedy assembly under vector normalisation.
```

### 6d. Practice, terceiro ponto

"a distinction that Section~\ref{sec:external} shows governs the loss." →

```latex
and Section~\ref{sec:e1} shows that only the within-group part of the
deviation costs efficiency under exact assembly; we therefore also
recommend reporting $\mathrm{TV}_B$ and $\mathrm{TV}_W$.
```

### 6e. Limitações — dois parágrafos

```latex
\emph{Empirical support for the ordering.}
Under optimal assembly the three normalisation levels are ordered by
$\mathrm{TV}$ on Fogo (Table~\ref{tab:tvorder}), but three levels with
\textit{vector} carrying most of the regressor variance do not identify
a predictive coefficient.
The interval $\mathrm{TV}\in(0.10,\,0.30)$ contains no standard
normalisation: Weitendorf's linear transformation is algebraically
identical to min--max (for a cost criterion,
$(x_{\max}-x)/(x_{\max}-x_{\min})=1-(x-x_{\min})/(x_{\max}-x_{\min})$),
hence $\mathrm{TV}=0$.
Populating the interval requires manipulating the amplitude directly,
for instance along the path $A_j(t)=\rho_j^{\,t}$, $t\in[0,1]$, which
interpolates between min--max ($t=0$) and vector normalisation ($t=1$).
Further normalisation families and a synthetic grid varying the
marginal distributions are reported in the Supplementary Material.

\emph{Instance dependence.}
The analytic results hold for any instance; the magnitudes do not.
Fogo's deviation vector is two-sided and concentrated
($m_{\mathrm{eff}}=4.05$ on $[2,11]$), with one criterion inflated
$2.88\times$, and the joint distribution of
$(\mathrm{TV}_B,\mathrm{TV}_W)$ in applied decision matrices is unknown;
establishing it would require a corpus of published matrices.
```

---

## 7. Conclusão

### 7a. Substituir os dois parágrafos

```latex
The choice of aggregation operator, the variable the applied literature
compares most, proved the least consequential: $+\AggContrast$~pp,
equivalent to zero within the pre-specified margin.
Normalisation was worth $+\NormGreedyContrast$~pp under greedy assembly.
Exact assembly had no average effect, because its sign depends on the
normalisation: it gained $+\AsmMM$~pp under min--max and lost
$\AsmVec$~pp under vector normalisation.
The explanation is analytical: in additive aggregation the effective
weight of a criterion is proportional to $w_jA_j$, and exact assembly
remains Pareto-efficient whenever amplitudes are constant within each
objective group.
A pre-registered intervention on Fogo confirmed that between-group
distortion alone costs nothing and that within-group distortion carries
most of the loss, and falsified our prediction that the two components
would not interact.

Two consequences bear directly on practice.
Integer programming on top of a ranking pays only when the normalisation
respects the grouping of the objectives; under vector normalisation it
is worse than reading the ranking top-down.
Normalising over alternatives that cannot be selected costs up to
$80$~pp of Pareto efficiency, far more than re-weighting alone predicts,
and the loss is strongly asymmetric between the two directions of
mismatch.
```

### 7b. Substituir o parágrafo "Three limits…"

```latex
Three limits delimit these findings.
The closed form is exact for additive aggregation; TOPSIS and VIKOR
combine distances to ideal points, where amplitudes enter quadratically
or in ratio form, and extending the characterisation to those families
remains open.
Proposition~\ref{prop:groupconst} gives a sufficient condition for exact
assembly to stay on the frontier; we have not established the converse
in general, and the amplification of within-group distortion by
between-group distortion observed in Section~\ref{sec:e1} is measured on
one instance and not yet explained.
The magnitudes are specific to one candidate set: the analytical results
hold for any instance, but the size of the distortion depends on the
marginal distributions, and a criterion with $350$ tied zeros among
$\Nvia$ sites is an adversarial case; extending the measurement to
further instances remains open.
```

---

## 8. A apagar

- Linhas 2028–2218 (sec:external e tab:external): passam para supplementary.tex, não compilado no main.
- Figura F2, dentro da antiga sec:interaction.
- No cabeçalho (linhas 1–4): actualizar título e data 2026-10-01.

---

## Verificação final (grep deve devolver zero linhas no main.tex)

```
29\.9|16\.0|29\.8|64\.6|54\.2|72\.4|50\.6|82\.3|76\.5|55\.5|22\.2|\$9\.2|\$5\.8\$|\$2\.2\$|5\.9~pp|\$0\.9\$|sec:external|\\slopeThree|\\RsqThree|\\hiiVecThree|\\SxxPctVecThree|\\slopeFive|\\SAWgreedyContrast|\\LossTabTVorder|\\Peldschus|\\RsqadjLtwo|\\RsqadjTV|\\RsqDrop
```

**Excepção:** `+2.2` dentro da `tab:assembly` (TOPSIS min–max) é legítimo. Se o grep o apanhar, mostrar a linha e deixá-la ficar.
