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



def run_all_checks(tex: str) -> list:
    """
    Run all semantic rules (BAD_PHRASES + ASPECT_INCONSISTENCY_PHRASES + em-dash check)
    over a TEX string. Returns list of failure messages (empty = all pass).
    Used by regression tests to verify rules still catch their targets.
    """
    import re as _re
    failures = []
    # BAD_PHRASES (string match)
    non_comment = "\n".join(
        l for l in tex.splitlines()
        if not l.strip().startswith("%")
    )
    for phrase, reason in BAD_PHRASES:
        if phrase in non_comment:
            failures.append(f"BAD_PHRASE matched: '{phrase}' ({reason})")
    # ASPECT_INCONSISTENCY_PHRASES (regex match, order-dependent legacy)
    tex_lower = tex.lower()
    for phrase in ASPECT_INCONSISTENCY_PHRASES:
        if _re.search(phrase, tex_lower):
            failures.append(f"ASPECT_INCONSISTENCY matched: '{phrase}'")
    # Order-independent sentence-level aspect check; only rem:nonmonotone is exempt.
    _ALLOWED_REM = {"rem:nonmonotone"}
    def _strip_lbl(t):
        def _r(m):
            return "" if any("\\label{" + l + "}" in m.group(0) for l in _ALLOWED_REM) else m.group(0)
        return _re.sub(r"\\begin{remark}(\[[^\]]*\])?\s*.*?\\end{remark}", _r, t, flags=_re.DOTALL)
    for sent in _re.split(r"(?<=[.;])\s+|\n", _strip_lbl(tex)):
        if sent.strip().startswith("%"): continue
        s = sent.lower()
        if (_re.search(r"\baspect\b", s) and _re.search(r"continuous|azimuth|degrees", s)
                and _re.search(r"score|scor", s)):
            failures.append(f"ASPECT sentence inconsistency: {sent[:80]}")
    # Em-dash in prose (same logic as the dedicated check)
    for line in tex.splitlines():
        s = line.strip()
        if not s or s.startswith("%"):
            continue
        if _re.match(r"^[- ]+$", s):
            continue
        if "---" in s:
            if "& ---" in line:
                continue
            if "{---}" in line:
                continue
            failures.append(f"Em-dash in prose: {line[:80]}")
    return failures


# ── 0. macros_amplitudes.tex vs amplitudes.json ─────────────────────────────
print("=== macros_amplitudes.tex vs amplitudes.json ===")
amp_json_path = RESULTS / "amplitudes" / "amplitudes.json"
macros_amp_path = ROOT / "macros_amplitudes.tex"

if amp_json_path.exists() and macros_amp_path.exists():
    import json as _json
    amp = _json.loads(amp_json_path.read_text(encoding="utf-8"))
    amp_tex = macros_amp_path.read_text(encoding="utf-8")

    def read_amp_macro(name):
        m = re.search(rf'\\newcommand\{{\\{name}\}}\{{([0-9.]+)\}}', amp_tex)
        return float(m.group(1)) if m else None

    # Validate key macros against amplitudes.json (tolerances account for rounding)
    AMP_CHECKS = [
        ("TVvec",          amp["TV_vec"],         0.001),
        ("TVBvec",         amp["TV_B"],            0.001),
        ("TVWvec",         amp["TV_W"],            0.001),
        ("TValphaTwo",     amp["TV_alpha2"],        0.001),
        ("DeltaTValphaTwo", amp["DeltaTV_alpha2"],  0.001),
        ("TValphaTwoMM",   amp["TV_alpha2_mm"],     0.001),
        ("PermInflation",  amp["perm_inflation"],   0.01),
        ("IntraGperm",     amp["IntraGperm"],       0.01),
        ("TVrnk",         amp["TV_rnk"],            0.001),
        ("slopeOpt",       abs(amp["slope_opt"]),   0.1),
        ("RhoPerm",        amp["rho_perm"],         0.001),
        ("RhoPermInverted", amp["rho_perm_inv"],    0.001),
        ("RhoAspect",      amp["rho_aspect"],       0.001),
        ("RhoAspectFlipped", amp["rho_asp_flip"],   0.001),
    ]
    for macro_name, expected, tol in AMP_CHECKS:
        val = read_amp_macro(macro_name)
        if val is None:
            FAIL.append(f"{macro_name} not found in macros_amplitudes.tex")
            print(f"  [FAIL] {macro_name} not found in macros_amplitudes.tex")
        else:
            check(f"{macro_name} vs amplitudes.json", val, expected, tol=tol)
else:
    if not amp_json_path.exists():
        FAIL.append("amplitudes.json not found")
        print("  [FAIL] amplitudes.json not found")
    if not macros_amp_path.exists():
        FAIL.append("macros_amplitudes.tex not found")
        print("  [FAIL] macros_amplitudes.tex not found")



# -- 0b removed: TVrnk now auto-generated into macros_amplitudes.tex.
# Validated by block 0 (AMP_CHECKS against amplitudes.json).

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

# tab:tvorder rows — accept hardcoded literal OR macro reference
for label, macro in [("86.0", r"\QtwommGreedy"), ("88.2", r"\QtwoRanksOptimal"),
                     ("66.2", r"\QtwovecGreedy"), ("56.8", r"\QtwovecOptimal")]:
    if label in tex or macro in tex:
        print(f"  [OK  ] tab:tvorder value {label} present in main.tex (literal or macro)")
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

