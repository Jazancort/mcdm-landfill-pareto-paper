# -*- coding: utf-8 -*-
"""audit_pareto_independent.py

Independent Pareto dominance implementation for E6 validation.

DOES NOT import anything from run_e6_generator.py.
Uses only numpy + standard library.

Pareto frontier for the E6 problem:
  F0 (cost G1)  — minimise
  F1 (cost G2)  — minimise
  F2 (benefit G3) — maximise

A trio t dominates trio u iff:
  F0(t) <= F0(u)  AND  F1(t) <= F1(u)  AND  F2(t) >= F2(u)
  with at least one strict inequality.

We implement this as a naive O(n^2) brute-force for correctness,
then compare n_pareto against the CSV for a sample of instances.
"""
import numpy as np
import json
import pandas as pd
from pathlib import Path

ROOT  = Path(__file__).parent.parent
e6_dir = ROOT / "results" / "e6"

# ── Independent implementations (no import from run_e6_generator) ───────────

def ind_haversine_dist(lat, lon):
    """Great-circle distance matrix in km. Pure numpy."""
    lat_r = np.radians(lat[:, None])
    lon_r = np.radians(lon[:, None])
    dlat  = lat_r - lat_r.T
    dlon  = lon_r - lon_r.T
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat))[:, None] * \
        np.cos(np.radians(lat))[None, :] * np.sin(dlon/2)**2
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def ind_feasible_trios(lat, lon, dmin_km):
    """All (i,j,k) with pairwise dist >= dmin_km. Independent implementation."""
    dist = ind_haversine_dist(lat, lon)
    ok   = dist >= dmin_km
    np.fill_diagonal(ok, False)
    ii, jj = np.where(np.triu(ok, k=1))
    trios = []
    for idx in range(len(ii)):
        i, j = ii[idx], jj[idx]
        ks = np.where(ok[i, j+1:] & ok[j, j+1:])[0] + j + 1
        for k in ks:
            trios.append((i, j, int(k)))
    return np.array(trios, dtype=np.int32) if trios else np.empty((0,3), dtype=np.int32)


def ind_objectives(X_norm, trios, groups, W_G):
    """
    Compute group objectives for each trio.
    groups: list of lists, e.g. [[0,1,2],[3,4,5,6,7],[8,9,10]]
    W_G:    group weights, e.g. [0.295, 0.356, 0.349]
    Returns F (n_trios, 3): F0 min, F1 min, F2 max.
    Cost criteria: G0 (indices 0-2) and G1 (indices 3-7) → cost, use (1-x)
    Benefit criteria: G2 (indices 8-10) → benefit, use x
    """
    W_crit = np.concatenate([
        np.full(len(g), W_G[gi] / len(g)) for gi, g in enumerate(groups)
    ])
    W_crit /= W_crit.sum()

    X_trios = X_norm[trios]           # (T, 3, 11)
    # Cost groups: oriented = 1 - x
    cost_idx = list(range(0, 8))
    ben_idx  = list(range(8, 11))
    X_or = X_trios.copy()
    X_or[:, :, cost_idx] = 1.0 - X_trios[:, :, cost_idx]

    w_g0 = W_crit[groups[0]]
    w_g1 = W_crit[groups[1]]
    w_g2 = W_crit[groups[2]]

    F0 = -(X_or[:, :, groups[0]] * w_g0).sum(axis=(1, 2))   # cost → minimise (negated)
    F1 = -(X_or[:, :, groups[1]] * w_g1).sum(axis=(1, 2))   # cost → minimise
    F2 =  (X_or[:, :, groups[2]] * w_g2).sum(axis=(1, 2))   # benefit → maximise
    return np.column_stack([F0, F1, F2])


def ind_pareto_brute(F):
    """
    Brute-force O(n^2) non-dominated set for 3 objectives.
    F0, F1: minimise.  F2: maximise.
    Returns set of non-dominated indices.
    """
    n = len(F)
    dominated = np.zeros(n, dtype=bool)
    for i in range(n):
        if dominated[i]:
            continue
        for j in range(n):
            if i == j or dominated[j]:
                continue
            # Does j dominate i?
            # j dom i iff F0[j]<=F0[i] AND F1[j]<=F1[i] AND F2[j]>=F2[i]
            # with at least one strict
            if (F[j, 0] <= F[i, 0] and F[j, 1] <= F[i, 1] and F[j, 2] >= F[i, 2] and
                    (F[j, 0] < F[i, 0] or F[j, 1] < F[i, 1] or F[j, 2] > F[i, 2])):
                dominated[i] = True
                break
    return set(np.where(~dominated)[0])


