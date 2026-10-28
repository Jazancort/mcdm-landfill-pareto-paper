# -*- coding: utf-8 -*-
"""
mc_unified.py  --  Corrida unica: factorial + portfolios + gap + bootstrap + macros.

Substitui mc_2cube_fixed.py + q3_perdraw.py + bootstrap_contrasts.py +
aggregation_strata.py numa unica corrida com semente fixa.

Saidas (results/unified/):
  mc_unified_raw.csv        -- 8000 linhas: 2 alphas x 500 draws x 8 celulas
  mc_unified_contrasts.csv  -- bootstrap CIs por contraste
  mc_unified_q3.csv         -- Q3 e gap condicional por celula
  mc_unified_macros.tex     -- macros prontos para copiar para macros.tex

Colulas de mc_unified_raw.csv:
  alpha, draw, agg, norm, mont,
  i0, i1, i2,         -- indices do trio em df_via (0..388)
  ft1, ft2, ft3,       -- objectivos do trio seleccionado
  nd_Q2Ap,             -- 1 se nao dominado
  gap                  -- distancia Tchebyshev ao frontier

Assercoes activas:
  q2==1 => gap==0   (para toda a celula e sorteio)
  frac_gap0 >= Q2   (por celula, no final)

Executar:
  uv run python scripts/mc_unified.py
"""

import os, sys, time, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ttest_rel

ROOT = Path(__file__).parent.parent
OUT  = ROOT / "results" / "unified"
OUT.mkdir(parents=True, exist_ok=True)

# ── Setup de dados (identico ao mc_2cube_fixed.py) ────────────────────────────
if "MCDM_DATA_DIR" not in os.environ:
    _athena  = "/home/julioazancort/scratch/mcdm"
    _windows = (
        "G:\\Faculdade\\Estudo\\Doutorado\\2025.1\\"
        "Otimiza\u00e7\u00e3o Bioinspirada\\"
        "Tentativa de dados via GIS"
    )
    os.environ["MCDM_DATA_DIR"] = _athena if os.path.exists(_athena) else _windows

sys.path.insert(0, str(ROOT / "scripts"))
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS,
    haversine_km, MIN_DIST_KM, _build_decision_matrix,
    greedy_trio,
)
from pareto_utils import build_pareto_utils
from scoring import make_scorers

E1_SHA  = "bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487"
KAPPA   = 200
N_DRAWS = 500
SEED    = 42
EPS     = 1e-9
B_BOOT  = 10_000

df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]] > 0].copy()
N = len(df_via)
assert N == 389

w_ahp     = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())

D     = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
valid = D >= MIN_DIST_KM
trios = np.array(
    [(i, j, k)
     for i in range(N) for j in range(i+1, N) if valid[i, j]
     for k in range(j+1, N) if valid[i, k] and valid[j, k]],
    dtype=np.int32,
)
T0, T1, T2 = trios[:, 0], trios[:, 1], trios[:, 2]
print(f"Sites: {N}  Trios: {len(trios):,}")

compute_objs, is_dominated, _ = build_pareto_utils(df_via, col_names, trios, eps=EPS)
X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b: X_adj[:, j] = 1.0 - X_via[:, j]
norms_via = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)
saw_sc, topsis_sc = make_scorers(X_via, X_adj, norms_via, benefit)

def argmax_trio(sc):
    st  = sc[T0] + sc[T1] + sc[T2]
    idx = int(st.argmax())
    return trios[idx]

wmat = ROOT / "results" / "e1" / "e1_weights_k200.npy"
sha  = hashlib.sha256(wmat.read_bytes()).hexdigest()
assert sha == E1_SHA, f"SHA mismatch: {sha[:16]}..."
W = np.load(wmat)
print(f"Pesos: shape={W.shape}  SHA OK")

CELLS_8 = [
    ("saw",   "minmax","greedy"), ("saw",   "minmax","optimal"),
    ("saw",   "vector","greedy"), ("saw",   "vector","optimal"),
    ("topsis","minmax","greedy"), ("topsis","minmax","optimal"),
    ("topsis","vector","greedy"), ("topsis","vector","optimal"),
]

