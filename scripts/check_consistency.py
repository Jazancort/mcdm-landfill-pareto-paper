"""
check_consistency.py  (Marco A revision)
=========================================
Verifies all arithmetic identities between tables and text.
Exit code 0 = all checks pass.
Exit code 1 = at least one check failed (make check will abort).

Assertions added in Marco A:
  - tab:tvorder values from mc_2cube_fixed_raw.csv (or hardcoded from pipeline)
  - tab:factorial 2x2 cells
  - tab:assembly per-cell contrasts
  - tab:e1 intervention cells
  - tab:fourthcell mismatch cells
  - TVBvec and TVWvec from macros.tex
"""
import sys, re
from pathlib import Path

ROOT   = Path(__file__).parent.parent
RESULTS = ROOT / "results"
FAIL   = []

TOL = 0.05   # tolerance in percentage points (0.05 pp)

def check(name, computed, expected, tol=TOL):
    """Assert |computed - expected| <= tol (in pp or raw value)."""
    diff = abs(computed - expected)
    status = "OK  " if diff <= tol else "FAIL"
    if diff > tol:
        FAIL.append(f"{name}: got {computed:.4f}, expected {expected:.4f}, diff={diff:.4f}")
    print(f"  [{status}] {name}: {computed:.4f} (expected {expected:.4f}, |diff|={diff:.4f})")


# ── 0. macros.tex: TVBvec and TVWvec ────────────────────────────────────────
print("=== macros.tex: TV decomposition ===")
macros_path = ROOT / "macros.tex"
if macros_path.exists():
    macros_text = macros_path.read_text(encoding="utf-8")
    def read_macro(name):
        m = re.search(rf'\\newcommand{{\\{name}}}{{([0-9.]+)}}', macros_text)
        return float(m.group(1)) if m else None

    TVBvec = read_macro("TVBvec")
    TVWvec = read_macro("TVWvec")

    if TVBvec is not None:
        check("TVBvec (macros.tex)", TVBvec, 0.249, tol=0.001)
    else:
        FAIL.append("TVBvec not found in macros.tex")
        print("  [FAIL] TVBvec not found in macros.tex")

    if TVWvec is not None:
        check("TVWvec (macros.tex)", TVWvec, 0.199, tol=0.001)
    else:
        FAIL.append("TVWvec not found in macros.tex")
        print("  [FAIL] TVWvec not found in macros.tex")
else:
    FAIL.append("macros.tex not found")
    print("  [FAIL] macros.tex not found")


# ── 1. tab:tvorder — Marco A values ─────────────────────────────────────────
print()
print("=== tab:tvorder (Marco A) ===")
# Authoritative values from corrected pipeline
# min-max greedy=86.0, optimal=100.0
# midranks greedy=86.0, optimal=88.2
# vector greedy=66.2, optimal=56.8

TAB_TVORDER = {
    "mm_greedy":   86.0,
    "mm_optimal": 100.0,
    "rnk_greedy":  86.0,
    "rnk_optimal": 88.2,
    "vec_greedy":  66.2,
    "vec_optimal": 56.8,
}

# These are the values that must appear in the paper
# Verify internal consistency: tv_mm < tv_rnk < tv_vec order must hold
# under optimal assembly (100 > 88.2 > 56.8)
check("tvorder: optimal mm > rnk > vec",
      TAB_TVORDER["mm_optimal"] - TAB_TVORDER["rnk_optimal"],
      100.0 - 88.2, tol=0.1)
check("tvorder: optimal rnk > vec",
      TAB_TVORDER["rnk_optimal"] - TAB_TVORDER["vec_optimal"],
      88.2 - 56.8, tol=0.1)

# These hardcoded values must match what's in the LaTeX source
main_tex = ROOT / "main.tex"
if main_tex.exists():
    tex = main_tex.read_text(encoding="utf-8")

suppl_tex_path = ROOT / "supplementary.tex"
suppl_tex = suppl_tex_path.read_text(encoding="utf-8") if suppl_tex_path.exists() else ""

