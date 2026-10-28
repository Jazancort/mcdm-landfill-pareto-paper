"""
Paired test: Peldschus vs min-max under greedy assembly.
Draws share seed=42 -> each draw is a paired observation.
Also tests optimal assembly and Q2_mean for completeness.
"""
import pandas as pd
import numpy as np
from scipy import stats

df = pd.read_csv('results/wp3_mc_results.csv')

# Isolate the two norms
mm  = df[df['norm'] == 'min-max'].sort_values('draw').reset_index(drop=True)
pel = df[df['norm'] == 'Peldschus'].sort_values('draw').reset_index(drop=True)

assert (mm['draw'].values == pel['draw'].values).all(), "Draws don't align"
n = len(mm)

# Paired differences (Peldschus - min-max), greedy and optimal
d_greedy  = pel['nd_greedy'].values  - mm['nd_greedy'].values
d_optimal = pel['nd_optimal'].values - mm['nd_optimal'].values
d_mean    = (d_greedy + d_optimal) / 2.0

def paired_t(d, label):
    t, p = stats.ttest_1samp(d, 0)
    mean_d = d.mean() * 100          # in pp
    se_d   = d.std(ddof=1) / np.sqrt(len(d)) * 100
    rho    = np.corrcoef(
        pel['nd_greedy'].values, mm['nd_greedy'].values)[0, 1]
    print(f"  {label}:")
    print(f"    n={n}, mean diff={mean_d:+.2f} pp, SE={se_d:.2f} pp")
    print(f"    t={t:.3f}, p={p:.4f} (two-tailed)")
    return mean_d, se_d, t, p

print("=== Paired test: Peldschus - min-max ===")
print(f"  Correlation of greedy outcomes across draws: "
      f"{np.corrcoef(pel['nd_greedy'].values, mm['nd_greedy'].values)[0,1]:.3f}")
print()

mg, seg, tg, pg = paired_t(d_greedy,  "Greedy assembly")
mo, seo, to, po = paired_t(d_optimal, "Optimal assembly")
mm_, sem_, tm_, pm_ = paired_t(d_mean, "Mean (greedy+optimal)")

print()
print("=== Summary ===")
print(f"  Greedy:  Peldschus {mg:+.1f} pp vs min-max, p={pg:.4f} => "
      f"{'SURVIVES' if pg < 0.05 else 'does NOT survive'} paired test")
print(f"  Optimal: Peldschus {mo:+.1f} pp vs min-max, p={po:.4f} => "
      f"{'SURVIVES' if po < 0.05 else 'does NOT survive'} paired test")
print(f"  Mean:    Peldschus {mm_:+.1f} pp vs min-max, p={pm_:.4f} => "
      f"{'SURVIVES' if pm_ < 0.05 else 'does NOT survive'} paired test")
print()
print("Interpretation:")
if pg < 0.05 and po >= 0.05:
    print("  Greedy effect survives pairing, optimal does not.")
    print("  => Peldschus finding is a RESULT (greedy foreclosure mitigation).")
elif pg < 0.05 and po < 0.05:
    print("  Both survive => Peldschus finding is a strong RESULT.")
elif pg >= 0.05:
    print("  Greedy effect does not survive pairing => relegate to footnote.")
