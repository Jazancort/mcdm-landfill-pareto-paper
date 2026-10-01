"""scripts/tvw_e4.py
Compute TV_W for the R-W cell of E4 using exact amplitude ratios
(range_389/range_473) from the project data via load_data().

TV_{W,g} = 0.5 * sum_{j in G_g} (w_j / W_g) * |A_j - 1|
TV_W     = sum_g W_g * TV_{W,g}

where A_j = r_j / rbar_g, r_j = range_389(j) / range_473(j),
rbar_g = sum_{j in G_g} w_j * r_j / W_g  (w-weighted mean within group).

Also saves the E1 weight matrix (500 draws, kappa=200, seed=42) as
results/e1_weights_k200.npy and prints its SHA-256 hash.

Run before committing DEV-E4-004. Commit this script and its output.

Run as: uv run python scripts/tvw_e4.py
"""
import hashlib
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent.parent
RESULTS = ROOT / "results"
sys.path.insert(0, str(ROOT / "scripts"))

from mcdm_experiment import (   # noqa: E402
    load_data, impute_nan, COL, AHP_WEIGHTS,
)

# ── Load datasets ──────────────────────────────────────────────────────────────
if "MCDM_DATA_DIR" not in os.environ:
    # Try Athena path; fallback to local data/
    athena = "/home/julioazancort/scratch/mcdm"
    local  = str(ROOT / "data")
    os.environ["MCDM_DATA_DIR"] = athena if os.path.exists(athena) else local

df_all, _par, _bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()

print(f"Candidates (df_imp): {len(df_imp)}")
print(f"Admissible (df_via): {len(df_via)}")
assert len(df_imp) == 473, f"Expected 473 candidates, got {len(df_imp)}"
assert len(df_via) == 389, f"Expected 389 admissible, got {len(df_via)}"

# ── AHP weights and groups ─────────────────────────────────────────────────────
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())

GROUPS = {
    "G1": ["perm", "slope", "roads"],
    "G2": ["rivers", "aspect", "coast", "protected", "wells"],
    "G3": ["urban", "aero", "cult"],
}

# ── Compute exact amplitude ratios r_j = range_389(j) / range_473(j) ──────────
def col_range(df, crit):
    c = COL[crit]
    vals = df[c].values.astype(float)
    rng = vals.max() - vals.min()
    return rng

r_j = {}
for crit in col_names:
    r473 = col_range(df_imp, crit)
    r389 = col_range(df_via, crit)
    r_j[crit] = 1.0 if r473 < 1e-12 else r389 / r473

print("\nAmplitude ratios r_j = range_389 / range_473:")
for crit in col_names:
    w = AHP_WEIGHTS[crit]
    print(f"  {crit:12s}: r_j={r_j[crit]:.4f}  w={w:.3f}")

# ── Compute TV_W(R-W) ──────────────────────────────────────────────────────────
print("\n=== TV_W(R-W) computation ===")
TV_W_total = 0.0
for g_name, crits in GROUPS.items():
    W_g   = sum(AHP_WEIGHTS[c] for c in crits)
    rbar_g = sum(AHP_WEIGHTS[c] * r_j[c] for c in crits) / W_g

    TV_Wg = 0.0
    for c in crits:
        w_j   = AHP_WEIGHTS[c]
        A_j   = r_j[c] / rbar_g
        TV_Wg += (w_j / W_g) * abs(A_j - 1.0)
    TV_Wg *= 0.5   # factor 1/2 in TV definition

    contrib = W_g * TV_Wg
    TV_W_total += contrib
    print(f"  {g_name}: W_g={W_g:.3f}  rbar_g={rbar_g:.4f}  "
          f"TV_Wg={TV_Wg:.4f}  W_g*TV_Wg={contrib:.5f}")
    for c in crits:
        A_j = r_j[c] / rbar_g
        print(f"    {c:12s}: r_j={r_j[c]:.4f}  A_j={A_j:.4f}  |A_j-1|={abs(A_j-1):.4f}")

