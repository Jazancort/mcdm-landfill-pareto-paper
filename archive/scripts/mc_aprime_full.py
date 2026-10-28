# -*- coding: utf-8 -*-
"""
mc_aprime_full.py — Round 11, tarefas 2, 3, 5
MC Q1 e Q2 em A' por método/variante, η² balanceado com bootstrap, contraexemplo P4.

Run: uv run --with pandas --with numpy --with scipy python scripts/mc_aprime_full.py
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

from mcdm_experiment import (
    load_data, impute_nan, compute_objectives, haversine_km,
    greedy_trio, COL, AHP_WEIGHTS, MIN_DIST_KM, _build_decision_matrix,
    COST,
)
try:
    from mcdm_experiment import INV
except ImportError:
    INV = set()

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# ─── Dados ────────────────────────────────────────────────────────────────────
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
col_names = list(AHP_WEIGHTS.keys())

# Matrizes
X_via, benefit = _build_decision_matrix(df_via)
valid = D_via >= MIN_DIST_KM

# Trios viáveis
print("Enumerando trios...")
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

# Fronteira A'
aprime_csv = os.path.join(RESULTS_DIR, "pareto_front_Aprime.csv")
df_front_P = pd.read_csv(aprime_csv)
front_P_set = set(
    frozenset([int(r.idx1), int(r.idx2), int(r.idx3)])
    for _, r in df_front_P.iterrows()
)

# ─── Funções auxiliares ───────────────────────────────────────────────────────
from mcdm_experiment import _norm

def compute_objs_w(w):
    """f1,f2,f3 por site em A' com pesos w (normalização 389)."""
    f1v = np.zeros(N, dtype=np.float32)
    f2v = np.zeros(N, dtype=np.float32)
    f3v = np.zeros(N, dtype=np.float32)
    for j, k in enumerate(col_names):
        col = COL[k]
        x = df_via[col].values.astype(float)
        ref = x  # normalização sobre os 389
        if k == "aspect":
            # c=0 for [90,180] (good class, lower impact); c=1 for ∉[90,180] (penalty).
            c = np.where((x >= 90) & (x <= 180), 0., 1.)
        elif k in INV:
            c = 1. - _norm(x, ref)
        elif k in COST:
            c = _norm(x, ref)
        else:
            c = _norm(x, ref)
        c = c.astype(np.float32) * w[j]
        if k in ("perm", "slope", "roads"):
            f1v += c
        elif k in ("rivers", "aspect", "coast", "protected", "wells"):
            f2v += c
        else:
            f3v += c
    return f1v, f2v, f3v

def trio_objs(f1v, f2v, f3v):
    return (f1v[trio_arr[:,0]]+f1v[trio_arr[:,1]]+f1v[trio_arr[:,2]],
            f2v[trio_arr[:,0]]+f2v[trio_arr[:,1]]+f2v[trio_arr[:,2]],
            f3v[trio_arr[:,0]]+f3v[trio_arr[:,1]]+f3v[trio_arr[:,2]])

def is_nd(i, j, k, F1, F2, F3, f1v, f2v, f3v):
    f1t=f1v[i]+f1v[j]+f1v[k]; f2t=f2v[i]+f2v[j]+f2v[k]; f3t=f3v[i]+f3v[j]+f3v[k]
    return not bool(((F1<=f1t)&(F2<=f2t)&(F3>=f3t)&((F1<f1t)|(F2<f2t)|(F3>f3t))).any())

def gap_nd(i, j, k, F1, F2, F3, f1v, f2v, f3v):
    if is_nd(i,j,k,F1,F2,F3,f1v,f2v,f3v): return 0.
    f1t=f1v[i]+f1v[j]+f1v[k]; f2t=f2v[i]+f2v[j]+f2v[k]; f3t=f3v[i]+f3v[j]+f3v[k]
    f1r=F1.max()-F1.min(); f2r=F2.max()-F2.min(); f3r=F3.max()-F3.min()
    return float(max(0., np.minimum(np.minimum((f1t-F1)/(f1r or 1),
                                               (f2t-F2)/(f2r or 1)),
                                              (F3-f3t)/(f3r or 1)).max()))

# X ajustado: colunas de custo invertidas para "maior=melhor"
X_adj = X_via.copy()
for j2, b in enumerate(benefit):
    if not b: X_adj[:, j2] = 1.0 - X_via[:, j2]

def saw(w): return (X_adj * w).sum(1)

def prom(w):
    R = np.apply_along_axis(lambda c: pd.Series(c).rank(method="average").values, 0, X_adj)
    return ((2*R - N - 1)/(N - 1)) @ w

def topsis(w, norm="minmax"):
    R = X_via.copy() if norm=="minmax" else X_via/np.maximum(np.sqrt((X_via**2).sum(0)),1e-12)
    V = R * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp = np.sqrt(((V-PIS)**2).sum(1)); dn = np.sqrt(((V-NIS)**2).sum(1))
    d = dp+dn; return np.where(d==0, 0.5, dn/d)

