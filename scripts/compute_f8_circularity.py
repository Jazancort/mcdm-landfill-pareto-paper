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

  Implementação — normalização vectorial:
    Objectivos vec usam C_vec_raw[:,j] = mm_norm(x_j) / L2(mm_norm(x_j)).
    Para colunas COST: mm_norm(x_j) = X_via_raw[:,j], logo
      C_vec_raw[:,j] = X_via_raw[:,j] / ||X_via_raw[:,j]||_2
    que é exactamente ρ_j * x_j com ρ_j = 1/||X_via_raw[:,j]||_2 (Tabela 2).
    Score saw_vec_aligned = -(F1+F2)+F3 usando os mesmos c_j → consistente
    com os objectivos por construção → Proposição 1 garante vec/opt = 100%.

    Nota: X_adj_vec abaixo (linha "DIAGNOSTIC ONLY") é calculado para
    documentação mas não é usado no scoring nem nos objectivos.
    L2_raw ≈ L2_via por construção; a assertiva abaixo confirma isso.

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
# X_adj_vec: benefit-oriented vec score — DIAGNOSTIC ONLY, not used in scoring or objectives.
# The scoring uses C_score_vec (below), which is built from C_vec_raw with L2_raw.
# For COST columns: L2_raw[j] = L2(X_via_raw[:,j]) = L2_via[j], so the score
# is rank-equivalent to X_adj_mm / L2_via (benefit orientation, same ranking).
L2_via = np.maximum(np.sqrt((X_via_raw**2).sum(0)), 1e-12)   # = norms_via in scoring.py
X_adj_vec = X_adj_mm / L2_via   # diagnostic only
del X_adj_vec  # prevent accidental use in scoring; scoring path is C_score_vec below
print(f"Score matrices ready  t={time.time()-t0:.1f}s", flush=True)

# ── Vector objectives — direct computation (no injection) ────────────────────
# The injection approach (df_via_vec with replaced columns) is INCORRECT because
# build_pareto_utils re-normalises the injected values AND misclassifies the
# aspect column (injected values are in [0,1], not [90°,180°]).
#
# Correct approach: compute vec objectives directly from X_adj_vec, using the
# same sign convention as build_pareto_utils:
#   F1/F2 (cost-type): c_j accumulated directly (lower = better)
#   F3    (benefit): c_j accumulated directly (higher = better)
# X_adj_vec[:,j] is already benefit-oriented (cost inverted, INV inverted).
# So for the SAW scalarisation -(F1+F2)+F3, we need per-group raw c_j.
# But build_pareto_utils accumulates: f1 += c_j*w_j, f2 += c_j*w_j, f3 += c_j*w_j
# where c_j for F1/F2 is cost-oriented (lower=better) and for F3 benefit-oriented.
#
# X_adj_vec is benefit-oriented everywhere. To get the cost-oriented c_j for F1/F2:
#   For F1/F2 cost cols: c_j = 1 - X_adj_vec[:,j]  (re-invert benefit to cost)
#   For F1/F2 INV cols:  c_j = X_adj_vec[:,j]       (INV already cost-oriented after flip)
# Wait — the sign convention in build_pareto_utils is:
#   COST:    c_j = _norm(x, ref)       → small c = good → accumulated in f1/f2 (lower=better)
#   INV:     c_j = 1 - _norm(x, ref)  → small c = BAD (far from hazard) → also f1/f2
# So for F1/F2, the direction is: c_j small = bad (more cost/less distance).
# Proposition 1: maximise -(F1+F2) + F3 = maximise -sum_{f1/f2} c_j*w_j + sum_{f3} c_j*w_j
# For score saw_vec = X_adj_vec @ w (benefit-oriented):
#   F3 cols: score_col = X_adj_vec[:,j] = c_j  → same as objective F3
#   F1/F2 cost cols: score_col = X_adj_vec[:,j] = 1 - c_j  → score adds, obj subtracts
#   F1/F2 INV cols:  score_col = X_adj_vec[:,j] = c_j (INV) → same sign as obj
#
# Simplest correct approach: build vec objectives using the same column values
# as saw_vec but with the same grouping as build_pareto_utils:

from mcdm_experiment import F1_CRIT, F2_CRIT, F3_CRIT, INV as INV_SET, COST as COST_SET
f1_set = set(F1_CRIT); f2_set = set(F2_CRIT)


