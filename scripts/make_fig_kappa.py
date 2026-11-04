# -*- coding: utf-8 -*-
"""make_fig_kappa.py — K6 (SAW-TOPSIS aggregation contrast) vs kappa.

Three datasets:
  - Fogo: authoritative E7 run, CI bands (from macros_e7.tex / macros.tex)
  - Santiago S-T: K6_per_kappa from santiago_predictions_v2.json (points, no CI)
  - Santiago S-N: K6_per_kappa from santiago_predictions_v2.json (points, no CI)

Style: fig_utils.py (Elsevier CAS-DC, Wong palette, legend below, COL2=7.48in).
JSON SHA-verified before reading.
kappa=inf separate markers, not connected to main curve.

Usage:
    uv run python scripts/make_fig_kappa.py

Output:
    figures/fig_kappa_santiago.pdf
    figures/fig_kappa_santiago.png  (300 DPI)
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from fig_utils import set_rcparams, savefig, COL2, WONG, legend_below

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

JSON_PATH  = ROOT / "results" / "santiago" / "santiago_predictions_v2.json"
K6CI_PATH  = ROOT / "results" / "santiago" / "santiago_k6_ci.json"
SHA_JSON   = "1fbc412b8ace6bdbd07d74f890f1460a2acdc268ce45ed59fc2a7900e520cf80"
SHA_K6CI   = "88fc473c994794aa83e6a7a45304a3ee65071af9dd9e81799aeb169e5a56395d"

# ── SHA-verify ─────────────────────────────────────────────────────────────────
got = hashlib.sha256(JSON_PATH.read_bytes()).hexdigest()
if got != SHA_JSON:
    raise RuntimeError(f"JSON SHA mismatch: got {got}")
print(f"  SHA OK: santiago_predictions_v2.json ({SHA_JSON[:16]})")

got_ci = hashlib.sha256(K6CI_PATH.read_bytes()).hexdigest()
if got_ci != SHA_K6CI:
    raise RuntimeError(f"K6 CI SHA mismatch: got {got_ci}")
print(f"  SHA OK: santiago_k6_ci.json ({SHA_K6CI[:16]})")

data   = json.loads(JSON_PATH.read_text(encoding="utf-8"))
k6_ci  = json.loads(K6CI_PATH.read_text(encoding="utf-8"))["results"]

def get_pred(branch, name):
    for p in data[branch]["predictions"]:
        if p["prediction"] == name:
            return p
    raise KeyError(name)

# ── Data ───────────────────────────────────────────────────────────────────────
KAPPAS = [25, 50, 100, 200, 400, 1000]

# Fogo K6 (SAW-TOPSIS Agg_pooled3) — authoritative E7 run
# Sources: macros_e7.tex (k=25,100,400,1000) + macros.tex (k=50: AggContrastKfifty, k=200: AggContrast)
FOGO_K6 = {25: +21.1, 50: +20.4, 100: +9.3, 200: -0.4, 400: -5.7, 1000: -9.0}
FOGO_LO = {25:  18.5, 50:  17.7, 100:  7.1, 200: -2.2, 400: -7.3, 1000: -10.5}
FOGO_HI = {25:  23.9, 50:  23.2, 100: 11.6, 200:  1.3, 400: -4.1, 1000:  -7.5}
FOGO_INF = 0.0   # macros_kappa_inf.tex

# Santiago K6 from JSON
st_s4 = get_pred("S-T", "S4")
sn_s4 = get_pred("S-N", "S4")
st_k6 = {int(k): v for k, v in st_s4["K6_per_kappa"].items()}
sn_k6 = {int(k): v for k, v in sn_s4["K6_per_kappa"].items()}
st_inf = st_s4["K6_inf"]   # 0.0
sn_inf = sn_s4["K6_inf"]   # -33.33

# Descriptive CIs from santiago_k6_ci.json (same method as Fogo E7)
def get_ci(branch_key, k):
    d = k6_ci[branch_key].get(str(k), {})
    return d.get("lo", None), d.get("hi", None)

ST_LO = np.array([get_ci("ST", k)[0] for k in KAPPAS])
ST_HI = np.array([get_ci("ST", k)[1] for k in KAPPAS])
SN_LO = np.array([get_ci("SN", k)[0] for k in KAPPAS])
SN_HI = np.array([get_ci("SN", k)[1] for k in KAPPAS])

# ── Style ──────────────────────────────────────────────────────────────────────
set_rcparams()

C_FOGO = WONG["blue"]    # #0072B2
C_ST   = WONG["vermil"]  # #D55E00
C_SN   = WONG["green"]   # #009E73
ALPHA_BAND = 0.15

xk = np.array(KAPPAS)
x_inf = 1500   # visual position for kappa=inf (right of separator)

# ── Figure ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(COL2, 3.6))

# Fogo: line + CI band
fg_y  = np.array([FOGO_K6[k] for k in KAPPAS])
fg_lo = np.array([FOGO_LO[k] for k in KAPPAS])
fg_hi = np.array([FOGO_HI[k] for k in KAPPAS])
ax.fill_between(xk, fg_lo, fg_hi, color=C_FOGO, alpha=ALPHA_BAND)
ax.plot(xk, fg_y, color=C_FOGO, lw=2.0, marker="o", ms=6,
        label="Fogo (E7, 95% CI)")

# Santiago S-T: line + descriptive CI band
st_y = np.array([st_k6[k] for k in KAPPAS])
ax.fill_between(xk, ST_LO, ST_HI, color=C_ST, alpha=ALPHA_BAND)
ax.plot(xk, st_y, color=C_ST, lw=1.4, marker="s", ms=6,
        label="Santiago S-T (descriptive CI)")

# Santiago S-N: line + descriptive CI band
sn_y = np.array([sn_k6[k] for k in KAPPAS])
ax.fill_between(xk, SN_LO, SN_HI, color=C_SN, alpha=ALPHA_BAND)
ax.plot(xk, sn_y, color=C_SN, lw=1.4, marker="^", ms=6,
        label="Santiago S-N (descriptive CI)")

# y=0 reference
ax.axhline(0, color="black", lw=0.8, ls="--", alpha=0.4, zorder=0)

# ── kappa=inf separate markers ─────────────────────────────────────────────────
ax.axvline(1250, color=WONG["gray"], lw=0.7, ls=":", alpha=0.7)
ax.plot(x_inf, FOGO_INF, color=C_FOGO, marker="o", ms=6, ls="", clip_on=False)
ax.plot(x_inf, st_inf,   color=C_ST,   marker="s", ms=7, ls="", clip_on=False)
ax.plot(x_inf, sn_inf,   color=C_SN,   marker="^", ms=7, ls="", clip_on=False)

# inf label
ylo = ax.get_ylim()[0]
ax.text(x_inf, ylo - 2, u"\u03ba\u202f=\u202f\u221e",
        ha="center", va="top", fontsize=10, color=WONG["gray"])

# ── Axes ───────────────────────────────────────────────────────────────────────
ax.set_xscale("log")
ax.set_xticks(KAPPAS)
ax.get_xaxis().set_major_formatter(mticker.ScalarFormatter())
ax.set_xlabel(r"$\kappa$ (penalty weight)")
ax.set_ylabel("SAW\u2212TOPSIS contrast (pp)")
ax.set_xlim(20, 1700)
ax.set_ylim(min(sn_y.min(), sn_inf) - 8, max(fg_hi.max(), st_y.max()) + 5)

# ── Legend below ──────────────────────────────────────────────────────────────
legend_below(ax, ncol=3, y_offset=-0.14)

# ── Save ──────────────────────────────────────────────────────────────────────
plt.tight_layout()
savefig(fig, "fig_kappa_santiago")

# Data summary
print("\n  Data check:")
print(f"  {'k':>6}  {'Fogo':>7} [{' lo':>5},{' hi':>5}]  {'S-T':>7}  {'S-N':>7}")
for k in KAPPAS:
    print(f"  {k:>6}  {FOGO_K6[k]:>+7.1f} [{FOGO_LO[k]:>+5.1f},{FOGO_HI[k]:>+5.1f}]"
          f"  {st_k6[k]:>+7.1f}  {sn_k6[k]:>+7.1f}")
print(f"  {'inf':>6}  {FOGO_INF:>+7.1f} [   --,   --]  {st_inf:>+7.1f}  {sn_inf:>+7.1f}")
