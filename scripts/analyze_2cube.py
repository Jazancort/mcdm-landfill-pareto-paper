# -*- coding: utf-8 -*-
"""analyze_2cube.py — processar mc_2cube_raw.csv e mc_4thcell_raw.csv"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

# ─── 2^3 balanceado ───────────────────────────────────────────────────────────
df = pd.read_csv(os.path.join(RESULTS_DIR, "mc_2cube_raw.csv"))
df200 = df[df["alpha"] == 200]
print("=== 2^3 tabela (alpha=200) ===")
tbl = df200.groupby(["agg","norm","mont"])[["nd_Q1A","nd_Q2A","nd_Q1Ap","nd_Q2Ap"]].mean().mul(100).round(1)
print(tbl.to_string())

print("\n=== Efeitos principais (alpha=200, Q2[A']) ===")
for f in ["norm","mont","agg"]:
    m = df200.groupby(f)["nd_Q2Ap"].mean()*100
    print(f"  {f}: {dict(m.round(1))}  amplitude={m.max()-m.min():.1f}pp")

draws = df200["draw"].unique()
rng = np.random.default_rng(0)

def calc_effects(d):
    p = d.groupby(["agg","norm","mont"])["nd_Q2Ap"].mean().reset_index()
    mm  = p[p["norm"]=="minmax"]["nd_Q2Ap"].mean()
    vec = p[p["norm"]=="vector"]["nd_Q2Ap"].mean()
    opt = p[p["mont"]=="optimal"]["nd_Q2Ap"].mean()
    gre = p[p["mont"]=="greedy"]["nd_Q2Ap"].mean()
    mm_opt = p[(p["norm"]=="minmax")&(p["mont"]=="optimal")]["nd_Q2Ap"].mean()
    mm_gre = p[(p["norm"]=="minmax")&(p["mont"]=="greedy") ]["nd_Q2Ap"].mean()
    vc_opt = p[(p["norm"]=="vector")&(p["mont"]=="optimal")]["nd_Q2Ap"].mean()
    vc_gre = p[(p["norm"]=="vector")&(p["mont"]=="greedy") ]["nd_Q2Ap"].mean()
    return (mm-vec)*100, (opt-gre)*100, (mm_opt-mm_gre)*100, (vc_opt-vc_gre)*100

pe = calc_effects(df200)
boots = [calc_effects(df200[df200["draw"].isin(rng.choice(draws,size=len(draws),replace=True))])
         for _ in range(2000)]
boots = np.array(boots)
labels = ["norm mm-vec","mont opt-gre","mont DENTRO mm","mont DENTRO vec"]
print("\n=== Efeitos e IC bootstrap (alpha=200, Q2[A'], 2^3, n_boot=2000) ===")
for i,(lab,val) in enumerate(zip(labels, pe)):
    lo,hi = np.percentile(boots[:,i],[2.5,97.5])
    print(f"  {lab:22s}: {val:+6.1f}pp  [{lo:+.1f}, {hi:+.1f}]")

# ─── Quarta casa ──────────────────────────────────────────────────────────────
print("\n=== Quarta casa: ref metodo {473,389} x avaliador {A,A'} (SAW×mm) ===")
df4 = pd.read_csv(os.path.join(RESULTS_DIR, "mc_4thcell_raw.csv"))
df4_200 = df4[df4["alpha"]==200]
saw473_g = df4_200[(df4_200["agg"]=="saw") & (df4_200["mont"]=="greedy")]
saw473_o = df4_200[(df4_200["agg"]=="saw") & (df4_200["mont"]=="optimal")]

mc18 = pd.read_csv(os.path.join(RESULTS_DIR, "mc_18cells_raw.csv"))
mc18_200 = mc18[(mc18["alpha"]==200) & (mc18["agg"]=="saw") & (mc18["norm"]=="minmax")]
saw389_g = mc18_200[mc18_200["mont"]=="greedy"]
saw389_o = mc18_200[mc18_200["mont"]=="optimal"]

q2v2 = pd.read_csv(os.path.join(RESULTS_DIR, "mc_q2v2_summary.csv"))
s473_Ag = q2v2[(q2v2["method"]=="SAW_s1")&(q2v2["variant"]=="greedy")&(q2v2["alpha"]==200)]
s473_Ao = q2v2[(q2v2["method"]=="SAW_s1")&(q2v2["variant"]=="optimal")&(q2v2["alpha"]==200)]

def g(df_, col):
    if len(df_) > 0 and col in df_.columns:
        return f"{df_[col].mean()*100:.1f}%"
    return "n/a"

print(f"  {'ref':>4}  {'avaliador':>10}  {'greedy':>8}  {'otimo':>8}  (Q2)")
print(f"  {'473':>4}  {'A':>10}  {g(s473_Ag,'pct_nd_Q2'):>8}  {g(s473_Ao,'pct_nd_Q2'):>8}")
q473g = saw473_g["nd_Q2Ap"].mean()*100 if len(saw473_g) else float("nan")
q473o = saw473_o["nd_Q2Ap"].mean()*100 if len(saw473_o) else float("nan")
q389g = saw389_g["nd_Q2Ap"].mean()*100 if len(saw389_g) else float("nan")
q389o = saw389_o["nd_Q2Ap"].mean()*100 if len(saw389_o) else float("nan")
print(f"  {'473':>4}  {'A prime':>10}  {q473g:8.1f}%  {q473o:8.1f}%")
print(f"  {'389':>4}  {'A prime':>10}  {q389g:8.1f}%  {q389o:8.1f}%")
print(f"\n  Efeito excluir inaviaveis (389 vs 473, avaliador A'):")
print(f"    greedy: {q389g:.1f}% - {q473g:.1f}% = {q389g-q473g:+.1f}pp")
print(f"    otimo:  {q389o:.1f}% - {q473o:.1f}% = {q389o-q473o:+.1f}pp")
