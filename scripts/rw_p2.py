# -*- coding: utf-8 -*-
"""
rw_p2.py — r_w (Pinto da Costa & Soares 2005) para SAW×ranks vs PROMETHEE II
Salva: results/rw_p2.csv
"""
import sys, os; sys.path.insert(0, '.')
import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix,
    saw_scores, promethee2_scores,
)

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
via_mask = df_imp[COL['protected']] > 0
df_via = df_imp[via_mask].copy()
w = np.array(list(AHP_WEIGHTS.values()))
X_via, benefit = _build_decision_matrix(df_via)
n = len(df_via)

# SAW sobre postos midrank normalizados [0,1]
R_mid = np.zeros_like(X_via, dtype=float)
for j in range(len(w)):
    x = X_via[:, j].astype(float)
    if not benefit[j]: x = -x
    r = rankdata(-x, method='average')
    lo, hi = r.min(), r.max()
    R_mid[:, j] = 1.0 - (r - lo) / (hi - lo) if hi > lo else 0.5

scores_saw = (R_mid * w).sum(axis=1)
scores_prom = promethee2_scores(df_via)

# Ranks para r_w (rank 1 = melhor)
rank_s = rankdata(-scores_saw,  method='average')
rank_p = rankdata(-scores_prom, method='average')

# r_w formula: Pinto da Costa & Soares 2005
# r_w = 1 - 6 * sum( d_i^2 * ((n - rank_s_i + 1) + (n - rank_p_i + 1)) ) / (n^4 + n^3 - n^2 - n)
d2 = (rank_s - rank_p) ** 2
weights_rw = (n - rank_s + 1) + (n - rank_p + 1)
num = 6.0 * float(np.sum(d2 * weights_rw))
den = float(n**4 + n**3 - n**2 - n)
rw = 1.0 - num / den

# Spearman simples para comparação
rho_sp, _ = spearmanr(scores_saw, scores_prom)

# Divergências no top-10 e top-3
top3_saw  = set(np.argsort(scores_saw)[-3:])
top3_prom = set(np.argsort(scores_prom)[-3:])
top10_saw  = set(np.argsort(scores_saw)[-10:])
top10_prom = set(np.argsort(scores_prom)[-10:])
jaccard3  = len(top3_saw  & top3_prom)  / len(top3_saw  | top3_prom)
jaccard10 = len(top10_saw & top10_prom) / len(top10_saw | top10_prom)

n_diff = int((rank_s != rank_p).sum())

print(f'n = {n}')
print(f'Spearman(SAW_ranks, PROMETHEE) = {rho_sp:.6f}')
print(f'r_w (Pinto da Costa 2005)      = {rw:.6f}')
print(f'Sites com ranking diferente    = {n_diff}/{n}')
print(f'Jaccard top-3  = {jaccard3:.4f}')
print(f'Jaccard top-10 = {jaccard10:.4f}')

out = pd.DataFrame([{
    'n': n,
    'spearman': round(rho_sp, 6),
    'rw': round(rw, 6),
    'n_rank_diff': n_diff,
    'jaccard_top3': round(jaccard3, 4),
    'jaccard_top10': round(jaccard10, 4),
}])
out.to_csv('results/rw_p2.csv', index=False)
print('Salvo em results/rw_p2.csv')
