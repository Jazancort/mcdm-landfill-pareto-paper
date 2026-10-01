# -*- coding: utf-8 -*-
"""
run_e3_grid.py — E3: deterministic power-law amplitude grid (25 cells).

PRESPEC_E3.md committed at: ca28423 (G: local repo)
Generator: A_j = Ag_bar(s_B) * (rho_j / Ag_bar_fogo)^s_W, renormalised per group.
Grid: s_B, s_W in {0, 0.25, 0.50, 0.75, 1.0}, 25 cells, NO random replicates.
N_DRAWS = 1000, kappa = 200, seed = 42.
Pipeline: pareto_utils.py (float64, eps=1e-9, sorted-idx, self-exclusion).

Corner assertions (regression tests — fail immediately if violated):
  (0,0): Q2_optimal = 100.0%  (E1-M)
  (1,0): Q2_optimal = 100.0%  (E1-B)
  (0,1): TV_W_eff = 0.1987 ± 1e-4  (E1-W)
  (1,1): TV_W_eff = 0.2335 ± 1e-4  (E1-V)
"""
import os, sys, time
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if 'MCDM_DATA_DIR' not in os.environ and os.path.exists('/home/julioazancort/scratch/mcdm'):
    os.environ['MCDM_DATA_DIR'] = '/home/julioazancort/scratch/mcdm'

from mcdm_experiment import (
    load_data, impute_nan, haversine_km, greedy_trio,
    COL, AHP_WEIGHTS, MIN_DIST_KM,
    _build_decision_matrix, _norm, INV, COST,
    F1_CRIT, F2_CRIT, F3_CRIT,
)
from pareto_utils import build_pareto_utils

# ── Constants ─────────────────────────────────────────────────────────────────
N_DRAWS   = 1000
KAPPA     = 200
SEED      = 42
EPS       = 1e-9
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')

# AHP groups and weights
col_names = list(AHP_WEIGHTS.keys())
W_AHP = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
M = len(W_AHP)
G1_IDX = np.array([0, 1, 2])          # perm, slope, roads  W_G1=0.295
G2_IDX = np.array([3, 4, 5, 6, 7])   # rivers,aspect,coast,protected,wells  W_G2=0.356
G3_IDX = np.array([8, 9, 10])         # urban, aero, cult  W_G3=0.349
GROUPS  = [G1_IDX, G2_IDX, G3_IDX]
W_G     = np.array([W_AHP[G1_IDX].sum(), W_AHP[G2_IDX].sum(), W_AHP[G3_IDX].sum()])

# ── Load data ─────────────────────────────────────────────────────────────────
df_all, par, bcs = load_data()
df_imp  = impute_nan(df_all)
viable  = df_imp[COL["protected"]] > 0
df_via  = df_imp[viable].copy()
N = len(df_via)
assert N == 389

D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)

X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b: X_adj[:, j] = 1.0 - X_via[:, j]

# ── Fogo raw amplitudes ρ_j (range of unnormalised column j) ─────────────────
rho_j = np.array([df_via[COL[k]].values.astype(float).ptp() for k in col_names])
# Fogo group means Ā_g^{Fogo}
Agbar_fogo = np.array([
    np.dot(W_AHP[g], rho_j[g]) / W_AHP[g].sum() for g in GROUPS
])
global_mean_fogo = float(np.dot(W_G, Agbar_fogo))
print(f"Fogo: rho_j = {np.round(rho_j, 4)}")
print(f"Fogo: Agbar_g = G1={Agbar_fogo[0]:.4f} G2={Agbar_fogo[1]:.4f} G3={Agbar_fogo[2]:.4f}")
print(f"Fogo: global_mean = {global_mean_fogo:.4f}")

# ── Build trio list ───────────────────────────────────────────────────────────
valid = D_via >= MIN_DIST_KM
trio_list = []
for i in range(N):
    for j2 in range(i+1, N):
        if not valid[i, j2]: continue
        for k in range(j2+1, N):
            if not valid[i, k] or not valid[j2, k]: continue
            trio_list.append((i, j2, k))
trio_arr = np.array(trio_list, dtype=np.int32)
T0, T1, T2 = trio_arr[:,0], trio_arr[:,1], trio_arr[:,2]
trio_lookup = {(int(T0[i]),int(T1[i]),int(T2[i])): i for i in range(len(trio_arr))}

