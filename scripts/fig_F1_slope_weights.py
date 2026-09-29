"""F1 — Slope chart: nominal weights vs effective weights.

Message: under min-max all lines are horizontal (weights preserved).
         Under vector, perm shoots up (2.88x) and urban drops (0.53x).
         Under ranks, perm drops (0.62x), everyone else rises (+12%).

Double column (figure*).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig_utils import set_rcparams, savefig, COL2, WONG
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

set_rcparams()

# ── Data from tab:amplitude (corrected values) ──────────────────────────
criteria = ['perm','slope','roads','rivers','aspect',
            'coast','protected','wells','urban','aero','cult']
w_nom = dict(perm=0.152,slope=0.113,roads=0.030,rivers=0.091,aspect=0.075,
             coast=0.069,protected=0.066,wells=0.055,urban=0.166,
             aero=0.102,cult=0.081)

A = dict(
    mm  = {c: 1.000 for c in criteria},
    vec = dict(perm=0.583,slope=0.135,roads=0.206,rivers=0.265,aspect=0.103,
               coast=0.126,protected=0.105,wells=0.081,urban=0.107,
               aero=0.086,cult=0.171),
    rank= dict(perm=0.547,slope=0.995,roads=0.995,rivers=0.995,aspect=0.499,
               coast=0.995,protected=0.995,wells=0.995,urban=0.989,
               aero=0.995,cult=0.981),
)

def weff(w, a):
    denom = sum(w[c] * a[c] for c in w)
    return {c: w[c] * a[c] / denom * 100 for c in w}

we = {k: weff(w_nom, A[k]) for k in A}
# perm vec=43.79%, urban vec=8.78%, max=43.79%, perm rank=9.37%, urban rank=18.50%

norms_order = ["mm", "vec", "rank"]
norms_label = ["Min\u2013max", "Vector", "Ranks"]
x_positions = [0, 1, 2]

highlight = {
    "perm":   (WONG["blue"],   "perm"),
    "urban":  (WONG["vermil"], "urban"),
    "aspect": (WONG["green"],  "aspect"),
}
default_color = WONG["gray"]
default_alpha = 0.35

y_max = we["vec"]["perm"] * 1.08   # 43.79 * 1.08 ≈ 47%

fig, ax = plt.subplots(figsize=(COL2 * 0.80, COL2 * 0.40))

# Grey background lines
for c in criteria:
    if c in highlight:
        continue
    ys = [we[nk][c] for nk in norms_order]
    ax.plot(x_positions, ys, color=default_color, alpha=default_alpha,
            lw=0.9, zorder=1)

# Highlighted lines + annotations at Ranks endpoint
for c, (color, label) in highlight.items():
    ys = [we[nk][c] for nk in norms_order]
    ax.plot(x_positions, ys, color=color, lw=1.8, zorder=3,
            marker="o", markersize=4)
    # Ratio is relative to vector normalisation
    vec_y  = we["vec"][c]
    rank_y = we["rank"][c]
    ratio  = vec_y / (w_nom[c] * 100)
    # Label placed to right of Ranks point (x=2), at rank_y level
    # For perm, the label would be at 9.37% — unambiguous, no overlap
    ax.text(2.08, rank_y, f"{label}  ({ratio:.2f}\u00d7)",
            fontsize=7, color=color, va="center")

# Nominal weight dots at x=0
for c in criteria:
    color = highlight[c][0] if c in highlight else default_color
    alpha = 1.0 if c in highlight else default_alpha
    ax.scatter([0], [w_nom[c] * 100], color=color, alpha=alpha,
               s=14, zorder=4)

# Dashed reference lines at nominal w_j
for c, (color, _) in highlight.items():
    ax.axhline(w_nom[c] * 100, color=color, alpha=0.18, lw=0.7, ls="--")

ax.set_xticks(x_positions)
ax.set_xticklabels(norms_label, fontsize=8.5)
ax.set_ylabel("Effective weight (%)", labelpad=5)
ax.set_xlim(-0.25, 2.85)
ax.set_ylim(0, y_max)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}"))

# Legend — upper left to avoid right-side annotations
grey_patch  = mlines.Line2D([], [], color=default_color, alpha=0.7, lw=1,
                              label="Other criteria")
perm_patch  = mlines.Line2D([], [], color=WONG["blue"],   lw=1.8, label="perm")
urban_patch = mlines.Line2D([], [], color=WONG["vermil"], lw=1.8, label="urban")
asp_patch   = mlines.Line2D([], [], color=WONG["green"],  lw=1.8, label="aspect")
ax.legend(handles=[perm_patch, urban_patch, asp_patch, grey_patch],
          loc="upper left", fontsize=7)

fig.tight_layout(pad=0.4)
savefig(fig, "fig_F1_slope_weights")
