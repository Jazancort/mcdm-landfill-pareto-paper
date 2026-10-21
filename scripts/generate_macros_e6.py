# -*- coding: utf-8 -*-
"""
generate_macros_e6.py  --  Generate macros_e6.tex from e6_raw_prespec.csv.

Output: macros_e6.tex  (in repo root, alongside macros.tex)

Run:
    uv run python scripts/generate_macros_e6.py

Naming convention (aligns with macros.tex):
  - CamelCase, no standalone digits
  - Prefix: Esix (block), then P[one/two/three/four], then Descriptor, then Suffix
  - Family suffixes: Logn / Beta / Unif / Zinf / All
  - p-values stored as full expression: p<0.001 or p=0.053 (no bare number)
  - Lo/Hi or Pct suffixes as needed
"""

import hashlib, json, subprocess, sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

REPO = Path(__file__).parent.parent
SRC_CSV = REPO / "results" / "e6" / "e6_raw_prespec.csv"
OUT_TEX = REPO / "macros_e6.tex"
OUT_JSON = REPO / "results" / "e6" / "e6_stats.json"

TOL = 1e-4   # tolerance for equality tests (same as e6_final_stats.py)

FAMILIES = ["lognormal", "beta13", "uniform", "zero_inflated"]
FAM_SUFFIX = {
    "lognormal":    "Logn",
    "beta13":       "Beta",
    "uniform":      "Unif",
    "zero_inflated":"Zinf",
    None:           "All",   # combined across families
}
N_REP = 30  # replicates per family

# ── Rounding ─────────────────────────────────────────────────────────────────

def rnd(x, nd):
    """Half-up rounding on the true decimal representation (avoids float bias)."""
    return str(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), ROUND_HALF_UP))


def fmt_p(p):
    """Format p-value as LaTeX string."""
    return r"p<0.001" if p < 0.001 else "p=" + rnd(p, 3)


def fmt_int(n):
    """Format integer with LaTeX thousands separator."""
    return f"{int(n):,}".replace(",", "{,}")


# ── Statistics per block ──────────────────────────────────────────────────────

def p1_stats(df):
    """P1: M and B cells must have Q2 = 100% on every draw."""
    total = 0; hits = 0
    for cell in ("M", "B"):
        sub = df[df["cell"] == cell]
        total += len(sub)
        hits  += int((sub["q2"] >= 1 - TOL).sum())
    return {"Hits": hits, "Total": total}


def p2_stats(df):
    """
    P2 (conservative): L≥F≥H AND H < L strictly per instance.
    - Primary count: monotone AND H strictly below L (excludes 3-way ties).
    - Three-way ties (L≈F≈H, counted as monotone by the weak criterion but
      degenerate under null=1/6) are identified and excluded from the main count.
    - Denominator = instances with any loss at levels L, F, or H.
    - Null = 1/6: under random ordering of 3 distinct values, P(L≥F≥H) = 1/6.
    """
    TW_CELLS = ["W_inf_L", "W_inf_F", "W_inf_H"]
    results = []
    for rep in df["inst_id"].unique():
        sub = df[(df["inst_id"] == rep) & (df["cell"].isin(TW_CELLS))]
        if sub.empty:
            continue
        agg = sub.groupby("cell")["q2"].mean()
        qL = agg.get("W_inf_L", 1.0)
        qF = agg.get("W_inf_F", 1.0)
        qH = agg.get("W_inf_H", 1.0)
        results.append({"qL": qL, "qF": qF, "qH": qH})
    results = pd.DataFrame(results)

    # Constant series (all levels ≈ 100%) → not informative
    mask_lossy = ~((results["qL"] > 1 - TOL) &
                   (results["qF"] > 1 - TOL) &
                   (results["qH"] > 1 - TOL))
    lossy = results[mask_lossy]

    L, F, H = lossy["qL"].values, lossy["qF"].values, lossy["qH"].values

    # Monotone (non-strict): L >= F >= H
    monotone  = (L >= F - TOL) & (F >= H - TOL)
    # Three-way tie: L ≈ F ≈ H (degenerate case — excluded from primary count)
    tie3      = (np.abs(L - F) <= TOL) & (np.abs(F - H) <= TOL)
    # Primary count: monotone AND H strictly below L (= monotone AND NOT tie3)
    mono_hl   = monotone & (L > H + TOL)   # L≥F≥H AND H<L strictly
    # Full reversal: L>=F>=H fails
    reversal  = ~monotone

    n = len(lossy)
    k = int(mono_hl.sum())   # 85 in TASKS.md
    pval = binomtest(k, n, 1/6, alternative="greater").pvalue

    return {
        "LossyN": n,
        "Strict": k,        # L≥F≥H AND H<L (conservative primary count)
        "Ties": int(tie3.sum()),          # three-way ties (excluded from Strict)
        "Reversal": int(reversal.sum()),  # L≥F≥H fails
        "P": pval,
    }


