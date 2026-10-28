# -*- coding: utf-8 -*-
"""
compute_aspect_polecoding.py
============================
Canonical computation of Kendall tau_b and top-K agreement between
TOPSIS/vec rankings under the two aspect orientations (leeward=1 vs leeward=0).

This is the authoritative source for the values reported in §6.9 of the manuscript:
  \\AspectTauB      -- Kendall tau_b between the two orderings
  \\AspectTopKAgree -- top-100 set agreement (fraction of top-100 in common)

Run:
    uv run python scripts/compute_aspect_polecoding.py

Output written to: results/amplitudes/aspect_polecoding.json
"""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.stats import kendalltau
from pathlib import Path
from mcdm_experiment import load_data, impute_nan, COL, AHP_WEIGHTS, _build_decision_matrix
from scoring import make_scorers

REPO = Path(__file__).parent.parent
TOP_K = 100

def main():
    df_all, _, _ = load_data()
    df_imp = impute_nan(df_all)
    df_via = df_imp[df_imp[COL['protected']] > 0].copy()  # 389 admissible sites

    col_names = list(AHP_WEIGHTS.keys())
    W_raw = np.array(list(AHP_WEIGHTS.values()))
    W = W_raw / W_raw.sum()

    X_via, benefit = _build_decision_matrix(df_via)
    asp_idx = col_names.index("aspect")

    # ── Build X_adj for both orientations ────────────────────────────────
    def make_adj(X, ben):
        Xa = X.copy()
        for j, is_ben in enumerate(ben):
            if not is_ben:
                Xa[:, j] = 1.0 - X[:, j]
        return Xa

    # Original: leeward=1 (benefit=True for aspect)
    X_adj_orig = make_adj(X_via, benefit)
    norms_orig = np.sqrt((X_via**2).sum(0))

    # Flipped: leeward=0 (non-leeward=1)
    X_via_flip = X_via.copy()
    X_via_flip[:, asp_idx] = 1.0 - X_via[:, asp_idx]
    benefit_flip = benefit.copy()   # benefit mask unchanged: aspect still "benefit"
    X_adj_flip = make_adj(X_via_flip, benefit_flip)
    norms_flip = np.sqrt((X_via_flip**2).sum(0))

    # ── TOPSIS/vec scores ─────────────────────────────────────────────────
    _, topsis_orig = make_scorers(X_via, X_adj_orig, norms_orig, benefit)
    _, topsis_flip = make_scorers(X_via_flip, X_adj_flip, norms_flip, benefit_flip)

    score_orig = topsis_orig(W, norm="vector")
    score_flip = topsis_flip(W, norm="vector")

    # ── Kendall tau_b ─────────────────────────────────────────────────────
    tau_b, _ = kendalltau(score_orig, score_flip)

    # ── Top-K agreement ───────────────────────────────────────────────────
    top_orig = set(np.argsort(-score_orig)[:TOP_K])
    top_flip = set(np.argsort(-score_flip)[:TOP_K])
    topk_agree = len(top_orig & top_flip) / TOP_K

    n1 = int((X_via[:, asp_idx] > 0.5).sum())  # leeward sites
    n0 = len(df_via) - n1

    result = {
        "n_sites": len(df_via),
        "n1_leeward": n1,
        "n0_nonleeward": n0,
        "top_k": TOP_K,
        "tau_b": round(float(tau_b), 4),
        "topk_agreement": round(float(topk_agree), 4),
        "method": "TOPSIS/vector, W=AHP normalised, 389 admissible sites",
    }

    out = REPO / "results" / "amplitudes" / "aspect_polecoding.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(result, f, indent=2)

    print(f"n_sites:         {result['n_sites']}  (n1_leeward={n1}, n0_nonleeward={n0})")
    print(f"Kendall tau_b:   {tau_b:.4f}   -> macro \\AspectTauB{{{round(tau_b, 2)}}}")
    print(f"Top-{TOP_K} agree:  {topk_agree:.4f}  -> macro \\AspectTopKAgree{{{round(topk_agree, 2)}}}")
    print(f"Written: {out}")

    if abs(tau_b - topk_agree) < 1e-6:
        print("\nWARNING: tau_b == topk_agree (suspicious coincidence — check for copy error)")
    else:
        delta = abs(tau_b - topk_agree)
        print(f"\nValues are distinct (delta={delta:.4f}) -- not a copy error")

if __name__ == "__main__":
    main()
