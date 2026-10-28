"""F2 — Normalisation × Assembly interaction, Intervention Window style."""
import sys, os, csv, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig_utils import set_rcparams, savefig, COL1, C_TREATMENT, C_BASELINE, C_GREEN
from collections import defaultdict
import matplotlib.pyplot as plt

set_rcparams()

here = os.path.dirname(os.path.abspath(__file__))
cells = defaultdict(list)
with open(os.path.join(here, "results", "mc_18cells_raw.csv"), newline="") as f:
    for r in csv.DictReader(f):
        cells[(r["norm"], r["mont"])].append(float(r["nd_Q2Ap"]))

def mean_ci(vals, z=1.96):
    n = len(vals); mu = sum(vals)/n
    return mu * 100, z * math.sqrt(mu*(1-mu)/n) * 100

norms_cfg = [
    ("minmax", "Min\u2013max", C_TREATMENT, "o"),
    ("vector", "Vector",      C_BASELINE,  "s"),
    ("ranks",  "Ranks",       C_GREEN,     "^"),
]
assembly_keys   = ["greedy", "optimal"]
assembly_labels = ["Greedy", "Optimal"]
x = [0, 1]

fig, ax = plt.subplots(figsize=(COL1 * 1.3, COL1 * 1.1))

for nk, label, color, marker in norms_cfg:
    means, cis = [], []
    for ak in assembly_keys:
        mu, ci = mean_ci(cells[(nk, ak)])
        means.append(mu); cis.append(ci)
    ax.plot(x, means, marker=marker, markersize=7, color=color,
            label=label, lw=2.5, zorder=3)
    for xi, (mu, ci) in enumerate(zip(means, cis)):
        ax.errorbar(xi, mu, yerr=ci, color=color, capsize=4,
                    lw=1.2, zorder=3)
    # Gain annotation at optimal
    gain = means[1] - means[0]
    ax.annotate(f"{gain:+.1f} pp",
                xy=(1, means[1]), xytext=(1.07, means[1]),
                fontsize=11, color=color, va="center")

ax.set_xticks(x)
ax.set_xticklabels(assembly_labels, fontsize=13)
ax.set_xlim(-0.22, 1.55)
ax.set_ylim(35, 100)
ax.set_ylabel(r"$Q_2[\mathcal{A}']$ (%)", fontweight="bold")
ax.set_xlabel("Assembly", fontweight="bold")
ax.text(0.02, 0.03, "Error bars: 95% CI",
        transform=ax.transAxes, fontsize=10, color="#666666")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14),
          ncol=3, frameon=False)

plt.tight_layout(pad=0.5)
plt.subplots_adjust(bottom=0.22)
savefig(fig, "fig_F2_interaction")
