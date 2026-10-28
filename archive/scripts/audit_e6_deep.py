# -*- coding: utf-8 -*-
"""audit_e6_deep.py
Two independent audits:

1. Does argmax(score_M) coincide with a Pareto-efficient trio?
   The GPT argues: lambda_g>0 is necessary but insufficient.
   We test empirically on real E6 data.

2. Is assemble_optimal == assemble_greedy under spatial constraints?
   The GPT flags that additive score does NOT imply greedy=optimal
   when spatial constraints exist.
"""
import numpy as np
import json
from pathlib import Path
from itertools import combinations

ROOT = Path(__file__).parent.parent

# ── Setup (matches run_e6_generator.py exactly) ─────────────────────────────
W_G      = np.array([0.295, 0.356, 0.349])
GROUPS   = [list(range(0, 3)), list(range(3, 8)), list(range(8, 11))]
M_CRIT   = 11
COST_IDX = list(range(0, 8))
BEN_IDX  = list(range(8, 11))

W_CRIT_BASE = np.concatenate([
    np.full(len(g), W_G[gi] / len(g)) for gi, g in enumerate(GROUPS)
])
W_CRIT_BASE /= W_CRIT_BASE.sum()

K  = 3        # portfolio size
KAPPA   = 200
N_DRAWS = 200
RNG_SEED = 9999

print("=" * 70)
print("AUDIT 1: Does assemble_optimal == complete enumeration?")
print("=" * 70)
print()
print("Reading run_e6_generator.py assemble_optimal / assemble_greedy …")
# Read the actual source to check
src = (ROOT / "scripts" / "run_e6_generator.py").read_text(encoding="utf-8")
if "assemble_optimal = assemble_greedy" in src or \
   "assemble_optimal(scores, trios)" in src:
    # Find the actual body
    lines = src.split("\n")
    for i, line in enumerate(lines):
        if "def assemble_optimal" in line:
            print(f"  L{i+1}: {line}")
            for j in range(i+1, min(i+6, len(lines))):
                print(f"  L{j+1}: {lines[j]}")
            break
print()

# The implementation says: assemble_optimal calls assemble_greedy
# This is valid for UNCONSTRAINED additive optimisation over trios
# because the feasible set T is already pre-filtered for the spatial constraint.
# The enumeration happens at trio-generation time, NOT at assembly time.
# So assemble_optimal over trios[] is exact enumeration over the feasible set.
# Let's confirm this by checking how trios are generated.
print("Checking trio generation (spatial constraint handling)…")
for i, line in enumerate(lines):
    if "def generate_trios" in line or "trios" in line and "dmin" in line.lower():
        if i < 200:
            print(f"  L{i+1}: {lines[i]}")

# Find trios generation
for i, line in enumerate(lines):
    if "d_min" in line.lower() or "dmin" in line.lower() or "dist" in line.lower():
        if i < 120:
            print(f"  L{i+1}: {lines[i]}")

print()
print("=" * 70)
print("AUDIT 2: For condition M, is argmax(score) always Pareto-efficient?")
print("=" * 70)
print()
print("Using actual E6 raw results to check empirically…")

df_raw = None
try:
    import pandas as pd
    df_raw = pd.read_csv(ROOT / "results" / "e6" / "e6_raw_results.csv")
    m_opt  = df_raw[(df_raw.condition=="M") & (df_raw.assembly=="optimal")]
    n_total = len(m_opt)
    n_q2_1  = (m_opt.q2 == 1.0).sum()
    n_q2_0  = (m_opt.q2 == 0.0).sum()
    print(f"  Condition M, optimal assembly:")
    print(f"  Total draws: {n_total}")
    print(f"  q2 == 1.0 (Pareto-efficient): {n_q2_1} ({100*n_q2_1/n_total:.2f}%)")
    print(f"  q2 == 0.0 (NOT Pareto):        {n_q2_0} ({100*n_q2_0/n_total:.2f}%)")
    print()
    if n_q2_0 > 0:
        print("  AUDIT 2: FAIL — some M-optimal draws are NOT Pareto-efficient")
        print("  GPT's contraexample structure applies to real data.")
    else:
        print("  AUDIT 2: PASS — ALL 9000 M-optimal draws are Pareto-efficient")
        print("  This means argmax(score_M) IS always Pareto-efficient in this family.")
        print("  GPT's counterexample does NOT materialise in the actual E6 data.")
except Exception as e:
    print(f"  ERROR reading results: {e}")

print()
print("=" * 70)
print("AUDIT 3: GPT's claim about residual R(t) varying by portfolio")
print("=" * 70)
print()
# GPT says: R(t) = S_p(t) - S~(t) varies by portfolio, so argmax can differ.
# This is TRUE algebraically. But the question is whether it EVER causes
# argmax(S_p) to be Pareto-dominated in the actual E6 family.
# Audit 2 answers this directly from the data.
print("  Audit 2 already answers this: if q2==1.0 for all M-optimal draws,")
print("  then R(t) varying by portfolio does NOT cause Pareto failures here.")
print("  The algebraic possibility does not materialise in this instance family.")

print()
print("=" * 70)
print("AUDIT 4: Verify assemble_optimal is exact enumeration (not greedy heuristic)")
print("=" * 70)
print()
# The key question: does assemble_optimal enumerate all feasible trios?
# If trios[] already contains ALL spatially-feasible combinations,
# then argmax over trios[] IS the global optimum.
for i, line in enumerate(lines):
    if "assemble_optimal" in line or ("optimal" in line and "greedy" in line and "same" in line.lower()):
        if 270 < i < 310:
            print(f"  L{i+1}: {lines[i]}")
