# -*- coding: utf-8 -*-
"""
mc_q1q2_aprime.py  — Tarefa 3: Desenho cruzado em A′ com MC Q2
normalização × agregação × montagem, com η² por fator.

Depende de: space_aprime.py ter rodado (pareto_front_Aprime.csv)
           e monte_carlo_q2_v2.py ter terminado (mc_q2v2_raw.csv).

Esta versão roda localmente após os dois pré-requisitos existirem.

Run: uv run --with pandas --with numpy --with scipy --with paretoset python scripts/mc_q1q2_aprime.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from scipy.stats import f as f_dist

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

# ─── Verificar pré-requisitos ─────────────────────────────────────────────────
aprime_csv = os.path.join(RESULTS_DIR, "pareto_front_Aprime.csv")
mc_csv     = os.path.join(RESULTS_DIR, "mc_q2v2_raw.csv")

if not os.path.exists(aprime_csv):
    print(f"FALTA: {aprime_csv} — rode space_aprime.py primeiro")
    sys.exit(1)
if not os.path.exists(mc_csv):
    print(f"FALTA: {mc_csv} — aguarde monte_carlo_q2_v2.py na Athena")
    sys.exit(1)

print("Carregando pré-requisitos...")
from mcdm_experiment import (
    load_data, impute_nan, compute_objectives, haversine_km,
    greedy_trio, COL, AHP_WEIGHTS, MIN_DIST_KM, _build_decision_matrix, COST,
)

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
via_global = df_via.index.values
N = len(df_via)
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
w_ahp = np.array(list(AHP_WEIGHTS.values()))
col_names = list(AHP_WEIGHTS.keys())

# Objetivos em A' (normalização 389)
objs_P = compute_objectives(df_via, df_via)
f1P = objs_P["f1"].values.astype(np.float32)
f2P = objs_P["f2"].values.astype(np.float32)
f3P = objs_P["f3"].values.astype(np.float32)

valid = D_via >= MIN_DIST_KM
trio_arr = []
for i in range(N):
    for j in range(i+1, N):
        if not valid[i,j]: continue
        for k in range(j+1, N):
            if not valid[i,k] or not valid[j,k]: continue
            trio_arr.append((i,j,k))
trio_arr = np.array(trio_arr, dtype=np.int32)
M = len(trio_arr)
F1P = f1P[trio_arr[:,0]]+f1P[trio_arr[:,1]]+f1P[trio_arr[:,2]]
F2P = f2P[trio_arr[:,0]]+f2P[trio_arr[:,1]]+f2P[trio_arr[:,2]]
F3P = f3P[trio_arr[:,0]]+f3P[trio_arr[:,1]]+f3P[trio_arr[:,2]]

# Fronteira A'
df_front_P = pd.read_csv(aprime_csv)
front_P = set(frozenset([int(r.idx1),int(r.idx2),int(r.idx3)]) for _,r in df_front_P.iterrows())

X_via, benefit = _build_decision_matrix(df_via)

# ─── Definir todos os cenários (normalização × agregação × montagem) ──────────
def saw_w(X_adj, w): return (X_adj * w).sum(1)
def prom_w(X_adj, w):
    ranks = np.apply_along_axis(lambda c: pd.Series(c).rank(method="average").values, 0, X_adj)
    return ((2*ranks - N - 1) / (N - 1)) @ w
def topsis_w(X, w, norm):
    if norm == "minmax":
        R = X
    else:
        norms = np.sqrt((X**2).sum(0)); norms[norms==0]=1.
        R = X / norms
    V = R * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp = np.sqrt(((V-PIS)**2).sum(1)); dn = np.sqrt(((V-NIS)**2).sum(1))
    d = dp+dn; return np.where(d==0, 0.5, dn/d)
def vikor_w(X, w, v=0.5):
    V = X * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    denom = np.abs(PIS-NIS); denom[denom==0]=1e-12
    nd = np.abs(V-PIS)/denom; S = (nd*w).sum(1); R = (nd*w).max(1)
    Q = v*(S-S.min())/((S.max()-S.min()) or 1) + (1-v)*(R-R.min())/((R.max()-R.min()) or 1)
    return -Q
def argmax_trio(sc):
    st = sc[trio_arr[:,0]]+sc[trio_arr[:,1]]+sc[trio_arr[:,2]]
    return trio_arr[st.argmax()]

def compute_objectives_w_aprime(w):
    """f1,f2,f3 por site em A' com pesos w."""
    from mcdm_experiment import INV, _norm
    f1_keys=["perm","slope","roads"]; f2_keys=["rivers","aspect","coast","protected","wells"]; f3_keys=["urban","aero","cult"]
    sc = {}
    for j, k in enumerate(col_names):
        col = COL[k]; x=df_via[col].values.astype(float); ref=df_via[col].values.astype(float)
        if k == "aspect": c = np.where((x>=90)&(x<=180),0.,1.)
        elif k in INV:    c = 1. - _norm(x, ref)
        elif k in COST:   c = _norm(x, ref)
        else:             c = _norm(x, ref)
        sc[k] = w[j] * c
    f1v = sum(sc[k] for k in f1_keys)
    f2v = sum(sc[k] for k in f2_keys)
    f3v = sum(sc[k] for k in f3_keys)
    return np.array(f1v,dtype=np.float32), np.array(f2v,dtype=np.float32), np.array(f3v,dtype=np.float32)

