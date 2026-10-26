lines = open('main.tex', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if ('slope' in l.lower() or ('effective weight' in l.lower() and 'figure' in l.lower()) or 'fig_F1' in l or 'slope_weight' in l) and not l.strip().startswith('%'):
        print(f'L{i}: {l.rstrip()[:100]}')
