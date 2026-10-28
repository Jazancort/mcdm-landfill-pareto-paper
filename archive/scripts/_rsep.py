import re
lines = open('main.tex', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'eq:rsep' in l or 'rsep' in l:
        if not l.strip().startswith('%'):
            print(f'L{i}: {l.rstrip()[:110]}')
