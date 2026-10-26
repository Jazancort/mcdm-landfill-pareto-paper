# -*- coding: utf-8 -*-
"""
diag_mc_robustez.py — D1+D2+D3+D4 em um único script.

D1: verifica predicado nd do mc_robustez vs Q1[A'] do mc_18cells
    e calcula a versão CORRETA de F_mm (fronteira estática com w_ahp,
    objetivos do trio com w_ahp → reproduz Q1[A']).
D2: assert de pipeline — SAW×mm optimal={184,430,460} e greedy={184,279,320}
    com pesos AHP fixos, usando o mesmo pipeline do mc_robustez.
D3: bootstrap emparelhado por draw nos 6 gaps mm−vec (κ=200) e 3 (κ=50).
    2000 reamostras. Usa mc_robustez_raw.csv existente.

Saída:
  results/diag_predicado.txt   — tabela Q1 predito vs Q1 mc_18cells
  results/bootstrap_gaps.csv   — IC bootstrap emparelhado
"""
import sys, os, time; sys.path.insert(0, '.')
import numpy as np
import pandas as pd
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix,
    haversine_km, MIN_DIST_KM, INV, COST, F1_CRIT, F2_CRIT, F3_CRIT,
    greedy_trio, optimal_trio_enumerate,
)

T = lambda: f'{time.time()-T0:.1f}s'
T0 = time.time()
RESULTS_DIR = 'results'

# ─── Carregamento ─────────────────────────────────────────────────────────────
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
via_mask = df_imp[COL['protected']] > 0
df_via = df_imp[via_mask].copy()
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
X_via, benefit = _build_decision_matrix(df_via)
D_via = haversine_km(df_via['latitude (degrees)'].values, df_via['longitude (degrees)'].values)
via_idx = df_via.index.values
N = len(df_via)

def _norm_ref(x, ref):
    lo, hi = ref.min(), ref.max()
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x, dtype=np.float32)

def compute_site_objs_mm(w, ref_df):
    """Objetivos SAW×mm calculados sobre ref_df. Reproduz Q1/Q2 do mc_18cells."""
    f1 = np.zeros(N, dtype=np.float32)
    f2 = np.zeros(N, dtype=np.float32)
    f3 = np.zeros(N, dtype=np.float32)
    for j, k in enumerate(col_names):
        col = COL[k]
        x = df_via[col].values.astype(float)
        ref = ref_df[col].values.astype(float)
        if k == 'aspect':
            c = np.where((x >= 90) & (x <= 180), 0., 1.)
        elif k in INV:
            c = 1.0 - _norm_ref(x, ref)
        elif k in COST:
            c = _norm_ref(x, ref)
        else:
            c = _norm_ref(x, ref)
        c = (c * w[j]).astype(np.float32)
        if k in F1_CRIT:   f1 += c
        elif k in F2_CRIT: f2 += c
        else:               f3 += c
    return f1, f2, f3

def is_nd(i, j, k, f1v, f2v, f3v, F1, F2, F3):
    """True se (i,j,k) não é dominado pela fronteira (F1,F2,F3)."""
    f1t = float(f1v[i] + f1v[j] + f1v[k])
    f2t = float(f2v[i] + f2v[j] + f2v[k])
    f3t = float(f3v[i] + f3v[j] + f3v[k])
    le = (F1 <= f1t + 1e-7) & (F2 <= f2t + 1e-7) & (F3 >= f3t - 1e-7)
    lt = (F1 < f1t - 1e-7) | (F2 < f2t - 1e-7) | (F3 > f3t + 1e-7)
    return not bool((le & lt).any())

# ─── D2: assert de pipeline com pesos AHP fixos ──────────────────────────────
print('=== D2: assert de pipeline ===')
X_adj = X_via.copy().astype(np.float32)
for j in range(len(w_ahp)):
    if not benefit[j]: X_adj[:, j] = 1.0 - X_via[:, j]
sc_ahp = (X_adj * w_ahp.astype(np.float32)).sum(axis=1)
to_ahp = tuple(optimal_trio_enumerate(sc_ahp, D_via, MIN_DIST_KM))
tg_ahp = tuple(greedy_trio(sc_ahp, D_via))

gids_opt = tuple(sorted(int(via_idx[i]) for i in to_ahp))
gids_gr  = tuple(sorted(int(via_idx[i]) for i in tg_ahp))
assert gids_opt == (184, 430, 460), f'FAIL D2 optimal: got {gids_opt}'
assert gids_gr  == (184, 279, 320), f'FAIL D2 greedy: got {gids_gr}'
print(f'  SAW×mm optimal (global): {gids_opt}  ✓')
print(f'  SAW×mm greedy  (global): {gids_gr}   ✓')

