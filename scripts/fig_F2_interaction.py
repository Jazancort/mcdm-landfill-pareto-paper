"""F2 — Normalisation x Assembly interaction (replaces tab:factorial).

Three lines (min-max, vector, ranks) across greedy vs optimal.
Points are means over all aggregation methods and MC draws.
Single column (90 mm).

This version supersedes fig_interaction.py (which was committed earlier
as a draft). The final version uses the same data but with proper
rcParams from fig_utils.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig_utils import set_rcparams, savefig, COL1, WONG
import csv, math
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

set_rcparams()

here  = os.path.dirname(os.path.abspath(__file__))
root  = os.path.dirname(here)
csv_p = os.path.join(here, "results", "mc_18cells_raw.csv")

cells = defaultdict(list)
with open(csv_p, newline="") as f:
    for r in csv.DictReader(f):
        cells[(r["norm"], r["mont"])].append(float(r["nd_Q2Ap"]))

def mean_ci(vals, z=1.96):
    n = len(vals); mu = sum(vals)/n
    return mu * 100, z * math.sqrt(mu*(1-mu)/n) * 100

norms_cfg = [
    ("minmax", "Min–max", WONG["blue"]),
    ("vector", "Vector",  WONG["vermil"]),
    ("ranks",  "Ranks",   WONG["green"]),
]
assembly_keys   = ["greedy", "optimal"]
assembly_labels = ["Greedy", "Optimal"]
x = [0, 1]

fig, ax = plt.subplots(figsize=(COL1, COL1 * 0.80))

for nk, label, color in norms_cfg:
    means, cis = [], []
    for ak in assembly_keys:
        mu, ci = mean_ci(cells[(nk, ak)])
        means.append(mu); cis.append(ci)
    ax.plot(x, means, marker="o", markersize=5, color=color,
            label=label, lw=1.6, zorder=3)
    for xi, (mu, ci) in enumerate(zip(means, cis)):
        ax.errorbar(xi, mu, yerr=ci, color=color,
                    capsize=3, lw=1.0, zorder=3)
    # Gain annotation at optimal side
    gain = means[1] - means[0]
    ax.annotate(f"{gain:+.1f} pp",
                xy=(1, means[1]), xytext=(1.05, means[1]),
                fontsize=7, color=color, va="center")

ax.set_xticks(x)
ax.set_xticklabels(assembly_labels)
ax.set_xlim(-0.22, 1.45)
ax.set_ylim(35, 100)
ax.set_ylabel(r"$Q_2[\mathcal{A}']$ (%)")
ax.set_xlabel("Assembly")
ax.legend(loc="lower left", fontsize=7.5, ncol=1)
ax.text(0.02, 0.02, "Error bars: 95% CI",
        transform=ax.transAxes, fontsize=6.5, color="#666666")

fig.tight_layout(pad=0.4)
savefig(fig, "fig_F2_interaction")
