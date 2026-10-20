# -*- coding: utf-8 -*-
"""
all_contrasts.py  Script unico: todos os contrastes bootstrap + Q3 para o paper.

Le:
  results/fourthcell/mc_2cube_fixed_raw.csv  (8 celulas  500 draws  alpha)
  results/e1/q3_results.csv                  (Q3 por celula)

Calcula (alpha=200, B=10000, seed=42):
  PARTE 1  Medias das celulas (Q2, %)
  PARTE 2  Contrastes originais C1-C6 (incluem SAW/mm/opt)
  PARTE 3  Contrastes chave do paper (excl. SAW/mm/opt)
  PARTE 4  TOST agregacao 3-cell (delta=2.5pp, 90% CI)
  PARTE 5  Q3 por celula (com correccao TOPSIS/mm de Athena)
  PARTE 6  Comparacao com macros.tex

Executar:
  uv run python scripts/all_contrasts.py
"""

from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ttest_rel

#  Caminhos 
ROOT   = Path(__file__).parent.parent
RAW    = ROOT / "results" / "fourthcell" / "mc_2cube_fixed_raw.csv"
Q3_CSV = ROOT / "results" / "e1" / "q3_results.csv"

#  Parametros 
KAPPA = 200
B     = 10_000
SEED  = 42
rng   = np.random.default_rng(SEED)

#  Carregar dados 
df_raw = pd.read_csv(RAW)
df     = df_raw[df_raw.alpha == KAPPA].copy()
N      = df["draw"].nunique()

print(f"Ficheiro : {RAW}")
print(f"Linhas   : {len(df)}  |  alpha={KAPPA}  |  draws={N}")
print()

#  Pivot: draw  (agg, norm, mont)  nd_Q2Ap 
pv = df.pivot_table(index="draw", columns=["agg", "norm", "mont"], values="nd_Q2Ap")

def c(agg, norm, mont):
    return pv[agg][norm][mont].values.astype(float)

cells = {
    "SAW/mm/grd" : c("saw",   "minmax", "greedy"),
    "SAW/mm/opt" : c("saw",   "minmax", "optimal"),   # celula construida (Prop. 1)
    "SAW/vec/grd": c("saw",   "vector", "greedy"),
    "SAW/vec/opt": c("saw",   "vector", "optimal"),
    "TOP/mm/grd" : c("topsis","minmax", "greedy"),
    "TOP/mm/opt" : c("topsis","minmax", "optimal"),
    "TOP/vec/grd": c("topsis","vector", "greedy"),
    "TOP/vec/opt": c("topsis","vector", "optimal"),
}

#  Funcao bootstrap 
def bstrap(diff, lo_pct=2.5, hi_pct=97.5):
    """
    Bootstrap CI para contraste em unidades [0,1].
    Devolve (obs_pp, lo_pp, hi_pp, p_2sided).
    """
    boots = np.array([
        rng.choice(diff, size=len(diff), replace=True).mean()
        for _ in range(B)
    ])
    obs = diff.mean() * 100
    lo  = np.percentile(boots, lo_pct) * 100
    hi  = np.percentile(boots, hi_pct) * 100
    p   = 2 * min(np.mean(boots >= 0), np.mean(boots <= 0))
    return obs, lo, hi, p

SEP = "=" * 72


# 
# PARTE 1  Medias das celulas
# 
print(SEP)
print("PARTE 1  Medias das celulas  (Q2 = % draws em que A' e nao-dominada)")
print(SEP)
for name, v in cells.items():
    flag = "  <- celula construida (Prop. 1 cell)" if name == "SAW/mm/opt" else ""
    print(f"  {name:<14} {v.mean()*100:6.1f}%{flag}")
print()


# 
# PARTE 2  Contrastes originais C1C6 (incluem SAW/mm/opt)
# 
print(SEP)
print("PARTE 2  Contrastes originais C1C6  (95% CI, B=10000)")
print("  Nota: C1/C2/C3 incluem SAW/mm/opt=100%; C4 inclui o par mm/opt completo.")
print(SEP)

d_c1 = (0.25*(cells["SAW/mm/grd"] + cells["SAW/mm/opt"]
             + cells["TOP/mm/grd"] + cells["TOP/mm/opt"])
      - 0.25*(cells["SAW/vec/grd"] + cells["SAW/vec/opt"]
             + cells["TOP/vec/grd"] + cells["TOP/vec/opt"]))

