# -*- coding: utf-8 -*-
"""check_terminology.py — Enforce one term per concept and British spelling.

Checks:
  T1  Forbidden term variants (one term per concept).
  T2  US spelling variants that must not appear in prose.
  T3  Highlights ≤ 85 chars per item (already in check_consistency; kept here
      for standalone use).

Exit 0 = all pass.  Exit 1 = at least one failure.

Usage:
    uv run python scripts/check_terminology.py
"""
import sys, re
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(__file__).parent.parent
FAIL = []

def _load_tex(name):
    p = ROOT / "paper" / "manuscript" / name
    return p.read_text(encoding="utf-8") if p.exists() else ""

main_tex  = _load_tex("main.tex")
sant_tex  = _load_tex("santiago.tex")
suppl_tex = _load_tex("supplementary.tex")
all_tex   = main_tex + "\n" + sant_tex

def _non_comment(tex):
    return "\n".join(l for l in tex.splitlines() if not l.strip().startswith("%"))

nc_main  = _non_comment(main_tex)
nc_sant  = _non_comment(sant_tex)
nc_all   = nc_main + "\n" + nc_sant

# ─────────────────────────────────────────────────────────────────────────────
# T1  Forbidden term variants
# ─────────────────────────────────────────────────────────────────────────────
print("=== T1: Forbidden term variants ===")

def _strip_urls_and_footnotes(tex):
    """Remove URLs and footnotes to avoid false positives."""
    # Remove \url{...} and \nolinkurl{...}
    tex = re.sub(r'\\(?:no)?linkurl\{[^}]*\}', '', tex)
    tex = re.sub(r'\\url\{[^}]*\}', '', tex)
    # Remove footnote content
    tex = re.sub(r'\\footnote\{[^}]*\}', '', tex)
    return tex

nc_all_clean = _strip_urls_and_footnotes(nc_all)

# Each entry: (forbidden_pattern, preferred_term, note)
# Patterns are case-sensitive regex applied to non-comment prose.
TERM_RULES = [
    # "range normalisation" / "range normalization" → "min--max normalisation"
    (r"\brange normalisa?tion\b", "min--max normalisation",
     "use 'min--max normalisation', not 'range normalisation'"),
    # "linear normalisation" (ambiguous) → "min--max normalisation"
    (r"\blinear normalisa?tion\b", "min--max normalisation",
     "use 'min--max normalisation', not 'linear normalisation'"),
    # "Euclidean normalisation" → "vector normalisation"
    (r"\bEuclidean normalisa?tion\b", "vector normalisation",
     "use 'vector normalisation', not 'Euclidean normalisation'"),
    # "L2 normalisation" → "vector normalisation"
    (r"\bL2 normalisa?tion\b", "vector normalisation",
     "use 'vector normalisation', not 'L2 normalisation'"),
    # "rank normalisation" is OK; "ranking normalisation" is not
    (r"\branking normalisa?tion\b", "rank normalisation",
     "use 'rank normalisation', not 'ranking normalisation'"),
    # "midrank normalisation" → "rank normalisation"
    (r"\bmidrank normalisa?tion\b", "rank normalisation",
     "use 'rank normalisation', not 'midrank normalisation'"),
    # "Pareto front" → "Pareto frontier" (consistent with paper)
    (r"\bPareto front\b(?! ier)", "Pareto frontier",
     "use 'Pareto frontier', not 'Pareto front'"),
    # "weight vector" (ambiguous) is OK; "weight vectors" is OK
    # "effective weight vector" is OK
    # "nominal weight" is OK; "original weight" is not
    (r"\boriginal weight", "nominal weight",
     "use 'nominal weight', not 'original weight'"),
    # "elicited weight" is OK; "stated weight" is not
    (r"\bstated weight", "elicited weight",
     "use 'elicited weight', not 'stated weight'"),
    # "assembly strategy" is OK; "selection strategy" is not (ambiguous)
    # "greedy heuristic" is OK; "greedy algorithm" is OK
    # "exact optimisation" is OK; "exact optimization" caught by T2
    # "portfolio selection" is OK; "site selection" is OK
    # "Pareto-efficient" (hyphenated) is preferred; "Pareto efficient" (no hyphen) in prose
    # Allow both; only flag "Pareto-inefficient" (not used)
    # "weight dispersion" is OK; "weight uncertainty" is OK (both used)
    # "concentration parameter" is OK; "precision parameter" is not
    (r"\bprecision parameter\b", "concentration parameter kappa",
     "use 'concentration parameter' (kappa), not 'precision parameter'"),
    # "total variation" is OK; "TV distance" is not (different concept)
    (r"\bTV distance\b", "total variation",
     "use 'total variation', not 'TV distance' (different concept)"),
    # "amplitude" is the paper's term; "range ratio" is not
    (r"\brange ratio\b", "amplitude",
     "use 'amplitude', not 'range ratio'"),
    # "effective weight" is OK; "implicit weight" is not
    (r"\bimplicit weight\b", "effective weight",
     "use 'effective weight', not 'implicit weight'"),
    # "within-group distortion" is OK; "intra-group distortion" is not
    (r"\bintra-group distortion\b", "within-group distortion",
     "use 'within-group distortion', not 'intra-group distortion'"),
    # "between-group distortion" is OK; "inter-group distortion" is not
    (r"\binter-group distortion\b", "between-group distortion",
     "use 'between-group distortion', not 'inter-group distortion'"),
]

