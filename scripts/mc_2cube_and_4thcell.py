# -*- coding: utf-8 -*-
"""
mc_2cube_and_4thcell.py — DEPRECATED. DO NOT USE.

This script has TWO known bugs confirmed on 2026-11-01 (DEV-E7-001):
  1. SAW/vector scorer uses X_via/norms instead of X_adj/norms.
     Cost criteria are treated as benefit criteria → portfolios always dominated.
  2. Q2 check uses float32 objectives without self-exclusion → massive false positives.
The two bugs cancel in the aggregate Q2 rate (coincidence verified by diagnose_q2_rates.py).

USE INSTEAD: mc_2cube_fixed.py (correct scorer + pareto_utils float64 Q2 check)
             scoring.py (canonical SAW/TOPSIS scorers, single source of truth)
"""
raise RuntimeError(
    "mc_2cube_and_4thcell.py is DEPRECATED (DEV-E7-001). "
    "Use mc_2cube_fixed.py or scoring.py instead."
)

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

from mcdm_experiment import (
    load_data, impute_nan, compute_objectives,
    haversine_km, greedy_trio, COL, AHP_WEIGHTS, MIN_DIST_KM,
    _build_decision_matrix, COST, _norm,
)
try:
    from mcdm_experiment import INV
except ImportError:
    INV = set()

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# ─── Dados ────────────────────────────────────────────────────────────────────
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
X_via, benefit = _build_decision_matrix(df_via)
valid = D_via >= MIN_DIST_KM

trio_arr = []
for i in range(N):
    for j in range(i+1, N):
        if not valid[i,j]: continue
        for k in range(j+1, N):
            if not valid[i,k] or not valid[j,k]: continue
            trio_arr.append((i,j,k))
trio_arr = np.array(trio_arr, dtype=np.int32)

X_adj = X_via.copy()
for j2, b in enumerate(benefit):
    if not b: X_adj[:, j2] = 1. - X_via[:, j2]

# ─── Funções de score e objetivos ─────────────────────────────────────────────
def saw_sc(w, norm="minmax"):
    if norm == "minmax":
        return (X_adj * w).sum(1)
    elif norm == "vector":
        norms = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)
        return ((X_via/norms) * w).sum(1)  # NB: SAW vetorial usa X_via não adj

def topsis_sc(w, norm="minmax"):
    Xb = X_via if norm=="minmax" else X_via/np.maximum(np.sqrt((X_via**2).sum(0)),1e-12)
    V = Xb * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp = np.sqrt(((V-PIS)**2).sum(1)); dn = np.sqrt(((V-NIS)**2).sum(1))
    return np.where(dp+dn==0, 0.5, dn/(dp+dn))

def argmax_trio_fn(sc):
    st = sc[trio_arr[:,0]]+sc[trio_arr[:,1]]+sc[trio_arr[:,2]]
    return trio_arr[st.argmax()]

def compute_objs_ref(w, ref_df):
    """Objetivos ponderados com normalização sobre ref_df."""
    f1=np.zeros(N,dtype=np.float32); f2=np.zeros(N,dtype=np.float32); f3=np.zeros(N,dtype=np.float32)
    for j, k in enumerate(col_names):
        col = COL[k]; x=df_via[col].values.astype(float); ref=ref_df[col].values.astype(float)
        if k=="aspect": c=np.where((x>=90)&(x<=180),0.,1.)
        elif k in INV:  c=1.-_norm(x,ref)
        elif k in COST: c=_norm(x,ref)
        else:           c=_norm(x,ref)
        c=c.astype(np.float32)*w[j]
        if k in ("perm","slope","roads"):           f1+=c
        elif k in ("rivers","aspect","coast","protected","wells"): f2+=c
        else:                                        f3+=c
    return f1,f2,f3

def trio_F(f1,f2,f3):
    return (f1[trio_arr[:,0]]+f1[trio_arr[:,1]]+f1[trio_arr[:,2]],
            f2[trio_arr[:,0]]+f2[trio_arr[:,1]]+f2[trio_arr[:,2]],
            f3[trio_arr[:,0]]+f3[trio_arr[:,1]]+f3[trio_arr[:,2]])

def is_nd_fn(i,j,k,F1,F2,F3,f1,f2,f3):
    f1t=f1[i]+f1[j]+f1[k]; f2t=f2[i]+f2[j]+f2[k]; f3t=f3[i]+f3[j]+f3[k]
    return not bool(((F1<=f1t)&(F2<=f2t)&(F3>=f3t)&((F1<f1t)|(F2<f2t)|(F3>f3t))).any())

