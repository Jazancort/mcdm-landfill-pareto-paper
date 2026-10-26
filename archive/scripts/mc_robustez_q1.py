# -*- coding: utf-8 -*-
"""
mc_robustez_q1.py — MC de robustez ao avaliador com predicado Q1 COERENTE.

Predicado: score com w_draw (escolhe o trio); objetivos do trio e da fronteira
calculados com w_AHP FIXO. Idêntico ao nd_Q1Ap do mc_18cells.py.

  nd_Fmm  = is_nd(trio[w_draw], f_mm[w_ahp],  F_mm[w_ahp])
  nd_Fvec = is_nd(trio[w_draw], f_vec[w_ahp],  F_vec[w_ahp])
  nd_Ffixo= is_nd(trio[w_draw], f_fixo[w_ahp], F_fixo[w_ahp])

Gate: nd_Fmm deve reproduzir Q1[A'] da secao 10 dentro de +/-5 pp.
  §10 κ=200: mm greedy=70.0% optimal=89.4% vec greedy=12.8% vec optimal=31.6%
  §10 κ=50:  mm greedy=72.6% optimal=83.8% vec greedy=50.6% vec optimal=59.0%

Salva: results/mc_robustez_q1_raw.csv
       results/mc_robustez_q1_summary.csv
       results/bootstrap_q1_gaps.csv
"""
import sys, os, time; sys.path.insert(0, '.')
import numpy as np
import pandas as pd
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix,
    haversine_km, MIN_DIST_KM, INV, COST, F1_CRIT, F2_CRIT, F3_CRIT,
    greedy_trio, optimal_trio_enumerate,
)

T0 = time.time()
T = lambda: f'{time.time()-T0:.1f}s'
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
N = len(df_via)
print(f'N={N} t={T()}', flush=True)

# ─── Asserts Gate R1 (herdados) ───────────────────────────────────────────────
assert abs(MIN_DIST_KM - 10.0) < 1e-6, f'GATE R1 FAIL: MIN_DIST_KM={MIN_DIST_KM}'
assert N == 389, f'GATE R1 FAIL: N={N}'
print(f'Gate R1 basico OK t={T()}', flush=True)

# ─── X_adj para SAWxmm ────────────────────────────────────────────────────────
X_adj = X_via.copy().astype(np.float32)
for j in range(len(w_ahp)):
    if not benefit[j]: X_adj[:, j] = 1.0 - X_via[:, j]

# ─── Pré-calcular trios viáveis ───────────────────────────────────────────────
print('Enumerando trios viáveis...', flush=True)
pairs_i, pairs_j = np.where(np.triu(D_via >= MIN_DIST_KM, k=1))
ti_l, tj_l, tk_l = [], [], []
for pi, pj in zip(pairs_i, pairs_j):
    ks = np.where((D_via[pi] >= MIN_DIST_KM) & (D_via[pj] >= MIN_DIST_KM))[0]
    ks = ks[ks > pj]
    ti_l.extend([pi]*len(ks)); tj_l.extend([pj]*len(ks)); tk_l.extend(ks.tolist())
trio_arr = np.stack([ti_l, tj_l, tk_l], axis=1).astype(np.int32)
print(f'M={len(trio_arr)} t={T()}', flush=True)

# ─── Carregar fronteiras ──────────────────────────────────────────────────────
front_mm   = pd.read_csv(os.path.join(RESULTS_DIR, 'pareto_front_Aprime.csv'))
front_vec  = pd.read_csv(os.path.join(RESULTS_DIR, 'mc_2x2_fvec.csv'))
front_fixo = pd.read_csv(os.path.join(RESULTS_DIR, 'mc_2x2_ffixo.csv'))
print(f'Fronteiras: F_mm={len(front_mm)} F_vec={len(front_vec)} F_fixo={len(front_fixo)} t={T()}', flush=True)

# ─── Objetivos FIXOS com w_AHP para cada fronteira ────────────────────────────
# Estas são as f1/f2/f3 usadas no teste de dominância — calculadas UMA VEZ com w_ahp.
# Mesma lógica do mc_18cells: f1_Ap, f2_Ap, f3_Ap = compute_objs(w_ahp, df_via)

def _norm(x, ref):
    lo, hi = ref.min(), ref.max()
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x, dtype=np.float32)

