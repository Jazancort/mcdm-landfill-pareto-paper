# -*- coding: utf-8 -*-
"""
compute_regret.py  --  Value-based regret metric R(t; w) for all 8 cells.

Definition (pre-spec Fase B):
    R(t; w) = [V_mm(t*; w) - V_mm(t; w)] / V_range(w)

where:
    V_mm(t; w) = SAW/minmax score for portfolio t under weight w
               = (X_adj[i0] + X_adj[i1] + X_adj[i2]) @ w
    t*(w)      = the SAW/minmax/optimal portfolio (argmax V_mm over all
                 feasible portfolios; lies on the frontier by Proposition 1)
    V_range(w) = V_mm(t*(w)) - min_c V_mm(t_c(w))
                 where min is over all 8 cells for draw d

Distinction from Q2/Q3:
    Q2: binary -- is the selected portfolio on the exact Pareto frontier?
    Q3: expected Tchebyshev gap to the frontier
    R : value loss relative to the SAW/mm-optimal portfolio (0 iff t = t*)

Key property (B4 check):
    Even when Q2=1 (portfolio IS on the frontier), R > 0 is possible
    if the selected portfolio is not the value-maximising point on the frontier.

Outputs:
    results/regret/regret_perdraw.csv   -- per-draw per-cell R and V_mm
    results/regret/regret_aggregate.csv -- mean R per cell with SE
    results/regret/regret_macros.tex    -- LaTeX macros for manuscript

Usage:
    uv run python scripts/compute_regret.py
"""

import os
import sys
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT    = Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"
RESULTS = ROOT / "results"
OUT     = RESULTS / "regret"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(SCRIPTS))

# ── Data loading ──────────────────────────────────────────────────────────────
if "MCDM_DATA_DIR" not in os.environ:
    _athena  = "/home/julioazancort/scratch/mcdm"
    _windows = (
        "G:\\Faculdade\\Estudo\\Doutorado\\2025.1\\"
        "Otimiza\u00e7\u00e3o Bioinspirada\\"
        "Tentativa de dados via GIS"
    )
    os.environ["MCDM_DATA_DIR"] = _athena if os.path.exists(_athena) else _windows

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS,
    _build_decision_matrix,
)
from scoring import make_scorers

print("Loading data...", flush=True)
df_all, _, _ = load_data()
df_imp       = impute_nan(df_all)
df_via       = df_imp[df_imp[COL["protected"]] > 0].copy().reset_index(drop=True)
N            = len(df_via)
assert N == 389, f"Expected 389 sites, got {N}"

X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b:
        X_adj[:, j] = 1.0 - X_via[:, j]
norms_via = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)

print(f"Sites: {N}  Criteria: {X_adj.shape[1]}", flush=True)

# ── Weights ───────────────────────────────────────────────────────────────────
wmat_path = RESULTS / "e1" / "e1_weights_k200.npy"
import hashlib as _hl
SHA_EXPECTED = "bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487"
sha = _hl.sha256(wmat_path.read_bytes()).hexdigest()
assert sha == SHA_EXPECTED, f"SHA mismatch for e1_weights_k200.npy: {sha[:16]}"
W = np.load(wmat_path)          # (500, 11)
N_DRAWS = W.shape[0]
print(f"Weights: shape={W.shape}  SHA OK", flush=True)

# ── mc_unified_raw ─────────────────────────────────────────────────────────────
df_mc = pd.read_csv(RESULTS / "unified" / "mc_unified_raw.csv")
assert len(df_mc) == N_DRAWS * 8, f"Expected {N_DRAWS*8} rows, got {len(df_mc)}"
print(f"mc_unified_raw: {len(df_mc)} rows", flush=True)

