"""add_section_intros.py — insere parágrafos introdutórios nas secções que não os têm."""

with open('main.tex', 'r', encoding='utf-8') as f:
    text = f.read()

intros = {

r"""\section{Literature review}
\label{sec:litreview}""": r"""\section{Literature review}
\label{sec:litreview}

Two bodies of work bear directly on this paper: the portfolio-assembly literature,
which treats the selection of a cardinality-constrained set as a combinatorial
problem, and the normalisation literature, which documents the effect of
scale transformations on multi-criteria scores.
The review is selective; it focuses on results that are directly used or challenged
in the remainder.""",

r"""\section{Problem formulation}
\label{sec:problem}""": r"""\section{Problem formulation}
\label{sec:problem}

This section defines the siting problem formally and introduces the three evaluation
axes, the separation constraint, and the Pareto frontier against which all
method--normalisation--assembly combinations are subsequently measured.""",

r"""\section{Methods}
\label{sec:methods}""": r"""\section{Methods}
\label{sec:methods}

The analysis is conducted on a GIS dataset for Fogo Island, Cape Verde.
This section describes the candidate grid, the criteria, and the preprocessing
decisions that affect the downstream amplitude calculations.""",

r"""\section{Experimental design}
\label{sec:design}""": r"""\section{Experimental design}
\label{sec:design}

The experiment evaluates every combination of aggregation method, normalisation
rule, and assembly strategy on the Fogo Island dataset.
This section defines the three sources of weight-vector variation, the performance
measure, and the normalisation reference set used throughout.""",

r"""\section{Normalisation as implicit re-weighting: a closed-form analysis}
\label{sec:propositions}""": r"""\section{Normalisation as implicit re-weighting: a closed-form analysis}
\label{sec:propositions}

The central analytical result of the paper is stated and derived in this section.
It takes the form of a lemma that expresses effective weights in closed form,
followed by three propositions that characterise the specific distortions
produced by min--max, vector, and rank normalisation.""",

r"""\section{Results}
\label{sec:results}""": r"""\section{Results}
\label{sec:results}

The results are organised in three parts: the base portfolios under nominal
weights, which establish the empirical magnitude of the normalisation and
assembly effects; the confirmation of the amplitude lemma against the
factorial data; and the cost of normalisation--assembly mismatch measured
against the exact Pareto frontier.""",

r"""\section{Discussion}
\label{sec:discussion}""": r"""\section{Discussion}
\label{sec:discussion}

The preceding results identify two independent mechanisms by which normalisation
affects portfolio quality.
This section interprets their relative severity, places them within the
portfolio decision analysis literature, and connects them to the broader
normalisation debate.""",

}

n = 0
for old, new in intros.items():
    if old in text:
        text = text.replace(old, new, 1)
        n += 1
    else:
        print(f'NOT FOUND: {old[:60]}')

with open('main.tex', 'w', encoding='utf-8') as f:
    f.write(text)

print(f'Inserted {n}/{len(intros)} section introductions.')
