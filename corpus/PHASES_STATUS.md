# Estado das fases: plano de melhoria
Referência: `corpus/IMPROVEMENT_PLAN.md` (o plano não se duplica aqui)  
Última actualização: 2026-10-01 23:16 | por: sessão 2026-10-01

## Legenda
**Estado:** `TODO` | `DOING` | `DONE` | `BLOCKED` (motivo na coluna Notas) | `SKIP` (justificar)  
Uma tarefa só passa a `DONE` quando o critério de aceitação foi verificado e a coluna Commit
aponta para o commit da **implementação** (não para o commit que actualiza este ficheiro).

## Próxima tarefa
Aguardar resultado numérico de M1 (Athena, tmux gap_m1 → results/math/math_m1_gap.log).
Depois: completar M1 → M2 → M3 → M4 em paralelo com B3 (convencção postos/perm).

---

## Fase Math: revisões matemáticas preliminares (antes de qualquer alteração de código)

> Objectivo: corrigir definições e provas para que o pipeline possa ser reproduzível
> sem reproduzir afirmações falsas.

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| M1 | Verificar gap: a definição actual (mínimo das melhorias em F1, F2, F3) satisfaz gap=0 sse dominado? Testar por script se existe portfólio com gap=0 e Q2=1 | — | Script com exemplo afirmativo ou prova negativa; reformular a definição se necessário; registar em Notas se Q3=0⟺Q2=1 se mantém | DOING | a3556f1 | **Análise algébrica concluída: FALSO.** gap usa dominação estrita (min dos 3 termos>0); Pareto usa dominação fraca (pelo menos 1 estrito, restantes ≥). Contra-exemplo: t' melhora F1 e F3, empata F2 → min=0 → gap=0, mas t' domina t. Q3=0 iff Q2=1 não se sustenta. Script math_m1_gap.py (a3556f1) a contar contra-exemplos nos dados reais (Athena, tmux gap_m1). Resultado numérico pendente. |
| M2 | Verificar a identidade PROMETHEE: (a) convenção posto maior=melhor no código; (b) dividir por N+1 não destrói equivalência de rankings — corrigir a frase que atribui a divergência a essa divisão; (c) a comparação "diferença à precisão de máquina" inclui a constante afim? | — | Script numérico com o sinal e a constante correctos; linha e ficheiro citados | TODO | | Depende de B3 para a convenção de postos |
| M3 | Restringir a "proposição do expoente" a SAW; reformular TOPSIS e PROMETHEE como propriedades distintas com alcance explícito (w_j²A_j² ≠ pesos efectivos do índice de proximidade TOPSIS; α=0 ≠ w_j^0) | M2 | Texto da proposição alterado; commit no main.tex | TODO | | |
| M4 | Substituir "quota da variação total do score" por "peso ponderado pela amplitude" em todas as ocorrências | — | grep sem ocorrências da frase antiga; check passa | TODO | | |

---

## Fase B: proveniência (só leitura — independente de A)

