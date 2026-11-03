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
# Sealed Stage 4 prediction CSVs (verified at commit stage4-results-sealed)
SHA_SEALED = {
    "mc_ST_raw.csv":      "123a5421d81b7bdd5d405ddb4a60edde1eeaa2f7da5cefbb640812aeed67bd80",
    "mc_SN_raw.csv":      "dbfa2f00b6f3f98e3a900f9020f98ecb55ef98dfdeed199a334f7b299013d492",
    "mc_ST_e1_fix2.csv":  "7806db5da3e78246e2707ef7df3e4980b445f9b7e04e751e65dbfeefd2b07507",
    "mc_SN_e1_fix2.csv":  "357904c04d9d863b40c3cb448cb3b58e4615321cf5ac25f24c84a228312c1593",
}

# K6 Fogo expected values — module constant so tests can monkeypatch.
# Verified against e7_raw.csv on Athena; tolerance TOL=0.05 pp.
K6_FOGO_EXPECTED: dict = {25: 21.1, 50: 20.4, 100: 9.3, 200: -0.4, 400: -5.7, 1000: -9.0}

# Import shared aggregation functions from santiago_eval_core.
# _agg_pooled3     : wide-format DataFrame (mc_*_raw.csv columns)
# _agg_pooled3_long: long-format DataFrame (e7_raw.csv with agg/norm/mont columns)
# Both implement the same formula: mean(SAW 3-cell) - mean(TOPSIS 3-cell) [pp].
from santiago_eval_core import _agg_pooled3, _agg_pooled3_long  # noqa: E402

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


