# DEV-SANT-TAG-001 — Historial de tags de lançamento (stage4-launch → r1 → r2)
Date: 2026-10-28 UTC
Type: nota de integridade pré-dados (sem resultado de MC calculado antes deste registo)

## O que aconteceu (r1)

A tag `stage4-launch` foi criada e publicada em 7f1028d:
  "pre-stage4: gate tolerances tightened; negative test; DEV-SANT-TIMING/KINF/ZDTI-retry;
   startup logging; DELTA_PP=2.5; S5 table per criterion"

Em seguida, foi adicionado `scripts/verify_stage4_sha.py` no commit d0635a3:
  "add verify_stage4_sha.py for pre-run data integrity check"

A tag foi deletada e recriada em d0635a3. No entanto, commits adicionais foram
necessários para resolver todos os bloqueadores pré-lançamento, levando a bc41fd5:
  "stage4-prelaunch: TAG-001; gate perm=[2.855,2.865] correct; neg test
   near-boundary; checkpoint SHA/commit verify; .gitignore npz/meta;
   timing explanation; launch cmds revised"

A tag `stage4-launch-r1` foi finalmente colocada em bc41fd5 e verificada na Athena.

## diff --stat 7f1028d..bc41fd5 (intervalo correcto para r1)

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

Nota: `scripts/run_santiago_mc.py` FOI alterado entre 7f1028d e bc41fd5 (42 linhas).
A afirmação anterior ("NÃO foi alterado entre 7f1028d e d0635a3") era correcta apenas
para o intervalo mais curto 7f1028d..d0635a3; não descreve o intervalo correcto r1.

## Checklist A5 sobre bc41fd5

A checklist da PRESPEC_SANTIAGO_A5 foi re-verificada sobre scripts/run_santiago_mc.py
em bc41fd5. As alterações entre 7f1028d e bc41fd5 em run_santiago_mc.py adicionaram:
- log_startup_provenance() com --untracked-files=no e SHA-256 dos CSVs
- _stage4_run_meta.json: verificação de commit hash + SHAs na retoma
- DELTA_PP = 2.5 (margem TOST, PRESPEC §1)
- κ=∞ = 1 draw (DEV-SANT-KINF-001)
Nenhuma destas alterações modifica a lógica de Q2, Pareto, bootstrap ou macros_santiago.
A checklist A5 (sementes, células, κ, thresholds, bootstrap B=2000, Holm K4) mantém-se
válida para bc41fd5. Verificado em 2026-10-28.

## Não houve contaminação de resultados

Entre 7f1028d e bc41fd5:
- Nenhum cálculo de Q2, R, score ou fronteira para Santiago foi executado.
- O log de timing (DEV-SANT-TIMING-001) guardou apenas duração e K1; sem Q2 guardado.
- Nenhuma decisão de análise dependeu dos dados de Santiago.

## Tag correcta (r1)

A tag canónica para Stage 4 é `stage4-launch-r1` em bc41fd5.
A tag `stage4-launch` (7f1028d) e a versão intermédia em d0635a3 existem na história
git mas não devem ser usadas como referência de lançamento.

## Como verificar na Athena

```bash
git fetch --tags --force origin
git describe --exact-match --tags bc41fd5   # deve devolver stage4-launch-r1
git log --oneline 7f1028d^..bc41fd5         # deve mostrar os 3 commits acima
git diff --stat 7f1028d bc41fd5             # deve corresponder ao diff acima
```

---

## Adenda: tag stage4-launch-r2

Date: 2026-10-28 UTC (adenda criada durante revisão pré-lançamento)

A revisão pré-lançamento identificou problemas bloqueadores adicionais que requerem
um novo commit antes do lançamento. A tag `stage4-launch-r2` será criada após este
commit ser verificado na Athena.

### diff --stat bc41fd5..r2 (antecipado)

```
 .gitignore                       |  1 +   # mc_full_*.log adicionado
 corpus/DEV-SANT-A5-001.md        | +180   # reescrita completa (a-h + SENS ladder)
 corpus/DEV-SANT-TAG-001.md       | +50    # este adendo
 corpus/DEV-SANT-SPACING-001.md   | +15    # nota regra pré-fixada independente de TV_B
 corpus/DEV-SANT-ZDTI-001.md      |  +5    # datas corrigidas 2026-10-29 → 2026-10-28 UTC
 scripts/compute_stage3b.py       | +30    # repr perm, check 1e-9, boundary ±0.0001, PRESPEC §6 cite
 scripts/run_santiago_mc.py       | +10    # SHA-256 completo (64 hex) + uv.lock hash no log
```

### Razão de r2

1. Perm w_eff/w = 2.86488... impresso apenas com 4 d.p.; print com repr() + check 1e-9
   vs amplitudes.json["perm_inflation"] adicionado.
2. Boundary tests no gate negativo a ±0.005 dos limites (2.870/2.850) — substituídos
   por testes a ±0.0001 (2.8649/2.8651/2.8551/2.8549).
3. Log de lançamento (mc_full_*.log) não estava em .gitignore; adicionado.
4. SHA-256 no log do arranque reportado como [:8]; actualizado para 64 hex + uv.lock hash.
5. DEV-SANT-A5-001.md tinha erros: área tabela (ilha vs S-N), 249 candidatos (1.25km),
   critério distância ambíguo, buffer 500m não declarado, S-T ausente, SENS-A5 com ordem
   inválida (SSh sem SH), reframing "PRESPEC intent", sem hash de commit.
6. DEV-SANT-SPACING-001.md sem nota explícita de que 1.0km vem de regra geométrica
   pré-fixada, independente de TV_B.
7. DEV-SANT-ZDTI-001.md com datas 2026-10-29 nos labels de tentativa (corrigido).

### Checklist SENS-A5 sobre r2

git show stage4-launch-r2:corpus/DEV-SANT-A5-001.md | grep -c "SENS-A5"
  Deve devolver ≥ 3 (referências à SENS pre-declarada no ficheiro)
