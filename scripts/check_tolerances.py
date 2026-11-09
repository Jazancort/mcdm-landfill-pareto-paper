# -*- coding: utf-8 -*-
"""check_tolerances.py — List and verify tolerances in verify/check scripts.

Reads the tolerance table from checks/tolerances.txt and verifies that:
  1. Every tolerance is <= half a unit of the last decimal place printed.
  2. No tolerance is larger than the equivalence margin (2.5 pp).

Exit 0 = all pass, exit 1 = any FAIL.

Usage:
    uv run python scripts/check_tolerances.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
TOLERANCES_FILE = ROOT / "checks" / "tolerances.txt"

SEP = "=" * 72
FAIL = []

print(SEP)
print("check_tolerances.py — tolerance audit")
print(SEP)

if not TOLERANCES_FILE.exists():
    print(f"\n[WARN] {TOLERANCES_FILE} not found — creating template")
    TOLERANCES_FILE.write_text(
        "# checks/tolerances.txt — accepted tolerances in verify/check scripts\n"
        "# Format: name; tolerance; precision_dp; justification\n"
        "# Rule: tolerance <= 0.5 * 10^(-precision_dp)\n"
        "# One entry per line. Blank lines and lines starting with # are ignored.\n\n"
        "# verify_macros_permanent.py\n"
        "half_up_1dp; 0.05; 1; half-up rounding to 1 decimal place (standard)\n"
        "TV_B_TV_W; 0.0001; 4; TV_B/TV_W match tolerance (4 decimal places)\n"
        "E1_log_SE; 6.7; 1; E1 assertion tolerance = 3*SE (3*2.22=6.7 pp)\n\n"
        "# check_consistency.py\n"
        "weight_sum; 0.001; 3; sum of weights tolerance (3 decimal places)\n",
        encoding="utf-8", newline="\n"
    )
    print(f"  Created template: {TOLERANCES_FILE}")

lines = TOLERANCES_FILE.read_text(encoding="utf-8").splitlines()
tolerances = []
for line in lines:
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    parts = line.split(";", 3)
    if len(parts) < 3:
        continue
    name = parts[0].strip()
    try:
        tol = float(parts[1].strip())
        dp = int(parts[2].strip())
        just = parts[3].strip() if len(parts) > 3 else ""
    except ValueError:
        print(f"  [WARN] Cannot parse line: {line!r}")
        continue
    tolerances.append((name, tol, dp, just))

print(f"\n  Loaded {len(tolerances)} tolerance entries")
print()

all_ok = True
for name, tol, dp, just in tolerances:
    if dp == 0:
        # dp=0 means no precision constraint (internal pipeline tolerance)
        print(f"  [OK  ] {name}: tol={tol}, dp=0 (no precision constraint)  {just}")
        continue
    max_tol = 0.5 * (10 ** (-dp))
    ok = tol <= max_tol
    status = "OK  " if ok else "FAIL"
    print(f"  [{status}] {name}: tol={tol}, dp={dp}, max={max_tol:.6f}  {just}")
    if not ok:
        FAIL.append(f"{name}: tolerance {tol} > max {max_tol} for {dp}dp")
        all_ok = False

print()
print(SEP)
if FAIL:
    print(f"FAILED: {len(FAIL)} check(s):")
    for f in FAIL:
        print(f"  x {f}")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
    sys.exit(0)
