"""Generate Figure: normalisation × assembly interaction plot.

Two lines (min-max and vector normalisation), x-axis = assembly
(greedy vs optimal), y-axis = Q2[A'] mean across draws and aggregation
methods.  The crossing pattern is the paper's key interaction finding.

Output: figures/fig_interaction.pdf  (for LaTeX)
        figures/fig_interaction.png  (300 dpi, for review)
"""
import csv, math, os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── rcParams (Elsevier / journal standard) ─────────────────────────────
plt.rcParams.update({
    'font.family':       'sans-serif',
    'font.sans-serif':   ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size':         10,
    'axes.labelsize':    11,
    'axes.titlesize':    11,
    'xtick.labelsize':   10,
    'ytick.labelsize':   10,
    'legend.fontsize':   10,
    'figure.dpi':        150,
    'savefig.dpi':       300,
    'axes.linewidth':    0.8,
    'lines.linewidth':   1.8,
    'lines.markersize':  7,
    'axes.spines.top':   False,
    'axes.spines.right': False,
})

# ── Load data ───────────────────────────────────────────────────────────
here = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(here, "results", "mc_18cells_raw.csv")

cells = defaultdict(list)
with open(csv_path, newline="") as f:
    for r in csv.DictReader(f):
        key = (r["norm"], r["mont"])
        cells[key].append(float(r["nd_Q2Ap"]))

def mean_ci(vals, z=1.96):
    n  = len(vals)
    mu = sum(vals) / n
    se = math.sqrt(mu * (1 - mu) / n)
    return mu, z * se

# ── Extract means ───────────────────────────────────────────────────────
norms = {
    "minmax": ("Min\u2013max", "#0072B2"),   # blue  (Wong palette)
    "vector": ("Vector",   "#D55E00"),   # vermillion
    "ranks":  ("Ranks",    "#009E73"),   # green
}
assembly_labels = ["Greedy", "Optimal"]
assembly_keys   = ["greedy", "optimal"]

results = {}
for nk in norms:
    means, cis = [], []
    for ak in assembly_keys:
        mu, ci = mean_ci(cells[(nk, ak)])
        means.append(mu * 100)
        cis.append(ci * 100)
    results[nk] = (means, cis)

# ── Plot ────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(5.0, 3.6))   # Elsevier single-column ~90 mm

x = [0, 1]
x_labels = assembly_labels

for nk, (label, color) in norms.items():
    means, cis = results[nk]
    ax.plot(x, means, marker="o", color=color, label=label, zorder=3)
    for xi, (mu, ci) in enumerate(zip(means, cis)):
        ax.errorbar(xi, mu, yerr=ci, color=color, capsize=4,
                    linewidth=1.2, zorder=3)

# ── Annotations: gains ──────────────────────────────────────────────────
for nk, (label, color) in norms.items():
    means, _ = results[nk]
    gain = means[1] - means[0]
    # Place label to the right of the "Optimal" point
    ax.annotate(
        f"{gain:+.1f} pp",
        xy=(1, means[1]),
        xytext=(1.06, means[1]),
        fontsize=8.5, color=color, va="center",
    )

# ── Axes ────────────────────────────────────────────────────────────────
ax.set_xticks(x)
ax.set_xticklabels(x_labels)
ax.set_xlim(-0.25, 1.45)
ax.set_ylim(35, 100)
ax.set_ylabel(r"$Q_2[\mathcal{A}']$ (%)", labelpad=6)
ax.set_xlabel("Assembly", labelpad=6)
ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%g'))

# ── Legend ──────────────────────────────────────────────────────────────
handles = [
    mpatches.Patch(color=norms[nk][1], label=norms[nk][0])
    for nk in norms
]
ax.legend(handles=handles, loc="lower left", frameon=False)

# ── Caption note ────────────────────────────────────────────────────────
ax.text(0.02, 0.02,
        "Error bars: 95% CI (proportion, normal approx.)",
        transform=ax.transAxes, fontsize=7.5, color="#555555",
        va="bottom")

plt.tight_layout(pad=0.5)

# ── Save ────────────────────────────────────────────────────────────────
out_dir = os.path.join(os.path.dirname(here), "figures")
os.makedirs(out_dir, exist_ok=True)

pdf_path = os.path.join(out_dir, "fig_interaction.pdf")
png_path = os.path.join(out_dir, "fig_interaction.png")
plt.savefig(pdf_path, bbox_inches="tight", facecolor="white")
plt.savefig(png_path, bbox_inches="tight", dpi=300, facecolor="white")
plt.close()

print(f"Saved: {pdf_path}")
print(f"Saved: {png_path}")

# ── Print table ─────────────────────────────────────────────────────────
print("\nCell means (Q2[A'] %):")
for nk, (label, _) in norms.items():
    means, cis = results[nk]
    gain = means[1] - means[0]
    print(f"  {label:8s}  greedy={means[0]:.1f}%  optimal={means[1]:.1f}%"
          f"  gain={gain:+.1f} pp")
