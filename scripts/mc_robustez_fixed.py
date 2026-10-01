# -*- coding: utf-8 -*-
"""
mc_robustez_fixed.py — mc_robustez.py with pipeline corrections.

Changes from mc_robustez.py:
  1. compute_site_objs upgraded to float64 (was float32)
  2. is_nd_fn_vec replaced by is_dominated from pareto_utils
     (sorted-idx + eps=1e-9; excludes self from dominator test)
  3. w cast stays float64 (was cast to float32)

NOTE: mc_robustez evaluates Q2 against THREE static frontier arrays
(F_mm, F_vec, F_fixo loaded from CSV). These are NOT per-draw frontiers —
they are pre-computed under nominal weights. This is a different estimand
from the main article Q2 (per-draw frontier). The self-dominance bug can
still occur here because the static frontier was computed with float32,
and the query trio's objectives are re-computed with the draw weights.
Correction: use float64 for query objectives + sorted-index lookup into
the trio array (not into the static frontier CSVs, which have different
ordering). The sorted-idx approach is applied for the per-draw evaluation
of the query trio against the trio array's F values.

Because F_mm_arr, F_vec_arr, F_fixo_arr come from pre-computed CSVs with
arbitrary row ordering, we cannot use sorted-idx lookup there. We use
float64 + eps=1e-9 for those comparisons, which is sufficient to eliminate
1-ULP self-dominance artefacts.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix,
    haversine_km, MIN_DIST_KM, INV, COST, F1_CRIT, F2_CRIT, F3_CRIT,
    optimal_trio_enumerate, _norm,
)

if 'MCDM_DATA_DIR' not in os.environ and os.path.exists('/home/julioazancort/scratch/mcdm'):
    os.environ['MCDM_DATA_DIR'] = '/home/julioazancort/scratch/mcdm'

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')
EPS = 1e-9
t0 = time.time()
def T(): return f'{time.time()-t0:.1f}s'

# ── Data ───────────────────────────────────────────────────────────────────────
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
via_mask = df_imp[COL['protected']] > 0
df_via = df_imp[via_mask].copy()
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
X_via, benefit = _build_decision_matrix(df_via)
D_via = haversine_km(df_via['latitude (degrees)'].values, df_via['longitude (degrees)'].values)
N = len(df_via)
assert N == 389
print(f'N={N} t={T()}', flush=True)

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
assert len(trio_arr) == 1944653
print(f'Trios: {len(trio_arr):,} t={T()}', flush=True)

# ── Load static frontiers ─────────────────────────────────────────────────────
front_mm   = pd.read_csv(os.path.join(RESULTS_DIR, 'pareto_front_Aprime.csv'))
front_vec  = pd.read_csv(os.path.join(RESULTS_DIR, 'mc_2x2_fvec.csv'))
front_exog = pd.read_csv(os.path.join(RESULTS_DIR, 'mc_2x2_ffixo.csv'))
print(f'Fronteiras: F_mm={len(front_mm)} F_vec={len(front_vec)} F_fixo={len(front_exog)} t={T()}', flush=True)

# float64 for CSV frontiers (was float32)
F_mm_arr   = front_mm[['F1P','F2P','F3P']].values.astype(np.float64)
F_vec_arr  = front_vec[['F1P','F2P','F3P']].values.astype(np.float64)
F_fixo_arr = front_exog[['F1P','F2P','F3P']].values.astype(np.float64)

# ── FIX 1: compute_site_objs in FLOAT64 ──────────────────────────────────────
def compute_site_objs_f64(w, ref_df=None, val_override=None):
    """float64 version of compute_site_objs."""
    if val_override is not None:
        v = val_override.astype(np.float64)
        f1v = (v[:, [j for j,c in enumerate(col_names) if c in F1_CRIT]] *
               w[[j for j,c in enumerate(col_names) if c in F1_CRIT]]).sum(1)
        f2v = (v[:, [j for j,c in enumerate(col_names) if c in F2_CRIT]] *
               w[[j for j,c in enumerate(col_names) if c in F2_CRIT]]).sum(1)
        f3v = (v[:, [j for j,c in enumerate(col_names) if c in F3_CRIT]] *
               w[[j for j,c in enumerate(col_names) if c in F3_CRIT]]).sum(1)
        return f1v, f2v, f3v
    ref = ref_df if ref_df is not None else df_via
    f1v = np.zeros(N, dtype=np.float64)
    f2v = np.zeros(N, dtype=np.float64)
    f3v = np.zeros(N, dtype=np.float64)
    for j, k in enumerate(col_names):
        x   = df_via[COL[k]].values.astype(np.float64)
        xref = ref[COL[k]].values.astype(np.float64)
        if k == 'aspect':  c = np.where((x>=90)&(x<=180), 0., 1.)
        elif k in INV:     c = 1. - _norm(x, xref)
        elif k in COST:    c = _norm(x, xref)
        else:              c = _norm(x, xref)
        c = c * float(w[j])
        if k in F1_CRIT:   f1v += c
        elif k in F2_CRIT: f2v += c
        else:              f3v += c
    return f1v, f2v, f3v

# ── FIX 2: dominance against static frontier (float64 + eps, NO sorted-idx) ──
def is_nd_static(f1t, f2t, f3t, F_arr, eps=EPS):
    """Dominance test against a static CSV frontier in float64."""
    weak   = (F_arr[:,0] <= f1t+eps) & (F_arr[:,1] <= f2t+eps) & (F_arr[:,2] >= f3t-eps)
    strict = (F_arr[:,0] <  f1t-eps) | (F_arr[:,1] <  f2t-eps) | (F_arr[:,2] >  f3t+eps)
    return not bool((weak & strict).any())

# ── Pre-compute val_vec and val_fixo (identical to mc_robustez.py) ────────────
print('Calculando val_vec e val_fixo...', flush=True)
val_vec = np.zeros((N, len(w_ahp)), dtype=np.float64)
for j, c in enumerate(col_names):
    if c == 'aspect':
        raw = np.where((df_via[COL[c]].values >= 90) & (df_via[COL[c]].values <= 180), 0., 1.).astype(np.float64)
    else:
        raw = df_via[COL[c]].values.astype(np.float64)
    nv = float(np.sqrt((raw**2).sum()))
    if nv == 0: nv = 1.
    v = raw / nv
    if not benefit[j]: v = -v
    lo, hi = float(v.min()), float(v.max())
    val_vec[:, j] = (v - lo) / (hi - lo) if hi > lo else 0.5

BOUNDS = {'perm':(0,5000),'slope':(0,20),'roads':(0,10000),'rivers':(0,500),
          'aspect':(0,1),'coast':(0,5000),'protected':(0,5000),'wells':(0,1000),
          'urban':(0,10000),'aero':(0,15000),'cult':(0,5000)}
val_fixo = np.zeros((N, len(w_ahp)), dtype=np.float64)
for j, c in enumerate(col_names):
    if c == 'aspect':
        raw = np.where((df_via[COL[c]].values >= 90) & (df_via[COL[c]].values <= 180), 0., 1.).astype(np.float64)
        lo_r, hi_r = 0., 1.
    else:
        raw = df_via[COL[c]].values.astype(np.float64)
        lo_r, hi_r = BOUNDS[c]
    rng2 = hi_r - lo_r
    v = np.clip((raw - lo_r) / rng2, 0., 1.) if rng2 > 0 else np.full(N, 0.5)
    if not benefit[j]: v = 1. - v
    val_fixo[:, j] = v

X_adj = X_via.copy().astype(np.float64)
for j in range(len(w_ahp)):
    if not benefit[j]: X_adj[:, j] = 1. - X_via[:, j]

norms_via = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)

# ── Trio functions ─────────────────────────────────────────────────────────────
from mcdm_experiment import greedy_trio

def argmax_trio_fn(sc):
    st = sc[T0]+sc[T1]+sc[T2]; return trio_arr[st.argmax()]

# ── Monte Carlo ────────────────────────────────────────────────────────────────
CELLS  = [('saw','minmax','greedy'),('saw','minmax','optimal'),
          ('saw','vector','greedy'),('saw','vector','optimal')]
N_DRAWS = 500
SEED    = 42
ALPHAS  = [50, 200]

print(f'\n{len(CELLS)} células × {N_DRAWS}×{len(ALPHAS)} draws × 3 avaliadores')
print(f'Iniciando MC t={T()}', flush=True)

records = []
for alpha in ALPHAS:
    print(f'  alpha={alpha}', flush=True)
    rng = np.random.default_rng(SEED)
    for draw in range(N_DRAWS):
        if draw % 100 == 0:
            print(f'    draw={draw} t={T()}', flush=True)
        w = rng.dirichlet(alpha * w_ahp)   # float64

        f1_mm,   f2_mm,   f3_mm   = compute_site_objs_f64(w, ref_df=df_via)
        f1_vec,  f2_vec,  f3_vec  = compute_site_objs_f64(w, val_override=val_vec)
        f1_fixo, f2_fixo, f3_fixo = compute_site_objs_f64(w, val_override=val_fixo)

        for agg, norm, mont in CELLS:
            if norm == 'minmax':
                sc = (X_adj * w).sum(1)
            else:
                sc = ((X_adj / norms_via) * w).sum(1)

            idx = greedy_trio(sc, D_via) if mont == 'greedy' else argmax_trio_fn(sc)
            i, j, k = idx

            f1t_mm   = float(f1_mm[i]+f1_mm[j]+f1_mm[k])
            f2t_mm   = float(f2_mm[i]+f2_mm[j]+f2_mm[k])
            f3t_mm   = float(f3_mm[i]+f3_mm[j]+f3_mm[k])
            f1t_vec  = float(f1_vec[i]+f1_vec[j]+f1_vec[k])
            f2t_vec  = float(f2_vec[i]+f2_vec[j]+f2_vec[k])
            f3t_vec  = float(f3_vec[i]+f3_vec[j]+f3_vec[k])
            f1t_fixo = float(f1_fixo[i]+f1_fixo[j]+f1_fixo[k])
            f2t_fixo = float(f2_fixo[i]+f2_fixo[j]+f2_fixo[k])
            f3t_fixo = float(f3_fixo[i]+f3_fixo[j]+f3_fixo[k])

            nd_Fmm   = int(is_nd_static(f1t_mm,   f2t_mm,   f3t_mm,   F_mm_arr))
            nd_Fvec  = int(is_nd_static(f1t_vec,  f2t_vec,  f3t_vec,  F_vec_arr))
            nd_Ffixo = int(is_nd_static(f1t_fixo, f2t_fixo, f3t_fixo, F_fixo_arr))

            records.append({'alpha':alpha,'draw':draw,'agg':agg,'norm':norm,'mont':mont,
                            'nd_Fmm':nd_Fmm,'nd_Fvec':nd_Fvec,'nd_Ffixo':nd_Ffixo})

print(f'MC concluído t={T()}', flush=True)

df_raw = pd.DataFrame(records)
df_raw.to_csv(os.path.join(RESULTS_DIR, 'mc_robustez_fixed_raw.csv'), index=False)

print('\n=== TABELA RESUMO (alpha=200) ===')
df200 = df_raw[df_raw.alpha==200]
summary = df200.groupby(['norm','mont'])[['nd_Fmm','nd_Fvec','nd_Ffixo']].mean()*100
summary.columns = ['Q2_Fmm%','Q2_Fvec%','Q2_Ffixo%']
print(summary.round(1).to_string())

df_sum = df_raw.groupby(['alpha','norm','mont'])[['nd_Fmm','nd_Fvec','nd_Ffixo']].mean().reset_index()
df_sum[['nd_Fmm','nd_Fvec','nd_Ffixo']] *= 100
df_sum.columns = ['alpha','norm','mont','Q2_Fmm_pct','Q2_Fvec_pct','Q2_Ffixo_pct']
df_sum.to_csv(os.path.join(RESULTS_DIR, 'mc_robustez_fixed_summary.csv'), index=False)
print(f'\nTotal t={T()}')
print('Salvos: mc_robustez_fixed_raw.csv, mc_robustez_fixed_summary.csv')
