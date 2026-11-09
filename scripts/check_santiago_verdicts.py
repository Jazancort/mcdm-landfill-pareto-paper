# -*- coding: utf-8 -*-
"""check_santiago_verdicts.py — Verify that LaTeX verdict macros match the JSON.

For each prediction S0–S7b in santiago_predictions_v2.json, checks that the
corresponding \\Sant{ST|SN}S*Result macro in macros_santiago.tex carries the
same verdict string.  Fails if any macro is missing or mismatched.

Usage:
    uv run python scripts/check_santiago_verdicts.py

Output: results/santiago/macros_santiago.tex  (read-only)
"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT      = Path(__file__).parent.parent
JSON_PATH = ROOT / "results" / "santiago" / "santiago_predictions_v2.json"
TEX_PATH  = ROOT / "results" / "santiago" / "macros_santiago.tex"

SHA_JSON  = "1fbc412b8ace6bdbd07d74f890f1460a2acdc268ce45ed59fc2a7900e520cf80"

SEP  = "=" * 72
SEP2 = "-" * 72

# Map prediction id → macro name suffix (Result macro = Sant{BR}{SUFFIX}Result)
PRED_SUFFIX = {
    "S0":  "Szero",
    "S1":  "Sone",
    "S2":  "Stwo",
    "S3a": "Sthreea",
    "S3b": "Sthreeb",
    "S5":  "Sfive",
    "S6":  "Ssix",
    "S7a": "Ssvna",
    "S7b": "Ssvnb",
}
# S4 is descriptive — no Result macro in the tex; skip.
SKIP = {"S4"}


def main():
    print(SEP)
    print("check_santiago_verdicts.py — JSON vs macro verdict check")
    print(SEP)

    # SHA-verify JSON
    if not JSON_PATH.exists():
        print(f"[FAIL] JSON not found: {JSON_PATH}")
        sys.exit(1)
    got = hashlib.sha256(JSON_PATH.read_bytes()).hexdigest()
    if got != SHA_JSON:
        print(f"[FAIL] SHA mismatch for santiago_predictions_v2.json")
        print(f"  expected {SHA_JSON}")
        print(f"  got      {got}")
        sys.exit(1)
    print(f"  SHA OK: santiago_predictions_v2.json ({SHA_JSON[:16]})")

    if not TEX_PATH.exists():
        print(f"[FAIL] macros_santiago.tex not found: {TEX_PATH}")
        sys.exit(1)

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    tex  = TEX_PATH.read_text(encoding="utf-8")

    # Parse all \newcommand{\...Result}{...} from the tex
    tex_macros = {}
    for m in re.finditer(r"\\newcommand\{\\(Sant(?:ST|SN)\w+Result)\}\{([^}]+)\}", tex):
        tex_macros[m.group(1)] = m.group(2)

    n_ok = n_fail = 0
    print()
    print(f"{'Prediction':<8}  {'Branch':<4}  {'Macro':<30}  {'JSON':<20}  {'Tex':<20}  Status")
    print(SEP2)

    for branch, br in [("S-T", "ST"), ("S-N", "SN")]:
        for pred in data[branch]["predictions"]:
            pid = pred["prediction"]
            if pid in SKIP:
                continue
            suffix = PRED_SUFFIX.get(pid)
            if suffix is None:
                continue
            macro_name = f"Sant{br}{suffix}Result"
            json_verdict = pred["result"]
            tex_verdict  = tex_macros.get(macro_name)
            if tex_verdict is None:
                status = "[FAIL] MISSING"
                n_fail += 1
            elif tex_verdict != json_verdict:
                status = "[FAIL] MISMATCH"
                n_fail += 1
            else:
                status = "OK"
                n_ok += 1
            print(f"{pid:<8}  {branch:<4}  {macro_name:<30}  {json_verdict:<20}  "
                  f"{tex_verdict or '(none)':<20}  {status}")

    print()
    print(SEP)
    if n_fail == 0:
        print(f"ALL VERDICTS MATCH ({n_ok} checks, 0 failures)")
    else:
        print(f"VERDICT CHECK FAILED: {n_fail} mismatch(es), {n_ok} OK")
    print(SEP)
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == "__main__":
    main()
