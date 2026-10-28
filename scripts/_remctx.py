lines = open('main.tex', encoding='utf-8').readlines()
targets = [
    (1238, 1253),  # remark Q2=1
    (1358, 1410),  # remark amplitude exponent
    (1411, 1424),  # corollary mm not neutral
    (1662, 1676),  # remark factorisation
    (1691, 1719),  # corollary order of ops
    (2167, 2188),  # remark non-monotone
]
for start, end in targets:
    print(f"=== L{start+1}-L{end+1} ===")
    for l in lines[start:end+1]:
        print(f"  {l.rstrip()[:100]}")
    print()
