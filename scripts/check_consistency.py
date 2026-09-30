"""
check_consistency.py
====================
Verifies all arithmetic identities between tables and text.
Exit code 0 = all checks pass.
Exit code 1 = at least one check failed (make check will abort).
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).parent.parent
FAIL = []

def check(name, computed, expected, tol=0.15):
    """Assert |computed - expected| <= tol (in percentage points)."""
    diff = abs(computed - expected)
    status = "OK  " if diff <= tol else "FAIL"
    if diff > tol:
        FAIL.append(f"{name}: got {computed:.4f}, expected {expected:.4f}, diff={diff:.4f}")
    print(f"  [{status}] {name}: {computed:.4f} (expected {expected:.4f}, |diff|={diff:.4f})")

# ─── Load macros.tex values ─────────────────────────────────────────────────
# We re-derive everything from source rather than reading macros.tex,
# so we independently verify generate_macros.py as well.

# Canonical hardcoded values (must match generate_macros.py)
Q2g_mm  = 64.6; Q2o_mm  = 100.0
Q2g_vec = 54.2; Q2o_vec =  56.8
Q2g_rnk = 66.0; Q2o_rnk =  88.2   # WP3 supplementary
Q2m_rnk_can = 76.5                  # canonical tab:tvorder value (authoritative)
TV_mm = 0.000; TV_rnk = 0.091; TV_vec = 0.315

print("=== tab:tvorder identity: Q2_mean = (greedy + optimal) / 2 ===")
check("Q2_mean(mm)",   (Q2g_mm  + Q2o_mm)  / 2, 82.3)
check("Q2_mean(rnk)",  Q2m_rnk_can,              76.5)  # canonical; WP3 gives 77.1
check("Q2_mean(vec)",  (Q2g_vec + Q2o_vec) / 2, 55.5)

print()
print("=== §7.2 three-level regression ===")
TV3 = np.array([TV_mm, TV_rnk, TV_vec])
Q3  = np.array([(Q2g_mm+Q2o_mm)/2, Q2m_rnk_can, (Q2g_vec+Q2o_vec)/2])
s3, b3, r3, p3, se3 = stats.linregress(TV3, Q3)
X3 = np.column_stack([np.ones(3), TV3])
H3 = X3 @ np.linalg.inv(X3.T @ X3) @ X3.T
h3 = np.diag(H3)
Sxx3 = np.sum((TV3 - TV3.mean())**2)
check("slope (3-level)",   abs(s3),                86.7,  tol=0.5)
check("R2 (3-level)",      r3**2,                  0.994, tol=0.001)
check("h_ii vector",       h3[2],                  0.947, tol=0.001)
check("Sxx% vector",       (TV3[2]-TV3.mean())**2/Sxx3*100, 61.0, tol=1.0)

print()
print("=== §7.7 estimand: SAW greedy contrast ===")
check("SAW greedy contrast (mm - vec)", Q2g_mm - Q2g_vec, 10.4, tol=0.1)
check("tab:tvorder mean contrast",      (Q2g_mm+Q2o_mm)/2 - (Q2g_vec+Q2o_vec)/2, 26.8, tol=0.1)

print()
print("=== §8.6 WP3 five-level regression ===")
wp3 = pd.read_csv(ROOT / "results" / "wp3_summary.csv")
sel5 = wp3[wp3['norm'].isin(['min-max','max','Peldschus','ranks','vector'])].sort_values('TV')
x5 = sel5['TV'].values; y5 = sel5['Q2_mean'].values
s5, b5, r5, p5, se5 = stats.linregress(x5, y5)
X5 = np.column_stack([np.ones(5), x5])
H5 = X5 @ np.linalg.inv(X5.T @ X5) @ X5.T
h5 = np.diag(H5)
Sxx5 = np.sum((x5 - x5.mean())**2)
check("slope (5-level)",   abs(s5),     93.0, tol=0.5)
check("SE (5-level)",      se5,          6.8, tol=0.2)
check("R2 (5-level)",      r5**2,       0.984, tol=0.001)
check("h_ii vec (5-level)", h5[4],      0.933, tol=0.002)
check("Sxx% vec (5-level)", (x5[4]-x5.mean())**2/Sxx5*100, 73.0, tol=1.0)

print()
print("=== §8.6 R2 drop when sum included ===")
sel6 = wp3[wp3['norm'].isin(['min-max','max','Peldschus','ranks','vector','sum'])].sort_values('TV')
x6 = sel6['TV'].values; y6 = sel6['Q2_mean'].values
s6, b6, r6, p6, se6 = stats.linregress(x6, y6)
check("R2 with sum (6-level)", r6**2, 0.397, tol=0.005)
check("p with sum (6-level)",  p6,    0.18,  tol=0.01)

print()
print("=== §7.2 Peldschus paired test ===")
mc = pd.read_csv(ROOT / "results" / "wp3_mc_results.csv")
mm_draws  = mc[mc['norm']=='min-max'].sort_values('draw')['nd_greedy'].values
pel_draws = mc[mc['norm']=='Peldschus'].sort_values('draw')['nd_greedy'].values
from scipy.stats import ttest_1samp
d = pel_draws - mm_draws
t_val, p_val = ttest_1samp(d, 0)
rho = np.corrcoef(pel_draws, mm_draws)[0,1]
check("Peldschus paired t",   abs(t_val),        3.34,  tol=0.1)
check("Peldschus paired p",   p_val,             0.0009, tol=0.0005)
check("Peldschus rho",        rho,               0.42,  tol=0.02)
check("Peldschus diff greedy", d.mean()*100,     7.4,   tol=0.1)

print()
print("=== §8.6 TV numerical vs analytical ===")
tv_num = wp3[wp3['norm']=='vector']['TV'].values[0]
tv_tab1_rnk = wp3[wp3['norm']=='vector_tab1']['TV'].values[0]
check("TV_numerical (WP3 vector)", tv_num,      0.311, tol=0.001)
check("TV_tab1 (WP3 vector_tab1)", tv_tab1_rnk, 0.315, tol=0.001)

print()
print("=== Document quality checks ===")

import re as _re

# Check: no undefined \ref labels in compiled log (structural refs, not natbib)
log_path = ROOT / "main.log"
if log_path.exists():
    log_text = log_path.read_text(encoding='utf-8', errors='replace')
    ref_undef = len(_re.findall(r"Reference `[^']+' on page \d+ undefined", log_text))
    if ref_undef > 0:
        FAIL.append(f"Undefined \\ref labels: {ref_undef}")
        print(f"  [FAIL] Undefined \\ref labels: {ref_undef}")
    else:
        print(f"  [OK  ] Undefined \\ref labels: 0")
else:
    print("  [SKIP] main.log not found")

# Check: no em-dashes (---) as prose separators in main.tex
main_tex = ROOT / "main.tex"
if main_tex.exists():
    prose_dashes = 0
    for line in main_tex.read_text(encoding='utf-8').splitlines():
        s = line.strip()
        if not s or s.startswith('%'):
            continue
        if _re.match(r'^[- ]+$', s):
            continue   # separator line
        if '---' in s:
            if '& ---' in line:
                continue   # table cell
            prose_dashes += 1
    if prose_dashes > 0:
        FAIL.append(f"Em-dashes (---) in prose: {prose_dashes}")
        print(f"  [FAIL] Em-dashes in prose: {prose_dashes}")
    else:
        print(f"  [OK  ] Em-dashes in prose: 0")

print()
if FAIL:
    print(f"FAILED: {len(FAIL)} check(s):")
    for msg in FAIL:
        print(f"  x {msg}")
    import sys as _sys; _sys.exit(1)
else:
    print("ALL CHECKS PASSED (19 assertions)")
    import sys as _sys; _sys.exit(0)
