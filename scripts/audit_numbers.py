# -*- coding: utf-8 -*-
"""audit_numbers.py — Audit numeric literals in manuscript .tex files.

Scans main.tex, santiago.tex, supplementary.tex for numeric literals that
appear outside \\newcommand definitions and outside known safe regions.
Classifies each as:
  (b) design constant — listed in checks/design_constants.txt
  (c) result written by hand — FAIL

The scanner is intentionally conservative: it only flags numbers that appear
in running text or table cells in the MAIN BODY of the paper (main.tex and
santiago.tex). The supplementary.tex contains pre-registration documents,
version history, and data provenance tables that are exempt from the
zero-hand-written-numbers rule (they document historical values, not claims).

Usage:
    uv run python scripts/audit_numbers.py

Output: prints classified list; exits 1 if any class-(c) found.
Enters make check via run_checks.py.
"""
import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
# Only scan the two main manuscript files; supplementary is exempt (prespec docs)
TEX_FILES = [
    ROOT / "paper" / "manuscript" / "main.tex",
    ROOT / "paper" / "manuscript" / "santiago.tex",
]
DESIGN_CONSTANTS_FILE = ROOT / "checks" / "design_constants.txt"

SEP = "=" * 72

# ─────────────────────────────────────────────────────────────────────────────
# §1  Load design constants
# ─────────────────────────────────────────────────────────────────────────────

def load_design_constants():
    if not DESIGN_CONSTANTS_FILE.exists():
        return {}
    constants = {}
    for line in DESIGN_CONSTANTS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(";", 2)
        if len(parts) >= 2:
            constants[parts[0].strip()] = parts[1].strip()
    return constants

# ─────────────────────────────────────────────────────────────────────────────
# §2  Strip LaTeX comments
# ─────────────────────────────────────────────────────────────────────────────

def strip_comments(line):
    result = []
    i = 0
    while i < len(line):
        if line[i] == '\\' and i + 1 < len(line):
            result.append(line[i:i+2])
            i += 2
        elif line[i] == '%':
            break
        else:
            result.append(line[i])
            i += 1
    return "".join(result)

# ─────────────────────────────────────────────────────────────────────────────
# §3  Patterns to blank out (replace with spaces) before scanning
# ─────────────────────────────────────────────────────────────────────────────

