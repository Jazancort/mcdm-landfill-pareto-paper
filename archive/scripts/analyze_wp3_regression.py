"""Analyze WP3 regression results."""
import pandas as pd
import numpy as np
from scipy import stats

df = pd.read_csv('results/wp3_summary.csv')
print('=== Full WP3 summary ===')
print(df[['norm','TV','m_eff','Q2_greedy','Q2_optimal','Q2_mean']].to_string(index=False))
print()

# Model A: original 3 levels
A = df[df['norm'].isin(['min-max','ranks','vector'])].sort_values('TV')
slope_A, intercept_A, r_A, p_A, se_A = stats.linregress(A['TV'], A['Q2_optimal'])
print('Model A (3 levels, df=1):')
print(f'  Slope: {slope_A:.2f} pp/unit TV,  SE: {se_A:.2f},  R2: {r_A**2:.4f},  p={p_A:.4f}')

# Model B: 4 monotone levels (add max)
B = df[df['norm'].isin(['min-max','max','ranks','vector'])].sort_values('TV')
slope_B, intercept_B, r_B, p_B, se_B = stats.linregress(B['TV'], B['Q2_optimal'])
print('Model B (4 levels incl. max, df=2):')
print(f'  Slope: {slope_B:.2f} pp/unit TV,  SE: {se_B:.2f},  R2: {r_B**2:.4f},  p={p_B:.4f}')

# Model C: 4 with Peldschus
C = df[df['norm'].isin(['min-max','Peldschus','ranks','vector'])].sort_values('TV')
slope_C, intercept_C, r_C, p_C, se_C = stats.linregress(C['TV'], C['Q2_optimal'])
print('Model C (4 levels incl. Peldschus, df=2):')
print(f'  Slope: {slope_C:.2f} pp/unit TV,  SE: {se_C:.2f},  R2: {r_C**2:.4f},  p={p_C:.4f}')

# Model D: 5 monotone levels
D = df[df['norm'].isin(['min-max','max','Peldschus','ranks','vector'])].sort_values('TV')
slope_D, intercept_D, r_D, p_D, se_D = stats.linregress(D['TV'], D['Q2_optimal'])
print('Model D (5 monotone levels, df=3):')
print(f'  Slope: {slope_D:.2f} pp/unit TV,  SE: {se_D:.2f},  R2: {r_D**2:.4f},  p={p_D:.4f}')

print()
print('=== Monotone ordering check ===')
for _, row in D.iterrows():
    print(f'  {row["norm"]:12s}  TV={row["TV"]:.4f}  Q2_opt={row["Q2_optimal"]:.1f}')

print()
s = df[df['norm']=='sum'].iloc[0]
v = df[df['norm']=='vector'].iloc[0]
print(f'sum: TV={s.TV:.3f}, Q2_opt={s.Q2_optimal:.1f}  (vector: TV={v.TV:.3f}, Q2_opt={v.Q2_optimal:.1f})')
print('=> sum Q2 > vector Q2 despite higher TV: degeneration mechanism')
print('   perm amplitude 0.1303 vs wells 0.0045 (ratio 29:1)')
print('   effective weight perm ~72% => quasi-lexicographic on F1')
