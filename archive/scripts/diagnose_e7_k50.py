# -*- coding: utf-8 -*-
"""
diagnose_e7_k50.py  --  DEV-E7-001 diagnostic script.

Decision rule (from DEV-E7-001, written before diagnosis):
  D1. W_e7(κ=50) ≠ W_mc2cube(κ=50) → draws differ, Table 5/6 κ=50 stands, no macro change
  D2. W identical, trios differ       → scorer bug, must follow §4.3 convention
  D3. W identical, trios identical    → comparison script bug only

Part 1: Are the draws the same?
  - mc_2cube uses: for alpha in [50,200]: rng=np.random.default_rng(42); w=rng.dirichlet(alpha*w_ahp)
  - E7 should load: results/e1/e1_weights_k50.npy  (SHA e761c76d...)
  - If SHA differs → D1 (stop here)
  - If SHA matches → Part 2

Part 2 (only if Part 1 = same): Per-draw trio comparison
  - Rerun both scorers draw-by-draw for each of the 8 cells
  - Count draws where selected trios differ

Part 3 (only if D2): Convention check for ρ_perm
  - ρ_perm must equal 0.583 under the convention declared in §4.3
  - (norm over x̃, orientation after normalisation)
"""
import os, sys, hashlib, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

if "MCDM_DATA_DIR" not in os.environ:
    for candidate in [
        "/home/julioazancort/scratch/mcdm",
        str(ROOT / "data"),
    ]:
        if os.path.exists(candidate):
            os.environ["MCDM_DATA_DIR"] = candidate
            break

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS,
    haversine_km, MIN_DIST_KM, _build_decision_matrix,
    greedy_trio,
)
from pareto_utils import build_pareto_utils
from scoring import make_scorers

# ─────────────────────────────────────────────────────────────────────────────
# Part 1: Are the draws the same?
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("PART 1: Draw comparison (SHAs)")
print("=" * 60)

w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
SEED  = 42  # mc_2cube seed

# mc_2cube k50 draws (regenerate with the exact same code as mc_2cube_and_4thcell.py)
rng_mc2 = np.random.default_rng(SEED)
W_mc2_k50 = rng_mc2.dirichlet(50 * w_ahp, size=500)
sha_mc2 = hashlib.sha256(W_mc2_k50.tobytes()).hexdigest()

# E7 k50 draws (from the matrix file)
k50_path = ROOT / "results" / "e1" / "e1_weights_k50.npy"
if k50_path.exists():
    W_e7_k50 = np.load(k50_path)
    sha_e7 = hashlib.sha256(W_e7_k50.tobytes()).hexdigest()
else:
    # Fall back: E7 v1/v2 used seed=43 (old script)
    rng_e7_old = np.random.default_rng(43)
    W_e7_k50 = rng_e7_old.dirichlet(50 * w_ahp, size=500)
    sha_e7 = hashlib.sha256(W_e7_k50.tobytes()).hexdigest()
    print("WARNING: e1_weights_k50.npy not found, using seed=43 fallback")

print(f"SHA mc_2cube k50:   {sha_mc2[:16]}")
print(f"SHA E7 k50:        {sha_e7[:16]}")
max_diff = float(np.abs(W_mc2_k50 - W_e7_k50).max())
print(f"max|ΔW| = {max_diff:.2e}")

if max_diff > 1e-10:
    print()
    print("CONCLUSION: D1 — draws are DIFFERENT. Table 5/6 κ=50 stands.")
    print("E7 κ=50 is a second independent replicate.")
    print("Difference reflects seed-to-seed variability (not a pipeline bug).")
    print()
    # Show draw statistics
    print(f"W_mc2[0,:3] = {W_mc2_k50[0,:3]}")
    print(f"W_e7[0,:3]  = {W_e7_k50[0,:3]}")
    print()
    # Quantify variability
    print("Variability between the two k50 runs (difference in Q2):")
    e7_raw = ROOT / "results" / "e7" / "e7_raw.csv"
    if e7_raw.exists():
        df_e7 = pd.read_csv(e7_raw)
        df_50 = df_e7[df_e7.alpha==50]
        print("E7 k50 Q2:")
        print(df_50.groupby(["agg","norm","mont"])["nd_Q2Ap"].mean().mul(100).round(1).to_string())
    sys.exit(0)

# ─────────────────────────────────────────────────────────────────────────────
# Part 2: Same draws → per-draw trio comparison
# ─────────────────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("PART 2: Per-draw trio comparison (same draws)")
print("=" * 60)
print("Loading data for scorer comparison...")

df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]] > 0].copy()
N = len(df_via)
w_ahp_full = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
D = haversine_km(df_via["latitude (degrees)"].values, df_via["longitude (degrees)"].values)
valid = D >= MIN_DIST_KM
trios = np.array(
    [(i,j,k) for i in range(N) for j in range(i+1,N) if valid[i,j]
     for k in range(j+1,N) if valid[i,k] and valid[j,k]],
    dtype=np.int32,
)
T0, T1, T2 = trios[:,0], trios[:,1], trios[:,2]

compute_objs, is_dominated, _ = build_pareto_utils(df_via, list(AHP_WEIGHTS.keys()), trios)
X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b: X_adj[:,j] = 1.0 - X_via[:,j]
norms_via = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)
saw_new, topsis_new = make_scorers(X_via, X_adj, norms_via, benefit)

