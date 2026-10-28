"""
compute_q2_raw_vs_shift.py  --  Q2 lookup: shift vs raw normalisation
======================================================================
For each draw in raw_sensitivity_4cells.csv, checks whether the raw-norm
portfolio is on the min-max Pareto frontier (using the same weights and
frontier checker as E1). Reports Q2_shift and Q2_raw per cell.

Requires:
  results/e1/e1_weights_k200.npy       -- 500 x 11 weight draws (seed=42)
  results/raw_sensitivity_4cells.csv   -- per-draw portfolio indices
  mcdm_experiment.py                   -- data loading and objectives

Output:
  Printed table: cell, Q2_shift, Q2_raw, delta, bound
  results/raw_sensitivity_q2.json      -- machine-readable
"""

import sys, os, json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, haversine_km, MIN_DIST_KM,
)
from pareto_utils import build_pareto_utils

# ── Load data ─────────────────────────────────────────────────────────────
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL['protected']] > 0].copy()
N_sites = len(df_via)
col_names = list(AHP_WEIGHTS.keys())
w_ahp = np.array(list(AHP_WEIGHTS.values()))

D = haversine_km(df_via['latitude (degrees)'].values,
                 df_via['longitude (degrees)'].values)
valid = D >= MIN_DIST_KM
trios_list = [(i, j, k)
              for i in range(N_sites) for j in range(i+1, N_sites) if valid[i, j]
              for k in range(j+1, N_sites) if valid[i, k] and valid[j, k]]
trios = np.array(trios_list, dtype=np.int32)
T0, T1, T2 = trios[:, 0], trios[:, 1], trios[:, 2]
n_trios = len(trios)
print(f"Sites={N_sites}  trios={n_trios:,}", flush=True)

compute_objs_mm, is_dominated_mm, _ = build_pareto_utils(
    df_via, col_names, trios, eps=1e-9
)
print("Pareto utils ready", flush=True)

# ── Load weights (same draws as E1 and raw_sensitivity) ───────────────────
W_PATH = ROOT / "results" / "e1" / "e1_weights_k200.npy"
W_draws = np.load(str(W_PATH))  # shape (500, 11)
N_DRAWS = len(W_draws)
assert N_DRAWS == 500, f"Expected 500 draws, got {N_DRAWS}"
print(f"Loaded weights: {W_draws.shape}", flush=True)

# ── Load raw_sensitivity CSV ───────────────────────────────────────────────
RS_CSV = ROOT / "results" / "raw_sensitivity_4cells.csv"
rs_sha = hashlib.sha256(RS_CSV.read_bytes()).hexdigest()[:16]
df_rs = pd.read_csv(RS_CSV)
assert len(df_rs) == 500

# Cells: (label, shift_col, raw_col, same_col)
CELLS = [
    ("SAW/opt",    "SAW_optimal_shift_idx",  "SAW_optimal_raw_idx",  "SAW_optimal_same"),
    ("SAW/grd",    "SAW_greedy_shift_idx",   "SAW_greedy_raw_idx",   "SAW_greedy_same"),
    ("TOPSIS/opt", "TOPSIS_optimal_shift_idx","TOPSIS_optimal_raw_idx","TOPSIS_optimal_same"),
    ("TOPSIS/grd", "TOPSIS_greedy_shift_idx", "TOPSIS_greedy_raw_idx", "TOPSIS_greedy_same"),
]

# ── Per-draw frontier check ────────────────────────────────────────────────
# Pre-compute per-draw objectives (expensive but only 500 draws)
print("Computing per-draw mm objectives...", flush=True)
# For each draw, is_dominated_mm needs F1, F2, F3 arrays (length = n_trios)
# We will check portfolios only for draws where shift != raw to save time.
# For draws where shift == raw: Q2_raw[draw] = Q2_shift[draw]

results = {}
for cell_label, shift_col, raw_col, same_col in CELLS:
    shift_idxs = df_rs[shift_col].values
    raw_idxs   = df_rs[raw_col].values
    same_flags = df_rs[same_col].values.astype(bool)

    n_same = int(same_flags.sum())
    n_diff = N_DRAWS - n_same
    diff_draws = np.where(~same_flags)[0]

    print(f"\n  {cell_label}: {n_same}/{N_DRAWS} same, {n_diff} different draws",
          flush=True)

    # For each draw, compute Q2_shift and Q2_raw
    q2_shift_count = 0
    q2_raw_count   = 0

    for di in range(N_DRAWS):
        w = W_draws[di]
        f1, f2, f3 = compute_objs_mm(w)
        F1 = f1[T0] + f1[T1] + f1[T2]
        F2 = f2[T0] + f2[T1] + f2[T2]
        F3 = f3[T0] + f3[T1] + f3[T2]

        s_idx = int(shift_idxs[di])
        r_idx = int(raw_idxs[di])

        s_trio = trios[s_idx]
        if not is_dominated_mm(s_trio, F1, F2, F3):
            q2_shift_count += 1

        if same_flags[di]:
            # raw == shift: same frontier membership
            if not is_dominated_mm(s_trio, F1, F2, F3):
                q2_raw_count += 1
        else:
            r_trio = trios[r_idx]
            if not is_dominated_mm(r_trio, F1, F2, F3):
                q2_raw_count += 1

        if di % 100 == 0:
            print(f"    draw {di}/500", flush=True)

    q2_shift = q2_shift_count / N_DRAWS * 100
    q2_raw   = q2_raw_count   / N_DRAWS * 100
    delta    = q2_raw - q2_shift
    bound    = n_diff / N_DRAWS * 100  # max possible |delta|

    print(f"  Q2_shift={q2_shift:.1f}%  Q2_raw={q2_raw:.1f}%  "
          f"delta={delta:+.1f}pp  bound=±{bound:.1f}pp", flush=True)

    results[cell_label] = {
        "Q2_shift": round(q2_shift, 1),
        "Q2_raw":   round(q2_raw,   1),
        "delta":    round(delta,     1),
        "bound":    round(bound,     1),
        "n_same":   n_same,
        "n_diff":   n_diff,
    }

# ── Save and print summary ─────────────────────────────────────────────────
out_path = ROOT / "results" / "raw_sensitivity_q2.json"
out_data = {
    "source_sha256": rs_sha,
    "weights_path": str(W_PATH.relative_to(ROOT)),
    "n_draws": N_DRAWS,
    "cells": results,
}
with open(out_path, "w") as f:
    json.dump(out_data, f, indent=2)

print("\n=== Q2 shift vs raw ===")
print(f"{'Cell':<14} {'Q2_shift':>9} {'Q2_raw':>8} {'delta':>8} {'bound':>8}")
for cell, r in results.items():
    print(f"{cell:<14} {r['Q2_shift']:>8.1f}% {r['Q2_raw']:>7.1f}% "
          f"{r['delta']:>+7.1f}pp {r['bound']:>7.1f}pp")

print(f"\nSaved: {out_path}")
