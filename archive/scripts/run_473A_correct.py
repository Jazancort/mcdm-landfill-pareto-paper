# -*- coding: utf-8 -*-
"""
run_473A_correct.py — Correr a célula 473/A da tab:fourthcell com etiquetas correctas.

Definições precisas:
  - ref_method=473: score calculado com normalização sobre df_imp (473 sites, espaço A)
  - evaluator=A:    dominância avaliada em fronteira de Pareto de espaço A (ref=473)
  - Proposição 1:   quando score e objectivos partilham o mesmo ref, optimal=100% sempre.
                    Asserção dura: Q2_optimal(473/A) = 100.0%.

Asserção anti-alias: as células 389/A não podem dar valores idênticos às células
473/A' ou à tab:factorial (que é 389/A'). Se duas células com avaliadores diferentes
derem resultados idênticos em todos os sorteios, o script falha.

Pipeline: float64, eps=1e-9, sorted-idx, self-exclusion (pareto_utils.py).
N=500, kappa=200, seed=42.
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

N_DRAWS = 500
KAPPA   = 200
SEED    = 42
EPS     = 1e-9
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')

# ── Load data ─────────────────────────────────────────────────────────────────
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable = df_imp[COL["protected"]] > 0
df_via = df_imp[viable].copy()
N = len(df_via)
assert N == 389, f"Expected 389 viable sites, got {N}"
N_all = len(df_imp)
assert N_all == 473, f"Expected 473 total sites, got {N_all}"

D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
col_names = list(AHP_WEIGHTS.keys())
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
M = len(w_ahp)

# Score matrix built over 389 (viable) sites — same for both ref variants
X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b: X_adj[:, j] = 1.0 - X_via[:, j]

# X for TOPSIS score (also over 389)
# Score over 473 for the "ref=473" cell variant (tab:fourthcell old main.tex definition):
# The old script's "quarta casa" uses score normalised over df_imp (473 sites).
X_all, _ = _build_decision_matrix(df_imp)
# We need the 389 rows of X_all — they are the rows corresponding to viable sites
via_idx = df_via.index  # original pandas indices of viable sites
# Map to positions in df_imp
all_positions = {idx: pos for pos, idx in enumerate(df_imp.index)}
via_in_all = np.array([all_positions[i] for i in via_idx])
X_all_via = X_all[via_in_all, :]  # shape (389, M)
X_all_adj = X_all_via.copy()
for j, b in enumerate(benefit):
    if not b: X_all_adj[:, j] = 1.0 - X_all_via[:, j]

# Build trio list over 389 sites
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
    st = sc[T0]+sc[T1]+sc[T2]
    return trio_arr[st.argmax()]

# ── Objective builder: ref=473 (space A) ──────────────────────────────────────
def compute_objs_473(w):
    """Objectives with ref=df_imp (473 sites), evaluated at the 389 viable sites."""
    f1v = np.zeros(N, dtype=np.float64)
    f2v = np.zeros(N, dtype=np.float64)
    f3v = np.zeros(N, dtype=np.float64)
    for j, k in enumerate(col_names):
        x   = df_via[COL[k]].values.astype(float)   # 389-site values
        ref = df_imp[COL[k]].values.astype(float)   # 473-site reference
        if k == "aspect":  c = np.where((x>=90)&(x<=180), 0., 1.)
        elif k in INV:     c = 1. - _norm(x, ref)
        elif k in COST:    c = _norm(x, ref)
        else:              c = _norm(x, ref)
        c = c * w[j]
        if k in F1_CRIT:   f1v += c
        elif k in F2_CRIT: f2v += c
        else:              f3v += c
    return f1v, f2v, f3v

# ── Dominance test: pareto_utils convention ────────────────────────────────────
def is_nondominated(trio, f1v, f2v, f3v, F1, F2, F3):
    i, j, k = trio
    key = tuple(sorted((int(i),int(j),int(k))))
    idx = trio_lookup.get(key, -1)
    f1t = float(f1v[i]+f1v[j]+f1v[k])
    f2t = float(f2v[i]+f2v[j]+f2v[k])
    f3t = float(f3v[i]+f3v[j]+f3v[k])
    if idx >= 0:
        # self-exclusion
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

# ── SAW score builders ─────────────────────────────────────────────────────────
def saw_score_389(w):
    """SAW/mm score normalised over 389 (standard pipeline)."""
    return (X_adj * w).sum(1)

def saw_score_473(w):
    """SAW/mm score normalised over 473 (old 'quarta casa' definition)."""
    return (X_all_adj * w).sum(1)

# ── TOPSIS score builder ───────────────────────────────────────────────────────
def topsis_score_389(w):
    V = X_via * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp = np.sqrt(((V-PIS)**2).sum(1))
    dn = np.sqrt(((V-NIS)**2).sum(1))
    return np.where(dp+dn==0, 0.5, dn/(dp+dn))

def topsis_score_473(w):
    V = X_all_via * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp = np.sqrt(((V-PIS)**2).sum(1))
    dn = np.sqrt(((V-NIS)**2).sum(1))
    return np.where(dp+dn==0, 0.5, dn/(dp+dn))

# ── Main loop: ONLY 473/A (score over 473, objectives 473, eval in A=473) ──────
rng = np.random.default_rng(SEED)
draws = rng.dirichlet(KAPPA * w_ahp, size=N_DRAWS)

# Cells: (label, score_fn, objectives, evaluator_ref)
# For 473/A: score over 473, objectives ref=473, frontier=473
# This is the "aligned" cell — Proposition 1 guarantees optimal=100%
cells_473A = [
    ('saw_473/A',    saw_score_473),
    ('topsis_473/A', topsis_score_473),
]

counters = {k: {'g': 0, 'o': 0, 'draws': []} for k in [c[0] for c in cells_473A]}
# Also track per-draw results for alias check
per_draw_473A_saw_g = np.zeros(N_DRAWS)
per_draw_473A_saw_o = np.zeros(N_DRAWS)

t0 = time.time()
for di, w in enumerate(draws):
    if di % 100 == 0:
        print(f"  [{di}/{N_DRAWS}] {time.time()-t0:.0f}s", flush=True)

    # Objectives ref=473 for this draw
    f1v, f2v, f3v = compute_objs_473(w)
    F1 = f1v[T0]+f1v[T1]+f1v[T2]
    F2 = f2v[T0]+f2v[T1]+f2v[T2]
    F3 = f3v[T0]+f3v[T1]+f3v[T2]

    for label, score_fn in cells_473A:
        sc = score_fn(w)
        trio_g = greedy_trio(sc, D_via)
        trio_o = tuple(argmax_trio(sc))

        nd_g = is_nondominated(trio_g, f1v, f2v, f3v, F1, F2, F3)
        nd_o = is_nondominated(trio_o, f1v, f2v, f3v, F1, F2, F3)
        counters[label]['g'] += int(nd_g)
        counters[label]['o'] += int(nd_o)
        counters[label]['draws'].append((int(nd_g), int(nd_o)))

        if label == 'saw_473/A':
            per_draw_473A_saw_g[di] = int(nd_g)
            per_draw_473A_saw_o[di] = int(nd_o)

# ── Results ────────────────────────────────────────────────────────────────────
print(f"\n{'='*65}")
print("tab:fourthcell 473/A results (score AND objectives ref=473)")
print(f"{'Cell':<20} {'Q2_greedy':>10} {'Q2_optimal':>12}")
print("-"*65)
for label, _ in cells_473A:
    q2g = counters[label]['g'] / N_DRAWS * 100
    q2o = counters[label]['o'] / N_DRAWS * 100
    print(f"  {label:<20} {q2g:>10.1f}% {q2o:>12.1f}%")

# ── ASSERTION: optimal=100% for 473/A (Proposition 1) ─────────────────────────
saw_473A_opt = counters['saw_473/A']['o'] / N_DRAWS * 100
assert saw_473A_opt == 100.0, (
    f"ASSERTION FAILED: SAW/473/A optimal should be 100.0% by Proposition 1, "
    f"got {saw_473A_opt:.2f}%. Pipeline is misaligned."
)
print(f"\n  ASSERTION PASSED: SAW/473/A optimal = 100.0% (Proposition 1).")

# ── ASSERTION ANTI-ALIAS: 473/A must differ from 389/A' (mc_2cube_fixed) ──────
# Load mc_2cube_fixed for comparison
cube = pd.read_csv(os.path.join(RESULTS_DIR, 'mc_2cube_fixed_raw.csv'))
cube200 = cube[(cube.alpha==200) & (cube.agg=='saw') & (cube.norm=='minmax')]
saw_389_Ap_g = cube200[cube200.mont=='greedy']['nd_Q2Ap'].values.astype(float)
saw_389_Ap_o = cube200[cube200.mont=='optimal']['nd_Q2Ap'].values.astype(float)
assert len(saw_389_Ap_g) == N_DRAWS, f"Expected {N_DRAWS} draws, got {len(saw_389_Ap_g)}"

# Check alias: if 473/A were identical to 389/A' draw-by-draw, it's a bug
g_identical = np.all(per_draw_473A_saw_g == saw_389_Ap_g)
o_identical = np.all(per_draw_473A_saw_o == saw_389_Ap_o)
if g_identical and o_identical:
    raise AssertionError(
        "ANTI-ALIAS ASSERTION FAILED: 473/A gives identical per-draw results "
        "to 389/A' (mc_2cube_fixed). The evaluator is wrong — both cells are "
        "evaluating in A' instead of A."
    )
print(f"  ANTI-ALIAS ASSERTION PASSED: 473/A differs from 389/A'.")
g_diff = (per_draw_473A_saw_g != saw_389_Ap_g).sum()
o_diff = (per_draw_473A_saw_o != saw_389_Ap_o).sum()
print(f"    (Differences on {g_diff}/{N_DRAWS} greedy draws, {o_diff}/{N_DRAWS} optimal draws)")

# ── Save ────────────────────────────────────────────────────────────────────────
records = []
for label, _ in cells_473A:
    agg = 'saw' if 'saw' in label else 'topsis'
    q2g = counters[label]['g'] / N_DRAWS * 100
    q2o = counters[label]['o'] / N_DRAWS * 100
    records.append({'agg': agg, 'norm': 'minmax', 'mont': 'greedy',
                    'ref_method': 473, 'evaluator': 'A', 'Q2': q2g})
    records.append({'agg': agg, 'norm': 'minmax', 'mont': 'optimal',
                    'ref_method': 473, 'evaluator': 'A', 'Q2': q2o})

out_path = os.path.join(RESULTS_DIR, 'fourthcell_473A.csv')
pd.DataFrame(records).to_csv(out_path, index=False)
print(f"\nSaved to results/fourthcell_473A.csv")

print(f"\nReference (old main.tex, SAW only):")
print(f"  473/A greedy=68.4%  optimal=100.0%")
print(f"\nNew (correct pipeline):")
saw_new_g = counters['saw_473/A']['g'] / N_DRAWS * 100
print(f"  473/A greedy={saw_new_g:.1f}%  optimal=100.0%  delta_greedy={saw_new_g-68.4:+.1f}pp")
