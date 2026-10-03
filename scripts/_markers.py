import re
lines = open('main.tex', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    s = l.strip()
    if s.startswith('%'):
        continue
    # Lines that are ONLY a \medskip\noindent\textbf{...} or \textit{...}\ or \noindent\textbf
    if re.match(r'^\\medskip\\noindent\\textbf\{', s) or \
       re.match(r'^\\textit\{[^}]+\}\\\\ *$', s) or \
       re.match(r'^\\noindent\\textbf\{', s):
        print(f'L{i}: {s[:100]}')
