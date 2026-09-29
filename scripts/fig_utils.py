"""fig_utils.py — shared rcParams, palette and helpers for all paper figures.

Elsevier CAS-DC specs (Omega):
  single column : 90 mm  → 3.54 in
  double column : 190 mm → 7.48 in
  min font size : 7 pt (normal), 6 pt (sub/superscript)
  format        : PDF vectorial + PNG 300 dpi
  palette       : Wong (colorblind-safe)
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── Elsevier column widths (inches) ─────────────────────────────────────
COL1 = 3.54   # 90 mm
COL2 = 7.48   # 190 mm

# ── Wong colorblind-safe palette ────────────────────────────────────────
WONG = {
    "black":   "#000000",
    "orange":  "#E69F00",
    "sky":     "#56B4E9",
    "green":   "#009E73",
    "yellow":  "#F0E442",
    "blue":    "#0072B2",
    "vermil":  "#D55E00",
    "purple":  "#CC79A7",
    "gray":    "#999999",
}

# ── rcParams ─────────────────────────────────────────────────────────────
def set_rcparams():
    plt.rcParams.update({
        "font.family":        "sans-serif",
        "font.sans-serif":    ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size":          8,
        "axes.labelsize":     9,
        "axes.titlesize":     9,
        "xtick.labelsize":    8,
        "ytick.labelsize":    8,
        "legend.fontsize":    8,
        "figure.dpi":         150,
        "savefig.dpi":        300,
        "axes.linewidth":     0.7,
        "lines.linewidth":    1.4,
        "lines.markersize":   5,
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "legend.frameon":     False,
        "axes.grid":          False,
    })

# ── Save helper ──────────────────────────────────────────────────────────
def savefig(fig, name, fig_dir=None):
    """Save PDF + PNG to figures/ dir relative to the paper root."""
    if fig_dir is None:
        here = os.path.dirname(os.path.abspath(__file__))
        fig_dir = os.path.join(os.path.dirname(here), "figures")
    os.makedirs(fig_dir, exist_ok=True)
    pdf = os.path.join(fig_dir, name + ".pdf")
    png = os.path.join(fig_dir, name + ".png")
    fig.savefig(pdf, bbox_inches="tight", facecolor="white")
    fig.savefig(png, bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)
    print(f"  saved {pdf}")
    print(f"  saved {png}")
