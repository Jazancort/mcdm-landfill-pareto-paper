import re
lines = open('main.tex', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    m = re.search(r'\\includegraphics[^{]*\{([^}]+)\}', l)
    if m and not l.strip().startswith('%'):
        print(f'L{i}: {m.group(1)}')
