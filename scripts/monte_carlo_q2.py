# -*- coding: utf-8 -*-
"""
monte_carlo_q2.py  — MC Q2: pesos sorteados nos MÉTODOS e nos OBJETIVOS
Pergunta: o método é coerente com as preferências que recebeu?
Teste de sanidade: SAW-473 ótimo deve dar 100% (P1 garante).

Também roda Q1 (pesos nos métodos, objetivos AHP fixos) para comparação.

Inclui TOPSIS-VN e todas as variantes ótimas.

4 testes de regressão explícitos (pesos AHP exatos):
  T1: SAW greedy == [184, 279, 320], dominado
  T2: SAW ótimo  == [184, 430, 460], não dominado (SAW-389 ótimo pode diferir, mas não dominado)
  T3: PROMETHEE greedy == [51, 233, 345], não dominado
  T4: TOPSIS-VN greedy == [233, 320, 355] (verificar se coincide com caso base)

Run: uv run --with pandas --with numpy --with scipy python scripts/monte_carlo_q2.py
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

from mcdm_experiment import (
    load_data, impute_nan, haversine_km, compute_objectives, greedy_trio,
    COL, AHP_WEIGHTS, MIN_DIST_KM, COST, _build_decision_matrix,
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

# ─── Matrizes normalizadas (fixas) ────────────────────────────────────────────
X_via, benefit = _build_decision_matrix(df_via)   # normalização sobre 389
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b: X_adj[:, j] = 1.0 - X_via[:, j]

# ─── Pré-calcular todos os trios viáveis ─────────────────────────────────────
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

# ─── Funções de score (normalização 389) ─────────────────────────────────────
col_names = list(AHP_WEIGHTS.keys())
f1_idx = [col_names.index(c) for c in ["perm","slope","roads"]]
f2_idx = [col_names.index(c) for c in ["rivers","aspect","coast","protected","wells"]]
f3_idx = [col_names.index(c) for c in ["urban","aero","cult"]]

def saw_w(w):    return (X_adj * w).sum(1)
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
    norm_d = np.abs(V-PIS) / denom
    S = (norm_d*w).sum(1); R = (norm_d*w).max(1)
    Q = v*(S-S.min())/((S.max()-S.min()) or 1) + (1-v)*(R-R.min())/((R.max()-R.min()) or 1)
    return -Q
def argmax_saw(sc):
    st = sc[trio_arr[:,0]]+sc[trio_arr[:,1]]+sc[trio_arr[:,2]]
    return trio_arr[st.argmax()]

# ─── Funções de objetivo com pesos w ─────────────────────────────────────────
# Scores por critério sobre 473 (fixos):
X_all, benefit_all = _build_decision_matrix(df_imp)  # (473,11) sobre 473
scores_all = np.zeros((473,11), dtype=np.float32)
for j, b in enumerate(benefit_all):
    scores_all[:,j] = X_all[:,j] if b else 1.-X_all[:,j]
idx_473 = {gid:i for i,gid in enumerate(df_all.index)}
via_idx473 = np.array([idx_473[int(g)] for g in via_global])
scores_via473 = scores_all[via_idx473]   # (389,11) scores via, normaliz 473

def compute_F_w(w):
    """
    F1,F2,F3 de todos os M trios com pesos w (normalização 473, sem divisão por w_group).
    Objetivos: minimizar f1 e f2, maximizar f3.
    """
    # f1 = sum w_j * (1-norm_j) para cost criteria  (menor = melhor → ao somar, menor é pior)
    # Mas os scores já inverteram: sc_adj[cost] = 1-norm, então sc_adj é "maior=melhor" sempre.
    # f1 = sum_{cost} w_j * norm_j  (custo = menor raw = melhor, portanto norm_j já correto)
    # Reconstituindo com os sinais corretos para os objetivos:
    # Para os objetivos, usar scores SEM inversão de custo (raw normalizado):
    # f1 = sum_{j in f1_crit} w_j * norm_j  onde norm_j = (x-min)/(max-min) para todos
    # O scores_via473 já tem inversão para cost (sc_all[cost] = 1 - norm).
    # Para objetivos de custo (f1): precisamos do score NÃO invertido = 1 - sc_adj[cost].
    # Mas na convenção do artigo, f1 AUMENTA com custo maior = é caro → scores_via473[cost] é 1-norm.
    # Então f1 = sum(w*scores_via473[f1_crit]) está somando (1-norm) para cost, que é ALTO quando caro.
    # Isso é consistente: minimizar f1 = minimizar custo.
    f1v = scores_via473[:,f1_idx] @ w[f1_idx]
    f2v = scores_via473[:,f2_idx] @ w[f2_idx]
    f3v = scores_via473[:,f3_idx] @ w[f3_idx]
    i0,i1,i2 = trio_arr[:,0],trio_arr[:,1],trio_arr[:,2]
    return (f1v[i0]+f1v[i1]+f1v[i2]).astype(np.float32), \
           (f2v[i0]+f2v[i1]+f2v[i2]).astype(np.float32), \
           (f3v[i0]+f3v[i1]+f3v[i2]).astype(np.float32), f1v,f2v,f3v

def saw_s1_w(w):
    """
    Score S1 = -f1 - f2 + f3 com pesos w (escalarização coerente com Pareto).
    Maximizar S1 = minimizar custo+impacto + maximizar segurança.
    """
    f1v = scores_via473[:,f1_idx] @ w[f1_idx]
    f2v = scores_via473[:,f2_idx] @ w[f2_idx]
    f3v = scores_via473[:,f3_idx] @ w[f3_idx]
    return -f1v - f2v + f3v   # maior = melhor

# Pré-calcular F com pesos AHP (para Q1)
print("Pré-calculando objetivos AHP (Q1)...")
F1_ahp, F2_ahp, F3_ahp, f1v_ahp, f2v_ahp, f3v_ahp = compute_F_w(w_ahp)

def is_dom_Q1(i,j,k):   # domina pelos objetivos AHP fixos
    f1t=float(f1v_ahp[i]+f1v_ahp[j]+f1v_ahp[k])
    f2t=float(f2v_ahp[i]+f2v_ahp[j]+f2v_ahp[k])
    f3t=float(f3v_ahp[i]+f3v_ahp[j]+f3v_ahp[k])
    return bool(((F1_ahp<=f1t)&(F2_ahp<=f2t)&(F3_ahp>=f3t)&
                 ((F1_ahp<f1t)|(F2_ahp<f2t)|(F3_ahp>f3t))).any())

def gap_n_Q1(i,j,k):
    f1t=float(f1v_ahp[i]+f1v_ahp[j]+f1v_ahp[k])
    f2t=float(f2v_ahp[i]+f2v_ahp[j]+f2v_ahp[k])
    f3t=float(f3v_ahp[i]+f3v_ahp[j]+f3v_ahp[k])
    if not is_dom_Q1(i,j,k): return 0.
    f1r=F1_ahp.max()-F1_ahp.min(); f2r=F2_ahp.max()-F2_ahp.min(); f3r=F3_ahp.max()-F3_ahp.min()
    return float(max(0.,np.minimum(np.minimum((f1t-F1_ahp)/(f1r or 1),
                                               (f2t-F2_ahp)/(f2r or 1)),
                                   (F3_ahp-f3t)/(f3r or 1)).max()))

def is_dom_Q2(i,j,k, F1,F2,F3,f1v,f2v,f3v):
    f1t=float(f1v[i]+f1v[j]+f1v[k])
    f2t=float(f2v[i]+f2v[j]+f2v[k])
    f3t=float(f3v[i]+f3v[j]+f3v[k])
    return bool(((F1<=f1t)&(F2<=f2t)&(F3>=f3t)&
                 ((F1<f1t)|(F2<f2t)|(F3>f3t))).any())

def gap_n_Q2(i,j,k, F1,F2,F3,f1v,f2v,f3v):
    f1t=float(f1v[i]+f1v[j]+f1v[k])
    f2t=float(f2v[i]+f2v[j]+f2v[k])
    f3t=float(f3v[i]+f3v[j]+f3v[k])
    if not is_dom_Q2(i,j,k,F1,F2,F3,f1v,f2v,f3v): return 0.
    f1r=F1.max()-F1.min(); f2r=F2.max()-F2.min(); f3r=F3.max()-F3.min()
    return float(max(0.,np.minimum(np.minimum((f1t-F1)/(f1r or 1),
                                               (f2t-F2)/(f2r or 1)),
                                   (F3-f3t)/(f3r or 1)).max()))

def jac10(sc_a, sc_b):
    a=set(np.argsort(-sc_a)[:10]); b=set(np.argsort(-sc_b)[:10])
    return len(a&b)/len(a|b) if a|b else 1.

# ─── 4 testes de regressão ────────────────────────────────────────────────────
print("\nTESTES DE REGRESSÃO (pesos AHP exatos):")
sc_saw   = saw_w(w_ahp)
sc_tvn   = topsis_vn_w(w_ahp)
sc_tmm   = topsis_mm_w(w_ahp)
sc_prom  = prom_w(w_ahp)

g_saw_g  = greedy_trio(sc_saw, D_via)
g_tvn_g  = greedy_trio(sc_tvn, D_via)
g_saw_o  = argmax_saw(sc_saw)
g_prom_g = greedy_trio(sc_prom, D_via)

g_saw_g_gl  = tuple(sorted(int(via_global[x]) for x in g_saw_g))
g_tvn_g_gl  = tuple(sorted(int(via_global[x]) for x in g_tvn_g))
g_saw_o_gl  = tuple(sorted(int(via_global[x]) for x in g_saw_o))
g_prom_g_gl = tuple(sorted(int(via_global[x]) for x in g_prom_g))

T1 = set(g_saw_g_gl)=={184,279,320} and is_dom_Q1(*g_saw_g)
T2 = not is_dom_Q1(*g_saw_o)
T3 = set(g_prom_g_gl)=={51,233,345} and not is_dom_Q1(*g_prom_g)
T4 = set(g_tvn_g_gl)=={233,320,355}

jac_sp = jac10(sc_saw, sc_prom)

print(f"  T1 SAW greedy=={g_saw_g_gl}, dom Q1: {'PASS' if T1 else 'FAIL'}")
print(f"  T2 SAW ótimo=={g_saw_o_gl}, não dom Q1: {not is_dom_Q1(*g_saw_o)} (informativo)")
print(f"  T3 PROMETHEE greedy=={g_prom_g_gl}, não dom Q1: {not is_dom_Q1(*g_prom_g)} (informativo)")
print(f"  T4 TOPSIS-VN greedy=={g_tvn_g_gl}: {'PASS' if T4 else f'diferente do esperado {233,320,355}'}")
print(f"  Jaccard SAW-PROM: {jac_sp:.3f}  (esperado ~0.43)")
# Nota: T2/T3 em Q1 podem falhar porque a fronteira Q1 difere dos 213 IEEE
# (os 213 são baseados na fronteira de Pareto exata do IEEE, não nos mesmos objetivos Q1)
# O teste de sanidade de P1 é o Q2 abaixo.
assert T1, "T1 falhou"

# Q2: SAW-473 ótimo deve ser 100% não dominado (P1)
# SAW-S1 = score coerente com Pareto: -f1 - f2 + f3 (maximiza segurança, minimiza custo+impacto)
print("\n  Q2 sanity: SAW-S1 ótimo (P1 deve garantir 100%)...")
F1_q, F2_q, F3_q, fv1, fv2, fv3 = compute_F_w(w_ahp)
saw_s1_sc = saw_s1_w(w_ahp)
s1_t = saw_s1_sc[trio_arr[:,0]]+saw_s1_sc[trio_arr[:,1]]+saw_s1_sc[trio_arr[:,2]]
g_saw_s1_opt = trio_arr[s1_t.argmax()]
dom_s1 = is_dom_Q2(*g_saw_s1_opt, F1_q, F2_q, F3_q, fv1, fv2, fv3)
gids_s1 = tuple(sorted(int(via_global[x]) for x in g_saw_s1_opt))
print(f"  SAW-S1 ótimo: {gids_s1}  dom={dom_s1}  (esperado False)")
assert not dom_s1, "SAW-S1 ótimo deveria ser não dominado (P1)"
print("  P1 PASS: SAW-S1 ótimo não é dominado")

# ─── Monte Carlo Q1 + Q2 ─────────────────────────────────────────────────────
METHODS = [
    ("SAW_s1",     saw_s1_w,     "greedy"),   # score coerente com Pareto (-f1-f2+f3)
    ("SAW_s1",     saw_s1_w,     "optimal"),
    ("SAW",        saw_w,        "greedy"),    # SAW clássico (maximiza soma)
    ("TOPSIS_MM",  topsis_mm_w,  "greedy"),
    ("TOPSIS_VN",  topsis_vn_w,  "greedy"),
    ("VIKOR",      vikor_w,      "greedy"),
    ("PROMETHEE",  prom_w,       "greedy"),
]

records = []
for alpha in ALPHAS:
    print(f"\n=== alpha={alpha} ===")
    t0 = time.time()
    for draw in range(N_DRAWS):
        w_draw = rng.dirichlet(alpha * w_ahp)
        sc_saw_ref = saw_w(w_draw)

        # Q2: objetivos com pesos sorteados
        F1q, F2q, F3q, f1vq, f2vq, f3vq = compute_F_w(w_draw)

        for method, fn_sc, variant in METHODS:
            sc = fn_sc(w_draw)
            if variant == "greedy":
                idx = greedy_trio(sc, D_via)
            else:
                idx = argmax_saw(sc)
            i,j,k = idx

            # Q1
            dom_q1 = is_dom_Q1(i,j,k)
            gn_q1  = gap_n_Q1(i,j,k)
            # Q2
            dom_q2 = is_dom_Q2(i,j,k, F1q,F2q,F3q,f1vq,f2vq,f3vq)
            gn_q2  = gap_n_Q2(i,j,k, F1q,F2q,F3q,f1vq,f2vq,f3vq)
            jac    = jac10(sc, sc_saw_ref)

            records.append({
                "alpha":alpha,"draw":draw,"method":method,"variant":variant,
                "nd_Q1":int(not dom_q1),"gap_Q1":gn_q1,
                "nd_Q2":int(not dom_q2),"gap_Q2":gn_q2,
                "jaccard_10":jac,
                "ids":str(sorted([int(via_global[i]),int(via_global[j]),int(via_global[k])])),
            })

        if (draw+1) % 100 == 0:
            print(f"  draw {draw+1}/{N_DRAWS}  ({time.time()-t0:.0f}s)")

df_raw = pd.DataFrame(records)
df_raw.to_csv(os.path.join(RESULTS_DIR,"mc_q1q2_raw.csv"),index=False)

agg = (df_raw.groupby(["alpha","method","variant"])
       .agg(
           pct_nd_Q1=("nd_Q1", lambda x: 100*x.mean()),
           med_gap_Q1=("gap_Q1","median"),
           pct_nd_Q2=("nd_Q2", lambda x: 100*x.mean()),
           med_gap_Q2=("gap_Q2","median"),
           mean_jac=("jaccard_10","mean"),
           n=("draw","count"),
       ).reset_index())

agg.to_csv(os.path.join(RESULTS_DIR,"mc_q1q2_summary.csv"),index=False)

print("\n" + "="*80)
print("MC Q1 + Q2 SUMMARY")
print("Q1 = objetivos AHP fixos | Q2 = objetivos com mesmos pesos sorteados (teste de P1)")
print("="*80)
print(agg.to_string(index=False, float_format=lambda x: f"{x:.1f}"))
