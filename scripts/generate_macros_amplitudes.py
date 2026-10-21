# -*- coding: utf-8 -*-
"""
generate_macros_amplitudes.py
==============================
Single source of truth for ALL amplitude-derived quantities.

Computes rho_j = 1/L2(mm_norm(x_j)) (rho_shift, the implementation formula)
for all 11 Fogo criteria, then derives TV_vec, TV_B, TV_W, m_eff, L2_vec,
perm_inflation, IntraGperm, RhoShiftMaxPct, and writes:

  1. results/amplitudes/amplitudes.json  -- canonical numbers + source SHA-256
  2. Terminal output of expected macro values

TV_W formula (§6.4, tvw_e4.py, run_e1.py): TV_W = sum_g W_g * TV_{W,g}
  TV_{W,g} = 0.5 * sum_{j in g} (w_j/W_g) * |rho_j/Abar_g - 1|
  where Abar_g = sum_{j in g} w_j*rho_j / W_g

This is the TV of cell W of E1 (Aj = rho_j/Abar_g) and is what
\TVWvec represents in the manuscript.

Run:
    uv run python scripts/generate_macros_amplitudes.py
"""

import hashlib
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from pathlib import Path

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix
)
from fogo_constants import OBJ_GROUPS, CRITERION_NAMES

REPO   = Path(__file__).parent.parent
OUT    = REPO / "results" / "amplitudes"
OUT.mkdir(parents=True, exist_ok=True)


def compute_amplitudes():
    # ── Load data ────────────────────────────────────────────────────────────
    df_all, _, _ = load_data()
    df_imp = impute_nan(df_all)
    df_via = df_imp[df_imp[COL['protected']] > 0].copy()

    # ── SHA-256 of source CSV ────────────────────────────────────────────────
    from mcdm_experiment import CACHE_CSV as _cache
    cache_csv = Path(_cache)
    sha256 = hashlib.sha256(cache_csv.read_bytes()).hexdigest() if cache_csv.exists() else "UNKNOWN"

    col_names = list(AHP_WEIGHTS.keys())
    W_raw = np.array(list(AHP_WEIGHTS.values()))
    W = W_raw / W_raw.sum()

    # ── rho_j (rho_shift = 1/L2(mm_norm(x_j))) ──────────────────────────────
    # Identical to run_e1.py lines 163-169: uses _build_decision_matrix output.
    X_via, benefit = _build_decision_matrix(df_via)
    rho = np.zeros(len(col_names))
    for j in range(len(col_names)):
        col = X_via[:, j].astype(float)
        rng_val = col.max() - col.min()   # = 1 for all non-constant mm-norm cols
        nrm = float(np.sqrt(np.sum(col**2)))
        rho[j] = rng_val / nrm if nrm > 0 else 0.0

    # ── TV_vec (total variation) ──────────────────────────────────────────────
    S = float(np.dot(W, rho))
    w_eff = W * rho / S
    delta = w_eff - W
    TV_vec = float(0.5 * np.abs(delta).sum())
    delta_L1 = float(np.abs(delta).sum())   # = 2*TV_vec
    delta_L2_sq = float(np.dot(delta, delta))
    m_eff  = float(delta_L1**2 / delta_L2_sq) if delta_L2_sq > 0 else 0.0
    L2_vec = float(np.sqrt(delta_L2_sq))
    # Verify: 2*TV/sqrt(m_eff) == L2_vec
    l2_check = 2.0 * TV_vec / np.sqrt(m_eff) if m_eff > 0 else 0.0
    assert abs(l2_check - L2_vec) < 1e-10, f"L2 formula mismatch: {l2_check:.8f} vs {L2_vec:.8f}"

    # ── TV_B (between-group TV) ───────────────────────────────────────────────
    group_avg_rho = np.zeros(len(col_names))
    for g in OBJ_GROUPS:
        wg  = W[g]
        gav = float(np.dot(wg, rho[g]) / wg.sum())
        for idx in g:
            group_avg_rho[idx] = gav

    S_B = float(np.dot(W, group_avg_rho))
    w_eff_B = W * group_avg_rho / S_B
    TV_B = float(0.5 * np.abs(w_eff_B - W).sum())

    # ── TV_W (within-group TV, §6.4 / tvw_e4.py) ─────────────────────────────
    # TV_W = sum_g W_g * [0.5 * sum_{j in g} (w_j/W_g) * |rho_j/Abar_g - 1|]
    TV_W = 0.0
    for g in OBJ_GROUPS:
        W_g   = float(W[g].sum())
        Abar_g = float(np.dot(W[g], rho[g]) / W_g)
        TV_Wg = 0.5 * sum((W[j] / W_g) * abs(rho[j] / Abar_g - 1.0) for j in g)
        TV_W += W_g * TV_Wg

    # ── Inflation factors ─────────────────────────────────────────────────────
    perm_idx  = col_names.index("perm")
    urban_idx = col_names.index("urban")
    aspect_idx = col_names.index("aspect")

    perm_inflation   = float(w_eff[perm_idx]  / W[perm_idx])
    urban_inflation  = float(w_eff[urban_idx] / W[urban_idx])
    aspect_inflation = float(w_eff[aspect_idx] / W[aspect_idx])

    # IntraGperm: perm amplitude relative to G1 group mean
    G1 = OBJ_GROUPS[0]
    Abar_G1 = float(np.dot(W[G1], rho[G1]) / W[G1].sum())
    IntraGperm = float(rho[perm_idx] / Abar_G1)

    # ── RhoShiftMaxPct/Crit ───────────────────────────────────────────────────
    # For criteria with min > 0, rho_shift differs from rho_raw.
    # RhoShiftMaxPct = max % difference; RhoShiftMaxCrit = which criterion.
    from fogo_constants import AJ_VEC as AJ_RAW
    rho_raw_tab2 = np.array(AJ_RAW)
    diffs = (rho - rho_raw_tab2) / rho_raw_tab2 * 100  # % difference
    max_pct_idx = int(np.argmax(np.abs(diffs)))
    max_pct = float(abs(diffs[max_pct_idx]))
    max_crit = col_names[max_pct_idx]

    # ── Collect ───────────────────────────────────────────────────────────────
    result = {
        "source_sha256": sha256,
        "rho_j": {k: round(float(rho[j]), 6) for j, k in enumerate(col_names)},
        "TV_vec": round(TV_vec, 6),
        "TV_B":   round(TV_B,   6),
        "TV_W":   round(TV_W,   6),
        "m_eff":  round(m_eff,  4),
        "L2_vec": round(L2_vec, 6),
        "S":      round(S,      6),
        "perm_inflation":   round(perm_inflation,   4),
        "urban_inflation":  round(urban_inflation,  4),
        "aspect_inflation": round(aspect_inflation, 4),
        "IntraGperm":  round(IntraGperm,  4),
        "RhoShiftMaxPct":  round(max_pct, 2),
        "RhoShiftMaxCrit": max_crit,
    }

    return result


