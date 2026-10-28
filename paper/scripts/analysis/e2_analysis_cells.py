# -*- coding: utf-8 -*-
"""
e2_analysis_cells.py — E2 analysis over 40 cell means + bootstrap IC ΔR².
Fixes DEV-E2-001 (TV_W = correct sum), DEV-E2-002 (M5), DEV-E2-003 (cell means),
DEV-E2-004 (P_E2_3 residuals from E1 cells).

Also: IC emparelhado para óptima < greedy (SAW e TOPSIS), Tarefa 5.
"""
import pandas as pd, numpy as np
from scipy.stats import linregress
from scipy.linalg import lstsq as sp_lstsq

# ── Load grid results ──────────────────────────────────────────────────────────
df = pd.read_csv('/home/julioazancort/scratch/mcdm-landfill-pareto/results/e2_grid_results.csv')
df['loss_opt'] = 100 - df['Q2_optimal']
df['loss_grd'] = 100 - df['Q2_greedy']

# Group weights (nominal)
W_G1, W_G2, W_G3 = 0.295, 0.356, 0.349

# TV_W = Σ_g W_g * TV_W_g  (correct, as pre-specified)
df['TV_W'] = W_G1*df['TV_W_G1'] + W_G2*df['TV_W_G2'] + W_G3*df['TV_W_G3']

# ── DEV-E2-003: aggregate to 40 cell means (s_B × s_W) ───────────────────────
cell_means = df.groupby(['s_B', 's_W']).agg(
    loss_opt_mean=('loss_opt', 'mean'),
    loss_grd_mean=('loss_grd', 'mean'),
    TV_B_mean=('TV_B', 'mean'),
    TV_W_mean=('TV_W', 'mean'),
    TV_W_eff_mean=('TV_W_eff', 'mean'),
    TV_total_mean=('TV_total', 'mean'),
    n=('rep', 'count'),
).reset_index()

N_cells = len(cell_means)
assert N_cells == 40, f"Expected 40 cells, got {N_cells}"

y   = cell_means['loss_opt_mean'].values
y_g = cell_means['loss_grd_mean'].values

print("="*70)
print(f"E2 analysis on {N_cells} cell means (s_B × s_W combinations)")
print("="*70)
print(f"loss_opt range: [{y.min():.2f}, {y.max():.2f}]pp  mean={y.mean():.2f}pp")
print(f"TV_W_eff range: [{cell_means['TV_W_eff_mean'].min():.4f}, {cell_means['TV_W_eff_mean'].max():.4f}]")
print(f"TV_W range:     [{cell_means['TV_W_mean'].min():.4f}, {cell_means['TV_W_mean'].max():.4f}]")

# ── OLS M1–M5 on cell means ───────────────────────────────────────────────────
print(f"\n{'='*70}")
print("OLS on 40 cell means (correct unit of analysis)")
print(f"{'Model':<8} {'Predictor':<16} {'R²':>7} {'slope':>9} {'intercept':>10} {'p-value':>12}")
print("-"*70)

def ols1(x, y):
    mask = np.isfinite(x)&np.isfinite(y)
    return linregress(x[mask], y[mask])

models = [
    ('M1', cell_means['TV_total_mean'].values, 'TV_total'),
    ('M2', cell_means['TV_W_mean'].values,     'TV_W (3 groups)'),
    ('M3', cell_means['TV_W_eff_mean'].values, 'TV_W_eff'),
    ('M4_B', cell_means['TV_B_mean'].values,   'TV_B'),
]

r2_results = {}
for lbl, x, name in models:
    res = ols1(x, y)
    r2 = res.rvalue**2
    r2_results[lbl] = r2
    print(f"  {lbl:<8} {name:<16} {r2:>7.4f} {res.slope:>+9.2f} {res.intercept:>10.2f} {res.pvalue:>12.4e}")

# M4 multivariate: loss ~ TV_W + TV_B
X4 = np.column_stack([cell_means['TV_W_mean'].values,
                       cell_means['TV_B_mean'].values,
                       np.ones(N_cells)])
