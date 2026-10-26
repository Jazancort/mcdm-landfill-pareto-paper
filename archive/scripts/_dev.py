lines = open('main.tex', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'DEV-E5' in l and not l.strip().startswith('%'):
        # show context
        start = max(0, i-4)
        end = min(len(lines), i+3)
        print(f"--- around L{i} ---")
        for j in range(start, end):
            print(f"L{j+1}: {lines[j].rstrip()}")
        print()
