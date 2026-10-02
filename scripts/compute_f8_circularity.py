"""
compute_f8_circularity.py  (F8 — circularidade do benchmark)
==============================================================
Design (PRESPEC F8, declarado antes de correr):

  Questão: a fronteira Pareto é circular relativamente à normalização min-max?
  
  Teste: reconstruir a fronteira com OBJECTIVOS em normalização VECTORIAL.
  Repetir as 4 células SAW × {mm, vec} × {greedy, opt}.

  Previsão (Proposição 1):
    SAW/vec/opt com objs vec  → Q2 = 100% (score e objs usam mesma norm)
    SAW/mm/opt  com objs vec  → Q2 < 100% (score e objs divergem)
  
  Confirmação: se vec/opt=100% e mm/opt<100%, a mensagem passa de
  "min-max é melhor" para "score deve coincidir com objs" — não circular.

Parâmetros: N=500, kappa=200, seed=42, Fogo A' (389 sites, k=3).
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
    F1_CRIT, F2_CRIT, F3_CRIT, COL as COL_MAP, INV, COST, _norm,
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
print(f"  N_via={N}  t={time.time()-t0:.1f}s", flush=True)

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

# ── Pareto utilities (uses compute_objs_f64 with mm objectives) ─────────────
# is_dominated is the shared dominance check; we reuse it
compute_objs_mm, is_dominated, _ = build_pareto_utils(
    df_via, col_names, trios, eps=1e-9
)

# ── Score matrices (same as mc_2cube_fixed.py) ──────────────────────────────
# X_adj_mm: benefit-oriented min-max score matrix
X_via_raw, benefit_flags = _build_decision_matrix(df_via)
X_adj_mm = X_via_raw.copy()
for j, b in enumerate(benefit_flags):
    if not b:
        X_adj_mm[:, j] = 1.0 - X_via_raw[:, j]
# X_adj_vec: vector score using same base as objectives (C_obj_mm)
# For Prop1: score and objectives must use same normalised values
# C_obj_mm has cost cols = _norm (small=good); for score we need benefit-oriented
# Score SAW maximises sum, so we need high score = good site
# For cost cols (small=good in C_obj_mm): score_cost = 1 - C_obj_mm (large=good)
# But that's X_adj_mm again... the issue is that C_obj_mm and X_adj_mm differ for cost cols.
# The correct Prop1 setup: objectives F_g(T) = sum_j w_j * phi_j(a) where phi_j in [0,1] benefit
# Score = sum_j w_j * phi_j(a) where phi_j = same benefit values
# So score_mm uses X_adj_mm, objectives use pareto_utils which uses _norm
# Prop1 holds because pareto_utils objectives are CONSISTENT with X_adj_mm score
# Verification: mm/opt passes 5/5 above.
#
# For vec: we need X_adj_vec_score = X_adj_mm / L2(X_adj_mm columns)
# and C_obj_vec = X_adj_mm / L2(X_adj_mm columns) (same thing)
# Then F_g_vec(T) = sum_{j in g} w_j * X_adj_vec[T, j]  (same as score)
X_adj_vec = X_adj_mm / np.maximum(np.sqrt((X_adj_mm**2).sum(0)), 1e-12)
print(f"Score matrices built  t={time.time()-t0:.1f}s", flush=True)

# ── Objective matrix for VECTOR normalisation ────────────────────────────────
# For F8: objectives built on vector-normalised partial values
# Uses same encoding as pareto_utils._norm (so sign convention matches is_dominated)
C_obj_mm = np.zeros((N, len(col_names)))
for j, k in enumerate(col_names):
    x = df_via[COL_MAP[k]].values.astype(float)
    if k == "aspect":   c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
    elif k in INV:      c = 1.0 - _norm(x, x)
    elif k in COST:     c = _norm(x, x)
    else:               c = _norm(x, x)
    C_obj_mm[:, j] = c

# Vector version: normalise X_adj_mm columns by their L2 norm
# This is consistent with X_adj_vec score above
C_obj_vec = X_adj_vec.copy()   # same matrix — score and objectives aligned

# Group indices for objectives
G_idx = [
    [col_names.index(c) for c in F1_CRIT],
    [col_names.index(c) for c in F2_CRIT],
    [col_names.index(c) for c in F3_CRIT],
]

# Pre-compute trio sums for vector objectives (~170MB)
print("Pre-computing CS_obj_vec...", flush=True)
CS_obj_vec = C_obj_vec[T0] + C_obj_vec[T1] + C_obj_vec[T2]
print(f"  {CS_obj_vec.nbytes/1e6:.0f}MB  t={time.time()-t0:.1f}s", flush=True)


def compute_f_vec(w):
    """F1,F2,F3 with vector-normalised objectives."""
    F = []
    for grp in G_idx:
        F.append((CS_obj_vec[:, grp] * w[grp]).sum(1))
    return F[0], F[1], F[2]


def saw_mm(w):
    return X_adj_mm @ w

def saw_vec(w):
    return X_adj_vec @ w

def top_opt(scores):
    """Return trio array [i,j,k] maximising sum of scores."""
    return trios[int(np.argmax(scores[T0] + scores[T1] + scores[T2]))]

def top_greedy(scores):
    order = np.argsort(scores)[::-1]
    sel = []
    for idx in order:
        if all(valid[idx, s] for s in sel):
            sel.append(idx)
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
    # mm score vs mm objectives (Prop1: must be True = not dominated)
    f1v, f2v, f3v = compute_objs_mm(w)
    F1m = f1v[T0]+f1v[T1]+f1v[T2]; F2m=f2v[T0]+f2v[T1]+f2v[T2]; F3m=f3v[T0]+f3v[T1]+f3v[T2]
    t_mm = top_opt(saw_mm(w))
    if not is_dominated(t_mm, F1m, F2m, F3m): pass_mm += 1

    # vec score vs vec objectives
    F1v, F2v, F3v = compute_f_vec(w)
    t_vec = top_opt(saw_vec(w))
    if not is_dominated(t_vec, F1v, F2v, F3v): pass_vec += 1

print(f"  mm/opt not dominated: {pass_mm}/5 (expect 5 for Prop1)", flush=True)
print(f"  vec/opt not dominated: {pass_vec}/5 (expect 5 for Prop1)", flush=True)
if pass_mm < 5:
    print("  WARNING: mm/opt fails Prop1 regression. Check score/obj alignment.", flush=True)
if pass_vec < 5:
    print("  WARNING: vec/opt fails Prop1 regression. Check score/obj alignment.", flush=True)


# ── Monte Carlo ─────────────────────────────────────────────────────────────
W_draws = sp_dirichlet.rvs(KAPPA * w_ahp, size=N_DRAWS,
                            random_state=np.random.default_rng(SEED))

cells = [("vec", "optimal"), ("mm", "optimal"), ("vec", "greedy"), ("mm", "greedy")]
rows = []

for norm_lbl, asm in cells:
    print(f"\n=== {norm_lbl}/{asm} (obj=vec) ===", flush=True)
    nd_cnt = 0; t_cell = time.time()

    for di, w in enumerate(W_draws):
        # Objectives: always VECTOR normalisation
        F1, F2, F3 = compute_f_vec(w)

        # Score
        sc = saw_vec(w) if norm_lbl == "vec" else saw_mm(w)

        # Assembly
        t = top_opt(sc) if asm == "optimal" else top_greedy(sc)

        if t is not None and not is_dominated(t, F1, F2, F3):
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
print(f"\nTotal: {time.time()-t0:.1f}s  Saved: {out/'f8_circularity.csv'}")
