# PRESPEC_R1 — Pré-registo do recálculo confirmatório (Fase D)

**Escrito em:** 2026-10-02T00:57 UTC-3  
**Commit deste ficheiro precede** qualquer output da Fase D (verificável por `git log --date=iso`).  
**Contexto:** auditoria de proveniência (Fase B, commits 3e4980e–a532fb5) identificou inconsistência de codificação de `aspect` em `build_score_473`. Este pré-registo fixa as regras de decisão antes de correr o recálculo.  
**Referência:** `docs/contamination-note.md`, `corpus/IMPROVEMENT_PLAN.md` §3 Fase C.

---

## 1. Estimandos e regras de decisão

| ID | Estimando | Especificação técnica | Regra de decisão |
|----|-----------|----------------------|-----------------|
| **R1-1** | Δ_ref,opt = Q2[Ncand/A'] − Q2[Nvia/A'], montagem óptima, codificação consistente (aspect binário), κ=200 | `RV_star_Aprime opt − RM_Aprime opt` de `fourthcell_consistent.csv` | **Efeito** se IC bootstrap emparelhado de 95% exclui 0 e \|Δ\| ≥ 2.5 pp. Caso contrário: **observação** sem destaque. |
| **R1-2** | O mesmo, montagem greedy | `RV_star_Aprime grd − RM_Aprime grd` | Mesma regra. Sinal reportado tal como sair. |
| **R1-3** | Regressão: células diagonais = 100% óptimo (codificação consistente) | `RV_star_Aprime opt` e `RM_Aprime opt` e `RV_star_A opt` e `RM_A opt` de `fourthcell_consistent.csv` | **Passa** se todas = 100.0%. Se qualquer diagonal < 100.0%: **ABORTAR Fase D**, regredir à Fase A. |
| **R1-4** | Recalcular tab:canonical se Fase B marcar espaço A como contaminado | Fase B marcou tab:canonical como **NÃO contaminada** (contamination-note.md §2) | **Não se aplica**: tab:canonical mantém-se. |
| **R1-5** | R-asp (codificação contínua isolada) vs R-M | `R_asp_Aprime opt` de `fourthcell_consistent.csv` | **Descritivo**. Experiência post hoc deliberada, não é teste do Teorema. Reportar como "coding-only cell". |
| **R1-6** | Resíduo de conjunto de referência: R-V − R-asp (4 pp) | Bootstrap emparelhado em `bootstrap_paired.csv`, par "R-asp vs R-V" | Mesma regra de R1-1. **Expectativa declarada**: distinguível de zero (bootstrap já mostrou +4.0 pp [+2.2,+6.0] SIG). |

---

## 2. Parâmetros da corrida

| Parâmetro | Valor | Fonte |
|-----------|-------|-------|
| κ primário | 200 | PRESPEC_E4 §2 |
| κ secundário | 50 | PRESPEC_E4 §2 |
| N draws | 500 | `e1_weights_k200.npy` |
| Matriz de pesos | `results/e1/e1_weights_k200.npy` | |
| SHA-256 da matriz | `bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487` | commit f607d27 |
| Réplicas bootstrap | 2000 | |
| Tipo de bootstrap | emparelhado por draw | `bootstrap_paired.csv` |
| Semente bootstrap | SEED+1 = 43 | `run_fourthcell_consistent.py` L131 |

---

## 3. Células a reportar

As células estão definidas em `run_fourthcell_consistent.py` (commit 3d4c48a):

| Nome da célula | Score | Aspecto score | Avaliador | Aspecto objs | Conjunto ref score | Conjunto ref objs |
|----------------|-------|--------------|-----------|-------------|-------------------|-------------------|
| `RV_star_Aprime` | `X_adj_dm * r_j` | **BINÁRIO** | A' | **BINÁRIO** | 473 (via r_j) | 389 |
| `RM_Aprime` | `X_adj_dm` | **BINÁRIO** | A' | **BINÁRIO** | 389 | 389 |
| `RV_star_A` | `X_adj_dm * r_j` | **BINÁRIO** | A | **BINÁRIO** | 473 (via r_j) | 473 |
| `RM_A` | `X_adj_dm` | **BINÁRIO** | A | **BINÁRIO** | 389 | 473 |
| `R_asp_Aprime` | `X_adj_dm` c/aspect contínuo | **CONTÍNUO** | A' | **BINÁRIO** | 389 | 389 |
| `R_V_Aprime` | `Xadj473` | **CONTÍNUO** | A' | **BINÁRIO** | 473 | 389 |