def p3_stats(df):
    """P3: Q2(V_inf_F) <= Q2(W_inf_F) (pre-registered criterion)."""
    results = []
    for rep in df["inst_id"].unique():
        v = df[(df["inst_id"] == rep) & (df["cell"] == "V_inf_F")]["q2"].mean()
        w = df[(df["inst_id"] == rep) & (df["cell"] == "W_inf_F")]["q2"].mean()
        diff = v - w
        results.append({
            "prereg": diff <= TOL,
            "strict": diff < -TOL,
            "rev":    diff >  TOL,
        })
    results = pd.DataFrame(results)
    n_prereg = int(results["prereg"].sum())
    n_denom  = len(results)
    n_inf = int((results["strict"] | results["rev"]).sum())
    n_strict_inf = int(results["strict"].sum())
    pval = binomtest(n_strict_inf, n_inf, 0.5, alternative="greater").pvalue if n_inf > 0 else float("nan")
    return {
        "PreregN": n_prereg,
        "PreregDenom": n_denom,
        "InfStrict": n_strict_inf,
        "InfDenom": n_inf,
        "P": pval,
    }


def p4_stats(df):
    """P4: Q2(W_inf_F) vs Q2(W_def_F) — two-sided binomial."""
    results = []
    for rep in df["inst_id"].unique():
        inf_q = df[(df["inst_id"] == rep) & (df["cell"] == "W_inf_F")]["q2"].mean()
        def_q = df[(df["inst_id"] == rep) & (df["cell"] == "W_def_F")]["q2"].mean()
        diff = inf_q - def_q
        results.append({
            "strict_inf_lt_def": diff < -TOL,   # inf < def: prediction direction
            "strict_def_lt_inf": diff >  TOL,   # deflate costs more: opposite direction
            "tied": abs(diff) <= TOL,
        })
    results = pd.DataFrame(results)
    n_defl = int(results["strict_def_lt_inf"].sum())   # deflate > inflate
    n_infl = int(results["strict_inf_lt_def"].sum())   # inflate > deflate (prediction)
    n_tied = int(results["tied"].sum())
    n_nontied = n_defl + n_infl
    pval = binomtest(n_defl, n_nontied, 0.5, alternative="two-sided").pvalue
    return {
        "Defl": n_defl,
        "Infl": n_infl,
        "NonTied": n_nontied,
        "Tied": n_tied,
        "P": pval,
    }


# ── Compute all stats ─────────────────────────────────────────────────────────

def compute_all_stats(df):
    """Compute P1-P4 stats per family and combined (All)."""
    S = {}
    # Combined first
    S["All"] = {
        "P1": p1_stats(df),
        "P2": p2_stats(df),
        "P3": p3_stats(df),
        "P4": p4_stats(df),
    }
    # Per family
    for fam in FAMILIES:
        suf = FAM_SUFFIX[fam]
        sub = df[df["family"] == fam]
        S[suf] = {
            "P1": p1_stats(sub),
            "P2": p2_stats(sub),
            "P3": p3_stats(sub),
            "P4": p4_stats(sub),
        }
    return S


# ── Regression invariants ─────────────────────────────────────────────────────

