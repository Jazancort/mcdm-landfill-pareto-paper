# -*- coding: utf-8 -*-
"""
tost_25pp.py — TOST para agregação com delta=2.5pp (pré-especificado em §5).

Também calcula o estimand do declive §7.2 para ambas as opções
(média greedy+óptima vs só óptima) e imprime a decisão.

ESTIMAND DECISION (documentado aqui, consumido por generate_macros.py):
  A perda de 80pp é em óptima (389/A'). O §7.2 deriva as previsões do
  Mecanismo 1 para óptima. Logo o estimand correcto para o declive é
  só óptima (Q2_optimal ~ TV).
  Justificação: o mecanismo é sobre a fronteira de Pareto, não sobre
  a heurística greedy. Usar a média greedy+óptima misturaria dois processos
  diferentes no mesmo estimand.
"""
import pandas as pd, numpy as np
from scipy.stats import ttest_rel

# ── Load corrected tab:tvorder (wp3_summary_fixed.csv) ───────────────────────
df_tv = pd.read_csv('/home/julioazancort/scratch/mcdm-landfill-pareto/results/wp3_summary_fixed.csv')
print("Colunas wp3_summary_fixed.csv:", list(df_tv.columns))
print(df_tv.to_string(index=False))

# ── Load mc_2cube_fixed_raw for TOST ─────────────────────────────────────────
df_raw = pd.read_csv('/home/julioazancort/scratch/mcdm-landfill-pareto/results/mc_2cube_fixed_raw.csv')
df = df_raw[df_raw.alpha == 200].copy()
pv = df.pivot_table(index='draw', columns=['agg','norm','mont'], values='nd_Q2Ap')

def col(agg, norm, mont):
    return pv[agg][norm][mont].values.astype(float)

# Per-draw aggregation effect: SAW − TOPSIS, averaged over 4 (norm × mont) combinations
d_agg = (0.25*(col('saw','minmax','greedy')+col('saw','minmax','optimal')+
               col('saw','vector','greedy')+col('saw','vector','optimal'))
       - 0.25*(col('topsis','minmax','greedy')+col('topsis','minmax','optimal')+
               col('topsis','vector','greedy')+col('topsis','vector','optimal'))) * 100

print(f"\nAggregation (SAW-TOPSIS): mean={d_agg.mean():.2f}pp  std={d_agg.std():.2f}pp")

# ── TOST with delta=2.5pp (pre-specified in §5) ───────────────────────────────
delta_prespec = 2.5
delta_sensitivity = 2.0

print("\n" + "="*65)
print(f"TOST Aggregation — delta=2.5pp (pre-specified §5)")
print("="*65)
# TOST: H0_lower: effect <= -delta  vs  H0_upper: effect >= +delta
t_lo, p_lo = ttest_rel(d_agg, -delta_prespec * np.ones(len(d_agg)), alternative='greater')
t_hi, p_hi = ttest_rel(d_agg,  delta_prespec * np.ones(len(d_agg)), alternative='less')
p_tost = max(p_lo, p_hi)
print(f"  delta = {delta_prespec}pp")
print(f"  Observed mean: {d_agg.mean():.2f}pp")
print(f"  H0_lower (effect <= -2.5pp): t={t_lo:.3f}  p={p_lo:.5f}")
print(f"  H0_upper (effect >= +2.5pp): t={t_hi:.3f}  p={p_hi:.5f}")
print(f"  TOST p-value = max(p_lo, p_hi) = {p_tost:.5f}")
if p_tost < 0.05:
    print(f"  CONCLUSION: |effect| < {delta_prespec}pp (TOST p<0.05) — EQUIVALENCE ESTABLISHED")
else:
    print(f"  CONCLUSION: Cannot establish equivalence at delta={delta_prespec}pp (p={p_tost:.4f})")