def vikor(w, v=0.5):
    V = X_via * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    denom = np.abs(PIS-NIS); denom[denom==0]=1e-12
    nd = np.abs(V-PIS)/denom; S=(nd*w).sum(1); R=(nd*w).max(1)
    Q=v*(S-S.min())/((S.max()-S.min()) or 1)+(1-v)*(R-R.min())/((R.max()-R.min()) or 1)
    return -Q

def argmax_trio(sc):
    st = sc[trio_arr[:,0]]+sc[trio_arr[:,1]]+sc[trio_arr[:,2]]
    return trio_arr[st.argmax()]

# Objetivos A' fixos (pesos AHP) — para Q1
f1A_fix, f2A_fix, f3A_fix = compute_objs_w(w_ahp)
F1A_fix, F2A_fix, F3A_fix = trio_objs(f1A_fix, f2A_fix, f3A_fix)

# ─── Definição dos métodos ────────────────────────────────────────────────────
METHODS = [
    # (key, norm, agg, mont, has_optimal)
    ("SAW_mm_g",    "minmax",  "linear",     "greedy",  False),
    ("SAW_mm_o",    "minmax",  "linear",     "optimal", True),
    ("TOPSIS_mm_g", "minmax",  "dist_ideal", "greedy",  False),
    ("TOPSIS_vn_g", "vector",  "dist_ideal", "greedy",  False),
    ("VIKOR_g",     "minmax",  "compromise", "greedy",  False),
    ("PROM_g",      "ranks",   "outranking", "greedy",  False),
    ("PROM_o",      "ranks",   "outranking", "optimal", True),
]

N_DRAWS = 500
SEED    = 42
ALPHAS  = [50, 200]
rng     = np.random.default_rng(SEED)

print("Rodando MC Q1 e Q2 em A'...")
t0 = time.time()
records = []
p4_counter = {a: None for a in ALPHAS}

for alpha in ALPHAS:
    print(f"  alpha={alpha}")
    rng_local = np.random.default_rng(SEED)
    for draw in range(N_DRAWS):
        w = rng_local.dirichlet(alpha * w_ahp)
        f1d, f2d, f3d = compute_objs_w(w)
        F1d, F2d, F3d = trio_objs(f1d, f2d, f3d)

        for key, norm, agg, mont, _ in METHODS:
            if norm == "minmax":     sc = saw(w) if agg=="linear" else (topsis(w,"minmax") if agg=="dist_ideal" else vikor(w))
            elif norm == "vector":   sc = topsis(w, "vector")
            else:                    sc = prom(w)

            if mont == "greedy":     idx = greedy_trio(sc, D_via)
            else:                    idx = argmax_trio(sc)
            i,j,k = idx

            # Q1: dominância em F_AHP (A' fixo)
            nd_q1 = int(is_nd(i,j,k, F1A_fix,F2A_fix,F3A_fix, f1A_fix,f2A_fix,f3A_fix))
            gp_q1 = gap_nd(i,j,k, F1A_fix,F2A_fix,F3A_fix, f1A_fix,f2A_fix,f3A_fix)
            # Q2: dominância em F_w (A' sorteado)
            nd_q2 = int(is_nd(i,j,k, F1d,F2d,F3d, f1d,f2d,f3d))
            gp_q2 = gap_nd(i,j,k, F1d,F2d,F3d, f1d,f2d,f3d)

            records.append({
                "alpha":alpha,"draw":draw,"method":key,"norm":norm,
                "agg":agg,"mont":mont,"nd_Q1":nd_q1,"gap_Q1":gp_q1,
                "nd_Q2":nd_q2,"gap_Q2":gp_q2
            })

            # P4: SAW_mm greedy dominado em Q2?
            if key=="SAW_mm_g" and nd_q2==0 and p4_counter[alpha] is None:
                gids = sorted([int(via_global[i]),int(via_global[j]),int(via_global[k])])
                p4_counter[alpha] = {
                    "alpha":alpha,"draw":draw,"w":w.tolist(),"gids":gids,
                    "gap_Q2":gp_q2,"gap_Q1":gp_q1
                }

print(f"  MC concluído em {time.time()-t0:.1f}s")

df_raw = pd.DataFrame(records)
df_raw.to_csv(os.path.join(RESULTS_DIR, "mc_aprime_full_raw.csv"), index=False)

# ─── Tarefa 2: tabela %nd por método ─────────────────────────────────────────
print("\n=== TAREFA 2: %nd por método em A' ===")
agg_t2 = (df_raw.groupby(["alpha","method","norm","agg","mont"])
          .agg(pct_Q1=("nd_Q1",lambda x:100*x.mean()),
               pct_Q2=("nd_Q2",lambda x:100*x.mean()),
               med_gap_Q1=("gap_Q1","median"),
               med_gap_Q2=("gap_Q2","median")).reset_index())