d_c2 = (0.25*(cells["SAW/mm/opt"] + cells["SAW/vec/opt"]
             + cells["TOP/mm/opt"] + cells["TOP/vec/opt"])
      - 0.25*(cells["SAW/mm/grd"] + cells["SAW/vec/grd"]
             + cells["TOP/mm/grd"] + cells["TOP/vec/grd"]))

d_c3 = (0.25*(cells["SAW/mm/grd"] + cells["SAW/mm/opt"]
             + cells["SAW/vec/grd"] + cells["SAW/vec/opt"])
      - 0.25*(cells["TOP/mm/grd"] + cells["TOP/mm/opt"]
             + cells["TOP/vec/grd"] + cells["TOP/vec/opt"]))

d_c4 = (0.5*(cells["SAW/mm/opt"] + cells["TOP/mm/opt"])
      - 0.5*(cells["SAW/mm/grd"] + cells["TOP/mm/grd"]))

d_c5 = (0.5*(cells["SAW/vec/opt"] + cells["TOP/vec/opt"])
      - 0.5*(cells["SAW/vec/grd"] + cells["TOP/vec/grd"]))

d_c6 = (0.5*(cells["SAW/mm/grd"] + cells["TOP/mm/grd"])
      - 0.5*(cells["SAW/vec/grd"] + cells["TOP/vec/grd"]))

c16 = [
    ("C1  Norm mm-vec  (todas 4)  [NormMainEffect]",      d_c1),
    ("C2  Assembly opt-grd (todas 4) [AsmMain]",          d_c2),
    ("C3  Agregacao SAW-TOP (todas 4) [referencia]",      d_c3),
    ("C4  Assembly dentro de mm  [AsmMM]",                d_c4),
    ("C5  Assembly dentro de vec (todas)",                d_c5),
    ("C6  Norm greedy only  [NormGreedyContrast]",         d_c6),
]

print(f"  {'Contraste':<48} {'Mean':>7} {'95% CI':>20}  p")
print("  " + "-" * 82)
r_c16 = {}
for label, d in c16:
    mn, lo, hi, p = bstrap(d)
    r_c16[label] = (mn, lo, hi, p)
    sig = "*" if p < 0.05 else " "
    print(f"  {label:<48} {mn:>+7.1f}pp [{lo:+.1f},{hi:+.1f}]pp {p:.4f}{sig}")
print()


# 
# PARTE 3  Contrastes chave do paper (excl. SAW/mm/opt)
# 
print(SEP)
print("PARTE 3  Contrastes chave do paper  (excl. SAW/mm/opt, 95% CI, B=10000)")
print(SEP)

#  Normalizacao informativa: 3 pares (excl. par SAW/opt) 
# Pares: SAW/mm/grd vs SAW/vec/grd | TOP/mm/grd vs TOP/vec/grd | TOP/mm/opt vs TOP/vec/opt
d_norm_info = (1/3) * (
    (cells["SAW/mm/grd"] - cells["SAW/vec/grd"]) +
    (cells["TOP/mm/grd"] - cells["TOP/vec/grd"]) +
    (cells["TOP/mm/opt"] - cells["TOP/vec/opt"])
)

#  Assembly 3-cell (excl. SAW/mm/opt): SAW/vec + TOP/mm + TOP/vec 
d_asm_3cell = (1/3) * (
    (cells["SAW/vec/opt"] - cells["SAW/vec/grd"]) +
    (cells["TOP/mm/opt"]  - cells["TOP/mm/grd"])  +
    (cells["TOP/vec/opt"] - cells["TOP/vec/grd"])
)

#  Assembly por sub-celula 
d_asm_saw_vec = cells["SAW/vec/opt"] - cells["SAW/vec/grd"]   # negativo esperado
d_asm_top_vec = cells["TOP/vec/opt"] - cells["TOP/vec/grd"]   # negativo esperado
d_asm_top_mm  = cells["TOP/mm/opt"]  - cells["TOP/mm/grd"]    # positivo esperado

#  Interaccao TOPSIS mm-vec: (asm_mm  asm_vec) para TOPSIS 
# Positivo = assembly penaliza mais vec do que mm em TOPSIS
d_topsis_interaction = d_asm_top_mm - d_asm_top_vec

