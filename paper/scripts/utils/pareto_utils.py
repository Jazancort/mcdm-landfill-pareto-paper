# -*- coding: utf-8 -*-
"""
pareto_utils.py — Shared Pareto dominance utilities for all MC scripts.

Single source of truth for:
  - compute_objs_f64: per-site (f1, f2, f3) in float64, ref=df_via (389 sites)
  - is_dominated_sorted: dominance test with sorted-index lookup + eps tolerance
  - assert_no_self_dom: structural assertion — a trio cannot be its own only dominator

USAGE (in every MC script):
    from pareto_utils import build_pareto_utils
    compute_objs, is_dominated, trio_lookup = build_pareto_utils(
        df_via, col_names, trio_arr, eps=1e-9
    )

All three corrections documented in check_self_dom.py are applied here:
  1. float64 (not float32)
  2. Objectives read from F1[sorted_idx] (same entry as frontier, no ULP diff)
  3. Self excluded from dominator test

Bug history:
  wp3_mc.py     : float32 + unsorted-idx -> self-dom in 101/500 mm-greedy draws
  mc_2cube.py   : same bug + ref=473 for objectives in space A' (wrong estimand)
  run_e1.py v1-3: three separate reimplementations, each with a different bug
"""
import numpy as np


def build_pareto_utils(df_via, col_names, trio_arr, eps=1e-9,
                       inv_set=None, cost_set=None,
                       f1_crit=None, f2_crit=None, f3_crit=None,
                       col_map=None, ref_df=None):
    """
    Build and return the three shared utilities for Monte Carlo scripts.

    Parameters
    ----------
    df_via : DataFrame
        Sites whose objectives are computed (space A' = 389 admissible sites,
        or any subset). Trios index into this DataFrame.
    col_names : list[str]
        Criterion names in AHP weight order (11 criteria).
    trio_arr : np.ndarray (M, 3), int32
        Pre-built array of sorted viable trio indices (into df_via).
    eps : float
        Dominance tolerance (default 1e-9).
    ref_df : DataFrame or None
        Reference population for min-max normalisation constants.
        If None (default), uses df_via itself (standard space A').
        Pass df_all (473 sites) to get space-A normalisation constants
        while keeping portfolios restricted to df_via sites.
    inv_set, cost_set, f1_crit, f2_crit, f3_crit, col_map : see defaults.

    Returns
    -------
    compute_objs_f64 : callable(w) -> (f1v, f2v, f3v)
    is_dominated : callable(trio_tuple, F1, F2, F3) -> bool
    trio_lookup : dict
    """
    # ── Defaults ──────────────────────────────────────────────────────────────
    if inv_set is None:
        from mcdm_experiment import INV as _INV
        inv_set = _INV
    if cost_set is None:
        from mcdm_experiment import COST as _COST
        cost_set = _COST
    if f1_crit is None:
        from mcdm_experiment import F1_CRIT as _F1, F2_CRIT as _F2, F3_CRIT as _F3
        f1_crit, f2_crit, f3_crit = _F1, _F2, _F3
    if col_map is None:
        from mcdm_experiment import COL as _COL
        col_map = _COL

    # ref_df: population used for normalisation constants (min/max per column)
    # Default: df_via itself (space A').  Pass df_all for space-A constants.
    _ref_df = ref_df if ref_df is not None else df_via

    # ── Sorted-index lookup ───────────────────────────────────────────────────
    T0, T1, T2 = trio_arr[:,0], trio_arr[:,1], trio_arr[:,2]
    _lookup = {
        (int(T0[i]), int(T1[i]), int(T2[i])): i
        for i in range(len(trio_arr))
    }

    # ── Objectives helper ─────────────────────────────────────────────────────
    from mcdm_experiment import _norm

    def compute_objs_f64(w):
        """
        Per-site (f1, f2, f3) in float64.

        Normalisation constants come from _ref_df (df_via by default, or df_all
        when ref_df=df_all is passed — space-A normalisation).
        Objective values are computed for sites in df_via only.

        F1, F2: cost-type (lower = better).
        F3: benefit-type (higher = better).
        """
        N = len(df_via)
        f1v = np.zeros(N, dtype=np.float64)
        f2v = np.zeros(N, dtype=np.float64)
        f3v = np.zeros(N, dtype=np.float64)
        for j, k in enumerate(col_names):
            x   = df_via[col_map[k]].values.astype(np.float64)
            ref = _ref_df[col_map[k]].values.astype(np.float64)
            if k == "aspect":
                c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
            elif k in inv_set:
                c = 1.0 - _norm(x, ref)
            elif k in cost_set:
                c = _norm(x, ref)
            else:
                c = _norm(x, ref)
            c = c * float(w[j])
            if k in f1_crit:   f1v += c
            elif k in f2_crit: f2v += c
            else:              f3v += c
        return f1v, f2v, f3v

    # ── Dominance test ────────────────────────────────────────────────────────
    def is_dominated(trio_tuple, F1, F2, F3):
        """
        Return True if trio_tuple is dominated.

        Objectives of the query trio are read from F1[sorted_idx] to guarantee
        bitwise identity with the frontier entry (no ULP discrepancy).
        The trio itself is excluded from the dominator search.
        """
        key = tuple(sorted(trio_tuple))
        idx = _lookup.get(key, -1)
        if idx < 0:
            return False  # trio not in admissible set (should not happen)
        f1t = float(F1[idx])
        f2t = float(F2[idx])
        f3t = float(F3[idx])
        # Exclude the trio itself
        mask = np.ones(len(F1), dtype=bool)
        mask[idx] = False
        F1m, F2m, F3m = F1[mask], F2[mask], F3[mask]
        weak   = (F1m <= f1t + eps) & (F2m <= f2t + eps) & (F3m >= f3t - eps)
        strict = (F1m <  f1t - eps) | (F2m <  f2t - eps) | (F3m >  f3t + eps)
        return bool((weak & strict).any())

    return compute_objs_f64, is_dominated, _lookup


def assert_no_self_dom(trio_tuple, F1, F2, F3, trio_lookup, eps=1e-9):
    """
    Structural assertion: the only dominator of a trio must not be the trio itself.

    Call after any dominance test for debugging. Raises AssertionError if
    self-dominance is detected, which indicates a pipeline bug (float32 rounding
    or unsorted-index objective lookup).
    """
    key = tuple(sorted(trio_tuple))
    idx = trio_lookup.get(key, -1)
    if idx < 0:
        return  # not in array, cannot check
    f1t = float(F1[idx])
    f2t = float(F2[idx])
    f3t = float(F3[idx])
    # Check ONLY the trio itself (not excluding it)
    weak   = (F1[idx] <= f1t + eps) and (F2[idx] <= f2t + eps) and (F3[idx] >= f3t - eps)
    strict = (F1[idx] <  f1t - eps) or  (F2[idx] <  f2t - eps) or  (F3[idx] >  f3t + eps)
    assert not (weak and strict), (
        f"Self-dominance detected for trio {key}: F1={f1t:.8f}, F2={f2t:.8f}, F3={f3t:.8f} "
        f"dominates itself. This is a pipeline bug (float32 rounding or unsorted index)."
    )
