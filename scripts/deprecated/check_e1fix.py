import hashlib
import pandas as pd
import sys
from pathlib import Path

FIX    = Path('/home/julioazancort/scratch/e1fix_run/results/santiago')
SEALED = Path('/home/julioazancort/scratch/mcdm-landfill-pareto-paper/results/santiago')

def sha8(p):
    return hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()[:8]

print('=== Gate 3: raw CSV SHA ===')
st_fix    = sha8(FIX    / 'mc_ST_raw.csv')
sn_fix    = sha8(FIX    / 'mc_SN_raw.csv')
st_sealed = sha8(SEALED / 'mc_ST_raw.csv')
sn_sealed = sha8(SEALED / 'mc_SN_raw.csv')
ok_st = (st_fix == st_sealed)
ok_sn = (sn_fix == sn_sealed)
print(f'  mc_ST_raw.csv: fix={st_fix}  sealed={st_sealed}  {"OK" if ok_st else "FAIL"}')
print(f'  mc_SN_raw.csv: fix={sn_fix}  sealed={sn_sealed}  {"OK" if ok_sn else "FAIL"}')

print()
print('=== E1 corrected values (S-T, Q2_opt %) ===')
df = pd.read_csv(FIX / 'mc_ST_e1.csv')
print(df.groupby(['e1_cell', 'kappa'])['Q2_opt'].mean().mul(100).round(1).to_string())

print()
print('=== E1 corrected values (S-N, Q2_opt %) ===')
df2 = pd.read_csv(FIX / 'mc_SN_e1.csv')
print(df2.groupby(['e1_cell', 'kappa'])['Q2_opt'].mean().mul(100).round(1).to_string())

print()
if ok_st and ok_sn:
    print('GATE 3 PASS — main cells SHA unchanged by E1 fix')
else:
    print('GATE 3 FAIL')
    sys.exit(1)
