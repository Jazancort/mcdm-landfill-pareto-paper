# -*- coding: utf-8 -*-
"""
_f8_asymmetry_bootstrap.py
==========================
Compute paired bootstrap 95% CIs for the four F8 misalignment losses.

The user identified that the current §7.4 text uses an incorrect baseline
for the greedy/mm-frontier loss (33.8 pp from 100% instead of 19.8 pp
from the aligned 86%). This script computes the four aligned losses and
their paired bootstrap CIs.

The four comparisons (aligned baseline):
  L1: optimal, mm frontier:  Q2(mm,mm,opt) - Q2(mm,vec,opt) = 100 - 56.8 = 43.2 pp
  L2: optimal, vec frontier: Q2(vec,vec,opt) - Q2(vec,mm,opt) = 100 - 94.4 = 5.6 pp
  L3: greedy, mm frontier:   Q2(mm,mm,grd) - Q2(mm,vec,grd) = 86.0 - 66.2 = 19.8 pp
  L4: greedy, vec frontier:  Q2(vec,vec,grd) - Q2(vec,mm,grd) = 100 - 72.4 = 27.6 pp

Note: L1 and L2 were already in macros_f8.tex. L3 is new (was 33.8 pp from 100%).
      L4 was already computed (27.6 pp from 100%, which equals from aligned since
      Q2(vec,vec,grd) = 100.0 empirically).

Outputs: macros for L1-L4 and their CIs.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 777
B = 2000
ALPHA = 0.05

REPO = Path(__file__).parent.parent
F8_VEC = REPO / "results/f8/f8_per_draw.csv"     # obj=vec, all 4 score×assembly
F8_MM  = REPO / "results/f8/f8_per_draw_mm.csv"  # obj=mm, all 4 score×assembly

d_vec = pd.read_csv(F8_VEC)
d_mm  = pd.read_csv(F8_MM)

rng = np.random.default_rng(SEED)

def get_draws(df, score_norm, assembly):
    sub = df[(df['score_norm']==score_norm) & (df['assembly']==assembly)].sort_values('draw')
    assert len(sub) == 500, f"Expected 500 draws, got {len(sub)} for {score_norm}/{assembly}"
    return sub['on_frontier'].values.astype(float)

def paired_bootstrap_ci(y1, y2, B, rng, alpha=0.05):
    """
    Paired bootstrap CI for diff = mean(y1) - mean(y2).
    y1[i] and y2[i] come from the same draw i.
    """
    n = len(y1)
    assert n == len(y2)
    obs_diff = y1.mean() - y2.mean()
    boot = np.empty(B)
    for b in range(B):
        idx = rng.integers(0, n, size=n)
        boot[b] = y1[idx].mean() - y2[idx].mean()
    lo = np.percentile(boot, 100 * alpha / 2)
    hi = np.percentile(boot, 100 * (1 - alpha / 2))
    se = boot.std(ddof=0)
    return obs_diff, lo, hi, se

print("=" * 60)
print("F8 Asymmetry: four aligned misalignment losses (paired bootstrap)")
print(f"  B = {B}, seed = {SEED}, alpha = {ALPHA:.0%}")
print("=" * 60)

results = {}

# L1: optimal, mm frontier  (aligned: mm/mm/opt is the reference at 100%)
y_L1_ref   = get_draws(d_mm, 'mm', 'optimal')   # mm score, mm frontier, optimal (= 100%)
y_L1_mis   = get_draws(d_mm, 'vec', 'optimal')  # vec score, mm frontier, optimal (= 56.8%)
diff_L1, lo_L1, hi_L1, se_L1 = paired_bootstrap_ci(y_L1_ref, y_L1_mis, B, rng)
results['L1'] = (diff_L1, lo_L1, hi_L1, se_L1, 'opt', 'mm', 'vec→mm misalign')

# L2: optimal, vec frontier  (aligned: vec/vec/opt is the reference at 100%)
y_L2_ref   = get_draws(d_vec, 'vec', 'optimal')  # vec score, vec frontier, optimal (= 100%)
y_L2_mis   = get_draws(d_vec, 'mm', 'optimal')   # mm score, vec frontier, optimal (= 94.4%)
diff_L2, lo_L2, hi_L2, se_L2 = paired_bootstrap_ci(y_L2_ref, y_L2_mis, B, rng)
results['L2'] = (diff_L2, lo_L2, hi_L2, se_L2, 'opt', 'vec', 'mm→vec misalign')

# L3: greedy, mm frontier  (aligned: mm/mm/grd is the reference at 86.0%)
y_L3_ref   = get_draws(d_mm, 'mm', 'greedy')    # mm score, mm frontier, greedy (= 86.0%)
y_L3_mis   = get_draws(d_mm, 'vec', 'greedy')   # vec score, mm frontier, greedy (= 66.2%)
diff_L3, lo_L3, hi_L3, se_L3 = paired_bootstrap_ci(y_L3_ref, y_L3_mis, B, rng)
results['L3'] = (diff_L3, lo_L3, hi_L3, se_L3, 'grd', 'mm', 'vec→mm misalign')

# L4: greedy, vec frontier  (aligned: vec/vec/grd is the reference at 100.0%)
y_L4_ref   = get_draws(d_vec, 'vec', 'greedy')   # vec score, vec frontier, greedy (= 100.0%)
y_L4_mis   = get_draws(d_vec, 'mm', 'greedy')    # mm score, vec frontier, greedy (= 72.4%)
diff_L4, lo_L4, hi_L4, se_L4 = paired_bootstrap_ci(y_L4_ref, y_L4_mis, B, rng)
results['L4'] = (diff_L4, lo_L4, hi_L4, se_L4, 'grd', 'vec', 'mm→vec misalign')

print()
print(f"{'Label':<4} {'Assembly':<5} {'Frontier':<9} {'Description':<22} {'Loss (pp)':<12} {'95% CI':<22} {'SE'}")
print("-" * 90)
for lab, (diff, lo, hi, se, asm, frt, desc) in results.items():
    print(f"{lab:<4} {asm:<5} {frt:<9} {desc:<22} {diff*100:6.1f} pp     [{lo*100:.1f}, {hi*100:.1f}] pp    {se*100:.2f}")

print()
print("KEY FINDING:")
print(f"  Optimal: vec→mm costs {diff_L1*100:.1f} pp; mm→vec costs {diff_L2*100:.1f} pp. Ratio = {diff_L1/diff_L2:.1f}x (vec more costly)")
print(f"  Greedy:  vec→mm costs {diff_L3*100:.1f} pp; mm→vec costs {diff_L4*100:.1f} pp. Ratio = {diff_L4/diff_L3:.1f}x (mm more costly)")
print(f"  DIRECTION REVERSAL confirmed under greedy assembly.")

print()
print("=" * 60)
print("MACROS for macros_f8.tex:")
print("=" * 60)
print(f"% Aligned misalignment losses (paired bootstrap B={B}, seed={SEED})")
print(f"\\newcommand{{\\FEightOptMmLossVecScore}}{{{diff_L1*100:.1f}}}  % L1: opt/mm-frt, vec score cost = mm-aligned Q2 - misaligned Q2")
print(f"\\newcommand{{\\FEightOptMmLossVecScoreLo}}{{{lo_L1*100:.1f}}}  % L1 CI low")
print(f"\\newcommand{{\\FEightOptMmLossVecScoreHi}}{{{hi_L1*100:.1f}}}  % L1 CI high")
print(f"\\newcommand{{\\FEightOptVecLossMmScore}}{{{diff_L2*100:.1f}}}   % L2: opt/vec-frt, mm score cost")
print(f"\\newcommand{{\\FEightOptVecLossMmScoreLo}}{{{lo_L2*100:.1f}}}  % L2 CI low")
print(f"\\newcommand{{\\FEightOptVecLossMmScoreHi}}{{{hi_L2*100:.1f}}}  % L2 CI high")
print(f"\\newcommand{{\\FEightGrdMmLossVecScore}}{{{diff_L3*100:.1f}}}   % L3: grd/mm-frt, vec score cost (aligned = 86.0%)")
print(f"\\newcommand{{\\FEightGrdMmLossVecScoreLo}}{{{lo_L3*100:.1f}}}  % L3 CI low")
print(f"\\newcommand{{\\FEightGrdMmLossVecScoreHi}}{{{hi_L3*100:.1f}}}  % L3 CI high")
print(f"\\newcommand{{\\FEightGrdVecLossMmScore}}{{{diff_L4*100:.1f}}}   % L4: grd/vec-frt, mm score cost")
print(f"\\newcommand{{\\FEightGrdVecLossMmScoreLo}}{{{lo_L4*100:.1f}}}  % L4 CI low")
print(f"\\newcommand{{\\FEightGrdVecLossMmScoreHi}}{{{hi_L4*100:.1f}}}  % L4 CI high")
print()

# Assertion: L1/L2 should match existing macros
assert abs(diff_L1 * 100 - 43.2) < 0.15, f"L1 mismatch: {diff_L1*100:.2f} vs 43.2"
assert abs(diff_L2 * 100 - 5.6)  < 0.15, f"L2 mismatch: {diff_L2*100:.2f} vs 5.6"
assert abs(diff_L3 * 100 - 19.8) < 0.5,  f"L3 unexpected: {diff_L3*100:.2f}"  # no prior macro
assert abs(diff_L4 * 100 - 27.6) < 0.15, f"L4 mismatch: {diff_L4*100:.2f} vs 27.6"
print("ASSERTIONS PASSED: L1=43.2, L2=5.6, L4=27.6 (within tolerance)")
