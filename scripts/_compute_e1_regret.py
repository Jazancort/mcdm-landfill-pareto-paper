# -*- coding: utf-8 -*-
"""
_compute_e1_regret.py  (v2: new denominator)
=============================================
Compute value regret R for all 8 E1 cells (M, B, W, V × greedy/optimal)
with the CORRECTED denominator: range over ALL feasible trios T.

R(t; w) = [V_mm(t*(w); w) - V_mm(t; w)] / [V_mm(t*(w); w) - V_mm(t_min(w); w)]

where:
  t*(w) = argmax V_mm over T (SAW/mm/optimal)
  t_min(w) = argmin V_mm over T (worst feasible trio)

R in [0,1] by construction; independent of which cells are compared.
"""
import sys, os, pathlib
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import pandas as pd

ROOT    = pathlib.Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

if "MCDM_DATA_DIR" not in os.environ:
    _w = ("G:\\Faculdade\\Estudo\\Doutorado\\2025.1\\"
          "Otimiza\u00e7\u00e3o Bioinspirada\\"
          "Tentativa de dados via GIS")
    os.environ["MCDM_DATA_DIR"] = _w

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, MIN_DIST_KM, haversine_km,
    _build_decision_matrix,
)
from fogo_constants import OBJ_GROUPS, AJ_VEC as rho_j, W as w_ahp_raw

df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]] > 0].copy().reset_index(drop=True)
N = len(df_via)
assert N == 389

X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b:
        X_adj[:, j] = 1.0 - X_via[:, j]

D = haversine_km(df_via["latitude (degrees)"].values,
                 df_via["longitude (degrees)"].values)
valid = D >= MIN_DIST_KM

w_ahp = w_ahp_raw / w_ahp_raw.sum()
W_draws = np.load(ROOT / "results" / "e1" / "e1_weights_k200.npy")  # (500, 11)
N_DRAWS = W_draws.shape[0]

# Precompute trio X_adj sums for ALL valid trios
trios = np.load(ROOT / "data" / "fogo_trios.npy").astype(int)  # shape (n_trios, 3)
n_trios = len(trios)
print(f"Sites: {N}, Trios: {n_trios}, Draws: {N_DRAWS}")

# Precompute X_adj sum for each trio: shape (n_trios, 11)
print("Precomputing trio scores ...", flush=True)
X_trio = X_adj[trios[:, 0]] + X_adj[trios[:, 1]] + X_adj[trios[:, 2]]  # (n_trios, 11)
print("Done.", flush=True)

# ── Compute V_max (t*) and V_min (t_min) over ALL trios per draw ──────────────
# V_range = V_max - V_min; R in [0,1] by construction.
# X_trio already loaded above (all trios).
print("Computing V_max and V_min over all trios (batched) ...", flush=True)
BATCH = 50000
V_max_draws = np.full(N_DRAWS, -np.inf)
V_min_draws = np.full(N_DRAWS, np.inf)
for start in range(0, n_trios, BATCH):
    end = min(start + BATCH, n_trios)
    V_batch = X_trio[start:end] @ W_draws.T  # (BATCH, N_DRAWS)
    np.maximum(V_max_draws, V_batch.max(axis=0), out=V_max_draws)
    np.minimum(V_min_draws, V_batch.min(axis=0), out=V_min_draws)
    if start % 500000 == 0:
        print(f"  {start}/{n_trios} ({100*start/n_trios:.0f}%)", flush=True)
V_range_draws = np.maximum(V_max_draws - V_min_draws, 1e-12)
print(f"V_range: min={V_range_draws.min():.4f} max={V_range_draws.max():.4f}", flush=True)

# Verify V_max matches regret_perdraw (SAW/mm/opt)
df_check = pd.read_csv(ROOT / "results" / "regret" / "regret_perdraw.csv")
saw_opt_check = df_check[(df_check["agg"]=="saw") & (df_check["norm"]=="minmax") &
                          (df_check["mont"]=="optimal")].sort_values("draw")
assert np.abs(V_max_draws - saw_opt_check["V_mm"].values).max() < 1e-9, "V_max mismatch"
print("V_max verified against regret_perdraw: OK")

# E1 amplitude sets
GROUPS = OBJ_GROUPS
Aj_bar = np.empty(11)
for g_idx in GROUPS:
    wg = w_ahp[g_idx]
    Ajbar_g = float(np.dot(wg, rho_j[g_idx])) / wg.sum()
    for j in g_idx:
        Aj_bar[j] = Ajbar_g

