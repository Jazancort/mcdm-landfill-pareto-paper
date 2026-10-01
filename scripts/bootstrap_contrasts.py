# -*- coding: utf-8 -*-
"""
bootstrap_contrasts.py — Bootstrap emparelhado dos 5 contrastes do factorial (2³)
e TOST da agregação, a partir de mc_2cube_fixed_raw.csv (pipeline correcto).

Contrastes:
  C1: Normalização (min-max − vector)
  C2: Assembly (óptima − greedy)
  C3: Agregação (SAW − TOPSIS)
  C4: Assembly dentro de min-max
  C5: Assembly dentro de vector
  C6: Normalização só em greedy

TOST para C3 (agregação): delta=2pp (relevância mínima para publicação)
"""
import pandas as pd, numpy as np
from scipy.stats import ttest_rel

df_raw = pd.read_csv('/home/julioazancort/scratch/mcdm-landfill-pareto/results/mc_2cube_fixed_raw.csv')
df = df_raw[df_raw.alpha == 200].copy()

N_DRAWS = df['draw'].nunique()
N_BOOT  = 10000
rng     = np.random.default_rng(42)

# Pivot: (draw) × (agg, norm, mont) → 0/1
pv = df.pivot_table(index='draw', columns=['agg','norm','mont'], values='nd_Q2Ap')
# convenience getter
def col(agg, norm, mont):
    return pv[agg][norm][mont].values.astype(float)

# All 8 cells
cells = {
    'SAW/mm/grd' : col('saw','minmax','greedy'),
    'SAW/mm/opt' : col('saw','minmax','optimal'),
    'SAW/vec/grd': col('saw','vector','greedy'),
    'SAW/vec/opt': col('saw','vector','optimal'),
    'TOP/mm/grd' : col('topsis','minmax','greedy'),
    'TOP/mm/opt' : col('topsis','minmax','optimal'),
    'TOP/vec/grd': col('topsis','vector','greedy'),
    'TOP/vec/opt': col('topsis','vector','optimal'),
}

means = {k: v.mean()*100 for k,v in cells.items()}
print("="*70)
print("Cell means:")
for k, v in means.items():
    print(f"  {k}: {v:.2f}%")

def contrast_per_draw(a_draws, b_draws):
    """Per-draw difference (a - b) in pp."""
    return (a_draws - b_draws) * 100

