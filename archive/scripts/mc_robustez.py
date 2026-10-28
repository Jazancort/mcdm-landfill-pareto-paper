# -*- coding: utf-8 -*-
"""
mc_robustez.py — Monte Carlo de robustez do avaliador para SAW × {mm, vec}.

Roda os mesmos 500 sorteios de pesos do mc_18cells (SEED=42, alpha∈{50,200})
mas avalia Q2 em 3 fronteiras:
  - F_mm  = A' (pareto_front_Aprime.csv)     — já calculada
  - F_vec = funções de valor vetoriais       — mc_2x2_fvec.csv
  - F_fixo= bounds regulatórios fixos        — mc_2x2_ffixo.csv

Salva: results/mc_robustez_raw.csv
       results/mc_robustez_summary.csv
"""
import sys, os, time; sys.path.insert(0, '.')
import numpy as np
import pandas as pd
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix,
    haversine_km, MIN_DIST_KM, INV, COST, F1_CRIT, F2_CRIT, F3_CRIT,
    optimal_trio_enumerate,
)

RESULTS_DIR = 'results'
t0 = time.time()
def T(): return f'{time.time()-t0:.1f}s'

# ── Carregamento ──────────────────────────────────────────────────────────────
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
via_mask = df_imp[COL['protected']] > 0
df_via = df_imp[via_mask].copy()
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
X_via, benefit = _build_decision_matrix(df_via)
D_via = haversine_km(df_via['latitude (degrees)'].values, df_via['longitude (degrees)'].values)
N = len(df_via)
print(f'N={N} t={T()}', flush=True)

# ── GATE R1: 4 asserts de regressão obrigatórios ──────────────────────────────
assert abs(MIN_DIST_KM - 10.0) < 1e-6, f'GATE R1 FAIL A1: MIN_DIST_KM={MIN_DIST_KM}, esperado 10.0 (bug alpha/d_min)'
assert N == 389, f'GATE R1 FAIL: N={N}, esperado 389'

# Assert P1: SAW×mm optimal com pesos AHP deve estar em A'
_X_adj_test = X_via.copy().astype(np.float32)
for _j in range(len(w_ahp)):
    if not benefit[_j]: _X_adj_test[:, _j] = 1.0 - X_via[:, _j]
_sc_test = (_X_adj_test * w_ahp.astype(np.float32)).sum(axis=1)
_D_test = haversine_km(df_via['latitude (degrees)'].values, df_via['longitude (degrees)'].values)
_to_test = optimal_trio_enumerate(_sc_test, _D_test, MIN_DIST_KM)
_via_idx_test = df_via.index.values
_gids_opt = frozenset(int(_via_idx_test[_i]) for _i in _to_test)
_front_test = pd.read_csv(os.path.join(RESULTS_DIR, 'pareto_front_Aprime.csv'))
_in_f = any(frozenset([int(r.idx1), int(r.idx2), int(r.idx3)]) == _gids_opt for _, r in _front_test.iterrows())
assert _in_f, f'GATE R1 FAIL P1: SAW×mm optimal {sorted(_gids_opt)} not in_front — P1 violada, pipeline incorreto'
del _X_adj_test, _sc_test, _D_test, _to_test, _via_idx_test, _gids_opt, _front_test, _in_f

print(f'GATE R1: todos os asserts passaram. t={T()}', flush=True)

# ── Pré-calcular trios viáveis ────────────────────────────────────────────────
print('Enumerando trios viáveis...', flush=True)
pairs_i, pairs_j = np.where(np.triu(D_via >= MIN_DIST_KM, k=1))
ti_l, tj_l, tk_l = [], [], []
for pi, pj in zip(pairs_i, pairs_j):
    ks = np.where((D_via[pi] >= MIN_DIST_KM) & (D_via[pj] >= MIN_DIST_KM))[0]
    ks = ks[ks > pj]
    ti_l.extend([pi]*len(ks)); tj_l.extend([pj]*len(ks)); tk_l.extend(ks.tolist())
trio_arr = np.stack([ti_l, tj_l, tk_l], axis=1).astype(np.int32)
M = len(trio_arr)
print(f'M={M} t={T()}', flush=True)

