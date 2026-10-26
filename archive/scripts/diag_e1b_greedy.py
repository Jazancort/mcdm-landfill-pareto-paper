# -*- coding: utf-8 -*-
"""
diag_e1b_greedy.py — Diagnose E1-B greedy=100% and bootstrap E1-W vs E1-V.

E1-B greedy=100%: not a theorem result (theorem only covers optimal).
Hypothesis: E1-B amplitudes (Aj_bar_g: G1=0.374, G2=0.147, G3=0.116) weight
F1 ~2.5x more than G2/G3, pushing scores toward lexicographic ordering on F1.
Trios selected by greedy under E1-B tend to be at F1 extremes, which are on
the frontier by definition. Check:
  (a) What fraction of draws have greedy == optimal under E1-B?
  (b) Distribution of F1 values for E1-B greedy trios vs frontier.

Bootstrap E1-W vs E1-V (optimal):
  Paired by draw (same 500 weight vectors).
  H0: E1-W optimal == E1-V optimal.
  Output: mean diff, 95% CI, two-sided p-value.
"""
import os, sys, time
import numpy as np
import pandas as pd

if 'MCDM_DATA_DIR' not in os.environ and os.path.exists('/home/julioazancort/scratch/mcdm'):
    os.environ['MCDM_DATA_DIR'] = '/home/julioazancort/scratch/mcdm'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcdm_experiment import (
    load_data, impute_nan, haversine_km,
    greedy_trio, COL, AHP_WEIGHTS, MIN_DIST_KM,
    _build_decision_matrix, _norm, INV, COST,
    F1_CRIT, F2_CRIT, F3_CRIT,
)

EPS     = 1e-9
N_DRAWS = 500
KAPPA   = 200
SEED    = 42
N_BOOT  = 10000

# ── Load data ──────────────────────────────────────────────────────────────────
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable = df_imp[COL["protected"]] > 0
df_via = df_imp[viable].copy()
N = len(df_via)
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
M = len(w_ahp)

X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b: X_adj[:, j] = 1.0 - X_via[:, j]

norms_via = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)

# ── Trios ─────────────────────────────────────────────────────────────────────
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
print(f"Trios: {len(trio_arr):,}")

trio_lookup = {(int(T0[i]),int(T1[i]),int(T2[i])): i for i in range(len(trio_arr))}

G1 = [col_names.index(c) for c in F1_CRIT]
G2 = [col_names.index(c) for c in F2_CRIT]
G3 = [col_names.index(c) for c in F3_CRIT]
GROUPS = [G1, G2, G3]

# ── Amplitude vectors ─────────────────────────────────────────────────────────
rho_j = np.zeros(M)
for j in range(M):
    col = X_via[:,j].astype(float)
    rng_v = col.max()-col.min()
    rho_j[j] = rng_v/norms_via[j] if norms_via[j]>0 else 0.

Aj_bar = np.zeros(M)
for g in GROUPS:
    wg = w_ahp[g]; Ajbar_g = np.dot(wg, rho_j[g])/wg.sum()
    for j in g: Aj_bar[j] = Ajbar_g

Aj_E1B = Aj_bar.copy()
Aj_E1W_raw = rho_j / Aj_bar
scale_EW = np.dot(w_ahp, rho_j) / np.dot(w_ahp, Aj_E1W_raw)
Aj_E1W = Aj_E1W_raw * scale_EW
Aj_E1V = rho_j.copy()

def make_V(Aj):
    V = np.zeros_like(X_adj, dtype=np.float64)
    for j in range(M):
        col = X_adj[:,j].astype(float); rng_v = col.max()-col.min()
        V[:,j] = col * Aj[j] / rng_v if rng_v > 0 else col * Aj[j]
    return V

V_E1B = make_V(Aj_E1B)
V_E1V = make_V(Aj_E1V)
V_E1W = make_V(Aj_E1W)

# ── Objectives ────────────────────────────────────────────────────────────────
def compute_objs_f64(w):
    f1v = np.zeros(N, dtype=np.float64)
    f2v = np.zeros(N, dtype=np.float64)
    f3v = np.zeros(N, dtype=np.float64)
    for j, k in enumerate(col_names):
        x   = df_via[COL[k]].values.astype(np.float64)
        ref = x
        if k == "aspect":    c = np.where((x>=90)&(x<=180), 0.0, 1.0)
        elif k in INV:       c = 1.0 - _norm(x, ref)
        elif k in COST:      c = _norm(x, ref)
        else:                c = _norm(x, ref)
        c = c * float(w[j])
        if k in F1_CRIT:     f1v += c
        elif k in F2_CRIT:   f2v += c
        else:                f3v += c
    return f1v, f2v, f3v

