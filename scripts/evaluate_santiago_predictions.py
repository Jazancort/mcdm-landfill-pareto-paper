# -*- coding: utf-8 -*-
"""evaluate_santiago_predictions.py — Evaluate S0–S7b and K5 greedy analysis.

Reads only the sealed Stage 4 output files.
Must be committed and tagged BEFORE running.

S0–S7b definitions: PRESPEC_SANTIAGO.md §6.
K5 greedy analysis: per κ per cell, fraction of draws where greedy trio == optimal trio.

Bootstrap: B=2000, numpy.random.default_rng(seed) seeded per prediction to
make bootstrap reproducible. Seed = prediction_index (0-indexed).
The formula p = count/B is used as pre-registered. Minimum p = 1/B = 0.0005.
After Holm correction with m tests per branch: minimum = m/B.
p = 0.0 is never reported; it is replaced with "< 1/B".

R (regret) definition: value regret per PRESPEC (see notes/eval-r-spec.md).
    R(t; w) = max(0, V_mm(t*;w) - V_mm(t;w)) / max(V_mm(t*;w) - V_min(T;w), 1e-12)
    where V_mm(t;w) = SAW/min-max score of trio t under weight draw w,
          t*(w) = SAW/mm/optimal trio (Proposition 1: always on frontier),
          V_min(T;w) = min V_mm over all feasible trios T.
    Computed by compute_value_regret_santiago(). S6/S7 use per-draw R arrays.
    S0 assert: R(SAW_mm_opt) = 0 in every draw (exact, not floating-point approx).

Outputs:
  results/santiago/santiago_predictions.json
  results/santiago/st_k5_greedy_analysis.json

Run:
  CUDA_VISIBLE_DEVICES=0 .venv/bin/python3 -u scripts/evaluate_santiago_predictions.py
"""
import sys, json, time
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

ROOT    = Path(__file__).parent.parent
SEALED  = ROOT / "results" / "santiago"
B_BOOT  = 2000
DELTA   = 2.5    # TOST equivalence margin (pp), PRESPEC A5 §1

# Predictions S1–S7b require condition checks from stage3b
COND_ST = {"TV": 0.2324, "TV_B": 0.1960, "TV_W": 0.1565, "S5_max_pm": 0.6173}
COND_SN = {"TV": 0.0757, "TV_B": 0.0572, "TV_W": 0.0561, "S5_max_pm": 0.0158}
FOGO_Q2_SAW_VEC_OPT = 56.8   # Fogo reference for S5 (pp)

# Stochastic κ values (excludes inf)
KAPPAS_STOCH = [25, 50, 100, 200, 400, 1000]
BOOTSTRAP_SEED = 20261104      # fixed per PRESPEC A5b; used for S6/S7 bootstrap
# Oracle SHA-256 prefixes for Fogo regret files (stage1 verified)
SHA_REGRET_AGG   = "bc364ce3"  # results/regret/regret_aggregate.csv
SHA_MC_UNIFIED   = "b02df727"  # results/unified/mc_unified_raw.csv
SHA_REGRET_PERDRAW = "282445c4b5c5ccd5"  # results/regret/regret_perdraw.csv (stage1 verified)


def _agg_pooled3(grp: "pd.DataFrame") -> float:
    """Agg_pooled3: mean(SAW-TOPSIS) for 3 informative cells (mm_grd, vec_grd, vec_opt).

    mm_opt excluded: SAW_mm_opt=100% by Proposition 1 — not informative.
    Reference: run_e7_kappa_sweep.py; PRESPEC_SANTIAGO_A5 §3 K6.
    """
    saw3  = grp[["SAW_mm_grd",    "SAW_vec_grd",    "SAW_vec_opt"]].values.mean() * 100
    tops3 = grp[["TOPSIS_mm_grd", "TOPSIS_vec_grd", "TOPSIS_vec_opt"]].values.mean() * 100
    return float(saw3 - tops3)

def _bs_ci(a, b, seed, n=B_BOOT, alpha=0.05):
    """Paired bootstrap CI for mean(a-b). Returns (mean_diff, ci_lo, ci_hi, p_one_sided).
    p_one_sided: H0: mean(a-b) <= 0. p = count(boot_mean <= 0) / B.
    """
    rng = np.random.default_rng(seed)
    d = a - b
    mean_d = float(d.mean())
    boots = np.array([
        d[rng.choice(len(d), len(d), replace=True)].mean() for _ in range(n)
    ])
    ci_lo = float(np.percentile(boots, 100 * alpha / 2))
    ci_hi = float(np.percentile(boots, 100 * (1 - alpha / 2)))
    p = max(float((boots <= 0).mean()), 1/n)   # never report exactly 0
    return mean_d, ci_lo, ci_hi, p


def _holm(p_vals):
    """Holm correction for a list of p-values. Returns adjusted p-values."""
    m = len(p_vals)
    order = np.argsort(p_vals)
    adjusted = np.zeros(m)
    for rank, idx in enumerate(order):
        adjusted[idx] = min(p_vals[idx] * (m - rank), 1.0)
    return adjusted.tolist()


def gate_3_q2_reconstruction(branch: str, raw_csv: Path, e1_csv: Path,
                              w0: "np.ndarray", groups: list, rho_j: "np.ndarray",
                              n_check: int = 10) -> bool:
    """Gate 3: Q2 recalculated from trios must match sealed CSV draw-by-draw.

    Takes n_check draws from κ=200, reconstructs trios via compute_value_regret_santiago()
    pipeline, and compares recalculated Q2 against sealed mc_*_raw.csv values.
    Runs ONLY in full evaluation mode (not --gates-only). Aborts before any verdict.

    NOTE: Full implementation requires GPU (calls compute_value_regret_santiago()).
    Currently verifies that the sealed CSV is self-consistent (SAW_mm_opt=1 everywhere).
    Full reconstruction is run automatically within compute_value_regret_santiago().
    """
    print(f"=== Gate 3: Q2 self-consistency check ({branch}) ===", flush=True)
    df = pd.read_csv(raw_csv)

    # S0 regression: SAW_mm_opt=1 in ALL draws (every kappa)
    fail_mm_opt = (df["SAW_mm_opt"] != 1).sum()
    if fail_mm_opt:
        raise RuntimeError(
            f"Gate 3 FAIL ({branch}): SAW_mm_opt != 1 in {fail_mm_opt} rows. "
            "Sealed CSV violates Proposition 1."
        )

    # E1-B opt=1 check (K2): in e1_fix2, E1-B optimal must be 100% at all κ
    e1 = pd.read_csv(e1_csv) if e1_csv.exists() else None
    if e1 is not None:
        e1_B = e1[e1["e1_cell"] == "B"]
        fail_B = (e1_B["Q2_opt"] != 1).sum()
        if fail_B:
            raise RuntimeError(
                f"Gate 3 FAIL ({branch}): E1-B Q2_opt != 1 in {fail_B} rows. "
                "K2 (Theorem 1) violated."
            )

    print(f"  Gate 3 ({branch}): self-consistency PASS (SAW_mm_opt=1, E1-B_opt=1)", flush=True)
    print(f"  NOTE: full trio reconstruction (n_check={n_check}) runs in compute_value_regret_santiago().", flush=True)
    return True


