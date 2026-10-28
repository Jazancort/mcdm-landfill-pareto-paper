import re

path = '/home/julioazancort/scratch/mcdm/scripts/mcdm_experiment.py'
with open(path, encoding='utf-8') as f:
    src = f.read()

new_block = (
    "_MCDM_DIR = '/home/julioazancort/scratch/mcdm'\n"
    "GIS_BASE     = _MCDM_DIR\n"
    "IEEE_RESULTS = _MCDM_DIR\n"
    "CACHE_CSV    = _MCDM_DIR + '/df_real_data_cached.csv'\n"
    "PARETO_CSV   = _MCDM_DIR + '/exhaustive_search_pareto.csv'\n"
    "BCS_CSV      = _MCDM_DIR + '/best_compromise_sites.csv'\n"
)

# Substituir o bloco GIS_BASE até BCS_CSV inclusive
src = re.sub(
    r'GIS_BASE = os\.path\.join\(.*?BCS_CSV\s*=\s*os\.path\.join\([^\n]+\n',
    new_block,
    src,
    flags=re.DOTALL
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(src)

# Verificar
lines = src.split('\n')
for i, line in enumerate(lines):
    if 'MCDM_DIR' in line or 'CACHE_CSV' in line or 'GIS_BASE' in line:
        print(f'L{i+1}: {line}')
print('patch OK')
