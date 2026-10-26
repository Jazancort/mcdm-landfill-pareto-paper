# -*- coding: utf-8 -*-
"""
generate_macros.py  --  Wrapper that runs all macro generators in dependency order.

Called by Makefile `macros` target. Each generator writes its own output file;
this script only orchestrates the order and exits 1 if any generator fails.

Order:
  1. generate_macros_amplitudes.py  -> macros_amplitudes.tex, amplitudes.json
  2. generate_macros_e1.py          -> results/e1/macros_e1.tex
  3. generate_macros_e6.py          -> macros_e6.tex
  4. generate_macros_f8.py          -> macros_f8.tex
  5. generate_macros_r1.py          -> results/r1/macros_r1.tex
  6. generate_macros_raw_sens.py    -> macros_raw_sens.tex

Run:
    uv run python scripts/generate_macros.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
PYTHON = sys.executable

GENERATORS = [
    "generate_macros_amplitudes.py",
    "generate_macros_e1.py",
    "generate_macros_e6.py",
    "generate_macros_f8.py",
    "generate_macros_r1.py",
    "generate_macros_raw_sens.py",
]

failed = []
for gen in GENERATORS:
    script = ROOT / "scripts" / gen
    if not script.exists():
        print(f"  [SKIP] {gen} not found")
        continue
    print(f"  [RUN ] {gen}")
    result = subprocess.run(
        [PYTHON, str(script)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  [FAIL] {gen}:")
        print(result.stdout[-500:] if result.stdout else "")
        print(result.stderr[-500:] if result.stderr else "")
        failed.append(gen)
    else:
        print(f"  [OK  ] {gen}")

if failed:
    print(f"\nFAILED: {len(failed)} generator(s): {failed}")
    sys.exit(1)
else:
    print(f"\nAll {len(GENERATORS)} generators ran successfully.")
