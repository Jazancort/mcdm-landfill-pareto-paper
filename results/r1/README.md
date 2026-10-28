# results/r1/ — Recálculo confirmatório (Fase D do plano de melhoria)

Esta pasta recebe os outputs da Fase D (IMPROVEMENT_PLAN.md).

## Ficheiros esperados (após Fase D)

| Ficheiro | Produzido por | Descrição |
|----------|---------------|-----------|
| `r1_aggregate.csv` | `run_r1.py` | Q2, Q3, SE por célula × kappa × montagem |
| `r1_perdraw.parquet` | `run_r1.py` | Indicadores por draw (kappa, draw, cell, assembly, in_frontier, gap) |
| `r1_meta.json` | `run_r1.py` | git HEAD, git status, hash de pesos, Python version, host |
| `r1_decisions.json` | `analyze_r1.py` | Decisão automática por contraste (R1-1 a R1-6) |
| `r1_bootstrap.csv` | `analyze_r1.py` | IC emparelhados de cada contraste |
| `macros_r1.tex` | `generate_macros.py` | Macros geradas automaticamente dos resultados R1 |

## Regras

1. Nenhum ficheiro nesta pasta é criado manualmente.
2. O commit de `run_r1.py` precede qualquer ficheiro aqui.
3. O `r1_meta.json` tem de mostrar `git_status_clean: true`.
4. Se R1-3 falhar (diagonais < 100%), a Fase D aborta e regressa à Fase A.

## PRESPEC

Ver `corpus/PRESPEC_R1.md` (a criar na Fase C).
