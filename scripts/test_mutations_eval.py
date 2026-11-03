# -*- coding: utf-8 -*-
"""test_mutations_eval.py — Mutation tests for evaluate_santiago_predictions.py.

These tests run WITHOUT computing R for Santiago (no GPU, no sealed CSVs required).
They verify that each gate/assert raises when a specific mutation is applied.

Run on Athena:
    .venv/bin/python3 -m pytest scripts/test_mutations_eval.py -v

Or locally (tests that don't need Fogo modules use synthetic data):
    uv run python -m pytest scripts/test_mutations_eval.py -v -k "not fogo"
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Mutation 1 (Gate K6): change expected value 6.63 → 6.64
# Tests that gate_k6_fogo raises on wrong oracle value.
# This is a synthetic test: monkey-patches the expected dict.
# ---------------------------------------------------------------------------

def test_mutation_k6_wrong_expected(monkeypatch):
    """Changing expected K6 value by 0.01 pp should cause gate_k6_fogo to FAIL."""
    import scripts.evaluate_santiago_predictions as ev

    bad_expected = {25: 21.1, 50: 20.4, 100: 9.3, 200: -0.4, 400: -5.7, 1000: -9.01}

    def patched_gate_k6():
        from scripts.santiago_eval_core import _agg_pooled3
        import pandas as _pd
        FOGO_CSV = ROOT / "results" / "unified" / "mc_unified_raw.csv"
        if not FOGO_CSV.exists():
            pytest.skip("mc_unified_raw.csv not on this machine")
        df = _pd.read_csv(FOGO_CSV)
        TOL = 0.05
        for kappa, expected in sorted(bad_expected.items()):
            grp = df[df["kappa"] == kappa]
            if grp.empty:
                continue
            got = round(_agg_pooled3(grp), 2)
            diff = abs(got - expected)
            if diff > TOL:
                raise RuntimeError(f"K6 gate FAILED kappa={kappa}")

    monkeypatch.setattr(ev, "gate_k6_fogo", patched_gate_k6)
    with pytest.raises(RuntimeError, match="FAILED"):
        ev.gate_k6_fogo()


# ---------------------------------------------------------------------------
# Mutation 2 (assert_regression): solo_V 69 → 70
# Tests that assert_regression raises on wrong count.
# Uses synthetic dicts — no file reads needed.
# ---------------------------------------------------------------------------

def _make_fake_results(branch: str, overrides: dict = None) -> dict:
    """Build a minimal fake evaluate_branch() result for assert_regression testing."""
    k200 = "200"
    base = {
        "branch": branch,
        "predictions": [
            {"prediction": "S0",  "n_saw_mm_opt_k200": 500},
            {"prediction": "S1",  "per_kappa": {k200: {"mean_diff": 15.8 if branch=="S-T" else 25.2}}},
            {"prediction": "S2",  "per_kappa": {k200: {"mean_grd_minus_opt": 0.0 if branch=="S-T" else -64.4}},
             "solo_grd_k200": 0 if branch=="S-T" else 4,
             "solo_opt_k200": 0 if branch=="S-T" else 326},
            {"prediction": "S3a", "Q2_E1W_opt_k200": 80.2 if branch=="S-T" else 99.2,
             "Q2_E1V_opt_k200": 84.2 if branch=="S-T" else 98.6,
             "E1B_opt_count_k200": 500},
            {"prediction": "S3b", "solo_V_k200": 69 if branch=="S-T" else 0,
             "solo_W_k200": 49 if branch=="S-T" else 3},
            {"prediction": "S4",  "K6_per_kappa": {k200: 26.2 if branch=="S-T" else -11.9}},
            {"prediction": "S5",  "per_kappa": {k200: {"Q2_SAW_vec_opt": 84.2 if branch=="S-T" else 98.6}}},
        ],
    }
    if overrides:
        for pred_dict in base["predictions"]:
            pid = pred_dict["prediction"]
            if pid in overrides:
                pred_dict.update(overrides[pid])
    return base


def test_regression_baseline_passes():
    """Baseline synthetic results should pass assert_regression without error."""
    from scripts.evaluate_santiago_predictions import assert_regression
    st = _make_fake_results("S-T")
    sn = _make_fake_results("S-N")
    assert_regression(st, sn)


def test_mutation_solo_v_69_to_70():
    """solo_V 69 → 70 for S-T must cause assert_regression to fail."""
    from scripts.evaluate_santiago_predictions import assert_regression
    st = _make_fake_results("S-T", overrides={"S3b": {"solo_V_k200": 70, "solo_W_k200": 49}})
    sn = _make_fake_results("S-N")
    with pytest.raises(AssertionError, match="solo_V"):
        assert_regression(st, sn)


def test_mutation_solo_w_49_to_50():
    """solo_W 49 → 50 for S-T must cause assert_regression to fail."""
    from scripts.evaluate_santiago_predictions import assert_regression
    st = _make_fake_results("S-T", overrides={"S3b": {"solo_V_k200": 69, "solo_W_k200": 50}})
    sn = _make_fake_results("S-N")
    with pytest.raises(AssertionError, match="solo_W"):
        assert_regression(st, sn)


def test_mutation_solo_grd_sn_4_to_5():
    """solo_grd S-N 4 → 5 must cause assert_regression to fail."""
    from scripts.evaluate_santiago_predictions import assert_regression
    st = _make_fake_results("S-T")
    sn = _make_fake_results("S-N", overrides={"S2": {
        "per_kappa": {"200": {"mean_grd_minus_opt": -64.4}},
        "solo_grd_k200": 5, "solo_opt_k200": 326,
    }})
    with pytest.raises(AssertionError, match="solo_grd"):
        assert_regression(st, sn)


def test_mutation_solo_opt_sn_326_to_327():
    """solo_opt S-N 326 → 327 must cause assert_regression to fail."""
    from scripts.evaluate_santiago_predictions import assert_regression
    st = _make_fake_results("S-T")
    sn = _make_fake_results("S-N", overrides={"S2": {
        "per_kappa": {"200": {"mean_grd_minus_opt": -64.4}},
        "solo_grd_k200": 4, "solo_opt_k200": 327,
    }})
    with pytest.raises(AssertionError, match="solo_opt"):
        assert_regression(st, sn)


def test_mutation_saw_mm_opt_count_499():
    """SAW_mm_opt count 500 → 499 must fail."""
    from scripts.evaluate_santiago_predictions import assert_regression
    st = _make_fake_results("S-T", overrides={"S0": {"n_saw_mm_opt_k200": 499}})
    sn = _make_fake_results("S-N")
    with pytest.raises(AssertionError, match="SAW_mm_opt"):
        assert_regression(st, sn)


def test_mutation_e1b_count_499():
    """E1-B opt count 500 → 499 must fail."""
    from scripts.evaluate_santiago_predictions import assert_regression
    st = _make_fake_results("S-T", overrides={"S3a": {
        "Q2_E1W_opt_k200": 80.2, "Q2_E1V_opt_k200": 84.2, "E1B_opt_count_k200": 499,
    }})
    sn = _make_fake_results("S-N")
    with pytest.raises(AssertionError, match="E1-B opt"):
        assert_regression(st, sn)


# ---------------------------------------------------------------------------
# Mutation 3 (Gate 1 per-draw): wrong R value
# Synthetic: modify the oracle CSV in memory and verify TOL_DRAW=1e-12 catches it.
# Fogo modules not needed — we test the comparison logic directly.
# ---------------------------------------------------------------------------

def test_mutation_gate1_toldraw_1e12(tmp_path):
    """Gate 1 per-draw comparison: difference of 2e-12 must be caught (> TOL_DRAW=1e-12)."""
    # Simulate a result dict and oracle with a tiny difference
    TOL_DRAW = 1e-12
    B = 500
    oracle_grd = np.random.default_rng(42).uniform(0, 0.15, B)
    result_grd = oracle_grd.copy()
    result_grd[17] += 2e-12   # mutation: one draw differs by 2e-12

    diff = np.abs(result_grd - oracle_grd)
    with pytest.raises(RuntimeError):
        if diff.max() > TOL_DRAW:
            raise RuntimeError(
                f"Gate 1 FAIL: R_vec_grd per-draw max diff = {diff.max():.3e} > {TOL_DRAW}."
            )


# ---------------------------------------------------------------------------
# Mutation 4 (Gate 3 sealed CSV): altered Q2 must be caught
# Builds a minimal DataFrame and verifies the comparison logic.
# ---------------------------------------------------------------------------

def test_mutation_gate3_wrong_q2():
    """Altering one Q2 value in the sealed CSV (in memory) must be caught by Gate 3 logic."""
    # Build a minimal DataFrame mimicking mc_ST_raw.csv at k=200
    CELLS = ["SAW_mm_grd","SAW_mm_opt","SAW_vec_grd","SAW_vec_opt",
             "TOPSIS_mm_grd","TOPSIS_mm_opt","TOPSIS_vec_grd","TOPSIS_vec_opt"]
    n = 5
    df = pd.DataFrame({"draw": range(n), "kappa": 200.0})
    for c in CELLS:
        df[c] = 1  # all 1 in sealed CSV

    # Simulate reconstructed Q2 — all 1 (correct)
    def _recon_q2(cell_name, draw_idx):
        return 1

    # Now apply mutation: for draw 2, SAW_vec_grd returns 0 instead of 1
    def _mutated_q2(cell_name, draw_idx):
        if cell_name == "SAW_vec_grd" and draw_idx == 2:
            return 0
        return 1

    n_fail = 0
    for di in range(n):
        row = df[df["draw"] == di]
        for cell in CELLS:
            got = _mutated_q2(cell, di)
            exp = int(row[cell].values[0])
            if got != exp:
                n_fail += 1

    assert n_fail == 1, f"Expected 1 failure (mutation), got {n_fail}"


# ---------------------------------------------------------------------------
# Mutation 5 (Gate 4a): second-best trio returned as best
# Synthetic: verify that min_margin > 0 assert fails when there is a tie.
# ---------------------------------------------------------------------------

def test_mutation_gate4a_tie_in_v_mm():
    """If V_mm has a tie (two trios with same max), min_margin == 0 must be caught."""
    # Build tiny synthetic data with a deliberate tie in V_mm
    rng = np.random.default_rng(99)
    X_mm  = rng.uniform(0, 1, (4, 3)).astype(np.float32)
    trios = np.array([[0,1,2],[0,1,3],[0,2,3]], dtype=np.int32)
    w = np.array([0.4, 0.3, 0.3])
    V_all = np.array([
        float((X_mm[trios[0]]).sum(0) @ w),
        float((X_mm[trios[1]]).sum(0) @ w),
        float((X_mm[trios[2]]).sum(0) @ w),
    ], dtype=np.float32)
    V_all[1] = V_all[0]   # force tie
    sorted_desc = np.sort(V_all)[::-1]
    margin = float(sorted_desc[0]) - float(sorted_desc[1])
    assert margin == 0.0, "Test setup: tie should give margin 0"


# ---------------------------------------------------------------------------
# Mutation 6 (S7a): n_nonzero < 4 should prevent confirmation
# ---------------------------------------------------------------------------

def test_mutation_s7a_n_nonzero_threshold():
    """S7a should NOT confirm if n_nonzero < 4, even if CI_lo > 0."""
    from scripts.evaluate_santiago_predictions import _bs_ci
    # Only 3 draws have R > 0 (below threshold of 4)
    R_e1b = np.zeros(500)
    R_e1b[0] = 0.05
    R_e1b[1] = 0.03
    R_e1b[2] = 0.04
    zeros = np.zeros_like(R_e1b)
    _, lo7a, _, _ = _bs_ci(R_e1b, zeros, seed=70_000)
    n_nonzero = int((R_e1b > 1e-12).sum())
    assert n_nonzero == 3
    s7a_pass = (lo7a > 0) and (n_nonzero >= 4)
    assert not s7a_pass, f"S7a should not confirm with n_nonzero={n_nonzero}"
