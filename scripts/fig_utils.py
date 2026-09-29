"""fig_utils.py — shared rcParams, palette and helpers.

Visual style: matches Intervention Window paper exactly.
  - font.size=11, labels 13pt bold, titles 14pt bold
  - linewidth=2.0, markersize=6, markevery=2
  - legend below, horizontal, frameon=False
  - spines top/right removed
  - shaded error bands alpha=0.15
  - white background

Elsevier CAS-DC column widths (inches):
  COL1 = 3.54 in  (90 mm)   — single column
  COL2 = 7.48 in  (190 mm)  — double column (figure*)

For Elsevier at 190mm, font.size=11 renders at ~8pt after 50% reduction
which meets the 6pt minimum. For 90mm figures (COL1) font.size=9 is used.
All sizes are set per-figure via the size argument to plt.subplots.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── Column widths (inches) ───────────────────────────────────────────────
COL1 = 3.54   # 90 mm  — single column
COL2 = 7.48   # 190 mm — double column (figure*)

# ── Wong colorblind-safe palette ─────────────────────────────────────────
# Matches Intervention Window exactly
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

# Semantic aliases used in Intervention Window
C_BASELINE  = "#C0392B"   # red-brown (A_baseline)
C_TREATMENT = "#2980B9"   # blue      (W6_d20 / min-max)
C_ORANGE    = "#E67E22"   # orange    (Qwen / vector)
C_GREEN     = "#009E73"   # green     (ranks)
C_GRAY      = "#7F8C8D"   # gray      (neutral / other)
C_PURPLE    = "#8E44AD"   # purple    (secondary)

# Zone backgrounds (retention zones — Intervention Window style)
C_HOMEOSTATIC = "#E8F6F3"   # >80% — green mint
C_BOUNDED     = "#FEF9E7"   # 60-80% — yellow
C_DEGRADATIVE = "#FDEDEC"   # <60% — pink

# ── rcParams — IDENTICAL to Intervention Window ──────────────────────────
def set_rcparams():
    plt.rcParams.update({
        "font.family":        "sans-serif",
        "font.sans-serif":    ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size":          11,          # Intervention Window standard
        "axes.labelsize":     13,
        "axes.titlesize":     14,
        "xtick.labelsize":    11,
        "ytick.labelsize":    11,
        "legend.fontsize":    11,
        "figure.dpi":         150,
        "savefig.dpi":        300,
        "axes.linewidth":     1.0,
        "lines.linewidth":    2.0,
        "lines.markersize":   6,
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "legend.frameon":     False,
        "axes.grid":          False,
    })

# ── Legend helpers ────────────────────────────────────────────────────────
def legend_below(ax, ncol=None, y_offset=-0.12, **kwargs):
    """Legend below the axes, horizontal, no frame — Intervention Window style."""
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        return
    if ncol is None:
        ncol = min(len(handles), 5)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, y_offset),
        ncol=ncol,
        frameon=False,
        **kwargs,
    )

def legend_below_fig(fig, axes, ncol=None, y_offset=-0.04, **kwargs):
    """Shared legend below a multi-panel figure."""
    handles, labels = [], []
    for ax in (axes if hasattr(axes, '__iter__') else [axes]):
        h, l = ax.get_legend_handles_labels()
        for hi, li in zip(h, l):
            if li not in labels:
                handles.append(hi)
                labels.append(li)
    if ncol is None:
        ncol = min(len(handles), 5)
    fig.legend(
        handles, labels,
        loc="upper center",
        bbox_to_anchor=(0.5, y_offset),
        ncol=ncol,
        frameon=False,
        **kwargs,
    )

# ── Error band helper ─────────────────────────────────────────────────────
def plot_line(ax, x, mean, se=None, color=None, marker="o", label=None,
              lw=2.0, alpha_band=0.15, markevery=2, linestyle="-", **kwargs):
    """Plot line + shaded error band, Intervention Window style."""
    if se is not None:
        ax.fill_between(x, mean - se, mean + se,
                        alpha=alpha_band, color=color)
    ax.plot(x, mean,
            linestyle=linestyle,
            marker=marker,
            color=color,
            linewidth=lw,
            markersize=6,
            markevery=markevery,
            label=label,
            **kwargs)

# ── Zone backgrounds ──────────────────────────────────────────────────────
def add_retention_zones(ax, y_max=105):
    """Add homeostatic/bounded/degradative background zones."""
    ax.axhspan(80, y_max, alpha=0.6, color=C_HOMEOSTATIC, zorder=0)
    ax.axhspan(60, 80,    alpha=0.6, color=C_BOUNDED,     zorder=0)
    ax.axhspan(0,  60,    alpha=0.6, color=C_DEGRADATIVE, zorder=0)

# ── Onset line ────────────────────────────────────────────────────────────
def add_onset(ax, x, label="", color="gray"):
    ax.axvline(x=x, color=color, linestyle="--", linewidth=1.0, alpha=0.6)
    if label:
        ylim = ax.get_ylim()
        ax.text(x + 0.1, ylim[1] * 0.97, label,
                fontsize=10, color="#555555", va="top")

# ── Save helper ───────────────────────────────────────────────────────────
def savefig(fig, name, fig_dir=None):
    """Save PDF + PNG 300dpi to figures/ dir."""
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
