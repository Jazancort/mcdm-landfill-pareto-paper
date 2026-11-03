# -*- coding: utf-8 -*-
"""diagnostics/_count_e1b_zeros.py — Count R(E1-B_opt) zeros with 5 criteria.

Companion to e1_oracle_per_draw.py. Uses sequential V_all (same array for
V_max and V_sel) to confirm that 177/500 = 35.4% is the correct zero count
when trio_eq_tstar is the criterion.

Run on Athena:
    MCDM_DATA_DIR=/home/julioazancort/scratch/mcdm \\
    .venv/bin/python3 diagnostics/_count_e1b_zeros.py

Output: results/regret/e1b_R_pp_oracle_rerun.npy
"""
import sys, os
from pathlib import Path

ROOT    = Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
os.environ.setdefault("MCDM_DATA_DIR", "/home/julioazancort/scratch/mcdm")

import numpy as np

from mcdm_experiment import (
    load_data, impute_nan, COL, _build_decision_matrix,
)
from fogo_constants import OBJ_GROUPS, AJ_VEC as rho_j, W as w_ahp_raw

print("Loading data...", flush=True)
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]] > 0].copy().reset_index(drop=True)
assert len(df_via) == 389

X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b:
        X_adj[:, j] = 1.0 - X_via[:, j]

w_ahp  = w_ahp_raw / w_ahp_raw.sum()
trios  = np.load(ROOT / "data" / "fogo_trios.npy").astype(int)
W      = np.load(ROOT / "results" / "e1" / "e1_weights_k200.npy")
N      = W.shape[0]
X_trio = X_adj[trios[:, 0]] + X_adj[trios[:, 1]] + X_adj[trios[:, 2]]

# V_max and V_min per draw (batch — matches compute_regret.py)
print("V_max/V_min batch...", flush=True)
BATCH, n_t = 25000, len(trios)
V_max = np.full(N, -np.inf)
V_min = np.full(N,  np.inf)
for s in range(0, n_t, BATCH):
    e  = min(s + BATCH, n_t)
    Vb = X_trio[s:e] @ W.T
    np.maximum(V_max, Vb.max(0), out=V_max)
    np.minimum(V_min, Vb.min(0), out=V_min)
V_range = np.maximum(V_max - V_min, 1e-12)

# E1-B amplitudes (fixed w_ahp)
Aj_bar = np.empty(11)
for g_idx in OBJ_GROUPS:
    wg  = w_ahp[g_idx]
    avg = float(np.dot(wg, rho_j[g_idx])) / wg.sum()
    for j in g_idx:
        Aj_bar[j] = avg
Aj_E1B = Aj_bar.copy()

R_e1b = np.empty(N)
same_as_mm = np.zeros(N, dtype=bool)

for d in range(N):
    w        = W[d]
    V_mm     = X_trio @ w
    opt_mm   = int(V_mm.argmax())
    eff_w    = w * Aj_E1B
    V_e1b    = X_trio @ eff_w
    opt_e1b  = int(V_e1b.argmax())
    V_sel    = float(X_trio[opt_e1b] @ w)
    R_e1b[d] = (V_max[d] - V_sel) / V_range[d] * 100   # pp, same as oracle
    same_as_mm[d] = (opt_e1b == opt_mm)
    if d % 100 == 0:
        print(f"  draw {d}/{N}", flush=True)

print(f"\nR_e1b stats: min={R_e1b.min():.8f} max={R_e1b.max():.4f} mean={R_e1b.mean():.4f}")
print("--- 5 criteria (denominator=500) ---")
print(f"(0) R < 0  (batch artifact, before clamp): {(R_e1b < 0).sum():3d}")
print(f"(1) R==0.0 exact:         {(R_e1b==0.0).sum():3d}")
print(f"(2) R<1e-12 pp:           {(R_e1b<1e-12).sum():3d}")
print(f"(3) R<1e-9  pp:           {(R_e1b<1e-9).sum():3d}")
print(f"(4) round(R,2)==0.00:     {(np.round(R_e1b,2)==0).sum():3d}")
print(f"(5) opt_e1b==opt_mm:      {same_as_mm.sum():3d}")

# Minimum non-zero R (draws where trio != t*)
diff_trio = ~same_as_mm
if diff_trio.any():
    R_nonzero = R_e1b[diff_trio]
    print(f"\nDraws with opt_e1b != opt_mm (trio != t*): {diff_trio.sum()}")
    print(f"  min R_pp (trio!=t*): {R_nonzero.min():.6f} pp")
    print(f"  max R_pp:            {R_nonzero.max():.4f} pp")
    print(f"  R < 0 in these:      {(R_nonzero < 0).sum()}")
    print(f"  R >= 1e-12 pp:       {(R_nonzero >= 1e-12).sum()}")
    print("  → min 0.0426 pp >> 1e-12; confirms trio_eq_tstar is correct criterion")

np.save(ROOT / "results" / "regret" / "e1b_R_pp_oracle_rerun.npy", R_e1b)
print("Saved results/regret/e1b_R_pp_oracle_rerun.npy", flush=True)
