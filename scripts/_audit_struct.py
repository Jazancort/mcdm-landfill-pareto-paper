import re, sys
path = sys.argv[1]
lines = open(path, encoding='utf-8').readlines()
print(f'Total lines: {len(lines)}')
sec_pat = re.compile(r'\\(section|subsection|subsubsection)\{')
lbl_pat = re.compile(r'\\label\{sec:')
for i, l in enumerate(lines, 1):
    s = l.rstrip()
    if s.lstrip().startswith('%'):
        continue
    if sec_pat.search(s) or lbl_pat.search(s):
        print(f'{i:5}: {s.strip()[:110]}')