def compute_objs_w(w, val_matrix=None):
    """
    Calcula f1/f2/f3 por site com pesos w.
    val_matrix: se fornecido, usa essa matriz de funções de valor (N x ncrit).
                Senão, usa min-max sobre df_via (ref=389).
    """
    if val_matrix is not None:
        f1v = (val_matrix[:, [j for j,c in enumerate(col_names) if c in F1_CRIT]]
               * w[[j for j,c in enumerate(col_names) if c in F1_CRIT]]).sum(axis=1)
        f2v = (val_matrix[:, [j for j,c in enumerate(col_names) if c in F2_CRIT]]
               * w[[j for j,c in enumerate(col_names) if c in F2_CRIT]]).sum(axis=1)
        f3v = (val_matrix[:, [j for j,c in enumerate(col_names) if c in F3_CRIT]]
               * w[[j for j,c in enumerate(col_names) if c in F3_CRIT]]).sum(axis=1)
        return f1v.astype(np.float32), f2v.astype(np.float32), f3v.astype(np.float32)
    f1v = np.zeros(N, dtype=np.float32)
    f2v = np.zeros(N, dtype=np.float32)
    f3v = np.zeros(N, dtype=np.float32)
    for j, k in enumerate(col_names):
        col = COL[k]; x = df_via[col].values.astype(float); ref = df_via[col].values.astype(float)
        if k == 'aspect': c = np.where((x >= 90) & (x <= 180), 0., 1.)
        elif k in INV:    c = 1.0 - _norm(x, ref)
        elif k in COST:   c = _norm(x, ref)
        else:             c = _norm(x, ref)
        c = (c * w[j]).astype(np.float32)
        if k in F1_CRIT:   f1v += c
        elif k in F2_CRIT: f2v += c
        else:               f3v += c
    return f1v, f2v, f3v

# val_mm fixa (min-max ref=df_via) — para f_mm_ahp, f_vec_ahp, f_fixo_ahp
val_mm = np.zeros((N, len(w_ahp)), dtype=np.float32)
for j, k in enumerate(col_names):
    col = COL[k]; x = df_via[col].values.astype(float); ref = df_via[col].values.astype(float)
    if k == 'aspect': c = np.where((x>=90)&(x<=180), 0., 1.)
    elif k in INV:    c = 1.0 - _norm(x, ref)
    elif k in COST:   c = _norm(x, ref)
    else:             c = _norm(x, ref)
    val_mm[:, j] = c.astype(np.float32)

# val_vec fixa (norma vetorial sobre dados brutos)
val_vec = np.zeros((N, len(w_ahp)), dtype=np.float32)
for j, c in enumerate(col_names):
    if c == 'aspect':
        raw = np.where((df_via[COL[c]].values >= 90) & (df_via[COL[c]].values <= 180), 0., 1.).astype(np.float32)
    else:
        raw = df_via[COL[c]].values.astype(np.float32)
    nv = float(np.sqrt((raw.astype(float)**2).sum())); nv = nv if nv > 0 else 1.
    v = raw / nv
    if not benefit[j]: v = -v
    lo, hi = float(v.min()), float(v.max())
    val_vec[:, j] = ((v - lo) / (hi - lo) if hi > lo else 0.5)

# val_fixo (bounds convencionais declarados a priori)
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

# Objetivos FIXOS com w_AHP para as três fronteiras
f1_mm_ahp,  f2_mm_ahp,  f3_mm_ahp  = compute_objs_w(w_ahp.astype(np.float32), val_mm)
f1_vec_ahp, f2_vec_ahp, f3_vec_ahp = compute_objs_w(w_ahp.astype(np.float32), val_vec)
f1_fix_ahp, f2_fix_ahp, f3_fix_ahp = compute_objs_w(w_ahp.astype(np.float32), val_fixo)

# Arrays das fronteiras
F_mm_arr   = front_mm[['F1P','F2P','F3P']].values.astype(np.float32)
F_vec_arr  = front_vec[['F1P','F2P','F3P']].values.astype(np.float32)
F_fixo_arr = front_fixo[['F1P','F2P','F3P']].values.astype(np.float32)

# ─── Predicado nd ─────────────────────────────────────────────────────────────
def is_nd_fn(i, j, k, f1v, f2v, f3v, F1, F2, F3):
    """True se (i,j,k) com objetivos f calculados com w_ahp nao e dominado pela fronteira F."""
    f1t = float(f1v[i] + f1v[j] + f1v[k])
    f2t = float(f2v[i] + f2v[j] + f2v[k])
    f3t = float(f3v[i] + f3v[j] + f3v[k])
    le = (F1 <= f1t + 1e-7) & (F2 <= f2t + 1e-7) & (F3 >= f3t - 1e-7)
    lt = (F1 < f1t - 1e-7) | (F2 < f2t - 1e-7) | (F3 > f3t + 1e-7)
    return not bool((le & lt).any())

