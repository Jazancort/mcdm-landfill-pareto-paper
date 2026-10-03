lines = open('main.tex', encoding='utf-8').readlines()
targets = [527, 549, 622, 841, 851, 877, 887, 1001, 1086, 2332, 2594]
for t in targets:
    print(f'=== L{t+1} ===')
    for l in lines[t:t+8]:
        print(' ', l.rstrip()[:100])
    print()
