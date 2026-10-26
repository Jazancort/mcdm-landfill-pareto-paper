import re
path = r'main.tex'
raw = open(path, encoding='utf-8').read()
m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', raw, re.DOTALL)
text = m.group(1)
clean = re.sub(r'\\[a-zA-Z]+(\{[^}]*\})?', '', text)
clean = re.sub(r'[\$\{\}\\]', ' ', clean)
wclean = len(clean.split())
print(f'Words (cleaned): {wclean}')
