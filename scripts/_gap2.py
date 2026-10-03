lines = open('main.tex', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'mathrm{gap}' in l or ('gap(' in l and 'max' in l) or 'eq:gap' in l or ('R_1' in l and 'R_2' in l):
        if not l.strip().startswith('%'):
            print(f'L{i}: {l.rstrip()[:110]}')