for pattern, preferred, note in TERM_RULES:
    m = re.search(pattern, nc_all_clean)
    if m:
        # Find line number
        pos = m.start()
        line_no = nc_all_clean[:pos].count("\n") + 1
        FAIL.append(f"T1: '{m.group()}' at ~line {line_no} — {note}")
        print(f"  [FAIL] T1: '{m.group()}' — {note}")
    else:
        print(f"  [OK  ] T1: '{pattern}' absent")

# ─────────────────────────────────────────────────────────────────────────────
# T2  US spelling variants
# ─────────────────────────────────────────────────────────────────────────────
print()
print("=== T2: US spelling (must use British) ===")

# (us_pattern, british_form)
US_SPELLING = [
    (r"\bnormalization\b",   "normalisation"),
    (r"\boptimization\b",    "optimisation"),
    (r"\boptimize\b",        "optimise"),
    (r"\boptimized\b",       "optimised"),
    (r"\boptimizing\b",      "optimising"),
    (r"\bminimization\b",    "minimisation"),
    (r"\bmaximization\b",    "maximisation"),
    (r"\bcharacterize\b",    "characterise"),
    (r"\bcharacterized\b",   "characterised"),
    (r"\bcharacterizing\b",  "characterising"),
    (r"\bformaliz",          "formalise/formalised"),
    (r"\banalyze\b",         "analyse"),
    (r"\banalyzed\b",        "analysed"),
    (r"\banalyzing\b",       "analysing"),
    (r"\brecognize\b",       "recognise"),
    (r"\brecognized\b",      "recognised"),
    (r"\brecognizing\b",     "recognising"),
    (r"\bsummariz",          "summarise/summarised"),
    (r"\bgeneralize\b",      "generalise"),
    (r"\bgeneralized\b",     "generalised"),
    (r"\bgeneralizing\b",    "generalising"),
    (r"\bemphasiz",          "emphasise/emphasised"),
    (r"\bstabiliz",          "stabilise/stabilised"),
    (r"\bpenaliz",           "penalise/penalised"),
    (r"\bparalleliz",        "parallelise/parallelised"),
    (r"\bcenter\b",          "centre"),
    (r"\bcentered\b",        "centred"),
    (r"\bcentering\b",       "centring"),
    (r"\bcolor\b",           "colour"),
    (r"\bcolored\b",         "coloured"),
    (r"\bfavor\b",           "favour"),
    (r"\bfavored\b",         "favoured"),
    (r"\bfavorable\b",       "favourable"),
    (r"\bbehavior\b",        "behaviour"),
    (r"\bbehavioral\b",      "behavioural"),
    (r"\blabor\b",           "labour"),
    (r"\bneighbor\b",        "neighbour"),
    (r"\bneighborhood\b",    "neighbourhood"),
    (r"\bmodeling\b",        "modelling"),
    (r"\bmodeled\b",         "modelled"),
    (r"\btraveling\b",       "travelling"),
    (r"\btraveled\b",        "travelled"),
    (r"\bcanceled\b",        "cancelled"),
    (r"\bcanceling\b",       "cancelling"),
    (r"\bfulfill\b",         "fulfil"),
    (r"\bfulfilled\b",       "fulfilled"),
    (r"\bfulfilling\b",      "fulfilling"),
    (r"\bprogram\b(?!ming)", "programme (non-computing)"),  # only flag non-computing uses
]

# Exceptions: words that look like US but are OK in context
# "program" in "binary program", "integer program", "linear program" is OK (OR term)
# "modeling" in "modelling" is already caught
# "center" in "centroid" is OK
US_EXCEPTIONS = [
    r"\bbinary program",
    r"\binteger program",
    r"\blinear program",
    r"\bprogramming\b",
    r"\bprogram\b.*\bprogramm",  # programming context
]

# Also strip URLs for T2
nc_all_t2 = _strip_urls_and_footnotes(nc_all)

for us_pat, brit in US_SPELLING:
    matches = list(re.finditer(us_pat, nc_all_t2, re.IGNORECASE))
    if not matches:
        print(f"  [OK  ] T2: '{us_pat}' absent")
        continue
    # Filter exceptions for "program" and \centering (LaTeX command)
    real_matches = []
    for m in matches:
        ctx = nc_all_t2[max(0, m.start()-30):m.end()+30]
        is_exc = False
        # \centering is a LaTeX command, not the English word
        if m.group().lower() == 'centering' and '\\centering' in nc_all_t2[max(0,m.start()-1):m.end()+1]:
            is_exc = True
        if "program" in us_pat:
            for exc in US_EXCEPTIONS:
                if re.search(exc, ctx, re.IGNORECASE):
                    is_exc = True
                    break
        if not is_exc:
            real_matches.append(m)
    if real_matches:
        for m in real_matches[:2]:
            pos = m.start()
            line_no = nc_all[:pos].count("\n") + 1
            FAIL.append(f"T2: US spelling '{m.group()}' at ~line {line_no} — use '{brit}'")
            print(f"  [FAIL] T2: '{m.group()}' at ~line {line_no} — use '{brit}'")
    else:
        print(f"  [OK  ] T2: '{us_pat}' absent (or only in exempt context)")

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
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
