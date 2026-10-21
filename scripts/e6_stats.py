# -*- coding: utf-8 -*-
"""
e6_stats.py  --  Canonical statistics for E6 PRESPEC.

Single source of truth for P1-P4 computations.
Imported by:
  scripts/e6_final_stats.py  (reporting / SUMARIO)
  scripts/generate_macros_e6.py  (macros_e6.tex generation)

Design:
  - All computations defined here; callers do NOT re-implement.
  - Tolerance TOL=1e-4 matches e6_final_stats.py convention.
  - P2 uses Poisson-binomial null (p_i=1/6 for n_distinct=3,
    1/3 for n_distinct=2, 0 for n_distinct=1).  Binomial(1/6) is
    anti-conservative for mixed-tie samples (underestimates E[successes]).
  - All return dicts; keys are stable across versions.
"""

import numpy as np
import pandas as pd
from scipy.stats import binomtest

TOL = 1e-4   # equality tolerance (also used in e6_final_stats.py)


def p1_stats(df: pd.DataFrame) -> dict:
    """P1: M and B cells — Q2_opt must equal 1 on every draw."""
    total = 0
    hits = 0
    for cell in ("M", "B"):
        sub = df[df["cell"] == cell]
        total += len(sub)
        hits  += int((sub["q2"] >= 1 - TOL).sum())
    return {"Hits": hits, "Total": total}


def p2_stats(df: pd.DataFrame) -> dict:
    """
    P2 (conservative): L >= F >= H AND H < L strictly per instance.

    Denominator: instances with loss > 0 at any TV_W level (L, F, H).
    Primary count (Strict): instances satisfying the above event.
    Three-way ties (L = F = H) are excluded from Strict (counted separately).

    Null model for statistical test:
      Labels (L, F, H) are a random permutation of the observed values.
      Probability of success = 1/6 if all three values are distinct (n_distinct=3),
      1/3 if exactly one pair is tied (n_distinct=2; L=F>H gives 1/3, L>F=H gives 1/3),
      0 if all three are equal (n_distinct=1; H=L => H<L impossible).
    Test: one-sided Poisson-binomial (exact).

    Returns
    -------
    dict with keys:
      LossyN   : denominator (informative instances)
      Strict   : L>=F>=H AND H<L (primary conservative count)
      Ties     : three-way ties L=F=H (excluded from Strict)
      Reversal : L>=F>=H fails (excluded from Strict)
      NDistinct3 / NDistinct2 : breakdown by n_distinct
      StrictOnly : sensitivity — n_distinct=3 AND success (for analysis of sensit.)
      ExpNull  : E[successes] under Poisson-binomial null
      P        : one-sided Poisson-binomial p-value
    """
    TW_CELLS = ["W_inf_L", "W_inf_F", "W_inf_H"]
    records = []
    for inst in df["inst_id"].unique():
        sub = df[(df["inst_id"] == inst) & (df["cell"].isin(TW_CELLS))]
        if sub.empty:
            continue
        agg = sub.groupby("cell")["q2"].mean()
        qL = float(agg.get("W_inf_L", 1.0))
        qF = float(agg.get("W_inf_F", 1.0))
        qH = float(agg.get("W_inf_H", 1.0))
        records.append({"qL": qL, "qF": qF, "qH": qH})

    res = pd.DataFrame(records)
    # Remove constant series (all levels ~100%)
    lossy_mask = ~((res["qL"] > 1 - TOL) & (res["qF"] > 1 - TOL) & (res["qH"] > 1 - TOL))
    lossy = res[lossy_mask]

    L, F, H = lossy["qL"].to_numpy(), lossy["qF"].to_numpy(), lossy["qH"].to_numpy()

    monotone = (L >= F - TOL) & (F >= H - TOL)
    tie3     = (np.abs(L - F) <= TOL) & (np.abs(F - H) <= TOL)
    mono_hl  = monotone & (L > H + TOL)     # success event
    reversal = ~monotone

    # n_distinct: 3 - number of tied pairs (floor 1)
    n_tp = ((np.abs(L-F) <= TOL).astype(int) +
            (np.abs(F-H) <= TOL).astype(int) +
            (np.abs(L-H) <= TOL).astype(int))
    n_distinct = np.clip(3 - n_tp, 1, 3)

    pi = np.where(n_distinct == 3, 1/6, np.where(n_distinct == 2, 1/3, 0.0))
    pmf = np.array([1.0])
    for p_i in pi:
        pmf = np.convolve(pmf, [1 - p_i, p_i])
    k = int(mono_hl.sum())
    p_val = float(pmf[k:].sum())
    e_null = float(pi.sum())
    k_strict3 = int(((n_distinct == 3) & mono_hl).sum())

    return {
        "LossyN":    len(lossy),
        "Strict":    k,
        "Ties":      int(tie3.sum()),
        "Reversal":  int(reversal.sum()),
        "NDistinct3": int((n_distinct == 3).sum()),
        "NDistinct2": int((n_distinct == 2).sum()),
        "StrictOnly": k_strict3,
        "ExpNull":   e_null,
        "P":         p_val,
    }