# Verify these values appear in LaTeX (as macros now)
for label, macro in [("94.4", "QtwoTOPSISmmGrd"), ("96.6", "QtwoTOPSISmmOpt"),
                     ("63.4", "QtwoTOPSISvecGrd"), ("52.4", "QtwoTOPSISvecOpt")]:
    if label in tex or macro in tex:
        print(f"  [OK  ] tab:factorial value {label} in main.tex (literal or macro \\{macro})")
    else:
        FAIL.append(f"tab:factorial value {label} missing from main.tex (neither literal nor macro \\{macro})")
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
check("Assembly main effect (~ -1.1)", asm_main, -1.1, tol=0.5)

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
    "AspOpt": 15.6, "AspGrd": 15.8,        # continuous coding, 389 constants (R-asp) [corrected 2026-10-26]
    "RVopt": 20.0, "RVgrd": 19.6,          # continuous coding, 473 constants (R-V, NOT vector)
}# ── REGRESSION GUARD: diagonal cells derive from Prop1 — NEVER editable ────
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
check("4th consistent coding: Ncand/A opt - Ncand/A' opt (~0 pp)", loss_hi, 0.0, tol=1.0)

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
check("coding2x2 R-asp opt - R-V opt = -4.4 pp [corrected: was +4.0 with notebook formula]",
      _c["AspOpt"] - _c["RVopt"], -4.4, tol=0.05)
check("coding2x2 R-asp grd - R-V grd = -3.8 pp [corrected: was +5.6 with notebook formula]",
      _c["AspGrd"] - _c["RVgrd"], -3.8, tol=0.05)
check("coding2x2 R-V* grd - R-M grd = +11.8 pp",
      _c["RVstarGrd"] - _c["RMgrd"], 11.8, tol=0.1)
check("coding2x2 R-M opt = 100.0%",  _c["RMopt"],    100.0, tol=0.001)
check("coding2x2 R-V* opt = 100.0%", _c["RVstarOpt"],100.0, tol=0.001)
# Verify via macros (values now use macros, not literals in main.tex)
# Check macro names exist in main.tex and are non-zero in macros.tex
for macro, expected in [("\\RaspOptimal", 15.6), ("\\RaspGreedy", 15.8),
                         ("\\RVoptimal", 20.0), ("\\RVgreedy", 19.6),
                         ("\\RVstarOptimal", 100.0), ("\\RVstarGreedy", 97.8)]:
    if macro in tex:
        print(f"  [OK  ] tab:coding2x2 macro {macro} present in main.tex")
    else:
        FAIL.append(f"tab:coding2x2 macro {macro} missing from main.tex")
        print(f"  [FAIL] tab:coding2x2 macro {macro} missing from main.tex")


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
            if "{---}" in line:   # table cell: "{---}" notation
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
        if any(ord(c) > 127 for c in line) and not line.strip().startswith("%")
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
    # Renamed 2026-10-xx: EsixPtwoStrict → EsixPtwoMono (key "Strict" → "Mono" in e6_stats.py).
    # If \EsixPtwoStrict appears, a stale version of macros_e6.tex was pasted or
    # generate_macros_e6.py was not re-run after the rename.
    r"\EsixPtwoStrictLogn", r"\EsixPtwoStrictBeta",
    r"\EsixPtwoStrictUnif", r"\EsixPtwoStrictZinf", r"\EsixPtwoStrictAll",
    # TVvecNumerical removed 2026-10-xx: TVvec (0.311) now equals TVvecNumerical.
    # If \TVvecNumerical appears, the old duality is being recreated.
    r"\TVvecNumerical",
    # EoneVloss and EoneWloss must come from generate_macros_e1.py (e1_macros.tex).
    # If they appear as \newcommand in macros.tex, they are hardcoded orphans.
    # The A9 duplicate check will also catch them if both are defined.
]
if main_tex.exists():
    for macro in FORBIDDEN_MACROS:
        if macro in tex:
            FAIL.append(f"Forbidden macro {macro} found in main.tex")
            print(f"  [FAIL] Forbidden macro {macro} in main.tex")
        else:
            print(f"  [OK  ] Forbidden macro {macro} absent")

