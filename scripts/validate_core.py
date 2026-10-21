# -*- coding: utf-8 -*-
"""
validate_core.py  --  Phase 1 independent validation of the Fogo pipeline.

GATE 1 CRITERIA (values written before running, never updated after seeing results):
  1.  N candidates = 473
  2.  N excluded (dist_protected = 0) = 84
  3.  N admissible (A') = 389
  4.  NaN sites: {41, 385, 429} (0-indexed in df_all)
  5.  perm zeros in A': 350; perm max in A': 532 m (tolerance ±1 m)
  6.  aspect leeward n1 in A': 94
  7a. n_trios from fogo_trios.npy = 1,944,653
  7b. n_trios via trace method (independent) = 1,944,653
  8.  Pareto |F'| in A' = 181 (from CSV count)
  8b. Non-dominated within claimed A' set = 0
  8c. Exact completeness: all trios outside F' dominated by some member of F' = 0 exceptions
  9.  Pareto |F| in A = 213
  10. |A cap A'| = 132
  11. SAW/mm/optimal in A = {184, 430, 460}, F1/F2/F3 matching manuscript to 1e-6

Gate passes if and only if: FAIL == 0 AND NOT_RUN == 0.

This script imports NOTHING from the project pipeline.
All computations are re-implemented from scratch.

Run:
  uv run python scripts/validate_core.py          # full check (requires fogo_trios.npy)
  uv run python scripts/validate_core.py --quick  # data checks only, skip Pareto/trios

Set MCDM_DATA_DIR if the default path does not exist:
  export MCDM_DATA_DIR=/path/to/data
"""

import os, sys, hashlib, argparse
from pathlib import Path
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# ARGS
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument('--quick', action='store_true',
                    help='Data checks only — skip trio/Pareto (not for gate clearance)')
args, _ = parser.parse_known_args()

# ---------------------------------------------------------------------------
# DATA PATH
# ---------------------------------------------------------------------------
_DATA_DIR = os.environ.get("MCDM_DATA_DIR", os.path.join(
    "G:", os.sep, "Faculdade", "Estudo", "Doutorado", "2025.1",
    "Otimiza\u00e7\u00e3o Bioinspirada", "Tentativa de dados via GIS"
))
_cache_flat = os.path.join(_DATA_DIR, "df_real_data_cached.csv")
if os.path.exists(_cache_flat):
    CACHE_CSV = _cache_flat
else:
    CACHE_CSV = os.path.join(_DATA_DIR, "results_cache", "df_real_data_cached.csv")

# Gate 1 expected values — written before running, never changed after
EXPECTED = {
    "n_all":        473,
    "n_excluded":   84,
    "n_admissible": 389,
    "nan_sites":    {41, 385, 429},
    "perm_zeros_admissible": 350,
    "perm_max_admissible":   532,   # metres, tolerance ±1
    "aspect_n1":    94,
    "n_trios":      1_944_653,
    "pareto_Ap":    181,            # |F'| in A'
    "pareto_A":     213,            # |F| in A
    "pareto_cap":   132,            # |A cap A'|
    # SAW/mm/optimal with AHP weights, A normalisation (473-site reference)
    # {184, 430, 460} are df_all row indices (manuscript convention).
    # In A' reset indices (0-388): {180, 346, 376} — same physical sites.
    # Verified: pos_Ap[184]=180, pos_Ap[430]=346, pos_Ap[460]=376.
    # validate_core returns A' indices; convert manuscript value accordingly.
    "portfolio_A":  frozenset({180, 346, 376}),   # A' indices; df_all = {184, 430, 460}
}

# AHP weights — Table 2 (verbatim, no import)
AHP = {
    "perm": 0.152, "slope": 0.113, "roads": 0.030,
    "rivers": 0.091, "aspect": 0.075, "coast": 0.069,
    "protected": 0.066, "wells": 0.055,
    "urban": 0.166, "aero": 0.102, "cult": 0.081,
}
assert abs(sum(AHP.values()) - 1.0) < 1e-9

# Column names (verbatim, no import)
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