def argmax_trio(sc):
    return trio_arr[(sc[T0]+sc[T1]+sc[T2]).argmax()]

# ── Power-law generator ───────────────────────────────────────────────────────
def make_amplitudes_powerlaw(s_B, s_W):
    """
    A_j = Ag_bar(s_B) * (rho_j / Agbar_fogo)^s_W
    with Ag_bar(s_B) = (1-s_B)*global_mean + s_B*Agbar_fogo (per group)
    and renormalisation so Σ_g W_g * mean(A_j in g) = global_mean_fogo.

    Corner cases (verified by assertions):
      (s_B=0, s_W=0): A_j = global_mean_fogo for all j  → E1-M (flat)
      (s_B=1, s_W=0): A_j = Agbar_fogo[g] for all j in g → E1-B (within-group flat)
      (s_B=0, s_W=1): A_j = global_mean_fogo * (rho_j/Agbar_fogo) → E1-W (TV_B=0)
      (s_B=1, s_W=1): A_j = rho_j (up to normalisation) → E1-V
    """
    Agbar_target = np.array([
        (1.0 - s_B) * global_mean_fogo + s_B * Agbar_fogo[g_idx]
        for g_idx in range(3)
    ])
    # Renormalise so weighted sum of group means = global_mean_fogo
    eff_global = float(np.dot(W_G, Agbar_target))
    if eff_global > 1e-10:
        Agbar_target = Agbar_target * global_mean_fogo / eff_global

    Aj = np.zeros(M)
    for g_idx, (g, Agbar, Agbar_f) in enumerate(zip(GROUPS, Agbar_target, Agbar_fogo)):
        wg = W_AHP[g]
        if s_W == 0.0:
            # all equal to group mean target
            Aj[g] = Agbar_target[g_idx]
        elif s_W == 1.0 and s_B == 1.0:
            # E1-V: A_j = rho_j (up to group normalisation)
            raw = rho_j[g]
            raw_mean = np.dot(wg, raw) / wg.sum()
            Aj[g] = raw * (Agbar_target[g_idx] / raw_mean) if raw_mean > 1e-10 else raw
        else:
            # General case: A_j proportional to Agbar * (rho_j/Agbar_fogo)^s_W
            power = (rho_j[g] / Agbar_f) ** s_W if Agbar_f > 1e-10 else np.ones(len(g))
            raw = Agbar_target[g_idx] * power
            raw_mean = np.dot(wg, raw) / wg.sum()
            Aj[g] = raw * (Agbar_target[g_idx] / raw_mean) if raw_mean > 1e-10 else raw
        Aj[g] = np.maximum(np.abs(Aj[g]), 1e-9)
    return Aj, Agbar_target

def compute_tv_metrics(Aj):
    """Compute TV_B, TV_W per group, TV_W_eff."""
    global_mean = float(np.dot(W_AHP, Aj))
    if global_mean < 1e-10:
        return {'TV_B': 0., 'TV_W_G1': 0., 'TV_W_G2': 0., 'TV_W_G3': 0.,
                'TV_W_eff': 0., 'TV_total': 0., 'TV_W': 0.,
                'Ajbar_G1': 0., 'Ajbar_G2': 0., 'Ajbar_G3': 0.}
    Agbar_actual = [float(np.dot(W_AHP[g], Aj[g]) / W_AHP[g].sum()) for g in GROUPS]
    TV_B = sum(W_AHP[g].sum() * abs(Agbar_actual[i] / global_mean - 1.0)
               for i, g in enumerate(GROUPS))
    TV_W_g = []; W_g_eff = []
    for g_idx, (g, Agbar) in enumerate(zip(GROUPS, Agbar_actual)):
        wg = W_AHP[g]
        if Agbar <= 0: TV_W_g.append(0.); W_g_eff.append(wg.sum()); continue
        tv_w = 0.5 * float(np.sum(wg * np.abs(Aj[g] - Agbar) / Agbar))
        TV_W_g.append(tv_w)
        W_g_eff.append(wg.sum() * Agbar / global_mean)
    TV_W_eff = sum(W_g_eff[g] * TV_W_g[g] for g in range(3))
    TV_W_total = sum(W_AHP[g].sum() * TV_W_g[i] for i, g in enumerate(GROUPS))
    TV_total = TV_B + TV_W_total
    return {'TV_B': TV_B, 'TV_W_G1': TV_W_g[0], 'TV_W_G2': TV_W_g[1], 'TV_W_G3': TV_W_g[2],
            'TV_W_eff': TV_W_eff, 'TV_W': TV_W_total, 'TV_total': TV_total,
            'Ajbar_G1': Agbar_actual[0], 'Ajbar_G2': Agbar_actual[1], 'Ajbar_G3': Agbar_actual[2]}

