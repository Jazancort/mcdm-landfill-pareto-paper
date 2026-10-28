# -*- coding: utf-8 -*-
"""
diag_rho_definition.py
======================
Determines which of two vec normalisation definitions matches Tabela 2.

  rho_raw   = range(x) / L2(x)           -- standard TOPSIS formula
  rho_shift = range(x) / L2(x - min(x))  -- code formula (= 1/L2(mm_norm(x)))

For each criterion: prints xmin (raw metres or binary), both rho values
rounded to 3dp, Tabela 2 value, and which formula matches.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

from mcdm_experiment import load_data, impute_nan, COL, AHP_WEIGHTS
from fogo_constants import AJ_VEC, CRITERION_NAMES

TABLE2 = dict(zip(CRITERION_NAMES, AJ_VEC))
col_names = list(AHP_WEIGHTS.keys())

print("Loading data...")
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL['protected']] > 0].copy()

rows = []
for k in col_names:
    x_raw = df_via[COL[k]].to_numpy(float)
    if k == "aspect":
        x = ((x_raw >= 90) & (x_raw <= 180)).astype(float)
        x_raw_display = x   # aspect is binary in both formulas
    else:
        x = x_raw.copy()

    x_min  = x.min()
    x_max  = x.max()
    x_range = x_max - x_min

    # rho_raw:   standard TOPSIS -- normalise by L2 of the raw column
    rho_raw   = x_range / np.linalg.norm(x) if np.linalg.norm(x) > 0 else 0.0

    # rho_shift: code formula -- normalise by L2 of (x - min)
    x_shifted = x - x_min
    rho_shift = x_range / np.linalg.norm(x_shifted) if np.linalg.norm(x_shifted) > 0 else 0.0

    tab2  = TABLE2[k]
    eq_raw   = abs(round(rho_raw,   3) - tab2) < 5e-4
    eq_shift = abs(round(rho_shift, 3) - tab2) < 5e-4

    rows.append(dict(
        crit       = k,
        xmin_raw   = round(float(x_min),  3),
        rho_raw    = round(rho_raw,   4),
        rho_shift  = round(rho_shift, 4),
        tab2       = tab2,
        eq_raw     = eq_raw,
        eq_shift   = eq_shift,
    ))

df_out = pd.DataFrame(rows)
print()
print(f"{'Criterion':12s}  {'xmin':>10}  {'rho_raw':>9}  {'rho_shift':>9}  {'Tab2':>6}  "
      f"{'raw==Tab2':>9}  {'shift==Tab2':>11}")
print("-" * 80)
for r in rows:
    marker = ""
    if r["eq_raw"] and not r["eq_shift"]:
        marker = "<-- raw"
    elif r["eq_shift"] and not r["eq_raw"]:
        marker = "<-- shift"
    elif r["eq_raw"] and r["eq_shift"]:
        marker = "<-- both"
    else:
        marker = "NEITHER"
    print(f"  {r['crit']:12s}  {r['xmin_raw']:10.3f}  {r['rho_raw']:9.4f}  "
          f"{r['rho_shift']:9.4f}  {r['tab2']:6.3f}  "
          f"{'YES':>9}  {'YES':>11}  {marker}" if (r["eq_raw"] and r["eq_shift"]) else
          f"  {r['crit']:12s}  {r['xmin_raw']:10.3f}  {r['rho_raw']:9.4f}  "
          f"{r['rho_shift']:9.4f}  {r['tab2']:6.3f}  "
          f"{'YES' if r['eq_raw'] else 'NO':>9}  "
          f"{'YES' if r['eq_shift'] else 'NO':>11}  {marker}")

print()
n_raw_match   = sum(1 for r in rows if r["eq_raw"])
n_shift_match = sum(1 for r in rows if r["eq_shift"])
print(f"Tabela 2 matches rho_raw   (to 3dp): {n_raw_match}/11")
print(f"Tabela 2 matches rho_shift (to 3dp): {n_shift_match}/11")

# Show protected specifically
r_prot = next(r for r in rows if r["crit"] == "protected")
print(f"\nprotected: xmin={r_prot['xmin_raw']}  rho_raw={r_prot['rho_raw']:.6f}  "
      f"rho_shift={r_prot['rho_shift']:.6f}  tab2={r_prot['tab2']}")
if abs(r_prot['xmin_raw']) < 0.01:
    print("  => protected xmin ~= 0 in mm-norm space; raw column min > 0 is expected")
    # Show actual raw min
    x_prot_raw = df_via[COL['protected']].to_numpy(float)
    print(f"  => protected raw (metres) min = {x_prot_raw.min():.1f}  "
          f"L2(x_raw)={np.linalg.norm(x_prot_raw):.1f}  "
          f"L2(x-min)={np.linalg.norm(x_prot_raw - x_prot_raw.min()):.1f}")
    rho_raw_metres  = (x_prot_raw.max()-x_prot_raw.min()) / np.linalg.norm(x_prot_raw)
    rho_shift_metres = (x_prot_raw.max()-x_prot_raw.min()) / np.linalg.norm(x_prot_raw - x_prot_raw.min())
    print(f"  => rho from RAW metres: raw={rho_raw_metres:.4f}  shift={rho_shift_metres:.4f}  tab2={r_prot['tab2']}")
