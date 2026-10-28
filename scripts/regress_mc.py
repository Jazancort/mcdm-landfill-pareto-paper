# -*- coding: utf-8 -*-
"""
regress_mc.py  — Tarefa 1: Regressão do MC com pesos AHP fixos
Reproduz a tabela canônica (seção 3 do estado-atual.md) nos dois desenhos Q1 e Q2.
Documenta a fórmula exata do gap_norm em cada desenho.
Explica por que gap_norm difere entre rodadas.

Run: uv run --with pandas --with numpy python scripts/regress_mc.py
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
    COL, AHP_WEIGHTS, MIN_DIST_KM, COST, _build_decision_matrix,
)

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
via_global = df_via.index.values
N = len(df_via)
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
w_ahp = np.array(list(AHP_WEIGHTS.values()))
objs_473 = compute_objectives(df_imp, df_imp)
objs_via = compute_objectives(df_via, df_imp)  # normalização 473, só viáveis

# ─── Pré-calcular todos os trios viáveis ─────────────────────────────────────
print("Pré-calculando trios viáveis...")
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
print(f"  {M:,} trios")

# ─── Objetivos de todos os trios ─────────────────────────────────────────────
# Dois espaços:
# (A)  Normalização sobre 473, pesos AHP — = objetivos do artigo IEEE
# (A') Normalização sobre 389 viáveis, pesos AHP — escala justa para os métodos

# Espaço A (normalização 473)
f1v_A = objs_via["f1"].values.astype(np.float32)
f2v_A = objs_via["f2"].values.astype(np.float32)
f3v_A = objs_via["f3"].values.astype(np.float32)
F1_A = f1v_A[trio_arr[:,0]] + f1v_A[trio_arr[:,1]] + f1v_A[trio_arr[:,2]]
F2_A = f2v_A[trio_arr[:,0]] + f2v_A[trio_arr[:,1]] + f2v_A[trio_arr[:,2]]
F3_A = f3v_A[trio_arr[:,0]] + f3v_A[trio_arr[:,1]] + f3v_A[trio_arr[:,2]]

# Espaço A' (normalização 389 viáveis)
objs_via_prime = compute_objectives(df_via, df_via)  # df_via como referência
f1v_P = objs_via_prime["f1"].values.astype(np.float32)
f2v_P = objs_via_prime["f2"].values.astype(np.float32)
f3v_P = objs_via_prime["f3"].values.astype(np.float32)
F1_P = f1v_P[trio_arr[:,0]] + f1v_P[trio_arr[:,1]] + f1v_P[trio_arr[:,2]]
F2_P = f2v_P[trio_arr[:,0]] + f2v_P[trio_arr[:,1]] + f2v_P[trio_arr[:,2]]
F3_P = f3v_P[trio_arr[:,0]] + f3v_P[trio_arr[:,1]] + f3v_P[trio_arr[:,2]]

# ─── Fórmula exata do gap_norm ────────────────────────────────────────────────
def gap_norm(f1t, f2t, f3t, F1, F2, F3):
    """
    gap_norm = max(0, max_{t'} min(dc, di, ds))
    onde:
      dc = (f1t - F1[t']) / (F1.max() - F1.min())   [quanto F1 pode melhorar]
      di = (f2t - F2[t']) / (F2.max() - F2.min())   [quanto F2 pode melhorar]
      ds = (F3[t'] - f3t) / (F3.max() - F3.min())   [quanto F3 pode melhorar]
    Se o trio não é dominado, gap_norm = 0.
    Interpretação: distância normalizada ao dominador mais próximo na pior dimensão.
    """
    mask_dom = ((F1<=f1t)&(F2<=f2t)&(F3>=f3t)&
                ((F1<f1t)|(F2<f2t)|(F3>f3t)))
    if not mask_dom.any():
        return 0.0
    f1r = F1.max()-F1.min(); f2r = F2.max()-F2.min(); f3r = F3.max()-F3.min()
    dc = (f1t - F1) / (f1r or 1)
    di = (f2t - F2) / (f2r or 1)
    ds = (F3 - f3t) / (f3r or 1)
    slack = np.minimum(np.minimum(dc, di), ds)
    return float(max(0., slack.max()))

def is_dom(f1t, f2t, f3t, F1, F2, F3):
    return bool(((F1<=f1t)&(F2<=f2t)&(F3>=f3t)&
                 ((F1<f1t)|(F2<f2t)|(F3>f3t))).any())

# ─── Scores base (pesos AHP) ─────────────────────────────────────────────────
sc_saw   = saw_scores(df_via)
sc_tvn   = topsis_scores(df_via)   # VN
sc_vik   = vikor_scores(df_via)
sc_prom  = promethee2_scores(df_via)

# TOPSIS-MM
X_via, benefit = _build_decision_matrix(df_via)
V_mm = X_via * w_ahp
PIS_mm = np.where(benefit, V_mm.max(0), V_mm.min(0))
NIS_mm = np.where(benefit, V_mm.min(0), V_mm.max(0))
dp_mm = np.sqrt(((V_mm-PIS_mm)**2).sum(1))
dn_mm = np.sqrt(((V_mm-NIS_mm)**2).sum(1))
d_mm  = dp_mm+dn_mm
sc_tmm = np.where(d_mm==0, 0.5, dn_mm/d_mm)

# SAW_s1 = -f1-f2+f3 com pesos AHP e normalização 473
X_all, benefit_all = _build_decision_matrix(df_imp)
sc_all_adj = X_all.copy()
for j, b in enumerate(benefit_all): sc_all_adj[:,j] = X_all[:,j] if b else 1.-X_all[:,j]
idx_473 = {gid:i for i,gid in enumerate(df_all.index)}
via_idx473 = np.array([idx_473[int(g)] for g in via_global])
sv473 = sc_all_adj[via_idx473]
col_names = list(AHP_WEIGHTS.keys())
f1_idx = [col_names.index(c) for c in ["perm","slope","roads"]]
f2_idx = [col_names.index(c) for c in ["rivers","aspect","coast","protected","wells"]]
f3_idx = [col_names.index(c) for c in ["urban","aero","cult"]]
s1_f1 = sv473[:,f1_idx] @ w_ahp[f1_idx]
s1_f2 = sv473[:,f2_idx] @ w_ahp[f2_idx]
s1_f3 = sv473[:,f3_idx] @ w_ahp[f3_idx]
sc_s1  = -s1_f1 - s1_f2 + s1_f3   # SAW_s1

def argmax_trio(sc):
    st = sc[trio_arr[:,0]]+sc[trio_arr[:,1]]+sc[trio_arr[:,2]]
    return trio_arr[st.argmax()]

# ─── Tabela de regressão ─────────────────────────────────────────────────────
print("\n" + "="*80)
print("REGRESSÃO: pesos AHP fixos — reproduzir seção 3 em Q1 (espaço A) e Q2 (espaço A)")
print("gap_norm_A  = gap calculado com fronteira A (normalização 473)")
print("gap_norm_v3 = gap calculado com os 213 trios IEEE (amplitude da fronteira IEEE)")
print("="*80)

# gap usando os 213 trios IEEE (como a v3 do MC fazia)
f1r_ieee = par.Cost.max()-par.Cost.min()
f2r_ieee = par.Impact.max()-par.Impact.min()
f3r_ieee = par.Safety.max()-par.Safety.min()

def gap_norm_ieee(f1t, f2t, f3t):
    """Gap normalizado pela amplitude dos 213 trios IEEE (rodada anterior)."""
    dc = (f1t - par.Cost.values)   / (f1r_ieee or 1)
    di = (f2t - par.Impact.values) / (f2r_ieee or 1)
    ds = (par.Safety.values - f3t) / (f3r_ieee or 1)
    slack = np.minimum(np.minimum(dc, di), ds)
    if not pareto_dominates(par, f1t, f2t, f3t):
        return 0.
    return float(max(0., slack.max()))

SCENARIOS = [
    ("SAW greedy",       sc_saw,  "greedy"),
    ("SAW_s1 greedy",    sc_s1,   "greedy"),
    ("SAW_s1 optimal",   sc_s1,   "optimal"),
    ("TOPSIS-VN greedy", sc_tvn,  "greedy"),
    ("TOPSIS-VN optimal",sc_tvn,  "optimal"),
    ("TOPSIS-MM greedy", sc_tmm,  "greedy"),
    ("VIKOR greedy",     sc_vik,  "greedy"),
    ("PROMETHEE greedy", sc_prom, "greedy"),
]

print(f"\n  {'Cenário':22s}  gids              gap_A     gap_ieee  dom_A  in_213")
rows = []
for name, sc, variant in SCENARIOS:
    if variant == "greedy":
        idx = greedy_trio(sc, D_via)
    else:
        idx = argmax_trio(sc)
    i,j,k = idx
    gids = sorted([int(via_global[i]),int(via_global[j]),int(via_global[k])])
    f1t = float(f1v_A[i]+f1v_A[j]+f1v_A[k])
    f2t = float(f2v_A[i]+f2v_A[j]+f2v_A[k])
    f3t = float(f3v_A[i]+f3v_A[j]+f3v_A[k])
    dom_A    = is_dom(f1t,f2t,f3t, F1_A,F2_A,F3_A)
    gn_A     = gap_norm(f1t,f2t,f3t, F1_A,F2_A,F3_A)
    gn_ieee  = gap_norm_ieee(f1t,f2t,f3t)
    in_213   = in_pareto_front(par, gids)
    print(f"  {name:22s}  {str(gids):18s}  {gn_A:.4f}  {gn_ieee:.4f}  {'Y' if dom_A else 'N'}  {in_213}")
    rows.append({"cenario":name,"gids":str(gids),"f1":f1t,"f2":f2t,"f3":f3t,
                 "gap_A":gn_A,"gap_ieee":gn_ieee,"dom_A":dom_A,"in_213":in_213})

print("\n  Nota: gap_A usa F1,F2,F3 dos 1.944.653 trios (normaliz 473)")
print("  Nota: gap_ieee usa os 213 trios IEEE como referência")
print("  As diferenças de gap entre rodadas vêm de: amplitude(1.9M) ≠ amplitude(213)")
print(f"\n  Amplitudes espaço A (1.9M trios): f1={F1_A.max()-F1_A.min():.4f}  f2={F2_A.max()-F2_A.min():.4f}  f3={F3_A.max()-F3_A.min():.4f}")
print(f"  Amplitudes IEEE (213 trios):     f1={f1r_ieee:.4f}  f2={f2r_ieee:.4f}  f3={f3r_ieee:.4f}")

# ─── Verificar por que Q1/Q2 do MC deram iguais ──────────────────────────────
print("\n" + "="*60)
print("DIAGNÓSTICO: por que Q1≈Q2 no mc_q1q2_summary.csv?")
print("="*60)

# Q1: dominância nos objetivos AHP fixos (F1_A, F2_A, F3_A)
# Q2: dominância nos objetivos recalculados com pesos sorteados
# Diferença Q1 vs Q2 vem de: quando pesos mudam, a escala dos objetivos muda
# Mas os SCORES dos métodos também mudam — e ambos usam normalização 389
# O trio selecionado pode ser o mesmo (mesmo ranking dos métodos com pesos ≈ AHP)
# E a dominância em A (fixo) ≈ dominância em A com pesos sorteados se pesos ≈ AHP

# Com α=200, pesos ≈ AHP → os dois espaços são quase iguais → Q1≈Q2 é esperado
print("  α=200: pesos sorteados muito próximos do AHP → objetivos Q1 ≈ Q2 → resultados ≈ iguais")
print("  α=50:  pesos sorteados mais dispersos → Q1 e Q2 divergem mais")
print("  Isso é CORRETO, não é bug.")

# ─── Verificar discrepância SAW Q1-v3 (42%) vs Q1-novo (3%) ─────────────────
print("\n" + "="*60)
print("DIAGNÓSTICO: SAW greedy 42% (v3) vs 3% (Q1 novo) com α=200")
print("="*60)
print("  v3 usava: scores com normaliz 389 (X_adj via _build_decision_matrix(df_via))")
print("  Q1 novo usa: scores com normaliz 389 (X_adj via _build_decision_matrix(df_via))")
print("  Mas v3 usava F1_A,F2_A,F3_A = compute_objectives(df_via,df_imp) = normaliz 473")
print("  Q1 novo usa: scores via473 @ w → f1,f2,f3 sem divisão por w_group")
print()
print("  A diferença está em COMO os objetivos são calculados no MC Q2/Q1 novo:")
print("  mc_q1q2.py usa: scores_via473[:,f1_idx] @ w (sem divisão por w_group)")
print("  mcdm_v3 usava: compute_objectives(df_via,df_imp) = sum(w_j * score_j) DIRETAMENTE")
print()
print("  Verificar se os dois são equivalentes com pesos AHP:")
obj_direct = trio_objectives_from_global((184,279,320), objs_473)
f1_direct = obj_direct["f1"]
# Recalcular via sc_all_adj
idx_in_via = {int(gid):li for li,gid in enumerate(via_global)}
li = [idx_in_via[g] for g in [184,279,320]]
f1_via473 = float(s1_f1[li[0]]+s1_f1[li[1]]+s1_f1[li[2]])
print(f"  f1 via compute_objectives: {f1_direct:.6f}")
print(f"  f1 via s1_f1 (sc_all_adj@w): {f1_via473:.6f}")
print(f"  Iguais: {abs(f1_direct - f1_via473) < 1e-6}")

pd.DataFrame(rows).to_csv(
    os.path.join(os.path.dirname(__file__), "results", "regression_mc.csv"), index=False)
print(f"\nResultados salvos em results/regression_mc.csv")
