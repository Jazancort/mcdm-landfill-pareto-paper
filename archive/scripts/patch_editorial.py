"""patch_editorial.py — converte remarks em paragraphs e table->table*

Edições:
1. 5 \begin{remark} → \paragraph{}
2. tab:amplitude: \begin{table} → \begin{table*}  e  \end{table} → \end{table*}
3. Clarifica "source study" em §7.1
"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

path = 'main.tex'
with open(path, encoding='utf-8') as f:
    src = f.read()

original_len = len(src)

# ── 1. Remark: what the benchmark is, and is not ────────────────────────
old = (r'\begin{remark}[what the benchmark is, and is not]'
       '\n\\label{rem:valuespace}')
new = (r'\paragraph{What the benchmark is, and is not.}'
       '\n\\label{rem:valuespace}')
src = src.replace(old, new, 1)

end_marker_1 = (
    'collapses them into a single score before the portfolio is assembled.\n'
    r'\end{remark}')
end_replace_1 = (
    'collapses them into a single score before the portfolio is assembled.')
src = src.replace(end_marker_1, end_replace_1, 1)

# ── 2. Remark: coherence condition ──────────────────────────────────────
old2 = (r'\begin{remark}[coherence condition]'
        '\n\\label{rem:coherence}')
new2 = (r'\paragraph{Coherence condition.}'
        '\n\\label{rem:coherence}')
src = src.replace(old2, new2, 1)

end2 = ('per draw.\n'
        r'\end{remark}')
rep2 = ('per draw; we state it explicitly to make the constraint auditable.')
src = src.replace(end2, rep2, 1)

# ── 3. Remark: scope and empirical confirmation ──────────────────────────
old3 = (r'\begin{remark}[scope and empirical confirmation]'
        '\n\\label{rem:scope}')
new3 = (r'\paragraph{Scope and empirical confirmation.}'
        '\n\\label{rem:scope}')
src = src.replace(old3, new3, 1)

end3 = ('it is visible exactly where a weighted sum is taken.\n'
        r'\end{remark}')
rep3 = ('it is visible exactly where a weighted sum is taken.')
src = src.replace(end3, rep3, 1)

# ── 4. Remark: anonymous (Proposition p1 coherence) ─────────────────────
old4 = ('\\begin{remark}\n'
        'Proposition~\\ref{prop:p1} holds for any normalisation, so long as the\n'
        'normalisation used to compute $F_\\ell$ matches the one in the score $s$.\n'
        'We use the $Q_2 = 1$ cell as a regression test: any implementation\n'
        'returning a value below~$1$ is faulty.\n'
        '\\end{remark}')
new4 = ('\\paragraph{Normalisation coherence in Proposition~\\ref{prop:p1}.}\n'
        'Proposition~\\ref{prop:p1} holds for any normalisation, provided the\n'
        'normalisation used to compute $F_\\ell$ matches the one in the score $s$.\n'
        'The $Q_2 = 1$ cell serves as a regression test: any implementation\n'
        'returning a value below~$1$ is faulty.')
src = src.replace(old4, new4, 1)

# ── 5. Remark: rank scaling is not innocuous ────────────────────────────
old5 = (r'\begin{remark}[rank scaling is not innocuous]'
        '\n\\label{rem:p2normalization}')
new5 = (r'\paragraph{Rank scaling is not innocuous.}'
        '\n\\label{rem:p2normalization}')
src = src.replace(old5, new5, 1)

end5 = ('two normalisations.\n'
        r'\end{remark}')
rep5 = 'two normalisations.'
src = src.replace(end5, rep5, 1)

# ── 6. tab:amplitude: table → table* ────────────────────────────────────
# The caption begins right after \begin{table}[t]
src = src.replace(
    '\\begin{table}[t]\n\\centering\n\\caption{Effective-weight amplitudes',
    '\\begin{table*}[t]\n\\centering\n\\caption{Effective-weight amplitudes',
    1)

# The end{table} immediately followed by the figure*
src = src.replace(
    '\\end{tabular}\n\\end{table}\n\n\\begin{figure*}[htbp]',
    '\\end{tabular}\n\\end{table*}\n\n\\begin{figure*}[htbp]',
    1)

# ── 7. Clarify "source study" in §7.1 ───────────────────────────────────
src = src.replace(
    'the best-compromise portfolio of the source study\n\\citep{AzancortNeto2026},',
    'the best-compromise portfolio identified by \\citet{AzancortNeto2026}\n'
    '(using the AHP weights of \\citealt{Andrade2015}),',
    1)

# ── Verify changes ───────────────────────────────────────────────────────
checks = {
    'rem:valuespace paragraph': r'\paragraph{What the benchmark',
    'rem:coherence paragraph': r'\paragraph{Coherence condition',
    'rem:scope paragraph': r'\paragraph{Scope and empirical',
    'rem:p1 paragraph': r'\paragraph{Normalisation coherence',
    'rem:p2norm paragraph': r'\paragraph{Rank scaling is not',
    'table* start': r'\begin{table*}[t]',
    'table* end': r'\end{table*}',
    'no remark envs left': None,
}

print('Verification:')
for name, pattern in checks.items():
    if pattern is None:
        count = src.count(r'\begin{remark}')
        status = 'OK (0)' if count == 0 else f'FAIL ({count} remaining)'
        print(f'  {name}: {status}')
    else:
        status = 'OK' if pattern in src else 'FAIL - NOT FOUND'
        print(f'  {name}: {status}')

print(f'\nSize: {original_len} → {len(src)} chars')

with open(path, 'w', encoding='utf-8') as f:
    f.write(src)
print('Written.')