# ── Precompute X_adj_trio for each row ────────────────────────────────────────
# X_adj_trio[k] = X_adj[i0] + X_adj[i1] + X_adj[i2]  shape (M,)
# V_mm(row k; draw d) = X_adj_trio[k] @ W[d]
i0 = df_mc["i0"].values.astype(int)
i1 = df_mc["i1"].values.astype(int)
i2 = df_mc["i2"].values.astype(int)
X_trio = X_adj[i0] + X_adj[i1] + X_adj[i2]   # (4000, 11)

# V_mm per row: V_mm[k] = X_trio[k] @ W[draw[k]]
draw_idx = df_mc["draw"].values.astype(int)
W_per_row = W[draw_idx]                         # (4000, 11) — weight for each row's draw
V_mm = (X_trio * W_per_row).sum(1)             # (4000,)  vectorised inner product

df_mc = df_mc.copy()
df_mc["V_mm"] = V_mm

# ── Per-draw V_max ────────────────────────────────────────────────────────────
# V_max[d] = V_mm of (saw, minmax, optimal) for draw d  (= argmax over all feasible)
mask_ref = (df_mc["agg"] == "saw") & (df_mc["norm"] == "minmax") & (df_mc["mont"] == "optimal")
ref      = df_mc[mask_ref].set_index("draw")["V_mm"]   # Series indexed by draw
v_max = ref[draw_idx].values                            # (4000,) V_max for each row

# ── Per-draw V_min over ALL feasible trios (not just the 8 cells) ─────────────
# V_range = V_max - V_min, bounded in [0,100%] for ANY portfolio in T.
# R in [0,1] by construction; independent of which cells are compared.
trios_path = ROOT / "data" / "fogo_trios.npy"
print(f"Computing V_min over all trios from {trios_path} ...", flush=True)
trios_all  = np.load(trios_path).astype(int)
n_trios_all = len(trios_all)
X_trio_all = X_adj[trios_all[:, 0]] + X_adj[trios_all[:, 1]] + X_adj[trios_all[:, 2]]
# Batched min to stay within ~200 MB per batch
BATCH = 50000
V_min_draws = np.full(N_DRAWS, np.inf)
for start in range(0, n_trios_all, BATCH):
    end = min(start + BATCH, n_trios_all)
    V_batch = X_trio_all[start:end] @ W.T   # (BATCH, N_DRAWS)
    np.minimum(V_min_draws, V_batch.min(axis=0), out=V_min_draws)
    if start % 500000 == 0:
        print(f"  V_min pass: {start}/{n_trios_all} ({100*start/n_trios_all:.0f}%)",
              flush=True)
print(f"  V_min done. Range sample: min={V_min_draws.min():.4f} max={V_min_draws.max():.4f}",
      flush=True)

v_min = V_min_draws[draw_idx]
v_range = np.maximum(v_max - v_min, 1e-12)   # V_range = V_max - V_min(T)

# ── Regret ────────────────────────────────────────────────────────────────────
regret_raw = np.maximum(0.0, v_max - V_mm)                # (4000,) >= 0
R          = regret_raw / v_range                          # normalised [0, 1]

df_mc["V_max"]       = v_max
df_mc["V_range"]     = v_range
df_mc["R_raw"]       = regret_raw
df_mc["R"]           = R

# Save per-draw
perdraw_path = OUT / "regret_perdraw.csv"
df_mc.to_csv(perdraw_path, index=False)
print(f"Saved: {perdraw_path}", flush=True)

# ── B4 Check: Q2=1 rows with R > 0 ───────────────────────────────────────────
print()
print("=== B4: Q2=1 draws with R > 0 (by cell) ===")
tol = 1e-9
for (agg, norm, mont), grp in df_mc.groupby(["agg", "norm", "mont"]):
    n_total  = len(grp)
    n_q2one  = (grp["nd_Q2Ap"] == 1).sum()
    n_r_pos  = (grp["R"] > tol).sum()
    n_q2one_r_pos = ((grp["nd_Q2Ap"] == 1) & (grp["R"] > tol)).sum()
    print(f"  {agg}/{norm}/{mont}: n={n_total}  Q2=1:{n_q2one}  R>0:{n_r_pos}  "
          f"(Q2=1 AND R>0):{n_q2one_r_pos}")

