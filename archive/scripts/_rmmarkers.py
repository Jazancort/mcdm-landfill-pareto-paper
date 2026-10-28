import re

path = 'main.tex'
content = open(path, encoding='utf-8').read()

# Remove all \medskip\noindent\textbf{Title.} lines (standalone heading lines)
# These are lines that consist ONLY of \medskip\noindent\textbf{...}
content = re.sub(
    r'\\medskip\\noindent\\textbf\{[^}]+\}\n',
    '',
    content
)

# Remove \noindent\textbf{Title.} standalone lines (without medskip)
# but ONLY when they are the whole line (not inline in a sentence)
content = re.sub(
    r'^\\noindent\\textbf\{[^}]+\}\n',
    '',
    content,
    flags=re.MULTILINE
)

# Remove \textit{Title.}\\ standalone markers (Missing values., Regulatory exclusion., etc.)
content = re.sub(
    r'^\\textit\{[^}]+\}\\\\\s*\n',
    '',
    content,
    flags=re.MULTILINE
)

# Clean up any double blank lines that result
content = re.sub(r'\n{3,}', '\n\n', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

# Report remaining
remaining = [l.strip() for l in content.splitlines()
             if (l.strip().startswith(r'\medskip\noindent\textbf{') or
                 re.match(r'^\\noindent\\textbf\{', l.strip()) or
                 re.match(r'^\\textit\{[^}]+\}\\\\', l.strip()))
             and not l.strip().startswith('%')]
print(f"Remaining markers: {len(remaining)}")
for r in remaining:
    print(f"  {r[:80]}")
