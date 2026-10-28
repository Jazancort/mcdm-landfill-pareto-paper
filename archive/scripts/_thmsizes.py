import re
lines = open('main.tex', encoding='utf-8').readlines()
env_pat = re.compile(r'\\begin\{(remark|corollary|proposition|lemma|theorem|definition)\}')
end_pat = re.compile(r'\\end\{(remark|corollary|proposition|lemma|theorem|definition)\}')
starts = []
for i, l in enumerate(lines):
    if not l.strip().startswith('%') and env_pat.search(l):
        starts.append(i)

for s in starts:
    # find end
    depth = 0
    end = s
    env_name = env_pat.search(lines[s]).group(1)
    for j in range(s, min(len(lines), s+40)):
        if env_pat.search(lines[j]) and not lines[j].strip().startswith('%'):
            depth += 1
        if end_pat.search(lines[j]) and not lines[j].strip().startswith('%'):
            depth -= 1
            if depth == 0:
                end = j
                break
    # count lines and words
    block = lines[s:end+1]
    text = ' '.join(l.strip() for l in block)
    words = len(text.split())
    print(f"L{s+1}-L{end+1} [{env_name}] ({words}w): {lines[s].strip()[:80]}")
