"""append_summary.py — one-shot: append final summary block to check_consistency.py"""
from pathlib import Path

p = Path(__file__).parent / "check_consistency.py"
text = p.read_text(encoding="utf-8")

ADDITION = """
# ─────────────────────────────────────────────────────────────────────────────
# FINAL SUMMARY — must be the last output line
# ─────────────────────────────────────────────────────────────────────────────
print()
if FAIL:
    print(f"FAILED: {len(FAIL)} check(s):")
    for msg in FAIL:
        print(f"  x {msg}")
    sys.exit(1)
else:
    print(f"ALL CHECKS PASSED (0 failures)")
    sys.exit(0)
"""

p.write_text(text.rstrip() + "\n" + ADDITION, encoding="utf-8", newline="\n")
print(f"done — {len(p.read_text(encoding='utf-8').splitlines())} lines")