def p3_stats(df: pd.DataFrame) -> dict:
    """P3: Q2(V_inf_F) <= Q2(W_inf_F) — pre-registered criterion."""
    records = []
    for inst in df["inst_id"].unique():
        v = df[(df["inst_id"] == inst) & (df["cell"] == "V_inf_F")]["q2"].mean()
        w = df[(df["inst_id"] == inst) & (df["cell"] == "W_inf_F")]["q2"].mean()
        diff = float(v - w)
        records.append({
            "prereg": diff <= TOL,
            "strict": diff < -TOL,
            "rev":    diff >  TOL,
        })
    res = pd.DataFrame(records)
    n_denom   = len(res)
    n_prereg  = int(res["prereg"].sum())
    n_inf     = int((res["strict"] | res["rev"]).sum())
    n_strict  = int(res["strict"].sum())
    p_val = binomtest(n_strict, n_inf, 0.5, alternative="greater").pvalue \
            if n_inf > 0 else float("nan")
    return {
        "PreregN":    n_prereg,
        "PreregDenom": n_denom,
        "InfStrict":  n_strict,
        "InfDenom":   n_inf,
        "P":          float(p_val),
    }


def p4_stats(df: pd.DataFrame) -> dict:
    """
    P4: Q2(W_inf_F) vs Q2(W_def_F) — two-sided binomial.
    Prediction: inflate costs more (Q2_inf < Q2_def).
    Observed trend: deflate costs more (opposite direction).
    """
    records = []
    for inst in df["inst_id"].unique():
        inf_q = df[(df["inst_id"] == inst) & (df["cell"] == "W_inf_F")]["q2"].mean()
        def_q = df[(df["inst_id"] == inst) & (df["cell"] == "W_def_F")]["q2"].mean()
        diff  = float(inf_q - def_q)
        records.append({
            "infl_lt_defl": diff < -TOL,   # inflate < deflate: prediction direction
            "defl_lt_infl": diff >  TOL,   # deflate < inflate: observed (opposite)
            "tied":         abs(diff) <= TOL,
        })
    res = pd.DataFrame(records)
    n_infl    = int(res["infl_lt_defl"].sum())   # prediction direction
    n_defl    = int(res["defl_lt_infl"].sum())   # observed direction (opposite)
    n_tied    = int(res["tied"].sum())
    n_nontied = n_defl + n_infl
    p_val = binomtest(n_defl, n_nontied, 0.5, alternative="two-sided").pvalue
    return {
        "Defl":     n_defl,
        "Infl":     n_infl,
        "NonTied":  n_nontied,
        "Tied":     n_tied,
        "P":        float(p_val),
    }


def compute_all_stats(df: pd.DataFrame, families: list) -> dict:
    """
    Compute P1-P4 for each family and combined (key='All').

    Parameters
    ----------
    df       : full e6_raw_prespec.csv DataFrame
    families : list of family name strings (column 'family')

    Returns
    -------
    dict {suf: {"P1": ..., "P2": ..., "P3": ..., "P4": ...}}
    where suf ∈ families + ['All'].
    """
    S = {"All": {"P1": p1_stats(df), "P2": p2_stats(df),
                 "P3": p3_stats(df), "P4": p4_stats(df)}}
    for fam in families:
        sub = df[df["family"] == fam]
        S[fam] = {"P1": p1_stats(sub), "P2": p2_stats(sub),
                  "P3": p3_stats(sub), "P4": p4_stats(sub)}
    return S


def check_invariants(S: dict, n_per_fam: int = 30) -> None:
    """Assert regression invariants against TASKS.md values (run at generation time)."""
    A = S["All"]
    assert A["P1"]["Hits"] == A["P1"]["Total"], "P1: some draws failed"
    p2 = A["P2"]
    assert (p2["Strict"], p2["Ties"], p2["Reversal"], p2["LossyN"]) == (85, 2, 1, 88), \
        f"P2 regression: {p2}"
    assert (p2["NDistinct3"], p2["NDistinct2"]) == (52, 34), \
        f"P2 n_distinct regression: {p2}"
    assert p2["StrictOnly"] == 52, f"P2 StrictOnly: {p2['StrictOnly']}"
    assert abs(p2["ExpNull"] - 20.0) < 0.1, f"P2 ExpNull: {p2['ExpNull']}"
    assert p2["P"] < 0.001, f"P2 Poisson-binomial p: {p2['P']}"
    p4 = A["P4"]
    assert (p4["Defl"], p4["NonTied"], p4["Tied"]) == (53, 87, 33), \
        f"P4 regression: {p4}"
    assert abs(p4["P"] - 0.053003) < 5e-6, f"P4 p-value: {p4['P']}"
    print("  Invariants: OK")