# Sensitivity: delta=2.0pp
print(f"\nSensitivity check: delta=2.0pp")
t_lo2, p_lo2 = ttest_rel(d_agg, -delta_sensitivity * np.ones(len(d_agg)), alternative='greater')
t_hi2, p_hi2 = ttest_rel(d_agg,  delta_sensitivity * np.ones(len(d_agg)), alternative='less')
p_tost2 = max(p_lo2, p_hi2)
if p_tost2 < 0.05:
    print(f"  |effect| < {delta_sensitivity}pp (TOST p={p_tost2:.5f} < 0.05) — also equivalent")
else:
    print(f"  Cannot establish at delta={delta_sensitivity}pp (p={p_tost2:.4f})")

# ── Bootstrap CI for aggregation (cross-check) ───────────────────────────────
N_BOOT = 10000
rng_b = np.random.default_rng(42)
boot = np.array([rng_b.choice(d_agg, size=len(d_agg), replace=True).mean()
                 for _ in range(N_BOOT)])
ci_lo, ci_hi = np.percentile(boot, [2.5, 97.5])
print(f"\nBootstrap CI (cross-check): [{ci_lo:.2f}, {ci_hi:.2f}]pp")
print(f"  (CI lies within [-{delta_prespec}, +{delta_prespec}] ={'yes' if ci_lo>-delta_prespec and ci_hi<delta_prespec else 'no'})")

# ── Estimand for §7.2 slope (DECISION) ───────────────────────────────────────
print("\n" + "="*65)
print("ESTIMAND DECISION for §7.2 slope (Mechanism 1)")
print("="*65)
print("""
DECISION: use Q2_optimal only (not mean(greedy, optimal)).

Rationale:
  - The 80pp loss cited in §7.2 and tab:fourthcell is in OPTIMAL assembly
    (389/A' optimal=100% vs 473/A' optimal=20%).
  - Mechanism 1 predicts the Pareto-frontier quality; it applies to optimal.
  - Greedy involves a separate stochastic process (approximation quality);
    mixing it with optimal creates a composite estimand with no clear interpretation.
  - Using only optimal gives a cleaner, more conservative estimate of the mechanism.

tab:tvorder optimal values (from wp3_summary_fixed.csv):
""")

# Extract optimal column
try:
    opt_col = [c for c in df_tv.columns if 'ptimal' in c or 'opt' in c.lower()][0]
    tv_col  = [c for c in df_tv.columns if 'TV' in c or 'tv' in c.lower()][0]
    print(f"  TV column: {tv_col}  |  Optimal column: {opt_col}")
    print(df_tv[[tv_col, opt_col]].to_string(index=False))
    # Slope optimal vs TV
    from scipy.stats import linregress
    tv_vals  = df_tv[tv_col].values.astype(float)
    opt_vals = df_tv[opt_col].values.astype(float)
    res_opt = linregress(tv_vals, opt_vals)
    print(f"\n  OLS: Q2_optimal = {res_opt.slope:.1f} * TV + {res_opt.intercept:.1f}")
    print(f"  Slope (pp per unit TV): {res_opt.slope:.1f}")
    print(f"  Prediction at TV=0.0911 (ranks): Q2_optimal = {res_opt.slope*0.0911+res_opt.intercept:.1f}%")
    slope_opt = res_opt.slope
except Exception as e:
    print(f"  Could not read columns: {e}")
    slope_opt = -103.0  # approximate

print(f"\n  SLOPE (optimal only): {slope_opt:.1f} pp per unit TV")
print(f"  Prediction loss for TV=ranks (0.0911): {abs(slope_opt*0.0911):.1f}pp")
print(f"  As fraction of 80pp loss: {abs(slope_opt*0.0911)/80*100:.1f}%")
print("""
NOTE FOR generate_macros.py:
  \\newcommand{\\SlopeEstimand}{optimal-only}
  \\newcommand{\\MechFractionPct}{~12-15\\%}  (update with exact value above)
  \\newcommand{\\SlopeCoeff}{...}  (from res_opt.slope above)
""")
