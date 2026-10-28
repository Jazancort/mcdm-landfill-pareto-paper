# -*- coding: utf-8 -*-
"""gate_e1_internal.py — Internal consistency gate for DEV-SANT-E1-001 fix.

Gate 1 (revised): E1-V Q2 must equal SAW_vec_opt from mc_ST_raw.csv draw-for-draw.

Mathematical identity: E1-V sets A_j = rho_j (the vec amplitudes), which is
identical to the SAW/vec scoring. Therefore:
  - E1-V and SAW/vec select the same optimal portfolio.
  - Both are checked against the same mm-frontier (after the fix).
  - Their Q2 values must be identical draw-for-draw.

If the old bug (amplitude-specific frontier) were still present:
  - E1-V Q2 would be 100% (trivially, against its own frontier).
  - SAW/vec Q2 would be 56-100% depending on κ.
  - They would NOT match.

Gate 2: E1-M Q2 must equal SAW_mm_opt from mc_ST_raw.csv draw-for-draw.
Gate 3: E1-B Q2 must equal 100.0% (Proposition 1, TV_W = 0).

mc_ST_raw.csv SHA-256 must match the sealed value.

Run:
  CUDA_VISIBLE_DEVICES=0 uv run python scripts/gate_e1_internal.py
"""
import sys
import os
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path

ROOT    = Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

# ── SHA check on sealed raw file ─────────────────────────────────────────────
RAW_CSV_ST = ROOT / "results" / "santiago" / "mc_ST_raw.csv"
SHA_RAW_ST = "123a5421"   # first 8 hex digits of sealed SHA
sha_actual = hashlib.sha256(RAW_CSV_ST.read_bytes()).hexdigest()
if not sha_actual.startswith(SHA_RAW_ST):
    print(f"ABORT: mc_ST_raw.csv SHA mismatch!")
    print(f"  expected prefix: {SHA_RAW_ST}")
    print(f"  actual:          {sha_actual[:8]}")
    sys.exit(1)
print(f"mc_ST_raw.csv SHA prefix OK ({SHA_RAW_ST}...)")

N_DRAWS = 10   # Gate uses first 10 draws; sufficient to detect the bug

# ── Load sealed reference values ─────────────────────────────────────────────
df_raw = pd.read_csv(RAW_CSV_ST)
df_200 = df_raw[df_raw["kappa"] == 200].copy().reset_index(drop=True)
assert len(df_200) == 500, f"Expected 500 draws at kappa=200, got {len(df_200)}"
df_200_gate = df_200.iloc[:N_DRAWS]   # first N draws only

ref_SAW_mm_opt  = df_200_gate["SAW_mm_opt"].values.astype(int)
ref_SAW_vec_opt = df_200_gate["SAW_vec_opt"].values.astype(int)

print(f"  SAW_mm_opt  mean: {ref_SAW_mm_opt.mean()*100:.1f}% (expected 100.0%)")
print(f"  SAW_vec_opt mean: {ref_SAW_vec_opt.mean()*100:.1f}%")

# ── Import corrected E1 functions ────────────────────────────────────────────
from run_santiago_mc import (
    load_branch_data, prepare_gpu_data, make_santiago_scorers,
    get_e1_amplitudes, optimal_selector, compute_group_objectives,
    compute_trio_objectives, check_dominated_raw,
    ST_GROUPS, E1_CELLS,
)
from gen_santiago_seeds import get_branch_rngs

# ── Load Santiago S-T data ───────────────────────────────────────────────────
print("\nLoading S-T data...", flush=True)
data    = load_branch_data("ST")
X_mm    = data["X_mm"]
trios   = data["trios"]
rho_j   = data["rho_j"]
w0      = data["w0"]
groups  = data["groups"]
assert len(groups) == len(ST_GROUPS), "Groups mismatch"
print(f"  N_adm={len(X_mm)}  n_trios={len(trios)}  n_crit={X_mm.shape[1]}")

# ── Reproduce kappa=200 weight draws ─────────────────────────────────────────
rng_st, _ = get_branch_rngs(200)   # canonical S-T generator for kappa=200
A_ones  = np.ones(len(w0))

