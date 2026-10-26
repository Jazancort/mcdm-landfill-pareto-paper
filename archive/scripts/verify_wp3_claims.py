"""
Verify all numerical claims in reviewer's critique.
Tasks:
  1. slope=-89.25 on Q2_mean (3 levels)
  2. Leverage h_ii and Cook D for vector
  3. Quadratic inestimability (p=0.67, VIF=23.8)
  4. Peldschus non-monotone: 86.6 > 82.9 by 3.7 pp
  5. sum Q2_mean=73.1% > vector 55.4% -> R2 drops to 0.40
  6. 72% perm effective weight under sum normalisation
  7. Tab3 legacy regression: slope=-86.72, SE=6.72, p=0.049 (3 levels on published Tab3 values)
"""
import numpy as np
import pandas as pd
from scipy import stats

df = pd.read_csv('results/wp3_summary.csv')

# ----- 1. Three-level regression on Q2_mean -----
sel3 = df[df['norm'].isin(['min-max','ranks','vector'])].sort_values('TV')
x3 = sel3['TV'].values
y3 = sel3['Q2_mean'].values
s3, b3, r3, p3, se3 = stats.linregress(x3, y3)
print("=== 3-level Q2_mean regression ===")
print(f"  slope={s3:.4f}  SE={se3:.4f}  R2={r3**2:.4f}  p={p3:.4f}")

# Tab3 published values (rounded)
x_tab3 = np.array([0.000, 0.091, 0.315])
y_tab3 = np.array([82.3, 76.5, 55.5])
st, bt, rt, pt, set_ = stats.linregress(x_tab3, y_tab3)
print(f"  [legacy Tab3 published values]: slope={st:.4f}  SE={set_:.4f}  R2={rt**2:.4f}  p={pt:.4f}")

# ----- 2. Leverage and Cook D -----
print("\n=== Leverage h_ii and Cook D (3-level, Q2_mean) ===")
n = len(x3)
X = np.column_stack([np.ones(n), x3])
H = X @ np.linalg.inv(X.T @ X) @ X.T
h = np.diag(H)
y_hat = b3 + s3 * x3
resid = y3 - y_hat
mse = np.sum(resid**2) / (n - 2)
p_params = 2
cook_d = (resid**2 / (p_params * mse)) * (h / (1 - h)**2)
for i, norm in enumerate(sel3['norm'].values):
    print(f"  {norm:10s}  TV={x3[i]:.4f}  h_ii={h[i]:.4f}  Cook_D={cook_d[i]:.4f}")

# ----- 3. Quadratic term (5 levels) -----
print("\n=== Quadratic term (5 monotone levels, Q2_mean) ===")
sel5 = df[df['norm'].isin(['min-max','max','Peldschus','ranks','vector'])].sort_values('TV')
x5 = sel5['TV'].values
y5 = sel5['Q2_mean'].values
X5 = np.column_stack([np.ones(5), x5, x5**2])
# Condition number check
cond = np.linalg.cond(X5.T @ X5)
print(f"  Condition number of X'X: {cond:.1f}")
try:
    beta5 = np.linalg.lstsq(X5, y5, rcond=None)[0]
    # VIF for x**2
    X_quad_on_lin = np.column_stack([np.ones(5), x5])
    r2_quad = stats.linregress(x5**2, x5)[2]**2
    # manual: regress x2 on [1, x, x^2] excluding x^2 itself
    # VIF(x^2) = 1/(1 - R^2 of x^2 regressed on others)
    r2_x2_on_x = stats.linregress(x5, x5**2)[2]**2
    vif_quad = 1 / (1 - r2_x2_on_x)
    # p-value for quad term using t-stat
    resid5 = y5 - X5 @ beta5
    mse5 = np.sum(resid5**2) / (5 - 3)
    XtX_inv = np.linalg.inv(X5.T @ X5)
    se_beta5 = np.sqrt(mse5 * np.diag(XtX_inv))
    t_quad = beta5[2] / se_beta5[2]
    p_quad = 2 * stats.t.sf(abs(t_quad), 5 - 3)
    print(f"  quad coef={beta5[2]:.2f}  SE={se_beta5[2]:.2f}  t={t_quad:.2f}  p={p_quad:.4f}")
    print(f"  VIF(x^2 on x): {vif_quad:.1f}")
    print(f"  Expected from reviewer: coef~-57.4, SE~117.5, p=0.67, VIF~23.8")
except Exception as e:
    print(f"  Error: {e}")

