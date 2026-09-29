"""F1 — Slope chart: nominal vs effective weights, Intervention Window style."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig_utils import set_rcparams, savefig, COL2, WONG, C_TREATMENT, C_BASELINE, C_ORANGE, C_GREEN, C_GRAY
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

set_rcparams()

criteria = ['perm','slope','roads','rivers','aspect',
            'coast','protected','wells','urban','aero','cult']
w_nom = dict(perm=0.152, slope=0.113, roads=0.030, rivers=0.091, aspect=0.075,
             coast=0.069, protected=0.066, wells=0.055, urban=0.166,
             aero=0.102, cult=0.081)
A = dict(
    mm  = {c: 1.000 for c in criteria},
    vec = dict(perm=0.583, slope=0.135, roads=0.206, rivers=0.265, aspect=0.103,
               coast=0.126, protected=0.105, wells=0.081, urban=0.107,
               aero=0.086, cult=0.171),
    rank= dict(perm=0.547, slope=0.995, roads=0.995, rivers=0.995, aspect=0.499,
               coast=0.995, protected=0.995, wells=0.995, urban=0.989,
               aero=0.995, cult=0.981),
)

def weff(w, a):
    d = sum(w[c] * a[c] for c in w)
    return {c: w[c] * a[c] / d * 100 for c in w}

we = {k: weff(w_nom, A[k]) for k in A}

highlight = {
    "perm":   (C_TREATMENT, "perm"),
    "urban":  (C_BASELINE,  "urban"),
    "aspect": (C_GREEN,     "aspect"),
}
norms_order = ["mm", "vec", "rank"]
norms_label = ["Min\u2013max", "Vector", "Ranks"]
x = [0, 1, 2]
y_max = we["vec"]["perm"] * 1.08

fig, ax = plt.subplots(figsize=(COL2 * 0.82, COL2 * 0.44))

# Grey background lines
for c in criteria:
    if c in highlight:
        continue
    ys = [we[k][c] for k in norms_order]
    ax.plot(x, ys, color=C_GRAY, alpha=0.30, lw=1.2, zorder=1)

# Highlighted lines
for c, (color, label) in highlight.items():
    ys = [we[k][c] for k in norms_order]
    ax.plot(x, ys, color=color, lw=2.5, zorder=3,
            marker="o", markersize=6)
    vec_y  = we["vec"][c]
    rank_y = we["rank"][c]
    ratio  = vec_y / (w_nom[c] * 100)
    ax.text(2.06, rank_y, f"{label}  ({ratio:.2f}\u00d7)",
            fontsize=11, color=color, va="center")

# Nominal dots at x=0
for c in criteria:
    color = highlight[c][0] if c in highlight else C_GRAY
    alpha = 1.0 if c in highlight else 0.30
    ax.scatter([0], [w_nom[c] * 100], color=color, alpha=alpha,
               s=18, zorder=4, linewidths=0)

# Dashed reference at nominal level
for c, (color, _) in highlight.items():
    ax.axhline(w_nom[c] * 100, color=color, alpha=0.15, lw=0.8, ls="--")

ax.set_xticks(x)
ax.set_xticklabels(norms_label, fontsize=13)
ax.set_ylabel("Effective weight (%)", fontweight="bold")
ax.set_xlim(-0.25, 2.82)
ax.set_ylim(0, y_max)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}"))

# Legend
grey_line  = mlines.Line2D([], [], color=C_GRAY, alpha=0.6, lw=1.5,
                            label="Other criteria")
perm_line  = mlines.Line2D([], [], color=C_TREATMENT, lw=2.5, label="perm")
urban_line = mlines.Line2D([], [], color=C_BASELINE,  lw=2.5, label="urban")
asp_line   = mlines.Line2D([], [], color=C_GREEN,     lw=2.5, label="aspect")
ax.legend(handles=[perm_line, urban_line, asp_line, grey_line],
          loc="upper center", bbox_to_anchor=(0.5, -0.11),
          ncol=4, frameon=False)

plt.tight_layout(pad=0.5)
plt.subplots_adjust(bottom=0.16)
savefig(fig, "fig_F1_slope_weights")
