# -*- coding: utf-8 -*-
"""
diag.py — diagnósticos round 6
Roda com: uv run --with pandas --with numpy python scripts/diag.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from mcdm_experiment import (
    load_data, impute_nan, compute_objectives, haversine_km,
    topsis_scores, saw_scores, _build_decision_matrix, _norm,
    COL, AHP_WEIGHTS, MIN_DIST_KM, INV, COST, BENEFIT,
)

# ─── load ──────────────────────────────────────────────────────────────────
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
via_global = df_via.index.values
objs_473 = compute_objectives(df_imp, df_imp)
TOL = 1e-9

# ─── (a) {51, 233, 345}: in_front / dominated / gap ───────────────────────
print("=" * 60)
print("(a/b) PROMETHEE trio {51, 233, 345}")
promethee_trio = sorted([51, 233, 345])
P_cost   = par["Cost"].values
P_impact = par["Impact"].values
P_safety = par["Safety"].values

# Objectives of the PROMETHEE greedy trio
obj = objs_473.loc[promethee_trio].sum()
f1_t, f2_t, f3_t = float(obj["f1"]), float(obj["f2"]), float(obj["f3"])
print(f"  f1={f1_t:.6f}  f2={f2_t:.6f}  f3={f3_t:.6f}")

# in_front: is this trio listed in exhaustive_search_pareto.csv?
pareto_ids = set(
    frozenset([int(r.idx1), int(r.idx2), int(r.idx3)])
    for _, r in par.iterrows()
)
in_front = frozenset(promethee_trio) in pareto_ids
print(f"  in_front: {in_front}")

# dominated with tolerance
le  = (P_cost   <= f1_t + TOL) & (P_impact <= f2_t + TOL) & (P_safety >= f3_t - TOL)
lt  = (P_cost   <  f1_t - TOL) | (P_impact <  f2_t - TOL) | (P_safety >  f3_t + TOL)
dom = le & lt
print(f"  dominated (tol=1e-9): {dom.any()}  n_dominators={dom.sum()}")
if dom.any():
    print("  First dominator:", par.loc[dom, ["idx1","idx2","idx3","Cost","Impact","Safety"]].head(3))

# gap = max(0, max_p min_m(t_m - p_m))  — all objectives as cost (flip safety)
# t_m - p_m > 0 means the trio is worse than p on objective m
diff_c = f1_t - P_cost         # > 0 if trio worse in cost
diff_i = f2_t - P_impact       # > 0 if trio worse in impact
diff_s = P_safety - f3_t       # > 0 if trio worse in safety (pareto has more safety)
gap_per_p = np.minimum(np.minimum(diff_c, diff_i), diff_s)  # min_m
gap = max(0.0, gap_per_p.max())   # max_p
print(f"  gap = max(0, max_p min_m(t_m - p_m)) = {gap:.2e}")

# ─── (c) TOPSIS code excerpt ───────────────────────────────────────────────
print()
print("=" * 60)
print("(c) TOPSIS — V and distances check on a 3-site toy")
# Pick 3 sites and verify manually that d+ = sqrt(sum (v-PIS)^2) with no extra w
toy = df_via.iloc[:3].copy()
X_toy, benefit_toy = _build_decision_matrix(toy)
w_arr = np.array(list(AHP_WEIGHTS.values()))
norms_toy = np.sqrt((X_toy**2).sum(axis=0)); norms_toy[norms_toy==0] = 1
R_toy = X_toy / norms_toy
V_toy = R_toy * w_arr
PIS_toy = np.where(benefit_toy, V_toy.max(0), V_toy.min(0))
NIS_toy = np.where(benefit_toy, V_toy.min(0), V_toy.max(0))
d_pos_toy = np.sqrt(((V_toy - PIS_toy)**2).sum(1))
d_neg_toy = np.sqrt(((V_toy - NIS_toy)**2).sum(1))
# Sanity: d_pos + d_neg should be <= d(PIS, NIS)
d_ideal = np.sqrt(((PIS_toy - NIS_toy)**2).sum())
print(f"  d(PIS,NIS)={d_ideal:.6f}")
for i in range(3):
    print(f"  site {toy.index[i]}: d+={d_pos_toy[i]:.6f}  d-={d_neg_toy[i]:.6f}  "
          f"d++d-={d_pos_toy[i]+d_neg_toy[i]:.6f}  C={d_neg_toy[i]/(d_pos_toy[i]+d_neg_toy[i]):.4f}")
print("  (each d+ + d- should be <= d(PIS,NIS) — property of TOPSIS)")

# ─── (d) TOPSIS with min-max normalisation ─────────────────────────────────
print()
print("=" * 60)
print("(d) TOPSIS top-10 with min-max vs vector normalisation")

def topsis_minmax(df: pd.DataFrame) -> np.ndarray:
    """TOPSIS with min-max normalisation instead of vector normalisation."""
    n = len(df)
    m = len(AHP_WEIGHTS)
    X = np.zeros((n, m)); benefit = []
    for j, k in enumerate(AHP_WEIGHTS):
        x = df[COL[k]].values.astype(float)
        if k == "aspect":
            c = np.where((x >= 90) & (x <= 180), 1.0, 0.0)
            benefit.append(True)
        elif k in COST:
            c = _norm(x, x); benefit.append(False)
        elif k in INV:
            c = _norm(x, x); benefit.append(True)
        else:
            c = _norm(x, x); benefit.append(True)
        X[:, j] = c
    benefit = np.array(benefit)
    w_arr = np.array(list(AHP_WEIGHTS.values()))
    V = X * w_arr   # weighted min-max (no vector normalisation)
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    d_pos = np.sqrt(((V - PIS)**2).sum(1))
    d_neg = np.sqrt(((V - NIS)**2).sum(1))
    denom = d_pos + d_neg
    return np.where(denom == 0, 0.5, d_neg / denom)

sc_topsis_mm = topsis_minmax(df_via)
sc_topsis_vn = topsis_scores(df_via)

s_mm = pd.Series(sc_topsis_mm, index=df_via.index)
s_vn = pd.Series(sc_topsis_vn, index=df_via.index)
top10_mm = s_mm.nlargest(10).index.tolist()
top10_vn = s_vn.nlargest(10).index.tolist()
print(f"  TOPSIS vector-norm top-10: {top10_vn}")
print(f"  TOPSIS min-max     top-10: {top10_mm}")
overlap = set(top10_mm) & set(top10_vn)
print(f"  Overlap: {sorted(overlap)}  ({len(overlap)} sites)")

# ─── (e) Frequency of top-k in Pareto trios ───────────────────────────────
print()
print("=" * 60)
print("(e) Frequency of top-k sites in the 213 Pareto trios")
pareto_site_counts = {}
for _, row in par.iterrows():
    for s in [int(row.idx1), int(row.idx2), int(row.idx3)]:
        pareto_site_counts[s] = pareto_site_counts.get(s, 0) + 1

sc_saw = saw_scores(df_via)
sc_topsis_vn_arr = topsis_scores(df_via)
sc_vikor = None  # skip for speed
sc_prom = None

from mcdm_experiment import promethee2_scores, vikor_scores
sc_prom_arr = promethee2_scores(df_via)
sc_vikor_arr = vikor_scores(df_via)

for mname, sc_arr in [("SAW", sc_saw), ("TOPSIS", sc_topsis_vn_arr),
                       ("VIKOR", sc_vikor_arr), ("PROMETHEE", sc_prom_arr)]:
    s = pd.Series(sc_arr, index=df_via.index)
    for k in (10, 20):
        topk = set(s.nlargest(k).index.tolist())
        in_par = sum(1 for sid in topk if sid in pareto_site_counts)
        print(f"  {mname:12s} top-{k:2d}: {in_par}/{k} sites appear in Pareto trios  "
              f"({sorted(topk & set(pareto_site_counts.keys()))})")

# ─── (f) Trios without NaN sites 41, 385, 429 ─────────────────────────────
print()
print("=" * 60)
print("(f) Trios without NaN-imputed sites {41, 385, 429}")
NAN_SITES = {41, 385, 429}
df_clean = df_via[~df_via.index.isin(NAN_SITES)].copy()
via_clean = df_clean.index.values
n_clean = len(df_clean)
print(f"  Clean viable sites: {n_clean} (removed {len(df_via)-n_clean})")

D_clean = haversine_km(df_clean["latitude (degrees)"].values,
                       df_clean["longitude (degrees)"].values)

from mcdm_experiment import greedy_trio

for mname, sc_arr in [("SAW", sc_saw), ("TOPSIS", sc_topsis_vn_arr),
                       ("VIKOR", sc_vikor_arr), ("PROMETHEE", sc_prom_arr)]:
    sc_clean = pd.Series(sc_arr, index=df_via.index).loc[df_clean.index].values
    g = greedy_trio(sc_clean, D_clean)
    gids = tuple(int(via_clean[i]) for i in g)
    obj = objs_473.loc[list(gids)].sum()
    f1, f2, f3 = float(obj.f1), float(obj.f2), float(obj.f3)
    le_c  = (P_cost <= f1+TOL) & (P_impact <= f2+TOL) & (P_safety >= f3-TOL)
    lt_c  = (P_cost < f1-TOL) | (P_impact < f2-TOL) | (P_safety > f3+TOL)
    dom_c = (le_c & lt_c).any()
    diff_c2 = f1 - P_cost; diff_i2 = f2 - P_impact; diff_s2 = P_safety - f3
    gap_c = max(0.0, np.minimum(np.minimum(diff_c2, diff_i2), diff_s2).max())
    in_f = frozenset(gids) in pareto_ids
    print(f"  {mname:12s} clean greedy: {sorted(gids)}  "
          f"f1={f1:.4f} f2={f2:.4f} f3={f3:.4f}  "
          f"in_front={in_f}  dom={dom_c}  gap={gap_c:.2e}")
