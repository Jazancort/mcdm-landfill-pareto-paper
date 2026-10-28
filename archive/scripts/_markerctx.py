lines = open('main.tex', encoding='utf-8').readlines()
targets = [674, 710, 850, 886, 931, 978, 1028, 1119, 1466, 1512, 1700, 1744, 2005, 2076, 2328, 2586]
for t in targets:
    print(f"=== L{t+1} ===")
    for l in lines[t:t+4]:
        print(f"  {l.rstrip()[:100]}")
    print()