# ─── Funções de trio ──────────────────────────────────────────────────────────
def greedy_fast(scores):
    order = np.argsort(-scores)
    chosen = []
    for idx in order:
        if all(D_via[idx, c] >= MIN_DIST_KM for c in chosen):
            chosen.append(int(idx))
        if len(chosen) == 3: break
    return tuple(chosen)

def optimal_fast(scores):
    st = scores[trio_arr[:, 0]] + scores[trio_arr[:, 1]] + scores[trio_arr[:, 2]]
    best = trio_arr[st.argmax()]
    return (int(best[0]), int(best[1]), int(best[2]))

# ─── Loop MC ──────────────────────────────────────────────────────────────────
CELLS = [
    ('saw', 'minmax',  'greedy'),
    ('saw', 'minmax',  'optimal'),
    ('saw', 'vector',  'greedy'),
    ('saw', 'vector',  'optimal'),
]
N_DRAWS = 500
SEED    = 42
ALPHAS  = [50, 200]

# Valores esperados para gate (§10 mc_18cells Q1[A'])
Q1_CANON = {
    (200,'minmax','greedy'):  70.0, (200,'minmax','optimal'): 89.4,
    (200,'vector','greedy'):  12.8, (200,'vector','optimal'): 31.6,
    (50, 'minmax','greedy'):  72.6, (50, 'minmax','optimal'): 83.8,
    (50, 'vector','greedy'):  50.6, (50, 'vector','optimal'): 59.0,
}
GATE_TOL = 5.0  # pp

print(f'\n{len(CELLS)} celulas x {N_DRAWS} sorteios x {len(ALPHAS)} alphas x 3 avaliadores', flush=True)
print(f'Iniciando MC t={T()}', flush=True)

records = []
for alpha in ALPHAS:
    print(f'  alpha={alpha}', flush=True)
    rng = np.random.default_rng(SEED)
    for draw in range(N_DRAWS):
        if draw % 100 == 0:
            print(f'    draw={draw} t={T()}', flush=True)
        w = rng.dirichlet(alpha * w_ahp).astype(np.float32)

        for agg, norm, mont in CELLS:
            # (a) Score com w_draw — escolhe o trio
            if norm == 'minmax':
                sc = (X_adj * w).sum(axis=1)
            else:
                Xraw = np.zeros((N, len(w)), dtype=np.float32)
                for j2, c2 in enumerate(col_names):
                    if c2 == 'aspect':
                        raw = np.where((df_via[COL[c2]].values >= 90) & (df_via[COL[c2]].values <= 180), 0., 1.).astype(np.float32)
                    else:
                        raw = df_via[COL[c2]].values.astype(np.float32)
                    nv_j = float(np.sqrt((raw.astype(float)**2).sum())); nv_j = nv_j if nv_j > 0 else 1.
                    v = raw / nv_j
                    if not benefit[j2]: v = -v
                    lo2, hi2 = float(v.min()), float(v.max())
                    Xraw[:, j2] = (v - lo2) / (hi2 - lo2) if hi2 > lo2 else 0.5
                sc = (Xraw * w).sum(axis=1)

            if mont == 'greedy':
                i, j2, k = greedy_fast(sc)
            else:
                i, j2, k = optimal_fast(sc)

            # (b) Objetivos do trio com w_AHP FIXO — (c) Fronteira com w_AHP FIXO
            nd_Fmm  = int(is_nd_fn(i, j2, k, f1_mm_ahp,  f2_mm_ahp,  f3_mm_ahp,
                                   F_mm_arr[:,0],  F_mm_arr[:,1],  F_mm_arr[:,2]))
            nd_Fvec = int(is_nd_fn(i, j2, k, f1_vec_ahp, f2_vec_ahp, f3_vec_ahp,
                                   F_vec_arr[:,0], F_vec_arr[:,1], F_vec_arr[:,2]))
            nd_Ffixo= int(is_nd_fn(i, j2, k, f1_fix_ahp, f2_fix_ahp, f3_fix_ahp,
                                   F_fixo_arr[:,0],F_fixo_arr[:,1],F_fixo_arr[:,2]))

            records.append({
                'alpha': alpha, 'draw': draw,
                'agg': agg, 'norm': norm, 'mont': mont,
                'nd_Fmm': nd_Fmm, 'nd_Fvec': nd_Fvec, 'nd_Ffixo': nd_Ffixo,
            })

print(f'MC concluido t={T()}', flush=True)
df_raw = pd.DataFrame(records)
df_raw.to_csv(os.path.join(RESULTS_DIR, 'mc_robustez_q1_raw.csv'), index=False)