def check_invariants(S):
    """Assertions against previously computed values (TASKS.md / corpus)."""
    A = S["All"]
    # P1
    assert A["P1"]["Hits"] == A["P1"]["Total"], "P1: some draws failed"
    # P2 conservative
    p2 = A["P2"]
    assert (p2["Strict"], p2["Ties"], p2["Reversal"], p2["LossyN"]) == (85, 2, 1, 88), \
        f"P2 regression: {p2}"
    # P4
    p4 = A["P4"]
    assert (p4["Defl"], p4["NonTied"], p4["Tied"]) == (53, 87, 33), \
        f"P4 regression: {p4}"
    assert abs(p4["P"] - 0.053003) < 5e-6, f"P4 p-value: {p4['P']}"
    # Family sums must equal All
    for blk in ("P2", "P4"):
        for key in ["Strict", "Ties", "Reversal", "LossyN"] if blk == "P2" \
                   else ["Defl", "Infl", "NonTied", "Tied"]:
            total_fam = sum(S[FAM_SUFFIX[f]][blk][key] for f in FAMILIES)
            assert total_fam == A[blk][key], \
                f"Family sum mismatch {blk}.{key}: {total_fam} vs {A[blk][key]}"
    print("  Invariants: OK")


# ── Write macros_e6.tex ──────────────────────────────────────────────────────