# Objetivos fixos AHP
f1_A,f2_A,f3_A   = compute_objs_ref(w_ahp, df_imp)   # ref=473 (espaço A)
f1_Ap,f2_Ap,f3_Ap = compute_objs_ref(w_ahp, df_via)  # ref=389 (espaço A')
F1_A, F2_A, F3_A   = trio_F(f1_A,f2_A,f3_A)
F1_Ap,F2_Ap,F3_Ap = trio_F(f1_Ap,f2_Ap,f3_Ap)

N_DRAWS = 500
SEED    = 42
ALPHAS  = [50, 200]

# ─── Tarefa 2: 2³ balanceado — SAW e TOPSIS, mm e vec, greedy e ótimo ─────────
CELLS_CUBE = [(agg, norm, mont)
              for agg in ["saw","topsis"]
              for norm in ["minmax","vector"]
              for mont in ["greedy","optimal"]]

# ─── Tarefa 3: quarta casa 2×2 — método ref=473, avaliador A' ─────────────────
# Células existentes: método ref=389, avaliador A  (mc_18cells_raw.csv)
#                    método ref=389, avaliador A'  (mc_18cells_raw.csv)
# Falta:             método ref=473, avaliador A'  (esta tarefa)
# Já existe:         método ref=473, avaliador A   (mc_q2v2_summary.csv)
# Usamos SAW×mm×greedy e TOPSIS×mm×greedy como representantes

print("Carregando dados...")
print(f"Rodando {len(CELLS_CUBE)} células do 2³ + quarta casa, {N_DRAWS}×{len(ALPHAS)} sorteios")

records   = []  # 2³
records_4 = []  # quarta casa

t0 = time.time()
for alpha in ALPHAS:
    print(f"  alpha={alpha}")
    rng = np.random.default_rng(SEED)
    for draw in range(N_DRAWS):
        w = rng.dirichlet(alpha * w_ahp)

        # Objetivos sorteados ref=389 (A') e ref=473 (A)
        f1_Apd,f2_Apd,f3_Apd = compute_objs_ref(w, df_via)
        f1_Ad, f2_Ad, f3_Ad   = compute_objs_ref(w, df_imp)
        F1_Apd,F2_Apd,F3_Apd = trio_F(f1_Apd,f2_Apd,f3_Apd)
        F1_Ad, F2_Ad, F3_Ad   = trio_F(f1_Ad, f2_Ad, f3_Ad)

        for agg, norm, mont in CELLS_CUBE:
            if agg == "saw":     sc = saw_sc(w, norm)
            else:                sc = topsis_sc(w, norm)

            if mont == "greedy": idx = greedy_trio(sc, D_via)
            else:                idx = argmax_trio_fn(sc)
            i,j,k = idx

            # Q1 e Q2 em A e A' (método usa ref=389 por construção do score)
            nd_Q1A  = int(is_nd_fn(i,j,k,F1_A,F2_A,F3_A,f1_A,f2_A,f3_A))
            nd_Q2A  = int(is_nd_fn(i,j,k,F1_Ad,F2_Ad,F3_Ad,f1_Ad,f2_Ad,f3_Ad))
            nd_Q1Ap = int(is_nd_fn(i,j,k,F1_Ap,F2_Ap,F3_Ap,f1_Ap,f2_Ap,f3_Ap))
            nd_Q2Ap = int(is_nd_fn(i,j,k,F1_Apd,F2_Apd,F3_Apd,f1_Apd,f2_Apd,f3_Apd))
            records.append({"alpha":alpha,"draw":draw,"agg":agg,"norm":norm,"mont":mont,
                            "nd_Q1A":nd_Q1A,"nd_Q2A":nd_Q2A,"nd_Q1Ap":nd_Q1Ap,"nd_Q2Ap":nd_Q2Ap})

        # Quarta casa: SAW×mm com score ref=473
        # O score ref=473 usa X_adj construído de df_imp (todos os 473)
        # Mas df_imp tem 473 linhas e X_via tem 389 — precisamos construir
        # o score sobre os 389 mas com normalização dos 473.
        # Aqui, construímos os scores usando os objetivos do MC Q2v2 como proxy:
        # usamos os pesos w para fazer SAW com normalização dos 473.
        for agg_4, norm_4, mont_4 in [("saw","minmax","greedy"),
                                       ("saw","minmax","optimal"),
                                       ("topsis","minmax","greedy"),
                                       ("topsis","minmax","optimal")]:
            # Score com normalização 473: usa X_imp_adj[viáveis]
            # _build_decision_matrix usa os valores de df já normalizados
            # Aqui fazemos a normalização manualmente para os 389 sites com ref=473
            Xb473 = np.zeros((N, len(col_names)), dtype=np.float32)
            for jj, crit in enumerate(col_names):
                col = COL[crit]
                x_via = df_via[col].values.astype(float)
                x_all = df_imp[col].values.astype(float)
                mn, mx = x_all.min(), x_all.max(); rng_c = mx-mn or 1.
                # min-max sobre 473, avaliado nos 389
                xnorm = (x_via - mn) / rng_c
                Xb473[:, jj] = xnorm.astype(np.float32)
            # Ajustar sentido (custo: 1-x para maximizar)
            Xadj473 = Xb473.copy()
            for jj, b in enumerate(benefit):
                if not b: Xadj473[:,jj] = 1. - Xb473[:,jj]

            if agg_4 == "saw":
                sc4 = (Xadj473 * w).sum(1)
            else:
                V = Xb473 * w
                PIS = np.where(benefit, V.max(0), V.min(0))
                NIS = np.where(benefit, V.min(0), V.max(0))
                dp = np.sqrt(((V-PIS)**2).sum(1)); dn = np.sqrt(((V-NIS)**2).sum(1))
                sc4 = np.where(dp+dn==0, 0.5, dn/(dp+dn))

            if mont_4 == "greedy": idx4 = greedy_trio(sc4, D_via)
            else:                  idx4 = argmax_trio_fn(sc4)
            i4,j4,k4 = idx4

            # Avaliar em A' (avaliador ref=389)
            nd_Q1Ap4 = int(is_nd_fn(i4,j4,k4,F1_Ap,F2_Ap,F3_Ap,f1_Ap,f2_Ap,f3_Ap))
            nd_Q2Ap4 = int(is_nd_fn(i4,j4,k4,F1_Apd,F2_Apd,F3_Apd,f1_Apd,f2_Apd,f3_Apd))
            records_4.append({"alpha":alpha,"draw":draw,"agg":agg_4,"norm":norm_4,"mont":mont_4,
                              "ref_method":473,"nd_Q1Ap":nd_Q1Ap4,"nd_Q2Ap":nd_Q2Ap4})

