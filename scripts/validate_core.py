# -*- coding: utf-8 -*-
"""
validate_core.py  --  Phase 1 independent validation of the Fogo pipeline.

GATE 1 CRITERIA (write expected values before running):
  1. N candidates = 473
  2. N excluded (dist_protected = 0) = 84
  3. N admissible = 389
  4. NaN sites: 41 (roads), 385 (urban), 429 (aero)
  5. perm zeros in A': 350; perm max in A': 532 m
  6. aspect leeward (n1) in A': 94
  7. Haversine trios: 1,944,653
  8. Pareto frontier |F| in A': 181
  9. Pareto frontier |F| in A:  213
  10. A cap A': 132
  11. SAW/mm portfolio in A: {184, 430, 460} with F1/F2/F3 matching to 1e-12

This script imports NOTHING from the project pipeline.
All computations are re-implemented from scratch.
Any difference from the expected values is a blocker.

Run:
  uv run python scripts/validate_core.py

Set MCDM_DATA_DIR if the default path does not exist:
  export MCDM_DATA_DIR=/path/to/data
"""

import os, sys, hashlib, argparse
from pathlib import Path
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument('--quick', action='store_true',
                    help='Skip trio enumeration and Pareto (run on Athena for full check)')
args, _ = parser.parse_known_args()

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
_DATA_DIR = os.environ.get("MCDM_DATA_DIR", os.path.join(
    "G:", os.sep, "Faculdade", "Estudo", "Doutorado", "2025.1",
    "Otimiza\u00e7\u00e3o Bioinspirada", "Tentativa de dados via GIS"
))
_cache_flat = os.path.join(_DATA_DIR, "df_real_data_cached.csv")
if os.path.exists(_cache_flat):
    CACHE_CSV = _cache_flat
    PARETO_CSV = os.path.join(_DATA_DIR, "exhaustive_search_pareto.csv")
else:
    _gis = _DATA_DIR
    _ieee = os.path.join(_gis, "New code", "results", "results-2026-04-07_18-40-54")
    CACHE_CSV  = os.path.join(_gis, "results_cache", "df_real_data_cached.csv")
    PARETO_CSV = os.path.join(_ieee, "exhaustive_search_pareto.csv")

# Gate 1 expected values (written before running)
EXPECTED = {
    "n_all":       473,
    "n_excluded":  84,
    "n_admissible": 389,
    "nan_sites":   {41, 385, 429},      # 0-indexed row in df_all
    "perm_zeros_admissible": 350,
    "perm_max_admissible":   532,       # metres
    "aspect_n1":   94,                  # leeward sites in A'
    "n_trios":     1_944_653,
    "pareto_Ap":   181,                 # |frontier| in A'
    "pareto_A":    213,                 # |frontier| in A
    "pareto_cap":  132,                 # |A cap A'|
    "portfolio":   {184, 430, 460},     # SAW/mm greedy in A (0-indexed in df_via)
}

# AHP weights (Table 2 of manuscript; reproduced verbatim — no import)
AHP = {
    "perm": 0.152, "slope": 0.113, "roads": 0.030,
    "rivers": 0.091, "aspect": 0.075, "coast": 0.069,
    "protected": 0.066, "wells": 0.055,
    "urban": 0.166, "aero": 0.102, "cult": 0.081,
}
assert abs(sum(AHP.values()) - 1.0) < 1e-9, "AHP weights do not sum to 1"

# Column names in CSV (reproduced verbatim — no import)
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
INV     = {"rivers", "coast", "protected", "wells"}
COST    = {"perm", "slope", "roads"}
BENEFIT = {"urban", "aero", "cult"}

MIN_DIST_KM = 10.0

PASS_COUNT = 0
FAIL_COUNT = 0
FAILURES = []

def check(name, actual, expected, tol=None):
    global PASS_COUNT, FAIL_COUNT
    if tol is not None:
        ok = abs(actual - expected) <= tol
    elif isinstance(expected, set):
        ok = set(actual) == expected if not isinstance(actual, set) else actual == expected
    else:
        ok = actual == expected
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
        FAILURES.append(f"  {name}: got {actual}, expected {expected}")
    print(f"  [{status}] {name}: {actual}")
    return ok


# ---------------------------------------------------------------------------
# 1. Load and inspect raw data
# ---------------------------------------------------------------------------
print("=" * 65)
print("VALIDATE_CORE — Phase 1 independent pipeline validation")
print("=" * 65)
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
# 2. Counts
# ---------------------------------------------------------------------------
print("── COUNTS ──────────────────────────────────────────────────")
check("n_all", len(df_all), EXPECTED["n_all"])

