# -*- coding: utf-8 -*-
"""
ablation_topsis.py  — Tarefa 4: Ablação do TOPSIS por critério
Troca um critério de cada vez de normalização vetorial para min-max.
Mede Jaccard@10 e gap_norm em relação ao TOPSIS-MM.

Run: uv run --with pandas --with numpy python scripts/ablation_topsis.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

from mcdm_experiment import (
    load_data, impute_nan, compute_objectives, haversine_km,
    greedy_trio, pareto_dominates, in_pareto_front,
    COL, AHP_WEIGHTS, MIN_DIST_KM, _build_decision_matrix,
)

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
via_global = df_via.index.values
N = len(df_via)
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
w = np.array(list(AHP_WEIGHTS.values()))
col_names = list(AHP_WEIGHTS.keys())

objs_via = compute_objectives(df_via, df_imp)
f1v = objs_via["f1"].values.astype(np.float32)
f2v = objs_via["f2"].values.astype(np.float32)
f3v = objs_via["f3"].values.astype(np.float32)

valid = D_via >= MIN_DIST_KM
trio_arr = []
for i in range(N):
    for j in range(i+1, N):
        if not valid[i,j]: continue
        for k in range(j+1, N):
            if not valid[i,k] or not valid[j,k]: continue
            trio_arr.append((i,j,k))
trio_arr = np.array(trio_arr, dtype=np.int32)
M = len(trio_arr)
F1 = f1v[trio_arr[:,0]]+f1v[trio_arr[:,1]]+f1v[trio_arr[:,2]]
F2 = f2v[trio_arr[:,0]]+f2v[trio_arr[:,1]]+f2v[trio_arr[:,2]]
F3 = f3v[trio_arr[:,0]]+f3v[trio_arr[:,1]]+f3v[trio_arr[:,2]]

X_via, benefit = _build_decision_matrix(df_via)

def topsis_hybrid(minmax_set):
    """
    TOPSIS com normalização híbrida: critérios em minmax_set usam min-max,
    os demais usam normalização vetorial.
    Retorna score e ranking.
    """
    X = X_via.copy()
    # Normalizar cada coluna
    R = np.zeros_like(X)
    for j in range(X.shape[1]):
        if col_names[j] in minmax_set:
            # min-max: já está em [0,1]
            R[:, j] = X[:, j]
        else:
            # vetorial
            norm_j = np.sqrt((X[:,j]**2).sum())
            R[:, j] = X[:,j] / (norm_j or 1.)
    V = R * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp = np.sqrt(((V-PIS)**2).sum(1))
    dn = np.sqrt(((V-NIS)**2).sum(1))
    d = dp+dn
    return np.where(d==0, 0.5, dn/d)

def eval_greedy(sc):
    idx = greedy_trio(sc, D_via)
    i,j,k = idx
    gids = sorted([int(via_global[i]),int(via_global[j]),int(via_global[k])])
    f1t=float(f1v[i]+f1v[j]+f1v[k]); f2t=float(f2v[i]+f2v[j]+f2v[k]); f3t=float(f3v[i]+f3v[j]+f3v[k])
    dom = bool(((F1<=f1t)&(F2<=f2t)&(F3>=f3t)&((F1<f1t)|(F2<f2t)|(F3>f3t))).any())
    if dom:
        f1r=F1.max()-F1.min(); f2r=F2.max()-F2.min(); f3r=F3.max()-F3.min()
        gn = float(max(0., np.minimum(np.minimum((f1t-F1)/(f1r or 1),(f2t-F2)/(f2r or 1)),(F3-f3t)/(f3r or 1)).max()))
    else:
        gn = 0.
    return gids, gn, dom

def jaccard10(sc_a, sc_b):
    a = set(np.argsort(-sc_a)[:10])
    b = set(np.argsort(-sc_b)[:10])
    return len(a&b)/len(a|b) if a|b else 1.

# ─── Baseline: TOPSIS-VN (todos vetorial) e TOPSIS-MM (todos min-max) ────────
sc_vn = topsis_hybrid(set())             # todos vetorial = TOPSIS-VN
sc_mm = topsis_hybrid(set(col_names))    # todos min-max  = TOPSIS-MM
gids_vn, gn_vn, dom_vn = eval_greedy(sc_vn)
gids_mm, gn_mm, dom_mm = eval_greedy(sc_mm)
jac_mm_mm = jaccard10(sc_mm, sc_mm)  # = 1.0

print("=" * 65)
print("ABLAÇÃO DO TOPSIS: troca de vetorial → min-max por critério")
print("=" * 65)
print(f"\n  Baseline TOPSIS-VN (todos vet): {gids_vn}  gap={gn_vn:.4f}  dom={'Y' if dom_vn else 'N'}")
print(f"  Baseline TOPSIS-MM (todos mm):  {gids_mm}  gap={gn_mm:.4f}  dom={'Y' if dom_mm else 'N'}")
print(f"\n  {'Critério trocado':14s}  gids               gap_norm  dom  Jac@10_vs_VN  Jac@10_vs_MM")

rows = []
for j, crit in enumerate(col_names):
    # Trocar só este critério para min-max
    sc = topsis_hybrid({crit})
    gids, gn, dom = eval_greedy(sc)
    jac_vn = jaccard10(sc, sc_vn)
    jac_mm = jaccard10(sc, sc_mm)
    delta_gap = gn_vn - gn  # positivo = troca melhorou
    print(f"  {crit:14s}  {str(gids):18s}  {gn:.4f}  {'Y' if dom else 'N'}  {jac_vn:.3f}        {jac_mm:.3f}   Δgap={delta_gap:+.4f}")
    rows.append({"criterio":crit,"w":w[j],"gids":str(gids),"gap":gn,"dom":dom,
                 "jac_vs_vn":jac_vn,"jac_vs_mm":jac_mm,"delta_gap":delta_gap})

df = pd.DataFrame(rows).sort_values("jac_vs_mm", ascending=False)
print(f"\n  Critérios ordenados por Jaccard@10 vs TOPSIS-MM (maior = mais impacto):")
print(f"  {'Critério':14s}  {'Jac@10_mm':>10}  {'Δgap':>8}")
for _, row in df.iterrows():
    print(f"  {row.criterio:14s}  {row.jac_vs_mm:10.3f}  {row.delta_gap:+8.4f}")

print(f"\n  O critério cuja troca mais aproxima o resultado do TOPSIS-MM é o mecanismo de P3.")
df.to_csv(os.path.join(os.path.dirname(__file__), "results", "ablation_topsis.csv"), index=False)
print("Resultados salvos em results/ablation_topsis.csv")