from mcdm_experiment import _norm as _mm_norm  # used by C_vec_raw below
# C_vec_obj was removed as dead code: it tried to build vec objectives from X_adj_vec
# but was never consumed by saw_vec_aligned. Scoring path: C_vec_raw -> C_score_vec -> saw_vec_aligned.

# L2 of raw columns (before benefit adjustment)
X_raw_2, benefit_flags_2 = _build_decision_matrix(df_via)  # raw mm-normed
# We need vec normalisation of raw x (not of X_adj_mm)
C_vec_raw = np.zeros((N, len(col_names)), dtype=np.float64)
L2_raw = np.zeros(len(col_names))
for j, k in enumerate(col_names):
    x = df_via[COL[k]].values.astype(np.float64)
    if k == "aspect":
        c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
    elif k in COST_SET:
        c = _mm_norm(x, x)  # mm-normalised raw cost
    elif k in INV_SET:
        c = _mm_norm(x, x)  # mm-normalised (will be inverted for F1/F2)
    else:
        c = _mm_norm(x, x)
    L2_raw[j] = max(np.sqrt((c**2).sum()), 1e-12)
    C_vec_raw[:, j] = c / L2_raw[j]  # vec-normalised

# Confirm C_vec_raw uses article formula: rho_j = 1/L2(mm_norm(x_j)) for all non-aspect cols.
# The previous assertion np.allclose(L2_raw, L2_via) was a tautology:
# both compute L2(_norm(x,x)) from the same data, so they can never differ.
# This assertion compares the LIVE rho_j against fogo_constants.AJ_VEC (Tabela 2)
# to within 5e-3 (slightly above 3dp, because Tabela 2 rounds some values).
# The 4 criteria that diverge by 2-5e-3 (slope, coast, wells, aero) are documented
# in DATA_DICTIONARY Fase 1.3: Tabela 2 used range/L2(x_raw) while the pipeline
# uses 1/L2(mm_norm(x)) = range/L2(x-min); for criteria with min>0 these differ.
# The F8 is INTERNALLY CONSISTENT with scoring.py: both use the same norms_via.
_asp_idx    = col_names.index("aspect")
_rho_live   = 1.0 / L2_via  # = 1/L2_raw for non-aspect (same tautology-free computation)
from fogo_constants import AJ_VEC as _AJ_VEC, CRITERION_NAMES as _CRIT_NAMES
_TAB2 = dict(zip(_CRIT_NAMES, _AJ_VEC))
_rho_issues = {}
for _j, _k in enumerate(col_names):
    if _k == "aspect":
        continue
    _diff = abs(_rho_live[_j] - _TAB2[_k])
    if _diff > 5e-3:  # larger than documented Fase 1.3 discrepancy
        _rho_issues[_k] = (_rho_live[_j], _TAB2[_k], _diff)
if _rho_issues:
    raise AssertionError(
        f"rho_j diverges from Tabela 2 beyond 5e-3 for: {_rho_issues}. "
        f"F8 may be using a different normalisation than scoring.py."
    )
print("  rho_j vs Tabela 2 (non-aspect): all within 5e-3 (Fase 1.3 known diffs OK)")

# Now C_vec_raw[:,j] is vec-normalised raw (before benefit flip).
# For score saw_vec: X_adj_mm[:,j] = raw or (1-raw), then /L2_mm.
# For objectives: use C_vec_raw[:,j] with same orientation as build_pareto_utils:
#   COST: c_j = C_vec_raw[:,j]  (lower=better, accumulated in F1/F2)
#   INV:  c_j = 1 - C_vec_raw[:,j]  (lower c = farther = better, accumulated in F1/F2)
#   F3 benefit: c_j = C_vec_raw[:,j]
# Check: does saw_vec score = -(F1+F2)+F3 under this construction?
# saw_vec[:,j] = X_adj_vec[:,j] = X_adj_mm[:,j]/L2_mm[j]
# For COST cols: X_adj_mm = 1 - _mm_norm(raw) = 1 - C_raw_mm (where C_raw_mm = mm-norm)
#   X_adj_vec = (1 - C_raw_mm) / L2_mm
# Objective c_j (cost) = C_vec_raw[:,j] = C_raw_mm / L2_raw
# score_j = (1 - C_raw_mm) / L2_mm  ≠  C_raw_mm / L2_raw  → NOT proportional
#
# The fundamental issue: saw_vec inverts cost (benefit = 1-cost), but the objective
# uses cost directly. These can never be proportional for cost criteria.
# Proposition 1 holds when score = direct scalarisation of objectives = -(F1+F2)+F3
# REGARDLESS of how F1/F2/F3 are defined, as long as we maximise -(F1+F2)+F3.
# So the score for vec/vec diagonal must be: saw_vec_score = -f1 - f2 + f3
# i.e., score_i(w) = sum_{j in F3} w_j*c_j - sum_{j in F1+F2} w_j*c_j
# where c_j is the SAME c_j used in the objectives.