agg_t2.to_csv(os.path.join(RESULTS_DIR,"mc_aprime_full_summary.csv"),index=False)
print(agg_t2.to_string(index=False, float_format=lambda x: f"{x:.1f}"))

# ─── Tarefa 3: η² balanceado com bootstrap ───────────────────────────────────
print("\n=== TAREFA 3: η² por fator (desenho balanceado) ===")
# Usar só greedy (todos os métodos têm greedy) para balancear montagem
df_bal = df_raw[df_raw["mont"]=="greedy"].copy()
# Remover confundimento: só métodos com exatamente 1 combinação de norm×agg
# Células: norm (mm/vec/rank) × agg (linear/dist_ideal/compromise/outranking) × draws
# SAW_mm_g: mm×linear; TOPSIS_mm_g: mm×dist_ideal; TOPSIS_vn_g: vec×dist_ideal;
# VIKOR_g: mm×compromise; PROM_g: rank×outranking — 5 células distintas

print("  Células do desenho:")
cell_counts = df_bal.groupby(["alpha","norm","agg"]).size().reset_index(name="n")
print(cell_counts.to_string(index=False))

def eta2_bootstrap(df, factor, response="gap_Q2", n_boot=500, rng_seed=0):
    """η² com IC 95% por bootstrap sobre os sorteios."""
    rng_b = np.random.default_rng(rng_seed)
    def _eta2(d):
        gm = d[response].mean()
        ss_tot = ((d[response]-gm)**2).sum()
        ss_f = sum(len(g)*(g[response].mean()-gm)**2 for _,g in d.groupby(factor))
        return ss_f/ss_tot if ss_tot>0 else 0.
    point = _eta2(df)
    draws = df["draw"].unique()
    boots = []
    for _ in range(n_boot):
        bd = rng_b.choice(draws, size=len(draws), replace=True)
        sub = df[df["draw"].isin(bd)]
        boots.append(_eta2(sub))
    boots = np.array(boots)
    return point, np.percentile(boots,2.5), np.percentile(boots,97.5)

print(f"\n  {'Fator':12s}  {'η² (gap Q2)':>12}  {'IC 95%':>18}  {'η² (nd Q1)':>12}")
for factor, label in [("norm","Normalização"),("agg","Agregação")]:
    e, lo, hi = eta2_bootstrap(df_bal[df_bal["alpha"]==200], factor, "gap_Q2")
    e2,_,_ = eta2_bootstrap(df_bal[df_bal["alpha"]==200], factor, "nd_Q1")
    print(f"  {label:12s}  {e:12.4f}  [{lo:.4f}, {hi:.4f}]  {e2:12.4f}")

# Efeito aleatório (sorteio): variância dentro vs entre sorteios
print(f"\n  Variância entre sorteios vs total (proxy para efeito aleatório):")
for factor in ["norm","agg"]:
    gm = df_bal["gap_Q2"].mean()
    ss_tot = ((df_bal["gap_Q2"]-gm)**2).sum()
    ss_draw = sum(len(g)*(g["gap_Q2"].mean()-gm)**2 for _,g in df_bal.groupby("draw"))
    print(f"    η²(sorteio, {factor} marginalizado) = {ss_draw/ss_tot:.4f}")

# Interação norm × agg
df_bal["cell"] = df_bal["norm"]+"×"+df_bal["agg"]
e_cell, lo_c, hi_c = eta2_bootstrap(df_bal[df_bal["alpha"]==200], "cell", "gap_Q2")
e_n, _,_ = eta2_bootstrap(df_bal[df_bal["alpha"]==200], "norm", "gap_Q2")
e_a, _,_ = eta2_bootstrap(df_bal[df_bal["alpha"]==200], "agg", "gap_Q2")
print(f"\n  η²(norm×agg celular) = {e_cell:.4f}  =>  interação ≈ {e_cell-e_n-e_a:.4f}")

# ─── Tarefa 5: contraexemplo P4 ───────────────────────────────────────────────
print("\n=== TAREFA 5: Contraexemplo P4 ===")
for alpha in ALPHAS:
    ce = p4_counter[alpha]
    if ce:
        print(f"  α={alpha}: draw={ce['draw']}  gids={ce['gids']}  gap_Q2={ce['gap_Q2']:.4f}  gap_Q1={ce['gap_Q1']:.4f}")
        print(f"  Vetor de pesos (5 primeiros): {[f'{x:.4f}' for x in ce['w'][:5]]}")
    else:
        print(f"  α={alpha}: SAW_mm greedy NUNCA dominado em Q2 (P1 análoga válida?)")

p4_rows = [v for v in p4_counter.values() if v]
if p4_rows:
    pd.DataFrame(p4_rows).to_csv(os.path.join(RESULTS_DIR,"p4_counterexample_aprime.csv"),index=False)
    print("  Salvo em results/p4_counterexample_aprime.csv")

print("\nConcluído.")