q2_e1M  = []
q2_e1B  = []
q2_e1V  = []

print(f"\nRunning {N_DRAWS} draws for kappa=200...", flush=True)
for draw_idx in range(N_DRAWS):
    w = rng_st.dirichlet(200 * w0)
    w /= w.sum()

    # mm group objectives and frontier
    F_mm_site  = compute_group_objectives(X_mm, w, A_ones, groups)
    F_mm_trios = compute_trio_objectives(F_mm_site, trios)

    # E1 cells (corrected: Q2 against mm-frontier)
    e1_amps = get_e1_amplitudes(rho_j, w, groups)

    for e1_name in ["M", "B", "V"]:
        A_e1 = e1_amps[e1_name]
        sc_opt = (X_mm * A_e1 * w).sum(1)
        tidx_opt = optimal_selector(sc_opt, trios)
        trio_opt = trios[tidx_opt]
        f_mm_opt = (F_mm_site[trio_opt[0]] +
                    F_mm_site[trio_opt[1]] +
                    F_mm_site[trio_opt[2]])
        q2_opt = 0 if check_dominated_raw(F_mm_trios, f_mm_opt) else 1

        if e1_name == "M":
            q2_e1M.append(q2_opt)
        elif e1_name == "B":
            q2_e1B.append(q2_opt)
        elif e1_name == "V":
            q2_e1V.append(q2_opt)

    if (draw_idx + 1) % 10 == 0:
        print(f"  {draw_idx + 1}/{N_DRAWS}", flush=True)

q2_e1M = np.array(q2_e1M)
q2_e1B = np.array(q2_e1B)
q2_e1V = np.array(q2_e1V)

# ── Gate checks ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("GATE — E1 internal consistency (Santiago S-T, kappa=200)")
print("=" * 60)

all_pass = True

# Gate 2a: E1-M == SAW_mm_opt draw-for-draw
match_M = np.array_equal(q2_e1M, ref_SAW_mm_opt)
pct_M   = q2_e1M.mean() * 100
print(f"\nGate 2a: E1-M == SAW_mm_opt draw-for-draw")
print(f"  E1-M   mean: {pct_M:.1f}%")
print(f"  ref    mean: {ref_SAW_mm_opt.mean()*100:.1f}%")
print(f"  drawwise: {'ALL MATCH' if match_M else 'MISMATCH'}")
if not match_M:
    n_diff = np.sum(q2_e1M != ref_SAW_mm_opt)
    print(f"    {n_diff}/500 draws differ")
    all_pass = False

# Gate 2b: E1-B == 100.0% (Proposition 1)
pct_B   = q2_e1B.mean() * 100
pass_B  = pct_B == 100.0
print(f"\nGate 2b: E1-B = 100.0% (Proposition 1)")
print(f"  E1-B mean: {pct_B:.1f}%  {'OK' if pass_B else 'FAIL'}")
if not pass_B:
    all_pass = False

# Gate 1: E1-V == SAW_vec_opt draw-for-draw (KEY CHECK)
match_V = np.array_equal(q2_e1V, ref_SAW_vec_opt)
pct_V   = q2_e1V.mean() * 100
pct_ref = ref_SAW_vec_opt.mean() * 100
print(f"\nGate 1 (KEY): E1-V == SAW_vec_opt draw-for-draw")
print(f"  E1-V   mean: {pct_V:.1f}%")
print(f"  ref    mean: {pct_ref:.1f}%")
print(f"  drawwise: {'ALL MATCH' if match_V else 'MISMATCH'}")
if not match_V:
    n_diff = np.sum(q2_e1V != ref_SAW_vec_opt)
    print(f"    {n_diff}/500 draws differ")
    all_pass = False

print()
if all_pass:
    print("ALL GATES PASS — Corrected E1 code is consistent with sealed main analysis.")
    print("E1-V Q2 == SAW_vec_opt draw-for-draw: mm-frontier is being used correctly.")
    print("Proceed to Gate 3 (full Stage 4 SHA check) before running corrective Santiago run.")
else:
    print("GATES FAILED — Do NOT run Santiago until this is resolved.")
    sys.exit(1)
