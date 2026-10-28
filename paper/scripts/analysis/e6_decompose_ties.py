# -*- coding: utf-8 -*-
"""
e6_decompose_ties.py — Decomposicao de empates em P2, P3 e P4 do E6 PRESPEC.

Identifica tres problemas da analise original:
  1. P2: fraccao de instancias com rho indefinido (serie constante)
  2. P3: instancias com V<W (estrito), V=W (empate), V>W
  3. P4: instancias com inf<def (estrito), inf=def (empate), inf>def
  4. Estrutura da familia zero_inflated: quantas colunas com massa em zero

Correccao da comparacao com Fogo:
  - Celula correta de Fogo: W = 35.8 pp (so TV_W, sem TV_B)
  - NAO 43.2 pp (celula V = TV_W + TV_B)

Fonte: results/e6/e6_raw_prespec.csv
"""

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr

ROOT = Path(__file__).parent.parent
df = pd.read_csv(ROOT / "results" / "e6" / "e6_raw_prespec.csv")

FAMILIES = ['lognormal', 'beta13', 'uniform', 'zero_inflated']
TW_MAP = {'M': 0.0, 'W_inf_L': 0.10, 'W_inf_F': 0.199, 'W_inf_H': 0.30}
P2_CELLS = ['M', 'W_inf_L', 'W_inf_F', 'W_inf_H']

print("=" * 70)
print("E6 — DECOMPOSICAO DE EMPATES (P2, P3, P4)")
print("Fonte: e6_raw_prespec.csv  |  120 instancias x 200 draws x 7 celulas")
print("=" * 70)

# ── P2: decompor ρ em < 0, indefinido, ≥ 0 ───────────────────────────────────
print("\n── P2: decomposicao do Spearman por instancia ──────────────────────────")
print(f"{'Familia':18s} {'rho<0':>8} {'rho_indef':>10} {'rho>=0':>8} {'Perdas>5pp':>12}")
print("-" * 62)

p2_rows = []
for fam in FAMILIES:
    n_neg, n_indef, n_pos, n_above5 = 0, 0, 0, 0
    for rep in range(30):
        inst_id = f"{fam}_r{rep:02d}"
        sub = df[(df['inst_id'] == inst_id) & (df['cell'].isin(P2_CELLS))]
        inst_agg = sub.groupby('cell')['q2'].mean()
        tv_levels = [TW_MAP[c] for c in inst_agg.index]
        q2_vals = inst_agg.values

        # Check if series is constant (all Q2 = 1.0)
        if np.std(q2_vals) < 1e-9:
            n_indef += 1
        else:
            with np.errstate(all='ignore'):
                rho, _ = spearmanr(tv_levels, q2_vals)
            if np.isnan(rho):
                n_indef += 1
            elif rho < 0:
                n_neg += 1
            else:
                n_pos += 1

        # Check if loss > 5 pp at H level
        q2_H = inst_agg.get('W_inf_H', 1.0)
        q2_M = inst_agg.get('M', 1.0)
        if (q2_M - q2_H) * 100 > 5.0:
            n_above5 += 1

    total = n_neg + n_indef + n_pos
    p2_rows.append({'family': fam, 'rho_neg': n_neg, 'rho_indef': n_indef,
                    'rho_pos': n_pos, 'above5pp': n_above5})
    print(f"  {fam:16s} {n_neg:6d}/30 {n_indef:8d}/30 {n_pos:6d}/30 {n_above5:10d}/30")

# ── P3: V_inf_F vs W_inf_F — estrito / empate / inverso ──────────────────────
print("\n── P3: Q2_opt(V_inf_F) vs Q2_opt(W_inf_F) ─────────────────────────────")
print(f"{'Familia':18s} {'V<W (strict)':>14} {'V=W (tied)':>12} {'V>W':>8} {'N inform.':>10}")
print("-" * 67)

p3_rows = []
for fam in FAMILIES:
    n_strict, n_tied, n_rev = 0, 0, 0
    for rep in range(30):
        inst_id = f"{fam}_r{rep:02d}"
        v = df[(df['inst_id'] == inst_id) & (df['cell'] == 'V_inf_F')]['q2'].mean()
        w = df[(df['inst_id'] == inst_id) & (df['cell'] == 'W_inf_F')]['q2'].mean()
        diff = v - w
        if diff < -1e-4:
            n_strict += 1
        elif diff > 1e-4:
            n_rev += 1
        else:
            n_tied += 1
    n_inform = n_strict + n_rev  # excluindo empates
    p3_rows.append({'family': fam, 'strict': n_strict, 'tied': n_tied,
                    'rev': n_rev, 'n_inform': n_inform})

    # Binomial test among non-tied instances
    if n_inform > 0:
        # binom_test deprecated in newer scipy; use binomtest
        try:
            from scipy.stats import binomtest
            bt = binomtest(n_strict, n_inform, 0.5, alternative='greater')
            pval = bt.pvalue
        except ImportError:
            pval = float('nan')
        pval_str = f"p={pval:.3f}"
    else:
        pval_str = "n/a"

    pct_strict_inform = f"{n_strict}/{n_inform}" if n_inform > 0 else "0/0"
    print(f"  {fam:16s} {n_strict:5d}/30 ({n_strict/30:.0%}) "
          f"{n_tied:5d}/30 {n_rev:5d}/30 "
          f"  strict|inform={pct_strict_inform} {pval_str}")

# ── P4: W_inf_F vs W_def_F — estrito / empate / inverso ──────────────────────
print("\n── P4: Q2_opt(W_inf_F) vs Q2_opt(W_def_F) ─────────────────────────────")
print(f"{'Familia':18s} {'inf<def (strict)':>17} {'inf=def (tied)':>15} {'inf>def':>9} {'N inform.':>10}")
print("-" * 74)

