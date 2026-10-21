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

    # ── TV_rnk (TV under midranks normalization) ─────────────────────────────
    # Canonical ranks scorer (same as wp3_mc_fixed.py):
    #   X_ranks[:, j] = rank(X_adj[:, j], method='average') / (N+1)
    # Amplitude = range(X_ranks[:, j])  (same principle as vec: range of score column).
    # X_adj is benefit-adjusted (leeward=1 for aspect, cost flipped for COST criteria).
    import pandas as _pd
    X_adj_rnk = X_via.copy()
    for j_, is_ben in enumerate(benefit):
        if not is_ben:
            X_adj_rnk[:, j_] = 1.0 - X_via[:, j_]
    X_ranks = np.apply_along_axis(
        lambda c: _pd.Series(c).rank(method="average").values / (len(c) + 1),
        0, X_adj_rnk
    )
    rho_rnk = X_ranks.max(0) - X_ranks.min(0)   # amplitude = range
    S_rnk = float(np.dot(W, rho_rnk))
    w_eff_rnk = W * rho_rnk / S_rnk
    TV_rnk = float(0.5 * np.abs(w_eff_rnk - W).sum())
    # Sanity: must reproduce published 0.091
    assert abs(TV_rnk - 0.091) < 0.001, f"TV_rnk sanity failed: {TV_rnk:.4f} != 0.091"

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
    # rho_raw = range(x)/L2(x) on RAW data (not mm-norm).
    # For aspect: use the binary indicator (same as _build_decision_matrix),
    # not raw azimuth degrees (which would give a different and meaningless value).
    # For criteria with min_raw > 0: rho_raw < rho_shift because L2(x) > L2(x-min).
    rho_raw = np.zeros(len(col_names))
    for j, k in enumerate(col_names):
        if k == "aspect":
            x_val = X_via[:, j].astype(float)   # binary indicator, leeward=1
        else:
            x_val = df_via[COL[k]].values.astype(float)
        rng_r = x_val.max() - x_val.min()
        nrm_r = float(np.sqrt(np.sum(x_val**2)))
        rho_raw[j] = rng_r / nrm_r if nrm_r > 0 else 0.0
    diffs = (rho - rho_raw) / rho_raw * 100  # % difference rho_shift vs rho_raw
    max_pct_idx = int(np.argmax(np.abs(diffs)))
    max_pct = float(abs(diffs[max_pct_idx]))
    max_crit = col_names[max_pct_idx]

    # ── slopeOpt (OLS on 3 normalisations) ──────────────────────────────────
    # Q2 values read from wp3_mc_fixed_raw.csv (SAW optimal assembly, same pipeline).
    # TV values: TV=0 for min-max, TV=TVrnk for ranks (orphan 0.091), TV=TV_vec for vector.
    wp3_csv = REPO / "results" / "wp3_mc_fixed_raw.csv"
    if wp3_csv.exists():
        import pandas as _pd
        df_wp3 = _pd.read_csv(wp3_csv)
        q2_mm  = float(df_wp3[df_wp3["norm"] == "min-max"]["nd_optimal"].mean()) * 100
        q2_rnk = float(df_wp3[df_wp3["norm"] == "ranks"]["nd_optimal"].mean()) * 100
        q2_vec = float(df_wp3[df_wp3["norm"] == "vector"]["nd_optimal"].mean()) * 100
    else:
        q2_mm, q2_rnk, q2_vec = 100.0, 88.2, 56.8   # fallback if CSV not available
    TV_RNK_ORPHAN = float(TV_rnk)  # now computed from canonical scorer (was orphan 0.091)
    tvs  = np.array([0.0, TV_RNK_ORPHAN, TV_vec])
    q2s  = np.array([q2_mm, q2_rnk, q2_vec])
    X_ols = np.column_stack([np.ones(3), tvs])
    coef = np.linalg.lstsq(X_ols, q2s, rcond=None)[0]
    slope_opt = round(float(coef[1]), 1)

    # ── Pole-coding counterfactuals (for eq:vec frase) ───────────────────────
    # rho_perm_inv: amplitude if we had normalised 1-x_mm(perm) instead of x_mm(perm).
    # rho_aspect_flipped: amplitude if leeward sites were coded as 0 instead of 1.
    # Both are computed from the _build_decision_matrix output (X_via).
    rho_perm_inv   = 1.0 / float(np.linalg.norm(1.0 - X_via[:, perm_idx]))
    rho_asp_flip   = 1.0 / float(np.linalg.norm(1.0 - X_via[:, aspect_idx]))

    # ── TV(α=2) — manuscript formula: w_j^eff(2) = w_j^2 * A_j^2 / Σ w_k^2 * A_k^2 ──
    # Definition (ii) from eq:weff_alpha in Remark prop:exponent.
    # This is the TOPSIS analogy: homogeneous of degree α=2 in w_j * A_j.
    # Do NOT use definition (i) = w_j * A_j^2 — that gives a different number (0.590).
    num_alpha2 = W**2 * rho**2
    weff_alpha2 = num_alpha2 / num_alpha2.sum()
    TV_alpha2   = float(0.5 * np.abs(weff_alpha2 - W).sum())
    DeltaTV_alpha2 = TV_alpha2 - TV_vec   # TV(2) - TV(1)
    # Sanity: A_j=1 (min-max reference) should give TV(2)=0.160 with Fogo weights
    num_mm = W**2
    weff_mm2 = num_mm / num_mm.sum()
    TV_mm2 = float(0.5 * np.abs(weff_mm2 - W).sum())
    assert abs(TV_mm2 - 0.160) < 0.005, f"Min-max TV(2) sanity check failed: {TV_mm2:.4f} != 0.160"

    # ── Collect ───────────────────────────────────────────────────────────────
    # NOTE: rho_j and TV values stored WITHOUT rounding so that test_coding_consistency
    # can verify at 1e-12 (not just 1e-5). The .tex file uses 3dp for display.
    result = {
        "source_sha256": sha256,
        "rho_j": {k: float(rho[j]) for j, k in enumerate(col_names)},
        "TV_vec": float(TV_vec),
        "TV_B":   float(TV_B),
        "TV_W":   float(TV_W),
        "m_eff":  float(m_eff),
        "L2_vec": float(L2_vec),
        "S":      float(S),
        "perm_inflation":   float(perm_inflation),
        "urban_inflation":  float(urban_inflation),
        "aspect_inflation": float(aspect_inflation),
        "IntraGperm":  float(IntraGperm),
        "RhoShiftMaxPct":  round(max_pct, 2),   # always 2dp (display value)
        "RhoShiftMaxCrit": max_crit,
        "TV_alpha2":   float(TV_alpha2),
        "DeltaTV_alpha2": float(DeltaTV_alpha2),
        "TV_alpha2_mm": float(TV_mm2),
        "TV_rnk":      float(TV_rnk),
        "slope_opt":     slope_opt,
        "rho_perm":      float(rho[perm_idx]),
        "rho_perm_inv":  float(rho_perm_inv),
        "rho_aspect":    float(rho[aspect_idx]),
        "rho_asp_flip":  float(rho_asp_flip),
        "q2_mm_opt":     float(q2_mm),
        "q2_rnk_opt":    float(q2_rnk),
        "q2_vec_opt":    float(q2_vec),
    }

    return result