print(f"  Concluído em {time.time()-t0:.1f}s")

df_cube = pd.DataFrame(records)
df_4th  = pd.DataFrame(records_4)
df_cube.to_csv(os.path.join(RESULTS_DIR,"mc_2cube_raw.csv"), index=False)
df_4th.to_csv(os.path.join(RESULTS_DIR,"mc_4thcell_raw.csv"), index=False)

# ─── Tabela 2³ ────────────────────────────────────────────────────────────────
print("\n=== 2³ balanceado — Q2[A'], α=200 ===")
df200c = df_cube[df_cube.alpha==200]
tbl = df200c.groupby(["agg","norm","mont"]).agg(
    Q1A =("nd_Q1A",  lambda x:100*x.mean()),
    Q2A =("nd_Q2A",  lambda x:100*x.mean()),
    Q1Ap=("nd_Q1Ap", lambda x:100*x.mean()),
    Q2Ap=("nd_Q2Ap", lambda x:100*x.mean()),
).reset_index()
print(tbl.to_string(index=False, float_format=lambda x: f"{x:.1f}"))

# ─── Efeitos principais e interação norm×mont (bootstrap pareado) ──────────────
print("\n=== Efeitos principais e interação norm×mont (α=200, Q2[A'], 2³) ===")
rng2 = np.random.default_rng(0)
draws = df200c["draw"].unique()

def marginals_2cube(d):
    pivot = d.groupby(["agg","norm","mont"])["nd_Q2Ap"].mean().reset_index()
    # Efeito norm: média sobre (agg,mont)
    e_norm = {n: pivot[pivot.norm==n]["nd_Q2Ap"].mean() for n in ["minmax","vector"]}
    e_mont = {m: pivot[pivot.mont==m]["nd_Q2Ap"].mean() for m in ["greedy","optimal"]}
    # Interação: montagem dentro de cada norm
    mont_in_mm  = pivot[pivot.norm=="minmax"].groupby("mont")["nd_Q2Ap"].mean()
    mont_in_vec = pivot[pivot.norm=="vector"].groupby("mont")["nd_Q2Ap"].mean()
    eff_mm_vec  = 100*(e_norm["minmax"]-e_norm["vector"])
    eff_opt_gre = 100*(e_mont["optimal"]-e_mont["greedy"])
    int_mont_mm  = 100*(mont_in_mm["optimal"]-mont_in_mm["greedy"])  if len(mont_in_mm)==2 else np.nan
    int_mont_vec = 100*(mont_in_vec["optimal"]-mont_in_vec["greedy"]) if len(mont_in_vec)==2 else np.nan
    return eff_mm_vec, eff_opt_gre, int_mont_mm, int_mont_vec

