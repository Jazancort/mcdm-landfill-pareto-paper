# -*- coding: utf-8 -*-
"""Verifica impacto do aspect corrigido na fronteira Pareto e Q2."""
import sys, numpy as np
sys.path.insert(0, 'scripts')
from mcdm_experiment import load_data, impute_nan, COL, AHP_WEIGHTS, compute_objectives
from pareto3d import pareto_front_3d

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
col_prot = COL['protected']
df_via = df_imp[df_imp[col_prot] > 0].copy()
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=float); w_ahp /= w_ahp.sum()
sites = list(df_via.index)
N = len(sites)

# CORRECTED objectives
objs = compute_objectives(df_via, df_imp)
f1 = objs['f1'].values; f2 = objs['f2'].values; f3 = objs['f3'].values

print("Aspect n1 check (should be 94):")
asp_col = COL['aspect']
asp_vals = df_via[asp_col].values
n1 = int(((asp_vals >= 90) & (asp_vals <= 180)).sum())
print(f"  n1 = {n1}")
print(f"  F2 range: [{f2.min():.4f}, {f2.max():.4f}]")
print()

# Load fogo_trios for Pareto
import os
trios_path = 'data/fogo_trios.npy'
if not os.path.exists(trios_path):
    print("fogo_trios.npy not found")
    sys.exit(0)

trios = np.load(trios_path).astype(np.int32)
F1t = f1[trios[:,0]] + f1[trios[:,1]] + f1[trios[:,2]]
F2t = f2[trios[:,0]] + f2[trios[:,1]] + f2[trios[:,2]]
F3t = f3[trios[:,0]] + f3[trios[:,1]] + f3[trios[:,2]]
F_all = np.column_stack([F1t, F2t, F3t])
is_nd = pareto_front_3d(F_all.astype(float))

n_front = int(is_nd.sum())
print(f"Pareto front (CORRECTED aspect): |F(A')| = {n_front}")
print(f"Published: |F(A')| = 181")
print()

# SAW optimal = argmax(F1t + F2t + F3t) — holds for any normalisation
saw_trio = F1t + F2t + F3t
best_idx = int(saw_trio.argmax())
best_sites = sorted([sites[trios[best_idx, k]] for k in range(3)])
print(f"SAW optimal (corrected): sites={best_sites}")
print(f"  In Pareto front: {is_nd[best_idx]}")
print(f"  F = ({F1t[best_idx]:.4f}, {F2t[best_idx]:.4f}, {F3t[best_idx]:.4f})")
print(f"  Published (Tab2): {{184,430,460}}, F=(0.0811, 0.5568, 0.6170)")
print()

# Quick Q2 estimate: fraction of SAW-optimal trios per draw
# Use nominal weights for a quick check
rng = np.random.default_rng(42)
n_draws = 200
kappa = 50
w_draws = rng.dirichlet(kappa * w_ahp, size=n_draws)
in_front_count = 0
for w_d in w_draws:
    saw_d = F1t * w_d[:4].sum() + F2t * w_d[4:8].sum() + F3t * w_d[8:].sum()
    # Use F1t+F2t+F3t as proxy — correct for min-max (Aj=1)
    # For min-max, SAW = sum(w_j * c_j) = sum over groups = F1+F2+F3 (unweighted)
    # Actually SAW = w·x where x is normalised. F_l = sum_{j in G_l} w_j c_j
    # So SAW = F1 + F2 + F3 independent of w (since Aj=1 for min-max)
    # For a quick check with the actual w draws:
    saw_d = F1t + F2t + F3t  # min-max SAW is weight-independent
    best_d = int(saw_d.argmax())
    if is_nd[best_d]:
        in_front_count += 1
q2_mm = in_front_count / n_draws
print(f"Quick Q2 check (min-max, {n_draws} draws): {q2_mm:.3f}")
print(f"Published Q2[SAW/mm/opt/A']: 1.000 (by prop:p1)")
print()
print("Note: Q2=1 for SAW/mm/opt by prop:p1 regardless of aspect convention.")
print("The material impact is on F2 values in Tab2 and vector-norm Q2.")
print()

# Compare F2 for published Tab2 portfolios
print("=== Tab2 F2 comparison ===")
portfolios = {
    'SAW greedy {184,279,320}':  [184, 279, 320],
    'SAW optimal {184,430,460}': [184, 430, 460],
    'TOPSIS vec {233,320,355}':  [233, 320, 355],
    'VIKOR {233,279,320}':       [233, 279, 320],
}
for name, p_sites in portfolios.items():
    f2_new = sum(objs.loc[s, 'f2'] for s in p_sites)
    print(f"  {name}: F2(corrected)={f2_new:.4f}")
