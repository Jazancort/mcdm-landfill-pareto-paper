# -*- coding: utf-8 -*-
"""check_inputs.py — Verify SHA-256 of non-versioned GIS input files.

The three input files live outside the repository (MCDM_DATA_DIR).
This script checks that the files exist and match the expected SHAs.
It is called by run_checks.py and exits 1 on any mismatch.

Usage:
    uv run python scripts/check_inputs.py
"""

import hashlib
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent

# ─────────────────────────────────────────────────────────────────────────────
# Expected SHAs (computed 2026-11-09 from local copies)
# ─────────────────────────────────────────────────────────────────────────────
INPUTS = [
    (
        "df_real_data_cached.csv",
        "234f6e1c2697ea540ed0e0674018e6446e9255b25009167cbb0c19c51311722a",
        "results_cache/df_real_data_cached.csv",
    ),
    (
        "exhaustive_search_pareto.csv",
        "ae4efe96d02ee50c6721dcfeaa59963002262c08c21ea59a30f9e4b582a9c311",
        "New code/results/results-2026-04-07_18-40-54/exhaustive_search_pareto.csv",
    ),
    (
        "best_compromise_sites.csv",
        "b736c0e46486abae1500d0772149bcf32abbf5177357fa568c749aa6ce7b384b",
        "New code/results/results-2026-04-07_18-40-54/best_compromise_sites.csv",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# Resolve MCDM_DATA_DIR
# ─────────────────────────────────────────────────────────────────────────────
_athena  = "/home/julioazancort/scratch/mcdm"
_windows = (
    "G:/Faculdade/Estudo/Doutorado/2025.1/"
    "Otimiza\u00e7\u00e3o Bioinspirada/Tentativa de dados via GIS"
)
data_dir = Path(os.environ.get("MCDM_DATA_DIR", _athena if Path(_athena).exists() else _windows))

print("=" * 72)
print("check_inputs.py — non-versioned GIS input SHA verification")
print("=" * 72)
print(f"  MCDM_DATA_DIR: {data_dir}")
print()

fails = 0
for name, sha_exp, rel in INPUTS:
    p = data_dir / rel
    if not p.exists():
        print(f"  [FAIL] NOT FOUND: {p}")
        fails += 1
        continue
    got = hashlib.sha256(p.read_bytes()).hexdigest()
    if got != sha_exp:
        print(f"  [FAIL] SHA mismatch: {name}")
        print(f"         expected {sha_exp}")
        print(f"         got      {got}")
        fails += 1
    else:
        print(f"  [OK  ] {name} ({sha_exp[:16]})")

print()
if fails:
    print(f"FAIL: {fails} input(s) missing or corrupted")
    sys.exit(1)
print("ALL INPUTS OK")
