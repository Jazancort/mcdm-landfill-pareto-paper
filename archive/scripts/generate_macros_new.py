# -*- coding: utf-8 -*-
"""
generate_macros_new.py -- Generate new macros required by the kappa-framing rewrite.

Macros produced:
  NormSigMin / NormSigMax      -- min/max of Norm_greedy where 95% CI excludes zero
  AsmVecSAWKtwentyfiveLo/Hi    -- CI for assembly vec SAW at kappa=25
  NeffWithinSlope/Lo/Hi        -- within-kappa fixed-effects slope (N_eff ~ contrast)

Appended to macros_e7.tex.
"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

OUT_MACROS = ROOT / "macros_e7.tex"

# ── Load e7_contrasts.csv ────────────────────────────────────────────────────
df_c = pd.read_csv(ROOT / "results" / "e7" / "e7_contrasts.csv")

# ── NormSigMin / NormSigMax  (Norm_greedy, CIs that exclude zero) ─────────────
norm = df_c[df_c["contrast"] == "Norm_greedy"].copy()
sig  = norm[norm["sig"] == "SIG"]

norm_sig_min = float(sig["diff_pp"].min())   # 13.3 at kappa=400
norm_sig_max = float(sig["diff_pp"].max())   # 29.2 at kappa=50

print(f"NormSigMin = {norm_sig_min:.1f}  (kappa={sig.loc[sig.diff_pp.idxmin(),'kappa']})")
print(f"NormSigMax = {norm_sig_max:.1f}  (kappa={sig.loc[sig.diff_pp.idxmax(),'kappa']})")

# ── AsmVecSAWKtwentyfiveLo / Hi  (from e7_contrasts.csv) ─────────────────────
asm25 = df_c[(df_c["contrast"] == "Asm_vec_SAW") & (df_c["kappa"] == 25)].iloc[0]
asm25_lo = float(asm25["ci_lo"])
asm25_hi = float(asm25["ci_hi"])
asm25_dp = float(asm25["diff_pp"])
asm25_sig = asm25["sig"]
print(f"\nAsmVecSAW k=25: {asm25_dp:+.1f} pp  CI=[{asm25_lo:.1f}, {asm25_hi:.1f}]  {asm25_sig}")

# CI excludes zero? → use "+3.4 pp" in text; if includes → "no detectable effect"
ci_includes_zero = (asm25_lo <= 0 <= asm25_hi)
print(f"  CI includes zero: {ci_includes_zero}")
if ci_includes_zero:
    print("  → use 'no detectable effect at kappa=25'")
else:
    print(f"  → use '+{asm25_dp:.1f} pp' at kappa=25")

# ── NeffWithinSlope / Lo / Hi  (within-kappa fixed-effects regression) ────────
df_r = pd.read_csv(ROOT / "results" / "e7" / "e7_raw.csv")

# Recompute N_eff per draw from weight seeds (same as analyze_neff_regression.py)
from mcdm_experiment import AHP_WEIGHTS
ALPHAS = [25, 50, 100, 200, 400, 1000]
N_DRAWS = 500
BASE_SEED = 100
SEED_K200 = 42
SEED_K50  = 42
DATA_SHA_K200 = "1d5bb4dae459e895c818343c1805f3c0e39b379d28c5454e6ef0e5bc23b807c1"
DATA_SHA_K50  = "8b91cba20b29b08bde9f26a19eaceeabf187791ae7c8d60bbb9982ea87084ddf"
import hashlib, numpy as np

w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
INF_CELLS = [("minmax","greedy"), ("minmax","optimal"), ("vector","greedy")]

def load_weights(alpha):
    if alpha == 200:
        W = np.load(ROOT / "results" / "e1" / "e1_weights_k200.npy")
        assert hashlib.sha256(W.tobytes()).hexdigest() == DATA_SHA_K200
        return W
    if alpha == 50:
        W = np.load(ROOT / "results" / "e1" / "e1_weights_k50.npy")
        assert hashlib.sha256(W.tobytes()).hexdigest() == DATA_SHA_K50
        return W
    rng = np.random.default_rng(BASE_SEED + alpha)
    return rng.dirichlet(alpha * w_ahp, size=N_DRAWS).astype(np.float64)

rows = []
for alpha in ALPHAS:
    W     = load_weights(alpha)
    sumsq = (W**2).sum(axis=1)
    neff  = 1.0 / sumsq
    df_a  = df_r[df_r["alpha"] == alpha]
    for draw_idx in range(N_DRAWS):
        df_d = df_a[df_a["draw"] == draw_idx]
        if len(df_d) == 0:
            continue
        cv = []
        for norm, mont in INF_CELLS:
            saw = df_d[(df_d["agg"]=="saw")&(df_d["norm"]==norm)&(df_d["mont"]==mont)]["nd_Q2Ap"].values
            top = df_d[(df_d["agg"]=="topsis")&(df_d["norm"]==norm)&(df_d["mont"]==mont)]["nd_Q2Ap"].values
            if len(saw)==1 and len(top)==1:
                cv.append(float(saw[0]) - float(top[0]))
        if cv:
            rows.append({"alpha": alpha, "draw": draw_idx,
                         "N_eff": neff[draw_idx], "contrast": float(np.mean(cv))})

df_full = pd.DataFrame(rows)

# Within-kappa fixed effects: demean contrast and N_eff within each alpha
df_full["c_mean"] = df_full.groupby("alpha")["contrast"].transform("mean")
df_full["n_mean"] = df_full.groupby("alpha")["N_eff"].transform("mean")
df_full["c_dm"]   = df_full["contrast"] - df_full["c_mean"]
df_full["n_dm"]   = df_full["N_eff"]    - df_full["n_mean"]

sl, ic, r, p, se = stats.linregress(df_full["n_dm"], df_full["c_dm"])

# Convert slope to pp (contrast is fraction 0-1, N_eff in [4,11])
sl_pp = sl * 100
se_pp = se * 100

# 95% CI using t-distribution (n-2 df)
n = len(df_full)
t95 = stats.t.ppf(0.975, df=n-2)
lo_pp = sl_pp - t95 * se_pp
hi_pp = sl_pp + t95 * se_pp

print(f"\nWithin-kappa fixed-effects regression:")
print(f"  slope  = {sl_pp:.2f} pp per unit N_eff")
print(f"  95% CI = [{lo_pp:.2f}, {hi_pp:.2f}]")
print(f"  r      = {r:.4f}, p = {p:.3e}")
ci_excludes_zero = not (lo_pp <= 0 <= hi_pp)
print(f"  CI excludes zero: {ci_excludes_zero}")
if ci_excludes_zero:
    print("  → VARIANT B: draws with more criteria favour TOPSIS at fixed kappa")
else:
    print("  → VARIANT A: N_eff does not explain reversal beyond kappa level")

# ── Write macros ─────────────────────────────────────────────────────────────
existing = OUT_MACROS.read_text(encoding="utf-8")

new_macros = f"""
% ── New macros for kappa-framing rewrite (generate_macros_new.py) ───────────
% NormSigMin/Max: min/max of Norm_greedy where 95%% CI excludes zero
\\newcommand{{\\NormSigMin}}{{{norm_sig_min:.1f}}}    % kappa={int(sig.loc[sig.diff_pp.idxmin(),'kappa'])}
\\newcommand{{\\NormSigMax}}{{{norm_sig_max:.1f}}}    % kappa={int(sig.loc[sig.diff_pp.idxmax(),'kappa'])}
% AsmVecSAW kappa=25 CI bounds (already in comment; now explicit macros)
\\newcommand{{\\AsmVecSAWKtwentyfiveLo}}{{{asm25_lo:.1f}}}  % [lo, hi] = [{asm25_lo:.1f}, {asm25_hi:.1f}]  {asm25_sig}
\\newcommand{{\\AsmVecSAWKtwentyfiveHi}}{{{asm25_hi:.1f}}}
% NeffWithin: within-kappa fixed-effects slope of contrast on N_eff
% CI includes zero: {ci_includes_zero_neff}
% → Variant {'B: draws spread over more criteria favour TOPSIS at fixed kappa' if not ci_includes_zero_neff else 'A: N_eff does not explain beyond kappa level'}
\\newcommand{{\\NeffWithinSlope}}{{{sl_pp:.2f}}}    % pp per unit N_eff (within-kappa FE)
\\newcommand{{\\NeffWithinLo}}{{{lo_pp:.2f}}}       % 95%% CI lower
\\newcommand{{\\NeffWithinHi}}{{{hi_pp:.2f}}}       % 95%% CI upper
"""

# detect whether CI for Neff within includes zero
ci_includes_zero_neff = (lo_pp <= 0 <= hi_pp)
# redo string with correct value
new_macros = f"""
% ── New macros for kappa-framing rewrite (generate_macros_new.py) ───────────
% NormSigMin/Max: min/max of Norm_greedy where 95%% CI excludes zero
\\newcommand{{\\NormSigMin}}{{{norm_sig_min:.1f}}}    % kappa={int(sig.loc[sig.diff_pp.idxmin(),'kappa'])}
\\newcommand{{\\NormSigMax}}{{{norm_sig_max:.1f}}}    % kappa={int(sig.loc[sig.diff_pp.idxmax(),'kappa'])}
% AsmVecSAW kappa=25 CI bounds
\\newcommand{{\\AsmVecSAWKtwentyfiveLo}}{{{asm25_lo:.1f}}}
\\newcommand{{\\AsmVecSAWKtwentyfiveHi}}{{{asm25_hi:.1f}}}
% NeffWithin: within-kappa fixed-effects slope (demeaned within each kappa)
% CI includes zero: {ci_includes_zero_neff} → Variant {'B' if not ci_includes_zero_neff else 'A'}
\\newcommand{{\\NeffWithinSlope}}{{{sl_pp:.2f}}}
\\newcommand{{\\NeffWithinLo}}{{{lo_pp:.2f}}}
\\newcommand{{\\NeffWithinHi}}{{{hi_pp:.2f}}}
"""

if "NormSigMin" not in existing:
    OUT_MACROS.write_text(existing + new_macros, encoding="utf-8")
    print(f"\nAppended new macros to {OUT_MACROS.name}")
else:
    print(f"\nMacros already present in {OUT_MACROS.name}")

print("\nSummary:")
print(f"  NormSigMin = {norm_sig_min:.1f}  NormSigMax = {norm_sig_max:.1f}")
print(f"  AsmVecSAW k=25: [{asm25_lo:.1f}, {asm25_hi:.1f}]  sig={asm25_sig}")
print(f"  NeffWithin: slope={sl_pp:.2f} pp/unit, CI=[{lo_pp:.2f}, {hi_pp:.2f}], variant={'B' if not ci_includes_zero_neff else 'A'}")