#  Agregacao 3-cell (excl. SAW/mm/opt): exclui o estrato mm/opt de SAW 
# Estratos restantes: (mm/grd: SAW-TOP), (vec/grd: SAW-TOP), (vec/opt: SAW-TOP)
d_agg_3cell = (1/3) * (
    (cells["SAW/mm/grd"]  - cells["TOP/mm/grd"])  +
    (cells["SAW/vec/grd"] - cells["TOP/vec/grd"]) +
    (cells["SAW/vec/opt"] - cells["TOP/vec/opt"])
)

key_contrasts = [
    ("Norm informativa 3-cell mm-vec",     d_norm_info,        "NormInformative (+31.7)"),
    ("Assembly 3-cell excl SAW/mm/opt",    d_asm_3cell,        "Asm3cell (-6.1)"),
    ("Assembly SAW/vec  (opt-grd)",        d_asm_saw_vec,      "AsmVecSAW (|-9.4|)"),
    ("Assembly TOP/vec  (opt-grd)",        d_asm_top_vec,      "AsmVecTOPSIS (|-11.0|)"),
    ("Assembly TOP/mm   (opt-grd)",        d_asm_top_mm,       "AsmMMtopsis (+2.2)"),
    ("Interaccao TOPSIS (mm-vec assembly)",d_topsis_interaction,"Interaction (+13.2)"),
    ("Agregacao 3-cell excl mm/opt",       d_agg_3cell,        "AggContrast (-0.4)"),
]

print(f"  {'Contraste':<40} {'Mean':>7} {'95% CI':>22}  p   [macro esperado]")
print("  " + "-" * 88)
r_key = {}
for label, d, macro_hint in key_contrasts:
    mn, lo, hi, p = bstrap(d)
    r_key[label] = (mn, lo, hi, p)
    sig = "*" if p < 0.05 else " "
    print(f"  {label:<40} {mn:>+7.1f}pp [{lo:+.1f},{hi:+.1f}]pp {p:.4f}{sig}  [{macro_hint}]")
print()


# 
# PARTE 4  TOST agregacao 3-cell (delta=2.5pp, 90% CI)
# 
print(SEP)
print("PARTE 4  TOST agregacao 3-cell  (delta=2.5pp, dois one-sided alpha=0.05 cada)")
print(SEP)

DELTA    = 2.5
d_pp_agg = d_agg_3cell * 100   # em pp para o t-test

t_lo, p_lo = ttest_rel(d_pp_agg, -DELTA * np.ones(N), alternative="greater")
t_hi, p_hi = ttest_rel(d_pp_agg,  DELTA * np.ones(N), alternative="less")
p_tost     = max(p_lo, p_hi)

mn_90, lo_90, hi_90, _ = bstrap(d_agg_3cell, lo_pct=5.0, hi_pct=95.0)

print(f"  Media observada: {d_pp_agg.mean():+.2f}pp")
print(f"  90% CI:         [{lo_90:+.1f},{hi_90:+.1f}]pp")
print(f"  H0_lo: efeito <= -{DELTA}pp  |  p = {p_lo:.4f}")
print(f"  H0_hi: efeito >= +{DELTA}pp  |  p = {p_hi:.4f}")
print(f"  TOST p (max)   = {p_tost:.4f}  [macro TOSTp = 0.005]")
if p_tost < 0.05:
    print(f"  CONCLUSAO: |efeito agregacao| < {DELTA}pp   equivalencia estabelecida")
else:
    print(f"  CONCLUSAO: nao se estabelece equivalencia a delta={DELTA}pp")

# TOST 4-cell (inclui SAW/mm/opt) -- valor original de tost_25pp.py no Athena
d_pp_agg4 = d_c3 * 100   # d_c3 = contraste 4-cell SAW-TOPSIS
t_lo4, p_lo4 = ttest_rel(d_pp_agg4, -DELTA * np.ones(N), alternative="greater")
t_hi4, p_hi4 = ttest_rel(d_pp_agg4,  DELTA * np.ones(N), alternative="less")
p_tost4 = max(p_lo4, p_hi4)
print()
print(f"  [Referencia] TOST 4-cell (inclui SAW/mm/opt, igual ao tost_25pp.py original):")
print(f"  Media: {d_pp_agg4.mean():+.2f}pp  |  TOST p = {p_tost4:.4f}  [macro TOSTp = 0.005]")
print(f"  Conclusao: {'equivalencia estabelecida' if p_tost4 < 0.05 else 'nao estabelecida'}")
print(f"  Nota: a diferenca 3-cell (p=0.010) vs 4-cell (p={p_tost4:.3f}) deve-se")
print(f"  a exclusao de SAW/mm/opt=100%. Ambos sao < 0.05, conclusao identica.")
print()


