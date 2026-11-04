# -*- coding: utf-8 -*-
"""make_fig_kappa.py — K6 (SAW-TOPSIS aggregation contrast) vs kappa.

Three curves: Fogo, Santiago S-T, Santiago S-N.
  - Fogo: line + CI shading (from macros_e7.tex and macros.tex — authoritative E7 run).
  - Santiago: points only (K6_per_kappa from santiago_predictions_v2.json, no CI).
    JSON SHA-verified before reading.
  - kappa=inf: separate markers (not connected to main curve).

Usage:
    uv run python scripts/make_fig_kappa.py

Output:
    figures/fig_kappa_santiago.pdf
    figures/fig_kappa_santiago.png  (300 DPI)
"""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

ROOT     = Path(__file__).parent.parent
JSON_PATH = ROOT / "results" / "santiago" / "santiago_predictions_v2.json"
OUT_DIR  = ROOT / "figures"

SHA_JSON = "1fbc412b8ace6bdbd07d74f890f1460a2acdc268ce45ed59fc2a7900e520cf80"

# ── SHA-verify JSON ────────────────────────────────────────────────────────────
got = hashlib.sha256(JSON_PATH.read_bytes()).hexdigest()
if got != SHA_JSON:
    raise RuntimeError(f"JSON SHA mismatch: got {got}")
print(f"  SHA OK: santiago_predictions_v2.json ({SHA_JSON[:16]})")

data = json.loads(JSON_PATH.read_text(encoding="utf-8"))

def get_pred(branch, name):
    for p in data[branch]["predictions"]:
        if p["prediction"] == name:
            return p
    raise KeyError(name)

# ── Data ───────────────────────────────────────────────────────────────────────
KAPPAS_STOCH = [25, 50, 100, 200, 400, 1000]

# Fogo K6 (SAW-TOPSIS Agg_pooled3) from authoritative E7 run (macros_e7.tex + macros.tex)
FOGO_K6 = {25: 21.1, 50: 20.4, 100: 9.3, 200: -0.4, 400: -5.7, 1000: -9.0}
FOGO_LO = {25: 18.5, 50: 17.7, 100:  7.1, 200: -2.2, 400: -7.3, 1000: -10.5}
FOGO_HI = {25: 23.9, 50: 23.2, 100: 11.6, 200:  1.3, 400: -4.1, 1000:  -7.5}
FOGO_INF = 0.0   # macros_kappa_inf.tex (K6 at kappa=inf)

# Santiago K6 from JSON (K6_per_kappa in S4/K5 prediction)
def get_k6(branch):
    p = get_pred(branch, "S4")
    return {int(k): v for k, v in p["K6_per_kappa"].items()}, p["K6_inf"]

st_k6, st_inf = get_k6("S-T")
sn_k6, sn_inf = get_k6("S-N")

# ── Plot settings ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":        "sans-serif",
    "font.sans-serif":    ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size":          10,
    "axes.labelsize":     11,
    "axes.titlesize":     11,
    "legend.fontsize":    9,
    "xtick.labelsize":    9,
    "ytick.labelsize":    9,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "savefig.dpi":        300,
    "figure.dpi":         150,
})

COL_FOGO = "#1f77b4"   # blue
COL_ST   = "#d62728"   # red
COL_SN   = "#2ca02c"   # green
ALPHA_CI = 0.15

fig, ax = plt.subplots(figsize=(6.5, 3.8))

xk = np.array(KAPPAS_STOCH)

# Fogo line + CI shading
fogo_y  = np.array([FOGO_K6[k] for k in KAPPAS_STOCH])
fogo_lo = np.array([FOGO_LO[k] for k in KAPPAS_STOCH])
fogo_hi = np.array([FOGO_HI[k] for k in KAPPAS_STOCH])
ax.plot(xk, fogo_y, color=COL_FOGO, lw=1.8, marker="o", ms=5, label="Fogo")
ax.fill_between(xk, fogo_lo, fogo_hi, color=COL_FOGO, alpha=ALPHA_CI)

# Santiago S-T points
st_y = np.array([st_k6[k] for k in KAPPAS_STOCH])
ax.plot(xk, st_y, color=COL_ST, lw=0, marker="s", ms=6,
        label="Santiago S-T")

# Santiago S-N points
sn_y = np.array([sn_k6[k] for k in KAPPAS_STOCH])
ax.plot(xk, sn_y, color=COL_SN, lw=0, marker="^", ms=6,
        label="Santiago S-N")

# Reference line y=0
ax.axhline(0, color="black", lw=0.8, ls="--", alpha=0.5)

# kappa=inf: separate markers with gap notation
# Use a dedicated x-position outside the stochastic range with a break indicator
ax.annotate("",
            xy=(1000, fogo_y[-1]), xycoords="data",
            xytext=(1500, fogo_y[-1]), textcoords="data",
            arrowprops=dict(arrowstyle="-", lw=0, color="white"))

# Inf point at x=1800 (visually separated, not connected)
x_inf = 1800
ax.plot(x_inf, FOGO_INF,  color=COL_FOGO, marker="o", ms=5, ls="",
        clip_on=False)
ax.plot(x_inf, st_inf,    color=COL_ST,   marker="s", ms=6, ls="",
        clip_on=False)
ax.plot(x_inf, sn_inf,    color=COL_SN,   marker="^", ms=6, ls="",
        clip_on=False)

# Vertical line separating stochastic from inf
ax.axvline(1300, color="gray", lw=0.6, ls=":", alpha=0.7)
ax.text(1560, ax.get_ylim()[0] + 1, r"$\kappa\!=\!\infty$",
        ha="center", va="bottom", fontsize=8, color="gray")

# x-axis: log scale for stochastic, custom tick for inf
ax.set_xscale("log")
ax.set_xticks([25, 50, 100, 200, 400, 1000])
ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
ax.set_xlabel(r"$\kappa$ (penalty weight)")
ax.set_ylabel("SAW\u2212TOPSIS contrast (pp)")

ax.legend(loc="upper right", frameon=False, handlelength=1.5)

plt.tight_layout()

# ── Save ───────────────────────────────────────────────────────────────────────
OUT_DIR.mkdir(parents=True, exist_ok=True)
out_pdf = OUT_DIR / "fig_kappa_santiago.pdf"
out_png = OUT_DIR / "fig_kappa_santiago.png"
fig.savefig(out_pdf, bbox_inches="tight")
fig.savefig(out_png, dpi=300, bbox_inches="tight")
print(f"  Saved: {out_pdf}")
print(f"  Saved: {out_png}")

# Print data summary for verification
print("\n  Data check (K6 by kappa):")
print(f"  {'k':>6}  {'Fogo':>7}  {'S-T':>7}  {'S-N':>7}")
for k in KAPPAS_STOCH:
    print(f"  {k:>6}  {FOGO_K6[k]:>7.1f}  {st_k6[k]:>7.1f}  {sn_k6[k]:>7.1f}")
print(f"  {'inf':>6}  {FOGO_INF:>7.1f}  {st_inf:>7.1f}  {sn_inf:>7.1f}")
