import re
lines = open('main.tex', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    s = l.strip()
    if not s.startswith('%') and re.match(r'\\begin\{(remark|corollary|proposition|lemma|theorem|definition)\}', s):
        # show the begin line and next 2
        print(f'L{i}: {s[:100]}')
        for j in range(i, min(len(lines), i+2)):
            print(f'  L{j+1}: {lines[j].rstrip()[:100]}')
        print()
