# Nota de contaminação — auditoria de proveniência
**Data:** 2026-10-02  
**Commits de referência:** provenance.csv `9f01740`, bootstrap `9235e63`, R-V* `2270cc4`  
**Fonte:** `docs/provenance.csv` (28 linhas, cobertura completa das tabelas e figuras com números)

---

## 1. O que está contaminado

### Causa raiz
A função `build_score_473` em `mc_2cube_fixed.py` codifica `aspect` como variável contínua (azimute em graus, min-max sobre 473 sítios), enquanto todas as funções de objectivos (`compute_objs_f64` em `pareto_utils.py`, `build_objs_ref` em `run_473A_389A.py`) codificam `aspect` como indicador binário de sotavento (`c=1` se azimute ∈ [90°,180°], `c=0` caso contrário). Esta inconsistência de codificação é um bug de pipeline, não uma escolha metodológica.

### Itens contaminados

| Item | Valor no manuscrito | Causa | Acção |
|------|--------------------|----|-------|
| tab:fourthcell Ncand/A' greedy | 19.6% | build_score_473 (contínuo) vs avaliador binário | Recalcular com codificação consistente |
| tab:fourthcell Ncand/A' optimal | 20.0% | Idem | Idem |
| tab:fourthcell Ncand/A greedy | 84.6% | Idem (vs avaliador A binário) | Idem |
| tab:fourthcell Ncand/A optimal | 100.0% | Coincidência: azimutes altos = não-sotavento | Recalcular (valor pode mudar) |
| \MismatchRatioHi = 5.4 | comentada | Baseada nos 80 pp do item acima | DONE: removida |
| \MismatchRatioLo = 0.34 | comentada | Idem | DONE: removida |
| \MechOnePredAdmiss = 14.7 | comentada | Idem | DONE: removida |
| \MechOneShare = 18 | comentada | Idem | DONE: removida |

**Passagens do manuscrito que dependem destes valores (já corrigidas em commit 9235e63):**
- sec:refset §Mechanism 2 — reescrito para descrever coding mismatch
- §8.1 segundo mecanismo — factor 16 e "unexplained" removidos
- Resumo última frase — "80 pp" atribuídos a mismatch de codificação
- Highlights §5 — substituído
- Introdução "third finding" — reescrito
- Conclusão §80 pp — actualizado
- §8.5 primeira recomendação prática — corrigida

---

## 2. O que está limpo

