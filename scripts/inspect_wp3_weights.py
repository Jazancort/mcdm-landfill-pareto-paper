# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, 'scripts')
import numpy as np
import pandas as pd
if 'MCDM_DATA_DIR' not in os.environ and os.path.exists('/home/julioazancort/scratch/mcdm'):
    os.environ['MCDM_DATA_DIR'] = '/home/julioazancort/scratch/mcdm'

from mcdm_experiment import load_data, impute_nan, COL, AHP_WEIGHTS

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL['protected']] > 0].copy()
N = len(df_via)
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=float)
crit_names = list(AHP_WEIGHTS.keys())

# Build raw X
X_raw = np.zeros((N, len(w_ahp)), dtype=float)
for j, k in enumerate(crit_names):
    col = COL[k]
    vals = df_via[col].values.astype(float)
    if k == 'aspect':
        X_raw[:, j] = np.where((vals >= 90) & (vals <= 180), 1.0, 0.0)
    else:
        X_raw[:, j] = vals

# Compute Aj for vector and sum
norms_raw = np.sqrt((X_raw**2).sum(0))
A_vec = (X_raw.max(0) - X_raw.min(0)) / norms_raw

sums_raw = X_raw.sum(0)
A_sum = (X_raw.max(0) - X_raw.min(0)) / sums_raw

# Effective weights
w_eff_vec = (w_ahp * A_vec) / (w_ahp * A_vec).sum()
w_eff_sum = (w_ahp * A_sum) / (w_ahp * A_sum).sum()

# Groups: G1 = perm, slope, roads; G2 = rivers, aspect, coast, protected, wells; G3 = urban, aero, cult
g1_idx = [0, 1, 2]
g2_idx = [3, 4, 5, 6, 7]
g3_idx = [8, 9, 10]

for j, k in enumerate(crit_names):
    grp = 'G1' if j in g1_idx else ('G2' if j in g2_idx else 'G3')
    f_vec = w_eff_vec[j] / w_ahp[j]
    f_sum = w_eff_sum[j] / w_ahp[j]
    print("%-12s %-5s %6.3f %6.3f %9.4f %9.2fx %6.4f %9.4f %9.2fx" % (
        k, grp, w_ahp[j], A_vec[j], w_eff_vec[j], f_vec, A_sum[j], w_eff_sum[j], f_sum
    ))

print("\n--- Group Sums of Effective Weights ---")
print("Group G1 (siting):    AHP=%.3f  vec=%.3f  sum=%.3f" % (w_ahp[g1_idx].sum(), w_eff_vec[g1_idx].sum(), w_eff_sum[g1_idx].sum()))
print("Group G2 (envir):     AHP=%.3f  vec=%.3f  sum=%.3f" % (w_ahp[g2_idx].sum(), w_eff_vec[g2_idx].sum(), w_eff_sum[g2_idx].sum()))
print("Group G3 (social):    AHP=%.3f  vec=%.3f  sum=%.3f" % (w_ahp[g3_idx].sum(), w_eff_vec[g3_idx].sum(), w_eff_sum[g3_idx].sum()))
