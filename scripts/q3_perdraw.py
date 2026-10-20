# -*- coding: utf-8 -*-
"""
q3_perdraw.py  v2  --  Q3 per-draw com scoring identico ao mc_2cube_fixed.py.

Correccoes em relacao a v1:
  - saw_sc e topsis_sc sao copias verbatim de mc_2cube_fixed.py (linhas 84-97).
    Qualquer alteracao aqui TEM de ser espelhada nesse ficheiro.
  - Q2 e recalculado neste script com is_dominated (nao importado de fora).
  - Assert: q2==1 => gap==0. O script para se a invariante for violada.
  - Assert: q2_recalc == q2_mc2cube. Detecta qualquer desconexao de portfolio.
  - Verificacao: taxa de coincidencia SAW/vec == TOP/vec.
  - Teste unitario TOPSIS: alternativa dominante fica em 1.o lugar.

Output: results/e1/q3_perdraw.csv
Colunas:
  draw, agg, norm, mont,
  i0, i1, i2,      -- indices em df_via (0..388) do trio seleccionado
  ft1, ft2, ft3,   -- objectivos do trio
  gap,             -- distancia Tchebyshev (Q3)
  q2,              -- Q2 recalculado neste script
  q2_mc2cube,      -- Q2 de mc_2cube_fixed_raw.csv (validacao cruzada)

Executar:
  uv run python scripts/q3_perdraw.py
"""

import os, sys, time, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent

# ── Dados ─────────────────────────────────────────────────────────────────────
if "MCDM_DATA_DIR" not in os.environ:
    _athena  = "/home/julioazancort/scratch/mcdm"
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

KAPPA   = 200
N_DRAWS = 500
EPS     = 1e-9
E1_SHA  = "bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487"

df_all, _, _ = load_data()
df_imp       = impute_nan(df_all)
df_via       = df_imp[df_imp[COL["protected"]] > 0].copy()
N            = len(df_via)
assert N == 389, f"Esperado 389, obtido {N}"

w_ahp     = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())

D     = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
valid = D >= MIN_DIST_KM
trios = np.array(
    [(i, j, k)
     for i in range(N) for j in range(i+1, N) if valid[i, j]
     for k in range(j+1, N) if valid[i, k] and valid[j, k]],
    dtype=np.int32,
)
T0, T1, T2 = trios[:, 0], trios[:, 1], trios[:, 2]
print(f"Sites: {N}  Trios: {len(trios):,}")

compute_objs, is_dominated, _ = build_pareto_utils(df_via, col_names, trios, eps=EPS)

X_via, benefit = _build_decision_matrix(df_via)
X_adj          = X_via.copy()
for j, b in enumerate(benefit):
    if not b:
        X_adj[:, j] = 1.0 - X_via[:, j]

# VERBATIM de mc_2cube_fixed.py linha 84: norms_via = ...
norms_via = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)

# VERBATIM de mc_2cube_fixed.py linhas 86-97: saw_sc, topsis_sc
# Qualquer alteracao aqui TEM de ser espelhada em mc_2cube_fixed.py.
def saw_sc(w, norm="minmax"):
    if norm == "minmax":
        return (X_adj * w).sum(1)
    else:  # vector: X_adj/norms (benefit-adjusted), consistent with wp3_mc_fixed
        return ((X_adj / norms_via) * w).sum(1)

def topsis_sc(w, norm="minmax"):
    Xb  = X_via if norm == "minmax" else X_via / norms_via
    V   = Xb * w
    PIS = np.where(benefit, V.max(0), V.min(0))
    NIS = np.where(benefit, V.min(0), V.max(0))
    dp  = np.sqrt(((V - PIS)**2).sum(1))
    dn  = np.sqrt(((V - NIS)**2).sum(1))
    return np.where(dp + dn == 0, 0.5, dn / (dp + dn))
# FIM VERBATIM

def sel_trio(sc, mont):
    if mont == "greedy":
        return greedy_trio(sc, D)
    st  = sc[T0] + sc[T1] + sc[T2]
    idx = int(st.argmax())
    return trios[idx]


# ── Teste unitario TOPSIS (orientacao) ───────────────────────────────────────
print("Teste unitario TOPSIS...")
_n, _m = N, len(w_ahp)
_X = X_via.copy()
# Alternativa dominante: melhor em todos os criterios de beneficio, pior nos de custo
_dominant_row = np.where(benefit, _X.max(0), _X.min(0)).reshape(1, _m)
_dominated_row = np.where(benefit, _X.min(0), _X.max(0)).reshape(1, _m)
_X_test = np.vstack([_dominant_row, _X, _dominated_row])
_benefit_test = benefit.copy()
_norms_test = np.maximum(np.sqrt((_X_test**2).sum(0)), 1e-12)

