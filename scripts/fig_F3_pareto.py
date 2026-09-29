"""F3 — Pareto frontier projections with canonical portfolios overlaid.

Three 2-D projections: (F1,F2), (F1,F3), (F2,F3).
Frontier points in grey; canonical portfolios colour-coded by gap=0 / gap>0.

Double column (figure*).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig_utils import set_rcparams, savefig, COL2, WONG
import csv
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

set_rcparams()

here = os.path.dirname(os.path.abspath(__file__))

# ── Load Pareto frontier (space A') ─────────────────────────────────────
pareto = []
with open(os.path.join(here, "results", "pareto_front_Aprime.csv")) as f:
    for r in csv.DictReader(f):
        pareto.append((float(r["F1P"]), float(r["F2P"]), float(r["F3P"])))

F1p = [p[0] for p in pareto]
F2p = [p[1] for p in pareto]
F3p = [p[2] for p in pareto]

# ── Canonical portfolios from tab:canonical (space A, evaluator A') ──────
# Columns: label, f1_A, f2_A, f3_A, in_A_213, gap_A, f1_P, f2_P, f3_P, in_Aprime, gap_P
canonical = []
with open(os.path.join(here, "results", "space_aprime_canonical.csv")) as f:
    for r in csv.DictReader(f):
        canonical.append({
            "label": r["label"],
            "f1": float(r["f1_P"]), "f2": float(r["f2_P"]), "f3": float(r["f3_P"]),
            "in_front": r["in_Aprime"].strip().lower() in ("true", "1"),
            "gap": float(r["gap_P"]),
        })

# ── Layout: 1 row × 3 cols ───────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(COL2, COL2 * 0.35))

projections = [
    (0, 1, r"$F_1$ (cost, min)", r"$F_2$ (impact, min)"),
    (0, 2, r"$F_1$ (cost, min)", r"$F_3$ (safety, max)"),
    (1, 2, r"$F_2$ (impact, min)", r"$F_3$ (safety, max)"),
]
coords = [F1p, F2p, F3p]
labels_panel = ["(a)", "(b)", "(c)"]

for ax, (xi, yi, xlabel, ylabel), lbl in zip(axes, projections, labels_panel):
    # Frontier
    ax.scatter(coords[xi], coords[yi],
               color=WONG["gray"], s=6, alpha=0.4, zorder=1,
               linewidths=0)

    # Canonical portfolios
    for c in canonical:
        cx = [F1p, F2p, F3p][xi]
        cy = [F1p, F2p, F3p][yi]
        x_val = c["f1"] if xi == 0 else (c["f2"] if xi == 1 else c["f3"])
        y_val = c["f1"] if yi == 0 else (c["f2"] if yi == 1 else c["f3"])

        color  = WONG["blue"] if c["in_front"] else WONG["vermil"]
        marker = "D"          if c["in_front"] else "X"
        ax.scatter([x_val], [y_val],
                   color=color, marker=marker, s=30, zorder=5,
                   linewidths=0.5, edgecolors="white")

    ax.set_xlabel(xlabel, fontsize=7.5)
    ax.set_ylabel(ylabel, fontsize=7.5)
    ax.tick_params(labelsize=7)
    ax.text(0.04, 0.96, lbl, transform=ax.transAxes,
            fontsize=8, fontweight="bold", va="top")

# ── Legend ───────────────────────────────────────────────────────────────
from matplotlib.lines import Line2D
handles = [
    mpatches.Patch(color=WONG["gray"],   alpha=0.5, label=f"Pareto frontier ($n={len(pareto)}$)"),
    Line2D([0],[0], marker="D", color="w", markerfacecolor=WONG["blue"],
           markersize=6, label="Canonical: Pareto-efficient (gap=0)"),
    Line2D([0],[0], marker="X", color="w", markerfacecolor=WONG["vermil"],
           markersize=6, label="Canonical: dominated (gap>0)"),
]
fig.legend(handles=handles, loc="lower center", ncol=3,
           bbox_to_anchor=(0.5, -0.10), fontsize=7.5)

fig.tight_layout(pad=0.4, w_pad=0.8)
savefig(fig, "fig_F3_pareto")
