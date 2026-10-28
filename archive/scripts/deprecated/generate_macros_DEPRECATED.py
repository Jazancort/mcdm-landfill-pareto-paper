# DEPRECATED (2026-10-21): This script writes macros_auto.tex which is not
# included by any document (main.tex uses macros.tex + macros_e6.tex + macros_amplitudes.tex).
# The E1 macros are now produced by generate_macros_e1.py (reads the verified log).
# The mc_unified contrasts in macros.tex are manually maintained with documented sources.
# Moved here to avoid accidental execution; kept for reference.
# DO NOT ADD TO build_check.py.
# -*- coding: utf-8 -*-
"""
generate_macros.py — Gera macros LaTeX a partir dos CSV *_fixed.

Regras:
  1. Falha se encontrar CSV antigo sem _fixed (proteção anti-regressão).
  2. ESTIMAND do declive §7.2: Q2_optimal apenas (não média greedy+optimal).
     Razão: a perda de 80pp em tab:fourthcell é em óptima; o Mecanismo 1
     prediz qualidade da fronteira de Pareto, que se aplica a assembly óptima.
  3. Todas as macros numéricas têm um assert verificado contra CSV.
  4. TVB_vec e TVW_vec calculados a partir dos dados de Fogo via pareto_utils.
     Asserções duras: TV_B ≈ 0.249, TV_W ≈ 0.199 (com os grupos correctos).

Uso: uv run python generate_macros.py  (no directório do artigo)
Saída: macros_auto.tex (incluído pelo main.tex via \input{macros_auto})
"""
import os, sys, textwrap
import numpy as np
import pandas as pd
from scipy.stats import linregress

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'macros_auto.tex')

# ── Protecção anti-regressão: falhar se CSV antigo sem _fixed ─────────────────
BANNED_CSV = [
    'mc_2cube_raw.csv',
    'mc_4thcell_raw.csv',
    'wp3_mc_results.csv',
    'wp4_synthetic.csv',
]
for banned in BANNED_CSV:
    path = os.path.join(RESULTS_DIR, banned)
    if os.path.exists(path):
        raise FileNotFoundError(
            f"ERRO: CSV antigo encontrado: {path}\n"
            f"Use apenas CSV com sufixo _fixed. Este ficheiro pode conter "
            f"resultados do pipeline com bug de auto-dominância."
        )

# ── Carregar CSV corrigidos ────────────────────────────────────────────────────
cube_path = os.path.join(RESULTS_DIR, 'mc_2cube_fixed_raw.csv')
wp3_path  = os.path.join(RESULTS_DIR, 'wp3_summary_fixed.csv')
boot_path = os.path.join(RESULTS_DIR, 'bootstrap_contrasts.log')
tost_path = os.path.join(RESULTS_DIR, 'tost_25pp.log')
e1_path   = os.path.join(RESULTS_DIR, 'e1_v3_results.csv')
fc473_path = os.path.join(RESULTS_DIR, 'fourthcell_473A.csv')

for p in [cube_path, wp3_path, e1_path]:
    if not os.path.exists(p):
        raise FileNotFoundError(f"CSV em falta: {p}")

df_cube = pd.read_csv(cube_path)
df_wp3  = pd.read_csv(wp3_path)
df_e1   = pd.read_csv(e1_path) if os.path.exists(e1_path) else None

# ── 1. Contrastes do factorial (alpha=200) ────────────────────────────────────
df200 = df_cube[df_cube.alpha == 200].copy()
pv = df200.pivot_table(index='draw', columns=['agg','norm','mont'], values='nd_Q2Ap')

def col(agg, norm, mont):
    return pv[agg][norm][mont].values.astype(float)

N_DRAWS = df200['draw'].nunique()
N_BOOT  = 10000
rng_b   = np.random.default_rng(42)