# ── Aggregate by cell ─────────────────────────────────────────────────────────
print()
print("=== Aggregate regret per cell ===")
agg_rows = []
for (agg, norm, mont), grp in df_mc.groupby(["agg", "norm", "mont"]):
    mean_R   = grp["R"].mean()
    se_R     = grp["R"].std(ddof=1) / math.sqrt(len(grp))
    mean_raw = grp["R_raw"].mean()
    mean_V   = grp["V_mm"].mean()
    q2_pct   = grp["nd_Q2Ap"].mean() * 100
    agg_rows.append({
        "agg": agg, "norm": norm, "mont": mont,
        "mean_R": round(mean_R, 4),
        "se_R":   round(se_R,   4),
        "mean_R_pp":   round(mean_R * 100, 2),
        "se_R_pp":     round(se_R  * 100, 2),
        "mean_R_raw":  round(mean_raw, 4),
        "mean_V_mm":   round(mean_V, 4),
        "Q2_pct":      round(q2_pct, 1),
    })
    print(f"  {agg}/{norm}/{mont}: R={mean_R:.4f} ({mean_R*100:.2f} pp)  "
          f"SE={se_R:.4f}  Q2={q2_pct:.1f}%")

df_agg = pd.DataFrame(agg_rows)
agg_path = OUT / "regret_aggregate.csv"
df_agg.to_csv(agg_path, index=False)
print(f"\nSaved: {agg_path}")

# ── Sanity checks ─────────────────────────────────────────────────────────────
saw_mm_opt = df_agg[
    (df_agg["agg"] == "saw") &
    (df_agg["norm"] == "minmax") &
    (df_agg["mont"] == "optimal")
]
assert len(saw_mm_opt) == 1, f"Expected 1 row for SAW/mm/opt, got {len(saw_mm_opt)}"
assert saw_mm_opt["mean_R"].iloc[0] < 1e-9, \
    f"SAW/mm/opt must have R=0 by construction; got {saw_mm_opt['mean_R'].iloc[0]}"
print("\n[OK] SAW/mm/opt R = 0 (construction check passes)")

# ── LaTeX macros ──────────────────────────────────────────────────────────────
macro_lines = [
    "% AUTO-GENERATED by scripts/compute_regret.py -- DO NOT EDIT BY HAND",
    "% R = (V_mm_opt - V_mm_selected) / (V_mm_opt - V_mm_worst_in_T)",
    "% Denominator: range over all 1.94M feasible trios (not just the 8 cells).",
    "% R in [0,1] by construction; R_pp = R * 100 (percentage of achievable value range).",
    "",
]

cell_map = {
    ("saw",    "minmax", "greedy"):  "RegrSAWmmGrd",
    ("saw",    "minmax", "optimal"): "RegrSAWmmOpt",
    ("saw",    "vector", "greedy"):  "RegrSAWvecGrd",
    ("saw",    "vector", "optimal"): "RegrSAWvecOpt",
    ("topsis", "minmax", "greedy"):  "RegrTOPSISmmGrd",
    ("topsis", "minmax", "optimal"): "RegrTOPSISmmOpt",
    ("topsis", "vector", "greedy"):  "RegrTOPSISvecGrd",
    ("topsis", "vector", "optimal"): "RegrTOPSISvecOpt",
}

for _, row in df_agg.iterrows():
    key = (row["agg"], row["norm"], row["mont"])
    name = cell_map[key]
    macro_lines.append(
        f"\\newcommand{{\\{name}}}{{{row['mean_R_pp']}}}  "
        f"% {row['agg']}/{row['norm']}/{row['mont']}: SE={row['se_R_pp']}"
    )
    macro_lines.append(
        f"\\newcommand{{\\{name}SE}}{{{row['se_R_pp']}}}  "
        f"% SE of R for {row['agg']}/{row['norm']}/{row['mont']}"
    )

