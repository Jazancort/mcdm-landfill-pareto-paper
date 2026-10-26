"""F3 — Pareto frontier projections, Intervention Window style."""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig_utils import set_rcparams, savefig, COL2, WONG, C_TREATMENT, C_BASELINE, C_GRAY
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches

set_rcparams()

here = os.path.dirname(os.path.abspath(__file__))

pareto = []
with open(os.path.join(here, "results", "pareto_front_Aprime.csv")) as f:
    for r in csv.DictReader(f):
        pareto.append((float(r["F1P"]), float(r["F2P"]), float(r["F3P"])))

canonical = []
with open(os.path.join(here, "results", "space_aprime_canonical.csv")) as f:
    for r in csv.DictReader(f):
        canonical.append({
            "f1": float(r["f1_P"]), "f2": float(r["f2_P"]), "f3": float(r["f3_P"]),
            "in_front": r["in_Aprime"].strip().lower() in ("true","1"),
        })

F = [[p[i] for p in pareto] for i in range(3)]
C = [[c["f1"], c["f2"], c["f3"]] for c in canonical]

projections = [
    (0, 1, r"$F_1$ (cost, min)", r"$F_2$ (impact, min)"),
    (0, 2, r"$F_1$ (cost, min)", r"$F_3$ (safety, max)"),
    (1, 2, r"$F_2$ (impact, min)", r"$F_3$ (safety, max)"),
]
panel_labels = ["(a)", "(b)", "(c)"]

fig, axes = plt.subplots(1, 3, figsize=(COL2, COL2 * 0.40))

for ax, (xi, yi, xlabel, ylabel), plbl in zip(axes, projections, panel_labels):
    # Frontier
    ax.scatter(F[xi], F[yi], color=C_GRAY, s=10, alpha=0.40,
               linewidths=0, zorder=1)
    # Canonical
    for c_dict, row in zip(canonical, C):
        xv = row[xi]; yv = row[yi]
        if c_dict["in_front"]:
            ax.scatter([xv], [yv], color=C_TREATMENT,
                       marker="D", s=55, zorder=5, linewidths=0.6,
                       edgecolors="white")
        else:
            ax.scatter([xv], [yv], color=C_BASELINE,
                       marker="X", s=55, zorder=5, linewidths=0.6,
                       edgecolors="white")

    ax.set_xlabel(xlabel, fontweight="bold")
    ax.set_ylabel(ylabel, fontweight="bold")
    ax.text(0.05, 0.95, plbl, transform=ax.transAxes,
            fontsize=14, fontweight="bold", va="top")

handles = [
    mpatches.Patch(color=C_GRAY, alpha=0.5,
                   label=f"Pareto frontier ($n={len(pareto)}$)"),
    mlines.Line2D([],[],marker="D",color="w",markerfacecolor=C_TREATMENT,
                  markersize=8, label="Canonical: efficient (gap=0)"),
    mlines.Line2D([],[],marker="X",color="w",markerfacecolor=C_BASELINE,
                  markersize=8, label="Canonical: dominated (gap>0)"),
]
fig.legend(handles=handles,
           loc="upper center", bbox_to_anchor=(0.5, -0.04),
           ncol=3, frameon=False)

plt.tight_layout(pad=0.5, w_pad=1.0)
plt.subplots_adjust(bottom=0.18)
savefig(fig, "fig_F3_pareto")
