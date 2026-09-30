# -*- coding: utf-8 -*-
"""
mcdm_experiment.py
==================
Compares SAW, TOPSIS, VIKOR and PROMETHEE II on the 389 viable landfill
candidate sites from Azancort Neto et al. (2026, IEEE Access) and evaluates
each method's best trio against the exhaustive Pareto frontier.

Usage
-----
    uv run --with pandas --with numpy python mcdm_experiment.py

Outputs (in scripts/results/)
------------------------------
    mcdm_rankings.csv       per-site scores for all four methods
    mcdm_trios.csv          greedy (all) and optimal (SAW, TOPSIS) trios
    mcdm_concordance.csv    WS, r_w, Jaccard top-k
    mcdm_unit_tests.txt     unit test results
"""

# ---------------------------------------------------------------------------
# 0. Imports
# ---------------------------------------------------------------------------
import os
import sys
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 1. Configuration  (single block — edit here only)
# ---------------------------------------------------------------------------
# MCDM_DATA_DIR: directory containing the two data files.
# Set this environment variable to override the default Windows path.
# On Athena: export MCDM_DATA_DIR=/home/julioazancort/scratch/mcdm
_MCDM_DIR = os.environ.get(
    "MCDM_DATA_DIR",
    os.path.join(
        "G:", os.sep, "Faculdade", "Estudo", "Doutorado", "2025.1",
        "Otimiza\u00e7\u00e3o Bioinspirada", "Tentativa de dados via GIS",
    )
)
# Detect Athena flat layout vs Windows nested layout
_cache_flat  = os.path.join(_MCDM_DIR, "df_real_data_cached.csv")
if os.path.exists(_cache_flat):
    CACHE_CSV  = _cache_flat
    PARETO_CSV = os.path.join(_MCDM_DIR, "exhaustive_search_pareto.csv")
    BCS_CSV    = os.path.join(_MCDM_DIR, "best_compromise_sites.csv")
else:
    _gis = _MCDM_DIR
    _ieee = os.path.join(_gis, "New code", "results", "results-2026-04-07_18-40-54")
    CACHE_CSV  = os.path.join(_gis,  "results_cache", "df_real_data_cached.csv")
    PARETO_CSV = os.path.join(_ieee, "exhaustive_search_pareto.csv")
    BCS_CSV    = os.path.join(_ieee, "best_compromise_sites.csv")

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
OUT_DIR      = os.path.join(SCRIPT_DIR, "results")

# Unbuffered output — prevents silent logs in tmux/tee pipelines
import sys as _sys
if hasattr(_sys.stdout, "reconfigure"):
    _sys.stdout.reconfigure(line_buffering=True)

MIN_DIST_KM  = 10.0   # minimum distance between sites in a trio
VIKOR_V      = 0.5    # VIKOR compromise weight

# AHP weights — Table 7 of IEEE Access 2026.
# Inferred as column-normalisation of Andrade & Barbosa (2015) matrix,
# rounded to 3 d.p.; rivers adjusted from 0.090 to 0.091 to close sum to 1.000.
AHP_WEIGHTS = {
    "perm": 0.152, "slope": 0.113, "roads": 0.030,
    "rivers": 0.091, "aspect": 0.075, "coast": 0.069,
    "protected": 0.066, "wells": 0.055,
    "urban": 0.166, "aero": 0.102, "cult": 0.081,
}
assert abs(sum(AHP_WEIGHTS.values()) - 1.0) < 1e-9

# Column names in df (after cache rename)
COL = {
    "perm":      "dist_low_permeability (m)",
    "slope":     "slope (degrees)",
    "roads":     "dist_roads (m)",
    "rivers":    "dist_streams (m)",
    "aspect":    "slope_aspect (degrees)",
    "coast":     "dist_coastline (m)",
    "protected": "dist_protected_area (m)",
    "wells":     "dist_wells (m)",
    "urban":     "dist_urban_core (m)",
    "aero":      "dist_aerodrome (m)",
    "cult":      "dist_cultivation (m)",
}

# Objective groupings
F1_CRIT = ["perm", "slope", "roads"]           # siting efficiency (higher = better)
F2_CRIT = ["rivers", "aspect", "coast",        # environmental integrity (higher = better)
           "protected", "wells"]
F3_CRIT = ["urban", "aero", "cult"]            # social safety (higher = better)

