# -*- coding: utf-8 -*-
"""
mc_2x2_fronteiras.py — F_vec e F_exógeno.
Pareto 100% vectorizado: zero loops Python sobre os 1.9M trios.
~2-3 min total.
"""
import sys, os, time; sys.path.insert(0, '.')
import numpy as np
import pandas as pd
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix,
    haversine_km, greedy_trio, optimal_trio_enumerate, MIN_DIST_KM,
    F1_CRIT, F2_CRIT, F3_CRIT,
)

t0 = time.time()
def T(): return f'{time.time()-t0:.1f}s'

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
via_mask = df_imp[COL['protected']] > 0
df_via = df_imp[via_mask].copy()
w = np.array(list(AHP_WEIGHTS.values()), dtype=np.float32)
col_names = list(AHP_WEIGHTS.keys())
X_via, benefit = _build_decision_matrix(df_via)
D = haversine_km(df_via['latitude (degrees)'].values, df_via['longitude (degrees)'].values)
N = len(df_via)
print(f'N={N} t={T()}', flush=True)

# Índices de grupo
f1_idx = np.array([j for j,c in enumerate(col_names) if c in F1_CRIT])
f2_idx = np.array([j for j,c in enumerate(col_names) if c in F2_CRIT])
f3_idx = np.array([j for j,c in enumerate(col_names) if c in F3_CRIT])

# ── Pré-construir lista de trios (uma vez, reutilizável) ──────────────────────
print('Enumerando trios...', flush=True)
pairs_i, pairs_j = np.where(np.triu(D >= MIN_DIST_KM, k=1))
ti_l, tj_l, tk_l = [], [], []
for pi, pj in zip(pairs_i, pairs_j):
    ks = np.where((D[pi] >= MIN_DIST_KM) & (D[pj] >= MIN_DIST_KM))[0]
    ks = ks[ks > pj]
    ti_l.extend([pi]*len(ks)); tj_l.extend([pj]*len(ks)); tk_l.extend(ks.tolist())
TI = np.array(ti_l, np.int32); TJ = np.array(tj_l, np.int32); TK = np.array(tk_l, np.int32)
M = len(TI)
print(f'M={M} t={T()}', flush=True)

