# -*- coding: utf-8 -*-
"""
analyze_14cells.py — Round 13, tarefa 3
Modelo logístico misto (efeito fixo: norm+agg+mont; efeito aleatório: sorteio)
usando as 14 células válidas do mc_18cells_raw.csv.

Células excluídas:
  - ranks×topsis e ranks×vikor (bug de sinal — substituídas pelo mc corrigido)
  - VIKOR×vector = VIKOR×minmax (duplicata por invariância afim do VIKOR)

Estratégia sem pacote de efeitos mistos:
  - Estimativa pontual dos efeitos marginais via média dos 500 sorteios
  - IC 95% por bootstrap sobre os sorteios (unidade de aleatorização natural)
  - Contraste pareado: fixar agg e mont, variar norm (e vice-versa)

Run: uv run --with pandas --with numpy --with scipy python scripts/analyze_14cells.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from scipy import stats

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
raw_csv = os.path.join(RESULTS_DIR, "mc_18cells_raw.csv")

if not os.path.exists(raw_csv):
    print(f"FALTA: {raw_csv} — aguardar mc_18cells.py na Athena")
    sys.exit(1)

df = pd.read_csv(raw_csv)
print(f"Carregado: {len(df)} linhas, alpha={sorted(df['alpha'].unique())}")

# ─── Definir células válidas ───────────────────────────────────────────────────
# Excluir ranks×topsis e ranks×vikor (bug de sinal)
invalid_ranks = (df['norm'] == 'ranks') & (df['agg'].isin(['topsis', 'vikor']))
df_valid = df[~invalid_ranks].copy()

# Tratar VIKOR×vector = VIKOR×minmax: remover uma delas
# Mantemos VIKOR×minmax como célula canônica e removemos VIKOR×vector
vikor_vec = (df_valid['agg'] == 'vikor') & (df_valid['norm'] == 'vector')
df_14 = df_valid[~vikor_vec].copy()

# Células restantes
cells = df_14.groupby(['agg','norm','mont']).size().reset_index(name='n')
print(f"\nCélulas válidas: {len(cells)}")
print(cells.to_string(index=False))

def boot_marginal(df_sub, groupby_col, response, n_boot=1000, seed=42):
    """
    Efeito marginal em pp: range(média por nível do fator).
    IC bootstrap sobre os sorteios (unidade de bloco aleatório).
    """
    rng = np.random.default_rng(seed)
    draws = df_sub['draw'].unique()
    
    def point(d):
        m = d.groupby(groupby_col)[response].mean()
        return 100 * (m.max() - m.min()), m.to_dict()
    
    pe, means = point(df_sub)
    boots = []
    for _ in range(n_boot):
        bd = rng.choice(draws, size=len(draws), replace=True)
        sub = df_sub[df_sub['draw'].isin(bd)]
        boots.append(point(sub)[0])
    boots = np.array(boots)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return pe, lo, hi, means

def boot_contrast(df_sub, col_a, val_a, col_b, val_b, response, n_boot=1000, seed=42):
    """Contraste direto: média(val_a) - média(val_b)."""
    rng = np.random.default_rng(seed)
    draws = df_sub['draw'].unique()
    
    def point(d):
        ma = d[d[col_a]==val_a][response].mean()
        mb = d[d[col_b]==val_b][response].mean()
        return 100 * (ma - mb)
    
    pe = point(df_sub)
    boots = []
    for _ in range(n_boot):
        bd = rng.choice(draws, size=len(draws), replace=True)
        sub = df_sub[df_sub['draw'].isin(bd)]
        boots.append(point(sub))
    boots = np.array(boots)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return pe, lo, hi

for alpha in [50, 200]:
    df_a = df_14[df_14['alpha'] == alpha]
    print(f"\n{'='*65}")
    print(f"alpha={alpha}, Q2[A'], 14 células válidas (sem VIKOR×vector, sem ranks×TOPSIS/VIKOR)")
    print(f"{'='*65}")
    
    # ── Tabela por célula
    tbl = df_a.groupby(['agg','norm','mont']).agg(
        pct_Q2Ap=('nd_Q2Ap', lambda x: 100*x.mean()),
        pct_Q1Ap=('nd_Q1Ap', lambda x: 100*x.mean()),
        pct_Q2A =('nd_Q2A',  lambda x: 100*x.mean()),
        pct_Q1A =('nd_Q1A',  lambda x: 100*x.mean()),
    ).reset_index().sort_values('pct_Q2Ap', ascending=False)
    print("\n  Tabela por célula (Q2[A'], ordenada):")
    print(tbl.to_string(index=False, float_format=lambda x: f"{x:.1f}"))
    
    # ── Efeitos marginais globais
    print("\n  Efeitos marginais sobre Q2[A'] (14 células, bootstrap 1000):")
    print(f"  {'Fator':12s}  {'Efeito (pp)':>12}  {'IC 95%':>22}  {'Níveis (mean)':>30}")
    for factor in ['norm', 'agg', 'mont']:
        pe, lo, hi, means = boot_marginal(df_a, factor, 'nd_Q2Ap')
        means_str = "  ".join(f"{k}={v:.1f}%" for k,v in sorted(means.items(), key=lambda x:-x[1]))
        print(f"  {factor:12s}  {pe:12.1f}  [{lo:.1f}, {hi:.1f}]  {means_str}")
    
    # ── Efeito ref A→A' (sorteio como efeito aleatório, média sobre células)
    diff_ref = 100 * (df_a['nd_Q1Ap'] - df_a['nd_Q1A']).mean()
    print(f"\n  Efeito referência A→A' (Q1, média células): {diff_ref:.1f} pp")
    
    # ── Contrastes pareados limpos (mesmo agg e mont)
    print("\n  Contrastes pareados de normalização (SAW, greedy):")
    saw_g = df_a[(df_a['agg']=='saw') & (df_a['mont']=='greedy')]
    for n1, n2 in [('minmax','vector'), ('minmax','ranks'), ('ranks','vector')]:
        if n1 in saw_g['norm'].values and n2 in saw_g['norm'].values:
            pe, lo, hi = boot_contrast(saw_g, 'norm', n1, 'norm', n2, 'nd_Q2Ap')
            print(f"    {n1} − {n2}: {pe:+.1f} pp  [{lo:.1f}, {hi:.1f}]")
    
    print("\n  Contrastes pareados de normalização (TOPSIS, greedy):")
    top_g = df_a[(df_a['agg']=='topsis') & (df_a['mont']=='greedy')]
    for n1, n2 in [('minmax','vector')]:
        if n1 in top_g['norm'].values and n2 in top_g['norm'].values:
            pe, lo, hi = boot_contrast(top_g, 'norm', n1, 'norm', n2, 'nd_Q2Ap')
            print(f"    {n1} − {n2}: {pe:+.1f} pp  [{lo:.1f}, {hi:.1f}]")
    
    print("\n  Contrastes de montagem (norm=minmax):")
    mm = df_a[df_a['norm']=='minmax']
    for agg in ['saw','topsis','vikor']:
        sub = mm[mm['agg']==agg]
        if len(sub['mont'].unique()) == 2:
            pe, lo, hi = boot_contrast(sub, 'mont', 'optimal', 'mont', 'greedy', 'nd_Q2Ap')
            print(f"    {agg} ótimo − greedy: {pe:+.1f} pp  [{lo:.1f}, {hi:.1f}]")
    
    # ── Efeito de agregação (norm=minmax, greedy — sem garantia P1)
    print("\n  Efeito de agregação (minmax, greedy — exclui célula P1):")
    mm_g = df_a[(df_a['norm']=='minmax') & (df_a['mont']=='greedy')]
    pe, lo, hi, means = boot_marginal(mm_g, 'agg', 'nd_Q2Ap')
    means_str = "  ".join(f"{k}={v:.1f}%" for k,v in sorted(means.items(), key=lambda x:-x[1]))
    print(f"    amplitude: {pe:.1f} pp  [{lo:.1f}, {hi:.1f}]  |  {means_str}")
    
    # ── Nota sobre P1 na interpretação
    saw_opt = tbl[(tbl['agg']=='saw') & (tbl['norm']=='minmax') & (tbl['mont']=='optimal')]['pct_Q2Ap'].values
    if len(saw_opt):
        print(f"\n  Nota: SAW×mm×ótimo = {saw_opt[0]:.1f}% (P1 garante 100%; infla efeito de montagem)")

outpath = os.path.join(RESULTS_DIR, "analysis_14cells.csv")
df_14.groupby(['alpha','agg','norm','mont']).agg(
    pct_Q2Ap=('nd_Q2Ap', lambda x:100*x.mean()),
    pct_Q1Ap=('nd_Q1Ap', lambda x:100*x.mean()),
    pct_Q2A =('nd_Q2A',  lambda x:100*x.mean()),
    pct_Q1A =('nd_Q1A',  lambda x:100*x.mean()),
).reset_index().to_csv(outpath, index=False)
print(f"\nSalvo em {outpath}")
