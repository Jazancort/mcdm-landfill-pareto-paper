lines = open('main.tex', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'weff_vec' in l or ('w_j^{\\mathrm{eff}}' in l and 'rho' in l) or ('qquad' in l and 'rho_j' in l):
        if not l.strip().startswith('%'):
            for j in range(max(0,i-3), min(len(lines), i+8)):
                print(f'L{j+1}: {lines[j].rstrip()}')
            print()