coef4, _, _, _ = sp_lstsq(X4, y)
y4 = X4 @ coef4
ss_res4 = np.sum((y-y4)**2); ss_tot = np.sum((y-y.mean())**2)
r2_M4 = 1 - ss_res4/ss_tot
r2_results['M4'] = r2_M4
print(f"  M4       TV_W+TV_B        {r2_M4:>7.4f} [coef_W={coef4[0]:+.2f} coef_B={coef4[1]:+.2f} int={coef4[2]:+.2f}]")

# M5: loss ~ TV_W_eff + I(TV_B > 0)
I_B = (cell_means['TV_B_mean'].values > 1e-6).astype(float)
X5 = np.column_stack([cell_means['TV_W_eff_mean'].values, I_B, np.ones(N_cells)])
coef5, _, _, _ = sp_lstsq(X5, y)
y5 = X5 @ coef5
r2_M5 = 1 - np.sum((y-y5)**2)/ss_tot
r2_results['M5'] = r2_M5
print(f"  M5       TV_W_eff+I(B>0)  {r2_M5:>7.4f} [coef_eff={coef5[0]:+.2f} coef_I={coef5[1]:+.2f} int={coef5[2]:+.2f}]")

# ── P_E2_1 check on cell means ────────────────────────────────────────────────
delta_r2 = r2_results['M3'] - r2_results['M1']
print(f"\nP_E2_1 on cell means: ΔR² = R²(M3) - R²(M1) = {r2_results['M3']:.4f} - {r2_results['M1']:.4f} = {delta_r2:.4f}")

# ── Bootstrap IC for ΔR² ─────────────────────────────────────────────────────
N_BOOT = 10000
rng_b = np.random.default_rng(42)
boot_delta = np.zeros(N_BOOT)
x3 = cell_means['TV_W_eff_mean'].values
x1 = cell_means['TV_total_mean'].values
for b in range(N_BOOT):
    idx = rng_b.integers(0, N_cells, size=N_cells)
    yb, x3b, x1b = y[idx], x3[idx], x1[idx]
    if np.std(x3b) < 1e-10 or np.std(x1b) < 1e-10:
        boot_delta[b] = 0.
        continue
    r2_3b = linregress(x3b, yb).rvalue**2
    r2_1b = linregress(x1b, yb).rvalue**2
    boot_delta[b] = r2_3b - r2_1b

ci_low, ci_high = np.percentile(boot_delta, [2.5, 97.5])
print(f"Bootstrap 95% CI for ΔR²: [{ci_low:.4f}, {ci_high:.4f}]")
print(f"Threshold: 0.10")
if ci_low > 0.10:
    print("P_E2_1: CONFIRMED (CI entirely above 0.10)")
elif ci_high < 0.10:
    print("P_E2_1: REJECTED (CI entirely below 0.10)")
else:
    print("P_E2_1: INCONCLUSIVE (CI spans 0.10; cannot confirm or reject)")

# ── P_E2_2: asserção s_W=0 ────────────────────────────────────────────────────
print(f"\nP_E2_2 (hard assertion): all s_W=0 cells have Q2_optimal=100%?")
sw0 = df[df['s_W']==0.0]
not_100 = sw0[sw0['Q2_optimal'] < 99.9]
if len(not_100) == 0:
    print(f"  PASS: all {len(sw0)} instances with s_W=0 have Q2_optimal=100.0%")
else:
    print(f"  FAIL: {len(not_100)} instances with s_W=0 have Q2_optimal < 100%:")
    print(not_100[['s_B','s_W','rep','Q2_optimal','TV_W_eff']].to_string())