eff0 = marginals_2cube(df200c)
boots = [marginals_2cube(df200c[df200c.draw.isin(rng2.choice(draws,size=len(draws),replace=True))])
         for _ in range(1000)]
boots = np.array(boots)
labels = ["norm (mm-vec)", "mont (opt-gre)", "mont DENTRO mm", "mont DENTRO vec"]
print(f"\n  {'Efeito':22s}  {'pp':>8}  {'IC 95%':>20}")
for i,(lab,val) in enumerate(zip(labels, eff0)):
    lo,hi = np.percentile(boots[:,i],[2.5,97.5])
    print(f"  {lab:22s}  {val:8.1f}  [{lo:.1f}, {hi:.1f}]")

# ─── Quarta casa 2×2 ──────────────────────────────────────────────────────────
print("\n=== Quarta casa 2×2: ref método {473,389} × avaliador {A,A'} ===")
print("  (SAW×mm×greedy como representante)")
df200_4 = df_4th[df_4th.alpha==200]
saw_473_g = df200_4[(df_4th.agg=="saw") & (df_4th.mont=="greedy")]
saw_473_o = df200_4[(df_4th.agg=="saw") & (df_4th.mont=="optimal")]

# ref=389, avaliador A' — do mc_18cells_raw.csv
raw_18 = pd.read_csv(os.path.join(RESULTS_DIR,"mc_18cells_raw.csv"))
saw_389_g = raw_18[(raw_18.alpha==200) & (raw_18.agg=="saw") & (raw_18.norm=="minmax") & (raw_18.mont=="greedy")]
saw_389_o = raw_18[(raw_18.alpha==200) & (raw_18.agg=="saw") & (raw_18.norm=="minmax") & (raw_18.mont=="optimal")]

# ref=473, avaliador A — do mc_q2v2
q2v2 = pd.read_csv(os.path.join(RESULTS_DIR,"mc_q2v2_summary.csv"))
saw473_A_g  = q2v2[(q2v2.method=="SAW_s1") & (q2v2.variant=="greedy") & (q2v2.alpha==200)]
saw473_A_o  = q2v2[(q2v2.method=="SAW_s1") & (q2v2.variant=="optimal") & (q2v2.alpha==200)]

print(f"\n  Método SAW×mm, α=200, Q2:")
print(f"  {'Ref método':12s}  {'Avaliador':10s}  {'greedy':>8}  {'ótimo':>8}")
print(f"  {'473':12s}  {'A':10s}  {saw473_A_g['pct_nd_Q2'].values[0] if len(saw473_A_g) else '?':8}  {saw473_A_o['pct_nd_Q2'].values[0] if len(saw473_A_o) else '?':8}")
q1ap_473g = saw_473_g["nd_Q2Ap"].mean()*100 if len(saw_473_g) else float("nan")
q1ap_473o = saw_473_o["nd_Q2Ap"].mean()*100 if len(saw_473_o) else float("nan")
q2ap_389g = saw_389_g["nd_Q2Ap"].mean()*100 if len(saw_389_g) else float("nan")
q2ap_389o = saw_389_o["nd_Q2Ap"].mean()*100 if len(saw_389_o) else float("nan")
print(f"  {'473':12s}  {'A′':10s}  {q1ap_473g:8.1f}  {q1ap_473o:8.1f}")
print(f"  {'389':12s}  {'A':10s}  {saw_389_g['nd_Q1A'].mean()*100:.1f}    (Q1[A])      {saw_389_o['nd_Q1A'].mean()*100:.1f}")
print(f"  {'389':12s}  {'A′':10s}  {q2ap_389g:8.1f}  {q2ap_389o:8.1f}")
print()
print("  Efeito 'excluir inviáveis antes de normalizar' (comparar ref 473 vs 389 com mesmo avaliador A'):")
diff_g = q2ap_389g - q1ap_473g
diff_o = q2ap_389o - q1ap_473o
print(f"    greedy: {q2ap_389g:.1f}% (389) - {q1ap_473g:.1f}% (473) = {diff_g:+.1f} pp")
print(f"    ótimo:  {q2ap_389o:.1f}% (389) - {q1ap_473o:.1f}% (473) = {diff_o:+.1f} pp")

print("\nSalvo em results/mc_2cube_raw.csv e mc_4thcell_raw.csv")
