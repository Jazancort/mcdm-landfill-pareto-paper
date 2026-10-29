# -*- coding: utf-8 -*-
"""gate_e1_fogo_v3.py — Fogo E1 gate with fixed w0 for Ā_g (E1-W amplitude).

Hypothesis: v3 log used FIXED AHP weights (w0) for Ā_g in E1-W amplitudes,
not per-draw weights. This gives a constant rescale factor = 0.2024 (published),
while per-draw weights give 0.2034 (compute_stage3b note).

If this passes, get_e1_amplitudes must be fixed to use w0 for Ā_g.

Reference values (e1_v3_rerun_20261002.log, SHA e05cd8a4...):
  E1-M: 100.0%  E1-B: 100.0%  E1-W: 64.2%  E1-V: 56.8%
"""
import json
import sys
import os
import numpy as np
from pathlib import Path

ROOT    = Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

if "MCDM_DATA_DIR" not in os.environ:
    os.environ["MCDM_DATA_DIR"] = "/home/julioazancort/scratch/mcdm"

# ── Fogo rho_j and w0 ─────────────────────────────────────────────────────────
AMP_JSON = ROOT / "results" / "amplitudes" / "amplitudes.json"
amp = json.loads(AMP_JSON.read_text())

FOGO_CRIT = [
    "perm", "slope", "roads", "rivers", "aspect", "coast",
    "protected", "wells", "urban", "aero", "cult",
]
rho_j_fogo = np.array([amp["rho_j"][c] for c in FOGO_CRIT], dtype=float)
FOGO_GROUPS = [[0, 1, 2], [3, 4, 5, 6, 7], [8, 9, 10]]

# Fixed AHP weights (Tab 2, 11 criteria)
FOGO_W0 = np.array([
    0.152, 0.113, 0.030, 0.091, 0.075, 0.069,
    0.066, 0.055, 0.166, 0.102, 0.081,
], dtype=float)
FOGO_W0 = FOGO_W0 / FOGO_W0.sum()

def get_e1_amplitudes_fixed_w0(rho_j, w0_fixed, groups):
    """E1 amplitudes using FIXED w0 for Ā_g (not per-draw weights).

    The rescale factor for E1-W is constant across draws (= 0.2024 published).
    This matches the v3 log convention.
    """
    M = len(rho_j)
    Abar_g = np.zeros(M)
    for g in groups:
        g_arr = np.array(g, dtype=int)
        W_g   = w0_fixed[g_arr].sum()
        avg   = float(np.dot(w0_fixed[g_arr], rho_j[g_arr]) / W_g) if W_g > 0 else 0.0
        Abar_g[g_arr] = avg

    return {
        "M": np.ones(M),
        "B": Abar_g.copy(),
        "W": np.where(Abar_g > 1e-15, rho_j / Abar_g, 0.0),
        "V": rho_j.copy(),
    }

# Verify rescale factor
e1_amps_w0 = get_e1_amplitudes_fixed_w0(rho_j_fogo, FOGO_W0, FOGO_GROUPS)
scale_EW = float(np.dot(FOGO_W0, e1_amps_w0["W"]))  # weighted mean of E1-W
scale_EV = float(np.dot(FOGO_W0, e1_amps_w0["V"]))  # weighted mean of E1-V
scale_ratio = scale_EW / scale_EV if scale_EV > 0 else 0.0
print(f"E1-W rescale check: weighted mean E1-W = {scale_EW:.4f}, E1-V = {scale_EV:.4f}")
print(f"  Ratio (should be 1.0 if properly scaled): {scale_ratio:.4f}")
print(f"  Published rescale factor: 0.2024")

# ── Load Fogo X_mm ─────────────────────────────────────────────────────────────
from mcdm_experiment import (
    load_data, impute_nan, COL, _build_decision_matrix,
)

df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]] > 0].copy().reset_index(drop=True)
X_raw, benefit = _build_decision_matrix(df_via)
X_adj = X_raw.copy()
for j, b in enumerate(benefit):
    if not b:
        X_adj[:, j] = 1.0 - X_raw[:, j]
lo = X_adj.min(0); hi = X_adj.max(0)
denom = np.where(hi - lo > 1e-9, hi - lo, 1.0)
X_mm = (X_adj - lo) / denom

print(f"\nFogo X_mm: shape={X_mm.shape}  N_adm={len(X_mm)}")

# ── Load trios and E1 weights ──────────────────────────────────────────────────
import hashlib
trios_path = ROOT / "data" / "fogo_trios.npy"
trios = np.load(trios_path).astype(np.int32)
wmat_path = ROOT / "results" / "e1" / "e1_weights_k200.npy"
SHA_W = "bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487"
assert hashlib.sha256(wmat_path.read_bytes()).hexdigest() == SHA_W
W = np.load(wmat_path)
print(f"n_trios={len(trios):,}  weights shape={W.shape}  SHA OK\n")

# ── Import core functions ──────────────────────────────────────────────────────
from run_santiago_mc import (
    optimal_selector, compute_group_objectives, compute_trio_objectives, check_dominated_raw,
)

# ── Run 500 draws ──────────────────────────────────────────────────────────────
N_DRAWS = 500
A_ones = np.ones(len(rho_j_fogo))
q2_opt = {"M": [], "B": [], "W": [], "V": []}

print(f"Running {N_DRAWS} draws (CPU, fixed w0 for Ā_g)...", flush=True)
for draw_idx in range(N_DRAWS):
    w = W[draw_idx]
    F_mm_site  = compute_group_objectives(X_mm, w, A_ones, FOGO_GROUPS)
    F_mm_trios = compute_trio_objectives(F_mm_site, trios)

    # E1 with fixed w0 for Ā_g
    e1_amps = get_e1_amplitudes_fixed_w0(rho_j_fogo, FOGO_W0, FOGO_GROUPS)
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

# ── Results ────────────────────────────────────────────────────────────────────
REF = {"M": 100.0, "B": 100.0, "W": 64.2, "V": 56.8}
TOL = 0.05

print()
print("=" * 60)
print("GATE v3 — fixed w0 for Ā_g")
print("=" * 60)
all_pass = True
for e1_name in ["M", "B", "W", "V"]:
    pct = float(np.mean(q2_opt[e1_name])) * 100
    ref = REF[e1_name]
    ok  = abs(pct - ref) <= TOL
    all_pass = all_pass and ok
    print(f"  E1-{e1_name}  {pct:.1f}%  ref {ref:.1f}%  diff {pct-ref:+.1f}pp  {'OK' if ok else 'FAIL'}")

print()
if all_pass:
    print("GATE PASS (fixed w0). Conclusion: get_e1_amplitudes must use w0 for Ā_g.")
else:
    print("GATE FAIL. Try per-draw weights or inspect X_mm loading.")
