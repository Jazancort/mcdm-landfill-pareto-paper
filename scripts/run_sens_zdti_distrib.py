# -*- coding: utf-8 -*-
"""run_sens_zdti_distrib.py — SENS-ZDTI-DISTRIB: Stage 4 S-N with within-Group-A redistribution.

Declared in: corpus/deviations/DEV-SANT-ZDTI-001.md §SENS-ZDTI-DISTRIB (2026-11-03)
Status:      POST-DATA sensitivity (S-N results sealed 2026-10-28); descriptive only.

Repeats Stage 4 S-N with W0_DISTRIB: A2 weight redistributed proportionally among
the 6 remaining Group A criteria (A1, A3, A4, A5, A6, A7), preserving Cabral group
weights for B, C, D.

Scale factor = 0.208 / (0.208 - 0.0314) = 1.17780

Output: results/santiago/sens_zdti_distrib.csv  (same schema as mc_SN_raw.csv)

Run on Athena:
    cd ~/scratch/mcdm-landfill-pareto-paper
    uv run python scripts/run_sens_zdti_distrib.py
"""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

# ─────────────────────────────────────────────────────────────────────────────
# §1  W0_DISTRIB (DEV-SANT-ZDTI-001.md, fixed 2026-11-03)
# ─────────────────────────────────────────────────────────────────────────────
# Order: A1, A3, A4, A5, A6, A7, B1, B2, B3, C1, C2, D1, D2
W0_DISTRIB_RAW = np.array([
    0.04535, 0.03086, 0.04535, 0.01861, 0.03698, 0.03086,
    0.20300, 0.10150, 0.10150,
    0.07350, 0.02450,
    0.09500, 0.19300,
], dtype=float)
W0_DISTRIB = W0_DISTRIB_RAW / W0_DISTRIB_RAW.sum()

assert abs(W0_DISTRIB.sum() - 1.0) < 1e-6, f"W0_DISTRIB sum={W0_DISTRIB.sum()}"
print(f"W0_DISTRIB sum = {W0_DISTRIB.sum():.8f}  (OK)")
print(f"Group A = {W0_DISTRIB[:6].sum():.5f}  (expected 0.20800)")
print(f"Group B = {W0_DISTRIB[6:9].sum():.5f}  (expected 0.40600)")
print(f"Group C = {W0_DISTRIB[9:11].sum():.5f}  (expected 0.09800)")
print(f"Group D = {W0_DISTRIB[11:].sum():.5f}  (expected 0.28800)")

# ─────────────────────────────────────────────────────────────────────────────
# §2  Patch run_santiago_mc: W0, RESULTS dir, output paths
# ─────────────────────────────────────────────────────────────────────────────
import run_santiago_mc as rmc

# Use a separate checkpoint dir so original mc_SN_k*.npz are not overwritten
SENS_DIR = rmc.RESULTS / "sens_zdti"
SENS_DIR.mkdir(exist_ok=True)

# Override W0 and RESULTS before run_branch is called
rmc.SN_W0 = W0_DISTRIB
rmc.BRANCH_CONFIG["SN"]["w0"] = W0_DISTRIB
rmc.RESULTS = SENS_DIR  # checkpoints go here

print("\n" + "=" * 70)
print("SENS-ZDTI-DISTRIB — Stage 4 S-N with W0_DISTRIB")
print("=" * 70)
print(f"Checkpoint dir: {SENS_DIR}")
print(f"Output CSV:     results/santiago/sens_zdti_distrib.csv")
print()

rmc.run_branch("SN")

# ─────────────────────────────────────────────────────────────────────────────
# §3  Move/copy output CSV to canonical location
# ─────────────────────────────────────────────────────────────────────────────
import shutil

src = SENS_DIR / "mc_SN_raw.csv"
dst = ROOT / "results" / "santiago" / "sens_zdti_distrib.csv"

if src.exists():
    shutil.copy2(src, dst)
    import hashlib, pandas as pd
    sha = hashlib.sha256(dst.read_bytes()).hexdigest()[:16]
    n = len(pd.read_csv(dst))
    print("\n" + "=" * 70)
    print(f"DONE: sens_zdti_distrib.csv  ({n} rows, SHA={sha})")
    print("=" * 70)
else:
    print("\nERROR: mc_SN_raw.csv not found in sens_zdti dir")
    sys.exit(1)