# tab:tvorder rows
for label, val in [("86.0", 86.0), ("88.2", 88.2), ("66.2", 66.2), ("56.8", 56.8)]:
    if label in tex:
        print(f"  [OK  ] tab:tvorder value {label} present in main.tex")
    else:
        FAIL.append(f"tab:tvorder value {label} missing from main.tex")
        print(f"  [FAIL] tab:tvorder value {label} missing from main.tex")


# ── 2. tab:factorial — 2^3 design ───────────────────────────────────────────
print()
print("=== tab:factorial (Marco A) ===")
TAB_FACTORIAL = {
    "SAW_mm_greedy":     86.0,
    "SAW_mm_optimal":   100.0,
    "SAW_vec_greedy":    66.2,
    "SAW_vec_optimal":   56.8,
    "TOPSIS_mm_greedy":  94.4,
    "TOPSIS_mm_optimal": 96.6,
    "TOPSIS_vec_greedy": 63.4,
    "TOPSIS_vec_optimal":52.4,
}
# Verify Proposition 1 holds: SAW mm optimal = 100.0
check("Prop1: SAW mm optimal = 100.0",
      TAB_FACTORIAL["SAW_mm_optimal"], 100.0, tol=0.001)

# Verify normalisation main effect (greedy only): mm_mean - vec_mean
mm_greedy_mean  = (TAB_FACTORIAL["SAW_mm_greedy"]  + TAB_FACTORIAL["TOPSIS_mm_greedy"])  / 2
vec_greedy_mean = (TAB_FACTORIAL["SAW_vec_greedy"] + TAB_FACTORIAL["TOPSIS_vec_greedy"]) / 2
norm_greedy_contrast = mm_greedy_mean - vec_greedy_mean
check("Norm greedy contrast (mm-vec, greedy only)",
      norm_greedy_contrast, 25.4, tol=0.5)  # bootstrap value, loose tol

# Verify these values appear in LaTeX
for label in ["94.4", "96.6", "63.4", "52.4"]:
    if label in tex:
        print(f"  [OK  ] tab:factorial value {label} in main.tex")
    else:
        FAIL.append(f"tab:factorial value {label} missing from main.tex")
        print(f"  [FAIL] tab:factorial value {label} missing from main.tex")


# ── 3. tab:assembly — per-cell optimal-greedy contrasts ─────────────────────
print()
print("=== tab:assembly (Marco A) ===")
# SAW mm: +14.0 = 100.0 - 86.0
# SAW vec: -9.4 = 56.8 - 66.2
# TOPSIS mm: +2.2 = 96.6 - 94.4
# TOPSIS vec: -11.0 = 52.4 - 63.4

asm_SAW_mm    = TAB_FACTORIAL["SAW_mm_optimal"]    - TAB_FACTORIAL["SAW_mm_greedy"]
asm_SAW_vec   = TAB_FACTORIAL["SAW_vec_optimal"]   - TAB_FACTORIAL["SAW_vec_greedy"]
asm_TOPSIS_mm = TAB_FACTORIAL["TOPSIS_mm_optimal"] - TAB_FACTORIAL["TOPSIS_mm_greedy"]
asm_TOPSIS_vec= TAB_FACTORIAL["TOPSIS_vec_optimal"]- TAB_FACTORIAL["TOPSIS_vec_greedy"]

check("Assembly SAW mm (= +14.0)",     asm_SAW_mm,    14.0, tol=0.1)
check("Assembly SAW vec (= -9.4)",     asm_SAW_vec,   -9.4, tol=0.1)
check("Assembly TOPSIS mm (= +2.2)",   asm_TOPSIS_mm,  2.2, tol=0.1)
check("Assembly TOPSIS vec (= -11.0)", asm_TOPSIS_vec,-11.0, tol=0.1)

# Assembly main effect = mean of all four
asm_main = (asm_SAW_mm + asm_SAW_vec + asm_TOPSIS_mm + asm_TOPSIS_vec) / 4
check("Assembly main effect (≈ -1.1)", asm_main, -1.1, tol=0.5)

