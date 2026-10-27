# -*- coding: utf-8 -*-
"""
verify_e7_gates.py  --  Rerun G1/G2/G3 gates on existing e7_raw.csv.
Uses .query() to avoid pandas StringDtype boolean indexing issues.
"""
import pandas as pd

df = pd.read_csv("results/e7/e7_raw.csv")

KNOWN_Q2 = {
    200: {
        ("saw","minmax","greedy"): 86.0,  ("saw","minmax","optimal"): 100.0,
        ("saw","vector","greedy"): 66.2,  ("saw","vector","optimal"):  56.8,
        ("topsis","minmax","greedy"): 94.4, ("topsis","minmax","optimal"): 96.6,
        ("topsis","vector","greedy"): 63.4, ("topsis","vector","optimal"): 52.4,
    },
    50: {
        ("saw","minmax","greedy"): 97.6,  ("saw","minmax","optimal"): 100.0,
        ("saw","vector","greedy"): 77.0,  ("saw","vector","optimal"):  79.4,
        ("topsis","minmax","greedy"): 89.8, ("topsis","minmax","optimal"): 92.2,
        ("topsis","vector","greedy"): 52.0, ("topsis","vector","optimal"): 51.0,
    },
}

all_pass = True
print("=== G1: kappa=200 and kappa=50 reproduce Table 5 ===")
for kappa, cells in KNOWN_Q2.items():
    for (agg, norm, mont), exp in cells.items():
        got = df.query(
            f"alpha=={kappa} and agg=='{agg}' and norm=='{norm}' and mont=='{mont}'"
        )["nd_Q2Ap"].mean() * 100
        ok = abs(got - exp) <= 0.5
        if not ok: all_pass = False
        print(f"  [{'PASS' if ok else 'FAIL'}] k={kappa} {agg}/{norm}/{mont}: {got:.1f}%  (expected {exp}%)")

print()
print("=== G2: SAW/mm/opt = 100% at all kappa ===")
for k in sorted(df["alpha"].unique()):
    q2 = df.query(f"alpha=={k} and agg=='saw' and norm=='minmax' and mont=='optimal'")["nd_Q2Ap"].mean() * 100
    ok = abs(q2 - 100.0) < 0.1
    if not ok: all_pass = False
    print(f"  [{'PASS' if ok else 'FAIL'}] k={k}: {q2:.1f}%")

print()
print("=== G3: 500 draws per kappa ===")
for k in sorted(df["alpha"].unique()):
    n = df.query(f"alpha=={k}")["draw"].nunique()
    ok = (n == 500)
    if not ok: all_pass = False
    print(f"  [{'PASS' if ok else 'FAIL'}] k={k}: {n} draws")

print()
print("ALL PASS" if all_pass else "SOME FAIL — see above")
