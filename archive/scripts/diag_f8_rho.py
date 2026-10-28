# -*- coding: utf-8 -*-
"""
diag_f8_rho.py
==============
Three questions about the F8 vec normalisation:

Q1. Do the rho_j from the LIVE pipeline (1/L2(mm_norm(x))) match Tabela 2?
    Tabela 2 values come from fogo_constants.AJ_VEC.

Q2. Is X_via_raw mm-normalised (as its name suggests) or raw metres?
    Test: does min(X_via_raw[:,protected]) == 0?
    If min > 0, the values are RAW metres, and the assertion in compute_f8 is NOT a tautology.
    If min == 0, X_via_raw is mm-normalised and the assertion is trivial.

Q3. What is \\TVvecNumerical = 0.311?
    Compute TV from the live rho_j and compare to 0.315 (Tab2) and 0.311 (macro).
    Identify the column that causes the discrepancy if any.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

from mcdm_experiment import load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix
from fogo_constants import AJ_VEC, CRITERION_NAMES, W, TV_VEC

TABLE2 = dict(zip(CRITERION_NAMES, AJ_VEC))
AHP_W  = dict(zip(CRITERION_NAMES, W))
col_names = list(AHP_WEIGHTS.keys())

print("Loading data...")
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL['protected']] > 0].copy()
N = len(df_via)

# ── Q2: Is X_via_raw mm-normalised or raw? ────────────────────────────────────
X_via_raw, benefit_flags = _build_decision_matrix(df_via)
prot_idx = col_names.index('protected')
perm_idx = col_names.index('perm')
print(f"\nQ2: Is X_via_raw mm-normalised?")
print(f"  min(X_via_raw[:,protected]) = {X_via_raw[:, prot_idx].min():.6f}  "
      f"(0 => mm-normed, >0 => raw metres)")
print(f"  min(X_via_raw[:,perm])      = {X_via_raw[:, perm_idx].min():.6f}  "
      f"(expected 0 since 350/389 zeros)")

# Conclusion from Q2
is_mm = abs(X_via_raw[:, prot_idx].min()) < 1e-9
print(f"  X_via_raw is {'mm-normalised' if is_mm else 'RAW (not mm)'}")
if not is_mm:
    print("  WARNING: If X_via_raw is raw, then L2_raw != L2_via and the assertion")
    print("  in compute_f8 is NOT a tautology.  Need separate investigation.")

# ── Q1: rho_j from live pipeline ──────────────────────────────────────────────
norms_via = np.maximum(np.sqrt((X_via_raw**2).sum(0)), 1e-12)
rho_live  = 1.0 / norms_via

print(f"\nQ1: rho_j from live pipeline vs Tabela 2")
print(f"{'Criterion':12s}  {'rho_live':>10}  {'Tab2':>8}  {'diff':>10}  Status")
print("-" * 62)
all_ok = True
for j, k in enumerate(col_names):
    tab2_val = TABLE2.get(k, None)
    if tab2_val is None:
        print(f"  {k:12s}: NOT in TABLE2")
        continue
    diff = rho_live[j] - tab2_val
    ok   = abs(diff) < 5e-4   # 3dp agreement
    status = "OK" if ok else "DIFERE"
    if not ok:
        all_ok = False
    print(f"  {k:12s}  {rho_live[j]:.6f}   {tab2_val:.3f}   {diff:+.6f}  {status}")

print(f"\n  All match to 3dp: {'YES' if all_ok else 'NO'}")

# ── Q3: TV from live rho_j ────────────────────────────────────────────────────
print(f"\nQ3: TV from live rho_j")
# TV = (1/2) * sum_j |w_eff_j - w_j| where w_eff_j = w_j * rho_j / S, S = sum(w_k * rho_k)
S = sum(AHP_W[k] * rho_live[j] for j, k in enumerate(col_names))
tv_live = 0.5 * sum(abs(AHP_W[k] * rho_live[j] / S - AHP_W[k]) for j, k in enumerate(col_names))
print(f"  TV(live rho_j)  = {tv_live:.6f}")
print(f"  TV_VEC (Tab2)   = {TV_VEC:.6f}")
print(f"  TVvecNumerical  = 0.311000  (macro in macros.tex)")
print(f"  TV(Tab2 rho_j)  = ", end="")
S2 = sum(AHP_W[k] * AJ_VEC[j] for j, k in enumerate(col_names))
tv_tab2 = 0.5 * sum(abs(AHP_W[k] * AJ_VEC[j] / S2 - AHP_W[k]) for j, k in enumerate(col_names))
print(f"{tv_tab2:.6f}")

# per-column breakdown of TV contribution
print(f"\n  TV breakdown by criterion:")
print(f"  {'Criterion':12s}  {'w_eff_live':>12}  {'w_AHP':>8}  {'|diff|':>10}")
for j, k in enumerate(col_names):
    w_eff = AHP_W[k] * rho_live[j] / S
    print(f"    {k:12s}  {w_eff:.6f}      {AHP_W[k]:.4f}    {abs(w_eff - AHP_W[k]):.6f}")

# Identify which criterion explains the gap TV_live vs TV_VEC
if abs(tv_live - TV_VEC) > 0.001:
    print(f"\n  Gap TV_live vs TV_VEC = {tv_live - TV_VEC:+.6f}")
    print("  Per-criterion contribution to gap:")
    S2t = sum(AHP_W[k] * AJ_VEC[j] for j, k in enumerate(col_names))
    for j, k in enumerate(col_names):
        w_eff_live = AHP_W[k] * rho_live[j] / S
        w_eff_tab2 = AHP_W[k] * AJ_VEC[j] / S2t
        contrib = abs(w_eff_live - AHP_W[k]) - abs(w_eff_tab2 - AHP_W[k])
        if abs(contrib) > 0.0005:
            print(f"    {k:12s}: delta_tv = {contrib:+.6f}  "
                  f"(rho_live={rho_live[j]:.6f} vs tab2={AJ_VEC[j]:.3f})")
else:
    print(f"  TV matches Tab2 to within 0.001.")

print("\nDone.")