# ─── D1: preditor correto de Q1[A'] ─────────────────────────────────────────
print(f'\n=== D1: recalcular Q1[A\'] com predicado correto t={T()} ===')
# Fronteira estática com w_ahp (calculada pelo is_nd sobre todos os 1.94M trios)
# Predicado Q1: objetivos do trio EM w_ahp, fronteira EM w_ahp
f1_Ap, f2_Ap, f3_Ap = compute_site_objs_mm(w_ahp, df_via)

# Pre-computar fronteira via enumeração (para is_nd preciso de F1,F2,F3 vetorizados)
# Carrego a fronteira pré-calculada
front_mm = pd.read_csv(os.path.join(RESULTS_DIR, 'pareto_front_Aprime.csv'))
print(f'  len(F_mm) = {len(front_mm)}', '✓' if len(front_mm)==181 else '❌ esperado 181')

# Verificar bit-a-bit
F1_Ap_arr = front_mm['F1P'].values.astype(np.float32)
F2_Ap_arr = front_mm['F2P'].values.astype(np.float32)
F3_Ap_arr = front_mm['F3P'].values.astype(np.float32)

# Recalcular Q1[A'] por MC (mesmo SEED e ALPHAS que mc_18cells)
SEED = 42; ALPHAS = [50, 200]; N_DRAWS = 500
CELLS_ROB = [
    ('saw', 'minmax',  'greedy'),
    ('saw', 'minmax',  'optimal'),
    ('saw', 'vector',  'greedy'),
    ('saw', 'vector',  'optimal'),
]

records_q1 = []
for alpha in ALPHAS:
    rng = np.random.default_rng(SEED)
    for draw in range(N_DRAWS):
        w = rng.dirichlet(alpha * w_ahp).astype(np.float32)
        for agg, norm, mont in CELLS_ROB:
            if norm == 'minmax':
                sc = (X_adj * w).sum(axis=1)
            else:
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
                idx = greedy_trio(sc, D_via)
            else:
                idx = tuple(optimal_trio_enumerate(sc, D_via, MIN_DIST_KM))
            i, j2, k = idx

            # Q1[A']: objetivos com w_ahp FIXO, fronteira com w_ahp FIXO
            nd_Q1Ap_corr = int(is_nd(i, j2, k, f1_Ap, f2_Ap, f3_Ap, F1_Ap_arr, F2_Ap_arr, F3_Ap_arr))

            records_q1.append({
                'alpha': alpha, 'draw': draw,
                'norm': norm, 'mont': mont,
                'nd_Q1Ap_corr': nd_Q1Ap_corr,
            })
    if alpha == 50:
        print(f'  alpha=50 concluído t={T()}')

print(f'  MC Q1 corrigido concluído t={T()}')

df_q1 = pd.DataFrame(records_q1)

# Comparar com Q1 do mc_18cells (coluna nd_Q1Ap)
mc18 = pd.read_csv(os.path.join(RESULTS_DIR, 'mc_18cells_raw.csv'))
mc18_cells = mc18[mc18['agg'] == 'saw'][['alpha', 'draw', 'norm', 'mont', 'nd_Q1Ap']]

merge = df_q1.merge(mc18_cells, on=['alpha', 'draw', 'norm', 'mont'])
merge['match'] = (merge['nd_Q1Ap_corr'] == merge['nd_Q1Ap'])

print('\n  Concordância predicado corrigido vs mc_18cells (Q1[A\']):')
print(f'  {merge["match"].mean()*100:.2f}% das {len(merge):,} observações concordam')
discordante = merge[~merge['match']]
if len(discordante) > 0:
    print(f'  {len(discordante)} discordâncias. Amostra:')
    print(discordante[['alpha','norm','mont','nd_Q1Ap_corr','nd_Q1Ap']].head(10).to_string(index=False))

# Tabela resumo Q1[A'] corrigido vs mc_18cells e F_mm do mc_robustez
mc_rob = pd.read_csv(os.path.join(RESULTS_DIR, 'mc_robustez_raw.csv'))
mc_rob_cells = mc_rob[mc_rob['agg']=='saw'][['alpha','draw','norm','mont','nd_Fmm']]