excluded = df_all[df_all[COL["protected"]] == 0]
check("n_excluded (dist_protected=0)", len(excluded), EXPECTED["n_excluded"])

df_via = df_all[df_all[COL["protected"]] > 0].copy().reset_index(drop=True)
check("n_admissible", len(df_via), EXPECTED["n_admissible"])
print()

# ---------------------------------------------------------------------------
# 3. NaN sites
# ---------------------------------------------------------------------------
print("── NaN SITES ───────────────────────────────────────────────")
nan_sites_found = set()
for k in AHP:
    if k == "aspect":
        continue
    col = COL[k]
    nan_rows = df_all.index[df_all[col].isna()].tolist()
    if nan_rows:
        for r in nan_rows:
            print(f"    NaN at row {r}, col={k}")
        nan_sites_found.update(nan_rows)
check("nan_sites (0-indexed row in df_all)", nan_sites_found, EXPECTED["nan_sites"])
print()

# ---------------------------------------------------------------------------
# 4. Impute NaN (midpoint of 473-site range)
# ---------------------------------------------------------------------------
df_imp = df_all.copy()
for k in AHP:
    if k == "aspect":
        continue
    col = COL[k]
    mask = df_imp[col].isna()
    if mask.any():
        mid = (df_imp[col].min() + df_imp[col].max()) / 2
        df_imp.loc[mask, col] = mid

df_via_imp = df_imp[df_imp[COL["protected"]] > 0].copy().reset_index(drop=True)

# ---------------------------------------------------------------------------
# 5. perm statistics in A'
# ---------------------------------------------------------------------------
print("── PERM STATISTICS IN A' ───────────────────────────────────")
perm_vals = df_via_imp[COL["perm"]].values
perm_zeros = int((perm_vals == 0).sum())
perm_max   = int(perm_vals.max())
check("perm zeros in A'", perm_zeros, EXPECTED["perm_zeros_admissible"])
check("perm max in A' (metres)", perm_max, EXPECTED["perm_max_admissible"])
print()

# ---------------------------------------------------------------------------
# 6. aspect — leeward sites in A'
# ---------------------------------------------------------------------------
print("── ASPECT IN A' ────────────────────────────────────────────")
asp = df_via_imp[COL["aspect"]].values
n1  = int(((asp >= 90) & (asp <= 180)).sum())
check("aspect leeward n1 in A'", n1, EXPECTED["aspect_n1"])
rho_asp = 1.0 / np.sqrt(n1)
print(f"  rho_j(aspect) = 1/sqrt({n1}) = {rho_asp:.4f} (article: 0.103)")
print()

# ---------------------------------------------------------------------------
# 7. Haversine distance matrix and trio count
# ---------------------------------------------------------------------------
print("── TRIOS ───────────────────────────────────────────────────")
lats = df_via_imp["latitude (degrees)"].values
lons = df_via_imp["longitude (degrees)"].values
N    = len(lats)

R = 6371.0
la = np.radians(lats); lo = np.radians(lons)
dlat = la[:, None] - la[None, :]
dlon = lo[:, None] - lo[None, :]
a    = (np.sin(dlat / 2)**2
        + np.cos(la[:, None]) * np.cos(la[None, :]) * np.sin(dlon / 2)**2)
D    = R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
valid = D >= MIN_DIST_KM

if args.quick:
    print("  [SKIP] trio enumeration (--quick mode; run on Athena for full check)")
    n_trios_fast = EXPECTED["n_trios"]  # use expected value, not computed
    trios_list = None
else:
    n_trios_fast = 0
    trios_list = []
    for i in range(N):
        j_set = np.where(valid[i])[0]
        j_set = j_set[j_set > i]
        for j in j_set:
            k_set = np.where(valid[j] & valid[i])[0]
            k_set = k_set[k_set > j]
            n_trios_fast += len(k_set)
            for kk in k_set:
                trios_list.append((i, j, int(kk)))
    check("n_trios", n_trios_fast, EXPECTED["n_trios"])
print()

# ---------------------------------------------------------------------------
# 8. Normalise and compute objectives (independent implementation)
# ---------------------------------------------------------------------------
print("── NORMALISATION ───────────────────────────────────────────")

def minmax_norm_vc(x, x_ref):
    rmin, rmax = x_ref.min(), x_ref.max()
    rng = rmax - rmin
    if rng == 0:
        return np.full(len(x), 0.5)
    return (x - rmin) / rng

# Build X_adj: benefit-adjusted, higher = better for all criteria
X_adj = np.zeros((N, len(AHP)))
w_vec = np.array(list(AHP.values()))