def bootstrap_ci(diff_draws, n_boot=N_BOOT):
    boot = np.array([rng.choice(diff_draws, size=len(diff_draws), replace=True).mean()
                     for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    # p-value: min(P(mean>=0), P(mean<=0)) * 2
    p = 2 * min(np.mean(boot >= 0), np.mean(boot <= 0))
    return boot.mean(), lo, hi, p

# ── Define contrasts per draw ──────────────────────────────────────────────────
# Normalisation: average of (mm - vec) across all 4 (agg × mont) combos
d_norm = contrast_per_draw(
    0.25*(cells['SAW/mm/grd']+cells['SAW/mm/opt']+cells['TOP/mm/grd']+cells['TOP/mm/opt']),
    0.25*(cells['SAW/vec/grd']+cells['SAW/vec/opt']+cells['TOP/vec/grd']+cells['TOP/vec/opt'])
)
# Assembly: average of (opt - grd) across all 4 (agg × norm) combos
d_asm = contrast_per_draw(
    0.25*(cells['SAW/mm/opt']+cells['SAW/vec/opt']+cells['TOP/mm/opt']+cells['TOP/vec/opt']),
    0.25*(cells['SAW/mm/grd']+cells['SAW/vec/grd']+cells['TOP/mm/grd']+cells['TOP/vec/grd'])
)
# Aggregation: average of (SAW - TOPSIS) across all 4 (norm × mont) combos
d_agg = contrast_per_draw(
    0.25*(cells['SAW/mm/grd']+cells['SAW/mm/opt']+cells['SAW/vec/grd']+cells['SAW/vec/opt']),
    0.25*(cells['TOP/mm/grd']+cells['TOP/mm/opt']+cells['TOP/vec/grd']+cells['TOP/vec/opt'])
)
# Assembly within min-max: average of (opt - grd) in mm
d_asm_mm = contrast_per_draw(
    0.5*(cells['SAW/mm/opt']+cells['TOP/mm/opt']),
    0.5*(cells['SAW/mm/grd']+cells['TOP/mm/grd'])
)
# Assembly within vector: average of (opt - grd) in vec
d_asm_vec = contrast_per_draw(
    0.5*(cells['SAW/vec/opt']+cells['TOP/vec/opt']),
    0.5*(cells['SAW/vec/grd']+cells['TOP/vec/grd'])
)
# Normalisation for greedy only
d_norm_grd = contrast_per_draw(
    0.5*(cells['SAW/mm/grd']+cells['TOP/mm/grd']),
    0.5*(cells['SAW/vec/grd']+cells['TOP/vec/grd'])
)

contrasts = [
    ('C1  Normalisation (mm−vec)',       d_norm),
    ('C2  Assembly (opt−grd)',           d_asm),
    ('C3  Aggregation (SAW−TOPSIS)',     d_agg),
    ('C4  Assembly within mm',          d_asm_mm),
    ('C5  Assembly within vector',      d_asm_vec),
    ('C6  Normalisation (greedy only)', d_norm_grd),
]

print("\n" + "="*70)
print("Bootstrap emparelhado dos contrastes (alpha=200, N=500 draws)")
print(f"{'Contrast':<35} {'Obs mean':>9} {'95% CI':>22} {'p':>8}")
print("-"*70)
for label, d in contrasts:
    mn, lo, hi, p = bootstrap_ci(d)
    print(f"  {label:<35} {mn:>+9.2f}pp [{lo:+.2f},{hi:+.2f}]pp {p:>8.4f}")

# ── TOST for C3 (aggregation) ─────────────────────────────────────────────────
print("\n" + "="*70)
print("TOST for Aggregation (SAW − TOPSIS), delta=2pp")
delta_tost = 2.0
# TOST: two one-sided t-tests on the per-draw differences
t_lo, p_lo = ttest_rel(d_agg, -delta_tost * np.ones(len(d_agg)), alternative='greater')
t_hi, p_hi = ttest_rel(d_agg,  delta_tost * np.ones(len(d_agg)), alternative='less')
p_tost = max(p_lo, p_hi)
print(f"  Observed mean: {d_agg.mean():+.2f}pp")
print(f"  H0 (lower): effect < −{delta_tost}pp | p = {p_lo:.4f}")
print(f"  H0 (upper): effect > +{delta_tost}pp | p = {p_hi:.4f}")
print(f"  TOST p-value (max) = {p_tost:.4f}")
if p_tost < 0.05:
    print(f"  CONCLUSION: |Aggregation effect| < {delta_tost}pp (p<0.05) — equivalence established")
else:
    print(f"  CONCLUSION: Cannot establish equivalence at delta={delta_tost}pp")

# ── Summary table (matches tab:effects format) ────────────────────────────────
print("\n" + "="*70)
print("Summary for tab:effects update")
print(f"{'Contrast':<35} {'Artigo actual':>14} {'Novo':>10} {'95% CI':>22}")
print("-"*70)
old = {
    'C1': '+29.9', 'C2': '+16.0', 'C3': '+0.9',
    'C4': '+29.8', 'C5': '+2.2',  'C6': '+16.1'
}
new_vals = [(label, bootstrap_ci(d)) for label, d in contrasts]
for (label, d), key in zip(new_vals, ['C1','C2','C3','C4','C5','C6']):
    mn, lo, hi, p = bootstrap_ci(d)
    print(f"  {label:<35} {old[key]:>14} {mn:>+10.1f}pp [{lo:+.1f},{hi:+.1f}]pp")
