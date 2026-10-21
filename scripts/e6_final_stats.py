# -*- coding: utf-8 -*-
"""
e6_final_stats.py  --  Estatisticas finais corrigidas para E6 PRESPEC.

Correccoes em relacao a e6_decompose_ties.py:
  P2: adicionar teste Q2(H) < Q2(L) entre instancias com alguma perda
      (exclui nivel 0 = M para nao confundir com P1)
  P4: usar teste bilateral; reportar p correcto para zero_inflated (0.092, nao 0.044)
  P3/P4: desvios DEV-E6-001 a DEV-E6-004

Fonte: results/e6/e6_raw_prespec.csv
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import binomtest

ROOT = Path(__file__).parent.parent
df = pd.read_csv(ROOT / "results" / "e6" / "e6_raw_prespec.csv")

FAMILIES = ['lognormal', 'beta13', 'uniform', 'zero_inflated']
FOGO_W_LOSS = 35.8   # E1 celula W: 100% - 64.2%

print("=" * 70)
print("E6 -- ESTATISTICAS FINAIS CORRIGIDAS")
print("=" * 70)

# ── P1 ────────────────────────────────────────────────────────────────────────
print("\nP1: M e B = 100% em todas as instancias")
for cell in ('M', 'B'):
    sub = df[df['cell'] == cell]
    failures = (sub['q2'] < 1).sum()
    print(f"  {cell}: {failures} falhas / {len(sub)} total  {'OK' if failures==0 else 'FAIL'}")

# ── P2 corrigido: nao usar nivel 0 (= M, fixado em 100% pela P1) ─────────────
print("\nP2 CORRIGIDO: testar apenas niveis L, F, H (excluir nivel 0)")
print("  Criterio: Q2(H) < Q2(L) entre instancias com alguma perda (Q2(L)<1)")
print()

TW_CELLS = ['W_inf_L', 'W_inf_F', 'W_inf_H']
TW_VALS  = {'W_inf_L': 0.10, 'W_inf_F': 0.199, 'W_inf_H': 0.30}

print(f"{'Familia':18s} {'Serie const (L=F=H=100%)':>24} "
      f"{'H<L strict':>12} {'H<L / inform':>14} {'p (1-sided)':>12}")
print("-" * 84)

p2_rows = []
for fam in FAMILIES:
    n_const, n_HL_strict, n_HL_rev, n_inform = 0, 0, 0, 0
    # Additional: L >= F >= H monotone
    n_monotone = 0

    for rep in range(30):
        inst_id = f"{fam}_r{rep:02d}"
        sub = df[(df['inst_id'] == inst_id) & (df['cell'].isin(TW_CELLS))]
        agg = sub.groupby('cell')['q2'].mean()
        qL = agg.get('W_inf_L', 1.0)
        qF = agg.get('W_inf_F', 1.0)
        qH = agg.get('W_inf_H', 1.0)

        # Constant series: all at 100%
        if max(qL, qF, qH) > 1 - 1e-4 and min(qL, qF, qH) > 1 - 1e-4:
            n_const += 1
            continue  # not informative for direction test

        n_inform += 1
        if qH < qL - 1e-4:
            n_HL_strict += 1
        elif qH > qL + 1e-4:
            n_HL_rev += 1
        # strict monotone L >= F >= H
        if qL >= qF - 1e-4 and qF >= qH - 1e-4:
            n_monotone += 1

    # One-sided binomial: H < L (direction prediction)
    if n_inform > 0:
        bt = binomtest(n_HL_strict, n_inform, 0.5, alternative='greater')
        pval = bt.pvalue
        pstr = f"{pval:.3f}"
    else:
        pstr = "n/a"

    pct_inform_HL = f"{n_HL_strict}/{n_inform}"
    pct_monotone = f"{n_monotone}/{n_inform}" if n_inform > 0 else "n/a"

    p2_rows.append({
        'family': fam, 'n_const': n_const, 'n_HL_strict': n_HL_strict,
        'n_HL_rev': n_HL_rev, 'n_inform': n_inform,
        'n_monotone': n_monotone, 'p_one_sided': pval if n_inform > 0 else float('nan')
    })
    print(f"  {fam:16s} {n_const:4d}/30 const  "
          f"{n_HL_strict:3d}/30 ({n_HL_strict/30:.0%})  "
          f"  H<L|inform={pct_inform_HL}  "
          f"monotone={pct_monotone}  p={pstr}")

print()
print("  [Nota] nivel 0 excluido: fixado a 100% pela P1 -- contribuiria")
print("  artificialmente para rho < 0 em qualquer serie com algum efeito.")

# ── P3 corrigido (bilateral para instancias informativas) ─────────────────────
print("\nP3: Q2(V_inf_F) <= Q2(W_inf_F)")
print("  Pela criterio pre-registado (conta empates como sucesso) e sem empates")
print()
print(f"{'Familia':18s} {'Pre-reg (V<=W)':>16} {'Strict V<W':>12} "
      f"{'Tied':>7} {'V>W':>7} {'Strict|Inform':>15} {'p (1-sided)':>12}")
print("-" * 90)

p3_rows = []
for fam in FAMILIES:
    n_prereg, n_strict, n_tied, n_rev = 0, 0, 0, 0
    for rep in range(30):
        inst_id = f"{fam}_r{rep:02d}"
        v = df[(df['inst_id'] == inst_id) & (df['cell'] == 'V_inf_F')]['q2'].mean()
        w = df[(df['inst_id'] == inst_id) & (df['cell'] == 'W_inf_F')]['q2'].mean()
        diff = v - w
        if diff <= 1e-4:  # pre-registered criterion (<=)
            n_prereg += 1
        if diff < -1e-4:
            n_strict += 1
        elif diff > 1e-4:
            n_rev += 1
        else:
            n_tied += 1

    n_inform = n_strict + n_rev
    if n_inform > 0:
        bt = binomtest(n_strict, n_inform, 0.5, alternative='greater')
        pval = bt.pvalue
        pstr = f"{pval:.3f}"
    else:
        pstr = "n/a"

    p3_rows.append({'family': fam, 'prereg': n_prereg, 'strict': n_strict,
                    'tied': n_tied, 'rev': n_rev, 'n_inform': n_inform,
                    'pval': pval if n_inform > 0 else float('nan')})

    print(f"  {fam:16s} {n_prereg:4d}/30 ({n_prereg/30:.0%})  "
          f"{n_strict:4d}/30 ({n_strict/30:.0%})  "
          f"{n_tied:4d}  {n_rev:4d}  "
          f"{n_strict}/{n_inform}  p={pstr}")

# ── P4 CORRIGIDO: teste bilateral ────────────────────────────────────────────
print("\nP4 CORRIGIDO: bilateral (direcção observada = oposta da prevista)")
print()
print(f"{'Familia':18s} {'inf<def strict':>15} {'tied':>6} {'inf>def':>9} "
      f"{'Inform':>8} {'p 1-sided inf<def':>19} {'p 2-sided':>11}")
print("-" * 92)

p4_rows = []
for fam in FAMILIES:
    n_strict, n_tied, n_rev = 0, 0, 0
    for rep in range(30):
        inst_id = f"{fam}_r{rep:02d}"
        inf_q = df[(df['inst_id'] == inst_id) & (df['cell'] == 'W_inf_F')]['q2'].mean()
        def_q = df[(df['inst_id'] == inst_id) & (df['cell'] == 'W_def_F')]['q2'].mean()
        diff = inf_q - def_q
        if diff < -1e-4:
            n_strict += 1
        elif diff > 1e-4:
            n_rev += 1
        else:
            n_tied += 1

    n_inform = n_strict + n_rev
    if n_inform > 0:
        # One-sided: inf < def (original prediction direction)
        bt_1 = binomtest(n_strict, n_inform, 0.5, alternative='greater')
        # Two-sided
        bt_2 = binomtest(n_strict, n_inform, 0.5, alternative='two-sided')
        p1, p2 = bt_1.pvalue, bt_2.pvalue
    else:
        p1, p2 = float('nan'), float('nan')

    p4_rows.append({'family': fam, 'strict': n_strict, 'tied': n_tied,
                    'rev': n_rev, 'n_inform': n_inform, 'p1': p1, 'p2': p2})

    print(f"  {fam:16s} {n_strict:4d}/30 ({n_strict/30:.0%})  "
          f"{n_tied:4d}  {n_rev:4d}/30 ({n_rev/30:.0%})  "
          f"{n_inform:6d}  "
          f"p1={p1:.3f}  p2={p2:.3f}")

# Combined across families (post hoc)
total_strict = sum(r['strict'] for r in p4_rows)
total_rev    = sum(r['rev']    for r in p4_rows)
total_inform = total_strict + total_rev
bt_combined  = binomtest(total_rev, total_inform, 0.5, alternative='two-sided')
print(f"\n  Combined (post hoc): deflate>inflate = {total_rev}/{total_inform} "
      f"({total_rev/total_inform:.0%}), p2={bt_combined.pvalue:.3f}")

# ── Comparacao correcta Fogo vs E6 ───────────────────────────────────────────
print("\nComparacao Fogo vs E6 (celula W_inf_F, TV_W=0.199, TV_B=0):")
print(f"  Fogo E1 celula W: {FOGO_W_LOSS:.1f} pp")
for fam in FAMILIES:
    w_q2 = df[(df['family'] == fam) & (df['cell'] == 'W_inf_F')]['q2'].mean() * 100
    print(f"  {fam:16s}: {100-w_q2:.1f} pp")

# ── Desvios DEV-E6-001 a 004 ─────────────────────────────────────────────────
print("\nDesvios DEV-E6-001 a DEV-E6-004:")
print("""
  DEV-E6-001: P3 e P4 -- empates nao pre-especificados.
              Original: proporcao sobre todas as instancias (empates contam conforme sinal).
              Actual: tambem reportar proporcao entre instancias informativas + teste binomial.

  DEV-E6-002: P2 -- nivel 0 incluido no Spearman.
              Original: Spearman sobre {0, L, F, H} (nivel 0 fixado a 100% pela P1).
              Actual: tambem reportar Q2(H) < Q2(L) entre instancias com perda.

  DEV-E6-003: P4 -- teste unilateral para a direcção prevista.
              Actual: teste bilateral (direcção observada oposta a prevista).

  DEV-E6-004: N draws -- 200 no E6, 500 no E1/Fogo.
              Declarado por razoes computacionais.
""")

print("=" * 70)
print("SUMARIO PARA MANUSCRITO:")
print("""
P1: CONFIRMADA -- 0 falhas em 24.000 draw-instancia.

P2 (criterio pre-reg falhou em 3/4 familias):
  Entre instancias com alguma perda (L,F,H), Q2(H)<Q2(L) na maioria --
  ver coluna H<L|inform acima. Reportar fracção informativa e p.
  A monotonia L>=F>=H e mais forte do que Q2(H)<Q2(L) -- ver coluna monotone.

P3 (criterio pre-reg PASSOU em 4/4 familias):
  Pelo criterio original (<=, conta empates), passa.
  Entre instancias informativas, nenhuma familia e significativa (p>=0.08).
  Reportar os dois resultados. Declarar DEV-E6-001.

P4 (criterio pre-reg falhou em 4/4 familias):
  Entre instancias informativas, deflate custa mais que inflate na maioria --
  OPOSTO da previsao. Nao significativo a 5% bilateral em nenhuma familia.
  Combinado post hoc: deflate>inflate em 53/87 (61%), p bilateral=0.043.
  Conclusao: sem suporte para a previsao; tendencia oposta nao conclusiva.
""")
