# -*- coding: utf-8 -*-
"""
space_b_v2.py  —  Espaço B v2 com paretoset (Tarefa 3)
Objetivos:
  B1 = sum f1(i)           custo total aditivo (minimizar)
  B2 = max_i f2(i)         pior impacto ambiental (minimizar)
  B3 = min_i f3(i)         gargalo de segurança (maximizar)
Algoritmo: paretoset (O(M log M), exato, validado).

Run: uv run --with pandas --with numpy --with paretoset python scripts/space_b_v2.py
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from paretoset import paretoset

from mcdm_experiment import (
    load_data, impute_nan, haversine_km, compute_objectives,
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

objs_via = compute_objectives(df_via, df_imp)
f1v = objs_via["f1"].values.astype(np.float32)
f2v = objs_via["f2"].values.astype(np.float32)
f3v = objs_via["f3"].values.astype(np.float32)

# ─── Enumeração ──────────────────────────────────────────────────────────────
print("Enumerando trios viáveis...")
valid = D_via >= MIN_DIST_KM
B1l, B2l, B3l, trio_ids = [], [], [], []
for i in range(N):
    for j in range(i+1, N):
        if not valid[i, j]: continue
        for k in range(j+1, N):
            if not valid[i, k] or not valid[j, k]: continue
            B1l.append(f1v[i]+f1v[j]+f1v[k])
            B2l.append(max(f2v[i],f2v[j],f2v[k]))
            B3l.append(min(f3v[i],f3v[j],f3v[k]))
            trio_ids.append((i,j,k))

B1 = np.array(B1l, dtype=np.float32)
B2 = np.array(B2l, dtype=np.float32)
B3 = np.array(B3l, dtype=np.float32)
M  = len(B1)
print(f"Trios: {M:,}  B1=[{B1.min():.4f},{B1.max():.4f}]  "
      f"B2=[{B2.min():.4f},{B2.max():.4f}]  B3=[{B3.min():.4f},{B3.max():.4f}]")

# ─── Validação N=80 ──────────────────────────────────────────────────────────
def brute_force(b1, b2, b3):
    M = len(b1)
    dominated = np.zeros(M, dtype=bool)
    for i in range(M):
        for j in range(M):
            if i==j: continue
            if (b1[j]<=b1[i] and b2[j]<=b2[i] and b3[j]>=b3[i] and
                (b1[j]<b1[i] or b2[j]<b2[i] or b3[j]>b3[i])):
                dominated[i]=True; break
    return ~dominated

print("\nValidando paretoset vs força bruta (N=80 subamostra)...")
rng = np.random.default_rng(42)
sub = rng.choice(N, 80, replace=False)
sv  = D_via[np.ix_(sub, sub)] >= MIN_DIST_KM
sb1, sb2, sb3 = [], [], []
for ii,i in enumerate(sub):
    for jj,j in enumerate(sub):
        if j<=i: continue
        if not sv[ii,jj]: continue
        for kk,k in enumerate(sub):
            if k<=j: continue
            if not sv[ii,kk] or not sv[jj,kk]: continue
            sb1.append(f1v[i]+f1v[j]+f1v[k])
            sb2.append(max(f2v[i],f2v[j],f2v[k]))
            sb3.append(min(f3v[i],f3v[j],f3v[k]))

sb1=np.array(sb1,dtype=np.float32); sb2=np.array(sb2,dtype=np.float32); sb3=np.array(sb3,dtype=np.float32)
print(f"  Subamostra: {len(sb1):,} trios")
t0=time.time(); nd_bf=brute_force(sb1,sb2,sb3); print(f"  Brute force: {nd_bf.sum()} ND ({time.time()-t0:.2f}s)")
t0=time.time()
nd_ps = paretoset(np.column_stack([sb1, sb2, -sb3]), sense=['min','min','min'])
print(f"  paretoset:   {nd_ps.sum()} ND ({time.time()-t0:.3f}s)")
if np.array_equal(nd_bf, nd_ps):
    print("  VALIDAÇÃO: PASS")
else:
    d=(nd_bf!=nd_ps).sum()
    print(f"  VALIDAÇÃO: FAIL — {d} diferenças")

# ─── Fronteira Pareto B ───────────────────────────────────────────────────────
print(f"\nCalculando fronteira Pareto B ({M:,} trios)...")
t0 = time.time()
pareto_b = paretoset(np.column_stack([B1, B2, -B3]), sense=['min','min','min'])
n_pb = pareto_b.sum()
print(f"Fronteira B: {n_pb:,} trios ({time.time()-t0:.2f}s)")
print(f"  B1=[{B1[pareto_b].min():.4f},{B1[pareto_b].max():.4f}]  "
      f"B2=[{B2[pareto_b].min():.4f},{B2[pareto_b].max():.4f}]  "
      f"B3=[{B3[pareto_b].min():.4f},{B3[pareto_b].max():.4f}]")

front_b_set, front_b_sites = set(), set()
for idx in np.where(pareto_b)[0]:
    i,j,k = trio_ids[idx]
    fs = frozenset([int(via_global[i]),int(via_global[j]),int(via_global[k])])
    front_b_set.add(fs); front_b_sites |= set(fs)
print(f"  Sites únicos: {len(front_b_sites)}")
front_a = set(frozenset([int(r.idx1),int(r.idx2),int(r.idx3)]) for _,r in par.iterrows())
print(f"  Trios A∩B: {len(front_a&front_b_set)}  (A={len(front_a)}, B={n_pb})")

# ─── Avaliação canônica ──────────────────────────────────────────────────────
print("\n" + "="*72)
print("Espaço B v2: B1=custo(sum), B2=pior_impacto(max), B3=gargalo_segurança(min)")
print(f"  {'Label':22s}  {'B1_cost':>8}  {'B2_worst':>8}  {'B3_min_s':>8}  in_B")
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
rows = []
for label, gids in CANONICAL:
    li = [g2l[g] for g in gids]
    b1=f1v[li[0]]+f1v[li[1]]+f1v[li[2]]
    b2=max(f2v[li[0]],f2v[li[1]],f2v[li[2]])
    b3=min(f3v[li[0]],f3v[li[1]],f3v[li[2]])
    inf_b = frozenset(gids) in front_b_set
    print(f"  {label:22s}  {b1:8.4f}  {b2:8.4f}  {b3:8.4f}  {inf_b}")
    rows.append({"label":label,"B1_cost":float(b1),"B2_worst_impact":float(b2),
                 "B3_min_safety":float(b3),"in_front_B":inf_b})

pd.DataFrame(rows).to_csv(os.path.join(RESULTS_DIR,"space_b_v2_canonical.csv"),index=False)
pd.DataFrame([{"B1":float(B1[idx]),"B2":float(B2[idx]),"B3":float(B3[idx]),
               "idx1":int(via_global[trio_ids[idx][0]]),"idx2":int(via_global[trio_ids[idx][1]]),
               "idx3":int(via_global[trio_ids[idx][2]])}
              for idx in np.where(pareto_b)[0]]).to_csv(
    os.path.join(RESULTS_DIR,"pareto_front_B_v2.csv"),index=False)
print(f"\nResultados salvos em {RESULTS_DIR}")
