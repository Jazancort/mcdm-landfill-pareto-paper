import re, sys

path = 'main.tex'
raw = open(path, encoding='utf-8').read()
lines = raw.splitlines()

def check(label, pat, context=True, invert=False, limit=6):
    """Search for pattern; invert=True means absence is the issue."""
    hits = [(i+1, l.strip()) for i, l in enumerate(lines)
            if not l.strip().startswith('%') and re.search(pat, l)]
    if invert:
        if not hits:
            print(f'  ISSUE: {label}')
        return
    shown = hits[:limit]
    if shown:
        print(f'  FOUND ({len(hits)} hits): {label}')
        if context:
            for ln, txt in shown:
                print(f'    L{ln}: {txt[:100]}')

def abstract_check():
    m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', raw, re.DOTALL)
    if not m:
        print('  CRITICAL: no abstract found')
        return
    text = re.sub(r'\\[a-zA-Z]+(\{[^}]*\})*', ' ', m.group(1))
    words = len(text.split())
    print(f'  Abstract word count: ~{words}')
    # Last sentence
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
    if sentences:
        print(f'  Last sentence: {sentences[-1][:120]}')

# ============================================================
print('=== ITEM 2: EPISTEMIC RULES ===')

# Causal verbs without identification
check('proves (empirical)', r'\bproves?\b(?! that [A-Z])')
check('demonstrates mechanism', r'demonstrate[sd]? (?:the )?mechanism')
check('attributable to (no experiment)', r'attributable to')
check('mechanisms driving', r'mechanism[s]? driving')
check('opposite mechanisms', r'opposite mechanism')

# Overclaim hedging
check('"clearly" or "obviously"', r'\b(clearly|obviously|it is clear|it is obvious)\b')
check('"likely" or "probably"', r'\b(likely|probably)\b')
check('"essentially"', r'\bessentially\b')
check('"groundbreaking/novel/unprecedented"', r'\b(groundbreaking|unprecedented)\b')
check('"significantly" without stat test nearby', r'\bsignificantly\b')
check('"robust" (vague)', r'\brobust\b')
check('"state-of-the-art"', r'state.of.the.art')

# ============================================================
print()
print('=== ITEM 3: STYLE RULES ===')

# Em-dashes as separators (--- or Unicode —)
check('em-dash as separator (---)', r'(?<![\\])---(?![\*\[\{])')
check('em-dash Unicode (—)', r'—')
# En-dash as separator outside math contexts
check('en-dash as phrase separator (-- outside math/range)', 
      r'(?<![0-9~\$\{A-Za-z])--(?![0-9\$\}A-Za-z])')

# Defensive language
check('defensive: "this is not X"', r'[Tt]his is not (a |an |the )?(?:error|mistake|bias|problem|flaw)')
check('defensive: "this was not"', r'[Tt]his was not')
check('defensive: "not a design error"', r'not a design')
check('meta-commentary "We state this explicitly"', r'[Ww]e state this explicitly')
check('meta-commentary "for clarity"', r'for clarity(?! of)')

# Internal references
check('script filename in body', r'(?<!\\verb)[a-z_]+\.(py|csv|json|txt|R)\b')
check('git branch/hash in body', r'\b(main|HEAD|origin|v[12]\.[0-9])\b')

# Bullet points in body text  
check('itemize/enumerate in body (not appendix)', r'\\begin\{(itemize|enumerate)\}')

# "performance" as generic metric
check('"performance" generic', r'\bperformance\b(?! measure| metric| gap| profile| assessment)')

# ============================================================
print()
print('=== ITEM 4: LATEX TECHNICAL ===')

# Unresolved refs
qmarks = sum(1 for l in lines if '??' in l and not l.strip().startswith('%'))
print(f'  ?? count: {qmarks}')