def write_macros(S, sha, commit):
    lines = [
        "% AUTO-GENERATED by scripts/generate_macros_e6.py -- DO NOT EDIT BY HAND",
        f"% source: results/e6/e6_raw_prespec.csv  sha256={sha[:16]}  commit={commit}",
        r"% Naming convention: CamelCase, \Esix prefix, family suffix (Logn/Beta/Unif/Zinf/All)",
        "",
    ]

    def m(name, val, note=""):
        cmd = rf"\newcommand{{\{name}}}{{{val}}}"
        if note:
            cmd += f"  % {note}"
        lines.append(cmd)

    # ── Design ──────────────────────────────────────────────────────────────
    lines.append("% ── Design ───────────────────────────────────────────────────────────")
    m("EsixNinst",    "120",           "total instances (4 families x 30 reps)")
    m("EsixNfam",     "4",             "number of marginal families")
    m("EsixNdraws",   fmt_int(24000),  "total draws (120 inst x 200 draws)")
    m("EsixPiZinf",   "0.90",          "zero-inflation rate for zero_inflated family")
    lines.append("")

    # ── P1 ──────────────────────────────────────────────────────────────────
    p1 = S["All"]["P1"]
    lines.append("% ── P1 ──────────────────────────────────────────────────────────────")
    m("EsixPoneHits",  fmt_int(p1["Hits"]),  "draws with TV_W=0 and Q2^opt=100%")
    m("EsixPoneTotal", fmt_int(p1["Total"]), "total M+B cell draws")
    lines.append("")

    # ── P2 ──────────────────────────────────────────────────────────────────
    lines.append("% ── P2 (conservative: 3-way ties counted as failures) ───────────────")
    lines.append("% denominator = instances with loss>0 at some TV_W level (L/F/H)")
    lines.append("% primary count = L>=F>=H AND H<L strictly (= monotone excl. 3-way ties)")
    lines.append("% null = 1/6: random ordering of 3 distinct values")
    for suf in [FAM_SUFFIX[f] for f in FAMILIES] + ["All"]:
        p2 = S[suf]["P2"]
        sfx = suf
        m(f"EsixPtwoLossyN{sfx}",   str(p2["LossyN"]),   "instances with any loss")
        m(f"EsixPtwoStrict{sfx}",   str(p2["Strict"]),   "L>=F>=H AND H<L (monotone excl. 3-way ties)")
        m(f"EsixPtwoTies{sfx}",     str(p2["Ties"]),     "3-way ties L=F=H (counted as failures)")
        m(f"EsixPtwoReversal{sfx}", str(p2["Reversal"]), "L>=F>=H fails")
        m(f"EsixPtwoP{sfx}",        fmt_p(p2["P"]),      "one-sided binomial null=1/6")
        lines.append("")

    # ── P3 ──────────────────────────────────────────────────────────────────
    lines.append("% ── P3 ──────────────────────────────────────────────────────────────")
    lines.append("% pre-registered: V_inf_F <= W_inf_F (TV_B agrava perda)")
    for suf in [FAM_SUFFIX[f] for f in FAMILIES] + ["All"]:
        p3 = S[suf]["P3"]
        sfx = suf
        m(f"EsixPthreePreregN{sfx}",    str(p3["PreregN"]),    "instances meeting pre-registered criterion V<=W")
        m(f"EsixPthreeDenom{sfx}",      str(p3["PreregDenom"]), "total instances tested (30 or 120)")
        m(f"EsixPthreeInfStrict{sfx}",  str(p3["InfStrict"]),  "informative strict V<W")
        m(f"EsixPthreeInfDenom{sfx}",   str(p3["InfDenom"]),   "informative denominator")
        m(f"EsixPthreeP{sfx}",          fmt_p(p3["P"]),         "one-sided binomial p (informative)")
        lines.append("")

    # ── P4 ──────────────────────────────────────────────────────────────────
    lines.append("% ── P4 (bilateral; post hoc pooling across families = All) ─────────")
    lines.append("% deflate > inflate is the OPPOSITE of the prediction (DEV-E6-003)")
    for suf in [FAM_SUFFIX[f] for f in FAMILIES] + ["All"]:
        p4 = S[suf]["P4"]
        sfx = suf
        note_p = "two-sided binomial" + (", post hoc pooling (DEV-E6-003)" if suf == "All" else "")
        m(f"EsixPfourDefl{sfx}",     str(p4["Defl"]),     "deflate>inflate strictly (OPPOSITE of prediction)")
        m(f"EsixPfourInfl{sfx}",     str(p4["Infl"]),     "inflate>deflate strictly (prediction direction)")
        m(f"EsixPfourNonTied{sfx}",  str(p4["NonTied"]),  "non-tied pairs (denominator for binomtest)")
        m(f"EsixPfourTied{sfx}",     str(p4["Tied"]),     "tied pairs (excluded from binomtest)")
        m(f"EsixPfourP{sfx}",        fmt_p(p4["P"]),      note_p)
        lines.append("")

    OUT_TEX.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Written: {OUT_TEX}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("generate_macros_e6.py")
    print(f"  Reading: {SRC_CSV}")
    df = pd.read_csv(SRC_CSV)
    sha = hashlib.sha256(SRC_CSV.read_bytes()).hexdigest()
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    print(f"  CSV sha256: {sha[:16]}  commit: {commit}")
    print(f"  Rows: {len(df)}  inst_id: {df['inst_id'].nunique()}  families: {df['family'].nunique()}")

    S = compute_all_stats(df)
    check_invariants(S)
    write_macros(S, sha, commit)

    # Write JSON for verify_macros_permanent.py
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"sha256": sha, "commit": commit,
               "stats": {k: {kk: {kkk: float(vvv) if isinstance(vvv, float) else vvv
                                   for kkk, vvv in vv.items()}
                              for kk, vv in v.items()}
                          for k, v in S.items()}},
              open(OUT_JSON, "w"), indent=2)
    print(f"  Written: {OUT_JSON}")

    # Print summary (from data, not hardcoded)
    A = S["All"]
    print()
    print("SUMMARY:")
    print(f"  P1: {A['P1']['Hits']}/{A['P1']['Total']} draws ({A['P1']['Hits']/A['P1']['Total']:.0%})")
    p2 = A["P2"]
    print(f"  P2: {p2['Strict']}/{p2['LossyN']} strict L>F>H "
          f"({p2['Ties']} 3-way ties, {p2['Reversal']} reversal)  "
          f"{fmt_p(p2['P'])} (null=1/6)")
    p4 = A["P4"]
    print(f"  P4: {p4['Defl']}/{p4['NonTied']} deflate>inflate "
          f"({p4['Tied']} tied)  {fmt_p(p4['P'])} two-sided")


if __name__ == "__main__":
    main()
