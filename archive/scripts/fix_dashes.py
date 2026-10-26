# -*- coding: utf-8 -*-
"""Replace em-dash separators (---) with correct punctuation."""

import re, sys

TEX = "main.tex"

with open(TEX, "r", encoding="utf-8") as f:
    text = f.read()

# Each tuple: (exact_old, exact_new)
# Ordered so that longer strings match first (no partial collision risk)
SUBS = [
    # Abstract / §1
    (
        "agreement with one another --- which establishes that methods differ, but",
        "agreement with one another, establishing that methods differ, but",
    ),
    (
        r"The decision is therefore a \emph{portfolio} problem --- choose $\kk$",
        r"The decision is therefore a \emph{portfolio} problem: choose $\kk$",
    ),
    (
        r"sites out of $N$ subject to a minimum pairwise separation --- rather than",
        r"sites out of $N$ subject to a minimum pairwise separation, rather than",
    ),
    (
        "exact Pareto frontier over three group-level objectives --- siting cost,",
        "exact Pareto frontier over three group-level objectives, namely siting cost,",
    ),
    (
        r"with a $95\%$ interval of $[-0.5,\,+2.3]$ --- statistically",
        r"with a $95\%$ interval of $[-0.5,\,+2.3]$ (statistically",
    ),
    (
        r"Adding integer programming on top of a ranking --- the established",
        r"Adding integer programming on top of a ranking, the established",
    ),
    (
        r"\citep{BransMareschal1992,Mavrotas2006,VetscheraDeAlmeida2012} --- pays",
        r"\citep{BransMareschal1992,Mavrotas2006,VetscheraDeAlmeida2012}, pays",
    ),
    (
        r"to $80$~pp of Pareto efficiency --- far more than the re-weighting alone",
        r"to $80$~pp of Pareto efficiency. This exceeds the loss predicted by re-weighting alone",
    ),
    (
        "Three effects previously reported separately --- vector-normalisation",
        "Three effects previously reported separately: vector-normalisation",
    ),
    (
        "from normalising over inadmissible alternatives --- become corollaries",
        "from normalising over inadmissible alternatives, become corollaries",
    ),
    # §3 list items
    (
        r"\item $\wsc$ --- the weights in the \emph{method score}, which order",
        r"\item $\wsc$: the weights in the \emph{method score}, which order",
    ),
    (
        r"\item $\wob$ --- the weights used to map the assembled portfolio to",
        r"\item $\wob$: the weights used to map the assembled portfolio to",
    ),
    (
        r"\item $\wfr$ --- the weights used to build the reference set,",
        r"\item $\wfr$: the weights used to build the reference set,",
    ),
    # §6
    (
        "selectable --- a set-dependence mechanism documented for TOPSIS by",
        "selectable, a set-dependence mechanism documented for TOPSIS by",
    ),
    (
        r"the amplitude result (see \S\ref{cor:three})(iii) --- independent of $n_1$.",
        r"the amplitude result (see \S\ref{cor:three})(iii), independent of $n_1$.",
    ),
    (
        r"Dividing midranks by $N+1$ --- the conventional rescaling to $(0,1)$",
        r"Dividing midranks by $N+1$ (the conventional rescaling to $(0,1)$)",
    ),
    (
        "construction --- all lines are horizontal at their nominal level (dashed",
        "construction; all lines are horizontal at their nominal level (dashed",
    ),
    (
        "performance, restricted to additive aggregation --- the scope in which",
        "performance, restricted to additive aggregation, which is the scope in which",
    ),
    # §7
    (
        "Greedy assembly, being myopic, is partly insulated --- it fails for its",
        "Greedy assembly, being myopic, is partly insulated from this effect, since it fails for its",
    ),
    # §8
    (
        "Where elicited weights carry normative content --- as with AHP judgements",
        "Where elicited weights carry normative content, as with AHP judgements",
    ),
    (
        "from stakeholders --- a normalisation that silently reweights them is",
        "from stakeholders, a normalisation that silently reweights them is",
    ),
    (
        "The choice of aggregation operator --- the variable the applied",
        "The choice of aggregation operator, which is the variable the applied",
    ),
    (
        "literature compares most --- proved the least consequential of the three,",
        "literature compares most, proved the least consequential of the three,",
    ),
    (
        "Second, normalising over alternatives that cannot be selected --- in our",
        "Second, normalising over alternatives that cannot be selected, in our",
    ),
    (
        r"data the $\Nexcl$ candidates overlapping protected areas --- calibrates",
        r"data the $\Nexcl$ candidates overlapping protected areas, calibrates",
    ),
    # §9
    (
        "Where the feasible set is enumerable --- as it is for",
        "Where the feasible set is enumerable, as it is for",
    ),
    (
        "cardinality-constrained siting problems of realistic size --- an exact",
        "cardinality-constrained siting problems of realistic size, an exact",
    ),
]

applied = 0
not_found = []
for old, new in SUBS:
    if old in text:
        text = text.replace(old, new, 1)
        applied += 1
    else:
        not_found.append(old[:70])

# Check for any remaining --- (excluding table cells with --- as value)
remaining = [(m.start(), text[max(0,m.start()-40):m.end()+40])
             for m in re.finditer(r' --- ', text)
             if '&' not in text[max(0,m.start()-5):m.end()+5]]

with open(TEX, "w", encoding="utf-8") as f:
    f.write(text)

print(f"Applied: {applied}/{len(SUBS)}")
if not_found:
    print("NOT FOUND:")
    for s in not_found:
        print(f"  {s}")
if remaining:
    print(f"\nRemaining --- occurrences ({len(remaining)}):")
    for pos, ctx in remaining:
        print(f"  pos {pos}: ...{ctx}...")
else:
    print("\nNo remaining em-dash separators.")
