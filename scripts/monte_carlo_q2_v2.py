# -*- coding: utf-8 -*-
"""
monte_carlo_q2_v2.py  — MC Q1+Q2 com objetivos corretos (compute_objectives)
Correção crítica: usar compute_objectives para F1,F2,F3 (não sc_all_adj@w).

Q1: pesos sorteados nos métodos; dominância nos F calculados com pesos AHP fixos.
Q2: pesos sorteados nos métodos E nos objetivos (teste de P1).
    Objetivos Q2 = compute_objectives com pesos sorteados.

Teste de sanidade P1: SAW_s1 ótimo (score = -f1-f2+f3, mesmos pesos) deve dar 100% em Q2.

Run: uv run --with pandas --with numpy --with scipy python scripts/monte_carlo_q2_v2.py
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

from mcdm_experiment import (
    load_data, impute_nan, compute_objectives, haversine_km, greedy_trio,
    COL, AHP_WEIGHTS, MIN_DIST_KM, COST, INV, _build_decision_matrix, _norm,
)

N_DRAWS  = 500
SEED     = 42
ALPHAS   = [50, 200]
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

print("Carregando dados...")
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
via_global = df_via.index.values
N = len(df_via)
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
w_ahp = np.array(list(AHP_WEIGHTS.values()))
rng   = np.random.default_rng(SEED)

# ─── Pré-calcular trios viáveis ───────────────────────────────────────────────
print("Pré-calculando trios...")
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
print(f"  {M:,} trios")

# ─── Objetivos AHP fixos (para Q1) ───────────────────────────────────────────
print("Calculando objetivos AHP fixos (Q1)...")
objs_ahp = compute_objectives(df_via, df_imp)
f1v_ahp = objs_ahp["f1"].values.astype(np.float32)
f2v_ahp = objs_ahp["f2"].values.astype(np.float32)
f3v_ahp = objs_ahp["f3"].values.astype(np.float32)
F1_ahp = f1v_ahp[trio_arr[:,0]] + f1v_ahp[trio_arr[:,1]] + f1v_ahp[trio_arr[:,2]]
F2_ahp = f2v_ahp[trio_arr[:,0]] + f2v_ahp[trio_arr[:,1]] + f2v_ahp[trio_arr[:,2]]
F3_ahp = f3v_ahp[trio_arr[:,0]] + f3v_ahp[trio_arr[:,1]] + f3v_ahp[trio_arr[:,2]]

# ─── compute_objectives com pesos customizados ───────────────────────────────
def compute_objectives_w(w):
    """
    Recalcula f1,f2,f3 por site viável com pesos w.
    Usa a mesma lógica de compute_objectives mas com pesos customizados.
    Para COST:    c = _norm(x, ref)      (menor x = menor c = menor f1 = melhor)
    Para INV:     c = 1 - _norm(x, ref)  (maior x = menor c = menor f2 = melhor)
    Para BENEFIT: c = _norm(x, ref)      (maior x = maior c = maior f3 = melhor)
    """
    col_names = list(w.keys() if hasattr(w, 'keys') else AHP_WEIGHTS.keys())
    w_arr = np.array(list(w) if not hasattr(w, 'keys') else list(w.values()))
    
    f1_keys = ["perm","slope","roads"]
    f2_keys = ["rivers","aspect","coast","protected","wells"]
    f3_keys = ["urban","aero","cult"]
    
    sc = {}
    for j, k in enumerate(AHP_WEIGHTS.keys()):
        col = COL[k]
        x   = df_via[col].values.astype(float)
        ref = df_imp[col].values.astype(float)
        if k == "aspect":
            c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
        elif k in INV:
            c = 1.0 - _norm(x, ref)
        elif k in COST:
            c = _norm(x, ref)
        else:  # BENEFIT
            c = _norm(x, ref)
        sc[k] = w_arr[j] * c
    
    f1v = sum(sc[k] for k in f1_keys)
    f2v = sum(sc[k] for k in f2_keys)
    f3v = sum(sc[k] for k in f3_keys)
    return (np.array(f1v, dtype=np.float32),
            np.array(f2v, dtype=np.float32),
            np.array(f3v, dtype=np.float32))

# ─── Scores dos métodos (normalização 389) ───────────────────────────────────
X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b: X_adj[:, j] = 1.0 - X_via[:, j]

col_names = list(AHP_WEIGHTS.keys())

def saw_w(w):     return (X_adj * w).sum(1)
def prom_w(w):
    ranks = np.apply_along_axis(
        lambda c: pd.Series(c).rank(method="average").values, 0, X_adj)
    return ((2*ranks - N - 1) / (N - 1)) @ w
def topsis_mm_w(w):
    V = X_via * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp = np.sqrt(((V-PIS)**2).sum(1)); dn = np.sqrt(((V-NIS)**2).sum(1))
    d = dp+dn; return np.where(d==0, 0.5, dn/d)
def topsis_vn_w(w):
    norms = np.sqrt((X_adj**2).sum(0)); norms[norms==0]=1.
    R = X_adj / norms; V = R * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp = np.sqrt(((V-PIS)**2).sum(1)); dn = np.sqrt(((V-NIS)**2).sum(1))
    d = dp+dn; return np.where(d==0, 0.5, dn/d)
def vikor_w(w, v=0.5):
    V = X_via * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    denom = np.abs(PIS-NIS); denom[denom==0]=1e-12
    nd = np.abs(V-PIS)/denom
    S = (nd*w).sum(1); R = (nd*w).max(1)
    Q = v*(S-S.min())/((S.max()-S.min()) or 1) + (1-v)*(R-R.min())/((R.max()-R.min()) or 1)
    return -Q

def saw_s1_w(w):
    """SAW_s1: score coerente com Pareto = -f1(w) - f2(w) + f3(w)"""
    f1v, f2v, f3v = compute_objectives_w(w)
    return -f1v - f2v + f3v

def argmax_trio(sc):
    st = sc[trio_arr[:,0]]+sc[trio_arr[:,1]]+sc[trio_arr[:,2]]
    return trio_arr[st.argmax()]

def is_dom(f1t, f2t, f3t, F1, F2, F3):
    return bool(((F1<=f1t)&(F2<=f2t)&(F3>=f3t)&((F1<f1t)|(F2<f2t)|(F3>f3t))).any())

def gap_n(f1t, f2t, f3t, F1, F2, F3):
    if not is_dom(f1t, f2t, f3t, F1, F2, F3): return 0.
    f1r=F1.max()-F1.min(); f2r=F2.max()-F2.min(); f3r=F3.max()-F3.min()
    return float(max(0., np.minimum(np.minimum((f1t-F1)/(f1r or 1),
                                               (f2t-F2)/(f2r or 1)),
                                   (F3-f3t)/(f3r or 1)).max()))

def jac10(sc_a, sc_b):
    a=set(np.argsort(-sc_a)[:10]); b=set(np.argsort(-sc_b)[:10])
    return len(a&b)/len(a|b) if a|b else 1.

# ─── 4 testes de regressão (pesos AHP fixos) ─────────────────────────────────
print("\nTESTES DE REGRESSÃO:")
sc_saw_ref = saw_w(w_ahp); sc_prom_ref = prom_w(w_ahp)
g_saw_g = greedy_trio(sc_saw_ref, D_via)
g_prom_g = greedy_trio(sc_prom_ref, D_via)
g_saw_s1_o = argmax_trio(saw_s1_w(w_ahp))

g_saw_g_gl  = tuple(sorted(int(via_global[x]) for x in g_saw_g))
g_prom_g_gl = tuple(sorted(int(via_global[x]) for x in g_prom_g))
g_s1_o_gl   = tuple(sorted(int(via_global[x]) for x in g_saw_s1_o))

i,j,k = g_saw_g
f1t=float(f1v_ahp[i]+f1v_ahp[j]+f1v_ahp[k])
f2t=float(f2v_ahp[i]+f2v_ahp[j]+f2v_ahp[k])
f3t=float(f3v_ahp[i]+f3v_ahp[j]+f3v_ahp[k])
T1_dom = is_dom(f1t, f2t, f3t, F1_ahp, F2_ahp, F3_ahp)

i,j,k = g_prom_g
f1p=float(f1v_ahp[i]+f1v_ahp[j]+f1v_ahp[k])
f2p=float(f2v_ahp[i]+f2v_ahp[j]+f2v_ahp[k])
f3p=float(f3v_ahp[i]+f3v_ahp[j]+f3v_ahp[k])
T3_nd = not is_dom(f1p, f2p, f3p, F1_ahp, F2_ahp, F3_ahp)

# P1: SAW_s1 ótimo não dominado em Q2 (objetivos = mesmos pesos)
f1v_s1, f2v_s1, f3v_s1 = compute_objectives_w(w_ahp)
F1_s1 = f1v_s1[trio_arr[:,0]]+f1v_s1[trio_arr[:,1]]+f1v_s1[trio_arr[:,2]]
F2_s1 = f2v_s1[trio_arr[:,0]]+f2v_s1[trio_arr[:,1]]+f2v_s1[trio_arr[:,2]]
F3_s1 = f3v_s1[trio_arr[:,0]]+f3v_s1[trio_arr[:,1]]+f3v_s1[trio_arr[:,2]]
i,j,k = g_saw_s1_o
f1s=float(f1v_s1[i]+f1v_s1[j]+f1v_s1[k])
f2s=float(f2v_s1[i]+f2v_s1[j]+f2v_s1[k])
f3s=float(f3v_s1[i]+f3v_s1[j]+f3v_s1[k])
T_p1 = not is_dom(f1s, f2s, f3s, F1_s1, F2_s1, F3_s1)

jac_sp = jac10(sc_saw_ref, sc_prom_ref)

print(f"  T1 SAW greedy=={g_saw_g_gl}, dom Q1: {'PASS' if T1_dom else 'FAIL'}")
print(f"  T3 PROMETHEE greedy=={g_prom_g_gl}, nd Q1: {'PASS' if T3_nd else 'FAIL'}")
print(f"  T_P1 SAW_s1 ótimo=={g_s1_o_gl}, nd Q2: {'PASS' if T_p1 else 'FAIL'}")
print(f"  Jaccard SAW-PROM: {jac_sp:.3f}  (esperado ~0.43)")

assert T1_dom and T3_nd and T_p1, "Regressão falhou"
print("  4/4 PASS")

# ─── Monte Carlo ─────────────────────────────────────────────────────────────
METHODS = [
    ("SAW_s1",    saw_s1_w,    "optimal"),
    ("SAW_s1",    saw_s1_w,    "greedy"),
    ("SAW",       saw_w,       "greedy"),
    ("TOPSIS_MM", topsis_mm_w, "greedy"),
    ("TOPSIS_VN", topsis_vn_w, "greedy"),
    ("VIKOR",     vikor_w,     "greedy"),
    ("PROMETHEE", prom_w,      "greedy"),
]

records = []
for alpha in ALPHAS:
    print(f"\n=== alpha={alpha} ===")
    t0 = time.time()
    for draw in range(N_DRAWS):
        w_draw = rng.dirichlet(alpha * w_ahp)
        sc_saw_ref_d = saw_w(w_draw)

        # Objetivos Q2 com pesos sorteados
        f1v_d, f2v_d, f3v_d = compute_objectives_w(w_draw)
        F1_d = f1v_d[trio_arr[:,0]]+f1v_d[trio_arr[:,1]]+f1v_d[trio_arr[:,2]]
        F2_d = f2v_d[trio_arr[:,0]]+f2v_d[trio_arr[:,1]]+f2v_d[trio_arr[:,2]]
        F3_d = f3v_d[trio_arr[:,0]]+f3v_d[trio_arr[:,1]]+f3v_d[trio_arr[:,2]]

        for method, fn_sc, variant in METHODS:
            sc = fn_sc(w_draw)
            if variant == "greedy":
                idx = greedy_trio(sc, D_via)
            else:
                idx = argmax_trio(sc)
            i,j,k = idx

            f1q1=float(f1v_ahp[i]+f1v_ahp[j]+f1v_ahp[k])
            f2q1=float(f2v_ahp[i]+f2v_ahp[j]+f2v_ahp[k])
            f3q1=float(f3v_ahp[i]+f3v_ahp[j]+f3v_ahp[k])
            nd_Q1 = int(not is_dom(f1q1,f2q1,f3q1, F1_ahp,F2_ahp,F3_ahp))
            gn_Q1 = gap_n(f1q1,f2q1,f3q1, F1_ahp,F2_ahp,F3_ahp)

            f1q2=float(f1v_d[i]+f1v_d[j]+f1v_d[k])
            f2q2=float(f2v_d[i]+f2v_d[j]+f2v_d[k])
            f3q2=float(f3v_d[i]+f3v_d[j]+f3v_d[k])
            nd_Q2 = int(not is_dom(f1q2,f2q2,f3q2, F1_d,F2_d,F3_d))
            gn_Q2 = gap_n(f1q2,f2q2,f3q2, F1_d,F2_d,F3_d)

            jac = jac10(sc, sc_saw_ref_d)
            records.append({"alpha":alpha,"draw":draw,"method":method,"variant":variant,
                            "nd_Q1":nd_Q1,"gap_Q1":gn_Q1,"nd_Q2":nd_Q2,"gap_Q2":gn_Q2,
                            "jaccard_10":jac})

        if (draw+1) % 100 == 0:
            print(f"  draw {draw+1}/{N_DRAWS}  ({time.time()-t0:.0f}s)")

import time as _time; t_start = _time.time()

df_raw = pd.DataFrame(records)
df_raw.to_csv(os.path.join(RESULTS_DIR,"mc_q2v2_raw.csv"),index=False)
agg = (df_raw.groupby(["alpha","method","variant"])
       .agg(pct_nd_Q1=("nd_Q1",lambda x:100*x.mean()),
            med_gap_Q1=("gap_Q1","median"),
            pct_nd_Q2=("nd_Q2",lambda x:100*x.mean()),
            med_gap_Q2=("gap_Q2","median"),
            n=("draw","count")).reset_index())
agg.to_csv(os.path.join(RESULTS_DIR,"mc_q2v2_summary.csv"),index=False)
print("\n"+"="*75)
print("MC Q2 v2 SUMMARY (objetivos via compute_objectives)")
print("="*75)
print(agg.to_string(index=False,float_format=lambda x:f"{x:.1f}"))

import time
