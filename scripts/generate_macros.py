"""
generate_macros.py
==================
Reads result CSVs and hardcoded canonical-run values, computes all derived
quantities, and writes macros.tex with \newcommand for every number that
appears in the manuscript body.

Run:  uv run python scripts/generate_macros.py
Output: macros.tex  (in repo root, \input{macros.tex} in main.tex)
"""
import sys, os, subprocess
from pathlib import Path
from scipy import stats
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent

# ─── helpers ─────────────────────────────────────────────────────────────────

def mac(name, value, fmt=None):
    """Return a LaTeX \newcommand line."""
    if fmt is None:
        if isinstance(value, float):
            fmt = f"{value:.4f}"
        else:
            fmt = str(value)
    # LaTeX command names: letters only
    return f"\\newcommand{{\\{name}}}{{{fmt}}}\n"

def pct(x, decimals=1):
    """Format as percentage string without % sign."""
    return f"{x:.{decimals}f}"

def git_hash():
    try:
        h = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT, stderr=subprocess.DEVNULL
        ).decode().strip()
        return h
    except Exception:
        return "unknown"

# ─── canonical run values (hardcoded; single authoritative source) ──────────
# These come from the original mc_aprime_full.py run (commit 8fcc93e and earlier).
# tab:factorial and tab:tvorder must both derive from this run.

# SAW rows (greedy and optimal separately)
Q2g_mm   = 64.6   # SAW min-max greedy
Q2o_mm   = 100.0  # SAW min-max optimal  (Prop.1 guarantees 100%)
Q2g_vec  = 54.2   # SAW vector greedy
Q2o_vec  = 56.8   # SAW vector optimal
Q2g_rnk = 66.0   # SAW ranks greedy    (WP3 supplementary; canonical unknown)
Q2o_rnk = 87.0   # SAW ranks optimal   → Q2m_rnk = 76.5 (tab:tvorder canonical)
# Note: canonical ranks greedy+optimal are not in wp4_cells_20.csv (SAW only).
# We back-solve from tab:tvorder Q2_mean=76.5: greedy+optimal = 153.0.
# WP3 gives greedy=66.0, optimal=88.2 → mean=77.1 ≠ 76.5.
# Use tab:tvorder Q2_mean=76.5 as the authoritative value for tab:tvorder.
# The individual greedy/optimal for ranks in the canonical run are not stored;
# only Q2_mean=76.5 is published.
Q2m_rnk_canonical = 76.5  # tab:tvorder canonical value

# TOPSIS rows — source: tab:factorial in main.tex, Round 11 (κ=200, space A', N=500)
# Verified against diag_r14.py which checks: mm greedy=72.4, mm optimal=96.6
# The values 83.4/53.5 that appeared in generate_macros.py were from a different
# run (different κ or space) and are NOT the values in tab:factorial. Removed.
# tab:factorial authoritative values (read from main.tex, NOT from a missing CSV):
Q2g_topsis_mm_factorial  = 72.4   # tab:factorial: TOPSIS min-max greedy
Q2g_topsis_vec_factorial = 50.6   # tab:factorial: TOPSIS vector greedy
Q2o_topsis_mm_factorial  = 96.6   # tab:factorial: TOPSIS min-max optimal
Q2o_topsis_vec_factorial = 52.4   # tab:factorial: TOPSIS vector optimal

# tab:tvorder Q2_mean (average of greedy and optimal)
Q2m_mm  = (Q2g_mm  + Q2o_mm)  / 2   # = 82.3
Q2m_vec = (Q2g_vec + Q2o_vec) / 2   # = 55.5
Q2m_rnk = Q2m_rnk_canonical          # = 76.5 (tab:tvorder canonical)

TV_mm  = 0.000
TV_rnk = 0.091
TV_vec = 0.315   # analytic (Table 1 rounded Aj); WP3 numerical = 0.311

# normalisation main effect (tab:effects): mean over SAW+TOPSIS, both assemblies
# = (Q2[SAW,mm,all] + Q2[TOPSIS,mm,all]) / 2  −  (Q2[SAW,vec,all] + Q2[TOPSIS,vec,all]) / 2
# From §8.3: 29.9 pp; 29.8 pp for +0.1 rounding in some contexts
NormMainEffect = 29.9

# SAW greedy contrast (estimand of synthetic grid, §7.7)
SAWgreadyContrast = Q2g_mm - Q2g_vec  # = 10.4 pp

# Greedy-only contrast: mean of SAW and TOPSIS greedy contrasts
# Excludes the tautological optimal cells fixed at 100% by Proposition 1
# Source: tab:factorial in main.tex (72.4/50.6 from Round 11, κ=200)
NormGreedyContrast = ((Q2g_mm - Q2g_vec) + (Q2g_topsis_mm_factorial - Q2g_topsis_vec_factorial)) / 2

