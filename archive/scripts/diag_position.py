# -*- coding: utf-8 -*-
"""diag_position.py — Posicao dos trios na fronteira A + importancia w_j*std(r_j)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix
)

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
via_global = df_via.index.values

ideal = np.array([par.Cost.min(), par.Impact.min(), par.Safety.max()])
nadir = np.array([par.Cost.max(), par.Impact.max(), par.Safety.min()])
span  = nadir - ideal

print("Fronteira A ideal/nadir:")
print(f"  Ideal: Cost={ideal[0]:.4f} Impact={ideal[1]:.4f} Safety={ideal[2]:.4f}")
print(f"  Nadir: Cost={nadir[0]:.4f} Impact={nadir[1]:.4f} Safety={nadir[2]:.4f}")

CANONICAL = [
    ("SAW greedy",        0.1273, 0.5963, 0.6207),
    ("SAW optimal",       0.0811, 0.5568, 0.6170),
    ("TOPSIS-VN greedy",  0.1113, 0.5669, 0.5358),
    ("TOPSIS-VN optimal", 0.0865, 0.5955, 0.5715),
    ("TOPSIS-MM greedy",  0.1104, 0.6712, 0.6883),
    ("VIKOR greedy",      0.1190, 0.5819, 0.5879),
    ("PROMETHEE greedy",  0.0447, 0.5900, 0.4852),
    ("BCS_IEEE ref",      0.0811, 0.5568, 0.6170),
]

print("\nPosicao relativa na fronteira A (0=ideal, 1=nadir):")
print(f"  {'Label':22s}  {'rC':>5}  {'rI':>5}  {'rS':>5}  Regiao")
for label, f1, f2, f3 in CANONICAL:
    r1 = (f1 - ideal[0]) / (span[0] or 1)
    r2 = (f2 - ideal[1]) / (span[1] or 1)
    r3 = (ideal[2] - f3) / (span[2] or 1)
    dist = (r1**2 + r2**2 + r3**2)**0.5
    if r1 < 0.25:
        reg = "extremo baixo custo"
    elif r3 < 0.25:
        reg = "extremo alta seguranca"
    elif dist < 0.4:
        reg = "compromisso"
    else:
        reg = "intermediario"
    print(f"  {label:22s}  {r1:5.3f}  {r2:5.3f}  {r3:5.3f}  {reg}")

# Importancia w_j * std(r_j)
print("\nImportancia dos criterios: w_j * std(r_j) normalizado:")
X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b:
        X_adj[:, j] = 1.0 - X_via[:, j]

w = np.array(list(AHP_WEIGHTS.values()))
col_names = list(AHP_WEIGHTS.keys())
std_r = X_adj.std(0)
imp   = w * std_r
imp_n = imp / imp.sum()

print(f"  {'Criterio':12s}  {'w':>6}  {'std_r':>7}  {'w*std_r':>8}  {'norm':>6}")
for j, k in enumerate(col_names):
    print(f"  {k:12s}  {w[j]:6.3f}  {std_r[j]:7.4f}  {imp[j]:8.4f}  {imp_n[j]:6.4f}")

print("\n  perm  eff_norm:", f"{imp_n[0]:.4f}  (w_nom={w[0]:.3f})")
print("  urban eff_norm:", f"{imp_n[8]:.4f}  (w_nom={w[8]:.3f})")
print(f"  urban/perm ratio: {imp_n[8]/imp_n[0]:.2f}x")