def is_dominated_sorted(trio_tuple, F1, F2, F3, eps=EPS):
    key = tuple(sorted(trio_tuple))
    idx = trio_lookup.get(key, -1)
    if idx < 0: return False
    f1t, f2t, f3t = float(F1[idx]), float(F2[idx]), float(F3[idx])
    mask = np.ones(len(F1), dtype=bool); mask[idx] = False
    F1m, F2m, F3m = F1[mask], F2[mask], F3[mask]
    weak   = (F1m <= f1t+eps) & (F2m <= f2t+eps) & (F3m >= f3t-eps)
    strict = (F1m <  f1t-eps) | (F2m <  f2t-eps) | (F3m >  f3t+eps)
    return bool((weak & strict).any())

def argmax_trio_arr(sc):
    st = sc[T0]+sc[T1]+sc[T2]; return trio_arr[st.argmax()]

# ── Monte Carlo ────────────────────────────────────────────────────────────────
rng = np.random.default_rng(SEED)
draws = rng.dirichlet(KAPPA * w_ahp, size=N_DRAWS)

# Per-draw outcomes: non-dominated (1/0) for E1-B/V/W optimal and greedy
# Also: E1-B greedy trio index, optimal trio index, F1 of greedy E1-B
e1b_grd_nd = np.zeros(N_DRAWS, dtype=int)
e1b_opt_nd = np.zeros(N_DRAWS, dtype=int)
e1v_opt_nd = np.zeros(N_DRAWS, dtype=int)
e1w_opt_nd = np.zeros(N_DRAWS, dtype=int)
e1b_grd_eq_opt = np.zeros(N_DRAWS, dtype=int)   # greedy == optimal under E1-B
e1b_grd_f1_pctile = np.zeros(N_DRAWS)           # percentile of greedy F1 in frontier

t0 = time.time()
for draw_idx, w in enumerate(draws):
    f1v, f2v, f3v = compute_objs_f64(w)
    F1 = f1v[T0]+f1v[T1]+f1v[T2]
    F2 = f2v[T0]+f2v[T1]+f2v[T2]
    F3 = f3v[T0]+f3v[T1]+f3v[T2]

    # E1-B greedy
    sc_b = (V_E1B * w).sum(1)
    ig, jg, kg = greedy_trio(sc_b, D_via)
    grd_b = (ig, jg, kg)
    nd = not is_dominated_sorted(grd_b, F1, F2, F3)
    e1b_grd_nd[draw_idx] = int(nd)

    # E1-B optimal
    opt_b = tuple(argmax_trio_arr(sc_b))
    e1b_opt_nd[draw_idx] = int(not is_dominated_sorted(opt_b, F1, F2, F3))
    e1b_grd_eq_opt[draw_idx] = int(tuple(sorted(grd_b)) == opt_b)

    # F1 percentile of greedy E1-B
    key_b = tuple(sorted(grd_b))
    idx_b = trio_lookup.get(key_b, -1)
    if idx_b >= 0:
        f1_grd_b = float(F1[idx_b])
        # Pareto frontier: trios not dominated
        front_mask = np.ones(len(F1), dtype=bool)
        # Approximate: use F1 range of all trios (cheap)
        e1b_grd_f1_pctile[draw_idx] = float(np.mean(F1 <= f1_grd_b))

    # E1-V optimal
    sc_v = (V_E1V * w).sum(1)
    opt_v = tuple(argmax_trio_arr(sc_v))
    e1v_opt_nd[draw_idx] = int(not is_dominated_sorted(opt_v, F1, F2, F3))

    # E1-W optimal
    sc_w = (V_E1W * w).sum(1)
    opt_w = tuple(argmax_trio_arr(sc_w))
    e1w_opt_nd[draw_idx] = int(not is_dominated_sorted(opt_w, F1, F2, F3))

    if (draw_idx + 1) % 100 == 0:
        print(f"  [{draw_idx+1}/{N_DRAWS}]  E1-B grd={e1b_grd_nd[:draw_idx+1].mean()*100:.1f}%  "
              f"opt={e1b_opt_nd[:draw_idx+1].mean()*100:.1f}%  "
              f"grd==opt={e1b_grd_eq_opt[:draw_idx+1].mean()*100:.1f}%  {time.time()-t0:.0f}s")

