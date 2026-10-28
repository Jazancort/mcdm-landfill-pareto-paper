# -*- coding: utf-8 -*-
"""
diag_tab2_corrected.py
======================
Computes the CORRECTED Tabela 2 rho_j values using rho_shift = 1/L2(mm_norm(x)).
Also computes TV_vec, TV_B, TV_W, m_eff, L2_vec from corrected rho_j.

These are the values that should replace the current Tab2 entries and
the macros TVvec, TVvecNumerical, TVBvec, TVWvec, meff, L2vec.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

from mcdm_experiment import load_data, impute_nan, COL, AHP_WEIGHTS
from fogo_constants import OBJ_GROUPS, CRITERION_NAMES, W as W_raw, AJ_VEC

df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL['protected']] > 0].copy()

col_names = list(AHP_WEIGHTS.keys())

def mm_norm(x):
    lo, hi = x.min(), x.max()
    d = hi - lo
    return (x - lo) / d if d > 0 else np.full(len(x), 0.5)

# ── rho_shift (code/implementation formula) ────────────────────────────────
rho = np.zeros(len(col_names))
for j, k in enumerate(col_names):
    x = df_via[COL[k]].to_numpy(float)
    c = ((x >= 90) & (x <= 180)).astype(float) if k == 'aspect' else mm_norm(x)
    rho[j] = 1.0 / max(np.linalg.norm(c), 1e-12)

W = W_raw / W_raw.sum()
S = float((W * rho).sum())
w_eff = W * rho / S
TV_vec = float(0.5 * np.abs(w_eff - W).sum())

# ── TV_B (between-group): replace each rho_j by the weighted group average ─
group_avg_rho = np.zeros(len(col_names))
for g in OBJ_GROUPS:
    wg   = W[g]
    gavg = float((wg * rho[g]).sum() / wg.sum())
    for idx in g:
        group_avg_rho[idx] = gavg

S_B = float((W * group_avg_rho).sum())
w_eff_B = W * group_avg_rho / S_B
TV_B = float(0.5 * np.abs(w_eff_B - W).sum())
TV_W = TV_vec - TV_B

# ── m_eff and L2 ────────────────────────────────────────────────────────────
m_eff  = float(1.0 / (w_eff**2).sum())
L2_vec = float(np.sqrt(2.0) * TV_vec)

# ── Print comparison ─────────────────────────────────────────────────────────

# ── m_eff and L2 from eq:meff and eq:l2fact (main.tex lines 1749-1767) ─────
# delta_j = w_eff_j - w_j
# m_eff = ||delta||_1^2 / ||delta||_2^2  (participation ratio)
# L2    = ||delta||_2 = 2*TV / sqrt(m_eff)
delta   = w_eff - W
delta_L1 = float(np.abs(delta).sum())      # = 2*TV_vec by definition
delta_L2_sq = float((delta**2).sum())
m_eff   = float(delta_L1**2 / delta_L2_sq)
L2_vec  = float(np.sqrt(delta_L2_sq))

print("=== Corrected Tabela 2 rho_j ===")
print(f"{'Criterion':12s}  {'rho_shift':>10}  {'rho_Tab2':>9}  {'Delta':>8}  {'Status':>8}  {'w_eff/w':>8}")
print("-" * 70)
for j, k in enumerate(col_names):
    tab2  = AJ_VEC[j]
    d     = rho[j] - tab2
    status = "OK" if abs(d) < 5e-4 else "UPDATE"
    ratio  = w_eff[j] / W[j]
    print(f"  {k:12s}  {rho[j]:10.4f}  {tab2:9.3f}  {d:+8.4f}  {status:>8}  {ratio:8.3f}")

print()
print("Derived quantities (corrected):")
print(f"  TV_vec  = {TV_vec:.6f}   was 0.314600 (TVvec=0.315)")
print(f"  TV_B    = {TV_B:.6f}   was 0.248900 (TVBvec=0.249)")
print(f"  TV_W    = NEEDS SEPARATE COMPUTATION (= TV of cell-W amplitude, not TV-TV_B)")
print(f"            TV_W=0.1986 was from E1 cell W score matrix, unchanged by rho_j fix")
print(f"  m_eff   = {m_eff:.4f}     was 4.0486   (meff=4.05)")
print(f"  L2_vec  = {L2_vec:.6f}   was 0.3127   (LtwoVec=0.313)")
print(f"  S       = {S:.6f}")
print(f"  perm w_eff/w = {w_eff[0]/W[0]:.4f}   was 2.88")
print()
print("Verification: L2_vec vs 2*TV/sqrt(m_eff) =", f"{2*TV_vec/m_eff**0.5:.6f}")

# ── Tab2 rows to update ───────────────────────────────────────────────────────
print()
print("=== Updated Tab2 rows (rho_j column only) ===")
for j, k in enumerate(col_names):
    tab2 = AJ_VEC[j]
    if abs(rho[j] - tab2) > 5e-4:
        print(f"  {k}: {tab2:.3f} -> {round(rho[j], 3):.3f}")

