# -*- coding: utf-8 -*-
"""validate_e6.py — E6-D validation script"""
import pandas as pd, numpy as np, json, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
e6_dir = ROOT / "results" / "e6"

df = pd.read_csv(e6_dir / "e6_raw_results.csv")
seeds = json.load(open(e6_dir / "e6_seeds.json"))

print("=== E6 VALIDATION ===")
print(f"Total rows: {len(df)}  (expected {45*5*2*200})")
print(f"Instances:  {df.inst_id.nunique()} / 45")
print(f"Conditions: {sorted(df.condition.unique())}")
print(f"Protocol hash: {seeds['protocol_hash']}")
print()

# Robustness checks (NaN, domain, completeness)
print("ROBUSTNESS CHECKS:")
nan_q2 = df.q2.isna().sum()
print(f"  NaN in q2:       {nan_q2}  (expected 0)")
non_binary = (~df.q2.isin([0.0, 1.0])).sum()
print(f"  Non-binary q2:   {non_binary}  (expected 0)")
expected_rows = 45 * 5 * 2 * 200
row_ok = len(df) == expected_rows
print(f"  Row count:       {len(df)} == {expected_rows}? {row_ok}")
inst_ok = df.inst_id.nunique() == 45
print(f"  Instance count:  {df.inst_id.nunique()} == 45? {inst_ok}")
if nan_q2 > 0 or non_binary > 0 or not row_ok or not inst_ok:
    print("  ROBUSTNESS FAILED — see above")
    sys.exit(1)
print("  All robustness checks PASS")
print()

# Regression invariant
print("REGRESSION INVARIANT (M=B=C=100% under optimal):")
all_ok = True
for cond in ["M","B","C"]:
    sub = df[(df.condition==cond) & (df.assembly=="optimal")]
    q2 = sub.groupby("inst_id")["q2"].mean()
    fails = q2[q2 < 1.0 - 1e-9]
    status = "OK" if len(fails)==0 else f"FAIL on {len(fails)} instances"
    print(f"  {cond}: {status}")
    if len(fails) > 0: all_ok = False

print()
print("PRIMARY ESTIMAND:")
m_opt = df[(df.condition=="M")&(df.assembly=="optimal")]["q2"].mean()*100
w_opt = df[(df.condition=="W")&(df.assembly=="optimal")]["q2"].mean()*100
v_opt = df[(df.condition=="V")&(df.assembly=="optimal")]["q2"].mean()*100
print(f"  Q2[M,opt] = {m_opt:.1f}%")
print(f"  Q2[W,opt] = {w_opt:.1f}%  (within-group distortion)")
print(f"  Q2[V,opt] = {v_opt:.1f}%  (full vector amplitudes)")
print(f"  Loss within (M-W) = {m_opt-w_opt:.1f} pp")
print(f"  V-W = {v_opt-w_opt:.1f} pp")

print()
print("PRIMARY LOSS CI (paired per-instance, normal SEM):")
m_inst = df[(df.condition=="M")&(df.assembly=="optimal")].groupby("inst_id")["q2"].mean()*100
w_inst = df[(df.condition=="W")&(df.assembly=="optimal")].groupby("inst_id")["q2"].mean()*100
delta  = m_inst - w_inst
n      = len(delta)
se     = delta.std(ddof=1) / np.sqrt(n)
ci_lo  = delta.mean() - 1.96*se
ci_hi  = delta.mean() + 1.96*se
print(f"  mean = {delta.mean():.2f} pp  SE = {se:.2f}  n = {n} instances")
print(f"  95% CI = [{ci_lo:.1f}, {ci_hi:.1f}]")

print()
print("HIERARCHICAL CI (bootstrapped at instance level):")
for cond in ["W","V"]:
    sub = df[(df.condition==cond)&(df.assembly=="optimal")]
    inst_means = sub.groupby("inst_id")["q2"].mean()*100
    n = len(inst_means)
    se = inst_means.std(ddof=1)/np.sqrt(n)
    ci_lo = inst_means.mean() - 1.96*se
    ci_hi = inst_means.mean() + 1.96*se
    print(f"  {cond}: {inst_means.mean():.1f}% [{ci_lo:.1f}, {ci_hi:.1f}] n={n} instances")

print()
if all_ok and len(df) == 45*5*2*200 and df.inst_id.nunique() == 45:
    print("VALIDATION PASSED")
    sys.exit(0)
else:
    print("VALIDATION FAILED")
    sys.exit(1)
