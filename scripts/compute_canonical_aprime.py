# -*- coding: utf-8 -*-
"""compute_canonical_aprime.py
Computes Pareto membership in space A' (389 admissible sites) for the
7 canonical portfolios from tab:canonical (main.tex).

Outputs verified "N of 7 in A'" count for §7.1 text.
"""
import sys, os, numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
if "MCDM_DATA_DIR" not in os.environ:
    athena = "/home/julioazancort/scratch/mcdm"
    os.environ["MCDM_DATA_DIR"] = athena if os.path.exists(athena) else str(ROOT / "data")

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS,
    _build_decision_matrix, INV, COST, F1_CRIT, F2_CRIT, F3_CRIT,
)
from pareto_utils import build_pareto_utils

# ── Data ─────────────────────────────────────────────────────────────────────
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]] > 0].copy().reset_index(drop=True)
assert len(df_via) == 389, f"Expected 389 sites, got {len(df_via)}"

# Site IDs (original row indices in df_all or site numbers from manuscript?)
# The manuscript uses IDs from df_imp index or a site_id column
print("df_via columns:", df_via.columns.tolist())
print("df_via index range:", df_via.index.min(), df_via.index.max())
if "site_id" in df_via.columns:
    print("Site IDs sample:", df_via["site_id"].head(10).tolist())
    site_id_col = "site_id"
else:
    # Use the original index from df_all
    site_id_col = None
    print("No site_id column; using integer index")

# ── Canonical portfolios (site IDs from tab:canonical) ───────────────────────
# These are the 1-based or 0-based IDs as they appear in the manuscript
CANONICAL = {
    "SAW/mm/opt":    (184, 430, 460),   # in F(A)=yes
    "SAW/mm/grd":    (184, 279, 320),   # in F(A)=no
    "TOPSIS/vec/opt": (227, 233, 345),  # in F(A)=no
    "TOPSIS/vec/grd": (233, 320, 355),  # in F(A)=no
    "TOPSIS/mm/grd": (184, 227, 460),   # in F(A)=yes
    "VIKOR/grd":     (233, 279, 320),   # in F(A)=no
    "PROMETHEE/grd": (51, 233, 345),    # in F(A)=yes
}

# ── Objective values for all trios ───────────────────────────────────────────
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())

X_raw, benefit = _build_decision_matrix(df_via)
X_adj = X_raw.copy()
for j, b in enumerate(benefit):
    if not b:
        X_adj[:, j] = 1.0 - X_raw[:, j]

# Group objective indices
f1_idx = [col_names.index(c) for c in F1_CRIT]
f2_idx = [col_names.index(c) for c in F2_CRIT]
f3_idx = [col_names.index(c) for c in F3_CRIT]

def objective_values(trio_indices):
    """Compute (F1, F2, F3) for a triplet of site indices (0-based)."""
    F1 = sum(X_adj[i, j] * w_ahp[j] for i in trio_indices for j in f1_idx)
    F2 = sum(X_adj[i, j] * w_ahp[j] for i in trio_indices for j in f2_idx)
    F3 = sum(X_adj[i, j] * w_ahp[j] for i in trio_indices for j in f3_idx)
    return F1, F2, F3

# ── Load trios and build A' Pareto frontier ──────────────────────────────────
trios = np.load(ROOT / "data" / "fogo_trios.npy")
print(f"Trios: {len(trios)}, site index range: {trios.min()}–{trios.max()}")

# Compute F1, F2, F3 for all trios using vectorized ops
print("Computing objective values for all trios (this may take ~30s)...")
F = X_adj.T  # shape (11, 389)
w = w_ahp

# F1 = sum_{j in F1_CRIT} w_j * (x_s1_j + x_s2_j + x_s3_j)
def batch_objectives(trios, X_adj, w, f1_idx, f2_idx, f3_idx):
    # trios: (N, 3) int array; X_adj: (389, 11); w: (11,)
    # Sum over sites in each trio
    trio_X = X_adj[trios[:, 0]] + X_adj[trios[:, 1]] + X_adj[trios[:, 2]]  # (N, 11)
    F1 = (trio_X[:, f1_idx] * w[f1_idx]).sum(axis=1)
    F2 = (trio_X[:, f2_idx] * w[f2_idx]).sum(axis=1)
    F3 = (trio_X[:, f3_idx] * w[f3_idx]).sum(axis=1)
    return F1, F2, F3

F1_all, F2_all, F3_all = batch_objectives(trios, X_adj, w, f1_idx, f2_idx, f3_idx)
print(f"Objectives computed. F1 range: [{F1_all.min():.4f}, {F1_all.max():.4f}]")

# Pareto frontier: F1 minimised, F2 minimised, F3 maximised
# Convert to minimisation: use F3_neg = -F3
OBJ = np.stack([F1_all, F2_all, -F3_all], axis=1)  # (N, 3), all minimised

from pareto_utils import build_pareto_utils
_, on_frontier = build_pareto_utils(OBJ)
# on_frontier is a boolean array or index set — check signature
print("on_frontier type:", type(on_frontier))
if hasattr(on_frontier, '__len__'):
    print("on_frontier size:", len(on_frontier))

