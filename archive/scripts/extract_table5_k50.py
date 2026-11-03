# -*- coding: utf-8 -*-
"""extract_table5_k50.py -- Extract Q2 per cell at k50 for Table 5.
Cross-checks k200 values against macros.tex.
"""
import pandas as pd, numpy as np

df = pd.read_csv('results/fourthcell/mc_2cube_fixed_raw.csv')

print('=== Table 5 Q2 values (from mc_2cube_fixed_raw.csv) ===')
for kappa in [50, 200]:
    dfk = df[df['alpha'] == kappa]
    grp = dfk.groupby(['norm','agg','mont'])['nd_Q2Ap'].agg(['mean','sem']).reset_index()
    grp['Q2'] = (grp['mean'] * 100).round(1)
    grp['SE'] = (grp['sem'] * 100).round(1)
    print(f'\nkappa={kappa}:')
    for _, row in grp.iterrows():
        label = f"{row['norm']:6}/{row['agg']:6}/{row['mont']:7}"
        print(f'  {label}: Q2={row["Q2"]:5.1f}% SE=({row["SE"]:.1f})')

# Cross-check k200 vs macros
print('\n=== Cross-check kappa=200 vs macros ===')
macro_k200 = {
    ('minmax','saw','greedy'): 86.0,
    ('minmax','saw','optimal'): 100.0,
    ('minmax','topsis','greedy'): 94.4,
    ('minmax','topsis','optimal'): 96.6,
    ('vector','saw','greedy'): 66.2,
    ('vector','saw','optimal'): 56.8,
    ('vector','topsis','greedy'): 63.4,
    ('vector','topsis','optimal'): 52.4,
}
for (norm, agg, mont), macro_val in macro_k200.items():
    mask = (df['alpha']==200) & (df['norm']==norm) & (df['agg']==agg) & (df['mont']==mont)
    data_val = df[mask]['nd_Q2Ap'].mean() * 100
    diff = abs(data_val - macro_val)
    status = 'OK' if diff < 0.15 else 'MISMATCH'
    print(f'  [{status}] {norm}/{agg}/{mont}: macro={macro_val}, data={data_val:.1f}')

# Check AggContrastKfifty
print('\n=== AggContrastKfifty check ===')
saw50 = df[(df['alpha']==50) & (df['agg']=='saw')].set_index(['draw','norm','mont'])['nd_Q2Ap']
topsis50 = df[(df['alpha']==50) & (df['agg']=='topsis')].set_index(['draw','norm','mont'])['nd_Q2Ap']
paired = saw50 - topsis50
print(f'Paired mean k50: {paired.mean()*100:.2f} pp (SE={paired.sem()*100:.2f})')
print('Macro AggContrastKfifty = +20.4 -- MISMATCH if data shows ~17.2')
print('ACTION REQUIRED: verify which value is correct before submission')
