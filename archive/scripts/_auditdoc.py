content_p  = open('C:/Users/julio/.kiro/steering/personal.md', encoding='utf-8').read()
content_l  = open('C:/Users/julio/.kiro/steering/latex-paper-standards.md', encoding='utf-8').read()
content_aw = open('C:/Users/julio/.kiro/agents/academic-writer.md', encoding='utf-8').read()
content_pr = open('C:/Users/julio/.kiro/agents/peer-reviewer/AGENT.md', encoding='utf-8').read()
content_rb = open('C:/Users/julio/.kiro/agents/rebuttal-assistant/AGENT.md', encoding='utf-8').read()

checks = [
    ('Formulas longas -> display (multline)',  'multline',            [content_p, content_l, content_aw]),
    ('Build 4 passes xelatex+bibtex',          '4 passes',            [content_p]),
    ('Proibido \\paragraph{}',                 'paragraph',           [content_p, content_l]),
    ('Seccao com 1 paragr proibida',           'unico',               [content_p]),
    ('Titulo seccao max ~50 chars',            '50',                  [content_p]),
    ('Captions curtas sem interpretacao',      'interpretacao',       [content_l]),
    ('Captions sem analise (rule)',             'Proibido na caption', [content_l]),
    ('Refs internas proibidas',                'referencias internas',[content_l, content_aw]),
    ('Travessoes proibidos',                   'travessao',           [content_l, content_aw]),
    ('Abstract 150-250 palavras',              '150',                 [content_l]),
    ('MCDM terminologia (implicit re-weighting)', 'implicit re-weighting', [content_aw]),
    ('MCDM venues Omega/EJOR',                 'Omega',               [content_aw]),
    ('peer-reviewer cobre OR/MS',              'EJOR',                [content_pr]),
    ('rebuttal-assistant cobre OR/MS',         'Omega',               [content_rb]),
    ('Equacoes overflow checklist',            'overflow',            [content_l, content_aw]),
    ('Formulas reutilizadas com eqref',        'reutilizad',          [content_p]),
    ('Titulo seccao desc (academic-writer)',   '50',                  [content_aw]),
]

print('AUDITORIA DE PREFERENCIAS NO .kiro')
print('-' * 55)
missing = []
for label, kw, files in checks:
    found = any(kw.lower() in f.lower() for f in files)
    status = 'OK     ' if found else 'MISSING'
    print(f'  {status}: {label}')
    if not found:
        missing.append(label)

print()
if missing:
    print(f'FALTAM {len(missing)} items:')
    for m in missing:
        print(f'  - {m}')
else:
    print('Tudo documentado.')
