"""
patch_main.py — applies 4 surgical edits to main.tex:
  1. Insert tab:amplitude after the second empirical-calibration block (P3)
  2. Convert tab:criteria references to point to tab:amplitude (fused)
  3. Replace §8.3 with the new Choo/Milani text (closes the \todo)
  4. Remove §5.2 Q1 definition paragraph + §5.5 evaluator-robustness subsection
"""
import re

SRC = "main.tex"

with open(SRC, encoding="utf-8") as f:
    txt = f.read()

# =========================================================
# 0.  Verify the file looks right
# =========================================================
assert r"\ref{tab:amplitude}" in txt, "tab:amplitude ref not found"
assert r"\ref{tab:criteria}" in txt, "tab:criteria ref not found"
assert r"Relation to the normalisation and rank-reversal" in txt, "§8.3 not found"

# =========================================================
# 1.  Insert tab:amplitude right after the P3 empirical-calibration block
#     (after the sentence ending "factor 0.51× as predicted...")
#     The insertion point: the line "% ---" before \subsection{Consequences}
# =========================================================
TAB_AMPLITUDE = r"""
% ----------------------------------------------------------
\begin{table}[t]
\centering
\caption{Effective-weight amplitudes $A_j$ and ratios
  $w_j^{\mathrm{eff}}/w_j$ for the $\Nvia$ admissible Fogo Island sites.
  Min--max gives $A_j=1$ for all criteria by construction; rank
  normalisation gives $A_j\approx0.995$ for continuous criteria (the
  near-constant follows from $N/[2(N+1)]\approx0.499$ per midrank unit)
  and $A_j\approx0.499$ for the binary \textit{aspect}.
  $\mathrm{TV}=\tfrac{1}{2}\sum_j|w_j^{\mathrm{eff}}-w_j|$.}
\label{tab:amplitude}
\begin{tabular}{lcrrrrrr}
\toprule
Criterion & Group & $w_j$ & $A_j^{\text{mm}}$ & $A_j^{\text{vec}}$ &
  $A_j^{\text{rank}}$ &
  $\frac{w^{\mathrm{eff}}}{w}$ (vec) & $\frac{w^{\mathrm{eff}}}{w}$ (rank) \\
\midrule
\textit{perm}      & $G_1$ & 0.152 & 1.000 & 0.583 & 0.547 & \textbf{2.93} & 0.62 \\
\textit{slope}     & $G_1$ & 0.113 & 1.000 & 0.135 & 0.995 & 0.68 & 1.12 \\
\textit{roads}     & $G_1$ & 0.030 & 1.000 & 0.206 & 0.995 & 1.03 & 1.12 \\
\textit{rivers}    & $G_2$ & 0.091 & 1.000 & 0.265 & 0.995 & 1.33 & 1.12 \\
\textit{aspect}    & $G_2$ & 0.075 & 1.000 & 0.058 & 0.499 & 0.29 & \textbf{0.56} \\
\textit{coast}     & $G_3$ & 0.069 & 1.000 & 0.126 & 0.995 & 0.63 & 1.12 \\
\textit{protected} & $G_3$ & 0.066 & 1.000 & 0.105 & 0.995 & 0.53 & 1.12 \\
\textit{wells}     & $G_3$ & 0.055 & 1.000 & 0.081 & 0.995 & 0.41 & 1.12 \\
\textit{urban}     & $G_3$ & 0.166 & 1.000 & 0.107 & 0.989 & \textbf{0.54} & 1.11 \\
\textit{aero}      & $G_3$ & 0.102 & 1.000 & 0.086 & 0.995 & 0.43 & 1.12 \\
\textit{cult}      & $G_3$ & 0.081 & 1.000 & 0.171 & 0.981 & 0.86 & 1.11 \\
\midrule
$\mathrm{TV}$ & & & 0.000 & & & 0.324 & 0.091 \\
\bottomrule
\end{tabular}
\end{table}
% ----------------------------------------------------------
"""

# Insertion point: the comment+subsection line before Consequences
INS_MARKER = "% ----------------------------------------------------------\n\\subsection{Consequences for the factorial comparison}"
assert INS_MARKER in txt, "Insertion marker not found"
txt = txt.replace(INS_MARKER, TAB_AMPLITUDE + INS_MARKER, 1)

# =========================================================
# 2.  tab:criteria → tab:amplitude (the table is now the same thing,
#     since we are fusing; keep the group/direction info inline in §3)
# =========================================================
txt = txt.replace(r"\ref{tab:criteria}", r"\ref{tab:amplitude}")

