# -*- coding: utf-8 -*-
"""diag_t2t3.py — diagnóstico dos testes T2 e T3"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from mcdm_experiment import (
    load_data, impute_nan, compute_objectives, haversine_km,
    pareto_dominates, in_pareto_front, trio_objectives_from_global,
    COL, AHP_WEIGHTS, MIN_DIST_KM, _build_decision_matrix
)

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
via_global = df_via.index.values
w = np.array(list(AHP_WEIGHTS.values()))

# Trio {184,430,460} com objetivos originais IEEE
objs_473 = compute_objectives(df_imp, df_imp)
obj = trio_objectives_from_global((184,430,460), objs_473)
dom = pareto_dominates(par, obj["f1"], obj["f2"], obj["f3"])
inf = in_pareto_front(par, (184,430,460))
print("Trio (184,430,460) com objetivos IEEE:")
print(f"  f1={obj['f1']:.4f} f2={obj['f2']:.4f} f3={obj['f3']:.4f}")
print(f"  in_pareto_front={inf}  dominated={dom}")

# Compare com compute_F_w (normalização 473, w_group division)
X_all, benefit_all = _build_decision_matrix(df_imp)
sc_all = X_all.copy()
for j, b in enumerate(benefit_all):
    if not b: sc_all[:,j] = 1.-X_all[:,j]
idx_473 = {gid:i for i,gid in enumerate(df_all.index)}
via_idx473 = np.array([idx_473[int(g)] for g in via_global])
sv = sc_all[via_idx473]
col_names = list(AHP_WEIGHTS.keys())
f1_idx = [col_names.index(c) for c in ["perm","slope","roads"]]
f2_idx = [col_names.index(c) for c in ["rivers","aspect","coast","protected","wells"]]
f3_idx = [col_names.index(c) for c in ["urban","aero","cult"]]
w1=w[f1_idx].sum(); w2=w[f2_idx].sum(); w3=w[f3_idx].sum()
f1v = sv[:,f1_idx] @ w[f1_idx] / w1
f2v = sv[:,f2_idx] @ w[f2_idx] / w2
f3v = sv[:,f3_idx] @ w[f3_idx] / w3
g2l = {int(gid): li for li, gid in enumerate(via_global)}
li = [g2l[g] for g in [184,430,460]]
f1t=f1v[li[0]]+f1v[li[1]]+f1v[li[2]]
f2t=f2v[li[0]]+f2v[li[1]]+f2v[li[2]]
f3t=f3v[li[0]]+f3v[li[1]]+f3v[li[2]]
print(f"\nTrio (184,430,460) com compute_F_w (w_group division):")
print(f"  f1={f1t:.4f} f2={f2t:.4f} f3={f3t:.4f}")
print(f"\nDiferença: os objetivos IEEE nao usam divisao por w_group.")
print(f"  IEEE: f1 = sum(w_j * score_j)  para j em f1_crit")
print(f"  Q2:   f1 = sum(w_j * score_j) / sum(w_j_f1)")
print(f"  Sao monotonamente relacionados mas com escalas diferentes.")
print(f"  Para o teste de P1 (Q2), usar a mesma definição dentro do sorteio.")
print(f"  A definição mais limpa: mesmos objetivos que o MC v3 usa para Q1.")
