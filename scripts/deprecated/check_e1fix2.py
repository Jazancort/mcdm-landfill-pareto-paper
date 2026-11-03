import hashlib
import pandas as pd
import sys
from pathlib import Path

FIX2   = Path('/home/julioazancort/scratch/e1fix2_run/results/santiago')
FIX1   = Path('/home/julioazancort/scratch/mcdm-landfill-pareto-paper/results/santiago')
SEALED = FIX1   # sealed = main repo results dir

def sha8(p):
    return hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()[:8]

# ── Gate 3: raw CSV SHA unchanged ────────────────────────────────────────────
print("=== Gate 3: raw CSV SHA (must match sealed) ===")
for branch in ["ST", "SN"]:
    fn = f"mc_{branch}_raw.csv"
    got    = sha8(FIX2 / fn)
    sealed = sha8(SEALED / fn)
    ok = got == sealed
    print(f"  {fn}: fix2={got}  sealed={sealed}  {'OK' if ok else 'FAIL'}")

# ── E1 values from e1fix2 ─────────────────────────────────────────────────────
for branch in ["ST", "SN"]:
    print(f"\n=== E1 corrected (E1-ABAR fix, {branch}, Q2_opt %) ===")
    df = pd.read_csv(FIX2 / f"mc_{branch}_e1.csv")
    print(df.groupby(['e1_cell', 'kappa'])['Q2_opt'].mean().mul(100).round(1).to_string())

# ── Compare E1-M, E1-B, E1-V to e1fix (E1-FRONT fix) ────────────────────────
print("\n=== Bit-exact comparison with e1fix (E1-M, E1-B, E1-V must match) ===")
for branch in ["ST", "SN"]:
    df2 = pd.read_csv(FIX2 / f"mc_{branch}_e1.csv")
    df1 = pd.read_csv(FIX1 / f"mc_{branch}_e1_fix.csv")
    for cell in ["M", "B", "V"]:
        a = df2[df2["e1_cell"] == cell]["Q2_opt"].values
        b = df1[df1["e1_cell"] == cell]["Q2_opt"].values
        if len(a) == len(b) and (a == b).all():
            print(f"  {branch} E1-{cell}: bit-exact OK ({len(a)} rows)")
        else:
            diff = int((a != b).sum()) if len(a) == len(b) else -1
            print(f"  {branch} E1-{cell}: MISMATCH ({diff} diffs)")