# ─── §7.2: three-level regression on canonical Q2_mean ──────────────────────
TV3 = np.array([TV_mm, TV_rnk, TV_vec])
Q3  = np.array([Q2m_mm, Q2m_rnk, Q2m_vec])   # Q2m_rnk = 76.5 (canonical)
s3, b3, r3, p3, se3 = stats.linregress(TV3, Q3)

# leverage and Sxx contribution for vector (3-level)
X3 = np.column_stack([np.ones(3), TV3])
H3 = X3 @ np.linalg.inv(X3.T @ X3) @ X3.T
h3 = np.diag(H3)
Sxx3 = np.sum((TV3 - TV3.mean())**2)
hii_vec_3level = h3[2]
sxx_pct_vec_3level = (TV3[2] - TV3.mean())**2 / Sxx3 * 100

# ─── WP3 supplementary run ──────────────────────────────────────────────────
wp3 = pd.read_csv(ROOT / "results" / "wp3_summary.csv")

# Five-level regression (TV < 0.35, i.e. exclude sum)
sel5 = wp3[wp3['norm'].isin(['min-max','max','Peldschus','ranks','vector'])].sort_values('TV')
x5 = sel5['TV'].values
y5 = sel5['Q2_mean'].values
s5, b5, r5, p5, se5 = stats.linregress(x5, y5)
df5 = len(x5) - 2  # = 3

# leverage for vector in 5-level
X5 = np.column_stack([np.ones(5), x5])
H5 = X5 @ np.linalg.inv(X5.T @ X5) @ X5.T
h5 = np.diag(H5)
Sxx5 = np.sum((x5 - x5.mean())**2)
hii_vec_5level = h5[4]
sxx_pct_vec_5level = (x5[4] - x5.mean())**2 / Sxx5 * 100

# Six-level (include sum)
sel6 = wp3[wp3['norm'].isin(['min-max','max','Peldschus','ranks','vector','sum'])].sort_values('TV')
x6 = sel6['TV'].values
y6 = sel6['Q2_mean'].values
s6, b6, r6, p6, se6 = stats.linregress(x6, y6)

# Peldschus paired test (from test_peldschus_paired.py results)
pel_t  = 3.343
pel_p  = 0.0009
pel_n  = 500
pel_rho = 0.42
pel_diff_greedy = 7.4   # pp
pel_diff_mean   = 3.7   # pp

# VIF quadratic (5-level, from verify_wp3_claims.py)
vif_quad = 23.5
p_quad   = 0.652

# WP3 numerical TV for vector
TV_vec_numerical = wp3[wp3['norm']=='vector']['TV'].values[0]  # 0.3113

# ─── WP4 synthetic grid ──────────────────────────────────────────────────────
wp4 = pd.read_csv(ROOT / "results" / "wp4_cells_20.csv")
# R2_adj for ||delta||_2 model (from §7.7 text)
R2adj_l2 = 0.488
R2adj_TV = 0.057

