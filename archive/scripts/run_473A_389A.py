# -*- coding: utf-8 -*-
"""
run_473A_389A.py — Correr as linhas 473/A e 389/A da tab:fourthcell.

Células que faltam (SAW e TOPSIS × min-max):
  473/A:  score sobre 389, objectivos com ref=473 (espaço A), avaliados em A
  389/A:  score sobre 389, objectivos com ref=389 (espaço A), avaliados em A

Estas são as células Q2 (avaliação em A), equivalentes ao factorial mas
com avaliação em vez de A'.

Pipeline correcto: pareto_utils.py (float64, sorted-idx, eps=1e-9, sem auto-dom)
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

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable = df_imp[COL["protected"]] > 0
df_via = df_imp[viable].copy()
N = len(df_via)
assert N == 389
N_imp = len(df_imp)
assert N_imp == 473

D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
col_names = list(AHP_WEIGHTS.keys())
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
M = len(w_ahp)

X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b: X_adj[:, j] = 1.0 - X_via[:, j]

# Build trio list
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

# SAW/min-max score function
def saw_mm_score(w):
    return (X_adj * w).sum(1)

def argmax_trio(sc):
    st = sc[T0]+sc[T1]+sc[T2]
    return trio_arr[st.argmax()]

# ── Objective functions ────────────────────────────────────────────────────────
def build_objs_ref(ref_df):
    """Compute per-draw objectives with ref=ref_df (float64, like pareto_utils)."""
    def compute(w):
        f1v = np.zeros(N, dtype=np.float64)
        f2v = np.zeros(N, dtype=np.float64)
        f3v = np.zeros(N, dtype=np.float64)
        for j, k in enumerate(col_names):
            x   = df_via[COL[k]].values.astype(float)
            ref = ref_df[COL[k]].values.astype(float)
            if k == "aspect":  c = np.where((x>=90)&(x<=180), 0., 1.)
            elif k in INV:     c = 1. - _norm(x, ref)
            elif k in COST:    c = _norm(x, ref)
            else:              c = _norm(x, ref)
            c = c * w[j]
            if k in F1_CRIT:   f1v += c
            elif k in F2_CRIT: f2v += c
            else:              f3v += c
        return f1v, f2v, f3v
    return compute

compute_A_ref389 = build_objs_ref(df_via)   # ref=389, avaliador A  (frontier 389)
compute_A_ref473 = build_objs_ref(df_imp)   # ref=473, avaliador A  (frontier 473)

def dom_noself_sorted(f1t, f2t, f3t, F1, F2, F3, sorted_idx, eps=EPS):
    """Dominância com sorted_idx excluído (pareto_utils convention)."""
    f1t2, f2t2, f3t2 = float(F1[sorted_idx]), float(F2[sorted_idx]), float(F3[sorted_idx])
    mask = np.ones(len(F1), dtype=bool); mask[sorted_idx] = False
    F1m, F2m, F3m = F1[mask], F2[mask], F3[mask]
    weak   = (F1m<=f1t2+eps)&(F2m<=f2t2+eps)&(F3m>=f3t2-eps)
    strict = (F1m< f1t2-eps)|(F2m< f2t2-eps)|(F3m> f3t2+eps)
    return bool((weak&strict).any())

# Build sorted-trio lookup for self-exclusion
trio_lookup = {(int(trio_arr[i,0]),int(trio_arr[i,1]),int(trio_arr[i,2])): i
               for i in range(len(trio_arr))}

def eval_trio(trio, f1v, f2v, f3v, F1, F2, F3):
    i,j,k = trio
    key = tuple(sorted((int(i),int(j),int(k))))
    idx = trio_lookup.get(key, -1)
    f1t = float(f1v[i]+f1v[j]+f1v[k])
    f2t = float(f2v[i]+f2v[j]+f2v[k])
    f3t = float(f3v[i]+f3v[j]+f3v[k])
    if idx < 0:
        # fallback: no self-exclusion
        weak = (F1<=f1t+EPS)&(F2<=f2t+EPS)&(F3>=f3t-EPS)
        strc = (F1< f1t-EPS)|(F2< f2t-EPS)|(F3> f3t+EPS)
        return 1 if not bool((weak&strc).any()) else 0
    return 1 if not dom_noself_sorted(f1t, f2t, f3t, F1, F2, F3, idx) else 0

# ── Main loop ─────────────────────────────────────────────────────────────────
rng = np.random.default_rng(SEED)
draws = rng.dirichlet(KAPPA * w_ahp, size=N_DRAWS)

cells = [
    ('saw','minmax','greedy',  473,'A'),
    ('saw','minmax','optimal', 473,'A'),
    ('topsis','minmax','greedy',  473,'A'),
    ('topsis','minmax','optimal', 473,'A'),
    ('saw','minmax','greedy',  389,'A'),
    ('saw','minmax','optimal', 389,'A'),
    ('topsis','minmax','greedy',  389,'A'),
    ('topsis','minmax','optimal', 389,'A'),
]
# accumulators indexed by (agg, norm, mont, ref_size, evaluator)
counters = {(c[0],c[1],c[2],c[3],c[4]): 0 for c in cells}

t0 = time.time()
for di, w in enumerate(draws):
    if di % 100 == 0:
        print(f"  [{di}/{N_DRAWS}] {time.time()-t0:.0f}s", flush=True)

    # SAW/min-max score (same for both ref since score uses X_adj from df_via)
    sc_mm = saw_mm_score(w)

    # Build objectives both refs
    f1_389, f2_389, f3_389 = compute_A_ref389(w)
    f1_473, f2_473, f3_473 = compute_A_ref473(w)
    F1_389 = f1_389[T0]+f1_389[T1]+f1_389[T2]
    F2_389 = f2_389[T0]+f2_389[T1]+f2_389[T2]
    F3_389 = f3_389[T0]+f3_389[T1]+f3_389[T2]
    F1_473 = f1_473[T0]+f1_473[T1]+f1_473[T2]
    F2_473 = f2_473[T0]+f2_473[T1]+f2_473[T2]
    F3_473 = f3_473[T0]+f3_473[T1]+f3_473[T2]

    # Greedy and optimal for SAW/mm
    trio_g = greedy_trio(sc_mm, D_via)
    trio_o = tuple(argmax_trio(sc_mm))

    # TOPSIS/mm
    # benefit already computed above via _build_decision_matrix
    X_imp, benefit_imp = _build_decision_matrix(df_imp)
    # TOPSIS score over 389 sites (score always over viable sites)
    V = X_via * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp = np.sqrt(((V-PIS)**2).sum(1))
    dn = np.sqrt(((V-NIS)**2).sum(1))
    sc_top = np.where(dp+dn==0, 0.5, dn/(dp+dn))
    trio_gt = greedy_trio(sc_top, D_via)
    trio_ot = tuple(argmax_trio(sc_top))

    for ref_size, f1v, f2v, f3v, F1, F2, F3 in [
        (389, f1_389, f2_389, f3_389, F1_389, F2_389, F3_389),
        (473, f1_473, f2_473, f3_473, F1_473, F2_473, F3_473),
    ]:
        for agg, sc_g, sc_o in [('saw', trio_g, trio_o), ('topsis', trio_gt, trio_ot)]:
            nd_g = eval_trio(sc_g, f1v, f2v, f3v, F1, F2, F3)
            nd_o = eval_trio(sc_o, f1v, f2v, f3v, F1, F2, F3)
            counters[(agg,'minmax','greedy', ref_size,'A')] += nd_g
            counters[(agg,'minmax','optimal',ref_size,'A')] += nd_o

# ── Results ───────────────────────────────────────────────────────────────────
print(f"\n{'='*65}")
print(f"tab:fourthcell missing cells: 473/A and 389/A")
print(f"{'Cell':<30} {'Greedy':>8} {'Optimal':>8}")
print(f"-"*65)
for ref_size in [473, 389]:
    for agg in ['saw','topsis']:
        q2g = counters[(agg,'minmax','greedy', ref_size,'A')] / N_DRAWS * 100
        q2o = counters[(agg,'minmax','optimal',ref_size,'A')] / N_DRAWS * 100
        print(f"  {agg.upper()}/mm/{ref_size}/A           {q2g:>8.1f}% {q2o:>8.1f}%")

# For reference: tab:fourthcell old values from main.tex
print(f"\nReference (old main.tex):")
print(f"  SAW/mm/473/A           greedy=68.4%  optimal=100.0%")
print(f"  SAW/mm/389/A           greedy=46.6%  optimal=95.0%")

# Save
records = []
for (agg, norm, mont, ref_size, ev), cnt in counters.items():
    records.append({'agg': agg, 'norm': norm, 'mont': mont,
                    'ref_method': ref_size, 'evaluator': ev,
                    'Q2': cnt/N_DRAWS*100})
pd.DataFrame(records).to_csv(os.path.join(RESULTS_DIR, 'fourthcell_missing.csv'), index=False)
print(f"\nSaved to results/fourthcell_missing.csv")
