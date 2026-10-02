# -*- coding: utf-8 -*-
"""
fig_E5_synthetic_grid.py — Figure: Q2_mm_greedy vs imposed TV_W for E5 synthetic grid

TV_W here is the amplitude spread parameter IMPOSED on the synthetic instance,
not derived from any particular normalisation. It measures within-group heterogeneity
of the amplitude vector used to scale both score and objectives.

Fogo reference: Q2_mm_greedy = 86.0% (from tab:tvorder, SAW/mm/greedy on Fogo).
TV_W_Fogo is NOT plotted on x-axis because Fogo's TV_W is computed from
min-max normalisation (TV_W(mm)=0 by construction — all A_j=1 within groups).
Instead, Fogo is shown as a horizontal reference line at Q2=86%.

The key message: Q2_mm_optimal=100% on all synthetic instances (Prop1);
Q2_mm_greedy varies with N and geometry, weakly with TV_W (r≈0).
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).parent.parent
df = pd.read_csv(ROOT / "results" / "e5" / "e5_grid_results.csv")

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 11,
    'axes.labelsize': 13,
    'axes.titlesize': 13,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'savefig.dpi': 300,
})

fig, axes = plt.subplots(1, 3, figsize=(13, 4.5), sharey=True)

geo_colors = {'uniform': '#0072B2', 'clustered': '#D55E00', 'grid': '#009E73'}
N_values = [50, 100, 200]

for ax, N in zip(axes, N_values):
    sub = df[df['N'] == N]
    for geo, color in geo_colors.items():
        g = sub[sub['geometry'] == geo]
        ax.scatter(g['TV_W'], g['Q2_mm_greedy'],
                   color=color, alpha=0.55, s=25,
                   label=geo if N == 50 else None)

    # Fogo reference: Q2_mm_greedy = 86.0% (horizontal line only — no TV_W x-ref)
    ax.axhline(86.0, color='black', linestyle=':', lw=1.5, alpha=0.7,
               label='Fogo (mm/grd=86%)' if N == 50 else None)
    ax.text(0.082, 87.5, 'Fogo\nmm/grd', fontsize=8, color='black', ha='right', va='bottom')

    # Regression line per panel
    x = sub['TV_W'].values
    y = sub['Q2_mm_greedy'].values
    if x.std() > 1e-5 and y.std() > 1e-5:
        m, b = np.polyfit(x, y, 1)
        xr = np.linspace(x.min(), x.max(), 50)
        ax.plot(xr, m * xr + b, color='gray', lw=1.5, ls='-', alpha=0.5)
        r = np.corrcoef(x, y)[0, 1]
        ax.text(0.003, 59, f'r = {r:+.2f}', fontsize=9, color='gray')

    ax.set_xlabel('Imposed $\\mathrm{TV}_W$ (amplitude spread)', fontweight='bold')
    ax.set_title(f'$N = {N}$ sites', fontweight='bold')
    ax.set_ylim(55, 105)
    ax.set_xlim(-0.005, 0.105)
    ax.yaxis.grid(True, alpha=0.3)

axes[0].set_ylabel('$Q_2$ min–max greedy (%)', fontweight='bold')

# Legend
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor=c, markersize=8, label=g)
    for g, c in geo_colors.items()
] + [Line2D([0], [0], color='black', lw=1.5, ls=':', label='Fogo Q2=86%')]
axes[0].legend(handles=legend_elements, loc='lower left', frameon=False, fontsize=9)

plt.suptitle(
    'E5: $Q_2$ min–max greedy vs imposed $\\mathrm{TV}_W$ across 405 synthetic instances\n'
    '$Q_2$ min–max optimal $=100\\%$ on all instances (not shown; Proposition~1 verified)',
    fontsize=10.5, y=1.02
)
plt.tight_layout()

out = ROOT / "figures"
plt.savefig(out / "fig_E5_synthetic.png", dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("Saved fig_E5_synthetic.png")
print(f"Fogo reference: Q2_mm_greedy = 86.0% (tab:tvorder)")
print(f"Note: Fogo TV_W(mm)=0 by construction (all A_j=1 in min-max); only Q2 reference shown")
print(f"TV_W on x-axis = imposed amplitude spread parameter (s_W), not derived from mm normalisation")
