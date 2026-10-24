# -*- coding: utf-8 -*-
import re
from pathlib import Path
ROOT = Path(__file__).parent.parent
suppl = (ROOT / 'supplementary.tex').read_text(encoding='utf-8')
macros_e6 = (ROOT / 'macros_e6.tex').read_text(encoding='utf-8')
block_start = suppl.find(r'\label{sec:e6-sensit}')
block_end   = suppl.find('% S0  Pre-registration')
block = suppl[block_start:block_end]
used = set(re.findall(r'\\(Esix[A-Za-z]+)', block))
defined = set(re.findall(r'newcommand\{\\([A-Za-z]+)\}', macros_e6))
missing = sorted(m for m in used if m not in defined)
print(f'Macros usados: {len(used)}')
print(f'Definidos:     {len(defined)}')
if missing:
    print('FALTA:')
    for m in missing:
        print(f'  \\{m}')
else:
    print('Todos OK - nenhum macro em falta')