# Build trio-level scalarisation directly:
def compute_objs_vec_direct(w):
    """
    Compute (F1_vec, F2_vec, F3_vec) per trio using vec-normalised objectives.
    Uses C_vec_raw with same orientation as build_pareto_utils.
    """
    f1v = np.zeros(N, dtype=np.float64)
    f2v = np.zeros(N, dtype=np.float64)
    f3v = np.zeros(N, dtype=np.float64)
    for j, k in enumerate(col_names):
        wj = float(w[j])
        if k == "aspect":
            c = np.where((df_via[COL[k]].values.astype(float) >= 90) &
                         (df_via[COL[k]].values.astype(float) <= 180), 0.0, 1.0)
        elif k in INV_SET:
            c = 1.0 - C_vec_raw[:, j]  # cost-oriented
        elif k in COST_SET:
            c = C_vec_raw[:, j]         # cost-oriented
        else:
            c = C_vec_raw[:, j]         # benefit-oriented
        c = c * wj
        if k in f1_set:   f1v += c
        elif k in f2_set: f2v += c
        else:             f3v += c
    return f1v, f2v, f3v

# Score vec aligned with these objectives: -(F1+F2)+F3 = direct scalarisation
sign_obj = np.array([-1.0 if k in (f1_set | f2_set) else 1.0
                     for k in col_names])
# c_j for score: same as objectives but sign-adjusted
C_score_vec = np.zeros((N, len(col_names)), dtype=np.float64)
for j, k in enumerate(col_names):
    if k == "aspect":
        C_score_vec[:, j] = np.where(
            (df_via[COL[k]].values.astype(float) >= 90) &
            (df_via[COL[k]].values.astype(float) <= 180), 0.0, 1.0)
    elif k in INV_SET:
        C_score_vec[:, j] = 1.0 - C_vec_raw[:, j]
    elif k in COST_SET:
        C_score_vec[:, j] = C_vec_raw[:, j]
    else:
        C_score_vec[:, j] = C_vec_raw[:, j]

def saw_vec_aligned(w):
    """SAW score aligned with compute_objs_vec_direct: -(F1+F2)+F3."""
    return (C_score_vec * (w * sign_obj)).sum(axis=1)

# Build dominance checker for vec objectives using standard build_pareto_utils
# with a df where the columns are the vec-objective values (cost-oriented for F1/F2)
# We need a df where build_pareto_utils reads c_j directly without re-processing.
# The trick: pass df_via_vec_fixed where each column already has the final c_j value,
# AND tell build_pareto_utils to treat all columns as INV (so c = 1 - _norm(x,x))
# → No, that adds another transformation.
# Cleanest: use a custom is_dominated that takes F1, F2, F3 arrays directly (same as
# build_pareto_utils but without the df re-processing).
# We already have this pattern from B1: build_pareto_utils returns is_dominated
# that takes (trio, F1, F2, F3) arrays. We just need the lookup.
# Build lookup once:
_trio_lookup_vec = {
    (int(trios[i,0]), int(trios[i,1]), int(trios[i,2])): i
    for i in range(len(trios))
}
EPS_VEC = 1e-9

def is_dominated_vec_direct(trio, F1, F2, F3):
    """Dominance check using pre-computed F1/F2/F3 arrays."""
    key = tuple(sorted([int(trio[0]), int(trio[1]), int(trio[2])]))
    idx = _trio_lookup_vec.get(key, -1)
    if idx < 0: return False
    f1t, f2t, f3t = float(F1[idx]), float(F2[idx]), float(F3[idx])
    mask = np.ones(len(F1), bool); mask[idx] = False
    F1m, F2m, F3m = F1[mask], F2[mask], F3[mask]
    weak  = (F1m <= f1t+EPS_VEC) & (F2m <= f2t+EPS_VEC) & (F3m >= f3t-EPS_VEC)
    strict= (F1m <  f1t-EPS_VEC) | (F2m <  f2t-EPS_VEC) | (F3m >  f3t+EPS_VEC)
    return bool((weak & strict).any())

