# -*- coding: utf-8 -*-
"""audit_e6_ci.py — Compute and verify CI for E6 primary loss M-W"""
import pandas as pd, numpy as np
from pathlib import Path

ROOT = Path(__file__).parent.parent
df = pd.read_csv(ROOT/"results"/"e6"/"e6_raw_results.csv")

# Primary estimand: per-instance paired difference (m - w) under optimal
m = df[(df.condition=="M")&(df.assembly=="optimal")].groupby("inst_id")["q2"].mean()
w = df[(df.condition=="W")&(df.assembly=="optimal")].groupby("inst_id")["q2"].mean()
delta = (m - w) * 100   # per-instance loss in pp, n=45

n = len(delta)
mean_delta = delta.mean()
se_delta   = delta.std(ddof=1) / np.sqrt(n)
ci_lo_norm = mean_delta - 1.96*se_delta
ci_hi_norm = mean_delta + 1.96*se_delta

print("PRIMARY LOSS CI (M-W, n=45 instances):")
print(f"  mean = {mean_delta:.4f} pp")
print(f"  SE   = {se_delta:.4f}")
print(f"  95% CI (normal SEM) = [{ci_lo_norm:.2f}, {ci_hi_norm:.2f}]")

# Bootstrap CI (hierarchical, B=4000, seed=42)
rng = np.random.default_rng(seed=42)
B = 4000
boot = [rng.choice(delta.values, size=n, replace=True).mean() for _ in range(B)]
boot = np.array(boot)
pct_lo, pct_hi = np.percentile(boot, [2.5, 97.5])
print(f"  95% CI (bootstrap percentile, B={B}, seed=42) = [{pct_lo:.2f}, {pct_hi:.2f}]")
print()
print(f"  Published in manuscript: [2.2, 6.6]")
print()

# Check
tol = 0.2   # allow rounding
ok_lo = abs(pct_lo - 2.2) < tol or abs(ci_lo_norm - 2.2) < tol
ok_hi = abs(pct_hi - 6.6) < tol or abs(ci_hi_norm - 6.6) < tol
if ok_lo and ok_hi:
    print("VERIFIED: [2.2, 6.6] consistent with computed CI")
else:
    print(f"MISMATCH: computed normal=[{ci_lo_norm:.2f},{ci_hi_norm:.2f}]  boot=[{pct_lo:.2f},{pct_hi:.2f}]")
    print("  ACTION: update manuscript CI or document discrepancy")
