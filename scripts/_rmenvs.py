import re

path = 'main.tex'
content = open(path, encoding='utf-8').read()

# Strategy: remove \begin{remark}[Title] ... \end{remark}
# and \begin{corollary}[Title] ... \end{corollary}
# keeping the body as plain running text

def strip_env(content, env):
    """Remove \begin{env}[...] and \end{env}, keep body."""
    # Pattern: \begin{env}[optional title]\n\label{...}\n ...body... \end{env}
    pat = re.compile(
        r'\\begin\{' + env + r'\}(?:\[[^\]]*\])?\n'
        r'(.*?)'
        r'\\end\{' + env + r'\}',
        re.DOTALL
    )
    def replacer(m):
        body = m.group(1)
        # Remove the \label line from body (keep label for cross-refs)
        # Actually keep \label so \ref still works
        return body.rstrip()
    
    new_content = pat.sub(replacer, content)
    count = len(pat.findall(content))
    return new_content, count

for env in ['remark', 'corollary']:
    content, n = strip_env(content, env)
    print(f'Stripped {n} {env} environments')

# Clean up double blank lines
content = re.sub(r'\n{3,}', '\n\n', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

# Verify none left
remaining = len(re.findall(r'\\begin\{(remark|corollary)\}', content))
print(f'Remaining remark/corollary: {remaining}')
print('Done.')
