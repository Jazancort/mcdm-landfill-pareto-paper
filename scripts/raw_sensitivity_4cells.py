# -*- coding: utf-8 -*-
"""
raw_sensitivity_4cells.py
=========================
Compare vec-normalised shift vs raw across 4 cells:
  SAW  × {greedy, optimal}   -- trivially 500/500 (shown analytically below)
  TOPSIS × {greedy, optimal} -- informative test

"Shift" = manuscript normalisation: x_j^vec = x_j^mm / L2(x_j^mm)
"Raw"   = textbook form:            x_j^vec = x_j^mm / (L2(x_j^raw) / range(x_j^raw))
          i.e., same X_via values but norms from the original unshifted data.

For criteria with min_raw = 0:  shift == raw (L2 is scale-invariant up to range).
For criteria with min_raw > 0 (slope, coast, wells, aero):
    L2(x_raw)/range != L2(x_mm), hence norms differ.

Analytical note (SAW):
  saw_raw(w) = (X_adj / norms_raw) * (w * scale)
             = X_adj * scale / norms_raw * w
             = X_adj * (norms_raw/norms_shift) / norms_raw * w
             = X_adj / norms_shift * w
             = saw_shift(w)
  So SAW/vec/shift == SAW/vec/raw for ANY weight vector -> 500/500 trivially.

Run:
    uv run python scripts/raw_sensitivity_4cells.py

Output:
    results/raw_sensitivity_4cells.csv
"""
import sys, os, time, hashlib, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import dirichlet as sp_dirichlet

ROOT = Path(__file__).parent.parent

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, haversine_km, MIN_DIST_KM,
    _build_decision_matrix,
)

t0 = time.time()
print("Loading data...", flush=True)
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL['protected']] > 0].copy()
N = len(df_via); assert N == 389
cols = list(AHP_WEIGHTS.keys())
W = np.array(list(AHP_WEIGHTS.values())); W /= W.sum()

X_via, benefit = _build_decision_matrix(df_via)  # min-max normalised, (N, M)
benefit = np.array(benefit)

# Distance matrix for greedy
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
valid = D_via >= MIN_DIST_KM

# Trios
trios = np.load(ROOT / 'data' / 'fogo_trios.npy')
assert len(trios) == 1944653
T0, T1, T2 = trios[:, 0], trios[:, 1], trios[:, 2]

# Pre-build lookup: frozenset -> trio_index  (makes greedy O(1) instead of O(T))
print("Building trio lookup dict...", flush=True)
trio_lookup = {frozenset(t): i for i, t in enumerate(trios)}
print(f"Data ready  t={time.time()-t0:.1f}s", flush=True)

# ── norms_shift: from amplitudes.json (manuscript) ──────────────────────────
amp = json.loads((ROOT / 'results' / 'amplitudes' / 'amplitudes.json').read_text())
rho_shift = np.array([amp['rho_j'][k] for k in cols])
norms_shift = 1.0 / np.maximum(rho_shift, 1e-12)   # L2(x_mm[:,j])

# ── norms_raw: from raw criterion data ──────────────────────────────────────
rho_raw = np.zeros(len(cols))
for j, k in enumerate(cols):
    if k == 'aspect':
        x = X_via[:, j].astype(float)
    else:
        x = df_via[COL[k]].values.astype(float)
    rng = float(x.max() - x.min())
    nrm = float(np.sqrt((x**2).sum()))
    rho_raw[j] = rng / nrm if nrm > 1e-12 else 0.0
norms_raw = 1.0 / np.maximum(rho_raw, 1e-12)

scale = rho_shift / np.maximum(rho_raw, 1e-12)
print("Scale factors (rho_shift/rho_raw) for criteria with |scale-1| > 0.001:")
for j, k in enumerate(cols):
    if abs(scale[j] - 1) > 0.001:
        print(f"  {k}: rho_raw={rho_raw[j]:.6f}  rho_shift={rho_shift[j]:.6f}  scale={scale[j]:.4f}")

# Analytical check: saw_raw == saw_shift
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b:
        X_adj[:, j] = 1.0 - X_via[:, j]

def saw_shift_fn(w):
    return (X_adj / norms_shift * w).sum(1)

def saw_raw_fn(w):
    return (X_adj / norms_raw * (w * scale)).sum(1)