# ----- 4. Peldschus non-monotone -----
print("\n=== Peldschus non-monotone check ===")
mm = df[df['norm']=='min-max']['Q2_mean'].values[0]
pel = df[df['norm']=='Peldschus']['Q2_mean'].values[0]
print(f"  min-max Q2_mean={mm:.1f}%  Peldschus Q2_mean={pel:.1f}%")
print(f"  Peldschus ABOVE min-max by {pel-mm:.1f} pp => non-monotone")
# Greedy assembly detail
mm_g = df[df['norm']=='min-max']['Q2_greedy'].values[0]
pel_g = df[df['norm']=='Peldschus']['Q2_greedy'].values[0]
mm_o = df[df['norm']=='min-max']['Q2_optimal'].values[0]
pel_o = df[df['norm']=='Peldschus']['Q2_optimal'].values[0]
print(f"  Greedy: min-max={mm_g:.1f}%  Peldschus={pel_g:.1f}%  diff={pel_g-mm_g:+.1f} pp")
print(f"  Optimal: min-max={mm_o:.1f}%  Peldschus={pel_o:.1f}%  diff={pel_o-mm_o:+.1f} pp")

# ----- 5. sum R2 drops -----
print("\n=== Sum: R2 drops, p becomes insignificant ===")
sel4_incl_sum = df[df['norm'].isin(['min-max','ranks','vector','sum'])].sort_values('TV')
xs = sel4_incl_sum['TV'].values
ys = sel4_incl_sum['Q2_mean'].values
ss, bs, rs, ps, ses = stats.linregress(xs, ys)
print(f"  4-level incl. sum: slope={ss:.2f}  SE={ses:.2f}  R2={rs**2:.4f}  p={ps:.4f}")
print(f"  Expected: R2~0.40, p~0.18")

# ----- 6. Sum normalisation 72% perm effective weight -----
print("\n=== Perm effective weight under sum normalisation ===")
# We need amplitudes under sum normalisation.
# sum normalisation: A_j = (mean_j of x_j^norm) for benefit cols; or range...
# Actually for sum-norm: x_j_norm = x_j / sum_j(x_j), so A_j = std(x_j_norm)
# But the review says perm amp range is [0.0045, 0.1303].
# That matches the Aj values we have in Tab1 (vector norm).
# Under SUM norm, Aj = std(x_j / mean(x_j)) * (1/n * ...) -- need raw data
# Instead: use the wp3_summary to extract the sum amplitude from the identity:
# ||delta||_2 = 2*TV/sqrt(m_eff)
sum_row = df[df['norm']=='sum'].iloc[0]
tv_sum = sum_row['TV']
meff_sum = sum_row['m_eff']
print(f"  sum: TV={tv_sum:.4f}  m_eff={meff_sum:.4f}")
# Under sum: effective weight w_eff_j = w_j * A_j / sum(w_k A_k)
# The claim is that perm effective weight = 72%
# This requires the 11 amplitudes under sum normalisation.
# We can cross-check: if perm Aj_sum = 0.1303 and sum of w*A = w_perm*0.1303/0.72
# Sum Aj_sum for 11 criteria must total to produce TV=0.567
# TV = ||w_eff - w|| = ||delta||
# Without the individual amplitudes we cannot reproduce the 72% claim directly.
# Report that it requires explicit amplitude array from wp3_amplitudes.py output.
print("  Cannot verify 72% without per-criterion amplitudes under sum norm.")
print("  Need: wp3_amplitudes.py output for sum normalisation (all 11 A_j values).")
print("  Claim: w_perm * A_j_perm^sum / sum_k(w_k * A_k^sum) = 0.72")
print("  Available: range [0.0045, 0.1303] cited in review, but individual weights unknown.")

# ----- 7. SE comparison: max alone vs max+Peldschus -----
print("\n=== SE with max only vs max+Peldschus ===")
sel4_max = df[df['norm'].isin(['min-max','max','ranks','vector'])].sort_values('TV')
x4m = sel4_max['TV'].values
y4m = sel4_max['Q2_mean'].values
s4m, b4m, r4m, p4m, se4m = stats.linregress(x4m, y4m)
print(f"  4-level (max only): slope={s4m:.2f}  SE={se4m:.2f}  R2={r4m**2:.4f}  p={p4m:.4f}")
# Note: reviewer says this gives slope=-89.7, SE=5.1
# Expected SE when Peldschus replaces or is added:
sel4_pel = df[df['norm'].isin(['min-max','Peldschus','ranks','vector'])].sort_values('TV')
x4p = sel4_pel['TV'].values
y4p = sel4_pel['Q2_mean'].values
s4p, b4p, r4p, p4p, se4p = stats.linregress(x4p, y4p)
print(f"  4-level (Peldschus only): slope={s4p:.2f}  SE={se4p:.2f}  R2={r4p**2:.4f}  p={p4p:.4f}")
# Now max change from 83.2 to 86.6: reviewer says SE goes 4.81->8.17
print(f"\n  Fragility: change max Q2_mean from 83.2 to 86.6")
y4m_alt = y4m.copy()
y4m_alt[1] = 86.6  # max is index 1 after sorting by TV
s4m_alt, b4m_alt, r4m_alt, p4m_alt, se4m_alt = stats.linregress(x4m, y4m_alt)
print(f"  max=83.2: SE={se4m:.2f} -> max=86.6: SE={se4m_alt:.2f}")