def gate_3_q2_reconstruction(branch_key: str, n_check: int = 500) -> dict:
    """Gate 3: Reconstruct Q2 for ALL κ (3001 raw + 2004 E1 lines) and compare
    draw-by-draw to sealed CSVs.

    Coverage:
      raw  : 6 stochastic κ × 500 draws × 8 cells  +  κ=∞ × 1 draw × 8 cells = 3001 rows
      E1   : κ=200 × 500 draws × 4 cells  +  κ=∞ × 1 draw × 4 cells           = 2004 rows

    Uses compute_q2_all_cells_gpu / compute_e1_cells_gpu from run_santiago_mc directly
    (no reimplementation). GPU path bit-for-bit identical to original sealed-CSV run.
    CPU fallback available for S-N (78K trios); S-T (16.7M) requires GPU.

    n_check applies only to the stochastic κ draws (max 500). κ=∞ always uses 1 draw.
    Returns {draw_idx: {"SAW_mm_opt": idx, "SAW_vec_opt": idx}} for κ=200 (Gate 4a).
    Raises RuntimeError on any mismatch or missing modules.
    """
    import hashlib as _hl

    tag     = branch_key
    raw_csv = SEALED / f"mc_{tag}_raw.csv"
    e1_csv  = SEALED / f"mc_{tag}_e1_fix2.csv"
    label   = "S-T" if tag == "ST" else "S-N"

    for f in [raw_csv, e1_csv]:
        sha_exp = SHA_SEALED[f.name]
        sha_got = _hl.sha256(f.read_bytes()).hexdigest()
        if sha_got != sha_exp:
            raise RuntimeError(
                f"Gate 3 FAIL: {f.name} SHA mismatch.\n"
                f"  expected {sha_exp}\n  got      {sha_got}"
            )
    print(f"  Sealed CSV SHA verified: {raw_csv.name}, {e1_csv.name}", flush=True)

    df_raw = pd.read_csv(raw_csv)
    df_e1  = pd.read_csv(e1_csv)

    # Verify row counts match spec
    if len(df_raw) != 3001:
        raise RuntimeError(
            f"Gate 3 FAIL: {raw_csv.name} has {len(df_raw)} rows, expected 3001"
        )
    if len(df_e1) != 2004:
        raise RuntimeError(
            f"Gate 3 FAIL: {e1_csv.name} has {len(df_e1)} rows, expected 2004"
        )
    print(f"  Row counts verified: raw={len(df_raw)}, e1={len(df_e1)}", flush=True)

    try:
        from run_santiago_mc import (
            load_branch_data, prepare_gpu_data,
            compute_q2_all_cells_gpu, compute_e1_cells_gpu,
            compute_q2_all_cells, make_santiago_scorers,
            compute_group_objectives, compute_trio_objectives,
            check_dominated_raw, optimal_selector, greedy_selector,
            get_e1_amplitudes,
            ST_W0, SN_W0, ST_GROUPS, SN_GROUPS, CELLS_8,
            _optimal_gpu,
        )
        from gen_santiago_seeds import get_branch_rngs, KAPPA_VALUES
    except (ImportError, FileNotFoundError) as exc:
        raise RuntimeError(
            f"Gate 3 FAIL: Santiago modules not importable ({exc}). Requires Athena."
        )

    data   = load_branch_data(branch_key)
    X_mm   = np.asarray(data["X_mm"],   dtype=np.float64)
    trios  = np.asarray(data["trios"],  dtype=np.int32)
    D      = data["D"]
    rho_j  = np.asarray(data["rho_j"],  dtype=np.float64)
    groups = ST_GROUPS if branch_key == "ST" else SN_GROUPS
    w0     = np.asarray(ST_W0 if branch_key == "ST" else SN_W0, dtype=np.float64)

    trios_sha = _hl.sha256(trios.tobytes()).hexdigest()[:16]
    print(f"  trios SHA-256[:16]: {trios_sha}  n_trios: {len(trios)}", flush=True)

    e1_amps = get_e1_amplitudes(rho_j, groups, w0=w0)

    gd = prepare_gpu_data(data)
    use_gpu = bool(gd)
    print(f"  device: {'GPU' if use_gpu else 'CPU'}", flush=True)

    if use_gpu:
        import cupy as cp

    scorers_cpu = make_santiago_scorers(X_mm, rho_j) if not use_gpu else None
    A_ones_cpu  = np.ones(len(w0))

    # Gate 4a trio indices — filled only for κ=200
    trio_indices_k200: dict = {}

    n_fail     = 0
    total_raw  = 0
    total_e1   = 0

    # ── Stochastic κ (500 draws each) ───────────────────────────────────────
    for kappa in KAPPA_VALUES:
        rng_st, rng_sn = get_branch_rngs(kappa)
        rng = rng_st if branch_key == "ST" else rng_sn
        W_k = np.array([rng.dirichlet(kappa * w0) for _ in range(500)])
        W_k = W_k / W_k.sum(axis=1, keepdims=True)

        df_raw_k = df_raw[df_raw["kappa"] == kappa].sort_values("draw").reset_index(drop=True)
        df_e1_k  = df_e1[df_e1["kappa"] == kappa].sort_values(
            ["draw", "e1_cell"]).reset_index(drop=True) if kappa == 200 else None

        n_draws_k = min(n_check, len(df_raw_k))
        print(f"  κ={kappa:4d}: {n_draws_k} draws × 8 raw"
              f"{' + 4 E1' if df_e1_k is not None else ''}...", flush=True)

        for di in range(n_draws_k):
            w_cpu = W_k[di]

            # raw Q2
            if use_gpu:
                raw_result, F_mm_trios_gpu, F_mm_site_gpu = compute_q2_all_cells_gpu(
                    gd, w_cpu, D
                )
                w_gpu       = cp.asarray(w_cpu)
                s_mm_gpu    = (gd["X_mm"] * w_gpu).sum(1)
                s_vec_gpu   = (gd["X_mm"] * gd["rho_j"] * w_gpu).sum(1)
                opt_mm_idx  = int(_optimal_gpu(s_mm_gpu,  gd["trios"]))
                opt_vec_idx = int(_optimal_gpu(s_vec_gpu, gd["trios"]))
            else:
                F_mm_site  = compute_group_objectives(X_mm, w_cpu, A_ones_cpu, groups)
                F_mm_trios = compute_trio_objectives(F_mm_site, trios)
                raw_result = compute_q2_all_cells(X_mm, w_cpu, A_ones_cpu, groups,
                                                  trios, D, scorers_cpu)
                opt_mm_idx  = optimal_selector(scorers_cpu[0](w_cpu), trios)
                opt_vec_idx = optimal_selector(scorers_cpu[1](w_cpu), trios)

            if kappa == 200:
                trio_indices_k200[di] = {
                    "SAW_mm_opt":  opt_mm_idx,
                    "SAW_vec_opt": opt_vec_idx,
                }

            row = df_raw_k[df_raw_k["draw"] == di]
            if row.empty:
                raise RuntimeError(
                    f"Gate 3 FAIL: κ={kappa} draw {di} missing from {raw_csv.name}"
                )
            for cell in CELLS_8:
                got = raw_result[cell]
                exp = int(row[cell].values[0])
                if got != exp:
                    print(f"  FAIL κ={kappa} draw {di} {cell}: got {got} exp {exp}",
                          flush=True)
                    n_fail += 1
                total_raw += 1

            # E1 cells (only κ=200)
            if df_e1_k is not None:
                if use_gpu:
                    e1_rows = compute_e1_cells_gpu(
                        gd, w_cpu, rho_j, groups, D,
                        F_mm_site_gpu, F_mm_trios_gpu, w0=w0,
                    )
                else:
                    e1_rows = []
                    for e1_name in ["M", "B", "W", "V"]:
                        A_j  = np.asarray(e1_amps[e1_name], dtype=np.float64)
                        sc   = (X_mm * (w_cpu * A_j)).sum(1)
                        tidx = optimal_selector(sc, trios)
                        f_grd = (F_mm_site[greedy_selector(sc, D)[0]] +
                                 F_mm_site[greedy_selector(sc, D)[1]] +
                                 F_mm_site[greedy_selector(sc, D)[2]])
                        q2_opt = 0 if check_dominated_raw(F_mm_trios, F_mm_trios[tidx]) else 1
                        q2_grd = 0 if check_dominated_raw(F_mm_trios, f_grd) else 1
                        e1_rows.append({"e1_cell": e1_name, "Q2_opt": q2_opt,
                                        "Q2_grd": q2_grd})
                for r in e1_rows:
                    e1_row = df_e1_k[
                        (df_e1_k["draw"] == di) & (df_e1_k["e1_cell"] == r["e1_cell"])
                    ]
                    if e1_row.empty:
                        raise RuntimeError(
                            f"Gate 3 FAIL: κ=200 draw {di} E1-{r['e1_cell']} missing"
                        )
                    exp_e1 = int(e1_row["Q2_opt"].values[0])
                    if r["Q2_opt"] != exp_e1:
                        print(f"  FAIL κ=200 draw {di} E1-{r['e1_cell']}: "
                              f"got {r['Q2_opt']} exp {exp_e1}", flush=True)
                        n_fail += 1
                    total_e1 += 1

        print(f"    κ={kappa:4d} OK ({n_fail} fails so far)", flush=True)

    # ── κ=∞ (1 draw — deterministic w0) ─────────────────────────────────────
    print(f"  κ=∞: 1 draw × 8 raw + 4 E1...", flush=True)
    w_inf = w0 / w0.sum()

    if use_gpu:
        raw_inf, F_mm_trios_inf, F_mm_site_inf = compute_q2_all_cells_gpu(gd, w_inf, D)
        e1_inf = compute_e1_cells_gpu(
            gd, w_inf, rho_j, groups, D, F_mm_site_inf, F_mm_trios_inf, w0=w0
        )
    else:
        F_mm_site_inf  = compute_group_objectives(X_mm, w_inf, A_ones_cpu, groups)
        F_mm_trios_inf = compute_trio_objectives(F_mm_site_inf, trios)
        raw_inf = compute_q2_all_cells(X_mm, w_inf, A_ones_cpu, groups,
                                       trios, D, scorers_cpu)
        e1_inf = []
        for e1_name in ["M", "B", "W", "V"]:
            A_j  = np.asarray(e1_amps[e1_name], dtype=np.float64)
            sc   = (X_mm * (w_inf * A_j)).sum(1)
            tidx = optimal_selector(sc, trios)
            trio_grd = greedy_selector(sc, D)
            f_grd = sum(F_mm_site_inf[trio_grd[i]] for i in range(3))
            q2_opt = 0 if check_dominated_raw(F_mm_trios_inf, F_mm_trios_inf[tidx]) else 1
            q2_grd = 0 if check_dominated_raw(F_mm_trios_inf, f_grd) else 1
            e1_inf.append({"e1_cell": e1_name, "Q2_opt": q2_opt, "Q2_grd": q2_grd})

    df_raw_inf = df_raw[df_raw["kappa"] == np.inf]
    df_e1_inf  = df_e1[df_e1["kappa"] == np.inf].sort_values("e1_cell")

    if len(df_raw_inf) != 1:
        raise RuntimeError(
            f"Gate 3 FAIL: expected 1 κ=∞ raw row, got {len(df_raw_inf)}"
        )
    for cell in CELLS_8:
        got = raw_inf[cell]
        exp = int(df_raw_inf[cell].values[0])
        if got != exp:
            print(f"  FAIL κ=∞ {cell}: got {got} exp {exp}", flush=True)
            n_fail += 1
        total_raw += 1

    for r in e1_inf:
        e1_row = df_e1_inf[df_e1_inf["e1_cell"] == r["e1_cell"]]
        if e1_row.empty:
            raise RuntimeError(
                f"Gate 3 FAIL: κ=∞ E1-{r['e1_cell']} missing from {e1_csv.name}"
            )
        exp_e1 = int(e1_row["Q2_opt"].values[0])
        if r["Q2_opt"] != exp_e1:
            print(f"  FAIL κ=∞ E1-{r['e1_cell']}: got {r['Q2_opt']} exp {exp_e1}",
                  flush=True)
            n_fail += 1
        total_e1 += 1

    print(f"  κ=∞ OK", flush=True)

    if n_fail:
        raise RuntimeError(
            f"Gate 3 FAIL ({label}): {n_fail} mismatches. "
            f"({total_raw} raw + {total_e1} E1 cells checked)"
        )

    print(
        f"  Gate 3 ({label}): {total_raw} raw + {total_e1} E1 cells ALL MATCH "
        f"({total_raw + total_e1} total)\n",
        flush=True,
    )
    return trio_indices_k200


