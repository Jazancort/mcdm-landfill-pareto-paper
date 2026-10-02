"""
compute_f8_circularity.py  (F8 — circularidade do benchmark)
==============================================================
Design declarado antes de correr (PRESPEC F8):

  Questão: a fronteira Pareto é circular relativamente à normalização min-max?
  
  Teste: reconstruir a fronteira com objectivos em normalização VECTORIAL.
  Repetir as 4 células SAW × {mm, vec} × {greedy, opt}.

  Previsão (Proposição 1):
    SAW/vec/opt com objs vec  → Q2 = 100% (score e objs mesma norm)
    SAW/mm/opt  com objs vec  → Q2 < 100% (score e objs divergem)

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
    F1_CRIT, F2_CRIT, F3_CRIT, COL as COL_MAP, INV, COST, _norm
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
trios_list = [(i,j,k) for i in range(N) for j in range(i+1,N) if valid[i,j]
              for k in range(j+1,N) if valid[i,k] and valid[j,k]]
trios = np.array(trios_list, dtype=np.int32)
T0, T1, T2 = trios[:,0], trios[:,1], trios[:,2]
n_trios = len(trios)
print(f"  trios={n_trios:,}  t={time.time()-t0:.1f}s", flush=True)

# ── build_pareto_utils (we only use is_dominated from it) ───────────────────
_, is_dominated, _ = build_pareto_utils(df_via, col_names, trios, eps=1e-9)

# ── Vector-normalised partial values ────────────────────────────────────────
# Use same column-mapping as pareto_utils (COL_MAP: short→df column name)
# and same benefit-orientation (INV = invert-distance cols, COST = cost cols)
def make_norm_cols(df_via, col_names, norm="vec"):
    """Return (N×m) matrix of normalised benefit-oriented partial values."""
    out = np.zeros((len(df_via), len(col_names)), dtype=np.float64)
    for j, k in enumerate(col_names):
        x = df_via[COL_MAP[k]].values.astype(np.float64)
        if k == "aspect":
            c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
        elif k in INV:
            c = 1.0 - _norm(x, x)   # invert: farther=better, normalise over df_via
        elif k in COST:
            c = _norm(x, x)
        else:
            c = _norm(x, x)
        # c is now benefit-oriented, min-max normalised
        # For vec: re-normalise by L2 norm of the benefit column
        if norm == "vec":
            nrm = np.sqrt(np.sum(c**2))
            c = c / nrm if nrm > 0 else c
        out[:, j] = c
    return out

print("Computing normalised matrices...", flush=True)
C_mm  = make_norm_cols(df_via, col_names, norm="mm")   # min-max benefit
C_vec = make_norm_cols(df_via, col_names, norm="vec")  # vector benefit
print(f"  done  t={time.time()-t0:.1f}s", flush=True)

# Group masks
groups = [F1_CRIT, F2_CRIT, F3_CRIT]
G_idx = [[col_names.index(c) for c in g] for g in groups]

# Pre-compute trio column sums (n_trios × m)  ~170 MB
print("Pre-computing CS_vec and CS_mm...", flush=True)
CS_vec = C_vec[T0] + C_vec[T1] + C_vec[T2]
CS_mm  = C_mm[T0]  + C_mm[T1]  + C_mm[T2]
print(f"  CS_vec {CS_vec.nbytes/1e6:.0f}MB  t={time.time()-t0:.1f}s", flush=True)

def objs_from_CS(CS, w, G_idx):
    """Compute (F1,F2,F3) from trio column sums and weight vector."""
    F = []
    for grp in G_idx:
        F.append((CS[:, grp] * w[grp]).sum(1))
    return F[0], F[1], F[2]

# SAW scores (per site)
def saw_mm(w):  return C_mm  @ w
def saw_vec(w): return C_vec @ w

def top_opt(scores): return int(np.argmax(scores[T0]+scores[T1]+scores[T2]))

def top_greedy(scores):
    order = np.argsort(scores)[::-1]
    sel = []
    for idx in order:
        if all(valid[idx, s] for s in sel):
            sel.append(idx)
        if len(sel) == 3: break
    if len(sel) < 3: return None
    sf = frozenset(sel)
    for i, t in enumerate(trios):
        if frozenset(t) == sf: return i
    return None

# ── Regression test ─────────────────────────────────────────────────────────
print("\n=== Regression test (vec/opt, vec objs, nominal w) ===", flush=True)
F1n, F2n, F3n = objs_from_CS(CS_vec, w_ahp, G_idx)
t_nom = top_opt(saw_vec(w_ahp))
print(f"  is_dominated(top_trio, F_vec)={is_dominated(trios[t_nom], F1n, F2n, F3n)}", flush=True)
assert not is_dominated(trios[t_nom], F1n, F2n, F3n), \
    "REGRESSION FAIL: vec/opt not on vec frontier at nominal w — BUG"
print("  PASS", flush=True)

# ── Monte Carlo ─────────────────────────────────────────────────────────────
N_DRAWS=500; KAPPA=200; SEED=42
W_draws = sp_dirichlet.rvs(KAPPA*w_ahp, size=N_DRAWS,
                            random_state=np.random.default_rng(SEED))

cells = [("vec","optimal"),("mm","optimal"),("vec","greedy"),("mm","greedy")]
rows = []

for norm_lbl, asm in cells:
    print(f"\n=== {norm_lbl}/{asm} ===", flush=True)
    nd_cnt = 0; t_cell = time.time()
    for di, w in enumerate(W_draws):
        F1, F2, F3 = objs_from_CS(CS_vec, w, G_idx)  # vec objectives always
        sc = saw_vec(w) if norm_lbl=="vec" else saw_mm(w)
        t_idx = top_opt(sc) if asm=="optimal" else top_greedy(sc)
        if t_idx is not None and not is_dominated(trios[t_idx], F1, F2, F3):
            nd_cnt += 1
        if di % 50 == 0:
            eta = (time.time()-t_cell)/(di+1)*(N_DRAWS-di-1)
            print(f"  {di}/{N_DRAWS} Q2={nd_cnt/(di+1)*100:.1f}% eta={eta:.0f}s", flush=True)
    Q2 = nd_cnt/N_DRAWS*100
    SE = np.sqrt(Q2*(100-Q2)/N_DRAWS)
    print(f"  RESULT: Q2={Q2:.1f}% SE={SE:.2f}  t={time.time()-t_cell:.0f}s", flush=True)
    rows.append({"obj_norm":"vec","score_norm":norm_lbl,"assembly":asm,
                 "Q2":round(Q2,2),"SE":round(SE,3),"n_trios":n_trios})

out = ROOT/"results"/"f8"; out.mkdir(exist_ok=True)
df = pd.DataFrame(rows)
df.to_csv(out/"f8_circularity.csv", index=False)
print(f"\n=== F8 RESULTS ===\n{df.to_string(index=False)}")
print(f"\nTotal: {time.time()-t0:.1f}s  Saved: {out/'f8_circularity.csv'}")
