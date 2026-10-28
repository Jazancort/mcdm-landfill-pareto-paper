# DEV-SANT-TAG-001 — Tag stage4-launch movida de 7f1028d para d0635a3
Date: 2026-10-28 UTC
Type: nota de integridade pré-dados (sem resultado de MC calculado antes deste registo)

## O que aconteceu

A tag `stage4-launch` foi criada e publicada em 7f1028d:
- Commit 7f1028d: "pre-stage4: gate tolerances tightened..."
- Tag criada com `git tag -a stage4-launch` → push

Em seguida, foi adicionado `scripts/verify_stage4_sha.py` (utilitário de verificação de SHAs)
no commit d0635a3: "add verify_stage4_sha.py for pre-run data integrity check".

A tag foi deletada e recriada em d0635a3, com push forçado.

## diff --stat entre os dois commits

```
 scripts/verify_stage4_sha.py | 24 ++++++++++++++++++++++++
 1 file changed, 24 insertions(+)
```

`scripts/run_santiago_mc.py` NÃO foi alterado entre 7f1028d e d0635a3.

## Checklist A5 mantém-se válida

A verificação da checklist da PRESPEC_SANTIAGO_A5 foi feita sobre o script
`run_santiago_mc.py` ao commit 7f1028d. Como esse ficheiro não mudou, a checklist
permanece válida para d0635a3.

## Não houve contaminação de resultados

Entre a criação da tag em 7f1028d e a adição de `verify_stage4_sha.py` em d0635a3:
- Nenhum cálculo de Q2, R, score ou fronteira para Santiago foi executado.
- A única operação foi adicionar o script utilitário `verify_stage4_sha.py`.
- O log de timing (5 sorteios/κ, K1 apenas) foi registado em DEV-SANT-TIMING-001.

## Tag correcta

A tag canónica para Stage 4 é `stage4-launch-r1` em d0635a3.
A tag `stage4-launch` original (7f1028d) existe como objecto na história do git
mas não deve ser usada como referência de lançamento.

## Como verificar na Athena

```bash
git fetch --tags --force origin
git describe --exact-match --tags d0635a3   # deve devolver stage4-launch-r1
git log --oneline 7f1028d..d0635a3          # deve mostrar só 1 commit (verify_stage4_sha.py)
```