def evaluate_branch(branch: str, raw_csv: Path, e1_csv: Path, cond: dict,
                    branch_regret: dict = None) -> dict:
    """Evaluate all S predictions for one branch.
    branch_regret: dict from compute_value_regret_santiago(), required for S6/S7.
    Raises RuntimeError if branch_regret is absent and S6 is testable.
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
        k6[str(int(k))] = round(_agg_pooled3(grp), 2)
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
        zeros_e1b      = np.zeros_like(R_e1b_pp)
        # SeedSequence(20261104): reproducible seeds for S7a/S7b (spawn index 0/1)
        from numpy.random import SeedSequence as _SS7
        _ss7 = _SS7(20261104).spawn(2)
        md7a, lo7a, hi7a, p7a = _bs_ci(R_e1b_pp, zeros_e1b, seed=_ss7[0])
        # "Zero" = trio_sel == t* (SAW/mm/opt trio). In production code,
        # R == 0.0 exactly iff opt_e1b_idx == opt_mm_idx (integer argmax).
        # Threshold 1e-12 pp is a guard; min non-zero R is 0.042616 pp >> 1e-12.
        # DEV-FOGO-E1B-001: 177/500 Fogo draws have trio==t* (35.4%).
        n_nonzero_e1b  = regret.get("summary", {}).get("n_nonzero_e1b_trio")
        if n_nonzero_e1b is None:
            # fallback: count from R (equivalent in production code)
            n_nonzero_e1b = int((R_e1b_pp > 1e-12).sum())
        frac_zero_e1b  = round(float((R_e1b_pp < 1e-12).mean()), 4)  # frac trio==t*
        # PRESPEC pass criterion: testable AND CI_lo > 0 (no n_nonzero condition).
        # n_nonzero is diagnostic only — reported but not part of the verdict.
        # The eval-r-spec.md ">=4" was post-data, not pre-registered.
        s7a_pass   = testable_s7a and lo7a > 0
        s7a_status = "CONFIRMED" if s7a_pass else "NOT CONFIRMED"
    else:
        md7a = lo7a = hi7a = p7a = None
        n_nonzero_e1b = None
        frac_zero_e1b = None
        s7a_pass      = False
        s7a_status    = "NOT CONFIRMED (no regret data)"
    if e1.empty and len(R_e1b_pp) == 0:
        raise RuntimeError(
            f"S7a evaluation for {branch} requires E1-B regret data."
        )
    s7a = {"prediction": "S7a",
           "text": "R(E1-B,opt) > 0, 95% CI excludes 0 (value regret, E1-B vs SAW/mm/opt)",
           "condition": f"TV_B>=0.05: {cond['TV_B']:.3f} {'✓' if testable_s7a else '✗'}",
           "testable": testable_s7a,
           "R_E1B_opt_mean_pp": round(float(R_e1b_pp.mean()), 2) if len(R_e1b_pp)==500 else None,
           "R_E1B_opt_mean_diff_pp": round(float(md7a), 2) if md7a is not None else None,
           "ci": [round(lo7a,2), round(hi7a,2)] if lo7a is not None else None,
           "p_one_sided": round(float(p7a), 4) if p7a is not None else None,
           "n_nonzero_e1b": n_nonzero_e1b,
           "frac_R_e1b_zero": frac_zero_e1b,
           "result": s7a_status,
           "note": ("PRESPEC criterion: testable AND CI_lo > 0. "
                    "n_nonzero reported as diagnostic (not part of verdict). "
                    "See PRESPEC_SANTIAGO.md S7a.")}

    # ── S7b ─────────────────────────────────────────────────────────────────
    # R(E1-B,opt) < R(E1-W,opt) | TV_B ≥ 0.05 AND TV_W ≥ 0.05
    testable_s7b = cond["TV_B"] >= 0.05 and cond["TV_W"] >= 0.05
    R_e1w_pp = np.array(regret.get("R_e1w_opt_pp") or [])
    if (testable_s7b and len(R_e1b_pp) == 500 and len(R_e1w_pp) == 500
            and not np.isnan(R_e1b_pp).any() and not np.isnan(R_e1w_pp).any()):
        n = min(len(R_e1b_pp), len(R_e1w_pp))
        _, lo7b, hi7b, _ = _bs_ci(R_e1w_pp[:n], R_e1b_pp[:n], seed=_ss7[1])
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
    """K6 Fogo gate: Agg_pooled3 at 6 stochastic κ from e7_raw.csv.

    e7_raw.csv uses long format with 'alpha' column (= κ) and agg/norm/mont per cell.
    mc_unified_raw.csv SHA is verified for Stage 1 integrity but not used for K6 values.
    TOL=0.05 pp. κ=∞ is theoretical (0.0); no stochastic data in e7_raw.csv.
    """
    import hashlib as _hl
    E7_CSV = ROOT / "results" / "e7" / "e7_raw.csv"
    MC_CSV = ROOT / "results" / "unified" / "mc_unified_raw.csv"

    # SHA verify mc_unified_raw.csv (Stage 1 integrity)
    if not MC_CSV.exists():
        raise RuntimeError(f"K6 gate FAIL: {MC_CSV} not found.")
    sha_mc = _hl.sha256(MC_CSV.read_bytes()).hexdigest()[:8]
    if sha_mc != SHA_MC_UNIFIED:
        raise RuntimeError(
            f"mc_unified_raw.csv SHA mismatch: expected {SHA_MC_UNIFIED}, got {sha_mc}"
        )
    print(f"  mc_unified_raw.csv SHA: {sha_mc} OK", flush=True)

    if not E7_CSV.exists() or E7_CSV.stat().st_size < 100:
        raise RuntimeError(
            f"K6 gate FAIL: {E7_CSV} not found or empty. Athena required."
        )

    # K6_FOGO_EXPECTED is a module constant — tests can monkeypatch it.
    # _agg_pooled3_long is the shared aggregation function (long format, e7_raw.csv).
    TOL = 0.05

    df_e7 = pd.read_csv(E7_CSV)
    if "alpha" not in df_e7.columns:
        raise RuntimeError("K6 gate FAIL: e7_raw.csv missing 'alpha' column. "
                           "Expected long-format with alpha=κ.")

    print("=== K6 Fogo gate (Agg_pooled3, 3 informative cells, TOL=0.05) ===",
          flush=True)

    for kappa, expected in sorted(K6_FOGO_EXPECTED.items()):
        grp = df_e7[df_e7["alpha"] == kappa]
        if grp.empty:
            raise RuntimeError(f"K6 gate FAIL: alpha={kappa} not in e7_raw.csv")

        got  = round(_agg_pooled3_long(grp), 2)
        diff = abs(got - expected)
        ok   = "PASS" if diff <= TOL else "FAIL"
        print(
            f"  alpha={kappa:5d}: expected {expected:+6.2f},"
            f" got {got:+7.2f}, diff={diff:.3f} [{ok}]",
            flush=True,
        )
        if ok == "FAIL":
            raise RuntimeError("K6 gate FAILED — Agg_pooled3 mismatch. Fix formula before tagging.")

    # κ=∞: MANDATORY. Read Q2 values from macros_kappa_inf.tex (SHA verified).
    # Generated by scripts/kappa_inf.py (kappa_inf.py log: commit 777e289 2026-11-02,
    # from restore ef12e7c 2026-10-27, confirmed working in 80574e5 2026-10-27).
    # Full SHA-256: 9c086c026d5846529fc938f5671e6756f6e6d5e4e1c9833f5ed12d93e3ccdbee
    SHA_KAPPA_INF = "9c086c026d5846529fc938f5671e6756f6e6d5e4e1c9833f5ed12d93e3ccdbee"
    KINF_TEX = ROOT / "macros" / "macros_kappa_inf.tex"

    if not KINF_TEX.exists():
        raise RuntimeError(
            f"K6 gate FAIL: {KINF_TEX} not found.\n"
            "Run scripts/kappa_inf.py to generate it, record SHA in DEV-K6."
        )
    sha_kinf = _hl.sha256(KINF_TEX.read_bytes()).hexdigest()
    if sha_kinf != SHA_KAPPA_INF:
        raise RuntimeError(
            f"K6 gate FAIL: macros_kappa_inf.tex SHA mismatch.\n"
            f"  expected {SHA_KAPPA_INF}\n  got      {sha_kinf}"
        )

    # Parse Q2 values and pass through _agg_pooled3() — SAME function as S4 evaluation.
    # Macro names from kappa_inf.py: QtwoInf[S/T][Mi/Ve][Gre/Opt]
    import re as _re
    tex = KINF_TEX.read_text(encoding="utf-8")

    def _q2inf(agg, norm, mont):
        prefix = "S" if agg == "saw" else "T"
        nm2    = norm.capitalize()[:2]
        mt2    = mont.capitalize()[:3]
        m = _re.search(r"\\newcommand\{\\QtwoInf" + prefix + nm2 + mt2 + r"\}\{([0-9]+)\}",
                       tex)
        if not m:
            raise RuntimeError(f"K6 gate FAIL: macro QtwoInf{prefix}{nm2}{mt2} not found")
        return float(m.group(1)) / 100.0  # convert to [0,1] for _agg_pooled3

    # Build single-row DataFrame matching mc_*_raw.csv wide format → _agg_pooled3
    import pandas as _pd
    df_inf_row = _pd.DataFrame([{
        "SAW_mm_grd":     _q2inf("saw",    "minmax", "greedy"),
        "SAW_mm_opt":     _q2inf("saw",    "minmax", "optimal"),
        "SAW_vec_grd":    _q2inf("saw",    "vector", "greedy"),
        "SAW_vec_opt":    _q2inf("saw",    "vector", "optimal"),
        "TOPSIS_mm_grd":  _q2inf("topsis", "minmax", "greedy"),
        "TOPSIS_mm_opt":  _q2inf("topsis", "minmax", "optimal"),
        "TOPSIS_vec_grd": _q2inf("topsis", "vector", "greedy"),
        "TOPSIS_vec_opt": _q2inf("topsis", "vector", "optimal"),
    }])
    # _agg_pooled3 uses [0,1] fractions × 100 internally — pass as-is
    got_inf   = round(_agg_pooled3(df_inf_row), 2)
    diff_inf  = abs(got_inf - 0.0)
    ok_inf    = "PASS" if diff_inf <= TOL else "FAIL"
    print(
        f"  kappa=  inf: expected  +0.00, got {got_inf:+7.2f}, diff={diff_inf:.3f} [{ok_inf}]"
        f"  (from macros_kappa_inf.tex SHA:{sha_kinf[:8]})",
        flush=True,
    )
    if ok_inf == "FAIL":
        raise RuntimeError(f"K6 gate κ=∞ FAILED: got {got_inf}, expected 0.0")

    print("  K6 gate: ALL 7 VALUES PASS\n", flush=True)
    return True


def gate_1_fogo_oracle() -> bool:
    """Gate 1: Call compute_value_regret() on Fogo data; compare draw-by-draw.

    NON-CIRCULAR: calls compute_value_regret() from santiago_eval_core (no _fogo_override)
    and compares its per-draw output against SHA-verified oracle files.

    FAILS if Fogo modules are not importable (no Windows fallback).
    FAILS if any per-draw R value differs > 1e-12 from oracle.
    FAILS if n_e1b_zero count != 177 (trio==t* criterion = 35.4% of 500 draws; DEV-FOGO-E1B-001).

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

    # ── E1-B and E1-W per-draw comparison against oracle CSV ─────────────────
    # Oracle: results/regret/e1_oracle_per_draw.csv (generated by
    #   diagnostics/e1_oracle_per_draw.py with SHA-verified _compute_e1_regret.py)
    # Comparison: |R_our_pp/100 - R_oracle_pp/100| <= TOL_DRAW = 1e-12 (fraction)
    # Zero criterion: trio_eq_tstar from oracle CSV (semantic: selected trio == t*)
    SHA_E1_ORACLE_CSV = "913396cea6a6288836783c9bc02a5f7a898b70643dd2788a5d0780b42155b56c"
    E1_ORACLE_CSV     = ROOT / "results" / "regret" / "e1_oracle_per_draw.csv"
    if not E1_ORACLE_CSV.exists():
        raise RuntimeError(
            f"Gate 1 FAIL: {E1_ORACLE_CSV} not found. "
            "Run: MCDM_DATA_DIR=/home/julioazancort/scratch/mcdm "
            ".venv/bin/python3 diagnostics/e1_oracle_per_draw.py"
        )
    sha_e1csv = _hl.sha256(E1_ORACLE_CSV.read_bytes()).hexdigest()
    if sha_e1csv != SHA_E1_ORACLE_CSV:
        raise RuntimeError(
            f"Gate 1 FAIL: e1_oracle_per_draw.csv SHA mismatch.\n"
            f"  expected {SHA_E1_ORACLE_CSV}\n  got      {sha_e1csv}"
        )
    print(f"  e1_oracle_per_draw.csv SHA: OK ({sha_e1csv[:8]})", flush=True)

    df_e1_or = pd.read_csv(E1_ORACLE_CSV)
    for e1_cell, r_key in [("B", "R_e1b_opt_pp"), ("W", "R_e1w_opt_pp")]:
        cell_or   = df_e1_or[(df_e1_or["cell"] == e1_cell) &
                              (df_e1_or["mont"] == "optimal")].sort_values("draw")
        R_or_frac = cell_or["R_pp"].values / 100.0       # fraction
        R_our_frac = np.array(result[r_key]) / 100.0     # fraction (R_pp/100)
        diff_e1 = np.abs(R_our_frac - R_or_frac)
        if diff_e1.max() > TOL_DRAW:
            raise RuntimeError(
                f"Gate 1 FAIL: E1-{e1_cell} per-draw max diff = {diff_e1.max():.3e} "
                f"> {TOL_DRAW}."
            )
        print(f"  E1-{e1_cell} per-draw: max diff={diff_e1.max():.2e} PASS", flush=True)

    # n_e1b_zero: READ FROM oracle CSV (trio_eq_tstar) — not hardcoded
    b_opt_or      = df_e1_or[(df_e1_or["cell"] == "B") &
                              (df_e1_or["mont"] == "optimal")].sort_values("draw")
    n_e1b_zero_or = int(b_opt_or["trio_eq_tstar"].sum())
    print(f"  n_e1b_zero oracle (trio==t*): {n_e1b_zero_or}/500 = "
          f"{n_e1b_zero_or/5:.1f}%", flush=True)

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

    # ── Exact count: oracle rerun gives 177/500 = 35.4% ─────────────────────
    # DEV-EVALR ER-7: macro \RegretEoneBfracZero{28} (28% = 140/500) was wrong.
    # _count_e1b_zeros.py on Athena (commit 56dc283) shows 177/500 = 35.4%
    # Zeros table using _compute_e1_regret.py logic (SHA verified, V_range from
    # regret_perdraw.csv, same as oracle):
    #   R==0.0 exact (batch V_max):         101/500 — floating-point batch artifact
    #   round(R,2)==0:                       177/500
    #   opt_e1b==opt_mm (semantic, same trio): 177/500
    # EVAL-R uses sequential V_all (V_max and V_sel from same array):
    #   R_current==0.0 exact = opt_e1b==opt_mm = 177/500 = 35.4%
    # The 177 is the semantically correct count (all match: same trio criterion).
    # The 28% (140) came from a 2026-10-25 run with different V_range (mean R=72pp),
    # superseded. Diff between 101 and 177 is batch vs sequential float64 artifact.
    # n_e1b_zero: read from oracle CSV (trio_eq_tstar criterion — not hardcoded)
    n_e1b_zero = summ.get("n_e1b_zero_exact")
    if n_e1b_zero != n_e1b_zero_or:
        raise RuntimeError(
            f"Gate 1 FAIL: n_e1b_zero = {n_e1b_zero} != {n_e1b_zero_or} "
            "(oracle trio==t* criterion; see diagnostics/README.md, DEV-SANT-EVALR-001 ER-7)"
        )
    print(f"  n_e1b_zero: {n_e1b_zero}/500 = 35.4% PASS", flush=True)
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
    import hashlib as _hl, subprocess as _sp
    _git_sha = _sp.check_output(["git","rev-parse","HEAD"], cwd=ROOT).decode().strip()
    _repo_clean = not _sp.check_output(["git","status","--porcelain"], cwd=ROOT).decode().strip()
    with open(out, "w") as f:
        json.dump({"S-T": st_res, "S-N": sn_res,
                   "B_BOOT": B_BOOT, "elapsed_s": round(time.time()-t0, 1),
                   "provenance": {
                       "script": "evaluate_santiago_predictions.py",
                       "git_commit": _git_sha,
                       "repo_clean": bool(_repo_clean),
                       "sealed_csvs": {
                           fn: _hl.sha256((SEALED/fn).read_bytes()).hexdigest()
                           for fn in SHA_SEALED
                       },
                   }}, f, indent=2)
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
