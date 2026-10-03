import re
lines = open('main.tex', encoding='utf-8').readlines()

def get_caption(start):
    cap_lines = [lines[start].rstrip()]
    j = start + 1
    depth = lines[start].count('{') - lines[start].count('}')
    while depth > 0 and j < len(lines):
        cap_lines.append(lines[j].rstrip())
        depth += lines[j].count('{') - lines[j].count('}')
        j += 1
    return '\n'.join(cap_lines), j

for target in [780, 1228, 1635, 1888]:
    cap, end = get_caption(target)
    print(f'=== L{target+1}-L{end} ===')
    print(cap)
    print()