for _norm in ["minmax", "vector"]:
    _Xb = _X_test if _norm == "minmax" else _X_test / _norms_test
    _V  = _Xb * w_ahp
    _PIS = np.where(_benefit_test, _V.max(0), _V.min(0))
    _NIS = np.where(_benefit_test, _V.min(0), _V.max(0))
    _dp  = np.sqrt(((_V - _PIS)**2).sum(1))
    _dn  = np.sqrt(((_V - _NIS)**2).sum(1))
    _sc  = np.where(_dp + _dn == 0, 0.5, _dn / (_dp + _dn))
    assert _sc[0] == _sc.max(), f"TOPSIS/{_norm}: dominante nao esta em 1.o lugar (score={_sc[0]:.4f} max={_sc.max():.4f})"
    assert _sc[-1] == _sc.min(), f"TOPSIS/{_norm}: dominada nao esta em ultimo lugar (score={_sc[-1]:.4f} min={_sc.min():.4f})"
    print(f"  TOPSIS/{_norm}: dominante={_sc[0]:.4f} (max), dominada={_sc[-1]:.4f} (min) OK")


# ── Q2 de referencia do pipeline factorial ────────────────────────────────────
wmat = ROOT / "results" / "e1" / "e1_weights_k200.npy"
sha  = hashlib.sha256(wmat.read_bytes()).hexdigest()
if sha != E1_SHA:
    print(f"AVISO SHA pesos: {sha[:16]}... != esperado")
W = np.load(wmat)

mc2cube = pd.read_csv(ROOT / "results" / "fourthcell" / "mc_2cube_fixed_raw.csv")
mc2cube = mc2cube[mc2cube.alpha == KAPPA][["draw","agg","norm","mont","nd_Q2Ap"]]
q2_ref  = mc2cube.set_index(["draw","agg","norm","mont"])["nd_Q2Ap"].to_dict()

CELLS_8 = [
    ("saw",   "minmax","greedy"), ("saw",   "minmax","optimal"),
    ("saw",   "vector","greedy"), ("saw",   "vector","optimal"),
    ("topsis","minmax","greedy"), ("topsis","minmax","optimal"),
    ("topsis","vector","greedy"), ("topsis","vector","optimal"),
]

# ── Loop principal ────────────────────────────────────────────────────────────
records    = []
saw_vec_set  = []   # para verificacao de coincidencia SAW/vec == TOP/vec
t0 = time.time()

for d in range(N_DRAWS):
    w = W[d]
    f1v, f2v, f3v = compute_objs(w)
    F1 = f1v[T0] + f1v[T1] + f1v[T2]
    F2 = f2v[T0] + f2v[T1] + f2v[T2]
    F3 = f3v[T0] + f3v[T1] + f3v[T2]
    R1 = F1.max() - F1.min()
    R2 = F2.max() - F2.min()
    R3 = F3.max() - F3.min()

    # Para verificacao de coincidencia
    trio_sawvec_grd = trio_topvec_grd = None
    trio_sawvec_opt = trio_topvec_opt = None

    for agg, norm, mont in CELLS_8:
        sc   = saw_sc(w, norm) if agg == "saw" else topsis_sc(w, norm)
        trio = sel_trio(sc, mont)
        i0, i1, i2 = int(trio[0]), int(trio[1]), int(trio[2])

        ft1 = f1v[i0] + f1v[i1] + f1v[i2]
        ft2 = f2v[i0] + f2v[i1] + f2v[i2]
        ft3 = f3v[i0] + f3v[i1] + f3v[i2]

        # gap (formula do paper)
        d1  = (ft1 - F1) / R1
        d2  = (ft2 - F2) / R2
        d3  = (F3  - ft3) / R3
        gap = float(max(0.0, np.minimum(np.minimum(d1, d2), d3).max()))

        # Q2 recalculado neste script (fonte de verdade local)
        q2_recalc = int(not is_dominated(trio, F1, F2, F3))

        # Validacao cruzada com mc_2cube_fixed_raw.csv
        q2_mc = int(q2_ref.get((d, agg, norm, mont), -1))

        # === ASSERTIONS ===
        # 1. Eficiente => gap = 0
        if q2_recalc == 1 and gap > EPS:
            raise AssertionError(
                f"draw={d} {agg}/{norm}/{mont}: q2_recalc=1 mas gap={gap:.6f} > 0. "
                f"Trio=({i0},{i1},{i2})"
            )
        # 2. Q2 recalculado deve coincidir com o do pipeline factorial
        if q2_mc != -1 and q2_recalc != q2_mc:
            raise AssertionError(
                f"draw={d} {agg}/{norm}/{mont}: q2_recalc={q2_recalc} != q2_mc2cube={q2_mc}. "
                f"Portfolio diferente do factorial! Trio=({i0},{i1},{i2})"
            )

        records.append({
            "draw": d, "agg": agg, "norm": norm, "mont": mont,
            "i0": i0, "i1": i1, "i2": i2,
            "ft1": round(ft1, 8), "ft2": round(ft2, 8), "ft3": round(ft3, 8),
            "gap":        round(gap, 10),
            "q2":         q2_recalc,
            "q2_mc2cube": q2_mc,
        })

        # Guardar para coincidencia SAW/vec vs TOP/vec
        key = tuple(sorted([i0, i1, i2]))
        if agg == "saw"    and norm == "vector" and mont == "greedy":  trio_sawvec_grd = key
        if agg == "saw"    and norm == "vector" and mont == "optimal": trio_sawvec_opt = key
        if agg == "topsis" and norm == "vector" and mont == "greedy":  trio_topvec_grd = key
        if agg == "topsis" and norm == "vector" and mont == "optimal": trio_topvec_opt = key

    saw_vec_set.append({
        "draw": d,
        "sawvec_grd_eq_topvec_grd": trio_sawvec_grd == trio_topvec_grd,
        "sawvec_opt_eq_topvec_opt": trio_sawvec_opt == trio_topvec_opt,
    })

    if d % 50 == 0:
        elapsed = time.time() - t0
        eta = elapsed / max(d, 1) * (N_DRAWS - d)
        print(f"  draw {d:3d}/{N_DRAWS}  {elapsed:5.0f}s  ETA {eta:4.0f}s", flush=True)

