# -*- coding: utf-8 -*-
"""
check_affinity.py — Affinity diagnostic for E1 pipeline.

For each of the 11 criteria j, regress c_site[j] on X_adj[:,j].
Expected: R²=1 exactly (perfect affine relationship), slope positive for
benefit criteria (G3) and negative for cost/impact (G1, G2 — since high
X_adj = high normalised benefit but low raw cost, so c_obj = _norm(raw, ref)
is LOW when X_adj is HIGH for cost criteria, meaning slope is NEGATIVE).

Any R² < 1 or wrong sign indicates that c_site[j] and X_adj[:,j] are not
affinely related, which would break the score/objective coherence that
Proposition 1 requires.

Also checks: for each criterion j, is X_adj[:,j] affinely related to c_obj
(the value used in compute_objs_Ap)?
"""
import os, sys
import numpy as np
from scipy.stats import linregress

if 'MCDM_DATA_DIR' not in os.environ and os.path.exists('/home/julioazancort/scratch/mcdm'):
    os.environ['MCDM_DATA_DIR'] = '/home/julioazancort/scratch/mcdm'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS,
    _build_decision_matrix, _norm, INV, COST,
    F1_CRIT, F2_CRIT, F3_CRIT,
)

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable = df_imp[COL["protected"]] > 0
df_via = df_imp[viable].copy()
N = len(df_via)

X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b:
        X_adj[:, j] = 1.0 - X_via[:, j]

col_names = list(AHP_WEIGHTS.keys())
M = len(col_names)

# Build c_site (same as check_float64.py / run_e1.py)
c_site = {}
for crit in col_names:
    col_key = COL[crit]
    x   = df_via[col_key].values.astype(np.float64)
    ref = df_via[col_key].values.astype(np.float64)
    if crit == "aspect":
        c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
    elif crit in INV:
        c = 1.0 - _norm(x, ref)
    elif crit in COST:
        c = _norm(x, ref)
    else:
        c = _norm(x, ref)
    c_site[crit] = c.astype(np.float64)

def group_of(crit):
    if crit in F1_CRIT: return "G1(cost)"
    if crit in F2_CRIT: return "G2(env)"
    return "G3(soc)"

print("=" * 80)
print("Affinity diagnostic: X_adj[:,j] ~ c_site[j] for each criterion j")
print("Expected: R²=1, sign: G1/G2 negative (cost→obj high=bad, adj high=good)")
print("=" * 80)
print(f"{'Criterion':<12} {'Group':<10} {'benefit':>8} {'slope':>10} {'intercept':>12} {'R²':>8} {'sign_ok':>8}")
print("-" * 80)

all_ok = True
for j, crit in enumerate(col_names):
    x = X_adj[:, j]       # benefit-oriented score column
    y = c_site[crit]      # objective column
    slope, intercept, r, p, se = linregress(x, y)
    r2 = r**2

    # Expected sign: for G3 (benefit), c_obj = _norm(x_raw) which increases with raw x,
    # and X_adj = _norm(x_raw) too (benefit criteria not flipped). So slope = +1.
    # For G1 (cost, not in INV): c_obj = _norm(x_raw) (lower cost = lower c),
    # X_adj = 1 - _norm(x_raw) (higher X_adj = lower cost = lower c). Slope = -1.
    # For G2 rivers/coast/protected/wells (INV): c_obj = 1-_norm(x_raw),
    # X_adj = 1 - (1-_norm) = _norm? No: INV in _build_decision_matrix inverts X_adj too.
    # Check: _build_decision_matrix for INV: benefit=True, so X_adj unchanged? Need to verify.
    is_benefit = bool(benefit[j])
    if crit in ("urban", "aero", "cult"):
        expected_sign = "+"  # G3 benefit
    else:
        expected_sign = "-"  # G1/G2 cost/impact

    r2_ok = r2 > 1 - 1e-6
    actual_sign = "+" if slope >= 0 else "-"
    sign_ok = actual_sign == expected_sign
    ok = r2_ok and sign_ok
    if not ok:
        all_ok = False

    flag = "OK" if ok else "FAIL"
    print(f"{crit:<12} {group_of(crit):<10} {str(is_benefit):>8} {slope:>10.4f} {intercept:>12.4f} {r2:>8.6f} {flag:>8}")
    if not ok:
        print(f"  >>> PROBLEM: R²={r2:.8f} (<1-1e-6={r2_ok}), sign expected={expected_sign} got={actual_sign}")

print("-" * 80)
print(f"All affine: {all_ok}")
if all_ok:
    print("All criteria satisfy R²≈1. Score/objective coherence holds.")
    print("P1 failure must be due to dominance tolerance or a sign error in F1/F2/F3.")
else:
    print("AFFINITY FAIL: score and objective columns are NOT affinely related.")
    print("This is the root cause of E1-B optimal < 100%.")
