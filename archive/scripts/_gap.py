import re
lines = open('main.tex', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'gap' in l.lower() and ('max' in l or 'min' in l) and ('F_1' in l or 'F_2' in l or 'R_1' in l):
        if not l.strip().startswith('%'):
            print(f'L{i}: {l.rstrip()}')
