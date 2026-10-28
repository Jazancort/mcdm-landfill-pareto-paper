import re

path = 'main.tex'
raw = open(path, encoding='utf-8').read()
lines = raw.splitlines()

# --- Abstract last 3 sentences ---
print('=== ABSTRACT LAST 4 SENTENCES ===')
m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', raw, re.DOTALL)
if m:
    text = m.group(1).strip()
    # Remove latex commands but keep structure
    text_clean = re.sub(r'\\[a-zA-Z]+\*?(\{[^}]*\})?', ' ', text)
    text_clean = re.sub(r'\$[^$]+\$', 'MATH', text_clean)
    text_clean = re.sub(r'\s+', ' ', text_clean).strip()
    sentences = [s.strip() for s in re.split(r'(?<=[.?!])\s+', text_clean) if len(s.strip()) > 20]
    for s in sentences[-4:]:
        print(f'  > {s[:140]}')
    print(f'  Word count (raw): {len(text.split())}')

# --- Introduction first 10 lines (to see actual opener) ---
print()
print('=== INTRODUCTION FIRST 300 chars ===')
intro_start = None
for i, l in enumerate(lines):
    if r'\section{Introduction}' in l:
        intro_start = i + 2
        break
if intro_start:
    intro = ' '.join(l.strip() for l in lines[intro_start:intro_start+15] if not l.strip().startswith('%'))
    print(f'  {intro[:400]}')

# --- Check actual Discussion opener (first 500 chars) ---
print()
print('=== DISCUSSION OPENER (first 500 chars) ===')
disc_start = None
for i, l in enumerate(lines):
    if r'\section{Discussion}' in l:
        disc_start = i + 2
        break
if disc_start:
    disc = ' '.join(l.strip() for l in lines[disc_start:disc_start+20] if not l.strip().startswith('%'))
    print(f'  {disc[:500]}')

# --- Check if Discussion has emph mechanism names ---
print()
print('=== DISCUSSION MECHANISM NAMES ===')
disc_lines = lines[2429:2830]
emph_hits = [(2429+i+1, l.strip()) for i, l in enumerate(disc_lines) if r'\emph{' in l and not l.strip().startswith('%')]
for ln, txt in emph_hits[:8]:
    print(f'  L{ln}: {txt[:110]}')

# --- Check Discussion closing (practice section) ---
print()
print('=== DISCUSSION PRACTICE SECTION (L2622+) ===')
for i, l in enumerate(lines[2621:2700], 2622):
    if l.strip() and not l.strip().startswith('%'):
        print(f'  L{i}: {l.strip()[:110]}')
    if i > 2660:
        break
