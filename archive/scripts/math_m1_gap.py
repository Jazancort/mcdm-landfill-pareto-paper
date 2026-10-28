"""scripts/math_m1_gap.py  (v3 — fully vectorised, CHUNK=2000, ~120MB per iter)
Verificação numérica M1: gap=0 AND weakly dominated = contra-exemplos.
"""
import os, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

if "MCDM_DATA_DIR" not in os.environ:
    os.environ["MCDM_DATA_DIR"] = "/home/julioazancort/scratch/mcdm"

from mcdm_experiment import load_data, impute_nan, COL, AHP_WEIGHTS, haversine_km, MIN_DIST_KM
from pareto_utils import build_pareto_utils

df_all,_,_ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]]>0].copy()
N = len(df_via); assert N == 389
col_names = list(AHP_WEIGHTS.keys())
w_ahp = np.array(list(AHP_WEIGHTS.values()))
D = haversine_km(df_via["latitude (degrees)"].values, df_via["longitude (degrees)"].values)
valid = D >= MIN_DIST_KM

trios_list = [(i,j,k) for i in range(N) for j in range(i+1,N) if valid[i,j]
              for k in range(j+1,N) if valid[i,k] and valid[j,k]]
trios = np.array(trios_list, dtype=np.int32)
T0,T1,T2 = trios[:,0],trios[:,1],trios[:,2]
n = len(trios)
print(f"Trios: {n:,}", flush=True)

compute_objs,_,_ = build_pareto_utils(df_via, col_names, trios, eps=1e-9)
f1v,f2v,f3v = compute_objs(w_ahp)
F1=f1v[T0]+f1v[T1]+f1v[T2]
F2=f2v[T0]+f2v[T1]+f2v[T2]
F3=f3v[T0]+f3v[T1]+f3v[T2]
R1=F1.max()-F1.min(); R2=F2.max()-F2.min(); R3=F3.max()-F3.min()
print(f"R1={R1:.4f} R2={R2:.4f} R3={R3:.4f}", flush=True)

EPS = 1e-9
CHUNK = 500   # ~23GB per chunk safe on Athena (92GiB available)

gap = np.zeros(n, dtype=np.float32)
weakly_dom = np.zeros(n, dtype=bool)

t0 = time.time()
print("Computing gap and weak dominance (vectorised chunks)...", flush=True)

for s in range(0, n, CHUNK):
    e = min(s + CHUNK, n)
    b = e - s

    F1b = F1[s:e, None]   # (b, 1)
    F2b = F2[s:e, None]
    F3b = F3[s:e, None]

    # --- strict gap (max over t' of min of 3 terms) ---
    d1 = (F1b - F1[None, :]) / R1   # (b, n): F1(t)-F1(t'), positive if t worse
    d2 = (F2b - F2[None, :]) / R2
    d3 = (F3[None, :] - F3b) / R3   # F3(t')-F3(t), positive if t' safer
    mn = np.minimum(np.minimum(d1, d2), d3)
    # exclude self-comparison
    for bi in range(b):
        mn[bi, s + bi] = -1.0
    gap[s:e] = np.maximum(0, mn.max(axis=1)).astype(np.float32)

    # --- weak Pareto dominance: exists t' such that ---
    # F1(t') <= F1(t)  AND  F2(t') <= F2(t)  AND  F3(t') >= F3(t)
    # with at least one strict inequality
    weak = (F1[None,:] <= F1b+EPS) & (F2[None,:] <= F2b+EPS) & (F3[None,:] >= F3b-EPS)
    strict = (F1[None,:] < F1b-EPS) | (F2[None,:] < F2b-EPS) | (F3[None,:] > F3b+EPS)
    dom = weak & strict
    for bi in range(b):
        dom[bi, s + bi] = False
    weakly_dom[s:e] = dom.any(axis=1)

    if (s // CHUNK) % 100 == 0:
        pct = e/n*100
        print(f"  {pct:.1f}%  elapsed={time.time()-t0:.0f}s", flush=True)

gap0 = gap < EPS
n_pareto  = int((~weakly_dom).sum())
n_wd      = int(weakly_dom.sum())
n_ce      = int((gap0 & weakly_dom).sum())   # counter-examples

print(f"\n=== Results ===", flush=True)
print(f"Total trios:                    {n:>10,}")
print(f"Pareto-efficient (~weakly_dom): {n_pareto:>10,}  ({n_pareto/n*100:.2f}%)")
print(f"Weakly dominated:               {n_wd:>10,}  ({n_wd/n*100:.2f}%)")
print(f"gap=0 AND weakly dominated:     {n_ce:>10,}  <- COUNTER-EXAMPLES")

if n_ce > 0:
    print("\nCONCLUSION: gap=0 does NOT imply Pareto-efficient.")
    print(f"  {n_ce:,} trios are weakly dominated but have gap=0.")
    print("  Claim 'gap(t)=0 iff t in F' is FALSE in Fogo data at nominal weights.")
    idx = np.where(gap0 & weakly_dom)[0][0]
    print(f"  First CE: trio_idx={idx} F1={F1[idx]:.4f} F2={F2[idx]:.4f} F3={F3[idx]:.4f} gap={gap[idx]:.2e}")
else:
    print("\nNo counter-examples at nominal AHP weights.")
    print("Claim holds empirically here; mathematical issue (strict vs weak) remains.")

print(f"\nTotal time: {time.time()-t0:.1f}s", flush=True)

out = ROOT / "results" / "math"
out.mkdir(exist_ok=True)
pd.DataFrame({
    "metric": ["n_trios","n_pareto","n_weakly_dom","n_gap0_weakly_dom"],
    "count":  [n, n_pareto, n_wd, n_ce],
    "pct":    [100, n_pareto/n*100, n_wd/n*100, n_ce/n*100],
}).to_csv(out/"math_m1_gap.csv", index=False)
print(f"Saved: {out}/math_m1_gap.csv")