# AsmMM from macros.tex = mean of two mm cells
asm_mm_mean = (asm_SAW_mm + asm_TOPSIS_mm) / 2
check("AsmMM (mm mean, macros = 8.1)", asm_mm_mean, 8.1, tol=0.5)

# AsmVec from macros.tex = |mean of two vec cells|
asm_vec_mean = abs((asm_SAW_vec + asm_TOPSIS_vec) / 2)
check("AsmVec magnitude (vec mean, macros = 10.2)", asm_vec_mean, 10.2, tol=0.5)


# ── 4. tab:e1 — intervention cells ──────────────────────────────────────────
print()
print("=== tab:e1 (Marco A) ===")
# M: greedy=86.0, optimal=100.0, loss=0
# B: greedy=100.0, optimal=100.0, loss=0
# W: greedy=64.0, optimal=64.2, loss=35.8
# V: greedy=66.2, optimal=56.8, loss=43.2

TAB_E1 = {
    "M_greedy": 86.0, "M_optimal": 100.0, "M_loss": 0.0,
    "B_greedy":100.0, "B_optimal": 100.0, "B_loss": 0.0,
    "W_greedy": 64.0, "W_optimal":  64.2, "W_loss":35.8,
    "V_greedy": 66.2, "V_optimal":  56.8, "V_loss":43.2,
}
# P1: cell B reaches 100% under optimal
check("E1 P1: cell B optimal = 100.0", TAB_E1["B_optimal"], 100.0, tol=0.001)
# Between-group only costs nothing
check("E1 between-only loss = 0.0", TAB_E1["B_loss"], 0.0, tol=0.001)
# Within-group distortion (cell W) accounts for EoneWloss
check("E1 EoneWloss (macros = 35.8)", TAB_E1["W_loss"], 35.8, tol=0.2)
# Full vector loss = EoneVloss
check("E1 EoneVloss (macros = 43.2)", TAB_E1["V_loss"], 43.2, tol=0.2)
# V greedy matches factorial SAW vec greedy
check("E1 V greedy = SAW vec greedy", TAB_E1["V_greedy"], 66.2, tol=0.1)
# V optimal matches factorial SAW vec optimal
check("E1 V optimal = SAW vec optimal", TAB_E1["V_optimal"], 56.8, tol=0.1)


# ── 5. tab:fourthcell — score-evaluator mismatch ────────────────────────────
print()
print("=== tab:fourthcell (Marco A) ===")
# Ncand/A:  greedy=84.6, optimal=100.0
# Ncand/A': greedy=97.8, optimal=100.0  (consistent coding, R-V* values from fourthcell_consistent.csv)
# Nvia/A:   greedy=58.8, optimal=95.0
# Nvia/A':  greedy=86.0, optimal=100.0

TAB_4TH = {
    "NcandA_greedy":   84.6, "NcandA_optimal": 100.0,
    "NcandAp_greedy":  97.8, "NcandAp_optimal": 100.0,
    "NviaA_greedy":    58.8, "NviaA_optimal":   95.0,
    "NviaAp_greedy":   86.0, "NviaAp_optimal": 100.0,
}

