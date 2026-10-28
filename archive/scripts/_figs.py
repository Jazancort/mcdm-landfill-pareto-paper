import re
lines = open('main.tex', encoding='utf-8').readlines()
# Find all \begin{figure} with their options
for i, l in enumerate(lines, 1):
    if r'\begin{figure' in l and not l.strip().startswith('%'):
        # collect figure block
        block = []
        j = i - 1
        while j < min(i+20, len(lines)):
            block.append(f'L{j+1}: {lines[j].rstrip()[:100]}')
            if r'\end{figure' in lines[j]:
                break
            j += 1
        print('\n'.join(block[:15]))
        print('---')
