# -*- coding: utf-8 -*-
"""run_checks.py — Orchestrate all make-check scripts and report a summary table.

Runs every checker even if one fails, then exits non-zero if any failed.
Called by the Makefile `check` target.

Usage:
    uv run python scripts/run_checks.py

Output: summary table (script, exit_code, n_FAIL, n_WARN) + final EXIT= line.
"""
import sys
import subprocess
import re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent

CHECKS = [
    # (label, args)
    ("make_santiago_macros",    ["scripts/make_santiago_macros.py"]),
    ("check_tab_amplitude",     ["scripts/check_tab_amplitude.py"]),
    ("generate_macros_r1",      ["scripts/generate_macros_r1.py"]),
    ("check_consistency",       ["scripts/check_consistency.py"]),
    ("verify_macros_permanent", ["scripts/verify_macros_permanent.py"]),
    ("verify_macros_santiago",  ["scripts/verify_macros_permanent.py", "--santiago"]),
    ("audit_numbers",           ["scripts/audit_numbers.py"]),
    ("check_macros_provenance", ["scripts/check_macros_provenance.py"]),
    ("check_tolerances",        ["scripts/check_tolerances.py"]),
    ("check_inputs",            ["scripts/check_inputs.py"]),
    ("check_seeds",             ["scripts/check_seeds.py"]),
]

SEP = "=" * 72

def count_markers(text, marker):
    return len(re.findall(rf"\[{marker}\s*\]", text))

results = []
any_failed = False

print(SEP)
print("run_checks.py — running all checkers")
print(SEP)

for label, args in CHECKS:
    cmd = [sys.executable, "-X", "utf8"] + [str(ROOT / a) for a in args]
    proc = subprocess.run(cmd, capture_output=False, text=True, cwd=str(ROOT))
    rc = proc.returncode
    # Re-run capturing output only for counting markers (already printed above)
    proc2 = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", cwd=str(ROOT))
    combined = proc2.stdout + proc2.stderr
    n_fail = count_markers(combined, "FAIL") + combined.count("[FAIL]")
    n_warn = count_markers(combined, "WARN") + combined.count("[WARN]")
    # deduplicate (the two patterns may overlap)
    n_fail = len(re.findall(r"\[FAIL[\s\]]*\]", combined))
    n_warn = len(re.findall(r"\[WARN[\s\]]*\]", combined))
    results.append((label, rc, n_fail, n_warn))
    if rc != 0:
        any_failed = True

print()
print(SEP)
print(f"{'Script':<30}  {'Exit':>4}  {'FAILs':>5}  {'WARNs':>5}")
print("-" * 52)
for label, rc, nf, nw in results:
    flag = "  <-- FAILED" if rc != 0 else ""
    print(f"{label:<30}  {rc:>4}  {nf:>5}  {nw:>5}{flag}")
print(SEP)

exit_code = 1 if any_failed else 0
print(f"EXIT={exit_code}")
sys.exit(exit_code)
