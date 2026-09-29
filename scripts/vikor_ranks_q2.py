# -*- coding: utf-8 -*-
"""
vikor_ranks_q2.py — Q2[A'] para VIKOR×ranks, índices locais corretos
Salva: results/vikor_ranks_q2.csv
"""
import sys, os; sys.path.insert(0, '.')
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix,
    haversine_km, greedy_trio, optimal_trio_enumerate, MIN_DIST_KM,
    INV, COST, F1_CRIT, F2_CRIT, F3_CRIT,
)

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
via_mask = df_imp[COL['protected']] > 0
df_via = df_imp[via_mask].copy()
w = np.array(list(AHP_WEIGHTS.values()))
col_names = list(AHP_WEIGHTS.keys())
X_via, benefit = _build_decision_matrix(df_via)
D = haversine_km(df_via['latitude (degrees)'].values, df_via['longitude (degrees)'].values)
N = len(df_via)

# Fronteira A' — índices LOCAIS (0-388), objetivos já calculados
front_df = pd.read_csv(os.path.join('results', 'pareto_front_Aprime.csv'))
F1_front = front_df['F1P'].values
F2_front = front_df['F2P'].values
F3_front = front_df['F3P'].values
front_sets = [frozenset([int(r.idx1), int(r.idx2), int(r.idx3)])
              for _, r in front_df.iterrows()]

def _norm(x, ref):
    lo, hi = ref.min(), ref.max()
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x)

def compute_objs_local(ref_df):
    """Calcula f1/f2/f3 por site (índices locais) com normalização sobre ref_df."""
    f1v = np.zeros(N, dtype=float)
    f2v = np.zeros(N, dtype=float)
    f3v = np.zeros(N, dtype=float)
    for j, k in enumerate(col_names):
        col = COL[k]
        x   = df_via[col].values.astype(float)
        ref = ref_df[col].values.astype(float)
        if k == 'aspect':
            c = np.where((x >= 90) & (x <= 180), 0., 1.)
        elif k in INV:
            c = 1. - _norm(x, ref)
        elif k in COST:
            c = _norm(x, ref)
        else:
            c = _norm(x, ref)
        c = c * w[j]
        if k in F1_CRIT: f1v += c
        elif k in F2_CRIT: f2v += c
        else: f3v += c
    return f1v, f2v, f3v

f1v, f2v, f3v = compute_objs_local(df_via)  # ref = 389

def trio_nd(i, j, k):
    """True se o trio (i,j,k) é não-dominado na fronteira A'."""
    f1t = f1v[i] + f1v[j] + f1v[k]
    f2t = f2v[i] + f2v[j] + f2v[k]
    f3t = f3v[i] + f3v[j] + f3v[k]
    dom = ((F1_front <= f1t + 1e-9) & (F2_front <= f2t + 1e-9) & (F3_front >= f3t - 1e-9) &
           ((F1_front < f1t - 1e-9) | (F2_front < f2t - 1e-9) | (F3_front > f3t + 1e-9)))
    return not dom.any()

def in_front(i, j, k):
    return frozenset([i, j, k]) in front_sets

# Postos normalizados [0,1], rank1=1.0
Rraw = np.zeros_like(X_via, dtype=float)
for j in range(len(w)):
    x = X_via[:, j].astype(float)
    if not benefit[j]: x = -x
    r = rankdata(-x, method='average')
    lo, hi = r.min(), r.max()
    Rraw[:, j] = 1.0 - (r - lo) / (hi - lo) if hi > lo else 0.5

v_p = 0.5
fstar  = Rraw.max(axis=0)
fminus = Rraw.min(axis=0)
denom  = np.abs(fstar - fminus); denom[denom == 0] = 1.
nd_mat = np.abs(fstar - Rraw) / denom
Sv = (w * nd_mat).sum(axis=1)
Rv = (w * nd_mat).max(axis=1)

def n01(a):
    lo, hi = a.min(), a.max()
    return np.zeros(len(a)) if hi == lo else (a - lo) / (hi - lo)

Q_v = v_p * n01(Sv) + (1 - v_p) * n01(Rv)
scores_vr = 1.0 - Q_v

print('VIKOR×ranks scores: min=', round(scores_vr.min(), 4), 'max=', round(scores_vr.max(), 4))

rows = []
for alpha in [50, 200]:
    tg = greedy_trio(scores_vr, D, MIN_DIST_KM)
    to = optimal_trio_enumerate(scores_vr, D, MIN_DIST_KM)

    nd_g = trio_nd(*tg)
    nd_o = trio_nd(*to)
    in_g = in_front(*tg)
    in_o = in_front(*to)

    # Q2 = 1 se na fronteira, 0 se dominado, 0.5 se nd mas não na fronteira
    q2g = 1.0 if in_g else (0.5 if nd_g else 0.0)
    q2o = 1.0 if in_o else (0.5 if nd_o else 0.0)

    print(f'alpha={alpha}:')
    print(f'  greedy  {tg} nd={nd_g} in_front={in_g} Q2~={q2g}')
    print(f'  optimal {to} nd={nd_o} in_front={in_o} Q2~={q2o}')

    rows.extend([
        {'alpha': alpha, 'mont': 'greedy',  'trio_local': str(tg), 'nd': nd_g, 'in_front': in_g, 'q2_approx': q2g},
        {'alpha': alpha, 'mont': 'optimal', 'trio_local': str(to), 'nd': nd_o, 'in_front': in_o, 'q2_approx': q2o},
    ])

print()
print('Nota: Q2 aqui é proxy binário. Para Q2 exacto (22.0%/34.8%) ver mc_18cells_raw.csv.')
out = pd.DataFrame(rows)
out.to_csv('results/vikor_ranks_q2.csv', index=False)
print('Salvo em results/vikor_ranks_q2.csv')
