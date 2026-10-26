lines = open('main.tex', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if r'\paragraph{' in l and not l.strip().startswith('%'):
        print(f'L{i}: {l.rstrip()}')
