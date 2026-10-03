import re
lines = open('main.tex', encoding='utf-8').readlines()
in_eq = False
for i, l in enumerate(lines, 1):
    s = l.strip()
    if r'\begin{equation}' in s or r'\begin{align' in s:
        in_eq = True
    if r'\end{equation}' in s or r'\end{align' in s:
        in_eq = False
    if in_eq and r'\qquad' in s and not s.startswith('%'):
        # Check if line is long (both sides of qquad have content)
        parts = s.split(r'\qquad')
        if len(parts) >= 2 and len(parts[0].strip()) > 10 and len(parts[1].strip()) > 10:
            print(f'L{i}: {s[:110]}')