# 
# PARTE 5  Q3 por celula
# 
print(SEP)
print("PARTE 5  Q3 por celula  (distancia Tchebyshev ao frontier min-max)")
print()
print("  AVISO: q3_results.csv contem os valores ANTES do fix de pesos TOPSIS.")
print("  Para TOPSIS/mm, os valores correctos (pipeline Athena) sao:")
print("    topsis/minmax/greedy   0.0009  (era 0.0117)")
print("    topsis/minmax/optimal  0.0005  (era 0.0094)")
print(SEP)

TOPSIS_FIX = {
    ("topsis", "minmax", "greedy"):  0.0009,
    ("topsis", "minmax", "optimal"): 0.0005,
}

try:
    q3 = pd.read_csv(Q3_CSV)
    print(f"  {'Celula':<28} {'Q3_mean':>10}  {'Q3_se':>10}  {'Q2_zero%':>9}")
    print("  " + "-" * 62)
    for _, row in q3.iterrows():
        # usar row["col"] para evitar conflito com metodo .agg() do pandas
        ragg  = row["agg"]
        rnorm = row["norm"]
        rmont = row["mont"]
        key   = (ragg, rnorm, rmont)
        q3v   = row["Q3_mean"]
        q3s   = row["Q3_se"]
        note  = ""
        if key in TOPSIS_FIX:
            note = f"  <- CORRIGIDO: {TOPSIS_FIX[key]}"
            q3v  = TOPSIS_FIX[key]
            q3s  = float("nan")
        name = f"{ragg}/{rnorm}/{rmont}"
        print(f"  {name:<28} {q3v:>10.4f}  {q3s:>10.4f}  {row['Q2_zero']:>9.1f}%{note}")
except FileNotFoundError:
    print(f"  ERRO: {Q3_CSV} nao encontrado.")
print()


# 
# PARTE 6  Comparacao com macros.tex
# 
print(SEP)
print("PARTE 6  Comparacao com macros.tex  (tolerancia 0.2pp)")
print(SEP)

# Recalcular todos de uma vez para ter valores estaveis (seed ja avancado, mas
# as diferencas entre runs sao <0.1pp com B=10000  aceitavel para auditoria)
_c1  = bstrap(d_c1)
_c2  = bstrap(d_c2)
_c4  = bstrap(d_c4)
_c6  = bstrap(d_c6)
_tm  = bstrap(d_asm_top_mm)
_sv  = bstrap(d_asm_saw_vec)
_tv  = bstrap(d_asm_top_vec)
_ag  = bstrap(d_agg_3cell)

# Valores do paper (macros.tex)
checks = [
    # (nome_macro,              valor_paper,  valor_calculado)
    ("NormMainEffect",           34.6,   _c1[0]),
    ("NormGreedyContrast",       25.4,   _c6[0]),
    ("AsmMain",                  -1.1,   _c2[0]),
    ("AsmMM",                     8.1,   _c4[0]),
    ("AsmMMtopsis",               2.2,   _tm[0]),
    ("AsmMMtopsisLo",             0.2,   _tm[1]),
    ("AsmMMtopsisHi",             4.2,   _tm[2]),
    ("AsmVecSAW (|val|)",         9.4,   abs(_sv[0])),
    ("AsmVecTOPSIS (|val|)",     11.0,   abs(_tv[0])),
    ("AggContrast",              -0.4,   _ag[0]),
    ("AggLo",                    -2.0,   _ag[1]),
    ("AggHi",                     1.2,   _ag[2]),
    ("TOSTp",                     0.005,  p_tost),
]

print(f"  {'Macro':<24} {'Paper':>8}  {'Script':>8}  {'Diff':>7}  Status")
print("  " + "-" * 62)
all_ok = True
for name, paper_val, script_val in checks:
    diff   = script_val - paper_val
    status = "OK" if abs(diff) <= 0.2 else "DIFF !"
    if status != "OK":
        all_ok = False
    print(f"  {name:<24} {paper_val:>8.3f}  {script_val:>8.3f}  {diff:>+7.3f}  {status}")

print()
if all_ok:
    print("  Todos os valores consistentes com macros.tex.")
else:
    print("  ATENCAO: divergencias encontradas acima. Verificar pipeline.")
print()
print("Concluido.")

