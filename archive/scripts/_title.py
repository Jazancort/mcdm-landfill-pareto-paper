import re
lines = open('main.tex', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if any(x in l for x in ['implicit re-weighting', 'Implicit Re-weighting', 'multi-criteria portfolio', 'closed form', 'shorttitle', 'title[']):
        if not l.strip().startswith('%'):
            print(f'L{i}: {l.rstrip()}')
