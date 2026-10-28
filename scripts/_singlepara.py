import re

lines = open('main.tex', encoding='utf-8').readlines()
raw = ''.join(lines)

# Find all section/subsection/subsubsection headings with line numbers
heading_pat = re.compile(r'\\(sub)*section\*?\{')
headings = []
for i, l in enumerate(lines):
    if heading_pat.search(l) and not l.strip().startswith('%'):
        title = l.strip()[:80]
        headings.append((i+1, title))

# For each heading, find content until next heading and count paragraphs
def count_paragraphs(start_ln, end_ln):
    """Count non-empty paragraph blocks between two line numbers."""
    block = lines[start_ln:end_ln]
    # Remove comments, commands-only lines, begin/end environments
    text_lines = []
    for l in block:
        s = l.strip()
        if (s and not s.startswith('%') and not s.startswith('\\begin')
                and not s.startswith('\\end') and not s.startswith('\\label')
                and not s.startswith('\\section') and not s.startswith('\\subsection')
                and not s.startswith('\\caption') and not s.startswith('\\FloatBarrier')):
            text_lines.append(s)
    # Count paragraph breaks (empty lines separating text)
    content = '\n'.join(text_lines)
    paras = [p.strip() for p in re.split(r'\n\s*\n', content) if p.strip()]
    return len(paras), len(content.split())

for idx, (ln, title) in enumerate(headings):
    next_ln = headings[idx+1][0] - 1 if idx+1 < len(headings) else len(lines)
    npar, nwords = count_paragraphs(ln, next_ln)
    if npar <= 1:
        print(f'L{ln} [{npar}par, ~{nwords}w]: {title}')
