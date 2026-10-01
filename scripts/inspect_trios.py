# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, 'scripts')
import numpy as np
import pandas as pd

df = pd.read_csv('results/wp3_mc_results.csv')
print("Total rows:", len(df))
print(df.groupby('norm')[['nd_greedy', 'nd_optimal']].mean())

# Look at overlap of trios with min-max
df_mm = df[df.norm == 'min-max'].set_index('draw')
for nm in ['max', 'ranks', 'vector', 'sum']:
    sub = df[df.norm == nm].set_index('draw')
    same_g = (sub['trio_g'] == df_mm['trio_g']).mean()
    same_o = (sub['trio_o'] == df_mm['trio_o']).mean()
    print("%-12s: same greedy as mm = %5.1f%%, same optimal as mm = %5.1f%%" % (
        nm, same_g * 100, same_o * 100
    ))
