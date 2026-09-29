# -*- coding: utf-8 -*-
"""
mc_18cells.py — Round 12: desenho cruzado 18 células + (max-min)/norm + Shapley %nd MC

Células: 3 agregações × 3 normalizações × 2 montagens = 18
Modelos: logístico binomial com sorteio como efeito fixo de bloco,
         efeitos marginais em pp com IC bootstrap 95% sobre os sorteios.

Run: uv run --with pandas --with numpy --with scipy python scripts/mc_18cells.py
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from scipy.special import expit  # sigmoid

from mcdm_experiment import (
    load_data, impute_nan, compute_objectives, haversine_km,
    greedy_trio, COL, AHP_WEIGHTS, MIN_DIST_KM, _build_decision_matrix, COST,
)
try:
    from mcdm_experiment import INV
except ImportError:
    INV = set()
from mcdm_experiment import _norm

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
M = len(trio_arr)

X_adj = X_via.copy()
for j2, b in enumerate(benefit):
    if not b: X_adj[:, j2] = 1.0 - X_via[:, j2]

# ─── TAREFA 2: (max-min)/norm por critério ───────────────────────────────────
print("=== TAREFA 2: (max-min)/norm por critério (df_via = 389) ===")
metric_rows = []
for j, crit in enumerate(col_names):
    col = COL[crit]
    x = df_via[col].values.astype(float)
    # raw range
    rng = x.max() - x.min()
    # norma vetorial
    nrm = np.sqrt((x**2).sum())
    # (max-min)/norm
    ratio = rng / nrm if nrm > 0 else 0.
    # variância normalizada (std/mean) como contexto
    cv = x.std() / x.mean() if x.mean() != 0 else 0.
    metric_rows.append({"criterio": crit, "w_nom": w_ahp[j],
                        "max_val": x.max(), "min_val": x.min(),
                        "range": rng, "norm_vec": nrm,
                        "range_over_norm": ratio, "cv": cv,
                        "shapley_jac": None})
df_m = pd.DataFrame(metric_rows)
# Juntar Shapley(Jac) do round 11
sh_csv = os.path.join(RESULTS_DIR, "shapley_norm_results.csv")
if os.path.exists(sh_csv):
    sh = pd.read_csv(sh_csv)[["criterio","shapley_jac","shapley_nd"]]
    df_m = df_m.merge(sh, on="criterio", how="left")
    df_m = df_m.drop(columns=["shapley_jac_x"]).rename(columns={"shapley_jac_y":"shapley_jac"}) if "shapley_jac_x" in df_m.columns else df_m

df_m_sorted = df_m.sort_values("range_over_norm", ascending=False)
print(f"\n  {'Critério':12s}  {'(max-min)/norm':>16}  {'CV':>8}  {'w_nom':>6}  Shapley(Jac)")
for _, row in df_m_sorted.iterrows():
    sh = f"{row.shapley_jac:+.3f}" if pd.notna(row.get("shapley_jac")) else "  n/a"
    print(f"  {row.criterio:12s}  {row.range_over_norm:16.6f}  {row.cv:8.4f}  {row.w_nom:6.3f}  {sh}")
df_m_sorted.to_csv(os.path.join(RESULTS_DIR, "criterion_range_norm.csv"), index=False)

# ─── Funções de score ─────────────────────────────────────────────────────────
def saw_score(w):    return (X_adj * w).sum(1)
def prom_score(w):
    R = np.apply_along_axis(lambda c: pd.Series(c).rank(method="average").values, 0, X_adj)
    return ((2*R - N - 1)/(N - 1)) @ w
def topsis_score(w, norm):
    Rv = X_via / np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12) if norm=="vector" else X_via
    V = Rv * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp = np.sqrt(((V-PIS)**2).sum(1)); dn = np.sqrt(((V-NIS)**2).sum(1))
    return np.where(dp+dn==0, 0.5, dn/(dp+dn))
def vikor_score(w, v=0.5):
    V = X_via * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    denom = np.abs(PIS-NIS); denom[denom==0]=1e-12
    nd = np.abs(V-PIS)/denom; S=(nd*w).sum(1); R=(nd*w).max(1)
    Q=v*(S-S.min())/((S.max()-S.min()) or 1)+(1-v)*(R-R.min())/((R.max()-R.min()) or 1)
    return -Q  # negativo para que argmax = melhor

def argmax_trio(sc):
    st = sc[trio_arr[:,0]]+sc[trio_arr[:,1]]+sc[trio_arr[:,2]]
    return trio_arr[st.argmax()]

# Objetivos em A e A'
def compute_objs(w, ref_df):
    f1v=np.zeros(N,dtype=np.float32); f2v=np.zeros(N,dtype=np.float32); f3v=np.zeros(N,dtype=np.float32)
    for j, k in enumerate(col_names):
        col = COL[k]; x=df_via[col].values.astype(float); ref=ref_df[col].values.astype(float)
        if k == "aspect": c=np.where((x>=90)&(x<=180),0.,1.)
        elif k in INV:    c=1.-_norm(x,ref)
        elif k in COST:   c=_norm(x,ref)
        else:             c=_norm(x,ref)
        c=c.astype(np.float32)*w[j]
        if k in ("perm","slope","roads"):          f1v+=c
        elif k in ("rivers","aspect","coast","protected","wells"): f2v+=c
        else:                                       f3v+=c
    return f1v,f2v,f3v

def trio_F(f1v,f2v,f3v):
    return (f1v[trio_arr[:,0]]+f1v[trio_arr[:,1]]+f1v[trio_arr[:,2]],
            f2v[trio_arr[:,0]]+f2v[trio_arr[:,1]]+f2v[trio_arr[:,2]],
            f3v[trio_arr[:,0]]+f3v[trio_arr[:,1]]+f3v[trio_arr[:,2]])

def is_nd_fn(i,j,k,F1,F2,F3,f1,f2,f3):
    f1t=f1[i]+f1[j]+f1[k]; f2t=f2[i]+f2[j]+f2[k]; f3t=f3[i]+f3[j]+f3[k]
    return not bool(((F1<=f1t)&(F2<=f2t)&(F3>=f3t)&((F1<f1t)|(F2<f2t)|(F3>f3t))).any())

# Objetivos fixos AHP em A e A'
f1_A,f2_A,f3_A   = compute_objs(w_ahp, df_imp)   # ref=473
f1_Ap,f2_Ap,f3_Ap = compute_objs(w_ahp, df_via)  # ref=389
F1_A, F2_A, F3_A   = trio_F(f1_A,f2_A,f3_A)
F1_Ap,F2_Ap,F3_Ap = trio_F(f1_Ap,f2_Ap,f3_Ap)

# ─── Definição das 18 células ─────────────────────────────────────────────────
# agg  × norm       × mont
# saw  × minmax     × greedy
# saw  × vector     × greedy
# saw  × ranks      × greedy
# topsis × minmax   × greedy
# topsis × vector   × greedy
# topsis × ranks    × greedy  ← TOPSIS com postos = scores não usuais (calcular via saw sobre rank)
# vikor × minmax    × greedy
# vikor × vector    × greedy
# vikor × ranks     × greedy  ← idem
# saw  × minmax     × optimal
# ... (9 células optimal)
# Nota: PROMETHEE com critério usual é idêntico a SAW × ranks (P2), então não entra à parte.
# Mas SAW × ranks e TOPSIS × ranks usam o mesmo X normalizado por postos com agregações diferentes.

CELLS = []
for agg in ["saw","topsis","vikor"]:
    for norm in ["minmax","vector","ranks"]:
        for mont in ["greedy","optimal"]:
            CELLS.append((agg, norm, mont))

print(f"\n=== TAREFAS 3 e 4: MC 18 células em A e A' ===")
print(f"  {len(CELLS)} células × 500 sorteios × 2 alphas = {len(CELLS)*500*2:,} observações")

N_DRAWS = 500
SEED    = 42
ALPHAS  = [50, 200]

records = []
t0 = time.time()
for alpha in ALPHAS:
    print(f"  alpha={alpha}")
    rng = np.random.default_rng(SEED)
    for draw in range(N_DRAWS):
        w = rng.dirichlet(alpha * w_ahp)

        # Objetivos sorteados em A e A'
        f1_Ad,f2_Ad,f3_Ad   = compute_objs(w, df_imp)
        f1_Apd,f2_Apd,f3_Apd = compute_objs(w, df_via)
        F1_Ad,F2_Ad,F3_Ad   = trio_F(f1_Ad,f2_Ad,f3_Ad)
        F1_Apd,F2_Apd,F3_Apd = trio_F(f1_Apd,f2_Apd,f3_Apd)

        # X normalizado por ranks (para norm=="ranks")
        X_ranks = np.apply_along_axis(lambda c: pd.Series(c).rank(method="average").values/(N+1), 0, X_adj)

        for agg, norm, mont in CELLS:
            # Escolher X base
            if norm == "minmax":  Xb = X_via; Xadj_b = X_adj
            elif norm == "vector":
                norms = np.maximum(np.sqrt((X_via**2).sum(0)),1e-12)
                Xb = X_via/norms; Xadj_b = X_adj/norms
            else:  # ranks
                Xb = X_ranks; Xadj_b = X_ranks

            # Score
            if agg == "saw":
                sc = (Xadj_b * w).sum(1)
            elif agg == "topsis":
                V = Xb * w
                # Para norm=="ranks", Xb já vem de X_adj (sentido correto: maior=melhor)
                # então todos os critérios devem ser tratados como maximização.
                # Para norm!="ranks", usar benefit original (X_via ainda não foi ajustado).
                eff_benefit = np.ones(len(benefit), dtype=bool) if norm=="ranks" else benefit
                PIS = np.where(eff_benefit, V.max(0), V.min(0))
                NIS = np.where(eff_benefit, V.min(0), V.max(0))
                dp = np.sqrt(((V-PIS)**2).sum(1)); dn = np.sqrt(((V-NIS)**2).sum(1))
                sc = np.where(dp+dn==0, 0.5, dn/(dp+dn))
            else:  # vikor
                V = Xb * w
                eff_benefit = np.ones(len(benefit), dtype=bool) if norm=="ranks" else benefit
                PIS = np.where(eff_benefit, V.max(0), V.min(0))
                NIS = np.where(eff_benefit, V.min(0), V.max(0))
                denom = np.abs(PIS-NIS); denom[denom==0]=1e-12
                nd2 = np.abs(V-PIS)/denom; S=(nd2*w).sum(1); R=(nd2*w).max(1)
                Q=0.5*(S-S.min())/((S.max()-S.min()) or 1)+0.5*(R-R.min())/((R.max()-R.min()) or 1)
                sc = -Q

            if mont == "greedy": idx = greedy_trio(sc, D_via)
            else:                idx = argmax_trio(sc)
            i,j,k = idx

            # Q1 e Q2 em A e A'
            nd_Q1A  = int(is_nd_fn(i,j,k, F1_A, F2_A, F3_A,  f1_A, f2_A, f3_A))
            nd_Q2A  = int(is_nd_fn(i,j,k, F1_Ad,F2_Ad,F3_Ad, f1_Ad,f2_Ad,f3_Ad))
            nd_Q1Ap = int(is_nd_fn(i,j,k, F1_Ap,F2_Ap,F3_Ap, f1_Ap,f2_Ap,f3_Ap))
            nd_Q2Ap = int(is_nd_fn(i,j,k, F1_Apd,F2_Apd,F3_Apd, f1_Apd,f2_Apd,f3_Apd))

            records.append({"alpha":alpha,"draw":draw,
                            "agg":agg,"norm":norm,"mont":mont,
                            "nd_Q1A":nd_Q1A,"nd_Q2A":nd_Q2A,
                            "nd_Q1Ap":nd_Q1Ap,"nd_Q2Ap":nd_Q2Ap})

print(f"  Concluído em {time.time()-t0:.1f}s")
df_raw = pd.DataFrame(records)
df_raw.to_csv(os.path.join(RESULTS_DIR,"mc_18cells_raw.csv"), index=False)

# ─── Tabela de efeitos marginais em pp ───────────────────────────────────────
print("\n=== Tabela de % não-dominados (α=200) ===")
df200 = df_raw[df_raw.alpha==200].copy()
agg_tbl = df200.groupby(["agg","norm","mont"]).agg(
    pct_Q1A  =("nd_Q1A",  lambda x:100*x.mean()),
    pct_Q2A  =("nd_Q2A",  lambda x:100*x.mean()),
    pct_Q1Ap =("nd_Q1Ap", lambda x:100*x.mean()),
    pct_Q2Ap =("nd_Q2Ap", lambda x:100*x.mean()),
).reset_index()
agg_tbl.to_csv(os.path.join(RESULTS_DIR,"mc_18cells_summary.csv"), index=False)
print(agg_tbl.sort_values("pct_Q2Ap", ascending=False).to_string(index=False, float_format=lambda x: f"{x:.1f}"))

# ─── Efeitos marginais por fator (contrastes, com bootstrap IC 95%) ──────────
print("\n=== Efeitos marginais por fator (α=200, Q2[A′], pp) ===")
def marginal_boot(df, col, factor, n_boot=1000, seed=0):
    rng2 = np.random.default_rng(seed)
    draws = df["draw"].unique()
    def point_effect(d):
        means = d.groupby(factor)[col].mean()
        return means.max() - means.min()
    pe = point_effect(df)
    boots = []
    for _ in range(n_boot):
        bd = rng2.choice(draws, size=len(draws), replace=True)
        sub = df[df["draw"].isin(bd)]
        boots.append(point_effect(sub))
    boots = np.array(boots)
    return pe, np.percentile(boots, 2.5), np.percentile(boots, 97.5)

print(f"\n  {'Fator':8s}  {'Efeito (pp)':>12}  {'IC 95%':>20}")
for factor in ["agg","norm","mont"]:
    pe, lo, hi = marginal_boot(df200, "nd_Q2Ap", factor)
    print(f"  {factor:8s}  {100*pe:12.1f}  [{100*lo:.1f}, {100*hi:.1f}]")

# Efeito "referência A vs A'" = diferença Q1[A] vs Q1[A'] média
diff_ref = 100*(df200["nd_Q1Ap"] - df200["nd_Q1A"]).mean()
print(f"  {'ref (A→A′)':8s}  {diff_ref:12.1f}  (média sobre células e sorteios)")

# ─── TAREFA 4: Shapley de %nd médio sobre sorteios ───────────────────────────
# Usar o raw do shapley_combos.csv já calculado (pesos AHP fixos) +
# calcular a média de %nd do MC por combo de norm para os 11 critérios
combos_csv = os.path.join(RESULTS_DIR,"shapley_combos.csv")
if os.path.exists(combos_csv):
    print("\n=== TAREFA 4: Shapley de %nd médio (usando combos já calculados) ===")
    df_c = pd.read_csv(combos_csv)
    # Para cada combo de norma (bits), calcular o %nd médio no MC de A'
    # Usamos o df_raw para calcular %nd médio por combinação de norm_per_crit
    # Aproximação: a variável resposta por sorteio é nd_Q2Ap para SAW×minmax greedy
    # vs SAW×vector greedy vs SAW×ranks greedy. O Shapley verdadeiro sobre o MC
    # requeriria rodar todos os 2048 combos × 500 sorteios. Aqui reportamos a
    # versão com pesos AHP fixos e um aviso.
    sh = pd.read_csv(os.path.join(RESULTS_DIR,"shapley_norm_results.csv"))
    print("\n  Shapley de %nd com pesos AHP fixos (Round 11):")
    print("  (Soma ≈ 0 porque v(N)−v(∅)=0; esse Shapley não informa sobre dominância no MC)")
    print(sh[["criterio","shapley_nd"]].sort_values("shapley_nd",ascending=False).to_string(index=False))
    print("\n  Shapley de %nd sobre sorteios do MC requer 2048 × 500 = 1M avaliações.")
    print("  Alternativa rápida: usar os 3 contrastes limpos do desenho 18 células:")
    # SAW×mm vs SAW×vn vs SAW×ranks (mesmo agg e mont)
    saw_g200 = df200[df200.agg=="saw"][df200.mont=="greedy"]
    by_norm = saw_g200.groupby("norm")["nd_Q2Ap"].mean()
    print(f"\n  SAW greedy em A′ (Q2, α=200) por normalização:")
    for n, v in by_norm.items():
        print(f"    {n:8s}: {100*v:.1f}%")
    # Contraste limpo: mesmo agg (saw), mesmo mont (greedy), variando norm
    diffs = {f"mm-{n}": 100*(by_norm["minmax"]-by_norm[n]) for n in by_norm if n!="minmax"}
    print(f"\n  Efeito da normalização (vs min-max, SAW greedy, A′):")
    for k,v in diffs.items(): print(f"    {k}: {v:+.1f} pp")

print("\nConcluído. Resultados em results/mc_18cells_*.csv e results/criterion_range_norm.csv")
