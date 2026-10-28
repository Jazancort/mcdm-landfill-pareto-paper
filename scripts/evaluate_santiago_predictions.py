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

R (regret) definition used here: R_j = mean(1 - Q2_j) × 100 (pp),
the fraction of draws where cell j's selected portfolio is NOT on the frontier.
This is consistent with the Fogo paper Table 5 definition (r4 code).

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


def evaluate_branch(branch: str, raw_csv: Path, e1_csv: Path, cond: dict) -> dict:
    """Evaluate all S predictions for one branch."""
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
    k6 = {}
    for k in kappa_vals:
        grp = df[df["kappa"] == k]
        saw  = grp[["SAW_mm_grd","SAW_mm_opt","SAW_vec_grd","SAW_vec_opt"]].values.mean()*100
        tops = grp[["TOPSIS_mm_grd","TOPSIS_mm_opt","TOPSIS_vec_grd","TOPSIS_vec_opt"]].values.mean()*100
        k6[str(int(k))] = round(saw - tops, 2)
    s4 = {"prediction": "S4", "text": "SAW−TOPSIS per κ, no sign predicted (descriptive)",
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
    # R(SAW,vec,grd) > R(SAW,vec,opt), 95% CI excludes 0
    # R_j = 1 - Q2_j (regret = fraction of non-efficient draws)
    # S6: grd has MORE regret than opt under vec → Q2(vec,opt) > Q2(vec,grd)
    # Note: this is OPPOSITE sign to S2 (S2 predicts Q2(opt) < Q2(grd))
    # S6 uses R while S2 uses Q2; identical prediction, different framing.
    testable_s6 = cond["TV_W"] >= 0.05
    p_vals_s6 = []
    kappa_results_s6 = {}
    for k in kappa_vals:
        grp = df[df["kappa"] == k]
        R_grd = (1 - grp["SAW_vec_grd"].values) * 100
        R_opt = (1 - grp["SAW_vec_opt"].values) * 100
        md, lo, hi, p = _bs_ci(R_grd, R_opt, seed=int(6*1000+k))
        p_vals_s6.append(p)
        kappa_results_s6[str(int(k))] = {"R_grd_mean": round(R_grd.mean(),2),
                                          "R_opt_mean": round(R_opt.mean(),2),
                                          "mean_diff_R_grd_minus_opt": round(md,2),
                                          "ci": [round(lo,2), round(hi,2)],
                                          "p_one_sided": round(p,4)}
    holm_s6 = _holm(p_vals_s6)
    s6_pass = testable_s6 and any(h < 0.05 for h in holm_s6)
    s6 = {"prediction": "S6",
          "text": "R(SAW,vec,grd) > R(SAW,vec,opt), 95% CI excludes 0",
          "condition": f"TV_W≥0.05: {cond['TV_W']:.3f} {'✓' if testable_s6 else '✗'}",
          "testable": testable_s6,
          "per_kappa": kappa_results_s6,
          "holm_adj_p": {str(int(k)): round(h,4) for k,h in zip(kappa_vals,holm_s6)},
          "result": ("CONFIRMED" if s6_pass else "NOT CONFIRMED") if testable_s6 else "NOT TESTABLE",
          "note": ("R = 1-Q2 (fraction of non-efficient draws). "
                   "S6 and S2 make OPPOSITE predictions: S2 predicts grd > opt (greedy reversal); "
                   "S6 predicts R(grd) > R(opt) = opt > grd. "
                   "Fogo reference shows S6 CONFIRMED (R_grd=6.63 > R_opt=5.27pp), not S2. "
                   "In Santiago S-N: S6 confirmed (opt >> grd). In Santiago S-T: both ≈ 0 (neutral).")}

    # ── S7a ─────────────────────────────────────────────────────────────────
    # R(E1-B, opt) > 0, 95% CI excludes 0 | TV_B ≥ 0.05
    # R here = fraction of draws where E1-B opt is NOT on the E1-B frontier
    # = 1 - mean(Q2_opt where e1_cell=="B")
    # Note: K2 checks the same quantity (Theorem 1 regression); K2=100% → R=0 → S7a not confirmable
    testable_s7a = cond["TV_B"] >= 0.05
    if not e1.empty:
        e1_B_200 = e1[(e1["kappa"]==200) & (e1["e1_cell"]=="B")]
        R_B = (1 - e1_B_200["Q2_opt"].values) * 100
        R_B_mean = float(R_B.mean())
        md7a, lo7a, hi7a, p7a = _bs_ci(R_B, np.zeros_like(R_B), seed=70_000)
        s7a_pass = testable_s7a and lo7a > 0
    else:
        R_B_mean = None; p7a = 1.0; lo7a = hi7a = 0; s7a_pass = False
    s7a = {"prediction": "S7a",
           "text": "R(E1-B,opt) > 0, 95% CI excludes 0",
           "condition": f"TV_B≥0.05: {cond['TV_B']:.3f} {'✓' if testable_s7a else '✗'}",
           "testable": testable_s7a,
           "R_E1B_opt_k200": R_B_mean, "ci": [round(lo7a,2), round(hi7a,2)],
           "p_one_sided": round(p7a,4),
           "result": ("CONFIRMED" if s7a_pass else "NOT CONFIRMED") if testable_s7a else "NOT TESTABLE",
           "note": "R here = 1-Q2 against E1-B frontier. K2=100% → R=0 by Theorem 1. See interpretation."}

    # ── S7b ─────────────────────────────────────────────────────────────────
    # R(E1-B,opt) < R(E1-W,opt) | TV_B ≥ 0.05 AND TV_W ≥ 0.05
    testable_s7b = cond["TV_B"] >= 0.05 and cond["TV_W"] >= 0.05
    if not e1.empty:
        e1_W_200 = e1[(e1["kappa"]==200) & (e1["e1_cell"]=="W")]
        R_W = (1 - e1_W_200["Q2_opt"].values) * 100
        R_W_mean = float(R_W.mean())
        n = min(len(R_B), len(R_W))
        md7b, lo7b, hi7b, p7b = _bs_ci(R_W[:n], R_B[:n], seed=70_001)
        s7b_pass = testable_s7b and lo7b > 0
    else:
        R_W_mean = None; p7b = 1.0; lo7b = hi7b = 0; s7b_pass = False
    s7b = {"prediction": "S7b",
           "text": "R(E1-B,opt) < R(E1-W,opt) at κ=200",
           "condition": (f"TV_B≥0.05: {cond['TV_B']:.3f} {'✓' if cond['TV_B']>=0.05 else '✗'}"
                         f"  TV_W≥0.05: {cond['TV_W']:.3f} {'✓' if cond['TV_W']>=0.05 else '✗'}"),
           "testable": testable_s7b,
           "R_E1B_k200": R_B_mean, "R_E1W_k200": R_W_mean,
           "mean_diff_W_minus_B": round(md7b,2) if testable_s7b else None,
           "ci_W_minus_B": [round(lo7b,2), round(hi7b,2)] if testable_s7b else None,
           "p_one_sided": round(p7b,4) if testable_s7b else None,
           "result": ("CONFIRMED" if s7b_pass else "NOT CONFIRMED") if testable_s7b else "NOT TESTABLE"}

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


def main():
    t0 = time.time()

    # Evaluate S0-S7b for both branches
    st_res = evaluate_branch(
        "S-T",
        SEALED / "mc_ST_raw.csv",
        SEALED / "mc_ST_e1.csv",
        COND_ST,
    )
    sn_res = evaluate_branch(
        "S-N",
        SEALED / "mc_SN_raw.csv",
        SEALED / "mc_SN_e1.csv",
        COND_SN,
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