Aj_E1M = np.ones(11)
Aj_E1B = Aj_bar.copy()
Aj_E1W_raw = rho_j / Aj_bar
scale_EW = np.dot(w_ahp, rho_j) / np.dot(w_ahp, Aj_E1W_raw)
Aj_E1W = Aj_E1W_raw * scale_EW
Aj_E1V = rho_j.copy()

CELLS = {"M": Aj_E1M, "B": Aj_E1B, "W": Aj_E1W, "V": Aj_E1V}

def greedy_trio(score_vec, valid):
    """Simple greedy: pick top-3 distinct valid pair."""
    order = np.argsort(-score_vec)
    chosen = []
    for i in order:
        if len(chosen) == 0:
            chosen.append(i)
        elif len(chosen) == 1:
            if valid[chosen[0], i]:
                chosen.append(i)
        elif len(chosen) == 2:
            if valid[chosen[0], i] and valid[chosen[1], i]:
                chosen.append(i)
                break
    return chosen if len(chosen) == 3 else None

print()
print(f"{'Cell':<5} {'Asm':<8} {'Q2%':>6} {'R_mean':>8} {'R_SE':>6} {'R_med':>8}")
print("-" * 50)

results = {}
for cell_name, A_j in CELLS.items():
    for asm in ["greedy", "optimal"]:
        R_vals = np.empty(N_DRAWS)
        Q2_vals = np.empty(N_DRAWS)
        for d in range(N_DRAWS):
            w = W_draws[d]
            eff_w = w * A_j          # effective weights for this cell
            # Score each candidate
            score = X_adj @ eff_w   # (389,)
            # Score each trio
            score_trio = X_trio @ eff_w  # (n_trios,)
            # Find optimal trio
            opt_idx = np.argmax(score_trio)
            opt_trio = trios[opt_idx]
            i0, i1, i2 = opt_trio
            # V_mm of optimal E1 portfolio
            V_e1_opt = float(X_trio[opt_idx] @ w)
            if asm == "optimal":
                V_sel = V_e1_opt
                Q2_vals[d] = np.nan  # filled below
            else:
                # Greedy
                g = greedy_trio(score, valid)
                if g is None:
                    V_sel = np.nan
                else:
                    i0g, i1g, i2g = sorted(g)
                    V_sel = float((X_adj[i0g] + X_adj[i1g] + X_adj[i2g]) @ w)
            R_vals[d] = (V_max_draws[d] - V_sel) / V_range_draws[d] * 100
        
        R_mean = np.nanmean(R_vals)
        R_se   = np.nanstd(R_vals, ddof=0) / np.sqrt(N_DRAWS)
        R_med  = np.nanmedian(R_vals)
        # Q2 from e1_macros
        q2_ref = {"M greedy":86.0,"M optimal":100.0,"B greedy":100.0,"B optimal":100.0,
                  "W greedy":64.0,"W optimal":64.2,"V greedy":66.2,"V optimal":56.8}
        q2 = q2_ref.get(f"{cell_name} {asm}", float('nan'))
        print(f"E1-{cell_name:<2} {asm:<8} {q2:>6.1f} {R_mean:>8.2f}  {R_se:>5.2f}  {R_med:>8.2f}")
        results[f"{cell_name}_{asm}"] = R_vals

print()
print("Paired bootstrap differences (grd - opt, B=2000, seed=55):")
rng = np.random.default_rng(55)
B = 2000
for cell_name in CELLS:
    grd = results[f"{cell_name}_greedy"]
    opt = results[f"{cell_name}_optimal"]
    obs = grd.mean() - opt.mean()
    boot = np.array([grd[rng.integers(0,N_DRAWS,N_DRAWS)].mean() -
                     opt[rng.integers(0,N_DRAWS,N_DRAWS)].mean() for _ in range(B)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    print(f"  E1-{cell_name}: grd-opt = {obs:.2f} pp  95%CI=[{lo:.1f},{hi:.1f}]")

print()
print("E1-B vs E1-V optimal (between-group cost only):")
rb = results["B_optimal"]
rv = results["V_optimal"]
obs2 = rv.mean() - rb.mean()  # V has MORE regret than B?
boot2 = np.array([(rv[rng.integers(0,N_DRAWS,N_DRAWS)].mean() -
                   rb[rng.integers(0,N_DRAWS,N_DRAWS)].mean()) for _ in range(B)])
lo2, hi2 = np.percentile(boot2, [2.5, 97.5])
print(f"  E1-V_opt - E1-B_opt = {obs2:.2f} pp  95%CI=[{lo2:.1f},{hi2:.1f}]")
print()
print("SAW/mm/opt R = 0 exactly (regression):", np.all(np.abs(results['M_optimal']) < 1e-9))
print("E1-B_opt = 0 (between-group costs nothing in R?): max R =", np.max(results['B_optimal']).round(4))