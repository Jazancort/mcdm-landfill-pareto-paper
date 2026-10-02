"""scripts/math_m1_gap.py
Verificação numérica para M1: conta trios com gap=0 mas fracamente dominados.

gap(t) = max_{t'} min( (F1(t)-F1(t'))/R1, (F2(t)-F2(t'))/R2, (F3(t')-F3(t))/R3 )^+

A hipótese do artigo: gap=0 iff t ∈ fronteira de Pareto.
A análise algébrica mostrou que isto é FALSO: gap usa dominação estrita,
Pareto usa dominação fraca. Este script conta contra-exemplos nos dados reais.

Corre em ~10 min na Athena (loop puro sobre 1.9M trios).
Output: results/math/math_m1_gap.log  e  results/math/math_m1_gap.csv
"""
import os, sys, time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

if "MCDM_DATA_DIR" not in os.environ:
    athena = "/home/julioazancort/scratch/mcdm"
    os.environ["MCDM_DATA_DIR"] = athena if os.path.exists(athena) else str(ROOT / "data")

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, haversine_km, MIN_DIST_KM,
)
from pareto_utils import build_pareto_utils

# ── Data ──────────────────────────────────────────────────────────────────────
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]] > 0].copy()
N = len(df_via)
assert N == 389

col_names = list(AHP_WEIGHTS.keys())
w_ahp     = np.array(list(AHP_WEIGHTS.values()))

D     = haversine_km(df_via["latitude (degrees)"].values, df_via["longitude (degrees)"].values)
valid = D >= MIN_DIST_KM

trios_list = [(i,j,k) for i in range(N) for j in range(i+1,N) if valid[i,j]
              for k in range(j+1,N) if valid[i,k] and valid[j,k]]
trios = np.array(trios_list, dtype=np.int32)
T0, T1, T2 = trios[:,0], trios[:,1], trios[:,2]
n = len(trios)
print(f"Trios: {n:,}")

# ── Objectives at nominal AHP weights ─────────────────────────────────────────
compute_objs, _, _ = build_pareto_utils(df_via, col_names, trios, eps=1e-9)
f1v, f2v, f3v = compute_objs(w_ahp)
F1 = f1v[T0]+f1v[T1]+f1v[T2]
F2 = f2v[T0]+f2v[T1]+f2v[T2]
F3 = f3v[T0]+f3v[T1]+f3v[T2]
R1 = F1.max()-F1.min(); R2 = F2.max()-F2.min(); R3 = F3.max()-F3.min()
print(f"R1={R1:.4f} R2={R2:.4f} R3={R3:.4f}")

EPS = 1e-9

# ── Vectorised computation (no per-trio loop — uses broadcasting in chunks) ───
CHUNK = 50_000
gap = np.zeros(n)
weakly_dom = np.zeros(n, dtype=bool)
strictly_dom = np.zeros(n, dtype=bool)

t0 = time.time()
for start in range(0, n, CHUNK):
    end = min(start + CHUNK, n)
    # F arrays for block: shape (block, n)
    F1b = F1[start:end, None]; F2b = F2[start:end, None]; F3b = F3[start:end, None]

    # strict gap: min of three strict improvements
    d1 = (F1b - F1[None,:]) / R1   # F1(t) - F1(t') (t costlier than t' iff >0)
    d2 = (F2b - F2[None,:]) / R2
    d3 = (F3[None,:] - F3b) / R3   # F3(t') - F3(t) (t' safer iff >0)
    mins = np.minimum(np.minimum(d1, d2), d3)
    # zero out self-comparison
    self_idx = np.arange(start, end) - start
    for bi in range(end - start):
        mins[bi, start + bi] = -1.0   # exclude self
    gap[start:end] = np.maximum(0, mins.max(axis=1))

    # weak Pareto dominance: t' weakly dominates t if
    # F1(t')<=F1(t) AND F2(t')<=F2(t) AND F3(t')>=F3(t), with at least one strict
    F1b2 = F1[start:end, None]; F2b2 = F2[start:end, None]; F3b2 = F3[start:end, None]
    weak   = (F1[None,:] <= F1b2+EPS) & (F2[None,:] <= F2b2+EPS) & (F3[None,:] >= F3b2-EPS)
    strict = (F1[None,:] <  F1b2-EPS) | (F2[None,:] <  F2b2-EPS) | (F3[None,:] >  F3b2+EPS)
    dominators = weak & strict
    # exclude self
    for bi in range(end - start):
        dominators[bi, start + bi] = False
    weakly_dom[start:end]   = dominators.any(axis=1)
    strictly_dom[start:end] = (mins > EPS).any(axis=1)  # has strict dominator

    if (start // CHUNK) % 5 == 0:
        pct = end/n*100
        print(f"  {pct:.0f}% ({end:,}/{n:,})  elapsed {time.time()-t0:.0f}s")

print(f"Done in {time.time()-t0:.1f}s")

gap0           = gap < EPS
n_gap0         = gap0.sum()
n_weakly_dom   = weakly_dom.sum()
n_strictly_dom = strictly_dom.sum()
n_gap0_weakly  = (gap0 & weakly_dom).sum()
n_pareto       = (~weakly_dom).sum()
n_gap0_pareto  = (gap0 & ~weakly_dom).sum()

print(f"\n=== Results ===")
print(f"Total trios:                      {n:>10,}")
print(f"gap=0 (no strict dominator):      {n_gap0:>10,}  ({n_gap0/n*100:.2f}%)")
print(f"Weakly dominated (Pareto):        {n_weakly_dom:>10,}  ({n_weakly_dom/n*100:.2f}%)")
print(f"Strictly dominated:               {n_strictly_dom:>10,}  ({n_strictly_dom/n*100:.2f}%)")
print(f"Pareto-efficient (~weakly_dom):   {n_pareto:>10,}  ({n_pareto/n*100:.2f}%)")
print(f"")
print(f"gap=0 AND weakly dominated:       {n_gap0_weakly:>10,}  <- COUNTER-EXAMPLES to claim")
print(f"gap=0 AND Pareto-efficient:       {n_gap0_pareto:>10,}")
print(f"")
if n_gap0_weakly > 0:
    print(f"CONCLUSION: gap=0 does NOT imply Pareto-efficient.")
    print(f"  {n_gap0_weakly:,} trios have gap=0 but are weakly dominated.")
    print(f"  The claim 'gap=0 iff t in F' is FALSE.")
    print(f"  Q3=0 iff Q2=1 does NOT hold with this definition of gap.")
else:
    print(f"CONCLUSION: no counter-examples found in Fogo data at nominal weights.")
    print(f"  The claim holds empirically here, but may fail at other weights.")

# Save
out_dir = ROOT / "results" / "math"
out_dir.mkdir(exist_ok=True)
results = pd.DataFrame({
    "metric": ["n_trios","gap0","weakly_dom","strictly_dom","pareto_efficient",
               "gap0_AND_weakly_dom","gap0_AND_pareto"],
    "count":  [n, n_gap0, n_weakly_dom, n_strictly_dom, n_pareto,
               n_gap0_weakly, n_gap0_pareto],
})
results.to_csv(out_dir / "math_m1_gap.csv", index=False)
print(f"\nSaved: {out_dir}/math_m1_gap.csv")