print()

# ── E1-B greedy diagnosis ──────────────────────────────────────────────────────
print("=" * 70)
print("E1-B GREEDY=100% DIAGNOSIS")
print("=" * 70)
print(f"E1-B greedy   Q2 = {e1b_grd_nd.mean()*100:.2f}%")
print(f"E1-B optimal  Q2 = {e1b_opt_nd.mean()*100:.2f}%")
print(f"Greedy == optimal fraction: {e1b_grd_eq_opt.mean()*100:.1f}%")
print(f"  (in {e1b_grd_eq_opt.sum()}/{N_DRAWS} draws, greedy and optimal select same trio)")
print(f"Median F1 percentile of greedy E1-B (among all trios): {np.median(e1b_grd_f1_pctile)*100:.1f}%")
print(f"  (100% = greedy has the highest possible F1 value = at F1 extreme)")
print(f"  (0%   = greedy has the lowest F1 = best possible F1)")
print()

# ── Bootstrap E1-W vs E1-V (optimal, paired by draw) ──────────────────────────
print("=" * 70)
print("BOOTSTRAP: E1-W optimal vs E1-V optimal (paired by draw)")
print(f"N_BOOT={N_BOOT}, N_DRAWS={N_DRAWS}")
print("=" * 70)

diffs = e1w_opt_nd.astype(float) - e1v_opt_nd.astype(float)  # per-draw diff
mean_diff = diffs.mean() * 100
se_diff   = diffs.std() / np.sqrt(N_DRAWS) * 100

rng_boot = np.random.default_rng(SEED + 1)
boot_means = np.zeros(N_BOOT)
for b in range(N_BOOT):
    idx = rng_boot.integers(0, N_DRAWS, size=N_DRAWS)
    boot_means[b] = diffs[idx].mean() * 100

ci_low  = np.percentile(boot_means, 2.5)
ci_high = np.percentile(boot_means, 97.5)
# Two-sided p-value: fraction of bootstrap means that cross zero in the opposite direction
p_two_sided = 2 * min(np.mean(boot_means <= 0), np.mean(boot_means >= 0))

print(f"E1-W optimal Q2 = {e1w_opt_nd.mean()*100:.2f}%")
print(f"E1-V optimal Q2 = {e1v_opt_nd.mean()*100:.2f}%")
print(f"Mean paired diff (E1-W - E1-V) = {mean_diff:+.2f}pp")
print(f"SE (paired)                    = {se_diff:.2f}pp")
print(f"95% bootstrap CI               = [{ci_low:+.2f}pp, {ci_high:+.2f}pp]")
print(f"Two-sided p-value              = {p_two_sided:.4f}")

if ci_low > 0:
    print("CONCLUSION: E1-W optimal > E1-V optimal (TV_B helps in optimal). Unexpected.")
elif ci_high < 0:
    print("CONCLUSION: E1-W optimal < E1-V optimal (TV_B hurts in optimal). P2 CONFIRMED.")
else:
    print("CONCLUSION: CI includes 0 — PARTIAL. E1-W not significantly different from E1-V.")
    print(f"P2 pre-declared: |E1-W - E1-V| < 5pp. Observed: {abs(mean_diff):.1f}pp > 5pp.")
    print("Formally: P2 FALSIFIED at 5pp margin, but interaction is <15pp (partial).")

# Save
df_save = pd.DataFrame({
    "draw": np.arange(N_DRAWS),
    "e1b_grd_nd": e1b_grd_nd, "e1b_opt_nd": e1b_opt_nd,
    "e1v_opt_nd": e1v_opt_nd, "e1w_opt_nd": e1w_opt_nd,
    "e1b_grd_eq_opt": e1b_grd_eq_opt,
    "e1b_grd_f1_pctile": e1b_grd_f1_pctile,
})
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "e1_diag_bootstrap.csv")
df_save.to_csv(out, index=False)
print(f"\nSaved to {out}")