p4_rows = []
for fam in FAMILIES:
    n_strict, n_tied, n_rev = 0, 0, 0
    for rep in range(30):
        inst_id = f"{fam}_r{rep:02d}"
        inf_val = df[(df['inst_id'] == inst_id) & (df['cell'] == 'W_inf_F')]['q2'].mean()
        def_val = df[(df['inst_id'] == inst_id) & (df['cell'] == 'W_def_F')]['q2'].mean()
        diff = inf_val - def_val
        if diff < -1e-4:
            n_strict += 1
        elif diff > 1e-4:
            n_rev += 1
        else:
            n_tied += 1
    n_inform = n_strict + n_rev
    p4_rows.append({'family': fam, 'strict': n_strict, 'tied': n_tied,
                    'rev': n_rev, 'n_inform': n_inform})

    if n_inform > 0:
        try:
            from scipy.stats import binomtest
            bt = binomtest(n_strict, n_inform, 0.5, alternative='greater')
            pval = bt.pvalue
        except ImportError:
            pval = float('nan')
        pval_str = f"p={pval:.3f}"
    else:
        pval_str = "n/a"

    pct_strict_inform = f"{n_strict}/{n_inform}" if n_inform > 0 else "0/0"
    print(f"  {fam:16s} {n_strict:5d}/30 ({n_strict/30:.0%}) "
          f"{n_tied:5d}/30 {n_rev:5d}/30 "
          f"  strict|inform={pct_strict_inform} {pval_str}")

# ── Comparacao correcta com Fogo ──────────────────────────────────────────────
print("\n── Comparacao correcta com Fogo (celula W, so TV_W) ────────────────────")
print("Fogo E1 W_inf_F: loss = 35.8 pp  (64.2% vs 100%;  TV_W=0.199, TV_B=0)")
print("Fogo E1 V_inf_F: loss = 43.2 pp  (56.8% vs 100%;  TV_W=0.199, TV_B=0.249)")
print()
print(f"{'Familia':18s} {'W_inf_F mean':>14} {'Perda W pp':>12} {'V_inf_F mean':>14} {'Perda V pp':>12}")
print("-" * 75)
for fam in FAMILIES:
    w_q2 = df[(df['family'] == fam) & (df['cell'] == 'W_inf_F')]['q2'].mean() * 100
    v_q2 = df[(df['family'] == fam) & (df['cell'] == 'V_inf_F')]['q2'].mean() * 100
    print(f"  {fam:16s} {w_q2:12.1f}% {100-w_q2:12.1f} pp {v_q2:12.1f}% {100-v_q2:12.1f} pp")

# ── Estrutura da familia zero_inflated: quantas colunas com massa em zero ─────
print("\n── Estrutura zero_inflated: massa em zero por coluna ───────────────────")
print("(gerado de novo com seed=42, instancia 0 = FAMILIES.index('zero_inflated')*30 + 0 = inst_idx 90)")
print()

SEED_BASE = 42
inst_idx_zi = 3 * 30 + 0   # zero_inflated, replicate 0
seed = SEED_BASE + inst_idx_zi

rng = np.random.default_rng(seed)
N, M = 389, 11
X_lognormal = rng.lognormal(mean=0.0, sigma=1.0, size=(N, M))
zero_mask = rng.uniform(size=(N, M)) < 0.90
X_zi = X_lognormal.copy()
X_zi[zero_mask] = 0.0

zero_pct = (X_zi == 0).mean(axis=0) * 100
print(f"{'Criterio':>10}  {'% zeros':>8}")
for j, pct in enumerate(zero_pct):
    name = ['perm','slope','roads','rivers','aspect','coast','prot','wells','urban','aero','cult'][j]
    print(f"  {name:8s}  {pct:6.1f}%")

print()
print("Nota: em Fogo, so perm tem massa em zero (350/389 = 90%).")
print("Na familia zero_inflated, TODAS as 11 colunas tem ~90% de zeros.")
print("Isso e uma diferencao estrutural importante em relacao a Fogo.")
print("O zero_inflated e muito mais extremo que Fogo no conjunto.")

# ── Sumario executivo ─────────────────────────────────────────────────────────
print("\n── Sumario executivo ────────────────────────────────────────────────────")
print("""
P2: o criterio pre-registado falhou em 3/4 familias (criterio: 80%).
    A razao nao e falta de potencia — e um efeito pequeno real.
    Instancias com serie constante (rho indefinido) representam a maioria nas
    familias continuas. A fraccao rho<0 e calculada so onde ha perda.
    Accao: manter qualificacao 'on this instance'; adicionar analise post hoc.

P3: recalcular com decomposicao estrita/empate/reverso.
    O criterio 'V <= W' conta empates como sucesso — enviesado nas familias
    continuas onde muitas instancias tem ambas celulas a 100%.

P4: recalcular com decomposicao estrita/empate/reverso.
    O criterio 'inf < def' conta empates como falha — enviesado no sentido
    contrario. A questao e o que acontece nas instancias informativas.

Comparacao com Fogo:
    Usar celula W (TV_W=0.199, TV_B=0) = 35.8 pp, NAO os 43.2 pp da celula V.
    A zero_inflated W_inf_F produce ~11 pp vs 35.8 pp de Fogo.

Diferenca estrutural:
    Em Fogo: 1 coluna com 90% de zeros (perm).
    No zero_inflated: 11 colunas com ~90% de zeros.
    O zero_inflated e estruturalmente mais extremo que Fogo, e ainda produz
    menos de um terco da perda. Ha outros factores (correlacao espacial,
    heterogeneidade entre colunas) que o E6 nao captura.
""")