> Objectivo: saber exactamente que números estão contaminados antes de recalcular.
> **B1 não depende de A1**: a proveniência documenta o estado actual do código, antes de o alterar.

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| B1 | `docs/provenance.csv` (número → macro/tabela → script → função score → função objs → aspect score → aspect obj → ref score → ref obj → contaminado?). Começar por tab:canonical e tab:fourthcell | — | Nenhuma linha "desconhecido" nestas duas tabelas | TODO | | |
| B2 | Completar cobertura: "6 de 7 em A'", reprodução {184,430,460}, \FAsize, \FAinter, tab:amprefset, \MechOne\*, \MismatchRatio\*, fig:pareto, fig:map | B1 | Nenhuma linha "desconhecido" em todo o ficheiro | TODO | | |
| B3 | Convenção da ordenação por postos (PROMETHEE) e orientação de *perm* no código: localizar a linha, registar o sentido | — | Linha e ficheiro citados na nota; bloqueia M2, F4, F5 até estar DONE | DONE | a3556f1 | **Verificado 2026-10-01.** `amplitude_regression.py` L47: `rank(method='average')` sobre `X_adj` (benefit-aligned). **Convenção: rank 1 = melhor sítio** (X_adj mínimo = pior raw invertido = melhor para score). Fórmula φ=(n+1)/(n-1)−(2/(n-1))Σw_j r_j é decrescente em r_j: maximizar φ = minimizar r_j = preferir rank 1 = melhor sítio. **Consistente.** perm: 350 zeros → X_adj_perm=1.0 → rank máximo 214.5; amplitude=0.547. Texto do manuscrito correcto para perm. D7 (citação de eq:Arank_binary para perm) não se verifica no texto — eq:Arank_binary cita apenas aspect. |
| B4 | Codificação de aspect usada no estudo-fonte (AzancortNeto2026): verificar se o artigo usa binário ou contínuo | — | Fonte citada (script ou artigo; página ou linha) | TODO | | |
| B5 | Nota-resumo de 1 página: o que está contaminado e decisão pela árvore (espaço A) | B1–B4 | Commit da nota em docs/ | TODO | | |

---

## Fase A: infra-estrutura (eliminar a classe de bug)

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| A1 | Criar `scripts/encoding.py` com `encode_criteria(df, ref_df)`; migrar `compute_objs_f64`, `build_score_473`, `_build_decision_matrix` e os construtores do E1 e do E4 | — | `grep -n aspect scripts/*.py` só encontra ocorrências em encoding.py e nas asserções | TODO | | |
| A2 | Asserções em todos os construtores: aspect ∈ {0,1}; coluna aspect igual entre score e objectivos; monotonia score↔objectivo em todas as colunas | A1 | Asserções presentes; corrida de fumo passa | TODO | | |
| A3 | `tests/test_encoding.py`: o teste falha no commit `efdc9d8` (demonstrar via worktree ou fixture que congela a função antiga) e passa no HEAD | A1, A2 | Output das duas corridas registado no Commit | TODO | | A falha legada não pode ser assumida — usar `git worktree add` ou uma fixture que importa a função antiga directamente |
| A4 | Gravar resultados por draw `results/<exp>_perdraw.parquet` (kappa, draw, cell, assembly, in_frontier, gap) | A1 | Corrida de fumo com 50 draws produz o ficheiro | TODO | | |
| A5 | Gravar `results/<exp>_meta.json` (HEAD, git status, hash dos pesos, versões, host); abortar se o git status não estiver vazio | — | Corrida com alterações não commitadas aborta com mensagem clara | TODO | | |
| A6 | Reconciliar o ramo da Athena com o main; deixar de usar SCP | — | `git rev-parse HEAD` igual nos dois lados antes de qualquer corrida | TODO | | |

---

## Fase C: pré-registo do recálculo

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| C1 | `corpus/PRESPEC_R1.md` com R1-1 a R1-6, regras de decisão, κ, draws, hash de pesos, bootstrap, semente. Declarar que draws não examinados ficam reservados para confirmação mais forte (eventual Fase I) | B5 | Commit com data anterior a qualquer output da Fase D (verificar contra o meta.json) | TODO | | |

---

## Fase D: recálculo confirmatório

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| D1 | `run_r1.py` (tab:fourthcell com codificação única e, se B5 o pedir, tab:canonical) | C1, A1–A6 | Ficheiros por draw e meta.json gerados a partir de commit limpo (git_status_clean: true) | TODO | | |
| D2 | `analyze_r1.py`: Q2, Q3, SE, IC emparelhado, decisões automáticas → `results/r1/r1_decisions.json` | D1 | R1-3 (diagonais = 100% sob óptimo) passa; se falhar → BLOCKED e regressar a A | TODO | | |
| D3 | `generate_macros.py`: regenerar macros a partir dos resultados | D2 | Nenhum número escrito à mão; macros novas em commit | TODO | | |
| D4 | Regenerar fig:pareto e fig:map, se R1-4 se aplicar | D2 | Figuras em commit com o script que as gerou | TODO | | |