# ── Carregar fronteiras ───────────────────────────────────────────────────────
front_mm   = pd.read_csv(os.path.join(RESULTS_DIR, 'pareto_front_Aprime.csv'))
front_vec  = pd.read_csv(os.path.join(RESULTS_DIR, 'mc_2x2_fvec.csv'))
front_exog = pd.read_csv(os.path.join(RESULTS_DIR, 'mc_2x2_ffixo.csv'))
print(f'Fronteiras: F_mm={len(front_mm)} F_vec={len(front_vec)} F_fixo={len(front_exog)} t={T()}', flush=True)

# Converter fronteiras para arrays numpy para avaliação vectorizada
F_mm_arr   = front_mm[['F1P','F2P','F3P']].values.astype(np.float32)
F_vec_arr  = front_vec[['F1P','F2P','F3P']].values.astype(np.float32)
F_fixo_arr = front_exog[['F1P','F2P','F3P']].values.astype(np.float32)

# ── Funções de normalização ───────────────────────────────────────────────────
def _norm(x, ref):
    lo, hi = ref.min(), ref.max()
    if hi <= lo: return np.zeros_like(x)
    return (x - lo) / (hi - lo)

def compute_site_objs(w, ref_df, val_override=None):
    """Calcula f1/f2/f3 por site com pesos w e normalização min-max sobre ref_df.
    val_override: se fornecido, usa essa matriz de valores em vez de calcular."""
    if val_override is not None:
        v = val_override  # (N, ncrit), alto=bom
        f1v = (v[:, [j for j,c in enumerate(col_names) if c in F1_CRIT]] * w[[j for j,c in enumerate(col_names) if c in F1_CRIT]]).sum(axis=1)
        f2v = (v[:, [j for j,c in enumerate(col_names) if c in F2_CRIT]] * w[[j for j,c in enumerate(col_names) if c in F2_CRIT]]).sum(axis=1)
        f3v = (v[:, [j for j,c in enumerate(col_names) if c in F3_CRIT]] * w[[j for j,c in enumerate(col_names) if c in F3_CRIT]]).sum(axis=1)
        return f1v.astype(np.float32), f2v.astype(np.float32), f3v.astype(np.float32)
    # Min-max sobre ref_df
    f1v = np.zeros(N, dtype=np.float32)
    f2v = np.zeros(N, dtype=np.float32)
    f3v = np.zeros(N, dtype=np.float32)
    for j, k in enumerate(col_names):
        col = COL[k]
        x = df_via[col].values.astype(float)
        ref = ref_df[col].values.astype(float)
        if k == 'aspect': c = np.where((x >= 90) & (x <= 180), 0., 1.)
        elif k in INV:    c = 1. - _norm(x, ref)
        elif k in COST:   c = _norm(x, ref)
        else:             c = _norm(x, ref)
        c = (c * w[j]).astype(np.float32)
        if k in F1_CRIT:   f1v += c
        elif k in F2_CRIT: f2v += c
        else:              f3v += c
    return f1v, f2v, f3v

# Pré-calcular val_vec e val_fixo (fixos, independentes de w)
print('Calculando val_vec e val_fixo...', flush=True)
val_vec = np.zeros((N, len(w_ahp)), dtype=np.float32)
for j, c in enumerate(col_names):
    if c == 'aspect':
        raw = np.where((df_via[COL[c]].values >= 90) & (df_via[COL[c]].values <= 180), 0., 1.).astype(np.float32)
    else:
        raw = df_via[COL[c]].values.astype(np.float32)
    nv = float(np.sqrt((raw.astype(float)**2).sum()))
    if nv == 0: nv = 1.
    v = raw / nv
    if not benefit[j]: v = -v
    lo, hi = float(v.min()), float(v.max())
    val_vec[:, j] = (v - lo) / (hi - lo) if hi > lo else 0.5

