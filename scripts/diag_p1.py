# -*- coding: utf-8 -*-
"""diag_p1.py — Verificar quando P1 vale e quando não vale no MC"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from mcdm_experiment import (
    load_data, impute_nan, haversine_km,
    COL, AHP_WEIGHTS, MIN_DIST_KM, _build_decision_matrix
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
f1_idx = [col_names.index(c) for c in ["perm","slope","roads"]]
f2_idx = [col_names.index(c) for c in ["rivers","aspect","coast","protected","wells"]]
f3_idx = [col_names.index(c) for c in ["urban","aero","cult"]]

# P1 só vale se score(trio) = alpha*f1 - beta*f2 + gamma*f3  (mesma combinação linear)
# Para isso, os objetivos precisam ser somados com os MESMOS pesos que o score.
# O SAW score = sum_j w_j * adj_j(a)
# O objetivo f1 = sum_{j em f1} w_j * adj_j(a)  [já inclui peso]
# Então: score(a) = f1(a) + f2(a) + f3(a)  apenas se os objetivos SÃO as partes do score.
# Isso vale para o SAW-473 (normalização 473): score_473(a) = f1_473(a) + f2_473(a) + f3_473(a)?

X_all, benefit_all = _build_decision_matrix(df_imp)
sc_all = X_all.copy()
for j, b in enumerate(benefit_all):
    if not b: sc_all[:,j] = 1.-X_all[:,j]
idx_473 = {gid:i for i,gid in enumerate(df_all.index)}
via_idx473 = np.array([idx_473[int(g)] for g in via_global])
sv = sc_all[via_idx473]  # (389,11) normalização 473

# SAW score = (sv * w).sum(1) = f1v + f2v + f3v onde:
f1v = sv[:,f1_idx] @ w[f1_idx]
f2v = sv[:,f2_idx] @ w[f2_idx]
f3v = sv[:,f3_idx] @ w[f3_idx]
saw_sc = (sv * w).sum(1)
check = f1v + f2v + f3v
print("P1 check: SAW score = f1+f2+f3?")
print(f"  max_diff = {np.abs(saw_sc - check).max():.2e}  {'PASS' if np.abs(saw_sc-check).max()<1e-9 else 'FAIL'}")

# Agora verificar se o argmax SAW ótimo tem objetivos não dominados
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

F1 = f1v[trio_arr[:,0]]+f1v[trio_arr[:,1]]+f1v[trio_arr[:,2]]
F2 = f2v[trio_arr[:,0]]+f2v[trio_arr[:,1]]+f2v[trio_arr[:,2]]
F3 = f3v[trio_arr[:,0]]+f3v[trio_arr[:,1]]+f3v[trio_arr[:,2]]
S  = saw_sc[trio_arr[:,0]]+saw_sc[trio_arr[:,1]]+saw_sc[trio_arr[:,2]]

best_idx = S.argmax()
best = trio_arr[best_idx]
gids = sorted(int(via_global[x]) for x in best)
f1t=F1[best_idx]; f2t=F2[best_idx]; f3t=F3[best_idx]
dom = ((F1<=f1t)&(F2<=f2t)&(F3>=f3t)&((F1<f1t)|(F2<f2t)|(F3>f3t))).any()
print(f"\nSAW-473 ótimo: {gids}")
print(f"  f1={f1t:.4f} f2={f2t:.4f} f3={f3t:.4f}")
print(f"  dominado pelos {M:,} trios (mesmos objetivos f1,f2,f3): {dom}")
print(f"  P1 VALE quando: objetivos = f1,f2,f3 com normalização 473 e pesos w")
print(f"  O argmax de S = argmax(f1+f2+f3) = não dominado na minimização de f1+f2-f3")
print(f"\nMas espera — P1 é para MINIMIZAR (f1,f2) e MAXIMIZAR f3.")
print(f"  Verificar dominancia correta: minimizar f1,f2; maximizar f3")
print(f"  Dominado se existe j com F1[j]<=f1t AND F2[j]<=f2t AND F3[j]>=f3t (com >= 1 estrito)")
print(f"  Mas argmax(f1+f2+f3) maximiza f1+f2+f3, o que mistura custo (minimizar) com segurança (maximizar)")
print(f"\nREMEDIO: P1 deve usar score com os SENTIDOS CORRETOS:")
print(f"  S1 = -f1 - f2 + f3 = -(custo+impacto) + segurança = SAW com inversão de f1,f2")
print(f"  Verificar S1:")
S1 = -F1 - F2 + F3
best_s1 = trio_arr[S1.argmax()]
gids_s1 = sorted(int(via_global[x]) for x in best_s1)
f1s=F1[S1.argmax()]; f2s=F2[S1.argmax()]; f3s=F3[S1.argmax()]
dom_s1 = ((F1<=f1s)&(F2<=f2s)&(F3>=f3s)&((F1<f1s)|(F2<f2s)|(F3>f3s))).any()
print(f"  S1 ótimo: {gids_s1}  f1={f1s:.4f} f2={f2s:.4f} f3={f3s:.4f}")
print(f"  S1 ótimo dominado: {dom_s1}  (deve ser False para P1 valer)")
