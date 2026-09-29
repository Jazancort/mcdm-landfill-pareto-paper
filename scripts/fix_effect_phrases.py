# -*- coding: utf-8 -*-
"""Replace effect-phrase sentences with calibrated versions (PLANO_ESTILO §5)."""

TEX = "main.tex"

with open(TEX, "r", encoding="utf-8") as f:
    text = f.read()

SUBS = [
    # Abstract
    (
        "which establishes that methods differ, but not that any is worse",
        "These statistics establish that rankings diverge, without establishing which ranking is closer to the decision maker's objectives.",
    ),
    (
        "We supply an external standard.",
        "This study introduces an external reference standard.",
    ),
    # §1
    (
        "and defeats the purpose of a distributed network",
        "reducing the operational redundancy that motivates a distributed configuration",
    ),
    (
        "Practice, however, is organised around rankings.",
        "Applied practice, however, relies predominantly on ranking procedures.",
    ),
    (
        "The answer is not about the aggregation methods.",
        "The results indicate that the aggregation operator is not the decisive factor.",
    ),
    # Cut this entire inversion sentence
    (
        "The variable that the literature compares most is the variable that matters least.",
        "",
    ),
    (
        "without any of this appearing in the analyst's report",
        "This redistribution is not reported by standard MCDM implementations.",
    ),
    # §7
    (
        "maximises the score exactly with respect to $w^{\\mathrm{eff}}$ rather than $w$",
        "maximises the score exactly with respect to $w^{\\mathrm{eff}}$ rather than $w$",
    ),  # already correct form; kept as no-op guard
    (
        "solves the wrong problem exactly",
        "maximises the score exactly with respect to $w^{\\mathrm{eff}}$ rather than $w$",
    ),
    (
        "Greedy assembly, being myopic, is partly insulated from this effect, since it fails for its",
        "Greedy assembly, being myopic, is partly insulated from this effect, since it fails for its",
    ),  # already fixed by dash script; no-op
    # §7.5
    (
        "The gap is the signature of Mechanism 2.",
        "The residual is attributed to the second mechanism.",
    ),
    # §8
    (
        "Mismatch is a specification error that removes the theoretical warrant for optimising at all.",
        r"Mismatch is a specification error: the Pareto-consistency guarantee of \S\ref{prop:p1} does not apply.",
    ),
    (
        "nothing in a standard TOPSIS or SAW report reveals that",
        "Standard TOPSIS and SAW implementations do not report the effective weights, so this redistribution remains undocumented.",
    ),
    # §8.5
    (
        "in decreasing order of cost to ignore",
        "ordered by the magnitude of the effect observed",
    ),
    # §7.3
    (
        "is not an inconclusive comparison; it is what the lemma predicts",
        r"is consistent with the prediction of Eq.~\eqref{eq:weff}: both aggregations operate on a matrix whose effective weights are already fixed.",
    ),
    # §9
    (
        "Fogo Island quantifies the mechanism; it does not estimate how large it typically is.",
        "The Fogo Island instance quantifies the mechanism for this dataset. Estimating its typical magnitude across contexts requires additional instances.",
    ),
    (
        "the ranking of design choices is not the one the literature's emphasis would suggest",
        "the relative importance of the design choices differs from the emphasis observed in the applied literature",
    ),
]

applied = 0
not_found = []
for old, new in SUBS:
    if not old:
        continue
    if old in text:
        text = text.replace(old, new, 1)
        applied += 1
    else:
        not_found.append(old[:70])

with open(TEX, "w", encoding="utf-8") as f:
    f.write(text)

print(f"Applied: {applied}/{sum(1 for o,n in SUBS if o)}")
if not_found:
    print("NOT FOUND:")
    for s in not_found:
        print(f"  {s}")
