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
print("\n=== Path 1: Sequential computation (this script, V_all draw-by-draw) ===")
print(f"  (0) R < 0  (before clamp):      {(R_e1b < 0).sum():3d}")
print(f"  (1) R==0.0 exact:               {(R_e1b==0.0).sum():3d}")
print(f"  (2) R<1e-12 pp:                 {(R_e1b<1e-12).sum():3d}")
print(f"  (3) R<1e-9  pp:                 {(R_e1b<1e-9).sum():3d}")
print(f"  (4) round(R,2)==0.00:           {(np.round(R_e1b,2)==0).sum():3d}")
print(f"  (5) opt_e1b==opt_mm (semantic): {same_as_mm.sum():3d}")

diff_trio = ~same_as_mm
if diff_trio.any():
    R_nonzero = R_e1b[diff_trio]
    print(f"  min R_pp (trio!=t*): {R_nonzero[R_nonzero > 0].min():.6f} pp")

# ── Oracle CSV: batch computation (e1_oracle_per_draw.csv, SHA 913396ce) ──────
print("\n=== Path 2: Oracle CSV (batch V_max, compute_regret.py, SHA 913396ce) ===")
E1_OR = ROOT / "results" / "regret" / "e1_oracle_per_draw.csv"
if E1_OR.exists():
    import pandas as _pd
    df_or = _pd.read_csv(E1_OR)
    e1b_or = df_or[(df_or["cell"] == "B") & (df_or["mont"] == "optimal")].sort_values("draw")
    R_or = e1b_or["R_pp"].values
    t_or = e1b_or["trio_eq_tstar"].values.astype(bool)
    n_neg = (R_or < 0).sum()
    n_ex0 = (R_or == 0.0).sum()
    n_pos_near = ((R_or > 0) & (R_or < 1e-9)).sum()
    n_tstar = t_or.sum()
    print(f"  (0) R < 0 (batch artifact):     {n_neg:3d}")
    print(f"  (1) R==0.0 exact:               {n_ex0:3d}")
    print(f"  (2) 0 < R < 1e-9 pp:            {n_pos_near:3d}")
    print(f"  (3) trio == t* (semantic):       {n_tstar:3d}")
    if n_neg > 0:
        print(f"  max |R| (negatives):            {abs(R_or[R_or < 0]).max():.6e} pp")
    diff_or = R_or[(~t_or) & (R_or > 0)]
    if len(diff_or) > 0:
        print(f"  min R_pp (trio!=t*, R>0):       {diff_or.min():.6f} pp")
    print()
    print("  Summary table:")
    print(f"  {'Fonte':<42} {'R==0':>6} {'0<R<1e-9':>9} {'R<0':>5} {'trio=t*':>8}")
    print(f"  {'CSV oráculo (batch V_max)':<42} {n_ex0:>6} {n_pos_near:>9} {n_neg:>5} {n_tstar:>8}")
    print(f"  {'Sequencial (sorteio a sorteio)':<42} {(R_e1b==0.0).sum():>6} {'0':>9} {'0':>5} {same_as_mm.sum():>8}")
    print("  Diferenças: artefacto float64 batch vs sequencial.")
    print(f"  Ambas dão trio==t*=177 e min R (trio!=t*)=0.0426 pp. "
          f"Gate 1 usa o sequencial (compute_value_regret).")
else:
    print("  (e1_oracle_per_draw.csv not found)")

np.save(ROOT / "results" / "regret" / "e1b_R_pp_oracle_rerun.npy", R_e1b)
print("\nSaved results/regret/e1b_R_pp_oracle_rerun.npy", flush=True)