# ── Corrida principal ─────────────────────────────────────────────────────────
records = []
rng_boot = np.random.default_rng(SEED)   # semente global para bootstrap
t0 = time.time()

for d in range(N_DRAWS):
    w = W[d]
    f1v, f2v, f3v = compute_objs(w)
    F1 = f1v[T0] + f1v[T1] + f1v[T2]
    F2 = f2v[T0] + f2v[T1] + f2v[T2]
    F3 = f3v[T0] + f3v[T1] + f3v[T2]
    R1 = F1.max() - F1.min()
    R2 = F2.max() - F2.min()
    R3 = F3.max() - F3.min()

    for agg, norm, mont in CELLS_8:
        sc   = saw_sc(w, norm) if agg == "saw" else topsis_sc(w, norm)
        trio = greedy_trio(sc, D) if mont == "greedy" else argmax_trio(sc)
        i0, i1, i2 = int(trio[0]), int(trio[1]), int(trio[2])

        ft1 = f1v[i0] + f1v[i1] + f1v[i2]
        ft2 = f2v[i0] + f2v[i1] + f2v[i2]
        ft3 = f3v[i0] + f3v[i1] + f3v[i2]

        d1  = (ft1 - F1) / R1
        d2  = (ft2 - F2) / R2
        d3  = (F3  - ft3) / R3
        gap = float(max(0.0, np.minimum(np.minimum(d1, d2), d3).max()))

        q2 = int(not is_dominated(trio, F1, F2, F3))

        # Assert: eficiente => gap = 0
        if q2 == 1 and gap > EPS:
            raise AssertionError(
                f"draw={d} {agg}/{norm}/{mont}: q2=1 mas gap={gap:.8f}  trio=({i0},{i1},{i2})"
            )

        records.append({
            "draw": d, "agg": agg, "norm": norm, "mont": mont,
            "i0": i0, "i1": i1, "i2": i2,
            "ft1": round(ft1, 8), "ft2": round(ft2, 8), "ft3": round(ft3, 8),
            "nd_Q2Ap": q2, "gap": round(gap, 10),
        })

    if d % 50 == 0:
        elapsed = time.time() - t0
        eta = elapsed / max(d, 1) * (N_DRAWS - d)
        print(f"  draw {d:3d}/{N_DRAWS}  {elapsed:5.0f}s  ETA {eta:4.0f}s", flush=True)

df = pd.DataFrame(records)
df.to_csv(OUT / "mc_unified_raw.csv", index=False)
print(f"\nCSV: {OUT/'mc_unified_raw.csv'}  ({len(df)} linhas)  {time.time()-t0:.1f}s")

# Assert frac_gap0 >= Q2 em todas as celulas
for (agg, norm, mont), g in df.groupby(["agg","norm","mont"]):
    q2pct  = g["nd_Q2Ap"].mean() * 100
    fg0pct = (g["gap"] < EPS).mean() * 100
    if fg0pct < q2pct - 1e-6:
        raise AssertionError(f"{agg}/{norm}/{mont}: frac_gap0={fg0pct:.1f}% < Q2={q2pct:.1f}%")
print("Assercao frac_gap0>=Q2: PASSOU em todas as 8 celulas.")

# ── Bootstrap ─────────────────────────────────────────────────────────────────
def bstrap(diff, lo_pct=2.5, hi_pct=97.5):
    """Bootstrap CI. diff in [0,1]. Devolve (obs_pp, lo_pp, hi_pp, p)."""
    boots = np.array([
        rng_boot.choice(diff, size=len(diff), replace=True).mean()
        for _ in range(B_BOOT)
    ])
    obs = diff.mean() * 100
    lo  = np.percentile(boots, lo_pct) * 100
    hi  = np.percentile(boots, hi_pct) * 100
    p   = 2 * min(np.mean(boots >= 0), np.mean(boots <= 0))
    return obs, lo, hi, p

