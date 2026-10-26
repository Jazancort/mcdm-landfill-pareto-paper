# -*- coding: utf-8 -*-
"""
diag_r9.py — Round 9: rSafety corrigido, w*dp nas 3 normalizações, decomposição de variância
Run: uv run --with pandas --with numpy python scripts/diag_r9.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

from mcdm_experiment import (
    load_data, impute_nan, compute_objectives, haversine_km,
    saw_scores, topsis_scores, vikor_scores, promethee2_scores,
    greedy_trio, pareto_dominates, in_pareto_front, gap_additive,
    trio_objectives_from_global,
    COL, AHP_WEIGHTS, MIN_DIST_KM, COST, INV,
    _build_decision_matrix, _norm,
)

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
via_global = df_via.index.values
N = len(df_via)
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
objs_473 = compute_objectives(df_imp, df_imp)
w = np.array(list(AHP_WEIGHTS.values()))
col_names = list(AHP_WEIGHTS.keys())

# ─── 1. rSafety corrigido ────────────────────────────────────────────────────
print("=" * 65)
print("1. POSIÇÃO DOS TRIOS NA FRONTEIRA A (rSafety CORRIGIDO)")
print("=" * 65)

ideal = np.array([par.Cost.min(), par.Impact.min(), par.Safety.max()])
nadir = np.array([par.Cost.max(), par.Impact.max(), par.Safety.min()])
span  = nadir - ideal
print(f"  Ideal: Cost={ideal[0]:.4f}  Impact={ideal[1]:.4f}  Safety={ideal[2]:.4f}")
print(f"  Nadir: Cost={nadir[0]:.4f}  Impact={nadir[1]:.4f}  Safety={nadir[2]:.4f}")

# Fórmula correta:
# rCost   = (f1 - ideal_cost)  / (nadir_cost  - ideal_cost)   [0=melhor]
# rImpact = (f2 - ideal_impact)/ (nadir_impact - ideal_impact) [0=melhor]
# rSafety = (ideal_safety - f3)/ (ideal_safety - nadir_safety) [0=melhor, f3 alta = bom]

def rel_pos(f1, f2, f3):
    rC = (f1 - ideal[0]) / (span[0] or 1)
    rI = (f2 - ideal[1]) / (span[1] or 1)
    rS = (ideal[2] - f3) / (ideal[2] - nadir[2] or 1)  # Safety: maior=melhor → 0 = ideal
    return rC, rI, rS

CANONICAL = [
    ("SAW greedy",        0.1273, 0.5963, 0.6207),
    ("SAW optimal",       0.0811, 0.5568, 0.6170),
    ("TOPSIS-VN greedy",  0.1113, 0.5669, 0.5358),
    ("TOPSIS-VN optimal", 0.0865, 0.5955, 0.5715),
    ("TOPSIS-MM greedy",  0.1104, 0.6712, 0.6883),
    ("VIKOR greedy",      0.1190, 0.5819, 0.5879),
    ("PROMETHEE greedy",  0.0447, 0.5900, 0.4852),
    ("BCS_IEEE",          0.0811, 0.5568, 0.6170),
]

print(f"\n  {'Label':22s}  {'rCost':>6}  {'rImpact':>7}  {'rSafety':>7}  Região")
rows = []
for label, f1, f2, f3 in CANONICAL:
    rC, rI, rS = rel_pos(f1, f2, f3)
    dist = (rC**2 + rI**2 + rS**2)**0.5
    if rS <= 0.10:
        reg = "extremo segurança máxima"
    elif rC <= 0.25:
        reg = "extremo baixo custo"
    elif dist < 0.45:
        reg = "compromisso central"
    else:
        reg = "intermediário"
    print(f"  {label:22s}  {rC:6.3f}  {rI:7.3f}  {rS:7.3f}  {reg}")
    rows.append({"label":label,"rCost":rC,"rImpact":rI,"rSafety":rS,"dist_ideal":dist,"region":reg})

pd.DataFrame(rows).to_csv(
    os.path.join(os.path.dirname(__file__), "results", "trio_positions.csv"), index=False)

# ─── 4. w*std(r_j) nas 3 normalizações ──────────────────────────────────────
print("\n" + "=" * 65)
print("4. w*std(r_j) NAS 3 NORMALIZAÇÕES")
print("=" * 65)

X_via, benefit = _build_decision_matrix(df_via)  # normalização sobre 389
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b:
        X_adj[:, j] = 1.0 - X_via[:, j]

# Min-max (X_adj com scores após inversão de custo)
std_mm = X_adj.std(0)
imp_mm = w * std_mm; imp_mm_n = imp_mm / imp_mm.sum()

# Vetorial: r_ij = x_ij / ||x_j||, então std(r_j) = std(x_j/||x_j||)
norms_vec = np.sqrt((X_adj**2).sum(0)); norms_vec[norms_vec == 0] = 1.0
R_vec = X_adj / norms_vec
std_vec = R_vec.std(0)
imp_vec = w * std_vec; imp_vec_n = imp_vec / imp_vec.sum()

# Postos: rank normalizado em [0,1]
R_rank = np.apply_along_axis(
    lambda c: (pd.Series(c).rank(method="average") - 1) / (N - 1), 0, X_adj
)
std_rk = R_rank.std(0)
imp_rk = w * std_rk; imp_rk_n = imp_rk / imp_rk.sum()

print(f"\n  {'Criterio':12s}  {'w':>5}  {'mm_n':>6}  {'vec_n':>6}  {'rank_n':>7}  Mudanca vec vs mm")
for j, k in enumerate(col_names):
    ratio = imp_vec_n[j] / (imp_mm_n[j] or 1e-9)
    flag  = " **INFLA**" if ratio > 2.0 else (" (reduz)" if ratio < 0.5 else "")
    print(f"  {k:12s}  {w[j]:5.3f}  {imp_mm_n[j]:6.4f}  {imp_vec_n[j]:6.4f}  {imp_rk_n[j]:7.4f}  {ratio:5.2f}x{flag}")

print(f"\n  perm:  vec/mm = {imp_vec_n[0]/imp_mm_n[0]:.2f}x  → {'P3 sustentada' if imp_vec_n[0]/imp_mm_n[0] > 2 else 'P3 NÃO sustentada'}")
print(f"  urban: vec/mm = {imp_vec_n[8]/imp_mm_n[8]:.2f}x")
j_asp = col_names.index("aspect")
print(f"  aspect (binario): mm_n={imp_mm_n[j_asp]:.4f}  rank_n={imp_rk_n[j_asp]:.4f}")
print(f"  → aspect binario tem desvio padrão máximo; min-max não é 'pesos nominais' para binárias")

pd.DataFrame({
    "criterio": col_names, "w_nom": w,
    "imp_mm_norm": imp_mm_n, "imp_vec_norm": imp_vec_n, "imp_rank_norm": imp_rk_n,
    "vec_over_mm": imp_vec_n / (imp_mm_n + 1e-12),
}).to_csv(os.path.join(os.path.dirname(__file__), "results", "effective_weights.csv"), index=False)

# ─── 3. Decomposição de variância preliminar ─────────────────────────────────
print("\n" + "=" * 65)
print("3. DECOMPOSIÇÃO PRELIMINAR DA VARIÂNCIA (Fogo, um vetor de pesos)")
print("=" * 65)

print("\n  Fator NORMALIZAÇÃO (greedy, pesos AHP fixos):")
# SAW greedy vs TOPSIS-MM greedy vs TOPSIS-VN greedy (todos greedy, agregação ≠)
# Para controlar agregação, usar apenas métodos aditivos: SAW vs TOPSIS-MM vs postos (PROMETHEE)
# e comparar gap_norm

# Pré-calcular all trios
valid = D_via >= MIN_DIST_KM
trio_arr = []
for i in range(N):
    for j in range(i+1,N):
        if not valid[i,j]: continue
        for k in range(j+1,N):
            if not valid[i,k] or not valid[j,k]: continue
            trio_arr.append((i,j,k))
trio_arr = np.array(trio_arr, dtype=np.int32)
M = len(trio_arr)

objs_via = compute_objectives(df_via, df_imp)
f1v = objs_via["f1"].values.astype(np.float32)
f2v = objs_via["f2"].values.astype(np.float32)
f3v = objs_via["f3"].values.astype(np.float32)
F1 = f1v[trio_arr[:,0]] + f1v[trio_arr[:,1]] + f1v[trio_arr[:,2]]
F2 = f2v[trio_arr[:,0]] + f2v[trio_arr[:,1]] + f2v[trio_arr[:,2]]
F3 = f3v[trio_arr[:,0]] + f3v[trio_arr[:,1]] + f3v[trio_arr[:,2]]

def gap_n(f1t, f2t, f3t):
    f1r = F1.max()-F1.min(); f2r = F2.max()-F2.min(); f3r = F3.max()-F3.min()
    if not ((F1<=f1t)&(F2<=f2t)&(F3>=f3t)&((F1<f1t)|(F2<f2t)|(F3>f3t))).any():
        return 0.0
    return float(max(0., np.minimum(np.minimum((f1t-F1)/(f1r or 1),(f2t-F2)/(f2r or 1)),(F3-f3t)/(f3r or 1)).max()))

def eval_trio_idx(ii):
    i,j,k = trio_arr[ii]
    return f1v[i]+f1v[j]+f1v[k], f2v[i]+f2v[j]+f2v[k], f3v[i]+f3v[j]+f3v[k]

# Métodos × montagem
from mcdm_experiment import topsis_scores

def topsis_vn_scores(df):
    X, benefit = _build_decision_matrix(df)
    norms = np.sqrt((X**2).sum(0)); norms[norms==0]=1.
    R = X / norms; V = R * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp = np.sqrt(((V-PIS)**2).sum(1)); dn = np.sqrt(((V-NIS)**2).sum(1))
    d = dp+dn; return np.where(d==0, 0.5, dn/d)

def topsis_mm_scores(df):
    X, benefit = _build_decision_matrix(df)
    V = X * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp = np.sqrt(((V-PIS)**2).sum(1)); dn = np.sqrt(((V-NIS)**2).sum(1))
    d = dp+dn; return np.where(d==0, 0.5, dn/d)

def argmax_trio(sc):
    st = sc[trio_arr[:,0]]+sc[trio_arr[:,1]]+sc[trio_arr[:,2]]
    return trio_arr[st.argmax()]

SCENARIOS = [
    # (nome, normalização, agregação, montagem)
    ("SAW-mm greedy",       "minmax",    "linear",    "greedy"),
    ("SAW-mm optimal",      "minmax",    "linear",    "optimal"),
    ("TOPSIS-mm greedy",    "minmax",    "dist_ideal","greedy"),
    ("TOPSIS-mm optimal",   "minmax",    "dist_ideal","optimal"),
    ("TOPSIS-vn greedy",    "vector",    "dist_ideal","greedy"),
    ("TOPSIS-vn optimal",   "vector",    "dist_ideal","optimal"),
    ("VIKOR-mm greedy",     "minmax",    "compromise","greedy"),
    ("PROMETHEE greedy",    "ranks",     "outranking","greedy"),
    ("PROMETHEE optimal",   "ranks",     "outranking","optimal"),
]

sc_saw  = saw_scores(df_via)
sc_tvn  = topsis_vn_scores(df_via)
sc_tmm  = topsis_mm_scores(df_via)
sc_vik  = vikor_scores(df_via)
sc_prom = promethee2_scores(df_via)

scores_map = {
    "SAW-mm greedy":      (sc_saw,  "greedy"),
    "SAW-mm optimal":     (sc_saw,  "optimal"),
    "TOPSIS-mm greedy":   (sc_tmm,  "greedy"),
    "TOPSIS-mm optimal":  (sc_tmm,  "optimal"),
    "TOPSIS-vn greedy":   (sc_tvn,  "greedy"),
    "TOPSIS-vn optimal":  (sc_tvn,  "optimal"),
    "VIKOR-mm greedy":    (sc_vik,  "greedy"),
    "PROMETHEE greedy":   (sc_prom, "greedy"),
    "PROMETHEE optimal":  (sc_prom, "optimal"),
}

def eval_trio_local(i, j, k):
    return f1v[i]+f1v[j]+f1v[k], f2v[i]+f2v[j]+f2v[k], f3v[i]+f3v[j]+f3v[k]

print(f"\n  {'Cenário':22s}  {'Norm':8s}  {'Agreg':10s}  {'Mont':7s}  gap_norm  dom")
decomp_rows = []
for name, norm, agg, mont in SCENARIOS:
    sc, variant = scores_map[name]
    if variant == "greedy":
        idx = greedy_trio(sc, D_via)
    else:
        idx = argmax_trio(sc)
    i, j, k = idx
    f1t, f2t, f3t = eval_trio_local(i, j, k)
    dom = bool(((F1<=f1t)&(F2<=f2t)&(F3>=f3t)&((F1<f1t)|(F2<f2t)|(F3>f3t))).any())
    gn  = gap_n(f1t, f2t, f3t)
    gids = sorted([int(via_global[i]),int(via_global[j]),int(via_global[k])])
    print(f"  {name:22s}  {norm:8s}  {agg:10s}  {mont:7s}  {gn:8.4f}  {'Y' if dom else 'N'}  {gids}")
    decomp_rows.append({"cenario":name,"norm":norm,"agregacao":agg,"montagem":mont,
                        "gap_norm":gn,"dominated":dom})

df_dec = pd.DataFrame(decomp_rows)
pd.DataFrame(df_dec).to_csv(
    os.path.join(os.path.dirname(__file__), "results", "variance_decomp_fogo.csv"), index=False)

print("\n  Média gap por fator:")
for factor, col in [("Normalização", "norm"), ("Agregação", "agregacao"), ("Montagem", "montagem")]:
    grp = df_dec.groupby(col)["gap_norm"].mean().sort_values()
    vals = "  ".join(f"{k}={v:.4f}" for k,v in grp.items())
    print(f"    {factor}: {vals}")

print("\n  Média gap por fator MONTAGEM (principal contraste):")
for mont, sub in df_dec.groupby("montagem"):
    print(f"    {mont}: mean_gap={sub.gap_norm.mean():.4f}  n={len(sub)}")