# ── Gravar CSV ────────────────────────────────────────────────────────────────
df_out = pd.DataFrame(records)
OUT    = ROOT / "results" / "e1" / "q3_perdraw.csv"
df_out.to_csv(OUT, index=False)
print(f"\nCSV: {OUT}  ({len(df_out)} linhas)")
print(f"Tempo: {time.time()-t0:.1f}s")

# ── Sumario Q3 ────────────────────────────────────────────────────────────────
print("\n=== Q3 por celula (media e SE) ===")
summary = (
    df_out.groupby(["agg","norm","mont"])
    .apply(lambda g: pd.Series({
        "Q2_pct":      round(g["q2"].mean() * 100, 1),
        "Q2zero_pct":  round((g["gap"] < EPS).mean() * 100, 1),
        "Q3_mean":     round(g["gap"].mean(), 6),
        "Q3_se":       round(g["gap"].std() / len(g)**0.5, 6),
        "violations":  int(((g["q2"] == 1) & (g["gap"] >= EPS)).sum()),
    }), include_groups=False)
    .reset_index()
)
print(summary.to_string(index=False))

# ── Verificacao coincidencia SAW/vec vs TOP/vec ───────────────────────────────
df_coin = pd.DataFrame(saw_vec_set)
grd_rate = df_coin["sawvec_grd_eq_topvec_grd"].mean() * 100
opt_rate = df_coin["sawvec_opt_eq_topvec_opt"].mean() * 100
print(f"\n=== Coincidencia SAW/vec == TOP/vec ===")
print(f"  greedy:  {grd_rate:.1f}% dos {N_DRAWS} sorteios")
print(f"  optimal: {opt_rate:.1f}% dos {N_DRAWS} sorteios")
if grd_rate > 90 or opt_rate > 90:
    print("  AVISO: taxa > 90% -- verificar se TOPSIS/vector nao esta a colapsar em SAW")
else:
    print("  OK: taxas abaixo de 90%")

# ── Assert final: frac_gap0 >= Q2 em todas as celulas ────────────────────────
print("\n=== Assert frac_gap0 >= Q2 ===")
all_ok = True
for _, row in summary.iterrows():
    ok = row["Q2zero_pct"] >= row["Q2_pct"] - 1e-6
    flag = "OK" if ok else "FALHA"
    if not ok:
        all_ok = False
    print(f"  {row['agg']}/{row['norm']}/{row['mont']}: "
          f"frac_gap0={row['Q2zero_pct']}% >= Q2={row['Q2_pct']}%  {flag}")

if not all_ok:
    raise AssertionError("frac_gap0 < Q2 em pelo menos uma celula -- Q3 ainda incorrecta")

print("\nTodas as asercoes passaram.")