def main():
    res = compute_amplitudes()
    col_names = list(AHP_WEIGHTS.keys())

    # ── Save JSON ─────────────────────────────────────────────────────────────
    out_json = OUT / "amplitudes.json"
    json.dump(res, out_json.open("w"), indent=2)
    print(f"Written: {out_json}")
    print(f"Source SHA-256: {res['source_sha256'][:16]}")

    # ── Print macro values ────────────────────────────────────────────────────
    print()
    print("=== Amplitude macros (corrected rho_shift) ===")
    print(f"  TVvec           = {res['TV_vec']:.4f}   (was 0.3146)")
    print(f"  TVBvec          = {res['TV_B']:.4f}   (was 0.2489)")
    print(f"  TVWvec          = {res['TV_W']:.4f}   (was 0.1986)")
    print(f"  m_eff           = {res['m_eff']:.4f}   (was 4.0486)")
    print(f"  L2_vec          = {res['L2_vec']:.4f}   (was 0.3127)")
    print(f"  perm inflation  = {res['perm_inflation']:.4f}x  (was 2.88)")
    print(f"  urban inflation = {res['urban_inflation']:.4f}x  (was 0.53)")
    print(f"  aspect inflate  = {res['aspect_inflation']:.4f}x  (was 0.51)")
    print(f"  IntraGperm      = {res['IntraGperm']:.4f}   (was 1.56)")
    print(f"  RhoShiftMaxPct  = {res['RhoShiftMaxPct']:.2f}%  ({res['RhoShiftMaxCrit']})")
    print()
    print("=== Tab2 rho_j changes ===")
    from fogo_constants import AJ_VEC as AJ_RAW
    for j, k in enumerate(col_names):
        old = round(AJ_RAW[j], 3)
        new = round(res['rho_j'][k], 3)
        status = "UPDATE" if old != new else "OK"
        print(f"  {k:12s}: {old:.3f} -> {new:.3f}  {status}")

    # ── Regression check (expected slopeOpt) ─────────────────────────────────
    # OLS on (TV_mm=0, TV_rnk=0.091, TV_vec=TV_vec) vs Q2_opt=(100, 88.2, 56.8)
    tvs  = np.array([0.0, 0.091, res['TV_vec']])
    q2s  = np.array([100.0, 88.2, 56.8])
    X_ols = np.column_stack([np.ones(3), tvs])
    coef = np.linalg.lstsq(X_ols, q2s, rcond=None)[0]
    print(f"\nExpected \\slopeOpt = {coef[1]:.1f}  (was -137.7)")
    Sxx = float(np.sum((tvs - tvs.mean())**2))
    print(f"Expected \\SxxPctVecOpt = {Sxx / np.sum((tvs - tvs.min())**2) * 100:.0f}%  [Sxx={Sxx:.5f}]")


if __name__ == "__main__":
    main()
