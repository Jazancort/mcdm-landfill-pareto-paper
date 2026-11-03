# -*- coding: utf-8 -*-
"""santiago_eval_core.py — Pure value-regret function + data loaders.

No branch-specific constants. No _fogo_override parameter. No global state.
Callers pass explicit data dicts from load_fogo_data() or load_santiago_data().

Precision contract (matches oracle compute_regret.py and run_santiago_mc.py GPU path):
  All arrays kept as float64 (load_branch_data() returns float64 X_mm).
  TOL_DRAW = 1e-12 in Gate 1 is achievable because both paths use float64.
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

    Precision contract: float64 throughout (matches oracle compute_regret.py).
      X_mm stays float64 (load_branch_data returns float64).
      w (per-draw) is float64 (dirichlet samples are float64).
      V_all = X_trio @ w — float64.
      V_vec = X_trio @ (rho_j * w) — float64.

    Parameters
    ----------
    X_mm      : (N, M) float64  -- min-max normalised decision matrix
    trios     : (T, 3) int32    -- feasible trio indices
    D         : (N, N) float64  -- pairwise distance matrix (km)
    rho_j     : (M,) float64    -- between-group amplitude vector (E1-V)
    W_draws   : (B, M) float64  -- weight samples; Fogo: from e1_weights_k200.npy;
                                   Santiago: pre-generated from canonical seeds
    w0        : (M,) float64    -- fixed nominal AHP weights
    e1_fn     : callable() -> dict{"M","B","W","V"}, optional.
                Takes NO arguments. Returns E1 amplitude vectors (constant across
                draws; amplitudes computed from fixed w0 via get_e1_amplitudes).
                If None, E1 cells are omitted and the gate raises RuntimeError.
    greedy_fn : callable(V_sites: ndarray, D: ndarray) -> [i0, i1, i2], optional
    label     : str
    verbose   : bool

    Returns
    -------
    dict with keys:
      R_mm_opt_pp        : list[float]  -- R(SAW/mm/opt) per draw in pp; all 0
      R_sawvec_grd_pp    : list[float]
      R_sawvec_opt_pp    : list[float]
      R_e1b_opt_pp       : list[float] or None  (None only if e1_fn is None)
      R_e1w_opt_pp       : list[float] or None
      trio_idx_mm_opt    : list[int]   -- argmax(V_mm) per draw  [Gate 4a identity]
      trio_idx_vec_opt   : list[int]   -- argmax(V_vec) per draw [Gate 4d identity]
      min_v_margin_mm    : float       -- min(v_max - v_second) [Gate 4a uniqueness]
      n_same_trio_sawvec : int
      summary            : dict
    """
    X_mm  = np.asarray(X_mm,  dtype=np.float64)
    trios = np.asarray(trios, dtype=np.int32)
    rho_j = np.asarray(rho_j, dtype=np.float64)
    w0    = np.asarray(w0,    dtype=np.float64)

    # e1_fn is MANDATORY: missing it is a caller error, not a skip.
    if e1_fn is None:
        raise RuntimeError(
            f"[EVAL-R {label}] e1_fn is required — pass e1_fn from "
            "load_fogo_data() or load_santiago_data(). "
            "e1_fn() must return dict{{'M','B','W','V'}} of amplitude vectors."
        )

    T = len(trios)
    B = len(W_draws)

    # Pre-compute trio sums (float64)
    X_trio     = X_mm[trios[:, 0]] + X_mm[trios[:, 1]] + X_mm[trios[:, 2]]  # (T, M)
    X_trio_rho = X_trio * rho_j                                                 # (T, M)

    # GPU setup — X_mm is float64, preserved on GPU
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

    # E1 amplitudes — constant across draws (computed from fixed w0)
    # Mandatory: e1_fn is not None (checked above).
    e1_avail = True
    e1_amps  = e1_fn()  # {"M": A_M, "B": A_B, "W": A_W, "V": A_V} — no per-draw arg
    A_B = np.asarray(e1_amps["B"], dtype=np.float64)
    A_W = np.asarray(e1_amps["W"], dtype=np.float64)
    A_V = np.asarray(e1_amps["V"], dtype=np.float64)  # = rho_j by definition
    A_M = np.asarray(e1_amps["M"], dtype=np.float64)  # = ones by definition
    # Gate 4d pre-check: E1-V amplitude must equal rho_j (definition)
    assert np.allclose(A_V, rho_j, rtol=1e-12, atol=1e-15), (
        f"[EVAL-R {label}] Gate 4d PRE: E1-V amplitude A_V != rho_j. "
        "Check get_e1_amplitudes return."
    )
    # Gate 4e pre-check: E1-M amplitude must be ones (definition)
    assert np.allclose(A_M, np.ones_like(A_M), rtol=1e-12, atol=1e-15), (
        f"[EVAL-R {label}] Gate 4e PRE: E1-M amplitude A_M != ones."
    )
    # Precompute trio-level E1 amplitude matrices (float64)
    X_trio_e1b = X_trio * A_B   # (T, M) — E1-B
    X_trio_e1w = X_trio * A_W   # (T, M) — E1-W
    # Gate 4d: E1-V uses A_V from e1_fn(), NOT X_trio_rho directly.
    # X_trio_e1v = X_trio * A_V; must agree with X_trio_rho since A_V == rho_j.
    X_trio_e1v = X_trio * A_V   # (T, M) — E1-V: uses e1_fn()["V"] explicitly

    R_mm_opt  = np.zeros(B, dtype=np.float64)
    R_vec_grd = np.zeros(B, dtype=np.float64)
    R_vec_opt = np.zeros(B, dtype=np.float64)
    R_e1b_opt = np.full(B, np.nan, dtype=np.float64)
    R_e1w_opt = np.full(B, np.nan, dtype=np.float64)

    trio_idx_mm_opt  = np.zeros(B, dtype=np.int32)
    trio_idx_vec_opt = np.zeros(B, dtype=np.int32)
    min_v_margin_mm  = np.inf
    n_same_trio      = 0
    n_nonzero_e1b_trio = 0  # draws where opt_e1b_idx != opt_mm_idx (trio != t*)

    for di in range(B):
        w = np.asarray(W_draws[di], dtype=np.float64)
        w = w / w.sum()

        # ── V_mm (float64): used for opt_mm_idx and R_mm_opt ────────────
        if use_gpu:
            import cupy as cp
            w_gpu = cp.asarray(w)
            V_all_gpu = (_gd["X_trio"] * w_gpu).sum(1)   # float64 on GPU
            V_all     = cp.asnumpy(V_all_gpu)             # float64 ndarray
        else:
            V_all = (X_trio * w).sum(1)                   # float64 ndarray

        v_max      = float(V_all.max())
        v_min      = float(V_all.min())
        v_rng      = max(v_max - v_min, 1e-12)
        opt_mm_idx = int(V_all.argmax())

        # ULP check: argmax must be stable under float32 precision.
        # If float32 and float64 disagree, the winning margin is < ULP(float32),
        # meaning the result is not robust. This is Gate 4a ULP FAIL.
        opt_mm_f32 = int(V_all.astype(np.float32).argmax())
        if opt_mm_f32 != opt_mm_idx:
            raise RuntimeError(
                f"[EVAL-R {label}] Gate 4a ULP FAIL draw {di}: "
                f"float64 argmax={opt_mm_idx} != float32 argmax={opt_mm_f32}. "
                "SAW/mm margin too small for robust argmax."
            )

        # Gate 4a uniqueness: record smallest gap to second-best
        if T >= 2:
            v_second = float(np.partition(V_all, -2)[-2])
            margin   = v_max - v_second
            if margin < min_v_margin_mm:
                min_v_margin_mm = margin

        trio_idx_mm_opt[di] = opt_mm_idx

        # R_mm_opt: argmax -> V_all[opt_mm_idx] == v_max -> R == 0.0 exactly
        R_mm_opt[di] = max(0.0, (v_max - float(V_all[opt_mm_idx])) / v_rng)
        assert R_mm_opt[di] == 0.0, (
            f"[EVAL-R {label}] draw {di}: R_mm_opt={R_mm_opt[di]:.3e} != 0.0"
        )

        # ── V_vec (float64): used for opt_vec_idx and R_vec ─────────────
        if use_gpu:
            import cupy as cp
            V_vec_sites_gpu  = (_gd["X_mm"] * _gd["rho_j"] * w_gpu).sum(1)
            V_vec_sites      = cp.asnumpy(V_vec_sites_gpu)
            V_vec_trios      = (_gd["X_trio_rho"] * w_gpu).sum(1)
            opt_vec_idx      = int(cp.argmax(V_vec_trios))
        else:
            V_vec_sites = (X_mm * rho_j * w).sum(1)        # (N,)
            V_vec_trios = (X_trio_rho * w).sum(1)           # (T,) float64
            opt_vec_idx = int(V_vec_trios.argmax())

        trio_idx_vec_opt[di] = opt_vec_idx

        v_opt_vec     = float(V_all[opt_vec_idx])
        R_vec_opt[di] = max(0.0, (v_max - v_opt_vec) / v_rng)

        # ── Greedy R ─────────────────────────────────────────────────────
        if greedy_fn is not None:
            grd_trio      = greedy_fn(V_vec_sites, D)
            v_grd         = float(sum(X_mm[s] for s in grd_trio) @ w)
            R_vec_grd[di] = max(0.0, (v_max - v_grd) / v_rng)
            # Gate 4c: same trio => R_grd == R_opt
            if frozenset(grd_trio) == frozenset(trios[opt_vec_idx]):
                n_same_trio += 1
                assert abs(R_vec_grd[di] - R_vec_opt[di]) < 1e-12, (
                    f"[EVAL-R {label}] draw {di}: same trio but "
                    f"R_grd={R_vec_grd[di]:.3e} != R_opt={R_vec_opt[di]:.3e}"
                )

        # ── E1 (constant amplitudes, per-draw w) ────────────────────────
        if e1_avail:
            V_e1b = (X_trio_e1b * w).sum(1)     # (T,) float64 — E1-B
            V_e1w = (X_trio_e1w * w).sum(1)     # (T,) float64 — E1-W
            # Gate 4d: E1-V uses X_trio_e1v (= X_trio * A_V from e1_fn()["V"])
            # Must agree with V_vec_trios since A_V == rho_j (checked pre-loop).
            V_e1v = (X_trio_e1v * w).sum(1)     # (T,) float64 — E1-V (via e1_fn["V"])
            V_e1m = V_all                        # (T,) float64 — E1-M = SAW_mm

            opt_e1b_idx = int(np.argmax(V_e1b))
            opt_e1w_idx = int(np.argmax(V_e1w))
            opt_e1v_idx = int(np.argmax(V_e1v))
            opt_e1m_idx = int(np.argmax(V_e1m))

            R_e1b_opt[di] = max(0.0, (v_max - float(V_all[opt_e1b_idx])) / v_rng)
            R_e1w_opt[di] = max(0.0, (v_max - float(V_all[opt_e1w_idx])) / v_rng)

            # Assert: (trio_sel != t*) <==> (R > 0)
            # In production code R == 0.0 exactly iff opt_e1b_idx == opt_mm_idx.
            # If this assert fires, there is a floating-point mismatch or a bug.
            trio_neq_tstar = (opt_e1b_idx != opt_mm_idx)
            r_e1b_pos      = (R_e1b_opt[di] > 0.0)
            assert trio_neq_tstar == r_e1b_pos, (
                f"[EVAL-R {label}] draw {di}: "
                f"trio_neq_tstar={trio_neq_tstar} but R_e1b>0={r_e1b_pos} "
                f"(R_e1b={R_e1b_opt[di]:.3e}); min non-zero R must be >> 1e-12"
            )
            n_nonzero_e1b_trio += int(trio_neq_tstar)

            # Gate 4d: E1-V ≡ SAW_vec (A_V = rho_j, so V_e1v = V_vec_trios)
            # Both use identical float64 computation; must agree exactly.
            assert opt_e1v_idx == opt_vec_idx, (
                f"[EVAL-R {label}] Gate 4d draw {di}: "
                f"E1-V opt={opt_e1v_idx} != SAW_vec opt={opt_vec_idx}. "
                "A_V != rho_j or floating-point disagrees."
            )
            # Gate 4e: E1-M ≡ SAW_mm (A_M = ones, so V_e1m = V_all)
            assert opt_e1m_idx == opt_mm_idx, (
                f"[EVAL-R {label}] Gate 4e draw {di}: "
                f"E1-M opt={opt_e1m_idx} != SAW_mm opt={opt_mm_idx}. "
                "A_M != ones or floating-point disagrees."
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
        if e1_avail:
            print("  Gate 4d (E1-V==SAW_vec): PASS", flush=True)
            print("  Gate 4e (E1-M==SAW_mm):  PASS", flush=True)
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
            "R_e1b_mean_pp":       round(float(np.nanmean(R_e1b_opt)   * 100), 2),
            "R_e1b_median_pp":     round(float(np.nanmedian(R_e1b_opt) * 100), 2),
            "R_e1w_mean_pp":       round(float(np.nanmean(R_e1w_opt)   * 100), 2),
            "R_e1w_median_pp":     round(float(np.nanmedian(R_e1w_opt) * 100), 2),
            "frac_R_e1b_zero":     round(float((R_e1b_opt < 1e-12).mean()), 4),
            "n_e1b_zero_exact":    int((R_e1b_opt < 1e-12).sum()),
            # Trio-based count (primary): n_nonzero = sum(trio_sel != t*)
            # Equivalent to R>0 by assertion; trio comparison is the definition.
            "n_nonzero_e1b_trio":  n_nonzero_e1b_trio,
        })
    return {
        "label":             label,
        "N_DRAWS":           B,
        "R_mm_opt_pp":       (R_mm_opt  * 100).tolist(),
        "R_sawvec_grd_pp":   (R_vec_grd * 100).tolist(),
        "R_sawvec_opt_pp":   (R_vec_opt * 100).tolist(),
        "R_e1b_opt_pp":      (R_e1b_opt * 100).tolist(),
        "R_e1w_opt_pp":      (R_e1w_opt * 100).tolist(),
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

    Returns dict with keys: X_mm, trios, D, rho_j, W_draws, w0, greedy_fn, e1_fn, label.
    Raises RuntimeError if Fogo modules are not importable.

    NOTE: e1_fn takes NO arguments. Returns constant E1 amplitude dict from w0.
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
    W_draws = np.load(ROOT / "results" / "e1" / "e1_weights_k200.npy")  # (500, 11) float64

    # OBJ_GROUPS is a list of lists: [[0,1,2],[3,4,5,6,7],[8,9,10]]
    groups = OBJ_GROUPS   # already a list — no .keys()
    w0     = np.asarray(W_raw, dtype=np.float64)
    w0     = w0 / w0.sum()

    rho_j_arr = np.asarray(rho_j_fogo, dtype=np.float64)

    def _e1_fn():
        """Return constant E1 amplitudes from fixed w0 (no per-draw arg)."""
        return get_e1_amplitudes(rho_j_arr, groups, w0=w0)

    return {
        "X_mm":      np.asarray(X_adj,      dtype=np.float64),
        "trios":     trios,
        "D":         np.asarray(D,          dtype=np.float64),
        "rho_j":     rho_j_arr,
        "W_draws":   W_draws,
        "w0":        w0,
        "greedy_fn": greedy_selector,
        "e1_fn":     _e1_fn,
        "label":     "FOGO",
    }


def load_santiago_data(branch_key: str, kappa: int = 200) -> dict:
    """Load Santiago branch data + pre-generate canonical weight draws.

    W_draws are generated in the SAME sequence as the MC run.
    e1_fn takes NO arguments (returns constant amplitudes from fixed w0).

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
    rho_j  = np.asarray(data["rho_j"], dtype=np.float64)

    def _e1_fn():
        """Return constant E1 amplitudes from fixed w0 (no per-draw arg)."""
        return get_e1_amplitudes(rho_j, groups, w0=w0)

    return {
        "X_mm":      np.asarray(data["X_mm"],   dtype=np.float64),
        "trios":     np.asarray(data["trios"],  dtype=np.int32),
        "D":         np.asarray(data["D"],      dtype=np.float64),
        "rho_j":     rho_j,
        "W_draws":   W_draws,
        "w0":        w0,
        "greedy_fn": greedy_selector,
        "e1_fn":     _e1_fn,
        "label":     f"SANT-{branch_key}-k{kappa}",
    }