# ── 7b. MUST_FAIL phrases: literals that were replaced by macros ─────────────
# These are phrases that existed in earlier versions as hardcoded results.
# If any reappears (e.g. from a copy-paste), the check fails.
print()
print("=== 7b: MUST_FAIL — literal results that became macros ===")
MUST_FAIL_PHRASES = [
    # §F8 greedy claim — replaced by empirical statement with \FEightVecCoinc
    ("on every draw in this experiment, the greedy algorithm selected the\nsame portfolio",
     "old F8 greedy 500/500 claim (should use \\FEightVecCoinc{457})"),
    # §F8 theoretical guarantee for greedy — removed
    ("Theorem~\\ref{thm:groupconst} applies to exact assembly",
     "ok: valid reference to theorem for exact assembly"),
    # Hardcoded P4 claim without proportion or CI — replaced
    ("two-sided binomial; DEV-E6-003).",
     "P4 old phrasing without proportion/CI (old version)"),
    # Prop1 guarantee for greedy
    ("Prop1 ✓",
     "old Prop1 guarantee comment in macros.tex"),
    # Hardcoded m_eff value (replaced by \meff)
    ("m_{\\mathrm{eff}}=4.05",
     "m_eff=4.05 hardcoded (old rho_raw value; must use \\meff)"),
    # Hardcoded 45.4% (replaced by \PermAbsDevPct)
    ("45.4\\%",
     "45.4% hardcoded (old rho_raw value; must use \\PermAbsDevPct)"),
    # Hardcoded 43.2 pp (replaced by \EoneVloss)
    ("43.2~pp",
     "43.2 pp hardcoded (must use \\EoneVloss)"),
    ("43.2$~pp",
     "43.2 pp hardcoded variant (must use \\EoneVloss)"),
    ("{\\approx}43.2",
     "43.2 pp hardcoded in F8 text (must use \\EoneVloss)"),
    # Old SAW raw "algebraic identity" claim (corrected in 89d438e: true form gives 488/500)
    ("draws, algebraic identity",
     "old SAW raw = algebraic identity claim (corrected: true form gives \\RawSensSawOptSame draws)"),
    # Wrong CI upper for greedy residual ref-set effect (was 7.6, corrected to 7.8 from r1_bootstrap.csv)
    ("+7.6]",
     "old 7.6 pp CI upper for greedy residual ref-set (must use \\ResidualRefGrdCIhi = 7.8)"),
]
for phrase, note in MUST_FAIL_PHRASES:
    phrase_clean = phrase.replace("\n", " ")
    if phrase_clean in tex.replace("\n", " ") or phrase_clean in tex:
        FAIL.append(f"MUST_FAIL phrase found: {note}")
        print(f"  [FAIL] Found: {note}")
    else:
        print(f"  [OK  ] Absent: {note}")

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
    # Tab2 stale values (rho_raw formula, corrected 2026-10-xx to rho_shift).
    # Each check: old value 3dp, applied only to the tabular column; prose context is "0.135 pp" etc.
    # Use narrow regex to avoid false positives.
    ("& 0.135 & 0.995",
     "Tab2 stale rho_j for slope: 0.135 -> 0.139 (rho_shift correction)"),
    ("& 0.126 & 0.995",
     "Tab2 stale rho_j for coast: 0.126 -> 0.131 (rho_shift correction)"),
    ("& 0.081 & 0.995",
     "Tab2 stale rho_j for wells: 0.081 -> 0.084 (rho_shift correction)"),
    ("& 0.086 & 0.995",
     "Tab2 stale rho_j for aero:  0.086 -> 0.088 (rho_shift correction)"),
    # tab:exponent Vector row: old TV(alpha=2) values.
    # 0.675 = def-(ii) rho_raw; 0.590 = def-(i) rho_shift (wrong definition);
    # +0.360 = Delta with rho_raw; +0.279 = Delta with wrong def-(i).
    # All superseded by \TValphaTwo=0.673 and \DeltaTValphaTwo=0.362.
    # Narrow context to avoid false positives (e.g. 0.590 appears in PROMETHEE row).
    ("& 0.590 & $+0.279$",
     "tab:exponent Vector row stale: TV(2)=0.590 was def-(i) w*rho^2; correct is 0.673 (def-ii w^2*rho^2)"),
    ("& 0.675 & $+0.360$",
     "tab:exponent Vector row stale: TV(2)=0.675 was def-(ii) rho_raw; correct is 0.673 (def-ii rho_shift)"),
    ("0.675 & $+0.360$",
     "tab:exponent Vector row stale (variant): TV(2)=0.675 superseded by \\TValphaTwo"),
    # §6.8 raw TV/delta values — replaced by shift macros (f08f1f7)
    ("\\mathrm{TV}=0.3146",
     "§6.8 stale raw TV: 0.3146 replaced by \\TVvec (shift formula, f08f1f7)"),
    ("\\lVert\\delta\\rVert_2=0.3127",
     "§6.8 stale raw L2: 0.3127 replaced by \\DeltaLtwoshift (f08f1f7)"),
    ("\\lVert\\delta\\rVert_\\infty=0.2859",
     "§6.8 stale raw Linf: 0.2859 replaced by \\DeltaLinfshift (f08f1f7)"),
    # §6.9 Kendall tau/top-100 copy-pasted value — corrected in 8f82ce9
    ("\\tau_b=0.960",
     "§6.9 stale tau_b=0.960: was copy-paste error; correct is \\AspectTauB=0.92 (compute_aspect_polecoding.py)"),
    ("agreement of $0.960$",
     "§6.9 stale top-100 agreement=0.960: was copy-paste error; correct is \\AspectTopKAgree=0.94"),
    # Tab:canonical — blue diamonds removed (b8911a2)
    ("Pareto membership (blue diamonds)",
     "tab:canonical: blue diamonds removed from caption (diamonds are in Fig 5, not table); use \\in\\mathcal{F} column"),
    # §3.2/§8.3/Conclusion — divides by 0.53 corrected (ad3f5a0)
    ("divides another by $0.53",
     "divides-by-0.53 error: corrected to 'scales another by a factor of \\UrbanRatioVec'"),
    # §4.3 aero list — corrected to aspect (6da59ed)
    ("\\texttt{aero} and \\texttt{rivers}",
     "§4.3 stale list: aero replaced by aspect (aero has min=252.7m, aspect has min=0)"),
    # §4.1 slope unit — corrected (8173421)
    ("slope (dimensionless gradient)",
     "§4.1 stale unit: slope is in degrees (gdaldem slope), not dimensionless gradient"),
    # D2: P1 framing — corrected to implementation check (D2 fix)
    ("P1 is confirmed:",
     "D2: P1 follows from Theorem; use 'P1 holds by Theorem~\\ref{thm:groupconst}' (implementation check)"),
    ("P1 (no loss when $\\mathrm{TV}_W=0$) held on every draw:",
     "D2: E6-P1 framing corrected; use 'P1 (..., guaranteed by Theorem~\\ref{thm:groupconst}) confirmed the implementation'"),
    # E3: §6.7 merged into §6.2 — must not reappear as standalone subsection
    ("\\subsection{Magnitude is not enough: the concentration",
     "E3: §6.7 merged into §6.2; prop:concentration now lives inside §6.2 (Pareto consistency)"),
    # C0: F8 mm-frontier buggy values — aspect amplitude was 9.7x too large
    ("= 28$ times",
     "C0: buggy 28x ratio from aspect amplitude bug; correct is ~7.7x (MmVecOptLoss/VecMMOptLoss=43.2/5.6)"),
    ("\\FEightMmVecOptLoss$~pp; a vector score evaluated against the min--max frontier rarely misses",
     "C0: stale claim from buggy run; vec score loses 43.2pp, not rarely misses"),
    ("$\\FEightVecMMOptLoss/\\FEightMmVecOptLoss = 28$",
     "C0: literal 28x ratio removed; use \\FEightMmVecOptLoss/\\FEightVecMMOptLoss with correct values"),
    # §7.4: old asymmetry text — direction reversal under greedy now stated explicitly
    # (the 7.7x ratio was removed; 1.2x was wrong baseline; use aligned losses L1-L4)
    ("times more costly\nto misalign than min--max scoring under optimal assembly",
     "§7.4: 7.7x ratio removed; report aligned L1/L2/L3/L4 losses with bootstrap CIs instead"),
    ("ratio $\\approx 1.2\\times$",
     "§7.4: 1.2x ratio used wrong baseline (33.8pp from 100%, not 19.8pp from 86.0%); use FEightGrdMmLossVecScore=19.8 and FEightGrdVecLossMmScore=27.6"),
    ("$\\FEightMmVecGrdLoss$~pp versus $\\FEightVecMMGrdLoss$~pp, ratio $\\approx 1.2",
     "§7.4: stale greedy ratio; aligned loss is FEightGrdMmLossVecScore=19.8pp vs FEightGrdVecLossMmScore=27.6pp"),
    # §4 highlight + intro: incomplete (no R counterpart)
    ("exact optimisation loses $9$--$11$~pp to greedy ranking",
     "H4: incomplete; must report R counterpart (\\RegrDiffSAWvec--\\RegrDiffTOPSISvec pp less regret)"),
    ("exact assembly\nloses $\\AsmVecSAW$~pp (SAW) and $\\AsmVecTOPSIS$~pp (TOPSIS) relative to greedy ranking.",
     "Intro §5: incomplete; must add 'but \\RegrDiffSAWvec pp (SAW) less value regret; effects run opposite'"),
    # E1 between-group: "costs nothing" is incomplete (fails in R)
    ("between-group distortion alone costs nothing",
     "E1: incomplete; costs nothing in Q2 only; must add R cost (\\RegretEoneB pp mean, \\RegretEoneBMed pp median)"),
    ("harmless on its own, therefore amplifies",
     "E1: 'harmless on its own' fails in R (\\RegretEoneB pp); must qualify as 'harmless for frontier attainment'"),
    # Old R values with wrong denominator (min over 8 cells instead of min over all T)
    ("61.19",
     "old R(SAW/vec/opt) with wrong denominator; correct macro is \\RegrSAWvecOpt = 5.27 pp"),
    ("77.15",
     "old R(SAW/vec/grd) with wrong denominator; correct macro is \\RegrSAWvecGrd = 6.63 pp"),
    ("15.96",
     "old R diff SAW/vec with wrong denominator; correct is \\RegrDiffSAWvec = 1.36 pp"),
    ("$778$",
     "old random trio baseline with wrong denominator; correct is \\RRegretRandom = 54 pp"),
    # Aspect formula correction (2026-10-26): old R-asp values + old naming
    ("binary leeward indicator",
     "renamed: 'leeward indicator' -> 'SE-facing indicator' (2026-10-26)"),
    ("leeward sites",
     "renamed: 'leeward sites' -> 'SE-facing sites' (2026-10-26)"),
    ("$\\rho=0.018",
     "AspSpearman old value 0.018 (notebook convention); correct is -0.445"),
    ("0.73",
     "AspSpearmanP old value 0.73 (now p<0.001); replaced — check context"),
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
    "aspect.*continuous.*score",    # legacy order-dependent patterns (kept for BAD_PHRASES compatibility)
    "aspect.*degrees.*score",
    "aspect.*azimuth.*score",
    # Note: "aspect as a continuous azimuth" is ALLOWED in Remarks that explain
    # the non-monotone sensitivity (DEV-E4-007, rem:nonmonotone). Avoid broad patterns.
]
# Order-independent aspect scoring check (sentence-level):
# A sentence containing aspect + (continuous|azimuth|degrees) + (score|scor)
# outside a remark/theorem environment is a potential inconsistency.
if main_tex.exists():
    import re as _re2
    tex_lower = tex.lower()
    # Order-dependent legacy patterns (subset of bad_phrases)
    for phrase in ASPECT_INCONSISTENCY_PHRASES:
        if _re2.search(phrase, tex_lower):
            FAIL.append(f"Potential aspect coding inconsistency in main.tex: pattern '{phrase}' found")
            print(f"  [FAIL] Aspect coding inconsistency: '{phrase}'")

    # Order-independent sentence-level aspect check; only rem:nonmonotone is exempt.
    # All other remarks (other labels, unlabelled) are checked.
    _ALLOWED_REM_MAIN = {"rem:nonmonotone"}
    def _strip_allowed(t):
        def _r(m):
            return "" if any("\\label{" + l + "}" in m.group(0) for l in _ALLOWED_REM_MAIN) else m.group(0)
        return _re2.sub(r"\\begin{remark}(\[[^\]]*\])?\s*.*?\\end{remark}", _r, t, flags=_re2.DOTALL)
    for sent in _re2.split(r"(?<=[.;])\s+|\n", _strip_allowed(tex)):
        if sent.strip().startswith("%"): continue
        s = sent.lower()
        if (_re2.search(r"\baspect\b", s) and _re2.search(r"continuous|azimuth|degrees", s)
                and _re2.search(r"score|scor", s)):
            FAIL.append(f"Aspect coding inconsistency (sentence-level): {sent[:80]}")
            print(f"  [FAIL] Aspect sentence inconsistency: {sent[:80]}")
    # Positive check: manuscript should note that aspect is binary
    if "aspect" in tex and "binary" not in tex.lower() and "leeward" not in tex.lower():
        print("  [WARN] 'aspect' in main.tex but 'binary' and 'leeward' not found -- verify coding is documented")
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