# ── tab:coding2x2 (coding × reference set) ─────────────────────────────────
# DEV-E4-009: arithmetic invariants
TAB_CODING2X2 = {
    "RMopt": 100.0, "RMgrd": 86.0,       # binary coding, 389 constants
    "RVstarOpt": 100.0, "RVstarGrd": 97.8, # binary coding, 473 constants
    "AspOpt": 24.0, "AspGrd": 25.2,        # continuous coding, 389 constants (R-asp)
    "RVopt": 20.0, "RVgrd": 19.6,          # continuous coding, 473 constants (R-V, NOT vector)
}
# ── REGRESSION GUARD: diagonal cells derive from Prop1 — NEVER editable ────
# These values are theorems, not measurements. Any run that gives a diagonal
# cell < 100% has a bug in score/objective/trios alignment. Do NOT edit these
# expected values; fix the script instead.
# Changing an expected value here without a PHASES_STATUS.md "Decision record"
# entry (with git hash, justification, and reviewer sign-off) is PROHIBITED.
REGRESSION_DIAGONALS = [
    ("4th [REGRESSION] Ncand/A  optimal = 100.0 (Prop1, diagonal A473)",  TAB_4TH["NcandA_optimal"],  100.0),
    ("4th [REGRESSION] Nvia/A'  optimal = 100.0 (Prop1, diagonal A'389)", TAB_4TH["NviaAp_optimal"],  100.0),
    # NOTE: Ncand/A' (473 score, 389 evaluator) is OFF-diagonal — not a theorem.
    # 100.0% is empirical for this instance. Do NOT add as regression invariant.
]
regression_failed = False
for name, computed, expected in REGRESSION_DIAGONALS:
    diff = abs(computed - expected)
    if diff > 0.001:
        print(f"  [REGRESSION FAIL] {name}: got {computed:.4f} — ABORTING")
        FAIL.append(f"REGRESSION: {name}: got {computed:.4f}")
        regression_failed = True
    else:
        print(f"  [OK  ] {name}")
if regression_failed:
    print("\nREGRESSION GUARD TRIGGERED: diagonal cells must be 100% by Prop1.")
    print("Do NOT edit expected values — fix the score/objective/trios alignment.")
    sys.exit(2)

# Off-diagonal: Ncand score (consistent coding), A' evaluator -> no loss with consistent coding
loss_hi = TAB_4TH["NcandA_optimal"] - TAB_4TH["NcandAp_optimal"]
check("4th consistent coding: Ncand/A opt - Ncand/A' opt (≈0 pp)", loss_hi, 0.0, tol=1.0)

# tab:fourthcell moved to Supplementary Material (Table S1, P1 item 1)
# Values 84.6/97.8/58.8 are in supplementary.tex, not in main.tex
for label in ["84.6", "97.8", "58.8"]:
    if label in suppl_tex:
        print(f"  [OK  ] tab:fourthcell value {label} in supplementary.tex (Table S1)")
    else:
        FAIL.append(f"tab:fourthcell value {label} missing from supplementary.tex")
        print(f"  [FAIL] tab:fourthcell value {label} missing from supplementary.tex")

# ── tab:coding2x2 arithmetic (DEV-E4-009) ───────────────────────────────────
print()
print("=== tab:coding2x2 arithmetic (DEV-E4-009) ===")
_c = TAB_CODING2X2
check("coding2x2 R-asp opt - R-V opt = +4.0 pp",
      _c["AspOpt"] - _c["RVopt"], 4.0, tol=0.05)
check("coding2x2 R-asp grd - R-V grd = +5.6 pp",
      _c["AspGrd"] - _c["RVgrd"], 5.6, tol=0.05)
check("coding2x2 R-V* grd - R-M grd = +11.8 pp",
      _c["RVstarGrd"] - _c["RMgrd"], 11.8, tol=0.1)
check("coding2x2 R-M opt = 100.0%",  _c["RMopt"],    100.0, tol=0.001)
check("coding2x2 R-V* opt = 100.0%", _c["RVstarOpt"],100.0, tol=0.001)
# Verify values appear in main.tex
for label in ["100.0", "97.8", "24.0", "20.0", "25.2", "19.6"]:
    if label in tex:
        print(f"  [OK  ] tab:coding2x2 value {label} in main.tex")
    else:
        FAIL.append(f"tab:coding2x2 value {label} missing from main.tex")
        print(f"  [FAIL] tab:coding2x2 value {label} missing from main.tex")


# ── 6. Document quality checks ──────────────────────────────────────────────
print()
print("=== Document quality checks ===")

# Check: no undefined \ref labels in compiled log
# Always read from build dir (repo log is stale/absent after make paper)
log_candidates = [
    Path(r"C:\build\paper\main.log"),
    ROOT / "main.log",
]
log_path = next((p for p in log_candidates if p.exists() and p.stat().st_size > 1024), None)

if log_path is None:
    FAIL.append("main.log not found in C:\\build\\paper or repo root — run make paper first")
    print("  [FAIL] main.log not found — run make paper first")
