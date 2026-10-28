# -*- coding: utf-8 -*-
"""
diag2.py  —  diagnósticos round 7
(a) taxa de base: quantas das 389 áreas aparecem em algum dos 213 trios
(b) pesos efetivos nos três espaços de normalização
(c) TOPSIS min-max guloso + ótimo
(d) PROMETHEE ótimo
(e) gap normalizado pela amplitude da fronteira

Run:  uv run --with pandas --with numpy python scripts/diag2.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

from mcdm_experiment import (
    load_data, impute_nan, compute_objectives, haversine_km,
    promethee2_scores, greedy_trio, optimal_trio_enumerate,
    in_pareto_front, pareto_dominates, gap_additive,
    trio_objectives_from_global,
    COL, AHP_WEIGHTS, MIN_DIST_KM, INV, COST, BENEFIT,
    _build_decision_matrix, _norm,
)

# ─── load + prep ────────────────────────────────────────────────────────────
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
via_global = df_via.index.values
objs_473 = compute_objectives(df_imp, df_imp)
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)

W_arr = np.array(list(AHP_WEIGHTS.values()))

# Frontier amplitude (for normalised gap)
f1_range = par["Cost"].max()   - par["Cost"].min()
f2_range = par["Impact"].max() - par["Impact"].min()
f3_range = par["Safety"].max() - par["Safety"].min()
print(f"Frontier amplitude: f1={f1_range:.4f}  f2={f2_range:.4f}  f3={f3_range:.4f}")


def gap_normalised(f1, f2, f3):
    """gap normalised by frontier amplitude, then take max(0, ...)."""
    diff_c = (f1 - par["Cost"].values)   / f1_range
    diff_i = (f2 - par["Impact"].values) / f2_range
    diff_s = (par["Safety"].values - f3) / f3_range
    return float(max(0.0, np.minimum(np.minimum(diff_c, diff_i), diff_s).max()))


def eval_trio_global(label, global_ids):
    obj = trio_objectives_from_global(global_ids, objs_473)
    f1, f2, f3 = obj["f1"], obj["f2"], obj["f3"]
    inf = in_pareto_front(par, global_ids)
    dom = pareto_dominates(par, f1, f2, f3)
    gap = gap_additive(par, f1, f2, f3)
    gap_n = gap_normalised(f1, f2, f3)
    print(f"  {label}: {sorted(global_ids)}")
    print(f"    f1={f1:.4f} f2={f2:.4f} f3={f3:.4f}  "
          f"in_front={inf}  dom={'Y' if dom else 'N'}  "
          f"gap={gap:.4f}  gap_norm={gap_n:.4f}")
    return inf, dom, gap, gap_n


# ─── (a) taxa de base ────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("(a) Taxa de base")
front_sites = np.unique(par[["idx1", "idx2", "idx3"]].values.ravel().astype(int))
n_front = len(front_sites)
n_front_in_via = sum(1 for s in front_sites if s in via_global)
base_rate = n_front_in_via / len(via_global)
print(f"  Sites únicos nos 213 trios: {n_front}")
print(f"  Desses, nos 389 viáveis:    {n_front_in_via}")
print(f"  Taxa de base (base rate):   {base_rate:.3f}  ({n_front_in_via}/{len(via_global)})")
print(f"  Top-10 aleatório esperado:  {base_rate*10:.1f} de 10")
print(f"  Top-20 aleatório esperado:  {base_rate*20:.1f} de 20")

# ─── (b) pesos efetivos nas 3 normalizações ──────────────────────────────────
print("\n" + "=" * 60)
print("(b) Pesos efetivos: amplitude de cada critério nas 3 normalizações")
X_raw, benefit = _build_decision_matrix(df_via)

# min-max (amplitude por coluna = 1 after min-max → weight contribution = w_j)
amp_minmax = X_raw.max(0) - X_raw.min(0)   # already in [0,1] after _norm

# vector normalisation: amplitude in V_j = w_j * (X_j / ||X_j||)
norms_vec = np.sqrt((X_raw**2).sum(0)); norms_vec[norms_vec == 0] = 1.0
R_vec = X_raw / norms_vec
V_vec = R_vec * W_arr
amp_vec = V_vec.max(0) - V_vec.min(0)

# rank normalisation (PROMETHEE-as-SAW)
ranks_all = np.apply_along_axis(
    lambda c: (pd.Series(c).rank(method="average") - 1) / (len(c) - 1), 0, X_raw
)
V_rank = ranks_all * W_arr
amp_rank = V_rank.max(0) - V_rank.min(0)

print(f"  {'Criterion':20s}  {'w':>6}  {'amp_minmax':>10}  {'amp_vec':>10}  {'amp_rank':>10}")
print(f"  {'':20s}  {'':>6}  {'eff_mm':>10}  {'eff_vec':>10}  {'eff_rank':>10}")
crit_names = list(AHP_WEIGHTS.keys())
# effective weight = w_j * amplitude / sum(w_k * amplitude_k)
for j, k in enumerate(AHP_WEIGHTS):
    eff_mm   = W_arr[j] * amp_minmax[j] / (W_arr * amp_minmax).sum()
    eff_vec  = W_arr[j] * amp_vec[j]    / (W_arr * amp_vec).sum()
    eff_rank = W_arr[j] * amp_rank[j]   / (W_arr * amp_rank).sum()
    print(f"  {k:20s}  {W_arr[j]:6.3f}  {eff_mm:10.4f}  {eff_vec:10.4f}  {eff_rank:10.4f}")

print()
# Highlight aspect
j_asp = crit_names.index("aspect")
print(f"  ASPECT effective weight:")
print(f"    min-max: {W_arr[j_asp] * amp_minmax[j_asp] / (W_arr * amp_minmax).sum():.4f}")
print(f"    vector : {W_arr[j_asp] * amp_vec[j_asp]    / (W_arr * amp_vec).sum():.4f}")
print(f"    ranks  : {W_arr[j_asp] * amp_rank[j_asp]   / (W_arr * amp_rank).sum():.4f}")

# ─── (c) TOPSIS min-max: guloso + ótimo ──────────────────────────────────────
print("\n" + "=" * 60)
print("(c) TOPSIS min-max — greedy + optimal")

def topsis_minmax_scores(df):
    X, benefit = _build_decision_matrix(df)
    V = X * W_arr          # weighted min-max
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    d_pos = np.sqrt(((V - PIS)**2).sum(1))
    d_neg = np.sqrt(((V - NIS)**2).sum(1))
    denom = d_pos + d_neg
    return np.where(denom == 0, 0.5, d_neg / denom)

sc_tmm = topsis_minmax_scores(df_via)
g_tmm = greedy_trio(sc_tmm, D_via)
g_tmm_global = tuple(int(via_global[i]) for i in g_tmm)
eval_trio_global("TOPSIS-mm greedy", g_tmm_global)

print("  TOPSIS-mm optimal: enumerating 1,944,653 trios...")
o_tmm = optimal_trio_enumerate(sc_tmm, D_via)
o_tmm_global = tuple(int(via_global[i]) for i in o_tmm)
eval_trio_global("TOPSIS-mm optimal", o_tmm_global)

# ─── (d) PROMETHEE ótimo ──────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("(d) PROMETHEE optimal")
sc_prom = promethee2_scores(df_via)
print("  PROMETHEE optimal: enumerating 1,944,653 trios...")
o_prom = optimal_trio_enumerate(sc_prom, D_via)
o_prom_global = tuple(int(via_global[i]) for i in o_prom)
eval_trio_global("PROMETHEE optimal", o_prom_global)

# ─── (e) gap normalizado para todos os trios existentes ──────────────────────
print("\n" + "=" * 60)
print("(e) Gap normalizado para os trios do experimento")

trios_to_eval = [
    ("SAW greedy",        (184, 279, 320)),
    ("SAW optimal",       (184, 430, 460)),
    ("TOPSIS-vn greedy",  (233, 320, 355)),
    ("TOPSIS-vn optimal", (227, 233, 345)),
    ("TOPSIS-mm greedy",  g_tmm_global),
    ("TOPSIS-mm optimal", o_tmm_global),
    ("VIKOR greedy",      (233, 279, 320)),
    ("PROMETHEE greedy",  (51, 233, 345)),
    ("PROMETHEE optimal", o_prom_global),
    ("BCS_IEEE",          (184, 430, 460)),
]
for label, gids in trios_to_eval:
    obj = trio_objectives_from_global(gids, objs_473)
    gn = gap_normalised(obj["f1"], obj["f2"], obj["f3"])
    inf = in_pareto_front(par, gids)
    dom = pareto_dominates(par, obj["f1"], obj["f2"], obj["f3"])
    print(f"  {label:22s}: gap_norm={gn:.4f}  in_front={inf}  dom={'Y' if dom else 'N'}")