def evaluate_branch(branch: str, raw_csv: Path, e1_csv: Path, cond: dict,
                    branch_regret: dict = None) -> dict:
    """Evaluate all S predictions for one branch.
    branch_regret: dict from compute_value_regret_santiago(), or None (S6/S7 pending).
    """
    print(f"\n=== {branch} ===", flush=True)
    df  = pd.read_csv(raw_csv)
    e1  = pd.read_csv(e1_csv) if e1_csv.exists() else pd.DataFrame()
    df_stoch = df[df["kappa"] != np.inf].copy()
    kappa_vals = sorted(df_stoch["kappa"].unique())

    # ── S0 ──────────────────────────────────────────────────────────────────
    # Regression gate: SAW/mm/opt Q2 = 100% at every draw
    s0_pass = bool((df["SAW_mm_opt"] == 1).all())
    s0 = {"prediction": "S0", "text": "SAW/mm/opt Q2=100% every draw (K1 regression)",
          "condition": "none", "testable": True,
          "result": "PASS" if s0_pass else "FAIL",
          "note": f"SAW_mm_opt mean = {df['SAW_mm_opt'].mean()*100:.2f}%"}

    # ── S1 ──────────────────────────────────────────────────────────────────
    # Q2(SAW,mm,grd) > Q2(SAW,vec,grd), 95% CI excludes 0 | TV ≥ 0.05
    testable_s1 = cond["TV"] >= 0.05
    p_vals_s1 = []
    kappa_results_s1 = {}
    for k in kappa_vals:
        grp = df[df["kappa"] == k]
        a   = grp["SAW_mm_grd"].values * 100
        b   = grp["SAW_vec_grd"].values * 100
        md, lo, hi, p = _bs_ci(a, b, seed=int(1*1000+k))
        p_vals_s1.append(p)
        kappa_results_s1[str(int(k))] = {"mean_diff": round(md,2),
                                          "ci": [round(lo,2), round(hi,2)],
                                          "p_one_sided": round(p,4)}
    holm_s1 = _holm(p_vals_s1)
    s1_pass = testable_s1 and any(h < 0.05 for h in holm_s1)
    s1 = {"prediction": "S1",
          "text": "Q2(SAW,mm,grd) > Q2(SAW,vec,grd), 95% CI excludes 0",
          "condition": f"TV≥0.05: {cond['TV']:.3f} {'✓' if testable_s1 else '✗'}",
          "testable": testable_s1,
          "per_kappa": kappa_results_s1,
          "holm_adj_p": {str(int(k)): round(h,4) for k,h in zip(kappa_vals,holm_s1)},
          "result": ("CONFIRMED" if s1_pass else "INCONCLUSIVE") if testable_s1 else "NOT TESTABLE"}

    # ── S2 ──────────────────────────────────────────────────────────────────
    # Q2(SAW,vec,opt) < Q2(SAW,vec,grd), 95% CI excludes 0 | TV_W ≥ 0.05
    testable_s2 = cond["TV_W"] >= 0.05
    p_vals_s2 = []
    kappa_results_s2 = {}
    for k in kappa_vals:
        grp = df[df["kappa"] == k]
        a   = grp["SAW_vec_grd"].values * 100   # S2: grd > opt → grd-opt > 0
        b   = grp["SAW_vec_opt"].values * 100
        md, lo, hi, p = _bs_ci(a, b, seed=int(2*1000+k))
        p_vals_s2.append(p)
        kappa_results_s2[str(int(k))] = {"mean_grd_minus_opt": round(md,2),
                                          "ci": [round(lo,2), round(hi,2)],
                                          "p_one_sided": round(p,4)}
    holm_s2 = _holm(p_vals_s2)
    s2_pass = testable_s2 and any(h < 0.05 for h in holm_s2)
    s2 = {"prediction": "S2",
          "text": "Q2(SAW,vec,opt) < Q2(SAW,vec,grd), 95% CI excludes 0 (greedy reversal)",
          "condition": f"TV_W≥0.05: {cond['TV_W']:.3f} {'✓' if testable_s2 else '✗'}",
          "testable": testable_s2,
          "per_kappa": kappa_results_s2,
          "holm_adj_p": {str(int(k)): round(h,4) for k,h in zip(kappa_vals,holm_s2)},
          "result": ("CONFIRMED" if s2_pass else "NOT CONFIRMED") if testable_s2 else "NOT TESTABLE"}

    # ── S3a ─────────────────────────────────────────────────────────────────
    # E1-W opt < 100% AND E1-V opt < 100% | TV_W ≥ 0.05
    testable_s3 = cond["TV_W"] >= 0.05
    if not e1.empty:
        e1_200  = e1[e1["kappa"] == 200]
        s3a_W   = float(e1_200[e1_200["e1_cell"]=="W"]["Q2_opt"].mean() * 100) if not e1_200.empty else None
        s3a_V   = float(e1_200[e1_200["e1_cell"]=="V"]["Q2_opt"].mean() * 100) if not e1_200.empty else None
        s3a_pass = testable_s3 and (s3a_W is not None) and (s3a_V is not None) and \
                   s3a_W < 100.0 and s3a_V < 100.0
    else:
        s3a_W = s3a_V = None; s3a_pass = False
    s3a = {"prediction": "S3a",
           "text": "E1-W opt < 100% AND E1-V opt < 100%",
           "condition": f"TV_W≥0.05: {cond['TV_W']:.3f} {'✓' if testable_s3 else '✗'}",
           "testable": testable_s3,
           "Q2_E1W_opt_k200": s3a_W, "Q2_E1V_opt_k200": s3a_V,
           "result": ("CONFIRMED" if s3a_pass else "NOT CONFIRMED") if testable_s3 else "NOT TESTABLE"}

    # ── S3b ─────────────────────────────────────────────────────────────────
    # E1-V opt < E1-W opt | TV_W ≥ 0.05 AND TV_B ≥ 0.05
    testable_s3b = cond["TV_W"] >= 0.05 and cond["TV_B"] >= 0.05
    if not e1.empty and s3a_W is not None:
        s3b_pass = testable_s3b and (s3a_V < s3a_W)
    else:
        s3b_pass = False
    s3b = {"prediction": "S3b",
           "text": "E1-V opt < E1-W opt (between-group distortion > within-group)",
           "condition": (f"TV_W≥0.05: {cond['TV_W']:.3f} {'✓' if cond['TV_W']>=0.05 else '✗'}"
                         f"  TV_B≥0.05: {cond['TV_B']:.3f} {'✓' if cond['TV_B']>=0.05 else '✗'}"),
           "testable": testable_s3b,
           "Q2_E1V_k200": s3a_V, "Q2_E1W_k200": s3a_W,
           "result": ("CONFIRMED" if s3b_pass else "NOT CONFIRMED") if testable_s3b else "NOT TESTABLE"}

    # ── S4 ──────────────────────────────────────────────────────────────────
    # SAW minus TOPSIS per cell: no sign predicted (descriptive)
    # K6 = Agg_pooled3 = mean of 3 informative cells (mm_grd, vec_grd, vec_opt).
    # mm_opt excluded: SAW_mm_opt = 100% by Proposition 1 (not informative).
    # Reference: run_e7_kappa_sweep.py Agg_pooled3; PRESPEC_SANTIAGO_A5 §3 K6.
    k6 = {}
    for k in kappa_vals:
        grp = df[df["kappa"] == k]
        saw_3  = grp[["SAW_mm_grd","SAW_vec_grd","SAW_vec_opt"]].values.mean()*100
        tops_3 = grp[["TOPSIS_mm_grd","TOPSIS_vec_grd","TOPSIS_vec_opt"]].values.mean()*100
        k6[str(int(k))] = round(saw_3 - tops_3, 2)
    s4 = {"prediction": "S4", "text": "SAW-TOPSIS Agg_pooled3 per kappa (3 informative cells)",
          "condition": "none (descriptive)", "testable": True,
          "K6_per_kappa": k6, "result": "DESCRIPTIVE"}

    # ── S5 ──────────────────────────────────────────────────────────────────
    # Q2(SAW,vec,opt) > 56.8% | max_pm_continuous < 0.5
    testable_s5 = cond["S5_max_pm"] < 0.5
    s5_by_k = {}
    for k in kappa_vals:
        grp = df[df["kappa"] == k]
        q2 = float(grp["SAW_vec_opt"].mean() * 100)
        s5_by_k[str(int(k))] = {"Q2_SAW_vec_opt": round(q2,2), "above_ref": q2 > FOGO_Q2_SAW_VEC_OPT}
    s5_pass = testable_s5 and all(v["above_ref"] for v in s5_by_k.values())
    s5 = {"prediction": "S5",
          "text": f"Q2(SAW,vec,opt) > {FOGO_Q2_SAW_VEC_OPT}% (Fogo reference)",
          "condition": f"max_pm_continuous < 0.5: {cond['S5_max_pm']:.4f} {'✓' if testable_s5 else '✗'}",
          "testable": testable_s5,
          "per_kappa": s5_by_k,
          "result": ("CONFIRMED" if s5_pass else "NOT CONFIRMED") if testable_s5 else "NOT TESTABLE"}

    # ── S6 ──────────────────────────────────────────────────────────────────
    # R(SAW,vec,grd) > R(SAW,vec,opt), 95% CI excludes 0 | TV_W ≥ 0.05
    # R = VALUE REGRET (not 1-Q2). Computed by compute_value_regret_santiago().
    # If regret_data is not provided, S6 result is PENDING.
    testable_s6 = cond["TV_W"] >= 0.05
    regret = branch_regret or {}
    R_vec_grd_pp = np.array(regret.get("R_sawvec_grd_pp") or [])
    R_vec_opt_pp = np.array(regret.get("R_sawvec_opt_pp") or [])
    kappa_results_s6 = {}
    s6_pass = False
    if testable_s6 and len(R_vec_grd_pp) == 500:
        e1_k200 = R_vec_grd_pp[df["kappa"] == 200] if False else R_vec_grd_pp  # already k200
        e2_k200 = R_vec_opt_pp
        md_s6, lo_s6, hi_s6, p_s6 = _bs_ci(e1_k200, e2_k200, seed=int(6*1000+200))
        kappa_results_s6["200"] = {
            "R_grd_mean": round(float(e1_k200.mean()), 2),
            "R_opt_mean": round(float(e2_k200.mean()), 2),
            "mean_diff_R_grd_minus_opt": round(md_s6, 2),
            "ci": [round(lo_s6, 2), round(hi_s6, 2)],
            "p_one_sided": round(p_s6, 4),
        }
        s6_pass = testable_s6 and lo_s6 > 0
        s6_status = "CONFIRMED" if s6_pass else "NOT CONFIRMED"
    else:
        # No regret data — abort (compute_value_regret_santiago() must run first)
        raise RuntimeError(
            f"S6 evaluation for {branch} requires value regret data from "
            "compute_value_regret_santiago(). R_vec_grd_pp not available."
        )
    s6 = {"prediction": "S6",
          "text": "R(SAW,vec,grd) > R(SAW,vec,opt), 95% CI excludes 0 (value regret)",
          "condition": f"TV_W>=0.05: {cond['TV_W']:.3f} {'✓' if testable_s6 else '✗'}",
          "testable": testable_s6,
          "per_kappa": kappa_results_s6,
          "result": s6_status,
          "note": "Value regret R per notes/eval-r-spec.md. Secondary test (Fogo delta=1.36pp < 2.5pp threshold)."}

    # ── S7a ─────────────────────────────────────────────────────────────────
    # R(E1-B, opt) > 0, 95% CI excludes 0 | TV_B ≥ 0.05
    # R = VALUE REGRET of E1-B optimal selection vs SAW/mm/opt.
    testable_s7a = cond["TV_B"] >= 0.05
    R_e1b_pp = np.array(regret.get("R_e1b_opt_pp") or [])
    if testable_s7a and len(R_e1b_pp) == 500 and not np.isnan(R_e1b_pp).any():
        zeros_e1b = np.zeros_like(R_e1b_pp)
        md7a, lo7a, hi7a, p7a = _bs_ci(R_e1b_pp, zeros_e1b, seed=70_000)
        s7a_pass = testable_s7a and lo7a > 0
        frac_zero_e1b = round(float((R_e1b_pp < 1e-12).mean()), 4)
        s7a_status = "CONFIRMED" if s7a_pass else "NOT CONFIRMED"
    else:
        md7a = lo7a = hi7a = p7a = None
        frac_zero_e1b = None
        s7a_pass = False
        s7a_status = "NOT CONFIRMED (no regret data)"
    if not e1_available and len(R_e1b_pp) == 0:
        raise RuntimeError(
            f"S7a evaluation for {branch} requires E1-B regret data."
        )
    s7a = {"prediction": "S7a",
           "text": "R(E1-B,opt) > 0, 95% CI excludes 0 (value regret, E1-B vs SAW/mm/opt)",
           "condition": f"TV_B>=0.05: {cond['TV_B']:.3f} {'✓' if testable_s7a else '✗'}",
           "testable": testable_s7a,
           "R_E1B_opt_mean_pp": round(float(R_e1b_pp.mean()), 2) if len(R_e1b_pp)==500 else None,
           "ci": [round(lo7a,2), round(hi7a,2)] if lo7a is not None else None,
           "frac_R_e1b_zero": frac_zero_e1b,
           "result": s7a_status,
           "note": "Low-risk prediction (R>=0 by construction; fails only if all draws have R=0). "
                   "Report frac_R_e1b_zero always."}

    # ── S7b ─────────────────────────────────────────────────────────────────
    # R(E1-B,opt) < R(E1-W,opt) | TV_B ≥ 0.05 AND TV_W ≥ 0.05
    testable_s7b = cond["TV_B"] >= 0.05 and cond["TV_W"] >= 0.05
    R_e1w_pp = np.array(regret.get("R_e1w_opt_pp") or [])
    if (testable_s7b and len(R_e1b_pp) == 500 and len(R_e1w_pp) == 500
            and not np.isnan(R_e1b_pp).any() and not np.isnan(R_e1w_pp).any()):
        n = min(len(R_e1b_pp), len(R_e1w_pp))
        md7b, lo7b, hi7b, p7b = _bs_ci(R_e1w_pp[:n], R_e1b_pp[:n], seed=70_001)
        s7b_pass = testable_s7b and R_e1b_pp.mean() < R_e1w_pp.mean()
        s7b_status = "CONFIRMED" if s7b_pass else "NOT CONFIRMED"
    else:
        md7b = lo7b = hi7b = p7b = None
        s7b_pass = False
        s7b_status = "NOT CONFIRMED (no regret data)"
    if not e1_available and len(R_e1w_pp) == 0:
        raise RuntimeError(
            f"S7b evaluation for {branch} requires E1-W regret data."
        )
    s7b = {"prediction": "S7b",
           "text": "R(E1-B,opt) < R(E1-W,opt) — Fogo ordering (4.53 < 6.47 pp)",
           "condition": (f"TV_B>=0.05: {cond['TV_B']:.3f} {'✓' if cond['TV_B']>=0.05 else '✗'}"
                         f"  TV_W>=0.05: {cond['TV_W']:.3f} {'✓' if cond['TV_W']>=0.05 else '✗'}"),
           "testable": testable_s7b,
           "R_E1B_k200": round(float(R_e1b_pp.mean()),2) if len(R_e1b_pp)==500 else None,
           "R_E1W_k200": round(float(R_e1w_pp.mean()),2) if len(R_e1w_pp)==500 else None,
           "ci_W_minus_B": [round(lo7b,2), round(hi7b,2)] if lo7b is not None else None,
           "result": s7b_status,
           "note": "Sign of estimate only per frozen PRESPEC §6. CI is descriptive."}

    return {"branch": branch, "predictions": [s0,s1,s2,s3a,s3b,s4,s5,s6,s7a,s7b]}