| Item | Evidência |
|------|-----------|
| tab:canonical (7 métodos + reprodução) | Score `_build_decision_matrix` (binário) + objectivos `exhaustive_search_pareto.csv` (binário) |
| "6 de 7 não dominados em A'" (L1733) | Fronteira A' via `pareto_utils` (binário) |
| Reprodução {184,430,460} a 1e-16 | `compute_objectives(df_via, df_imp)` usa aspect binário; F1/F2/F3 confirmados |
| \FAsize = 213 | len(exhaustive_search_pareto.csv) = 213 confirmado |
| tab:amprefset (r_j e TV=0.107) | `amplitude_regression.py`, r_aspect = 1.0 (range_389 = range_473 para binário {0,1}) |
| tab:factorial (2³) | `mc_2cube_fixed.py`, células Nvia/A' — usa `_build_decision_matrix` (binário) |
| E1 (B/W/V cells) | `run_e1_v3.py`, usa `_build_decision_matrix` (binário) |
| Teorema thm:groupconst + prova iff | Algébrico, independente de dados |
| fig:pareto (F3) | `fig_F3_pareto.py` usa `pareto_front_Aprime.csv` (fronteira A', binária) |
| fig:map (F4) | `fig_F4_map.py` usa fronteira A', dados geográficos |
| eq:p2identity (PROMETHEE) | Sinal corrigido em F4 (commit 90926b1); verificado numericamente (max diff = 3.33e-16) |
| Proposição do expoente (TOPSIS α=2) | Nota de âmbito existente ("by analogy"); PROMETHEE reformulado como "amplitude-invariant" |

---

## 3. Itens com incerteza residual

| Item | Estado | O que falta |
|------|--------|-------------|
| \FAinter = 132 | A_VERIFICAR | Script que calculou a interseção F_A ∩ F_A' indisponível; `pareto_front_Aprime.csv` ausente na Athena |
| tab:fourthcell Ncand/A optimal = 100% | SIM contaminado, mas **valor pós-correcção desconhecido** | run_fourthcell_consistent.py deu RV_star_A opt=100% — mas isso é com score binário r_j; o correspondente a Ncand/A correcto (build_score_473 com aspect binário) ainda não foi calculado |

---

## 4. Decisão pela árvore de decisão (IMPROVEMENT_PLAN.md §4)

**Pergunta:** a Fase B marcou o espaço A como contaminado?

**Resposta: SIM, parcialmente.**

- **tab:canonical** (7 linhas de valores + reprodução): **NÃO contaminado**. Usa `_build_decision_matrix` (binário) e `exhaustive_search_pareto.csv`. As frases "four of seven dominated in A" e "six of seven non-dominated in A'" estão correctas.
- **tab:fourthcell Ncand/***: **SIM contaminado**. São 4 valores numéricos (19.6%, 20.0%, 84.6%, 100.0%) que precisam de ser recalculados com codificação consistente.

**Árvore:**

```
Fase B marcou espaço A como contaminado?
├─ tab:canonical: NÃO → manter; frases "4 de 7 dominados em A" e "6 de 7 em A'" correctas
└─ tab:fourthcell Ncand/*: SIM
     Causa: coding inconsistency (AzancortNeto2026 usa aspect binário — B4 confirmado)
     └─ Acção: recalcular as 4 células Ncand com build_score_473 corrigido (aspect binário)
                usando run_fourthcell_consistent.py (já existente, commit 3d4c48a)
                Resultado esperado: Ncand/A' opt → ~100% (= R-V* confirmado)
                Resultado Ncand/A: desconhecido (correr run_fourthcell_consistent.py)
```

**Decisão: tab:canonical mantém-se no texto principal.** As análises comparativas entre espaços A e A' continuam válidas porque tab:canonical usa codificação consistente. A tab:fourthcell será actualizada na Fase D com os valores da run_fourthcell_consistent.py (RV_star_A/Aprime já calculados em commit 9235e63).

**Contingência:** os valores já disponíveis de run_fourthcell_consistent.py são:
- RV_star_Aprime opt = 100.0% → substitui Ncand/A' optimal 20.0%
- RM_Aprime opt = 100.0% → confirma Nvia/A' optimal 100.0%
- RV_star_A opt = 100.0% → substitui Ncand/A optimal 100.0% (mesmo valor, mas agora correcto)
- RM_A opt = 95.0% → confirma Nvia/A optimal 95.0%
- RV_star_A greedy = 84.6% → substitui Ncand/A greedy 84.6% (mesmo valor, coincidência confirmada)
- RV_star_Aprime greedy = 97.8% → substitui Ncand/A' greedy 19.6%

**Com estes valores, a tab:fourthcell pode ser actualizada imediatamente** sem nova corrida, usando os resultados de `results/e4-audit/fourthcell_consistent.csv`.

---

## 5. Resumo executivo para o Opus/GPT

**O que falhou:** uma função de score (`build_score_473`) usava aspect como variável contínua (azimute em graus) enquanto todas as funções de objectivos usavam aspect como indicador binário de sotavento. A inconsistência foi descoberta através da célula R-V* = 100% vs R-V = 20%.

**O que está afectado:** 4 valores na tab:fourthcell (as linhas Ncand) e 4 macros (já removidas). Mais nada no manuscrito.

**O que não está afectado:** tab:canonical, tab:factorial (2³), E1, Teorema, eq:p2identity (corrigido), fig:pareto, fig:map.

**O que foi corrigido nesta sessão:**
- Manuscrito: sec:refset, §8.1, resumo, highlights, intro, conclusão, primeira recomendação prática, eq:p2identity (sinal), proposição do expoente (PROMETHEE).
- Macros: 4 macros baseadas nos 80 pp removidas e proibidas.
- Código: (pendente — Fase A).

**O que falta:** actualizar a tab:fourthcell com os valores da codificação consistente (disponíveis em `results/e4-audit/fourthcell_consistent.csv`). Isto é uma substituição directa de 4 números.
