# -*- coding: utf-8 -*-
"""Extract unique cod_form + lit from geologia_santiago_wfs.geojson."""
import json, pathlib, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = pathlib.Path('05-referencia/Novos/geologia_santiago_wfs.geojson')
data = json.loads(p.read_text(encoding='utf-8'))
features = data['features']
print(f'Total features: {len(features)}')

seen = {}
for f in features:
    props = f['properties']
    cod   = props.get('cod_form') or ''
    lit   = props.get('lit') or ''
    grupo = props.get('grupo') or ''
    idade = props.get('idade') or ''
    if cod not in seen:
        seen[cod] = {'lit_values': set(), 'grupo': grupo, 'idade': idade}
    seen[cod]['lit_values'].add(lit)

print(f'Unique cod_form: {len(seen)}')
print()
print(f"{'cod_form':<10} | {'grupo':<25} | {'idade':<28} | lit")
print('-' * 110)
for cod in sorted(seen.keys(), key=lambda x: x or ''):
    d = seen[cod]
    lits  = ' | '.join(sorted(d['lit_values']))
    grupo = d['grupo']
    idade = d['idade']
    print(f'{cod:<10} | {grupo:<25} | {idade:<28} | {lits}')
    d = seen[cod]
    lits = ' | '.join(sorted(d['lit_values']))
    grupo = d['grupo'] or ''
    idade = d['idade'] or ''
    cod_s = cod or '(None)'
    print(f'{cod_s:<10} | {grupo:<25} | {idade:<28} | {lits}')
