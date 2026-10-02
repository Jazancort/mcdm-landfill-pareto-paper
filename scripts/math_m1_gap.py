"""scripts/math_m1_gap.py  (v2 — memory-efficient)
Verificação numérica para M1: conta trios com gap=0 mas fracamente dominados.

gap(t) = max_{t'} min( (F1(t)-F1(t'))/R1, (F2(t)-F2(t'))/R2, (F3(t')-F3(t))/R3 )^+

Abordagem eficiente em memória:
1. Calcular a fronteira de Pareto (dominação fraca) com pareto_utils (já existente).
2. Para cada trio, verificar se é dominado fracamente = não está na fronteira.
3. Calcular gap(t) usando apenas o melhor t' em cada eixo — upper bound.
   Se o upper bound de gap é 0, então gap=0. Se >0, verificar exactamente.

Alternativa mais simples: para os ~F trios na fronteira, gap=0 por construção.
Para os trios fora da fronteira, verificamos se gap=0 (sem dominador estrito).
Se gap=0 para um trio fora da fronteira → contra-exemplo confirmado.
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

from mcdm_experiment import load_data, impute_nan, COL, AHP_WEIGHTS, haversine_km, MIN_DIST_KM
from pareto_utils import build_pareto_utils

# ── Data ──────────────────────────────────────────────────────────────────────
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
print(f"Trios: {n:,}")

compute_objs, is_dominated, _ = build_pareto_utils(df_via, col_names, trios, eps=1e-9)
f1v,f2v,f3v = compute_objs(w_ahp)
F1=f1v[T0]+f1v[T1]+f1v[T2]; F2=f2v[T0]+f2v[T1]+f2v[T2]; F3=f3v[T0]+f3v[T1]+f3v[T2]
R1=F1.max()-F1.min(); R2=F2.max()-F2.min(); R3=F3.max()-F3.min()
print(f"R1={R1:.4f} R2={R2:.4f} R3={R3:.4f}")

EPS = 1e-9

# ── Step 1: classify each trio as weakly dominated or not ────────────────────
# Use is_dominated from pareto_utils (built with weak dominance + self-exclusion)
print("Classifying trios as weakly dominated...")
t0 = time.time()
weakly_dom = np.zeros(n, dtype=bool)
for i in range(n):
    weakly_dom[i] = is_dominated(trios[i], F1, F2, F3)
    if i % 100000 == 0:
        print(f"  {i/n*100:.1f}%  {time.time()-t0:.0f}s")

n_pareto = (~weakly_dom).sum()
n_weakly_dom = weakly_dom.sum()
print(f"Pareto-efficient: {n_pareto:,} ({n_pareto/n*100:.2f}%)")
print(f"Weakly dominated: {n_weakly_dom:,} ({n_weakly_dom/n*100:.2f}%)")

# ── Step 2: for weakly-dominated trios, compute strict gap ──────────────────
# gap(t) = max_{t'} min( d1(t,t'), d2(t,t'), d3(t,t') )^+
# where d1=(F1(t)-F1(t'))/R1, d2=(F2(t)-F2(t'))/R2, d3=(F3(t')-F3(t))/R3
# If gap=0 for a weakly-dominated trio → counter-example
print("\nComputing strict gap for weakly-dominated trios...")
dom_indices = np.where(weakly_dom)[0]
n_gap0_weakly = 0
counter_examples = []

t1 = time.time()
for ci, i in enumerate(dom_indices):
    # For this trio, find max strict improvement
    # mask out self
    mask = np.ones(n, bool); mask[i] = False
    d1 = (F1[i] - F1[mask]) / R1
    d2 = (F2[i] - F2[mask]) / R2
    d3 = (F3[mask] - F3[i]) / R3
    strict_gap = np.maximum(0, np.minimum(np.minimum(d1,d2),d3).max())
    if strict_gap < EPS:
        n_gap0_weakly += 1
        if len(counter_examples) < 5:  # save first 5
            counter_examples.append({
                "trio_idx": i, "F1": F1[i], "F2": F2[i], "F3": F3[i],
                "gap": strict_gap
            })
    if ci % 50000 == 0:
        print(f"  {ci/len(dom_indices)*100:.1f}%  found {n_gap0_weakly} so far  {time.time()-t1:.0f}s")

print(f"\nTotal time: {time.time()-t0:.1f}s")
print(f"\n=== Results ===")
print(f"Total trios:                    {n:>10,}")
print(f"Pareto-efficient (~weakly_dom): {n_pareto:>10,}  ({n_pareto/n*100:.2f}%)")
print(f"Weakly dominated:               {n_weakly_dom:>10,}  ({n_weakly_dom/n*100:.2f}%)")
print(f"gap=0 AND weakly dominated:     {n_gap0_weakly:>10,}  <- COUNTER-EXAMPLES")
print()

if n_gap0_weakly > 0:
    print("CONCLUSION: gap=0 does NOT imply Pareto-efficient.")
    print(f"  {n_gap0_weakly:,} trios are weakly dominated but have gap=0.")
    print(f"  Claim 'gap(t)=0 iff t in F' is FALSE in Fogo data.")
    print(f"  Q3=0 iff Q2=1 does NOT hold with this definition of gap.")
    if counter_examples:
        print(f"\nFirst counter-example:")
        ce = counter_examples[0]
        print(f"  trio_idx={ce['trio_idx']}, F1={ce['F1']:.4f}, F2={ce['F2']:.4f}, F3={ce['F3']:.4f}, gap={ce['gap']:.2e}")
else:
    print("No counter-examples in Fogo data at nominal AHP weights.")
    print("Claim holds empirically here, but may still fail at other weight draws.")
    print("The mathematical issue (strict vs weak dominance) remains.")

# Save
out_dir = ROOT / "results" / "math"
out_dir.mkdir(exist_ok=True)
pd.DataFrame({
    "metric": ["n_trios","n_pareto","n_weakly_dom","n_gap0_weakly_dom"],
    "count":  [n, n_pareto, n_weakly_dom, n_gap0_weakly],
    "pct":    [100, n_pareto/n*100, n_weakly_dom/n*100, n_gap0_weakly/n*100],
}).to_csv(out_dir/"math_m1_gap.csv", index=False)
if counter_examples:
    pd.DataFrame(counter_examples).to_csv(out_dir/"math_m1_counterexamples.csv", index=False)
print(f"\nSaved to {out_dir}/")
