# -*- coding: utf-8 -*-
"""audit_gpt_counterexample.py
Test whether GPT's proposed counterexample structure can arise in the E6 family.

GPT's counterexample:
- p_{G1} = (0.110, 0.095, 0.090), sum=0.295 (lambda_1=1)
- p_{G2} = q_{G2} (lambda_2=1)
- p_{G3} = q_{G3} (lambda_3=1)
- Sites A: x_or[:,G1] = (1,0,0) → all G1 weight on first criterion only
- Sites B: x_or[:,G1] = (0.36,0.36,0.36) → balanced
- Score_M prefers T_A but T_B Pareto-dominates T_A

Issue: in E6, criterion columns are continuous min-max normalised values
with 11 criteria over all trios. The "all weight on first criterion"
structure is extremely unlikely with Dirichlet draws.

But more importantly: the E6 data already shows q2=100% for ALL 9000 draws.
This means the counterexample structure does NOT arise in any of the 45
instances × 200 draws.

We verify this by checking: is there ANY draw in E6 where M-optimal is not Pareto?
"""
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).parent.parent
df = pd.read_csv(ROOT / "results" / "e6" / "e6_raw_results.csv")

print("=" * 60)
print("VERIFYING GPT COUNTEREXAMPLE CANNOT ARISE IN E6 DATA")
print("=" * 60)
print()

# Check M, optimal across all instances and draws
m_opt = df[(df.condition=="M") & (df.assembly=="optimal")]

# Per-draw check
non_pareto = m_opt[m_opt.q2 < 1.0 - 1e-9]
print(f"Total M-optimal draws: {len(m_opt)}")
print(f"Draws where M-optimal NOT Pareto: {len(non_pareto)}")

if len(non_pareto) == 0:
    print()
    print("CONCLUSION: GPT's counterexample DOES NOT ARISE in any of the")
    print(f"  {m_opt.inst_id.nunique()} instances × {m_opt.groupby('inst_id').size().max()} draws")
    print("  = {len(m_opt)} total draw-instances.")
    print()
    print("The algebraic argument is valid in principle but the structure")
    print("it requires (weight concentrated on one criterion within a group,")
    print("while sites have matching concentrated values) does not occur in")
    print("the E6 family with min-max normalised data and Dirichlet(200) draws.")
    print()
    print("Reporting as: '100% confirmed empirically on all 9000 draws;")
    print("consistent with the group-scalarisation theorem under the drawn")
    print("weight distribution.'")
else:
    print(f"WARNING: {len(non_pareto)} failures found!")
    print(non_pareto[["inst_id","q2"]].head(10))

print()
print("=" * 60)
print("ALSO CHECK: B and C conditions")
print("=" * 60)
for cond in ["B", "C"]:
    sub = df[(df.condition==cond) & (df.assembly=="optimal")]
    n_fail = (sub.q2 < 1.0 - 1e-9).sum()
    print(f"  {cond}: {len(sub)} draws, {n_fail} non-Pareto ({100*n_fail/len(sub):.2f}%)")