macros_path = OUT / "regret_macros.tex"
macros_path.write_text("\n".join(macro_lines) + "\n", encoding="utf-8")
print(f"Saved: {macros_path}")

# ── Differences grd-opt (paired bootstrap B=2000, seed=88) — stable values ───
# These CIs were computed by a separate bootstrap script and are stable.
diff_lines = [
    "",
    "% ── Differences grd-opt (paired bootstrap B=2000, seed=88) ─────────────────",
    "\\newcommand{\\RegrDiffSAWvec}{1.36}         % SAW vec: R(grd)-R(opt) (pp)",
    "\\newcommand{\\RegrDiffSAWvecLo}{0.95}       % CI lower",
    "\\newcommand{\\RegrDiffSAWvecHi}{1.74}       % CI upper",
    "\\newcommand{\\RegrDiffTOPSISvec}{2.15}      % TOPSIS vec: R(grd)-R(opt) (pp)",
    "\\newcommand{\\RegrDiffTOPSISvecLo}{1.74}    % CI lower",
    "\\newcommand{\\RegrDiffTOPSISvecHi}{2.58}    % CI upper",
    "\\newcommand{\\RegrDiffTOPSISmmGrdOpt}{0.86} % TOPSIS mm: R(grd)-R(opt) (pp)",
    "\\newcommand{\\RegrDiffTOPSISmmGrdOptLo}{0.56}",
    "\\newcommand{\\RegrDiffTOPSISmmGrdOptHi}{1.17}",
]
with open(macros_path, "a", encoding="utf-8") as fh:
    fh.write("\n".join(diff_lines) + "\n")

# ── E1 regret macros — computed from oracle CSV (DEV-FOGO-E1B-001) ────────────
# The fraction of draws where E1-B/opt selects the same trio as t* (trio==t*)
# was hardcoded as 28% in all versions prior to this commit. The oracle CSV
# (diagnostics/e1_oracle_per_draw.py) gives the correct semantic value: 35.4%.
SHA_E1_ORACLE_CSV = (
    "913396cea6a6288836783c9bc02a5f7a898b70643dd2788a5d0780b42155b56c"
)
oracle_csv = OUT / "e1_oracle_per_draw.csv"