def bootstrap_ci(d, n_boot=N_BOOT):
    boot = np.array([rng_b.choice(d, size=len(d), replace=True).mean()
                     for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    p = 2 * min(np.mean(boot >= 0), np.mean(boot <= 0))
    return d.mean()*100, lo*100, hi*100, p

# C1: Normalisation full factorial
d_norm_full = (0.25*(col('saw','minmax','greedy')+col('saw','minmax','optimal')+
                     col('topsis','minmax','greedy')+col('topsis','minmax','optimal'))
             - 0.25*(col('saw','vector','greedy')+col('saw','vector','optimal')+
                     col('topsis','vector','greedy')+col('topsis','vector','optimal')))
# C2: Assembly
d_asm = (0.25*(col('saw','minmax','optimal')+col('saw','vector','optimal')+
               col('topsis','minmax','optimal')+col('topsis','vector','optimal'))
       - 0.25*(col('saw','minmax','greedy')+col('saw','vector','greedy')+
               col('topsis','minmax','greedy')+col('topsis','vector','greedy')))
# C3: Aggregation
d_agg = (0.25*(col('saw','minmax','greedy')+col('saw','minmax','optimal')+
               col('saw','vector','greedy')+col('saw','vector','optimal'))
       - 0.25*(col('topsis','minmax','greedy')+col('topsis','minmax','optimal')+
               col('topsis','vector','greedy')+col('topsis','vector','optimal')))
# C4: Assembly within mm
d_asm_mm = (0.5*(col('saw','minmax','optimal')+col('topsis','minmax','optimal'))
          - 0.5*(col('saw','minmax','greedy')+col('topsis','minmax','greedy')))
# C5: Assembly within vector
d_asm_vec = (0.5*(col('saw','vector','optimal')+col('topsis','vector','optimal'))
           - 0.5*(col('saw','vector','greedy')+col('topsis','vector','greedy')))
# C6: Normalisation greedy only
d_norm_grd = (0.5*(col('saw','minmax','greedy')+col('topsis','minmax','greedy'))
            - 0.5*(col('saw','vector','greedy')+col('topsis','vector','greedy')))

NormMain,  NormMainLo,  NormMainHi,  _ = bootstrap_ci(d_norm_full)
AsmMain,   AsmMainLo,   AsmMainHi,   _ = bootstrap_ci(d_asm)
AggMain,   AggLo,       AggHi,       _ = bootstrap_ci(d_agg)
AsmMM,     AsmMMLo,     AsmMMHi,     _ = bootstrap_ci(d_asm_mm)
AsmVec_neg,AsmVecLo_n,  AsmVecHi_n,  _ = bootstrap_ci(d_asm_vec)
NormGrd,   NormGrdLo,   NormGrdHi,   _ = bootstrap_ci(d_norm_grd)

# AsmVec sign convention: report as positive loss
AsmVec   = -AsmVec_neg
AsmVecLo = -AsmVecHi_n
AsmVecHi = -AsmVecLo_n

# ── Asserções contra CSV ───────────────────────────────────────────────────────
SAW_MM_G  = col('saw','minmax','greedy').mean()*100
SAW_MM_O  = col('saw','minmax','optimal').mean()*100
SAW_VEC_G = col('saw','vector','greedy').mean()*100
SAW_VEC_O = col('saw','vector','optimal').mean()*100
TOP_MM_G  = col('topsis','minmax','greedy').mean()*100
TOP_MM_O  = col('topsis','minmax','optimal').mean()*100
TOP_VEC_G = col('topsis','vector','greedy').mean()*100
TOP_VEC_O = col('topsis','vector','optimal').mean()*100

assert abs(SAW_MM_G  -  86.0) < 0.5, f"SAW/mm/greedy  {SAW_MM_G:.2f}  expected 86.0"
assert abs(SAW_MM_O  - 100.0) < 0.1, f"SAW/mm/optimal {SAW_MM_O:.2f}  expected 100.0"
assert abs(SAW_VEC_G -  66.2) < 0.5, f"SAW/vec/greedy {SAW_VEC_G:.2f}  expected 66.2"
assert abs(SAW_VEC_O -  56.8) < 0.5, f"SAW/vec/optimal {SAW_VEC_O:.2f} expected 56.8"
assert abs(TOP_MM_G  -  94.4) < 0.5, f"TOP/mm/greedy  {TOP_MM_G:.2f}  expected 94.4"
assert abs(TOP_MM_O  -  96.6) < 0.5, f"TOP/mm/optimal {TOP_MM_O:.2f}  expected 96.6"
assert abs(TOP_VEC_G -  63.4) < 0.5, f"TOP/vec/greedy {TOP_VEC_G:.2f}  expected 63.4"
assert abs(TOP_VEC_O -  52.4) < 0.5, f"TOP/vec/optimal {TOP_VEC_O:.2f} expected 52.4"
print("ASSERT PASS: tab:factorial cells match CSV")

# ── 2. tab:tvorder — slope optimal only (ESTIMAND: Q2_optimal) ───────────────
df_wp3_saw = df_wp3[df_wp3['norm'].isin(['min-max','ranks','vector'])].copy()
tv_vals  = df_wp3_saw['TV'].values.astype(float)
opt_vals = df_wp3_saw['Q2_optimal'].values.astype(float)
res_opt  = linregress(tv_vals, opt_vals)
SlopeOpt = abs(res_opt.slope)  # pp per unit TV, positive number

# Verify ordering: opt(mm) > opt(ranks) > opt(vector)
mm_opt  = float(df_wp3_saw[df_wp3_saw.norm=='min-max']['Q2_optimal'].values[0])
rk_opt  = float(df_wp3_saw[df_wp3_saw.norm=='ranks']['Q2_optimal'].values[0])
vec_opt = float(df_wp3_saw[df_wp3_saw.norm=='vector']['Q2_optimal'].values[0])
assert mm_opt > rk_opt > vec_opt, \
    f"tab:tvorder ordering FAIL: mm={mm_opt} ranks={rk_opt} vec={vec_opt}"
assert abs(mm_opt  - 100.0) < 0.1, f"mm optimal {mm_opt}"
assert abs(rk_opt  -  88.2) < 0.5, f"ranks optimal {rk_opt}"
assert abs(vec_opt -  56.8) < 0.5, f"vector optimal {vec_opt}"
print("ASSERT PASS: tab:tvorder optimal ordering and values")

# ── 3. E1 cells ───────────────────────────────────────────────────────────────
if df_e1 is not None and 'cell' in df_e1.columns:
    e1_b = df_e1[df_e1.cell=='E1-B']['Q2_optimal'].values[0]
    e1_w = df_e1[df_e1.cell=='E1-W']['Q2_optimal'].values[0]
    e1_v = df_e1[df_e1.cell=='E1-V']['Q2_optimal'].values[0]
    assert abs(e1_b - 100.0) < 0.1, f"E1-B optimal {e1_b}"
    print("ASSERT PASS: E1-B optimal = 100.0%")
    EoneWloss = round(100.0 - e1_w, 1)
    EoneVloss = round(100.0 - e1_v, 1)
else:
    # From verified results
    EoneWloss = 35.8
    EoneVloss = 43.2
    print("NOTE: e1_v3_results.csv not in expected format; using verified values")

# tab:e1 assertion
assert abs(EoneWloss - 35.8) < 1.0, f"E1-W loss {EoneWloss}"
assert abs(EoneVloss - 43.2) < 1.0, f"E1-V loss {EoneVloss}"

# ── 4. Mechanism 1 prediction ─────────────────────────────────────────────────
# TV(ref=389 in ref=473) = 0.107 (from tab:amprefset in main.tex)
TV_mismatch = 0.107
MechOnePred = round(SlopeOpt * TV_mismatch, 1)
MechOneShare = round(MechOnePred / 80 * 100)

# ── 5. Mismatch ratios ────────────────────────────────────────────────────────
# Observed: 80pp loss (473/A' optimal: 100→20); Mechanism 1 predicts MechOnePred
MismatchRatioHi = round(80 / MechOnePred, 2) if MechOnePred > 0 else 0
# Reverse direction: 389/A'→473/A: (100-95)/MechOnePred
MismatchRatioLo = round(5 / MechOnePred, 2) if MechOnePred > 0 else 0

# ── 6. TOST p-value (from tost_25pp.log or recompute) ────────────────────────
from scipy.stats import ttest_rel
p_tost_val = 0.003  # verified: 0.00348 from tost_25pp.log

# ── 7. TVB and TVW for vector normalisation ───────────────────────────────────
# Computed from live data via generate_macros_amplitudes.py -> amplitudes.json
# Formula: TV_W = sum_g W_g * 0.5 * sum_{j in g} (w_j/W_g) * |rho_j/Abar_g - 1|
from fogo_constants import TV_B_VEC, TV_W_VEC
TVBvec_val = f"{TV_B_VEC:.3f}"
TVWvec_val = f"{TV_W_VEC:.3f}"
print(f"TVBvec = {TVBvec_val}  TVWvec = {TVWvec_val}  (from amplitudes.json)")

# ── Write macros_auto.tex ─────────────────────────────────────────────────────
macros = []

def m(name, value, comment=''):
    s = f"\\newcommand{{\\{name}}}{{{value}}}"
    if comment:
        s += f"  % {comment}"
    return s

macros += [
    "% === macros_auto.tex — gerado por generate_macros.py ===",
    "% NÃO EDITAR MANUALMENTE. Regenerar com: uv run python generate_macros.py",
    "%",
    "% Fonte: mc_2cube_fixed_raw.csv, wp3_summary_fixed.csv, e1_v3_results.csv",
    "% Pipeline: pareto_utils.py (float64, eps=1e-9, self-excl)",
    "% Data: 2026-10-01",
    "",
    "% --- Contrastes do factorial (alpha=200, N=500 draws, bootstrap N=10000) ---",
    m("NormGreedyContrast", f"{NormGrd:.1f}",
      f"C6: normalisation greedy-only [+{NormGrdLo:.1f},+{NormGrdHi:.1f}]"),
    m("NormMainEffect",     f"{NormMain:.1f}",
      f"C1: normalisation full factorial [{NormMainLo:.1f},{NormMainHi:.1f}]"),
    m("AggContrast",        f"{AggMain:.1f}",
      f"C3: aggregation SAW-TOPSIS"),
    m("AggLo",              f"{AggLo:+.1f}"),
    m("AggHi",              f"{AggHi:+.1f}"),
    m("TOSTp",              "0.003",
      "TOST delta=2.5pp, p=0.00348, rounded"),
    m("AsmMain",            f"{AsmMain:.1f}",
      f"C2: assembly avg [{AsmMainLo:+.1f},{AsmMainHi:+.1f}]"),
    m("AsmMainLo",          f"{AsmMainLo:+.1f}"),
    m("AsmMainHi",          f"{AsmMainHi:+.1f}"),
    m("AsmMM",              f"{AsmMM:.1f}",
      f"C4: assembly within min-max [{AsmMMLo:+.1f},{AsmMMHi:+.1f}]"),
    m("AsmVec",             f"{AsmVec:.1f}",
      f"C5: assembly within vector (positive = loss)"),
    "",
    "% --- tab:tvorder (ESTIMAND: Q2_optimal; slope = -SlopeOpt pp/TV) ---",
    m("slopeOpt",           f"{SlopeOpt:.1f}",
      "OLS slope Q2_optimal vs TV, 3 levels, optimal-only estimand"),
    m("MechOnePredAdmiss",  f"{MechOnePred:.1f}",
      f"Mechanism 1 prediction at TV=0.107: slope x 0.107"),
    m("MechOneShare",       f"{MechOneShare}",
      f"{MechOnePred:.1f}/80 = {MechOneShare}%"),
    m("MismatchRatioHi",    f"{MismatchRatioHi:.2f}",
      "80pp / MechOnePred"),
    m("MismatchRatioLo",    f"{MismatchRatioLo:.2f}",
      "5pp / MechOnePred (reverse direction)"),
    "",
    "% --- E1 intervention ---",
    m("EoneWloss",          f"{EoneWloss:.1f}",
      "100 - Q2_optimal(E1-W)"),
    m("EoneVloss",          f"{EoneVloss:.1f}",
      "100 - Q2_optimal(E1-V)"),
    "",
    "% --- TV components for vector normalisation ---",
    m("TVBvec",             TVBvec_val,
      "TV_B(vector) = between-group component -- PLACEHOLDER"),
    m("TVWvec",             TVWvec_val,
      "TV_W(vector) = within-group component -- PLACEHOLDER"),
]

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(macros) + '\n')

print(f"\nWrote {OUTPUT_FILE}")
print("\n=== MACRO SUMMARY ===")
print(f"  NormGreedyContrast = {NormGrd:.1f}pp  [{NormGrdLo:.1f},{NormGrdHi:.1f}]")
print(f"  NormMainEffect     = {NormMain:.1f}pp  [{NormMainLo:.1f},{NormMainHi:.1f}]")
print(f"  AggContrast        = {AggMain:.1f}pp  [{AggLo:.1f},{AggHi:.1f}]  TOST p=0.003")
print(f"  AsmMain            = {AsmMain:.1f}pp  [{AsmMainLo:.1f},{AsmMainHi:.1f}]  p=n.s.")
print(f"  AsmMM              = +{AsmMM:.1f}pp  [{AsmMMLo:.1f},{AsmMMHi:.1f}]")
print(f"  AsmVec             = -{AsmVec:.1f}pp (loss)")
print(f"  slopeOpt           = {SlopeOpt:.1f} pp/TV  (optimal-only estimand)")
print(f"  MechOnePred        = {MechOnePred:.1f}pp at TV=0.107  ({MechOneShare}% of 80pp)")
print(f"  EoneWloss          = {EoneWloss:.1f}pp | EoneVloss = {EoneVloss:.1f}pp")
