# -*- coding: utf-8 -*-
"""check_seeds.py — Verify seeds and B values in canonical scripts.

Reads SEED/B_BOOT/N_DRAWS constants from the canonical scripts and
checks them against the pre-registered values in PRESPEC.md.

Usage:
    uv run python scripts/check_seeds.py
"""

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent

# ─────────────────────────────────────────────────────────────────────────────
# Pre-registered canonical values (from PRESPEC.md and PRESPEC_SANTIAGO.md)
# ─────────────────────────────────────────────────────────────────────────────
# Each entry: script_name -> {constant_name: (regex_pattern, expected_int)}
# regex_pattern is matched against the full file text (re.M)
CANONICAL = {
    "mc_unified.py": {
        "SEED":    (r"^SEED\s*=\s*([\d_]+)",    42),
        "N_DRAWS": (r"^N_DRAWS\s*=\s*([\d_]+)", 500),
        "B_BOOT":  (r"^B_BOOT\s*=\s*([\d_]+)",  10_000),
    },
    "mc_2cube_fixed.py": {
        "SEED":    (r"^SEED\s*=\s*([\d_]+)",    42),
        "N_DRAWS": (r"^N_DRAWS\s*=\s*([\d_]+)", 500),
    },
    "run_e7_kappa_sweep.py": {
        "BASE_SEED": (r"^BASE_SEED\s*=\s*([\d_]+)", 100),
        "N_DRAWS":   (r"^N_DRAWS\s*=\s*([\d_]+)",   500),
        "B_BOOT":    (r"^B_BOOT\s*=\s*([\d_]+)",    2000),
    },
    "run_santiago_mc.py": {
        "N_DRAWS": (r"^N_DRAWS\s*=\s*([\d_]+)", 500),
        "B_BOOT":  (r"^B_BOOT\s*=\s*([\d_]+)",  2000),
    },
    "evaluate_santiago_predictions.py": {
        "BOOTSTRAP_SEED": (r"^BOOTSTRAP_SEED\s*=\s*([\d_]+)", 20261104),
        "B_BOOT":         (r"^B_BOOT\s*=\s*([\d_]+)",         2000),
    },
    # make_santiago_macros.py uses B_BOOT=2000 from evaluate_santiago_predictions.py
    # (no module-level constant; verified via the comment in the generated header)
}

SEED_PAT  = re.compile(r"^SEED\s*=\s*([\d_]+)", re.M)
DRAWS_PAT = re.compile(r"^N_DRAWS\s*=\s*([\d_]+)", re.M)
BOOT_PAT  = re.compile(r"^B_BOOT\s*=\s*([\d_]+)", re.M)


def _parse_int(s):
    """Parse Python integer literal (may contain underscores)."""
    return int(s.replace("_", ""))

print("=" * 72)
print("check_seeds.py — canonical seed/B verification")
print("=" * 72)
print()

SEP = "-" * 72

# ─────────────────────────────────────────────────────────────────────────────
# §1  Canonical scripts
# ─────────────────────────────────────────────────────────────────────────────
print("§1  Canonical scripts")
print(SEP)

fails = 0
for script, checks in CANONICAL.items():
    p = ROOT / "scripts" / script
    if not p.exists():
        print(f"  [WARN] {script}: not found (may be on Athena only)")
        continue
    text = p.read_text(encoding="utf-8", errors="replace")

    ok = True
    parts = []
    for key, (pat, expected) in checks.items():
        m = re.search(pat, text, re.M)
        got = _parse_int(m.group(1)) if m else None
        if got != expected:
            print(f"  [FAIL] {script}: {key}={got} (expected {expected})")
            fails += 1
            ok = False
        else:
            parts.append(f"{key}={got}")
    if ok:
        print(f"  [OK  ] {script}: {', '.join(parts)}")

print()

# ─────────────────────────────────────────────────────────────────────────────
# §2  Full seed table (informational)
# ─────────────────────────────────────────────────────────────────────────────
print("§2  Full seed table (all scripts with SEED/N_DRAWS/B_BOOT)")
print(SEP)
print(f"  {'Script':<45} {'SEED':>8} {'N_DRAWS':>8} {'B_BOOT':>8}")
print(f"  {'-'*45} {'-'*8} {'-'*8} {'-'*8}")

for f in sorted((ROOT / "scripts").glob("*.py")):
    text = f.read_text(encoding="utf-8", errors="replace")
    seed  = SEED_PAT.search(text)
    draws = DRAWS_PAT.search(text)
    boot  = BOOT_PAT.search(text)
    if seed or draws or boot:
        sv = seed.group(1)  if seed  else "-"
        dv = draws.group(1) if draws else "-"
        bv = boot.group(1)  if boot  else "-"
        print(f"  {f.name:<45} {sv:>8} {dv:>8} {bv:>8}")

print()
if fails:
    print(f"FAIL: {fails} seed mismatch(es)")
    sys.exit(1)
print("ALL SEEDS OK")
