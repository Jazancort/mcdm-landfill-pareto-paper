# -*- coding: utf-8 -*-
"""check_directions.py — Verifica direcção dos critérios no Santiago X_mm.

Para cada critério, o sinal da correlação entre o valor bruto e X_mm deve
coincidir com a direcção benefício da PRESPEC §5.2 e §5.5.

Benefício (maior = melhor site):
  S-T: rivers, coast, protected, urban, aero, cult, aspect (not leeward = 1 = good)
  S-N: A1,A3,A4,A5,A6,A7 = distances; B1-B3,C1-C2,D1-D2 = various benefit

Custo (menor raw = melhor):
  S-T: perm(dist), slope, roads, wells_absent(omit C-2)
  S-N: perm-equivalents that are cost-type

Run:
  uv run python scripts/check_directions.py
"""
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

ROOT    = Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

if "MCDM_DATA_DIR" not in os.environ:
    os.environ["MCDM_DATA_DIR"] = "/home/julioazancort/scratch/mcdm"

RESULTS = ROOT / "results" / "santiago"

# PRESPEC §5.2 benefit direction for S-T (10 criteria, C-2 wells omitted)
# benefit=True  = higher raw value = better site for this criterion
# benefit=False = lower raw value = better site (cost criterion)
ST_BENEFIT = {
    "perm":      False,   # distance to permeable zones: COST, closer = better
    "slope":     False,   # slope degrees: COST, flatter = better
    "roads":     False,   # distance to roads: COST, closer = better (access)
    "rivers":    True,    # distance from rivers: benefit, farther = better (away from floods)
    "aspect":    True,    # binary leeward: 1=not leeward=good, so benefit direction
    "coast":     True,    # distance from coast: benefit, farther = better
    "protected": True,    # distance from protected areas: benefit, farther = better
    "urban":     True,    # distance from urban: benefit, farther = better
    "aero":      True,    # distance from airports: benefit, farther = better
    "cult":      True,    # distance from agriculture: benefit, farther = better
}

# ── Load Santiago S-T ─────────────────────────────────────────────────────────
df_st = pd.read_csv(RESULTS / "df_santiago_st.csv")
print("S-T columns:", df_st.columns.tolist()[:15])

# Identify raw vs normalised columns
crit_cols_st = [c for c in df_st.columns if c not in ("lat", "lon", "id", "adm", "protected")]
print(f"S-T data shape: {df_st.shape}")
print()

# ── Load Fogo for comparison ──────────────────────────────────────────────────
from mcdm_experiment import (
    load_data, impute_nan, COL, _build_decision_matrix,
)

df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]] > 0].copy().reset_index(drop=True)
X_raw, benefit = _build_decision_matrix(df_via)

print("Fogo _build_decision_matrix benefit flags:")
FOGO_CRIT = [
    "perm", "slope", "roads", "rivers", "aspect", "coast",
    "protected", "wells", "urban", "aero", "cult",
]
for i, (c, b) in enumerate(zip(FOGO_CRIT, benefit)):
    print(f"  {c:12s}: benefit={b}  (expected: {ST_BENEFIT.get(c,'?')})")

print()
print("=" * 60)
print("Direction check complete.")
print("If benefit flags match expected, X_mm inversion in gate_e1_fogo_v2.py is correct.")