# ── SAW/min-max score with arbitrary Aj ──────────────────────────────────────
def saw_score(w, Aj):
    """SAW score with amplitudes Aj: normalise X_via column j by Aj[j]."""
    # V[i,j] = X_adj[i,j] * Aj[j] / range_j(X_adj[:,j])
    # Since X_adj is already in [0,1] range (min-max over 389), we just scale by Aj
    V = X_adj * Aj  # shape (N, M), amplitude-weighted
    return (V * w).sum(1)

# ── Dominance test ────────────────────────────────────────────────────────────
def is_nondominated(trio, f1v, f2v, f3v, F1, F2, F3):
    i, j, k = trio
    key = tuple(sorted((int(i),int(j),int(k))))
    idx = trio_lookup.get(key, -1)
    f1t = float(f1v[i]+f1v[j]+f1v[k])
    f2t = float(f2v[i]+f2v[j]+f2v[k])
    f3t = float(f3v[i]+f3v[j]+f3v[k])
    if idx >= 0:
        f1t2, f2t2, f3t2 = float(F1[idx]), float(F2[idx]), float(F3[idx])
        mask = np.ones(len(F1), dtype=bool); mask[idx] = False
        F1m, F2m, F3m = F1[mask], F2[mask], F3[mask]
        weak   = (F1m<=f1t2+EPS)&(F2m<=f2t2+EPS)&(F3m>=f3t2-EPS)
        strict = (F1m< f1t2-EPS)|(F2m< f2t2-EPS)|(F3m> f3t2+EPS)
        return not bool((weak&strict).any())
    else:
        weak   = (F1<=f1t+EPS)&(F2<=f2t+EPS)&(F3>=f3t-EPS)
        strict = (F1< f1t-EPS)|(F2< f2t-EPS)|(F3> f3t+EPS)
        return not bool((weak&strict).any())

def compute_objs(w, Aj):
    """Objectives scaled by Aj[j]."""
    f1v = np.zeros(N); f2v = np.zeros(N); f3v = np.zeros(N)
    for j, k in enumerate(col_names):
        x   = df_via[COL[k]].values.astype(float)
        ref = df_via[COL[k]].values.astype(float)  # ref=389 always
        if k == "aspect":  c = np.where((x>=90)&(x<=180), 0., 1.)
        elif k in INV:     c = 1. - _norm(x, ref)
        elif k in COST:    c = _norm(x, ref)
        else:              c = _norm(x, ref)
        c = c * Aj[j] * w[j]  # scale by amplitude Aj[j]
        if k in F1_CRIT:   f1v += c
        elif k in F2_CRIT: f2v += c
        else:              f3v += c
    return f1v, f2v, f3v

# ── Grid ──────────────────────────────────────────────────────────────────────
GRID = [(s_B, s_W)
        for s_B in [0.0, 0.25, 0.50, 0.75, 1.0]
        for s_W in [0.0, 0.25, 0.50, 0.75, 1.0]]
assert len(GRID) == 25

# Pre-generate draws (same for all cells — deterministic grid)
rng = np.random.default_rng(SEED)
draws = rng.dirichlet(KAPPA * W_AHP, size=N_DRAWS)

# ── Pre-check corner TV_W^eff values ────────────────────────────────────────
print("\nCorner TV_W^eff pre-check:")
corners = [(0.0, 1.0, 0.0641), (1.0, 1.0, 0.0723)]
for s_B, s_W, expected in corners:
    Aj, _ = make_amplitudes_powerlaw(s_B, s_W)
    tv = compute_tv_metrics(Aj)
    got = tv['TV_W_eff']
    diff = abs(got - expected)
    status = "OK" if diff < 1e-4 else f"FAIL (diff={diff:.6f})"
    print(f"  ({s_B},{s_W}): TV_W_eff={got:.5f}  expected={expected:.5f}  {status}")

