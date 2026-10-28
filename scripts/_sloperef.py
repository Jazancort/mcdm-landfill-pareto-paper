lines = open('main.tex', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'fig:slope' in l and not l.strip().startswith('%'):
        print(f'L{i}: {l.rstrip()[:100]}')
