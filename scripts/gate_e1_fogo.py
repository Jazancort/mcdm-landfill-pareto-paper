# -*- coding: utf-8 -*-
"""gate_e1_fogo.py — Gate 1 of DEV-SANT-E1-001.

Applies the CORRECTED E1 logic (mm-frontier) from run_santiago_mc.py
to Fogo data. Must reproduce the reference values from e1_macros.tex.

Expected (half-last-decimal-place tolerance = 0.05 pp):
  E1-M opt: 100.0%
  E1-B opt: 100.0%
  E1-W opt:  64.2%
  E1-V opt:  56.8%

E1-V opt must equal SAW/vec/opt exactly at the draw level (same draws, same A_j = rho_j).

Run:
  CUDA_VISIBLE_DEVICES=0 uv run python scripts/gate_e1_fogo.py
"""
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

# ── Load Fogo data (same as run_e1.py) ──────────────────────────────────────
from mcdm_experiment import (
    load_data, impute_nan, haversine_km, greedy_trio,
    COL, AHP_WEIGHTS, MIN_DIST_KM,
    _build_decision_matrix, _norm, INV, COST,
    F1_CRIT, F2_CRIT, F3_CRIT,
)

print("Loading Fogo data...", flush=True)
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]] > 0].copy().reset_index(drop=True)
N = len(df_via)
assert N == 389, f"Expected 389 admissible sites, got {N}"

X_raw, benefit = _build_decision_matrix(df_via)
X_adj = X_raw.copy()
for j, b in enumerate(benefit):
    if not b:
        X_adj[:, j] = 1.0 - X_raw[:, j]

# min-max normalise (admissible only, same as WP3)
lo = X_adj.min(0); hi = X_adj.max(0)
denom = np.where(hi - lo > 1e-12, hi - lo, 1.0)
X_mm = (X_adj - lo) / denom     # (389, 11)

# rho_j (vector normalisation amplitudes) — from run_e1.py logic
rho_j = np.std(X_mm, axis=0, ddof=1)    # (11,) amplitudes
rho_j = np.maximum(rho_j, 1e-12)

# Distance matrix — not needed for optimal check only (gate focuses on Q2_opt)
# Included for completeness but not used in the gate criterion
D = None  # greedy skipped in this gate

# Load trios
trios_path = ROOT / "data" / "fogo_trios.npy"
assert trios_path.exists(), f"Missing: {trios_path}"
trios = np.load(trios_path).astype(np.int32)    # (n_trios, 3)
print(f"  Sites: {N}  Trios: {len(trios)}", flush=True)

# ── Load E1 weights ──────────────────────────────────────────────────────────
wmat_path = ROOT / "results" / "e1" / "e1_weights_k200.npy"
SHA_EXPECTED = "bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487"
sha = hashlib.sha256(wmat_path.read_bytes()).hexdigest()
assert sha == SHA_EXPECTED, f"SHA mismatch for e1_weights_k200.npy: {sha[:16]}"
W = np.load(wmat_path)    # (500, 11)
print(f"  Weights: {W.shape}  SHA OK", flush=True)

# ── Import corrected E1 functions from run_santiago_mc.py ───────────────────
from run_santiago_mc import (
    get_e1_amplitudes, optimal_selector, greedy_selector,
    check_dominated_raw, compute_group_objectives, compute_trio_objectives,
)

# Fogo groups match Santiago S-T groups (perm/slope/roads / rivers/aspect/coast/prot/wells / urban/aero/cult)
GROUPS_FOGO = [
    [0, 1, 2],          # G1: perm, slope, roads
    [3, 4, 5, 6, 7],    # G2: rivers, aspect, coast, prot, wells
    [8, 9, 10],         # G3: urban, aero, cult
]
E1_CELLS = ["M", "B", "W", "V"]

# ── Run corrected E1 gate ────────────────────────────────────────────────────
N_DRAWS = W.shape[0]
q2_opt_per_cell = {c: [] for c in E1_CELLS}
q2_grd_per_cell = {c: [] for c in E1_CELLS}
q2_vec_opt_ref  = []    # SAW/vec/opt from the main analysis (same draws)

