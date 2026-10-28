lines = open('main.tex', encoding='utf-8').readlines()
# Show heading line for each merge target to get exact text
for t in [527, 549, 841, 851, 877, 887, 1001, 1086, 1090, 2332, 2341, 2594, 2621]:
    print(f'L{t+1}: {lines[t].rstrip()}')
