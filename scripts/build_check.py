# -*- coding: utf-8 -*-
"""
build_check.py  --  Full build and consistency verification for the Fogo paper.

Regenerates all auto-generated macro files, verifies they are committed,
then runs all consistency and coding tests.

Run:
    uv run python scripts/build_check.py

Exit code 0 = ALL PASS. Exit code 1 = at least one step failed.

Steps:
  1. generate_macros_amplitudes.py  -> macros_amplitudes.tex + amplitudes.json
  2. generate_macros_e6.py          -> macros_e6.tex
  3. git diff --exit-code            -> verify no uncommitted changes in generated files
  4. check_consistency.py           -> all arithmetic and semantic checks
  5. test_coding_consistency.py     -> 4-path coding test at <=1e-12
  6. validate_core.py --quick       -> core numerical invariants (if available)
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def run(cmd, label=None):
    label = label or " ".join(str(c) for c in cmd)
    print(f"\n>> {label}")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"\nFAIL at: {label}")
        sys.exit(1)


if __name__ == "__main__":
    # Step 1: Regenerate amplitude macros
    run(["uv", "run", "python", "scripts/generate_macros_amplitudes.py"],
        "Regenerate macros_amplitudes.tex")

    # Step 2: Regenerate E6 macros
    run(["uv", "run", "python", "scripts/generate_macros_e6.py"],
        "Regenerate macros_e6.tex")

    # Step 3: Verify no uncommitted changes in generated files
    run(["git", "diff", "--exit-code",
         "macros_amplitudes.tex", "macros_e6.tex",
         "results/amplitudes/amplitudes.json"],
        "git diff --exit-code (generated files)")

    # Step 4: Consistency checks
    run(["uv", "run", "python", "scripts/check_consistency.py"],
        "check_consistency.py")

    # Step 5: Coding consistency
    run(["uv", "run", "python", "scripts/test_coding_consistency.py"],
        "test_coding_consistency.py")

    # Step 6: validate_core (if available)
    vc = ROOT / "scripts" / "validate_core.py"
    if vc.exists():
        run(["uv", "run", "python", str(vc)], "validate_core.py")
    else:
        print("\n[SKIP] validate_core.py not found")

    print("\n" + "=" * 50)
    print("BUILD CHECK: ALL PASS")
    print("=" * 50)