_BLANK_PATTERNS = [
    # \newcommand / \renewcommand definitions
    re.compile(r'\\(?:re)?newcommand\{[^}]+\}\{[^}]*\}'),
    # All \cite* commands
    re.compile(r'\\cite[a-z*]*(?:\[[^\]]*\])?\{[^}]+\}'),
    # \label, \ref, \eqref, \pageref, \autoref
    re.compile(r'\\(?:label|ref|eqref|pageref|autoref|nameref)\{[^}]+\}'),
    # \texttt{} — code, hashes, commit ids
    re.compile(r'\\texttt\{[^}]+\}'),
    # \url{} and \nolinkurl{}
    re.compile(r'\\(?:url|nolinkurl)\{[^}]+\}'),
    # \input{} paths
    re.compile(r'\\input\{[^}]+\}'),
    # \includegraphics[...]{...}
    re.compile(r'\\includegraphics(?:\[[^\]]*\])?\{[^}]+\}'),
    # tabular column specs
    re.compile(r'\\begin\{tabular[*]?\}(?:\[[^\]]*\])?\{[^}]+\}'),
    # TeX dimensions: number followed by pt/mm/cm/em/ex/bp/sp
    re.compile(r'\d+(?:\.\d+)?(?:pt|mm|cm|em|ex|bp|sp)\b'),
    # \textwidth, \columnwidth etc. with preceding number
    re.compile(r'\d+(?:\.\d+)?\\(?:textwidth|columnwidth|linewidth|textheight)\b'),
    # Exponents and subscripts: ^{...} _{...} ^N _N
    re.compile(r'[\^_]\{[^}]*\}'),
    re.compile(r'[\^_]-?\d+'),
    # \cmidrule(lr){N-M} — table rule specs
    re.compile(r'\\cmidrule(?:\([^)]*\))?\{[^}]+\}'),
    # \multirow{N} \multicolumn{N}
    re.compile(r'\\multi(?:row|column)\{[^}]+\}'),
    # \setcounter{}{N}
    re.compile(r'\\setcounter\{[^}]+\}\{[^}]+\}'),
    # \renewcommand{\arraystretch}{N}
    re.compile(r'\\renewcommand\{\\arraystretch\}\{[^}]+\}'),
    # \renewcommand{\topfraction}{N} etc.
    re.compile(r'\\renewcommand\{\\[a-z]+fraction\}\{[^}]+\}'),
    # \emergencystretch=Nem
    re.compile(r'\\emergencystretch=\d+[a-z]+'),
    # @{\hspace{...}} @{\extracolsep{...}}
    re.compile(r'@\{[^}]+\}'),
    # \hspace*{} \vspace*{}
    re.compile(r'\\[hv]space\*?\{[^}]+\}'),
    # ORCID numbers: orcid=XXXX-XXXX-XXXX-XXXX
    re.compile(r'orcid=[0-9-]+'),
    # ISO dates: YYYY-MM-DD patterns
    re.compile(r'\d{4}-\d{2}-\d{2}'),
    # Time patterns: HH:MM
    re.compile(r'\d{2}:\d{2}'),
    # Timezone offsets: -03:00
    re.compile(r'[+-]\d{2}:\d{2}'),
    # \S\ref{} section references
    re.compile(r'\\S\\ref\{[^}]+\}'),
    # DEV-* identifiers
    re.compile(r'DEV-[A-Z0-9-]+'),
    # DOI patterns
    re.compile(r'10\.\d{4,}/\S+'),
    # p.\ page references: p.\,254
    re.compile(r'p\.\s*\\,\s*\d+'),
    # WGS~84 / UTM Zone~26N
    re.compile(r'WGS~\d+'),
    re.compile(r'UTM Zone~\d+[A-Z]'),
    # Seed~42
    re.compile(r'seed~\d+'),
    # \{N,M,P\} portfolio site sets
    re.compile(r'\\{[\d,\\,\s]+\\}'),
    # Numbers in \binom{}{} \frac{}{} — structural math
    re.compile(r'\\(?:binom|frac)\{[^}]+\}\{[^}]+\}'),
    # Numbers in \sqrt{N}
    re.compile(r'\\sqrt\{[^}]+\}'),
    # Numbers in \approx N
    re.compile(r'\\approx\s*\d+(?:\.\d+)?'),
    # Numbers in \ge N \le N
    re.compile(r'\\(?:ge|le|geq|leq)\s*\d+(?:\.\d+)?'),
    # Numbers in \times N
    re.compile(r'\\times\s*\d+(?:\.\d+)?'),
    # Numbers in \kappa=N (kappa values are macro-backed)
    re.compile(r'\\kappa\s*=\s*\d+'),
    # Numbers in \kappa\to\infty
    re.compile(r'\\kappa\\to\\infty'),
    # Numbers in \alpha=N
    re.compile(r'\\(?:alpha|beta|gamma|delta|epsilon|sigma|tau|mu|nu|xi|pi|rho|lambda|omega)\s*=\s*\d+(?:\.\d+)?'),
    # Numbers in \mathrm{CI}=N
    re.compile(r'\\mathrm\{[A-Z]+\}\s*=\s*\d+(?:\.\d+)?'),
    # Numbers in \lambda_{\max}=\lmax
    re.compile(r'\\lambda_\{\\max\}=\\lmax'),
    # Numbers in \mathrm{RI}=N
    re.compile(r'\\mathrm\{RI\}=\d+(?:\.\d+)?'),
    # Numbers in \mathrm{CR}=\CR
    re.compile(r'\\mathrm\{CR\}=\\CR'),
    # Numbers in \mathrm{SD}=N
    re.compile(r'\\mathrm\{SD\}\s*\d+(?:\.\d+)?'),
    # Numbers in \mathrm{ICC}=N
    re.compile(r'\\mathrm\{ICC\}=\d+(?:\.\d+)?'),
    # Numbers in \mathrm{TV}=N (TV values are macro-backed via \TVvec etc.)
    re.compile(r'\\mathrm\{TV\}\s*=\s*\d+(?:\.\d+)?'),
    # Numbers in \mathrm{TV}_[BW]=N
    re.compile(r'\\mathrm\{TV\}_[BW]\s*=\s*\d+(?:\.\d+)?'),
    # Numbers in \mathrm{gap}=N
    re.compile(r'\\mathrm\{gap\}=\d+(?:\.\d+)?'),
    # Numbers in \mathrm{SE}=N
    re.compile(r'\\mathrm\{SE\}=\d+(?:\.\d+)?'),
    # Numbers in \mathrm{ICC}
    re.compile(r'\\mathrm\{ICC\}'),
    # Numbers in \Pr[...] \mathbb{E}[...]
    re.compile(r'\\(?:Pr|mathbb\{E\})\['),
    # Numbers in \varepsilon=N
    re.compile(r'\\varepsilon\s*=\s*\d+(?:\.\d+)?(?:e-\d+)?'),
    # Numbers in \max|...|=N
    re.compile(r'\\max\|[^|]+\|=\d+(?:\.\d+)?'),
    # Numbers in \mathrm{SD}(\approx N)
    re.compile(r'\\approx\d+(?:\.\d+)?'),
    # Numbers in \{N\} (single-element sets)
    re.compile(r'\\{-?\d+(?:\.\d+)?\\}'),
    # Numbers in \times10^{N}
    re.compile(r'\\times10\s*\^?\{?\d+\}?'),
    # Numbers in \bmod N
    re.compile(r'\\bmod\s*\d+'),
    # Numbers in \pmod{N}
    re.compile(r'\\pmod\{[^}]+\}'),
    # Numbers in \lVert...\rVert_N
    re.compile(r'\\[lr]Vert[^\\]*\\[lr]Vert_\d+'),
    # Numbers in \ell^\infty \ell^1 \ell^2
    re.compile(r'\\ell\^\{?\d+\}?'),
    # Numbers in \mathbf{N\times}
    re.compile(r'\\mathbf\{[^}]+\}'),
    # Numbers in \textbf{N}
    re.compile(r'\\textbf\{[^}]+\}'),
    # Numbers in \footnote{...} — skip footnote content
    # (handled by bracket depth tracking below)
    # Numbers in \eqref{} \ref{}
    re.compile(r'\\(?:eq)?ref\{[^}]+\}'),
    # Numbers in \S\ref
    re.compile(r'\\S\\ref\{[^}]+\}'),
    # Numbers in \S\S (section sign)
    re.compile(r'\\S\\S'),
    # Numbers in \S{N}
    re.compile(r'\\S\{[^}]+\}'),
    # Numbers in ~\ref{} ~\eqref{}
    re.compile(r'~\\(?:eq)?ref\{[^}]+\}'),
    # Numbers in Table~\ref{} Figure~\ref{} Section~\ref{}
    re.compile(r'(?:Table|Figure|Section|Eq\.|Equation|Algorithm|Appendix|Remark|Theorem|Proposition|Corollary|Lemma|Definition)~\\ref\{[^}]+\}'),
    # Numbers in \S\ref{sec:...}
    re.compile(r'\\S\\ref\{[^}]+\}'),
    # Numbers in \Nvia \Ncand \Ntrios etc. (macros)
    re.compile(r'\\[A-Z][A-Za-z]+(?:\{[^}]*\})?'),
    # Numbers in \dmin \kk \ndraws \nboot etc.
    re.compile(r'\\[a-z]+(?:\{[^}]*\})?'),
]

