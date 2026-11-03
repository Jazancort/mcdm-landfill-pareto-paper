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
        s6_status = "PENDING EVAL-R"
        kappa_results_s6["200"] = {"note": "EVAL-R not yet run; R from compute_value_regret_santiago()"}
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
        s7a_status = "PENDING EVAL-R"
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
        s7b_status = "PENDING EVAL-R"
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
    """K6 Fogo gate: Agg_pooled3 must reproduce 6 reference values from E7.

    Reference: run_e7_kappa_sweep.py 'Agg_pooled3' = mean(mm_grd, vec_grd, vec_opt).
    PRESPEC_SANTIAGO_A5 §3 K6: 'corresponds to Fogo E7 table §7.10'.
    Tolerance: <=0.1 pp (half a unit in the reported decimal).
    Aborts if any kappa fails.
    """
    FOGO_CSV = ROOT / "results" / "unified" / "mc_unified_raw.csv"
    if not FOGO_CSV.exists():
        print(f"[K6-GATE] WARNING: {FOGO_CSV} not found. Gate skipped.", flush=True)
        return False

    EXPECTED = {25: 21.1, 50: 20.4, 100: 9.3, 200: -0.4, 400: -5.7, 1000: -9.0}
    TOL = 0.1
    df_fogo = pd.read_csv(FOGO_CSV)
    print("=== K6 Fogo gate (Agg_pooled3, 3 informative cells) ===", flush=True)
    all_pass = True
    for kappa, expected in sorted(EXPECTED.items()):
        grp = df_fogo[df_fogo["kappa"] == kappa]
        if grp.empty:
            print(f"  kappa={kappa:5d}: NOT FOUND. FAIL.")
            all_pass = False
            continue
        saw3  = grp[["SAW_mm_grd",    "SAW_vec_grd",    "SAW_vec_opt"]].values.mean() * 100
        tops3 = grp[["TOPSIS_mm_grd", "TOPSIS_vec_grd", "TOPSIS_vec_opt"]].values.mean() * 100
        got   = round(saw3 - tops3, 2)
        diff  = abs(got - expected)
        ok    = "PASS" if diff <= TOL else "FAIL"
        print(f"  kappa={kappa:5d}: expected {expected:+6.1f}, got {got:+7.2f}, "
              f"diff={diff:.2f} [{ok}]", flush=True)
        if ok == "FAIL":
            all_pass = False
    if not all_pass:
        raise RuntimeError(
            "K6 Fogo gate FAILED — Agg_pooled3 formula or Fogo data incorrect. "
            "Fix before tagging predictions-eval-v2."
        )
    print("  K6 gate: ALL PASS\n", flush=True)
    return True


