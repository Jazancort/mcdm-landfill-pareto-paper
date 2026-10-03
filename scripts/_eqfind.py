import re
lines = open('main.tex', encoding='utf-8').readlines()
# find equation label eq:feasible or the T = { t subset S definition
for i, l in enumerate(lines, 1):
    if 'satisfies' in l or 'mathcal{T}' in l or '1{,}944{,}653' in l or 'eq:feasible' in l or 'Ntrios' in l:
        if not l.strip().startswith('%'):
            print(f'L{i}: {l.rstrip()[:110]}')
