import re

path = 'main.tex'
content = open(path, encoding='utf-8').read()
orig = content

# Strategy:
# Design. / Results. -> \subsubsection*{Design} (proper unnumbered heading)
# All others -> absorb title into first sentence of the paragraph
# (drop \paragraph{Title.} and capitalise/integrate if needed)

replacements = [
    # E6 Design/Results -> subsubsection* (proper heading, not inline italic)
    (r'\\paragraph\{Design\.\}\n', r'\\subsubsection*{Design}\n'),
    (r'\\paragraph\{Results\.\}\n', r'\\subsubsection*{Results}\n'),

    # Data section: three short technical notes — drop label, fold title into text
    (r'\\paragraph\{Missing values\.\}\n',
     r'\\textit{Missing values.}\\ '),
    (r'\\paragraph\{Regulatory exclusion\.\}\n',
     r'\\textit{Regulatory exclusion.}\\ '),
    (r'\\paragraph\{Criterion orientation\.\}\n',
     r'\\textit{Criterion orientation.}\\ '),

    # Remarks with labels — keep label, use \noindent\textbf or just drop
    (r'\\paragraph\{What the benchmark is, and is not\.\}\n',
     r'\\medskip\\noindent\\textbf{What the benchmark is, and is not.}\n'),
    (r'\\paragraph\{Coherence condition\.\}\n',
     r'\\medskip\\noindent\\textbf{Coherence condition.}\n'),
    (r'\\paragraph\{Scope and empirical confirmation\.\}\n',
     r'\\medskip\\noindent\\textbf{Scope and empirical confirmation.}\n'),
    (r'\\paragraph\{Rank scaling is not innocuous\.\}\n',
     r'\\medskip\\noindent\\textbf{Rank scaling is not innocuous.}\n'),
    (r'\\paragraph\{Benchmark circularity\.\}\n',
     r'\\medskip\\noindent\\textbf{Benchmark circularity.}\n'),

    # Analytical paragraphs — drop and fold title into opening sentence
    # (title is informative enough to keep as bold inline)
    (r'\\paragraph\{Mixed senses and the SAW orientation\.\}\n',
     r'\\medskip\\noindent\\textbf{Mixed senses and the SAW orientation.}\n'),
    (r'\\paragraph\{Pre-specification\.\}\n',
     r'\\medskip\\noindent\\textbf{Pre-specification.}\n'),
    (r'\\paragraph\{Empirical comparison of SAW and TOPSIS distortions\.\}\n',
     r'\\medskip\\noindent\\textbf{Empirical comparison of SAW and TOPSIS distortions.}\n'),
    (r'\\paragraph\{Fogo Island\.\}\n',
     r'\\medskip\\noindent\\textbf{Fogo Island.}\n'),
    (r'\\paragraph\{Empirical magnitude on Fogo Island\.\}\n',
     r'\\medskip\\noindent\\textbf{Empirical magnitude on Fogo Island.}\n'),
    (r'\\paragraph\{Why pooling aggregation families obscures the mechanism\.\}\n',
     r'\\medskip\\noindent\\textbf{Why pooling aggregation families obscures the mechanism.}\n'),
    (r'\\paragraph\{A coding inconsistency amplified by exact assembly\.\}\n',
     r'\\medskip\\noindent\\textbf{A coding inconsistency amplified by exact assembly.}\n'),
]

for old, new in replacements:
    before = content
    content = re.sub(old, new, content)
    n = content.count(new.replace('\\\\', '\\')) 
    found = before != content
    print(f'{"OK" if found else "MISS"}: {old[:60]}')

# verify no \paragraph{ left (except commented)
remaining = [l for l in content.splitlines() if r'\paragraph{' in l and not l.strip().startswith('%')]
print(f'\nRemaining \\paragraph: {len(remaining)}')
for r in remaining:
    print(f'  {r.strip()[:80]}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('\nDone.')