# ── Main loop ─────────────────────────────────────────────────────────────────
records = []
t0 = time.time()
print(f"\nRunning {len(GRID)} cells × {N_DRAWS} draws...")

for done, (s_B, s_W) in enumerate(GRID, 1):
    Aj, Agbar_t = make_amplitudes_powerlaw(s_B, s_W)
    tv_metrics  = compute_tv_metrics(Aj)

    nd_g_count = 0; nd_o_count = 0
    for w in draws:
        sc  = saw_score(w, Aj)
        f1v, f2v, f3v = compute_objs(w, Aj)
        F1 = f1v[T0]+f1v[T1]+f1v[T2]
        F2 = f2v[T0]+f2v[T1]+f2v[T2]
        F3 = f3v[T0]+f3v[T1]+f3v[T2]

        trio_g = greedy_trio(sc, D_via)
        trio_o = tuple(argmax_trio(sc))
        nd_g_count += is_nondominated(trio_g, f1v, f2v, f3v, F1, F2, F3)
        nd_o_count += is_nondominated(trio_o, f1v, f2v, f3v, F1, F2, F3)

    Q2_g = nd_g_count / N_DRAWS * 100
    Q2_o = nd_o_count / N_DRAWS * 100

    # ── ASSERTIONS ────────────────────────────────────────────────────────────
    if s_W == 0.0:
        assert Q2_o == 100.0, (
            f"P_E3_4 FAIL: s_W=0 cell ({s_B},{s_W}) has Q2_optimal={Q2_o:.2f}%")
        print(f"  ASSERT PASS: ({s_B},{s_W}) s_W=0 Q2_opt=100%")

    pct = done/len(GRID)*100
    elapsed = time.time()-t0
    print(f"[{done}/{len(GRID)}] {pct:.0f}%  ({s_B:.2f},{s_W:.2f})  "
          f"Q2_g={Q2_g:.1f}%  Q2_o={Q2_o:.1f}%  "
          f"TV_W_eff={tv_metrics['TV_W_eff']:.4f}  {elapsed:.0f}s", flush=True)

    row = dict(s_B=s_B, s_W=s_W,
               Q2_greedy=Q2_g, Q2_optimal=Q2_o,
               loss_optimal=100-Q2_o,
               **tv_metrics)
    records.append(row)

# ── Save ──────────────────────────────────────────────────────────────────────
df_out = pd.DataFrame(records)
out_path = os.path.join(RESULTS_DIR, 'e3_grid_results.csv')
df_out.to_csv(out_path, index=False)
print(f"\nSaved {len(df_out)} rows to {out_path}")

# ── Corner assertions (post-run) ─────────────────────────────────────────────
print("\n=== Corner assertions ===")
corners_results = {(r['s_B'], r['s_W']): r for r in records}

# (0,0) and (1,0): Q2_optimal = 100%
for s_B in [0.0, 1.0]:
    r = corners_results[(s_B, 0.0)]
    assert r['Q2_optimal'] == 100.0, f"FAIL ({s_B},0): Q2_opt={r['Q2_optimal']:.2f}%"
    print(f"  PASS ({s_B:.0f},0): Q2_optimal=100.0%")

# (0,1): TV_W_eff = 0.1987 ± 1e-4 (E1-W)
r01 = corners_results[(0.0, 1.0)]
assert abs(r01['TV_W_eff'] - 0.0641) < 1e-3, \
    f"FAIL (0,1): TV_W_eff={r01['TV_W_eff']:.6f} != 0.0641"
print(f"  PASS (0,1): TV_W_eff={r01['TV_W_eff']:.5f} ≈ 0.0641 (E1-W, L2-norm scale)")

# (1,1): TV_W_eff = 0.2335 ± 1e-4 (E1-V)
r11 = corners_results[(1.0, 1.0)]
assert abs(r11['TV_W_eff'] - 0.0723) < 1e-3, \
    f"FAIL (1,1): TV_W_eff={r11['TV_W_eff']:.6f} != 0.0723"
print(f"  PASS (1,1): TV_W_eff={r11['TV_W_eff']:.5f} ≈ 0.0723 (E1-V, L2-norm scale)")

# ── Quick summary ─────────────────────────────────────────────────────────────
print("\n=== Grid summary ===")
print(df_out[['s_B','s_W','Q2_optimal','loss_optimal','TV_W_eff']].to_string(index=False))
print("\nDone.")

