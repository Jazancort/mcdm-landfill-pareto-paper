import pandas as pd
import glob
from pathlib import Path

results_dir = Path(__file__).parent.parent / 'results'
csv_files = sorted(results_dir.glob('wp4_synthetic_w*.csv'))
print(f"Found {len(csv_files)} worker files: {[f.name for f in csv_files]}")

dfs = [pd.read_csv(f) for f in csv_files]
df = pd.concat(dfs, ignore_index=True)
df = df.sort_values(['n_sparse', 'p0', 'shape', 'rep']).reset_index(drop=True)

out_csv = results_dir / 'wp4_synthetic.csv'
df.to_csv(out_csv, index=False)
print(f"Saved merged results ({len(df)} rows) to {out_csv.name}")

print("\n=== Regression check (Q2_mm_opt must be 1.000) ===")
bad = df[df['Q2_mm_opt'] < 0.999]
if len(bad):
    print(f"WARNING: {len(bad)} violations!")
    print(bad[['n_sparse', 'p0', 'shape', 'rep', 'Q2_mm_opt']])
else:
    print("PERFECT: 0 violations across all 240 instances (all Q2_mm_opt == 1.000)!")

print("\n=== Summary by Cell (Mean Q2 and Q3) ===")
q2_cols = [c for c in df.columns if c.startswith('Q2_') and not c.startswith('Q2_se_')]
q3_cols = [c for c in df.columns if c.startswith('Q3_')]
print("Mean Q2:\n", df[q2_cols].mean().round(4).to_string())
print("\nMean Q3:\n", df[q3_cols].mean().round(4).to_string())

print("\n=== Q2 by N_SPARSE ===")
print(df.groupby('n_sparse')[['tv_vec'] + q2_cols].mean().round(3).to_string())

print("\n=== Q2 by (N_SPARSE, P0) ===")
print(df.groupby(['n_sparse', 'p0'])[['tv_vec', 'Q2_mm_grd', 'Q2_vec_grd', 'Q2_vec_opt']].mean().round(3).to_string())

print("\n=== Primary Outcome: Contrast Q2(mm/grd) - Q2(vec/grd) ===")
df['loss_comb']   = df['Q2_mm_opt']  - df['Q2_mm_grd']    # Combinatorial loss only
df['loss_reweight'] = df['Q2_mm_opt'] - df['Q2_vec_opt']  # Pure reweighting loss
df['loss_both']   = df['Q2_mm_grd']  - df['Q2_vec_grd']   # Contrast Q2(mm/grd) - Q2(vec/grd)
print(df.groupby('n_sparse')[['tv_vec', 'loss_comb', 'loss_reweight', 'loss_both']].mean().round(3).to_string())

print("\n=== Correlation with TV(vector) ===")
corr = df[['tv_vec', 'loss_reweight', 'loss_both', 'Q2_vec_grd', 'Q2_vec_opt']].corr()
print(corr['tv_vec'].round(4).to_string())