def c(agg, norm, mont):
    return df[(df.agg==agg)&(df.norm==norm)&(df.mont==mont)]["nd_Q2Ap"].values.astype(float)

cells = {k: c(*k) for k in CELLS_8}

# Contrastes principais
d_c1       = 0.25*(cells[("saw","minmax","greedy")]+cells[("saw","minmax","optimal")]
                  +cells[("topsis","minmax","greedy")]+cells[("topsis","minmax","optimal")]) \
           - 0.25*(cells[("saw","vector","greedy")]+cells[("saw","vector","optimal")]
                  +cells[("topsis","vector","greedy")]+cells[("topsis","vector","optimal")])
d_c6       = 0.5*(cells[("saw","minmax","greedy")]+cells[("topsis","minmax","greedy")]) \
           - 0.5*(cells[("saw","vector","greedy")]+cells[("topsis","vector","greedy")])
d_c2       = 0.25*(cells[("saw","minmax","optimal")]+cells[("saw","vector","optimal")]
                  +cells[("topsis","minmax","optimal")]+cells[("topsis","vector","optimal")]) \
           - 0.25*(cells[("saw","minmax","greedy")]+cells[("saw","vector","greedy")]
                  +cells[("topsis","minmax","greedy")]+cells[("topsis","vector","greedy")])
d_c4       = 0.5*(cells[("saw","minmax","optimal")]+cells[("topsis","minmax","optimal")]) \
           - 0.5*(cells[("saw","minmax","greedy")]+cells[("topsis","minmax","greedy")])

# Contrastes chave (excl. SAW/mm/opt)
d_norm_info = (1/3) * (
    (cells[("saw","minmax","greedy")]    - cells[("saw","vector","greedy")]) +
    (cells[("topsis","minmax","greedy")] - cells[("topsis","vector","greedy")]) +
    (cells[("topsis","minmax","optimal")]- cells[("topsis","vector","optimal")])
)
d_asm_3cell = (1/3) * (
    (cells[("saw","vector","optimal")]    - cells[("saw","vector","greedy")]) +
    (cells[("topsis","minmax","optimal")] - cells[("topsis","minmax","greedy")]) +
    (cells[("topsis","vector","optimal")] - cells[("topsis","vector","greedy")])
)
d_asm_sv = cells[("saw","vector","optimal")]    - cells[("saw","vector","greedy")]
d_asm_tv = cells[("topsis","vector","optimal")] - cells[("topsis","vector","greedy")]
d_asm_tm = cells[("topsis","minmax","optimal")] - cells[("topsis","minmax","greedy")]
d_topsis_ix = d_asm_tm - d_asm_tv

# Agregacao 3-cell (excl. mm/opt = SAW/mm/opt)
d_agg_3cell = (1/3) * (
    (cells[("saw","minmax","greedy")]  - cells[("topsis","minmax","greedy")]) +
    (cells[("saw","vector","greedy")]  - cells[("topsis","vector","greedy")]) +
    (cells[("saw","vector","optimal")] - cells[("topsis","vector","optimal")])
)

# Agregacao por estrato
agg_strata = {}
for (norm, mont), g in df.groupby(["norm","mont"]):
    key = (norm, mont)
    saw_v = g.loc[g["agg"]=="saw",    "nd_Q2Ap"].values.astype(float)
    top_v = g.loc[g["agg"]=="topsis", "nd_Q2Ap"].values.astype(float)
    mn, lo, hi, p = bstrap(saw_v - top_v)
    agg_strata[key] = (mn, lo, hi, p)

