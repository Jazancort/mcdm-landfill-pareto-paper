# -*- coding: utf-8 -*-
"""Patch 2: remaining effect phrases (exact text confirmed from file)."""

TEX = "main.tex"

with open(TEX, "r", encoding="utf-8") as f:
    text = f.read()

SUBS = [
    # Abstract (line 89-92 — already partially replaced by dash script; now fix remainder)
    (
        "agreement with one another, establishing that methods differ, but\nnot that any is worse.",
        "agreement with one another. These statistics establish that rankings diverge, without establishing which ranking is closer to the decision maker's objectives.",
    ),
    # §1 line 143-144
    (
        "and public opposition in one area, and defeats the purpose of a\ndistributed network.",
        "and public opposition in one area, reducing the operational redundancy that motivates a distributed configuration.",
    ),
    # §1 line 183-184
    (
        "The variable that the literature compares most is the variable that\nmatters least.\n",
        "",
    ),
    # §7.5 line 1469
    (
        "The gap is the signature of Mechanism~2.",
        "The residual is attributed to the second mechanism.",
    ),
    # §8.1 line 1591-1592
    (
        "It is also invisible: nothing in a standard TOPSIS or SAW report reveals\nthat \\texttt{perm} entered at $2.88$ times its nominal weight.",
        "Standard TOPSIS and SAW implementations do not report the effective weights, so this redistribution remains undocumented: \\texttt{perm} entered at $2.88$ times its nominal weight.",
    ),
    # §8.1 line 1616-1617
    (
        "Mismatch is a specification error that removes the theoretical warrant\nfor optimising at all.",
        r"Mismatch is a specification error: the Pareto-consistency guarantee of \S\ref{prop:p1} does not apply.",
    ),
    # §8.6 line 1773-1774
    (
        "Fogo Island quantifies the mechanism; it does not estimate its typical\nsize.",
        "The Fogo Island instance quantifies the mechanism for this dataset. Estimating its typical magnitude across contexts requires additional instances.",
    ),
    # §9 line 1857-1858
    (
        "Fogo Island quantifies the mechanism; it does not estimate how large it\ntypically is.",
        "The Fogo Island instance quantifies the mechanism for this dataset. Estimating its typical magnitude across contexts requires additional instances.",
    ),
    # §9 line 1867-1868
    (
        "ranking of design choices is not the one the literature's emphasis would\nsuggest.",
        "relative importance of the design choices differs from the emphasis observed in the applied literature.",
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

with open(TEX, "w", encoding="utf-8") as f:
    f.write(text)

print(f"Applied: {applied}/{len(SUBS)}")
if not_found:
    print("NOT FOUND:")
    for s in not_found:
        print(f"  {repr(s)}")
