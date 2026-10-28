import re

path = 'main.tex'
lines = open(path, encoding='utf-8').readlines()

def show(label, hits, limit=4):
    if hits:
        print(f'  [{label}] ({len(hits)} hits):')
        for ln, txt in hits[:limit]:
            print(f'    L{ln}: {txt[:110]}')

# --- "attributable to" contexts ---
print('=== attributable to (context check) ===')
hits = [(i+1, l.strip()) for i, l in enumerate(lines)
        if 'attributable to' in l and not l.strip().startswith('%')]
show('attributable to', hits)

# --- "significantly" context ---
print()
print('=== significantly (context) ===')
hits = [(i+1, l.strip()) for i, l in enumerate(lines)
        if 'significantly' in l and not l.strip().startswith('%')]
show('significantly', hits)

# --- "robust" context ---
print()
print('=== robust (context) ===')
hits = [(i+1, l.strip()) for i, l in enumerate(lines)
        if 'robust' in l.lower() and not l.strip().startswith('%')]
show('robust', hits, limit=6)

# --- internal file refs ---
print()
print('=== internal file refs (exact) ===')
hits = [(i+1, l.strip()) for i, l in enumerate(lines)
        if re.search(r'(?<!\\verb)[a-z_]+\.(py|csv|json)', l) and not l.strip().startswith('%')]
show('file refs', hits, limit=8)

# --- en-dash in non-math contexts ---
print()
print('=== en-dash -- (all, to classify) ===')
hits = [(i+1, l.strip()) for i, l in enumerate(lines)
        if '--' in l and not l.strip().startswith('%')]
show('en-dash --', hits, limit=10)

# --- enumerate/itemize contexts ---
print()
print('=== enumerate/itemize (context check) ===')
hits = [(i+1, l.strip()) for i, l in enumerate(lines)
        if re.search(r'\\begin\{(itemize|enumerate)', l) and not l.strip().startswith('%')]
show('lists', hits)

# --- We state this explicitly context ---
print()
print('=== "We state this explicitly" context ===')
hits = [(i+1, l.strip()) for i, l in enumerate(lines)
        if 'We state this explicitly' in l and not l.strip().startswith('%')]
show('meta-commentary', hits)
if hits:
    ln = hits[0][0]
    print('  Surrounding context:')
    for c in lines[ln-2:ln+2]:
        print(f'    {c.rstrip()[:110]}')

# --- "spread" as amplitude synonym check ---
print()
print('=== "spread" contexts ===')
hits = [(i+1, l.strip()) for i, l in enumerate(lines)
        if re.search(r'\bspread\b', l) and not l.strip().startswith('%')]
show('spread', hits, limit=6)

# --- Abstract word count with pdftotext ---
print()
print('=== ABSTRACT RAW TEXT ===')
raw = open(path, encoding='utf-8').read()
m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', raw, re.DOTALL)
if m:
    text = m.group(1)
    # Count words including LaTeX tokens
    words = len(text.split())
    print(f'  Words (incl. LaTeX tokens): {words}')
    # Rough estimate stripping LaTeX
    clean = re.sub(r'\\[a-zA-Z]+(\{[^}]*\})?', '', text)
    clean = re.sub(r'[\$\{\}\\]', ' ', clean)
    wclean = len(clean.split())
    print(f'  Words (LaTeX stripped): {wclean}')
    # Show last sentence
    sentences = re.split(r'(?<=[.!?])\s+', clean.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
    print(f'  Last sentence: {sentences[-1][:150]}')