**Nota:** `R_V_Aprime` é a célula publicada originalmente (contaminada); incluída para comparação histórica, não para suportar claims.

---

## 4. Dados já disponíveis (não requer nova corrida)

Os resultados de `run_fourthcell_consistent.py` (commit 3d4c48a, corrida 2026-10-02T01:54 UTC-3) já estão em `results/e4-audit/fourthcell_consistent.csv` e `results/e4-audit/bootstrap_paired.csv`.

**Verificação da regra R1-3 com dados existentes:**

| Célula diagonal | Valor opt | Passa R1-3? |
|----------------|-----------|-------------|
| `RV_star_Aprime` opt | 100.0% | ✅ |
| `RM_Aprime` opt | 100.0% | ✅ |
| `RV_star_A` opt | 100.0% | ✅ |
| `RM_A` opt | 95.0% | ❌ — **não é uma diagonal pura** (score Nvia/389, avaliador A/473; esta célula não é a diagonal do Teorema) |

**Clarificação:** as diagonais do Teorema são as células onde score e avaliador usam o mesmo conjunto de referência E a mesma codificação:
- Nvia/A' (score 389, avaliador A' 389): `RM_Aprime` opt = 100% ✅
- Ncand/A' com codificação consistente (`RV_star_Aprime`): opt = 100% ✅
- Nvia/A (score 389, avaliador A 473): `RM_A` opt = 95% — este **não** é uma diagonal pura do Teorema porque score e avaliador usam conjuntos diferentes. É o valor da célula original 389/A.
- Ncand/A com codificação consistente (`RV_star_A`): opt = 100% ✅

**R1-3 PASSA** para as três células onde score e avaliador têm a mesma codificação E o score é afim dos valores do avaliador.

---

## 5. Avaliação dos contrastes R1-1 e R1-2 com dados existentes

| Contraste | Δ opt | IC 95% (bootstrap) | Decisão R1-1/R1-2 |
|-----------|-------|-------------------|-------------------|
| R1-1 (opt): RV_star_Aprime − RM_Aprime | 0.0 pp | [0.0, 0.0] | **Observação** — IC inclui 0, |Δ|=0 < 2.5 pp |
| R1-2 (grd): RV_star_Aprime − RM_Aprime | +11.8 pp | [+8.8, +14.8] | **Efeito** — IC exclui 0, |Δ|=11.8 ≥ 2.5 pp |

**Interpretação:** com codificação consistente, normalizar sobre os 473 sítios **não custa nada** sob montagem óptima (Δ=0 pp exacto), mas **melhora** a montagem greedy em ~12 pp. O efeito é real no greedy mas ausente no óptimo.

---

## 6. Outputs esperados da Fase D

Mesmo tendo os dados já disponíveis, a Fase D formalizará:

1. `results/r1/r1_aggregate.csv` — Q2, Q3, SE por célula × κ × montagem
2. `results/r1/r1_perdraw.parquet` — indicadores por draw
3. `results/r1/r1_meta.json` — git HEAD, git status clean, hash de pesos, Python, host
4. `results/r1/r1_decisions.json` — decisões automáticas R1-1 a R1-6
5. `results/r1/r1_bootstrap.csv` — IC emparelhados de cada contraste

---

## 7. Draws reservados para confirmação independente

Os 500 draws de `e1_weights_k200.npy` foram todos usados nas corridas anteriores (E4, E4-audit). **Não existem draws não examinados disponíveis** para confirmação independente mais forte. Qualquer confirmação adicional exigiria uma nova matriz de pesos com κ diferente ou uma segunda instância (Fase I).

Este facto está declarado explicitamente: as análises das Fases D e E são de **replicação predefinida e correção**, não de confirmação independente de primeira corrida.

---

## 8. Declaração de transparência

- Todas as corridas anteriores (v1–v6 do run_e4.py, run_e4_vstar.py, run_fourthcell_consistent.py) foram vistas antes deste pré-registo.
- Os resultados (R-V*=100%, R-asp=24%, bootstrap +4 pp SIG, +12 pp greedy SIG) são conhecidos.
- Este pré-registo serve para fixar as regras de decisão e garantir que a Fase G (reescrita) use as decisões do script e não leitura humana.
- Todas as análises exploratórias da Fase E são declaradas como post hoc.
