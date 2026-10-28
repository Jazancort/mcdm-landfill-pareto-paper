lines = open('main.tex', encoding='utf-8').readlines()
# Find fig:slope_weights reference in text
for i, l in enumerate(lines, 1):
    if 'slope_weights' in l and 'ref' in l and not l.strip().startswith('%'):
        print(f'L{i}: {l.rstrip()}')
# Also show what table precedes it
for i, l in enumerate(lines, 1):
    if r'\end{table*}' in l:
        print(f'end table* at L{i}')
