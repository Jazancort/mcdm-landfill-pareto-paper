# -*- coding: utf-8 -*-
"""
analyze_neff_regression.py -- E7 mechanism B2: N_eff regression.

Per-draw regression of the SAW-TOPSIS aggregation contrast on
N_eff = 1/sum_j w_j^2  (effective number of criteria).

Uses e7_raw.csv for Q2 outcomes and regenerates weight draws from
the same seeds as run_e7_kappa_sweep.py to compute N_eff per draw.

PRESPEC AMENDMENT A2 (corpus/PRESPEC_E7_KAPPA_A2.md).
"""
from __future__ import annotations
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from mcdm_experiment import AHP_WEIGHTS

# ── Seeds (must match run_e7_kappa_sweep.py) ─────────────────────────────────
ALPHAS     = [25, 50, 100, 200, 400, 1000]
N_DRAWS    = 500
BASE_SEED  = 100
SEED_K200  = 42
SEED_K50   = 42
DATA_SHA_K200 = "1d5bb4dae459e895c818343c1805f3c0e39b379d28c5454e6ef0e5bc23b807c1"
DATA_SHA_K50  = "8b91cba20b29b08bde9f26a19eaceeabf187791ae7c8d60bbb9982ea87084ddf"

# ── Three informative cells (SAW-TOPSIS contrast) ────────────────────────────
# Same as Agg_pooled3 in run_e7_kappa_sweep.py: average over three cells
INF_CELLS = [("minmax", "greedy"), ("minmax", "optimal"), ("vector", "greedy")]

w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)


def load_weights(alpha: int) -> np.ndarray:
    """Return (N_DRAWS, n_criteria) weight matrix for given alpha."""
    if alpha == 200:
        path = ROOT / "results" / "e1" / "e1_weights_k200.npy"
        W = np.load(path)
        sha = hashlib.sha256(W.tobytes()).hexdigest()
        assert sha == DATA_SHA_K200, f"k=200 data SHA mismatch: {sha[:16]}"
        return W
    if alpha == 50:
        path = ROOT / "results" / "e1" / "e1_weights_k50.npy"
        W = np.load(path)
        sha = hashlib.sha256(W.tobytes()).hexdigest()
        assert sha == DATA_SHA_K50, f"k=50 data SHA mismatch: {sha[:16]}"
        return W
    seed = BASE_SEED + alpha
    rng = np.random.default_rng(seed)
    return rng.dirichlet(alpha * w_ahp, size=N_DRAWS).astype(np.float64)


def build_per_draw_df() -> pd.DataFrame:
    """Build DataFrame with (alpha, draw, N_eff, H_w, contrast_3inf)."""
    df_raw = pd.read_csv(ROOT / "results" / "e7" / "e7_raw.csv")

    records = []
    for alpha in ALPHAS:
        W = load_weights(alpha)
        sumsq = (W ** 2).sum(axis=1)      # Herfindahl: sum_j w_j^2, shape (N_DRAWS,)
        neff  = 1.0 / sumsq               # N_eff per draw

        df_a = df_raw[df_raw["alpha"] == alpha]

        for draw_idx in range(N_DRAWS):
            df_d = df_a[df_a["draw"] == draw_idx]
            if len(df_d) == 0:
                continue

            # Per-draw contrast averaged over three informative cells
            contrast_vals: list[float] = []
            for norm, mont in INF_CELLS:
                row_saw = df_d[
                    (df_d["agg"] == "saw") &
                    (df_d["norm"] == norm) &
                    (df_d["mont"] == mont)
                ]["nd_Q2Ap"].values
                row_top = df_d[
                    (df_d["agg"] == "topsis") &
                    (df_d["norm"] == norm) &
                    (df_d["mont"] == mont)
                ]["nd_Q2Ap"].values
                if len(row_saw) == 1 and len(row_top) == 1:
                    contrast_vals.append(float(row_saw[0]) - float(row_top[0]))

            if not contrast_vals:
                continue

            # H_w is constant within a draw (same weight vector for all cells)
            hw = float(df_d["H_w"].iloc[0])

            records.append({
                "alpha"      : alpha,
                "draw"       : draw_idx,
                "N_eff"      : neff[draw_idx],
                "sumsq_w"    : sumsq[draw_idx],
                "H_w"        : hw,
                "contrast"   : float(np.mean(contrast_vals)),
            })

    return pd.DataFrame(records)