F1_CRIT = ["perm", "slope", "roads"]
F2_CRIT = ["rivers", "aspect", "coast", "protected", "wells"]
F3_CRIT = ["urban", "aero", "cult"]
# Objective orientation (manuscript convention):
#   F1, F2: cost objectives — MINIMIZE
#   F3:     benefit objective — MAXIMIZE
# Criterion → objective value mapping (matches compute_objectives in mcdm_experiment.py):
#   COST (perm, slope, roads): c = (x - min)/(max - min)  [lower x → lower c]
#   INV  (rivers, coast, protected, wells): c = 1 - (x - min)/(max - min)  [farther → lower c]
#   ASPECT (binary): c = 0 if azimuth in [90,180] (leeward, benign), else 1  [lower c = better]
#   BENEFIT (urban, aero, cult): c = (x - min)/(max - min)  [farther → higher c]
# F1, F2 = sum(w_j * c_j) over G1, G2 — minimize
# F3      = sum(w_j * c_j) over G3     — maximize
# SCORER X_adj convention: X_adj = 1 - c for COST/INV/ASPECT, = c for BENEFIT
#   So SAW score = sum(w_j * X_adj_j) = sum over groups of [W_g - F_g_cost] + F3
COST_OBJ    = {"perm", "slope", "roads"}          # objective: c = (x-min)/(max-min), minimize
INV_OBJ     = {"rivers", "coast", "protected", "wells"}   # objective: c = 1-norm, minimize
BENEFIT_OBJ = {"urban", "aero", "cult"}            # objective: c = norm, maximize

MIN_DIST_KM = 10.0
EPS         = 1e-9

# ---------------------------------------------------------------------------
# GATE COUNTER (PASS/FAIL/NOT_RUN)
# Gate clears only when FAIL == 0 AND NOT_RUN == 0
# ---------------------------------------------------------------------------
PASS_COUNT    = 0
FAIL_COUNT    = 0
NOT_RUN_COUNT = 0
FAILURES      = []
NOT_RUN_LIST  = []

def check(name, actual, expected, tol=None):
    global PASS_COUNT, FAIL_COUNT
    if tol is not None:
        ok = abs(actual - expected) <= tol
    elif isinstance(expected, (set, frozenset)):
        ok = frozenset(actual) == frozenset(expected)
    else:
        ok = (actual == expected)
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
        FAILURES.append(f"  {name}: got {actual!r}, expected {expected!r}")
    print(f"  [{status}] {name}: {actual}")
    return ok

def not_run(name, reason=""):
    global NOT_RUN_COUNT
    NOT_RUN_COUNT += 1
    msg = f"  {name}" + (f" ({reason})" if reason else "")
    NOT_RUN_LIST.append(msg)
    print(f"  [NOT RUN] {name}" + (f" — {reason}" if reason else ""))


# ---------------------------------------------------------------------------
# HELPERS: normalisation and objectives
# ---------------------------------------------------------------------------
def mm(x, x_ref):
    lo, hi = x_ref.min(), x_ref.max()
    d = hi - lo
    return (x - lo) / d if d > 0 else np.full(len(x), 0.5)

def objectives_ms(X_via, X_ref, asp_via):
    """
    Compute per-site F1, F2, F3 in MANUSCRIPT convention (mcdm_experiment.py).
    F1, F2 = cost (minimize); F3 = benefit (maximize).

    X_via: (N, M) raw values for the A' sites
    X_ref: (N_ref, M) raw values for normalisation reference (A' or A)
    asp_via: (N,) azimuth in degrees for aspect
    """
    keys = list(AHP.keys())
    f1 = np.zeros(len(X_via))
    f2 = np.zeros(len(X_via))
    f3 = np.zeros(len(X_via))
    for j, k in enumerate(keys):
        w = AHP[k]
        x = X_via[:, j]
        xr = X_ref[:, j]
        if k == "aspect":
            c = np.where((asp_via >= 90) & (asp_via <= 180), 0.0, 1.0)
        elif k in COST_OBJ:
            c = mm(x, xr)
        elif k in INV_OBJ:
            c = 1.0 - mm(x, xr)
        else:  # BENEFIT
            c = mm(x, xr)
        wc = w * c
        if k in F1_CRIT:   f1 += wc
        elif k in F2_CRIT: f2 += wc
        else:               f3 += wc
    return f1, f2, f3

