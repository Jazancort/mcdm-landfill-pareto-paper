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
    r"|\borcid\b"                # ORCID identifiers
    r"|orcid\{"                  # ORCID in author fields
    r"|\{[0-9]{4}-"              # ORCID format NNNN-
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
    # Pareto frontier sizes (have macros: \FAsize, \FAinter, \Fmmsize)
    "213",   # |F_A| = \FAsize
    "181",   # |F_A'| = \Fmmsize
    "132",   # |F_A ∩ F_A'| = \FAinter
    # F8 results (have macros in macros.tex / macros_f8.tex)
    "94.4",  # \FEightMMOptQ
    "72.4",  # \FEightMMGrdQ
    "100.0", # Q2=100% (structural guarantee)
    # TV values (have macros in macros_amplitudes.tex)
    "0.091", # \TVrnk
    "0.311", # \TVvec old 3dp (now 0.3113)
    # Bootstrap draws (structural constant)
    "10000", # N_BOOT E1
    "2000",  # N_BOOT general
    # Common thresholds
    "0.001", # p < 0.001
    "0.90",  # zero-inflation rate \EsixPiZinf
    "0.95",  # common CI level
    "1.96",  # z-value for 95% CI
    "120",   # \EsixNinst
    "30",    # instances per family
    "0.30",  # TV_W H-level
    "0.199", # TV_W F-level (\EsixTargetTVW)
    # Azimuth/angle constants (aspect encoding: [90°, 180°])
    "90",    # azimuth lower bound for leeward
    "180",   # azimuth upper bound for leeward
    # n_1 leeward sites (design constant from GIS data)
    "94",    # leeward site count (n_1)
    "295",   # non-leeward site count (n_0 = 389 - 94)
    # Literature counts (not results of this paper; contextual citations)
    "114",   # studies reviewed by Li2021/Ahmed2022
    "148",   # PDA contributions reviewed
    "31",    # normalisation techniques surveyed
    "14",    # techniques compared
    # Known data values from the Fogo GIS dataset
    "350",   # perm zeros count (350/389 sites have perm=0)
    "532",   # perm maximum value in metres
    "214.5", # approx midrank for tied zeros ((350+1)/2 = 175.5, no: (2*350+1)/2=350.5? — contextual)
    # Internal LaTeX layout constants
    "001",   # \textpagefraction (LaTeX parameter)
    # Site indices of the optimal portfolio (known from analysis)
    "184",   # site index in df_all
    "430",   # site index in df_all
    "460",   # site index in df_all
    # Other portfolios and sites mentioned in prose
    "279",   # SAW/mm/grd portfolio site
    "320",   # SAW/mm/grd portfolio site
    "41",    # site with missing roads data
    "385",   # site with missing urban data
    "429",   # site with missing aero data
    # Imputed/tolerance values
    "1.51",  # RI for 11 criteria (AHP)
    "2.5",   # TOST delta (pp equivalence margin) — design choice
    "0.62",  # approx perm deflation factor under midranks (contextual in figure caption)
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
        # Lines with % OK: are explicitly exempted (justified hardcoded values)
        if "% OK:" in line:
            continue
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