# ── P_E2_3: E1 residuals ──────────────────────────────────────────────────────
print(f"\nP_E2_3: E1 cells on M3 regression line (residual < 5pp)?")
res3 = ols1(x3, y)
e1_cells = [
    ('E1-B', 0.0000, 0.0),
    ('E1-W', 0.1987, 35.8),
    ('E1-V', 0.2335, 43.2),
]
print(f"M3 model: loss = {res3.slope:.2f} * TV_W_eff + {res3.intercept:.2f}")
print(f"{'Cell':<8} {'TV_W_eff':>10} {'Observed':>10} {'Predicted':>10} {'Residual':>10}")
for name, tvweff, obs_loss in e1_cells:
    pred = res3.slope * tvweff + res3.intercept
    resid = obs_loss - pred
    flag = "OK" if abs(resid) < 5 else "FAIL"
    print(f"  {name:<8} {tvweff:>10.4f} {obs_loss:>10.1f}pp {pred:>10.1f}pp {resid:>+10.1f}pp  {flag}")

# ── Monotonicity check ────────────────────────────────────────────────────────
print(f"\nNon-monotone cases (loss > 30pp but TV_W_eff < median):")
tv_med = np.median(cell_means['TV_W_eff_mean'])
hi_loss = cell_means[cell_means['loss_opt_mean'] > 10]
non_mono = hi_loss[hi_loss['TV_W_eff_mean'] < tv_med]
if len(non_mono) > 0:
    print(non_mono[['s_B','s_W','TV_W_eff_mean','loss_opt_mean']].to_string())
else:
    print("  None (all high-loss cells have TV_W_eff > median)")

print(f"\nCorrelation (Spearman) TV_W_eff vs loss_opt:")
from scipy.stats import spearmanr
rho, p = spearmanr(cell_means['TV_W_eff_mean'], cell_means['loss_opt_mean'])
print(f"  ρ = {rho:.4f}  p = {p:.4e}")

# ── Tarefa 5: IC emparelhado óptima < greedy (SAW e TOPSIS) ──────────────────
print(f"\n{'='*70}")
print("Tarefa 5: IC emparelhado bootstrap — óptima < greedy")
print("="*70)

df_cube = pd.read_csv('/home/julioazancort/scratch/mcdm-landfill-pareto/results/mc_2cube_fixed_raw.csv')
df200 = df_cube[df_cube.alpha==200].copy()

# Pivot: one row per draw, columns = (agg, norm, mont)
pivot = df200.pivot_table(index='draw', columns=['agg','norm','mont'], values='nd_Q2Ap')

N_BOOT_IC = 10000
rng_ic = np.random.default_rng(42)

pairs = [
    ('SAW/min-max',   ('saw','minmax','optimal'),  ('saw','minmax','greedy')),
    ('SAW/vector',    ('saw','vector','optimal'),   ('saw','vector','greedy')),
    ('TOPSIS/min-max',('topsis','minmax','optimal'),('topsis','minmax','greedy')),
    ('TOPSIS/vector', ('topsis','vector','optimal'),('topsis','vector','greedy')),
]

print(f"{'Pair':<20} {'Opt Q2':>8} {'Grd Q2':>8} {'Diff':>8} {'95% CI':>22} {'p':>8}")
print("-"*75)
for label, opt_key, grd_key in pairs:
    opt_col = pivot[opt_key[0]][opt_key[1]][opt_key[2]].values.astype(float)
    grd_col = pivot[grd_key[0]][grd_key[1]][grd_key[2]].values.astype(float)
    diff_draws = opt_col - grd_col   # per-draw difference
    mean_diff = diff_draws.mean() * 100
    opt_q2 = opt_col.mean() * 100
    grd_q2 = grd_col.mean() * 100

    # Bootstrap
    boot_m = np.zeros(N_BOOT_IC)
    for b in range(N_BOOT_IC):
        idx = rng_ic.integers(0, len(diff_draws), size=len(diff_draws))
        boot_m[b] = diff_draws[idx].mean() * 100
    ci_l, ci_h = np.percentile(boot_m, [2.5, 97.5])
    p_val = 2 * min(np.mean(boot_m >= 0), np.mean(boot_m <= 0))
    print(f"  {label:<20} {opt_q2:>8.2f}% {grd_q2:>8.2f}% {mean_diff:>+8.2f}pp [{ci_l:+.2f},{ci_h:+.2f}]pp {p_val:>8.4f}")

print()
print("Negative diff = optimal WORSE than greedy.")
print("CI entirely below 0 => optimal significantly worse.")
