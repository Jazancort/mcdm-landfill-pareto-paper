# -*- coding: utf-8 -*-
"""gate_e1_fogo_v2.py — Fogo E1 regression gate for DEV-SANT-E1-001 fix.

Uses the correct rho_j from amplitudes.json (1/L2(mm_norm(x_j))), not np.std.
Root cause of gate_e1_fogo.py failure (gate_e1_fogo_v1): rho_j ≈ uniform from
np.std, which made E1-W ≡ E1-M, giving trivially 100% for both.

Reference values (source: data/e1_v3_rerun_20261002.log, SHA e05cd8a4...):
  E1-M opt: 100.0%   E1-B opt: 100.0%
  E1-W opt:  64.2%   E1-V opt:  56.8%

Convention: all-benefit X_mm (cost criteria inverted), consistent with WP3 pipeline.
Verified by cross-check in e1_macros.tex: EoneVloss == 100 - QtwovecOptimal (56.8%).

Run:
  CUDA_VISIBLE_DEVICES=0 uv run python scripts/gate_e1_fogo_v2.py
"""
import json
import sys
import os
import hashlib
import numpy as np
from pathlib import Path

ROOT    = Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

if "MCDM_DATA_DIR" not in os.environ:
    os.environ["MCDM_DATA_DIR"] = "/home/julioazancort/scratch/mcdm"

# ── Load correct Fogo rho_j from amplitudes.json ─────────────────────────────
AMP_JSON = ROOT / "results" / "amplitudes" / "amplitudes.json"
assert AMP_JSON.exists(), f"Missing: {AMP_JSON}"
amp = json.loads(AMP_JSON.read_text())

FOGO_CRIT = [
    "perm", "slope", "roads", "rivers", "aspect", "coast",
    "protected", "wells", "urban", "aero", "cult",
]
rho_j_fogo = np.array([amp["rho_j"][c] for c in FOGO_CRIT], dtype=float)
FOGO_GROUPS = [[0, 1, 2], [3, 4, 5, 6, 7], [8, 9, 10]]
print(f"rho_j from amplitudes.json:")
for c, r in zip(FOGO_CRIT, rho_j_fogo):
    print(f"  {c:12s}: {r:.6f}")

# Quick sanity: perm_inflation = rho_j[perm] / sum(w * rho_j) / w[perm]
# Not needed here; compute_stage3b.py already validates this gate

# ── Load Fogo X_mm (all-benefit direction) ───────────────────────────────────
from mcdm_experiment import (
    load_data, impute_nan, COL, _build_decision_matrix,
)

print("\nLoading Fogo data...", flush=True)
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]] > 0].copy().reset_index(drop=True)
N = len(df_via)
assert N == 389, f"Expected 389 admissible sites, got {N}"

# _build_decision_matrix returns (X, benefit) where:
#   benefit=True  → X is already benefit direction (higher = better)
#   benefit=False → X is COST direction (lower = better, need to invert to 1-X)
X_raw, benefit = _build_decision_matrix(df_via)

# Convert all columns to benefit direction (higher = better)
X_adj = X_raw.copy()
for j, b in enumerate(benefit):
    if not b:
        X_adj[:, j] = 1.0 - X_raw[:, j]

# Min-max normalise each column over admissible sites
# (columns are already in [0,1] from _build_decision_matrix/_norm,
#  but normalise again to be safe with the admissible subset)
lo = X_adj.min(0)
hi = X_adj.max(0)
denom = np.where(hi - lo > 1e-9, hi - lo, 1.0)
X_mm = (X_adj - lo) / denom   # (389, 11), all benefit direction
print(f"  N_adm={N}  X_mm shape={X_mm.shape}  benefit_flags={benefit.tolist()}")

# ── Load trios ────────────────────────────────────────────────────────────────
trios_path = ROOT / "data" / "fogo_trios.npy"
trios = np.load(trios_path).astype(np.int32)
assert len(trios) == 1_944_653, f"Expected 1,944,653 trios, got {len(trios)}"
print(f"  n_trios={len(trios):,}")

# ── Load E1 weights ───────────────────────────────────────────────────────────
wmat_path = ROOT / "results" / "e1" / "e1_weights_k200.npy"
SHA_W = "bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487"
assert hashlib.sha256(wmat_path.read_bytes()).hexdigest() == SHA_W, "SHA mismatch"
W = np.load(wmat_path)   # (500, 11)
print(f"  E1 weights: shape={W.shape}  SHA OK")

# ── Import corrected E1 functions ─────────────────────────────────────────────
from run_santiago_mc import (
    get_e1_amplitudes, optimal_selector,
    compute_group_objectives, compute_trio_objectives, check_dominated_raw,
)

# ── Run 500 draws ─────────────────────────────────────────────────────────────
N_DRAWS = 500
A_ones = np.ones(len(rho_j_fogo))
q2_opt = {"M": [], "B": [], "W": [], "V": []}

print(f"\nRunning {N_DRAWS} draws (CPU)...", flush=True)
for draw_idx in range(N_DRAWS):
    w = W[draw_idx]

    # mm group objectives and frontier (all-benefit convention)
    F_mm_site  = compute_group_objectives(X_mm, w, A_ones, FOGO_GROUPS)
    F_mm_trios = compute_trio_objectives(F_mm_site, trios)

    # E1 cells with corrected mm-frontier logic
    e1_amps = get_e1_amplitudes(rho_j_fogo, w, FOGO_GROUPS)
    for e1_name in ["M", "B", "W", "V"]:
        A_e1 = e1_amps[e1_name]
        sc_opt = (X_mm * A_e1 * w).sum(1)
        tidx_opt = optimal_selector(sc_opt, trios)
        trio_opt = trios[tidx_opt]
        f_mm_opt = (F_mm_site[trio_opt[0]] +
                    F_mm_site[trio_opt[1]] +
                    F_mm_site[trio_opt[2]])
        q2 = 0 if check_dominated_raw(F_mm_trios, f_mm_opt) else 1
        q2_opt[e1_name].append(q2)

    if (draw_idx + 1) % 100 == 0:
        print(f"  {draw_idx + 1}/{N_DRAWS}", flush=True)

# ── Results ───────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("GATE — Fogo E1 regression (v2, correct rho_j from amplitudes.json)")
print("=" * 60)

# Reference from v3 log (e1_stats.json)
REF = {"M": 100.0, "B": 100.0, "W": 64.2, "V": 56.8}
TOL = 0.05   # half last decimal place of reference values

all_pass = True
for e1_name in ["M", "B", "W", "V"]:
    pct  = float(np.mean(q2_opt[e1_name])) * 100
    ref  = REF[e1_name]
    ok   = abs(pct - ref) <= TOL
    all_pass = all_pass and ok
    print(f"  E1-{e1_name}  opt: {pct:.1f}%  ref: {ref:.1f}%  "
          f"diff: {pct-ref:+.1f}pp  {'OK' if ok else 'FAIL'}")

print()
if all_pass:
    print("GATE PASS — Corrected E1 code reproduces Fogo v3 log values.")
    print("E1-W and E1-V are NOT trivially 100%: code is using mm-frontier correctly.")
else:
    print("GATE FAIL — E1 computation does not match Fogo oracle.")
    sys.exit(1)
