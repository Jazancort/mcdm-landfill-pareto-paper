import re

lines = open('main.tex', encoding='utf-8').readlines()

heading_pat = re.compile(r'\\(sub)*section\*?\s*\{')
headings = []
for i, l in enumerate(lines):
    if heading_pat.search(l) and not l.strip().startswith('%'):
        headings.append((i, l.strip()[:80]))

def is_text_line(l):
    s = l.strip()
    if not s or s.startswith('%'): return False
    # skip pure-command lines
    if re.match(r'^\\(label|begin|end|caption|FloatBarrier|medskip|noindent|textbf|subsubsection|subsection|section|newcommand|renewcommand|setcounter|hline|toprule|midrule|bottomrule|multicolumn|includegraphics|ref|eqref|cite)', s):
        return False
    return True

def count_text_paragraphs(start, end):
    """Count distinct text paragraphs (separated by blank lines) between start and end."""
    block = lines[start:end]
    paragraphs = 0
    in_para = False
    for l in block:
        s = l.strip()
        if is_text_line(l):
            if not in_para:
                paragraphs += 1
                in_para = True
        else:
            if not s:  # blank line = paragraph break
                in_para = False
    return paragraphs

print(f"{'Line':>6} {'Par':>4}  Title")
print("-" * 80)
for idx, (ln, title) in enumerate(headings):
    next_ln = headings[idx+1][0] if idx+1 < len(headings) else len(lines)
    level = 'sub' * title.count('sub') 
    npar = count_text_paragraphs(ln+1, next_ln)
    flag = ' *** SINGLE ***' if npar <= 1 else ''
    indent = '  ' * title.count('sub')
    print(f"L{ln+1:5} {npar:4}  {indent}{title[:70]}{flag}")
