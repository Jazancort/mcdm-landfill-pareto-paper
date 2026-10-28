# -*- coding: utf-8 -*-
"""
diag_h1_h2.py  --  Teste decisivo H1 vs H2 (< 2 minutos).

Para draws 0-4, compara:
  A) portfolios que o pipeline factorial (mc_2cube_fixed.py) teria escolhido,
     usando as funcoes de score IDENTICAS do mc_2cube_fixed
  B) portfolios em q3_perdraw.csv (i0, i1, i2)

Se A != B nas celulas erradas -> H1 (bug so no script Q3).
Se A == B nas celulas erradas -> H2 (bug no pipeline principal).

Tambem:
  C) TOPSIS/vector com pesos nominais AHP: deve dar {227, 233, 345} (Tabela 3)
  D) Verificacao de espaco de indices: i0..i2 sao 0..388 ou 1..473?

Saida: results/e1/diag_h1_h2.log
"""

import os, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent

if "MCDM_DATA_DIR" not in os.environ:
    _athena = "/home/julioazancort/scratch/mcdm"
    _windows = (
        "G:\\Faculdade\\Estudo\\Doutorado\\2025.1\\"
        "Otimiza\u00e7\u00e3o Bioinspirada\\"
        "Tentativa de dados via GIS"
    )
    os.environ["MCDM_DATA_DIR"] = _athena if os.path.exists(_athena) else _windows

sys.path.insert(0, str(ROOT / "scripts"))
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS,
    haversine_km, MIN_DIST_KM, _build_decision_matrix,
    greedy_trio,
)
from pareto_utils import build_pareto_utils

# ── Setup identico ao mc_2cube_fixed.py ───────────────────────────────────────
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]] > 0].copy()
N = len(df_via)
assert N == 389, f"Esperado 389 sites, obtido {N}"

w_ahp     = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
D         = haversine_km(df_via["latitude (degrees)"].values, df_via["longitude (degrees)"].values)
valid     = D >= MIN_DIST_KM

trio_list = [(i,j,k)
             for i in range(N) for j in range(i+1,N) if valid[i,j]
             for k in range(j+1,N) if valid[i,k] and valid[j,k]]
trios = np.array(trio_list, dtype=np.int32)
T0, T1, T2 = trios[:,0], trios[:,1], trios[:,2]
print(f"Sites: {N}  Trios: {len(trios):,}")

X_raw, benefit = _build_decision_matrix(df_via)
X_adj = X_raw.copy()
for j, b in enumerate(benefit):
    if not b: X_adj[:, j] = 1.0 - X_raw[:, j]

norms_via = np.maximum(np.sqrt((X_raw**2).sum(0)), 1e-12)

# Funcoes IDENTICAS ao mc_2cube_fixed.py
def saw_sc_fixed(w, norm):
    if norm == "minmax":
        return (X_adj * w).sum(1)
    else:
        return ((X_adj / norms_via) * w).sum(1)

def topsis_sc_fixed(w, norm):
    Xb  = X_raw if norm == "minmax" else X_raw / norms_via
    V   = Xb * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp  = np.sqrt(((V - PIS)**2).sum(1))
    dn  = np.sqrt(((V - NIS)**2).sum(1))
    return np.where(dp + dn == 0, 0.5, dn / (dp + dn))

def sel_trio(sc, mont):
    if mont == "greedy":
        return tuple(sorted(greedy_trio(sc, D)))
    else:
        st  = sc[T0] + sc[T1] + sc[T2]
        idx = int(st.argmax())
        return tuple(sorted([int(T0[idx]), int(T1[idx]), int(T2[idx])]))

# ── Carregar pesos e q3_perdraw ───────────────────────────────────────────────
W = np.load(ROOT / "results" / "e1" / "e1_weights_k200.npy")

q3pd = pd.read_csv(ROOT / "results" / "e1" / "q3_perdraw.csv")
q3pd["trio_q3"] = q3pd.apply(
    lambda r: tuple(sorted([int(r.i0), int(r.i1), int(r.i2)])), axis=1
)

log = []
def pr(s=""):
    print(s)
    log.append(s)

# ── A: Comparacao portfolios draws 0-4 ───────────────────────────────────────
pr("=" * 70)
pr("A) Comparacao portfolios: pipeline factorial vs q3_perdraw (draws 0-4)")
pr("=" * 70)
pr(f"  {'draw':<5} {'cell':<25} {'factorial':^15} {'q3_perdraw':^15} {'match'}")
pr("  " + "-"*68)