# =========================================================
# 3.  Replace §8.3 (Relation to normalisation literature)
#     From the subsection title to the next \subsection
# =========================================================
SEC83_OLD = r"""\subsection{Relation to the normalisation and rank-reversal literature}

Set dependence of normalisation is documented, principally for TOPSIS.
\citet{GarciaCascales2012} demonstrate rank reversal under changes to
the alternative set and recommend scales that do not depend on it;
\citet{Kuo2017} identifies a failure of the closeness index;
\citet{OpricovicTzeng2004} observe that VIKOR uses a linear and TOPSIS
a vector normalisation, with consequences for unit invariance.
Empirical comparisons proceed largely by rank-agreement statistics
\citep{Jahan2015,Aytekin2021,Vafaei2018,Vafaei2022,Salabun2020Sym}.

Our contribution is to give the mechanism a closed form and to measure
its cost against an exact reference rather than against another ranking.
Three previously separate observations become corollaries of one
identity: the vector-normalisation distortion of
Proposition~\ref{prop:p3}, the tie-induced contraction in rank space
(Remark~\ref{rem:p2normalization}), and the amplitude loss from
normalising over inadmissible alternatives~\eqref{eq:refsetA}.
The account also explains a structural fact the rank-agreement literature
records without explanation: VIKOR's invariance to vector normalisation
follows immediately, since a common amplitude factor cancels
in~\eqref{eq:weff}.
\todo{Before submission: targeted search on ``effective weights'',
  ``implicit weighting'', ``normalisation weight distortion'' in MCDM to
  confirm the closed form is not already published. If it is, reposition
  the contribution as the empirical cost measurement against an exact
  frontier, which stands independently.}"""

SEC83_NEW = r"""\subsection{Relation to the normalisation literature}

That criterion weights cannot be interpreted independently of the
normalisation is established.
\citet{Choo1999} show that a weight is meaningful only relative to the
scale and range of the criterion it multiplies, and distinguish nominal
from effective weights; \citet{Milani2005} demonstrate empirically that
the choice of normalisation norm changes rankings, particularly under
TOPSIS.
Set dependence has been documented for specific methods:
\citet{GarciaCascales2012} exhibit rank reversal under changes to the
alternative set, \citet{Kuo2017} identifies a failure of the closeness
index, and \citet{OpricovicTzeng2004} trace the linear-versus-vector
contrast between VIKOR and TOPSIS.

Our contribution is not the existence of the effect but its closed form
and its cost.
Lemma~\ref{lem:amplitude} expresses the effective weight as
$w_j^{\mathrm{eff}}\propto w_j A_j$ and identifies $A_j$ for each of
the three standard normalisations, which yields three results that the
qualitative statement does not: min--max is the unique weight-preserving
choice among them; every binary criterion loses half its weight in rank
space irrespective of class balance; and VIKOR's invariance to vector
normalisation follows immediately, since a common amplitude factor
cancels in~\eqref{eq:weff}.
Three observations previously treated separately become corollaries of
one identity: Proposition~\ref{prop:p3},
Remark~\ref{rem:p2normalization}, and the amplitude loss
of~\eqref{eq:refsetA}.

The second difference is evidential.
Existing comparisons measure the consequence of a normalisation choice by
agreement between rankings
\citep{Jahan2015,Aytekin2021,Vafaei2018,Vafaei2022,Salabun2020Sym},
which establishes that outcomes differ without establishing that any of
them is worse.
We measure the consequence against an exhaustively enumerated Pareto set:
a loss of $26.8$~pp in the probability of selecting a non-dominated
portfolio is a statement about decision quality, not about disagreement.

This leads us to qualify a standing recommendation.
\citet{Milani2005} advise vector normalisation on the grounds that it is
less sensitive to the scale and range of the raw data.
Our results indicate that the advantage is bought at a price:
insensitivity to unit artefacts is obtained by letting the distributional
shape of each criterion determine its amplitude, and hence its effective
weight.
Where weights carry no normative content the trade may be acceptable.
Where they encode elicited stakeholder judgements, as AHP weights do, a
normalisation that silently multiplies one criterion by $2.93\times$ and
divides another by $0.54\times$ is difficult to defend, and min--max
on the admissible set is preferable on precisely the grounds
\citet{Choo1999} articulate."""

assert SEC83_OLD in txt, "§8.3 old text not found — check whitespace"
txt = txt.replace(SEC83_OLD, SEC83_NEW, 1)

# =========================================================
# 4a. Remove §5.2 Q1 paragraph (from "\subsection{Two robustness measures}"
#     through the Q1/Q2 align block and explanatory text, stopping just
#     before "\subsection{Normalisation reference set}")
#     Strategy: replace the whole \subsection{Two robustness measures} block
#     with a single sentence that introduces Q2
# =========================================================
Q1_BLOCK_OLD = r"""\subsection{Two robustness measures}

Both quantities below satisfy the coherence condition of
Remark~\ref{rem:coherence}:
\begin{align}
  Q_1 &= \Pr_{w}\bigl[\,M(w)\in\Fset(\wahp)\,\bigr],
    && \wsc=w,\quad \wob=\wfr=\wahp, \label{eq:Q1} \\
  Q_2 &= \Pr_{w}\bigl[\,M(w)\in\Fset(w)\,\bigr],
    && \wsc=\wob=\wfr=w. \label{eq:Q2}
\end{align}
They answer different questions.
$Q_2$ is \emph{internal consistency}: given a weight vector, does the
method recover a portfolio that is Pareto-efficient under that same weight
vector?
$Q_1$ is \emph{robustness to weight misspecification}: how often does a
perturbed method still land on the reference set of the nominal decision
maker?
$Q_2$ is the primary measure reported in this work.
$Q_1$ is reported as absolute levels with confidence intervals and is not
differenced across methods; because $Q_1$ with min-max normalisation
evaluates portfolios chosen under various normalisation methods using a
reference set built with min-max, any contrast between methods in $Q_1$
conflates normalisation effects with evaluator alignment."""

