# DEV-SANT-TAG-001 — Historial de tags de lançamento (stage4-launch → r1 → r2 → r3)
Date: 2026-10-28 UTC
Type: nota de integridade pré-dados (sem resultado de MC calculado antes deste registo)

## Estado actual das tags no remote (git ls-remote --tags)

```
de7d9d7c  refs/tags/stage4-launch         (tag object)
d0635a32  refs/tags/stage4-launch^{}       (commit: add verify_stage4_sha.py)
8252fb81  refs/tags/stage4-launch-r1      (tag object)
bc41fd57  refs/tags/stage4-launch-r1^{}   (commit: stage4-prelaunch all 5 blockers)
460a1cca  refs/tags/stage4-launch-r2      (tag object)
fae83f0b  refs/tags/stage4-launch-r2^{}   (commit: hash annotation in TAG-001)
```

Nota: `stage4-launch` ficou em d0635a3 (add verify_stage4_sha.py). Não deve ser
usada como referência de lançamento; existe apenas para registo histórico.

## Historial completo

### stage4-launch → 7f1028d → d0635a3

A tag `stage4-launch` foi criada em 7f1028d ("pre-stage4: gate tolerances tightened,
DEV files, startup logging, DELTA_PP=2.5"), depois movida para d0635a3 ("add
verify_stage4_sha.py"). A tag ficou no remote a apontar para d0635a3.

### stage4-launch-r1 → bc41fd5

Tag criada após resolver os 5 bloqueadores pré-lançamento. Commit bc41fd5:
"stage4-prelaunch: TAG-001; gate perm=[2.855,2.865] correct; neg test near-boundary;
checkpoint SHA/commit verify; .gitignore npz/meta; timing explanation; launch cmds revised"

diff --stat 7f1028d..bc41fd5 (real — git diff --stat 7f1028d bc41fd5):
```
 .gitignore                   |  9 +++++++-
 TASKS_REVISION.md            | 46 +++++++++++++++++++++++++++++++++++++++-
 corpus/DEV-SANT-TAG-001.md   | 50 ++++++++++++++++++++++++++++++++++++++++++++
 corpus/DEV-SANT-ZDTI-001.md  |  2 +-
 scripts/compute_stage3b.py   | 46 +++++++++++++++++++++++++++-------------
 scripts/run_santiago_mc.py   | 42 +++++++++++++++++++++++++++++++++++++
 scripts/verify_stage4_sha.py | 24 +++++++++++++++++++++
 7 files changed, 201 insertions(+), 18 deletions(-)
```

Nota: run_santiago_mc.py FOI alterado entre 7f1028d e bc41fd5 (42 linhas).
A checklist A5 foi re-verificada sobre bc41fd5 — as alterações em run_santiago_mc.py
adicionaram apenas log_startup_provenance(), checkpoint SHA verify, DELTA_PP=2.5 e κ=∞=1 draw.
Nenhuma destas alterações modifica Q2, Pareto, bootstrap ou macros. Checklist válida.

### stage4-launch-r2 → fae83f0

Tag criada após correcções r2: gate perm repr/1e-9/boundary±0.0001; mc_full log
gitignore; SHA-256 completo + uv.lock hash; DEV-A5 reescrita; DEV-TAG hash fix;
DEV-SPACING regra pré-fixada; DEV-ZDTI datas.

diff --stat bc41fd5..fae83f0 (real — git diff --stat bc41fd5 fae83f0):
```
 .gitignore                     |   1 +
 corpus/DEV-SANT-A5-001.md      | 153 +++++++++++++++++++++++++++++------------
 corpus/DEV-SANT-SPACING-001.md |  12 ++++
 corpus/DEV-SANT-TAG-001.md     | 112 +++++++++++++++++++++++-------
 corpus/DEV-SANT-ZDTI-001.md    |  15 +++-
 scripts/compute_stage3b.py     |  95 +++++++++++++++++--------
 scripts/run_santiago_mc.py     |  16 ++++-
 7 files changed, 300 insertions(+), 104 deletions(-)
```

### stage4-launch-r3 → [a criar neste commit]

Tag a criar após correcções r3: DEV-A5 buffer/proveniência/SENS-AGR; DEV-SPACING
data/descoberta/sensibilidade-1.25km; DEV-ZDTI pesos/autor/persistente/email;
DEV-TAG diff real; run_santiago_mc.py w0 assert.

O diff fae83f0..[r3] e a checklist A5 vão na mensagem da tag anotada (não neste ficheiro,
que não consegue conter o hash do commit em que está). Usar:
```bash
git tag -a stage4-launch-r3 --no-sign -m "
r3: DEV-A5 buffer PRESPEC explicit (0m, not deviation); SENS-AGR-1/2/BUF mandatory;
provenance 249 not 387; DEV-SPACING date/discovery/1.25km sensitivity;
DEV-ZDTI weights denom 0.9637, author discrepancy, persistent, email;
DEV-TAG real diffs; mc.py w0 assert in log

diff --stat fae83f0..[r3_hash]: [to be filled]

A5 checklist on r3:
- seeds KAPPA_VALUES=[25,50,100,200,400,1000] parent=[1,4,15,17,28,30] SeedSequence.spawn(2) PASS
- N_DRAWS=500, B_BOOT=2000 PASS
- K1 abort (K1 FAIL → return abort) PASS
- kappa=inf = 1 draw (DEV-SANT-KINF-001) PASS
- E1 cells at κ=200 and κ=inf only PASS
- Bootstrap paired, Holm K4 PASS
- DELTA_PP=2.5 PASS
- git status --untracked-files=no in log PASS
- SHA-256 full (64 hex) for CSVs + uv.lock hash PASS
- w0 assert in log_startup_provenance() PASS
"
git push origin stage4-launch-r3
```

## v1.7 tag state

A tag v1.7 local é lightweight (aponta directamente para o commit a7092642).
A tag v1.7 remota é annotated (objecto 92b98e50 → commit a7092642).
Ambas apontam para o MESMO commit. A rejeição no push --tags foi porque os objectos
de tag são diferentes (lightweight vs annotated). Não é uma divergência de conteúdo.
Resolução: apagar v1.7 local e fazer fetch do remote.
```bash
git tag -d v1.7
git fetch origin refs/tags/v1.7:refs/tags/v1.7
git push origin <tag> para publicar tags futuras (nunca --tags global)
```

## Não houve contaminação de resultados

Em nenhum dos commits r1, r2, r3: nenhum cálculo de Q2, R, score ou fronteira para
Santiago foi executado. Os logs de timing (DEV-SANT-TIMING-001) guardaram apenas
duração e K1; sem Q2 guardado. Nenhuma decisão de análise dependeu dos dados de Santiago.