---

## Fase E: diagnósticos exploratórios (máximo 4)

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| E1 | Greedy ≈ 97,8% com r_j: W_g^eff, proporção greedy=óptimo, percentis em F1–F3 | D2 | Script, output e 1 frase marcada como exploratória | TODO | | |
| E2 | TV_B e TV_W calculados para os padrões r_j e 1/r_j (não são simétricos — já verificado: 0,0815 vs 0,0852) | A1 | Valores em macro; diferença registada | TODO | | TV_W(r_j)=0.0815, TV_W(1/r_j)=0.0852 já calculados |
| E3 | Spearman(azimute normalizado, indicador); proporção de sítios com score alto e indicador=0 | A1 | Valores em macro; 1 frase "consistent with" | TODO | | |
| E4 | (Opcional) amplificação W×B: variar W_G1 com o padrão interno fixo | D2 | Só se houver tempo; caso contrário SKIP para future work | TODO | | |
| E5 | Completar DEV-E4-007: v1–v5 corridas com resultados vistos; outputs em `results/e4/`; P_E4_3 "falhado como especificado, pouco informativo"; P_E4_5 exploratório | — | Commit no PRESPEC_E4 | TODO | | Parcialmente feito em b0e5c66; verificar completude |

---

## Fase F: correcções independentes

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| F1 | Agregação por estrato com IC emparelhado; contraste sem a célula fixa; resumo e highlight: "no consistent effect: sign depends on cell; pooled +0.6 pp" | A4 | `aggregation_strata.py` e macros novas; frase e highlight reformulados | TODO | | |
| F2 | Circularidade do min–max: §5 e Limitações | — | Parágrafos inseridos; check passa | TODO | | |
| F3 | Q3 na tab:factorial e na tab:e1 | A4 | Macros geradas pelo script | TODO | | |
| F4 | Sinal da identidade PROMETHEE (eq. e frase de verificação) | B3, M2 | Verificação numérica com o sinal e a constante correctos | TODO | | B3 DONE. Aguarda M2. |
| F5 | Intervalo de *perm* em postos segundo a orientação real; deixar de citar eq:Arank_binary para *perm* | B3 | Valores impressos pelo script; sem referência a eq:Arank_binary | TODO | | B3 DONE. D7 não se verifica: eq:Arank_binary já não é citada para perm. F5 pode ser SKIP após verificação em M2. |
| F6 | Resumo ≤ 250 palavras | G2a | `texcount` ≤ 250 | TODO | | |
| F7 | Cabeçalho do .tex, contagens de resultados, restos de texto antigo | — | check passa | TODO | | |

---

