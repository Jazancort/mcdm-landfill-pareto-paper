import re
lines = open('main.tex', encoding='utf-8').readlines()
pat = re.compile(r'\\(sub)*section\*?\{([^}]+)\}')
for i, l in enumerate(lines, 1):
    if l.strip().startswith('%'):
        continue
    m = pat.search(l)
    if m:
        level = m.group(1) or ''
        title = m.group(2)
        words = len(title.split())
        chars = len(title)
        flag = ' *** LONG ***' if chars > 50 else ''
        indent = '  ' * (level.count('sub'))
        print(f"L{i:5} [{chars:3}c,{words:2}w]{flag}: {indent}{title}")