# Bootstrap de todos os contrastes
contrasts_def = [
    ("C1_norm_all4",         d_c1),
    ("C6_norm_greedy",       d_c6),
    ("C2_asm_all4",          d_c2),
    ("C4_asm_mm",            d_c4),
    ("norm_info_3cell",      d_norm_info),
    ("asm_3cell",            d_asm_3cell),
    ("asm_saw_vec",          d_asm_sv),
    ("asm_top_vec",          d_asm_tv),
    ("asm_top_mm",           d_asm_tm),
    ("topsis_interaction",   d_topsis_ix),
    ("agg_3cell",            d_agg_3cell),
]
contrast_rows = []
for name, d_vec in contrasts_def:
    mn, lo, hi, p = bstrap(d_vec)
    contrast_rows.append({"contrast": name, "mean_pp": round(mn,2),
                          "ci_lo": round(lo,2), "ci_hi": round(hi,2), "p": round(p,4)})
    print(f"  {name:<25} {mn:+6.1f}pp [{lo:+.1f},{hi:+.1f}] p={p:.4f}")

df_contrasts = pd.DataFrame(contrast_rows)
df_contrasts.to_csv(OUT / "mc_unified_contrasts.csv", index=False)

# TOST agregacao 3-cell (delta=2.5pp, 90% CI, dois one-sided alpha=0.05)
DELTA = 2.5
d_pp  = d_agg_3cell * 100
_, p_lo = ttest_rel(d_pp, -DELTA * np.ones(N_DRAWS), alternative="greater")
_, p_hi = ttest_rel(d_pp,  DELTA * np.ones(N_DRAWS), alternative="less")
p_tost  = max(p_lo, p_hi)
_, lo_90, hi_90, _ = bstrap(d_agg_3cell, lo_pct=5.0, hi_pct=95.0)
print(f"\nTOST 3-cell: mean={d_pp.mean():+.2f}pp  90%CI=[{lo_90:+.1f},{hi_90:+.1f}]  p={p_tost:.4f}")

# Q3 por celula
q3_rows = []
for (agg, norm, mont), g in df.groupby(["agg","norm","mont"]):
    q2pct = g["nd_Q2Ap"].mean() * 100
    q3    = g["gap"].mean()
    q3se  = g["gap"].std() / len(g)**0.5
    fg0   = (g["gap"] < EPS).mean() * 100
    fm    = 1 - g["nd_Q2Ap"].mean()
    cg    = q3 / fm * 100 if fm > 0 else float("nan")
    q3_rows.append({"agg":agg,"norm":norm,"mont":mont,
                    "Q2_pct":round(q2pct,1),
                    "Q3_mean":round(q3,6),"Q3_se":round(q3se,6),
                    "frac_gap0":round(fg0,1),"cond_gap_pct":round(cg,4)})
df_q3 = pd.DataFrame(q3_rows)
df_q3.to_csv(OUT / "mc_unified_q3.csv", index=False)

# ── Gerar macros ──────────────────────────────────────────────────────────────
cr = {r["contrast"]: r for r in contrast_rows}
ag = {k: v for k, v in agg_strata.items()}

def m(name, val, note=""):
    if isinstance(val, float) and abs(val) < 0.005:
        s = f"{val:.4f}"
    elif isinstance(val, float):
        s = f"{val:.1f}" if abs(val) > 0.5 else f"{val:.4f}"
    else:
        s = str(val)
    comment = f"  % {note}" if note else ""
    return f"\\newcommand{{\\{name}}}{{{s}}}{comment}\n"

q3d = {(r["agg"],r["norm"],r["mont"]): r for r in q3_rows}
def q3v(agg,norm,mont): return q3d[(agg,norm,mont)]