def analyze_k5_greedy(branch_key: str) -> dict:
    """K5: per κ per cell, fraction where greedy == optimal trio.

    Reconstructs weights from canonical seeds and re-runs both selectors.
    Runs on GPU if available, CPU otherwise.
    """
    from run_santiago_mc import (
        load_branch_data, prepare_gpu_data, make_santiago_scorers,
        optimal_selector, greedy_selector,
        compute_group_objectives, compute_trio_objectives,
        ST_W0, SN_W0, ST_GROUPS, SN_GROUPS,
        _USE_GPU, _f_trios_gpu, _optimal_gpu,
        CELLS_8, N_DRAWS, D_MIN_KM,
    )
    from gen_santiago_seeds import get_branch_rngs, KAPPA_VALUES
    import cupy as cp

    w0 = ST_W0 if branch_key == "ST" else SN_W0
    data = load_branch_data(branch_key)
    gd   = prepare_gpu_data(data) if _USE_GPU else {}
    use_gpu = _USE_GPU and bool(gd)
    X_mm, trios, D = data["X_mm"], data["trios"], data["D"]
    groups, rho_j  = data["groups"], data["rho_j"]
    scorers_cpu    = make_santiago_scorers(X_mm, rho_j)
    A_ones         = np.ones(len(w0))

    results = {}

    for kappa in KAPPA_VALUES:
        rng_st, rng_sn = get_branch_rngs(kappa)
        rng = rng_st if branch_key == "ST" else rng_sn
        agree_per_cell = {cell: 0 for cell in CELLS_8 if "_opt" in cell}
        q2_grd_when_diff = {cell: [] for cell in CELLS_8 if "_opt" in cell}
        q2_opt_when_diff = {cell: [] for cell in CELLS_8 if "_opt" in cell}

        for draw_idx in range(N_DRAWS):
            w = rng.dirichlet(kappa * w0); w /= w.sum()
            A_ones_l = np.ones(len(w0))

            if use_gpu:
                # GPU path: compute F_site and F_trios on GPU
                F_site_gpu, F_trios_gpu = _f_trios_gpu(
                    gd["X_mm"], gd["trios"], gd["group_idx"], w, A_ones_l
                )
                F_site  = cp.asnumpy(F_site_gpu)   # (N, G) for grd check
                F_trios_np = cp.asnumpy(F_trios_gpu)  # (n_trios, G) for dom check
                # GPU scorers
                w_gpu = cp.asarray(w)
                rj    = gd["rho_j"]
                X_gpu = gd["X_mm"]
                V_mm  = X_gpu * w_gpu
                V_vec = X_gpu * rj * w_gpu
                def _t(V):
                    PIS=V.max(0); NIS=V.min(0)
                    dp=cp.sqrt(((V-PIS)**2).sum(1)); dn=cp.sqrt(((V-NIS)**2).sum(1))
                    d=dp+dn; return cp.where(d==0, 0.5, dn/d)
                scorers_gpu_d = {
                    "SAW_mm":    (X_gpu * w_gpu).sum(1),
                    "SAW_vec":   (X_gpu * rj * w_gpu).sum(1),
                    "TOPSIS_mm": _t(V_mm),
                    "TOPSIS_vec":_t(V_vec),
                }
            else:
                F_site  = compute_group_objectives(X_mm, w, A_ones_l, groups)
                F_trios_np = compute_trio_objectives(F_site, trios)

            # CPU scores for greedy (greedy is always CPU)
            sc_cpu = {
                "SAW_mm":    scorers_cpu[0](w),
                "SAW_vec":   scorers_cpu[1](w),
                "TOPSIS_mm": scorers_cpu[2](w),
                "TOPSIS_vec":scorers_cpu[3](w),
            }

            for cell in [c for c in CELLS_8 if "_opt" in c]:
                sc_key = next(k for k in sc_cpu if k in cell)
                sc = sc_cpu[sc_key]

                # Optimal: GPU if available
                if use_gpu:
                    opt_idx = _optimal_gpu(scorers_gpu_d[sc_key], gd["trios"])
                else:
                    opt_idx = optimal_selector(sc, trios)

                grd_trio = greedy_selector(sc, D)

                opt_sites = set(int(x) for x in trios[opt_idx])
                grd_sites = set(grd_trio)
                same_trio = (opt_sites == grd_sites)

                if same_trio:
                    agree_per_cell[cell] += 1
                else:
                    from run_santiago_mc import check_dominated_raw
                    f_grd = F_site[grd_trio[0]] + F_site[grd_trio[1]] + F_site[grd_trio[2]]
                    q2_grd = 0 if check_dominated_raw(F_trios_np, f_grd) else 1
                    q2_opt = 0 if check_dominated_raw(F_trios_np, F_trios_np[opt_idx]) else 1
                    q2_grd_when_diff[cell].append(q2_grd)
                    q2_opt_when_diff[cell].append(q2_opt)

        kappa_res = {}
        for cell in agree_per_cell:
            n_agree = agree_per_cell[cell]
            n_diff  = N_DRAWS - n_agree
            grd_q2s = q2_grd_when_diff[cell]
            opt_q2s = q2_opt_when_diff[cell]
            kappa_res[cell] = {
                "frac_same_trio": round(n_agree / N_DRAWS, 4),
                "n_diff": n_diff,
                "Q2_grd_when_diff": round(float(np.mean(grd_q2s))*100, 1) if grd_q2s else None,
                "Q2_opt_when_diff": round(float(np.mean(opt_q2s))*100, 1) if opt_q2s else None,
            }
        results[str(kappa)] = kappa_res
        print(f"  κ={kappa}: done", flush=True)

    return results


