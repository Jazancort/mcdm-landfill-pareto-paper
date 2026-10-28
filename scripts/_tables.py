lines = open('main.tex', encoding='utf-8').readlines()
targets = [1908, 1977, 2038, 2137, 2289, 2392]
for t in targets:
    print(f"=== L{t+1} ===")
    for l in lines[t:t+6]:
        print(f"  {l.rstrip()[:110]}")
    print()
