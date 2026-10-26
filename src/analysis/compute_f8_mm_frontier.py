# -*- coding: utf-8 -*-
"""
compute_f8_mm_frontier.py  (F8 extension — min-max frontier cells)
==================================================================
Computes the 4 missing cells of the F8 2×2 alignment matrix:

  obj_norm=mm × score_norm={mm,vec} × assembly={optimal,greedy}

The existing compute_f8_circularity.py covers obj_norm=vec.
This script covers obj_norm=mm.

Expected results:
  mm/mm/opt  ~ 100%  (Theorem 1: score and objectives share the same normalisation)
  mm/mm/grd  ~ 86%   (matches factorial SAW/mm/greedy — same pipeline)
  mm/vec/opt ~ ?     (score=vec portfolio vs mm frontier — interesting cross-alignment)
  mm/vec/grd ~ ?     (greedy vec portfolio vs mm frontier)

Output: results/f8/f8_circularity_mm.csv
        results/f8/f8_per_draw_mm.csv

Usage:
    uv run python scripts/compute_f8_mm_frontier.py           # N=500 (full)
    N_DRAWS=20 uv run python scripts/compute_f8_mm_frontier.py # quick smoke test
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import dirichlet as sp_dirichlet

ROOT = Path(__file__).parent.parent

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, haversine_km, MIN_DIST_KM,
    _build_decision_matrix
)
from pareto_utils import build_pareto_utils

N_DRAWS = int(os.environ.get("N_DRAWS", 500))
KAPPA   = 200
SEED    = 42

t0 = time.time()
print(f"Loading data (N_DRAWS={N_DRAWS})...", flush=True)
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL['protected']] > 0].copy()
N = len(df_via)
col_names = list(AHP_WEIGHTS.keys())
w_ahp = np.array(list(AHP_WEIGHTS.values()))

print("Building trios...", flush=True)
D = haversine_km(df_via['latitude (degrees)'].values,
                 df_via['longitude (degrees)'].values)
valid = D >= MIN_DIST_KM
trios_list = [(i, j, k)
              for i in range(N) for j in range(i+1, N) if valid[i, j]
              for k in range(j+1, N) if valid[i, k] and valid[j, k]]
trios = np.array(trios_list, dtype=np.int32)
T0, T1, T2 = trios[:, 0], trios[:, 1], trios[:, 2]
n_trios = len(trios)
print(f"  trios={n_trios:,}  t={time.time()-t0:.1f}s", flush=True)

# ── Score matrices ────────────────────────────────────────────────────────────
X_via_raw, benefit_flags = _build_decision_matrix(df_via)
X_adj_mm = X_via_raw.copy()
for j, b in enumerate(benefit_flags):
    if not b:
        X_adj_mm[:, j] = 1.0 - X_via_raw[:, j]

# Vec score: use canonical scorer from scoring.py
# BUG HISTORY: earlier reimplementation set C_score_vec[:, aspect] = raw {0,1}
# (not L2-normalised), inflating aspect amplitude by ~9.7x and collapsing TV to ~0.
# Fix: import make_scorers — same path as mc_unified.py and run_e1.py.
from scoring import make_scorers
norms_via = np.array([max(float(np.sqrt((X_via_raw[:,j]**2).sum())), 1e-12)
                      for j in range(len(col_names))])
_saw_sc_fn, _ = make_scorers(X_via_raw, X_adj_mm, norms_via, benefit_flags)

# Assert canonical amplitudes match macros_amplitudes.json as sanity check
import json as _json
_amp = _json.loads((ROOT/"results/amplitudes/amplitudes.json").read_text())
for j, k in enumerate(col_names):
    expected_rho = _amp["rho_j"][k]
    got_rho = 1.0/norms_via[j]
    assert abs(got_rho - expected_rho) < 0.001, (
        f"rho mismatch for {k}: expected {expected_rho:.4f} got {got_rho:.4f}")
print("  rho_j assertion passed", flush=True)

def saw_mm(w): return X_adj_mm @ w
def saw_vec(w): return _saw_sc_fn(w, norm='vector')

def top_opt(scores):
    return trios[int(np.argmax(scores[T0] + scores[T1] + scores[T2]))]

def top_greedy(scores):
    order = np.argsort(scores)[::-1]
    sel = []
    for idx in order:
        if all(valid[idx, s] for s in sel): sel.append(idx)
        if len(sel) == 3: break
    if len(sel) < 3: return None
    sf = frozenset(sel)
    for t in trios:
        if frozenset(t) == sf: return t
    return None

# ── Min-max objective utilities ───────────────────────────────────────────────
compute_objs_mm, is_dominated_mm, _ = build_pareto_utils(
    df_via, col_names, trios, eps=1e-9
)
print(f"Min-max objective utilities ready  t={time.time()-t0:.1f}s", flush=True)

# ── Monte Carlo ───────────────────────────────────────────────────────────────
# Load canonical weights (same draws as mc_unified.py / run_e1.py / factorial)
_wmat = ROOT / "results/e1/e1_weights_k200.npy"
_W_all = np.load(_wmat)
W_draws = _W_all[:N_DRAWS]
assert W_draws.shape == (N_DRAWS, len(col_names)), (
    f"Weight matrix shape mismatch: expected ({N_DRAWS},{len(col_names)}), got {W_draws.shape}")
print(f"Loaded {N_DRAWS} weight draws from {_wmat.name}", flush=True)

cells = [("mm", "optimal"), ("mm", "greedy"), ("vec", "optimal"), ("vec", "greedy")]
rows = []
per_draw_rows = []

for score_lbl, asm in cells:
    print(f"\n=== obj=mm / score={score_lbl} / {asm} ===", flush=True)
    nd_cnt = 0; t_cell = time.time()

    for di, w in enumerate(W_draws):
        # Objectives: mm normalisation
        f1m, f2m, f3m = compute_objs_mm(w)
        F1 = f1m[T0]+f1m[T1]+f1m[T2]
        F2 = f2m[T0]+f2m[T1]+f2m[T2]
        F3 = f3m[T0]+f3m[T1]+f3m[T2]

        # Score
        sc = saw_mm(w) if score_lbl == "mm" else saw_vec(w)

        # Assembly
        t = top_opt(sc) if asm == "optimal" else top_greedy(sc)

        on_frontier = (t is not None and
                       not is_dominated_mm(t, F1, F2, F3))
        if on_frontier:
            nd_cnt += 1

        per_draw_rows.append({
            "obj_norm": "mm", "score_norm": score_lbl, "assembly": asm,
            "draw": di, "on_frontier": int(on_frontier)
        })

        if di % 50 == 0:
            elapsed = time.time()-t_cell
            eta = elapsed / (di+1) * (N_DRAWS-di-1)
            print(f"  {di}/{N_DRAWS} Q2={nd_cnt/(di+1)*100:.1f}%  eta={eta:.0f}s",
                  flush=True)

    Q2 = nd_cnt / N_DRAWS * 100
    SE = np.sqrt(Q2 * (100 - Q2) / N_DRAWS)
    print(f"  RESULT: obj=mm / score={score_lbl} / {asm}: Q2={Q2:.1f}% SE={SE:.2f}",
          flush=True)
    rows.append({
        "obj_norm": "mm", "score_norm": score_lbl, "assembly": asm,
        "Q2": round(Q2, 2), "SE": round(SE, 3), "n_trios": n_trios
    })

# ── Verify Theorem 1 for mm/mm/opt ───────────────────────────────────────────
df_pd = pd.DataFrame(per_draw_rows)
mm_mm_opt = df_pd[(df_pd["score_norm"]=="mm") & (df_pd["assembly"]=="optimal")]["on_frontier"]
n_fail = int((mm_mm_opt == 0).sum())
if n_fail > 0:
    print(f"\n  WARNING: Theorem 1 mm/mm/opt: {n_fail}/{len(mm_mm_opt)} draws failed!")
else:
    print(f"\n  Theorem 1 mm/mm/opt: {len(mm_mm_opt)}/{len(mm_mm_opt)} draws on frontier")

# ── Write output ──────────────────────────────────────────────────────────────
out = ROOT / "results" / "f8"
out.mkdir(exist_ok=True)

df = pd.DataFrame(rows)
print(f"\n=== F8 mm-frontier RESULTS ===\n{df.to_string(index=False)}")

df.to_csv(out / "f8_circularity_mm.csv", index=False)
df_pd.to_csv(out / "f8_per_draw_mm.csv", index=False)
print(f"\nWritten: {out / 'f8_circularity_mm.csv'}")
print(f"Written: {out / 'f8_per_draw_mm.csv'}")
print(f"Total: {time.time()-t0:.1f}s")