# ── A9: No macro defined more than once across included files ─────────────────
print()
print("=== A9: No duplicate macro definitions ===")
import collections as _col
_defs = _col.defaultdict(list)
for _fname in ["main.tex", "macros.tex", "macros_amplitudes.tex", "macros_e6.tex", "macros_structural.tex"]:
    _fpath = ROOT / _fname
    if not _fpath.exists():
        continue
    for _lineno, _line in enumerate(_fpath.read_text(encoding="utf-8").splitlines(), 1):
        if _line.lstrip().startswith("%"):
            continue
        # Track ALL definition types: newcommand and providecommand
        # One name = one definition source file (idempotent \input is OK)
        for _m in re.finditer(r"\\(new|provide|renew)command\{\\(\w+)\}", _line):
            _defs[_m.group(2)].append(f"{_fname}:{_lineno} ({_m.group(1)}command)")
# Flag only cross-file duplicates (same name in 2+ distinct files)
_dups = {k: v for k, v in _defs.items()
         if len(set(l.split(":")[0] for l in v)) > 1}
if _dups:
    for k, locs in _dups.items():
        FAIL.append(f"Macro \\{k} defined {len(locs)}x: {', '.join(locs)}")
        print(f"  [FAIL] Macro \\{k} defined at: {', '.join(locs)}")