Q1_BLOCK_NEW = r"""\subsection{Performance measure}

The experiment evaluates each method--normalisation--assembly cell by
\begin{equation}
  Q_2 = \Pr_{w}\bigl[\,M(w)\in\Fset(w)\,\bigr],
    \qquad \wsc=\wob=\wfr=w. \label{eq:Q2}
\end{equation}
$Q_2$ is \emph{internal consistency}: given a weight vector, does the
method recover a portfolio that is Pareto-efficient under that same weight
vector?"""

assert Q1_BLOCK_OLD in txt, "Q1 block not found — check whitespace"
txt = txt.replace(Q1_BLOCK_OLD, Q1_BLOCK_NEW, 1)

# =========================================================
# 4b. Remove §5.5 Evaluator robustness subsection
#     From \subsection{Evaluator robustness} to the next section marker
# =========================================================
SEC55_OLD = r"""\subsection{Evaluator robustness}
\label{sec:evaluators}

Because the reference set of the $2^3$ design uses min-max partial value
functions, part of the normalisation effect may reflect alignment with the
evaluator rather than an intrinsic property.
We therefore rebuild the reference set under two alternative partial value
functions, holding $\Tset$ fixed:
\begin{itemize}
  \item $\Fset_{\mathrm{vec}}$: vector-normalised partial values
    ($|\Fset|=\Fvecsize$ portfolios);
  \item $\Fset_{\mathrm{fix}}$: partial values on \emph{a priori} fixed
    bounds, independent of the candidate sample
    ($|\Fset|=\Ffixsize$ portfolios).
\end{itemize}
The second follows the recommendation of \citet{GarciaCascales2012} that
the value scale should not depend on the alternative set.
The bounds are conventional physical and planning ranges fixed before the
analysis; we make no regulatory claim for them, since the applicable
jurisdiction is Cape Verde and the fixed-bound evaluator serves only to
break sample dependence, which requires independence from the sample, not
legal authority.
\todo{D2/slope: if any bound is to be presented as normative, convert and
  cite correctly --- a 30\% gradient is $\arctan(0.30)\approx16.7^\circ$,
  not $20^\circ$.}

In this dataset, the two alternative evaluators produce nearly identical
classifications: the reference sets $\Fset_{\mathrm{vec}}$ and
$\Fset_{\mathrm{fix}}$ share only 29 portfolios in common
($|\Fset_{\mathrm{vec}}\cap\Fset_{\mathrm{fix}}|=29$ out of a union of
$264$; Jaccard $0.11$), yet they return the same verdict on
$99.9\%$ of draws.
This is not a base-rate artefact: at the observed hit rates the
chance-agreement level is $93$--$96\%$, giving $\kappa\approx 0.98$,
and on the informative subset --- draws where at least one evaluator
reports non-dominance --- agreement is above $90\%$ against $1.1\%$
expected under independence.
The two evaluators therefore do not constitute independent evidence:
the assembled portfolio is almost always the same across draws, and both
exogenous scales classify that portfolio identically.
We report $\Fset_{\mathrm{fix}}$ as a confirmatory check rather than as
a second independent test."""

assert SEC55_OLD in txt, "§5.5 block not found — check whitespace"
txt = txt.replace(SEC55_OLD, "", 1)

# =========================================================
# 5.  Update Lemma statement to include "we state in closed form"
#     positioning per Choo1999
# =========================================================
# Find the Lemma statement opening
LEMMA_OLD = r"""\begin{lemma}[amplitude re-weighting]
\label{lem:amplitude}
Let $\mathbf{x}_j$ be the raw criterion~$j$ column for the $N$ alternatives
and let $A_j$ denote its \emph{amplitude} under a given linear
normalisation."""

LEMMA_NEW = r"""\begin{lemma}[amplitude re-weighting]
\label{lem:amplitude}
The following closed-form identity restates in explicit form a qualitative
relationship established by \citet{Choo1999}: a weight cannot be
interpreted independently of the scale and range of its criterion.
Let $\mathbf{x}_j$ be the raw criterion~$j$ column for the $N$ alternatives
and let $A_j$ denote its \emph{amplitude} under a given linear
normalisation."""

if LEMMA_OLD in txt:
    txt = txt.replace(LEMMA_OLD, LEMMA_NEW, 1)
    print("Lemma repositioned OK")
else:
    print("WARNING: Lemma marker not found — skipping lemma edit")

# =========================================================
# Write output
# =========================================================
with open(SRC, "w", encoding="utf-8") as f:
    f.write(txt)

print("All edits applied.")
print(f"Lines: {len(txt.splitlines())}")