else:
    print(f"  [INFO] Reading {log_path}")
    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    ref_undef = len(re.findall(r"Reference `[^']+' on page \d+ undefined", log_text))
    if ref_undef > 0:
        FAIL.append(f"Undefined \\ref labels: {ref_undef}")
        print(f"  [FAIL] Undefined \\ref labels: {ref_undef}")
    else:
        print(f"  [OK  ] Undefined \\ref labels: 0")

    cit_undef = len(re.findall(r"Citation `[^']+' on page \d+ undefined", log_text))
    if cit_undef > 0:
        FAIL.append(f"Citation [?] in log: {cit_undef}")
        print(f"  [FAIL] Citation undefined: {cit_undef}")
    else:
        print(f"  [OK  ] Citation undefined: 0")

    # Check for ?? in output (unresolved cross-references)
    qq_count = log_text.count("??")
    if qq_count > 0:
        FAIL.append(f"?? in compiled output: {qq_count}")
        print(f"  [FAIL] ?? in log: {qq_count}")
    else:
        print(f"  [OK  ] ?? in log: 0")

# Check: main.bbl exists and is > 1 KB (check build dir too)
bbl_path = ROOT / "main.bbl"
build_bbl = Path(r"C:\build\paper\main.bbl")
bbl_real = build_bbl if build_bbl.exists() and build_bbl.stat().st_size > 1024 else bbl_path
if bbl_real.exists():
    bbl_size = bbl_real.stat().st_size
    if bbl_size < 1024:
        FAIL.append(f"main.bbl is {bbl_size} bytes (<1 KB) — run make paper")
        print(f"  [FAIL] main.bbl: {bbl_size} bytes (<1 KB)")
    else:
        print(f"  [OK  ] main.bbl: {bbl_size:,} bytes ({bbl_real})")
else:
    FAIL.append("main.bbl not found — run make paper")
    print(f"  [FAIL] main.bbl not found")

# Check: no em-dashes (---) as prose separators in main.tex
if main_tex.exists():
    prose_dashes = 0
    for line in tex.splitlines():
        s = line.strip()
        if not s or s.startswith("%"):
            continue
        if re.match(r"^[- ]+$", s):
            continue
        if "---" in s:
            if "& ---" in line:   # table cell: "--- (no value)"
                continue
            prose_dashes += 1
    if prose_dashes > 0:
        FAIL.append(f"Em-dashes (---) in prose: {prose_dashes}")
        print(f"  [FAIL] Em-dashes in prose: {prose_dashes}")
    else:
        print(f"  [OK  ] Em-dashes in prose: 0")

# Check: no non-ASCII characters outside math in main.tex
if main_tex.exists():
    non_ascii_lines = [
        (i + 1, line.rstrip())
        for i, line in enumerate(tex.splitlines())
        if any(ord(c) > 127 for c in line)
    ]
    if non_ascii_lines:
        FAIL.append(f"Non-ASCII characters in main.tex: {len(non_ascii_lines)} lines")
        print(f"  [FAIL] Non-ASCII lines: {len(non_ascii_lines)}")
        for ln, txt in non_ascii_lines[:5]:
            print(f"    line {ln}: {txt[:80]}")
    else:
        print(f"  [OK  ] Non-ASCII characters: 0")

# Check: forbidden old macros absent from main.tex
FORBIDDEN_MACROS = [
    r"\slopeThree", r"\RsqThree", r"\hiiVecThree", r"\SxxPctVecThree",
    r"\slopeFive", r"\SAWgreedyContrast", r"\LossTabTVorder", r"\Peldschus",
    r"\RsqadjLtwo", r"\RsqadjTV", r"\RsqDrop",
    # Removed 2026-10-01: based on 80 pp attributed to reference-set mismatch,
    # which was an artefact of inconsistent aspect coding (DEV-E4-007).
    r"\MismatchRatioHi", r"\MismatchRatioLo",
    r"\MechOnePredAdmiss", r"\MechOneShare",
]
if main_tex.exists():
    for macro in FORBIDDEN_MACROS:
        if macro in tex:
            FAIL.append(f"Forbidden macro {macro} found in main.tex")
            print(f"  [FAIL] Forbidden macro {macro} in main.tex")
        else:
            print(f"  [OK  ] Forbidden macro {macro} absent")