print(f"\nTV_W(R-W) = {TV_W_total:.4f}")

# ── Cross-check: TV_W(E1-V) ────────────────────────────────────────────────────
# rho_j from tab:e1 of the manuscript (vector normalisation amplitudes)
RHO = {
    "perm": 0.583, "slope": 0.135, "roads": 0.206,
    "rivers": 0.265, "aspect": 0.103, "coast": 0.126,
    "protected": 0.105, "wells": 0.081,
    "urban": 0.107, "aero": 0.086, "cult": 0.171,
}
print("\n=== Cross-check: TV_W(E1-V) using same formula ===")
TV_W_vec = 0.0
for g_name, crits in GROUPS.items():
    W_g    = sum(AHP_WEIGHTS[c] for c in crits)
    Abar_g = sum(AHP_WEIGHTS[c] * RHO[c] for c in crits) / W_g
    TV_Wg  = 0.0
    for c in crits:
        w_j  = AHP_WEIGHTS[c]
        A_j  = RHO[c] / Abar_g
        TV_Wg += (w_j / W_g) * abs(A_j - 1.0)
    TV_Wg *= 0.5
    contrib = W_g * TV_Wg
    TV_W_vec += contrib
    print(f"  {g_name}: Abar_g={Abar_g:.4f}  TV_Wg={TV_Wg:.4f}  contrib={contrib:.5f}")

print(f"TV_W(E1-V) computed = {TV_W_vec:.4f}  (manuscript \\TVWvec = 0.199)")

# ── Save E1 weight matrix ─────────────────────────────────────────────────────
print("\n=== E1 weight matrix (seed=42, kappa=200, N=500) ===")
KAPPA    = 200
SEED     = 42
N_DRAWS  = 500
rng      = np.random.default_rng(SEED)
e1_weights = rng.dirichlet(KAPPA * w_ahp, size=N_DRAWS)
assert e1_weights.shape == (N_DRAWS, len(w_ahp))

RESULTS.mkdir(exist_ok=True)
out_path = RESULTS / "e1_weights_k200.npy"
np.save(out_path, e1_weights)
sha256 = hashlib.sha256(out_path.read_bytes()).hexdigest()
print(f"Saved : {out_path}")
print(f"SHA-256: {sha256}")
print(f"Shape  : {e1_weights.shape}  dtype={e1_weights.dtype}")
print(f"Row 0 sum: {e1_weights[0].sum():.10f}  (must be 1.0)")

# ── G1 intra-group distortion comparison E1-W vs R-W ─────────────────────────
print("\n=== G1 intra-group distortion: E1-W vs R-W ===")
W_G1    = sum(AHP_WEIGHTS[c] for c in GROUPS["G1"])
Abar_G1_vec = sum(AHP_WEIGHTS[c] * RHO[c] for c in GROUPS["G1"]) / W_G1
rbar_G1_ref = sum(AHP_WEIGHTS[c] * r_j[c] for c in GROUPS["G1"]) / W_G1
print(f"  E1-W: perm factor = rho_perm/Abar_G1 = {RHO['perm']:.3f}/{Abar_G1_vec:.3f} "
      f"= {RHO['perm']/Abar_G1_vec:.3f}x  (inflation)")
print(f"  R-W : perm factor = r_perm/rbar_G1   = {r_j['perm']:.3f}/{rbar_G1_ref:.3f} "
      f"= {r_j['perm']/rbar_G1_ref:.3f}x  (deflation)")

print("\n=== Summary for DEV-E4-003 and DEV-E4-004 ===")
print(f"  TV_W(R-W)  = {TV_W_total:.4f}")
print(f"  TV_W(E1-V) = {TV_W_vec:.4f}  (cross-check vs 0.199)")
print(f"  E1 weight matrix: {out_path.name}")
print(f"  SHA-256: {sha256}")
