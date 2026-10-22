# -*- coding: utf-8 -*-
"""
Raw sensitivity: compare SAW/vec with rho_shift vs rho_raw for 500 draws.
Scale factors: rho_shift/rho_raw for criteria with min_raw > 0 (slope, coast, wells, aero).
Control: first 20 draws must give same portfolio (scale is small, ~1.02-1.04).
"""
import sys, numpy as np, json
sys.path.insert(0, '/home/julioazancort/scratch/mcdm-landfill-pareto/scripts')
from pathlib import Path
import pandas as pd
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix
)
from scipy.stats import dirichlet as sp_dirichlet

ROOT = Path('/home/julioazancort/scratch/mcdm-landfill-pareto')

# Load data and amplitudes
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL['protected']] > 0].copy()
X_via, benefit = _build_decision_matrix(df_via)
cols = list(AHP_WEIGHTS.keys())
W = np.array(list(AHP_WEIGHTS.values())); W /= W.sum()

amp = json.loads((ROOT / 'results/amplitudes/amplitudes.json').read_text())
rho_shift = np.array([amp['rho_j'][k] for k in cols])

# rho_raw = range(x)/L2(x) on raw data (aspect uses binary indicator)
rho_raw = np.zeros(len(cols))
for j, k in enumerate(cols):
    if k == 'aspect':
        x = X_via[:, j].astype(float)   # binary indicator
    else:
        x = df_via[COL[k]].values.astype(float)
    rng = x.max() - x.min()
    nrm = float(np.sqrt(np.sum(x**2)))
    rho_raw[j] = rng / nrm if nrm > 0 else 0.0

scale = rho_shift / rho_raw
print('Scale factors (rho_shift/rho_raw) for criteria with scale != 1:')
for j, k in enumerate(cols):
    if abs(scale[j] - 1) > 0.001:
        print(f'  {k}: raw={rho_raw[j]:.6f} shift={rho_shift[j]:.6f} scale={scale[j]:.4f}')

# TV under raw weights
W_raw_scaled = W * scale
W_raw_norm = W_raw_scaled / W_raw_scaled.sum()
TV_raw = float(0.5 * np.abs(W_raw_norm - W).sum())
print(f'\nTV(shift)={amp["TV_vec"]:.4f}  TV(raw via scaled weights)={TV_raw:.4f}')

# Load trios
trios = np.load(ROOT / 'data/fogo_trios.npy')
T0, T1, T2 = trios[:, 0], trios[:, 1], trios[:, 2]

# Dirichlet draws (same seed as E1)
N_DRAWS = 500
KAPPA = 200
rng_w = np.random.default_rng(42)
W_DRAWS = sp_dirichlet.rvs(W * KAPPA, size=N_DRAWS, random_state=rng_w)

# Scoring matrices
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b:
        X_adj[:, j] = 1.0 - X_via[:, j]

norms_shift = 1.0 / rho_shift   # = L2(X_via cols)
norms_raw   = 1.0 / rho_raw

def top_trio(scores):
    ts = scores[T0] + scores[T1] + scores[T2]
    return int(ts.argmax())

def saw_shift(w):
    return ((X_adj / norms_shift) * w).sum(1)

def saw_raw(w):
    # Equivalent: use raw norms and rescale weights proportionally
    return ((X_adj / norms_raw) * (w * scale)).sum(1)

# Run comparison
results = []
same_20 = 0
same_total = 0
for d, w in enumerate(W_DRAWS):
    best_shift = top_trio(saw_shift(w))
    best_raw   = top_trio(saw_raw(w))
    same = (best_shift == best_raw)
    results.append({'draw': d, 'best_shift': best_shift, 'best_raw': best_raw, 'same': int(same)})
    if same:
        same_total += 1
    if d < 20 and same:
        same_20 += 1

print(f'\nControl (first 20 draws): shift==raw in {same_20}/20 draws')
print(f'Full 500 draws: shift==raw in {same_total}/500 draws')

df = pd.DataFrame(results)
out = ROOT / 'results/raw_sensitivity.csv'
df.to_csv(out, index=False)
import hashlib
sha = hashlib.sha256(out.read_bytes()).hexdigest()
print(f'Saved to {out}')
print(f'SHA-256: {sha[:16]}')
print('DONE')