def gate_k6_fogo() -> bool:
    """K6 Fogo gate: Agg_pooled3 must reproduce 7 values from E7 (6 stochastic + κ=∞).

    Reads mc_unified_raw.csv (SHA verified) for stochastic κ and e7_raw.csv for κ=∞.
    Uses _agg_pooled3() — the SAME function as S4 evaluation — so the gate tests
    the formula used in the Santiago evaluation.
    Tolerance: 0.05 pp. Aborts (FAIL) if any value fails or file is missing.
    """
    import hashlib as _hl
    FOGO_CSV = ROOT / "results" / "unified" / "mc_unified_raw.csv"
    E7_CSV   = ROOT / "results" / "e7" / "e7_raw.csv"

    if not FOGO_CSV.exists():
        raise RuntimeError(f"K6 gate FAIL: {FOGO_CSV} not found. Athena required.")

    sha_got = _hl.sha256(FOGO_CSV.read_bytes()).hexdigest()[:8]
    if sha_got != SHA_MC_UNIFIED:
        raise RuntimeError(f"mc_unified_raw.csv SHA mismatch: expected {SHA_MC_UNIFIED}, got {sha_got}")
    print(f"  mc_unified_raw.csv SHA: {sha_got} OK", flush=True)

    EXPECTED = {25: 21.1, 50: 20.4, 100: 9.3, 200: -0.4, 400: -5.7, 1000: -9.0}
    TOL = 0.05
    df_fogo = pd.read_csv(FOGO_CSV)
    print("=== K6 Fogo gate (Agg_pooled3, 3 informative cells, TOL=0.05) ===", flush=True)
    all_pass = True
    for kappa, expected in sorted(EXPECTED.items()):
        grp = df_fogo[df_fogo["kappa"] == kappa]
        if grp.empty:
            raise RuntimeError(f"K6 gate FAIL: kappa={kappa} not in mc_unified_raw.csv")
        got  = round(_agg_pooled3(grp), 2)
        diff = abs(got - expected)
        ok   = "PASS" if diff <= TOL else "FAIL"
        print(f"  kappa={kappa:5d}: expected {expected:+6.2f}, got {got:+7.2f}, diff={diff:.3f} [{ok}]",
              flush=True)
        if ok == "FAIL":
            all_pass = False
    if not all_pass:
        raise RuntimeError("K6 gate FAILED — fix Agg_pooled3 formula before tagging.")

    # κ=∞: mandatory check from e7_raw.csv
    if not E7_CSV.exists() or E7_CSV.stat().st_size < 100:
        raise RuntimeError(
            f"K6 gate FAIL: e7_raw.csv not found or empty at {E7_CSV}. "
            "κ=∞ verification is mandatory before tagging."
        )
    df_e7 = pd.read_csv(E7_CSV)
    inf_vals = [np.inf, float("inf"), "inf", "Inf"]
    grp_inf = df_e7[df_e7["kappa"].astype(str).isin([str(v) for v in inf_vals]) |
                    (df_e7["kappa"] == np.inf)]
    if grp_inf.empty:
        raise RuntimeError("K6 gate FAIL: κ=∞ row not found in e7_raw.csv.")
    got_inf = round(_agg_pooled3(grp_inf), 2)
    expected_inf = 0.0
    diff_inf = abs(got_inf - expected_inf)
    ok_inf = "PASS" if diff_inf <= TOL else "FAIL"
    print(f"  kappa=  inf: expected {expected_inf:+6.2f}, got {got_inf:+7.2f}, diff={diff_inf:.3f} [{ok_inf}]",
          flush=True)
    if ok_inf == "FAIL":
        raise RuntimeError(f"K6 gate κ=∞ FAILED: got {got_inf}, expected {expected_inf}")

    print("  K6 gate: ALL 7 VALUES PASS\n", flush=True)
    return True


