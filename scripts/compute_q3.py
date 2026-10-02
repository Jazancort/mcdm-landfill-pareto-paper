"""scripts/compute_q3.py
F3: Q3 = E[gap(M(w), w)] for each cell in mc_2cube_fixed_raw.csv.

gap(t, w) = max_{t'} min((F1(t)-F1(t'))/R1, (F2(t)-F2(t'))/R2, (F3(t')-F3(t))/R3)^+

Efficient approach: for each draw, compute F1/F2/F3 for all trios,
then for each method's selected portfolio (greedy+optimal per cell),
compute gap against all trios.

Only the 8 main cells (SAW/TOPSIS × minmax/vector × greedy/optimal).
kappa=200, N=500 draws.
Output: results/e1/q3_results.csv
"""
import os, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

if "MCDM_DATA_DIR" not in os.environ:
    athena = "/home/julioazancort/scratch/mcdm"
    os.environ["MCDM_DATA_DIR"] = athena if os.path.exists(athena) else str(ROOT/"data")

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS,
    haversine_km, MIN_DIST_KM, _build_decision_matrix,
    saw_scores, topsis_scores, greedy_trio,
)
from pareto_utils import build_pareto_utils
import hashlib

E1_SHA = "bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487"
KAPPA  = 200; N_DRAWS = 500; EPS = 1e-9

# ── Data ──────────────────────────────────────────────────────────────────────
df_all,_,_ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]]>0].copy()
N = len(df_via)
col_names = list(AHP_WEIGHTS.keys())
w_ahp = np.array(list(AHP_WEIGHTS.values()))

wmat = ROOT/"results"/"e1"/"e1_weights_k200.npy"
assert hashlib.sha256(wmat.read_bytes()).hexdigest() == E1_SHA
W = np.load(wmat)

D = haversine_km(df_via["latitude (degrees)"].values, df_via["longitude (degrees)"].values)
valid = D >= MIN_DIST_KM
trios_list = [(i,j,k) for i in range(N) for j in range(i+1,N) if valid[i,j]
              for k in range(j+1,N) if valid[i,k] and valid[j,k]]
trios = np.array(trios_list, dtype=np.int32)
T0,T1,T2 = trios[:,0],trios[:,1],trios[:,2]
n = len(trios)
print(f"Trios: {n:,}")

compute_objs, is_dominated, _ = build_pareto_utils(df_via, col_names, trios, eps=EPS)

X_raw, benefit = _build_decision_matrix(df_via)
X_adj = X_raw.copy()
for j,b in enumerate(benefit):
    if not b: X_adj[:,j] = 1.0 - X_raw[:,j]

# ── Score functions ────────────────────────────────────────────────────────────
def get_score(agg, norm, w):
    if norm == "minmax":
        if agg == "saw":   return (X_adj * w).sum(1)
        else:              return topsis_scores(df_via)   # NOTE: topsis uses w internally via _build_decision_matrix
    else:  # vector
        # vector: raw / ||raw||_2, benefit-aligned
        X_vec = np.zeros((N, len(w)))
        for j,c in enumerate(col_names):
            x = df_via[COL[c]].values.astype(float)
            nv = np.sqrt((x**2).sum()) or 1.0
            v = x / nv
            if not benefit[j]: v = -v
            X_vec[:,j] = v
        if agg == "saw":   return (X_vec * w).sum(1)
        else:
            PIS = np.where(benefit, X_vec.max(0), X_vec.min(0))
            NIS = np.where(benefit, X_vec.min(0), X_vec.max(0))
            dp  = np.sqrt(((X_vec * w[:,None].T - PIS * w[:,None].T)**2).sum(1))
            dn  = np.sqrt(((X_vec * w[:,None].T - NIS * w[:,None].T)**2).sum(1))
            return np.where(dp+dn==0, 0.5, dn/(dp+dn))

# ── Compute Q3 per cell ────────────────────────────────────────────────────────
cells_8 = [
    ("saw","minmax","greedy"), ("saw","minmax","optimal"),
    ("saw","vector","greedy"),  ("saw","vector","optimal"),
    ("topsis","minmax","greedy"),("topsis","minmax","optimal"),
    ("topsis","vector","greedy"),("topsis","vector","optimal"),
]

records = []
t0 = time.time()
for d in range(N_DRAWS):
    w = W[d]
    f1v,f2v,f3v = compute_objs(w)
    F1=f1v[T0]+f1v[T1]+f1v[T2]; F2=f2v[T0]+f2v[T1]+f2v[T2]; F3=f3v[T0]+f3v[T1]+f3v[T2]
    R1=F1.max()-F1.min(); R2=F2.max()-F2.min(); R3=F3.max()-F3.min()
    
    for agg,norm,mont in cells_8:
        sc = get_score(agg, norm, w)
        if mont == "greedy":
            trio = greedy_trio(sc, D)
        else:
            st = sc[T0]+sc[T1]+sc[T2]
            idx = np.argmax(st)
            trio = np.array([T0[idx],T1[idx],T2[idx]])
        
        # gap: max over all t' of min(d1,d2,d3)^+
        i0,i1,i2 = int(trio[0]),int(trio[1]),int(trio[2])
        ft1=f1v[i0]+f1v[i1]+f1v[i2]; ft2=f2v[i0]+f2v[i1]+f2v[i2]; ft3=f3v[i0]+f3v[i1]+f3v[i2]
        d1=(ft1-F1)/R1; d2=(ft2-F2)/R2; d3=(F3-ft3)/R3
        gap = max(0.0, np.minimum(np.minimum(d1,d2),d3).max())
        records.append({"draw":d,"agg":agg,"norm":norm,"mont":mont,"gap":gap})
    
    if d % 100 == 0:
        print(f"  {d/N_DRAWS*100:.0f}%  {time.time()-t0:.0f}s", flush=True)

df_out = pd.DataFrame(records)
# Q3 per cell
q3 = df_out.groupby(["agg","norm","mont"]).agg(
    Q3_mean=("gap","mean"), Q3_se=("gap",lambda x: x.std()/np.sqrt(len(x))),
    Q2_zero=("gap", lambda x: (x<EPS).mean()*100)
).reset_index()
print("\n=== Q3 results ===")
print(q3.to_string(index=False))

out = ROOT/"results"/"e1"
out.mkdir(exist_ok=True)
df_out.to_parquet(out/"q3_perdraw.parquet", index=False)
q3.to_csv(out/"q3_results.csv", index=False)
print(f"\nSaved. Time: {time.time()-t0:.1f}s")
