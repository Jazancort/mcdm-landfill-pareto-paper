# -*- coding: utf-8 -*-
import sys, os; sys.path.insert(0, '.')
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix,
    haversine_km, saw_scores, vikor_scores, promethee2_scores,
    greedy_trio, optimal_trio_enumerate,
    pareto_dominates, in_pareto_front,
    MIN_DIST_KM,
)

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL['protected']] > 0
df_via = df_imp[viable_mask].copy()
col_names = list(AHP_WEIGHTS.keys())
w = np.array(list(AHP_WEIGHTS.values()))
X_via, benefit = _build_decision_matrix(df_via)
alpha = 200

# Distancia
D = haversine_km(df_via['latitude (degrees)'].values, df_via['longitude (degrees)'].values)
via_idx = df_via.index.values

# Fronteira A'
front_csv = os.path.join('results', 'pareto_front_Aprime.csv')
front_df = pd.read_csv(front_csv)

def eval_trio(trio_local, via_idx, bcs, front_df, par):
    global_ids = tuple(via_idx[i] for i in trio_local)
    obj_s = bcs.loc[list(global_ids)].sum()
    f1, f2, f3 = float(obj_s['f1']), float(obj_s['f2']), float(obj_s['f3'])
    dominated = pareto_dominates(par, f1, f2, f3)
    in_front = in_pareto_front(par, global_ids)
    return {'global_ids': global_ids, 'dominated': dominated, 'in_front': in_front}

# ===== S3: VIKOR x ranks =====
print('=== S3: VIKOR x ranks ===')
# Postos normalizados [0,1], invertidos (rank 1 = 1.0)
R_raw = np.zeros_like(X_via, dtype=float)
for j in range(len(w)):
    x = X_via[:, j].astype(float)
    if not benefit[j]:
        x = -x
    R_raw[:, j] = rankdata(-x, method='average')
Rn = np.zeros_like(R_raw)
for j in range(len(w)):
    lo, hi = R_raw[:, j].min(), R_raw[:, j].max()
    Rn[:, j] = 1.0 - (R_raw[:, j] - lo) / (hi - lo) if hi > lo else 0.5

# VIKOR manual sobre Rn
v_param = 0.5
f_star = Rn.max(axis=0)
f_minus = Rn.min(axis=0)
denom_v = np.abs(f_star - f_minus)
denom_v[denom_v == 0] = 1.0
norm_d = np.abs(f_star - Rn) / denom_v
S_v = (w * norm_d).sum(axis=1)
Rv = (w * norm_d).max(axis=1)
def norm01(arr):
    lo, hi = arr.min(), arr.max()
    return np.zeros(len(arr)) if hi == lo else (arr - lo) / (hi - lo)
Q_v = v_param * norm01(S_v) + (1 - v_param) * norm01(Rv)
scores_vr = 1.0 - Q_v

trio_g = greedy_trio(scores_vr, D, alpha)
trio_o = optimal_trio_enumerate(scores_vr, D, alpha)
r_g = eval_trio(trio_g, via_idx, bcs, front_df, par)
r_o = eval_trio(trio_o, via_idx, bcs, front_df, par)
print('greedy :', r_g['global_ids'], '| in_front:', r_g['in_front'], '| dominated:', r_g['dominated'])
print('optimal:', r_o['global_ids'], '| in_front:', r_o['in_front'], '| dominated:', r_o['dominated'])

# Q2 aproximado: em_front = Q2=100%; dominado mas nao in_front = Q2=0%
# Calculo correto de Q2 exigiria contar fracao da fronteira nao-dominada
# Para o diagnostico: suficiente saber se e dominado
not_domin_g = not r_g['dominated']
not_domin_o = not r_o['dominated']
print('VIKOR x ranks colapsa (ambos dominados)?', r_g['dominated'] and r_o['dominated'])
print()

# ===== S4: P2 midranks vs PROMETHEE =====
print('=== S4: P2 - SAW x midranks vs PROMETHEE II ===')
# SAW sobre postos midrank (nao normalizado)
R_mid = np.zeros_like(X_via, dtype=float)
for j in range(len(w)):
    x = X_via[:, j].astype(float)
    if not benefit[j]:
        x = -x
    R_mid[:, j] = rankdata(-x, method='average')
scores_saw_mid = (R_mid * w).sum(axis=1)

scores_prom = promethee2_scores(df_via)
rho_sp, p_sp = spearmanr(scores_saw_mid, scores_prom)
print('Spearman(SAW_midranks, PROMETHEE2) =', round(rho_sp, 6))

def zn(a):
    s = a.std()
    return (a - a.mean()) / s if s > 0 else np.zeros_like(a)

max_diff = float(np.abs(zn(scores_saw_mid) - zn(scores_prom)).max())
print('Max diff (z-scores):', round(max_diff, 6))

rank_saw_s = pd.Series(scores_saw_mid).rank(method='average')
rank_prom_s = pd.Series(scores_prom).rank(method='average')
n_diff = int((rank_saw_s != rank_prom_s).sum())
print('Sites com ranking diferente:', n_diff, 'de', len(df_via))

perm_idx = col_names.index('perm')
zeros_perm = int((X_via[:, perm_idx] == 0).sum())
print('Zeros em perm (X_via binarizado):', zeros_perm, 'de', len(df_via))

if n_diff > 0:
    diff_i = np.where((rank_saw_s != rank_prom_s).values)[0][:8]
    print('Primeiros divergentes:')
    for i in diff_i:
        pv = float(X_via[i, perm_idx])
        print('  site', via_idx[i],
              '| saw_r=', round(rank_saw_s.iloc[i], 1),
              '| prom_r=', round(rank_prom_s.iloc[i], 1),
              '| perm=', pv)
