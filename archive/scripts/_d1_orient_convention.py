# -*- coding: utf-8 -*-
"""
_d1_orient_convention.py
Compute rho_j under the "orientation-before-norm" convention for D1.

Convention A (paper, orientation AFTER norm):
    col = mm_norm(x_j)           [for all criteria]
    rho_j = range(col) / L2(col) = 1/L2(col)

Convention B (orientation BEFORE norm, only for cost criteria G1+G2):
    col_cost = 1 - mm_norm(x_j)  [cost criteria only; benefit: unchanged]
    rho_j_B  = 1 / L2(col_cost)

For G3 benefit criteria: rho_j_B = rho_j (no change).
For G1/G2 cost criteria: rho_j_B = 1/L2(1 - mm_norm(x_j)).

The script prints a LaTeX booktabs table for the supplementary.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pathlib import Path
from mcdm_experiment import load_data, impute_nan, COL, AHP_WEIGHTS
from fogo_constants import OBJ_GROUPS, CRITERION_NAMES

REPO = Path(__file__).parent.parent

# ── Load data ─────────────────────────────────────────────────────────────────
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL['protected']] > 0].copy()

crit_order = ['perm','slope','roads','rivers','aspect','coast','protected','wells',
              'urban','aero','cult']
groups = {'perm':'G1','slope':'G1','roads':'G1',
          'rivers':'G2','aspect':'G2','coast':'G2','protected':'G2','wells':'G2',
          'urban':'G3','aero':'G3','cult':'G3'}
cost = {'perm','slope','roads','rivers','aspect','coast','protected','wells'}  # G1+G2

N = len(df_via)

rows = []
for c in crit_order:
    x = df_via[COL[c]].values.astype(float)
    # min-max normalize
    lo, hi = x.min(), x.max()
    x_mm = (x - lo)/(hi - lo)

    # aspect: use binary encoding (b_asp) already encoded as 0/1
    # The data column 'aspect' in df_via is already b_asp (0/1 leeward indicator)?
    # Check: aspect values
    if c == 'aspect':
        # aspect is stored as continuous azimuth; the binarisation is applied in scoring.py
        # For this table, we use the binary encoding b_asp=1[aspect in [90,180]]
        b_asp = ((x >= 90) & (x <= 180)).astype(float)
        x_mm = b_asp  # binary encoding, already in {0,1}
        n1 = int(b_asp.sum())

    # Convention A: rho_j = 1/L2(x_mm)
    rho_A = 1.0 / np.linalg.norm(x_mm)

    # Convention B: orientation before norm (only for cost/G1+G2)
    if c in cost:
        x_b = 1.0 - x_mm   # flip for cost orientation
        rho_B = 1.0 / np.linalg.norm(x_b)
    else:
        rho_B = rho_A  # no change for G3

    rows.append((c, groups[c], rho_A, rho_B))
    print(f"  {c:10s}  {groups[c]}  rho_A={rho_A:.4f}  rho_B={rho_B:.4f}  diff={rho_B-rho_A:+.4f}")

print()
print("LaTeX table (supplementary tab:orient_conv):")
print(r"\begin{table}[!t]")
print(r"\centering")
print(r"\caption{Vector normalisation amplitudes $\rho_j$ under two orientation conventions.")
print(r"  Convention~A (paper): orientation applied after normalisation via the sign of the")
print(r"  SAW contribution; $\rho_j=1/\lVert\tilde{\mathbf{x}}_j\rVert_2$.")
print(r"  Convention~B: cost orientation $1-\tilde{x}_j$ applied before forming the norm.")
print(r"  $G_3$ criteria are identical under both conventions.")
print(r"  Differences exceeding $0.01$ are in \textbf{bold}.}")
print(r"\label{tab:orient_conv}")
print(r"\begin{tabular}{@{}llrrl@{}}")
print(r"\toprule")
print(r"Criterion & Group & $\rho_j^A$ & $\rho_j^B$ & Remark \\")
print(r"\midrule")
for (c, g, rA, rB) in rows:
    diff = abs(rB - rA)
    bold = diff > 0.01
    rA_s = f"{rA:.3f}"
    rB_s = f"{rB:.3f}"
    if bold:
        rB_s = r"\textbf{" + rB_s + r"}"
    note = ""
    if c == 'perm':
        note = r"zero-inflated (350 tied zeros)"
    elif c == 'aspect':
        note = r"binary ($n_1=94$ leeward)"
    print(rf"\textit{{{c}}} & ${g}$ & {rA_s} & {rB_s} & {note} \\")
print(r"\bottomrule")
print(r"\end{tabular}")
print(r"\end{table}")