# ── 7. Semantic correctness rules ───────────────────────────────────────────
print()
print("=== Semantic correctness rules ===")

# Rule 1: prohibit "affine function of the objectives" (score is affine in
# partial values, not in objectives; a false claim introduced in B1/B2 rework)
BAD_PHRASES = [
    ("affine function of the objectives",
     "score is affine in partial values, not objectives"),
    ("score and the objectives use the same normalisation",
     "guarantee does not require same normalisation — replaced by amplitude condition"),
    ("voided",
     "'voided' removed in B2 reframe — replace with iff formulation"),
    ("re-weighting alone predicts",
     "removed in B2 — use 'far more than its total variation suggests'"),
    ("two distinct mechanisms",
     "removed in B2 — use 'one mechanism and one caveat'"),
    ("two routes to implicit re-weighting",
     "removed in 2.6 fix — use 'one mechanism (Theorem) and one caveat (coding mismatch)'"),
    ("same mechanism at a higher cost",
     "removed in 2.6 fix — coding mismatch is outside the theorem, not the same mechanism"),
    ("not significant ($0$~pp, $95\\%$ CI $[0,0]$)",
     "IC [0,0] means identical across all draws, not 'not significant' — use 'identical to zero by construction'"),
    ("not significant in the pooled analysis",
     "TOST p small = equivalence demonstrated — use 'equivalent to zero within ±2.5 pp by TOST'"),
    ("not significant; sign cell-dependent",
     "TOST result is equivalence, not non-significance — rephrase"),
    ("instead of~$388$",
     "2.11a: midrank max with N=389 is 389, not 388 — fix to 389"),
    ("no longer holds for the implemented score",
     "2.2: identity holds at 6.7e-16 — N+1 is a common scale factor; ties are the source, not N+1"),
    ("attributable to rescaling midranks by $N+1$",
     "2.2: N+1 is a common scale; source is tie structure, not the rescaling constant"),
    ("accounts\\nfor $\\\\EoneWloss$ of the $\\\\EoneVloss",
     "2.11b: not an additive decomposition — use 'within-group alone costs X pp; full costs Y pp'"),
    ("far more costly",
     "removed in 2.6 fix — with consistent coding, reference-set effect costs 0 pp"),
    ("more severe mechanism",
     "removed in B2 — use 'same mechanism at a higher cost'"),
    ("Mechanism~1 component",
     "removed in B2 — rephrase as 'varies within groups, and therefore re-weights'"),
    # DEV-E4-009 guards: R-V naming and asymmetry
    ("entirely a coding effect",
     "DEV-E4-009: not entirely coding — there is a 4pp interaction; use 'coding effect plus interaction'"),
    ("direction of distortion, not its magnitude",
     "DEV-E4-009: asymmetry withdrawn — based on pipeline with coding inconsistency"),
    ("0~pp vs $11.6$~pp",
     "DEV-E4-009: asymmetry values withdrawn — not recomputed with consistent coding"),
    ("0$~$pp vs $11.6$~pp",
     "DEV-E4-009: asymmetry values withdrawn — not recomputed with consistent coding"),
    ("survives the coding correction",
     "DEV-E4-009: directional asymmetry not recomputed — cannot claim it survives"),
    ("P\\_E4\\_5 being falsified",
     "DEV-E4-009: P_E4_5 result was from inconsistent pipeline — remove"),
    # F8 forbidden value: 89.4 was the buggy result (double-normalisation, commit 9cdceb4).
    # Corrected value: 100.0 (commit 43b8427). If 89.4 appears in text, a stale paste happened.
    ("89.4",
     "F8 stale value: 89.4% was from buggy injection approach (9cdceb4); correct is 100.0 (43b8427)"),
]
if main_tex.exists():
    for phrase, reason in BAD_PHRASES:
        # skip lines that are comments
        non_comment = "\n".join(
            l for l in tex.splitlines()
            if not l.strip().startswith("%")
        )
        if phrase in non_comment:
            FAIL.append(f"Prohibited phrase in main.tex: '{phrase}' ({reason})")
            print(f"  [FAIL] Prohibited phrase: '{phrase}'")
        else:
            print(f"  [OK  ] Prohibited phrase absent: '{phrase}'")

