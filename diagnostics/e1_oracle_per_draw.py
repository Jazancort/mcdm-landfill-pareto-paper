# -*- coding: utf-8 -*-
"""diagnostics/e1_oracle_per_draw.py — Per-draw E1 oracle CSV.

Reproduces _compute_e1_regret.py logic (SHA-verified) and saves one row per
(draw, cell, assembly) with: R in pp, selected trio indices, t* indices,
and whether the trio equals t*.

Used by Gate 1 to compare E1-B and E1-W draw-by-draw.

Usage (on Athena):
    MCDM_DATA_DIR=/home/julioazancort/scratch/mcdm \\
    .venv/bin/python3 diagnostics/e1_oracle_per_draw.py

Output:
    results/regret/e1_oracle_per_draw.csv
    (run sha256sum to record SHA before committing)
"""
import sys, os, hashlib
from pathlib import Path

ROOT    = Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"
OUT_CSV = ROOT / "results" / "regret" / "e1_oracle_per_draw.csv"

sys.path.insert(0, str(SCRIPTS))
os.environ.setdefault("MCDM_DATA_DIR", "/home/julioazancort/scratch/mcdm")

# ── SHA-verify _compute_e1_regret.py ─────────────────────────────────────────
SHA_E1_ORACLE = "1df1b7e7b9a6438f275b0849623971d69fd039d3e74bc20d6cbb43988ea8978e"
oracle_path   = SCRIPTS / "_compute_e1_regret.py"
sha_got       = hashlib.sha256(oracle_path.read_bytes()).hexdigest()
assert sha_got == SHA_E1_ORACLE, (
    f"SHA mismatch for _compute_e1_regret.py:\n"
    f"  expected {SHA_E1_ORACLE}\n  got      {sha_got}"
)
print(f"SHA _compute_e1_regret.py: OK ({sha_got[:16]})", flush=True)

import numpy as np
import pandas as pd

from mcdm_experiment import (
    load_data, impute_nan, COL, haversine_km, MIN_DIST_KM, _build_decision_matrix,
)
from fogo_constants import OBJ_GROUPS, AJ_VEC as rho_j, W as w_ahp_raw

# ── Data (same as _compute_e1_regret.py) ─────────────────────────────────────
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

D     = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
valid = D >= MIN_DIST_KM
w_ahp = w_ahp_raw / w_ahp_raw.sum()
W     = np.load(ROOT / "results" / "e1" / "e1_weights_k200.npy")   # (500, 11) float64
N     = W.shape[0]

trios   = np.load(ROOT / "data" / "fogo_trios.npy").astype(int)
X_trio  = X_adj[trios[:, 0]] + X_adj[trios[:, 1]] + X_adj[trios[:, 2]]
n_trios = len(trios)

# ── V_range from regret_perdraw.csv (same as v2 of _compute_e1_regret.py) ────
print("Loading V_range from regret_perdraw.csv...", flush=True)
df_rpd   = pd.read_csv(ROOT / "results" / "regret" / "regret_perdraw.csv")
saw_opt  = df_rpd[(df_rpd["agg"] == "saw") & (df_rpd["norm"] == "minmax") &
                  (df_rpd["mont"] == "optimal")].sort_values("draw")
assert len(saw_opt) == N, f"Expected {N} saw/mm/opt rows, got {len(saw_opt)}"
V_max_csv   = saw_opt["V_mm"].values      # (500,) — V_mm of SAW/mm/opt per draw
V_range_csv = saw_opt["V_range"].values   # (500,) — V_range over all T per draw

# ── E1 amplitude sets (same as _compute_e1_regret.py) ────────────────────────
Aj_bar = np.empty(11)
for g_idx in OBJ_GROUPS:
    wg  = w_ahp[g_idx]
    avg = float(np.dot(wg, rho_j[g_idx])) / wg.sum()
    for j in g_idx:
        Aj_bar[j] = avg

Aj_E1M  = np.ones(11)
Aj_E1B  = Aj_bar.copy()
Aj_E1W_raw = rho_j / Aj_bar
scale_EW   = np.dot(w_ahp, rho_j) / np.dot(w_ahp, Aj_E1W_raw)
Aj_E1W  = Aj_E1W_raw * scale_EW
Aj_E1V  = rho_j.copy()
CELLS   = {"M": Aj_E1M, "B": Aj_E1B, "W": Aj_E1W, "V": Aj_E1V}

# ── Greedy selector (same logic as _compute_e1_regret.py) ────────────────────
def greedy_sel(score_vec):
    """Same implementation as greedy_trio() in _compute_e1_regret.py."""
    order  = np.argsort(-score_vec)
    chosen = []
    for i in order:
        if len(chosen) == 0:
            chosen.append(int(i))
        elif len(chosen) == 1:
            if valid[chosen[0], i]:
                chosen.append(int(i))
        elif len(chosen) == 2:
            if valid[chosen[0], i] and valid[chosen[1], i]:
                chosen.append(int(i))
                break
    return chosen if len(chosen) == 3 else None

