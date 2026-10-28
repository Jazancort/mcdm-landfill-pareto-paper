# -*- coding: utf-8 -*-
"""
check_a1_amplitudes.py — A1: Verificar qual X usa a normalizacao vector.

Questao: norms_via = sqrt((X_via**2).sum(0)) usa X_via que ja e min-max.
         rho_j = (max-min)/||x||_2 — a que "x" se aplica? ao bruto ou ao mm?

Para criterios com min_raw=0 (perm) os dois dao o mesmo.
Para criterios com min_raw>0 (slope, wells, urban...) podem diferir.

Output: tabela com rho_j_raw, rho_j_mm, ratio, e os valores do artigo (Tabela 2).
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault(
    "MCDM_DATA_DIR",
    "G:\\Faculdade\\Estudo\\Doutorado\\2025.1\\"
    "Otimiza\u00e7\u00e3o Bioinspirada\\"
    "Tentativa de dados via GIS"
)
import numpy as np
import pandas as pd

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS,
    _build_decision_matrix, _norm,
)

df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]] > 0].copy()
N = len(df_via)
print(f"N sites: {N}")

# X_via: already min-max normalised (output of _build_decision_matrix)
X_mm, benefit = _build_decision_matrix(df_via)

# Raw data columns (before any normalisation)
col_names = list(AHP_WEIGHTS.keys())
w_ahp     = np.array(list(AHP_WEIGHTS.values()))

rows = []
for j, crit in enumerate(col_names):
    x_raw = df_via[COL[crit]].values.astype(float)
    x_mm  = X_mm[:, j]

    # rho from RAW data (paper formula if x = raw)
    rmin_r, rmax_r = x_raw.min(), x_raw.max()
    norm_r  = np.sqrt((x_raw**2).sum())
    rho_raw = (rmax_r - rmin_r) / norm_r if norm_r > 0 else 0.0

    # rho from MIN-MAX data (what the code actually computes)
    rmin_m, rmax_m = x_mm.min(), x_mm.max()
    norm_m  = np.sqrt((x_mm**2).sum())
    rho_mm  = (rmax_m - rmin_m) / norm_m if norm_m > 0 else 0.0

    # norms_via as computed in scoring.py: ||X_via||_2 per column
    norms_via_j = np.sqrt((x_mm**2).sum())  # same as norm_m

    # effective weight factor = rho / mean(rho), where mean weighted by w_ahp
    A_j_raw = rho_raw
    A_j_mm  = rho_mm

    rows.append({
        "crit":    crit,
        "w_ahp":   round(w_ahp[j], 3),
        "benefit": bool(benefit[j]),
        "min_raw": round(rmin_r, 4),
        "max_raw": round(rmax_r, 4),
        "rho_raw": round(rho_raw, 4),
        "rho_mm":  round(rho_mm, 4),
        "diff_pct": round(abs(rho_raw - rho_mm) / rho_raw * 100, 1) if rho_raw > 0 else 0.0,
    })

df_out = pd.DataFrame(rows)

# Compute w_eff = w * rho / sum(w * rho) for both
weff_raw_unnorm = w_ahp * df_out.rho_raw.values
weff_mm_unnorm  = w_ahp * df_out.rho_mm.values
weff_raw = weff_raw_unnorm / weff_raw_unnorm.sum()
weff_mm  = weff_mm_unnorm  / weff_mm_unnorm.sum()
df_out["weff_raw"] = np.round(weff_raw, 4)
df_out["weff_mm"]  = np.round(weff_mm,  4)
df_out["factor_raw"] = np.round(weff_raw / w_ahp, 3)
df_out["factor_mm"]  = np.round(weff_mm  / w_ahp, 3)

print("\n=== A1: rho_j from RAW vs MIN-MAX data ===")
print(df_out[["crit","w_ahp","min_raw","rho_raw","rho_mm","diff_pct","factor_raw","factor_mm"]].to_string(index=False))

print("\n=== TV_W and TV_B (vector normalisation) ===")
# TV = 0.5 * sum |w_j_eff - w_j|
tv_raw = 0.5 * np.abs(weff_raw - w_ahp).sum()
tv_mm  = 0.5 * np.abs(weff_mm  - w_ahp).sum()
print(f"  TV (from raw):    {tv_raw:.4f}")
print(f"  TV (from mm):     {tv_mm:.4f}")
print(f"  Paper Table 2:    0.315 (TVvec)")

print("\n=== perm amplitude ===")
perm_row = df_out[df_out.crit=="perm"].iloc[0]
print(f"  rho_raw = {perm_row.rho_raw:.4f}  factor = {perm_row.factor_raw:.3f}x")
print(f"  rho_mm  = {perm_row.rho_mm:.4f}   factor = {perm_row.factor_mm:.3f}x")
print(f"  Paper: 2.88x")

print("\n=== urban amplitude ===")
urban_row = df_out[df_out.crit=="urban"].iloc[0]
print(f"  rho_raw = {urban_row.rho_raw:.4f}  factor = {urban_row.factor_raw:.3f}x")
print(f"  rho_mm  = {urban_row.rho_mm:.4f}   factor = {urban_row.factor_mm:.3f}x")
print(f"  Paper: 0.53x")

# Conclusion
print("\n=== CONCLUSAO A1 ===")
max_diff = df_out.diff_pct.max()
print(f"  Diferenca maxima rho_raw vs rho_mm: {max_diff:.1f}%")
if max_diff < 1.0:
    print("  Valores praticalmente identicos — a equacao do artigo e o codigo sao consistentes.")
else:
    crit_max = df_out.loc[df_out.diff_pct.idxmax(), "crit"]
    print(f"  DIVERGENCIA em {crit_max} ({max_diff:.1f}%). Verificar Tabela 2 e Eq. (9).")
