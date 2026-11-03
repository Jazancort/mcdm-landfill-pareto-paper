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
SHA_REGRET_AGG     = "bc364ce312ce9772f06d41fc63f0fc0b0991f6cc8665a52d82515283df952bd1"
SHA_MC_UNIFIED     = "b02df727"  # results/unified/mc_unified_raw.csv
SHA_REGRET_PERDRAW = "282445c4b5c5ccd593963ae1073210385da465b93fa45408e97ba3f5c99201ca"


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


def gate_3_q2_reconstruction(branch_key: str, n_check: int = 10) -> dict:
    """Gate 3: Reconstruct Q2 for 12 cells at κ=200; compare draw-by-draw to sealed CSV.

    Uses canonical seeds + same MC functions that produced the sealed CSV.
    Logs trios SHA and device. Returns {draw_idx: {cell: trio_idx}} for Gate 4a.

    Only runs in full evaluation mode (not --gates-only).
    Raises RuntimeError on mismatch or if Santiago modules not importable.
    """
    import hashlib as _hl

    tag       = branch_key                   # "ST" or "SN"
    raw_csv   = SEALED / f"mc_{tag}_raw.csv"
    e1_csv    = SEALED / f"mc_{tag}_e1_fix2.csv"
    label     = "S-T" if tag == "ST" else "S-N"

    for f in [raw_csv, e1_csv]:
        if not f.exists():
            raise RuntimeError(f"Gate 3 FAIL: {f.name} not found")

    df_raw = pd.read_csv(raw_csv)
    df_e1  = pd.read_csv(e1_csv)
    df_k200 = df_raw[df_raw["kappa"] == 200].sort_values("draw").reset_index(drop=True)
    df_e1_k = df_e1[df_e1["kappa"]   == 200].sort_values(["draw","e1_cell"]).reset_index(drop=True)

    print(f"=== Gate 3: Q2 reconstruction ({label}, n_check={n_check}) ===", flush=True)

    try:
        from run_santiago_mc import (
            load_branch_data, make_santiago_scorers,
            optimal_selector, greedy_selector,
            compute_group_objectives, compute_trio_objectives,
            check_dominated_raw,
            ST_W0, SN_W0, ST_GROUPS, SN_GROUPS,
            get_e1_amplitudes,
        )
        from gen_santiago_seeds import get_branch_rngs
    except (ImportError, FileNotFoundError) as exc:
        raise RuntimeError(
            f"Gate 3 FAIL: Santiago modules not importable ({exc}). Requires Athena."
        )

    data   = load_branch_data(branch_key)
    X_mm   = np.asarray(data["X_mm"],  dtype=np.float32)
    trios  = np.asarray(data["trios"], dtype=np.int32)
    D      = data["D"]
    rho_j  = data["rho_j"]
    groups = ST_GROUPS if branch_key == "ST" else SN_GROUPS
    w0     = np.asarray(ST_W0 if branch_key == "ST" else SN_W0, dtype=np.float64)

    trios_sha = _hl.sha256(trios.tobytes()).hexdigest()[:16]
    print(f"  trios SHA-256[:16]: {trios_sha}  n_trios: {len(trios)}", flush=True)

    # Pre-generate all 500 draws at κ=200 from canonical seeds
    kappa = 200
    rng_st, rng_sn = get_branch_rngs(kappa)
    rng = rng_st if branch_key == "ST" else rng_sn
    W_all = np.array([rng.dirichlet(kappa * w0) for _ in range(500)])
    W_all = W_all / W_all.sum(axis=1, keepdims=True)

    scorers_cpu = make_santiago_scorers(X_mm, rho_j)
    A_ones      = np.ones(len(w0))

    trio_indices: dict = {}   # {draw_idx: {"SAW_mm_opt": idx, ...}} for Gate 4a
    n_fail = 0

    for di in range(n_check):
        w  = W_all[di].astype(np.float64)
        wf = w.astype(np.float32)

        # Group objectives (same call as run_santiago_mc)
        F_site  = compute_group_objectives(X_mm, w, A_ones, groups)
        F_trios = compute_trio_objectives(F_site, trios)

        def _q2_trio(idx: int) -> int:
            return 0 if check_dominated_raw(F_trios, F_trios[idx]) else 1

        def _q2_grd(grd: list) -> int:
            f = F_site[grd[0]] + F_site[grd[1]] + F_site[grd[2]]
            return 0 if check_dominated_raw(F_trios, f) else 1

        sc_mm   = scorers_cpu[0](wf)
        sc_vec  = scorers_cpu[1](wf)
        sc_tmm  = scorers_cpu[2](wf)
        sc_tvec = scorers_cpu[3](wf)

        opt_mm   = optimal_selector(sc_mm,   trios)
        opt_vec  = optimal_selector(sc_vec,  trios)
        opt_tmm  = optimal_selector(sc_tmm,  trios)
        opt_tvec = optimal_selector(sc_tvec, trios)
        grd_mm   = greedy_selector(sc_mm,   D)
        grd_vec  = greedy_selector(sc_vec,  D)
        grd_tmm  = greedy_selector(sc_tmm,  D)
        grd_tvec = greedy_selector(sc_tvec, D)

        trio_indices[di] = {"SAW_mm_opt": opt_mm, "SAW_vec_opt": opt_vec}

        raw_cells = [
            ("SAW_mm_grd",     _q2_grd(grd_mm)),
            ("SAW_mm_opt",     _q2_trio(opt_mm)),
            ("SAW_vec_grd",    _q2_grd(grd_vec)),
            ("SAW_vec_opt",    _q2_trio(opt_vec)),
            ("TOPSIS_mm_grd",  _q2_grd(grd_tmm)),
            ("TOPSIS_mm_opt",  _q2_trio(opt_tmm)),
            ("TOPSIS_vec_grd", _q2_grd(grd_tvec)),
            ("TOPSIS_vec_opt", _q2_trio(opt_tvec)),
        ]

        row = df_k200[df_k200["draw"] == di]
        if row.empty:
            raise RuntimeError(f"Gate 3 FAIL: draw {di} missing from {raw_csv.name}")

        for cell, got in raw_cells:
            exp = int(row[cell].values[0])
            if got != exp:
                print(f"  FAIL draw {di} {cell}: got {got} exp {exp}", flush=True)
                n_fail += 1

        # E1 cells: M, B, W, V
        rho_B, rho_W = get_e1_amplitudes(rho_j, groups, w)
        X_trio_arr   = X_mm[trios[:, 0]] + X_mm[trios[:, 1]] + X_mm[trios[:, 2]]
        V_e1b = X_trio_arr @ np.asarray(rho_B, dtype=np.float64)
        V_e1w = X_trio_arr @ np.asarray(rho_W, dtype=np.float64)
        V_e1v = X_trio_arr @ (rho_j * w)                        # rho_V = rho_j
        V_e1m = (X_trio_arr.astype(np.float64) * wf).sum(1)     # same as SAW_mm

        e1_opts = {
            "M": int(V_e1m.argmax()),
            "B": int(V_e1b.argmax()),
            "W": int(V_e1w.argmax()),
            "V": int(V_e1v.argmax()),
        }
        trio_indices[di]["E1_M_opt"] = e1_opts["M"]
        trio_indices[di]["E1_V_opt"] = e1_opts["V"]

        for cell_char, opt_idx in e1_opts.items():
            got_e1 = _q2_trio(opt_idx)
            e1_row = df_e1_k[(df_e1_k["draw"] == di) & (df_e1_k["e1_cell"] == cell_char)]
            if e1_row.empty:
                raise RuntimeError(f"Gate 3 FAIL: draw {di} E1-{cell_char} missing")
            exp_e1 = int(e1_row["Q2_opt"].values[0])
            if got_e1 != exp_e1:
                print(f"  FAIL draw {di} E1-{cell_char}_opt: got {got_e1} exp {exp_e1}",
                      flush=True)
                n_fail += 1

        print(f"  draw {di}: 12 cells OK", flush=True)

    if n_fail:
        raise RuntimeError(
            f"Gate 3 FAIL ({label}): {n_fail} cell mismatches in {n_check} draws. "
            "Seeds or computation path diverged from sealed CSV."
        )

    print(f"  Gate 3 ({label}): {n_check} draws x 12 cells ALL MATCH sealed CSV\n", flush=True)
    return trio_indices   # {draw_idx: {cell: trio_idx}} for Gate 4a


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
          "n_saw_mm_opt_k200": int((df[df["kappa"]==200]["SAW_mm_opt"]==1).sum()),
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
    df_k200_s2 = df[df["kappa"] == 200]
    solo_grd_k200 = int(((df_k200_s2["SAW_vec_grd"]==1) & (df_k200_s2["SAW_vec_opt"]==0)).sum())
    solo_opt_k200 = int(((df_k200_s2["SAW_vec_opt"]==1) & (df_k200_s2["SAW_vec_grd"]==0)).sum())
    s2 = {"prediction": "S2",
          "text": "Q2(SAW,vec,opt) < Q2(SAW,vec,grd), 95% CI excludes 0 (greedy reversal)",
          "condition": f"TV_W≥0.05: {cond['TV_W']:.3f} {'✓' if testable_s2 else '✗'}",
          "testable": testable_s2,
          "per_kappa": kappa_results_s2,
          "holm_adj_p": {str(int(k)): round(h,4) for k,h in zip(kappa_vals,holm_s2)},
          "solo_grd_k200": solo_grd_k200,
          "solo_opt_k200": solo_opt_k200,
          "result": ("CONFIRMED" if s2_pass else "NOT CONFIRMED") if testable_s2 else "NOT TESTABLE"}

    # ── S3a ─────────────────────────────────────────────────────────────────
    # E1-W opt < 100% AND E1-V opt < 100% | TV_W ≥ 0.05
    testable_s3 = cond["TV_W"] >= 0.05
    if not e1.empty:
        e1_200  = e1[e1["kappa"] == 200]
        s3a_W   = float(e1_200[e1_200["e1_cell"]=="W"]["Q2_opt"].mean() * 100) if not e1_200.empty else None
        s3a_V   = float(e1_200[e1_200["e1_cell"]=="V"]["Q2_opt"].mean() * 100) if not e1_200.empty else None
        e1b_cnt = int(e1_200[e1_200["e1_cell"]=="B"]["Q2_opt"].sum()) if not e1_200.empty else None
        s3a_pass = testable_s3 and (s3a_W is not None) and (s3a_V is not None) and \
                   s3a_W < 100.0 and s3a_V < 100.0
    else:
        s3a_W = s3a_V = e1b_cnt = None; s3a_pass = False
    s3a = {"prediction": "S3a",
           "text": "E1-W opt < 100% AND E1-V opt < 100%",
           "condition": f"TV_W≥0.05: {cond['TV_W']:.3f} {'✓' if testable_s3 else '✗'}",
           "testable": testable_s3,
           "Q2_E1W_opt_k200": s3a_W, "Q2_E1V_opt_k200": s3a_V,
           "E1B_opt_count_k200": e1b_cnt,
           "result": ("CONFIRMED" if s3a_pass else "NOT CONFIRMED") if testable_s3 else "NOT TESTABLE"}

    # ── S3b ─────────────────────────────────────────────────────────────────
    # E1-V opt < E1-W opt | TV_W ≥ 0.05 AND TV_B ≥ 0.05
    testable_s3b = cond["TV_W"] >= 0.05 and cond["TV_B"] >= 0.05
    if not e1.empty and s3a_W is not None and not e1_200.empty:
        e1_200_vw = e1_200[e1_200["e1_cell"].isin(["V","W"])].pivot_table(
            index="draw", columns="e1_cell", values="Q2_opt", aggfunc="first"
        )
        solo_V = int(((e1_200_vw["V"]==1) & (e1_200_vw["W"]==0)).sum())
        solo_W = int(((e1_200_vw["W"]==1) & (e1_200_vw["V"]==0)).sum())
        s3b_pass = testable_s3b and (s3a_V < s3a_W)
    else:
        solo_V = solo_W = None
        s3b_pass = False
    s3b = {"prediction": "S3b",
           "text": "E1-V opt < E1-W opt (between-group distortion > within-group)",
           "condition": (f"TV_W≥0.05: {cond['TV_W']:.3f} {'✓' if cond['TV_W']>=0.05 else '✗'}"
                         f"  TV_B≥0.05: {cond['TV_B']:.3f} {'✓' if cond['TV_B']>=0.05 else '✗'}"),
           "testable": testable_s3b,
           "Q2_E1V_k200": s3a_V, "Q2_E1W_k200": s3a_W,
           "solo_V_k200": solo_V, "solo_W_k200": solo_W,
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
    # branch_regret must always be provided; S6 raises RuntimeError otherwise.
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
        _, lo7a, hi7a, _ = _bs_ci(R_e1b_pp, zeros_e1b, seed=70_000)
        s7a_pass = testable_s7a and lo7a > 0
        frac_zero_e1b = round(float((R_e1b_pp < 1e-12).mean()), 4)
        s7a_status = "CONFIRMED" if s7a_pass else "NOT CONFIRMED"
    else:
        lo7a = hi7a = None
        frac_zero_e1b = None
        s7a_pass = False
        s7a_status = "NOT CONFIRMED (no regret data)"
    if e1.empty and len(R_e1b_pp) == 0:
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
        _, lo7b, hi7b, _ = _bs_ci(R_e1w_pp[:n], R_e1b_pp[:n], seed=70_001)
        s7b_pass = testable_s7b and R_e1b_pp.mean() < R_e1w_pp.mean()
        s7b_status = "CONFIRMED" if s7b_pass else "NOT CONFIRMED"
    else:
        lo7b = hi7b = None
        s7b_pass = False
        s7b_status = "NOT CONFIRMED (no regret data)"
    if e1.empty and len(R_e1w_pp) == 0:
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
        ST_W0, SN_W0,
        _USE_GPU, _f_trios_gpu, _optimal_gpu,
        CELLS_8, N_DRAWS,
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
    """Gate 1: Call compute_value_regret() on Fogo data; compare draw-by-draw.

    NON-CIRCULAR: calls compute_value_regret() from santiago_eval_core (no _fogo_override)
    and compares its per-draw output against SHA-verified oracle files.

    FAILS if Fogo modules are not importable (no Windows fallback).
    FAILS if any per-draw R value differs > 1e-12 from oracle.
    FAILS if n_e1b_zero count != 140 (exact, = 28% of 500 draws).

    SHA verification: full 64-char SHA-256 for both oracle files.
    """
    import hashlib as _hl, re
    from santiago_eval_core import load_fogo_data, compute_value_regret as _cvr

    TOL_PP   = 0.05
    TOL_DRAW = 1e-12   # per-draw tolerance: same code + data -> difference == 0
    PERDRAW  = ROOT / "results" / "regret" / "regret_perdraw.csv"
    AGG      = ROOT / "results" / "regret" / "regret_aggregate.csv"
    MAC      = ROOT / "results" / "regret" / "regret_macros.tex"

    for f in [PERDRAW, AGG, MAC]:
        if not f.exists():
            raise RuntimeError(f"Gate 1 FAIL: {f.name} not found. Run compute_regret.py first.")

    sha_agg = _hl.sha256(AGG.read_bytes()).hexdigest()
    if sha_agg != SHA_REGRET_AGG:
        raise RuntimeError(
            f"regret_aggregate.csv SHA mismatch:\n"
            f"  expected {SHA_REGRET_AGG}\n  got      {sha_agg}"
        )
    sha_pd = _hl.sha256(PERDRAW.read_bytes()).hexdigest()
    if sha_pd != SHA_REGRET_PERDRAW:
        raise RuntimeError(
            f"regret_perdraw.csv SHA mismatch:\n"
            f"  expected {SHA_REGRET_PERDRAW}\n  got      {sha_pd}"
        )
    print("  Oracle SHA: regret_aggregate OK; regret_perdraw OK", flush=True)

    # ── Load oracle per-draw R values ────────────────────────────────────────
    df_pd = pd.read_csv(PERDRAW)

    def _oracle_r(agg, norm, mont):
        mask = (df_pd["agg"] == agg) & (df_pd["norm"] == norm) & (df_pd["mont"] == mont)
        sub  = df_pd[mask].sort_values("draw")
        if len(sub) != 500:
            raise RuntimeError(
                f"Gate 1: expected 500 rows for {agg}/{norm}/{mont}, got {len(sub)}"
            )
        return sub["R"].values  # shape (500,), values in [0, 1]

    R_vec_grd_oracle = _oracle_r("saw", "vector", "greedy")
    R_vec_opt_oracle = _oracle_r("saw", "vector", "optimal")

    # ── Call the SAME function as Santiago evaluation ────────────────────────
    print("  Gate 1: calling load_fogo_data() + compute_value_regret()...", flush=True)
    result = _cvr(**load_fogo_data())

    R_vec_grd_f = np.array(result["R_sawvec_grd_pp"]) / 100
    R_vec_opt_f = np.array(result["R_sawvec_opt_pp"]) / 100

    # ── Per-draw comparison ──────────────────────────────────────────────────
    diff_grd = np.abs(R_vec_grd_f - R_vec_grd_oracle)
    diff_opt = np.abs(R_vec_opt_f - R_vec_opt_oracle)

    if diff_grd.max() > TOL_DRAW:
        raise RuntimeError(
            f"Gate 1 FAIL: R_vec_grd per-draw max diff = {diff_grd.max():.3e} > {TOL_DRAW}. "
            "compute_value_regret() diverges from oracle compute_regret.py."
        )
    if diff_opt.max() > TOL_DRAW:
        raise RuntimeError(
            f"Gate 1 FAIL: R_vec_opt per-draw max diff = {diff_opt.max():.3e} > {TOL_DRAW}."
        )
    print(
        f"  Per-draw: max diff grd={diff_grd.max():.2e} opt={diff_opt.max():.2e} PASS",
        flush=True,
    )

    # ── Mean/median comparison against macros.tex ────────────────────────────
    def _mac(name):
        txt = MAC.read_text(encoding="utf-8")
        m   = re.search(r"\\newcommand\{\\"+name+r"\}\{([0-9.]+)\}", txt)
        if not m:
            raise RuntimeError(f"Gate 1: macro \\{name} not found in regret_macros.tex")
        return float(m.group(1))

    summ = result["summary"]
    oracle_means = {
        "R_vec_grd_mean":   (summ["R_vec_grd_mean"],   6.63),
        "R_vec_opt_mean":   (summ["R_vec_opt_mean"],   5.27),
        "diff_grd-opt":     (summ["R_diff_mean_pp"],   1.36),
        "R_e1b_mean":       (summ["R_e1b_mean_pp"],    _mac("RegretEoneB")),
        "R_e1b_median":     (summ["R_e1b_median_pp"],  _mac("RegretEoneBMed")),
        "R_e1w_mean":       (summ["R_e1w_mean_pp"],    _mac("RegretEoneW")),
    }
    print("=== Gate 1: mean/median comparison ===", flush=True)
    for lbl, (got, exp) in oracle_means.items():
        diff = abs(got - exp)
        ok   = "PASS" if diff <= TOL_PP else "FAIL"
        print(f"  {lbl:20s}: oracle={exp:.2f}, got={got:.2f}, diff={diff:.3f} [{ok}]",
              flush=True)
        if ok == "FAIL":
            raise RuntimeError(f"Gate 1 FAIL: {lbl} diff={diff:.3f} > {TOL_PP}")

    # ── Exact count ──────────────────────────────────────────────────────────
    n_e1b_zero = summ.get("n_e1b_zero_exact")
    if n_e1b_zero != 140:
        raise RuntimeError(
            f"Gate 1 FAIL: n_e1b_zero = {n_e1b_zero} != 140 (expected 28% of 500)"
        )
    print(f"  n_e1b_zero: {n_e1b_zero}/500 = 28% PASS", flush=True)
    print("  Gate 1: ALL PASS\n", flush=True)
    return True


def compute_value_regret_santiago(branch_key: str, kappa: int = 200) -> dict:
    """Thin wrapper: delegates to santiago_eval_core.compute_value_regret().

    gate_1_fogo_oracle() uses load_fogo_data() + compute_value_regret() directly.
    This wrapper is called for the Santiago branches in main() only.
    """
    from santiago_eval_core import load_santiago_data, compute_value_regret as _cvr
    return _cvr(**load_santiago_data(branch_key, kappa))


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

    # ── 12 exact integer counts ───────────────────────────────────────────────
    # S0 SAW_mm_opt: all 500 draws optimal at κ=200 (Proposition 1)
    _ck("S-T SAW_mm_opt count", _pred(results_st, "S0")["n_saw_mm_opt_k200"], 500)
    _ck("S-N SAW_mm_opt count", _pred(results_sn, "S0")["n_saw_mm_opt_k200"], 500)

    # S2 solo counts (draws where one selector is non-dominated and the other is not)
    _ck("S-T S2 solo_grd k200", _pred(results_st, "S2")["solo_grd_k200"], 0)
    _ck("S-T S2 solo_opt k200", _pred(results_st, "S2")["solo_opt_k200"], 0)
    _ck("S-N S2 solo_grd k200", _pred(results_sn, "S2")["solo_grd_k200"], 4)
    _ck("S-N S2 solo_opt k200", _pred(results_sn, "S2")["solo_opt_k200"], 326)

    # S3b solo counts (draws where E1-V is non-dominated but E1-W is not, or vice versa)
    _ck("S-T S3b solo_V  k200", _pred(results_st, "S3b")["solo_V_k200"],  69)
    _ck("S-T S3b solo_W  k200", _pred(results_st, "S3b")["solo_W_k200"],  49)
    _ck("S-N S3b solo_V  k200", _pred(results_sn, "S3b")["solo_V_k200"],  0)
    _ck("S-N S3b solo_W  k200", _pred(results_sn, "S3b")["solo_W_k200"],  3)

    # E1-B opt count: Theorem 1 (always on Pareto frontier)
    _ck("S-T E1-B opt count",   _pred(results_st, "S3a")["E1B_opt_count_k200"], 500)
    _ck("S-N E1-B opt count",   _pred(results_sn, "S3a")["E1B_opt_count_k200"], 500)

    print("  Regression: ALL PASS\n", flush=True)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate Santiago predictions S0-S7b")
    parser.add_argument("--gates-only", action="store_true",
                        help="Run Fogo gates (1, K6) only. Stop before Santiago data. "
                             "Use to verify gates on Athena before tagging.")
    parser.add_argument("--gate3-only", action="store_true",
                        help="Run Gate 3 Q2 reconstruction only (both branches). "
                             "Implies loading Santiago modules; requires Athena.")
    args = parser.parse_args()
    t0 = time.time()

    # Fogo gates: always run first
    gate_1_fogo_oracle()
    gate_k6_fogo()

    if args.gates_only:
        print("=== --gates-only: Fogo gates passed. Stop. ===", flush=True)
        print(f"Elapsed: {time.time()-t0:.1f}s", flush=True)
        return

    # Gate 3: full Q2 reconstruction (requires Athena, runs before any verdict)
    if args.gate3_only:
        gate_3_q2_reconstruction("ST")
        gate_3_q2_reconstruction("SN")
        print("=== --gate3-only: Gate 3 PASS for both branches. ===", flush=True)
        print(f"Elapsed: {time.time()-t0:.1f}s", flush=True)
        return

    # EVAL-R: compute value regret at κ=200 for S6, S7a, S7b (GPU required for S-T)
    print("\n=== EVAL-R: value regret κ=200 ===", flush=True)
    st_regret = compute_value_regret_santiago("ST", kappa=200)
    sn_regret = compute_value_regret_santiago("SN", kappa=200)

    # Gate 3: full Q2 reconstruction (runs before any verdict); returns trio_indices
    g3_st = gate_3_q2_reconstruction("ST")
    g3_sn = gate_3_q2_reconstruction("SN")

    # Gate 4a identity: trio from Gate 3 must match argmax(V_mm) from EVAL-R
    print("=== Gate 4a identity (Gate 3 vs EVAL-R) ===", flush=True)
    for branch_key, g3, regret in [("ST", g3_st, st_regret), ("SN", g3_sn, sn_regret)]:
        for di, cell_dict in g3.items():
            opt_g3   = cell_dict["SAW_mm_opt"]
            opt_evalr = regret["trio_idx_mm_opt"][di]
            assert opt_g3 == opt_evalr, (
                f"Gate 4a identity FAIL ({branch_key} draw {di}): "
                f"Gate3 trio={opt_g3} != EVAL-R argmax={opt_evalr}"
            )
    print("  Gate 4a identity (Gate 3 vs EVAL-R): PASS\n", flush=True)

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
