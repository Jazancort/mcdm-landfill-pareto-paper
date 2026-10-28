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

# vector: rho_shift = 1/L2(mm_norm(x)) -- same as scoring.py / run_e1.py
Avec = np.zeros(len(w_ahp))
for j, k in enumerate(col_names):
    if k == 'aspect':
        # leeward [90,180] = 1 (beneficial, same as _build_decision_matrix)
        raw = np.where((df_via[COL[k]].values >= 90) & (df_via[COL[k]].values <= 180), 1., 0.).astype(float)
    else:
        raw = df_via[COL[k]].values.astype(float)
    # mm-norm (same as _build_decision_matrix)
    lo, hi = raw.min(), raw.max()
    mm = (raw - lo) / (hi - lo) if hi > lo else np.full(len(raw), 0.5)
    nv = np.sqrt((mm**2).sum())
    if nv < 1e-12:
        Avec[j] = 0.0
    else:
        Avec[j] = mm.max() - mm.min()   # = 1 always for mm-norm
        Avec[j] = 1.0 / nv              # rho_shift

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

from numpy.linalg import lstsq
from scipy.stats import t as t_dist

# TV (total variation) = (1/2) * sum_j |w_eff_j - w_j|
# Requires normalised weights (sum = 1).
def tv(A, w):
    w_norm = w / w.sum()                       # normalise to avoid wrong TV
    denom = np.sum(w_norm * A)
    weff = (w_norm * A) / denom
    return 0.5 * np.sum(np.abs(weff - w_norm))

TV_mm   = tv(A_mm,   w_ahp)
TV_vec  = tv(Avec,   w_ahp)
TV_rank = tv(Arank,  w_ahp)
print(f'\nTV(mm)={TV_mm:.4f}  TV(vec)={TV_vec:.4f}  TV(rank)={TV_rank:.4f}')

# Verify invariance: multiplying all A by 0.5 should not change TV
TV_mm_half   = tv(A_mm   * 0.5, w_ahp)
TV_vec_half  = tv(Avec   * 0.5, w_ahp)
TV_rank_half = tv(Arank  * 0.5, w_ahp)
print(f'TV invariance check (x0.5): mm={TV_mm_half:.4f} vec={TV_vec_half:.4f} rank={TV_rank_half:.4f}')

# ─── Q2[A'] por célula de mc_18cells_raw ─────────────────────────────────────
mc = pd.read_csv(os.path.join('results', 'mc_18cells_raw.csv'))
# Filtrar as células relevantes: SAW e TOPSIS, kappa=200
cells_200 = mc[mc.alpha == 200].groupby(['agg', 'norm', 'mont'])['nd_Q2Ap'].mean().reset_index()
cells_200['Q2'] = cells_200['nd_Q2Ap'] * 100

# Mapear normalização -> TV
tv_map = {'minmax': TV_mm, 'vector': TV_vec, 'ranks': TV_rank}
cells_200['TV'] = cells_200['norm'].map(tv_map)

print('\n=== Q2[A\'] por célula (kappa=200) ===')
print(cells_200[['agg','norm','mont','Q2','TV']].to_string(index=False))

# ─── SAW-only: escopo do Lema ─────────────────────────────────────────────────
saw_200 = cells_200[cells_200['agg'] == 'saw'].copy()
marg_saw = saw_200.groupby('norm').agg(Q2=('Q2','mean'), TV=('TV','first')).reset_index()
marg_saw = marg_saw.sort_values('TV')
print('\n=== SAW-only médias por normalização (kappa=200, escopo do Lema) ===')
print(marg_saw.to_string(index=False))