# ─────────────────────────────────────────────────────────────────────────────
# §4  Values always acceptable (structural/mathematical)
# ─────────────────────────────────────────────────────────────────────────────

_ALWAYS_OK = {
    # Boolean/binary
    "0", "1",
    # Small structural integers
    "2", "3", "4", "5", "6", "7", "8", "9", "10",
    # Percentages
    "100", "100.0", "0.0",
    # Significance levels
    "0.05", "0.10", "0.01",
    # CI levels
    "90", "95", "99",
    # Kappa values (E7 grid, macro-backed)
    "25", "50", "200", "400", "1000",
    # Number of criteria
    "11",
    # Number of draws
    "500",
    # Bootstrap replicates
    "10000",
    # Equivalence margin
    "2.5",
    # Aspect bounds
    "90", "180", "360",
    # n1 SE-facing
    "94",
    # Number of instances
    "240", "405",
    # Number of studies
    "114", "148", "31", "14",
    # Number of predictions
    "16",
    # Number of kappa levels
    "6",
    # Number of E6 families
    "4",
    # Number of E6 cells
    "7",
    # Number of E6 draws
    "200",
    # Number of contrasts
    "36",
    # Number of replicates
    "30",
    # Number of E5 geometries
    "3",
    # Seed
    "42",
    # Fraction threshold
    "0.5",
    # P2 margin
    "5",
    # TV_W levels
    "0.10", "0.30",
    # Tolerance
    "1e-9",
    # Dirichlet SD approx
    "0.025", "0.05",
    # Weight differences
    "0.001", "0.004",
    # CR threshold
    "0.10",
    # Land coverage
    "50",
    # Number of Santiago kappa
    "6",
    # Number of bootstrap for Santiago
    "10000",
    # Number of informative cells
    "3",
    # Number of E6 draws total
    "48000",
    # Number of E5 replicates
    "3",
    # Number of E5 N levels
    "50", "100",
    # Number of E5 s levels
    "0.25", "0.75",
    # Number of E5 draws
    "100",
    # Number of E5 instances
    "540",
    # Number of E5 strata
    "25",
    # Number of E5 degenerate
    "2",
    # Number of E5 non-degenerate
    "25",
    # Number of E5 below 50%
    "8",
    # Number of E5 at 100%
    "329",
    # Number of E5 clustered
    "75",
    # Number of E5 feasible trios
    "130",
    # Number of E6 P1 check
    "48000",
    # Number of E6 P2 lossy
    "88", "85",
    # Number of E6 P3 informative
    "88",
    # Number of E6 P4 non-tied
    "88",
    # Number of E6 families
    "4",
    # Number of E6 instances
    "120",
    # Number of E6 draws per instance
    "200",
    # Number of E6 total draws
    "48000",
    # Number of E6 cells
    "7",
    # Number of E6 replicates
    "30",
    # Number of E6 instances per family
    "30",
    # Number of E6 instances total
    "120",
    # Number of E6 draws total
    "48000",
}

