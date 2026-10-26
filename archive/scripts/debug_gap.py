# -*- coding: utf-8 -*-
"""Investiga discrepancia de gaps - v2."""
import sys, numpy as np, pandas as pd, os
sys.path.insert(0, 'scripts')
from mcdm_experiment import load_data, impute_nan, COL, compute_objectives

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
col_prot = COL['protected']
df_via = df_imp[df_imp[col_prot] > 0].copy()

# par uses 0-based indices into df_via (not df_all)
# via_idx[i] = original row index in df_imp
via_idx = list(df_via.index)  # 389 elements, values are original df indices

print(f"df_via size: {len(df_via)}, max local idx par uses: {par[['idx1','idx2','idx3']].max().max()}")

objs_A = compute_objectives(df_via, df_imp)  # space A

# Mapping: par.idx_i -> via_idx[par.idx_i] -> objs_A row
# Check row 0
r0 = par.iloc[0]
g0,g1,g2 = via_idx[int(r0.idx1)], via_idx[int(r0.idx2)], via_idx[int(r0.idx3)]
our_f1 = objs_A.loc[g0,'f1']+objs_A.loc[g1,'f1']+objs_A.loc[g2,'f1']
print(f"Par row0 local[{int(r0.idx1)},{int(r0.idx2)},{int(r0.idx3)}] -> global[{g0},{g1},{g2}]")
print(f"  par.Cost={r0.Cost:.6f}  our_f1={our_f1:.6f}  1-our_f1={1-our_f1:.6f}")

# Neither matches. The pareto CSV is from the older code with different normalisation.
# Let's try direct global index (not local)
print()
print("Trying global indices directly:")
g0d,g1d,g2d = int(r0.idx1), int(r0.idx2), int(r0.idx3)
if g0d in objs_A.index and g1d in objs_A.index and g2d in objs_A.index:
    f1d = objs_A.loc[g0d,'f1']+objs_A.loc[g1d,'f1']+objs_A.loc[g2d,'f1']
    f2d = objs_A.loc[g0d,'f2']+objs_A.loc[g1d,'f2']+objs_A.loc[g2d,'f2']
    print(f"  f1={f1d:.6f} par.Cost={r0.Cost:.6f}")
else:
    print("  Global indices not all in objs_A")

# The key question: what does eq:gap in the article use as R_l?
# eq:gap: R_l = max F_l - min F_l over T (all feasible trios)
# We don't have all feasible trios, only 213 Pareto ones.
# But mcdm_trios.csv has gap=0.0097. Let's check the gap source code.
# Load and inspect mc_aprime_full.py or monte_carlo_q2.py for gap computation

# Check what space_aprime.py gives
sa_path = 'scripts/results/space_aprime.csv'
mc_path = 'scripts/results/mcdm_trios.csv'
print()
print("mcdm_trios.csv (gap=0.0097):")
trios = pd.read_csv(mc_path)
row = trios[trios['global_ids']=='[184, 279, 320]']
print(row[['f1','f2','f3','gap']].to_string(index=False))

print()
print("Files in scripts/results/:")
for f in sorted(os.listdir('scripts/results/')):
    sz = os.path.getsize(f'scripts/results/{f}')
    print(f'  {f}  ({sz} bytes)')