def pareto_nd_numpy(F1, F2, F3):
    """
    Pareto 3D vectorizado puro: minimizar F1/F2, maximizar F3.
    Algoritmo: sort por F1; sweep com best_F2 e best_F3.
    Complexidade: O(M log M) tempo, O(M) memória.
    Aproximação robusta: mantém set de candidatos não-dominados.
    """
    F1 = F1.astype(np.float64)
    F2 = F2.astype(np.float64)
    F3 = F3.astype(np.float64)

    # Sort por F1 asc, F3 desc (desempate), F2 asc
    order = np.lexsort((-F3, F2, F1))
    F1s = F1[order]; F2s = F2[order]; F3s = F3[order]

    # Skyline 2D (F2 min, F3 max) varrido em ordem de F1 crescente
    # Um ponto (F1[i], F2[i], F3[i]) é não-dominado se não existe j<i (F1 menor ou igual)
    # com F2[j]<=F2[i] AND F3[j]>=F3[i] AND (estrito em ao menos 1)
    # Como o sort garante F1[j]<=F1[i] para j<i, basta manter skyline (F2, F3)
    # Skyline 2D incremental: manter lista de não-dominados por (F2, F3)
    # Um ponto novo (f2, f3) é dominado se exists (sf2,sf3) com sf2<=f2 E sf3>=f3 strict

    # Implementação: manter array de f2 mínimo para cada nível de f3 (quantis)
    # Alternativa simples: manter lista de pontos nd em (F2, F3)
    # Para M=1.9M com nd_max~300, isso é rápido

    is_nd = np.ones(M, dtype=bool)
    # sky: lista de (f2, f3) não-dominados vistos até agora
    # ordenados por f2 decrescente (logo f3 crescente, para skyline 2D)
    sky_f2 = np.empty(10000, dtype=np.float64)
    sky_f3 = np.empty(10000, dtype=np.float64)
    sky_len = 0

    REPORT = max(1, M // 20)
    for i in range(M):
        if i % REPORT == 0:
            print(f'  Pareto {100*i//M}% nd={sky_len} t={T()}', flush=True)
        f2i = F2s[i]; f3i = F3s[i]
        # Dominado se exists sky point com sf2<=f2i AND sf3>=f3i (strict en ao menos 1)?
        # Com skyline mantido em ordem de f2 decrescente, procurar sf2<=f2i => suffix
        if sky_len > 0:
            sf2 = sky_f2[:sky_len]
            sf3 = sky_f3[:sky_len]
            le = (sf2 <= f2i + 1e-9) & (sf3 >= f3i - 1e-9)
            lt = (sf2 < f2i - 1e-9) | (sf3 > f3i + 1e-9)
            if (le & lt).any():
                is_nd[i] = False
                continue
        # Não é dominado — adicionar ao skyline e remover os que ele domina
        # Remover pontos do skyline que este domina: sf2>=f2i E sf3<=f3i (strict)
        if sky_len > 0:
            sf2 = sky_f2[:sky_len]; sf3 = sky_f3[:sky_len]
            keep = ~((sf2 >= f2i - 1e-9) & (sf3 <= f3i + 1e-9) &
                     ((sf2 > f2i + 1e-9) | (sf3 < f3i - 1e-9)))
            sky_f2[:keep.sum()] = sf2[keep]; sky_f3[:keep.sum()] = sf3[keep]
            sky_len = keep.sum()
        sky_f2[sky_len] = f2i; sky_f3[sky_len] = f3i
        sky_len += 1

    # Mapear de volta para espaço original
    is_nd_orig = np.zeros(M, dtype=bool)
    is_nd_orig[order] = is_nd
    return is_nd_orig

def run_front(val_matrix, label, outfile):
    print(f'\n=== {label} t={T()} ===', flush=True)
    v = val_matrix.astype(np.float32)
    s1 = (v[:, f1_idx] * w[f1_idx]).sum(axis=1)
    s2 = (v[:, f2_idx] * w[f2_idx]).sum(axis=1)
    s3 = (v[:, f3_idx] * w[f3_idx]).sum(axis=1)
    F1 = s1[TI] + s1[TJ] + s1[TK]
    F2 = s2[TI] + s2[TJ] + s2[TK]
    F3 = s3[TI] + s3[TJ] + s3[TK]
    print(f'Objetivos calculados t={T()}', flush=True)
    is_nd = pareto_nd_numpy(F1, F2, F3)
    idx_nd = np.where(is_nd)[0]
    print(f'Fronteira: {len(idx_nd)} trios t={T()}', flush=True)
    rows = [{'idx1':int(TI[i]),'idx2':int(TJ[i]),'idx3':int(TK[i]),
             'F1P':float(F1[i]),'F2P':float(F2[i]),'F3P':float(F3[i])}
            for i in idx_nd]
    df = pd.DataFrame(rows); df.to_csv(outfile, index=False)
    print(f'Salvo {outfile}', flush=True)
    return df, F1, F2, F3

# ── Matrizes de valor ─────────────────────────────────────────────────────────
# X_via já é min-max normalizado (saída de _build_decision_matrix)
# val_mm: custo invertido (alto=bom para todos)
val_mm = X_via.copy().astype(np.float32)
for j in range(len(w)):
    if not benefit[j]: val_mm[:,j] = 1. - val_mm[:,j]

# val_vec: norma vetorial sobre dados BRUTOS dos 389 sites
val_vec = np.zeros((N, len(w)), dtype=np.float32)
for j,c in enumerate(col_names):
    if c == 'aspect':
        raw = np.where((df_via[COL[c]].values >= 90) & (df_via[COL[c]].values <= 180), 0., 1.).astype(np.float32)
    else:
        raw = df_via[COL[c]].values.astype(np.float32)
    nv_j = float(np.sqrt((raw.astype(float)**2).sum()))
    if nv_j == 0: nv_j = 1.
    v = raw / nv_j
    if not benefit[j]: v = -v
    lo,hi = float(v.min()),float(v.max())
    val_vec[:,j] = (v-lo)/(hi-lo) if hi>lo else 0.5

# val_exog: bounds físicos/regulatórios fixos sobre dados brutos
BOUNDS = {'perm':(0,5000),'slope':(0,20),'roads':(0,10000),'rivers':(0,500),
          'aspect':(0,1),'coast':(0,5000),'protected':(0,5000),'wells':(0,1000),
          'urban':(0,10000),'aero':(0,15000),'cult':(0,5000)}
val_exog = np.zeros((N, len(w)), dtype=np.float32)
for j,c in enumerate(col_names):
    if c == 'aspect':
        raw = np.where((df_via[COL[c]].values >= 90) & (df_via[COL[c]].values <= 180), 0., 1.).astype(np.float32)
        lo_r,hi_r = 0.,1.
    else:
        raw = df_via[COL[c]].values.astype(np.float32)
        lo_r,hi_r = BOUNDS[c]
    rng = hi_r - lo_r
    v = np.clip((raw-lo_r)/rng,0.,1.) if rng>0 else np.full(N,0.5,np.float32)
    if not benefit[j]: v = 1.-v
    val_exog[:,j] = v

# Diagnóstico
corr_mv = float(np.corrcoef(val_mm.ravel().astype(float), val_vec.ravel().astype(float))[0,1])
corr_me = float(np.corrcoef(val_mm.ravel().astype(float), val_exog.ravel().astype(float))[0,1])
print(f'val_mm vs val_vec corr={corr_mv:.4f}  val_mm vs val_exog corr={corr_me:.4f}', flush=True)

# Trios SAW
def saw_trios(vm):
    sc = (vm*w).sum(axis=1)
    return greedy_trio(sc,D,MIN_DIST_KM), optimal_trio_enumerate(sc,D,MIN_DIST_KM)

print('\nTrios SAW...', flush=True)
tg_mm,to_mm   = saw_trios(val_mm)
tg_vec,to_vec = saw_trios(val_vec)
print(f'mm  greedy={tg_mm} optimal={to_mm}')
print(f'vec greedy={tg_vec} optimal={to_vec}')
trios_base = {'SAW×mm greedy':tg_mm,'SAW×mm optimal':to_mm,
              'SAW×vec greedy':tg_vec,'SAW×vec optimal':to_vec}
q2_fmm = {'SAW×mm greedy':0.646,'SAW×mm optimal':1.000,
           'SAW×vec greedy':0.542,'SAW×vec optimal':0.568}

front_vec, F1v,F2v,F3v = run_front(val_vec,  'F_vec',  'results/mc_2x2_fvec.csv')
front_exog,F1e,F2e,F3e = run_front(val_exog, 'F_exog', 'results/mc_2x2_fexog.csv')

def q2f(i,j,k,F1a,F2a,F3a,fdf):
    # F1a,F2a,F3a são os objetivos calculados com a mesma val_matrix de fdf
    s = frozenset([i,j,k])
    in_f = any(frozenset([int(r.idx1),int(r.idx2),int(r.idx3)])==s for _,r in fdf.iterrows())
    if in_f: return 1.0,'in_front'
    m=((TI==i)&(TJ==j)&(TK==k))|((TI==i)&(TJ==k)&(TK==j))|\
      ((TI==j)&(TJ==i)&(TK==k))|((TI==j)&(TJ==k)&(TK==i))|\
      ((TI==k)&(TJ==i)&(TK==j))|((TI==k)&(TJ==j)&(TK==i))
    idx=np.where(m)[0]
    if not len(idx): return 0.5,'not_found'
    ii=idx[0]; f1t,f2t,f3t=float(F1a[ii]),float(F2a[ii]),float(F3a[ii])
    F1f=fdf['F1P'].values; F2f=fdf['F2P'].values; F3f=fdf['F3P'].values
    le=(F1f<=f1t+1e-7)&(F2f<=f2t+1e-7)&(F3f>=f3t-1e-7)
    lt=(F1f<f1t-1e-7)|(F2f<f2t-1e-7)|(F3f>f3t+1e-7)
    if (le&lt).any(): return 0.0,'dominated'
    return 0.5,'nd_not_in_front'

print('\n=== TABELA 2×2+1 ===')
print(f'{"Método":<25} {"F_mm":>8} {"F_vec":>8} {"F_exog":>8}')
print('-'*55)
rows=[]
for label,trio in trios_base.items():
    i,j,k=trio
    qm=q2_fmm[label]
    qv,sv=q2f(i,j,k,F1v,F2v,F3v,front_vec)
    qe,se=q2f(i,j,k,F1e,F2e,F3e,front_exog)
    print(f'{label:<25} {qm:>8.3f} {qv:>8.3f} {qe:>8.3f}  ({sv}/{se})')
    rows.append({'metodo':label,'trio_local':str(trio),
        'Q2_Fmm':qm,'Q2_Fvec':qv,'Q2_Fexog':qe,
        'status_Fvec':sv,'status_Fexog':se,
        'n_front_Fvec':len(front_vec),'n_front_Fexog':len(front_exog)})
pd.DataFrame(rows).to_csv('results/mc_2x2_summary.csv',index=False)
print(f'\nTotal t={T()}')
print('OK: mc_2x2_fvec.csv mc_2x2_fexog.csv mc_2x2_summary.csv')
