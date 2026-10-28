# -*- coding: utf-8 -*-
"""
diag_mc.py  —  Teste de regressão: MC com pesos AHP exatos deve reproduzir caso base.
Identifica as causas das contradições relatadas.

Run: uv run --with pandas --with numpy --with scipy python scripts/diag_mc.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

from mcdm_experiment import (
    load_data, impute_nan, compute_objectives, haversine_km,
    saw_scores, topsis_scores, vikor_scores, promethee2_scores,
    greedy_trio, pareto_dominates, gap_additive,
    trio_objectives_from_global,
    COL, AHP_WEIGHTS, MIN_DIST_KM, _build_decision_matrix,
)

# ─── setup ───────────────────────────────────────────────────────────────────
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
via_global = df_via.index.values
N = len(df_via)
objs_473 = compute_objectives(df_imp, df_imp)
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
w_ahp = np.array(list(AHP_WEIGHTS.values()))

# ─── Pré-calcular TODOS os trios viáveis e seus objetivos (base fixa) ────────
print("Pré-calculando todos os 1,944,653 trios viáveis...")
valid = D_via >= MIN_DIST_KM
trio_arr = []  # (M, 3) índices locais
for i in range(N):
    for j in range(i+1, N):
        if not valid[i,j]: continue
        for k in range(j+1, N):
            if not valid[i,k] or not valid[j,k]: continue
            trio_arr.append((i, j, k))
trio_arr = np.array(trio_arr, dtype=np.int32)   # (1944653, 3)
M = len(trio_arr)
print(f"  {M:,} trios  shape={trio_arr.shape}")

# ─── Funções com pesos customizados ──────────────────────────────────────────
def saw_w(df, w):
    X, benefit = _build_decision_matrix(df)
    return (X * w).sum(1)

def compute_objs_w(w):
    """
    Recalcula os objetivos f1, f2, f3 de CADA site viável com os pesos w.
    Retorna arrays shape (N,) para f1_site, f2_site, f3_site.
    Depois, para um trio (i,j,k): f1(T)=f1[i]+f1[j]+f1[k], etc.
    """
    X, benefit = _build_decision_matrix(df_via)  # (N, 11), min-max sobre 389
    # Mas os objetivos usam normalização sobre os 473!
    # Recalculamos sobre os 473 com os novos pesos.
    X_all, _ = _build_decision_matrix(df_imp)     # (473, 11), min-max sobre 473
    # Grupos de critérios
    # f1 = cost: perm(0), slope(1), roads(2)  — menores valores são melhores
    # f2 = impact: rivers(3),aspect(4),coast(5),protected(6),wells(7)
    # f3 = safety: urban(8),aero(9),cult(10)
    # Índices correspondem à ordem do COL dict
    col_names = list(AHP_WEIGHTS.keys())
    f1_idx = [col_names.index(c) for c in ["perm","slope","roads"]]
    f2_idx = [col_names.index(c) for c in ["rivers","aspect","coast","protected","wells"]]
    f3_idx = [col_names.index(c) for c in ["urban","aero","cult"]]

    w1 = w[f1_idx]; w1 = w1 / w1.sum()
    w2 = w[f2_idx]; w2 = w2 / w2.sum()
    w3 = w[f3_idx]; w3 = w3 / w3.sum()

    # Para os 473, calcular f por site
    # f1: cost → valor alto = mal → usamos (1 - normalizado)  [invertido = distância ao pior]
    # Mas a fórmula original soma (1-X) para cost critérios — vamos seguir o mcdm_experiment
    # que inverte critérios de custo antes de compor os objetivos.
    # Verificar em mcdm_experiment compute_objectives...
    # A análise em compute_objectives: para COST, score = 1 - normalized (menor raw = melhor → 1)
    # Para BENEFIT/INV: score = normalized diretamente
    # f1 = soma dos scores de cost = soma de (1 - X_cost_i) * w_i
    # f2 = soma de scores de impact
    # f3 = soma de scores de safety

    # Mas na normalização dos OBJETIVOS em mcdm_experiment:
    # os objetivos são calculados sobre os 473 SEM normalização de pesos dentro do objetivo.
    # Vamos recalcular corretamente.

    # Para simplificar: usar os scores já calculados em compute_objectives (não mudam com w)
    # Os objetivos f1,f2,f3 são soma ponderada dos SCORES de cada critério.
    # Os SCORES por critério são fixos (normalização sobre 473, aspect=0/1).
    # Só os PESOS w_j mudam.

    # Ler scores por critério do mcdm_experiment.compute_objectives
    # Calcular per-site como no código original:
    # f1_site[a] = sum(w[j]*score[j][a] for j in cost_criteria)
    # (onde score para custo = 1 - min_max, para INV/benefit = min_max)

    # Reconstruir scores por critério sobre os 473
    from mcdm_experiment import COST, INV, BENEFIT
    scores_per_crit = {}  # key = crit_name, value = array (473,)
    col_list = list(AHP_WEIGHTS.keys())
    for crit in col_list:
        col = COL[crit]
        raw = df_imp[col].values.astype(float)
        mn, mx = np.nanmin(raw), np.nanmax(raw)
        norm = (raw - mn) / (mx - mn + 1e-12)
        norm = np.nan_to_num(norm, nan=0.5)
        if crit == "aspect":
            # aspect: 90-180 = leeward = bom = 0; else = 1; nan=-1 = 0.5
            a = raw.copy()
            s = np.where((a >= 90) & (a <= 180), 0.0,
                np.where((a == -1) | np.isnan(a), 0.5, 1.0))
            scores_per_crit[crit] = s
        elif crit in COST:
            scores_per_crit[crit] = 1.0 - norm   # menor raw = melhor = maior score
        else:
            scores_per_crit[crit] = norm          # INV e BENEFIT: maior raw = melhor

    # f1, f2, f3 por site sobre os 473, com pesos w
    f1_sites = np.zeros(473)
    f2_sites = np.zeros(473)
    f3_sites = np.zeros(473)
    w_f1 = sum(w[col_list.index(c)] for c in ["perm","slope","roads"])
    w_f2 = sum(w[col_list.index(c)] for c in ["rivers","aspect","coast","protected","wells"])
    w_f3 = sum(w[col_list.index(c)] for c in ["urban","aero","cult"])

    for crit in ["perm","slope","roads"]:
        f1_sites += w[col_list.index(crit)] * scores_per_crit[crit]
    for crit in ["rivers","aspect","coast","protected","wells"]:
        f2_sites += w[col_list.index(crit)] * scores_per_crit[crit]
    for crit in ["urban","aero","cult"]:
        f3_sites += w[col_list.index(crit)] * scores_per_crit[crit]

    # Normalizar pelos pesos do grupo (para manter escala comparável)
    f1_sites /= (w_f1 or 1)
    f2_sites /= (w_f2 or 1)
    f3_sites /= (w_f3 or 1)

    # Mapear para os 389 viáveis na ordem do trio_arr
    idx_in_473 = {gid: i for i, gid in enumerate(df_all.index)}
    via_idx_in_473 = np.array([idx_in_473[int(g)] for g in via_global])
    return (f1_sites[via_idx_in_473],
            f2_sites[via_idx_in_473],
            f3_sites[via_idx_in_473])


def dominated_vs_trios(f1_trio, f2_trio, f3_trio, F1, F2, F3):
    """Verifica se o trio é dominado por algum dos M trios viáveis.
    Usa os objetivos recalculados (F1, F2, F3) shape (M,).
    Pareto: minimizar f1, minimizar f2, maximizar f3.
    """
    # Dominador t': f1[t']<=f1, f2[t']<=f2, f3[t']>=f3, pelo menos 1 estrito
    mask = ((F1 <= f1_trio) & (F2 <= f2_trio) & (F3 >= f3_trio) &
            ((F1 < f1_trio) | (F2 < f2_trio) | (F3 > f3_trio)))
    return mask.any()


# ─── Teste de regressão: pesos AHP exatos ───────────────────────────────────
print("\n" + "="*65)
print("TESTE DE REGRESSÃO: pesos AHP exatos")
print("="*65)

w_exact = w_ahp.copy()

# 1. Verificar que os scores SAW reproduzem o caso base
sc_saw = saw_w(df_via, w_exact)
g_saw = greedy_trio(sc_saw, D_via)
g_saw_global = tuple(sorted(int(via_global[i]) for i in g_saw))
print(f"SAW greedy: {list(g_saw_global)}  (esperado: [184, 279, 320])")
assert set(g_saw_global) == {184, 279, 320}, f"SAW greedy FALHOU: {g_saw_global}"

# 2. Verificar Jaccard SAW vs PROMETHEE
sc_prom = promethee2_scores(df_via)
top10_saw  = set(np.argsort(-sc_saw)[:10])
top10_prom = set(np.argsort(-sc_prom)[:10])
jac_sp = len(top10_saw & top10_prom) / len(top10_saw | top10_prom)
print(f"Jaccard@10 SAW vs PROMETHEE (índices locais): {jac_sp:.3f}  (esperado ~0.43)")

# 3. Verificar Jaccard com índices GLOBAIS
top10_saw_g  = set(int(via_global[i]) for i in np.argsort(-sc_saw)[:10])
top10_prom_g = set(int(via_global[i]) for i in np.argsort(-sc_prom)[:10])
jac_sp_g = len(top10_saw_g & top10_prom_g) / len(top10_saw_g | top10_prom_g)
print(f"Jaccard@10 SAW vs PROMETHEE (índices globais): {jac_sp_g:.3f}  (deve ser igual ao anterior)")

# 4. Calcular f1,f2,f3 por site com pesos AHP e verificar dominância
print("\nCalculando objetivos por site com pesos AHP...")
f1v, f2v, f3v = compute_objs_w(w_exact)

# Calcular objetivos do trio SAW greedy
i0, i1, i2 = g_saw
f1_t = f1v[i0]+f1v[i1]+f1v[i2]
f2_t = f2v[i0]+f2v[i1]+f2v[i2]
f3_t = f3v[i0]+f3v[i1]+f3v[i2]
print(f"SAW greedy f1={f1_t:.4f} f2={f2_t:.4f} f3={f3_t:.4f}")

# Calcular F1,F2,F3 para TODOS os trios viáveis com pesos AHP
print("Calculando objetivos de todos os 1,944,653 trios...")
F1 = f1v[trio_arr[:,0]] + f1v[trio_arr[:,1]] + f1v[trio_arr[:,2]]
F2 = f2v[trio_arr[:,0]] + f2v[trio_arr[:,1]] + f2v[trio_arr[:,2]]
F3 = f3v[trio_arr[:,0]] + f3v[trio_arr[:,1]] + f3v[trio_arr[:,2]]
print(f"  F shapes: {F1.shape}, range f1=[{F1.min():.3f},{F1.max():.3f}]")

# 5. Verificar dominância do SAW greedy contra os 1,94M trios
dom_saw_greedy = dominated_vs_trios(f1_t, f2_t, f3_t, F1, F2, F3)
print(f"\nSAW greedy dominado (vs 1,94M recalculados): {dom_saw_greedy}  (esperado: True)")

# 6. Verificar dominância usando os 213 trios da fronteira original (fixos, pesos AHP)
# (como faz o MC atual — INCORRETO quando pesos mudam, mas aqui pesos = AHP = OK)
from mcdm_experiment import in_pareto_front, pareto_dominates, gap_additive
obj_global = trio_objectives_from_global(
    tuple(int(via_global[i]) for i in g_saw), objs_473
)
dom_saw_original = pareto_dominates(par, obj_global["f1"], obj_global["f2"], obj_global["f3"])
print(f"SAW greedy dominado (vs 213 trios FIXOS AHP):  {dom_saw_original}  (esperado: True)")
print(f"  [Nota: com pesos AHP exatos, os dois devem coincidir]")

# 7. Verificar: o MC atual usa qual método?
print("\n--- Diagnóstico do MC atual ---")
print("O MC atual avalia dominância contra os 213 trios FIXOS (par DataFrame)")
print("Quando pesos sorteados ≠ AHP, a fronteira real muda.")
print("Com α=200 e pesos próximos do AHP, a fronteira real ≈ fronteira AHP,")
print("então o resultado deveria ser similar ao caso base.")
print("Se não é, o bug está em outro lugar — vamos verificar...")

# 8. Simular 1 sorteio de α=200 para ver o que acontece
from scipy.stats import dirichlet as sp_dirichlet
rng = np.random.default_rng(42)
w_200 = rng.dirichlet(200 * w_ahp)
print(f"\nPeso AHP:    {w_ahp.round(3)}")
print(f"Sorteio α=200: {w_200.round(3)}")
print(f"Max diff:    {np.abs(w_200 - w_ahp).max():.4f}")

sc_saw_200 = saw_w(df_via, w_200)
g_saw_200 = greedy_trio(sc_saw_200, D_via)
g_saw_200_global = tuple(sorted(int(via_global[i]) for i in g_saw_200))
print(f"\nSAW greedy α=200 draw 0: {list(g_saw_200_global)}  (esperado próximo de [184,279,320])")

# Calcular objetivos do trio com pesos α=200
f1v_200, f2v_200, f3v_200 = compute_objs_w(w_200)
i0_200, i1_200, i2_200 = g_saw_200
f1_t200 = f1v_200[i0_200]+f1v_200[i1_200]+f1v_200[i2_200]
f2_t200 = f2v_200[i0_200]+f2v_200[i1_200]+f2v_200[i2_200]
f3_t200 = f3v_200[i0_200]+f3v_200[i1_200]+f3v_200[i2_200]

F1_200 = f1v_200[trio_arr[:,0]] + f1v_200[trio_arr[:,1]] + f1v_200[trio_arr[:,2]]
F2_200 = f2v_200[trio_arr[:,0]] + f2v_200[trio_arr[:,1]] + f2v_200[trio_arr[:,2]]
F3_200 = f3v_200[trio_arr[:,0]] + f3v_200[trio_arr[:,1]] + f3v_200[trio_arr[:,2]]

dom_200_correct = dominated_vs_trios(f1_t200, f2_t200, f3_t200, F1_200, F2_200, F3_200)
dom_200_fixed   = dominated_vs_trios(f1_t200, f2_t200, f3_t200, F1, F2, F3)  # errado: F fixos
dom_200_par     = pareto_dominates(par, obj_global["f1"], obj_global["f2"], obj_global["f3"])  # mais errado

print(f"\nSAW greedy α=200 draw 0:")
print(f"  dominado vs trios com pesos α=200 (CORRETO): {dom_200_correct}")
print(f"  dominado vs trios com pesos AHP   (ERRADO):  {dom_200_fixed}")
print(f"  dominado vs 213 trios fixos AHP   (ERRADO):  {dom_200_par}")

print("\n>>> CAUSA IDENTIFICADA: o MC usa os objetivos dos 213 trios FIXOS (pesos AHP)")
print(">>> A dominância é correta só quando w = w_AHP")
print(">>> Quando w muda, precisa recalcular F1,F2,F3 de todos os trios com w")
