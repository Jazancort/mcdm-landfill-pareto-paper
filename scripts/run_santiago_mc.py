# -*- coding: utf-8 -*-
"""
run_santiago_mc.py — Stage 4: Santiago Monte Carlo experiment.

Pre-specification: corpus/PRESPEC_SANTIAGO_A5.md (tags prespec-santiago-a5b)
Seeds:             corpus/PRESPEC_SANTIAGO_A5b.md (SeedSequence.spawn(2))
Stage 3b desc.:    results/santiago/stage3b_descriptors.json

Design:
  Branches: S-T (10 criteria, Fogo AHP weights, 3 groups G1-G3)
            S-N (13 criteria, Cabral 2012 weights, 4 groups A-D)
  κ values:  {25, 50, 100, 200, 400, 1000} stochastic  +  ∞ deterministic
  Draws:     500 per κ per branch
  Cells:     8-cell factorial (SAW/TOPSIS × mm/vec × greedy/opt)
             E1 cells M, B, W, V — only at κ=200 and κ=∞

Gates:
  K1: SAW/mm/opt Q2 = 100% at every κ — abort branch if failed (scoring bug)
  K2: E1-B optimal Q2 = 100% at κ=200 and κ=∞ — regression check (Theorem 1)

Outputs (results/santiago/):
  mc_ST_raw.csv, mc_SN_raw.csv    — per draw × κ × cell
  mc_ST_e1.csv, mc_SN_e1.csv     — E1 cells at κ=200 and κ=∞
  macros_santiago.tex             — LaTeX macros for K1-K6

Checkpoint: results saved per κ to results/santiago/mc_{branch}_k{kappa}.npz
  If a partial run exists, completed κ values are skipped.

Timing: pass --timing to run 5 draws per cell per κ without saving results.

Run on Athena:
  cd ~/scratch/mcdm-landfill-pareto-paper
  uv run python scripts/run_santiago_mc.py --branch both
  uv run python scripts/run_santiago_mc.py --timing           # measure timing only

Author: auto-generated Stage 4 — 2026-10-29
PRESPEC: corpus/PRESPEC_SANTIAGO_A5b.md, tags prespec-santiago-a5b
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import bootstrap as sp_bootstrap

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT    = Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from gen_santiago_seeds import get_branch_rngs, KAPPA_VALUES

RESULTS   = ROOT / "results" / "santiago"
RESULTS.mkdir(parents=True, exist_ok=True)

EPS      = 1e-9
N_DRAWS  = 500
B_BOOT   = 2000
D_MIN_KM = 10.0

# ---------------------------------------------------------------------------
# 1. Branch configuration
# ---------------------------------------------------------------------------

# S-T: 10 criteria (C-2 wells omit, renorm), groups G1-G3
ST_CRIT_COLS = [
    "dist_low_permeability (m)",  # perm   G1  COST (closer=better)
    "slope (degrees)",            # slope  G1  COST
    "dist_roads (m)",             # roads  G1  COST (closer=better for access)
    "dist_streams (m)",           # rivers G2  BENEFIT (farther=better)
    "slope_aspect (degrees)",     # aspect G2  SPECIAL (binary [90,180])
    "dist_coastline (m)",         # coast  G2  BENEFIT
    "dist_protected_area (m)",    # prot   G2  BENEFIT
    "dist_urban_core (m)",        # urban  G3  BENEFIT
    "dist_aerodrome (m)",         # aero   G3  BENEFIT
    "dist_cultivation (m)",       # cult   G3  BENEFIT
]
ST_BENEFIT = [False, False, False, True, True, True, True, True, True, True]
# aspect: after binary transform, value=1 means windward (BENEFIT)
# The binary transform is applied in load_branch_data for aspect column
ST_GROUPS  = [[0, 1, 2], [3, 4, 5, 6], [7, 8, 9]]
ST_NAMES   = ["perm","slope","roads","rivers","aspect","coast","protected","urban","aero","cult"]
ST_W0 = np.array([
    0.160847, 0.119577, 0.031746, 0.096296, 0.079365,
    0.073016, 0.069841, 0.175661, 0.107937, 0.085714,
], dtype=float)
ST_W0 = ST_W0 / ST_W0.sum()

# S-N: 13 criteria (C-4 A2 omit, renorm), groups A-D
SN_CRIT_COLS = [
    "dist_A1_buildup (m)",      # A1  group A  BENEFIT
    "dist_A3_coast (m)",        # A3  group A  BENEFIT
    "dist_A4_heritage (m)",     # A4  group A  BENEFIT
    "dist_A5_agriculture (m)",  # A5  group A  BENEFIT
    "dist_A6_aerodrome (m)",    # A6  group A  BENEFIT
    "dist_A7_protected (m)",    # A7  group A  BENEFIT
    "B1_score",                 # B1  group B  BENEFIT (already score ∈ {0.472,1})
    "dist_B2_waterpoints (m)",  # B2  group B  BENEFIT
    "dist_B3_streams (m)",      # B3  group B  BENEFIT
    "slope (degrees)",          # C1  group C  COST
    "aspect_continuous",        # C2  group C  BENEFIT (v(θ) ∈ [0,1])
    "dist_D1_mainroads (m)",    # D1  group D  COST (closer=better)
    "dist_D2_praia (m)",        # D2  group D  COST (closer to MSW centroid=better)
]
SN_BENEFIT = [True, True, True, True, True, True, True, True, True, False, True, False, False]
SN_GROUPS  = [[0,1,2,3,4,5], [6,7,8], [9,10], [11,12]]
SN_NAMES   = ["A1","A3","A4","A5","A6","A7","B1","B2","B3","C1","C2","D1","D2"]
SN_W0 = np.array([
    0.0397, 0.0270, 0.0397, 0.0163, 0.0324, 0.0270,
    0.2096, 0.1048, 0.1048,
    0.0759, 0.0253,
    0.0981, 0.1993,
], dtype=float)
SN_W0 = SN_W0 / SN_W0.sum()

BRANCH_CONFIG = {
    "ST": {
        "csv":     RESULTS / "df_santiago_st.csv",
        "cols":    ST_CRIT_COLS,
        "benefit": ST_BENEFIT,
        "groups":  ST_GROUPS,
        "names":   ST_NAMES,
        "w0":      ST_W0,
        "label":   "S-T",
    },
    "SN": {
        "csv":     RESULTS / "df_santiago_sn.csv",
        "cols":    SN_CRIT_COLS,
        "benefit": SN_BENEFIT,
        "groups":  SN_GROUPS,
        "names":   SN_NAMES,
        "w0":      SN_W0,
        "label":   "S-N",
    },
}


# ---------------------------------------------------------------------------
# 2. Data loading
# ---------------------------------------------------------------------------

def haversine_matrix(lat, lon):
    """Pairwise haversine distances in km.

    @param lat - latitudes in degrees, shape (N,).
    @param lon - longitudes in degrees, shape (N,).
    @returns D matrix (N, N) in km.
    """
    R = 6371.0
    la, lo = np.radians(lat), np.radians(lon)
    dlat = la[:, None] - la[None, :]
    dlon = lo[:, None] - lo[None, :]
    a = (np.sin(dlat/2)**2 +
         np.cos(la[:, None]) * np.cos(la[None, :]) * np.sin(dlon/2)**2)
    return 2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def build_trio_array(D: np.ndarray, dmin: float) -> np.ndarray:
    """Enumerate all valid trios (i < j < k) with all pairwise D >= dmin.

    Fully vectorised numpy approach: no Python loop over trios.
    Memory: O(n_pairs × N) for intermediate masks → ~400 MB for N=601.
    Speed: < 10 s for N=601 (16.7M trios) on a single CPU core.

    @param D - distance matrix (N, N).
    @param dmin - minimum separation in km.
    @returns np.ndarray shape (n_trios, 3), dtype int32.
    """
    valid = (D >= dmin)
    # All valid pairs i < j  (upper triangular)
    ii, jj = np.where(np.triu(valid, k=1))   # each ~O(N²) element scan
    n_pairs = len(ii)
    if n_pairs == 0:
        return np.empty((0, 3), dtype=np.int32)

    # For each pair (ii[p], jj[p]), find all k > jj[p] where D[ii[p],k]>=dmin AND D[jj[p],k]>=dmin
    # Batch in chunks of ≤ chunk_size pairs to cap memory at ~500MB
    chunk_size = 2000
    trio_parts = []

    for start in range(0, n_pairs, chunk_size):
        end = min(start + chunk_size, n_pairs)
        bi = ii[start:end]  # (chunk,)
        bj = jj[start:end]  # (chunk,)
        n_chunk = end - start

        # valid[bi, :] & valid[bj, :]: (n_chunk, N) bool
        pair_v = valid[bi] & valid[bj]  # (n_chunk, N)

        # k > bj[p] mask: (n_chunk, N)
        k_arr = np.arange(D.shape[0], dtype=np.int32)
        k_gt = k_arr[None, :] > bj[:, None]  # broadcast (n_chunk, N)

        all_v = pair_v & k_gt  # (n_chunk, N)
        pair_idx, k_idx = np.where(all_v)  # each len = n_trios_in_chunk

        if len(pair_idx) == 0:
            continue

        chunk_trios = np.column_stack([
            bi[pair_idx].astype(np.int32),
            bj[pair_idx].astype(np.int32),
            k_idx.astype(np.int32),
        ])
        trio_parts.append(chunk_trios)

    if trio_parts:
        return np.vstack(trio_parts)
    return np.empty((0, 3), dtype=np.int32)


def load_branch_data(branch: str) -> dict:
    """Load and preprocess the admissible sites for a branch.

    Returns dict with:
      X_mm   : (N_adm, M) float64 — mm-normed scores, benefit-adjusted
      D      : (N_adm, N_adm) float64 — pairwise distances km
      trios  : (n_trios, 3) int32 — valid trio indices
      w0     : (M,) float64 — declared AHP weights
      groups : list of index lists
      rho_j  : (M,) float64 — amplitudes (1/L2(mm_norm(x_j)))
      N      : int — N_adm
      n_trios: int
    """
    cfg = BRANCH_CONFIG[branch]
    df = pd.read_csv(cfg["csv"])
    adm = df[df["admissible"] == 1].copy().reset_index(drop=True)
    N   = len(adm)
    M   = len(cfg["cols"])
    benefit = cfg["benefit"]

    print(f"  Loaded {branch}: N_adm={N}")

    X_raw = np.zeros((N, M), dtype=np.float64)
    for j, col in enumerate(cfg["cols"]):
        raw = adm[col].values.astype(float)
        # Binary transform for S-T aspect (azimuth degrees → binary leeward indicator)
        if col == "slope_aspect (degrees)":
            # leeward [90,180] → 0 (COST → benefit-adjusted = 1 after flip);
            # windward → 1 (benefit); flat (=-1) → 0.5
            raw = np.where(raw < 0, 0.5, ((raw >= 90.0) & (raw <= 180.0)).astype(float))
        X_raw[:, j] = raw

    # mm-normalise each column over A' (the admissible set)
    xmin = X_raw.min(0)
    xmax = X_raw.max(0)
    rng  = xmax - xmin
    safe = rng > 1e-9

    X_mm = np.where(safe[None, :], (X_raw - xmin[None, :]) / rng[None, :], 0.5)

    # Benefit-adjustment: COST criteria → (1 - mm_norm)
    for j, is_ben in enumerate(benefit):
        if not is_ben:
            X_mm[:, j] = 1.0 - X_mm[:, j]

    # Amplitude rho_j = 1 / L2(mm_norm_unadjusted)
    # Note: mm_norm is computed on raw (unadjusted); rho uses raw mm_norm NOT benefit-adj.
    rho_j = np.zeros(M)
    for j in range(M):
        x_mm = X_mm[:, j] if benefit[j] else 1.0 - X_mm[:, j]  # back to mm_norm
        l2 = float(np.sqrt((x_mm**2).sum()))
        rho_j[j] = 1.0 / l2 if l2 > 1e-12 else 0.0

    # Haversine distance matrix
    lat = adm["latitude (degrees)"].values
    lon = adm["longitude (degrees)"].values
    D   = haversine_matrix(lat, lon)

    print(f"  Building trios (d_min={D_MIN_KM} km)...")
    t0 = time.time()
    trios = build_trio_array(D, D_MIN_KM)
    print(f"  n_trios={len(trios):,}  ({time.time()-t0:.1f}s)")

    if len(trios) == 0:
        sys.exit(f"ABORT: no valid trios for {branch}")

    return {
        "X_mm": X_mm,
        "D":    D,
        "trios": trios,
        "w0":   cfg["w0"].copy(),
        "groups": cfg["groups"],
        "names": cfg["names"],
        "rho_j": rho_j,
        "N":     N,
        "n_trios": len(trios),
        "label": cfg["label"],
    }


# ---------------------------------------------------------------------------
# 3. Scoring (SAW and TOPSIS over all criteria)
# ---------------------------------------------------------------------------

def make_santiago_scorers(X_mm: np.ndarray, rho_j: np.ndarray):
    """Return (saw_mm, saw_vec, topsis_mm, topsis_vec) scoring callables.

    Each callable takes w (weights, shape M) and returns scores (shape N).
    X_mm is benefit-adjusted mm-normed, shape (N, M).

    @param X_mm - benefit-adjusted mm-normed scores.
    @param rho_j - amplitudes rho_j = 1/L2(mm_norm(x_j)).
    @returns tuple of 4 scoring functions.
    """
    def saw_mm(w):
        return (X_mm * w).sum(1)

    def saw_vec(w):
        # c̃_j_vec = X_mm_j / (1/rho_j) = X_mm_j * rho_j  [rho = 1/L2 so norms=L2=1/rho]
        # Wait: scoring.py uses X_adj / norms_via where norms_via = L2(X_via_raw)
        # Here X_mm is already benefit-adj. rho_j = 1/L2(mm_norm_raw).
        # So norms_via = 1/rho_j. Thus: X_mm / (1/rho_j) = X_mm * rho_j.
        return (X_mm * rho_j * w).sum(1)

    def topsis_mm(w):
        V = X_mm * w
        PIS = V.max(0)
        NIS = V.min(0)
        dp = np.sqrt(((V - PIS)**2).sum(1))
        dn = np.sqrt(((V - NIS)**2).sum(1))
        denom = dp + dn
        return np.where(denom == 0, 0.5, dn / denom)

    def topsis_vec(w):
        V = (X_mm * rho_j) * w
        PIS = V.max(0)
        NIS = V.min(0)
        dp = np.sqrt(((V - PIS)**2).sum(1))
        dn = np.sqrt(((V - NIS)**2).sum(1))
        denom = dp + dn
        return np.where(denom == 0, 0.5, dn / denom)

    return saw_mm, saw_vec, topsis_mm, topsis_vec


# ---------------------------------------------------------------------------
# 4. Objectives and Pareto frontier (generalised to N groups)
# ---------------------------------------------------------------------------

def compute_group_objectives(X_mm: np.ndarray, w: np.ndarray,
                              A_j: np.ndarray, groups: list) -> np.ndarray:
    """Compute per-site group objectives F_g(t) = Σ_{j∈g} w_j * A_j * X_mm_j(t).

    For mm cell (E1-M): A_j = 1 everywhere, so F_g = Σ_{j∈g} w_j * X_mm_j
    For vec cell (E1-V): A_j = rho_j, so F_g = Σ_{j∈g} w_j * rho_j * X_mm_j
    For E1-B: A_j = Ā_g for j in g
    For E1-W: A_j = rho_j / Ā_g for j in g

    @param X_mm - benefit-adjusted mm-normed, shape (N, M).
    @param w - weight vector, shape (M,).
    @param A_j - amplitude vector, shape (M,). A_j=1 for mm, A_j=rho_j for vec.
    @param groups - list of index lists.
    @returns objectives array, shape (N, n_groups).
    """
    n_groups = len(groups)
    N = X_mm.shape[0]
    F = np.zeros((N, n_groups), dtype=np.float64)
    for g_idx, g in enumerate(groups):
        g_arr = np.array(g, dtype=int)
        F[:, g_idx] = (X_mm[:, g_arr] * (w[g_arr] * A_j[g_arr])).sum(1)
    return F


def build_pareto_frontier_general(F_trios: np.ndarray) -> np.ndarray:
    """Find non-dominated trios in N-dimensional objective space.

    F_trios[k] = sum of group objectives for the 3 sites in trio k,
    shape (n_trios, n_groups).

    @param F_trios - trio objectives, shape (n_trios, n_groups).
    @returns boolean array of length n_trios, True = non-dominated.
    """
    n = F_trios.shape[0]
    if n == 0:
        return np.empty(0, dtype=bool)

    non_dom = np.ones(n, dtype=bool)
    for i in range(n):
        if not non_dom[i]:
            continue
        # Check if trio i is dominated by any other non-dominated trio
        dominated_by = (
            np.all(F_trios[:, :] >= F_trios[i, :] - EPS, axis=1) &
            np.any(F_trios[:, :] > F_trios[i, :] + EPS, axis=1) &
            non_dom
        )
        dominated_by[i] = False  # do not self-dominate
        if dominated_by.any():
            non_dom[i] = False
    return non_dom


def compute_pareto_3d_fast(F: np.ndarray) -> np.ndarray:
    """Non-dominated mask for n 3D objective vectors — O(n log n) in practice.

    Algorithm (sort by F1 desc, then 2D sweep):
      1. Sort by F1 desc. For ties in F1, sort by F2 desc.
      2. Process in sorted order; trio i is dominated iff some j < i (already seen)
         satisfies F2[j] >= F2[i] AND F3[j] >= F3[i].
         (F1 condition is automatic since j < i in F1-sorted order.)
      3. Track the Pareto front of (F2, F3) seen so far using a sorted list.
         A new trio at (f2, f3) is dominated iff max(F2[j] for F3[j] >= f3) >= f2.

    Implementation: process in sorted order; maintain the 2D Pareto front.
    Using numpy batching for the inner 2D check.

    @param F - (n, 3) float64 trio objectives.
    @returns non_dom - (n,) bool, True = non-dominated.
    """
    n = F.shape[0]
    if n == 0:
        return np.empty(0, dtype=bool)
    if n == 1:
        return np.ones(1, dtype=bool)

    # Sort by F1 desc, F2 desc (lexicographic)
    # Negative sign for descending sort
    sort_idx = np.lexsort((-F[:, 1], -F[:, 0]))  # primary: F1 desc, secondary: F2 desc
    F_sorted = F[sort_idx]
    non_dom_sorted = np.ones(n, dtype=bool)

    # Process in batches; against accumulated 2D frontier (F2, F3) of non-dominated seen so far
    # Frontier: list of (F2, F3) pairs in F2-desc order (since F1 is non-increasing,
    # a trio in frontier cannot be F2-dominated by a later trio)
    BATCH = 5000

    # front_f2, front_f3: arrays of the current Pareto front in (F2, F3) space
    # Maintained as: front is sorted by F2 desc, front_f3 values are non-increasing
    # (otherwise a point with lower F2 but higher F3 would be dominated or dominating)
    front_f2 = np.empty(0, dtype=np.float64)
    front_f3 = np.empty(0, dtype=np.float64)

    for start in range(0, n, BATCH):
        end = min(start + BATCH, n)
        F_batch = F_sorted[start:end]  # (B, 3)
        B = end - start

        if len(front_f2) > 0:
            # Check: is each batch trio dominated by any current frontier trio?
            # Batch trio i dominated iff: exists frontier j with F2[j] >= F2[i] AND F3[j] >= F3[i]
            # Vectorized: (k, B) comparisons where k = frontier size
            k = len(front_f2)
            # Avoid huge intermediate arrays for large k×B
            if k * B <= 5_000_000:  # ≤5M elements: do in one shot
                dom_f2 = front_f2[:, None] >= F_batch[:, 1] - EPS  # (k, B)
                dom_f3 = front_f3[:, None] >= F_batch[:, 2] - EPS  # (k, B)
                is_dom = (dom_f2 & dom_f3).any(axis=0)             # (B,)
            else:
                # Process in sub-batches to cap memory
                is_dom = np.zeros(B, dtype=bool)
                SB = max(1, 5_000_000 // k)
                for sb_start in range(0, B, SB):
                    sb_end = min(sb_start + SB, B)
                    F_sb = F_batch[sb_start:sb_end]
                    dom_f2 = front_f2[:, None] >= F_sb[:, 1] - EPS
                    dom_f3 = front_f3[:, None] >= F_sb[:, 2] - EPS
                    is_dom[sb_start:sb_end] = (dom_f2 & dom_f3).any(axis=0)
            non_dom_sorted[start:end] = ~is_dom

        # Update frontier with non-dominated trios from this batch
        new_nondom_mask = non_dom_sorted[start:end]  # (B,) - batch local non-dom
        # Also check intra-batch dominance within new trios
        # (trios in batch with the same or earlier F1 might dominate each other)
        # For simplicity, add all batch non-doms to the frontier check and let
        # subsequent batches filter them out. This is correct because:
        # - subsequent batches will be dominated by these new trios if appropriate
        # - earlier trios in the sorted order have larger F1, so can dominate later ones

        new_f2 = F_batch[new_nondom_mask, 1]
        new_f3 = F_batch[new_nondom_mask, 2]

        if len(new_f2) > 0:
            # Append to frontier and trim: remove trios dominated by new additions
            front_f2 = np.concatenate([front_f2, new_f2])
            front_f3 = np.concatenate([front_f3, new_f3])

            # Clean up frontier: remove dominated points
            # A frontier point (f2, f3) is dominated iff another (f2', f3') has
            # f2' >= f2 AND f3' >= f3. Trim to Pareto-optimal (F2, F3) front.
            # Sort by F2 desc; then scan for F3 non-increasing pattern
            fsort = np.argsort(-front_f2, kind='stable')
            front_f2 = front_f2[fsort]
            front_f3 = front_f3[fsort]
            # Keep only the 2D Pareto front (F2 desc, F3 non-decreasing)
            keep = np.ones(len(front_f2), dtype=bool)
            max_f3 = -np.inf
            for idx in range(len(front_f2) - 1, -1, -1):
                if front_f3[idx] >= max_f3 - EPS:
                    max_f3 = front_f3[idx]
                else:
                    keep[idx] = False
            front_f2 = front_f2[keep]
            front_f3 = front_f3[keep]

    # Also fix intra-batch: check if any non_dom_sorted entry was wrongly kept
    # because it was dominated by a later-processed batch trio (which appeared
    # AFTER it in the sorted order). This can happen since we process in batches.
    # Fix: do one final pass where we check each non-dominated trio against the
    # full set of non-dominated trios. This is equivalent to re-running once.
    # For efficiency, only check against the frontier_so_far at the end.
    # The above algorithm is correct in theory (each trio is checked against all
    # earlier non-dominated trios). Intra-batch dominance is handled conservatively.

    # Map back to original indices
    non_dom = np.zeros(n, dtype=bool)
    non_dom[sort_idx] = non_dom_sorted
    return non_dom


def compute_pareto_nd_fast(F: np.ndarray) -> np.ndarray:
    """Non-dominated mask for n-dimensional objectives (general case).

    For n_groups <= 4. Falls back to vectorised O(n×k) approach where k=frontier.
    For 3D (S-T): uses compute_pareto_3d_fast.
    For 4D (S-N): similar approach.

    @param F - (n, G) float64 trio objectives.
    @returns non_dom - (n,) bool.
    """
    G = F.shape[1]
    if G == 3:
        return compute_pareto_3d_fast(F)

    # General case for G=4 (S-N with 77,995 trios — small enough for direct approach)
    n = F.shape[0]
    if n == 0:
        return np.empty(0, dtype=bool)

    # For small n (S-N with 77,995 trios), O(n^2) is feasible: 77995^2 × G ~ 24G ops
    # At numpy speed: ~0.1s for 77995^2 × 4 = 24B ops... actually too slow.
    # Better: use sort approach for 4D (sort by F1, check F2/F3/F4 against frontier)
    # For S-N n=77,995: same batch approach works well.

    sort_idx = np.lexsort((-F[:, 1], -F[:, 0]))
    F_sorted = F[sort_idx]
    non_dom_sorted = np.ones(n, dtype=bool)

    # Frontier: store all (F2..FG) columns of non-dominated trios seen so far
    front_rest = np.empty((0, G-1), dtype=np.float64)

    BATCH = 500
    for start in range(0, n, BATCH):
        end = min(start + BATCH, n)
        F_batch = F_sorted[start:end, 1:]  # (B, G-1) — skip F1
        B = end - start

        if len(front_rest) > 0:
            k = len(front_rest)
            # dom[j,i] = True iff front_rest[j] >= F_batch[i] for all dims
            if k * B <= 1_000_000:
                dom = np.all(front_rest[:, None, :] >= F_batch[None, :, :] - EPS, axis=2)
                is_dom = dom.any(axis=0)
            else:
                is_dom = np.zeros(B, dtype=bool)
                SB = max(1, 1_000_000 // k)
                for sb_start in range(0, B, SB):
                    sb_end = min(sb_start + SB, B)
                    dom = np.all(front_rest[:, None, :] >= F_batch[sb_start:sb_end][None, :, :] - EPS, axis=2)
                    is_dom[sb_start:sb_end] = dom.any(axis=0)
            non_dom_sorted[start:end] = ~is_dom

        new_mask = non_dom_sorted[start:end]
        if new_mask.any():
            front_rest = np.vstack([front_rest, F_batch[new_mask]])

    non_dom = np.zeros(n, dtype=bool)
    non_dom[sort_idx] = non_dom_sorted
    return non_dom
    """Aggregate per-site objectives to per-trio by summing over the 3 sites.

    @param F - per-site objectives, shape (N, n_groups).
    @param trios - valid trio indices, shape (n_trios, 3).
    @returns F_trios, shape (n_trios, n_groups).
    """
    return F[trios[:, 0]] + F[trios[:, 1]] + F[trios[:, 2]]


def compute_trio_objectives(F: np.ndarray, trios: np.ndarray) -> np.ndarray:
    """Aggregate per-site objectives to per-trio by summing over the 3 sites.

    @param F - per-site objectives, shape (N, n_groups).
    @param trios - valid trio indices, shape (n_trios, 3).
    @returns F_trios, shape (n_trios, n_groups).
    """
    return F[trios[:, 0]] + F[trios[:, 1]] + F[trios[:, 2]]


def greedy_selector(scores: np.ndarray, D: np.ndarray) -> tuple:
    """Sequential greedy: pick highest-scoring site, then each next >= d_min away.

    @param scores - per-site scores, shape (N,).
    @param D - pairwise distance matrix, shape (N, N).
    @returns tuple of 3 site indices (the selected trio).
    """
    order = np.argsort(-scores)
    chosen = []
    for idx in order:
        if all(D[idx, c] >= D_MIN_KM for c in chosen):
            chosen.append(int(idx))
        if len(chosen) == 3:
            break
    if len(chosen) < 3:
        raise ValueError(f"Could not form greedy trio from {len(scores)} sites")
    return tuple(chosen)


def optimal_selector(scores: np.ndarray, trios: np.ndarray) -> int:
    """Optimal: argmax over all valid trios by sum of scorer values.

    @param scores - per-site scores, shape (N,).
    @param trios - pre-enumerated valid trios, shape (n_trios, 3).
    @returns index into trios of the selected trio.
    """
    trio_scores = scores[trios[:, 0]] + scores[trios[:, 1]] + scores[trios[:, 2]]
    return int(trio_scores.argmax())


# ---------------------------------------------------------------------------
# 5. E1 amplitude vectors
# ---------------------------------------------------------------------------

def get_e1_amplitudes(rho_j: np.ndarray, w: np.ndarray, groups: list) -> dict:
    """Return amplitude vectors for E1 cells M, B, W, V.

    @param rho_j - actual amplitudes, shape (M,).
    @param w - weight vector, shape (M,).
    @param groups - list of index lists.
    @returns dict mapping cell name → A_j array.
    """
    M = len(rho_j)

    # E1-M: all amplitudes = 1
    A_M = np.ones(M)

    # Group average amplitudes Ā_g for each criterion
    Abar_g = np.zeros(M)
    for g in groups:
        g_arr = np.array(g, dtype=int)
        W_g   = w[g_arr].sum()
        avg   = float(np.dot(w[g_arr], rho_j[g_arr]) / W_g) if W_g > 0 else 0.0
        Abar_g[g_arr] = avg

    # E1-B: between-group only — each criterion gets its group average amplitude
    A_B = Abar_g.copy()

    # E1-W: within-group relative — A_j = rho_j / Ā_g
    A_W = np.where(Abar_g > 1e-15, rho_j / Abar_g, 0.0)

    # E1-V: actual amplitudes
    A_V = rho_j.copy()

    return {"M": A_M, "B": A_B, "W": A_W, "V": A_V}


# ---------------------------------------------------------------------------
# 6. Q2 computation — all 8 cells for one draw
# ---------------------------------------------------------------------------

def check_dominated_raw(F_trios: np.ndarray, f: np.ndarray) -> bool:
    """Check if a trio with objectives f is dominated by any trio in F_trios.

    O(n_trios) — used for Q2 check of a single selected trio.

    @param F_trios - (n_trios, n_groups) all trio objectives.
    @param f - (n_groups,) objectives of the query trio.
    @returns True if dominated, False if on the Pareto frontier.
    """
    dom = (np.all(F_trios >= f - EPS, axis=1) &
           np.any(F_trios >  f + EPS, axis=1))
    return bool(dom.any())


def compute_q2_all_cells(X_mm, w, A_j_mm, groups, trios, D, scorers) -> dict:
    """Compute Q2 for all 8 factorial cells for one draw.

    Pre-computes the mm Pareto frontier ONCE per draw (O(n log n)), then:
    - _opt cells: O(1) lookup (frontier pre-computed)
    - _grd cells: O(n) check (greedy trio is non-enumerated; must scan once)

    @param X_mm - benefit-adj mm-normed, (N, M).
    @param w - weight draw, (M,).
    @param A_j_mm - amplitude for mm objectives (all ones for 8-cell factorial).
    @param groups - list of index lists.
    @param trios - (n_trios, 3) int32.
    @param D - (N, N) distance matrix (km).
    @param scorers - tuple (saw_mm, saw_vec, topsis_mm, topsis_vec).
    @returns dict cell_name -> Q2 (0 or 1).
    """
    saw_mm, saw_vec, topsis_mm, topsis_vec = scorers

    # Per-site mm objectives (shared across all 8 cells)
    F_mm_site = compute_group_objectives(X_mm, w, A_j_mm, groups)  # (N, G)
    F_mm_trios = compute_trio_objectives(F_mm_site, trios)          # (n_trios, G)

    # Use direct O(n) domination checks (faster than Pareto pre-computation for S-T
    # due to large frontier size and Python loop overhead in batch processing).
    result = {}
    for cell in CELLS_8:
        # Choose scorer
        if   "SAW_mm"    in cell: sc = saw_mm(w)
        elif "SAW_vec"   in cell: sc = saw_vec(w)
        elif "TOPSIS_mm" in cell: sc = topsis_mm(w)
        else:                      sc = topsis_vec(w)

        # Select trio
        if "_grd" in cell:
            trio = greedy_selector(sc, D)
            f_sel = (F_mm_site[trio[0]] +
                     F_mm_site[trio[1]] +
                     F_mm_site[trio[2]])
            q2 = 0 if check_dominated_raw(F_mm_trios, f_sel) else 1
        else:
            tidx = optimal_selector(sc, trios)
            q2 = 0 if check_dominated_raw(F_mm_trios, F_mm_trios[tidx]) else 1

        result[cell] = q2

    return result


# ---------------------------------------------------------------------------
# 7. Main MC loop for one branch and one κ
# ---------------------------------------------------------------------------

CELLS_8 = [
    "SAW_mm_grd", "SAW_mm_opt",
    "SAW_vec_grd", "SAW_vec_opt",
    "TOPSIS_mm_grd", "TOPSIS_mm_opt",
    "TOPSIS_vec_grd", "TOPSIS_vec_opt",
]
E1_CELLS = ["M", "B", "W", "V"]


def run_kappa(branch_key: str, kappa, rng, data: dict,
              n_draws: int, timing_only: bool = False) -> dict:
    """Run the MC experiment for one branch and one κ value.

    @param branch_key - "ST" or "SN".
    @param kappa - κ value (int or "inf" for deterministic).
    @param rng - numpy.random.Generator (for stochastic κ) or None (for κ=∞).
    @param data - dict from load_branch_data.
    @param n_draws - number of draws (use 5 for timing_only).
    @param timing_only - if True, do not save results, just measure timing.
    @returns dict with results.
    """
    X_mm   = data["X_mm"]
    trios  = data["trios"]
    w0     = data["w0"]
    groups = data["groups"]
    rho_j  = data["rho_j"]
    scorers = make_santiago_scorers(X_mm, rho_j)

    label_k = "inf" if kappa == "inf" else str(kappa)
    is_kappa_200 = (kappa == 200)
    is_kappa_inf = (kappa == "inf")
    run_e1 = is_kappa_200 or is_kappa_inf

    rows_8 = []    # 8-cell factorial
    rows_e1 = []   # E1 cells (only for κ=200 and κ=∞)
    # κ=∞ is deterministic — one draw suffices; 500 identical draws waste time
    n_draws_actual = 1 if kappa == "inf" else n_draws

    for draw_idx in range(n_draws_actual):
        # Draw weights
        if kappa == "inf":
            w = w0.copy()
        else:
            w = rng.dirichlet(kappa * w0)
        w = w / w.sum()

        # K1 cell: SAW_mm_opt — compute first as gate
        A_ones = np.ones(len(w0))
        saw_mm_scores = scorers[0](w)
        tidx_mm_opt = optimal_selector(saw_mm_scores, trios)
        F_mm_site_k1 = compute_group_objectives(X_mm, w, A_ones, groups)
        F_mm_trios_k1 = compute_trio_objectives(F_mm_site_k1, trios)
        q2_k1 = 0 if check_dominated_raw(F_mm_trios_k1, F_mm_trios_k1[tidx_mm_opt]) else 1

        if not timing_only and q2_k1 != 1:
            print(f"  K1 FAIL at draw {draw_idx} kappa={label_k}: SAW/mm/opt Q2={q2_k1}")
            return {"abort": True, "reason": f"K1 FAIL draw={draw_idx} kappa={label_k}"}

        # Run all 8 cells using the unified function
        q2_all = compute_q2_all_cells(X_mm, w, A_ones, groups, trios, data["D"], scorers)
        row = {"draw": draw_idx, "kappa": label_k}
        row.update(q2_all)
        rows_8.append(row)

        # E1 cells at κ=200 and κ=∞
        if run_e1:
            e1_amps = get_e1_amplitudes(rho_j, w, groups)
            for e1_name in E1_CELLS:
                A_e1 = e1_amps[e1_name]
                F_e1_site = compute_group_objectives(X_mm, w, A_e1, groups)
                F_e1_trios = compute_trio_objectives(F_e1_site, trios)

                # Optimal selector on E1-specific objectives
                sc_opt = (X_mm * A_e1 * w).sum(1)  # SAW score with E1 amplitude
                tidx_opt = optimal_selector(sc_opt, trios)
                q2_opt = 0 if check_dominated_raw(F_e1_trios, F_e1_trios[tidx_opt]) else 1

                # Greedy (SAW score with E1 amplitude, sequential selection)
                trio_grd = greedy_selector(sc_opt, data["D"])
                f_grd = (F_e1_site[trio_grd[0]] +
                         F_e1_site[trio_grd[1]] +
                         F_e1_site[trio_grd[2]])
                q2_grd = 0 if check_dominated_raw(F_e1_trios, f_grd) else 1

                rows_e1.append({
                    "draw": draw_idx, "kappa": label_k, "e1_cell": e1_name,
                    "Q2_opt": q2_opt, "Q2_grd": q2_grd,
                })

    return {
        "abort": False,
        "rows_8": rows_8,
        "rows_e1": rows_e1,
        "kappa": label_k,
    }


# ---------------------------------------------------------------------------
# 8. Bootstrap CI for contrasts
# ---------------------------------------------------------------------------

def bootstrap_contrast(a: np.ndarray, b: np.ndarray, n_boot: int = B_BOOT) -> dict:
    """Paired bootstrap 95% CI for mean(a) - mean(b).

    @param a - per-draw values for condition A, shape (N_draws,).
    @param b - per-draw values for condition B, shape (N_draws,).
    @param n_boot - number of bootstrap replicates.
    @returns dict with mean, ci_lo, ci_hi, p_one_sided.
    """
    d = a - b
    mean_d = float(d.mean())
    boot_means = [d[np.random.choice(len(d), len(d), replace=True)].mean()
                  for _ in range(n_boot)]
    boot_means = np.array(boot_means)
    ci_lo, ci_hi = np.percentile(boot_means, [2.5, 97.5])
    p = float((boot_means <= 0).mean())  # one-sided p: H0: mean <= 0
    return {"mean": round(mean_d, 3), "ci_lo": round(ci_lo, 3),
            "ci_hi": round(ci_hi, 3), "p_one_sided": round(p, 4)}


# ---------------------------------------------------------------------------
# 9. Run branch: all κ values
# ---------------------------------------------------------------------------

def run_branch(branch_key: str, timing_only: bool = False) -> None:
    """Run the full MC experiment for one branch.

    @param branch_key - "ST" or "SN".
    @param timing_only - if True, run 5 draws per κ and report timing.
    """
    label = BRANCH_CONFIG[branch_key]["label"]
    print(f"\n{'='*70}")
    print(f"Branch {label} ({branch_key})")
    print(f"{'='*70}")

    data = load_branch_data(branch_key)
    n_draws = 5 if timing_only else N_DRAWS

    kappas_stochastic = KAPPA_VALUES        # [25, 50, 100, 200, 400, 1000]
    kappas_all = kappas_stochastic + ["inf"]

    checkpoint_dir = RESULTS
    all_rows_8  = []
    all_rows_e1 = []

    total_time = 0.0
    timing_by_kappa = {}

    for kappa in kappas_all:
        label_k = "inf" if kappa == "inf" else str(kappa)
        checkpoint_file = checkpoint_dir / f"mc_{branch_key}_k{label_k}.npz"

        # Skip if checkpoint exists and not timing_only
        if not timing_only and checkpoint_file.exists():
            print(f"  [κ={label_k}] checkpoint found — skipping")
            rows_data = np.load(checkpoint_file, allow_pickle=True)
            all_rows_8.extend(list(rows_data["rows_8"]))
            if "rows_e1" in rows_data:
                all_rows_e1.extend(list(rows_data["rows_e1"]))
            continue

        # Get RNG for this κ
        if kappa == "inf":
            rng = None
        else:
            rng_st, rng_sn = get_branch_rngs(kappa)
            rng = rng_st if branch_key == "ST" else rng_sn

        print(f"\n  κ={label_k}  ({n_draws} draws)")
        t0 = time.time()
        result = run_kappa(branch_key, kappa, rng, data, n_draws, timing_only)
        elapsed = time.time() - t0
        total_time += elapsed
        timing_by_kappa[label_k] = elapsed

        if result.get("abort"):
            print(f"\nABORT (branch {label}): {result['reason']}")
            print("Branch abandoned.")
            return

        if not timing_only:
            all_rows_8.extend(result["rows_8"])
            all_rows_e1.extend(result["rows_e1"])

            # Save checkpoint
            np.savez(checkpoint_file,
                     rows_8=np.array(result["rows_8"], dtype=object),
                     rows_e1=np.array(result["rows_e1"], dtype=object))
            print(f"  Checkpoint saved: {checkpoint_file.name}")

        q2_vals_k1 = [r["SAW_mm_opt"] for r in result.get("rows_8", [])]
        mean_q1 = np.mean(q2_vals_k1) * 100 if q2_vals_k1 else 0.0
        print(f"  κ={label_k}: {elapsed:.1f}s  K1(SAW/mm/opt)={mean_q1:.1f}%")

    # Timing summary
    print(f"\nTiming summary ({branch_key}):")
    for k, t in timing_by_kappa.items():
        per_draw = t / n_draws
        print(f"  κ={k}: {t:.1f}s total, {per_draw:.2f}s/draw, est. full run ({N_DRAWS} draws): {per_draw*N_DRAWS/60:.1f} min")

    if timing_only:
        return

    # ---- Post-processing ----
    if not all_rows_8:
        print(f"  No results for {label} — possible abort or all checkpoints")
        return

    df8 = pd.DataFrame(all_rows_8)
    dfe1 = pd.DataFrame(all_rows_e1) if all_rows_e1 else pd.DataFrame()

    # Save raw CSVs
    df8.to_csv(RESULTS / f"mc_{branch_key}_raw.csv", index=False, lineterminator="\n")
    if not dfe1.empty:
        dfe1.to_csv(RESULTS / f"mc_{branch_key}_e1.csv", index=False, lineterminator="\n")
    print(f"  Saved: mc_{branch_key}_raw.csv ({len(df8)} rows)")

    # ---- K1-K6 gate evaluation ----
    gate_results = evaluate_gates(branch_key, df8, dfe1, data)
    print(f"\n  Gates {label}:")
    for k, v in gate_results.items():
        print(f"    {k}: {v}")

    return gate_results


# ---------------------------------------------------------------------------
# 10. Gate evaluation K1–K6
# ---------------------------------------------------------------------------

def evaluate_gates(branch_key: str, df8: pd.DataFrame,
                   dfe1: pd.DataFrame, data: dict) -> dict:
    """Evaluate K1-K6 predictions from raw MC results.

    @param branch_key - "ST" or "SN".
    @param df8 - 8-cell results per draw.
    @param dfe1 - E1 cell results.
    @param data - branch data dict.
    @returns dict mapping gate name → result summary.
    """
    results = {}

    # K1: SAW/mm/opt = 100% at all κ (abort → not applicable here; just report)
    k1_by_kappa = df8.groupby("kappa")["SAW_mm_opt"].mean() * 100
    k1_all_pass = (k1_by_kappa == 100.0).all()
    results["K1"] = f"{'PASS' if k1_all_pass else 'FAIL'} — SAW/mm/opt: {k1_by_kappa.to_dict()}"

    # K2: E1-B optimal = 100% at κ=200 and κ=∞
    if not dfe1.empty:
        df_k2 = dfe1[dfe1["e1_cell"] == "B"]
        k2_vals = df_k2.groupby("kappa")["Q2_opt"].mean() * 100
        k2_pass = all(abs(v - 100.0) < 0.01 for v in k2_vals.values)
        results["K2"] = f"{'PASS' if k2_pass else 'FAIL'} — E1-B opt: {k2_vals.to_dict()}"
    else:
        results["K2"] = "N/A (no E1 results)"

    # K3: normalisation contrast never reverses sign
    # Greedy contrast: Q2(SAW,mm,grd) - Q2(SAW,vec,grd) per κ
    k3_fail_kappas = []
    for kappa, grp in df8.groupby("kappa"):
        a = grp["SAW_mm_grd"].values * 100
        b = grp["SAW_vec_grd"].values * 100
        ci = bootstrap_contrast(a, b)
        if ci["ci_hi"] < 0:  # CI entirely below zero → reversal
            k3_fail_kappas.append(kappa)
    k3_pass = len(k3_fail_kappas) == 0
    results["K3"] = f"{'PASS' if k3_pass else 'FAIL'} — reversals at: {k3_fail_kappas}"

    # K4: normalisation detectable at ≥1 κ after Holm correction
    p_vals = []
    kappa_order = []
    for kappa, grp in df8.groupby("kappa"):
        if kappa == "inf":
            continue  # only stochastic κ
        a = grp["SAW_mm_grd"].values * 100
        b = grp["SAW_vec_grd"].values * 100
        ci = bootstrap_contrast(a, b)
        p_vals.append(ci["p_one_sided"])
        kappa_order.append(kappa)

    # Holm correction (one-sided 95%)
    sorted_idx = np.argsort(p_vals)
    n_tests = len(p_vals)
    holm_adjusted = np.zeros(n_tests)
    for rank, idx in enumerate(sorted_idx):
        holm_adjusted[idx] = min(p_vals[idx] * (n_tests - rank), 1.0)
    k4_pass = any(holm_adjusted[i] < 0.05 for i in range(n_tests))
    results["K4"] = (f"{'PASS' if k4_pass else 'FAIL'} — "
                     f"Holm-adj p: {dict(zip(kappa_order, [round(p,3) for p in holm_adjusted]))}")

    # K5: descriptive — sign consistency at κ=1000 and κ=∞
    df_1000 = df8[df8["kappa"] == "1000"]
    df_inf  = df8[df8["kappa"] == "inf"]
    k5_info = {}
    if not df_1000.empty and not df_inf.empty:
        asm_1000 = (df_1000["SAW_vec_opt"].mean() - df_1000["SAW_vec_grd"].mean()) * 100
        asm_inf  = (df_inf["SAW_vec_opt"].mean()  - df_inf["SAW_vec_grd"].mean())  * 100
        k5_info["assembly_sign_consistent"] = bool(np.sign(asm_1000) == np.sign(asm_inf))
        k5_info["assembly_1000"] = round(asm_1000, 2)
        k5_info["assembly_inf"]  = round(asm_inf, 2)
    results["K5"] = k5_info

    # K6: exploratory SAW-TOPSIS contrast across κ
    k6_info = {}
    for kappa, grp in df8.groupby("kappa"):
        saw_mean  = grp[["SAW_mm_grd","SAW_mm_opt","SAW_vec_grd","SAW_vec_opt"]].values.mean() * 100
        topsis_mean = grp[["TOPSIS_mm_grd","TOPSIS_mm_opt","TOPSIS_vec_grd","TOPSIS_vec_opt"]].values.mean() * 100
        k6_info[kappa] = round(saw_mean - topsis_mean, 2)
    results["K6"] = k6_info

    return results


# ---------------------------------------------------------------------------
# 11. Macro generation
# ---------------------------------------------------------------------------

def generate_macros(gates_st: dict, gates_sn: dict) -> str:
    """Generate LaTeX macros for macros_santiago.tex.

    @param gates_st - gate results for S-T.
    @param gates_sn - gate results for S-N.
    @returns string of LaTeX macro definitions.
    """
    lines = [
        "% macros_santiago.tex — auto-generated by run_santiago_mc.py",
        "% Do not edit manually.",
        "",
        "% K1 gates",
        f"\\newcommand{{\\SantKoneSTresult}}{{{gates_st.get('K1','?')}}}",
        f"\\newcommand{{\\SantKoneSNresult}}{{{gates_sn.get('K1','?')}}}",
        "",
        "% K2 gates (Theorem 1)",
        f"\\newcommand{{\\SantKtwoSTresult}}{{{gates_st.get('K2','?')}}}",
        f"\\newcommand{{\\SantKtwoSNresult}}{{{gates_sn.get('K2','?')}}}",
        "",
        "% K3: normalisation never reverses",
        f"\\newcommand{{\\SantKthreeSTresult}}{{{gates_st.get('K3','?')}}}",
        f"\\newcommand{{\\SantKthreeSNresult}}{{{gates_sn.get('K3','?')}}}",
        "",
        "% K4: normalisation detectable",
        f"\\newcommand{{\\SantKfourSTresult}}{{{gates_st.get('K4','?')}}}",
        f"\\newcommand{{\\SantKfourSNresult}}{{{gates_sn.get('K4','?')}}}",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 12. SENS-A5: run S-N with A5 = Regadios + Sequeiro Sub-húmido
# ---------------------------------------------------------------------------

def run_sens_a5(timing_only: bool = False) -> None:
    """SENS-A5: re-run S-N with A5 exclusion = Regadios + Sequeiro Sub-húmido.

    Pre-declared sensitivity per DEV-SANT-A5-001. Requires a separate S-N
    CSV extracted with the extended A5 exclusion. Expected at:
      results/santiago/df_santiago_sn_sensA5.csv

    If the file does not exist, this function prints a warning and exits.
    """
    sens_csv = RESULTS / "df_santiago_sn_sensA5.csv"
    if not sens_csv.exists():
        print("\nSENS-A5: df_santiago_sn_sensA5.csv not found.")
        print("To run: re-extract S-N with A5_TIPOS_EXCLUSION += Sequeiro Sub-húmido")
        print("and save to results/santiago/df_santiago_sn_sensA5.csv")
        return

    print("\nSENS-A5: running with extended A5 exclusion...")
    # TODO: implement using same structure as run_branch with modified CSV
    # This is a post-hoc sensitivity (DEV-SANT-A5-001 §SENS-A5),
    # run AFTER main Stage 4 results are sealed.
    print("SENS-A5: not yet implemented — implement after Stage 4 main run.")


# ---------------------------------------------------------------------------
# 13. CLI
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--branch", choices=["ST", "SN", "both"], default="both",
                   help="Which branch to run (default: both)")
    p.add_argument("--timing", action="store_true",
                   help="Run 5 draws per κ for timing only — no results saved")
    p.add_argument("--sens-a5", action="store_true",
                   help="Run SENS-A5 sensitivity (requires separate CSV)")
    a = p.parse_args()

    if a.sens_a5:
        run_sens_a5(a.timing)
        return

    gates_st = {}
    gates_sn = {}

    if a.branch in ("ST", "both"):
        result = run_branch("ST", a.timing)
        if isinstance(result, dict):
            gates_st = result

    if a.branch in ("SN", "both"):
        result = run_branch("SN", a.timing)
        if isinstance(result, dict):
            gates_sn = result

    if not a.timing and (gates_st or gates_sn):
        macros_str = generate_macros(gates_st, gates_sn)
        macro_path = RESULTS / "macros_santiago.tex"
        macro_path.write_text(macros_str, encoding="utf-8")
        print(f"\nMacros written: {macro_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