# ─── build macros ────────────────────────────────────────────────────────────
lines = [
    "% AUTO-GENERATED by scripts/generate_macros.py — DO NOT EDIT BY HAND\n",
    f"% git HEAD: {git_hash()}\n",
    "\n",
    "% ── Canonical run: tab:tvorder ──────────────────────────────────────────\n",
    mac("QtwommGreedy",   Q2g_mm,  pct(Q2g_mm)),
    mac("QtwommOptimal",  Q2o_mm,  pct(Q2o_mm)),
    mac("QtwovecGreedy",  Q2g_vec, pct(Q2g_vec)),
    mac("QtwovecOptimal", Q2o_vec, pct(Q2o_vec)),
    mac("QtwommMean",     Q2m_mm,  pct(Q2m_mm)),
    mac("QtwovecMean",    Q2m_vec, pct(Q2m_vec)),
    mac("QtwoRanksMean",  Q2m_rnk, pct(Q2m_rnk)),
    mac("TVvec",          TV_vec,  f"{TV_vec:.3f}"),
    mac("TVrnk",          TV_rnk,  f"{TV_rnk:.3f}"),
    mac("TVvecNumerical", TV_vec_numerical, f"{TV_vec_numerical:.3f}"),
    "\n",
    "% ── Canonical run: cost contrast ───────────────────────────────────────\n",
    mac("NormMainEffect",    NormMainEffect,    pct(NormMainEffect)),
    mac("SAWgreedyContrast", SAWgreadyContrast, pct(SAWgreadyContrast)),
    mac("NormGreedyContrast", NormGreedyContrast, pct(NormGreedyContrast)),
    mac("LossTabTVorder",    Q2m_mm - Q2m_vec,  pct(Q2m_mm - Q2m_vec)),
    # TV on admissible range (vector, 389 sites): 86.7 * 0.107 = 9.3 pp
    # 0.107 is hardcoded — source: separate WP3 run on admissible candidates only.
    # TODO: read from a CSV when that run is stored.
    mac("MechOnePredAdmiss", abs(s3) * 0.107,   f"{abs(s3) * 0.107:.1f}"),
    # tab:fourthcell values: N_cand/A' = 100%->20% loss of 80pp; N_via/A = 100%->95% loss of 5pp
    # Source: tab:fourthcell in main.tex (lines ~1973-1985)
    mac("FourthCellLossHi",  100.0 - 20.0,   f"{100.0-20.0:.0f}"),
    mac("FourthCellLossLo",  100.0 - 95.0,   f"{100.0-95.0:.0f}"),
    # Mechanism 1 share and mismatch ratios (§8.1)
    mac("MechOneShare",    abs(s3) * 0.107 / (100.0-20.0) * 100,  f"{round(abs(s3)*0.107/(100.0-20.0)*100):.0f}"),
    mac("MismatchRatioHi", (100.0-20.0) / (abs(s3) * 0.107),      f"{(100.0-20.0)/(abs(s3)*0.107):.1f}"),
    mac("MismatchRatioLo", (100.0-95.0) / (abs(s3) * 0.107),      f"{(100.0-95.0)/(abs(s3)*0.107):.2f}"),
    "\n",
    "% ── §7.2: three-level regression ────────────────────────────────────────\n",
    mac("slopeThree",   abs(s3),         f"{abs(s3):.1f}"),
    mac("RsqThree",     r3**2,           f"{r3**2:.3f}"),
    mac("hiiVecThree",  hii_vec_3level,  f"{hii_vec_3level:.3f}"),
    mac("SxxPctVecThree", sxx_pct_vec_3level, f"{int(round(sxx_pct_vec_3level))}"),
    "\n",
    "% ── §8.6: WP3 five-level regression ─────────────────────────────────────\n",
    mac("slopeFive",    abs(s5),         f"{abs(s5):.1f}"),
    mac("SEfive",       se5,             f"{se5:.1f}"),
    mac("dffive",       df5,             str(df5)),
    mac("RsqFive",      r5**2,           f"{r5**2:.3f}"),
    mac("hiiVecFive",   hii_vec_5level,  f"{hii_vec_5level:.3f}"),
    mac("SxxPctVecFive", sxx_pct_vec_5level, f"{int(round(sxx_pct_vec_5level))}"),
    mac("VIFquad",      vif_quad,        f"{vif_quad:.1f}"),
    mac("pQuad",        p_quad,          f"{p_quad:.2f}"),
    "\n",
    "% ── §8.6: R2 drop with sum ──────────────────────────────────────────────\n",
    mac("RsqDropFrom",  r5**2,  f"{r5**2:.3f}"),
    mac("RsqDropTo",    r6**2,  f"{r6**2:.3f}"),
    mac("slopeDropSum", abs(s6), f"{abs(s6):.1f}"),
    mac("pDropSum",     p6,     f"{p6:.2f}"),
    "\n",
    "% ── §7.2: Peldschus paired test ─────────────────────────────────────────\n",
    mac("PeldschusT",        pel_t,          f"{pel_t:.2f}"),
    mac("PeldschusP",        pel_p,          f"{pel_p:.4f}"),
    mac("PeldschusN",        pel_n,          str(pel_n)),
    mac("PeldschusRho",      pel_rho,        f"{pel_rho:.2f}"),
    mac("PeldschusDiffGreedy", pel_diff_greedy, f"{pel_diff_greedy:.1f}"),
    mac("PeldschusDiffMean",   pel_diff_mean,   f"{pel_diff_mean:.1f}"),
    "\n",
    "% ── §7.7: synthetic grid ────────────────────────────────────────────────\n",
    mac("RsqadjLtwo", R2adj_l2, f"{R2adj_l2:.3f}"),
    mac("RsqadjTV",   R2adj_TV, f"{R2adj_TV:.3f}"),
]

out = ROOT / "macros.tex"
out.write_text("".join(lines), encoding="utf-8")
print(f"Written {out} ({len(lines)} lines)")

# ─── sanity print ─────────────────────────────────────────────────────────────
print(f"\nKey values:")
print(f"  tab:tvorder  mm={Q2m_mm:.1f}  rnk={Q2m_rnk:.1f}  vec={Q2m_vec:.1f}")
print(f"  §7.2 slope=-{abs(s3):.1f}  R2={r3**2:.3f}  h_ii={hii_vec_3level:.3f}  Sxx={sxx_pct_vec_3level:.0f}%")
print(f"  §8.6 five-level slope=-{abs(s5):.1f}  SE={se5:.1f}  df={df5}  R2={r5**2:.3f}")
print(f"  §8.6 R2 drop {r5**2:.3f} -> {r6**2:.3f}  p={p6:.2f}")
print(f"  §7.7 SAW greedy contrast={SAWgreadyContrast:.1f} pp")
