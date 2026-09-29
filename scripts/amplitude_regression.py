# -*- coding: utf-8 -*-
"""
amplitude_regression.py
Calcula A_{j,c} para as 3 normalizações e regride Q2[A'] contra D_c.
"""
import sys, os; sys.path.insert(0, '.')
import numpy as np
import pandas as pd
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix,
    INV, COST, F1_CRIT, F2_CRIT, F3_CRIT,
)

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
via_mask = df_imp[COL['protected']] > 0
df_via = df_imp[via_mask].copy()
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
X_via, benefit = _build_decision_matrix(df_via)
N = len(df_via)

# ─── Amplitude por normalização ───────────────────────────────────────────────
# min-max: X_via (benefício já alinhado pelo _build_decision_matrix)
A_mm = np.ones(len(w_ahp))  # por construção

# vector: x_raw / norm
Avec = np.zeros(len(w_ahp))
for j, k in enumerate(col_names):
    if k == 'aspect':
        raw = np.where((df_via[COL[k]].values >= 90) & (df_via[COL[k]].values <= 180), 0., 1.).astype(float)
    else:
        raw = df_via[COL[k]].values.astype(float)
    nv = np.sqrt((raw**2).sum()); nv = nv if nv > 0 else 1.
    v = raw / nv
    if not benefit[j]: v = -v
    Avec[j] = v.max() - v.min()

# ranks: midranks / (N+1)
# X_adj = benefício alinhado
X_adj = X_via.copy()
for j in range(len(w_ahp)):
    if not benefit[j]: X_adj[:, j] = 1. - X_via[:, j]

Arank = np.zeros(len(w_ahp))
for j in range(len(w_ahp)):
    r = pd.Series(X_adj[:, j]).rank(method='average').values / (N + 1)
    Arank[j] = r.max() - r.min()

print('=== Amplitude A_j por normalização ===')
print(f'{"Critério":12s}  {"w_ahp":6s}  {"A_mm":6s}  {"A_vec":6s}  {"A_rank":6s}')
for j, k in enumerate(col_names):
    print(f'{k:12s}  {w_ahp[j]:.4f}  {A_mm[j]:.4f}  {Avec[j]:.4f}  {Arank[j]:.4f}')

# TV (total variation) = sum_j w_j |A_j - 1|
TV_mm   = float(np.sum(w_ahp * np.abs(A_mm   - 1)))
TV_vec  = float(np.sum(w_ahp * np.abs(Avec   - 1)))
TV_rank = float(np.sum(w_ahp * np.abs(Arank  - 1)))
print(f'\nTV(mm)={TV_mm:.4f}  TV(vec)={TV_vec:.4f}  TV(rank)={TV_rank:.4f}')

# ─── Q2[A'] por célula de mc_18cells_raw ─────────────────────────────────────
mc = pd.read_csv(os.path.join('results', 'mc_18cells_raw.csv'))
# Filtrar as células relevantes: SAW e TOPSIS, kappa=200
cells_200 = mc[mc.alpha == 200].groupby(['agg', 'norm', 'mont'])['nd_Q2Ap'].mean().reset_index()
cells_200['Q2'] = cells_200['nd_Q2Ap'] * 100

# Mapear normalização -> TV
tv_map = {'minmax': TV_mm, 'vector': TV_vec, 'ranks': TV_rank}
cells_200['D'] = cells_200['norm'].map(tv_map)

print('\n=== Q2[A\'] por célula (kappa=200) ===')
print(cells_200[['agg','norm','mont','Q2','D']].to_string(index=False))

# ─── Regressão OLS: Q2 ~ D + kappa ───────────────────────────────────────────
# Incluir kappa=50 também para mais graus de liberdade
cells_50 = mc[mc.alpha == 50].groupby(['agg', 'norm', 'mont'])['nd_Q2Ap'].mean().reset_index()
cells_50['Q2'] = cells_50['nd_Q2Ap'] * 100
cells_50['D']  = cells_50['norm'].map(tv_map)
cells_50['kappa'] = 50