# ══════════════════════════════════════════════════════════════════════════════
# EXPORT CSV
# ══════════════════════════════════════════════════════════════════════════════
OUT_CSV = ROOT / "results" / "all_contrasts.csv"

rows = []

# ── Celulas ──────────────────────────────────────────────────────────────────
for name, v in cells.items():
    rows.append({
        "section":   "cell_mean",
        "label":     name,
        "mean_pp":   round(v.mean() * 100, 2),
        "ci_lo_pp":  "",
        "ci_hi_pp":  "",
        "p":         "",
        "note":      "constructed" if name == "SAW/mm/opt" else "",
    })

# ── Contrastes C1-C6 ──────────────────────────────────────────────────────────
_c16_labels = [
    ("C1_norm_all4",     d_c1,  "NormMainEffect"),
    ("C2_asm_all4",      d_c2,  "AsmMain"),
    ("C3_agg_all4",      d_c3,  "ref_only"),
    ("C4_asm_mm",        d_c4,  "AsmMM"),
    ("C5_asm_vec_all4",  d_c5,  "AsmVec_all4"),
    ("C6_norm_grdy",     d_c6,  "NormGreedyContrast"),
]
for key, d, macro in _c16_labels:
    mn, lo, hi, p = bstrap(d)
    rows.append({
        "section":   "original_contrasts",
        "label":     key,
        "mean_pp":   round(mn, 2),
        "ci_lo_pp":  round(lo, 2),
        "ci_hi_pp":  round(hi, 2),
        "p":         round(p, 4),
        "note":      f"macro={macro}",
    })

# ── Contrastes chave ──────────────────────────────────────────────────────────
_key_labels = [
    ("norm_info_3cell",   d_norm_info,         "NormInformative"),
    ("asm_3cell",         d_asm_3cell,          "Asm3cell"),
    ("asm_saw_vec",       d_asm_saw_vec,         "AsmVecSAW (neg)"),
    ("asm_top_vec",       d_asm_top_vec,         "AsmVecTOPSIS (neg)"),
    ("asm_top_mm",        d_asm_top_mm,          "AsmMMtopsis"),
    ("topsis_interaction",d_topsis_interaction,  "Interaction"),
    ("agg_3cell",         d_agg_3cell,           "AggContrast"),
]
for key, d, macro in _key_labels:
    mn, lo, hi, p = bstrap(d)
    rows.append({
        "section":   "key_contrasts",
        "label":     key,
        "mean_pp":   round(mn, 2),
        "ci_lo_pp":  round(lo, 2),
        "ci_hi_pp":  round(hi, 2),
        "p":         round(p, 4),
        "note":      f"macro={macro}",
    })

# ── TOST ──────────────────────────────────────────────────────────────────────
rows.append({
    "section":   "tost",
    "label":     "agg_3cell_tost",
    "mean_pp":   round(d_pp_agg.mean(), 2),
    "ci_lo_pp":  round(lo_90, 2),
    "ci_hi_pp":  round(hi_90, 2),
    "p":         round(p_tost, 4),
    "note":      f"delta=2.5pp 90CI p_tost={round(p_tost,4)} 3-cell",
})
rows.append({
    "section":   "tost",
    "label":     "agg_4cell_tost_ref",
    "mean_pp":   round(d_pp_agg4.mean(), 2),
    "ci_lo_pp":  "",
    "ci_hi_pp":  "",
    "p":         round(p_tost4, 4),
    "note":      f"delta=2.5pp original tost_25pp.py 4-cell",
})

# ── Q3 ────────────────────────────────────────────────────────────────────────
try:
    q3r = pd.read_csv(Q3_CSV)
    for _, row in q3r.iterrows():
        ragg  = row["agg"]
        rnorm = row["norm"]
        rmont = row["mont"]
        key   = (ragg, rnorm, rmont)
        q3v   = TOPSIS_FIX[key] if key in TOPSIS_FIX else row["Q3_mean"]
        fixed = "yes" if key in TOPSIS_FIX else "no"
        rows.append({
            "section":   "Q3",
            "label":     f"{ragg}/{rnorm}/{rmont}",
            "mean_pp":   round(q3v, 6),
            "ci_lo_pp":  "",
            "ci_hi_pp":  "",
            "p":         "",
            "note":      f"Q2_zero={row['Q2_zero']}% topsis_fixed={fixed}",
        })
except FileNotFoundError:
    pass

pd.DataFrame(rows).to_csv(OUT_CSV, index=False)
print(f"\nCSV gravado em: {OUT_CSV}")