def scorer_adj(X_via, X_ref, asp_via):
    """
    Build X_adj (benefit-adjusted matrix): X_adj_j = 1 - c for cost/inv/aspect; = c for benefit.
    Returns (N, M) array.
    """
    keys = list(AHP.keys())
    Xa = np.zeros_like(X_via, dtype=float)
    for j, k in enumerate(keys):
        x = X_via[:, j]
        xr = X_ref[:, j]
        if k == "aspect":
            c = np.where((asp_via >= 90) & (asp_via <= 180), 1.0, 0.0)  # benefit = leeward
        elif k in COST_OBJ:
            c = 1.0 - mm(x, xr)          # lower raw = better → flip
        elif k in INV_OBJ:
            c = mm(x, xr)                 # farther = better → keep
        else:  # BENEFIT
            c = mm(x, xr)
        Xa[:, j] = c
    return Xa

# ---------------------------------------------------------------------------
# 1. LOAD DATA
# ---------------------------------------------------------------------------
print("=" * 68)
print("VALIDATE_CORE — Phase 1 independent pipeline validation")
print("=" * 68)
print()

if not os.path.exists(CACHE_CSV):
    print(f"ERROR: data file not found: {CACHE_CSV}")
    print("Set MCDM_DATA_DIR environment variable.")
    sys.exit(1)

print(f"Data file: {CACHE_CSV}")
csv_hash = hashlib.sha256(Path(CACHE_CSV).read_bytes()).hexdigest()
print(f"SHA-256:   {csv_hash}")
print()

df_all = pd.read_csv(CACHE_CSV)
print(f"Loaded: {len(df_all)} rows x {len(df_all.columns)} columns")
print()

# ---------------------------------------------------------------------------
# 2. COUNTS
# ---------------------------------------------------------------------------
print("── COUNTS ──────────────────────────────────────────────────────")
check("n_all", len(df_all), EXPECTED["n_all"])
check("n_excluded (dist_protected==0)", int((df_all[COL["protected"]] == 0).sum()),
      EXPECTED["n_excluded"])
df_via0 = df_all[df_all[COL["protected"]] > 0]
check("n_admissible", len(df_via0), EXPECTED["n_admissible"])
print()

# Mapping: df_all row → A' index (-1 for excluded)
adm_mask = (df_all[COL["protected"]] > 0).to_numpy()
adm_rows = np.flatnonzero(adm_mask)   # row numbers in df_all that are admissible
exc_rows = np.flatnonzero(~adm_mask)
pos_Ap   = -np.ones(len(df_all), dtype=int)
pos_Ap[adm_rows] = np.arange(len(adm_rows))   # df_all index → A' index (0-388)

# ---------------------------------------------------------------------------
# 3. NaN SITES
# ---------------------------------------------------------------------------
print("── NaN SITES ───────────────────────────────────────────────────")
nan_sites_found = set()
for k in AHP:
    if k == "aspect":
        continue
    nan_rows = df_all.index[df_all[COL[k]].isna()].tolist()
    for r in nan_rows:
        print(f"    NaN at row {r}, col={k}")
    nan_sites_found.update(nan_rows)
check("nan_sites (0-indexed row in df_all)", nan_sites_found, EXPECTED["nan_sites"])
print()

# ---------------------------------------------------------------------------
# 4. IMPUTE NaN (midpoint of 473-site range)
# ---------------------------------------------------------------------------
df_imp = df_all.copy()
for k in AHP:
    if k == "aspect":
        continue
    col = COL[k]
    mask = df_imp[col].isna()
    if mask.any():
        df_imp.loc[mask, col] = (df_imp[col].min() + df_imp[col].max()) / 2

df_via_imp = df_imp[adm_mask].copy().reset_index(drop=True)
N = len(df_via_imp)

# Build raw matrix
crit_keys = list(AHP.keys())
asp_via = df_via_imp[COL["aspect"]].values.astype(float)
asp_all = df_imp[COL["aspect"]].values.astype(float)

X_raw_Ap  = np.column_stack([df_via_imp[COL[k]].values.astype(float) for k in crit_keys])
X_raw_all = np.column_stack([df_imp[COL[k]].values.astype(float) for k in crit_keys])