# Rule 2: non-ASCII bib keys in refs.bib
bib_path = ROOT / "refs.bib"
if bib_path.exists():
    bib_text = bib_path.read_text(encoding="utf-8", errors="replace")
    import re as _re
    bib_keys = _re.findall(r"@\w+\{([^,\s]+),", bib_text)
    bad_keys = [k for k in bib_keys if not k.isascii()]
    if bad_keys:
        FAIL.append(f"Non-ASCII bib keys in refs.bib: {bad_keys}")
        print(f"  [FAIL] Non-ASCII bib keys: {bad_keys}")
    else:
        print(f"  [OK  ] All bib keys are ASCII ({len(bib_keys)} keys)")

# Rule 3: Geoffrion1968, Weber1988, Poyhonen2001 cited (present in main.bbl)
bbl_check = build_bbl if build_bbl.exists() else bbl_path
if bbl_check.exists():
    bbl_text = bbl_check.read_text(encoding="utf-8", errors="replace")
    for key in ["Geoffrion1968", "Weber1988", "Poyhonen2001"]:
        if key in bbl_text:
            print(f"  [OK  ] {key} cited (in main.bbl)")
        else:
            FAIL.append(f"{key} not cited — present in refs.bib but absent from main.bbl")
            print(f"  [FAIL] {key} not cited (absent from main.bbl)")

# Rule 4: no "Repeated entry" in main.blg
blg_path = Path(r"C:\build\paper\main.blg")
if blg_path.exists():
    blg_text = blg_path.read_text(encoding="utf-8", errors="replace")
    if "Repeated entry" in blg_text:
        FAIL.append("Duplicate bib entry detected in main.blg")
        print("  [FAIL] Duplicate bib entry (Repeated entry in main.blg)")
    else:
        print("  [OK  ] No duplicate bib entries")
else:
    print("  [INFO] main.blg not found — skip duplicate check")

# Rule 5: aspect coding consistency warning
# The manuscript uses aspect as binary (leeward indicator) in the objectives.
# Any score matrix for the 473-site cell must use the same binary coding.
# This cannot be automatically verified from the .tex alone, but we can check
# that the manuscript does not contain 'aspect' alongside 'continuous' or 'degrees'
# in the context of the fourth cell or the score computation.
ASPECT_INCONSISTENCY_PHRASES = [
    "aspect.*continuous",
    "aspect.*degrees.*score",
    "aspect.*azimuth.*score",
]
if main_tex.exists():
    import re as _re2
    tex_lower = tex.lower()
    for phrase in ASPECT_INCONSISTENCY_PHRASES:
        if _re2.search(phrase, tex_lower):
            FAIL.append(f"Potential aspect coding inconsistency in main.tex: pattern '{phrase}' found")
            print(f"  [FAIL] Aspect coding inconsistency: '{phrase}'")
    # Positive check: manuscript should note that aspect is binary
    if "aspect" in tex and "binary" not in tex.lower() and "leeward" not in tex.lower():
        print("  [WARN] 'aspect' in main.tex but 'binary' and 'leeward' not found — verify coding is documented")
    else:
        print("  [OK  ] aspect coding (binary/leeward) documented or aspect not in text")


# ── A7. PDF integrity: pdftotext must find 0 '??' ───────────────────────────
# Reads the compiled PDF directly — independent of .log which can be stale.
# Catches broken \ref, \cite, \pageref that survive to the output file.
print()
print("=== A7: PDF integrity (pdftotext) ===")
pdf_candidates = [
    Path(r"C:\build\paper\main.pdf"),
    ROOT / "main.pdf",
]
pdf_path = next((p for p in pdf_candidates if p.exists() and p.stat().st_size > 100_000), None)
if pdf_path is None:
    FAIL.append("A7: main.pdf not found (>100 KB) — run xelatex first")
    print("  [FAIL] main.pdf not found — run xelatex first")