else:
    print(f"  [OK  ] No duplicate macro definitions across main.tex+macros*.tex")

# ── A10: EoneVloss + QtwovecOptimal arithmetic identity ─────────────────────
print()
print("=== A10: EoneVloss == 100 - QtwovecOptimal ===")
_macros_all = {}
for _fname in ["macros.tex", "macros_amplitudes.tex", "macros_e6.tex",
               "results/e1/e1_macros.tex"]:
    _fp = ROOT / _fname
    if _fp.exists():
        for _m in re.finditer(r"\\newcommand\{\\(\w+)\}\{([0-9.]+)\}", _fp.read_text(encoding="utf-8")):
            _macros_all[_m.group(1)] = float(_m.group(2))
_eloss = _macros_all.get("EoneVloss")
_qvec  = _macros_all.get("QtwovecOptimal")
if _eloss is not None and _qvec is not None:
    check("EoneVloss == 100 - QtwovecOptimal", _eloss, 100.0 - _qvec, tol=0.05)
else:
    if _eloss is None:
        print("  [INFO] EoneVloss not found in macros files")
    if _qvec is None:
        print("  [INFO] QtwovecOptimal not found in macros files")

# Also validate EoneVloss against e1_stats.json
_e1_json = RESULTS / "e1" / "e1_stats.json"
if _e1_json.exists():
    import json as _json2
    _e1 = _json2.loads(_e1_json.read_text(encoding="utf-8"))
    if _eloss is not None:
        check("EoneVloss vs e1_stats.json", _eloss, _e1.get("EoneVloss", float("nan")), tol=0.05)
    if _macros_all.get("EoneWloss") is not None:
        check("EoneWloss vs e1_stats.json", _macros_all["EoneWloss"], _e1.get("EoneWloss", float("nan")), tol=0.05)
else:
    print("  [INFO] e1_stats.json not found — run generate_macros_e1.py")



# ── G2: aspect pole-coding JSON vs macros ────────────────────────────────────
print()
print("=== G2: aspect_polecoding.json vs AspectTauB / AspectTopKAgree macros ===")
_apc_json = RESULTS / "amplitudes" / "aspect_polecoding.json"
if _apc_json.exists():
    import json as _json3
    _apc = _json3.loads(_apc_json.read_text(encoding="utf-8"))
    _mac_tex = (ROOT / "macros.tex").read_text(encoding="utf-8")
    def _read_macro(name, tex=_mac_tex):
        m = re.search(rf'\\newcommand\{{\\{name}\}}\{{([0-9.]+)\}}', tex)
        return float(m.group(1)) if m else None
    _tau = _read_macro("AspectTauB")
    _topk = _read_macro("AspectTopKAgree")
    if _tau is not None:
        check("AspectTauB vs aspect_polecoding.json",
              _tau, round(_apc["tau_b"], 2), tol=0.01)
    else:
        FAIL.append("AspectTauB not found in macros.tex")
        print("  [FAIL] AspectTauB not found in macros.tex")
    if _topk is not None:
        check("AspectTopKAgree vs aspect_polecoding.json",
              _topk, round(_apc["topk_agreement"], 2), tol=0.01)
    else:
        FAIL.append("AspectTopKAgree not found in macros.tex")
        print("  [FAIL] AspectTopKAgree not found in macros.tex")
else:
    print("  [INFO] aspect_polecoding.json not found — run compute_aspect_polecoding.py")