def main() -> None:
    print("Building per-draw dataset ...", flush=True)
    df = build_per_draw_df()
    print(f"  {len(df)} rows  ({df['alpha'].nunique()} alpha values × {N_DRAWS} draws)\n",
          flush=True)

    # ── Pooled regression across all alpha values ─────────────────────────────
    sl, ic, r, p, se = stats.linregress(df["N_eff"], df["contrast"])
    n_total = len(df)
    print("=" * 60)
    print("POOLED REGRESSION (all alpha): contrast ~ N_eff")
    print(f"  n         = {n_total}")
    print(f"  intercept = {ic:.4f}")
    print(f"  slope     = {sl:.4f}  (pp per unit N_eff)")
    print(f"  r         = {r:.4f}")
    print(f"  p         = {p:.2e}")
    print(f"  SE(slope) = {se:.4f}")

    # Zero-crossing N_eff* = -intercept / slope
    neff_star = -ic / sl
    print(f"  N_eff*    = {neff_star:.2f}  (predicted crossover)")
    print()

    # ── Within-alpha regressions ───────────────────────────────────────────────
    print("PER-ALPHA REGRESSIONS")
    for alpha in ALPHAS:
        sub = df[df["alpha"] == alpha].copy()
        if len(sub) < 10:
            continue
        sl_a, ic_a, r_a, p_a, _ = stats.linregress(sub["N_eff"], sub["contrast"])
        mean_neff = sub["N_eff"].mean()
        print(f"  alpha={alpha:4d}: slope={sl_a:+.4f}  r={r_a:+.4f}  "
              f"p={p_a:.2e}  mean_N_eff={mean_neff:.2f}")
    print()

    # ── N_eff summary statistics by alpha ─────────────────────────────────────
    print("N_eff SUMMARY BY ALPHA")
    for alpha in ALPHAS:
        sub = df[df["alpha"] == alpha]
        print(f"  alpha={alpha:4d}: mean={sub['N_eff'].mean():.2f}  "
              f"sd={sub['N_eff'].std():.2f}  "
              f"[{sub['N_eff'].min():.2f}, {sub['N_eff'].max():.2f}]")
    print()

    # ── Mean contrast by alpha (for cross-check with e7_contrasts.csv) ────────
    print("MEAN CONTRAST (3inf) BY ALPHA  [cross-check vs Agg_pooled3]")
    for alpha in ALPHAS:
        sub = df[df["alpha"] == alpha]
        print(f"  alpha={alpha:4d}: mean contrast = {sub['contrast'].mean()*100:.2f} pp")
    print()

    # ── Export regression summary ──────────────────────────────────────────────
    out_dir = ROOT / "results" / "e7"
    summary = {
        "n_draws_pooled": n_total,
        "pooled_slope": round(sl, 6),
        "pooled_intercept": round(ic, 6),
        "pooled_r": round(r, 6),
        "pooled_p": float(p),
        "pooled_se": round(se, 6),
        "neff_star": round(neff_star, 2),
    }
    import json
    outpath = out_dir / "neff_regression.json"
    with open(outpath, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to {outpath.relative_to(ROOT)}")

    # ── LaTeX macro suggestions ────────────────────────────────────────────────
    print("\nMACRO SUGGESTIONS for macros_e7.tex:")
    print(f"  \\NeffRegrSlope    = {sl*100:.2f}  % pp per unit N_eff (×100 to match pp scale)")
    print(f"  \\NeffRegrR        = {r:.3f}")
    print(f"  \\NeffRegrP        = ...  (from p-value)")
    print(f"  \\NeffCrossover    = {neff_star:.1f}")
    print(f"  \\NeffRegrN        = {n_total:,}")


if __name__ == "__main__":
    main()
