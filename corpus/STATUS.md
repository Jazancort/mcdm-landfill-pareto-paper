# Estado actual — handoff para próxima sessão

**Ramo:** `writing-santiago` HEAD `fa00c1b`.

## Estado actual (HEAD fa00c1b — Ronda 1F concluída)

```
BRANCH:  writing-santiago
HEAD:    fa00c1b  (sobre 6813f89)
MAKE PAPER: exit 0 (34 páginas)
MAKE CHECK: exit 0 (0 falhas)

Ronda 1F — make check fiável (itens 1F-1 a 1F-8):

  1F-1: scripts/run_checks.py — orquestrador; corre todos os verificadores
        mesmo que um falhe; tabela (script, exit, FAILs, WARNs); sai !=0 se algum falhou.
        Makefile: alvo check chama run_checks.py.

  1F-2: check_consistency.py — sys.stdout.reconfigure(encoding="utf-8") no topo;
        resumo "ALL CHECKS PASSED" movido para DEPOIS de Anti-X_adj_vec e R9-R12.

  1F-3: check_tab_amplitude.py — "TV row not found" → FAIL (era WARN);
        regex TV_PATTERN aceita macro ($\TVvec$); mensagem final só diz "+ TV_vec"
        se TV foi verificado.

  1F-4: checks/exceptions.txt — avisos aceites:
        OVERFULL-MAKETITLE (artefacto CAS-DC) e NGRAM-BINARY-CRITERION
        (repetição intencional, a eliminar na Ronda 8).

  1F-5: verify_macros_permanent.py — Step 0: cross-check MACRO_STRINGS contra
        paper/manuscript/macros.tex (o ficheiro que entra no PDF).
        Falha com "QtwommGreedy: macro=99.9 CSV=86.0" se a cópia divergir.

  1F-6: Teste negativo B (log antigo): confirmado.
        FAIL: main.log is older than main.tex
        (log=2026-11-09 00:57:15, main.tex=2026-11-09 00:59:14)

  1F-7: Limpeza:
        C:\build não existe.
        git worktree list: só repositório principal + stage1_worktree.
        .git/worktrees/: só stage1_worktree (neg_test_worktree, wt-neg, wt-neg2 removidos).
        stage1_worktree: em uso (HEAD 94b5baf, detached), NÃO apagar.

  1F-8: make paper EXIT=0 (34 páginas); make check EXIT=0 (0 falhas).

TESTE NEGATIVO A2 (Ronda 1F):
  Worktree wt-neg2 criado em HEAD fa00c1b.
  make paper correu no worktree (log fresco).
  QtwommGreedy 86.0→99.9 em paper/manuscript/macros.tex do worktree
    (o ficheiro que build_paper.py copia para build/paper/ e compila).
  make paper correu novamente (log actualizado).
  pdftotext confirmou: PDF contém "99.9%" em múltiplos sítios.
  make check → EXIT=2 (≠0).
  FAILs detectados pela razão certa:
    check_consistency: A9b — macros/macros.tex e paper/manuscript/macros.tex divergem
      (QtwommGreedy: 99.9 vs 86.0 — diff explícito)
    verify_macros_permanent: [FAIL] QtwommGreedy: macro=99.9 CSV=86.0  ← razão certa
    verify_macros_santiago: idem (--santiago também apanha)
  Tabela run_checks.py:
    check_consistency       Exit=1  FAILs=1  WARNs=5  <-- FAILED
    verify_macros_permanent Exit=1  FAILs=1  WARNs=0  <-- FAILED
    verify_macros_santiago  Exit=1  FAILs=1  WARNs=0  <-- FAILED
  Worktree removido: rmdir /s /q + git worktree prune.

TESTE NEGATIVO B (Ronda 1F):
  touch main.tex (copy /b) sem recompilar.
  make check → EXIT=2.
  FAIL: main.log is older than main.tex
        (log=2026-11-09 00:57:15, main.tex=2026-11-09 00:59:14)

NOTA R4 (selados):
  git diff stage4-results-sealed -- results/santiago/mc_*_raw.csv
    → NÃO vazio (mc_ST_raw.csv e mc_SN_raw.csv foram adicionados DEPOIS do tag).
    Esta é uma condição pré-existente, não introduzida pela Ronda 1F.
    A ser resolvida numa ronda futura (Ronda 4 ou Fase D).
  git diff stage4-e1fix2-sealed -- results/santiago/mc_*_e1_fix2.csv → vazio.
  git diff prespec-santiago-f0-amend-final -- corpus/PRESPEC_SANTIAGO*.md
    → NÃO vazio (PRESPEC_SANTIAGO.md foi removido do branch; pré-existente).
```

## Próximo passo

```
SESSÃO SEGUINTE:
  Ronda 2a — Estrutura (substituições de texto + fonte única de macros).
  Itens: 2a-1 (substituições main.tex) e 2a-2 (fonte única macros/).
  Antes de começar: git status --porcelain (deve estar limpo).
```

## Plano de trabalho

```
Ver corpus/WORK_PLAN.md para o plano completo (Rondas 1F-12 + Scorecard).
```