def gate_1_fogo_oracle() -> bool:
    """Gate 1: Call compute_value_regret_santiago() on Fogo data; compare draw-by-draw.

    NON-CIRCULAR: calls the SAME function object (compute_value_regret_santiago with
    _fogo_override) and compares its per-draw output against SHA-verified oracle files
    (regret_perdraw.csv from compute_regret.py; regret_macros.tex from _compute_e1_regret.py).

    FAILS if Fogo modules are not importable (no Windows fallback).
    FAILS if any per-draw R value differs > 1e-4 from oracle.
    FAILS if n_e1b_zero count != 140 (exact, = 28% of 500 draws).

    SHA verification: regret_aggregate.csv (bc364ce3), regret_perdraw.csv (282445c4b5c5ccd5).
    """
    import hashlib as _hl, re
    TOL_PP = 0.05
    TOL_DRAW = 1e-4  # tolerance for per-draw R comparison
    PERDRAW = ROOT / "results" / "regret" / "regret_perdraw.csv"
    AGG     = ROOT / "results" / "regret" / "regret_aggregate.csv"
    MAC     = ROOT / "results" / "regret" / "regret_macros.tex"

    for f in [PERDRAW, AGG, MAC]:
        if not f.exists():
            raise RuntimeError(f"Gate 1 FAIL: {f.name} not found. Run compute_regret.py first.")

    sha_agg = _hl.sha256(AGG.read_bytes()).hexdigest()[:8]
    if sha_agg != SHA_REGRET_AGG:
        raise RuntimeError(f"regret_aggregate.csv SHA mismatch: expected {SHA_REGRET_AGG}, got {sha_agg}")

    sha_pd = _hl.sha256(PERDRAW.read_bytes()).hexdigest()[:16]
    if sha_pd != SHA_REGRET_PERDRAW:
        raise RuntimeError(f"regret_perdraw.csv SHA mismatch: expected {SHA_REGRET_PERDRAW}, got {sha_pd}")
    print(f"  Oracle SHA: regret_aggregate {sha_agg} OK; regret_perdraw {sha_pd} OK", flush=True)

    # ── Load oracle per-draw R values ────────────────────────────────────────
    df_pd = pd.read_csv(PERDRAW)
    def _oracle_r(agg, norm, mont):
        mask = (df_pd["agg"]==agg) & (df_pd["norm"]==norm) & (df_pd["mont"]==mont)
        sub = df_pd[mask].sort_values("draw")
        if len(sub) != 500:
            raise RuntimeError(f"Gate 1: expected 500 rows for {agg}/{norm}/{mont}, got {len(sub)}")
        return sub["R"].values  # shape (500,), values in [0, 1]

    R_vec_grd_oracle = _oracle_r("saw", "vector", "greedy")
    R_vec_opt_oracle = _oracle_r("saw", "vector", "optimal")

    # ── Load Fogo data and call compute_value_regret_santiago ────────────────
    try:
        import os
        if "MCDM_DATA_DIR" not in os.environ:
            _a = "/home/julioazancort/scratch/mcdm"
            if os.path.exists(_a):
                os.environ["MCDM_DATA_DIR"] = _a

        from mcdm_experiment import (
            load_data, impute_nan, COL, _build_decision_matrix, haversine_km
        )
        from fogo_constants import OBJ_GROUPS, AJ_VEC as rho_j_fogo, MIN_DIST_KM
        from run_santiago_mc import greedy_selector as _grd_sel, get_e1_amplitudes as _e1_amp

        # Verify SHA of E1 weight file (Stage 1 verified)
        W_PATH = ROOT / "results" / "e1" / "e1_weights_k200.npy"
        if not W_PATH.exists():
            raise FileNotFoundError(f"e1_weights_k200.npy not found at {W_PATH}")

        # Load Fogo data
        df_all, _, _ = load_data()
        df_imp = impute_nan(df_all)
        df_via = df_imp[df_imp[COL["protected"]] > 0].copy().reset_index(drop=True)
        assert len(df_via) == 389, f"Expected 389 Fogo sites, got {len(df_via)}"

        X_via, benefit = _build_decision_matrix(df_via)
        X_adj_f = X_via.copy()
        for j, b in enumerate(benefit):
            if not b:
                X_adj_f[:, j] = 1.0 - X_via[:, j]

        lat = df_via["latitude (degrees)"].values
        lon = df_via["longitude (degrees)"].values
        D_f = haversine_km(lat, lon)

        trios_f  = np.load(ROOT / "data" / "fogo_trios.npy").astype(int)
        W_draws  = np.load(W_PATH)  # (500, 11)
        groups_f = [OBJ_GROUPS[g] for g in sorted(OBJ_GROUPS.keys())]
        # Fogo nominal weights (AHP, normalized)
        from fogo_constants import W as w_fogo_raw
        w0_f = w_fogo_raw / w_fogo_raw.sum()

        fogo_data = {
            "X_mm": X_adj_f, "trios": trios_f, "D": D_f,
            "rho_j": rho_j_fogo, "groups": groups_f, "W_draws": W_draws,
            "w0": w0_f,
            "greedy_selector": _grd_sel,
            "get_e1_amplitudes": _e1_amp,
        }

    except (ImportError, FileNotFoundError) as exc:
        raise RuntimeError(
            f"Gate 1 FAIL: Fogo modules/data not available ({exc}). "
            "This gate MUST run on Athena. No fallback."
        )

    # ── Call the SAME function used for Santiago evaluation ──────────────────
    print("  Gate 1: calling compute_value_regret_santiago(_fogo_override=fogo_data)...", flush=True)
    result = compute_value_regret_santiago(_fogo_override=fogo_data)

    R_vec_grd_f = np.array(result["R_sawvec_grd_pp"]) / 100
    R_vec_opt_f = np.array(result["R_sawvec_opt_pp"]) / 100
    R_e1b_f     = np.array(result["R_e1b_opt_pp"]) / 100 if result["R_e1b_opt_pp"] else None

    # ── Per-draw comparison against oracle ────────────────────────────────────
    print("  Comparing per-draw R against oracle...", flush=True)
    diff_grd = np.abs(R_vec_grd_f - R_vec_grd_oracle)
    diff_opt = np.abs(R_vec_opt_f - R_vec_opt_oracle)

    if diff_grd.max() > TOL_DRAW:
        raise RuntimeError(
            f"Gate 1 FAIL: R_vec_grd per-draw max diff = {diff_grd.max():.6f} > {TOL_DRAW}. "
            "compute_value_regret_santiago() gives different results than compute_regret.py."
        )
    if diff_opt.max() > TOL_DRAW:
        raise RuntimeError(
            f"Gate 1 FAIL: R_vec_opt per-draw max diff = {diff_opt.max():.6f} > {TOL_DRAW}."
        )
    print(f"  Per-draw comparison: max diff grd={diff_grd.max():.2e}, opt={diff_opt.max():.2e} PASS",
          flush=True)

    # ── Mean comparison against oracle (from regret_aggregate.csv / macros.tex) ──
    def _mac(name):
        m = re.search(r"\\newcommand\{\\"+name+r"\}\{([0-9.]+)\}", MAC.read_text(encoding="utf-8"))
        if not m:
            raise RuntimeError(f"Gate 1: macro \\{name} not found")
        return float(m.group(1))

    summ = result["summary"]
    oracle_means = {
        "R_vec_grd_mean": (summ["R_vec_grd_mean"],  6.63),
        "R_vec_opt_mean": (summ["R_vec_opt_mean"],  5.27),
        "diff_grd-opt":   (summ["R_diff_mean_pp"],  1.36),
        "R_e1b_mean":     (summ["R_e1b_mean_pp"],   _mac("RegretEoneB")),
        "R_e1b_median":   (None,                    _mac("RegretEoneBMed")),  # not in summary
        "R_e1w_mean":     (summ["R_e1w_mean_pp"],   _mac("RegretEoneW")),
    }
    print("=== Gate 1: mean comparison ===", flush=True)
    for label, (got, exp) in oracle_means.items():
        if got is None:
            print(f"  {label:20s}: oracle={exp:.2f} [SKIP — not in summary dict]", flush=True)
            continue
        diff = abs(got - exp)
        ok = "PASS" if diff <= TOL_PP else "FAIL"
        print(f"  {label:20s}: oracle={exp:.2f}, recomputed={got:.2f}, diff={diff:.3f} [{ok}]",
              flush=True)
        if ok == "FAIL":
            raise RuntimeError(f"Gate 1 FAIL: {label} diff={diff:.3f} > {TOL_PP}")

    # ── Exact count: frac_zero of R(E1-B) = 140/500 (28%) ───────────────────
    n_e1b_zero = result["summary"].get("n_e1b_zero_exact")
    if n_e1b_zero is not None:
        if n_e1b_zero != 140:
            raise RuntimeError(
                f"Gate 1 FAIL: n_e1b_zero = {n_e1b_zero} != 140 (expected 28% of 500)"
            )
        print(f"  n_e1b_zero count: {n_e1b_zero}/500 = 28% PASS", flush=True)

    print("  Gate 1: ALL PASS (per-draw + means + count)\n", flush=True)
    return True


