# -*- coding: utf-8 -*-
"""
monte_carlo.py  v3 — Versão corrigida e bem definida.

DEFINIÇÃO CLARA DO EXPERIMENTO:
  - Perturbamos os PESOS dos métodos MCDM (Dirichlet(alpha*w_AHP))
  - Cada método seleciona um trio com os pesos sorteados
  - A dominância é avaliada no espaço A ORIGINAL (objetivos com normalização 473, pesos AHP)
    usando os 1,944,653 trios viáveis calculados com os objetivos originais.
  - Isso responde: "se o decisor tivesse outros pesos plausíveis, o método ainda
    selecionaria um trio Pareto-ótimo no espaço de avaliação do artigo?"

CORREÇÕES em relação à v1:
  1. Scores calculados com _build_decision_matrix(df_via) + inversão explícita
     (normalização sobre 389, consistente com mcdm_experiment)
  2. Dominância avaliada contra objetivos ORIGINAIS (473, pesos AHP) — FIXOS
  3. Variante ótima via argmax vetorizado (O(M))
  4. Jaccard usa índices locais (0..388) em ambos os lados

Run:  uv run --with pandas --with numpy --with scipy python scripts/monte_carlo.py
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

from mcdm_experiment import (
    load_data, impute_nan, haversine_km, greedy_trio,
    COL, AHP_WEIGHTS, MIN_DIST_KM, COST,
    _build_decision_matrix,
    trio_objectives_from_global,
    pareto_dominates, in_pareto_front, gap_additive,
)

# ─── constantes ──────────────────────────────────────────────────────────────
N_DRAWS  = 500
SEED     = 42
ALPHAS   = [50, 200]
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# ─── load + prep ─────────────────────────────────────────────────────────────
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
rng = np.random.default_rng(SEED)

# ─── Pré-calcular matriz de scores (normalização sobre 389, benefit corrigido) ─
print("Pré-calculando matriz de scores dos 389 viáveis...")
X_via, benefit_via = _build_decision_matrix(df_via)  # (389, 11), [0,1] sobre 389
# Para SAW/PROMETHEE: precisamos de X_adj onde "maior = melhor" para todos
X_adj = X_via.copy()
for j, b in enumerate(benefit_via):
    if not b:
        X_adj[:, j] = 1.0 - X_via[:, j]
# X_adj: todos os critérios em [0,1] com "maior = melhor"

# ─── Objetivos ORIGINAIS para avaliação (fixos, pesos AHP, normalização 473) ──
print("Pré-calculando objetivos originais de todos os 1,944,653 trios viáveis...")
from mcdm_experiment import compute_objectives
objs_via = compute_objectives(df_via, df_imp)  # usa normalização 473 (df_imp como ref)

f1v_orig = objs_via["f1"].values.astype(np.float32)
f2v_orig = objs_via["f2"].values.astype(np.float32)
f3v_orig = objs_via["f3"].values.astype(np.float32)

valid = D_via >= MIN_DIST_KM
trio_arr = []
for i in range(N):
    for j in range(i+1, N):
        if not valid[i,j]: continue
        for k in range(j+1, N):
            if not valid[i,k] or not valid[j,k]: continue
            trio_arr.append((i, j, k))
trio_arr = np.array(trio_arr, dtype=np.int32)  # (M, 3)
M = len(trio_arr)
print(f"  {M:,} trios")

i0a, i1a, i2a = trio_arr[:,0], trio_arr[:,1], trio_arr[:,2]
F1_orig = (f1v_orig[i0a] + f1v_orig[i1a] + f1v_orig[i2a])
F2_orig = (f2v_orig[i0a] + f2v_orig[i1a] + f2v_orig[i2a])
F3_orig = (f3v_orig[i0a] + f3v_orig[i1a] + f3v_orig[i2a])
print(f"  F1 range: [{F1_orig.min():.4f}, {F1_orig.max():.4f}]")
print(f"  F2 range: [{F2_orig.min():.4f}, {F2_orig.max():.4f}]")
print(f"  F3 range: [{F3_orig.min():.4f}, {F3_orig.max():.4f}]")

# ─── Funções de score com pesos w (normalização 389) ─────────────────────────
def compute_scores_w(w):
    """SAW com pesos w, normalização sobre 389."""
    return (X_adj * w).sum(1)

def topsis_minmax_w(w):
    """TOPSIS min-max com pesos w, normalização sobre 389."""
    V = X_via * w
    PIS = np.where(benefit_via, V.max(0), V.min(0))
    NIS = np.where(benefit_via, V.min(0), V.max(0))
    d_pos = np.sqrt(((V - PIS)**2).sum(1))
    d_neg = np.sqrt(((V - NIS)**2).sum(1))
    denom = d_pos + d_neg
    return np.where(denom == 0, 0.5, d_neg / denom)

def vikor_w(w, v=0.5):
    """VIKOR com pesos w, normalização sobre 389."""
    V = X_via * w
    PIS = np.where(benefit_via, V.max(0), V.min(0))
    NIS = np.where(benefit_via, V.min(0), V.max(0))
    denom = np.abs(PIS - NIS); denom[denom == 0] = 1e-12
    norm_d = np.abs(V - PIS) / denom
    S = (norm_d * w).sum(1)
    R = (norm_d * w).max(1)
    Q = v*(S-S.min())/((S.max()-S.min()) or 1) + (1-v)*(R-R.min())/((R.max()-R.min()) or 1)
    return -Q

def promethee_w(w):
    """PROMETHEE II (critério usual) com pesos w, postos sobre X_adj."""
    ranks = np.apply_along_axis(
        lambda c: pd.Series(c).rank(method="average").values, 0, X_adj
    )
    return ((2*ranks - N - 1) / (N - 1)) @ w

def optimal_trio_saw(sc):
    """Ótimo SAW: argmax da soma de scores. O(M)."""
    s_t = sc[trio_arr[:,0]] + sc[trio_arr[:,1]] + sc[trio_arr[:,2]]
    best = trio_arr[s_t.argmax()]
    return tuple(int(x) for x in best)

def is_dominated_orig(i0, i1, i2):
    """Dominância no espaço ORIGINAL (pesos AHP, norm 473)."""
    f1t = float(f1v_orig[i0]+f1v_orig[i1]+f1v_orig[i2])
    f2t = float(f2v_orig[i0]+f2v_orig[i1]+f2v_orig[i2])
    f3t = float(f3v_orig[i0]+f3v_orig[i1]+f3v_orig[i2])
    mask = ((F1_orig <= f1t) & (F2_orig <= f2t) & (F3_orig >= f3t) &
            ((F1_orig < f1t) | (F2_orig < f2t) | (F3_orig > f3t)))
    return bool(mask.any())

def gap_norm_orig(i0, i1, i2):
    """Gap normalizado no espaço original."""
    f1t = float(f1v_orig[i0]+f1v_orig[i1]+f1v_orig[i2])
    f2t = float(f2v_orig[i0]+f2v_orig[i1]+f2v_orig[i2])
    f3t = float(f3v_orig[i0]+f3v_orig[i1]+f3v_orig[i2])
    if not is_dominated_orig(i0, i1, i2):
        return 0.0
    f1r = F1_orig.max() - F1_orig.min()
    f2r = F2_orig.max() - F2_orig.min()
    f3r = F3_orig.max() - F3_orig.min()
    dc = (f1t - F1_orig) / (f1r or 1)
    di = (f2t - F2_orig) / (f2r or 1)
    ds = (F3_orig - f3t) / (f3r or 1)
    return float(max(0.0, np.minimum(np.minimum(dc, di), ds).max()))

def jaccard_topk(sc_a, sc_b, k=10):
    a = set(np.argsort(-sc_a)[:k])
    b = set(np.argsort(-sc_b)[:k])
    return len(a & b) / len(a | b) if a | b else 1.0

# ─── Teste de regressão ───────────────────────────────────────────────────────
print("\nTESTE DE REGRESSÃO (pesos AHP exatos)...")
sc_saw_ref   = compute_scores_w(w_ahp)
sc_prom_ref  = promethee_w(w_ahp)
g_saw_greedy = greedy_trio(sc_saw_ref, D_via)
g_prom_greedy = greedy_trio(sc_prom_ref, D_via)
g_saw_opt     = optimal_trio_saw(sc_saw_ref)

gsg = tuple(sorted(int(via_global[i]) for i in g_saw_greedy))
gpg = tuple(sorted(int(via_global[i]) for i in g_prom_greedy))
gso = tuple(sorted(int(via_global[i]) for i in g_saw_opt))
jac_sp = jaccard_topk(sc_saw_ref, sc_prom_ref)

assert set(gsg) == {184, 279, 320}, f"SAW greedy: {gsg}"
assert set(gpg) == {51, 233, 345},  f"PROMETHEE greedy: {gpg}"
assert abs(jac_sp - 0.43) < 0.05,  f"Jaccard SAW-PROM: {jac_sp:.3f}"

dom_sg  = is_dominated_orig(*g_saw_greedy)
dom_so  = is_dominated_orig(*g_saw_opt)
dom_pg  = is_dominated_orig(*g_prom_greedy)
assert dom_sg,   f"SAW greedy deveria ser dominado"
assert not dom_so, f"SAW ótimo deveria ser não-dominado, trio={gso}"
assert not dom_pg, f"PROMETHEE greedy deveria ser não-dominado"

print(f"  PASS SAW greedy={gsg} dom={dom_sg}")
print(f"  PASS SAW ótimo={gso}  dom={dom_so}")
print(f"  PASS PROMETHEE greedy={gpg} dom={dom_pg}")
print(f"  PASS Jaccard SAW-PROM={jac_sp:.3f}")

# ─── Monte Carlo ─────────────────────────────────────────────────────────────
METHODS = [
    ("SAW",       compute_scores_w,  "greedy"),
    ("SAW",       compute_scores_w,  "optimal"),
    ("TOPSIS_MM", topsis_minmax_w,   "greedy"),
    ("VIKOR",     vikor_w,           "greedy"),
    ("PROMETHEE", promethee_w,       "greedy"),
]

records = []
for alpha in ALPHAS:
    print(f"\n=== alpha={alpha} ===")
    t0 = time.time()
    for draw in range(N_DRAWS):
        w_draw = rng.dirichlet(alpha * w_ahp)
        sc_saw = compute_scores_w(w_draw)  # referência para Jaccard

        for method_lbl, fn_sc, variant in METHODS:
            sc = fn_sc(w_draw)
            if variant == "greedy":
                idx = greedy_trio(sc, D_via)
                i0, i1, i2 = idx
            else:  # optimal (SAW)
                idx = optimal_trio_saw(sc)
                i0, i1, i2 = idx

            dom = is_dominated_orig(i0, i1, i2)
            gn  = gap_norm_orig(i0, i1, i2)
            jac = jaccard_topk(sc, sc_saw, k=10)

            records.append({
                "alpha": alpha, "draw": draw,
                "method": method_lbl, "variant": variant,
                "non_dominated": int(not dom),
                "gap_norm": gn,
                "jaccard_10_vs_saw": jac,
                "ids": str(sorted([int(via_global[i0]),
                                   int(via_global[i1]),
                                   int(via_global[i2])])),
            })

        if (draw+1) % 100 == 0:
            print(f"  draw {draw+1}/{N_DRAWS}  ({time.time()-t0:.1f}s)")

# ─── salvar e agregar ────────────────────────────────────────────────────────
df_raw = pd.DataFrame(records)
df_raw.to_csv(os.path.join(RESULTS_DIR, "monte_carlo_raw.csv"), index=False)

agg = (df_raw
    .groupby(["alpha","method","variant"])
    .agg(
        pct_non_dominated=("non_dominated", lambda x: 100*x.mean()),
        median_gap_norm=("gap_norm", "median"),
        mean_jaccard_10=("jaccard_10_vs_saw", "mean"),
        n=("draw","count"),
    ).reset_index())

agg.to_csv(os.path.join(RESULTS_DIR, "monte_carlo_summary.csv"), index=False)
print("\n" + "="*72)
print("MONTE CARLO SUMMARY v3 (dominância no espaço A original, ótimo incluído)")
print("="*72)
print(agg.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