# OLS sobre 3 pontos SAW (médias marginais)
X_saw = np.column_stack([np.ones(3), marg_saw['TV'].values])
y_saw = marg_saw['Q2'].values
coef_saw, _, _, _ = lstsq(X_saw, y_saw, rcond=None)
yhat_saw = X_saw @ coef_saw
ss_res_saw = ((y_saw - yhat_saw)**2).sum()
ss_tot_saw = ((y_saw - y_saw.mean())**2).sum()
R2_saw = 1 - ss_res_saw / ss_tot_saw if ss_tot_saw > 0 else float('nan')
df_saw = len(y_saw) - 2
mse_saw = ss_res_saw / df_saw if df_saw > 0 else np.nan
se_saw = np.sqrt(np.diag(np.linalg.pinv(X_saw.T @ X_saw) * mse_saw)) if df_saw > 0 else [np.nan]*2
t_saw = coef_saw / se_saw
p_saw = 2 * t_dist.sf(np.abs(t_saw), df=df_saw)
print(f'\nOLS SAW-only: intercept={coef_saw[0]:.1f} pp  beta_TV={coef_saw[1]:.1f} pp/unit')
print(f'R2={R2_saw:.3f}  df={df_saw}  p(beta)={p_saw[1]:.3f}')
print('(n=3, df=1 — reportar ordenação, não coeficiente preditivo)')

# ─── Regressão OLS: Q2 ~ D + kappa ───────────────────────────────────────────
# Incluir kappa=50 também para mais graus de liberdade
cells_50 = mc[mc.alpha == 50].groupby(['agg', 'norm', 'mont'])['nd_Q2Ap'].mean().reset_index()
cells_50['Q2'] = cells_50['nd_Q2Ap'] * 100
cells_50['TV']    = cells_50['norm'].map(tv_map)
cells_50['kappa'] = 50

cells_200_k = cells_200.copy(); cells_200_k['kappa'] = 200
df_reg = pd.concat([cells_50, cells_200_k], ignore_index=True)

# Células válidas (excluir VIKOR×vector que é redundante por invariância afim)
df_reg = df_reg[~((df_reg.agg == 'vikor') & (df_reg.norm == 'vector'))]
print(f'\nTotal células na regressão completa: {len(df_reg)}')

X_reg = np.column_stack([
    np.ones(len(df_reg)),
    df_reg['TV'].values,
    (df_reg['kappa'] == 200).astype(float),
    (df_reg['mont'] == 'optimal').astype(float),
])
y_reg = df_reg['Q2'].values
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

print(f'\n=== OLS completa: Q2 ~ intercept + TV + kappa200_dummy + optimal_dummy ===')
print(f'n={n}  df_err={df_err}  R2={R2:.3f}')
labels = ['intercept', 'beta_D', 'gamma_kappa200', 'delta_optimal']
for lab, c, s, tv, pv in zip(labels, coef, se, t_stats, p_vals):
    print(f'  {lab:20s}: {c:+8.2f}  se={s:.2f}  t={tv:+.2f}  p={pv:.3f}')

# Regressão simples apenas D (marginal, sem controles)
X_simple = np.column_stack([np.ones(len(df_reg)), df_reg['TV'].values])
coef_s, _, _, _ = lstsq(X_simple, y_reg, rcond=None)
yhat_s = X_simple @ coef_s
R2_s = 1 - ((y_reg - yhat_s)**2).sum() / ss_tot
df_err_s = len(y_reg) - 2
mse_s = ((y_reg - yhat_s)**2).sum() / df_err_s
se_s = np.sqrt(np.diag(np.linalg.pinv(X_simple.T @ X_simple) * mse_s))
t_s = coef_s / se_s
p_s = 2 * t_dist.sf(np.abs(t_s), df=df_err_s)
print(f'\n=== OLS simples completa: Q2 ~ intercept + TV ===')
print(f'n={len(y_reg)}  df={df_err_s}  R2={R2_s:.3f}')
print(f'  intercept: {coef_s[0]:+.2f}  p={p_s[0]:.3f}')
print(f'  beta_TV:   {coef_s[1]:+.2f}  p={p_s[1]:.3f}')

# Por médias marginais (todas células)
print('\n=== Médias marginais por normalização (kappa=200) ===')
marg = cells_200.groupby('norm')['Q2'].mean().reset_index()
marg['TV'] = marg['norm'].map(tv_map)
print(marg[['norm','Q2','TV']].to_string(index=False))

# Salvar resultado
df_reg.to_csv(os.path.join('results', 'amplitude_regression.csv'), index=False)
print('\nSalvo: results/amplitude_regression.csv')