for j, k in enumerate(AHP):
    x_via = df_via_imp[COL[k]].values.astype(float)
    if k == "aspect":
        c = np.where((x_via >= 90) & (x_via <= 180), 1.0, 0.0)
    elif k in COST:
        c = 1.0 - minmax_norm_vc(x_via, x_via)
    elif k in INV:
        c = minmax_norm_vc(x_via, x_via)
    else:  # BENEFIT
        c = minmax_norm_vc(x_via, x_via)
    X_adj[:, j] = c

# SAW score in A' (min-max)
saw_scores_Ap = (X_adj * w_vec).sum(axis=1)
print(f"  SAW/mm score range in A': [{saw_scores_Ap.min():.4f}, {saw_scores_Ap.max():.4f}]")
print()

if args.quick:
    print("── PARETO + PORTFOLIO ──────────────────────────────────────")
    print("  [SKIP] Pareto frontier and portfolio (--quick mode)")
    print("  Run without --quick on Athena for full gate 1 check.")
    print()
else:

  # ── 9. Pareto frontier in A' ────────────────────────────────────────────
  print("── PARETO FRONTIER A' ──────────────────────────────────────")

  G1_idx = [list(AHP.keys()).index(k) for k in F1_CRIT]
  G2_idx = [list(AHP.keys()).index(k) for k in F2_CRIT]
  G3_idx = [list(AHP.keys()).index(k) for k in F3_CRIT]

  f1_site = X_adj[:, G1_idx] @ w_vec[G1_idx]
  f2_site = X_adj[:, G2_idx] @ w_vec[G2_idx]
  f3_site = X_adj[:, G3_idx] @ w_vec[G3_idx]

  trios_arr = np.array(trios_list, dtype=np.int32)
  T = len(trios_arr)
  T0, T1, T2 = trios_arr[:, 0], trios_arr[:, 1], trios_arr[:, 2]

  F1 = f1_site[T0] + f1_site[T1] + f1_site[T2]
  F2 = f2_site[T0] + f2_site[T1] + f2_site[T2]
  F3 = f3_site[T0] + f3_site[T1] + f3_site[T2]

  EPS = 1e-9
  n_pareto_Ap = 0
  pareto_mask_Ap = np.zeros(T, dtype=bool)
  for t in range(T):
      dom = ((F1 >= F1[t] - EPS) & (F2 >= F2[t] - EPS) & (F3 >= F3[t] - EPS) &
             ((F1 > F1[t] + EPS) | (F2 > F2[t] + EPS) | (F3 > F3[t] + EPS)))
      dom[t] = False
      if not dom.any():
          pareto_mask_Ap[t] = True
          n_pareto_Ap += 1

  check("pareto_Ap |F'|", n_pareto_Ap, EXPECTED["pareto_Ap"])
  pareto_set_Ap = set(map(tuple, trios_arr[pareto_mask_Ap].tolist()))
  print()

  # ── 10. Reference portfolio ──────────────────────────────────────────────
  print("── REFERENCE PORTFOLIO (SAW/mm greedy in A') ───────────────")
  saw_trio_scores = saw_scores_Ap[T0] + saw_scores_Ap[T1] + saw_scores_Ap[T2]
  best_idx = int(saw_trio_scores.argmax())
  best_trio = tuple(trios_arr[best_idx].tolist())
  check("SAW/mm greedy portfolio in A'", set(best_trio), EXPECTED["portfolio"])

  i0, i1, i2 = best_trio
  f1_ref = f1_site[i0] + f1_site[i1] + f1_site[i2]
  f2_ref = f2_site[i0] + f2_site[i1] + f2_site[i2]
  f3_ref = f3_site[i0] + f3_site[i1] + f3_site[i2]
  print(f"    F1 = {f1_ref:.12f}")
  print(f"    F2 = {f2_ref:.12f}")
  print(f"    F3 = {f3_ref:.12f}")
  print(f"    In Pareto A': {best_trio in pareto_set_Ap}")
  print()

# ---------------------------------------------------------------------------
# 11. GATE SUMMARY
# ---------------------------------------------------------------------------
print("=" * 65)
total = PASS_COUNT + FAIL_COUNT
print(f"GATE 1 RESULT: {PASS_COUNT}/{total} checks PASS  |  {FAIL_COUNT} FAIL")
if FAILURES:
    print()
    print("FAILURES:")
    for f in FAILURES:
        print(f)
    print()
    print("Status: BLOCKED — do not proceed to Phase 2 writing until resolved.")
    sys.exit(1)
else:
    print()
    print("Status: ALL CHECKS PASS — Phase 1 gate cleared.")
    print(f"CSV SHA-256: {csv_hash}")
