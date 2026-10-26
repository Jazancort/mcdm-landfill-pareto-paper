lines = open('main.tex', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'sum_{j' in l and ('G_2' in l or 'G_3' in l) and 'c_j' in l:
        if not l.strip().startswith('%'):
            print(f'L{i}: {l.rstrip()[:120]}')
