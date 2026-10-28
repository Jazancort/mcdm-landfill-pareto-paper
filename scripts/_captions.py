import re
lines = open('main.tex', encoding='utf-8').readlines()
i = 0
while i < len(lines):
    l = lines[i]
    if r'\caption' in l and not l.strip().startswith('%'):
        # collect full caption (may span multiple lines until })
        cap = l.rstrip()
        j = i + 1
        depth = l.count('{') - l.count('}')
        while depth > 0 and j < len(lines):
            cap += ' ' + lines[j].rstrip()
            depth += lines[j].count('{') - lines[j].count('}')
            j += 1
        # clean latex
        clean = re.sub(r'\\[a-zA-Z]+(\[[^\]]*\])?(\{[^}]*\})?', ' ', cap)
        clean = re.sub(r'[\$\{\}\\]', ' ', clean)
        words = len(clean.split())
        flag = '*** LONG ***' if words > 60 else ''
        print(f'L{i+1} ({words}w) {flag}: {cap[:100]}')
    i += 1
