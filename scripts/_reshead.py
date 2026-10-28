lines = open('main.tex', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'Results' in l and not l.strip().startswith('%'):
        if 'section' in l or 'subsubsection' in l:
            print(f'L{i}: {l.rstrip()}')
