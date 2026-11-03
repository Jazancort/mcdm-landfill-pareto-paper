# -*- coding: utf-8 -*-
"""check_e7_gates.py -- Standalone gate check for E7 output."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent.parent
df_raw = pd.read_csv(ROOT / "results" / "e7" / "e7_raw.csv")
print(f"Loaded {len(df_raw)} rows")
print("Columns:", df_raw.columns.tolist())
print("Alphas:", sorted(df_raw.alpha.unique()))

KNOWN_Q2 = {
    200: {("saw","minmax","greedy"):86.0, ("saw","minmax","optimal"):100.0,
          ("saw","vector","greedy"):66.2, ("saw","vector","optimal"):56.8,
          ("topsis","minmax","greedy"):94.4, ("topsis","minmax","optimal"):96.6,
          ("topsis","vector","greedy"):63.4, ("topsis","vector","optimal"):52.4},
    50:  {("saw","minmax","greedy"):97.6, ("saw","minmax","optimal"):100.0,
          ("saw","vector","greedy"):77.0, ("saw","vector","optimal"):79.4,
          ("topsis","minmax","greedy"):89.8, ("topsis","minmax","optimal"):92.2,
          ("topsis","vector","greedy"):52.0, ("topsis","vector","optimal"):51.0},
}

all_pass = True
for kappa, cells in KNOWN_Q2.items():
    dfk = df_raw[df_raw["alpha"] == kappa]
    for (agg, norm, mont), expected in cells.items():
        sub = dfk[(dfk["agg"]==agg)&(dfk["norm"]==norm)&(dfk["mont"]==mont)]
        got = sub["nd_Q2Ap"].mean() * 100
        ok = abs(got - expected) <= 0.5
        status = "PASS" if ok else "WARN"
        print(f"[{status}] G1 κ={kappa} {agg}/{norm}/{mont}: {got:.1f}% vs expected {expected:.1f}%")
        if not ok: all_pass = False

print()
for kappa in sorted(df_raw["alpha"].unique()):
    dfk = df_raw[df_raw["alpha"] == kappa]
    sub = dfk[(dfk["agg"]=="saw")&(dfk["norm"]=="minmax")&(dfk["mont"]=="optimal")]
    q2 = sub["nd_Q2Ap"].mean() * 100
    ok = abs(q2 - 100.0) < 0.01
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] G2 SAW/mm/opt κ={kappa}: {q2:.1f}%")
    if not ok: all_pass = False

print()
for kappa in sorted(df_raw["alpha"].unique()):
    n = df_raw[df_raw["alpha"]==kappa]["draw"].nunique()
    ok = (n == 500)
    print(f"[{'PASS' if ok else 'FAIL'}] G3 N_draws κ={kappa}: {n}")
    if not ok: all_pass = False

print()
print("ALL GATES PASS" if all_pass else "WARNING: some gates outside tolerance")
