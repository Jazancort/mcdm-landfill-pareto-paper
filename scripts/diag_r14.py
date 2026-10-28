# -*- coding: utf-8 -*-
"""
diag_r14.py — Round 14: diagnósticos aspect, perm top-10, bit-a-bit, Q2 idêntico TOPSIS-vec
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from mcdm_experiment import (load_data, impute_nan, COL, AHP_WEIGHTS,
                               _build_decision_matrix, haversine_km, greedy_trio)
try:
    from mcdm_experiment import INV, COST, _norm
except ImportError:
    INV = set(); COST = set()

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
N = len(df_via)
w = np.array(list(AHP_WEIGHTS.values()))
col_names = list(AHP_WEIGHTS.keys())
X_via, benefit = _build_decision_matrix(df_via)
via_global = df_via.index.values
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)

# ─── 1. aspect: qual coluna vai ao TOPSIS? ────────────────────────────────────
print("=== 1. aspect — pipeline completo ===")
asp_raw = df_via[COL["aspect"]].values
# _build_decision_matrix: o que faz com aspect?
# Inspecionamos o índice da coluna aspect em X_via
j_asp = col_names.index("aspect")
x_asp_in_X = X_via[:, j_asp]

print(f"  raw aspect: min={asp_raw.min():.3f}  max={asp_raw.max():.3f}  mean={asp_raw.mean():.3f}")
print(f"  X_via[:,aspect] (após _build_decision_matrix): min={x_asp_in_X.min():.3f}  max={x_asp_in_X.max():.3f}  mean={x_asp_in_X.mean():.3f}")
print(f"  benefit[aspect]={benefit[j_asp]}  (True=maximizar)")
print(f"  Valores únicos de X_via[:,aspect] (primeiros 10): {np.sort(np.unique(x_asp_in_X))[:10]}")

# Verificar se é binário após normalização min-max
mm_asp = (x_asp_in_X - x_asp_in_X.min()) / (x_asp_in_X.max() - x_asp_in_X.min() + 1e-12)
print(f"  Após min-max: distinct values = {len(np.unique(mm_asp))} (se =2, é binário)")

# Forma fechada para aspect binário
# c (X_via) = 1 se aspecto NOT in [90,180], 0 caso contrário
# n0=94 (c=0, flat), n1=295 (c=1)
n0, n1 = int((x_asp_in_X == 0).sum()), int((x_asp_in_X == 1).sum())
print(f"  n(c=0)={n0}  n(c=1)={n1}  são os únicos valores? {set(np.unique(x_asp_in_X)) <= {0.0, 1.0}}")

if set(np.unique(x_asp_in_X)) <= {0.0, 1.0}:
    # Forma fechada: ||x|| = sqrt(n1), (max-min) = 1
    ratio_closed = 1.0 / np.sqrt(n1)
    nrm_empirico = np.sqrt((x_asp_in_X**2).sum())
    ratio_empirico = (x_asp_in_X.max() - x_asp_in_X.min()) / nrm_empirico
    print(f"  Forma fechada: ratio = 1/sqrt(n1) = 1/sqrt({n1}) = {ratio_closed:.6f}")
    print(f"  Empírico:      ratio = {ratio_empirico:.6f}")
    cv_closed = np.sqrt((1.0/n1) * (1 - 1.0/n1) / ((1.0/n1)**2 + 1e-12)) # não exato
    cv_empirico = x_asp_in_X.std() / x_asp_in_X.mean()
    print(f"  CV empírico = {cv_empirico:.4f}")
    # Fórmula da revisão: codif c=1 dentro (n1=94), ratio = 1/sqrt(94) = 0.103
    r_alt = 1.0 / np.sqrt(94)
    print(f"  Codif alternativa (n1=94): 1/sqrt(94) = {r_alt:.6f}")
    print(f"  Tabela seção 8: ratio_389 = 0.0967")
    print(f"  Match: benefit[aspect]={benefit[j_asp]}, c=1 significa 'fora de [90,180]' (n1={n1})")
    print(f"  1/sqrt({n1}) = {1/np.sqrt(n1):.6f} → {'bate' if abs(1/np.sqrt(n1) - 0.0967) < 0.001 else 'NÃO bate'}")

print()

# ─── 2. perm top-10 de scores ─────────────────────────────────────────────────
print("=== 2. perm no top-10 (SAW min-max greedy e vetorial) ===")
# scores SAW min-max
mm_all = np.zeros(N)
vn_all = np.zeros(N)
X_adj = X_via.copy()
for jj, b in enumerate(benefit):
    if not b: X_adj[:, jj] = 1. - X_via[:, jj]
mm_all = (X_adj * w).sum(1)
vn_norms = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)
X_vn = X_via / vn_norms
vn_all = (X_vn * w).sum(1)  # SAW vetorial (mesmo ajuste de benefit dentro de X_adj)

# Top-10 por score mm e vn
top10_mm = np.argsort(-mm_all)[:10]
top10_vn = np.argsort(-vn_all)[:10]

j_perm = col_names.index("perm")
perm_col = df_via[COL["perm"]].values

print(f"  perm raw: min={perm_col.min():.4f}  max={perm_col.max():.4f}  median={np.median(perm_col):.4f}")
print(f"  Fração no mínimo (=min): {(perm_col == perm_col.min()).sum()/N:.3f}")
print()
print(f"  Top-10 por SAW min-max:")
for rank, idx in enumerate(top10_mm):
    sid = int(via_global[idx])
    print(f"    {rank+1:2d}. site {sid:3d}  perm={perm_col[idx]:.4f}  score_mm={mm_all[idx]:.4f}")
print()
print(f"  Top-10 por SAW vetorial (X_adj):")
for rank, idx in enumerate(top10_vn):
    sid = int(via_global[idx])
    print(f"    {rank+1:2d}. site {sid:3d}  perm={perm_col[idx]:.4f}  score_vn={vn_all[idx]:.4f}")
print()

# ─── 3. Regressão bit-a-bit (14 células não-postos antes/depois do fix) ───────
print("=== 3. Regressão bit-a-bit (células não-postos) ===")
raw_csv = os.path.join(RESULTS_DIR, "mc_18cells_raw.csv")
if not os.path.exists(raw_csv):
    print("  FALTA mc_18cells_raw.csv (versão corrigida)")
else:
    df = pd.read_csv(raw_csv)
    # Células não-postos
    non_ranks = df[df["norm"] != "ranks"]
    # Verificar: SAW×minmax deve ser idêntico antes e depois
    # (o fix só afeta norm=="ranks" com topsis/vikor)
    # Carregar versão anterior (round 12) se existir
    raw_old = os.path.join(RESULTS_DIR, "mc_18cells_raw_r12.csv")
    if os.path.exists(raw_old):
        df_old = pd.read_csv(raw_old)[df_old["norm"] != "ranks"]
        df_new = non_ranks.copy()
        # Merge por alpha, draw, agg, norm, mont
        merged = df_old.merge(df_new, on=["alpha","draw","agg","norm","mont"],
                              suffixes=("_old","_new"))
        for col in ["nd_Q1A","nd_Q2A","nd_Q1Ap","nd_Q2Ap"]:
            diff = (merged[f"{col}_old"] != merged[f"{col}_new"]).sum()
            print(f"  {col}: {diff} diferenças de {len(merged)} linhas")
    else:
        print("  mc_18cells_raw_r12.csv não encontrado — usando SAW×mm como controle interno")
        saw_mm = df[(df["agg"]=="saw") & (df["norm"]=="minmax")]
        print(f"  SAW×mm×greedy α=200 Q2[A']: {saw_mm[saw_mm['mont']=='greedy']['nd_Q2Ap'].mean()*100:.1f}%")
        print(f"  SAW×mm×optimal α=200 Q2[A']: {saw_mm[saw_mm['mont']=='optimal']['nd_Q2Ap'].mean()*100:.1f}%")
        print(f"  Esperado (Round 11 mc_aprime_full): greedy≈64.6%, optimal≈100% → ", end="")
        g_ok = abs(saw_mm[saw_mm["mont"]=="greedy"]["nd_Q2Ap"].mean()*100 - 64.6) < 1.0
        o_ok = abs(saw_mm[saw_mm["mont"]=="optimal"]["nd_Q2Ap"].mean()*100 - 100.0) < 1.0
        print("PASS" if g_ok and o_ok else "FAIL")
        # Verifica TOPSIS mm
        topsis_mm = df[(df["agg"]=="topsis") & (df["norm"]=="minmax")]
        t_g = topsis_mm[topsis_mm["mont"]=="greedy"]["nd_Q2Ap"].mean()*100
        t_o = topsis_mm[topsis_mm["mont"]=="optimal"]["nd_Q2Ap"].mean()*100
        print(f"  TOPSIS×mm×greedy α=200 Q2[A']: {t_g:.1f}%  (Round 11: 72.4%) {'PASS' if abs(t_g-72.4)<2 else 'FAIL'}")
        print(f"  TOPSIS×mm×optimal α=200 Q2[A']: {t_o:.1f}%  (Round 11: 96.6%) {'PASS' if abs(t_o-96.6)<2 else 'FAIL'}")

print()

# ─── 4. Q2[A]=14.2% idêntico em TOPSIS-vec greedy e ótimo ────────────────────
print("=== 4. Q2[A]=14.2% idêntico em TOPSIS-vec greedy e ótimo ===")
df_all_raw = pd.read_csv(raw_csv)
tv = df_all_raw[(df_all_raw["agg"]=="topsis") & (df_all_raw["norm"]=="vector") & (df_all_raw["alpha"]==200)]
tv_g = tv[tv["mont"]=="greedy"]
tv_o = tv[tv["mont"]=="optimal"]
print(f"  greedy Q2[A] mean: {tv_g['nd_Q2A'].mean()*100:.2f}%")
print(f"  optimal Q2[A] mean: {tv_o['nd_Q2A'].mean()*100:.2f}%")
# Conta trios idênticos por draw
merged_tv = tv_g[["alpha","draw","nd_Q1A","nd_Q2A","nd_Q1Ap","nd_Q2Ap"]].merge(
    tv_o[["alpha","draw","nd_Q1A","nd_Q2A","nd_Q1Ap","nd_Q2Ap"]],
    on=["alpha","draw"], suffixes=("_g","_o"))
same_Q2A  = (merged_tv["nd_Q2A_g"] == merged_tv["nd_Q2A_o"]).sum()
same_Q2Ap = (merged_tv["nd_Q2Ap_g"] == merged_tv["nd_Q2Ap_o"]).sum()
print(f"  Q2[A]  greedy==optimal por sorteio: {same_Q2A}/{len(merged_tv)}")
print(f"  Q2[A'] greedy==optimal por sorteio: {same_Q2Ap}/{len(merged_tv)}")
print(f"  Conclusão: {'coincidência (diferentes trios, mesmo resultado)' if same_Q2A < len(merged_tv)*0.99 else 'trios idênticos'}")

print()

# ─── 5. Médias por nível corretas (α=200, Q2[A']) ─────────────────────────────
print("=== 5. Médias por nível corretas (α=200, Q2[A'], 12 células válidas) ===")
df200 = df_all_raw[df_all_raw["alpha"]==200]
# 12 células: excluir ranks×(topsis|vikor) e vikor×vector
invalid = ((df200["norm"]=="ranks") & (df200["agg"].isin(["topsis","vikor"]))) | \
          ((df200["agg"]=="vikor") & (df200["norm"]=="vector"))
df12 = df200[~invalid]
print(f"  Células: {df12.groupby(['agg','norm','mont']).size().reset_index(name='n')[['agg','norm','mont']].to_string(index=False)}")
print()
for factor, levels in [("norm", ["minmax","ranks","vector"]),
                        ("mont", ["optimal","greedy"]),
                        ("agg",  ["saw","topsis","vikor"])]:
    print(f"  Médias por {factor}:")
    for lvl in levels:
        sub = df12[df12[factor]==lvl]
        if len(sub):
            m = sub["nd_Q2Ap"].mean()*100
            print(f"    {lvl:8s}: {m:.1f}%  (n_cells={df12[df12[factor]==lvl].groupby(['agg','norm','mont']).ngroups})")
print()
print(f"  Amplitudes (max-min):")
for factor in ["norm","mont","agg"]:
    means = df12.groupby(factor)["nd_Q2Ap"].mean()*100
    print(f"    {factor}: {means.max()-means.min():.1f} pp  |  {dict(means.round(1))}")
