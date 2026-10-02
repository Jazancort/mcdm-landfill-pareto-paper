# -*- coding: utf-8 -*-
"""
fig_E5_synthetic_grid.py — Figure: Q2_mm_greedy vs TV_W for E5 synthetic grid
Shows that TV_W is not a robust predictor across synthetic instances,
but geometry and N matter. Fogo is shown as reference point.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).parent.parent
df = pd.read_csv(ROOT / "results" / "e5" / "e5_grid_results.csv")

# Style
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
N_markers  = {50: 'o', 100: 's', 200: '^'}

for ax, N in zip(axes, [50, 100, 200]):
    sub = df[df['N'] == N]
    for geo, color in geo_colors.items():
        g = sub[sub['geometry'] == geo]
        ax.scatter(g['TV_W'], g['Q2_mm_greedy'],
                   color=color, alpha=0.55, s=25, marker=N_markers[N],
                   label=geo if N == 50 else None)

    # Fogo reference
    ax.axvline(0.032, color='black', linestyle='--', lw=1.2, alpha=0.6)
    ax.axhline(66.2, color='black', linestyle=':', lw=1.2, alpha=0.6)
    ax.text(0.033, 63, 'Fogo', fontsize=9, color='black', ha='left')

    # Regression line
    x = sub['TV_W'].values
    y = sub['Q2_mm_greedy'].values
    if x.std() > 1e-5:
        m, b = np.polyfit(x, y, 1)
        xr = np.linspace(x.min(), x.max(), 50)
        ax.plot(xr, m*xr + b, color='gray', lw=1.5, ls='-', alpha=0.6)
        r = np.corrcoef(x, y)[0, 1]
        ax.text(0.005, 72, f'r={r:.2f}', fontsize=9, color='gray')

    ax.set_xlabel('TV$_W$ (within-group amplitude variation)', fontweight='bold')
    ax.set_title(f'N = {N} sites', fontweight='bold')
    ax.set_ylim(55, 105)
    ax.set_xlim(-0.005, 0.105)
    ax.yaxis.grid(True, alpha=0.3)

axes[0].set_ylabel('$Q_2$ min–max greedy (%)', fontweight='bold')

# Legend
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor=c, markersize=8, label=g)
    for g, c in geo_colors.items()
]
axes[0].legend(handles=legend_elements, loc='lower right', frameon=False, fontsize=9)

plt.suptitle(
    'E5 synthetic grid: TV$_W$ vs $Q_2$ greedy across 405 instances\n'
    '(Q$_2$ mm-optimal = 100% on all instances; Fogo reference shown)',
    fontsize=11, y=1.02
)
plt.tight_layout()

out = ROOT / "figures"
plt.savefig(out / "fig_E5_synthetic.png", dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig(out / "fig_E5_synthetic.pdf", bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved figures/fig_E5_synthetic.png and .pdf")