cells_200_k = cells_200.copy(); cells_200_k['kappa'] = 200
df_reg = pd.concat([cells_50, cells_200_k], ignore_index=True)

# Células válidas (excluir VIKOR×vector que é redundante por invariância afim)
df_reg = df_reg[~((df_reg.agg == 'vikor') & (df_reg.norm == 'vector'))]
print(f'\nTotal células na regressão: {len(df_reg)}')

# OLS manual: Q2 ~ intercept + beta*D + gamma*kappa_dummy
from numpy.linalg import lstsq
X_reg = np.column_stack([
    np.ones(len(df_reg)),
    df_reg['D'].values,
    (df_reg['kappa'] == 200).astype(float),
    (df_reg['mont'] == 'optimal').astype(float),
])
y_reg = df_reg['Q2'].values
coef, res, rank, sv = lstsq(X_reg, y_reg, rcond=None)
y_hat = X_reg @ coef
ss_res = ((y_reg - y_hat)**2).sum()
ss_tot = ((y_reg - y_reg.mean())**2).sum()
R2 = 1 - ss_res / ss_tot
n, p = len(y_reg), len(coef)
df_err = n - p
mse = ss_res / df_err if df_err > 0 else np.nan
# std errors
XtX_inv = np.linalg.pinv(X_reg.T @ X_reg)
se = np.sqrt(np.diag(XtX_inv) * mse) if df_err > 0 else np.full(p, np.nan)
t_stats = coef / se
from scipy.stats import t as t_dist
p_vals = 2 * t_dist.sf(np.abs(t_stats), df=df_err)

print(f'\n=== OLS: Q2 ~ intercept + D + kappa200_dummy + optimal_dummy ===')
print(f'n={n}  df_err={df_err}  R2={R2:.3f}')
labels = ['intercept', 'beta_D', 'gamma_kappa200', 'delta_optimal']
for lab, c, s, tv, pv in zip(labels, coef, se, t_stats, p_vals):
    print(f'  {lab:20s}: {c:+8.2f}  se={s:.2f}  t={tv:+.2f}  p={pv:.3f}')

# Regressão simples apenas D (marginal, sem controles)
X_simple = np.column_stack([np.ones(len(df_reg)), df_reg['D'].values])
coef_s, _, _, _ = lstsq(X_simple, y_reg, rcond=None)
yhat_s = X_simple @ coef_s
R2_s = 1 - ((y_reg - yhat_s)**2).sum() / ss_tot
df_err_s = len(y_reg) - 2
mse_s = ((y_reg - yhat_s)**2).sum() / df_err_s
se_s = np.sqrt(np.diag(np.linalg.pinv(X_simple.T @ X_simple) * mse_s))
t_s = coef_s / se_s
p_s = 2 * t_dist.sf(np.abs(t_s), df=df_err_s)
print(f'\n=== OLS simples: Q2 ~ intercept + D ===')
print(f'n={len(y_reg)}  df={df_err_s}  R2={R2_s:.3f}')
print(f'  intercept: {coef_s[0]:+.2f}  p={p_s[0]:.3f}')
print(f'  beta_D:    {coef_s[1]:+.2f}  p={p_s[1]:.3f}')

# Por médias marginais (3 pontos, conforme análise do usuário)
print('\n=== Médias marginais por normalização (kappa=200, SAW+TOPSIS, greedy+optimal) ===')
marg = cells_200.groupby('norm')['Q2'].mean().reset_index()
marg['D'] = marg['norm'].map(tv_map)
print(marg[['norm','Q2','D']].to_string(index=False))

# Salvar resultado
df_reg.to_csv(os.path.join('results', 'amplitude_regression.csv'), index=False)
print('\nSalvo: results/amplitude_regression.csv')
