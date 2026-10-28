# -*- coding: utf-8 -*-
"""
shapley_norm.py — Tarefa 4: Shapley exato da normalização do TOPSIS em A'
2^11 = 2048 combinações de (vetorial | min-max) por critério.
Variáveis resposta: Jaccard@10 vs TOPSIS-MM e % não-dominados no MC em A'.

Run: uv run --with pandas --with numpy python scripts/shapley_norm.py
"""
import sys, os, itertools, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

from mcdm_experiment import (
    load_data, impute_nan, compute_objectives, haversine_km,
    greedy_trio, COL, AHP_WEIGHTS, MIN_DIST_KM, _build_decision_matrix, COST,
)
try:
    from mcdm_experiment import INV
except ImportError:
    INV = set()
from mcdm_experiment import _norm

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

print("Carregando dados...")
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
via_global = df_via.index.values
N = len(df_via)
D_via = haversine_km(df_via["latitude (degrees)"].values, df_via["longitude (degrees)"].values)
w_ahp = np.array(list(AHP_WEIGHTS.values()))
col_names = list(AHP_WEIGHTS.keys())
X_via, benefit = _build_decision_matrix(df_via)
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

# Objetivos A' fixos (pesos AHP) para %nd
def compute_objs_w(w):
    f1v=np.zeros(N,dtype=np.float32); f2v=np.zeros(N,dtype=np.float32); f3v=np.zeros(N,dtype=np.float32)
    for j,k in enumerate(col_names):
        col=COL[k]; x=df_via[col].values.astype(float)
        if k=='aspect': c=np.where((x>=90)&(x<=180),0.,1.)
        elif k in INV:  c=1.-_norm(x,x)
        elif k in COST: c=_norm(x,x)
        else:           c=_norm(x,x)
        c=c.astype(np.float32)*w[j]
        if k in ('perm','slope','roads'): f1v+=c
        elif k in ('rivers','aspect','coast','protected','wells'): f2v+=c
        else: f3v+=c
    return f1v,f2v,f3v

f1A,f2A,f3A = compute_objs_w(w_ahp)
F1A=f1A[trio_arr[:,0]]+f1A[trio_arr[:,1]]+f1A[trio_arr[:,2]]
F2A=f2A[trio_arr[:,0]]+f2A[trio_arr[:,1]]+f2A[trio_arr[:,2]]
F3A=f3A[trio_arr[:,0]]+f3A[trio_arr[:,1]]+f3A[trio_arr[:,2]]

def is_nd_A(i,j,k):
    f1t=f1A[i]+f1A[j]+f1A[k]; f2t=f2A[i]+f2A[j]+f2A[k]; f3t=f3A[i]+f3A[j]+f3A[k]
    return not bool(((F1A<=f1t)&(F2A<=f2t)&(F3A>=f3t)&((F1A<f1t)|(F2A<f2t)|(F3A>f3t))).any())

def topsis_hybrid(minmax_mask):
    """
    minmax_mask: bool array len=11. True = min-max para aquele critério, False = vetorial.
    Retorna scores (N,).
    """
    norms_vec = np.sqrt((X_via**2).sum(0)); norms_vec[norms_vec==0]=1.
    R = np.where(minmax_mask, X_via, X_via/norms_vec)
    V = R * w_ahp
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp = np.sqrt(((V-PIS)**2).sum(1)); dn = np.sqrt(((V-NIS)**2).sum(1))
    d = dp+dn; return np.where(d==0, 0.5, dn/d)

def jaccard_k(sc_a, sc_b, k=10):
    a=set(np.argsort(-sc_a)[:k]); b=set(np.argsort(-sc_b)[:k])
    return len(a&b)/len(a|b) if a|b else 1.

# Baselines
sc_mm_full = topsis_hybrid(np.ones(len(col_names), dtype=bool))
sc_vn_full = topsis_hybrid(np.zeros(len(col_names), dtype=bool))
idx_mm = greedy_trio(sc_mm_full, D_via)
idx_vn = greedy_trio(sc_vn_full, D_via)
nd_mm = is_nd_A(*idx_mm)
nd_vn = is_nd_A(*idx_vn)
print(f"TOPSIS-MM ({col_names}): gids={sorted([int(via_global[x]) for x in idx_mm])}  nd={nd_mm}")
print(f"TOPSIS-VN: gids={sorted([int(via_global[x]) for x in idx_vn])}  nd={nd_vn}")
print(f"\nCalculando 2^11={2**11} combinações...")