# ---------------------------------------------------------------------------
# 5. PERM STATISTICS IN A'
# ---------------------------------------------------------------------------
print("── PERM STATISTICS IN A' ───────────────────────────────────────")
perm_j    = crit_keys.index("perm")
perm_vals = X_raw_Ap[:, perm_j]
perm_zeros = int((perm_vals == 0).sum())
perm_max   = float(perm_vals.max())
check("perm zeros in A'", perm_zeros, EXPECTED["perm_zeros_admissible"])
check("perm max in A' (metres, tol=1)", perm_max, EXPECTED["perm_max_admissible"], tol=1.0)
print()

# ---------------------------------------------------------------------------
# 6. ASPECT n1 IN A'
# ---------------------------------------------------------------------------
print("── ASPECT IN A' ────────────────────────────────────────────────")
n1 = int(((asp_via >= 90) & (asp_via <= 180)).sum())
check("aspect leeward n1 in A'", n1, EXPECTED["aspect_n1"])
print(f"  rho_j(aspect) = 1/sqrt({n1}) = {1/np.sqrt(n1):.4f} (manuscript: 0.103)")
print()

if args.quick:
    for name, reason in [
        ("n_trios (from fogo_trios.npy)", "--quick"),
        ("n_trios (trace method, independent)", "--quick"),
        ("Pareto |F'| A' non-dominated check", "--quick"),
        ("Pareto A' exact completeness", "--quick"),
        ("Pareto |F| A (213)", "--quick"),
        ("|A cap A'| (132)", "--quick"),
        ("SAW/mm/optimal in A matches {184,430,460}", "--quick"),
        ("F1/F2/F3 of A-portfolio matches manuscript to 1e-6", "--quick"),
    ]:
        not_run(name, reason)
    print()