# F_fixo: bounds convencionais declarados a priori, independentes da amostra.
# Justificativa: quebrar circularidade exige apenas independência dos dados, não
# autoridade legal. Bounds derivados de critérios técnicos gerais para aterros;
# não reivindicam correspondência com nenhuma norma específica (NBR, CONAMA, ANAC
# ou Diretiva 1999/31/CE). slope=(0,20) em graus é bound convencional de projeto
# (20° ≈ 36% de inclinação); a NBR 13.896 usa percentual (~30% ≈ 16.7°), mas
# esta norma é inaplicável à jurisdição cabo-verdiana.
BOUNDS = {'perm':(0,5000),'slope':(0,20),'roads':(0,10000),'rivers':(0,500),
          'aspect':(0,1),'coast':(0,5000),'protected':(0,5000),'wells':(0,1000),
          'urban':(0,10000),'aero':(0,15000),'cult':(0,5000)}
val_fixo = np.zeros((N, len(w_ahp)), dtype=np.float32)
for j, c in enumerate(col_names):
    if c == 'aspect':
        raw = np.where((df_via[COL[c]].values >= 90) & (df_via[COL[c]].values <= 180), 0., 1.).astype(np.float32)
        lo_r, hi_r = 0., 1.
    else:
        raw = df_via[COL[c]].values.astype(np.float32)
        lo_r, hi_r = BOUNDS[c]
    rng2 = hi_r - lo_r
    v = np.clip((raw - lo_r) / rng2, 0., 1.) if rng2 > 0 else np.full(N, 0.5, np.float32)
    if not benefit[j]: v = 1. - v
    val_fixo[:, j] = v

# X_adj para SAW (benefit direction)
X_adj = X_via.copy().astype(np.float32)
for j in range(len(w_ahp)):
    if not benefit[j]: X_adj[:, j] = 1. - X_via[:, j]

# ── Funções de trio ───────────────────────────────────────────────────────────
def greedy_trio_fast(scores):
    order = np.argsort(-scores)
    chosen = []
    for idx in order:
        if all(D_via[idx, c] >= MIN_DIST_KM for c in chosen):
            chosen.append(int(idx))
        if len(chosen) == 3:
            break
    return tuple(chosen)

def argmax_trio_fast(scores):
    st = scores[trio_arr[:, 0]] + scores[trio_arr[:, 1]] + scores[trio_arr[:, 2]]
    best = trio_arr[st.argmax()]
    return (int(best[0]), int(best[1]), int(best[2]))

def is_nd_fn_vec(i, j, k, f1v, f2v, f3v, F_arr):
    """True se o trio (i,j,k) não é dominado pela fronteira F_arr."""
    f1t = float(f1v[i] + f1v[j] + f1v[k])
    f2t = float(f2v[i] + f2v[j] + f2v[k])
    f3t = float(f3v[i] + f3v[j] + f3v[k])
    le  = (F_arr[:, 0] <= f1t + 1e-7) & (F_arr[:, 1] <= f2t + 1e-7) & (F_arr[:, 2] >= f3t - 1e-7)
    lt  = (F_arr[:, 0] < f1t - 1e-7)  | (F_arr[:, 1] < f2t - 1e-7)  | (F_arr[:, 2] > f3t + 1e-7)
    return not bool((le & lt).any())

# ── Loop Monte Carlo ──────────────────────────────────────────────────────────
CELLS = [
    ('saw', 'minmax',  'greedy'),
    ('saw', 'minmax',  'optimal'),
    ('saw', 'vector',  'greedy'),
    ('saw', 'vector',  'optimal'),
]

N_DRAWS = 500
SEED    = 42
ALPHAS  = [50, 200]

print(f'\n{len(CELLS)} células × {N_DRAWS} sorteios × {len(ALPHAS)} alphas × 3 avaliadores = {len(CELLS)*N_DRAWS*len(ALPHAS):,} obs', flush=True)
print(f'Iniciando MC t={T()}', flush=True)