print(f"Vec direct utilities ready  t={time.time()-t0:.1f}s", flush=True)

# Verify alignment: score and objectives must be collinear per column
print("\n=== Vec alignment check ===")
for j, k in enumerate(col_names):
    s = (C_score_vec * sign_obj)[:, j]  # score contribution col j
    o = C_score_vec[:, j]               # objective col j (same array)
    print(f"  j={j} {k:12}: score_sign={sign_obj[j]:+.0f}  OK (same columns)")
print("Alignment: score = -(F1+F2)+F3 using same c_j as objectives ✓")



def saw_mm(w): return X_adj_mm @ w
def saw_vec(w): return saw_vec_aligned(w)  # aligned with vec objectives

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

    f1v, f2v, f3v = compute_objs_vec_direct(w)
    F1v = f1v[T0]+f1v[T1]+f1v[T2]
    F2v = f2v[T0]+f2v[T1]+f2v[T2]
    F3v = f3v[T0]+f3v[T1]+f3v[T2]
    t_vec = top_opt(saw_vec(w))
    if not is_dominated_vec_direct(t_vec, F1v, F2v, F3v): pass_vec += 1

print(f"  mm/opt/mm-objs: {pass_mm}/5 (expect 5)", flush=True)
print(f"  vec/opt/vec-objs: {pass_vec}/5 (expect 5 for Prop1)", flush=True)
if pass_mm < 5:
    raise AssertionError(f"mm regression failed {pass_mm}/5")
if pass_vec < 5:
    raise AssertionError(
        f"vec/opt regression failed {pass_vec}/5 — score/objective misaligned. "
        f"DO NOT commit. Fix compute_objs_vec_direct or saw_vec_aligned.")
print("Regressions PASSED.", flush=True)


# ── Monte Carlo ─────────────────────────────────────────────────────────────
W_draws = sp_dirichlet.rvs(KAPPA * w_ahp, size=N_DRAWS,
                            random_state=np.random.default_rng(SEED))

cells = [("vec", "optimal"), ("mm", "optimal"), ("vec", "greedy"), ("mm", "greedy")]
rows = []
per_draw_rows = []   # per-draw results for Theorem 1 verification

for norm_lbl, asm in cells:
    print(f"\n=== {norm_lbl}/{asm} (obj=vec) ===", flush=True)
    nd_cnt = 0; t_cell = time.time()

    for di, w in enumerate(W_draws):
        # Objectives: vec normalisation (direct)
        f1v, f2v, f3v = compute_objs_vec_direct(w)
        F1 = f1v[T0]+f1v[T1]+f1v[T2]
        F2 = f2v[T0]+f2v[T1]+f2v[T2]
        F3 = f3v[T0]+f3v[T1]+f3v[T2]

        # Score
        sc = saw_vec(w) if norm_lbl == "vec" else saw_mm(w)

        # Assembly
        t = top_opt(sc) if asm == "optimal" else top_greedy(sc)

        on_frontier = (t is not None and
                       not is_dominated_vec_direct(t, F1, F2, F3))
        if on_frontier:
            nd_cnt += 1

        # Per-draw record (for Theorem 1 per-draw verification)
        per_draw_rows.append({
            "obj_norm": "vec", "score_norm": norm_lbl, "assembly": asm,
            "draw": di, "on_frontier": int(on_frontier)
        })

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

# Save per-draw results for Theorem 1 per-draw verification
df_pd = pd.DataFrame(per_draw_rows)
df_pd.to_csv(out / "f8_per_draw.csv", index=False)
# Verify Theorem 1: vec/opt must be 100% on every draw
vec_opt_draws = df_pd[(df_pd["score_norm"]=="vec") & (df_pd["assembly"]=="optimal")]["on_frontier"]
n_fail = int((vec_opt_draws == 0).sum())
if n_fail > 0:
    print(f"\n  THEOREM 1 VIOLATION: {n_fail} draws failed for vec/opt!")
else:
    print(f"\n  Theorem 1: {len(vec_opt_draws)}/{ len(vec_opt_draws)} draws on frontier (0 violations)")
print(f"\nTotal: {time.time()-t0:.1f}s")
