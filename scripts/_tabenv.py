import re
lines = open('main.tex', encoding='utf-8').readlines()

# For each table target, find the enclosing \begin{table} and its type
targets = [1908, 1977, 2038, 2137, 2289, 2392]
for t in targets:
    # Search backwards for \begin{table
    for i in range(t, max(0,t-30), -1):
        if r'\begin{table' in lines[i]:
            env = lines[i].strip()
            print(f"L{t+1} overflow -> table starts at L{i+1}: {env}")
            break
    # Also show column spec
    print(f"  col spec: {lines[t].strip()}")
    print()
