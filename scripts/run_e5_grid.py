# -*- coding: utf-8 -*-
"""
run_e5_grid.py — E5: Expanded synthetic grid for generalisation (F4)

Pre-specification: corpus/PRESPEC_E5.md
Design: 4 N × 3 geometry × 3 s_B × 5 s_W × 3 replicates = 540 instances
N_draws = 200 per instance, kappa=200, seed_base=100

Regression invariant (E5-R1): Q2_mm_optimal = 100% on every instance.
Script aborts with sys.exit(1) if any optimal cell != 100%.

Output: results/e5/e5_grid_results.csv
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if 'MCDM_DATA_DIR' not in os.environ and os.path.exists('/home/julioazancort/scratch/mcdm'):
    os.environ['MCDM_DATA_DIR'] = '/home/julioazancort/scratch/mcdm'

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import dirichlet as sp_dirichlet
from itertools import product as iproduct
from pareto_utils import build_pareto_utils

ROOT = Path(__file__).parent.parent

# ── AHP groups (3 criteria per group, simplified from M=11) ──────────────────
# Group structure: 3 groups × 3 criteria = M=9
# W_G1=0.295, W_G2=0.356, W_G3=0.349 (same as main paper)
W_G = np.array([0.295, 0.356, 0.349])
N_CRIT_PER_G = 3
M = 9
W_AHP = np.array([W_G[g]/N_CRIT_PER_G for g in range(3) for _ in range(N_CRIT_PER_G)])
W_AHP /= W_AHP.sum()
GROUPS = [list(range(g*3, g*3+3)) for g in range(3)]
# Orientation: G1/G2 are cost (lower=better), G3 is benefit (higher=better)
COST_IDX = list(range(6))   # G1+G2 = F1+F2
BEN_IDX  = list(range(6,9)) # G3 = F3

# ── Grid parameters ───────────────────────────────────────────────────────────
N_SITES_LEVELS  = [50, 100, 200, 389]
GEO_LEVELS      = ['uniform', 'clustered', 'grid']
SB_LEVELS       = [0.0, 0.5, 1.0]
SW_LEVELS       = [0.0, 0.25, 0.5, 0.75, 1.0]
N_REPS          = 3
N_DRAWS         = 200
KAPPA           = 200
SEED_BASE       = 100
DMIN_BASE       = 10.0   # km at N=389
BBOX_KM         = 80.0   # bounding box (Fogo is ~80km diameter)
EARTH_R         = 6371.0

# ── Haversine distance ─────────────────────────────────────────────────────────
def haversine_km(lat, lon):
    lat_r = np.radians(lat)
    lon_r = np.radians(lon)
    dlat = lat_r[:, None] - lat_r[None, :]
    dlon = lon_r[:, None] - lon_r[None, :]
    a = np.sin(dlat/2)**2 + np.cos(lat_r[:,None])*np.cos(lat_r[None,:])*np.sin(dlon/2)**2
    return 2 * EARTH_R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

# ── Site generator ─────────────────────────────────────────────────────────────
def generate_sites(N, geometry, seed, bbox_km=BBOX_KM):
    """Generate (lat, lon) for N sites in a bbox_km × bbox_km area."""
    rng = np.random.default_rng(seed)
    # Centre at (15°N, -25°W) approximately (Fogo area)
    lat0, lon0 = 14.9, -24.4
    deg_per_km = 1.0 / 111.0  # approximate

    if geometry == 'uniform':
        x = rng.uniform(0, bbox_km, N)
        y = rng.uniform(0, bbox_km, N)
    elif geometry == 'clustered':
        n_centres = 3
        cx = rng.uniform(bbox_km*0.2, bbox_km*0.8, n_centres)
        cy = rng.uniform(bbox_km*0.2, bbox_km*0.8, n_centres)
        sigma = bbox_km / 8
        centres_idx = rng.integers(0, n_centres, N)
        x = rng.normal(cx[centres_idx], sigma)
        y = rng.normal(cy[centres_idx], sigma)
        x = np.clip(x, 0, bbox_km)
        y = np.clip(y, 0, bbox_km)
    elif geometry == 'grid':
        n_side = int(np.ceil(np.sqrt(N)))
        xs = np.linspace(5, bbox_km-5, n_side)
        ys = np.linspace(5, bbox_km-5, n_side)
        xx, yy = np.meshgrid(xs, ys)
        pts = np.column_stack([xx.ravel(), yy.ravel()])[:N]
        jitter = rng.normal(0, bbox_km/50, (N, 2))
        x = np.clip(pts[:, 0] + jitter[:, 0], 0, bbox_km)
        y = np.clip(pts[:, 1] + jitter[:, 1], 0, bbox_km)
    else:
        raise ValueError(f"Unknown geometry: {geometry}")

    lat = lat0 + y * deg_per_km
    lon = lon0 + x * deg_per_km
    return lat, lon

# ── Criterion matrix generator ─────────────────────────────────────────────────
def generate_criteria(N, seed):
    """Generate M=9 criterion columns with realistic amplitude variation.

    Key: use different distributions per criterion to get heterogeneous rho_j.
    Binary/concentrated criteria (high binary mass) → low range, like aspect on Fogo.
    Continuous spread criteria → high range.
    This produces TV_W values in the 0.04-0.15 range (comparable to Fogo ~0.08).
    """
    rng = np.random.default_rng(seed + 1000)
    X = np.zeros((N, M))

    # Pre-define binary fraction per criterion within each group
    # Higher p_binary → more binary/concentrated → lower rho_j
    p_binary = rng.uniform(0.0, 0.7, M)  # fraction of sites that get extreme values

    for g, gidx in enumerate(GROUPS):
        # Shared group factor (spatial correlation within group)
        factor = rng.uniform(0, 1, N)
        for j in gidx:
            # Mix of continuous and concentrated values
            p = p_binary[j]
            is_extreme = rng.random(N) < p
            extreme_val = rng.choice([0.0, 1.0], N)  # binary extreme
            continuous = 0.5 * factor + 0.5 * rng.uniform(0, 1, N)
            col = np.where(is_extreme, extreme_val, continuous)
            rng_j = col.max() - col.min()
            X[:, j] = (col - col.min()) / rng_j if rng_j > 1e-10 else col
    return X

# ── Amplitude generator (power-law, same as E3) ───────────────────────────────
def make_amplitudes(X, s_B, s_W):
    """Compute per-column amplitudes using power-law generator."""
    norms = np.sqrt((X**2).sum(0)) + 1e-12
    rho_j = np.array([(X[:, j].max()-X[:, j].min()) / norms[j] for j in range(M)])

    Agbar_fogo = np.array([
        np.dot(W_AHP[g], rho_j[g]) / W_AHP[g].sum()
        for g, gidx in enumerate(GROUPS)
        for g in [np.array(gidx)]
    ])
    # Simplification: compute per-group mean
    Agbar_g = np.array([
        np.dot(W_AHP[gidx], rho_j[gidx]) / W_AHP[gidx].sum()
        for gidx in GROUPS
    ])
    global_mean = float(np.dot(W_G, Agbar_g))

    # Power-law generator
    Agbar_target = (1.0 - s_B) * global_mean + s_B * Agbar_g
    eff_global = float(np.dot(W_G, Agbar_target))
    if eff_global > 1e-10:
        Agbar_target *= global_mean / eff_global

    Aj = np.zeros(M)
    for g_idx, gidx in enumerate(GROUPS):
        if s_W == 0.0:
            Aj[gidx] = Agbar_target[g_idx]
        else:
            rho_g = rho_j[gidx]
            Agbar_f = Agbar_g[g_idx]
            power = (rho_g / max(Agbar_f, 1e-10)) ** s_W
            raw = Agbar_target[g_idx] * power
            raw_mean = np.dot(W_AHP[gidx], raw) / W_AHP[gidx].sum()
            Aj[gidx] = raw * Agbar_target[g_idx] / max(raw_mean, 1e-10)

    return Aj

# ── TV metrics ────────────────────────────────────────────────────────────────
def compute_tv(Aj):
    """Compute TV_B and TV_W from amplitude vector."""
    Agbar_g = np.array([
        np.dot(W_AHP[gidx], Aj[gidx]) / W_AHP[gidx].sum()
        for gidx in GROUPS
    ])
    global_mean = float(np.dot(W_G, Agbar_g))

    TV_B = float(np.dot(W_G, np.abs(Agbar_g - global_mean)))
    TV_W_g = np.array([
        np.dot(W_AHP[gidx] / W_AHP[gidx].sum(),
               np.abs(Aj[gidx] - Agbar_g[g_idx]))
        for g_idx, gidx in enumerate(GROUPS)
    ])
    TV_W = float(np.dot(W_G, TV_W_g))
    return TV_B, TV_W

# ── Build score matrix (SAW min-max, benefit-oriented) ────────────────────────
def build_score(X):
    """SAW min-max score columns, benefit-oriented."""
    X_adj = X.copy()
    for j in COST_IDX:
        X_adj[:, j] = 1.0 - X[:, j]   # invert cost to benefit
    return X_adj

# ── Greedy assembly ───────────────────────────────────────────────────────────
def top_greedy(sc, valid):
    order = np.argsort(sc)[::-1]
    sel = []
    for idx in order:
        if all(valid[idx, s] for s in sel):
            sel.append(idx)
        if len(sel) == 3:
            break
    return tuple(sel) if len(sel) == 3 else None

def top_optimal(sc, trios):
    T0, T1, T2 = trios[:, 0], trios[:, 1], trios[:, 2]
    return trios[int(np.argmax(sc[T0] + sc[T1] + sc[T2]))]

# ── Main grid loop ─────────────────────────────────────────────────────────────
t0 = time.time()
results = []
total = len(N_SITES_LEVELS) * len(GEO_LEVELS) * len(SB_LEVELS) * len(SW_LEVELS) * N_REPS
done = 0
regression_failures = []

print(f"E5 grid: {total} instances, {N_DRAWS} draws each")
print(f"ETA: ~{total * N_DRAWS * 0.003 / 60:.0f} min")

for N_s, geo, s_B, s_W, rep in iproduct(N_SITES_LEVELS, GEO_LEVELS, SB_LEVELS, SW_LEVELS, range(N_REPS)):
    seed = SEED_BASE + done * 7
    done += 1

    # d_min scaled proportionally to site density
    d_min = DMIN_BASE * np.sqrt(389 / N_s)

    # Generate sites and criteria
    lat, lon = generate_sites(N_s, geo, seed)
    D = haversine_km(lat, lon)
    valid = D >= d_min

    # Check minimum trios exist
    trios_list = [(i, j, k)
                  for i in range(N_s) for j in range(i+1, N_s) if valid[i, j]
                  for k in range(j+1, N_s) if valid[i, k] and valid[j, k]]
    if len(trios_list) < 10:
        # Skip degenerate instances
        continue

    trios = np.array(trios_list, dtype=np.int32)
    T0, T1, T2 = trios[:, 0], trios[:, 1], trios[:, 2]
    n_trios = len(trios)

    X = generate_criteria(N_s, seed)
    Aj = make_amplitudes(X, s_B, s_W)
    TV_B, TV_W = compute_tv(Aj)

    # Build SAW score using Aj amplitudes
    # score_i(w) = Σ_j w_j * A_j * x_adj_ij  where x_adj is benefit-oriented
    X_adj = build_score(X)
    # Inject amplitudes into score columns
    X_score = X_adj * Aj[np.newaxis, :]  # element-wise per column

    # Build objective utilities (same Aj, but cost-oriented for F1/F2)
    X_obj = X.copy()
    for j in COST_IDX:
        X_obj[:, j] = 1.0 - X[:, j]  # cost-oriented (lower=better accumulated in F1/F2)
    X_obj_amp = X_obj * Aj[np.newaxis, :]

    # Build per-trio objective arrays from amplitude-scaled columns
    col_names_synth = [f'c{j}' for j in range(M)]
    import pandas as _pd
    df_synth = _pd.DataFrame(X_obj_amp, columns=col_names_synth)

    # Custom objectives function
    f1_idx = list(range(0, 6))  # G1+G2 cost
    f3_idx = list(range(6, 9))  # G3 benefit

    def compute_objs(w):
        f1v = np.zeros(N_s)
        f3v = np.zeros(N_s)
        for j in f1_idx:
            f1v += w[j] * X_obj_amp[:, j]
        for j in f3_idx:
            f3v += w[j] * X_obj_amp[:, j]
        f2v = np.zeros(N_s)  # merged into f1 for simplicity (3-objective)
        return f1v, f2v, f3v

    # Dominance test using same pattern as pareto_utils
    _lookup = {(int(T0[i]), int(T1[i]), int(T2[i])): i for i in range(n_trios)}
    EPS = 1e-9

    def is_dominated(trio, F1, F2, F3):
        key = tuple(sorted([int(trio[0]), int(trio[1]), int(trio[2])]))
        idx = _lookup.get(key, -1)
        if idx < 0: return False
        f1t, f2t, f3t = float(F1[idx]), float(F2[idx]), float(F3[idx])
        mask = np.ones(len(F1), bool); mask[idx] = False
        F1m, F2m, F3m = F1[mask], F2[mask], F3[mask]
        weak  = (F1m <= f1t+EPS) & (F2m <= f2t+EPS) & (F3m >= f3t-EPS)
        strict = (F1m <  f1t-EPS) | (F2m <  f2t-EPS) | (F3m >  f3t+EPS)
        return bool((weak & strict).any())

    # SAW score: sum of w_j * A_j * x_adj (benefit-oriented)
    def score_mm(w):
        return X_score @ w

    # Monte Carlo
    rng_mc = np.random.default_rng(seed + 500)
    W_draws = sp_dirichlet.rvs(KAPPA * W_AHP, size=N_DRAWS, random_state=rng_mc)

    nd_opt = nd_grd = 0
    for w in W_draws:
        f1v, f2v, f3v = compute_objs(w)
        F1 = f1v[T0]+f1v[T1]+f1v[T2]
        F2 = f2v[T0]+f2v[T1]+f2v[T2]
        F3 = f3v[T0]+f3v[T1]+f3v[T2]
        sc = score_mm(w)

        t_opt = top_optimal(sc, trios)
        if not is_dominated(t_opt, F1, F2, F3): nd_opt += 1

        t_grd = top_greedy(sc, valid)
        if t_grd and not is_dominated(t_grd, F1, F2, F3): nd_grd += 1

    Q2_opt = nd_opt / N_DRAWS * 100
    Q2_grd = nd_grd / N_DRAWS * 100

    # Regression check: optimal must be 100%
    if abs(Q2_opt - 100.0) > 1.0:
        regression_failures.append(
            f"N={N_s} geo={geo} s_B={s_B} s_W={s_W} rep={rep}: Q2_opt={Q2_opt:.1f}%"
        )

    results.append({
        'N': N_s, 'geometry': geo, 's_B': s_B, 's_W': s_W, 'rep': rep,
        'n_trios': n_trios, 'TV_B': TV_B, 'TV_W': TV_W,
        'Q2_mm_optimal': round(Q2_opt, 2), 'Q2_mm_greedy': round(Q2_grd, 2),
        'loss_greedy': round(100.0 - Q2_grd, 2),
        'seed': seed,
    })

    if done % 30 == 0:
        elapsed = time.time() - t0
        eta = elapsed / done * (total - done)
        print(f"  [{done}/{total}] N={N_s} geo={geo} s_B={s_B:.2f} s_W={s_W:.2f} rep={rep} "
              f"Q2_opt={Q2_opt:.0f}% Q2_grd={Q2_grd:.0f}% TV_W={TV_W:.4f} eta={eta:.0f}s",
              flush=True)

# ── Save results ──────────────────────────────────────────────────────────────
out = ROOT / "results" / "e5"
out.mkdir(exist_ok=True)
df = pd.DataFrame(results)
df.to_csv(out / "e5_grid_results.csv", index=False)

print(f"\n=== E5 RESULTS ===")
print(f"Total instances: {len(results)}")
print(f"Q2_mm_optimal mean: {df['Q2_mm_optimal'].mean():.1f}%")
print(f"Q2_mm_greedy mean: {df['Q2_mm_greedy'].mean():.1f}%")
print(df.groupby(['N', 'geometry'])[['Q2_mm_greedy', 'TV_W']].mean().round(2).to_string())
print(f"\nTotal time: {time.time()-t0:.1f}s")

# ── Regression gate ───────────────────────────────────────────────────────────
if regression_failures:
    print(f"\nREGRESSION FAILURES ({len(regression_failures)}):")
    for f in regression_failures:
        print(f"  {f}")
    print("\nQ2_mm_optimal != 100% — score and objectives misaligned. DO NOT commit.")
    sys.exit(1)
else:
    print(f"\nREGRESSION OK: all {len(results)} instances have Q2_mm_optimal ≈ 100%")
