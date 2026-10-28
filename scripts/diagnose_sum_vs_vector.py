# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, 'scripts')
import numpy as np
import pandas as pd
if 'MCDM_DATA_DIR' not in os.environ and os.path.exists('/home/julioazancort/scratch/mcdm'):
    os.environ['MCDM_DATA_DIR'] = '/home/julioazancort/scratch/mcdm'

from mcdm_experiment import load_data, impute_nan, COL, AHP_WEIGHTS

df_raw = pd.read_csv('results/wp3_mc_results.csv')

# Find draws where vector was dominated, but sum was non-dominated
vec_dom = df_raw[(df_raw.norm == 'vector') & (df_raw.nd_optimal == 0)].set_index('draw')
sum_nd  = df_raw[(df_raw.norm == 'sum') & (df_raw.nd_optimal == 1)].set_index('draw')
common_draws = vec_dom.index.intersection(sum_nd.index)
print("Draws where vector optimal is dominated, but sum optimal is non-dominated: %d / 500" % len(common_draws))

# Find draws where sum was dominated, but vector was non-dominated
sum_dom = df_raw[(df_raw.norm == 'sum') & (df_raw.nd_optimal == 0)].set_index('draw')
vec_nd  = df_raw[(df_raw.norm == 'vector') & (df_raw.nd_optimal == 1)].set_index('draw')
common_rev = sum_dom.index.intersection(vec_nd.index)
print("Draws where sum optimal is dominated, but vector optimal is non-dominated: %d / 500" % len(common_rev))

# Print top 5 most frequent trios for vector vs sum
print("\nTop 5 optimal trios for vector:")
print(df_raw[df_raw.norm == 'vector']['trio_o'].value_counts().head(5))

print("\nTop 5 optimal trios for sum:")
print(df_raw[df_raw.norm == 'sum']['trio_o'].value_counts().head(5))

print("\nTop 5 optimal trios for min-max:")
print(df_raw[df_raw.norm == 'min-max']['trio_o'].value_counts().head(5))
