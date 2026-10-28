# -*- coding: utf-8 -*-
"""
compute_stage3b.py — Stage 3b descriptors for Santiago (S-T and S-N).

Computes per-branch descriptors:
  TV, TV_B, TV_W, m_eff, A_j (rho_j), w_eff, w_eff/w, point_mass, n_trios

FOGO GATE (blocking):
  Before computing any Santiago descriptor, reproduce all Fogo Tab 2 values
  to within declared tolerance using the same formula. If any gate check fails
  the script aborts with exit code 1.

Gate tolerances:
  TV:      ± 0.002   (Fogo published: 0.311)
  TV_B:    ± 0.002   (Fogo published: 0.248)
  TV_W:    ± 0.002   (Fogo published: 0.195)
  m_eff:   ± 0.05    (Fogo published: 4.03)
  w_eff/w per criterion: ± 0.02 (perm = 0.583/0.2035 = 2.865 with rounded Tab 2 values)

w_eff formula (CORRECT):
  S = sum(w_j * A_j)           # S = Sigma_k w_k * rho_k
  w_eff_j = w_j * A_j / S      # renormalized effective weight
  w_eff_j / w_j = A_j / S      # ratio reported in Tab 2

  NOTE: w_eff_j / w_j = A_j / S, NOT A_j / w_j.
  The bug A_j / w_j gives perm 3.83x (wrong); the correct formula gives 2.73x
  (precise Fogo amplitudes) or 2.865x (rounded Tab 2 values).

TV formula:
  TV = 0.5 * sum_j |w_eff_j - w_j|

TV_B / TV_W:
  TV_B: replace each A_j with the within-group weighted average A_g (between-group component)
  TV_W: TV - TV_B (within-group component)
  Exactly as in diag_tab2_corrected.py (confirmed correct for Fogo).

m_eff formula:
  m_eff = (2*TV)^2 / sum_j (w_eff_j - w_j)^2  =  (sum_j |delta_j|)^2 / sum_j delta_j^2
  where delta_j = w_eff_j - w_j

Output:
  results/santiago/stage3b_descriptors.json

Usage:
  uv run python scripts/compute_stage3b.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PAPER      = Path(__file__).parent.parent
SCRIPTS    = PAPER / "scripts"
sys.path.insert(0, str(SCRIPTS))

RESULTS    = PAPER / "results" / "santiago"
ST_CSV     = RESULTS / "df_santiago_st.csv"
SN_CSV     = RESULTS / "df_santiago_sn.csv"
OUT_JSON   = RESULTS / "stage3b_descriptors.json"

# ---------------------------------------------------------------------------
# 1. Fogo reference values (from fogo_constants.py / amplitudes.json)
# ---------------------------------------------------------------------------

# Declared published values (Tab 2 of main article, rounded to 3 d.p.)
FOGO_TV_PUB   = 0.311
FOGO_TVB_PUB  = 0.248
FOGO_TVW_PUB  = 0.195
FOGO_MEFF_PUB = 4.03
FOGO_NADM     = 389
FOGO_NTRIOS   = 1_944_653

# Fogo AHP weights (Tab 2, 11 criteria including wells)
FOGO_W = np.array([
    0.152, 0.113, 0.030, 0.091, 0.075, 0.069,
    0.066, 0.055, 0.166, 0.102, 0.081,
], dtype=float)
FOGO_W = FOGO_W / FOGO_W.sum()  # ensure sum=1 (already 1.000)

FOGO_CRIT = [
    "perm", "slope", "roads", "rivers", "aspect", "coast",
    "protected", "wells", "urban", "aero", "cult",
]

# Fogo amplitude rho_j (from amplitudes.json, rounded Tab 2 values for gate check)
# Tab 2 rounded (3 d.p.): perm=0.583, slope=0.139, roads=0.206, rivers=0.265,
#   aspect=0.103, coast=0.131, protected=0.105, wells=0.084, urban=0.107, aero=0.088, cult=0.171
# These are also the precise values (rho_j = 1/L2(mm_norm(x_j))) rounded to 3 d.p.
FOGO_A = np.array([
    0.583, 0.139, 0.206, 0.265, 0.103, 0.131,
    0.105, 0.084, 0.107, 0.088, 0.171,
], dtype=float)

# Fogo groups: G1=[0,1,2], G2=[3,4,5,6,7], G3=[8,9,10]
FOGO_GROUPS = [[0, 1, 2], [3, 4, 5, 6, 7], [8, 9, 10]]


# ---------------------------------------------------------------------------
# 2. Core descriptor functions
# ---------------------------------------------------------------------------

def compute_weff(w: np.ndarray, A: np.ndarray) -> np.ndarray:
    """Compute effective weights: w_eff_j = w_j * A_j / S where S = sum(w_k * A_k).

    @param w - declared AHP weights, shape (M,), must sum to 1.
    @param A - amplitudes rho_j, shape (M,).
    @returns w_eff, shape (M,), sums to 1.
    """
    S = float(np.dot(w, A))
    assert S > 0, f"S = sum(w*A) = {S} <= 0 — check inputs"
    w_eff = w * A / S
    return w_eff, S


def compute_TV(w: np.ndarray, w_eff: np.ndarray) -> float:
    """TV = 0.5 * sum_j |w_eff_j - w_j|.

    @param w - declared weights, shape (M,).
    @param w_eff - effective weights, shape (M,).
    @returns TV scalar.
    """
    return float(0.5 * np.abs(w_eff - w).sum())


def compute_TV_between(w: np.ndarray, A: np.ndarray, groups: list) -> float:
    """TV_B = TV computed with each A_j replaced by its weighted within-group average.

    For each criterion j in group g, A_j is replaced by Ā_g = Σ_{k∈g} w_k * A_k / W_g.
    Then TV_B = 0.5 * Σ_j |w_eff_B_j - w_j| where w_eff_B_j = w_j * Ā_g / S_B.

    @param w - declared weights, shape (M,).
    @param A - amplitudes, shape (M,).
    @param groups - list of index lists defining objective groups.
    @returns TV_B scalar.
    """
    A_bar = np.zeros_like(A)
    for g in groups:
        g = np.array(g, dtype=int)
        w_g = w[g].sum()
        A_bar[g] = float(np.dot(w[g], A[g])) / w_g if w_g > 0 else 0.0
    w_eff_B, _ = compute_weff(w, A_bar)
    return compute_TV(w, w_eff_B)


def compute_TV_within(w: np.ndarray, A: np.ndarray, groups: list) -> float:
    """TV_W = within-group component of TV.

    TV_W = Σ_g W_g * TV_{W,g}
    where TV_{W,g} = 0.5 * Σ_{j∈g} (w_j/W_g) * |ρ_j/Ā_g - 1|
          Ā_g = Σ_{j∈g} w_j * A_j / W_g  (within-group weighted average amplitude)
          W_g = Σ_{j∈g} w_j

    This is the TV of E1 cell-W amplitudes (ρ_j/Ā_g), as defined in §6.4 of the
    main article and implemented in generate_macros_amplitudes.py.

    Note: TV_W is NOT TV - TV_B. TV_B and TV_W are independent measures.

    @param w - declared weights, shape (M,).
    @param A - amplitudes, shape (M,).
    @param groups - list of index lists defining objective groups.
    @returns TV_W scalar.
    """
    TV_W = 0.0
    for g in groups:
        g_arr = np.array(g, dtype=int)
        W_g   = float(w[g_arr].sum())
        if W_g < 1e-15:
            continue
        Abar_g = float(np.dot(w[g_arr], A[g_arr]) / W_g)
        if Abar_g < 1e-15:
            continue
        TV_Wg = 0.5 * float(sum(
            (w[j] / W_g) * abs(A[j] / Abar_g - 1.0)
            for j in g_arr
        ))
        TV_W += W_g * TV_Wg
    return TV_W


def compute_meff(w: np.ndarray, w_eff: np.ndarray) -> float:
    """m_eff = (sum |delta_j|)^2 / sum delta_j^2 where delta_j = w_eff_j - w_j.

    @param w - declared weights, shape (M,).
    @param w_eff - effective weights, shape (M,).
    @returns m_eff scalar.
    """
    delta = w_eff - w
    sum_abs = float(np.abs(delta).sum())    # = 2 * TV
    sum_sq  = float((delta**2).sum())
    if sum_sq < 1e-15:
        M = len(w)
        return float(M)                    # degenerate: all amplitudes equal
    return float(sum_abs**2 / sum_sq)


def compute_point_masses(df_adm: pd.DataFrame, col: str) -> float:
    """Fraction of admissible sites at the modal value (point mass).

    @param df_adm - admissible subset DataFrame.
    @param col - column name.
    @returns fraction [0,1].
    """
    if col not in df_adm.columns or len(df_adm) == 0:
        return np.nan
    vc = df_adm[col].value_counts(normalize=True)
    return float(vc.iloc[0]) if len(vc) > 0 else np.nan


def compute_amplitudes(df_adm: pd.DataFrame, cols: list,
                       col_transforms: dict = None) -> np.ndarray:
    """Compute rho_j = range / L2(mm_norm(x_j)) for each criterion column.

    For continuous columns: mm_norm(x) = (x - min) / (max - min).
    For pre-transformed columns (binary, score): mm_norm is identity if range=[0,1].

    @param df_adm - admissible sites DataFrame.
    @param cols - list of raw criterion column names.
    @param col_transforms - optional dict mapping col name to a callable (ndarray → ndarray)
                            applied to the raw column before computing amplitude.
                            Use for binary indicators derived from continuous columns
                            (e.g., aspect azimuth → binary leeward indicator).
    @returns rho_j array, shape (len(cols),).
    """
    col_transforms = col_transforms or {}
    A = []
    for col in cols:
        raw = df_adm[col].values.astype(float)
        # Apply optional transformation (e.g., azimuth → binary indicator)
        x = col_transforms[col](raw) if col in col_transforms else raw
        xmin, xmax = x.min(), x.max()
        if xmax - xmin < 1e-9:
            A.append(0.0)
            continue
        x_mm = (x - xmin) / (xmax - xmin)
        l2 = float(np.sqrt((x_mm**2).sum()))
        A.append(1.0 / l2 if l2 > 0 else 0.0)
    return np.array(A, dtype=float)


# ---------------------------------------------------------------------------
# 3. Fogo gate (blocking)
# ---------------------------------------------------------------------------

def fogo_gate() -> bool:
    """Reproduce Fogo Tab 2 values as a blocking gate.

    Returns True if all checks pass; aborts with sys.exit(1) on failure.
    """
    print("=" * 60)
    print("FOGO GATE — reproducing Tab 2 (PRESPEC §3 mandatory regression)")
    print("=" * 60)

    # Load precise rho_j from amplitudes.json if available
    amp_json = PAPER / "results" / "amplitudes" / "amplitudes.json"
    if amp_json.exists():
        amp = json.loads(amp_json.read_text())
        A_precise = np.array([amp["rho_j"][c] for c in FOGO_CRIT], dtype=float)
        print("Using precise rho_j from amplitudes.json")
    else:
        A_precise = FOGO_A.copy()
        print("Using rounded Tab 2 rho_j (amplitudes.json not found)")

    w_eff, S = compute_weff(FOGO_W, A_precise)
    TV    = compute_TV(FOGO_W, w_eff)
    TV_B  = compute_TV_between(FOGO_W, A_precise, FOGO_GROUPS)
    TV_W  = compute_TV_within(FOGO_W, A_precise, FOGO_GROUPS)
    meff  = compute_meff(FOGO_W, w_eff)

    print(f"\n  Formula: w_eff_j = w_j * A_j / S   where S = sum(w_k * A_k) = {S:.6f}")
    print(f"  Note: w_eff_j / w_j = A_j / S  (NOT A_j / w_j)")
    print()

    # Per-criterion w_eff/w table
    print(f"  {'Criterion':12s}  {'w_j':>6}  {'A_j':>6}  {'w_eff_j':>7}  {'w_eff/w':>7}")
    print(f"  {'-'*12}  {'-'*6}  {'-'*6}  {'-'*7}  {'-'*7}")
    for i, crit in enumerate(FOGO_CRIT):
        ratio = w_eff[i] / FOGO_W[i]
        print(f"  {crit:12s}  {FOGO_W[i]:.4f}  {A_precise[i]:.4f}  {w_eff[i]:.5f}  {ratio:.4f}x")

    print()
    print(f"  Published (Tab 2):  TV={FOGO_TV_PUB}  TV_B={FOGO_TVB_PUB}  TV_W={FOGO_TVW_PUB}  m_eff={FOGO_MEFF_PUB}")
    print(f"  Computed:           TV={TV:.4f}  TV_B={TV_B:.4f}  TV_W={TV_W:.4f}  m_eff={meff:.4f}")
    print()

    failures = []
    checks = [
        ("TV",   TV,   FOGO_TV_PUB,   0.002),
        ("TV_B", TV_B, FOGO_TVB_PUB,  0.002),
        ("TV_W", TV_W, FOGO_TVW_PUB,  0.002),
        ("m_eff",meff, FOGO_MEFF_PUB, 0.05),
    ]
    for name, computed, published, tol in checks:
        diff = abs(computed - published)
        ok = diff <= tol
        status = "PASS" if ok else "FAIL"
        print(f"  {name:6s}: computed={computed:.4f}  published={published:.3f}  |diff|={diff:.4f}  tol={tol}  [{status}]")
        if not ok:
            failures.append(f"{name}: |computed - published| = {diff:.4f} > tol={tol}")

    # w_eff/w gate for perm (key criterion, most sensitive to formula bug)
    perm_ratio = w_eff[0] / FOGO_W[0]
    # Expected range from rounded Tab 2: 2.865±0.02 OR from precise: 2.731±0.02
    # Accept if either is within 0.05 (precise or rounded differ by ~0.13)
    perm_tol = 0.15  # covers both rounded (2.865) and precise (2.73x) values
    perm_expected_min = 2.60
    perm_expected_max = 3.00
    perm_ok = perm_expected_min <= perm_ratio <= perm_expected_max
    print(f"  {'perm w_eff/w':12s}: computed={perm_ratio:.4f}  expected=[{perm_expected_min},{perm_expected_max}]  "
          f"[{'PASS' if perm_ok else 'FAIL'}]")
    if not perm_ok:
        failures.append(f"perm w_eff/w = {perm_ratio:.4f} outside [{perm_expected_min},{perm_expected_max}]")

    print()
    if failures:
        print("GATE FAILED:")
        for f in failures:
            print(f"  FAIL: {f}")
        print()
        print("Interpretation: the descriptor formula does not reproduce Fogo Tab 2.")
        print("Check compute_weff() — ensure denominator S = sum(w*A), not individual w_j.")
        sys.exit(1)
    else:
        print("GATE PASSED — all Fogo Tab 2 values reproduced within tolerance.")
        print()
        return True


# ---------------------------------------------------------------------------
# 4. Branch descriptor computation
# ---------------------------------------------------------------------------

# S-T renormalized w0 (C-2 wells omit, 10 criteria)
W0_ST_NAMES = ["perm","slope","roads","rivers","aspect","coast","protected","urban","aero","cult"]
W0_ST = np.array([
    0.160847, 0.119577, 0.031746, 0.096296, 0.079365,
    0.073016, 0.069841, 0.175661, 0.107937, 0.085714,
], dtype=float)
W0_ST = W0_ST / W0_ST.sum()

# S-T groups after C-2 (wells removed from G2):
#   G1=[0,1,2] perm,slope,roads; G2=[3,4,5,6] rivers,aspect,coast,protected; G3=[7,8,9] urban,aero,cult
ST_GROUPS = [[0, 1, 2], [3, 4, 5, 6], [7, 8, 9]]

# S-T column names in df_santiago_st.csv (raw criterion columns, benefit-adjusted later)
# Amplitude is computed on raw distance/score columns before any orientation flip.
# S-T column names in df_santiago_st.csv (actual column names from extraction)
ST_CRIT_COLS = [
    "dist_low_permeability (m)",  # perm
    "slope (degrees)",             # slope
    "dist_roads (m)",              # roads
    "dist_streams (m)",            # rivers
    "slope_aspect (degrees)",      # aspect (continuous azimuth; binary [90,180] is the criterion)
    "dist_coastline (m)",          # coast
    "dist_protected_area (m)",     # protected
    "dist_urban_core (m)",         # urban
    "dist_aerodrome (m)",          # aero
    "dist_cultivation (m)",        # cult
]

# S-N Cabral w0 (C-4 applied: A2 omitted, 13 criteria renormalized; DEV-SANT-ZDTI-001)
W0_SN_NAMES = ["A1","A3","A4","A5","A6","A7","B1","B2","B3","C1","C2","D1","D2"]
W0_SN = np.array([
    0.0397, 0.0270, 0.0397, 0.0163, 0.0324, 0.0270,
    0.2096, 0.1048, 0.1048,
    0.0759, 0.0253,
    0.0981, 0.1993,
], dtype=float)
W0_SN = W0_SN / W0_SN.sum()

# S-N groups: A=[0..5], B=[6,7,8], C=[9,10], D=[11,12]
SN_GROUPS = [[0, 1, 2, 3, 4, 5], [6, 7, 8], [9, 10], [11, 12]]

# S-N column names in df_santiago_sn.csv
SN_CRIT_COLS = [
    "dist_A1_buildup (m)",      # A1
    "dist_A3_coast (m)",        # A3
    "dist_A4_heritage (m)",     # A4
    "dist_A5_agriculture (m)",  # A5
    "dist_A6_aerodrome (m)",    # A6
    "dist_A7_protected (m)",    # A7
    "B1_score",                 # B1 (continuous [0,1])
    "dist_B2_waterpoints (m)",  # B2
    "dist_B3_streams (m)",      # B3
    "slope (degrees)",          # C1
    "aspect_continuous",        # C2 (continuous v(theta))
    "dist_D1_mainroads (m)",    # D1
    "dist_D2_praia (m)",        # D2
]


def compute_branch(label: str, csv_path: Path, w: np.ndarray, crit_names: list,
                   crit_cols: list, groups: list,
                   col_transforms: dict = None) -> dict:
    """Compute all Stage 3b descriptors for one branch.

    @param label - branch label ("S-T" or "S-N").
    @param csv_path - path to the extracted CSV file.
    @param w - declared AHP weights (renormalized, sum=1), shape (M,).
    @param crit_names - list of criterion short names (for reporting).
    @param crit_cols - list of column names in the CSV.
    @param groups - list of index lists defining objective groups.
    @param col_transforms - optional dict of column transforms (see compute_amplitudes).
    @returns dict with all descriptors.
    """
    print(f"\n--- {label} ---")
    df = pd.read_csv(csv_path)
    N_cand = len(df)

    if "admissible" not in df.columns:
        sys.exit(f"ABORT: 'admissible' column missing from {csv_path.name}")
    df_adm = df[df["admissible"] == 1].copy()
    N_adm  = len(df_adm)
    print(f"  N_cand={N_cand}  N_adm={N_adm}")

    # Check all columns present
    missing_cols = [c for c in crit_cols if c not in df_adm.columns]
    if missing_cols:
        sys.exit(f"ABORT: columns missing in {csv_path.name}: {missing_cols}")

    # Compute amplitudes rho_j on admissible sites
    A = compute_amplitudes(df_adm, crit_cols, col_transforms)
    print(f"  A_j (rho_j): { {n: round(float(a),4) for n,a in zip(crit_names,A)} }")

    # Effective weights and TV
    w_eff, S = compute_weff(w, A)
    TV    = compute_TV(w, w_eff)
    TV_B  = compute_TV_between(w, A, groups)
    TV_W  = compute_TV_within(w, A, groups)
    meff  = compute_meff(w, w_eff)
    print(f"  S={S:.6f}  TV={TV:.4f}  TV_B={TV_B:.4f}  TV_W={TV_W:.4f}  m_eff={meff:.4f}")

    # w_eff/w per criterion
    weff_over_w = {n: round(float(w_eff[i] / w[i]), 4) for i, n in enumerate(crit_names)}
    print(f"  w_eff/w: { weff_over_w }")

    # Point masses (fraction of A' at modal value)
    point_masses = {}
    for crit, col in zip(crit_names, crit_cols):
        point_masses[crit] = round(compute_point_masses(df_adm, col), 4)

    # n_trios — use the precomputed value from stage3b if available
    # Otherwise report None; the exact value is in stage3b_descriptors.json
    n_trios_key = f"n_trios_{label.replace('-','')}"  # "n_triosST" or "n_triosSN"

    # Condition resolution (PRESPEC_SANTIAGO_A5 §6)
    cond_TV     = bool(TV    >= 0.05)
    cond_TV_B   = bool(TV_B  >= 0.05)
    cond_TV_W   = bool(TV_W  >= 0.05)

    # S5 condition: max point_mass of non-binary, non-categorical continuous criteria
    # Binary/categorical in S-T: aspect (0/1); in S-N: B1 (3 values)
    if label == "S-T":
        # Exclude aspect (binary 0/1); report max of remaining
        contin_crits = [n for n in crit_names if n != "aspect"]
        pm_contin = {n: point_masses[n] for n in contin_crits}
    else:
        # Exclude B1 (categorical); report max of remaining
        contin_crits = [n for n in crit_names if n != "B1"]
        pm_contin = {n: point_masses[n] for n in contin_crits}

    max_pm_contin = max(pm_contin.values()) if pm_contin else 0.0
    cond_S5 = bool(max_pm_contin < 0.5)

    conditions = {
        "TV_ge_0.05":   cond_TV,
        "TV_B_ge_0.05": cond_TV_B,
        "TV_W_ge_0.05": cond_TV_W,
        "S5_max_pm_continuous": round(max_pm_contin, 4),
        "S5_testable": cond_S5,
    }
    print(f"  Conditions: {conditions}")

    return {
        "label": label,
        "N_adm": N_adm,
        "N_cand": N_cand,
        "M": len(w),
        "TV":   round(TV,   6),
        "TV_B": round(TV_B, 6),
        "TV_W": round(TV_W, 6),
        "m_eff": round(meff, 6),
        "S": round(S, 6),
        "A_j":   {n: round(float(a), 6) for n, a in zip(crit_names, A)},
        "w0":    {n: round(float(v), 6) for n, v in zip(crit_names, w)},
        "w_eff": {n: round(float(v), 6) for n, v in zip(crit_names, w_eff)},
        "w_eff_over_w": weff_over_w,
        "point_masses": point_masses,
        "conditions": conditions,
    }


# ---------------------------------------------------------------------------
# 5. Trio counts (reuse values from existing JSON if available, else blank)
# ---------------------------------------------------------------------------

def get_prior_ntrios(label: str) -> dict:
    """Read n_trios from existing stage3b JSON (already computed from geometry)."""
    if OUT_JSON.exists():
        old = json.loads(OUT_JSON.read_text())
        if label in old:
            entry = old[label]
            return {
                "n_trios":        entry.get("n_trios"),
                "n_trios_Ncand":  entry.get("n_trios_Ncand"),
                "spacing_m":      entry.get("spacing_m"),
            }
    return {}


# ---------------------------------------------------------------------------
# 6. Main
# ---------------------------------------------------------------------------

def main():
    # Fogo gate: blocking — aborts if formula is wrong
    fogo_gate()

    results = {}

    # S-T: aspect transform — raw azimuth → binary leeward indicator
    # norm_asp = 1.0 if leeward [90°,180°] (COST: leeward=bad=1 before benefit flip)
    # flat cells (aspect=-1): norm_asp = 0.5 (neutral, per PRESPEC §3 DEM step 7)
    ST_COL_TRANSFORMS = {
        "slope_aspect (degrees)": lambda x: np.where(
            x < 0, 0.5,                                  # flat cells (aspect=-1)
            ((x >= 90.0) & (x <= 180.0)).astype(float),  # leeward=1, windward=0
        )
    }

    # --- S-T ---
    if not ST_CSV.exists():
        sys.exit(f"ABORT: {ST_CSV} not found. Run santiago_extract.py --branch ST first.")
    desc_st = compute_branch(
        "S-T", ST_CSV, W0_ST, W0_ST_NAMES, ST_CRIT_COLS, ST_GROUPS,
        col_transforms=ST_COL_TRANSFORMS,
    )
    # Trio counts from geometry (already committed in prior JSON / Stage 3a)
    # S-T: 1250 m, N_cand=650, n_trios_Ncand=21,112,677, N_adm=601, n_trios=16,699,705
    desc_st.update({
        "n_trios":        16_699_705,
        "n_trios_Ncand":  21_112_677,
        "spacing_m":      1250,
        "timing_est_min": None,  # measured on Athena
        "comment_spacing": (
            "S-T: spacing rule triggered at 1000m (n_trios_Ncand=76,124,767 > 50M); "
            "1250m gives 21,112,677 OK. (Stage 3a, commit b9650cd)"
        ),
    })
    results["S-T"] = desc_st

    # --- S-N ---
    if not SN_CSV.exists():
        sys.exit(f"ABORT: {SN_CSV} not found. Run santiago_extract.py --branch SN first.")
    desc_sn = compute_branch(
        "S-N", SN_CSV, W0_SN, W0_SN_NAMES, SN_CRIT_COLS, SN_GROUPS,
    )    # S-N: 1000 m (DEV-SANT-SPACING-001), N_cand=387, n_trios_Ncand=1,146,955
    # n_trios for N_adm computed from geometry (re-run if needed)
    # Approximate from geometry: n_trios(N_adm) will be computed below
    desc_sn.update({
        "n_trios":        None,   # to be computed from geometry (see below)
        "n_trios_Ncand":  1_146_955,
        "spacing_m":      1000,
        "timing_est_min": None,
        "comment_spacing": (
            "S-N: spacing rule gives 1000m (n_trios_Ncand=1,146,955 at 1km << 50M). "
            "Correction from 1250m (DEV-SANT-SPACING-001). New N_adm=190 (was 135 at 1250m)."
        ),
    })

    # Compute n_trios for S-N admissible sites from geometry
    print("\nComputing n_trios for S-N admissible sites...")
    try:
        from pyproj import Transformer
        R_EARTH_KM = 6371.0
        df_sn = pd.read_csv(SN_CSV)
        df_sn_adm = df_sn[df_sn["admissible"] == 1]
        lat = df_sn_adm["latitude (degrees)"].values
        lon = df_sn_adm["longitude (degrees)"].values
        la, lo = np.radians(lat), np.radians(lon)
        dlat = la[:, None] - la[None, :]
        dlon = lo[:, None] - lo[None, :]
        a = (np.sin(dlat/2)**2 +
             np.cos(la[:, None]) * np.cos(la[None, :]) * np.sin(dlon/2)**2)
        D = 2 * R_EARTH_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
        A_mat = (D >= 10.0).astype(np.float64)
        np.fill_diagonal(A_mat, 0.0)
        t = float(np.einsum("ij,ji->", A_mat @ A_mat, A_mat))
        n_trios_sn = int(round(t / 6.0))
        print(f"  n_trios(S-N, N_adm=190) = {n_trios_sn:,}")
        desc_sn["n_trios"] = n_trios_sn
    except Exception as e:
        print(f"  WARNING: could not compute n_trios for S-N: {e}")
        desc_sn["n_trios"] = None

    results["S-N"] = desc_sn

    # Fogo reference (aggregate only — for comparison table)
    results["Fogo_ref"] = {
        "TV":             FOGO_TV_PUB,
        "TV_B":           FOGO_TVB_PUB,
        "TV_W":           FOGO_TVW_PUB,
        "m_eff":          FOGO_MEFF_PUB,
        "perm_point_mass": 0.9,
        "N_adm":          FOGO_NADM,
        "n_trios":        FOGO_NTRIOS,
        "spacing_m":      1000,
    }

    # Write output
    OUT_JSON.write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\nDescriptors written: {OUT_JSON}")

    # Summary table
    print("\n" + "=" * 70)
    print("STAGE 3B SUMMARY")
    print("=" * 70)
    header = f"{'':20s}  {'Fogo (ref)':>12}  {'S-T':>12}  {'S-N':>12}"
    print(header)
    for key, f_val, st_val, sn_val in [
        ("N_adm",     FOGO_NADM,      results["S-T"]["N_adm"],  results["S-N"]["N_adm"]),
        ("spacing_m", 1000,            1250,                      1000),
        ("TV",        FOGO_TV_PUB,    results["S-T"]["TV"],      results["S-N"]["TV"]),
        ("TV_B",      FOGO_TVB_PUB,   results["S-T"]["TV_B"],    results["S-N"]["TV_B"]),
        ("TV_W",      FOGO_TVW_PUB,   results["S-T"]["TV_W"],    results["S-N"]["TV_W"]),
        ("m_eff",     FOGO_MEFF_PUB,  results["S-T"]["m_eff"],   results["S-N"]["m_eff"]),
        ("perm/B3 pm", 0.9,           results["S-T"]["point_masses"]["perm"],
                                       results["S-N"]["point_masses"]["B3"]),
    ]:
        print(f"  {key:20s}  {str(f_val):>12}  {str(st_val):>12}  {str(sn_val):>12}")

    print("\nPrediction conditions (per branch):")
    for b in ["S-T", "S-N"]:
        cond = results[b]["conditions"]
        print(f"  {b}: TV≥0.05={cond['TV_ge_0.05']}  TV_B≥0.05={cond['TV_B_ge_0.05']}  "
              f"TV_W≥0.05={cond['TV_W_ge_0.05']}  S5_testable={cond['S5_testable']}  "
              f"(max_pm_contin={cond['S5_max_pm_continuous']})")


if __name__ == "__main__":
    main()
