path = 'main.tex'
content = open(path, encoding='utf-8').read()

replacements = [
    # L1075: section title (this is the main section, keep descriptive but shorter)
    (r'\section{Normalisation as implicit re-weighting: a closed-form analysis}',
     r'\section{Closed-form analysis of implicit re-weighting}'),

    # L1371: subsection
    (r'\subsection{The amplitude exponent: extension beyond additive aggregation}',
     r'\subsection{Beyond additive aggregation}'),

    # L1488: subsection
    (r'\subsection{PROMETHEE~II with usual criterion equals rank-weighted SAW}',
     r'\subsection{PROMETHEE~II equals rank-weighted SAW}'),

    # L1631: subsection
    (r'\subsection{Magnitude is not enough: the concentration of the distortion}',
     r'\subsection{Concentration of the distortion}'),

    # L2066: subsection
    (r'\subsection{The reference set: a coding inconsistency outside the theorem}',
     r'\subsection{Coding inconsistency outside the theorem}'),

    # L2252: subsection
    (r'\subsection{Isolating within-group distortion: a follow-up intervention}',
     r'\subsection{Within-group distortion: follow-up intervention}'),

    # L2429: subsection in Discussion
    (r'\subsection{One mechanism and one caveat, ordered by implication}',
     r'\subsection{Two findings, ordered by implication}'),

    # Also shorten a few borderline ones
    (r'\subsection{Pareto consistency of optimal linear aggregation}',
     r'\subsection{Pareto consistency of optimal assembly}'),

    (r'\subsection{Which part of the distortion costs efficiency}',
     r'\subsection{Which distortion costs efficiency}'),

    (r'\subsection{The factorial design: aggregation is downstream}',
     r'\subsection{Aggregation is downstream}'),

    (r'\subsection{Exact assembly: no average effect, opposite signs}',
     r'\subsection{Exact assembly: opposite signs, no average effect}'),
]

count = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new, 1)
        words_before = len(old.split('{')[1].split('}')[0].split())
        words_after = len(new.split('{')[1].split('}')[0].split())
        print(f"OK ({words_before}w -> {words_after}w): {new[:70]}")
        count += 1
    else:
        print(f"MISS: {old[:70]}")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"\n{count} replacements applied.")