w_test = W.copy()
diff_saw = np.max(np.abs(saw_shift_fn(w_test) - saw_raw_fn(w_test)))
print(f"\nAnalytical check SAW: max|saw_shift - saw_raw| = {diff_saw:.2e}")
assert diff_saw < 1e-10, "SAW algebraic identity broken!"
print("SAW identity confirmed: shift == raw trivially (re-weighting equivalence).")

# ── TOPSIS scoring ───────────────────────────────────────────────────────────
def topsis_sc_fn(w, norms):
    """TOPSIS with specified column norms."""
    Xb  = X_via / norms
    V   = Xb * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp  = np.sqrt(((V - PIS)**2).sum(1))
    dn  = np.sqrt(((V - NIS)**2).sum(1))
    return np.where(dp + dn == 0, 0.5, dn / (dp + dn))

def topsis_shift_fn(w): return topsis_sc_fn(w, norms_shift)
def topsis_raw_fn(w):   return topsis_sc_fn(w, norms_raw)

# ── Assembly functions ───────────────────────────────────────────────────────
def top_opt(scores):
    return int((scores[T0] + scores[T1] + scores[T2]).argmax())

def top_greedy(scores):
    order = np.argsort(scores)[::-1]
    sel = []
    for idx in order:
        if all(valid[idx, s] for s in sel):
            sel.append(idx)
        if len(sel) == 3:
            break
    if len(sel) < 3:
        return None
    return trio_lookup.get(frozenset(sel))  # O(1) lookup

# ── Monte Carlo ──────────────────────────────────────────────────────────────
N_DRAWS = 500; KAPPA = 200; SEED = 42
W_DRAWS = sp_dirichlet.rvs(W * KAPPA, size=N_DRAWS,
                            random_state=np.random.default_rng(SEED))

CELLS = [
    ("SAW",    "optimal", saw_shift_fn,    saw_raw_fn),
    ("SAW",    "greedy",  saw_shift_fn,    saw_raw_fn),
    ("TOPSIS", "optimal", topsis_shift_fn, topsis_raw_fn),
    ("TOPSIS", "greedy",  topsis_shift_fn, topsis_raw_fn),
]

print(f"\nRunning {N_DRAWS} draws × {len(CELLS)} cells...", flush=True)

records = []
t_mc = time.time()
for d, w in enumerate(W_DRAWS):
    row = {'draw': d}
    for scorer, asm, fn_shift, fn_raw in CELLS:
        sc_s = fn_shift(w)
        sc_r = fn_raw(w)
        if asm == "optimal":
            idx_s = top_opt(sc_s)
            idx_r = top_opt(sc_r)
        else:
            idx_s = top_greedy(sc_s)
            idx_r = top_greedy(sc_r)
        same = int(idx_s == idx_r) if (idx_s is not None and idx_r is not None) else 0
        key = f"{scorer}_{asm}"
        row[f"{key}_shift_idx"] = idx_s
        row[f"{key}_raw_idx"]   = idx_r
        row[f"{key}_same"]      = same
    records.append(row)

    if (d + 1) % 50 == 0:
        elapsed = time.time() - t_mc
        eta = elapsed / (d + 1) * (N_DRAWS - d - 1)
        print(f"  [{d+1}/{N_DRAWS}]  "
              f"T_opt_same={sum(r['TOPSIS_optimal_same'] for r in records)}/{d+1}  "
              f"T_grd_same={sum(r['TOPSIS_greedy_same'] for r in records)}/{d+1}  "
              f"eta={eta:.0f}s", flush=True)

df = pd.DataFrame(records)
out = ROOT / 'results' / 'raw_sensitivity_4cells.csv'
df.to_csv(out, index=False)
sha = hashlib.sha256(out.read_bytes()).hexdigest()

print(f"\n{'='*60}")
print("RAW SENSITIVITY 4-CELL RESULTS")
print(f"{'='*60}")
for scorer, asm, _, _ in CELLS:
    key = f"{scorer}_{asm}"
    n_same = int(df[f"{key}_same"].sum())
    trivial = " (trivial: algebraic identity)" if scorer == "SAW" else ""
    print(f"  {scorer}/{asm:7s} shift==raw: {n_same}/{N_DRAWS}{trivial}")
print()
print(f"Saved: {out}")
print(f"SHA-256: {sha}")
print(f"Total elapsed: {(time.time()-t0)/60:.1f} min")
print("DONE")
