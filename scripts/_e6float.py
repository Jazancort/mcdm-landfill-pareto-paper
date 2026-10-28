import re
lines = open('main.tex', encoding='utf-8').readlines()
# Find the Results subsubsection and surrounding floats
for i, l in enumerate(lines, 1):
    s = l.strip()
    if not s.startswith('%') and any(x in s for x in [
        r'\FloatBarrier', r'\subsubsection*{Results}', 
        r'\begin{table*}', r'\end{table*}', r'\begin{figure', 
        r'\end{figure', r'sec:e6', r'tab:e6']):
        print(f'L{i}: {s[:100]}')
