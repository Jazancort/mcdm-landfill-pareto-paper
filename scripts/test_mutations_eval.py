# -*- coding: utf-8 -*-
"""test_mutations_eval.py — 13 mutation tests for evaluate_santiago_predictions.py.

Each test calls a PRODUCTION function (no logic copies).

Mutation table:

| # | Function called                          | Mutation                               | Expected raise    |
|---|------------------------------------------|----------------------------------------|-------------------|
| 1 | gate_k6_fogo() [REAL — slow]             | K6_FOGO_EXPECTED[100]: 9.3→9.4         | RuntimeError      |
| 2 | _check_perdraw_tol() [production helper] | diff[17] += 2e-12 > TOL_DRAW=1e-12     | RuntimeError      |
| 3 | assert_regression()                      | solo_V S-T: 69→70                      | AssertionError    |
| 4 | assert_regression()                      | solo_W S-T: 49→50                      | AssertionError    |
| 5 | assert_regression()                      | E1-B opt count: 500→499                | AssertionError    |
| 6 | compute_value_regret()                   | e1_fn=None (mandatory)                 | RuntimeError      |
| 7 | compute_value_regret()                   | synthetic data: f32 argmax≠f64 argmax  | RuntimeError      |
| 8 | _check_gate3_row_counts() [production]   | n_raw=3000 instead of 3001             | RuntimeError      |
| 9 | _check_perdraw_tol() via oracle CSV      | oracle R_grd draw 6: +0.01pp shift     | RuntimeError      |
|10 | compute_value_regret()                   | e1_fn returns A_M≠ones (E1-ABAR bug)   | AssertionError    |
|11 | _check_gate4a_identity() [production]    | second-best trio returned by Gate 3    | RuntimeError      |
|12 | _check_q2_cell() [production]            | flip one sealed Q2: 0→1                | RuntimeError      |
|13 | compute_value_regret()                   | tie: trio≠t* but R forced to 0         | AssertionError    |

Tests 1 requires e7_raw.csv (Athena); skips locally if absent.
Test 9 requires results/regret/regret_perdraw.csv (local); skips if absent.
All other tests are fully synthetic and run without Athena data.

Run on Athena (full suite, 0 skipped):
    uv run --with pytest pytest scripts/test_mutations_eval.py -v

Run locally (synthetic-only):
    uv run python -m pytest scripts/test_mutations_eval.py -v -k "not k6 and not oracle_csv"
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent
import sys as _sys
_sys.path.insert(0, str(ROOT / "scripts"))


# ──────────────────────────────────────────────────────────────────────────────
# Helpers shared across tests
# ──────────────────────────────────────────────────────────────────────────────

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


def _synthetic_regret_data(N=9, M=4, T=3, B=4, seed=0):
    """Build minimal inputs for compute_value_regret that pass all gates."""
    rng = np.random.default_rng(seed)
    X_mm = rng.uniform(0.1, 0.9, (N, M))
    # Three non-overlapping trios
    trios = np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]], dtype=np.int32)
    D = np.ones((N, N)) * 30.0; np.fill_diagonal(D, 0.0)
    rho = rng.dirichlet(np.ones(M))
    w0  = rng.dirichlet(np.ones(M))
    W   = rng.dirichlet(np.ones(M) * 5, size=B)
    W   = W / W.sum(axis=1, keepdims=True)

    def e1_fn():
        return {"M": np.ones(M), "B": np.ones(M),
                "W": np.ones(M), "V": rho.copy()}

    return dict(X_mm=X_mm, trios=trios, D=D, rho_j=rho, W_draws=W, w0=w0,
                e1_fn=e1_fn, label="TEST")


# ──────────────────────────────────────────────────────────────────────────────
# Mutation 1 — K6: call REAL gate_k6_fogo() with monkeypatched K6_FOGO_EXPECTED
# Requires e7_raw.csv (Athena); skips locally if absent.
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_1_k6_gate_real(monkeypatch):
    """K6_FOGO_EXPECTED[100] 9.3→9.4: real gate_k6_fogo() must raise RuntimeError."""
    import evaluate_santiago_predictions as ev
    E7_CSV = ROOT / "results" / "e7" / "e7_raw.csv"
    if not E7_CSV.exists():
        pytest.skip("e7_raw.csv not available on this machine")

    mutated = dict(ev.K6_FOGO_EXPECTED)
    mutated[100] = 9.4   # real value ≈9.33; diff 0.07 > TOL 0.05
    monkeypatch.setattr(ev, "K6_FOGO_EXPECTED", mutated)

    with pytest.raises(RuntimeError, match="K6.*FAILED"):
        ev.gate_k6_fogo()


# ──────────────────────────────────────────────────────────────────────────────
# Mutation 2 — Gate 1 per-draw tolerance: call _check_perdraw_tol() from production
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_2_gate1_perdraw_tol():
    """Gate 1 per-draw: _check_perdraw_tol raises if diff > TOL_DRAW=1e-12."""
    from evaluate_santiago_predictions import _check_perdraw_tol
    TOL_DRAW = 1e-12
    rng = np.random.default_rng(42)
    oracle_r = rng.uniform(0, 0.1, 500) / 100.0
    result_r = oracle_r.copy()
    result_r[17] += 2e-12   # mutation: draw 17 off by 2e-12

    with pytest.raises(RuntimeError, match="per-draw"):
        _check_perdraw_tol(oracle_r, result_r, TOL_DRAW, "grd")


# ──────────────────────────────────────────────────────────────────────────────
# Mutations 3–5 — assert_regression: three counts mutated
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_3_regression_solo_v_70():
    """solo_V S-T 69→70 must cause assert_regression to raise AssertionError."""
    from evaluate_santiago_predictions import assert_regression
    st = _make_fake_results("S-T", overrides={"S3b": {"solo_V_k200": 70, "solo_W_k200": 49}})
    sn = _make_fake_results("S-N")
    with pytest.raises(AssertionError, match="solo_V"):
        assert_regression(st, sn)


def test_mutation_4_regression_solo_w_50():
    """solo_W S-T 49→50 must cause assert_regression to raise AssertionError."""
    from evaluate_santiago_predictions import assert_regression
    st = _make_fake_results("S-T", overrides={"S3b": {"solo_V_k200": 69, "solo_W_k200": 50}})
    sn = _make_fake_results("S-N")
    with pytest.raises(AssertionError, match="solo_W"):
        assert_regression(st, sn)


def test_mutation_5_regression_e1b_count_499():
    """E1-B opt count 500→499 must cause assert_regression to raise AssertionError."""
    from evaluate_santiago_predictions import assert_regression
    st = _make_fake_results("S-T", overrides={"S3a": {
        "Q2_E1W_opt_k200": 80.2, "Q2_E1V_opt_k200": 84.2, "E1B_opt_count_k200": 499,
    }})
    sn = _make_fake_results("S-N")
    with pytest.raises(AssertionError, match="E1-B opt"):
        assert_regression(st, sn)


# ──────────────────────────────────────────────────────────────────────────────
# Mutation 6 — compute_value_regret: e1_fn=None must raise RuntimeError
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_6_e1_fn_mandatory():
    """Passing e1_fn=None to compute_value_regret must raise RuntimeError."""
    from santiago_eval_core import compute_value_regret
    d = _synthetic_regret_data()
    d["e1_fn"] = None   # mutation

    with pytest.raises(RuntimeError, match="e1_fn is required"):
        compute_value_regret(**d)


# ──────────────────────────────────────────────────────────────────────────────
# Mutation 7 — compute_value_regret: ULP check fires when f32 argmax ≠ f64 argmax
# Calls the PRODUCTION function with synthetic data engineered to trigger the check.
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_7_ulp_argmax_fail():
    """ULP check in compute_value_regret raises when f32 argmax != f64 argmax."""
    from santiago_eval_core import compute_value_regret

    # Build T=2 trios such that V_all = [3.0, 3.0 + delta] where delta < 1 ULP(f32)
    # → f64 argmax=1, f32 argmax=0 → Gate 4a ULP FAIL
    _eps32 = float(np.finfo(np.float32).eps)
    delta  = float(np.spacing(np.float32(3.0))) * 0.4 / 3.0   # < 1 float32 ULP of 3.0

    N, M = 6, 2
    X_mm = np.zeros((N, M))
    X_mm[:3, 0] = 1.0           # trio 0: X_trio = [3, 0]
    X_mm[3:, 0] = 1.0 + delta   # trio 1: X_trio = [3(1+delta), 0]

    trios = np.array([[0, 1, 2], [3, 4, 5]], dtype=np.int32)
    D     = np.ones((N, N)) * 20.0; np.fill_diagonal(D, 0.0)
    rho   = np.array([0.5, 0.5])   # A_V = rho for Gate 4d
    w0    = np.array([0.5, 0.5])

    # w = [1, 0]: V_all = [3.0, 3+3*delta] → f32 rounds to [3.0, 3.0], argmax=0
    W_draws = np.array([[1.0, 0.0]], dtype=np.float64)

    def e1_fn():
        return {"M": np.ones(2), "B": np.ones(2),
                "W": np.ones(2), "V": rho.copy()}

    # Sanity: verify the trigger condition
    V_all_test = np.array([3.0, 3.0 + 3 * delta])
    assert V_all_test.argmax() == 1, "test setup: f64 argmax must be 1"
    assert V_all_test.astype(np.float32).argmax() == 0, "test setup: f32 argmax must be 0"

    with pytest.raises(RuntimeError, match="ULP FAIL"):
        compute_value_regret(X_mm, trios, D, rho, W_draws, w0, e1_fn=e1_fn,
                             label="ULP-TEST", verbose=False)


# ──────────────────────────────────────────────────────────────────────────────
# Mutation 8 — Gate 3 row count: call _check_gate3_row_counts() from production
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_8_gate3_wrong_row_count():
    """_check_gate3_row_counts must raise RuntimeError(match='3001') for 3000 rows."""
    from evaluate_santiago_predictions import _check_gate3_row_counts

    with pytest.raises(RuntimeError, match="3001"):
        _check_gate3_row_counts(3000, 2004, "mc_ST_raw.csv", "mc_ST_e1_fix2.csv")


# ──────────────────────────────────────────────────────────────────────────────
# Mutation 9 — Oracle fogo R: +0.01 pp shift on draw 6 in _check_perdraw_tol
# Requires results/regret/regret_perdraw.csv; skips if absent.
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_9_oracle_fogo_shift(tmp_path):
    """Oracle Fogo R[draw 6, grd] + 0.01pp shift must raise via _check_perdraw_tol.

    Requires results/regret/regret_perdraw.csv. FAILS (not skips) if absent.
    """
    from evaluate_santiago_predictions import _check_perdraw_tol
    PERDRAW = ROOT / "results" / "regret" / "regret_perdraw.csv"
    if not PERDRAW.exists():
        pytest.fail(
            f"regret_perdraw.csv not found at {PERDRAW}. "
            "This file must exist; run compute_regret.py on Athena first."
        )

    df = pd.read_csv(PERDRAW)
    mask = (df["agg"] == "saw") & (df["norm"] == "vector") & (df["mont"] == "greedy")
    sub  = df[mask].sort_values("draw")
    assert len(sub) == 500, "expected 500 rows"

    oracle_r = sub["R"].values / 100.0          # fraction
    result_r = oracle_r.copy()
    result_r[6] += 0.01 / 100.0               # mutation: +0.01 pp = 1e-4 fraction >> 1e-12

    with pytest.raises(RuntimeError, match="per-draw"):
        _check_perdraw_tol(oracle_r, result_r, 1e-12, "grd-oracle-test")


# ──────────────────────────────────────────────────────────────────────────────
# Mutation 10 — E1-ABAR bug: e1_fn returns A_M != ones → Gate 4e PRE fires
# Simulates the bug where e1_fn uses per-draw w as w0 instead of fixed w0,
# which would give A_M != all-ones.
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_10_e1_abar_w_not_w0():
    """e1_fn with A_M != ones (E1-ABAR bug) must trigger Gate 4e PRE AssertionError."""
    from santiago_eval_core import compute_value_regret
    d = _synthetic_regret_data()
    rho = d["rho_j"]
    w0  = d["w0"]

    # Wrong e1_fn: A_M = w0 (not ones). Simulates using w instead of ones for E1-M.
    def bad_e1_fn():
        return {"M": w0.copy(),    # A_M != ones → Gate 4e fires
                "B": np.ones(len(w0)),
                "W": np.ones(len(w0)),
                "V": rho.copy()}

    d["e1_fn"] = bad_e1_fn
    with pytest.raises(AssertionError, match="Gate 4e PRE"):
        compute_value_regret(**d)


# ──────────────────────────────────────────────────────────────────────────────
# Mutations 11a–11c — Gate 4a: parametrized 7-array check + missing key + trios required
# ──────────────────────────────────────────────────────────────────────────────

_np11 = np  # alias for Gate 4a test fixtures (numpy already imported at module top)

# 7-entry trios array for Gate 4a tests; trios[0] = sites [0,1,2]
_TRIOS_T11 = _np11.array(
    [[0,1,2],[3,4,5],[6,7,8],[0,2,3],[1,3,5],[2,4,6],[0,3,6]], dtype=_np11.int32
)
_ALL_G3_KEYS = ["SAW_mm_opt","SAW_vec_opt","SAW_vec_grd","E1M_opt","E1B_opt","E1W_opt","E1V_opt"]
_KEY_TO_REGRET = {
    "SAW_mm_opt":  "trio_idx_mm_opt",
    "SAW_vec_opt": "trio_idx_vec_opt",
    "E1M_opt":     "trio_idx_e1m_opt",
    "E1B_opt":     "trio_idx_e1b_opt",
    "E1W_opt":     "trio_idx_e1w_opt",
    "E1V_opt":     "trio_idx_e1v_opt",
}

def _g3_base(B=3):
    """Gate3 dict with all 7 keys set to 0 for draws 0..B-1."""
    return {di: {k: 0 for k in _ALL_G3_KEYS} for di in range(B)}

def _regret_base(B=3):
    """compute_value_regret dict matching g3_base (all zeros, grd sites = trios[0])."""
    return {
        "trio_idx_mm_opt":   [0]*B,
        "trio_idx_vec_opt":  [0]*B,
        "trio_idx_e1m_opt":  [0]*B,
        "trio_idx_e1b_opt":  [0]*B,
        "trio_idx_e1w_opt":  [0]*B,
        "trio_idx_e1v_opt":  [0]*B,
        "trio_grd_vec_sites": [[0,1,2]]*B,   # matches _TRIOS_T11[0]
    }


@pytest.mark.parametrize("wrong_key", _ALL_G3_KEYS)
def test_mutation_11a_gate4a_each_array(wrong_key):
    """Each of the 7 Gate3 arrays triggers FAIL when draw 0 differs from EVAL-R."""
    from evaluate_santiago_predictions import _check_gate4a_identity
    B = 3
    g3     = _g3_base(B)
    regret = _regret_base(B)

    # Mutate: draw 0 in g3 differs from regret (g3 says 0, regret says 1)
    if wrong_key == "SAW_vec_grd":
        # Mismatch: regret grd_sites don't match _TRIOS_T11[0]=[0,1,2]
        regret["trio_grd_vec_sites"][0] = [10, 20, 30]
    elif wrong_key in _KEY_TO_REGRET:
        evalr_key = _KEY_TO_REGRET[wrong_key]
        regret[evalr_key][0] = 1   # different from g3 value (0)

    with pytest.raises(RuntimeError, match="Gate 4a identity FAIL"):
        _check_gate4a_identity(g3, regret, "TEST", trios=_TRIOS_T11)


def test_mutation_11b_gate4a_missing_key():
    """Gate 4a must FAIL if a required key is missing from g3_dict (no silent skip)."""
    from evaluate_santiago_predictions import _check_gate4a_identity
    B = 2
    g3     = _g3_base(B)
    regret = _regret_base(B)
    # Remove SAW_vec_grd from g3
    for di in g3:
        del g3[di]["SAW_vec_grd"]
    with pytest.raises(RuntimeError, match="Gate 4a identity FAIL"):
        _check_gate4a_identity(g3, regret, "TEST", trios=_TRIOS_T11)


def test_mutation_11c_gate4a_trios_required():
    """Gate 4a must FAIL (not skip) when trios is not provided."""
    from evaluate_santiago_predictions import _check_gate4a_identity
    B = 2
    g3     = _g3_base(B)
    regret = _regret_base(B)
    # Calling without trios: trios is now a required positional arg → TypeError,
    # OR RuntimeError if a None sentinel is passed
    with pytest.raises((RuntimeError, TypeError)):
        # No trios argument — either TypeError (missing arg) or RuntimeError
        _check_gate4a_identity(g3, regret, "TEST")


# ──────────────────────────────────────────────────────────────────────────────
# Mutation 12 — Sealed Q2 in memory: flip one cell value → _check_q2_cell raises
# Simulates a single in-memory Q2 modification during Gate 3 execution.
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_12_q2_sealed_mismatch():
    """_check_q2_cell raises when got=1 but exp=0 (flipped sealed Q2 value)."""
    from evaluate_santiago_predictions import _check_q2_cell
    with pytest.raises(RuntimeError, match="Gate 3 FAIL Q2"):
        _check_q2_cell(got=1, exp=0, kappa=200, draw=7, cell="SAW_mm_grd")


# ──────────────────────────────────────────────────────────────────────────────
# Mutation 13 — trio≠t* with R=0 forced: assert in compute_value_regret fires
# Constructs a TIE (two trios have identical SAW_mm score) so that:
#   argmax(V_mm)  = 0  (first in tie = t*)
#   argmax(V_e1b) = 1  (second trio wins on E1-B criterion)
#   R_e1b         = 0  (V_all[1] == V_all[0] by tie)
# This contradicts the invariant trio_neq_tstar <==> R_e1b > 0.
# ──────────────────────────────────────────────────────────────────────────────

def test_mutation_13_trio_neq_tstar_r_zero():
    """Tie construction: trio≠t* but R_e1b==0 must trigger assert in compute_value_regret."""
    from santiago_eval_core import compute_value_regret

    # N=6, M=2, T=2 trios
    # X_mm[:3] = [[1, 0], ...]: trio 0 → X_trio = [3, 0]
    # X_mm[3:] = [[0, 1], ...]: trio 1 → X_trio = [0, 3]
    # w = [0.5, 0.5]: V_mm[0] = 1.5, V_mm[1] = 1.5 → TIE
    # argmax(V_mm) = 0 (t*, first in tie)
    # A_B = [0, 1]: V_e1b[0] = 0, V_e1b[1] = 1.5 → argmax=1 (trio ≠ t*)
    # R_e1b = max(0, (1.5 - 1.5) / v_rng) = 0 → assert fires
    N, M = 6, 2
    X_mm = np.zeros((N, M), dtype=np.float64)
    X_mm[:3, 0] = 1.0  # trio 0: X_trio_0 = [3, 0]
    X_mm[3:, 1] = 1.0  # trio 1: X_trio_1 = [0, 3]

    trios   = np.array([[0, 1, 2], [3, 4, 5]], dtype=np.int32)
    D       = np.ones((N, N)) * 20.0; np.fill_diagonal(D, 0.0)
    rho     = np.array([0.5, 0.5])   # A_V = rho (Gate 4d)
    w0      = np.array([0.5, 0.5])
    W_draws = np.array([[0.5, 0.5]], dtype=np.float64)   # produces the tie

    def bad_e1_fn():
        return {
            "M": np.ones(2),          # A_M = ones (Gate 4e passes)
            "B": np.array([0.0, 1.0]),  # A_B: E1-B focuses on feature 1
            "W": np.ones(2),
            "V": rho.copy(),           # A_V = rho (Gate 4d passes)
        }

    # Verify tie and argmax conditions
    X_trio = np.array([[3.0, 0.0], [0.0, 3.0]])   # (2, 2) float64
    w_test = np.array([0.5, 0.5])
    V_all  = (X_trio * w_test).sum(1)
    assert V_all[0] == V_all[1] == 1.5, "test setup: V_mm must be a tie"
    assert int(V_all.argmax()) == 0, "test setup: f64 argmax of tie must be 0"
    V_e1b = (X_trio * np.array([0.0, 1.0]) * w_test).sum(1)
    assert int(V_e1b.argmax()) == 1, "test setup: E1-B argmax must be 1"

    with pytest.raises(AssertionError):
        compute_value_regret(X_mm, trios, D, rho, W_draws, w0,
                             e1_fn=bad_e1_fn, label="TIE-TEST", verbose=False)