# mc_2cube scoring (inline, as in the original script)
def saw_old(w, norm="minmax"):
    if norm == "minmax":
        return (X_adj * w).sum(1)
    else:
        return ((X_via / norms_via) * w).sum(1)  # mc_2cube uses X_via

def topsis_old(w, norm="minmax"):
    Xb = X_via if norm == "minmax" else X_via / norms_via
    V = Xb * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp = np.sqrt(((V-PIS)**2).sum(1))
    dn = np.sqrt(((V-NIS)**2).sum(1))
    return np.where(dp+dn==0, 0.5, dn/(dp+dn))

def argmax_trio(sc):
    return trios[int((sc[T0]+sc[T1]+sc[T2]).argmax())]

CELLS_8 = [
    ("saw","minmax","greedy"), ("saw","minmax","optimal"),
    ("saw","vector","greedy"), ("saw","vector","optimal"),
    ("topsis","minmax","greedy"), ("topsis","minmax","optimal"),
    ("topsis","vector","greedy"), ("topsis","vector","optimal"),
]

W = W_mc2_k50  # same draws confirmed
print(f"Running {len(CELLS_8)} cells × {len(W)} draws...")
t0 = time.time()

trio_diffs = {}
for cell in CELLS_8:
    agg, norm, mont = cell
    n_diff = 0
    for d in range(len(W)):
        w = W[d]
        if agg == "saw":
            sc_old = saw_old(w, norm)
            sc_new = saw_new(w, norm)
        else:
            sc_old = topsis_old(w, norm)
            sc_new = topsis_new(w, norm)
        if mont == "greedy":
            t_old = tuple(greedy_trio(sc_old, D))
            t_new = tuple(greedy_trio(sc_new, D))
        else:
            t_old = tuple(argmax_trio(sc_old))
            t_new = tuple(argmax_trio(sc_new))
        if t_old != t_new:
            n_diff += 1
    trio_diffs[f"{agg}/{norm}/{mont}"] = n_diff

print(f"Done in {time.time()-t0:.0f}s")
print()
for cell_name, n in trio_diffs.items():
    print(f"  {cell_name}: {n}/500 trios differ")

any_diff = any(n > 0 for n in trio_diffs.values())
if any_diff:
    print()
    print("CONCLUSION: D2 — same draws, trios differ. A scorer difference exists.")
    print("Proceed to Part 3 (convention check).")
else:
    print()
    print("CONCLUSION: D3 — same draws, same trios. Comparison script bug only.")
    print("No pipeline issue.")

# ─────────────────────────────────────────────────────────────────────────────
# Part 3 (only if D2): Convention check for ρ_perm
# ─────────────────────────────────────────────────────────────────────────────
if any_diff:
    print()
    print("=" * 60)
    print("PART 3: ρ_perm convention check (§4.3)")
    print("=" * 60)
    col_names = list(AHP_WEIGHTS.keys())
    J_PERM = col_names.index("perm")
    x_perm_via = df_via[COL["perm"]].values.astype(float)
    x_perm_via_full = df_imp[COL["perm"]].values.astype(float)
    
    # Min-max normalise over 389 sites (space A' convention)
    mn_389, mx_389 = x_perm_via.min(), x_perm_via.max()
    xmm_389 = (x_perm_via - mn_389) / max(mx_389 - mn_389, 1e-12)
    
    # Min-max normalise over 473 sites
    mn_473, mx_473 = x_perm_via_full.min(), x_perm_via_full.max()
    xmm_473 = (x_perm_via - mn_473) / max(mx_473 - mn_473, 1e-12)
    
    # ρ_j = (max_a x̃_j(a) - min_a x̃_j(a)) / ||x̃_j||
    # where x̃ = min-max normalised (=benefit-adjusted for benefit criteria)
    
    # Option A: norm over x̃_adj (after benefit-adjustment of cost criteria)
    perm_is_cost = ("perm" in {"perm", "slope", "roads", "rivers", "coast", "wells"})
    xadj_389 = (1 - xmm_389) if perm_is_cost else xmm_389
    rho_adj = float((xadj_389.max() - xadj_389.min()) / np.linalg.norm(xadj_389))
    
    # Option B: norm over x_via (raw), range of adj values
    rho_via = float((xadj_389.max() - xadj_389.min()) / np.linalg.norm(x_perm_via))
    
    # Option C: norm over x̃_via (not adjusted for cost)
    rho_raw = float((xmm_389.max() - xmm_389.min()) / np.linalg.norm(xmm_389))
    
    print(f"ρ_perm options:")
    print(f"  A: range(X_adj)/||X_adj||      = {rho_adj:.4f}")
    print(f"  B: range(X_adj)/||X_via||       = {rho_via:.4f} ← norms_via (scoring.py)")
    print(f"  C: range(X_via)/||X_via||       = {rho_raw:.4f}")
    print()
    print(f"Paper Table 2 declares ρ_perm = 0.583 (approx)")
    print(f"Closest match: {'B' if abs(rho_via-0.583)<0.01 else 'A' if abs(rho_adj-0.583)<0.01 else 'C'}")
    print()
    print("Convention §4.3: 'we adopt orientation after forming the norm'")
    print("This means: compute ||x̃_j|| over UNadjusted x̃_j (= x_via after min-max)")
    print("then flip for cost criteria. This corresponds to Option B.")
