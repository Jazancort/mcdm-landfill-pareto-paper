# -*- coding: utf-8 -*-
"""
audit_hardcoded.py  --  Find hardcoded numeric results in .tex files.
Classifies numbers as DESIGN (known constants) or RESULT? (candidates for macros).
Run:
    uv run python scripts/audit_hardcoded.py
Exit code 0 = clean; 1 = candidates found.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

ALLOW = re.compile(
    r"(19|20)\d\d"          # years
    r"|Fig\.|Table|Eq\."
    r"|\\cite|\\ref|\\label|\\eqref|\\url"
    r"|\\hspace|\\vspace|\\textwidth|\\linewidth"
    r"|\bpt\b|\bcm\b|\bem\b|\bex\b"
    r"|\b[0-9]\.[0-9]{3,}\b"     # 4+ decimals (LaTeX spacing, tolerance constants)
    r"|0\.\d+\s*(cm|pt|em|ex)"
)

# Numbers to skip: known design constants and thresholds
DESIGN_EXACT = {
    "10",    # MIN_DIST_KM
    "11",    # M_CRIT
    "200",   # KAPPA
    "500",   # N_DRAWS
    "389",   # N_via
    "473",   # N_all
    "84",    # N_excluded
    "3",     # K portfolio
    "2",     # K=2 in some comparisons
    "50",    # kappa=50 robustness
    "0.5",   # VIKOR v
    "0.05",  # significance threshold (conventional)
    "0.10",  # CR threshold
    "95",    # confidence level %
    "100",   # 100% (proportion) and Q2 perfect
    "0.08",  # EsixPthreeInfPminFam threshold
}

NUM = re.compile(
    r"(?<![\\{}])"
    r"(?<!\w)"
    r"(\d+\.\d+|\d{2,}(?:\{,\}\d{3})*)"
    r"(?:\s*(?:pp|\\%|%|/\d+))?"
    r"(?!\w)"
)

rows = []
for fname in ["main.tex"] + list(ROOT.glob("supplementary*.tex")):
    fpath = ROOT / fname if not Path(fname).is_absolute() else Path(fname)
    if not fpath.exists():
        continue
    for i, line in enumerate(fpath.read_text(encoding="utf-8").splitlines(), 1):
        # Strip comments
        s = re.sub(r"(?<!\\)%.*", "", line)
        # Strip known command arguments
        s = re.sub(r"\\(ref|eqref|cite\w*|label|url|includegraphics|input)(\[[^\]]*\])?\{[^}]*\}", "", s)
        # Strip macro names (e.g. \newcommand{\Foo}{3.14} -- the 3.14 is the macro VALUE, OK)
        if r"\newcommand" in s or r"\providecommand" in s:
            continue
        for m in NUM.finditer(s):
            val_str = m.group(1).replace("{,}", "")
            ctx = s[max(0, m.start()-40): m.end()+40].strip()
            if ALLOW.search(ctx):
                continue
            kind = "DESIGN" if val_str in DESIGN_EXACT else "RESULT?"
            rows.append((str(fpath.name), i, m.group(0), kind, ctx[:80]))

n_result  = sum(r[3] == "RESULT?" for r in rows)
n_design  = sum(r[3] == "DESIGN"  for r in rows)

if rows:
    print(f"{'File':20s} {'Line':5s} {'Value':12s} {'Kind':8s}  Context")
    print("-" * 90)
    for fname, lno, val, kind, ctx in sorted(rows, key=lambda r: (r[3], r[0], r[1])):
        print(f"  {fname:18s} {lno:5d}  {val:12s} {kind:8s}  {ctx}")
    print()
print(f"Total: {n_result} RESULT? candidates, {n_design} DESIGN constants.")
sys.exit(1 if n_result > 0 else 0)