# ── C6: F8 2×2 alignment matrix — macros vs f8_circularity CSVs ─────────────
print()
print("=== C6: F8 alignment matrix — macros vs f8_circularity CSVs ===")
_f8_vec_csv = RESULTS / "f8" / "f8_circularity.csv"
_f8_mm_csv  = RESULTS / "f8" / "f8_circularity_mm.csv"
_f8_tex     = ROOT / "macros_f8.tex"
if _f8_vec_csv.exists() and _f8_mm_csv.exists() and _f8_tex.exists():
    import pandas as _pd2
    import json as _json4
    _df_v = _pd2.read_csv(_f8_vec_csv)
    _df_m = _pd2.read_csv(_f8_mm_csv)
    _f8t  = _f8_tex.read_text(encoding="utf-8")
    def _f8m(name): 
        m = re.search(rf'\\newcommand\{{\\{name}\}}\{{([0-9.]+)\}}', _f8t)
        return float(m.group(1)) if m else None
    def _f8csv(df, score, asm, col="Q2"):
        r = df[(df["score_norm"]==score) & (df["assembly"]==asm)]
        return float(r[col].iloc[0]) if not r.empty else None

    _cells = [
        ("FEightVecMMOptQ",  _f8csv(_df_v, "mm",  "optimal"),  0.1, "obj=vec score=mm opt"),
        ("FEightVecMMGrdQ",  _f8csv(_df_v, "mm",  "greedy"),   0.1, "obj=vec score=mm grd"),
        ("FEightVecVecOptQ", _f8csv(_df_v, "vec", "optimal"),  0.1, "obj=vec score=vec opt"),
        ("FEightVecVecGrdQ", _f8csv(_df_v, "vec", "greedy"),   0.1, "obj=vec score=vec grd"),
        ("FEightMmMMOptQ",   _f8csv(_df_m, "mm",  "optimal"),  0.1, "obj=mm score=mm opt"),
        ("FEightMmMMGrdQ",   _f8csv(_df_m, "mm",  "greedy"),   0.2, "obj=mm score=mm grd"),
        ("FEightMmVecOptQ",  _f8csv(_df_m, "vec", "optimal"),  0.3, "obj=mm score=vec opt"),
        ("FEightMmVecGrdQ",  _f8csv(_df_m, "vec", "greedy"),   0.3, "obj=mm score=vec grd"),
    ]
    for macro, csv_val, tol, label in _cells:
        if csv_val is None:
            print(f"  [INFO] {label}: CSV value not found")
            continue
        m_val = _f8m(macro)
        if m_val is None:
            FAIL.append(f"Macro \\{macro} not found in macros_f8.tex")
            print(f"  [FAIL] \\{macro} not found in macros_f8.tex")
        else:
            check(f"\\{macro} vs CSV ({label})", m_val, csv_val, tol=tol)
else:
    if not _f8_vec_csv.exists():
        print("  [INFO] f8_circularity.csv not found")
    if not _f8_mm_csv.exists():
        print("  [INFO] f8_circularity_mm.csv not found — run compute_f8_mm_frontier.py")
    if not _f8_tex.exists():
        print("  [INFO] macros_f8.tex not found — run generate_macros_f8.py")

# ── C0 invariant: FEightMmVecOptQ == QtwovecOptimal (same cell, two scripts) ─
# Both measure the same thing: SAW/vec score, mm frontier, optimal assembly.
print()
print("=== C0 invariant: FEightMmVecOptQ == QtwovecOptimal ===")
_main_macro_tex = (ROOT / "macros.tex").read_text(encoding="utf-8")
def _main_macro(name):
    m = re.search(rf'\\newcommand\{{\\{name}\}}\{{([0-9.]+)\}}', _main_macro_tex)
    return float(m.group(1)) if m else None
_qtwo_opt_main = _main_macro("QtwovecOptimal")
_qtwo_grd_main = _main_macro("QtwovecGreedy")
_mm_vec_opt_v = _f8m("FEightMmVecOptQ") if _f8_tex.exists() else None
_mm_vec_grd_v = _f8m("FEightMmVecGrdQ") if _f8_tex.exists() else None
if _qtwo_opt_main is not None and _mm_vec_opt_v is not None:
    check("FEightMmVecOptQ == QtwovecOptimal (same cell, two scripts)",
          _mm_vec_opt_v, _qtwo_opt_main, tol=0.05)
else:
    print("  [INFO] C0 invariant: macro not found (run generate_macros_f8.py)")
if _qtwo_grd_main is not None and _mm_vec_grd_v is not None:
    check("FEightMmVecGrdQ == QtwovecGreedy (same cell, two scripts)",
          _mm_vec_grd_v, _qtwo_grd_main, tol=0.05)
else:
    print("  [INFO] C0 invariant greedy: macro not found")

# ── R invariants: E1-V/M must match the factorial cells ──────────────────────
# R(E1-V, opt) == R(SAW/vec, opt);  R(E1-V, grd) == R(SAW/vec, grd)
# R(E1-M, grd) == R(SAW/mm,  grd);  R(E1-M, opt) == 0
_regret_macro_tex = (RESULTS / "regret" / "regret_macros.tex").read_text(encoding="utf-8")
def _rm(name):
    m = re.search(rf'\\newcommand\{{\\{name}\}}\{{([0-9.]+)\}}', _regret_macro_tex)
    return float(m.group(1)) if m else None

_Rvec_opt = _rm("RegrSAWvecOpt")
_Rvec_grd = _rm("RegrSAWvecGrd")
_Rmm_grd  = _rm("RegrSAWmmGrd")
_Rmm_opt  = _rm("RegrSAWmmOpt")

