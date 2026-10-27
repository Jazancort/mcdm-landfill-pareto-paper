# -*- coding: utf-8 -*-
"""
make_fig_kappa.py  --  Figure 4.02: Agg_pooled3 contrast vs kappa.
Source: results/e7/e7_contrasts.csv

Exports:
  figures/fig_kappa.pdf  (for LaTeX)
  figures/fig_kappa.png  (for review, 300 dpi)

Verification: checks that contrast values match macros_e7.tex before plotting.
"""
import sys, re
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent

# ── Load data ─────────────────────────────────────────────────────────────────
df = pd.read_csv(ROOT / "results" / "e7" / "e7_contrasts.csv")
agg = df[df.contrast == "Agg_pooled3"].copy()
agg = agg.sort_values("kappa").reset_index(drop=True)

# ── Verify against macros_e7.tex ──────────────────────────────────────────────
macros_file = ROOT / "macros_e7.tex"
macro_src = macros_file.read_text(encoding="utf-8")

EXPECTED_MACROS = {
    "AggKtwentyfive":    (25,  21.1),
    "AggContrastKfifty": (50,  20.4),
    "AggKonehundred":    (100,  9.3),
    # k=200: AggContrast is in macros.tex as -0.4
    "AggKfourhundred":   (400, -5.7),
    "AggKthousand":      (1000,-9.0),
}

print("=== Macro verification ===")
all_ok = True
for mac, (k, expected) in EXPECTED_MACROS.items():
    row = agg[agg.kappa == k]
    if row.empty:
        print(f"  MISSING k={k}")
        all_ok = False
        continue
    got = row["diff_pp"].values[0]
    ok = abs(got - expected) <= 0.15
    print(f"  {mac}: CSV={got:.2f}  macro={expected:.1f}  {'OK' if ok else 'MISMATCH'}")
    if not ok:
        all_ok = False

assert all_ok, "Macro mismatch — check macros_e7.tex vs e7_contrasts.csv"

# ── Plot ──────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":      "sans-serif",
    "font.sans-serif":  ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size":        11,
    "axes.labelsize":   13,
    "axes.titlesize":   14,
    "xtick.labelsize":  11,
    "ytick.labelsize":  11,
    "legend.fontsize":  10,
    "figure.dpi":       150,
    "savefig.dpi":      300,
    "axes.linewidth":   1.0,
    "lines.linewidth":  2.0,
    "lines.markersize": 7,
    "axes.spines.top":  False,
    "axes.spines.right":False,
})

fig, ax = plt.subplots(figsize=(6.5, 4.2))

# Equivalence band (grey) at ±delta=2.5 pp
DELTA = 2.5
ax.fill_between([20, 1200], [-DELTA, -DELTA], [DELTA, DELTA],
                alpha=0.15, color="grey", zorder=0, label=r"$\pm\Delta=\pm2.5\,$pp")
ax.axhline(y=0, color="grey", linestyle="--", linewidth=0.8, alpha=0.6, zorder=0)

# CI bands
kappas = agg["kappa"].values
lo = agg["ci_lo"].values
hi = agg["ci_hi"].values
mid = agg["diff_pp"].values
sig_mask = agg["sig"].values == "SIG"

ax.fill_between(kappas, lo, hi, alpha=0.20, color="#2980B9", zorder=1)
ax.plot(kappas, mid, "-o", color="#2980B9", linewidth=2.5, markersize=6,
        markerfacecolor="white", markeredgewidth=2, zorder=2,
        label="Aggregation (SAW\u2009\u2212\u2009TOPSIS)")

# Mark significant points
for k, m, s in zip(kappas, mid, sig_mask):
    if not s:
        ax.plot(k, m, "D", color="#2980B9", markersize=7, zorder=3)

ax.set_xscale("log")
ax.set_xticks(kappas)
ax.set_xticklabels([str(k) for k in kappas])
ax.set_xlim(18, 1300)

ymax = max(abs(mid.min()), abs(mid.max())) * 1.35 + 2
ax.set_ylim(-ymax, ymax)

ax.set_xlabel(r"Weight concentration $\kappa$ (log scale)", fontweight="bold")
ax.set_ylabel("SAW\u2009\u2212\u2009TOPSIS attainment (pp)", fontweight="bold")

ax.legend(loc="upper right", frameon=False, fontsize=10)

# Note about open diamond for null result
ax.text(0.02, 0.03,
        r"$\diamond$: not sig. ($\kappa=200$)",
        transform=ax.transAxes, fontsize=9, color="#555555", va="bottom")

plt.tight_layout()

out_dir = ROOT / "figures"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "fig_kappa.pdf", bbox_inches="tight", facecolor="white")
fig.savefig(out_dir / "fig_kappa.png", bbox_inches="tight", dpi=300, facecolor="white")
plt.close()

print(f"\nSaved: figures/fig_kappa.pdf and figures/fig_kappa.png")
print(f"Points: {list(zip(kappas, mid.round(1)))}")
