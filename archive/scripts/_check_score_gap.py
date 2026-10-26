# -*- coding: utf-8 -*-
"""
Verifica score gap para os 43 draws onde greedy != optimal em saw_vec_aligned.
Hipótese H1 (score ties): se score_gap ≈ 0, o portfolio é diferente mas o score é igual.

Run: uv run python scripts/_check_score_gap.py
"""
import sys, numpy as np, pandas as pd, ast, re
sys.path.insert(0, 'scripts')
from pathlib import Path
from scipy.stats import dirichlet as sp_dirichlet

ROOT = Path(__file__).parent.parent

# Infrastructure (same as _f8_vec_frontier_coincidence.py)
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix,
    F1_CRIT, F2_CRIT, F3_CRIT, INV as INV_SET, COST as COST_SET, _norm as _mm_norm
)
import json

df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL['protected']] > 0].copy()
N = len(df_via); assert N == 389
cols = list(AHP_WEIGHTS.keys())
w_ahp = np.array(list(AHP_WEIGHTS.values()))

X_via, benefit = _build_decision_matrix(df_via)
benefit = np.array(benefit)

trios = np.load(ROOT / 'data' / 'fogo_trios.npy')
T0, T1, T2 = trios[:, 0], trios[:, 1], trios[:, 2]

amp = json.loads((ROOT / 'results' / 'amplitudes' / 'amplitudes.json').read_text())
rho_shift = np.array([amp['rho_j'][k] for k in cols])
norms_shift = 1.0 / np.maximum(rho_shift, 1e-12)

f1_set = set(F1_CRIT); f2_set = set(F2_CRIT)
C_vec_raw = np.zeros((N, len(cols)), dtype=np.float64)
for j, k in enumerate(cols):
    x = df_via[COL[k]].values.astype(np.float64)
    if k == 'aspect':
        c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
    else:
        c = _mm_norm(x, x)
    L2_c = max(float(np.sqrt((c**2).sum())), 1e-12)
    C_vec_raw[:, j] = c / L2_c

sign_obj = np.array([-1.0 if k in (f1_set | f2_set) else 1.0 for k in cols])
C_score_vec = np.zeros((N, len(cols)), dtype=np.float64)
for j, k in enumerate(cols):
    if k == 'aspect':
        C_score_vec[:, j] = np.where(
            (df_via[COL[k]].values.astype(float) >= 90) &
            (df_via[COL[k]].values.astype(float) <= 180), 0.0, 1.0)
    elif k in INV_SET:
        C_score_vec[:, j] = 1.0 - C_vec_raw[:, j]
    else:
        C_score_vec[:, j] = C_vec_raw[:, j]

def saw_vec_aligned(w):
    return (C_score_vec * (w * sign_obj)).sum(axis=1)

D_via = np.load(ROOT / 'data' / 'fogo_trios.npy')  # not distance, reload separately
from mcdm_experiment import haversine_km, MIN_DIST_KM
D_via = haversine_km(df_via["latitude (degrees)"].values, df_via["longitude (degrees)"].values)
valid = D_via >= MIN_DIST_KM

def top_greedy(scores):
    order = np.argsort(scores)[::-1]
    sel = []
    for idx in order:
        if all(valid[idx, s] for s in sel):
            sel.append(idx)
        if len(sel) == 3: break
    if len(sel) < 3: return None
    return frozenset(sel)

# Load coincidence CSV to find the 43 discordant draws
coinc = pd.read_csv(ROOT / 'results' / 'f8' / 'f8_coincidence_v2.csv')
diff_draws = coinc[coinc['vv_same'] == 0]['draw'].values
print(f"Draws com portfolio diferente (vv_same=0): {len(diff_draws)}")

# Recompute saw_vec_aligned scores for those draws
N_DRAWS = 500; KAPPA = 200; SEED = 42
W_DRAWS = sp_dirichlet.rvs(w_ahp * KAPPA, size=N_DRAWS, random_state=np.random.default_rng(SEED))

score_gaps = []
tied_count = 0
for d in diff_draws:
    w = W_DRAWS[d]
    scores = saw_vec_aligned(w)
    trio_scores = scores[T0] + scores[T1] + scores[T2]

    opt_idx = int(trio_scores.argmax())
    grd_fs  = top_greedy(scores)
    if grd_fs is None:
        continue

    grd_score = sum(scores[s] for s in grd_fs)
    opt_score = trio_scores[opt_idx]
    gap = float(opt_score - grd_score)
    score_gaps.append(gap)
    if abs(gap) < 1e-12:
        tied_count += 1

gaps = np.array(score_gaps)
print(f"\nScore gap (opt - grd) nos 43 draws discordantes:")
print(f"  min={gaps.min():.2e}  max={gaps.max():.2e}  mean={gaps.mean():.2e}")
print(f"  Draws com gap < 1e-12 (score tie): {tied_count}")
print(f"  Draws com gap > 1e-12 (opt genuinamente melhor): {len(gaps) - tied_count}")
print()
print("INTERPRETAÇÃO:")
if tied_count > 0:
    print(f"  {tied_count} dos 43 são score ties: greedy e optimal escolhem trios diferentes")
    print(f"  com o MESMO score SAW. Ambos são válidos; argmax usa o índice do array como tiebreak.")
    print(f"  {len(gaps) - tied_count} draws: greedy é genuinamente subóptimo no SAW (gap > 0).")
    print(f"  \FEightVecCoinc{{457}} = correcta; 43 = {tied_count} ties + {len(gaps)-tied_count} genuinamente diferentes")
else:
    print(f"  Sem score ties: os 43 draws são genuinamente diferentes (greedy subóptimo).")
    print(f"  A hipótese H1 não se aplica.")
