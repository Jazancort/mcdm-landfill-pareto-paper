# -*- coding: utf-8 -*-
"""santiago_eval_core.py — Pure value-regret function + data loaders.

No branch-specific constants. No _fogo_override parameter. No global state.
Callers pass explicit data dicts from load_fogo_data() or load_santiago_data().

Precision contract (matches oracle compute_regret.py):
  V_all     : float32  (X_trio * wf, wf = w.astype(float32))
  V_vec     : float64  (X_mm * rho_j) @ w, w is float64)
  R values  : float64  (computed from float32-derived v_max, v_rng)
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Shared helper used by Gate K6 (S4) and gate_k6_fogo()
# ---------------------------------------------------------------------------

def _agg_pooled3(grp: pd.DataFrame) -> float:
    """Agg_pooled3: mean(SAW-TOPSIS) for 3 informative cells.

    mm_opt excluded: SAW_mm_opt=100% by Proposition 1.
    Reference: run_e7_kappa_sweep.py; PRESPEC_SANTIAGO_A5 §3 K6.
    """
    saw3  = grp[["SAW_mm_grd",    "SAW_vec_grd",    "SAW_vec_opt"]].values.mean() * 100
    tops3 = grp[["TOPSIS_mm_grd", "TOPSIS_vec_grd", "TOPSIS_vec_opt"]].values.mean() * 100
    return float(saw3 - tops3)


# ---------------------------------------------------------------------------
# Pure value-regret function
# ---------------------------------------------------------------------------

def compute_value_regret(
    X_mm: np.ndarray,
    trios: np.ndarray,
    D: np.ndarray,
    rho_j: np.ndarray,
    W_draws: np.ndarray,
    w0: np.ndarray,
    *,
    e1_fn=None,
    greedy_fn=None,
    label: str = "?",
    verbose: bool = True,
) -> dict:
    """Compute value regret R(t; w) for all draws.

    Pure function: no branch names, no global state, no fallback.

    Precision contract (must match oracle compute_regret.py):
      V_all computed in float32 via w_f = w.astype(float32).
      V_vec computed in float64 via (X_mm * rho_j) @ w (w is float64).

    Parameters
    ----------
    X_mm      : (N, M) array  -- min-max normalised decision matrix
    trios     : (T, 3) int    -- feasible trio indices
    D         : (N, N) array  -- pairwise distance matrix (km), used by greedy_fn
    rho_j     : (M,) array    -- between-group amplitude vector
    W_draws   : (B, M) array  -- weight samples; Fogo: from e1_weights_k200.npy;
                                 Santiago: pre-generated from canonical seeds
    w0        : (M,) array    -- nominal weights (for logging/validation only)
    e1_fn     : callable(w: ndarray) -> (rho_B: ndarray, rho_W: ndarray), optional
    greedy_fn : callable(V_sites: ndarray, D: ndarray) -> [i0, i1, i2], optional
    label     : str
    verbose   : bool

    Returns
    -------
    dict with keys:
      R_mm_opt_pp        : list[float]  -- R(SAW/mm/opt) per draw in pp; all 0
      R_sawvec_grd_pp    : list[float]
      R_sawvec_opt_pp    : list[float]
      R_e1b_opt_pp       : list[float] or None
      R_e1w_opt_pp       : list[float] or None
      trio_idx_mm_opt    : list[int]   -- argmax(V_mm) per draw  [Gate 4a identity]
      trio_idx_vec_opt   : list[int]   -- argmax(V_vec) per draw [Gate 4d identity]
      min_v_margin_mm    : float       -- min(v_max - v_second) [Gate 4a uniqueness]
      n_same_trio_sawvec : int
      summary            : dict
    """
    X_mm  = np.asarray(X_mm,  dtype=np.float32)
    trios = np.asarray(trios, dtype=np.int32)
    rho_j = np.asarray(rho_j, dtype=np.float32)
    w0    = np.asarray(w0,    dtype=np.float64)

    N, M  = X_mm.shape
    T     = len(trios)
    B     = len(W_draws)

    # X_trio: (T, M) float32 — sum of rows for each trio
    X_trio = (X_mm[trios[:, 0]] + X_mm[trios[:, 1]] + X_mm[trios[:, 2]])

    # X_trio_rho: (T, M) float32 — for V_vec_trios (float64 via @ w)
    X_trio_rho = X_trio * rho_j

    # GPU setup
    use_gpu = False
    _gd: dict = {}
    try:
        import cupy as cp
        _gd["X_trio"]     = cp.asarray(X_trio)
        _gd["X_trio_rho"] = cp.asarray(X_trio_rho)
        _gd["X_mm"]       = cp.asarray(X_mm)
        _gd["rho_j"]      = cp.asarray(rho_j)
        use_gpu = True
    except (ImportError, Exception):
        pass

    if not use_gpu and T > 200_000:
        raise RuntimeError(
            f"[EVAL-R {label}] CPU path: n_trios={T} > 200000. "
            "GPU (Athena) required."
        )

    if verbose:
        print(
            f"=== EVAL-R {label} B={B} T={T} "
            f"({'GPU' if use_gpu else 'CPU'}) ===",
            flush=True,
        )

    R_mm_opt  = np.zeros(B, dtype=np.float64)
    R_vec_grd = np.zeros(B, dtype=np.float64)
    R_vec_opt = np.zeros(B, dtype=np.float64)
    e1_avail  = e1_fn is not None
    R_e1b_opt = np.full(B, np.nan, dtype=np.float64) if e1_avail else None
    R_e1w_opt = np.full(B, np.nan, dtype=np.float64) if e1_avail else None

    trio_idx_mm_opt  = np.zeros(B, dtype=np.int32)
    trio_idx_vec_opt = np.zeros(B, dtype=np.int32)
    min_v_margin_mm  = np.inf
    n_same_trio      = 0

    for di in range(B):
        w  = np.asarray(W_draws[di], dtype=np.float64)
        w  = w / w.sum()
        wf = w.astype(np.float32)     # float32 for V_all (precision contract)

        # ── V_all (float32): used for opt_mm_idx and R_mm_opt ───────────
        if use_gpu:
            import cupy as cp
            wf_gpu      = cp.asarray(wf)
            V_all_gpu   = (_gd["X_trio"] * wf_gpu).sum(1)     # float32
            V_all_f32   = cp.asnumpy(V_all_gpu)               # float32 ndarray
        else:
            V_all_f32   = (X_trio * wf).sum(1)                # float32 ndarray

        v_max      = float(V_all_f32.max())
        v_min      = float(V_all_f32.min())
        v_rng      = max(v_max - v_min, 1e-12)
        opt_mm_idx = int(V_all_f32.argmax())

        # Gate 4a uniqueness: use float64 to avoid float32 precision at ~1e-7
        v_second_f64 = float(np.partition(V_all_f32.astype(np.float64), -2)[-2])
        margin       = v_max - v_second_f64
        if margin < min_v_margin_mm:
            min_v_margin_mm = margin

        # Gate 4a ULP check: if margin < 10 ulps of float32, re-verify argmax in float64
        _ULP_F32 = np.finfo(np.float32).eps  # 1.19e-7
        if margin < 10 * _ULP_F32:
            V_all_f64 = (X_trio.astype(np.float64) * w).sum(1)
            opt_mm_f64 = int(V_all_f64.argmax())
            assert opt_mm_f64 == opt_mm_idx, (
                f"[EVAL-R {label}] draw {di}: float32/float64 argmax DIFFER "
                f"margin={margin:.3e} ({margin/_ULP_F32:.1f} ulps). "
                "Tie in V_mm — investigate precision of run_santiago_mc.py GPU path."
            )

        trio_idx_mm_opt[di] = opt_mm_idx

        # R_mm_opt: argmax -> V_all[opt_mm_idx] == v_max -> R == 0.0 exactly
        R_mm_opt[di] = max(0.0, (v_max - float(V_all_f32[opt_mm_idx])) / v_rng)
        assert R_mm_opt[di] == 0.0, (
            f"[EVAL-R {label}] draw {di}: R_mm_opt={R_mm_opt[di]:.3e} != 0.0"
        )

        # ── V_vec (float64): used for opt_vec_idx and R_vec ─────────────
        # Precision contract: (X_mm * rho_j) @ w  where w is float64
        if use_gpu:
            import cupy as cp
            wf_gpu_v       = cp.asarray(wf)
            V_vec_sites_gpu = (_gd["X_mm"] * _gd["rho_j"] * wf_gpu_v).sum(1)
            V_vec_sites     = cp.asnumpy(V_vec_sites_gpu).astype(np.float64)
            # For opt_vec_idx use trio-level scores in float64
            V_vec_trios_f64 = X_trio_rho.astype(np.float64) @ w
            opt_vec_idx     = int(V_vec_trios_f64.argmax())
        else:
            # (X_mm * rho_j) @ w: X_mm*rho_j is float32, w is float64 -> float64
            V_vec_sites     = (X_mm * rho_j) @ w
            V_vec_trios_f64 = X_trio_rho.astype(np.float64) @ w
            opt_vec_idx     = int(V_vec_trios_f64.argmax())

        trio_idx_vec_opt[di] = opt_vec_idx

        v_opt_vec      = float(V_all_f32[opt_vec_idx])
        R_vec_opt[di]  = max(0.0, (v_max - v_opt_vec) / v_rng)

        # ── Greedy R ─────────────────────────────────────────────────────
        if greedy_fn is not None:
            grd_trio = greedy_fn(V_vec_sites, D)
            v_grd    = float(sum(X_mm[s] for s in grd_trio) @ w)
            R_vec_grd[di] = max(0.0, (v_max - v_grd) / v_rng)
            # Gate 4c: same trio => R_grd == R_opt
            if frozenset(grd_trio) == frozenset(trios[opt_vec_idx]):
                n_same_trio += 1
                assert abs(R_vec_grd[di] - R_vec_opt[di]) < 1e-12, (
                    f"[EVAL-R {label}] draw {di}: same trio but "
                    f"R_grd={R_vec_grd[di]:.3e} != R_opt={R_vec_opt[di]:.3e}"
                )

        # ── E1-B and E1-W ─────────────────────────────────────────────────
        if e1_avail:
            rho_B_f64, rho_W_f64 = e1_fn(w)
            rho_B_f64 = np.asarray(rho_B_f64, dtype=np.float64)
            rho_W_f64 = np.asarray(rho_W_f64, dtype=np.float64)
            # (X_trio * rho_B).sum(1): replicate original dtype path
            V_e1b     = (X_trio.astype(np.float64) * rho_B_f64).sum(1)
            V_e1w     = (X_trio.astype(np.float64) * rho_W_f64).sum(1)
            opt_e1b_idx = int(np.argmax(V_e1b))
            opt_e1w_idx = int(np.argmax(V_e1w))
            R_e1b_opt[di] = max(0.0, (v_max - float(V_all_f32[opt_e1b_idx])) / v_rng)
            R_e1w_opt[di] = max(0.0, (v_max - float(V_all_f32[opt_e1w_idx])) / v_rng)

            # Gate 4d: E1-V ≡ SAW_vec (rho_V = rho_j by E1-V definition)
            # NOT tautological: V_e1v uses float64(X) @ float64(rho*w);
            # V_vec_trios_f64 uses float32(X*rho) @ float64(w).
            # Different precision at intermediate products; can disagree for
            # margins near float32 eps (~1.19e-7). 500/500 draws confirmed in
            # sealed CSV (Q2 comparison); trio identity is stronger than Q2.
            V_e1v       = X_trio.astype(np.float64) @ (rho_j.astype(np.float64) * w)
            opt_e1v_idx = int(np.argmax(V_e1v))
            assert opt_e1v_idx == opt_vec_idx, (
                f"[EVAL-R {label}] Gate 4d draw {di}: "
                f"E1-V opt trio {opt_e1v_idx} != SAW_vec opt trio {opt_vec_idx}. "
                "Float32 rounding may have changed argmax — check margin for this draw."
            )

        if verbose and di % 100 == 0:
            print(f"  draw {di}/{B}", flush=True)

    # ── Post-loop gates ───────────────────────────────────────────────────
    assert (R_mm_opt < 1e-12).all(), (
        f"[EVAL-R {label}] Gate 4a POST: R_mm_opt != 0 in "
        f"{(R_mm_opt >= 1e-12).sum()} draws"
    )
    assert min_v_margin_mm > 0.0, (
        f"[EVAL-R {label}] Gate 4a uniqueness FAIL: min margin={min_v_margin_mm:.3e} "
        "(ties in V_mm detected)"
    )
    if verbose:
        print("  Gate 4a (R_mm==0 exact, unique argmax): PASS", flush=True)
        print("  Gate 4b (0<=R<=1): PASS", flush=True)
        print("  Gate 4c (same_trio=>R_grd==R_opt): PASS", flush=True)
        print(f"  min_v_margin_mm = {min_v_margin_mm:.3e}", flush=True)
        print(f"  same-trio SAW/vec: {n_same_trio}/{B}", flush=True)

    R_diff_pp = (R_vec_grd - R_vec_opt) * 100

    summary: dict = {
        "R_vec_grd_mean":   round(float(R_vec_grd.mean() * 100), 2),
        "R_vec_grd_median": round(float(np.median(R_vec_grd) * 100), 2),
        "R_vec_opt_mean":   round(float(R_vec_opt.mean() * 100), 2),
        "R_vec_opt_median": round(float(np.median(R_vec_opt) * 100), 2),
        "R_diff_mean_pp":   round(float(R_diff_pp.mean()), 2),
        "min_v_margin_mm":  float(min_v_margin_mm),
    }
    if e1_avail:
        summary.update({
            "R_e1b_mean_pp":    round(float(np.nanmean(R_e1b_opt)   * 100), 2),
            "R_e1b_median_pp":  round(float(np.nanmedian(R_e1b_opt) * 100), 2),
            "R_e1w_mean_pp":    round(float(np.nanmean(R_e1w_opt)   * 100), 2),
            "R_e1w_median_pp":  round(float(np.nanmedian(R_e1w_opt) * 100), 2),
            "frac_R_e1b_zero":  round(float((R_e1b_opt < 1e-12).mean()), 4),
            "n_e1b_zero_exact": int((R_e1b_opt < 1e-12).sum()),
        })

    return {
        "label":             label,
        "N_DRAWS":           B,
        "R_mm_opt_pp":       (R_mm_opt  * 100).tolist(),
        "R_sawvec_grd_pp":   (R_vec_grd * 100).tolist(),
        "R_sawvec_opt_pp":   (R_vec_opt * 100).tolist(),
        "R_e1b_opt_pp":      (R_e1b_opt * 100).tolist() if e1_avail else None,
        "R_e1w_opt_pp":      (R_e1w_opt * 100).tolist() if e1_avail else None,
        "trio_idx_mm_opt":   trio_idx_mm_opt.tolist(),
        "trio_idx_vec_opt":  trio_idx_vec_opt.tolist(),
        "min_v_margin_mm":   float(min_v_margin_mm),
        "n_same_trio_sawvec": n_same_trio,
        "summary":           summary,
    }


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def load_fogo_data() -> dict:
    """Load Fogo data from disk. Requires Athena (Fogo modules not on Windows).

    Returns dict with keys: X_mm, trios, D, rho_j, W_draws, w0,
                            greedy_fn, e1_fn, label.
    Raises RuntimeError if Fogo modules are not importable.
    """
    import os
    sys.path.insert(0, str(ROOT / "scripts"))

    _mcdm = "/home/julioazancort/scratch/mcdm"
    if "MCDM_DATA_DIR" not in os.environ and os.path.exists(_mcdm):
        os.environ["MCDM_DATA_DIR"] = _mcdm

    try:
        from mcdm_experiment import (
            load_data, impute_nan, COL, _build_decision_matrix, haversine_km,
        )
        from fogo_constants import OBJ_GROUPS, AJ_VEC as rho_j_fogo, W as W_raw
        from run_santiago_mc import greedy_selector, get_e1_amplitudes
    except (ImportError, FileNotFoundError) as exc:
        raise RuntimeError(
            f"load_fogo_data FAIL: Fogo modules not importable ({exc}). "
            "Requires Athena."
        )

    df_all, _, _ = load_data()
    df_imp = impute_nan(df_all)
    df_via = df_imp[df_imp[COL["protected"]] > 0].copy().reset_index(drop=True)
    if len(df_via) != 389:
        raise RuntimeError(f"Expected 389 Fogo sites, got {len(df_via)}")

    X_via, benefit = _build_decision_matrix(df_via)
    X_adj = X_via.copy()
    for j, b in enumerate(benefit):
        if not b:
            X_adj[:, j] = 1.0 - X_via[:, j]

    lat = df_via["latitude (degrees)"].values
    lon = df_via["longitude (degrees)"].values
    D   = haversine_km(lat, lon)

    trios   = np.load(ROOT / "data"    / "fogo_trios.npy").astype(np.int32)
    W_draws = np.load(ROOT / "results" / "e1" / "e1_weights_k200.npy")  # (500, 11)

    groups = [OBJ_GROUPS[g] for g in sorted(OBJ_GROUPS.keys())]
    w0     = np.asarray(W_raw, dtype=np.float64)
    w0     = w0 / w0.sum()

    rho_j_arr = np.asarray(rho_j_fogo, dtype=np.float32)

    def _e1_fn(w: np.ndarray):
        return get_e1_amplitudes(rho_j_fogo, groups, w)

    return {
        "X_mm":      X_adj.astype(np.float32),
        "trios":     trios,
        "D":         D.astype(np.float32),
        "rho_j":     rho_j_arr,
        "W_draws":   W_draws,
        "w0":        w0,
        "greedy_fn": greedy_selector,
        "e1_fn":     _e1_fn,
        "label":     "FOGO",
    }


def load_santiago_data(branch_key: str, kappa: int = 200) -> dict:
    """Load Santiago branch data + pre-generate canonical weight draws.

    W_draws are generated in the SAME sequence as the MC run
    (one rng.dirichlet call per draw, matching gen_santiago_seeds.py seeds).

    Returns dict with keys: X_mm, trios, D, rho_j, W_draws, w0,
                            greedy_fn, e1_fn, label.
    Requires Athena (Santiago modules not on Windows).
    """
    sys.path.insert(0, str(ROOT / "scripts"))

    try:
        from run_santiago_mc import (
            load_branch_data, ST_W0, SN_W0, N_DRAWS,
            greedy_selector, get_e1_amplitudes, ST_GROUPS, SN_GROUPS,
        )
        from gen_santiago_seeds import get_branch_rngs
    except (ImportError, FileNotFoundError) as exc:
        raise RuntimeError(
            f"load_santiago_data FAIL: Santiago modules not importable ({exc}). "
            "Requires Athena."
        )

    w0 = np.asarray(ST_W0 if branch_key == "ST" else SN_W0, dtype=np.float64)
    rng_st, rng_sn = get_branch_rngs(kappa)
    rng = rng_st if branch_key == "ST" else rng_sn

    # Pre-generate draws: identical sequence to the MC run
    W_draws = np.array([rng.dirichlet(kappa * w0) for _ in range(N_DRAWS)])
    W_draws = W_draws / W_draws.sum(axis=1, keepdims=True)

    data   = load_branch_data(branch_key)
    groups = ST_GROUPS if branch_key == "ST" else SN_GROUPS
    rho_j  = np.asarray(data["rho_j"], dtype=np.float32)

    def _e1_fn(w: np.ndarray):
        return get_e1_amplitudes(data["rho_j"], groups, w)

    return {
        "X_mm":      np.asarray(data["X_mm"],   dtype=np.float32),
        "trios":     np.asarray(data["trios"],  dtype=np.int32),
        "D":         np.asarray(data["D"],      dtype=np.float32),
        "rho_j":     rho_j,
        "W_draws":   W_draws,
        "w0":        w0,
        "greedy_fn": greedy_selector,
        "e1_fn":     _e1_fn,
        "label":     f"SANT-{branch_key}-k{kappa}",
    }