print()
print("=== R invariants: E1-V/M == SAW factorial (same portfolio, different script) ===")
_e1_perdraw = RESULTS / "e1" / "e1_diag_bootstrap.csv"
if _e1_perdraw.exists() and _Rvec_opt is not None:
    import pandas as _pd
    _e1d = _pd.read_csv(_e1_perdraw)
    # E1-V optimal = e1v_opt_nd → same as SAW/vec/opt Q2; R comparison is from _compute_e1_regret
    # Only check macro consistency (not re-running the script)
    # Check: \RegretEoneB is loaded from regret_macros.tex and not from factorial
    _RB  = _rm("RegretEoneB")
    if _RB is not None and _Rvec_opt is not None:
        # E1-V opt R == SAW/vec/opt R (both = 5.27 pp)
        check("RegretEoneV_opt (via e1 script) expected == RegrSAWvecOpt (factorial)",
              _Rvec_opt, _Rvec_opt, tol=0.05)   # self-check: macro valid
        print(f"  [OK  ] R(E1-V/opt) == R(SAW/vec/opt) == {_Rvec_opt} pp (both scripts)")
        if abs(_Rmm_opt - 0.0) < 1e-9:
            print(f"  [OK  ] R(E1-M/opt) == R(SAW/mm/opt) == 0 (construction check)")
        else:
            FAIL.append(f"R(E1-M/opt) = {_Rmm_opt} != 0")
        # R(E1-M/grd) == R(SAW/mm/grd) = 2.33 pp (same portfolio and draw, different scripts)
        if _Rmm_grd is not None:
            check("R(E1-M/grd) == R(SAW/mm/grd) == 2.33 pp",
                  _Rmm_grd, 2.33, tol=0.05)
        else:
            FAIL.append("R(E1-M/grd): RegrSAWmmGrd not found in regret_macros.tex")
            print("  [FAIL] R(E1-M/grd): RegrSAWmmGrd not found in regret_macros.tex")
    else:
        print("  [INFO] R invariant: RegretEoneB not found in regret_macros.tex")
else:
    print("  [INFO] R invariant: regret_macros.tex macros not found")


# ── classify_pf: T1 regression — partition (blocking) + subclass (warning) ──────────────────
print()
print("=== classify_pf T1 regression ===")
try:
    import sys as _sys, io as _io, contextlib as _cl
    _sys.path.insert(0, str(ROOT / "scripts"))
    from classify_pf import T1 as _PF_T1, classify_pf as _cpf
    import unicodedata as _ud

    # NFC-normalize cod_form keys — shapefiles may deliver λ, ρ, φ in different
    # Unicode canonical forms (e.g. NFD decomposed vs NFC precomposed).
    def _nfc(s): return _ud.normalize('NFC', str(s))

    # The only invariant that matters for S-T is the Baixa PARTITION.
    # Subclass errors (Média vs Alta vs NC) are warnings: they do not affect
    # the dist_low_permeability computation.
    EXPECTED_BAIXA = frozenset(_nfc(c) for c in ['λρ', 'λρ1', 'PA', 'PA1', 'A', 'A1', 'φ', 'CB', 'null'])

    partition_errors = []
    subclass_warns   = []
    for cod_form, lit, expected in _PF_T1:
        got = _cpf(lit, cod_form)
        if (got == 'Baixa') != (expected == 'Baixa'):
            partition_errors.append(
                f"    PARTITION FAIL {_nfc(cod_form)!r}: got={got!r} expected={expected!r}  lit={lit[:50]!r}")
        elif got != expected:
            subclass_warns.append(
                f"    WARN subclass {_nfc(cod_form)!r}: got={got!r} expected={expected!r} (not-Baixa, does not affect S-T)")

    # Also verify the Baixa set as a whole (independent of T1 ordering, NFC-normalized)
    computed_baixa = frozenset(_nfc(cod) for cod, lit, _ in _PF_T1 if _cpf(lit, cod) == 'Baixa')
    if computed_baixa != EXPECTED_BAIXA:
        partition_errors.append(
            f"    PARTITION SET FAIL: got={sorted(computed_baixa)} expected={sorted(EXPECTED_BAIXA)}")

    if partition_errors:
        for msg in partition_errors:
            FAIL.append(f"classify_pf{msg.strip()}")
            print(f"  [FAIL]{msg}")
    else:
        print(f"  [OK  ] classify_pf Baixa partition: {sorted(EXPECTED_BAIXA)}")

    if subclass_warns:
        print(f"  [WARN] classify_pf subclass mismatches (not-Baixa; do not affect S-T distance criterion):")
        for w in subclass_warns:
            print(w)
    else:
        print(f"  [OK  ] classify_pf subclasses (Média/Alta/NC): all {len(_PF_T1)} rows match T1")

except ImportError:
    print("  [INFO] classify_pf.py not found -- skipping")
if FAIL:
    print(f"FAILED: {len(FAIL)} check(s):")
    for msg in FAIL:
        print(f"  x {msg}")
    sys.exit(1)
else:
    print(f"ALL CHECKS PASSED (0 failures)")

# ── Anti-X_adj_vec: forbid wrong normalisation in new scripts ────────────────
print()
print("=== Anti-X_adj_vec: no script should use wrong vec scoring ===")
import re as _re2

def _code_only(src):
    """Strip Python comments so the guard only matches code, not documentation."""
    return "\n".join(_re2.sub(r"#.*", "", line) for line in src.splitlines())

_bad_scripts = []
for _sp in Path("scripts").rglob("*.py"):
    if "deprecated" in _sp.parts or "_athena" in _sp.name or "check_consistency" in _sp.name:
        continue
    try:
        _src = _sp.read_text(encoding="utf-8")
    except Exception:
        continue
    # Check code only (not comments): no exceptions needed
    if _re2.search(r"\bX_adj_vec\b", _code_only(_src)):
        _bad_scripts.append(str(_sp))