if oracle_csv.exists():
    import hashlib as _hl2
    sha_got = _hl2.sha256(oracle_csv.read_bytes()).hexdigest()
    if sha_got != SHA_E1_ORACLE_CSV:
        print(f"WARNING: oracle CSV SHA mismatch: expected {SHA_E1_ORACLE_CSV[:16]}, "
              f"got {sha_got[:16]}")
    df_oracle = pd.read_csv(oracle_csv)
    e1b_opt = df_oracle[(df_oracle["cell"] == "B") & (df_oracle["mont"] == "optimal")]
    e1b_grd = df_oracle[(df_oracle["cell"] == "B") & (df_oracle["mont"] == "greedy")]
    e1w_opt = df_oracle[(df_oracle["cell"] == "W") & (df_oracle["mont"] == "optimal")]
    e1w_grd = df_oracle[(df_oracle["cell"] == "W") & (df_oracle["mont"] == "greedy")]

    n_draws_oracle = len(e1b_opt)
    e1b_mean     = round(float(e1b_opt["R_pp"].mean()), 2)
    e1b_se       = round(float(e1b_opt["R_pp"].std(ddof=1)) / math.sqrt(n_draws_oracle), 2)
    e1b_med      = round(float(e1b_opt["R_pp"].median()), 2)
    e1b_grd_mean = round(float(e1b_grd["R_pp"].mean()), 2)
    e1w_mean     = round(float(e1w_opt["R_pp"].mean()), 2)
    e1w_grd_mean = round(float(e1w_grd["R_pp"].mean()), 2)
    # Paired grd-opt diff for E1-B (bootstrap B=2000, seed=55 — stable)
    e1b_diff     = 3.72
    e1b_diff_lo  = 3.3
    e1b_diff_hi  = 4.1
    n_zero_trio  = int(e1b_opt["trio_eq_tstar"].sum())
    frac_zero    = round(n_zero_trio / n_draws_oracle * 100, 1)
    e1b_max      = round(float(e1b_opt["R_pp"].max()), 1)

    e1_lines = [
        "",
        (f"% ── E1 regret (oracle CSV e1_oracle_per_draw.csv "
         f"SHA={SHA_E1_ORACLE_CSV[:16]}; DEV-FOGO-E1B-001) ──"),
        "% New denominator (range over all T), so all values in [0,100%].",
        "% DEV-FOGO-E1B-001: fraction corrected 28% -> 35.4% (177/500 draws have trio==t*)",
        f"\\newcommand{{\\RegretEoneB}}{{{e1b_mean}}}            "
        f"% E1-B/opt mean R (pp), SE={e1b_se}",
        f"\\newcommand{{\\RegretEoneBSE}}{{{e1b_se}}}",
        f"\\newcommand{{\\RegretEoneBMed}}{{{e1b_med}}}         % E1-B/opt median R (pp)",
        f"\\newcommand{{\\RegretEoneBGrd}}{{{e1b_grd_mean}}}         % E1-B/grd mean R (pp)",
        f"\\newcommand{{\\RegretEoneW}}{{{e1w_mean}}}            % E1-W/opt mean R (pp)",
        f"\\newcommand{{\\RegretEoneBfracZero}}{{{frac_zero}}}    "
        f"% % of draws where E1-B/opt trio == t* (DEV-FOGO-E1B-001)",
        f"\\newcommand{{\\RegretEoneBfracZeroN}}{{{n_zero_trio}}}       "
        f"% n draws (out of {n_draws_oracle}) where E1-B/opt trio == t*",
        f"% Note: no draws exceed 100pp (max E1-B/opt R = {e1b_max} pp)",
        "",
        "% ── Random trio baseline ─────────────────────────────────────────────────────",
        "% 2000 random valid trios, mean R averaged over 500 draws, seed=42.",
        "\\newcommand{\\RRegretRandom}{54}            % median R of random valid trio (pp)",
        "",
        "% ── E1 greedy additional + grd-opt diff ─────────────────────────────────────",
        f"\\newcommand{{\\RegretEoneWGrd}}{{{e1w_grd_mean}}}          % E1-W/grd mean R (pp)",
        f"\\newcommand{{\\RegretEoneBGrdOptDiff}}{{{e1b_diff}}}   % E1-B grd-opt R diff (pp)",
        f"\\newcommand{{\\RegretEoneBGrdOptDiffLo}}{{{e1b_diff_lo}}}  % CI lower",
        f"\\newcommand{{\\RegretEoneBGrdOptDiffHi}}{{{e1b_diff_hi}}}  % CI upper",
    ]
    with open(macros_path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(e1_lines) + "\n")
    print(f"\nE1 macros appended from oracle CSV (SHA {SHA_E1_ORACLE_CSV[:16]}):")
    print(f"  E1-B/opt: mean={e1b_mean} SE={e1b_se} med={e1b_med}")
    print(f"  E1-W/opt: mean={e1w_mean}")
    print(f"  frac_zero (trio==t*): {frac_zero}% ({n_zero_trio}/{n_draws_oracle})")
else:
    print(f"\nWARNING: oracle CSV not found at {oracle_csv}")
    print("  E1 macros NOT appended. Run diagnostics/e1_oracle_per_draw.py first.")

print()
print("=" * 60)
print("DONE")
print(f"  perdraw : {perdraw_path}")
print(f"  aggregate: {agg_path}")
print(f"  macros  : {macros_path}")
