import re
lines = open('main.tex', encoding='utf-8').readlines()
raw = open('main.tex', encoding='utf-8').read()

par_lines = [(i+1, l.rstrip()) for i, l in enumerate(lines) if r'\paragraph{' in l and not l.strip().startswith('%')]

for ln, l in par_lines:
    # check if next 2 lines have a \label
    block = ''.join(lines[ln-1:ln+2])
    label = re.search(r'\\label\{([^}]+)\}', block)
    lbl = label.group(1) if label else None
    # check if label is referenced
    refs = 0
    if lbl:
        refs = raw.count(f'ref{{{lbl}}}')
    title = re.search(r'\\paragraph\{([^}]+)\}', l).group(1)
    print(f'L{ln}: [{title}] label={lbl} refs={refs}')
