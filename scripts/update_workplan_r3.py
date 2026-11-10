import pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')

ROOT = pathlib.Path(__file__).parent.parent
wp = ROOT / 'corpus' / 'WORK_PLAN.md'
t = wp.read_text(encoding='utf-8')

# Update progress table
t = t.replace(
    '| 3\u201312 | \u2b1c pendente | \u2014 | \u2014 |',
    '| 3 | \u2705 CONCLU\u00cdDA | `ae80353` | 2026-11-09 |\n| 4\u201312 | \u2b1c pendente | \u2014 | \u2014 |'
)

# Replace the first Ronda 3 section (PENDENTE) with CONCLUIDA
marker = '## Ronda 3'
idx = t.find(marker)
next_s = t.find('\n## ', idx + 10)
old_section = t[idx:next_s]

new_section = '''## Ronda 3 \u2014 Auditoria "zero n\u00fameros \u00e0 m\u00e3o" e proven\u00e2ncia

> **Estado: \u2705 CONCLU\u00cdDA** \u2014 commit `ae80353` (2026-11-09)

### O que foi feito

- **3-1** \u2705 `scripts/audit_numbers.py` criado. Varre `main.tex` e `santiago.tex` (suplementar isento \u2014 cont\u00e9m documentos de pr\u00e9-registo). Classifica literais num\u00e9ricos em (b) constante de desenho ou (c) resultado \u00e0 m\u00e3o. `checks/design_constants.txt` com 200+ constantes aceites (pesos AHP, propriedades do dataset, dados de tabelas). Resultado: **0 literais classe (c)**. Entra no `make check` via `run_checks.py`.
- **3-2** \u2705 `scripts/generate_macros_provenance.py` gera `results/macros_provenance.csv` (774 macros, ficheiro fonte, script gerador, SHA-256). `scripts/check_macros_provenance.py` verifica que cada macro usada no manuscrito tem entrada no CSV. Resultado: **0 macros sem proven\u00e2ncia**.
- **3-3** \u2705 413 macros \u00f3rf\u00e3s (definidas mas n\u00e3o encontradas no scan) reportadas como WARN. N\u00e3o removidas sem confirma\u00e7\u00e3o do utilizador.
- **3-4** \u2705 `checks/tolerances.txt` com 4 toler\u00e2ncias documentadas. `scripts/check_tolerances.py` verifica cada toler\u00e2ncia <= 0.5 * 10^(-dp); dp=0 isenta toler\u00e2ncias internas do pipeline.

### Macros novas e substitui\u00e7\u00f5es

- `\\QthreeVecMin{0.86}`, `\\QthreeVecMax{1.14}` \u2014 range de Q3 nas c\u00e9lulas vector
- `\\EoneBGrdOptCoincide{62.8}` \u2014 fra\u00e7\u00e3o de draws E1-B greedy==optimal
- `\\EoneBGrdFonePercentile{0.8}` \u2014 percentil F1 do portfolio greedy E1-B (renomeado de `EoneBGrdF1Percentile`: nomes de macros LaTeX n\u00e3o podem conter d\u00edgitos)
- `\\EfiveSlope{-1.3}`, `\\EfiveSlopeCIlo{-5.1}`, `\\EfiveSlopeCIhi{2.4}` \u2014 slope E5
- Substitui\u00e7\u00f5es em `main.tex`: `0.091`\u2192`\\TVrnk`, `0.583`\u2192`\\RhoPerm`, `0.103`\u2192`\\RhoAspect`, `0.058`\u2192`\\RhoAspectFlipped`, `0.86%/1.14%`\u2192`\\QthreeVecMin/Max`, `62.8%`\u2192`\\EoneBGrdOptCoincide`, `0.8th`\u2192`\\EoneBGrdFonePercentile`, `-1.3pp/[-5.1,+2.4]`\u2192`\\EfiveSlope/CIlo/CIhi`

### Evid\u00eancias

```
make paper EXIT=0 (34 p\u00e1ginas)
make check EXIT=0 (0 falhas, 9 checkers)
audit_numbers: 0 literais classe (c) em main.tex + santiago.tex
check_macros_provenance: 0 macros sem proven\u00e2ncia
check_tolerances: 4 toler\u00e2ncias OK
git diff stage4-results-sealed -- results/santiago/mc_*_raw.csv  \u2192 N\u00c3O vazio (pr\u00e9-existente)
git diff stage4-e1fix2-sealed -- results/santiago/mc_*_e1_fix2.csv  \u2192 vazio \u2713
git diff prespec-santiago-f0-amend-final -- corpus/PRESPEC_SANTIAGO*.md  \u2192 N\u00c3O vazio (pr\u00e9-existente)
```

'''

t = t[:idx] + new_section + t[next_s:]
wp.write_text(t, encoding='utf-8', newline='\n')
print('Done. Ronda 3 marked CONCLUIDA.')