## Fase G: reescrita do manuscrito (um commit por linha)

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| G1 | Aplicar a árvore de decisão a `r1_decisions.json`; registar o ramo escolhido na coluna Notas | D2, B5 | Ramo registado aqui | TODO | | |
| G2a | Resumo | G1, F1 | Sem "80 pp" de mismatch; agregação correcta; ≤ 250 palavras (F6) | TODO | | |
| G2b | Highlights | G1, F1 | Highlight 5 retirado ou substituído | TODO | | |
| G2c | Introdução (third finding, contribuição i) | G1 | — | TODO | | |
| G2d | §3: parágrafo "Mixed senses" (uma só codificação) | A1 | — | TODO | | |
| G2e | §5: conjunto de referência como factor secundário; acrescentar circularidade (F2) | G1, F2 | — | TODO | | |
| G2f | §6: F4, F5; manter eq:refsetA e tab:amprefset | F4, F5 | — | TODO | | |
| G2g | sec:refset reescrita; tab:fourthcell com valores novos da Fase D | G1, D3 | Sem "Mechanism 2"; sem factor 16; sem "unexplained" | TODO | | |
| G2h | Remark "non-monotone recoding" (R-asp, post hoc deliberado, 24%) | D2, E3 | Historial do bug apenas no Suplementar | TODO | | |
| G2i | sec:interaction: factor 1,56× como macro | E2 | — | TODO | | |
| G2j | §8.1: um mecanismo, duas origens; sem factor 16; sem "unexplained" | G1 | — | TODO | | |
| G2k | §8.5 Prática: rec. 1 reescrita; nova recomendação "uma função de codificação"; E1 se houver resultado | G1, E1 | — | TODO | | |
| G2l | Limitações: circularidade, instância única, carácter exploratório do E4 | F2 | — | TODO | | |
| G2m | Conclusão alinhada com o resumo | G2a | — | TODO | | |
| G2n | Suplementar: PRESPEC_E4 (DEV 001–007), PRESPEC_R1, historial v1–v6, tabela de proveniência | E5, C1, B2 | — | TODO | | |
| G3 | Regras novas no check: macros proibidas, frases proibidas, números "pp" fora de macro, test_encoding no make check, macros usadas↔definidas | G2a–G2n | `make check` exit 0; ≥ 55 asserções | TODO | | |

---

## Fase H: revisão interna

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| H1 | Leitura a frio 24 h depois da reescrita; lista de afirmações sem evidência | G3 | Lista vazia ou cada item tem resposta documentada | TODO | | |
| H2 | Três objecções de revisor (circularidade, instância única, agregação) com resposta no texto | G3 | Secção e linha de cada resposta | TODO | | |
| H3 | Matriz afirmação → evidência para o resumo e os highlights | G3 | Ficheiro em commit | TODO | | |
| H4 | provenance.csv final igual ao estado do PDF | G3 | diff vazio | TODO | | |

---

## Fase I: generalização

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| I0 | Inspeccionar `results/corpus/corpus_amplitudes.csv` e `corpus_mc_results.csv`: o que contêm e se servem para I1 | — | Nota em Notas | TODO | | Pode correr em paralelo com G |
| I1 | Corpus de matrizes publicadas: distribuição de (TV, TV_B, TV_W, m_eff), com PRESPEC_I1 | I0, A1 | Secção nova no artigo | TODO | | |
| I2 | Instâncias sintéticas calibradas, com PRESPEC_I2 | A1 | Idem | TODO | | |
| I3 | Segunda instância real, com PRESPEC_I3 | H4 | Idem | TODO | | |

---

## Registo de decisões

| Data | Decisão | Base (ficheiro/commit) |
|------|---------|----------------------|
| 2026-10-01 | Codificação contínua de aspect em build_score_473 é inconsistente com avaliador binário. R-V*=100%, R-asp=24% confirmam. | corpus/PRESPEC_E4.md DEV-E4-007, commit b0e5c66 |
| 2026-10-01 | B1 declarado independente de A1: proveniência documenta o código actual antes de o alterar | corpus/PHASES_STATUS.md |
| 2026-10-01 | Fase Math adicionada antes de A: M1 (gap), M2 (PROMETHEE), M3 (proposição expoente), M4 (nomenclatura) | corpus/PHASES_STATUS.md |
| 2026-10-01 | B3 verificado: rank 1 = melhor sítio; φ=(n+1)/(n-1)−(2/(n-1))Σ decrescente em r_j; texto do manuscrito correcto para perm (0.547); D7 não se verifica (eq:Arank_binary não é citada para perm). | amplitude_regression.py L47, Athena verificação directa |

## Bloqueios abertos

| ID tarefa | Motivo | Desde |
|-----------|--------|-------|
| F4 | Aguarda M2 (B3 já DONE) | 2026-10-01 |
| M1 | Aguarda resultado numérico (Athena, tmux gap_m1) | 2026-10-01 |
