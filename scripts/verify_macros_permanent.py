#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
verify_macros_permanent.py
--------------------------
Permanent provenance audit for primary quantitative claims in macros.tex.

Reads mc_2cube_fixed_raw.csv (alpha=200, 8 unique combinations, 500 draws each),
asserts uniqueness (no pivot_table aggregation that could mask duplicates),
and computes NormMainEffect and NormGreedyContrast with explicit half-up rounding.

Rounding policy: ROUND_HALF_UP to 1 decimal place (Decimal module, prec=28).
Source file: results/fourthcell/mc_2cube_fixed_raw.csv
File hash (SHA-256 first 16 hex): ea5dfe07d12bd5ff

Also verifies TV_B_VEC / TV_W_VEC via AJ_VEC+W+formula,
and reports E1 per-draw claim from log.

Exit 0 = ALL PASS, exit 1 = any FAIL.
"""
import sys
import hashlib
import os
import numpy as np
from decimal import Decimal, getcontext, ROUND_HALF_UP

getcontext().prec = 28
ROUND1 = Decimal('0.1')

# ---------------------------------------------------------------------------
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUBE_PATH = os.path.join(REPO, 'results', 'fourthcell', 'mc_2cube_fixed_raw.csv')
E1_LOG    = os.path.join(REPO, 'data', 'e1_v3_rerun_20261002.log')
EXPECTED_HASH = 'ea5dfe07d12bd5ff'   # SHA-256[:16] of mc_2cube_fixed_raw.csv

# Macros to verify (as strings, exactly as rendered in macros.tex)
MACRO_STRINGS = {
    'NormMainEffect':     '34.6',
    'NormGreedyContrast': '25.4',
    'QtwovecGreedy':      '66.2',
    'QtwovecOptimal':     '56.8',
    'QtwommGreedy':       '86.0',
    'QtwommOptimal':      '100.0',
    'EoneWloss':          '35.8',
    'EoneVloss':          '43.2',
}

FAIL = []

def check(name, computed_raw, macro_str, formula=''):
    """Compare computed (float) against macro string after half-up rounding."""
    d = Decimal(str(computed_raw)).quantize(ROUND1, rounding=ROUND_HALF_UP)
    rendered = str(d)
    ok = (rendered == macro_str)
    status = 'OK  ' if ok else 'FAIL'
    print(f'  [{status}] {name}:')
    print(f'         computed_raw={computed_raw:.10f}')
    print(f'         rounded={rendered}  macro={macro_str}  match={ok}')
    if formula:
        print(f'         formula: {formula}')
    if not ok:
        FAIL.append(f'{name}: computed={rendered} != macro={macro_str}')

# ---------------------------------------------------------------------------
print('=' * 60)
print('verify_macros_permanent.py')
print('=' * 60)

# Step 1: File hash
with open(CUBE_PATH, 'rb') as f:
    actual_hash = hashlib.sha256(f.read()).hexdigest()[:16]
print(f'\n[hash] mc_2cube_fixed_raw.csv: {actual_hash}')
if actual_hash != EXPECTED_HASH:
    FAIL.append(f'file_hash mismatch: got {actual_hash}, expected {EXPECTED_HASH}')
    print(f'  [FAIL] hash mismatch — wrong file?')
else:
    print(f'  [OK  ] hash matches')

# Step 2: Load and assert uniqueness WITHOUT pivot_table
import pandas as pd
df = pd.read_csv(CUBE_PATH)
df200 = df[df['alpha'] == 200].copy()

# Assert 8 combinations, no duplicates, 500 draws each
groups = df200.groupby(['agg', 'norm', 'mont'])
n_combos = len(groups)
if n_combos != 8:
    FAIL.append(f'expected 8 combos, got {n_combos}')
    print(f'  [FAIL] {n_combos} combos, expected 8')
else:
    print(f'  [OK  ] 8 combinations present')

sizes = groups.size()
if (sizes != 500).any():
    FAIL.append(f'some cells have != 500 draws: {sizes[sizes!=500].to_dict()}')
else:
    print(f'  [OK  ] 500 draws per cell')

# Assert no duplicate (draw, agg, norm, mont)
dup_check = df200.groupby(['draw', 'agg', 'norm', 'mont']).size()
if (dup_check > 1).any():
    FAIL.append('duplicates detected in (draw, agg, norm, mont)')
    print('  [FAIL] duplicates found')
else:
    print('  [OK  ] no duplicates')

# Step 3: Compute contrasts WITHOUT pivot_table — use direct groupby mean
cell_means = (df200.groupby(['agg', 'norm', 'mont'])['nd_Q2Ap']
              .mean()
              .reset_index()
              .rename(columns={'nd_Q2Ap': 'mean_q2'}))
cell_means['mean_pct'] = cell_means['mean_q2'] * 100.0

def cell(agg, norm, mont):
    row = cell_means[
        (cell_means['agg'].astype(str) == agg) &
        (cell_means['norm'].astype(str) == norm) &
        (cell_means['mont'].astype(str) == mont)
    ]
    assert len(row) == 1, f'cell ({agg},{norm},{mont}) not found'
    return float(row['mean_pct'].iloc[0])

print('\n--- 8 cell means (%, 10 dp) ---')
for _, r in cell_means.iterrows():
    print(f"  {str(r['agg']):6s}/{str(r['norm']):6s}/{str(r['mont']):7s}  {float(r['mean_pct']):.10f}")

# Step 4: Verify per-draw paired contrasts (no bootstrap needed for point estimate)
# C1: full factorial norm contrast (mean of paired differences across all draws)
# Use per-draw subtraction to get paired contrast, then mean
df200_mm  = df200[df200.norm=='minmax'].set_index(['draw','agg','mont'])['nd_Q2Ap']
df200_vec = df200[df200.norm=='vector'].set_index(['draw','agg','mont'])['nd_Q2Ap']
paired_norm_full = (df200_mm - df200_vec).reset_index()['nd_Q2Ap']
NormMain_raw = float(paired_norm_full.mean()) * 100.0

# C6: greedy-only norm contrast
df200_mm_grd  = df200[(df200.norm=='minmax')&(df200.mont=='greedy')].set_index(['draw','agg'])['nd_Q2Ap']
df200_vec_grd = df200[(df200.norm=='vector')&(df200.mont=='greedy')].set_index(['draw','agg'])['nd_Q2Ap']
paired_norm_grd = (df200_mm_grd - df200_vec_grd).reset_index()['nd_Q2Ap']
NormGrd_raw = float(paired_norm_grd.mean()) * 100.0

print('\n--- Norm contrasts (paired, 10 dp) ---')
print(f'  NormMain (full factorial): {NormMain_raw:.10f} pp')
print(f'  NormGrd  (greedy only):    {NormGrd_raw:.10f} pp')
print(f'  n_pairs NormMain: {len(paired_norm_full)}  (expected 2000 = 4 cells x 500 draws)')
print(f'  n_pairs NormGrd:  {len(paired_norm_grd)}   (expected 1000 = 2 cells x 500 draws)')

# Step 5: Check QtwommGreedy etc. from cell means
Q_saw_mm_grd  = cell('saw',    'minmax', 'greedy')
Q_saw_mm_opt  = cell('saw',    'minmax', 'optimal')
Q_saw_vec_grd = cell('saw',    'vector', 'greedy')
Q_saw_vec_opt = cell('saw',    'vector', 'optimal')
Q_top_mm_grd  = cell('topsis', 'minmax', 'greedy')
Q_top_mm_opt  = cell('topsis', 'minmax', 'optimal')
Q_top_vec_grd = cell('topsis', 'vector', 'greedy')
Q_top_vec_opt = cell('topsis', 'vector', 'optimal')

# Cross-check with Decimal arithmetic (as GPT computed)
print('\n--- GPT Decimal cross-check ---')
vals = {k: Decimal(f'{v:.4f}') for k, v in [
    ('saw_mm_grd',  Q_saw_mm_grd),  ('saw_mm_opt',  Q_saw_mm_opt),
    ('saw_vec_grd', Q_saw_vec_grd), ('saw_vec_opt',  Q_saw_vec_opt),
    ('top_mm_grd',  Q_top_mm_grd),  ('top_mm_opt',   Q_top_mm_opt),
    ('top_vec_grd', Q_top_vec_grd), ('top_vec_opt',  Q_top_vec_opt),
]}
mm_overall  = (vals['saw_mm_grd']+vals['saw_mm_opt']+vals['top_mm_grd']+vals['top_mm_opt'])/Decimal(4)
vec_overall = (vals['saw_vec_grd']+vals['saw_vec_opt']+vals['top_vec_grd']+vals['top_vec_opt'])/Decimal(4)
diff_dec = mm_overall - vec_overall
diff_dec_rounded = diff_dec.quantize(ROUND1, rounding=ROUND_HALF_UP)
print(f'  mm_overall={mm_overall}  vec_overall={vec_overall}')
print(f'  diff={diff_dec}  rounded_half_up={diff_dec_rounded}  (macro=34.6)')

grd_diff_dec = ((vals['saw_mm_grd']+vals['top_mm_grd'])/Decimal(2) -
                (vals['saw_vec_grd']+vals['top_vec_grd'])/Decimal(2))
print(f'  greedy_diff={grd_diff_dec}  (macro=25.4)')

print('\n--- Macro verification ---')
check('NormMainEffect',     NormMain_raw, '34.6',
      'mean paired (minmax-vector) across all 4 agg/mont x 500 draws')
check('NormGreedyContrast', NormGrd_raw,  '25.4',
      'mean paired (minmax-vector) greedy only x 2 agg x 500 draws')
check('QtwovecGreedy',      Q_saw_vec_grd,'66.2', 'cell saw/vector/greedy mean%')
check('QtwovecOptimal',     Q_saw_vec_opt,'56.8', 'cell saw/vector/optimal mean%')
check('QtwommGreedy',       Q_saw_mm_grd, '86.0', 'cell saw/minmax/greedy mean%')
check('QtwommOptimal',      Q_saw_mm_opt, '100.0','cell saw/minmax/optimal mean%')

# Step 6: TV_B_VEC / TV_W_VEC from fogo_constants
sys.path.insert(0, os.path.join(REPO, 'scripts'))
import fogo_constants as fc
AJ = np.array(fc.AJ_VEC)
W  = np.array(fc.W)
groups_idx = fc.OBJ_GROUPS
denom = float(np.dot(W, AJ))
Weff = W * AJ / denom
TV   = 0.5 * float(np.sum(np.abs(Weff - W)))
TV_B = 0.5 * sum(abs(sum(Weff[j] for j in g) - sum(W[j] for j in g)) for g in groups_idx)
TV_W = 0.0
for g in groups_idx:
    Wg     = float(sum(W[j] for j in g))
    Wg_eff = float(sum(Weff[j] for j in g))
    if Wg > 0 and Wg_eff > 0:
        tv_wg = 0.5 * sum(abs(Weff[j]/Wg_eff - W[j]/Wg) for j in g)
        TV_W += Wg * tv_wg
arr_hash = hashlib.sha256(AJ.tobytes() + W.tobytes()).hexdigest()[:16]
print(f'\n--- TV_B/TV_W (source_hash AJ_VEC+W: {arr_hash}) ---')
print(f'  TV_B computed={TV_B:.10f}  stored={fc.TV_B_VEC}')
print(f'  TV_W computed={TV_W:.10f}  stored={fc.TV_W_VEC}')
ok_B = abs(TV_B - fc.TV_B_VEC) < 1e-4
ok_W = abs(TV_W - fc.TV_W_VEC) < 1e-4
print(f'  TV_B match={ok_B}  TV_W match={ok_W}')
if not (ok_B and ok_W):
    FAIL.append(f'TV_B/TV_W mismatch: B={TV_B:.6f} vs {fc.TV_B_VEC}, W={TV_W:.6f} vs {fc.TV_W_VEC}')

# Step 7: E1-W per-draw log (EoneWloss, EoneVloss)
print(f'\n--- E1 per-draw log ---')
if os.path.exists(E1_LOG):
    import re
    # Parse RESULT lines: "  RESULT: greedy=X.XX% (SE=Y.YY)  optimal=Z.ZZ% (SE=W.WW)"
    # We need the RESULT line for E1-W and E1-V blocks
    e1_results = {}
    current_cell = None
    with open(E1_LOG, encoding='utf-8') as f:
        for line in f:
            m_hdr = re.match(r'---\s*(E1-[WVBM]):', line)
            if m_hdr:
                current_cell = m_hdr.group(1)
            m_res = re.search(r'RESULT:\s*greedy=([\d.]+)%.*?optimal=([\d.]+)%.*?\(SE=([\d.]+)\)', line)
            if m_res and current_cell:
                e1_results[current_cell] = {
                    'greedy': float(m_res.group(1)),
                    'optimal': float(m_res.group(2)),
                    'se_opt': float(m_res.group(3)),
                }
    for cell_name in ['E1-W', 'E1-V', 'E1-B', 'E1-M']:
        if cell_name in e1_results:
            r = e1_results[cell_name]
            print(f'  {cell_name}: greedy={r["greedy"]:.4f}%  optimal={r["optimal"]:.10f}%  SE={r["se_opt"]}')
        else:
            print(f'  {cell_name}: NOT FOUND in log')
    if 'E1-W' in e1_results:
        ew_opt_raw  = e1_results['E1-W']['optimal']
        eone_w_loss = 100.0 - ew_opt_raw
        check('EoneWloss', eone_w_loss, '35.8',
              f'100 - E1-W/optimal={ew_opt_raw} from {os.path.basename(E1_LOG)}')
    else:
        FAIL.append('E1-W RESULT not found in log')
    if 'E1-V' in e1_results:
        ev_opt_raw  = e1_results['E1-V']['optimal']
        eone_v_loss = 100.0 - ev_opt_raw
        check('EoneVloss', eone_v_loss, '43.2',
              f'100 - E1-V/optimal={ev_opt_raw} from {os.path.basename(E1_LOG)}')
    else:
        FAIL.append('E1-V RESULT not found in log')
else:
    FAIL.append(f'E1 log not found: {E1_LOG}')
    print(f'  [FAIL] log not found')

# ---------------------------------------------------------------------------
print('\n' + '=' * 60)
if FAIL:
    print(f'FAILED: {len(FAIL)} check(s):')
    for f in FAIL:
        print(f'  x {f}')
    sys.exit(1)
else:
    print('ALL CHECKS PASSED')
    sys.exit(0)
