"""Verify SHA-256 of Stage 4 input files against committed expected values."""
import hashlib, sys
from pathlib import Path

PAPER = Path(__file__).parent.parent
EXPECTED = {
    "results/santiago/df_santiago_st.csv": "0980d076",
    "results/santiago/df_santiago_sn.csv": "65160166",
}

all_ok = True
for rel, exp in EXPECTED.items():
    f = PAPER / rel
    if not f.exists():
        print(f"MISSING: {rel}")
        all_ok = False
        continue
    actual = hashlib.sha256(f.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:8]
    ok = actual == exp
    print(f"{'OK' if ok else 'MISMATCH'}: {rel}  got={actual}  expected={exp}")
    if not ok:
        all_ok = False

sys.exit(0 if all_ok else 1)
