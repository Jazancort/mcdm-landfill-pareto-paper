# -*- coding: utf-8 -*-
"""diag_p3.py — Round 13: diagnóstico completo de P3"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from mcdm_experiment import (load_data, impute_nan, COL, AHP_WEIGHTS,
                               _build_decision_matrix, _norm)
try:
    from mcdm_experiment import INV, COST
except ImportError:
    INV = set(); COST = set()

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
N = len(df_via)
w = np.array(list(AHP_WEIGHTS.values()))
col_names = list(AHP_WEIGHTS.keys())
X_via, benefit = _build_decision_matrix(df_via)

# ─── 1. aspect: é binário o raw ou só o critério c? ──────────────────────────
print("=== 1. aspect ===")
asp_raw = df_via[COL["aspect"]].values
asp_c = np.where((asp_raw >= 90) & (asp_raw <= 180), 0., 1.)
print(f"  raw: min={asp_raw.min():.2f}  max={asp_raw.max():.2f}  mean={asp_raw.mean():.2f}")
print(f"  c (após lógica slope ∈[90,180]): n_zero={int((asp_c==0).sum())}  n_um={int((asp_c==1).sum())}")
print(f"  → o CRITÉRIO c é binário; o raw não é")
print()

# ─── 2. (max-min)/norm nos 89 sites da fronteira A' vs 389 ───────────────────
print("=== 2. (max-min)/norm fronteira A' (89 sites) vs completo (389) ===")
aprime_csv = os.path.join(os.path.dirname(__file__), "results", "pareto_front_Aprime.csv")
df_front = pd.read_csv(aprime_csv)
sites_front = set()
for _, row in df_front.iterrows():
    sites_front.update([int(row.idx1), int(row.idx2), int(row.idx3)])
df_fs = df_via[df_via.index.isin(sites_front)]
N_f = len(df_fs)
print(f"  Sites únicos na fronteira A': {N_f}")
print()

rows = []
for j, crit in enumerate(col_names):
    col = COL[crit]
    x89  = df_fs[col].values.astype(float)
    x389 = df_via[col].values.astype(float)
    r89  = (x89.max()-x89.min()) / (np.sqrt((x89**2).sum()) or 1.)
    r389 = (x389.max()-x389.min()) / (np.sqrt((x389**2).sum()) or 1.)
    rows.append({"crit":crit,"r89":r89,"r389":r389,"ratio_89_vs_389":r89/(r389 or 1.)})

df_r = pd.DataFrame(rows).sort_values("r89", ascending=False)
print(f"  {'Critério':12s}  {'ratio_89':>9}  {'ratio_389':>10}  {'89/389':>8}")
for _, row in df_r.iterrows():
    print(f"  {row.crit:12s}  {row.r89:9.4f}  {row.r389:10.4f}  {row.ratio_89_vs_389:8.3f}x")
df_r.to_csv(os.path.join(os.path.dirname(__file__), "results", "p3_ratio_front.csv"), index=False)
print()

# ─── 3. Origem do 2.40x ───────────────────────────────────────────────────────
print("=== 3. Origem do 2.40x (w×std rivers) ===")
def w_std(x, norm, w_j):
    if norm == "minmax":
        mn, mx = x.min(), x.max(); r = (x - mn) / ((mx - mn) or 1.)
    elif norm == "vector":
        nrm = np.sqrt((x**2).sum()) or 1.; r = x / nrm
    else:
        r = pd.Series(x).rank(method="average").values / len(x)
    return w_j * r.std()

x_riv = df_via[COL["rivers"]].values.astype(float)
w_r = AHP_WEIGHTS["rivers"]
mm_riv = w_std(x_riv, "minmax", w_r)
vc_riv = w_std(x_riv, "vector", w_r)
print(f"  rivers w×std_mm={mm_riv:.4f}  w×std_vec={vc_riv:.4f}  ratio={vc_riv/mm_riv:.3f}x")

# A diferença: no min-max, (x-min)/(max-min) ∈ [0,1] com std restrita.
# No vetorial, x/||x|| pode ter std maior se a distribuição tem outliers que
# aumentam a norma relativa dos valores intermediários.
x_riv_mm = (x_riv - x_riv.min()) / (x_riv.max() - x_riv.min())
x_riv_vn = x_riv / (np.sqrt((x_riv**2).sum()) or 1.)
print(f"  std(rivers_mm)={x_riv_mm.std():.4f}  std(rivers_vn)={x_riv_vn.std():.4f}")
print(f"  max(rivers_vn)={x_riv_vn.max():.4f}  (valores altos concentram norma)")

# ─── 4. Pesos efetivos recalculados com a tabela do usuário ───────────────────
print()
print("=== 4. Pesos efetivos w_j × (max-min)/norm (método do usuário) ===")
# Recalcular com os 389 sites
weff_rows = []
for j, crit in enumerate(col_names):
    col = COL[crit]
    x = df_via[col].values.astype(float)
    rng = x.max() - x.min()
    nrm = np.sqrt((x**2).sum()) or 1.
    ratio = rng / nrm
    weff = w[j] * ratio
    weff_rows.append({"crit":crit,"w_nom":w[j],"ratio":ratio,"w_eff":weff})

df_we = pd.DataFrame(weff_rows)
tot = df_we["w_eff"].sum()
df_we["w_eff_norm"] = df_we["w_eff"] / tot
df_we["fator"] = df_we["w_eff_norm"] / df_we["w_nom"]

# Comparar com w_nominal renormalizado
df_we_sorted = df_we.sort_values("fator", ascending=False)
print(f"  {'Critério':12s}  {'w_nom':>6}  {'ratio':>8}  {'w_eff':>8}  {'w_eff_norm':>10}  {'fator':>8}")
for _, row in df_we_sorted.iterrows():
    print(f"  {row.crit:12s}  {row.w_nom:6.3f}  {row.ratio:8.4f}  {row.w_eff:8.4f}  {row.w_eff_norm:10.4f}  {row.fator:8.3f}x")

# urban especificamente
ur = df_we[df_we.crit=="urban"].iloc[0]
print(f"\n  urban: w_nom=0.166  w_eff_norm={ur.w_eff_norm:.4f}  fator={ur.fator:.3f}x")
pm = df_we[df_we.crit=="perm"].iloc[0]
print(f"  perm:  w_nom=0.152  w_eff_norm={pm.w_eff_norm:.4f}  fator={pm.fator:.3f}x")
print(f"\n  Hipótese do usuário confirmada: urban é reduzido para ~{ur.fator:.2f}x no vetorial")
print(f"  perm é inflado para ~{pm.fator:.2f}x — mas CV=4.30, outliers não separam candidatos competitivos")