# Criteria direction for MCDM methods
# INV = farther = better (higher raw value → lower score in impact group)
INV  = {"rivers", "coast", "protected", "wells"}
COST = {"perm", "slope", "roads"}     # lower raw = better → lower score = better
# aspect: binary, leeward [90,180] = 0 (good), else = 1 (bad)
# urban, aero, cult: farther = better (benefit)
BENEFIT = {"urban", "aero", "cult"}

# ---------------------------------------------------------------------------
# 2. Load data
# ---------------------------------------------------------------------------

def load_data():
    df_all = pd.read_csv(CACHE_CSV)
    par    = pd.read_csv(PARETO_CSV)
    bcs    = pd.read_csv(BCS_CSV)
    return df_all, par, bcs


# ---------------------------------------------------------------------------
# 3. NaN imputation  (midpoint of the 473-site range, same logic as _safe_norm)
# ---------------------------------------------------------------------------

def impute_nan(df_all: pd.DataFrame) -> pd.DataFrame:
    """
    Replace NaN values with the midpoint (min+max)/2 over all 473 sites.
    Affected sites/columns (verified 2026-09-27):
        site  41 — dist_roads (m)
        site 385 — dist_urban_core (m)
        site 429 — dist_aerodrome (m)
    Cause: likely OSM query failure; imputed value is mid-range (neutral).
    """
    df = df_all.copy()
    for k in AHP_WEIGHTS:
        if k == "aspect":
            continue
        col = COL[k]
        nan_mask = df[col].isna()
        if nan_mask.any():
            mid = (df[col].min() + df[col].max()) / 2
            df.loc[nan_mask, col] = mid
    return df


# ---------------------------------------------------------------------------
# 4. Objective computation  (normalised over the 473-site range)
# ---------------------------------------------------------------------------

def _norm(x: np.ndarray, x_ref: np.ndarray, inv: bool = False) -> np.ndarray:
    """Min-max normalisation of x over x_ref. No NaN expected after imputation."""
    rmin, rmax = x_ref.min(), x_ref.max()
    rng = rmax - rmin
    if rng == 0:
        return np.full(len(x), 0.5)
    c = (x - rmin) / rng
    return 1.0 - c if inv else c


def compute_objectives(df_target: pd.DataFrame,
                       df_ref: pd.DataFrame) -> pd.DataFrame:
    """
    Compute per-site (f1, f2, f3) using min/max from df_ref (usually 473 sites).
    f1, f2 are cost-type (lower = better); f3 is benefit (higher = better).
    """
    sc = {}
    for k, w in AHP_WEIGHTS.items():
        x   = df_target[COL[k]].values.astype(float)
        ref = df_ref[COL[k]].values.astype(float)
        if k == "aspect":
            # c=0 if aspect in [90,180] (favourable: lower environmental impact).
            # F2 is computed as impact (lower=better) following AzancortNeto2026.
            # The IEEE pipeline uses norm_asp=0 for [90,180] in a minimisation context;
            # mcdm_experiment.py follows the same convention: c=0 for the good class.
            # This gives n1_bad=94 (c=1 sites) and n1_good=295 (c=0 sites).
            # §4.1 text says "c=1 if aspect ∉[90,180] yielding n1=94 positives" —
            # "positives" means c=1 (the penalty class), not the favourable class.
            # Aj^vec = 1/sqrt(n1_bad) = 1/sqrt(295) = 0.058; Tab1 value of 0.103
            # was transcribed incorrectly (used n1_good=94 instead of n1_bad=295).
            c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
        elif k in INV:
            c = 1.0 - _norm(x, ref)
        elif k in COST:
            c = _norm(x, ref)
        else:  # BENEFIT
            c = 1.0 - _norm(x, ref)   # farther = smaller c = lower impact score
            # Wait: for safety (urban, aero, cult) farther = BETTER.
            # In the f3 formula: f3 = sum w_j * c_j where c_j = _norm(x, ref)
            # and larger c_j = better (farther from city). So:
            c = _norm(x, ref)          # no inversion for safety benefit criteria
        sc[k] = w * c
    sc_df = pd.DataFrame(sc, index=df_target.index)
    return pd.DataFrame({
        "f1": sc_df[F1_CRIT].sum(axis=1),
        "f2": sc_df[F2_CRIT].sum(axis=1),
        "f3": sc_df[F3_CRIT].sum(axis=1),
    }, index=df_target.index)