# hline instead of booktabs
check('\\hline (should use booktabs)', r'\\hline')
# Midrule before bottomrule
check('\\midrule immediately before \\bottomrule', r'\\midrule\s*\\bottomrule')
# No vertical lines... actually check for |c| or |l| in tabular
check('vertical lines in tabular', r'\\begin\{tabular\}\{[^}]*\|[^}]*\}')
check('[TBD] placeholder', r'\[TBD\]|\bTBD\b')
# Mixed image extensions
exts = set(re.findall(r'\\includegraphics[^{]*\{[^}]+\.([a-zA-Z]+)\}', raw))
print(f'  Image extensions used: {exts}')
# Paragraph hierarchy
check('\\paragraph{} (verify renders as inline italic)', r'\\paragraph\{')
# Table without intro sentence - check for \begin{table} right after section heading
check('table right after section heading (no intro sentence)', 
      r'\\(sub)*section\{[^}]+\}\s*\\label\{[^}]+\}\s*\\begin\{table')

# ============================================================
print()
print('=== ITEM 5: ABSTRACT ===')
abstract_check()

# ============================================================
print()
print('=== ITEM 6: MCDM TERMINOLOGY ===')

# Terms that MUST appear (invert=False checks presence)
print('  --- MUST EXIST ---')
check('implicit re-weighting defined with \\emph', r'\\emph\{implicit re.weighting\}', invert=False)
check('effective weight ($w.*eff$)', r'w.*\{\\mathrm\{eff\}\}|w.*eff', invert=False)
check('amplitude ($A_j$)', r'A_j|A_\{j\}', invert=False)
check('mismatch defined', r'\\emph\{mismatch\}|mismatch', invert=False)
check('exact Pareto frontier', r'exact Pareto', invert=False)

# Forbidden synonyms (should not exist)
print('  --- MUST NOT EXIST ---')
check('normalisation bias (forbidden synonym)', r'normalisation bias')
check('weight distortion (forbidden synonym)', r'weight distortion')
check('"spread" as synonym for amplitude', r'\bspread\b(?! of | in | across )')
check('"Pareto front" (use "frontier")', r'Pareto front(?!ier)')
check('"actual weight" / "real weight"', r'\b(actual|real) weight')
check('"ILP post-processing"', r'ILP post.process')

# ============================================================
print()
print('=== ITEM 7: INTRODUCTION AND DISCUSSION STRUCTURE ===')

# Introduction: check for key paragraph markers
intro_text = '\n'.join(lines[154:316])
print('  --- INTRODUCTION ---')
print(f'  "Applied practice.*however" present: {bool(re.search(r"Applied practice.*however", intro_text))}')
print(f'  "ranking procedures" present: {bool(re.search(r"ranking procedures", intro_text))}')
print(f'  roadmap sentence present: {bool(re.search(r"Section.*review|organised as follows|paper is (structured|organised)", intro_text))}')
print(f'  quantitative findings in intro: {bool(re.search(r"[0-9]+[.,][0-9]+\s*pp|\\\\[A-Z][a-z]+pp|percentage.point", intro_text))}')

# Discussion: check for key patterns
disc_text = '\n'.join(lines[2429:2830])
print()
print('  --- DISCUSSION ---')
print(f'  Opens with "two.*mechanisms" or "separate": {bool(re.search(r"(two|2).*mechanism|separate.*mechanism", disc_text[:500]))}')
print(f'  "\\emph{{...}}" mechanism names present: {bool(re.search(r"\\\\emph\\{", disc_text))}')
print(f'  "Re-weighting is a modelling error" present: {bool(re.search(r"[Rr]e.weighting is a modelling error", disc_text))}')
print(f'  "Mismatch is a specification error" present: {bool(re.search(r"[Mm]ismatch is a specification error", disc_text))}')
print(f'  "The explanation is analytical" present: {bool(re.search(r"explanation is analytical", disc_text))}')
print(f'  "Two consequences bear directly on practice" present: {bool(re.search(r"[Tt]wo consequences bear", disc_text))}')
