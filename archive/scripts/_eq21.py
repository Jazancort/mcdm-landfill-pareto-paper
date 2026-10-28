lines = open('main.tex', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'rho_j' in l and ('max_a' in l or 'min_a' in l or 'lVert' in l):
        if not l.strip().startswith('%'):
            start = max(0, i-3)
            for j in range(start, min(len(lines), i+6)):
                print(f'L{j+1}: {lines[j].rstrip()}')
            print()
            break