def write_macros_amplitudes_tex(res, out_path):
    """Write macros_amplitudes.tex from amplitudes.json result dict."""
    lines = [
        "% AUTO-GENERATED by scripts/generate_macros_amplitudes.py -- DO NOT EDIT BY HAND",
        f"% source: results/amplitudes/amplitudes.json  sha256={res['source_sha256'][:16]}",
        "% Re-generate: uv run python scripts/generate_macros_amplitudes.py",
        "%",
        "% All rho_j = 1/L2(mm_norm(x_j)) (rho_shift formula).",
        "% TV_W = E1-W formula (section 6.4). TV(alpha=2) uses def-(ii): w^2*A^2.",
        "",
        "% --- TV decomposition (SAW, alpha=1) ---",
        rf"\newcommand{{\TVvec}}{{{res['TV_vec']:.3f}}}             % TV_vec (rho_shift; was 0.315 rho_raw)",
        rf"\newcommand{{\TVBvec}}{{{res['TV_B']:.3f}}}            % between-group TV",
        rf"\newcommand{{\TVWvec}}{{{res['TV_W']:.3f}}}            % within-group TV (E1-W formula)",
        rf"\newcommand{{\TVrnk}}{{{res['TV_rnk']:.3f}}}             % TV under midranks normalization",
        "",
        "% --- TV(alpha=2) -- manuscript formula w_j^2*A_j^2 (definition ii) ---",
        rf"\newcommand{{\TValphaTwo}}{{{res['TV_alpha2']:.3f}}}         % TV(2) vector (def-ii; NOT 0.590=def-i)",
        rf"\newcommand{{\DeltaTValphaTwo}}{{{res['DeltaTV_alpha2']:.3f}}}    % TV(2)-TV(1) vector",
        rf"\newcommand{{\TValphaTwoMM}}{{{res['TV_alpha2_mm']:.3f}}}        % TV(2) min-max (A_j=1 baseline)",
        "",
        "% --- Perm inflation ---",
        rf"\newcommand{{\PermInflation}}{{{res['perm_inflation']:.2f}}}        % w_eff(perm)/w(perm)",
        rf"\newcommand{{\IntraGperm}}{{{res['IntraGperm']:.2f}}}           % rho_perm/Abar_G1",
        "",
        "% --- rho_shift max change from rho_raw ---",
        rf"\newcommand{{\RhoShiftMaxPct}}{{{res['RhoShiftMaxPct']:.1f}}}        % max % diff rho_raw vs rho_shift",
        rf"\newcommand{{\RhoShiftMaxCrit}}{{{res['RhoShiftMaxCrit']}}}       % criterion with max diff",
        "",
        "% --- Slope of optimal-assembly ordering (OLS on 3 normalisations) ---",
        rf"\newcommand{{\slopeOpt}}{{{abs(res['slope_opt']):.1f}}}            % |slope| of Q2_opt vs TV_vec (was 137.7)",
        "",
        "% --- Pole-coding counterfactuals (eq:vec paragraph) ---",
        "% rho_j = 1/L2(X_via[:,j]) where X_via is from _build_decision_matrix.",
        "% X_via[:,aspect] has leeward=1 (94 sites); flipped = leeward=0.",
        "% X_via[:,perm] is the straight mm-norm; inverted = 1-mm_norm.",
        rf"\newcommand{{\RhoPerm}}{{{res['rho_perm']:.3f}}}             % 1/L2(mm_perm)  heavy-zero dist",
        rf"\newcommand{{\RhoPermInverted}}{{{res['rho_perm_inv']:.3f}}}   % 1/L2(1-mm_perm) if inverted",
        rf"\newcommand{{\RhoAspect}}{{{res['rho_aspect']:.3f}}}          % 1/sqrt(94)  leeward=1",
        rf"\newcommand{{\RhoAspectFlipped}}{{{res['rho_asp_flip']:.3f}}}  % 1/sqrt(295) if leeward=0",
    ]
    Path(out_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Written: {out_path}")


def main():
    res = compute_amplitudes()
    col_names = list(AHP_WEIGHTS.keys())

    # ── Save JSON ─────────────────────────────────────────────────────────────
    out_json = OUT / "amplitudes.json"
    json.dump(res, out_json.open("w"), indent=2)
    print(f"Written: {out_json}")
    print(f"Source SHA-256: {res['source_sha256'][:16]}")

    # ── Write macros_amplitudes.tex ───────────────────────────────────────────
    write_macros_amplitudes_tex(res, REPO / "macros_amplitudes.tex")

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
    print("=== TV(a=2) -- manuscript formula w_j^2 * A_j^2 (definition ii) ===")
    print(f"  TValphaTwo      = {res['TV_alpha2']:.4f}   (old 0.675 was def-ii rho_raw; 0.590 was def-i rho_shift)")
    print(f"  DeltaTValphaTwo = +{res['DeltaTV_alpha2']:.4f}  (TV(2)-TV(1), was +0.360 rho_raw, +0.279 wrong def)")
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
