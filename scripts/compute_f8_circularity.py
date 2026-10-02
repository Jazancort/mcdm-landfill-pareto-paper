"""
compute_f8_circularity.py  (F8 — circularidade do benchmark)
==============================================================
Design (PRESPEC F8):

  Questão: a fronteira Pareto é circular relativamente à normalização min-max?
  
  Teste: reconstruir a fronteira com OBJECTIVOS em normalização VECTORIAL.
  Repetir as 4 células SAW × {mm, vec} × {greedy, opt}.

  Previsão (Proposição 1):
    SAW/vec/opt com objs vec  → Q2 = 100% (score e objs mesma norm)
    SAW/mm/opt  com objs vec  → Q2 < 100% (score e objs divergem)

  Abordagem: criar df_via_vec com colunas vectorialmente normalizadas,
  passar ao build_pareto_utils. O compute_objs_f64_vec resultante usa
  _norm sobre colunas já normalizadas → objectivos consistentes com
  saw_vec = X_adj_vec @ w.

Output: results/f8/f8_circularity.csv
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

t0 = time.time()
print("Loading data...", flush=True)
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

# ── Standard (mm) utilities — used for mm cells and regression verification ──
compute_objs_mm, is_dominated_mm, _ = build_pareto_utils(
    df_via, col_names, trios, eps=1e-9
)

# ── Score matrices ────────────────────────────────────────────────────────────
# X_adj_mm: standard benefit-oriented min-max score (same as mc_2cube_fixed)
X_via_raw, benefit_flags = _build_decision_matrix(df_via)
X_adj_mm = X_via_raw.copy()
for j, b in enumerate(benefit_flags):
    if not b:
        X_adj_mm[:, j] = 1.0 - X_via_raw[:, j]
# X_adj_vec: vector-normalised benefit score (normalise X_adj_mm columns by L2)
L2_mm = np.maximum(np.sqrt((X_adj_mm**2).sum(0)), 1e-12)
X_adj_vec = X_adj_mm / L2_mm
print(f"Score matrices ready  t={time.time()-t0:.1f}s", flush=True)

# ── Vector objectives via modified df_via ─────────────────────────────────────
# Inject X_adj_vec into df_via so that build_pareto_utils uses vec columns.
# build_pareto_utils calls df_via[col_map[k]] for each criterion k.
# We replace those columns with X_adj_vec values (already benefit-oriented).
# To avoid modifying the original, create df_via_vec with replaced columns.
df_via_vec = df_via.copy()
for j, k in enumerate(col_names):
    df_col = COL[k]   # actual df column name
    df_via_vec[df_col] = X_adj_vec[:, j]   # inject vec-normalised benefit values

# build_pareto_utils with vec df: _norm over vec columns → objectives ≡ X_adj_vec @ w
# The dominance check (is_dominated) reuses the same _lookup so indices match
compute_objs_vec, is_dominated_vec, _ = build_pareto_utils(
    df_via_vec, col_names, trios, eps=1e-9
)
print(f"Vec utilities ready  t={time.time()-t0:.1f}s", flush=True)


def saw_mm(w): return X_adj_mm @ w
def saw_vec(w): return X_adj_vec @ w

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


# ── Regression tests ─────────────────────────────────────────────────────────
N_DRAWS = 500; KAPPA = 200; SEED = 42
print("\n=== Regression tests ===", flush=True)
W_check = sp_dirichlet.rvs(KAPPA * w_ahp, size=5,
                            random_state=np.random.default_rng(99))
pass_mm = 0; pass_vec = 0
for w in W_check:
    f1v, f2v, f3v = compute_objs_mm(w)
    F1m = f1v[T0]+f1v[T1]+f1v[T2]
    F2m = f2v[T0]+f2v[T1]+f2v[T2]
    F3m = f3v[T0]+f3v[T1]+f3v[T2]
    t_mm = top_opt(saw_mm(w))
    if not is_dominated_mm(t_mm, F1m, F2m, F3m): pass_mm += 1

    f1v, f2v, f3v = compute_objs_vec(w)
    F1v = f1v[T0]+f1v[T1]+f1v[T2]
    F2v = f2v[T0]+f2v[T1]+f2v[T2]
    F3v = f3v[T0]+f3v[T1]+f3v[T2]
    t_vec = top_opt(saw_vec(w))
    if not is_dominated_vec(t_vec, F1v, F2v, F3v): pass_vec += 1

print(f"  mm/opt/mm-objs: {pass_mm}/5 (expect 5)", flush=True)
print(f"  vec/opt/vec-objs: {pass_vec}/5 (expect 5 for Prop1)", flush=True)
if pass_mm < 5:
    raise AssertionError(f"mm regression failed {pass_mm}/5 — score/obj misaligned")
if pass_vec < 5:
    print(f"  WARNING: vec/opt fails {pass_vec}/5 — checking...", flush=True)
    # Debug: show top vec trio score vs dominated status
    f1v, f2v, f3v = compute_objs_vec(W_check[0])
    F1v=f1v[T0]+f1v[T1]+f1v[T2]; F2v=f2v[T0]+f2v[T1]+f2v[T2]; F3v=f3v[T0]+f3v[T1]+f3v[T2]
    t_dbg = top_opt(saw_vec(W_check[0]))
    print(f"  debug top_vec={t_dbg}, dom={is_dominated_vec(t_dbg,F1v,F2v,F3v)}", flush=True)
print("Regressions done.", flush=True)


# ── Monte Carlo ─────────────────────────────────────────────────────────────
W_draws = sp_dirichlet.rvs(KAPPA * w_ahp, size=N_DRAWS,
                            random_state=np.random.default_rng(SEED))

cells = [("vec", "optimal"), ("mm", "optimal"), ("vec", "greedy"), ("mm", "greedy")]
rows = []

for norm_lbl, asm in cells:
    print(f"\n=== {norm_lbl}/{asm} (obj=vec) ===", flush=True)
    nd_cnt = 0; t_cell = time.time()

    for di, w in enumerate(W_draws):
        # Objectives: vec normalisation
        f1v, f2v, f3v = compute_objs_vec(w)
        F1 = f1v[T0]+f1v[T1]+f1v[T2]
        F2 = f2v[T0]+f2v[T1]+f2v[T2]
        F3 = f3v[T0]+f3v[T1]+f3v[T2]

        # Score
        sc = saw_vec(w) if norm_lbl == "vec" else saw_mm(w)

        # Assembly
        t = top_opt(sc) if asm == "optimal" else top_greedy(sc)

        if t is not None and not is_dominated_vec(t, F1, F2, F3):
            nd_cnt += 1

        if di % 50 == 0:
            eta = (time.time()-t_cell) / (di+1) * (N_DRAWS-di-1)
            print(f"  {di}/{N_DRAWS} Q2={nd_cnt/(di+1)*100:.1f}% eta={eta:.0f}s",
                  flush=True)

    Q2 = nd_cnt / N_DRAWS * 100
    SE = np.sqrt(Q2 * (100 - Q2) / N_DRAWS)
    print(f"  RESULT: Q2={Q2:.1f}% SE={SE:.2f}  t={time.time()-t_cell:.0f}s",
          flush=True)
    rows.append({
        "obj_norm": "vec", "score_norm": norm_lbl, "assembly": asm,
        "Q2": round(Q2, 2), "SE": round(SE, 3), "n_trios": n_trios
    })

out = ROOT / "results" / "f8"
out.mkdir(exist_ok=True)
df = pd.DataFrame(rows)
df.to_csv(out / "f8_circularity.csv", index=False)
print(f"\n=== F8 RESULTS ===\n{df.to_string(index=False)}")
print(f"\nTotal: {time.time()-t0:.1f}s")
