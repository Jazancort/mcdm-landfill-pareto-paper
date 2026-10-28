"""
fix_emdashes.py  —  remove --- (em-dash) de prosa e substitui por pontuação correcta.
Regra: --- como separador parentético → vírgulas; --- como pausa forte → ponto e vírgula ou dois pontos.
"""

with open('main.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# Cada substituição: (padrão exacto, substituição)
replacements = [
    # L100
    ('agreement with one another --- which establishes that methods differ, but',
     'agreement with one another, which establishes that methods differ, but'),

    # L156-157
    ('The decision is therefore a \\emph{portfolio} problem --- choose $\\kk$\nsites out of $N$ subject to a minimum pairwise separation --- rather than',
     'The decision is therefore a \\emph{portfolio} problem: choose $\\kk$\nsites out of $N$ subject to a minimum pairwise separation, rather than'),

    # L179
    ('exact Pareto frontier over three group-level objectives --- siting cost,',
     'exact Pareto frontier over three group-level objectives: siting cost,'),

    # L190
    ('with a $95\\%$ interval of $[-0.5,\\,+2.3]$ --- statistically',
     'with a $95\\%$ interval of $[-0.5,\\,+2.3]$, statistically'),

    # L227, L229
    ('Adding integer programming on top of a ranking --- the established\nupgrade path in portfolio MCDM~\\citep{BransMareschal1992,Mavrotas2006,VetscheraDeAlmeida2012} --- pays',
     'Adding integer programming on top of a ranking, the established\nupgrade path in portfolio MCDM~\\citep{BransMareschal1992,Mavrotas2006,VetscheraDeAlmeida2012}, pays'),

    # L239
    ('to $80$~pp of Pareto efficiency --- far more than the re-weighting alone',
     'to $80$~pp of Pareto efficiency, far more than the re-weighting alone'),

    # L251, L253
    ('    Three effects previously reported separately --- vector-normalisation\n    bias, the assembly gain, and the amplitude shrinkage that results\n    from normalising over inadmissible alternatives --- become corollaries',
     '    Three effects previously reported separately, namely vector-normalisation\n    bias, the assembly gain, and the amplitude shrinkage that results\n    from normalising over inadmissible alternatives, become corollaries'),

    # L751-755 (lista com ---)
    ('  \\item $\\wsc$ --- the weights in the \\emph{method score}, which order',
     '  \\item $\\wsc$: the weights in the \\emph{method score}, which order'),
    ('  \\item $\\wob$ --- the weights used to map the assembled portfolio to',
     '  \\item $\\wob$: the weights used to map the assembled portfolio to'),
    ('  \\item $\\wfr$ --- the weights used to build the reference set,',
     '  \\item $\\wfr$: the weights used to build the reference set,'),

    # L800
    ('selectable --- a set-dependence mechanism documented for TOPSIS by',
     'selectable, a set-dependence mechanism documented for TOPSIS by'),

    # L872
    ('against predicted distortions $\\mathrm{TV}=0$, $0.091$ and $0.315$ ---',
     'against predicted distortions $\\mathrm{TV}=0$, $0.091$ and $0.315$,'),

    # L948
    ('Corollary~\\ref{cor:three}(iii) --- independent of $n_1$.',
     'Corollary~\\ref{cor:three}(iii), independent of $n_1$.'),

    # L1038-1039
    ('Dividing midranks by $N+1$ --- the conventional rescaling to $(0,1)$\n--- does not equalise criterion amplitudes when ties are massive.',
     'Dividing midranks by $N+1$, the conventional rescaling to $(0,1)$,\ndoes not equalise criterion amplitudes when ties are massive.'),

    # L1141
    ('  construction --- all lines are horizontal at their nominal level (dashed',
     '  construction: all lines are horizontal at their nominal level (dashed'),

    # L1291
    ('performance, restricted to additive aggregation --- the scope in which',
     'performance, restricted to additive aggregation, the scope in which'),

    # L1319-1320
    ('The claim we make is the analytic one of Corollary~\\ref{cor:three} ---\nmin--max is the unique weight-preserving choice among the three ---',
     'The claim we make is the analytic one of Corollary~\\ref{cor:three}:\nmin--max is the unique weight-preserving choice among the three,'),

    # L1439
    ('Greedy assembly, being myopic, is partly insulated --- it fails for its',
     'Greedy assembly, being myopic, is partly insulated; it fails for its'),

    # L1593
    ('--- the former is a combinatorial loss, the latter a re-parameterisation',
     'the former is a combinatorial loss, the latter a re-parameterisation'),

    # L1770-1771
    ('Where elicited weights carry normative content --- as with AHP judgements\nfrom stakeholders --- a normalisation that silently reweights them is',
     'Where elicited weights carry normative content, as with AHP judgements\nfrom stakeholders, a normalisation that silently reweights them is'),

    # L1831-1832
    ('The choice of aggregation operator --- the variable the applied\nliterature compares most --- proved the least consequential of the three,',
     'The choice of aggregation operator, the variable the applied\nliterature compares most, proved the least consequential of the three,'),

    # L1843
    ('its weight, and rank rescaling penalises criteria with heavy tie mass ---',
     'its weight, and rank rescaling penalises criteria with heavy tie mass;'),

    # L1855-1856
    ('Second, normalising over alternatives that cannot be selected --- in our\ndata the $\\Nexcl$ candidates overlapping protected areas --- calibrates',
     'Second, normalising over alternatives that cannot be selected, in our\ndata the $\\Nexcl$ candidates overlapping protected areas, calibrates'),

    # L1892-1893
    ('Where the feasible set is enumerable --- as it is for\ncardinality-constrained siting problems of realistic size --- an exact',
     'Where the feasible set is enumerable, as it is for\ncardinality-constrained siting problems of realistic size, an exact'),
]

n_replaced = 0
for old, new in replacements:
    if old in text:
        text = text.replace(old, new)
        n_replaced += 1
    else:
        print(f'NOT FOUND: {repr(old[:60])}')

with open('main.tex', 'w', encoding='utf-8') as f:
    f.write(text)

print(f'\nSubstituições aplicadas: {n_replaced}/{len(replacements)}')

# Verificar se ainda há ---
import re
lines = text.split('\n')
remaining = [(i+1, l) for i, l in enumerate(lines)
             if '---' in l and '&' not in l and not l.strip().startswith('%')]
print(f'--- restantes em prosa: {len(remaining)}')
for ln, l in remaining:
    print(f'  L{ln}: {l[:100]}')
