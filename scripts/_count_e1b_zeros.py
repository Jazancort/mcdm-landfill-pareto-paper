# -*- coding: utf-8 -*-
"""_count_e1b_zeros.py — Count draws where R(E1-B_opt) == 0 with 5 criteria.

Replicates _compute_e1_regret.py logic (same data, same amplitudes, same R formula).
Loops over draws (no large matrix transpose to avoid OOM on Athena).
"""
import sys, os
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("MCDM_DATA_DIR", "/home/julioazancort/scratch/mcdm")

import numpy as np

from mcdm_experiment import (
    load_data, impute_nan, COL, haversine_km, _build_decision_matrix,
)
from fogo_constants import OBJ_GROUPS, AJ_VEC as rho_j, W as w_ahp_raw

# ── Data loading ──────────────────────────────────────────────────────────────
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
W      = np.load(ROOT / "results" / "e1" / "e1_weights_k200.npy")  # (500, 11)
N      = W.shape[0]
X_trio = X_adj[trios[:, 0]] + X_adj[trios[:, 1]] + X_adj[trios[:, 2]]  # (n_trios, 11)
n_t    = len(trios)
print(f"N_DRAWS={N}  n_trios={n_t}", flush=True)

# ── E1-B amplitudes (fixed w_ahp, same as _compute_e1_regret.py) ─────────────
Aj_bar = np.empty(11)
for g_idx in OBJ_GROUPS:
    wg  = w_ahp[g_idx]
    avg = float(np.dot(wg, rho_j[g_idx])) / wg.sum()
    for j in g_idx:
        Aj_bar[j] = avg
Aj_E1B = Aj_bar.copy()

# ── V_max and V_min per draw (batch, same as oracle) ────────────────────────
print("Computing V_max, V_min...", flush=True)
BATCH = 25000
V_max = np.full(N, -np.inf)
V_min = np.full(N,  np.inf)
for s in range(0, n_t, BATCH):
    e  = min(s + BATCH, n_t)
    Vb = X_trio[s:e] @ W.T   # (BATCH, N)
    np.maximum(V_max, Vb.max(0), out=V_max)
    np.minimum(V_min, Vb.min(0), out=V_min)
V_range = np.maximum(V_max - V_min, 1e-12)
print(f"V_range: min={V_range.min():.4f} max={V_range.max():.4f}", flush=True)

# ── Per-draw computation ──────────────────────────────────────────────────────
R_e1b   = np.empty(N)
same_as_mm = np.zeros(N, dtype=bool)

for d in range(N):
    w  = W[d]                          # float64 draw
    # SAW_mm score and opt index
    V_mm   = X_trio @ w               # (n_trios,)
    opt_mm = int(V_mm.argmax())

    # E1-B score and opt index
    eff_w  = w * Aj_E1B               # (11,)
    V_e1b  = X_trio @ eff_w           # (n_trios,)
    opt_e1b = int(V_e1b.argmax())

    # V_mm of the E1-B optimal trio (same as oracle: X_trio[opt] @ w)
    V_sel  = float(X_trio[opt_e1b] @ w)
    R_e1b[d] = (V_max[d] - V_sel) / V_range[d] * 100  # pp, same as oracle formula

    same_as_mm[d] = (opt_e1b == opt_mm)

    if d % 100 == 0:
        print(f"  draw {d}/{N}", flush=True)

# ── Count zeros with 5 criteria ───────────────────────────────────────────────
print("\n--- R_e1b stats (pp) ---")
print(f"min={R_e1b.min():.8f}  max={R_e1b.max():.4f}  mean={R_e1b.mean():.4f}")
print(f"N where R < 1e-14 pp:  {(R_e1b < 1e-14).sum()}")
print()
print("--- 5 criteria (denominator = 500 draws) ---")
print(f"(1) R_vals == 0.0 exact:        {(R_e1b == 0.0).sum():3d} / {N}  = {(R_e1b == 0.0).mean()*100:.1f}%")
print(f"(2) R_vals < 1e-12 pp:          {(R_e1b < 1e-12).sum():3d} / {N}  = {(R_e1b < 1e-12).mean()*100:.1f}%")
print(f"(3) R_vals < 1e-9  pp:          {(R_e1b < 1e-9 ).sum():3d} / {N}  = {(R_e1b < 1e-9).mean()*100:.1f}%")
print(f"(4) round(R_vals,2) == 0.00:    {(np.round(R_e1b,2)==0).sum():3d} / {N}  = {(np.round(R_e1b,2)==0).mean()*100:.1f}%")
print(f"(5) opt_e1b == opt_mm (trio=t*):{same_as_mm.sum():3d} / {N}  = {same_as_mm.mean()*100:.1f}%")
print()

# Save R_e1b for further inspection
np.save(ROOT / "results" / "regret" / "e1b_R_pp_oracle_rerun.npy", R_e1b)
print("Saved results/regret/e1b_R_pp_oracle_rerun.npy", flush=True)