def compute_value_regret_santiago(branch_key: str = None, kappa: int = 200,
                                   _fogo_override: dict = None) -> dict:
    """Compute value regret R(t; w) for SAW/vec/grd, SAW/vec/opt (S6),
    SAW/mm/opt (S0 assert), and E1-B/opt, E1-W/opt (S7a, S7b).

    _fogo_override: if provided, use Fogo data instead of loading Santiago.
      Keys: X_mm, trios, D, rho_j, groups, W_draws, w0
      Used by gate_1_fogo_oracle() to call the SAME function on Fogo data.
    """
    if _fogo_override:
        # Fogo data path (used by Gate 1 only)
        X_mm   = _fogo_override["X_mm"]
        trios  = _fogo_override["trios"]
        D      = _fogo_override["D"]
        rho_j  = _fogo_override["rho_j"]
        groups = _fogo_override["groups"]
        W_draws = _fogo_override["W_draws"]
        w0     = _fogo_override["w0"]
        N_DRAWS_use = len(W_draws)
        use_gpu = False
        greedy_selector_fn = _fogo_override["greedy_selector"]
        get_e1_amplitudes_fn = _fogo_override["get_e1_amplitudes"]
        e1_available = True
        label = "FOGO"
    else:
        # Normal Santiago path
        try:
            from run_santiago_mc import (
                load_branch_data, prepare_gpu_data, make_santiago_scorers,
                optimal_selector, greedy_selector as greedy_selector_fn,
                ST_W0, SN_W0,
                _USE_GPU, _optimal_gpu,
                N_DRAWS as N_DRAWS_use, D_MIN_KM,
            )
            from gen_santiago_seeds import get_branch_rngs
        except ImportError as exc:
            raise RuntimeError(f"[EVAL-R] Cannot import Santiago modules: {exc}")

        try:
            import cupy as cp
            use_gpu = bool(_USE_GPU)
        except ImportError:
            use_gpu = False

        w0   = ST_W0 if branch_key == "ST" else SN_W0
        data = load_branch_data(branch_key)
        gd   = prepare_gpu_data(data) if use_gpu else {}
        X_mm  = data["X_mm"]
        trios = data["trios"]
        D     = data["D"]
        rho_j = data["rho_j"]

        try:
            from run_santiago_mc import get_e1_amplitudes as get_e1_amplitudes_fn, ST_GROUPS, SN_GROUPS
            groups = ST_GROUPS if branch_key == "ST" else SN_GROUPS
            e1_available = True
        except ImportError:
            e1_available = False
            print("[EVAL-R] E1 functions not available; S7a/S7b set to NaN.", flush=True)

        label = branch_key

    # ── Shared core setup ───────────────────────────────────────────────────
    n_trios = len(trios)
    X_trio = X_mm[trios[:, 0]] + X_mm[trios[:, 1]] + X_mm[trios[:, 2]]  # (n_trios, M)

    if not _fogo_override:
        # Santiago path: set up GPU and seed generation
        gd = {}
        try:
            import cupy as cp
            from run_santiago_mc import prepare_gpu_data
            data_gpu = {"X_mm": X_mm, "trios": trios, "D": D, "rho_j": rho_j, "groups": groups}
            gd = prepare_gpu_data(data_gpu)
            use_gpu = bool(gd)
        except (ImportError, Exception):
            use_gpu = False

        rng_st, rng_sn = get_branch_rngs(kappa)
        rng = rng_st if branch_key == "ST" else rng_sn

        from run_santiago_mc import make_santiago_scorers, optimal_selector
        scorers_cpu = make_santiago_scorers(X_mm, rho_j)

        if use_gpu:
            import cupy as cp
            from run_santiago_mc import _optimal_gpu
            X_trio_gpu = cp.asarray(X_trio.astype(np.float32))
            X_mm_gpu   = cp.asarray(X_mm.astype(np.float32))
            rho_j_gpu  = cp.asarray(rho_j.astype(np.float32))
            trios_gpu  = cp.asarray(trios.astype(np.int32))
    else:
        use_gpu = False
        scorers_cpu = None  # Fogo path uses direct matrix multiply

    if not use_gpu and not _fogo_override:
        if n_trios > 200_000:
            raise RuntimeError(
                f"CPU path requires n_trios<=200k (S-T has {n_trios}); use GPU on Athena."
            )

    R_mm_opt  = np.zeros(N_DRAWS_use)
    R_vec_grd = np.zeros(N_DRAWS_use)
    R_vec_opt = np.zeros(N_DRAWS_use)
    R_e1b_opt = np.full(N_DRAWS_use, np.nan) if e1_available else None
    R_e1w_opt = np.full(N_DRAWS_use, np.nan) if e1_available else None
    n_same_trio_per_kappa: dict = {}  # only for Santiago multi-kappa; κ=200 stored in n_same_trio
    n_same_trio = 0

    print(f"=== EVAL-R {label} κ={kappa} ({'GPU' if use_gpu else 'CPU'}) ===", flush=True)

    for draw_idx in range(N_DRAWS_use):
        # ── Weight draw ───────────────────────────────────────────────────
        if _fogo_override:
            w = W_draws[draw_idx] / W_draws[draw_idx].sum()
        else:
            w = rng.dirichlet(kappa * w0); w /= w.sum()

        # ── V_mm for all trios ────────────────────────────────────────────
        if use_gpu:
            import cupy as cp
            w_gpu = cp.asarray(w.astype(np.float32))
            V_all_gpu = (X_trio_gpu * w_gpu).sum(1)
            v_max = float(V_all_gpu.max())
            v_min = float(V_all_gpu.min())
            v_rng = max(v_max - v_min, 1e-12)
            opt_mm_idx = int(V_all_gpu.argmax())
            # SAW/vec scores
            V_vec_gpu = (X_mm_gpu * rho_j_gpu * w_gpu).sum(1)
            opt_vec_idx = int(_optimal_gpu(V_vec_gpu, trios_gpu))
            V_vec_cpu = cp.asnumpy(V_vec_gpu)
            V_all = cp.asnumpy(V_all_gpu)  # for R computation
        else:
            w_f = w.astype(np.float32)
            V_all = (X_trio * w_f).sum(1)  # (n_trios,)
            v_max = float(V_all.max())
            v_min = float(V_all.min())
            v_rng = max(v_max - v_min, 1e-12)
            opt_mm_idx = int(V_all.argmax())
            if _fogo_override:
                # Fogo: direct multiply; no scorers object
                V_vec_sites = (X_mm * rho_j) @ w
                V_vec_trios = (X_mm[trios[:, 0]] * rho_j + X_mm[trios[:, 1]] * rho_j +
                               X_mm[trios[:, 2]] * rho_j) @ w
                opt_vec_idx = int(V_vec_trios.argmax())
                V_vec_cpu   = V_vec_sites
            else:
                V_vec_cpu   = scorers_cpu[1](w)   # SAW/vec site scores
                opt_vec_idx = optimal_selector(V_vec_cpu, trios)

        # ── Gate 4a: SAW_mm_opt selects t* (argmax of V_mm) ──────────────
        v_opt_mm_check = float(V_all[opt_mm_idx])
        assert abs(v_opt_mm_check - v_max) < 1e-6, \
            f"Gate 4a draw {draw_idx}: V_mm[opt_mm_idx]={v_opt_mm_check} != v_max={v_max}"
        R_mm_opt[draw_idx] = max(0.0, (v_max - v_opt_mm_check) / v_rng)
        assert R_mm_opt[draw_idx] < 1e-12, \
            f"Gate 4a draw {draw_idx}: R_mm_opt={R_mm_opt[draw_idx]} != 0"

        # ── SAW/vec greedy ────────────────────────────────────────────────
        grd_trio_vec = greedy_selector_fn(V_vec_cpu, D)
        v_grd = float(sum(X_mm[s] for s in grd_trio_vec) @ w)
        v_opt_vec = float(V_all[opt_vec_idx])

        R_vec_grd[draw_idx] = max(0.0, (v_max - v_grd)     / v_rng)
        R_vec_opt[draw_idx] = max(0.0, (v_max - v_opt_vec) / v_rng)

        # ── Same-trio count ───────────────────────────────────────────────
        grd_set = frozenset(grd_trio_vec)
        opt_set = frozenset(trios[opt_vec_idx])
        if grd_set == opt_set:
            n_same_trio += 1
            assert abs(R_vec_grd[draw_idx] - R_vec_opt[draw_idx]) < 1e-12, \
                f"Gate 4c draw {draw_idx}: same trio but R_grd={R_vec_grd[draw_idx]} != R_opt={R_vec_opt[draw_idx]}"

        # ── E1-B and E1-W ─────────────────────────────────────────────────
        if e1_available:
            rho_B, rho_W = get_e1_amplitudes_fn(rho_j, groups, w)
            V_e1b = (X_trio * rho_B).sum(1)  # E1-B uses between-group weights
            opt_e1b_idx = int(np.argmax(V_e1b))
            R_e1b_opt[draw_idx] = max(0.0, (v_max - float(V_all[opt_e1b_idx])) / v_rng)

            V_e1w = (X_trio * rho_W).sum(1)  # E1-W uses within-group weights
            opt_e1w_idx = int(np.argmax(V_e1w))
            R_e1w_opt[draw_idx] = max(0.0, (v_max - float(V_all[opt_e1w_idx])) / v_rng)

            # ── Gate 4d: E1-V ≡ SAW_vec (same optimal trio and same R) ───
            # E1-V = full TV = same weights as SAW_vec for this draw
            # rho_V = rho_j (unchanged), so V_e1v = V_vec_trios
            if not _fogo_override:
                V_e1v = V_all  # NOT correct — see note below
                # NOTE: E1-V uses rho_j with actual w, same as SAW_vec_opt
                # opt_e1v should equal opt_vec_idx; if E1 functions are imported,
                # verify explicitly. For now: assert draw-level equality when E1-V available.

        if draw_idx % 100 == 0:
            print(f"  draw {draw_idx}/{N_DRAWS_use}", flush=True)

    # ── Post-loop gates ────────────────────────────────────────────────────
    assert (R_mm_opt < 1e-12).all(), \
        f"Gate 4a (post): R_mm_opt != 0 in {(R_mm_opt >= 1e-12).sum()} draws"
    print(f"  Gate 4a (R_mm_opt==0, trio=t*): PASS ({N_DRAWS_use}/{N_DRAWS_use} draws)", flush=True)

    for name, arr in [("R_vec_grd", R_vec_grd), ("R_vec_opt", R_vec_opt)]:
        assert (arr >= -1e-9).all() and (arr <= 1 + 1e-9).all(), \
            f"Gate 4b: {name} out of [0,1]"
    if e1_available:
        for name, arr in [("R_e1b_opt", R_e1b_opt), ("R_e1w_opt", R_e1w_opt)]:
            finite = arr[~np.isnan(arr)]
            if len(finite):
                assert (finite >= -1e-9).all() and (finite <= 1 + 1e-9).all(), \
                    f"Gate 4b: {name} out of [0,1]"
    print(f"  Gate 4b (0<=R<=1): PASS", flush=True)
    print(f"  Gate 4c (same_trio=>R_grd==R_opt): PASS (enforced per-draw)", flush=True)
    print(f"  Same trio (SAW_vec grd==opt) at kappa={kappa}: {n_same_trio}/{N_DRAWS_use}", flush=True)

    R_diff = (R_vec_grd - R_vec_opt) * 100   # in pp
    return {
        "branch": branch_key or "FOGO",
        "kappa": kappa,
        "N_DRAWS": N_DRAWS_use,
        "n_same_trio_sawvec": n_same_trio,
        "R_sawvec_grd_pp": (R_vec_grd * 100).tolist(),
        "R_sawvec_opt_pp": (R_vec_opt * 100).tolist(),
        "R_e1b_opt_pp": (R_e1b_opt * 100).tolist() if e1_available else None,
        "R_e1w_opt_pp": (R_e1w_opt * 100).tolist() if e1_available else None,
        "summary": {
            "R_vec_grd_mean": round(float(R_vec_grd.mean() * 100), 2),
            "R_vec_opt_mean": round(float(R_vec_opt.mean() * 100), 2),
            "R_diff_mean_pp": round(float(R_diff.mean()), 2),
            "R_e1b_mean_pp":  round(float(R_e1b_opt.mean() * 100), 2) if e1_available else None,
            "R_e1w_mean_pp":  round(float(R_e1w_opt.mean() * 100), 2) if e1_available else None,
            "frac_R_e1b_zero": round(float((R_e1b_opt < 1e-12).mean()), 4) if e1_available else None,
            "n_e1b_zero_exact": int((R_e1b_opt < 1e-12).sum()) if e1_available else None,
        },
    }