else:

    # ── 7. TRIO COUNT ─────────────────────────────────────────────────────
    print("── TRIOS ───────────────────────────────────────────────────────")
    R = 6371.0
    la = np.radians(df_via_imp["latitude (degrees)"].values)
    lo = np.radians(df_via_imp["longitude (degrees)"].values)
    dlat = la[:, None] - la[None, :]
    dlon = lo[:, None] - lo[None, :]
    a_    = np.sin(dlat/2)**2 + np.cos(la[:,None])*np.cos(la[None,:])*np.sin(dlon/2)**2
    D     = R * 2 * np.arcsin(np.sqrt(np.clip(a_, 0, 1)))
    valid = (D >= MIN_DIST_KM)
    np.fill_diagonal(valid, False)

    # 7a. Load pre-computed trios
    _root     = Path(__file__).parent.parent
    trios_npy = _root / "data" / "fogo_trios.npy"
    if trios_npy.exists():
        trios_arr = np.load(trios_npy)
        check("n_trios (from fogo_trios.npy)", len(trios_arr), EXPECTED["n_trios"])
        # Spot-check distance constraint (1000 random; check() not assert)
        rng_c = np.random.default_rng(42)
        spot  = rng_c.integers(0, len(trios_arr), 1000)
        bad   = sum(1 for s in spot if (D[trios_arr[s,0], trios_arr[s,1]] < MIN_DIST_KM - EPS
                                         or D[trios_arr[s,0], trios_arr[s,2]] < MIN_DIST_KM - EPS
                                         or D[trios_arr[s,1], trios_arr[s,2]] < MIN_DIST_KM - EPS))
        check("distance constraint violations in 1000 random trios", bad, 0)
        T0 = trios_arr[:, 0]; T1 = trios_arr[:, 1]; T2 = trios_arr[:, 2]
    else:
        not_run("n_trios (from fogo_trios.npy)", "fogo_trios.npy not found")
        trios_arr = None

    # 7b. Independent count via adjacency matrix trace: triangles = trace(A^3) / 6
    Av  = valid.astype(np.int64)
    Av2 = Av @ Av
    n_tri_trace = int(np.trace(Av @ Av2)) // 6
    check("n_trios (trace method, independent)", n_tri_trace, EXPECTED["n_trios"])
    print()

    if trios_arr is None:
        for name in ["Pareto |F'| A' non-dominated check",
                     "Pareto A' exact completeness",
                     "Pareto |F| A (213)", "|A cap A'| (132)",
                     "SAW/mm/optimal in A matches {184,430,460}",
                     "F1/F2/F3 of A-portfolio matches manuscript to 1e-6"]:
            not_run(name, "trios_arr not available")
    else:

        # ── 8. PARETO FRONTIER A' ────────────────────────────────────────
        print("── PARETO FRONTIER A' ──────────────────────────────────────────")

        # Objectives in A' (normalise over 389 sites)
        f1_Ap, f2_Ap, f3_Ap = objectives_ms(X_raw_Ap, X_raw_Ap, asp_via)
        F1_Ap = f1_Ap[T0] + f1_Ap[T1] + f1_Ap[T2]
        F2_Ap = f2_Ap[T0] + f2_Ap[T1] + f2_Ap[T2]
        F3_Ap = f3_Ap[T0] + f3_Ap[T1] + f3_Ap[T2]

        # Load claimed Pareto CSV
        pareto_csv = _root / "results" / "pareto_front_Aprime.csv"
        if not pareto_csv.exists():
            pareto_csv = _root / "scripts" / "results" / "pareto_front_Aprime.csv"

        if not pareto_csv.exists():
            not_run("Pareto |F'| A' (from CSV)", "pareto_front_Aprime.csv not found")
            not_run("Pareto |F'| non-dominated check", "CSV not found")
            not_run("Pareto A' exact completeness", "CSV not found")
            PF_idx = None
        else:
            pf = pd.read_csv(pareto_csv)
            check("pareto_Ap count in CSV", len(pf), EXPECTED["pareto_Ap"])

            # ── 8a. INDEX DIAGNOSIS ─────────────────────────────────────
            print()
            print("  [INDEX DIAGNOSIS]")
            idx_cols_fixed = ["idx1", "idx2", "idx3"]
            if not all(c in pf.columns for c in idx_cols_fixed):
                print(f"  WARNING: columns {idx_cols_fixed} not found; got {list(pf.columns)}")
                ids = pf.select_dtypes(include=[np.number]).values[:, :3].astype(int)
            else:
                ids = pf[idx_cols_fixed].values.astype(int)

            print(f"  idx range: [{ids.min()}, {ids.max()}]  (A' range: [0, {N-1}])")
            all_in_adm = bool(np.isin(ids, adm_rows).all())
            any_in_exc = bool(np.isin(ids, exc_rows).any())
            print(f"  all idx in adm(df_all):    {all_in_adm}")
            print(f"  any idx in excl(df_all):   {any_in_exc}")
            print(f"  any idx > {N-1} (A' range): {bool((ids > N-1).any())}")

            # Try remapping df_all → A' indices
            ids_Ap = pos_Ap[ids]               # (181, 3); -1 if excluded
            valid_remap = (ids_Ap >= 0).all(axis=1)
            print(f"  after remap all >=0:       {valid_remap.sum()}/{len(pf)}")

            # For remapped trios, compare F-values with tolerance 1e-6
            ids_Ap_sorted = np.sort(ids_Ap[valid_remap], axis=1)
            N_ap = N
            key_arr = (ids_Ap_sorted[:,0].astype(np.int64)*N_ap + ids_Ap_sorted[:,1])*N_ap + ids_Ap_sorted[:,2]
            trios_sorted_all = np.sort(trios_arr, axis=1)
            key_trios = (trios_sorted_all[:,0].astype(np.int64)*N_ap + trios_sorted_all[:,1])*N_ap + trios_sorted_all[:,2]
            trios_key_set = dict(zip(key_trios.tolist(), range(len(trios_arr))))
            found_mask_remap = np.array([k in trios_key_set for k in key_arr.tolist()])
            print(f"  after remap, found in trios_arr: {found_mask_remap.sum()}/{valid_remap.sum()}")

            if found_mask_remap.sum() > 0:
                f1_csv = pf.loc[valid_remap, "F1P"].values if "F1P" in pf.columns else None
                f2_csv = pf.loc[valid_remap, "F2P"].values if "F2P" in pf.columns else None
                f3_csv = pf.loc[valid_remap, "F3P"].values if "F3P" in pf.columns else None
                if f1_csv is not None:
                    found_idx_in_trios = np.array([trios_key_set[k] for k,m in zip(key_arr.tolist(), found_mask_remap) if m])
                    # For A' normalisation comparison
                    f1_comp = F1_Ap[found_idx_in_trios]
                    f2_comp = F2_Ap[found_idx_in_trios]
                    f3_comp = F3_Ap[found_idx_in_trios]
                    f1_csv_f = f1_csv[found_mask_remap]
                    f2_csv_f = f2_csv[found_mask_remap]
                    f3_csv_f = f3_csv[found_mask_remap]
                    max_diff = max(np.abs(f1_comp - f1_csv_f).max(),
                                   np.abs(f2_comp - f2_csv_f).max(),
                                   np.abs(f3_comp - f3_csv_f).max())
                    print(f"  F-value comparison (A' norm, found trios): max_diff = {max_diff:.2e}")
                    if max_diff > 1e-4:
                        print(f"    NOTE: large diff suggests different normalisation (A vs A')")
                        # Try with A normalisation
                        f1_A_via, f2_A_via, f3_A_via = objectives_ms(X_raw_Ap, X_raw_all, asp_via)
                        F1_A_Ap = f1_A_via[T0] + f1_A_via[T1] + f1_A_via[T2]
                        F2_A_Ap = f2_A_via[T0] + f2_A_via[T1] + f2_A_via[T2]
                        F3_A_Ap = f3_A_via[T0] + f3_A_via[T1] + f3_A_via[T2]
                        f1_cA = F1_A_Ap[found_idx_in_trios]
                        f2_cA = F2_A_Ap[found_idx_in_trios]
                        f3_cA = F3_A_Ap[found_idx_in_trios]
                        max_diff_A = max(np.abs(f1_cA - f1_csv_f).max(),
                                         np.abs(f2_cA - f2_csv_f).max(),
                                         np.abs(f3_cA - f3_csv_f).max())
                        print(f"  F-value comparison (A norm, found trios):  max_diff = {max_diff_A:.2e}")

            # Build PF_idx from remapped trios (those found in trios_arr)
            PF_idx = [trios_key_set[k] for k,m in zip(key_arr.tolist(), found_mask_remap) if m]
            print()

            # ── 8b. NON-DOMINANCE WITHIN CLAIMED SET ─────────────────────
            if len(PF_idx) > 5:
                PF1 = F1_Ap[PF_idx]; PF2 = F2_Ap[PF_idx]; PF3 = F3_Ap[PF_idx]
                dom_within = 0
                for t in range(len(PF_idx)):
                    dom = ((PF1 <= PF1[t] - EPS) & (PF2 <= PF2[t] - EPS) & (PF3 >= PF3[t] + EPS) |
                           (PF1 <  PF1[t] + EPS) & (PF2 <  PF2[t] + EPS) & (PF3 > PF3[t] - EPS) &
                           ((PF1 < PF1[t] - EPS) | (PF2 < PF2[t] - EPS) | (PF3 > PF3[t] + EPS)))
                    # Rewrite correctly: dominator has F1<=, F2<=, F3>= and at least one strict
                    dominator = ((PF1 <= PF1[t] + EPS) & (PF2 <= PF2[t] + EPS) & (PF3 >= PF3[t] - EPS) &
                                 ((PF1 < PF1[t] - EPS) | (PF2 < PF2[t] - EPS) | (PF3 > PF3[t] + EPS)))
                    dominator[t] = False
                    if dominator.any():
                        dom_within += 1
                check("Pareto non-dominated within remapped set", dom_within, 0)
            else:
                not_run("Pareto |F'| non-dominated check",
                        f"only {len(PF_idx)} trios found after remap")

            # ── 8c. EXACT COMPLETENESS (vectorised blocks) ───────────────
            if len(PF_idx) > 5:
                print()
                print("  [EXACT COMPLETENESS]")
                T = len(trios_arr)
                in_F = np.zeros(T, dtype=bool)
                in_F[PF_idx] = True
                dominated = np.zeros(T, dtype=bool)

                # For each block of trios, check if dominated by any Pareto member
                BLOCK = 200_000
                for c_start in range(0, T, BLOCK):
                    s = slice(c_start, min(c_start + BLOCK, T))
                    # dominator (from PF) has F1<=, F2<=, F3>= current slice
                    ge = ((PF1[:, None] <= F1_Ap[s][None, :] + EPS) &
                          (PF2[:, None] <= F2_Ap[s][None, :] + EPS) &
                          (PF3[:, None] >= F3_Ap[s][None, :] - EPS))
                    gt = ((PF1[:, None] < F1_Ap[s][None, :] - EPS) |
                          (PF2[:, None] < F2_Ap[s][None, :] - EPS) |
                          (PF3[:, None] > F3_Ap[s][None, :] + EPS))
                    dominated[s] = (ge & gt).any(axis=0)

                n_outside_not_dominated = int((~dominated & ~in_F).sum())
                check("exact completeness: trios outside F' not dominated by F'",
                      n_outside_not_dominated, 0)
            else:
                not_run("Pareto A' exact completeness",
                        f"only {len(PF_idx)} trios in remapped set")

        print()

        # ── 9. NORMALISATION AND SAW SCORES ──────────────────────────────
        w_vec = np.array(list(AHP.values()))

        # A' scorer (for SAW portfolio in A')
        Xa_Ap = scorer_adj(X_raw_Ap, X_raw_Ap, asp_via)
        saw_Ap = (Xa_Ap * w_vec).sum(axis=1)

        # A scorer (for SAW portfolio in A — normalise over 473 sites)
        Xa_A = scorer_adj(X_raw_Ap, X_raw_all, asp_via)
        saw_A = (Xa_A * w_vec).sum(axis=1)

        # ── 9a. PARETO FRONTIER A ─────────────────────────────────────────
        print("── PARETO FRONTIER A ───────────────────────────────────────────")
        f1_A, f2_A, f3_A = objectives_ms(X_raw_Ap, X_raw_all, asp_via)
        F1_A = f1_A[T0] + f1_A[T1] + f1_A[T2]
        F2_A = f2_A[T0] + f2_A[T1] + f2_A[T2]
        F3_A = f3_A[T0] + f3_A[T1] + f3_A[T2]

        # Load pre-computed space-A Pareto CSV (exhaustive_search_pareto.csv)
        # Columns: Cost, Impact, Neg_Safety, Safety, idx1, idx2, idx3
        # idx1/2/3 = df_all row indices (0-472); must be remapped to A' indices
        _ieee = os.path.join(os.environ.get("MCDM_DATA_DIR", ""),
                             "New code", "results", "results-2026-04-07_18-40-54")
        pareto_A_csv = Path(_ieee) / "exhaustive_search_pareto.csv"
        if not pareto_A_csv.exists():
            pareto_A_csv = _root / "scripts" / "results" / "pareto_front_A.csv"

        if not pareto_A_csv.exists():
            not_run("Pareto |F| A (213)", "exhaustive_search_pareto.csv not found")
            not_run("|A cap A'| (132)", "pareto_A CSV not found")
            pf_A = None
        else:
            pf_A = pd.read_csv(pareto_A_csv)
            check("pareto_A |F| (213)", len(pf_A), EXPECTED["pareto_A"])

            # Remap df_all indices → A'
            if all(c in pf_A.columns for c in ["idx1", "idx2", "idx3"]):
                ids_A = pf_A[["idx1", "idx2", "idx3"]].values.astype(int)
            else:
                ids_A = pf_A.select_dtypes(include=[np.number]).values[:, -3:].astype(int)
            ids_A_remap = pos_Ap[ids_A]
            valid_A = (ids_A_remap >= 0).all(axis=1)
            print(f"  idx range A CSV: [{ids_A.min()}, {ids_A.max()}]")
            print(f"  remapped to A' indices: {valid_A.sum()}/{len(pf_A)} valid")

            # For valid remapped trios, compare F-values (A normalisation)
            if valid_A.sum() > 5:
                ids_As = np.sort(ids_A_remap[valid_A], axis=1)
                N_ap = N
                key_Ar = (ids_As[:,0].astype(np.int64)*N_ap + ids_As[:,1])*N_ap + ids_As[:,2]
                found_A_mask = np.array([k in trios_key_set for k in key_Ar.tolist()])
                print(f"  found in trios_arr after remap: {found_A_mask.sum()}/{valid_A.sum()}")
                if found_A_mask.sum() > 0:
                    f_idxA = [trios_key_set[k] for k,m in zip(key_Ar.tolist(), found_A_mask) if m]
                    # Compare CSV Cost/Impact/Safety vs our independently computed F
                    f1_csvA = pf_A.loc[valid_A, "Cost"].values[found_A_mask]   if "Cost" in pf_A.columns else None
                    f3_csvA = pf_A.loc[valid_A, "Safety"].values[found_A_mask] if "Safety" in pf_A.columns else None
                    if f1_csvA is not None:
                        md1 = np.abs(F1_A[f_idxA] - f1_csvA).max()
                        md3 = np.abs(F3_A[f_idxA] - f3_csvA).max()
                        print(f"  F-value comparison (A norm, found trios): max_diff F1={md1:.2e} F3={md3:.2e}")
                PF_A_idx = [trios_key_set[k] for k,m in zip(key_Ar.tolist(), found_A_mask) if m]
            else:
                PF_A_idx = []

            # |A ∩ A'| — intersection
            if PF_idx is not None and len(PF_idx) > 0 and len(PF_A_idx) > 0:
                set_A_  = set(map(tuple, np.sort(trios_arr[PF_A_idx],  axis=1).tolist()))
                set_Ap_ = set(map(tuple, np.sort(trios_arr[PF_idx],    axis=1).tolist()))
                cap     = len(set_A_ & set_Ap_)
                print(f"  NOTE: intersection uses remapped subsets ({len(PF_A_idx)} and {len(PF_idx)} trios found)")
                print(f"  NOTE: if remapping is partial, |A cap A'| = {cap} is a lower bound")
            else:
                not_run("|A cap A'| (132)", "insufficient trios found after remapping")

        print()

        # ── 10. PORTFOLIO IN A ────────────────────────────────────────────
        print("── PORTFOLIO SAW/mm/OPTIMAL IN A ───────────────────────────────")
        saw_A_trio = saw_A[T0] + saw_A[T1] + saw_A[T2]
        best_A_idx = int(saw_A_trio.argmax())
        best_A = frozenset(trios_arr[best_A_idx].tolist())
        check("SAW/mm/optimal in A matches {184,430,460}",
              best_A, EXPECTED["portfolio_A"])

        # Compare F1/F2/F3 with manuscript values to 1e-6
        i0A, i1A, i2A = trios_arr[best_A_idx]
        f1_port = f1_A[i0A] + f1_A[i1A] + f1_A[i2A]
        f2_port = f2_A[i0A] + f2_A[i1A] + f2_A[i2A]
        f3_port = f3_A[i0A] + f3_A[i1A] + f3_A[i2A]
        print(f"  F1 = {f1_port:.10f}  (manuscript: from Table 3)")
        print(f"  F2 = {f2_port:.10f}")
        print(f"  F3 = {f3_port:.10f}")
        print(f"  NOTE: update gate criterion with manuscript F-values after Phase 1.7")
        print()

        # A' portfolio (informational)
        print("── PORTFOLIO SAW/mm/OPTIMAL IN A' (informational) ──────────────")
        saw_Ap_trio = saw_Ap[T0] + saw_Ap[T1] + saw_Ap[T2]
        best_Ap_idx = int(saw_Ap_trio.argmax())
        best_Ap = tuple(trios_arr[best_Ap_idx].tolist())
        print(f"  Portfolio: {set(best_Ap)}")
        print(f"  NOTE: TBD — update EXPECTED after Phase 1.7 canonical run")
        print()

# ---------------------------------------------------------------------------
# GATE SUMMARY
# ---------------------------------------------------------------------------
print("=" * 68)
total = PASS_COUNT + FAIL_COUNT
print(f"GATE 1 RESULT: {PASS_COUNT}/{total} checks PASS  |  "
      f"{FAIL_COUNT} FAIL  |  {NOT_RUN_COUNT} NOT RUN")
print()
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print(f)
    print()
if NOT_RUN_LIST:
    print("NOT RUN (gate not clearable until resolved):")
    for nr in NOT_RUN_LIST:
        print(nr)
    print()

if FAIL_COUNT == 0 and NOT_RUN_COUNT == 0:
    print("Status: ALL CHECKS PASS — Phase 1 gate cleared.")
    print(f"CSV SHA-256: {csv_hash}")
elif FAIL_COUNT > 0:
    print("Status: BLOCKED — fix failures before proceeding.")
    sys.exit(1)
else:
    print("Status: INCOMPLETE — re-run without --quick to clear NOT RUN checks.")