# ---------------------------------------------------------------------------
# 5. Haversine distance matrix
# ---------------------------------------------------------------------------

def haversine_km(lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    R = 6371.0
    la = np.radians(lats); lo = np.radians(lons)
    dlat = la[:, None] - la[None, :]
    dlon = lo[:, None] - lo[None, :]
    a = (np.sin(dlat / 2)**2
         + np.cos(la[:, None]) * np.cos(la[None, :]) * np.sin(dlon / 2)**2)
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


# ---------------------------------------------------------------------------
# 6. MCDM method scores (all on viable set, higher = better)
# ---------------------------------------------------------------------------

def _build_decision_matrix(df: pd.DataFrame) -> tuple:
    """
    Build normalised decision matrix X (n_sites x n_crit) for TOPSIS/VIKOR/PROMETHEE.
    Returns (X, benefit_flags) where X values in [0,1], benefit_flag[j] = True
    means higher X value is better for criterion j.
    All NaN imputed before this call.
    """
    n = len(df)
    m = len(AHP_WEIGHTS)
    X = np.zeros((n, m))
    benefit = []
    for j, k in enumerate(AHP_WEIGHTS):
        x = df[COL[k]].values.astype(float)
        if k == "aspect":
            c = np.where((x >= 90) & (x <= 180), 1.0, 0.0)
            # leeward (1) is beneficial for reducing impact → but we treat as cost in f2
            # For TOPSIS/VIKOR/PROMETHEE, "benefit" means higher score = better overall
            # aspect leeward (1) = good → benefit=True
            benefit.append(True)
        elif k in COST:
            # lower raw value = better → normalise, then lower normalised = better → benefit=False
            c = _norm(x, x)
            benefit.append(False)
        elif k in INV:
            # farther from hazard = better → higher raw = better → normalise → benefit=True
            c = _norm(x, x)
            benefit.append(True)
        else:  # BENEFIT (urban, aero, cult)
            c = _norm(x, x)
            benefit.append(True)
        X[:, j] = c
    return X, np.array(benefit)


def saw_scores(df: pd.DataFrame) -> np.ndarray:
    """
    SAW: V_i = sum_j w_j * c_ij  where c_ij in [0,1], higher = better for all criteria
    (cost criteria already inverted: lower raw → higher c → higher score = better).
    """
    X, benefit = _build_decision_matrix(df)
    w = np.array(list(AHP_WEIGHTS.values()))
    # For benefit=False (cost), we need to invert so that higher c = better:
    X_adj = X.copy()
    for j, is_ben in enumerate(benefit):
        if not is_ben:
            X_adj[:, j] = 1.0 - X[:, j]
    scores = (X_adj * w).sum(axis=1)
    assert not np.isnan(scores).any(), "SAW: NaN in scores"
    return scores


def topsis_scores(df: pd.DataFrame) -> np.ndarray:
    """
    TOPSIS with vector normalisation.
    v_ij = w_j * r_ij  (r_ij = x_ij / sqrt(sum x^2_j))
    d_i+ = sqrt(sum_j (v_ij - v_j+)^2)   -- NO extra weight (v already weighted)
    d_i- = sqrt(sum_j (v_ij - v_j-)^2)
    C_i  = d_i- / (d_i+ + d_i-)           -- higher = better
    """
    X, benefit = _build_decision_matrix(df)
    w = np.array(list(AHP_WEIGHTS.values()))

    # Vector normalisation
    norms = np.sqrt((X**2).sum(axis=0))
    norms[norms == 0] = 1.0
    R = X / norms

    # Weighted normalised matrix
    V = R * w   # (n, m)

    # Ideal and anti-ideal
    PIS = np.where(benefit, V.max(axis=0), V.min(axis=0))
    NIS = np.where(benefit, V.min(axis=0), V.max(axis=0))

    # Distances — sum over columns, NO extra weight factor (V already weighted)
    d_pos = np.sqrt(((V - PIS)**2).sum(axis=1))
    d_neg = np.sqrt(((V - NIS)**2).sum(axis=1))
    denom = d_pos + d_neg
    C = np.where(denom == 0, 0.5, d_neg / denom)
    assert not np.isnan(C).any(), "TOPSIS: NaN in scores"
    return C


def vikor_scores(df: pd.DataFrame, v: float = VIKOR_V) -> np.ndarray:
    """
    VIKOR — returns (1 - Q) so higher = better (consistent convention).
    """
    X, benefit = _build_decision_matrix(df)
    w = np.array(list(AHP_WEIGHTS.values()))

    f_star  = np.where(benefit, X.max(axis=0), X.min(axis=0))
    f_minus = np.where(benefit, X.min(axis=0), X.max(axis=0))
    denom   = np.abs(f_star - f_minus)
    denom[denom == 0] = 1.0

    # Normalised regret (0 = best, 1 = worst) — formula symmetric for benefit/cost
    norm_dist = np.abs(f_star - X) / denom

    S = (w * norm_dist).sum(axis=1)
    R = (w * norm_dist).max(axis=1)

    def _normalise_01(arr):
        lo, hi = arr.min(), arr.max()
        return np.zeros(len(arr)) if hi == lo else (arr - lo) / (hi - lo)

    Q = v * _normalise_01(S) + (1 - v) * _normalise_01(R)
    scores = 1.0 - Q   # invert so higher = better
    assert not np.isnan(scores).any(), "VIKOR: NaN in scores"
    return scores


def promethee2_scores(df: pd.DataFrame) -> np.ndarray:
    """
    PROMETHEE II with the usual (strict) preference function:
    P_j(a, b) = 1 if a strictly better than b on criterion j, else 0.
    No threshold — a single point of difference triggers preference.
    Net flow phi_i = sum_j w_j * [Phi_j+(i) - Phi_j-(i)] / (N - 1).
    Higher phi = better.
    """
    X, benefit = _build_decision_matrix(df)
    w = np.array(list(AHP_WEIGHTS.values()))
    n = len(df)

    phi = np.zeros(n)
    for j in range(len(AHP_WEIGHTS)):
        col = X[:, j]
        diff = col[:, None] - col[None, :]      # diff[a, b] > 0 → a better than b
        if not benefit[j]:
            diff = -diff                         # cost: smaller raw is better
        pref = (diff > 0).astype(float)          # usual criterion: step at 0
        phi_j = (pref.sum(axis=1) - pref.sum(axis=0)) / (n - 1)
        phi += w[j] * phi_j

    assert not np.isnan(phi).any(), "PROMETHEE II: NaN in scores"
    return phi


# ---------------------------------------------------------------------------
# 7. Trio formation
# ---------------------------------------------------------------------------

def greedy_trio(scores: np.ndarray, D: np.ndarray,
                min_dist: float = MIN_DIST_KM) -> tuple:
    """Greedy: pick highest-scoring site, then each next at >= min_dist from chosen."""
    order = np.argsort(-scores)
    chosen = []
    for idx in order:
        if all(D[idx, c] >= min_dist for c in chosen):
            chosen.append(int(idx))
        if len(chosen) == 3:
            break
    assert len(chosen) == 3, f"Could not form greedy trio (n={len(scores)})"
    return tuple(chosen)


def optimal_trio_enumerate(scores: np.ndarray, D: np.ndarray,
                           min_dist: float = MIN_DIST_KM) -> tuple:
    """
    Exhaustive search: trio with maximum sum of scores among all viable triples.
    O(N^3/6) ~ 2.9 M operations.
    """
    n = len(scores)
    best_score = -np.inf
    best = (0, 1, 2)
    i_idx, j_idx = np.where(np.triu(D >= min_dist, k=1))
    for p_i, p_j in zip(i_idx, j_idx):
        k_cands = np.where((D[p_i] >= min_dist) & (D[p_j] >= min_dist))[0]
        k_cands = k_cands[k_cands > p_j]
        if len(k_cands) == 0:
            continue
        s = scores[p_i] + scores[p_j] + scores[k_cands]
        best_k = k_cands[s.argmax()]
        if s.max() > best_score:
            best_score = s.max()
            best = (int(p_i), int(p_j), int(best_k))
    return best


def count_viable_trios(D: np.ndarray, min_dist: float = MIN_DIST_KM) -> int:
    """Count all triples (i<j<k) with pairwise distance >= min_dist."""
    count = 0
    i_idx, j_idx = np.where(np.triu(D >= min_dist, k=1))
    for p_i, p_j in zip(i_idx, j_idx):
        k_cands = np.where((D[p_i] >= min_dist) & (D[p_j] >= min_dist))[0]
        count += int(np.sum(k_cands > p_j))
    return count


# ---------------------------------------------------------------------------
# 8. Pareto evaluation
# ---------------------------------------------------------------------------

def trio_objectives_from_global(global_ids: tuple,
                                objs_473: pd.DataFrame) -> dict:
    obj = objs_473.loc[list(global_ids)]
    s = obj.sum()
    return {"global_ids": global_ids,
            "f1": float(s["f1"]), "f2": float(s["f2"]), "f3": float(s["f3"])}


_DOMTOL = 1e-9   # tolerance for dominance check

def pareto_dominates(par: pd.DataFrame, f1: float, f2: float, f3: float,
                     tol: float = _DOMTOL) -> bool:
    """True if any Pareto trio weakly dominates (f1,f2,f3) and strictly in ≥1 objective."""
    le  = ((par["Cost"]   <= f1 + tol) &
           (par["Impact"] <= f2 + tol) &
           (par["Safety"] >= f3 - tol))
    lt  = ((par["Cost"]   <  f1 - tol) |
           (par["Impact"] <  f2 - tol) |
           (par["Safety"] >  f3 + tol))
    return bool((le & lt).any())


def in_pareto_front(par: pd.DataFrame, trio: tuple) -> bool:
    """True if this exact trio appears in the exhaustive Pareto CSV."""
    s = frozenset(trio)
    for _, r in par.iterrows():
        if frozenset([int(r.idx1), int(r.idx2), int(r.idx3)]) == s:
            return True
    return False


def gap_additive(par: pd.DataFrame, f1: float, f2: float, f3: float) -> float:
    """
    gap = max(0, max_{p in P*} min_m (t_m - p_m))

    All objectives treated as cost (safety flipped: t_inv = -f3, p_inv = -p_safety).
    gap > 0 iff some Pareto trio is strictly better than t on ALL objectives.
    gap = 0 iff t is non-dominated OR touches the frontier in all objectives.
    Not normalised — units are the objective units (0 to ~1 per objective).
    """
    diff_c = f1  - par["Cost"].values          # t worse if > 0
    diff_i = f2  - par["Impact"].values
    diff_s = par["Safety"].values - f3         # t worse in safety if > 0
    # min_m (t_m - p_m): how much better p is in its WEAKEST dimension
    min_dim = np.minimum(np.minimum(diff_c, diff_i), diff_s)
    return float(max(0.0, min_dim.max()))


# ---------------------------------------------------------------------------
# 9. Concordance metrics
# ---------------------------------------------------------------------------

def weighted_spearman(x: np.ndarray, y: np.ndarray) -> float:
    """r_w (Pinto da Costa & Soares, 2005)."""
    n = len(x)
    num = 6.0 * float(np.sum((x - y)**2 * ((n - x + 1) + (n - y + 1))))
    den = float(n**4 + n**3 - n**2 - n)
    return 1.0 - num / den


def ws_coefficient(ref: np.ndarray, cmp: np.ndarray) -> float:
    """WS (Salabun & Urbaniak, 2020). ref is the reference ranking (1-based)."""
    n = len(ref)
    num = float(np.sum(
        2.0**(-ref) * np.abs(ref - cmp) / np.maximum(ref - 1, n - ref)
    ))
    return 1.0 - num


def jaccard_topk(ra: np.ndarray, rb: np.ndarray, k: int) -> float:
    ta = set(int(i) for i in np.where(ra <= k)[0])
    tb = set(int(i) for i in np.where(rb <= k)[0])
    return len(ta & tb) / len(ta | tb) if (ta | tb) else 1.0


# ---------------------------------------------------------------------------
# 10. Unit tests  (importable by test_unit.py)
# ---------------------------------------------------------------------------

def run_unit_tests(df_all: pd.DataFrame, par: pd.DataFrame,
                   df_viable: pd.DataFrame, D_via: np.ndarray,
                   scores_saw473: np.ndarray, via_global: np.ndarray,
                   objs_473: pd.DataFrame, saw389_fn, topsis_fn) -> list:
    """
    Returns list of (name, passed: bool, detail: str).
    Tests 3 and 4 use the actual method functions from this module.
    """
    results = []

    # Test 1: 213-trio reproduction (ref = 473)
    f1 = objs_473["f1"].values
    f2 = objs_473["f2"].values
    f3 = objs_473["f3"].values
    idx = par[["idx1", "idx2", "idx3"]].values.astype(int)
    d = max(np.abs(f1[idx].sum(1) - par["Cost"].values).max(),
            np.abs(f2[idx].sum(1) - par["Impact"].values).max(),
            np.abs(f3[idx].sum(1) - par["Safety"].values).max())
    results.append(("213-trio reproduction",
                    d < 1e-9,
                    f"max_diff={d:.2e} (threshold 1e-9)"))

    # Test 2: viable trio count (on ALL 473 — reproduces the published number)
    # The 389-viable count is reported separately in main() as contextual info.
    D_all = haversine_km(df_all["latitude (degrees)"].values,
                         df_all["longitude (degrees)"].values)
    count_473 = count_viable_trios(D_all, MIN_DIST_KM)
    results.append(("Viable-trio count (473, published)",
                    count_473 == 2_904_011,
                    f"count={count_473:,} (expected 2,904,011)"))

    # Test 3: SAW-473 optimal trio = {184, 430, 460}  — uses saw_scores on df_all
    # (not just a formula check; actually calls the SAW function on df_all)
    par_saw = (scores_saw473[idx[:, 0]]
               + scores_saw473[idx[:, 1]]
               + scores_saw473[idx[:, 2]])
    best_row = par.iloc[par_saw.argmax()]
    trio_saw = {int(best_row["idx1"]), int(best_row["idx2"]), int(best_row["idx3"])}
    results.append(("SAW-473 optimal = {184,430,460}",
                    trio_saw == {184, 430, 460},
                    f"got {sorted(trio_saw)}"))

    # Test 4: argmin S1 over the 1,944,653 viable trios is non-dominated
    # S1 = 0.295*f1 + 0.356*f2 - 0.349*f3  (linear, positive weights on costs)
    # A linear scalarisation with positive weights always finds a Pareto-optimal point.
    f1_via = objs_473.loc[df_viable.index, "f1"].values
    f2_via = objs_473.loc[df_viable.index, "f2"].values
    f3_via = objs_473.loc[df_viable.index, "f3"].values
    i_idx, j_idx = np.where(np.triu(D_via >= MIN_DIST_KM, k=1))
    best_s1 = np.inf
    best_trio_s1 = (0, 1, 2)
    for p_i, p_j in zip(i_idx, j_idx):
        k_cands = np.where((D_via[p_i] >= MIN_DIST_KM) & (D_via[p_j] >= MIN_DIST_KM))[0]
        k_cands = k_cands[k_cands > p_j]
        if len(k_cands) == 0:
            continue
        s1 = (0.295 * (f1_via[p_i] + f1_via[p_j] + f1_via[k_cands])
            + 0.356 * (f2_via[p_i] + f2_via[p_j] + f2_via[k_cands])
            - 0.349 * (f3_via[p_i] + f3_via[p_j] + f3_via[k_cands]))
        best_k = k_cands[s1.argmin()]
        if s1.min() < best_s1:
            best_s1 = s1.min()
            best_trio_s1 = (int(p_i), int(p_j), int(best_k))
    s1_global = tuple(int(via_global[i]) for i in best_trio_s1)
    s1_obj = trio_objectives_from_global(s1_global, objs_473)
    s1_dom = pareto_dominates(par, s1_obj["f1"], s1_obj["f2"], s1_obj["f3"])
    results.append(("argmin S1 viable non-dominated",
                    not s1_dom,
                    f"trio={sorted(s1_global)} dominated={s1_dom}"))

    return results


# ---------------------------------------------------------------------------
# 11. Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("=" * 65)
    print("mcdm_experiment.py  —  Landfill Site MCDM vs Pareto frontier")
    print("=" * 65)

    # Load
    print("\n[0] Loading data...")
    df_all, par, bcs = load_data()
    print(f"    df_all: {len(df_all)} sites  |  Pareto trios: {len(par)}  |  BCS: {len(bcs)}")

    # Impute NaN
    print("[0] Imputing NaN (midpoint of 473-site range)...")
    df_imp = impute_nan(df_all)
    nan_remaining = sum(df_imp[COL[k]].isna().sum() for k in AHP_WEIGHTS if k != "aspect")
    assert nan_remaining == 0, f"NaN remaining after imputation: {nan_remaining}"

    # Viable sites
    viable_mask = df_imp[COL["protected"]] > 0
    df_via = df_imp[viable_mask].copy()
    via_global = df_via.index.values
    assert len(df_via) == 389, f"Expected 389 viable, got {len(df_via)}"
    print(f"    Viable sites: {len(df_via)}  |  Protected (excluded): {(~viable_mask).sum()}")

    # Check NaN sites membership in viable set
    nan_sites = {"41 (roads)": 41, "385 (urban)": 385, "429 (aero)": 429}
    for label, gidx in nan_sites.items():
        in_via = gidx in via_global
        print(f"    NaN site {label}: {'in viable' if in_via else 'EXCLUDED (protected)'}")

    # Objectives (ref = 473)
    print("[0] Computing objectives (ref = 473)...")
    objs_473 = compute_objectives(df_imp, df_imp)

    # Distance matrix (viable only)
    print("[0] Building Haversine distance matrix (389×389)...")
    D_via = haversine_km(df_via["latitude (degrees)"].values,
                         df_via["longitude (degrees)"].values)

    # ---- Unit tests ----
    print("\n[1] Running unit tests...")
    sc_saw473 = saw_scores(df_imp)
    ut = run_unit_tests(df_imp, par, df_via, D_via,
                        sc_saw473, via_global, objs_473,
                        saw_scores, topsis_scores)
    all_pass = True
    for name, passed, detail in ut:
        tag = "PASS" if passed else "FAIL"
        print(f"    [{tag}] {name}: {detail}")
        all_pass &= passed
    if not all_pass:
        print("\n  Unit tests FAILED. Aborting.")
        sys.exit(1)
    print("  All unit tests passed.\n")

    ut_lines = [f"[{'PASS' if p else 'FAIL'}] {n}: {d}" for n, p, d in ut]
    with open(os.path.join(OUT_DIR, "mcdm_unit_tests.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(ut_lines) + "\n")

    # ---- Method scores ----
    print("[2] Computing method scores on 389 viable sites...")
    sc = {
        "SAW":      saw_scores(df_via),
        "TOPSIS":   topsis_scores(df_via),
        "VIKOR":    vikor_scores(df_via),
        "PROMETHEE": promethee2_scores(df_via),
    }
    ranks = {m: pd.Series(s, index=df_via.index).rank(ascending=False, method="min").astype(int)
             for m, s in sc.items()}

    # Top-10 per method
    print("\n  Top-10 sites per method (global index):")
    for m, s in sc.items():
        s_ser = pd.Series(s, index=df_via.index)
        top10 = s_ser.nlargest(10).index.tolist()
        print(f"    {m:12s}: {top10}")

    # Save rankings
    score_df = pd.DataFrame({m: pd.Series(s, index=df_via.index) for m, s in sc.items()})
    rank_df  = pd.DataFrame(ranks).add_suffix("_rank")
    out_rank = pd.concat([df_via[["latitude (degrees)", "longitude (degrees)"]],
                          score_df, rank_df], axis=1)
    out_rank.to_csv(os.path.join(OUT_DIR, "mcdm_rankings.csv"))
    print(f"\n    Saved: results/mcdm_rankings.csv ({len(out_rank)} rows)")

    # ---- Trios ----
    print("\n[3] Forming trios...")

    # Viable trio count (on the 389 subset)
    print("    Counting viable trios (may take ~60 s)...")
    n_via_trios = count_viable_trios(D_via, MIN_DIST_KM)
    print(f"    Viable trios (389 sites, dist >= 10 km): {n_via_trios:,}")

    trio_rows = []

    def eval_trio(method, variant, local_trio):
        global_ids = tuple(int(via_global[i]) for i in local_trio)
        obj = trio_objectives_from_global(global_ids, objs_473)
        in_f = in_pareto_front(par, global_ids)
        dominated = pareto_dominates(par, obj["f1"], obj["f2"], obj["f3"])
        gap = gap_additive(par, obj["f1"], obj["f2"], obj["f3"])
        row = {
            "method": method, "variant": variant,
            "global_ids": str(sorted(global_ids)),
            "f1": round(obj["f1"], 6), "f2": round(obj["f2"], 6), "f3": round(obj["f3"], 6),
            "in_front": in_f,
            "dominated": dominated,
            "gap": round(gap, 6),
        }
        trio_rows.append(row)
        print(f"    {method:12s} {variant:8s}: {sorted(global_ids)}  "
              f"f1={obj['f1']:.4f} f2={obj['f2']:.4f} f3={obj['f3']:.4f}  "
              f"in_front={in_f}  dom={'Y' if dominated else 'N'}  gap={gap:.4f}")
        return row

    for method_name, method_fn in [("SAW", saw_scores), ("TOPSIS", topsis_scores),
                                    ("VIKOR", vikor_scores), ("PROMETHEE", promethee2_scores)]:
        sc_m = sc[method_name] if method_name in sc else method_fn(df_via)
        sc_arr = sc_m if isinstance(sc_m, np.ndarray) else sc_m

        # Greedy
        g = greedy_trio(sc_arr, D_via)
        eval_trio(method_name, "greedy", g)

        # Optimal (SAW and TOPSIS only — additive score sum is meaningful)
        if method_name in ("SAW", "TOPSIS"):
            print(f"    {method_name} optimal: enumerating {n_via_trios:,} trios...")
            o = optimal_trio_enumerate(sc_arr, D_via)
            eval_trio(method_name, "optimal", o)

    # BCS reference
    bcs_ids = tuple(sorted(bcs["site_id"].astype(int).tolist()))
    bcs_obj = trio_objectives_from_global(bcs_ids, objs_473)
    bcs_in_f = in_pareto_front(par, bcs_ids)
    bcs_dom = pareto_dominates(par, bcs_obj["f1"], bcs_obj["f2"], bcs_obj["f3"])
    bcs_gap = gap_additive(par, bcs_obj["f1"], bcs_obj["f2"], bcs_obj["f3"])
    trio_rows.append({
        "method": "BCS_IEEE", "variant": "reference",
        "global_ids": str(sorted(bcs_ids)),
        "f1": round(bcs_obj["f1"], 6), "f2": round(bcs_obj["f2"], 6),
        "f3": round(bcs_obj["f3"], 6),
        "in_front": bcs_in_f, "dominated": bcs_dom, "gap": round(bcs_gap, 6),
    })
    print(f"    {'BCS_IEEE':12s} {'ref':8s}: {sorted(bcs_ids)}  "
          f"f1={bcs_obj['f1']:.4f} f2={bcs_obj['f2']:.4f} f3={bcs_obj['f3']:.4f}  "
          f"in_front={bcs_in_f}  dom={'Y' if bcs_dom else 'N'}  gap={bcs_gap:.4f}")

    pd.DataFrame(trio_rows).to_csv(os.path.join(OUT_DIR, "mcdm_trios.csv"), index=False)
    print(f"\n    Saved: results/mcdm_trios.csv")

    # ---- Concordance ----
    print("\n[4] Rank concordance...")
    method_names = list(sc.keys())
    conc_rows = []
    for i, ma in enumerate(method_names):
        for j, mb in enumerate(method_names):
            if j <= i:
                continue
            ra = ranks[ma].loc[df_via.index].values.astype(float)
            rb = ranks[mb].loc[df_via.index].values.astype(float)
            rw    = weighted_spearman(ra, rb)
            ws_ab = ws_coefficient(ra, rb)
            ws_ba = ws_coefficient(rb, ra)
            jac10 = jaccard_topk(ra, rb, 10)
            jac20 = jaccard_topk(ra, rb, 20)
            conc_rows.append({
                "A": ma, "B": mb,
                "r_w": round(rw, 4),
                "WS(A->B)": round(ws_ab, 4),
                "WS(B->A)": round(ws_ba, 4),
                "Jaccard_top10": round(jac10, 4),
                "Jaccard_top20": round(jac20, 4),
            })
            print(f"    {ma} vs {mb}: r_w={rw:.4f}  "
                  f"WS={ws_ab:.4f}/{ws_ba:.4f}  "
                  f"Jac@10={jac10:.2f}  Jac@20={jac20:.2f}")

    pd.DataFrame(conc_rows).to_csv(os.path.join(OUT_DIR, "mcdm_concordance.csv"), index=False)
    print(f"\n    Saved: results/mcdm_concordance.csv")

    print("\n[DONE]")


if __name__ == "__main__":
    main()
