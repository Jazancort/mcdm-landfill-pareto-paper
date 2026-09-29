import re

with open('main.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# figure single-column: remover argumento opcional
n1 = text.count(r'\begin{figure}[tbp]')
text = text.replace(r'\begin{figure}[tbp]', r'\begin{figure}')
n2 = text.count(r'\begin{figure}[t]')
text = text.replace(r'\begin{figure}[t]', r'\begin{figure}')

with open('main.tex', 'w', encoding='utf-8') as f:
    f.write(text)

print(f'Removed [tbp] from {n1} figures, [t] from {n2} figures')

# Verificar
with open('main.tex', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines, 1):
    if r'\begin{figure' in l:
        print(f'L{i}: {l.rstrip()[:70]}')