# ── Configuration (must match run_e6_generator.py constants) ────────────────
GROUPS  = [[0, 1, 2], [3, 4, 5, 6, 7], [8, 9, 10]]
W_G     = np.array([0.295, 0.356, 0.349])
DMIN_KM = 5.0
BBOX_KM = 80.0


def regenerate_instance(N, geometry, sp_seed):
    """
    Regenerate one E6 instance using numpy only.
    Mirrors generate_sites and generate_criteria exactly.
    """
    # Sites (same RNG as generate_sites)
    rng = np.random.default_rng(sp_seed)
    lat0, lon0 = 14.9, -24.4
    deg_per_km = 1.0 / 111.0
    if geometry == "uniform":
        x = rng.uniform(0, BBOX_KM, N)
        y = rng.uniform(0, BBOX_KM, N)
    elif geometry == "clustered":
        n_c = 3
        cx  = rng.uniform(BBOX_KM*0.2, BBOX_KM*0.8, n_c)
        cy  = rng.uniform(BBOX_KM*0.2, BBOX_KM*0.8, n_c)
        sig = BBOX_KM / 8
        idx = rng.integers(0, n_c, N)
        x   = np.clip(rng.normal(cx[idx], sig), 0, BBOX_KM)
        y   = np.clip(rng.normal(cy[idx], sig), 0, BBOX_KM)
    elif geometry == "grid":
        n_side = int(np.ceil(np.sqrt(N)))
        xs = np.linspace(5, BBOX_KM-5, n_side)
        ys = np.linspace(5, BBOX_KM-5, n_side)
        xx, yy = np.meshgrid(xs, ys)
        pts = np.column_stack([xx.ravel(), yy.ravel()])[:N]
        jit = rng.normal(0, BBOX_KM/50, (N, 2))
        x = np.clip(pts[:,0]+jit[:,0], 0, BBOX_KM)
        y = np.clip(pts[:,1]+jit[:,1], 0, BBOX_KM)
    else:
        raise ValueError(geometry)
    lat = lat0 + y * deg_per_km
    lon = lon0 + x * deg_per_km

    # Criteria (same RNG as generate_criteria: seed + 1000)
    rng2  = np.random.default_rng(sp_seed + 1000)
    X_raw = rng2.uniform(0, 1, (N, 11))

    # Min-max normalise
    lo = X_raw.min(axis=0); hi = X_raw.max(axis=0)
    rng_c = hi - lo; rng_c[rng_c == 0] = 1.0
    X_norm = (X_raw - lo) / rng_c

    return lat, lon, X_norm


# ── Main audit ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    seeds = json.load(open(e6_dir / "e6_seeds.json"))
    df    = pd.read_csv(e6_dir / "e6_raw_results.csv")

    # Test a sample of instances (first 5: N=50, all geometries and seeds varied)
    test_cases = [
        (50, "uniform",   10),
        (50, "clustered", 10),
        (50, "grid",      10),
        (50, "uniform",   20),
        (100,"uniform",   10),
    ]

    print("=" * 65)
    print("INDEPENDENT PARETO AUDIT (no import from run_e6_generator)")
    print("Brute-force O(n^2) dominance vs CSV n_pareto")
    print("=" * 65)

    all_match = True
    for N, geom, sid in test_cases:
        inst_id = f"N{N}_{geom}_s{sid}"
        lat, lon, X_norm = regenerate_instance(N, geom, sid)
        trios  = ind_feasible_trios(lat, lon, DMIN_KM)
        F      = ind_objectives(X_norm, trios, GROUPS, W_G)

        # Brute-force (exact) — slow but independent
        par_brute = ind_pareto_brute(F)

        # CSV value
        row = df[(df.inst_id==inst_id) & (df.draw==0) &
                 (df.condition=="M") & (df.assembly=="optimal")]
        n_par_csv = int(row.n_pareto.values[0]) if len(row) > 0 else -1

        match = len(par_brute) == n_par_csv
        print(f"  {inst_id:22s}  n_trios={len(trios):6d}  "
              f"n_pareto_brute={len(par_brute):4d}  "
              f"n_pareto_csv={n_par_csv:4d}  match={match}")
        if not match:
            all_match = False

    print()
    if all_match:
        print("INDEPENDENT AUDIT PASSED — brute-force dominance agrees with CSV")
    else:
        print("INDEPENDENT AUDIT FAILED — see mismatches above")
        raise SystemExit(1)