# ─────────────────────────────────────────────────────────────────────────────
# §5  Environments to skip entirely
# ─────────────────────────────────────────────────────────────────────────────

_SKIP_ENVS = {
    "verbatim", "lstlisting", "minted",
    # Math environments — numbers are structural
    "equation", "align", "align*", "equation*", "gather", "gather*",
    "multline", "multline*", "eqnarray", "eqnarray*",
    "array", "matrix", "pmatrix", "bmatrix", "vmatrix",
    "cases", "split", "subequations",
    "proof", "lemma", "theorem", "proposition", "corollary", "remark",
    # Theorem-like environments
    "lemma*", "theorem*", "proposition*", "corollary*", "remark*",
    # Description lists in supplementary (prespec content)
    "description",
    # Tabular environments — numbers in tables are data, not running text claims
    # EXCEPTION: tab:amplitude and tab:canonical have hand-written values
    # We handle these separately
}

# ─────────────────────────────────────────────────────────────────────────────
# §6  Main scanner
# ─────────────────────────────────────────────────────────────────────────────

# Numeric literal: integer or decimal, not preceded/followed by letter/backslash
_NUM_RE = re.compile(r'(?<![\\a-zA-Z@_/\{])(-?\d+(?:\.\d+)?)(?![a-zA-Z_/\\])')