print(f"Running {N_DRAWS} draws...", flush=True)
for draw_idx in range(N_DRAWS):
    w = W[draw_idx]

    A_ones = np.ones(len(w))

    # mm group objectives and frontier (used for Q2 checks)
    F_mm_site  = compute_group_objectives(X_mm, w, A_ones, GROUPS_FOGO)
    F_mm_trios = compute_trio_objectives(F_mm_site, trios)

    # SAW/vec/opt reference (for E1-V equivalence check)
    sc_vec = (X_mm * rho_j * w).sum(1)
    tidx_vec_opt = optimal_selector(sc_vec, trios)
    trio_vec_opt = trios[tidx_vec_opt]
    f_mm_vec_opt = (F_mm_site[trio_vec_opt[0]] +
                    F_mm_site[trio_vec_opt[1]] +
                    F_mm_site[trio_vec_opt[2]])
    q2_vec = 0 if check_dominated_raw(F_mm_trios, f_mm_vec_opt) else 1
    q2_vec_opt_ref.append(q2_vec)

    # E1 cells with corrected mm-frontier logic (optimal only — gate criterion)
    e1_amps = get_e1_amplitudes(rho_j, w, GROUPS_FOGO)
    for e1_name in E1_CELLS:
        A_e1 = e1_amps[e1_name]
        sc_opt = (X_mm * A_e1 * w).sum(1)

        tidx_opt = optimal_selector(sc_opt, trios)
        trio_opt = trios[tidx_opt]
        f_mm_opt = (F_mm_site[trio_opt[0]] +
                    F_mm_site[trio_opt[1]] +
                    F_mm_site[trio_opt[2]])
        q2_opt = 0 if check_dominated_raw(F_mm_trios, f_mm_opt) else 1
        q2_opt_per_cell[e1_name].append(q2_opt)

    if (draw_idx + 1) % 100 == 0:
        print(f"  {draw_idx + 1}/{N_DRAWS}", flush=True)

# ── Results ──────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("GATE 1 — Fogo E1 regression (corrected mm-frontier code)")
print("=" * 60)

# Reference values from e1_macros.tex
REF = {
    "M": {"opt": 100.0, "grd": 86.0},
    "B": {"opt": 100.0, "grd": 100.0},
    "W": {"opt": 64.2,  "grd": 64.0},
    "V": {"opt": 56.8,  "grd": 66.2},
}
TOL = 0.05   # half last decimal place of reference values

all_pass = True
for e1_name in E1_CELLS:
    opt_pct = float(np.mean(q2_opt_per_cell[e1_name])) * 100
    ref_opt = REF[e1_name]["opt"]
    pass_opt = abs(opt_pct - ref_opt) <= TOL
    all_pass = all_pass and pass_opt
    print(f"  E1-{e1_name}  opt: {opt_pct:.1f}% (ref {ref_opt:.1f}%)  {'OK' if pass_opt else 'FAIL'}")

# E1-V opt must equal SAW/vec/opt draw-for-draw
vec_opt_pct = float(np.mean(q2_vec_opt_ref)) * 100
e1v_opt_pct = float(np.mean(q2_opt_per_cell["V"])) * 100
v_eq = vec_opt_pct == e1v_opt_pct   # should be exactly equal since same A_j = rho_j
print(f"\n  E1-V opt = SAW/vec/opt drawwise: "
      f"SAW/vec/opt={vec_opt_pct:.1f}%  E1-V={e1v_opt_pct:.1f}%  "
      f"{'OK (exact)' if v_eq else 'CHECK (may differ by rounding)'}")

# Check draw-level equality (exact, not just aggregate)
v_drawwise_eq = all(
    q2_opt_per_cell["V"][i] == q2_vec_opt_ref[i] for i in range(N_DRAWS)
)
print(f"  E1-V opt == SAW/vec/opt per draw: {'ALL MATCH' if v_drawwise_eq else 'MISMATCH'}")
if not v_drawwise_eq:
    n_diff = sum(q2_opt_per_cell["V"][i] != q2_vec_opt_ref[i] for i in range(N_DRAWS))
    print(f"    {n_diff}/{N_DRAWS} draws differ")
    all_pass = False

print()
if all_pass:
    print("GATE 1: PASS — Corrected code reproduces Fogo E1 reference values.")
    print("Safe to proceed to Gate 2 (Santiago internal consistency).")
else:
    print("GATE 1: FAIL — Do NOT run Santiago until this is resolved.")
    sys.exit(1)