# ─── Avaliar todas as 2^11 combinações ────────────────────────────────────────
NC = len(col_names)
t0 = time.time()
combo_results = []
for bits in range(2**NC):
    mm_mask = np.array([(bits >> j) & 1 for j in range(NC)], dtype=bool)
    sc = topsis_hybrid(mm_mask)
    jac_mm = jaccard_k(sc, sc_mm_full, 10)
    jac_vn = jaccard_k(sc, sc_vn_full, 10)
    idx = greedy_trio(sc, D_via)
    nd = int(is_nd_A(*idx))
    n_mm = int(mm_mask.sum())
    combo_results.append({
        "bits":bits, "n_minmax":n_mm,
        "jac_vs_mm":jac_mm, "jac_vs_vn":jac_vn, "nd":nd,
        **{f"mm_{c}":int(mm_mask[j]) for j,c in enumerate(col_names)}
    })
    if bits % 256 == 0:
        print(f"  {bits}/2048 ({time.time()-t0:.1f}s)", end="\r")

print(f"\n  Concluído em {time.time()-t0:.1f}s")
df_combo = pd.DataFrame(combo_results)
df_combo.to_csv(os.path.join(RESULTS_DIR,"shapley_combos.csv"), index=False)

# ─── Shapley exato por critério ───────────────────────────────────────────────
print("\n=== Shapley da normalização ===")
# Shapley(j) = media sobre todos os subsets S que nao incluem j de
#              [v(S∪{j}) - v(S)]  * coef(|S|, N)
# Variável v: jac_vs_mm

def shapley_exact(col_idx, response="jac_vs_mm"):
    """Shapley exato para o critério col_idx usando a resposta response."""
    NC2 = NC
    total = 0.
    for bits_S in range(2**NC2):
        if (bits_S >> col_idx) & 1: continue  # j já está em S, pular
        bits_Sj = bits_S | (1 << col_idx)
        v_S  = df_combo.loc[df_combo.bits==bits_S,  response].values[0]
        v_Sj = df_combo.loc[df_combo.bits==bits_Sj, response].values[0]
        s = bin(bits_S).count("1")  # |S|
        import math
        coef = math.factorial(s)*math.factorial(NC2-s-1)/math.factorial(NC2)
        total += coef*(v_Sj - v_S)
    return total

import math
print(f"{'Critério':12s}  {'w_nom':>6}  {'Shapley(Jac@10 vs MM)':>22}  {'Shapley(nd)':>12}")
shapley_rows = []
for j, crit in enumerate(col_names):
    sh_jac = shapley_exact(j, "jac_vs_mm")
    sh_nd  = shapley_exact(j, "nd")
    print(f"  {crit:12s}  {w_ahp[j]:6.3f}  {sh_jac:22.6f}  {sh_nd:12.6f}")
    shapley_rows.append({"criterio":crit,"w_nom":w_ahp[j],"shapley_jac":sh_jac,"shapley_nd":sh_nd})

df_sh = pd.DataFrame(shapley_rows).sort_values("shapley_jac", ascending=False)
df_sh.to_csv(os.path.join(RESULTS_DIR,"shapley_norm_results.csv"), index=False)

print(f"\n=== Critérios por Shapley(Jac@10 vs MM) ===")
print(df_sh[["criterio","w_nom","shapley_jac","shapley_nd"]].to_string(index=False, float_format=lambda x: f"{x:+.6f}"))

# Estatísticas resumo
print(f"\n  Soma Shapley(Jac): {df_sh.shapley_jac.sum():.6f}  (deve ser ≈ v(N) - v(∅) = {jaccard_k(sc_mm_full,sc_mm_full)-jaccard_k(sc_vn_full,sc_mm_full):.6f})")
print(f"  %nd vs n_minmax: {df_combo.groupby('n_minmax')['nd'].mean().to_dict()}")
print("\nSalvo em results/shapley_norm_results.csv e shapley_combos.csv")