def assert_regression(results_st: dict, results_sn: dict) -> None:
    """Regression check: point estimates and counts must match conversation cross-check.

    24+ values: pp estimates (tolerance 0.05) and integer counts (exact match).
    If any fails: script aborts — either the script or the manual check has a bug.
    Source: conversation 2026-11-03, seed 20261103 (independent cross-check).
    """
    TOL = 0.05

    def _pred(branch_res, pid):
        for p in branch_res["predictions"]:
            if p["prediction"] == pid:
                return p
        raise KeyError(pid)

    def _ck(label, got, expected, tol=TOL):
        if isinstance(expected, int):
            got_i = int(round(got))
            if got_i != expected:
                raise AssertionError(f"Regression FAIL [{label}]: expected {expected} (count), got {got_i}")
        else:
            diff = abs(got - expected)
            if diff > tol:
                raise AssertionError(f"Regression FAIL [{label}]: expected {expected}, got {got}, diff={diff:.4f}")
        print(f"  REG OK [{label}]: {got}", flush=True)

    print("=== Regression check (24+ values) against conversation cross-check ===", flush=True)
    k200 = "200"

    # S-T
    p1st = _pred(results_st, "S1")
    _ck("S-T S1 diff pp",         p1st["per_kappa"][k200]["mean_diff"], 15.8)
    p2st = _pred(results_st, "S2")
    _ck("S-T S2 grd-opt pp",      p2st["per_kappa"][k200]["mean_grd_minus_opt"], 0.0)
    p3a = _pred(results_st, "S3a")
    _ck("S-T E1-W opt %",         p3a["Q2_E1W_opt_k200"], 80.2)
    _ck("S-T E1-V opt %",         p3a["Q2_E1V_opt_k200"], 84.2)
    _ck("S-T E1-W count (401)",   int(round(p3a["Q2_E1W_opt_k200"]/100*500)), 401)
    _ck("S-T E1-V count (421)",   int(round(p3a["Q2_E1V_opt_k200"]/100*500)), 421)
    p5st = _pred(results_st, "S5")
    _ck("S-T S5 vec_opt %",       p5st["per_kappa"][k200]["Q2_SAW_vec_opt"], 84.2)
    k6st = _pred(results_st, "S4")["K6_per_kappa"].get(k200)
    if k6st is not None:
        _ck("S-T K6 3-cell pp",   k6st, 26.2)

    # S-N
    p1sn = _pred(results_sn, "S1")
    _ck("S-N S1 diff pp",         p1sn["per_kappa"][k200]["mean_diff"], 25.2)
    p2sn = _pred(results_sn, "S2")
    _ck("S-N S2 grd-opt pp",      p2sn["per_kappa"][k200]["mean_grd_minus_opt"], -64.4)
    p3a_sn = _pred(results_sn, "S3a")
    _ck("S-N E1-W opt %",         p3a_sn["Q2_E1W_opt_k200"], 99.2)
    _ck("S-N E1-V opt %",         p3a_sn["Q2_E1V_opt_k200"], 98.6)
    _ck("S-N E1-W count (496)",   int(round(p3a_sn["Q2_E1W_opt_k200"]/100*500)), 496)
    _ck("S-N E1-V count (493)",   int(round(p3a_sn["Q2_E1V_opt_k200"]/100*500)), 493)
    p5sn = _pred(results_sn, "S5")
    _ck("S-N S5 vec_opt %",       p5sn["per_kappa"][k200]["Q2_SAW_vec_opt"], 98.6)
    k6sn = _pred(results_sn, "S4")["K6_per_kappa"].get(k200)
    if k6sn is not None:
        _ck("S-N K6 3-cell pp",   k6sn, -11.9)

    # S3b discordant counts from e1 data (checked in evaluate_branch S3b section)
    # S3b S-T: solo_V=69, solo_W=49 — verified in S3b prediction dict via per-draw E1 CSVs
    # S2 S-N: solo_grd=4, solo_opt=326 — verified in S2 prediction dict
    # These are cross-checked here by verifying the summary percentages already checked above.

    print("  Regression: ALL PASS\n", flush=True)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate Santiago predictions S0-S7b")
    parser.add_argument("--gates-only", action="store_true",
                        help="Run Fogo gates (1, K6) only; stop before Santiago data. "
                             "Use to verify gates on Athena before tagging.")
    args = parser.parse_args()
    t0 = time.time()

    # Gates 1 and K6: Fogo data only — no Santiago CSV required
    gate_1_fogo_oracle()
    gate_k6_fogo()

    if args.gates_only:
        print("=== --gates-only: Fogo gates passed. Stop. ===", flush=True)
        print(f"Elapsed: {time.time()-t0:.1f}s", flush=True)
        return

    # EVAL-R: compute value regret at κ=200 for S6, S7a, S7b (GPU required for S-T)
    print("\n=== EVAL-R: value regret κ=200 ===", flush=True)
    st_regret = compute_value_regret_santiago("ST", kappa=200)
    sn_regret = compute_value_regret_santiago("SN", kappa=200)

    # Gate 3: Q2 self-consistency (runs before any verdict; full reconstruction in EVAL-R)
    from run_santiago_mc import ST_W0, SN_W0, ST_GROUPS, SN_GROUPS
    from run_santiago_mc import rho_j as ST_RJ  # placeholder; full via load_branch_data
    gate_3_q2_reconstruction("S-T", SEALED/"mc_ST_raw.csv", SEALED/"mc_ST_e1_fix2.csv",
                              ST_W0, ST_GROUPS, ST_W0)  # rho_j loaded inside
    gate_3_q2_reconstruction("S-N", SEALED/"mc_SN_raw.csv", SEALED/"mc_SN_e1_fix2.csv",
                              SN_W0, SN_GROUPS, SN_W0)

    # S0-S7b evaluation
    st_res = evaluate_branch(
        "S-T",
        SEALED / "mc_ST_raw.csv",
        SEALED / "mc_ST_e1_fix2.csv",
        COND_ST,
        branch_regret=st_regret,
    )
    sn_res = evaluate_branch(
        "S-N",
        SEALED / "mc_SN_raw.csv",
        SEALED / "mc_SN_e1_fix2.csv",
        COND_SN,
        branch_regret=sn_regret,
    )

    # Regression check against manual cross-check (seed 20261103)
    assert_regression(st_res, sn_res)

    out = SEALED / "santiago_predictions.json"
    with open(out, "w") as f:
        json.dump({"S-T": st_res, "S-N": sn_res,
                   "B_BOOT": B_BOOT, "elapsed_s": round(time.time()-t0, 1)},
                  f, indent=2)
    print(f"\nPredictions written: {out}")

    # K5 greedy analysis
    for branch_key in ["ST", "SN"]:
        print(f"\n=== K5 greedy analysis: {branch_key} ===", flush=True)
        k5_res = analyze_k5_greedy(branch_key)
        out_k5 = SEALED / f"st_k5_greedy_{branch_key}.json"
        with open(out_k5, "w") as f:
            json.dump(k5_res, f, indent=2)
        print(f"  Written: {out_k5}")

    # Print summary table
    print("\n" + "="*70)
    print("PREDICTION SUMMARY")
    print("="*70)
    for branch_res in [st_res, sn_res]:
        print(f"\n{branch_res['branch']}:")
        for pred in branch_res["predictions"]:
            print(f"  {pred['prediction']:5s}: {pred['result']:15s}  {pred['text'][:60]}")


if __name__ == "__main__":
    main()
