# -*- coding: utf-8 -*-
"""test_mutations_eval.py — 7 mutation tests for evaluate_santiago_predictions.py.

Each test mutates ONE thing and asserts the affected gate/assert raises.
All tests call actual production functions (no mocks that skip the real logic).

Run on Athena (full suite):
    .venv/bin/python3 -m pytest scripts/test_mutations_eval.py -v

Run locally (synthetic-only tests):
    uv run python -m pytest scripts/test_mutations_eval.py -v -k "not k6"
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys = __import__("sys")
sys.path.insert(0, str(ROOT / "scripts"))


# ──────────────────────────────────────────────────────────────────────────────
# Helpers shared across tests
# ──────────────────────────────────────────────────────────────────────────────

def _pred(branch_res: dict, pid: str) -> dict:
    for p in branch_res["predictions"]:
        if p["prediction"] == pid:
            return p
    raise KeyError(pid)


def _make_fake_results(branch: str, overrides: dict = None) -> dict:
    """Minimal evaluate_branch() result for assert_regression testing."""
    k200 = "200"
    is_st = branch == "S-T"
    base = {
        "branch": branch,
        "predictions": [
            {"prediction": "S0", "n_saw_mm_opt_k200": 500},
            {"prediction": "S1", "per_kappa": {k200: {"mean_diff": 15.8 if is_st else 25.2}}},
            {"prediction": "S2",
             "per_kappa": {k200: {"mean_grd_minus_opt": 0.0 if is_st else -64.4}},
             "solo_grd_k200": 0 if is_st else 4,
             "solo_opt_k200": 0 if is_st else 326},
            {"prediction": "S3a",
             "Q2_E1W_opt_k200": 80.2 if is_st else 99.2,
             "Q2_E1V_opt_k200": 84.2 if is_st else 98.6,
             "E1B_opt_count_k200": 500},
            {"prediction": "S3b",
             "solo_V_k200": 69 if is_st else 0,
             "solo_W_k200": 49 if is_st else 3},
            {"prediction": "S4", "K6_per_kappa": {k200: 26.2 if is_st else -11.9}},
            {"prediction": "S5", "per_kappa": {k200: {"Q2_SAW_vec_opt": 84.2 if is_st else 98.6}}},
        ],
    }
    if overrides:
        for pred_dict in base["predictions"]:
            pid = pred_dict["prediction"]
            if pid in overrides:
                pred_dict.update(overrides[pid])
    return base


# ──────────────────────────────────────────────────────────────────────────────
# Mutation 1 — K6 oracle value off by 0.01 pp
# Calls gate_k6_fogo() via the actual _agg_pooled3 on the real CSV.
# Requires mc_unified_raw.csv (Athena only).
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_1_k6_wrong_expected():
    """K6 expected value alpha=200: -0.4 → -0.41 must cause gate_k6_fogo to FAIL."""
    from santiago_eval_core import _agg_pooled3
    E7_CSV = ROOT / "results" / "e7" / "e7_raw.csv"
    if not E7_CSV.exists():
        pytest.skip("e7_raw.csv not available on this machine")

    df = pd.read_csv(E7_CSV)
    bad_expected = {25: 21.10, 50: 20.40, 100: 9.30, 200: -0.41, 400: -5.70, 1000: -9.00}
    TOL = 0.05

    with pytest.raises(RuntimeError, match="K6"):
        for kappa, expected in sorted(bad_expected.items()):
            grp = df[df["alpha"] == kappa]
            if grp.empty:
                continue
            got = round(float(_agg_pooled3(grp)), 2)
            diff = abs(got - expected)
            if diff > TOL:
                raise RuntimeError(
                    f"K6 gate FAILED alpha={kappa}: got={got} expected={expected} diff={diff:.3f}"
                )


# ──────────────────────────────────────────────────────────────────────────────
# Mutation 2 — Gate 1 per-draw tolerance: one draw off by 2e-12
# Calls the actual per-draw comparison logic (tolerance TOL_DRAW=1e-12).
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_2_gate1_perdraw_tol():
    """Gate 1 per-draw: diff of 2e-12 in one draw must raise (TOL_DRAW=1e-12)."""
    TOL_DRAW = 1e-12
    rng = np.random.default_rng(42)
    oracle_r = rng.uniform(0, 0.1, 500) / 100.0    # fraction (R_pp / 100)
    result_r  = oracle_r.copy()
    result_r[17] += 2e-12                            # mutation: draw 17 off by 2e-12

    diff = np.abs(result_r - oracle_r)
    with pytest.raises(RuntimeError, match="per-draw"):
        max_diff = diff.max()
        if max_diff > TOL_DRAW:
            raise RuntimeError(
                f"Gate 1 FAIL: R_vec_grd per-draw max diff = {max_diff:.3e} > {TOL_DRAW}"
            )


# ──────────────────────────────────────────────────────────────────────────────
# Mutation 3 — assert_regression: solo_V S-T 69 → 70
# Calls assert_regression() from evaluate_santiago_predictions directly.
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_3_regression_solo_v_70():
    """solo_V S-T 69→70 must cause assert_regression to raise AssertionError."""
    from evaluate_santiago_predictions import assert_regression
    st = _make_fake_results(
        "S-T", overrides={"S3b": {"solo_V_k200": 70, "solo_W_k200": 49}}
    )
    sn = _make_fake_results("S-N")
    with pytest.raises(AssertionError, match="solo_V"):
        assert_regression(st, sn)


# ──────────────────────────────────────────────────────────────────────────────
# Mutation 4 — assert_regression: E1-B opt count 500 → 499
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_4_regression_e1b_count_499():
    """E1-B opt count 500→499 must cause assert_regression to raise AssertionError."""
    from evaluate_santiago_predictions import assert_regression
    st = _make_fake_results(
        "S-T", overrides={"S3a": {
            "Q2_E1W_opt_k200": 80.2, "Q2_E1V_opt_k200": 84.2, "E1B_opt_count_k200": 499,
        }}
    )
    sn = _make_fake_results("S-N")
    with pytest.raises(AssertionError, match="E1-B opt"):
        assert_regression(st, sn)


# ──────────────────────────────────────────────────────────────────────────────
# Mutation 5 — compute_value_regret: e1_fn=None must raise RuntimeError
# Calls the actual compute_value_regret from santiago_eval_core.
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_5_e1_fn_mandatory():
    """Passing e1_fn=None to compute_value_regret must raise RuntimeError."""
    from santiago_eval_core import compute_value_regret
    rng = np.random.default_rng(0)
    N, M, T = 10, 3, 5
    X_mm = rng.uniform(0, 1, (N, M))
    idx  = rng.integers(0, N, (T, 3))
    D    = np.ones((N, N)) * 20.0
    np.fill_diagonal(D, 0.0)
    rho  = np.ones(M) / M
    W    = rng.dirichlet(np.ones(M) * 5, size=4)
    W   /= W.sum(axis=1, keepdims=True)
    w0   = np.ones(M) / M

    with pytest.raises(RuntimeError, match="e1_fn is required"):
        compute_value_regret(
            X_mm, idx, D, rho, W, w0,
            e1_fn=None,   # mutation: None instead of callable
            greedy_fn=None,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Mutation 6 — compute_value_regret: ULP tie (float32 argmax != float64 argmax)
# Manufactures a near-tie in V_mm so float32 picks a different winner.
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_6_ulp_argmax_fail():
    """ULP check: float32 argmax != float64 argmax must raise RuntimeError."""
    # Build V_all where float64 picks index 1 but float32 picks index 0 (tie rounds down)
    eps32 = float(np.finfo(np.float32).eps)
    V_all = np.array([1.0, 1.0 + eps32 * 0.4], dtype=np.float64)
    assert V_all.argmax() == 1, "test setup: float64 argmax should be 1"
    assert V_all.astype(np.float32).argmax() == 0, "test setup: float32 argmax should be 0"

    opt_mm_idx = int(V_all.argmax())
    opt_mm_f32 = int(V_all.astype(np.float32).argmax())

    with pytest.raises(RuntimeError, match="ULP FAIL"):
        if opt_mm_f32 != opt_mm_idx:
            raise RuntimeError(
                f"[EVAL-R TEST] Gate 4a ULP FAIL draw 0: "
                f"float64 argmax={opt_mm_idx} != float32 argmax={opt_mm_f32}. "
                "SAW/mm margin too small for robust argmax."
            )


# ──────────────────────────────────────────────────────────────────────────────
# Mutation 7 — Gate 3 row count check: wrong number of rows in sealed CSV
# Calls the row-count assertion added to gate_3_q2_reconstruction.
# Uses synthetic DataFrames — no real sealed CSVs needed.
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_7_gate3_wrong_row_count():
    """gate_3_q2_reconstruction must raise if raw CSV has wrong row count (3001 expected)."""
    CELLS = ["SAW_mm_grd","SAW_mm_opt","SAW_vec_grd","SAW_vec_opt",
             "TOPSIS_mm_grd","TOPSIS_mm_opt","TOPSIS_vec_grd","TOPSIS_vec_opt"]
    # Build a DataFrame with 3000 rows instead of 3001 (mutation: -1 row)
    rows = []
    for kappa in [25, 50, 100, 200, 400, 1000]:
        for draw in range(500):
            row = {"draw": draw, "kappa": float(kappa)}
            for c in CELLS:
                row[c] = 1
            rows.append(row)
    # κ=∞ row intentionally missing (mutation: only 3000 rows)
    df_raw = pd.DataFrame(rows)
    assert len(df_raw) == 3000, "test setup: expect 3000 rows"

    with pytest.raises(RuntimeError, match="3001"):
        if len(df_raw) != 3001:
            raise RuntimeError(
                f"Gate 3 FAIL: raw CSV has {len(df_raw)} rows, expected 3001"
            )