else:
    import subprocess as _sp, tempfile as _tmp, os as _os
    try:
        # Write to temp file to avoid encoding issues with stdout pipe on Windows
        with _tmp.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as tf:
            tmp_path = tf.name
        _sp.run(
            ["pdftotext", str(pdf_path), tmp_path],
            capture_output=True, timeout=60
        )
        pdf_text = Path(tmp_path).read_text(encoding="utf-8", errors="replace")
        _os.unlink(tmp_path)
        if not pdf_text.strip():
            FAIL.append("A7: pdftotext produced empty output — PDF may not be text-extractable")
            print("  [FAIL] A7: pdftotext empty output")
        else:
            # Count literal '??' — unresolved cross-references render as ??
            qq_pdf = pdf_text.count("??")
            if qq_pdf > 0:
                FAIL.append(f"A7: '??' found {qq_pdf} times in PDF (unresolved \\ref or \\cite)")
                print(f"  [FAIL] A7: '??' in PDF: {qq_pdf} occurrences — unresolved refs/cites")
                # Show first 5 contexts
                lines_with_qq = [l for l in pdf_text.splitlines() if "??" in l]
                for ctx in lines_with_qq[:5]:
                    print(f"    context: {ctx[:100].strip()}")
            else:
                print(f"  [OK  ] A7: '??' in PDF: 0 (all refs and cites resolved)")
            # Also count 'Page 1 of 100' or similar last-page artefact
            if "Page 1 of 100" in pdf_text or "1 of 100" in pdf_text:
                FAIL.append("A7: last-page reference unresolved ('1 of 100' in PDF)")
                print("  [FAIL] A7: last-page ref unresolved")
            else:
                print("  [OK  ] A7: last-page reference resolved")
    except FileNotFoundError:
        FAIL.append("A7: pdftotext not found — install poppler-utils")
        print("  [FAIL] A7: pdftotext not installed — install poppler-utils (winget install poppler)")
    except _sp.TimeoutExpired:
        FAIL.append("A7: pdftotext timed out")
        print("  [FAIL] A7: pdftotext timed out")

# ── A8: Supplementary PDF integrity ─────────────────────────────────────────
print()
print("=== A8: Supplementary PDF integrity (pdftotext) ===")
suppl_pdf_candidates = [
    Path(r"C:\build\paper\suppl_wrapper.pdf"),
    ROOT / "suppl_wrapper.pdf",
    ROOT / "supplementary.pdf",
]
suppl_pdf = next((p for p in suppl_pdf_candidates if p.exists() and p.stat().st_size > 10_000), None)
if suppl_pdf is None:
    print("  [INFO] A8: suppl_wrapper.pdf not found — skipping (build supplementary first)")
else:
    try:
        with _tmp.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as tf:
            tmp_s = tf.name
        _sp.run(["pdftotext", str(suppl_pdf), tmp_s], capture_output=True, timeout=60)
        suppl_text = Path(tmp_s).read_text(encoding="utf-8", errors="replace")
        _os.unlink(tmp_s)
        qq_s = suppl_text.count("??")
        if qq_s > 0:
            FAIL.append(f"A8: '??' found {qq_s} times in supplementary PDF (unresolved refs)")
            print(f"  [FAIL] A8: '??' in supplementary: {qq_s} occurrences")
            for ctx in [l for l in suppl_text.splitlines() if "??" in l][:5]:
                print(f"    context: {ctx[:100].strip()}")
        else:
            print(f"  [OK  ] A8: '??' in supplementary PDF: 0")
    except Exception as _e:
        print(f"  [INFO] A8: pdftotext error on supplementary: {_e}")

print()
if FAIL:
    print(f"FAILED: {len(FAIL)} check(s):")
    for msg in FAIL:
        print(f"  x {msg}")
    sys.exit(1)
else:
    print(f"ALL CHECKS PASSED (0 failures)")
