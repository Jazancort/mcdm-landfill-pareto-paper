# -*- coding: utf-8 -*-
"""
assert_r1.py — 4 asserts de regressão do gate R1.

Falha com mensagem clara se qualquer invariante for violada.
Passar todos os 4 asserts é pré-condição para reexecutar mc_robustez.py.
"""
import sys, os; sys.path.insert(0, '.')
import numpy as np
import pandas as pd
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix,
    haversine_km, optimal_trio_enumerate, greedy_trio, MIN_DIST_KM,
    INV, COST, F1_CRIT, F2_CRIT, F3_CRIT,
)

print('=== GATE R1: 4 asserts de regressão ===\n')
PASS = 0; FAIL = 0

def check(name, cond, msg_fail):
    global PASS, FAIL
    if cond:
        print(f'  PASS  {name}')
        PASS += 1
    else:
        print(f'  FAIL  {name}')
        print(f'        {msg_fail}')
        FAIL += 1

# ── Carregamento ──────────────────────────────────────────────────────────────
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
via_mask = df_imp[COL['protected']] > 0
df_via = df_imp[via_mask].copy()
w = np.array(list(AHP_WEIGHTS.values()), dtype=np.float32)
col_names = list(AHP_WEIGHTS.keys())
X_via, benefit = _build_decision_matrix(df_via)
D = haversine_km(df_via['latitude (degrees)'].values, df_via['longitude (degrees)'].values)
via_idx = df_via.index.values
N = len(df_via)

# ── Assert 1: MIN_DIST_KM == 10 (não 200) ────────────────────────────────────
check(
    'A1: MIN_DIST_KM == 10.0 km',
    abs(MIN_DIST_KM - 10.0) < 1e-6,
    f'MIN_DIST_KM={MIN_DIST_KM} — bug α/d_min: deve ser 10.0, não 200',
)

# ── Assert 2: universo de trios == 1_944_653 ─────────────────────────────────
pairs_i, pairs_j = np.where(np.triu(D >= MIN_DIST_KM, k=1))
count = 0
for pi, pj in zip(pairs_i, pairs_j):
    ks = np.where((D[pi] >= MIN_DIST_KM) & (D[pj] >= MIN_DIST_KM))[0]
    count += int(np.sum(ks > pj))
check(
    'A2: len(trios) == 1_944_653',
    count == 1_944_653,
    f'len(trios)={count} — esperado 1_944_653; verifique MIN_DIST_KM e dataset',
)

# ── Assert 3: fronteira A' == 181 trios ──────────────────────────────────────
front_mm = pd.read_csv(os.path.join('results', 'pareto_front_Aprime.csv'))
check(
    'A3: len(pareto_front_Aprime) == 181',
    len(front_mm) == 181,
    f'len(front)={len(front_mm)} — esperado 181; fronteira foi recalculada?',
)

# ── Assert 4: SAW×mm optimal == {184,430,460} (IDs globais) ──────────────────
X_adj = X_via.copy().astype(np.float32)
for j in range(len(w)):
    if not benefit[j]: X_adj[:, j] = 1.0 - X_via[:, j]
sc = (X_adj * w).sum(axis=1)
to = optimal_trio_enumerate(sc, D, MIN_DIST_KM)
gids_opt = frozenset(int(via_idx[i]) for i in to)
expected_opt = frozenset([184, 430, 460])
check(
    'A4: SAW×mm optimal (global IDs) == {184, 430, 460}',
    gids_opt == expected_opt,
    f'got {sorted(gids_opt)} — esperado {{184, 430, 460}}; verifique indexação local→global',
)

# ── Assert P1 (bônus): Q2[F_mm](SAW×mm optimal) == 100% ─────────────────────
# Calcular objetivos do trio optimal e verificar in_front
def _norm(x, ref):
    lo, hi = ref.min(), ref.max()
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x)

f1v = np.zeros(N, dtype=np.float32)
f2v = np.zeros(N, dtype=np.float32)
f3v = np.zeros(N, dtype=np.float32)
for j, k in enumerate(col_names):
    col = COL[k]
    x = df_via[col].values.astype(float)
    ref = df_via[col].values.astype(float)
    if k == 'aspect': c = np.where((x >= 90) & (x <= 180), 0., 1.)
    elif k in INV:    c = 1. - _norm(x, ref)
    elif k in COST:   c = _norm(x, ref)
    else:             c = _norm(x, ref)
    c = (c * w[j]).astype(np.float32)
    if k in F1_CRIT:   f1v += c
    elif k in F2_CRIT: f2v += c
    else:              f3v += c

i, j2, k2 = to
# to contém índices LOCAIS (0-388). A fronteira armazena IDs GLOBAIS.
gids_to = frozenset(int(via_idx[i]) for i in to)
s_global = gids_to  # IDs globais do trio optimal
in_f = any(frozenset([int(r.idx1), int(r.idx2), int(r.idx3)]) == s_global
           for _, r in front_mm.iterrows())

# Calcular objetivos para a mensagem de diagnóstico
f1t = float(f1v[to[0]] + f1v[to[1]] + f1v[to[2]])
f2t = float(f2v[to[0]] + f2v[to[1]] + f2v[to[2]])
f3t = float(f3v[to[0]] + f3v[to[1]] + f3v[to[2]])
check(
    'P1 gate: SAW×mm optimal in_front(A prime) == True',
    in_f,
    f'in_front=False (f1={f1t:.4f}, f2={f2t:.4f}, f3={f3t:.4f}) — P1 violada; objetivos ou fronteira incorretos',
)

# ── Resultado ─────────────────────────────────────────────────────────────────
print(f'\nResultado: {PASS} PASS, {FAIL} FAIL')
if FAIL > 0:
    print('GATE R1 NÃO PASSOU. Não execute mc_robustez.py.')
    sys.exit(1)
else:
    print('GATE R1 PASSOU. Pode executar mc_robustez.py.')
