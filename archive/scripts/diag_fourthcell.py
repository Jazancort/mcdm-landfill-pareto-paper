# -*- coding: utf-8 -*-
import sys, os; sys.path.insert(0, '.')
import numpy as np, pandas as pd
from mcdm_experiment import load_data, impute_nan, COL, AHP_WEIGHTS

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
via_mask = df_imp[COL['protected']] > 0
df_via = df_imp[via_mask].copy()
w = np.array(list(AHP_WEIGHTS.values()))
col_names = list(AHP_WEIGHTS.keys())

# === ITEM 1: A_j pela eq refsetA ===
print('=== A_j pela eq refsetA (amplitude 389 / amplitude 473) ===')
A_refset = np.zeros(len(w))
for j, k in enumerate(col_names):
    col = COL[k]
    if k == 'aspect':
        x389 = np.where((df_via[col].values >= 90) & (df_via[col].values <= 180), 0., 1.)
        x473 = np.where((df_imp[col].values >= 90) & (df_imp[col].values <= 180), 0., 1.)
    else:
        x389 = df_via[col].values.astype(float)
        x473 = df_imp[col].values.astype(float)
    amp389 = x389.max() - x389.min()
    amp473 = x473.max() - x473.min()
    A_j = amp389 / amp473 if amp473 > 0 else 1.0
    A_refset[j] = A_j
    print(f'  {k:12s}  amp389={amp389:.4f}  amp473={amp473:.4f}  A_j={A_j:.4f}')

denom = np.sum(w * A_refset)
weff_refset = (w * A_refset) / denom
TV_refset = 0.5 * np.sum(np.abs(weff_refset - w))
print(f'\nTV(refset 473 to 389) = {TV_refset:.4f}')
print('Comparacao: TV(vec)=0.3245  TV(rank)=0.0911  TV(mm)=0.0000')

# === ITEM 2: verificar 76.5% ranks ===
mc = pd.read_csv(os.path.join('results', 'mc_18cells_raw.csv'))
print('\n=== Verificacao 76.5% ranks ===')
for alpha in [200, 50]:
    for mont in ['greedy', 'optimal']:
        sub = mc[(mc.alpha == alpha) & (mc.norm == 'ranks') & (mc.agg == 'saw') & (mc.mont == mont)]
        if len(sub) > 0:
            q2 = sub.nd_Q2Ap.mean() * 100
            print(f'  kappa={alpha} ranks {mont}: n={len(sub)} Q2={q2:.1f}%')
    sub_both = mc[(mc.alpha == alpha) & (mc.norm == 'ranks') & (mc.agg == 'saw')]
    q2_both = sub_both.nd_Q2Ap.mean() * 100
    print(f'  kappa={alpha} ranks BOTH: Q2={q2_both:.1f}%')

print('\nCelulas ranks no mc_18cells:')
print(mc[mc.norm == 'ranks'].groupby(['agg', 'norm', 'mont'])['nd_Q2Ap'].mean().mul(100).round(1))