# ── Per-draw computation ──────────────────────────────────────────────────────
print(f"Computing per-draw oracle (N={N}, n_trios={n_trios})...", flush=True)
rows = []
for d in range(N):
    w = W[d]
    V_range_d = V_range_csv[d]
    V_max_d   = V_max_csv[d]

    # t* = SAW/mm/opt trio for this draw (argmax V_mm over all trios)
    V_mm = X_trio @ w
    tstar_idx  = int(V_mm.argmax())
    tstar_trio = sorted(trios[tstar_idx].tolist())

    for cell_name, A_j in CELLS.items():
        eff_w = w * A_j
        score = X_adj @ eff_w   # (N,) per-site scores

        for mont in ["optimal", "greedy"]:
            if mont == "optimal":
                score_trio = X_trio @ eff_w
                sel_idx    = int(score_trio.argmax())
                sel_trio   = sorted(trios[sel_idx].tolist())
            else:
                g = greedy_sel(score)
                if g is None:
                    rows.append({
                        "draw": d, "cell": cell_name, "mont": mont,
                        "R_pp": np.nan,
                        "i0": -1, "i1": -1, "i2": -1,
                        "tstar_i0": tstar_trio[0], "tstar_i1": tstar_trio[1],
                        "tstar_i2": tstar_trio[2],
                        "trio_eq_tstar": False,
                    })
                    continue
                sel_trio = sorted(g)

            V_sel = float((X_adj[sel_trio[0]] + X_adj[sel_trio[1]] + X_adj[sel_trio[2]]) @ w)
            R_pp  = (V_max_d - V_sel) / V_range_d * 100

            rows.append({
                "draw": d, "cell": cell_name, "mont": mont,
                "R_pp": R_pp,
                "i0": sel_trio[0], "i1": sel_trio[1], "i2": sel_trio[2],
                "tstar_i0": tstar_trio[0], "tstar_i1": tstar_trio[1],
                "tstar_i2": tstar_trio[2],
                "trio_eq_tstar": (sel_trio == tstar_trio),
            })

    if d % 100 == 0:
        print(f"  draw {d}/{N}", flush=True)
df_out = pd.DataFrame(rows)
df_out.to_csv(OUT_CSV, index=False)
sha_out = hashlib.sha256(OUT_CSV.read_bytes()).hexdigest()
print(f"\nSaved: {OUT_CSV}")
print(f"SHA-256: {sha_out}")
print(f"Rows: {len(df_out)}")

# ── Verify 101/177 split ──────────────────────────────────────────────────────
e1b_opt = df_out[(df_out["cell"] == "B") & (df_out["mont"] == "optimal")]
n_trio_eq = e1b_opt["trio_eq_tstar"].sum()
n_r_zero  = (e1b_opt["R_pp"] == 0.0).sum()
n_r_near  = (e1b_opt["R_pp"] < 1e-9).sum()
print(f"\nE1-B opt zeros table (N={len(e1b_opt)}):")
print(f"  R_pp == 0.0 exact:      {n_r_zero:3d}  ({100*n_r_zero/N:.1f}%)")
print(f"  R_pp < 1e-9:            {n_r_near:3d}  ({100*n_r_near/N:.1f}%)")
print(f"  trio == t* (semantic):  {n_trio_eq:3d}  ({100*n_trio_eq/N:.1f}%)")

# ── Verify: 76 draws with R in (0, 1e-12) have trio == t* ────────────────────
near_zero = e1b_opt[(e1b_opt["R_pp"] > 0) & (e1b_opt["R_pp"] < 1e-9)]
if len(near_zero) > 0:
    all_tstar = near_zero["trio_eq_tstar"].all()
    print(f"\n76 draws with 0 < R_pp < 1e-9: {len(near_zero)} draws, trio==t* in ALL: {all_tstar}")
    print(f"  max R_pp in these draws: {near_zero['R_pp'].max():.3e}")

# ── Smallest R among draws where trio != t* ──────────────────────────────────
different_trio = e1b_opt[~e1b_opt["trio_eq_tstar"]]
if len(different_trio) > 0:
    min_R_diff = different_trio["R_pp"].min()
    print(f"\nDraws with trio != t*: {len(different_trio)}")
    print(f"  smallest R_pp (non-tstar): {min_R_diff:.6f} pp")
    print("  (must be >> 1e-12 pp to justify 177 as correct criterion)")

print("\nDone.", flush=True)