macros_out = [
    "% AUTO-GENERATED by mc_unified.py — DO NOT EDIT BY HAND\n",
    f"% Seed={SEED}  N={N_DRAWS}  B={B_BOOT}  KAPPA={KAPPA}\n\n",
    "% ── Contrastes principais ──────────────────────────────────────────────\n",
    m("NormMainEffect",     cr["C1_norm_all4"]["mean_pp"],  "C1 all4"),
    m("NormGreedyContrast", cr["C6_norm_greedy"]["mean_pp"],"C6 greedy-only"),
    m("AsmMain",            cr["C2_asm_all4"]["mean_pp"],   "C2 all4"),
    m("AsmMM",              cr["C4_asm_mm"]["mean_pp"],     "C4 within mm"),
    "\n% ── Agregacao 3-cell ───────────────────────────────────────────────────\n",
    m("AggContrast",   round(cr["agg_3cell"]["mean_pp"],1), "SAW-TOP excl mm/opt"),
    m("AggLo",         round(cr["agg_3cell"]["ci_lo"],1),   "95% CI lo"),
    m("AggHi",         round(cr["agg_3cell"]["ci_hi"],1),   "95% CI hi"),
    m("TOSTp",         round(p_tost,3),                     "TOST p delta=2.5pp"),
    "\n% ── Assembly ────────────────────────────────────────────────────────────\n",
    m("AsmMMtopsis",      round(cr["asm_top_mm"]["mean_pp"],1)),
    m("AsmMMtopsisLo",    round(cr["asm_top_mm"]["ci_lo"],1)),
    m("AsmMMtopsisHi",    round(cr["asm_top_mm"]["ci_hi"],1)),
    m("AsmVecSAW",        abs(round(cr["asm_saw_vec"]["mean_pp"],1))),
    m("AsmVecTOPSIS",     abs(round(cr["asm_top_vec"]["mean_pp"],1))),
    m("AsmVec",           abs(round((cr["asm_saw_vec"]["mean_pp"]+cr["asm_top_vec"]["mean_pp"])/2,1))),
    "\n% ── Norm informativa e interaccao ────────────────────────────────────────\n",
    m("NormInfoEffect",   round(cr["norm_info_3cell"]["mean_pp"],1),  "norm 3-cell"),
    m("NormInfoLo",       round(cr["norm_info_3cell"]["ci_lo"],1)),
    m("NormInfoHi",       round(cr["norm_info_3cell"]["ci_hi"],1)),
    m("AsmThreecell",     round(cr["asm_3cell"]["mean_pp"],1),        "asm 3-cell"),
    m("AsmThreecellLo",   round(cr["asm_3cell"]["ci_lo"],1)),
    m("AsmThreecellHi",   round(cr["asm_3cell"]["ci_hi"],1)),
    m("AsmVecSAWLo",      round(cr["asm_saw_vec"]["ci_lo"],1)),
    m("AsmVecSAWHi",      round(cr["asm_saw_vec"]["ci_hi"],1)),
    m("AsmVecTOPSISLo",   round(cr["asm_top_vec"]["ci_lo"],1)),
    m("AsmVecTOPSISHi",   round(cr["asm_top_vec"]["ci_hi"],1)),
    m("InteractionTOPSIS",     round(cr["topsis_interaction"]["mean_pp"],1)),
    m("InteractionTOPSISLo",   round(cr["topsis_interaction"]["ci_lo"],1)),
    m("InteractionTOPSISHi",   round(cr["topsis_interaction"]["ci_hi"],1)),
    "\n% ── Agregacao por estrato ───────────────────────────────────────────────\n",
    m("AggStratumMMgrd",  round(ag[("minmax","greedy")][0],1),  "SAW-TOP mm/grd"),
    m("AggStratumVecgrd", round(ag[("vector","greedy")][0],1),  "SAW-TOP vec/grd"),
    m("AggStratumMMopt",  round(ag[("minmax","optimal")][0],1), "SAW-TOP mm/opt"),
    m("AggStratumVecopt", round(ag[("vector","optimal")][0],1), "SAW-TOP vec/opt"),
    m("AggMMgrdCIlo",     round(ag[("minmax","greedy")][1],1)),
    m("AggMMgrdCIhi",     round(ag[("minmax","greedy")][2],1)),
    m("AggVecgrdCIlo",    round(ag[("vector","greedy")][1],1)),
    m("AggVecgrdCIhi",    round(ag[("vector","greedy")][2],1)),
    m("AggMMoptCIlo",     round(ag[("minmax","optimal")][1],1)),
    m("AggMMoptCIhi",     round(ag[("minmax","optimal")][2],1)),
    m("AggVecoptCIlo",    round(ag[("vector","optimal")][1],1)),
    m("AggVecoptCIhi",    round(ag[("vector","optimal")][2],1)),
    "\n% ── Q3 (4dp) ──────────────────────────────────────────────────────────────\n",
    m("QthreeSAWmmOpt",      round(q3v("saw","minmax","optimal")["Q3_mean"],4)),
    m("QthreeSAWmmGrd",      round(q3v("saw","minmax","greedy")["Q3_mean"],4)),
    m("QthreeSAWvecGrd",     round(q3v("saw","vector","greedy")["Q3_mean"],4)),
    m("QthreeSAWvecOpt",     round(q3v("saw","vector","optimal")["Q3_mean"],4)),
    m("QthreeTOPSISmmGrd",   round(q3v("topsis","minmax","greedy")["Q3_mean"],4)),
    m("QthreeTOPSISmmOpt",   round(q3v("topsis","minmax","optimal")["Q3_mean"],4)),
    m("QthreeTOPSISvecGrd",  round(q3v("topsis","vector","greedy")["Q3_mean"],4)),
    m("QthreeTOPSISvecOpt",  round(q3v("topsis","vector","optimal")["Q3_mean"],4)),
    "\n% ── Q3 em % do intervalo ──────────────────────────────────────────────────\n",
    m("QthreeSAWmmGrdPct",       round(q3v("saw","minmax","greedy")["Q3_mean"]*100,2)),
    m("QthreeSAWmmOptPct",       round(q3v("saw","minmax","optimal")["Q3_mean"]*100,2)),
    m("QthreeSAWvecGrdPct",      round(q3v("saw","vector","greedy")["Q3_mean"]*100,2)),
    m("QthreeSAWvecOptPct",      round(q3v("saw","vector","optimal")["Q3_mean"]*100,2)),
    m("QthreeTOPSISmmGrdPct",    round(q3v("topsis","minmax","greedy")["Q3_mean"]*100,2)),
    m("QthreeTOPSISmmOptPct",    round(q3v("topsis","minmax","optimal")["Q3_mean"]*100,2)),
    m("QthreeTOPSISvecGrdPct",   round(q3v("topsis","vector","greedy")["Q3_mean"]*100,2)),
    m("QthreeTOPSISvecOptPct",   round(q3v("topsis","vector","optimal")["Q3_mean"]*100,2)),
    "\n% ── Gap condicional em % ────────────────────────────────────────────────\n",
    m("CondGapSAWmmGrd",    round(q3v("saw","minmax","greedy")["cond_gap_pct"],2)),
    m("CondGapSAWvecGrd",   round(q3v("saw","vector","greedy")["cond_gap_pct"],2)),
    m("CondGapSAWvecOpt",   round(q3v("saw","vector","optimal")["cond_gap_pct"],2)),
    m("CondGapTOPSISmmGrd", round(q3v("topsis","minmax","greedy")["cond_gap_pct"],2)),
    m("CondGapTOPSISmmOpt", round(q3v("topsis","minmax","optimal")["cond_gap_pct"],2)),
    m("CondGapTOPSISvecGrd",round(q3v("topsis","vector","greedy")["cond_gap_pct"],2)),
    m("CondGapTOPSISvecOpt",round(q3v("topsis","vector","optimal")["cond_gap_pct"],2)),
    "\n% ── Q2 celulas ─────────────────────────────────────────────────────────\n",
    m("QtwommGreedy",   q3v("saw","minmax","greedy")["Q2_pct"]),
    m("QtwommOptimal",  q3v("saw","minmax","optimal")["Q2_pct"]),
    m("QtwovecGreedy",  q3v("saw","vector","greedy")["Q2_pct"]),
    m("QtwovecOptimal", q3v("saw","vector","optimal")["Q2_pct"]),
]

macros_path = OUT / "mc_unified_macros.tex"
macros_path.write_text("".join(macros_out), encoding="utf-8")
print(f"\nMacros: {macros_path}")
print(f"\nTempo total: {time.time()-t0:.1f}s")
print("\nCONCLUIDO.")
