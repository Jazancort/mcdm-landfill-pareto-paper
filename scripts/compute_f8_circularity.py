"""
compute_f8_circularity.py  (F8 — circularidade do benchmark)
==============================================================
Design declarado antes de correr (PRESPEC F8):

  Questão: a fronteira Pareto é circular relativamente à normalização min-max?
  
  Teste: reconstruir a fronteira com objectivos em normalização VECTORIAL.
  Repetir as 4 células SAW × {mm, vec} × {greedy, opt}.

  Previsão (Proposição 1):
    SAW/vec/opt com objs vec  → Q2 = 100% (score e objs usam mesma norm)
    SAW/mm/opt  com objs vec  → Q2 < 100% (score e objs divergem)
  
  Se confirmado: a mensagem passa de "min-max é melhor" para
  "score e objectivos devem usar a mesma normalização" — não circular.

Parâmetros: N=500, kappa=200, seed=42, Fogo A' (389 admissíveis, k=3).
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
    load_data, impute_nan, COL, AHP_WEIGHTS, haversine_km, MIN_DIST_KM
)
from pareto_utils import build_pareto_utils

t0 = time.time()
print("Loading data...", flush=True)
df_all, par, bcs = load_data()
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
print(f"  N_via={N}, trios={n_trios:,}  t={time.time()-t0:.1f}s", flush=True)

# ── Vector-normalised partial values ────────────────────────────────────────
cost_cols = {'perm','slope','rivers','urban','aero','cult',
             'coast','protected','wells'}
X_raw = df_via[col_names].values.astype(float)

def make_vec_cols(X, col_names):
    V = np.zeros_like(X)
    for j, c in enumerate(col_names):
        col = X[:, j].copy()
        if c in cost_cols:
            col = col.max() + col.min() - col   # benefit-orient
        nrm = np.sqrt(np.sum(col**2))
        V[:, j] = col / nrm if nrm > 0 else 0.0
    return V

def make_mm_cols(X, col_names):
    M = np.zeros_like(X)
    for j, c in enumerate(col_names):
        col = X[:, j].copy()
        lo, hi = col.min(), col.max()
        if c in cost_cols:
            M[:, j] = (hi - col) / (hi - lo) if hi > lo else 0.0
        else:
            M[:, j] = (col - lo) / (hi - lo) if hi > lo else 0.0
    return M

V_vec = make_vec_cols(X_raw, col_names)   # (N x m) vector-norm benefit
V_mm  = make_mm_cols(X_raw, col_names)    # (N x m) min-max benefit

# ── build_pareto_utils with VECTOR objectives ────────────────────────────────
# build_pareto_utils(df_via, col_names, trios, eps) uses df_via columns
# and computes objectives internally. We bypass it and use a direct approach:
# inject V_vec as the partial-value matrix.
# Strategy: monkey-patch by passing a modified df_via where columns = V_vec
# Simpler: compute trio objectives directly from V_vec and use is_dominated.

# Re-use the is_dominated function from pareto_utils
compute_objs_mm, is_dominated, _ = build_pareto_utils(
    df_via, col_names, trios, eps=1e-9
)

# For vec objectives: compute manually
# f_g(T,w) = sum_{j in g} w_j * (V[a1,j] + V[a2,j] + V[a3,j])
# Groups (from fogo_constants):
# G1=cost=[0,1,2], G2=env=[3,4,5,6,7], G3=soc=[8,9,10]
OBJ_GROUPS = [[0,1,2],[3,4,5,6,7],[8,9,10]]

# ── Pre-compute trio contributions for fast objective calculation ──────────
# F_g(T,w) = sum_{j in g} w_j * col_sum[T,j]
# where col_sum[T,j] = V[T0,j]+V[T1,j]+V[T2,j]
print("Pre-computing trio column sums (vec)...", flush=True)
# CS_vec[t, j] = V[T0,j]+V[T1,j]+V[T2,j]  — (n_trios × m)
# This is a (1.9M × 11) matrix = ~170 MB float64, feasible
CS_vec = V_vec[T0] + V_vec[T1] + V_vec[T2]   # (n_trios × m)
print(f"  CS_vec shape: {CS_vec.shape}  ({CS_vec.nbytes/1e6:.0f} MB)  t={time.time()-t0:.1f}s", flush=True)

# Group masks for objective computation
G_mask = np.zeros((3, len(col_names)), dtype=float)
for gi, grp in enumerate(OBJ_GROUPS):
    G_mask[gi, grp] = 1.0

def compute_objs_vec(w):
    """Return (F1,F2,F3): vectorised over all trios."""
    # Fobj[g] = CS_vec @ (G_mask[g] * w)
    F = CS_vec @ (G_mask * w).T   # (n_trios × 3)
    return F[:, 0], F[:, 1], F[:, 2]

# Pre-compute mm column sums
CS_mm = V_mm[T0] + V_mm[T1] + V_mm[T2]   # (n_trios × m)
print(f"  CS_mm shape:  {CS_mm.shape}  t={time.time()-t0:.1f}s", flush=True)

# Fast non-dominated set using sorted sweep (same as FAinter computation)
EPS = 1e-9

def frontier_sorted(F1, F2, F3):
    idx = np.argsort(F1)[::-1]
    nd_set = []
    nd_mask = np.zeros(n_trios, dtype=bool)
    for i in idx:
        f1i, f2i, f3i = F1[i], F2[i], F3[i]
        dominated = False
        new_nd = []
        for (f1j, f2j, f3j, j) in nd_set:
            if (f1j >= f1i-EPS and f2j >= f2i-EPS and f3j >= f3i-EPS and
                    (f1j > f1i+EPS or f2j > f2i+EPS or f3j > f3i+EPS)):
                dominated = True
                new_nd.append((f1j, f2j, f3j, j))
                break
            if not (f1i >= f1j-EPS and f2i >= f2j-EPS and f3i >= f3j-EPS and
                    (f1i > f1j+EPS or f2i > f2j+EPS or f3i > f3j+EPS)):
                new_nd.append((f1j, f2j, f3j, j))
        if not dominated:
            new_nd.append((f1i, f2i, f3i, i))
            nd_mask[i] = True
        nd_set = new_nd
    return nd_mask

# ── SAW scores ───────────────────────────────────────────────────────────────
def saw_score_mm(w):
    return V_mm @ w

def saw_score_vec(w):
    return V_vec @ w

def top_trio_greedy(scores):
    order = np.argsort(scores)[::-1]
    sel = []
    for idx in order:
        if all(valid[idx, s] for s in sel):
            sel.append(idx)
        if len(sel) == 3:
            break
    if len(sel) < 3:
        return None
    sel_set = frozenset(sel)
    for i, t in enumerate(trios):
        if frozenset(t) == sel_set:
            return i
    return None

def top_trio_opt(scores):
    ts = scores[T0] + scores[T1] + scores[T2]
    return int(np.argmax(ts))

# ── Regression test: vec/opt with vec objectives must = 100% ─────────────────
print("\n=== Regression test (vec/opt with vec objs, nominal w) ===", flush=True)
F1n, F2n, F3n = compute_objs_vec(w_ahp)
nd_nom = frontier_sorted(F1n, F2n, F3n)
fr_nom = set(np.where(nd_nom)[0])
sc_vec_nom = saw_score_vec(w_ahp)
t_idx_nom = top_trio_opt(sc_vec_nom)
print(f"  |frontier| = {len(fr_nom)}, top trio in frontier: {t_idx_nom in fr_nom}", flush=True)
assert t_idx_nom in fr_nom, "REGRESSION FAIL: vec/opt/vec-objs not in frontier at nominal w — BUG"

# Also test mm/opt with mm objectives
F1n_mm, _, _ = compute_objs_mm(w_ahp)
# compute_objs_mm returns 3 objectives; use is_dominated
# shortcut: use same frontier approach but with mm objectives
V_mm_obj_F1 = np.zeros(n_trios); V_mm_obj_F2 = np.zeros(n_trios); V_mm_obj_F3 = np.zeros(n_trios)
for j in OBJ_GROUPS[0]: wj=w_ahp[j]; V_mm_obj_F1+=wj*(V_mm[T0,j]+V_mm[T1,j]+V_mm[T2,j])
for j in OBJ_GROUPS[1]: wj=w_ahp[j]; V_mm_obj_F2+=wj*(V_mm[T0,j]+V_mm[T1,j]+V_mm[T2,j])
for j in OBJ_GROUPS[2]: wj=w_ahp[j]; V_mm_obj_F3+=wj*(V_mm[T0,j]+V_mm[T1,j]+V_mm[T2,j])
nd_mm_nom = frontier_sorted(V_mm_obj_F1, V_mm_obj_F2, V_mm_obj_F3)
fr_mm_nom = set(np.where(nd_mm_nom)[0])
t_mm_nom = top_trio_opt(saw_score_mm(w_ahp))
print(f"  mm/opt/mm-objs: top in frontier: {t_mm_nom in fr_mm_nom}", flush=True)
assert t_mm_nom in fr_mm_nom, "REGRESSION FAIL: mm/opt/mm-objs not in frontier — BUG"
print("  Regression PASS", flush=True)

# ── Monte Carlo ────────────────────────────────────────────────────────────
N_DRAWS = 500; KAPPA = 200; SEED = 42
RNG = np.random.default_rng(SEED)
alpha = KAPPA * w_ahp
W_draws = sp_dirichlet.rvs(alpha, size=N_DRAWS, random_state=RNG)

cells = [("vec","optimal"), ("mm","optimal"), ("vec","greedy"), ("mm","greedy")]
rows = []

for norm_lbl, asm in cells:
    print(f"\n=== {norm_lbl}/{asm} ===", flush=True)
    nd_cnt = 0; fr_sum = 0; t_cell = time.time()

    for di, w in enumerate(W_draws):
        # Frontier: ALWAYS vec objectives
        F1, F2, F3 = compute_objs_vec(w)
        nd_mask = frontier_sorted(F1, F2, F3)
        fr = set(np.where(nd_mask)[0])
        fr_sum += len(fr)

        # Score
        sc = saw_score_vec(w) if norm_lbl == "vec" else saw_score_mm(w)

        # Assembly
        t_idx = top_trio_opt(sc) if asm == "optimal" else top_trio_greedy(sc)
        if t_idx is not None and t_idx in fr:
            nd_cnt += 1

        if di % 50 == 0:
            elapsed = time.time() - t_cell
            eta = elapsed / (di+1) * (N_DRAWS - di - 1)
            print(f"  {di}/{N_DRAWS} Q2={nd_cnt/(di+1)*100:.1f}% |fr|={len(fr)} eta={eta:.0f}s",
                  flush=True)

    Q2 = nd_cnt / N_DRAWS * 100
    SE = np.sqrt(Q2 * (100-Q2) / N_DRAWS)
    fr_mean = fr_sum / N_DRAWS
    print(f"  RESULT: Q2={Q2:.1f}% SE={SE:.2f} |fr_mean|={fr_mean:.0f}  t={time.time()-t_cell:.0f}s",
          flush=True)
    rows.append({"obj_norm":"vec", "score_norm":norm_lbl, "assembly":asm,
                 "Q2":round(Q2,2), "SE":round(SE,3), "n_frontier_mean":round(fr_mean,1),
                 "n_trios":n_trios})

out = ROOT/"results"/"f8"
out.mkdir(exist_ok=True)
df = pd.DataFrame(rows)
df.to_csv(out/"f8_circularity.csv", index=False)
print(f"\n=== F8 RESULTS ==="); print(df.to_string(index=False))
print(f"\nTotal: {time.time()-t0:.1f}s")
