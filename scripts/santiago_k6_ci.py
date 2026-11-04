# -*- coding: utf-8 -*-
"""santiago_k6_ci.py — Descriptive bootstrap CIs for Santiago K6 (Agg_pooled3).

K6 = SAW minus TOPSIS aggregation contrast (Agg_pooled3, 3 informative cells).
These CIs are DESCRIPTIVE and COMPUTED AFTER THE EVALUATION. No verdict depends on them.
They are added to the κ figure only to make the bands comparable to Fogo (E7).

Method: identical to run_e7_kappa_sweep.py bstrap() — percentile bootstrap, B=2000,
resample-with-replacement over the 500 per-draw Agg_pooled3 values.
  Source confirmation: run_e7_kappa_sweep.py:320-327
    def bstrap(diff_pp, B=B_BOOT, seed=99):
        rng_b = np.random.default_rng(seed)
        boots = np.array([rng_b.choice(diff_pp, size=len(diff_pp), replace=True).mean()
                          for _ in range(B)])
        lo = float(np.percentile(boots, 2.5))
        hi = float(np.percentile(boots, 97.5))

Formula: Agg_pooled3 = mean(SAW - TOPSIS) over cells (mm_grd, vec_grd, vec_opt).
  Source confirmation: santiago_eval_core.py:23-35
    saw3  = grp[["SAW_mm_grd",    "SAW_vec_grd",    "SAW_vec_opt"]].values.mean() * 100
    tops3 = grp[["TOPSIS_mm_grd", "TOPSIS_vec_grd", "TOPSIS_vec_opt"]].values.mean() * 100

Seeds: from numpy.random.SeedSequence(20261104).
  ST branch seed from child 0, SN branch seed from child 1.

Input: results/santiago/mc_ST_raw.csv and mc_SN_raw.csv (SHA-verified).
Output: results/santiago/santiago_k6_ci.json (SHA logged on stdout).

Usage:
    uv run python scripts/santiago_k6_ci.py
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT   = Path(__file__).parent.parent
SEALED = ROOT / "results" / "santiago"

# SHAs from santiago_predictions_v2.json provenance (eval run d02a324)
SHA_ST_RAW = "123a5421d81b7bdd5d405ddb4a60edde1eeaa2f7da5cefbb640812aeed67bd80"
SHA_SN_RAW = "dbfa2f00b6f3f98e3a900f9020f98ecb55ef98dfdeed199a334f7b299013d492"

B_BOOT    = 2000
KAPPAS    = [25, 50, 100, 200, 400, 1000]


# ── SHA-verify inputs ──────────────────────────────────────────────────────────
def verify_csv(name, expected_sha):
    path = SEALED / name
    if not path.exists():
        raise RuntimeError(f"Not found: {path}")
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != expected_sha:
        raise RuntimeError(
            f"SHA mismatch for {name}:\n  expected {expected_sha}\n  got      {got}"
        )
    print(f"  SHA OK: {name} ({expected_sha[:16]})")
    return pd.read_csv(path)


# ── Agg_pooled3 per draw × κ ───────────────────────────────────────────────────
def compute_k6_per_draw(df):
    """Return DataFrame with columns draw, kappa, k6 (Agg_pooled3 in pp)."""
    rows = []
    for (kappa, draw), grp in df.groupby(["kappa", "draw"]):
        if not np.isfinite(kappa):  # skip kappa=inf rows
            continue
        saw3  = grp[["SAW_mm_grd",    "SAW_vec_grd",    "SAW_vec_opt"]].values.mean() * 100
        tops3 = grp[["TOPSIS_mm_grd", "TOPSIS_vec_grd", "TOPSIS_vec_opt"]].values.mean() * 100
        rows.append({"kappa": int(kappa), "draw": int(draw),
                     "k6": float(saw3 - tops3)})
    return pd.DataFrame(rows)


# ── Percentile bootstrap ───────────────────────────────────────────────────────
def bstrap(diff_pp, B, rng):
    """Percentile bootstrap CI; same method as run_e7_kappa_sweep.py:320-327."""
    boots = np.array([
        rng.choice(diff_pp, size=len(diff_pp), replace=True).mean()
        for _ in range(B)
    ])
    obs = float(diff_pp.mean())
    lo  = float(np.percentile(boots, 2.5))
    hi  = float(np.percentile(boots, 97.5))
    return obs, lo, hi


# ── Main ───────────────────────────────────────────────────────────────────────
print("Santiago K6 descriptive bootstrap CIs")
print("  Method: percentile bootstrap, B=2000 (same as Fogo E7)")
print("  Cells: Agg_pooled3 = mean(SAW-TOPSIS) over (mm_grd, vec_grd, vec_opt)")
print("  Seeds: SeedSequence(20261104); ST=child[0], SN=child[1]")
print()

df_st = verify_csv("mc_ST_raw.csv", SHA_ST_RAW)
df_sn = verify_csv("mc_SN_raw.csv", SHA_SN_RAW)

# Seeds from SeedSequence(20261104)
ss     = np.random.SeedSequence(20261104)
seeds  = ss.spawn(2)   # child 0 = ST, child 1 = SN
seed_st = int(seeds[0].generate_state(1)[0])
seed_sn = int(seeds[1].generate_state(1)[0])
print(f"\n  SeedSequence(20261104): ST seed={seed_st}, SN seed={seed_sn}")

results = {}

for branch, df, seed in [("ST", df_st, seed_st), ("SN", df_sn, seed_sn)]:
    rng     = np.random.default_rng(seed)
    k6_df   = compute_k6_per_draw(df)
    branch_res = {}
    print(f"\n  Branch {branch}:")
    print(f"  {'k':>6}  {'obs':>7}  {'lo':>7}  {'hi':>7}  draws")
    for k in KAPPAS:
        sub = k6_df[k6_df["kappa"] == k]["k6"].values
        if len(sub) == 0:
            print(f"  {k:>6}  WARNING: no data")
            continue
        obs, lo, hi = bstrap(sub, B_BOOT, rng)
        branch_res[str(k)] = {
            "obs": round(obs, 2),
            "lo":  round(lo,  2),
            "hi":  round(hi,  2),
        }
        print(f"  {k:>6}  {obs:>+7.2f}  {lo:>+7.2f}  {hi:>+7.2f}  n={len(sub)}")
    results[branch] = branch_res

out = {
    "description": (
        "Descriptive bootstrap CIs for Santiago K6 (Agg_pooled3). "
        "Computed after evaluation. No verdict depends on these CIs. "
        "Method: identical to run_e7_kappa_sweep.py bstrap() — "
        "percentile bootstrap B=2000, resample draws with replacement."
    ),
    "source_script": "scripts/santiago_k6_ci.py",
    "method": "percentile bootstrap, B=2000, resample draws (same as Fogo E7)",
    "cells": ["SAW_mm_grd-TOPSIS_mm_grd", "SAW_vec_grd-TOPSIS_vec_grd",
              "SAW_vec_opt-TOPSIS_vec_opt"],
    "seed_sequence": "numpy.random.SeedSequence(20261104)",
    "sealed_csv_shas": {"mc_ST_raw.csv": SHA_ST_RAW, "mc_SN_raw.csv": SHA_SN_RAW},
    "results": results,
}

out_path = SEALED / "santiago_k6_ci.json"
out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
sha_out = hashlib.sha256(out_path.read_bytes()).hexdigest()
print(f"\n  Written: {out_path}")
print(f"  SHA-256: {sha_out}")
print(f"  SHA[:16]: {sha_out[:16]}")