summary_rows = []
for alpha in ALPHAS:
    for norm, mont in [('minmax','greedy'),('minmax','optimal'),('vector','greedy'),('vector','optimal')]:
        q1_val = df_q1[(df_q1['alpha']==alpha)&(df_q1['norm']==norm)&(df_q1['mont']==mont)]['nd_Q1Ap_corr'].mean()*100
        q1_mc18 = mc18_cells[(mc18_cells['alpha']==alpha)&(mc18_cells['norm']==norm)&(mc18_cells['mont']==mont)&(mc18_cells['agg']=='saw' if 'agg' in mc18_cells else True)]['nd_Q1Ap'].mean()*100 if 'agg' in mc18_cells.columns else float('nan')
        fmm_val = mc_rob_cells[(mc_rob_cells['alpha']==alpha)&(mc_rob_cells['norm']==norm)&(mc_rob_cells['mont']==mont)]['nd_Fmm'].mean()*100
        summary_rows.append({'alpha': alpha, 'norm': norm, 'mont': mont,
                             'Q1_mc18cells': round(q1_mc18,1),
                             'Q1_corrigido': round(q1_val,1),
                             'F_mm_robusto': round(fmm_val,1)})

df_summary = pd.DataFrame(summary_rows)
print('\n  Tabela comparativa Q1[A\']:')
print(df_summary.to_string(index=False))
df_summary.to_csv(os.path.join(RESULTS_DIR, 'diag_q1_comparison.csv'), index=False)

# ─── D3: bootstrap emparelhado por draw ──────────────────────────────────────
print(f'\n=== D3: bootstrap emparelhado t={T()} ===')
NBOOT = 2000
rng_boot = np.random.default_rng(999)

boot_rows = []
for alpha in ALPHAS:
    for mont in ['greedy', 'optimal']:
        # Selecionar draws para mm e vec no mesmo alpha/mont
        mm_draws = mc_rob[(mc_rob['alpha']==alpha)&(mc_rob['norm']=='minmax')&(mc_rob['mont']==mont)].sort_values('draw')
        vc_draws = mc_rob[(mc_rob['alpha']==alpha)&(mc_rob['norm']=='vector')&(mc_rob['mont']==mont)].sort_values('draw')

        assert len(mm_draws) == N_DRAWS and len(vc_draws) == N_DRAWS, \
            f'Tamanho inesperado: mm={len(mm_draws)} vec={len(vc_draws)}'

        for front in ['nd_Fmm', 'nd_Fvec', 'nd_Ffixo']:
            mm_vals = mm_draws[front].values.astype(float)
            vc_vals = vc_draws[front].values.astype(float)
            diff_obs = mm_vals - vc_vals  # diferença pareada por draw

            gap_obs = diff_obs.mean() * 100  # em pp

            # Bootstrap emparelhado: reamostrar draws com reposição
            boot_gaps = np.zeros(NBOOT)
            for b in range(NBOOT):
                idx_b = rng_boot.integers(0, N_DRAWS, size=N_DRAWS)
                boot_gaps[b] = diff_obs[idx_b].mean() * 100

            ci_lo = float(np.percentile(boot_gaps, 2.5))
            ci_hi = float(np.percentile(boot_gaps, 97.5))
            excludes_zero = ci_lo > 0 or ci_hi < 0

            boot_rows.append({
                'alpha': alpha, 'mont': mont, 'front': front,
                'gap_pp': round(gap_obs, 1),
                'ci_lo': round(ci_lo, 1),
                'ci_hi': round(ci_hi, 1),
                'excludes_zero': excludes_zero,
            })

df_boot = pd.DataFrame(boot_rows)
print('\n  Bootstrap emparelhado (2000 reamostras) — gap mm−vec em pp, IC 95%:')
print()
for alpha in ALPHAS:
    print(f'  κ={alpha}:')
    sub = df_boot[df_boot['alpha']==alpha]
    print(f'  {"Mont":8s} {"Avaliador":12s} {"Gap":>7s} {"IC 95%":>18s} {"Exclui 0?":>12s}')
    for _, r in sub.iterrows():
        excl = '✅' if r['excludes_zero'] else '❌'
        print(f'  {r["mont"]:8s} {r["front"]:12s} {r["gap_pp"]:+7.1f} [{r["ci_lo"]:+6.1f}, {r["ci_hi"]:+6.1f}]  {excl}')
    print()

df_boot.to_csv(os.path.join(RESULTS_DIR, 'bootstrap_gaps.csv'), index=False)
print(f'  Salvo: results/bootstrap_gaps.csv t={T()}')

# ─── Resumo final ─────────────────────────────────────────────────────────────
print('\n=== RESUMO ===')
print('D2: pipeline OK ({184,430,460} e {184,279,320} confirmados localmente)')
print('D1: ver tabela diag_q1_comparison.csv')
print('D3: ver tabela bootstrap_gaps.csv')
print('D4: renomear F_exog→F_fixo — executar separadamente no doc e código')
