# -*- coding: utf-8 -*-
"""
space_aprime.py  — Tarefa 2: Espaço A′ (normalização sobre os 389 viáveis)
Calcula a fronteira exata de A′ e compara com A (213 trios IEEE).

Run: uv run --with pandas --with numpy --with paretoset python scripts/space_aprime.py
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from paretoset import paretoset

from mcdm_experiment import (
    load_data, impute_nan, compute_objectives, haversine_km,
    in_pareto_front, pareto_dominates,
    COL, AHP_WEIGHTS, MIN_DIST_KM,
)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

print("Carregando dados...")
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
via_global = df_via.index.values
N = len(df_via)
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)

# Espaço A  (normalização 473, pesos AHP) — referência IEEE
objs_A = compute_objectives(df_via, df_imp)
f1A = objs_A["f1"].values  # float64 — sem cast float32 (causava diff 7e-8 no validate_core)
f2A = objs_A["f2"].values
f3A = objs_A["f3"].values

# Espaço A' (normalização 389, pesos AHP) — escala justa
objs_P = compute_objectives(df_via, df_via)
f1P = objs_P["f1"].values  # float64
f2P = objs_P["f2"].values
f3P = objs_P["f3"].values

print(f"Site 184 em A : f1={f1A[list(df_via.index).index(184)]:.4f}  f2={f2A[list(df_via.index).index(184)]:.4f}  f3={f3A[list(df_via.index).index(184)]:.4f}")
print(f"Site 184 em A': f1={f1P[list(df_via.index).index(184)]:.4f}  f2={f2P[list(df_via.index).index(184)]:.4f}  f3={f3P[list(df_via.index).index(184)]:.4f}")

# ─── Enumeração dos trios viáveis ─────────────────────────────────────────────
print("Enumerando trios viáveis...")
valid = D_via >= MIN_DIST_KM
trio_arr = []
for i in range(N):
    for j in range(i+1, N):
        if not valid[i,j]: continue
        for k in range(j+1, N):
            if not valid[i,k] or not valid[j,k]: continue
            trio_arr.append((i,j,k))
trio_arr = np.array(trio_arr, dtype=np.int32)
M = len(trio_arr)
print(f"  {M:,} trios")

i0,i1,i2 = trio_arr[:,0],trio_arr[:,1],trio_arr[:,2]

# Objetivos de todos os trios nos dois espaços
F1A = f1A[i0]+f1A[i1]+f1A[i2]
F2A = f2A[i0]+f2A[i1]+f2A[i2]
F3A = f3A[i0]+f3A[i1]+f3A[i2]

F1P = f1P[i0]+f1P[i1]+f1P[i2]
F2P = f2P[i0]+f2P[i1]+f2P[i2]
F3P = f3P[i0]+f3P[i1]+f3P[i2]

# ─── Fronteira Pareto A' ──────────────────────────────────────────────────────
print("Calculando fronteira A' com paretoset...")
t0 = time.time()
# minimizar F1P, F2P; maximizar F3P → minimizar -F3P
nd_P = paretoset(np.column_stack([F1P, F2P, -F3P]), sense=['min','min','min'])
n_P = nd_P.sum()
print(f"Fronteira A': {n_P:,} trios ({time.time()-t0:.2f}s)")
print(f"  F1P=[{F1P[nd_P].min():.4f},{F1P[nd_P].max():.4f}]")
print(f"  F2P=[{F2P[nd_P].min():.4f},{F2P[nd_P].max():.4f}]")
print(f"  F3P=[{F3P[nd_P].min():.4f},{F3P[nd_P].max():.4f}]")

# Fronteira Pareto A (1.9M trios, para comparação)
print("Calculando fronteira A (1.9M trios) com paretoset...")
t0 = time.time()
nd_A = paretoset(np.column_stack([F1A, F2A, -F3A]), sense=['min','min','min'])
n_A  = nd_A.sum()
print(f"Fronteira A: {n_A:,} trios ({time.time()-t0:.2f}s)")

# ─── Sites únicos e sobreposição ─────────────────────────────────────────────
front_P = set()
front_P_sites = set()
for idx in np.where(nd_P)[0]:
    i,j,k = trio_arr[idx]
    fs = frozenset([int(via_global[i]),int(via_global[j]),int(via_global[k])])
    front_P.add(fs); front_P_sites |= set(fs)

front_A_1M = set()
for idx in np.where(nd_A)[0]:
    i,j,k = trio_arr[idx]
    front_A_1M.add(frozenset([int(via_global[i]),int(via_global[j]),int(via_global[k])]))

front_A_213 = set(frozenset([int(r.idx1),int(r.idx2),int(r.idx3)]) for _,r in par.iterrows())

print(f"\nSobreposicao fronteiras:")
print(f"  A' n A(1M): {len(front_P & front_A_1M)}  de {n_P} (A') e {n_A} (A-1M)")
print(f"  A' n A(213 IEEE): {len(front_P & front_A_213)}  de {n_P} (A') e 213 (A-IEEE)")
print(f"  Sites unicos A': {len(front_P_sites)}")

# ─── Avaliação dos trios canônicos em A' ─────────────────────────────────────
def gap_n(f1t, f2t, f3t, F1, F2, F3):
    mask = ((F1<=f1t)&(F2<=f2t)&(F3>=f3t)&((F1<f1t)|(F2<f2t)|(F3>f3t)))
    if not mask.any(): return 0.
    f1r=F1.max()-F1.min(); f2r=F2.max()-F2.min(); f3r=F3.max()-F3.min()
    return float(max(0., np.minimum(np.minimum(
        (f1t-F1)/(f1r or 1),(f2t-F2)/(f2r or 1)),(F3-f3t)/(f3r or 1)).max()))

g2l = {int(gid): li for li, gid in enumerate(via_global)}
CANONICAL = [
    ("SAW greedy",        (184,279,320)),
    ("SAW optimal",       (184,430,460)),
    ("TOPSIS-VN greedy",  (233,320,355)),
    ("TOPSIS-VN optimal", (227,233,345)),
    ("TOPSIS-MM greedy",  (184,227,460)),
    ("VIKOR greedy",      (233,279,320)),
    ("PROMETHEE greedy",  (51,233,345)),
    ("BCS_IEEE",          (184,430,460)),
]

print(f"\n{'Label':22s}  {'f1_A':>6}  {'f2_A':>6}  {'f3_A':>6}  in_A  gap_A  | f1_P  f2_P  f3_P  in_P  gap_P")
rows = []
for label, gids in CANONICAL:
    li = [g2l[g] for g in gids]
    f1a=float(f1A[li[0]]+f1A[li[1]]+f1A[li[2]]); f2a=float(f2A[li[0]]+f2A[li[1]]+f2A[li[2]]); f3a=float(f3A[li[0]]+f3A[li[1]]+f3A[li[2]])
    f1p=float(f1P[li[0]]+f1P[li[1]]+f1P[li[2]]); f2p=float(f2P[li[0]]+f2P[li[1]]+f2P[li[2]]); f3p=float(f3P[li[0]]+f3P[li[1]]+f3P[li[2]])
    in_A_213 = frozenset(gids) in front_A_213
    in_P     = frozenset(gids) in front_P
    gn_A = gap_n(f1a,f2a,f3a, F1A,F2A,F3A)
    gn_P = gap_n(f1p,f2p,f3p, F1P,F2P,F3P)
    print(f"{label:22s}  {f1a:6.4f}  {f2a:6.4f}  {f3a:6.4f}  {'T' if in_A_213 else 'F'}  {gn_A:.3f}  | {f1p:6.4f}  {f2p:6.4f}  {f3p:6.4f}  {'T' if in_P else 'F'}  {gn_P:.3f}")
    rows.append({"label":label,"f1_A":f1a,"f2_A":f2a,"f3_A":f3a,"in_A_213":in_A_213,"gap_A":gn_A,
                 "f1_P":f1p,"f2_P":f2p,"f3_P":f3p,"in_Aprime":in_P,"gap_P":gn_P})

pd.DataFrame(rows).to_csv(os.path.join(RESULTS_DIR,"space_aprime_canonical.csv"),index=False)

# Salvar fronteira A'
pb_rows = [{"F1P":float(F1P[idx]),"F2P":float(F2P[idx]),"F3P":float(F3P[idx]),
            "idx1":int(via_global[trio_arr[idx][0]]),"idx2":int(via_global[trio_arr[idx][1]]),
            "idx3":int(via_global[trio_arr[idx][2]])}
           for idx in np.where(nd_P)[0]]
pd.DataFrame(pb_rows).to_csv(os.path.join(RESULTS_DIR,"pareto_front_Aprime.csv"),index=False)
print(f"\nResultados salvos.")