records = []
for alpha in ALPHAS:
    print(f'  alpha={alpha}', flush=True)
    rng = np.random.default_rng(SEED)
    for draw in range(N_DRAWS):
        if draw % 100 == 0:
            print(f'    draw={draw} t={T()}', flush=True)
        w = rng.dirichlet(alpha * w_ahp).astype(np.float32)

        # Objetivos em A' com escala mm (para F_mm)
        f1_mm, f2_mm, f3_mm = compute_site_objs(w, df_via)
        # Objetivos em A' com escala vec (para F_vec) — val_vec fixo, só w muda
        f1_vec, f2_vec, f3_vec = compute_site_objs(w, None, val_override=val_vec)
        # Objetivos em A' com escala exog (para F_fixo) — val_fixo fixo, só w muda
        f1_fixo, f2_fixo, f3_fixo = compute_site_objs(w, None, val_override=val_fixo)

        for agg, norm, mont in CELLS:
            # Score SAW (apenas mm e vec aqui)
            if norm == 'minmax':
                sc = (X_adj * w).sum(axis=1)
            else:  # vector — usar dados BRUTOS, não X_via
                Xraw = np.zeros((N, len(w)), dtype=np.float32)
                for j2, c2 in enumerate(col_names):
                    if c2 == 'aspect':
                        raw = np.where((df_via[COL[c2]].values >= 90) & (df_via[COL[c2]].values <= 180), 0., 1.).astype(np.float32)
                    else:
                        raw = df_via[COL[c2]].values.astype(np.float32)
                    nv_j = float(np.sqrt((raw.astype(float)**2).sum()))
                    if nv_j == 0: nv_j = 1.
                    v = raw / nv_j
                    if not benefit[j2]: v = -v
                    lo2, hi2 = float(v.min()), float(v.max())
                    Xraw[:, j2] = (v - lo2) / (hi2 - lo2) if hi2 > lo2 else 0.5
                sc = (Xraw * w).sum(axis=1)

            if mont == 'greedy':
                i, j, k = greedy_trio_fast(sc)
            else:
                i, j, k = argmax_trio_fast(sc)

            # Q2 nos 3 avaliadores
            nd_Fmm   = int(is_nd_fn_vec(i, j, k, f1_mm,   f2_mm,   f3_mm,   F_mm_arr))
            nd_Fvec  = int(is_nd_fn_vec(i, j, k, f1_vec,  f2_vec,  f3_vec,  F_vec_arr))
            nd_Ffixo = int(is_nd_fn_vec(i, j, k, f1_fixo, f2_fixo, f3_fixo, F_fixo_arr))

            records.append({
                'alpha': alpha, 'draw': draw,
                'agg': agg, 'norm': norm, 'mont': mont,
                'nd_Fmm': nd_Fmm, 'nd_Fvec': nd_Fvec, 'nd_Ffixo': nd_Ffixo,
            })

print(f'MC concluído t={T()}', flush=True)

df_raw = pd.DataFrame(records)
df_raw.to_csv(os.path.join(RESULTS_DIR, 'mc_robustez_raw.csv'), index=False)

# ── Tabela resumo ─────────────────────────────────────────────────────────────
print('\n=== TABELA RESUMO 2×2+1 (Q2 via MC, média sobre 500 draws) ===')
for alpha in ALPHAS:
    df_a = df_raw[df_raw['alpha'] == alpha]
    summary = df_a.groupby(['norm', 'mont'])[['nd_Fmm', 'nd_Fvec', 'nd_Ffixo']].mean() * 100
    summary.columns = ['Q2_Fmm%', 'Q2_Fvec%', 'Q2_Ffixo%']
    print(f'\nalpha={alpha}:')
    print(summary.round(1).to_string())

df_sum = df_raw.groupby(['alpha', 'norm', 'mont'])[['nd_Fmm', 'nd_Fvec', 'nd_Ffixo']].mean().reset_index()
df_sum[['nd_Fmm', 'nd_Fvec', 'nd_Ffixo']] *= 100
df_sum.columns = ['alpha', 'norm', 'mont', 'Q2_Fmm_pct', 'Q2_Fvec_pct', 'Q2_Ffixo_pct']
df_sum.to_csv(os.path.join(RESULTS_DIR, 'mc_robustez_summary.csv'), index=False)

print(f'\nTotal t={T()}')
print('Salvos: mc_robustez_raw.csv, mc_robustez_summary.csv')