mismatches = []
for d in range(5):
    w = W[d]
    for agg, norm, mont in [
        ("saw",   "minmax","greedy"), ("saw",   "minmax","optimal"),
        ("saw",   "vector","greedy"), ("saw",   "vector","optimal"),
        ("topsis","minmax","greedy"), ("topsis","minmax","optimal"),
        ("topsis","vector","greedy"), ("topsis","vector","optimal"),
    ]:
        sc  = saw_sc_fixed(w, norm) if agg == "saw" else topsis_sc_fixed(w, norm)
        t_fac = sel_trio(sc, mont)
        row   = q3pd[(q3pd.draw==d)&(q3pd.agg==agg)&(q3pd.norm==norm)&(q3pd.mont==mont)]
        t_q3  = row["trio_q3"].values[0] if len(row) else None
        match = (t_fac == t_q3)
        if not match:
            mismatches.append((d, agg, norm, mont, t_fac, t_q3))
        flag  = "OK" if match else "DIFF !"
        cell  = f"{agg}/{norm}/{mont}"
        pr(f"  {d:<5} {cell:<25} {str(t_fac):^15} {str(t_q3):^15} {flag}")

pr()
pr(f"Total mismatches (draws 0-4): {len(mismatches)}")
if len(mismatches) == 0:
    pr("  -> H1 DESCARTADO: portfolios identicos. Bug esta no pipeline principal (H2).")
else:
    pr("  -> H1 CONFIRMADO: portfolios diferentes no script Q3.")
    pr("  Celulas diferentes:")
    for d, agg, norm, mont, tf, tq in mismatches:
        pr(f"    draw={d} {agg}/{norm}/{mont}: factorial={tf}  q3={tq}")

# ── B: TOPSIS/vector com pesos nominais AHP ──────────────────────────────────
pr()
pr("=" * 70)
pr("B) Orientacao TOPSIS/vector com pesos nominais AHP (Tabela 3)")
pr("   Esperado greedy={233,320,355} ou {227,233,345}  optimal={227,233,345}")
pr("=" * 70)
sc_nom = topsis_sc_fixed(w_ahp, "vector")
t_grd  = sel_trio(sc_nom, "greedy")
t_opt  = sel_trio(sc_nom, "optimal")
pr(f"  greedy:  {t_grd}")
pr(f"  optimal: {t_opt}")
EXPECTED_OPT = {227, 233, 345}
EXPECTED_GRD = {233, 320, 355}
opt_ok = set(t_opt) == EXPECTED_OPT
grd_ok = set(t_grd) == EXPECTED_GRD or set(t_grd) == {227, 233, 345}
pr(f"  optimal match {EXPECTED_OPT}: {'OK' if opt_ok else 'FAIL'}")
pr(f"  greedy  match {EXPECTED_GRD}: {'OK' if grd_ok else 'FAIL  -> orientacao invertida'}")

# ── C: Verificacao espaco de indices ─────────────────────────────────────────
pr()
pr("=" * 70)
pr("C) Espaco de indices: i0..i2 em q3_perdraw sao 0..388 ou IDs dos 473?")
pr("=" * 70)
max_idx = q3pd[["i0","i1","i2"]].values.max()
min_idx = q3pd[["i0","i1","i2"]].values.min()
pr(f"  Valores: min={min_idx}  max={max_idx}")
if max_idx <= 388:
    pr("  OK: indices em 0..388 (espaco df_via de 389 sites)")
else:
    pr(f"  PROBLEMA: max={max_idx} excede 388 -> possivelmente IDs dos 473 sites")

# Verificar que os indices 0-388 no factorial dao os mesmos trios
pr()
pr("  Verificacao cruzada: os sites i0..i2 do draw 0 existem em df_via?")
for _, row in q3pd[q3pd.draw == 0].iterrows():
    for idx_val in [row.i0, row.i1, row.i2]:
        idx_val = int(idx_val)
        if idx_val < 0 or idx_val >= N:
            pr(f"  FORA DE RANGE: idx={idx_val} em {row.agg}/{row.norm}/{row.mont}")
pr("  Todos os indices estao em 0..388." if max_idx <= 388 else "  Indices fora de range encontrados.")

# ── Gravar log ────────────────────────────────────────────────────────────────
out = ROOT / "results" / "e1" / "diag_h1_h2.log"
out.write_text("\n".join(log), encoding="utf-8")
print(f"\nLog gravado: {out}")