# ─── Tabela resumo ────────────────────────────────────────────────────────────
print('\n=== TABELA Q1 sob 3 avaliadores ===')
for alpha in ALPHAS:
    df_a = df_raw[df_raw['alpha'] == alpha]
    summary = df_a.groupby(['norm', 'mont'])[['nd_Fmm', 'nd_Fvec', 'nd_Ffixo']].mean() * 100
    summary.columns = ['Q1_Fmm%', 'Q1_Fvec%', 'Q1_Ffixo%']
    print(f'\nkappa={alpha}:')
    print(summary.round(1).to_string())

df_sum = df_raw.groupby(['alpha','norm','mont'])[['nd_Fmm','nd_Fvec','nd_Ffixo']].mean().reset_index()
df_sum[['nd_Fmm','nd_Fvec','nd_Ffixo']] *= 100
df_sum.columns = ['alpha','norm','mont','Q1_Fmm_pct','Q1_Fvec_pct','Q1_Ffixo_pct']
df_sum.to_csv(os.path.join(RESULTS_DIR, 'mc_robustez_q1_summary.csv'), index=False)

# ─── Gate: F_mm deve reproduzir §10 Q1[A'] ───────────────────────────────────
print('\n=== GATE: Q1_Fmm vs Q1[A\'] da secao 10 ===')
fails = []
for alpha in ALPHAS:
    for norm, mont in [('minmax','greedy'),('minmax','optimal'),('vector','greedy'),('vector','optimal')]:
        got = df_sum[(df_sum.alpha==alpha)&(df_sum.norm==norm)&(df_sum.mont==mont)]['Q1_Fmm_pct'].values[0]
        exp = Q1_CANON[(alpha, norm, mont)]
        delta = got - exp
        status = 'PASS' if abs(delta) <= GATE_TOL else 'FAIL'
        if status == 'FAIL': fails.append((alpha, norm, mont, got, exp, delta))
        print(f'  kappa={alpha} {norm:7s} {mont:7s}: got={got:.1f}% exp={exp:.1f}% delta={delta:+.1f}pp  {status}')

if fails:
    print(f'\n{len(fails)} FALHAS no gate. Investigar antes de publicar.')
else:
    print('\nGATE PASSOU: F_mm reproduz §10 dentro de +/-5 pp em todas as 8 celulas.')

# ─── Bootstrap emparelhado ───────────────────────────────────────────────────
print(f'\n=== Bootstrap emparelhado D3 (2000 reamostras) t={T()} ===')
NBOOT = 2000
rng_boot = np.random.default_rng(999)
boot_rows = []

for alpha in ALPHAS:
    for mont in ['greedy', 'optimal']:
        mm_d = df_raw[(df_raw.alpha==alpha)&(df_raw.norm=='minmax')&(df_raw.mont==mont)].sort_values('draw')
        vc_d = df_raw[(df_raw.alpha==alpha)&(df_raw.norm=='vector')&(df_raw.mont==mont)].sort_values('draw')
        for front in ['nd_Fmm', 'nd_Fvec', 'nd_Ffixo']:
            mm_v = mm_d[front].values.astype(float)
            vc_v = vc_d[front].values.astype(float)
            diff = mm_v - vc_v
            gap = diff.mean() * 100
            boots = np.array([diff[rng_boot.integers(0, N_DRAWS, N_DRAWS)].mean()*100 for _ in range(NBOOT)])
            ci_lo = float(np.percentile(boots, 2.5))
            ci_hi = float(np.percentile(boots, 97.5))
            excl = ci_lo > 0 or ci_hi < 0
            boot_rows.append({'alpha':alpha,'mont':mont,'front':front,
                              'gap_pp':round(gap,1),'ci_lo':round(ci_lo,1),'ci_hi':round(ci_hi,1),
                              'excludes_zero': excl})

df_boot = pd.DataFrame(boot_rows)
df_boot.to_csv(os.path.join(RESULTS_DIR, 'bootstrap_q1_gaps.csv'), index=False)

print('\nBootstrap emparelhado (Q1 coerente):')
for alpha in ALPHAS:
    print(f'\n  kappa={alpha}:')
    sub = df_boot[df_boot.alpha==alpha]
    print(f'  {"Mont":8s} {"Avaliador":12s} {"Gap":>7s} {"IC 95%":>20s} {"Excl0?"}')
    for _, r in sub.iterrows():
        e = 'SIM' if r['excludes_zero'] else 'NAO'
        print(f'  {r["mont"]:8s} {r["front"]:12s} {r["gap_pp"]:+7.1f} [{r["ci_lo"]:+6.1f}, {r["ci_hi"]:+6.1f}]  {e}')

print(f'\nTotal t={T()}')
print('Salvos: mc_robustez_q1_raw.csv, mc_robustez_q1_summary.csv, bootstrap_q1_gaps.csv')