def is_dom_aprime(i,j,k,F1,F2,F3,f1v,f2v,f3v):
    f1t=float(f1v[i]+f1v[j]+f1v[k]); f2t=float(f2v[i]+f2v[j]+f2v[k]); f3t=float(f3v[i]+f3v[j]+f3v[k])
    return bool(((F1<=f1t)&(F2<=f2t)&(F3>=f3t)&((F1<f1t)|(F2<f2t)|(F3>f3t))).any())

def gap_aprime(i,j,k,F1,F2,F3,f1v,f2v,f3v):
    f1t=float(f1v[i]+f1v[j]+f1v[k]); f2t=float(f2v[i]+f2v[j]+f2v[k]); f3t=float(f3v[i]+f3v[j]+f3v[k])
    if not is_dom_aprime(i,j,k,F1,F2,F3,f1v,f2v,f3v): return 0.
    f1r=F1.max()-F1.min(); f2r=F2.max()-F2.min(); f3r=F3.max()-F3.min()
    return float(max(0., np.minimum(np.minimum((f1t-F1)/(f1r or 1),(f2t-F2)/(f2r or 1)),(F3-f3t)/(f3r or 1)).max()))

SCENARIOS = [
    # (nome, norm, agg, mont, fn_score, fn_X_adj)
    ("SAW_mm_g",    "minmax", "linear",    "greedy",  "saw",   None),
    ("SAW_mm_o",    "minmax", "linear",    "optimal", "saw",   None),
    ("TOPSIS_mm_g", "minmax", "dist_ideal","greedy",  "topsis_mm", None),
    ("TOPSIS_vn_g", "vector", "dist_ideal","greedy",  "topsis_vn", None),
    ("VIKOR_mm_g",  "minmax", "compromise","greedy",  "vikor",  None),
    ("PROM_rank_g", "ranks",  "outranking","greedy",  "prom",   None),
    ("PROM_rank_o", "ranks",  "outranking","optimal", "prom",   None),
]

# ─── MC Q2 em A' ──────────────────────────────────────────────────────────────
N_DRAWS = 500
SEED    = 42
ALPHAS  = [50, 200]
rng     = np.random.default_rng(SEED)

print("Rodando MC Q2 em A'...")
records = []
from mcdm_experiment import COST as COST_SET

for alpha in ALPHAS:
    print(f"  alpha={alpha}")
    for draw in range(N_DRAWS):
        w_draw = rng.dirichlet(alpha * w_ahp)
        X_adj = X_via.copy()
        for j2, b in enumerate(benefit):
            if not b: X_adj[:, j2] = 1.0 - X_via[:, j2]

        # Objetivos Q2 em A'
        f1v_d, f2v_d, f3v_d = compute_objectives_w_aprime(w_draw)
        F1d = f1v_d[trio_arr[:,0]]+f1v_d[trio_arr[:,1]]+f1v_d[trio_arr[:,2]]
        F2d = f2v_d[trio_arr[:,0]]+f2v_d[trio_arr[:,1]]+f2v_d[trio_arr[:,2]]
        F3d = f3v_d[trio_arr[:,0]]+f3v_d[trio_arr[:,1]]+f3v_d[trio_arr[:,2]]

        for name, norm, agg, mont, fn, _ in SCENARIOS:
            if fn == "saw":     sc = saw_w(X_adj, w_draw)
            elif fn=="topsis_mm": sc = topsis_w(X_via, w_draw, "minmax")
            elif fn=="topsis_vn": sc = topsis_w(X_via, w_draw, "vector")
            elif fn=="vikor":   sc = vikor_w(X_via, w_draw)
            else:               sc = prom_w(X_adj, w_draw)

            if mont == "greedy":  idx = greedy_trio(sc, D_via)
            else:                 idx = argmax_trio(sc)
            i,j,k = idx

            nd = int(not is_dom_aprime(i,j,k, F1d,F2d,F3d,f1v_d,f2v_d,f3v_d))
            gn = gap_aprime(i,j,k, F1d,F2d,F3d,f1v_d,f2v_d,f3v_d)
            records.append({"alpha":alpha,"draw":draw,"cenario":name,"norm":norm,
                            "agg":agg,"mont":mont,"nd_Q2":nd,"gap_Q2":gn})

df_raw = pd.DataFrame(records)
df_raw.to_csv(os.path.join(RESULTS_DIR,"mc_aprime_raw.csv"), index=False)

# ─── Agregação e η² ───────────────────────────────────────────────────────────
agg = (df_raw.groupby(["alpha","cenario","norm","agg","mont"])
       .agg(pct_nd=("nd_Q2",lambda x:100*x.mean()),
            med_gap=("gap_Q2","median")).reset_index())
agg.to_csv(os.path.join(RESULTS_DIR,"mc_aprime_summary.csv"), index=False)

print("\n=== MC Q2 em A' — SUMMARY ===")
print(agg.to_string(index=False, float_format=lambda x: f"{x:.1f}"))

# Decomposição da variância (η²) por fator, combinando os dois α
df_all_draws = df_raw.copy()
def eta2(df, factor, response="gap_Q2"):
    grand_mean = df[response].mean()
    ss_total   = ((df[response] - grand_mean)**2).sum()
    ss_factor  = sum(len(g)*(g[response].mean()-grand_mean)**2 for _,g in df.groupby(factor))
    return ss_factor / ss_total if ss_total > 0 else 0.

print("\n=== Decomposição η² por fator (todos os α) ===")
for factor in ["norm","agg","mont"]:
    e = eta2(df_all_draws, factor)
    print(f"  η²({factor}) = {e:.4f}  ({e*100:.1f}%)")

print("\nResultados salvos em results/mc_aprime_*.csv")