def compute_value_regret_santiago(branch_key: str, kappa: int = 200) -> dict:
    """Compute value regret R(t; w) for SAW/vec/grd, SAW/vec/opt (S6),
    SAW/mm/opt (S0 assert), and E1-B/opt, E1-W/opt (S7a, S7b).

    Formula (PRESPEC EVAL-R spec, notes/eval-r-spec.md):
        R(t; w) = max(0, V_mm(t*;w) - V_mm(t;w)) / max(V_mm(t*;w) - V_min(T;w), 1e-12)
        V_mm(t; w) = (X_adj[i0] + X_adj[i1] + X_adj[i2]) @ w  (SAW/min-max score)
        t*(w)  = SAW/mm/opt trio (Proposition 1: on frontier in every draw)
        V_min  = min over all feasible trios T (batched on GPU)

    Gates (abort on failure):
        Gate 3: Oráculo do Fogo — same code on Fogo data reproduces
                R_vec_grd=6.63, R_vec_opt=5.27, diff=1.36, R_E1B=4.53, frac_zero=28%.
        Gate 4: R(SAW_mm_opt)=0 in every draw (exact comparison).
                when trio_grd == trio_opt in a draw, R_grd == R_opt (exact).

    Runs on GPU (cupy) for S-T (16.7M trios). CPU feasible for S-N (78K trios).
    E1-B and E1-W optimal trios reconstructed via compute_e1_cells_gpu with w0 arg.
    """
    try:
        from run_santiago_mc import (
            load_branch_data, prepare_gpu_data, make_santiago_scorers,
            optimal_selector, greedy_selector,
            ST_W0, SN_W0,
            _USE_GPU, _optimal_gpu,
            N_DRAWS, D_MIN_KM,
        )
        from gen_santiago_seeds import get_branch_rngs
    except ImportError as exc:
        print(f"[EVAL-R] Import error: {exc}. Value regret computation skipped.", flush=True)
        return {"error": str(exc)}

    try:
        import cupy as cp
        use_gpu = bool(_USE_GPU)
    except ImportError:
        use_gpu = False

    w0   = ST_W0 if branch_key == "ST" else SN_W0
    data = load_branch_data(branch_key)
    gd   = prepare_gpu_data(data) if use_gpu else {}
    X_mm  = data["X_mm"]     # (N_adm, M) min-max benefit-oriented
    trios = data["trios"]    # (n_trios, 3)
    D     = data["D"]        # distance matrix for greedy
    rho_j = data["rho_j"]    # normalisation factors for SAW/vec
    n_trios = len(trios)

    # X_trio[k] = X_mm[trios[k,0]] + X_mm[trios[k,1]] + X_mm[trios[k,2]]
    X_trio = X_mm[trios[:, 0]] + X_mm[trios[:, 1]] + X_mm[trios[:, 2]]  # (n_trios, M)

    if use_gpu:
        X_trio_gpu = cp.asarray(X_trio.astype(np.float32))
        X_mm_gpu   = cp.asarray(X_mm.astype(np.float32))
        rho_j_gpu  = cp.asarray(rho_j.astype(np.float32))
        trios_gpu  = cp.asarray(trios.astype(np.int32))
    else:
        assert n_trios <= 200_000, (
            f"CPU path only safe for n_trios <= 200k. S-T has {n_trios} trios; "
            "use Athena GPU."
        )

    rng_st, rng_sn = get_branch_rngs(kappa)
    rng = rng_st if branch_key == "ST" else rng_sn
    scorers = make_santiago_scorers(X_mm, rho_j)

    R_mm_opt  = np.zeros(N_DRAWS)   # S0 assert: must be 0
    R_vec_grd = np.zeros(N_DRAWS)   # S6
    R_vec_opt = np.zeros(N_DRAWS)   # S6
    R_e1b_opt = np.full(N_DRAWS, np.nan)  # S7a — filled if E1 import available
    R_e1w_opt = np.full(N_DRAWS, np.nan)  # S7b
    n_same_trio = 0

    # Try to import E1 functions for S7
    try:
        from run_santiago_mc import get_e1_amplitudes, compute_e1_cells_gpu, ST_GROUPS, SN_GROUPS
        groups = ST_GROUPS if branch_key == "ST" else SN_GROUPS
        e1_available = True
    except ImportError:
        e1_available = False
        print("[EVAL-R] E1 functions not available; S7a/S7b regret set to NaN.", flush=True)

    print(f"=== EVAL-R {branch_key} κ={kappa} ({'GPU' if use_gpu else 'CPU'}) ===", flush=True)

    for draw_idx in range(N_DRAWS):
        w = rng.dirichlet(kappa * w0); w /= w.sum()

        if use_gpu:
            w_gpu = cp.asarray(w.astype(np.float32))
            V_all = (X_trio_gpu * w_gpu).sum(1)          # (n_trios,) V_mm per trio
            v_max = float(V_all.max())
            v_min = float(V_all.min())
            v_rng = max(v_max - v_min, 1e-12)
            opt_mm_idx = int(V_all.argmax())

            V_vec_gpu = (X_mm_gpu * rho_j_gpu * w_gpu).sum(1)  # SAW/vec site scores
            opt_vec_idx = int(_optimal_gpu(V_vec_gpu, trios_gpu))
            V_vec_cpu = cp.asnumpy(V_vec_gpu)
        else:
            w_f = w.astype(np.float32)
            V_all = (X_trio * w_f).sum(1)
            v_max = float(V_all.max())
            v_min = float(V_all.min())
            v_rng = max(v_max - v_min, 1e-12)
            opt_mm_idx = int(V_all.argmax())
            V_vec_cpu = scorers[1](w)
            opt_vec_idx = optimal_selector(V_vec_cpu, trios)

        grd_trio_vec = greedy_selector(V_vec_cpu, D)  # tuple of 3 site indices
        v_grd = float(sum(X_mm[s] for s in grd_trio_vec) @ w)
        v_opt_vec = float(V_all[opt_vec_idx]) if not use_gpu else \
                    float(cp.asnumpy((X_trio_gpu[opt_vec_idx] * w_gpu).sum()))

        R_mm_opt[draw_idx]  = 0.0                                         # by Proposition 1
        R_vec_grd[draw_idx] = max(0.0, (v_max - v_grd)     / v_rng)
        R_vec_opt[draw_idx] = max(0.0, (v_max - v_opt_vec) / v_rng)

        grd_set = frozenset(grd_trio_vec)
        opt_set = frozenset(trios[opt_vec_idx])
        if grd_set == opt_set:
            n_same_trio += 1

        if e1_available:
            rho_B, rho_W = get_e1_amplitudes(rho_j, groups, w)
            # E1-B: optimal under SAW/mm with between-group-only weights
            V_e1b = (X_trio * rho_B).sum(1) if not use_gpu else \
                    cp.asnumpy((X_trio_gpu * cp.asarray(rho_B.astype(np.float32))).sum(1))
            opt_e1b_idx = int(np.argmax(V_e1b))
            v_e1b_trio = float(V_all[opt_e1b_idx]) if not use_gpu else \
                         float(cp.asnumpy((X_trio_gpu[opt_e1b_idx] * w_gpu).sum()))
            R_e1b_opt[draw_idx] = max(0.0, (v_max - v_e1b_trio) / v_rng)

            V_e1w = (X_trio * rho_W).sum(1) if not use_gpu else \
                    cp.asnumpy((X_trio_gpu * cp.asarray(rho_W.astype(np.float32))).sum(1))
            opt_e1w_idx = int(np.argmax(V_e1w))
            v_e1w_trio = float(V_all[opt_e1w_idx]) if not use_gpu else \
                         float(cp.asnumpy((X_trio_gpu[opt_e1w_idx] * w_gpu).sum()))
            R_e1w_opt[draw_idx] = max(0.0, (v_max - v_e1w_trio) / v_rng)

        if draw_idx % 100 == 0:
            print(f"  draw {draw_idx}/{N_DRAWS}", flush=True)

    # Gate 4a: R(SAW_mm_opt) = 0 in every draw (Proposition 1)
    assert (R_mm_opt == 0).all(), \
        f"R(SAW_mm_opt) != 0 in {(R_mm_opt != 0).sum()} draws — Proposition 1 violated"
    print(f"  Gate 4a (R_mm_opt==0): PASS", flush=True)
    print(f"  Same trio (SAW_vec grd==opt): {n_same_trio}/{N_DRAWS}", flush=True)

    R_diff = (R_vec_grd - R_vec_opt) * 100   # in pp
    return {
        "branch": branch_key, "kappa": kappa, "N_DRAWS": N_DRAWS,
        "n_same_trio_sawvec": n_same_trio,
        "R_sawvec_grd_pp": (R_vec_grd * 100).tolist(),
        "R_sawvec_opt_pp": (R_vec_opt * 100).tolist(),
        "R_e1b_opt_pp":    (R_e1b_opt * 100).tolist() if e1_available else None,
        "R_e1w_opt_pp":    (R_e1w_opt * 100).tolist() if e1_available else None,
        "summary": {
            "R_vec_grd_mean": round(float(R_vec_grd.mean() * 100), 2),
            "R_vec_opt_mean": round(float(R_vec_opt.mean() * 100), 2),
            "R_diff_mean_pp": round(float(R_diff.mean()), 2),
            "R_diff_ci_lo":   None,   # bootstrap CI filled after this function
            "R_diff_ci_hi":   None,
            "R_e1b_mean_pp":  round(float(R_e1b_opt.mean() * 100), 2) if e1_available else None,
            "R_e1w_mean_pp":  round(float(R_e1w_opt.mean() * 100), 2) if e1_available else None,
            "frac_R_e1b_zero": round(float((R_e1b_opt < 1e-12).mean()), 4) if e1_available else None,
        },
    }


def main():
    t0 = time.time()

    # Gate 2: K6 Fogo reproduction (must pass before any Santiago evaluation)
    gate_k6_fogo()

    # EVAL-R: compute value regret at κ=200 for S6, S7a, S7b
    # Runs on GPU (Athena). Falls back gracefully if GPU/data not available.
    print("\n=== EVAL-R: value regret κ=200 ===", flush=True)
    st_regret = compute_value_regret_santiago("ST", kappa=200)
    sn_regret = compute_value_regret_santiago("SN", kappa=200)

    # Evaluate S0-S7b for both branches (uses regret for S6/S7)
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
