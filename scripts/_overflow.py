import re
lines = open('main.tex', encoding='utf-8').readlines()

# Line numbers from log (1-indexed) to check context
targets = [171, 188, 454, 510, 618, 711, 816, 1244, 1417, 1561, 1770, 1909, 1978, 2039, 2070, 2138, 2290, 2393, 2632, 2664, 2807]

def context(ln, n=3):
    start = max(0, ln-n-1)
    end = min(len(lines), ln+n)
    return [(start+i+1, lines[start+i].rstrip()[:100]) for i in range(end-start)]

for t in targets:
    ctx = context(t, 1)
    relevant = ctx[1][1] if len(ctx) > 1 else ''
    # Classify
    is_table = any('tabular' in lines[max(0,t-10):t+2][i].lower() or 
                   'hline' in lines[max(0,t-10):t+2][i].lower() or
                   '&' in lines[max(0,t-10):t+2][i]
                   for i in range(min(12, len(lines[max(0,t-10):t+2]))))
    print(f"L{t}: {'[TABLE]' if is_table else '[TEXT ]'} {relevant[:80]}")