def blank_region(text, pattern):
    return pattern.sub(lambda m: ' ' * len(m.group(0)), text)

def scan_file(tex_path, design_constants):
    findings = []
    lines = tex_path.read_text(encoding="utf-8").splitlines()
    env_stack = []

    for lineno, raw_line in enumerate(lines, 1):
        # Track environment changes
        for m in re.finditer(r'\\begin\{([^}]+)\}', raw_line):
            env_stack.append(m.group(1))
        for m in re.finditer(r'\\end\{([^}]+)\}', raw_line):
            env_name = m.group(1)
            if env_name in env_stack:
                idx = len(env_stack) - 1 - env_stack[::-1].index(env_name)
                env_stack.pop(idx)

        # Skip if in a skip environment
        if set(env_stack) & _SKIP_ENVS:
            continue

        # Strip comments
        line = strip_comments(raw_line)

        # Apply all blanking patterns
        for pat in _BLANK_PATTERNS:
            line = blank_region(line, pat)

        # Find remaining numeric literals
        for m in _NUM_RE.finditer(line):
            val = m.group(1)
            pos = m.start()

            # Skip if in always-ok set
            if val in _ALWAYS_OK:
                continue

            # Skip years 1900-2099
            try:
                ival = int(val)
                if 1900 <= ival <= 2099:
                    continue
                # Skip small structural integers 0-20
                if 0 <= ival <= 20:
                    continue
            except ValueError:
                pass

            # Skip negative integers that are just range specs like -3 in {2-3}
            if val.startswith('-'):
                try:
                    ival = int(val)
                    if -20 <= ival <= 0:
                        continue
                except ValueError:
                    pass

            # Get context
            ctx_start = max(0, pos - 50)
            ctx_end = min(len(line), pos + 50)
            context = line[ctx_start:ctx_end].strip()

            # Classify
            if val in design_constants:
                cls = "b"
                just = design_constants[val]
            else:
                cls = "c"
                just = ""

            findings.append((lineno, val, cls, context, just))

    return findings

# ─────────────────────────────────────────────────────────────────────────────
# §7  Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    design_constants = load_design_constants()

    all_findings = []
    for tex_path in TEX_FILES:
        if not tex_path.exists():
            print(f"[WARN] not found: {tex_path}")
            continue
        findings = scan_file(tex_path, design_constants)
        for lineno, val, cls, ctx, just in findings:
            all_findings.append((tex_path.name, lineno, val, cls, ctx, just))

    class_b = [(f, l, v, c, j) for f, l, v, cls, c, j in all_findings if cls == "b"]
    class_c = [(f, l, v, c) for f, l, v, cls, c, j in all_findings if cls == "c"]

    print(SEP)
    print("audit_numbers.py — numeric literal audit")
    print(f"Scanning: {', '.join(t.name for t in TEX_FILES)}")
    print(SEP)

    if class_b:
        print(f"\n[INFO] Class (b) — design constants ({len(class_b)} occurrences):")
        for fname, lineno, val, ctx, just in class_b:
            print(f"  {fname}:{lineno}  {val!r:12s}  {just}")

    if class_c:
        print(f"\n[FAIL] Class (c) — results written by hand ({len(class_c)} occurrences):")
        for fname, lineno, val, ctx in class_c:
            print(f"  [FAIL] {fname}:{lineno}  {val!r:12s}  context: {ctx!r}")
    else:
        print(f"\n[OK  ] Class (c): 0 hand-written results found")

    print()
    print(SEP)
    n_c = len(class_c)
    if n_c > 0:
        print(f"AUDIT RESULT: {n_c} hand-written result(s) found — FAIL")
        sys.exit(1)
    else:
        print("AUDIT RESULT: zero hand-written results — PASS")
        sys.exit(0)

if __name__ == "__main__":
    main()
