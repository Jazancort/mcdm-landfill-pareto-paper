# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, 'scripts')
import numpy as np
import pandas as pd
if 'MCDM_DATA_DIR' not in os.environ and os.path.exists('/home/julioazancort/scratch/mcdm'):
    os.environ['MCDM_DATA_DIR'] = '/home/julioazancort/scratch/mcdm'

from mcdm_experiment import load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL['protected']] > 0].copy()
N = len(df_via)
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=float)
crit_names = list(AHP_WEIGHTS.keys())

X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j2, b in enumerate(benefit):
    if not b: X_adj[:, j2] = 1.0 - X_via[:, j2]

# If sum norm is applied to X_adj:
sums_adj = X_adj.sum(0)
A_sum_adj = (X_adj.max(0) - X_adj.min(0)) / sums_adj
num = w_ahp * A_sum_adj
weff_sum_adj = num / num.sum()
tv_sum_adj = 0.5 * np.abs(weff_sum_adj - w_ahp).sum()

# If sum norm is applied to X_via:
sums_via = X_via.sum(0)
A_sum_via = (X_via.max(0) - X_via.min(0)) / sums_via
num = w_ahp * A_sum_via
weff_sum_via = num / num.sum()
tv_sum_via = 0.5 * np.abs(weff_sum_via - w_ahp).sum()

print("TV(sum on raw X):    0.56693")
print("TV(sum on X_via):    %.5f" % tv_sum_via)
print("TV(sum on X_adj):    %.5f" % tv_sum_adj)
print("\nA_j (sum on X_adj):", dict(zip(crit_names, A_sum_adj.round(4))))
print("A_j (sum on X_via):", dict(zip(crit_names, A_sum_via.round(4))))
