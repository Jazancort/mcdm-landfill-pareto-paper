"""convert_theorems.py
Converte Lemma/Corollary/Proposition/Proof para prosa com equações numeradas.
Mantém todos os labels e equações internas; substitui apenas os ambientes.
"""

with open('main.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# ===========================================================================
# 1. LEMMA → \subsection + prosa, proof integrada como "Derivation."
# ===========================================================================
old_lemma = r"""\begin{lemma}[Normalisation as implicit re-weighting]
\label{lem:amplitude}
The following states in closed form a qualitative relationship established
by \citet{Choo1999}: a weight cannot be interpreted independently of the
scale and range of its criterion.
Let $n_j : \mathbb{R}^N \to \mathbb{R}^N$ be a normalisation applied
column-wise to criterion $j$, and let
\begin{equation}
  A_j = \max_i n_j(x_{ij}) - \min_i n_j(x_{ij})
\end{equation}
be the \emph{amplitude} of the normalised column.
In any additive aggregation $s(i) = \sum_j w_j n_j(x_{ij})$, the
contribution of criterion $j$ to score differences between any two
alternatives is proportional to $w_j A_j$.
The effective weights are therefore
\begin{equation}
  \label{eq:weff}
  w_j^{\mathrm{eff}} = \frac{w_j A_j}{\sum_k w_k A_k},
\end{equation}
and $w^{\mathrm{eff}} = w$ for all $w$ if and only if $A_j$ is constant
across $j$.
\end{lemma}

\begin{proof}
For any two alternatives $i$ and $i'$,
$s(i) - s(i') = \sum_j w_j [n_j(x_{ij}) - n_j(x_{i'j})]$.
The maximum absolute contribution of criterion $j$ to this difference,
over all pairs $(i,i')$, is $w_j A_j$.
The share of total score variation attributable to criterion $j$ is
therefore $w_j A_j / \sum_k w_k A_k$, which is $w_j^{\mathrm{eff}}$
in~\eqref{eq:weff}.
The ``if and only if'' follows because $w^{\mathrm{eff}} = w$ iff
$w_j A_j / \sum_k w_k A_k = w_j$ for all $j$, which holds iff all
$A_j$ equal the same constant.
\end{proof}"""

new_lemma = r"""\subsubsection*{The amplitude identity}
\label{lem:amplitude}
The following states in closed form a qualitative relationship established
by \citet{Choo1999}: a weight cannot be interpreted independently of the
scale and range of its criterion.
Let $n_j : \mathbb{R}^N \to \mathbb{R}^N$ be a normalisation applied
column-wise to criterion $j$, and let
\begin{equation}
  A_j = \max_i n_j(x_{ij}) - \min_i n_j(x_{ij})
\end{equation}
be the \emph{amplitude} of the normalised column.
In any additive aggregation $s(i) = \sum_j w_j n_j(x_{ij})$, the
contribution of criterion $j$ to score differences between any two
alternatives is proportional to $w_j A_j$.
The effective weights are therefore
\begin{equation}
  \label{eq:weff}
  w_j^{\mathrm{eff}} = \frac{w_j A_j}{\sum_k w_k A_k},
\end{equation}
and $w^{\mathrm{eff}} = w$ for all $w$ if and only if $A_j$ is constant
across $j$.

\textit{Derivation.}
For any two alternatives $i$ and $i'$,
$s(i) - s(i') = \sum_j w_j [n_j(x_{ij}) - n_j(x_{i'j})]$.
The maximum absolute contribution of criterion $j$ to this difference,
over all pairs $(i,i')$, is $w_j A_j$.
The share of total score variation attributable to criterion $j$ is
therefore $w_j A_j / \sum_k w_k A_k$, which is $w_j^{\mathrm{eff}}$
in~\eqref{eq:weff}.
The ``if and only if'' follows because $w^{\mathrm{eff}} = w$ iff
$w_j A_j / \sum_k w_k A_k = w_j$ for all $j$, which holds iff all
$A_j$ equal the same constant.\hfill$\square$"""

assert old_lemma in text, "Lemma not found"
text = text.replace(old_lemma, new_lemma, 1)
print("Lemma converted")

# ===========================================================================
# 2. COROLLARY → \subsection + itens numerados bold, eq:Arank_binary adicionado
# ===========================================================================
old_corollary = r"""\begin{corollary}[the three standard normalisations]
\label{cor:three}

A natural measure of aggregate distortion is the total variation
\begin{equation}
  \label{eq:TV}
  \mathrm{TV} = \tfrac{1}{2}\sum_j |w_j^{\mathrm{eff}} - w_j|,
\end{equation}
which is invariant to multiplication of all $A_j$ by a common constant
(since that constant cancels in the renormalisation of~\eqref{eq:weff}
and leaves $w^{\mathrm{eff}}$ unchanged).
Any faithful measure of re-weighting must inherit this invariance;
$D = \sum_j w_j |A_j - 1|$ does not, and is therefore not an
appropriate summary of the distortion.

\begin{enumerate}[label=(\roman*)]
  \item \textbf{Min--max.}
    $A_j \equiv 1$ by construction; hence $w^{\mathrm{eff}} = w$.
    Min--max is the unique member of the three that preserves elicited
    weights exactly (for additive aggregations).
  \item \textbf{Vector.}
    $A_j = \rho_j = (\max_j x_j - \min_j x_j) / \lVert\mathbf{x}_j\rVert_2$,
    which depends on the shape of the marginal distribution.
    Criteria with heavy tails obtain $\rho_j$ close to unity (large
    norm dominated by outliers); criteria with most mass at the median
    obtain small $\rho_j$.
  \item \textbf{Midranks scaled by $N+1$.}
    $A_j = (r_j^{\max} - r_j^{\min})/(N+1)$, which approaches~$1$
    when ties are absent but contracts with tie mass.
    For a binary criterion with $n_0$ zeros and $n_1 = N-n_0$ ones,
    the midranks of the two groups are $(1+n_0)/2$ and $(n_0+1+N)/2$,
    giving
    \begin{equation}
      A_j = \frac{(n_0+1+N)/2 - (1+n_0)/2}{N+1} = \frac{N}{2(N+1)} \approx \frac{1}{2}.
    \end{equation}
    The result is \emph{independent of $n_1$}: every binary criterion
    loses approximately half its nominal weight in rank space, regardless
    of the balance between the two classes.
    A binary indicator contributes half the amplitude of a continuous
    criterion with no ties.
\end{enumerate}
\end{corollary}"""

new_corollary = r"""\subsection{Amplitude under the three standard normalisations}
\label{sec:three_norms}
\label{cor:three}

A natural measure of aggregate distortion is the total variation
\begin{equation}
  \label{eq:TV}
  \mathrm{TV} = \tfrac{1}{2}\sum_j |w_j^{\mathrm{eff}} - w_j|,
\end{equation}
which is invariant to multiplication of all $A_j$ by a common constant,
since that constant cancels in the renormalisation of~\eqref{eq:weff}.
Any faithful measure of re-weighting must inherit this invariance;
$D = \sum_j w_j |A_j - 1|$ does not, and is therefore not an
appropriate summary of the distortion.
The amplitude takes the following form in each of the three families.

\textbf{1) Min--max.}\;
$A_j \equiv 1$ by construction; hence $w^{\mathrm{eff}} = w$.
Min--max is the unique member of the three that preserves elicited
weights exactly under additive aggregation.

\textbf{2) Vector.}\;
$A_j = \rho_j = (\max_j x_j - \min_j x_j) / \lVert\mathbf{x}_j\rVert_2$,
which depends on the shape of the marginal distribution.
Criteria with heavy tails obtain $\rho_j$ close to unity;
criteria with most mass at the median obtain small $\rho_j$.

\textbf{3) Midranks scaled by $N+1$.}\;
$A_j = (r_j^{\max} - r_j^{\min})/(N+1)$, which approaches~$1$
when ties are absent but contracts with tie mass.
For a binary criterion with $n_0$ zeros and $n_1 = N-n_0$ ones,
the midranks of the two groups are $(1+n_0)/2$ and $(n_0+1+N)/2$,
giving
\begin{equation}
  \label{eq:Arank_binary}
  A_j = \frac{N}{2(N+1)} \approx \frac{1}{2}.
\end{equation}
The result is \emph{independent of $n_1$}: every binary criterion
loses approximately half its nominal weight in rank space, whatever the
class balance.
A binary indicator contributes half the amplitude of a continuous
criterion with no ties.\hfill$\square$"""

assert old_corollary in text, "Corollary not found"
text = text.replace(old_corollary, new_corollary, 1)
print("Corollary converted")

# ===========================================================================
# 3. PROPOSITION 1 + PROOF → subsection + proof integrada
# ===========================================================================
old_p1 = r"""\begin{proposition}[Pareto consistency of optimal linear aggregation]
\label{prop:p1}
Let $v_j(a)$ be the normalised criterion values entering the objectives
\eqref{eq:F1}--\eqref{eq:F3}, and let $s(a) = \sum_j w_j v_j(a)$ be
the SAW score with the same weights and normalisation.
Then the optimal set
$T^* = \argmax_{T \in \Tset} \sum_{a \in T} s(a)$
satisfies $T^* \in \Fset$, i.e., $Q_2 = 1$ almost surely.
\end{proposition}

\begin{proof}
Suppose $T^*$ is dominated by $T' \in \Tset$.
Then $F_\ell(T') \succeq F_\ell(T^*)$ for all $\ell$ and strictly for
some $\ell$.
Since each $F_\ell$ is a positive linear combination of the same
per-site scores summed over the portfolio, strict improvement in
$F_\ell$ implies $\sum_{a \in T'} s(a) > \sum_{a \in T^*} s(a)$,
contradicting the optimality of $T^*$.
\end{proof}"""

new_p1 = r"""\subsection{Pareto consistency of optimal linear aggregation}
\label{prop:p1}
Let $v_j(a)$ be the normalised criterion values entering the objectives
\eqref{eq:F1}--\eqref{eq:F3}, and let $s(a) = \sum_j w_j v_j(a)$ be
the SAW score with the same weights and normalisation.
Then the optimal set
$T^* = \argmax_{T \in \Tset} \sum_{a \in T} s(a)$
satisfies $T^* \in \Fset$, i.e., $Q_2 = 1$ almost surely.

\textit{Derivation.}
Suppose $T^*$ is dominated by $T' \in \Tset$.
Then $F_\ell(T') \succeq F_\ell(T^*)$ for all $\ell$ and strictly for
some $\ell$.
Since each $F_\ell$ is a positive linear combination of the same
per-site scores summed over the portfolio, strict improvement in
$F_\ell$ implies $\sum_{a \in T'} s(a) > \sum_{a \in T^*} s(a)$,
contradicting the optimality of $T^*$.\hfill$\square$"""

assert old_p1 in text, "Proposition 1 not found"
text = text.replace(old_p1, new_p1, 1)
print("Proposition 1 converted")

# ===========================================================================
# 4. PROPOSITION 2 + PROOF → subsection
# ===========================================================================
old_p2 = r"""\begin{proposition}[PROMETHEE~II with usual criterion equals rank-weighted SAW]
\label{prop:p2}
Let $P_j(d) = \mathbf{1}[d > 0]$.
Denoting by $r_j(a)$ the midrank of site $a$ on criterion $j$, the
PROMETHEE~II net flow satisfies
\begin{equation}
  \label{eq:p2identity}
  \phi(a) = \frac{n+1}{n-1} - \frac{2}{n-1}\sum_{j=1}^m w_j\, r_j(a),
\end{equation}
for any tied-value pattern.
The ranking induced by $\phi$ is therefore identical to that of
$\tilde{s}(a) = \sum_j w_j r_j(a)$.
\end{proposition}

\begin{proof}
For site $a$ and criterion $j$, let $B_j(a)$ count strictly worse sites
and $T_j(a)$ be the tied-block size.
The midrank satisfies $2r_j(a) = 2B_j(a) + T_j(a) + 1$.
The net PROMETHEE flow on criterion $j$ is
$\phi_j(a) = [B_j(a) - (n - B_j(a) - T_j(a))]/(n-1)
            = [2r_j(a) - 1 - n]/(n-1)$.
Summing with weights and simplifying gives~\eqref{eq:p2identity}.
\end{proof}"""

new_p2 = r"""\subsection{PROMETHEE~II with usual criterion equals rank-weighted SAW}
\label{prop:p2}
Let $P_j(d) = \mathbf{1}[d > 0]$.
Denoting by $r_j(a)$ the midrank of site $a$ on criterion $j$, the
PROMETHEE~II net flow satisfies
\begin{equation}
  \label{eq:p2identity}
  \phi(a) = \frac{n+1}{n-1} - \frac{2}{n-1}\sum_{j=1}^m w_j\, r_j(a),
\end{equation}
for any tied-value pattern.
The ranking induced by $\phi$ is therefore identical to that of
$\tilde{s}(a) = \sum_j w_j r_j(a)$.

\textit{Derivation.}
For site $a$ and criterion $j$, let $B_j(a)$ count strictly worse sites
and $T_j(a)$ be the tied-block size.
The midrank satisfies $2r_j(a) = 2B_j(a) + T_j(a) + 1$.
The net PROMETHEE flow on criterion $j$ is
$\phi_j(a) = [B_j(a) - (n - B_j(a) - T_j(a))]/(n-1)
            = [2r_j(a) - 1 - n]/(n-1)$.
Summing with weights and simplifying gives~\eqref{eq:p2identity}.\hfill$\square$"""

assert old_p2 in text, "Proposition 2 not found"
text = text.replace(old_p2, new_p2, 1)
print("Proposition 2 converted")

# ===========================================================================
# 5. PROPOSITION 3 + PROOF → subsection
# ===========================================================================
old_p3 = r"""\begin{proposition}[Vector normalisation distorts effective weights]
\label{prop:p3}
Under vector normalisation, $v_j(a) = x_j(a) / \lVert\mathbf{x}_j\rVert_2$.
The amplitude is $A_j = \rho_j$ as defined in
Lemma~\ref{lem:amplitude}, and by~\eqref{eq:weff}
\begin{equation}
  \label{eq:weff_vec}
  w_j^{\mathrm{eff}} = \frac{w_j\,\rho_j}{\sum_k w_k\,\rho_k},
  \qquad
  \rho_j = \frac{\max_a x_j(a) - \min_a x_j(a)}
                {\lVert\mathbf{x}_j\rVert_2}.
\end{equation}
For binary criteria, $\rho_j = 1/\sqrt{n_1}$ exactly, where $n_1$ is
the number of ones.
\end{proposition}

\begin{proof}
The range of $v_j(a)$ over all sites is
$(\max_a x_j(a) - \min_a x_j(a)) / \lVert\mathbf{x}_j\rVert_2 = \rho_j$,
so $A_j = \rho_j$ and~\eqref{eq:weff_vec} follows from~\eqref{eq:weff}.
For binary $x_j \in \{0,1\}$ with $n_1$ ones,
$\lVert\mathbf{x}_j\rVert_2 = \sqrt{n_1}$ and
$\max - \min = 1$, giving $\rho_j = 1/\sqrt{n_1}$.
\end{proof}"""

new_p3 = r"""\subsection{Vector normalisation distorts effective weights}
\label{prop:p3}
Under vector normalisation, $v_j(a) = x_j(a) / \lVert\mathbf{x}_j\rVert_2$.
The amplitude is $A_j = \rho_j$ as defined in
Section~\ref{sec:amp_identity}, and by~\eqref{eq:weff}
\begin{equation}
  \label{eq:weff_vec}
  w_j^{\mathrm{eff}} = \frac{w_j\,\rho_j}{\sum_k w_k\,\rho_k},
  \qquad
  \rho_j = \frac{\max_a x_j(a) - \min_a x_j(a)}
                {\lVert\mathbf{x}_j\rVert_2}.
\end{equation}
For binary criteria, $\rho_j = 1/\sqrt{n_1}$ exactly, where $n_1$ is
the number of ones.

\textit{Derivation.}
The range of $v_j(a)$ over all sites is
$(\max_a x_j(a) - \min_a x_j(a)) / \lVert\mathbf{x}_j\rVert_2 = \rho_j$,
so $A_j = \rho_j$ and~\eqref{eq:weff_vec} follows from~\eqref{eq:weff}.
For binary $x_j \in \{0,1\}$ with $n_1$ ones,
$\lVert\mathbf{x}_j\rVert_2 = \sqrt{n_1}$ and
$\max - \min = 1$, giving $\rho_j = 1/\sqrt{n_1}$.\hfill$\square$"""

assert old_p3 in text, "Proposition 3 not found"
text = text.replace(old_p3, new_p3, 1)
print("Proposition 3 converted")

# ===========================================================================
# 6. Adicionar \label{sec:amp_identity} no subsection do Lemma
# ===========================================================================
text = text.replace(
    r"""\subsubsection*{The amplitude identity}
\label{lem:amplitude}""",
    r"""\subsubsection*{The amplitude identity}
\label{sec:amp_identity}
\label{lem:amplitude}""",
    1
)
print("Added sec:amp_identity label")

# ===========================================================================
# 7. REFERÊNCIAS CRUZADAS — substituições globais
# ===========================================================================
import re

# Lemma~\ref{lem:amplitude} → the amplitude identity~\eqref{eq:weff}
replacements = [
    # narrativo com "Lemma~\ref{lem:amplitude}"
    (r'Lemma~\\ref\{lem:amplitude\}',
     r'the amplitude identity~\\eqref{eq:weff}'),
    # Corollary~\ref{cor:three}(i) / (ii) / (iii) → \eqref{eq:Arank_binary} or text
    (r'Corollary~\\ref\{cor:three\}\(iii\)',
     r'\\eqref{eq:Arank_binary}'),
    (r'Corollary~\\ref\{cor:three\}\(ii\)',
     r'Section~\\ref{sec:three_norms}(ii)'),
    (r'Corollary~\\ref\{cor:three\}\(i\)',
     r'Section~\\ref{sec:three_norms}(i)'),
    (r'Corollary~\\ref\{cor:three\}',
     r'Section~\\ref{sec:three_norms}'),
    # Proposition~\ref{prop:p1} etc (deixar como section ref)
    (r'Proposition~\\ref\{prop:p1\}',
     r'Section~\\ref{prop:p1}'),
    (r'Proposition~\\ref\{prop:p2\}',
     r'Section~\\ref{prop:p2}'),
    (r'Proposition~\\ref\{prop:p3\}',
     r'Section~\\ref{prop:p3}'),
    (r'Propositions~\\ref\{prop:p1\}--\\ref\{prop:p3\}',
     r'Sections~\\ref{prop:p1}--\\ref{prop:p3}'),
]

n_refs = 0
for old_pat, new_repl in replacements:
    count = len(re.findall(old_pat, text))
    if count:
        text = re.sub(old_pat, new_repl, text)
        print(f"  Replaced {count}x: {old_pat[:50]}")
        n_refs += count
print(f"Total ref replacements: {n_refs}")

# ===========================================================================
# 8. Remark scope — remover \begin{remark} / \end{remark} se ainda existir
# ===========================================================================
# O remark de scope (L885) está fora de qualquer ambiente depois da nossa edição do Lemma
# Verificar se ainda há \begin{remark}
if r'\begin{remark}' in text:
    print("WARNING: \\begin{remark} still present — check manually")
else:
    print("No \\begin{remark} remaining")

# ===========================================================================
with open('main.tex', 'w', encoding='utf-8') as f:
    f.write(text)

print("\nDone. Run xelatex to verify.")