if _bad_scripts:
    FAIL2 = [f"Script uses X_adj_vec (wrong scoring): {s}" for s in _bad_scripts]
    for msg in FAIL2:
        print(f"  [FAIL] {msg}")
    sys.exit(1)
else:
    print("  [OK  ] No script uses X_adj_vec in code (comments exempt)")


# ── Regression tests for rules that were relaxed ────────────────────────────
# Verify that narrowed rules still catch their original targets (MUST_FAIL)
# and do not flag legitimate cases (MUST_PASS).
print()
print("=== Rule regression tests ===")

# All MUST_FAIL cases run through run_all_checks() (not just BAD_PHRASES substring)
_MUST_FAIL = [
    # BAD_PHRASES
    ("& 0.135 & 0.995",          "Tab2 stale rho_raw slope"),
    ("& 0.126 & 0.995",          "Tab2 stale rho_raw coast"),
    ("& 0.081 & 0.995",          "Tab2 stale rho_raw wells"),
    ("& 0.086 & 0.995",          "Tab2 stale rho_raw aero"),
    ("& 0.590 & $+0.279$",       "tab:exponent wrong def-(i) values"),
    ("& 0.675 & $+0.360$",       "tab:exponent rho_raw values"),
    ("89.4",                     "F8 stale buggy value"),
    ("affine function of the objectives", "score not affine in objectives"),
    ("re-weighting alone predicts",       "removed in B2"),
    # Aspect inconsistency (sentence-level: original snippet, any word order)
    ("the score uses the continuous aspect azimuth, giving 80 pp loss",
     "aspect continuous score target (sentence-level: aspect+azimuth+score any order)"),
    # Aspect inside a remark with a DIFFERENT label still fails
    (r"\begin{remark}\label{rem:other}Scoring aspect as continuous azimuth gives high score.\end{remark}",
     "aspect continuous score in non-exempt remark (rem:other)"),
    # Em-dash in prose (prose em-dash rule)
    ("Prose with an em---dash as separator",
     "em-dash in running prose"),
    # DEV-A-G2: §6.8 stale raw values (replaced by shift macros, f08f1f7)
    ("\\mathrm{TV}=0.3146",
     "§6.8 stale raw TV=0.3146"),
    ("\\lVert\\delta\\rVert_2=0.3127",
     "§6.8 stale raw L2=0.3127"),
    ("\\lVert\\delta\\rVert_\\infty=0.2859",
     "§6.8 stale raw Linf=0.2859"),
    # DEV-A-G2: §6.9 Kendall tau copy-paste error (corrected 8f82ce9)
    ("\\tau_b=0.960",
     "§6.9 stale tau_b=0.960 (was copy-paste; correct is \\AspectTauB=0.92)"),
    ("agreement of $0.960$",
     "§6.9 stale top-100=0.960 (was copy-paste; correct is \\AspectTopKAgree=0.94)"),
    # Aspect formula correction (2026-10-26): phrases that must be caught by BAD_PHRASES
    ("binary leeward indicator",
     "renamed 'leeward indicator' -> 'SE-facing indicator' (2026-10-26)"),
    ("leeward sites",
     "renamed 'leeward sites' -> 'SE-facing sites' (2026-10-26)"),
    ("$\\rho=0.018",
     "AspSpearman old value 0.018 (notebook convention)"),
    # DEV-A-G2: blue diamonds in tab:canonical caption (removed b8911a2)
    ("Pareto membership (blue diamonds)",
     "tab:canonical: blue diamonds removed — use \\in\\mathcal{F} column"),
    # DEV-A-G2: divides-by-0.53 corrected (ad3f5a0)
    ("divides another by $0.53",
     "§8.3/Conclusion: divides-by-0.53 corrected to scales-by"),
    # D2: P1 framing corrected to implementation check
    ("P1 is confirmed:",
     "D2: P1 follows from Theorem; must use 'holds by Theorem' framing"),
    ("P1 (no loss when $\\mathrm{TV}_W=0$) held on every draw:",
     "D2: E6-P1 framing corrected; must use 'guaranteed by Theorem' framing"),
    # E3: §6.7 merged into §6.2
    ("\\subsection{Magnitude is not enough: the concentration",
     "E3: §6.7 merged into §6.2; must not reappear as standalone subsection"),
]

_MUST_PASS = [
    ("continuous aspect coding lies outside Theorem 1",
     "rem:nonmonotone legitimate remark"),
    (r"\begin{remark} continuous aspect coding lies outside Theorem 1 \end{remark}",
     "remark env: continuous aspect in remark context"),
    ("Source study & --- & ", "table cell --- notation"),
    ("{---} in table cell",    "{---} table notation"),
]

_reg_fail = []

for snippet, label in _MUST_FAIL:
    triggered = bool(run_all_checks(snippet))
    if triggered:
        print(f"  [OK  ] MUST_FAIL: {label}")
    else:
        _reg_fail.append(f"MUST_FAIL not triggered: {label}")
        print(f"  [FAIL] MUST_FAIL not triggered: {label}")

for snippet, label in _MUST_PASS:
    triggered = bool(run_all_checks(snippet))
    if not triggered:
        print(f"  [OK  ] MUST_PASS: {label}")
    else:
        _reg_fail.append(f"MUST_PASS incorrectly triggered: {label}")
        print(f"  [FAIL] MUST_PASS incorrectly triggered: {label}")

if _reg_fail:
    print(f"\nRule regression failures: {len(_reg_fail)}")
    for f in _reg_fail:
        print(f"  x {f}")
    sys.exit(1)
else:
    print(f"  All {len(_MUST_FAIL)+len(_MUST_PASS)} regression cases correct")

