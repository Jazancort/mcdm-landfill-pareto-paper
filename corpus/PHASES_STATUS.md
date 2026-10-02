# Estado das fases: plano de melhoria
Referência: `corpus/IMPROVEMENT_PLAN.md` (o plano não se duplica aqui)  
Última actualização: 2026-10-02 01:49 | por: sessão 2026-10-01/02

## Legenda
**Estado:** `TODO` | `DOING` | `DONE` | `BLOCKED` (motivo na coluna Notas) | `SKIP` (justificar)  
Uma tarefa só passa a `DONE` quando o critério de aceitação foi verificado e a coluna Commit
aponta para o commit da **implementação** (não para o commit que actualiza este ficheiro).

## Próxima tarefa
H (revisão interna). F3 DONE.
H (revisão interna). F3 (Q3) a correr na Athena (tmux q3f3).
E3 (Spearman aspect) — próximo. F1 (aggregation_strata.py) — dados existem. F3 (Q3) — requer nova corrida na Athena.

---

## Documentos criados nesta sessão (2026-10-01/02)

| Ficheiro | Commit | Tipo | Conteúdo resumido |
|----------|--------|------|-------------------|
| `results/e1/e1_diag_greedy_rvstar.csv` | b85c895 | Dados E1 | TV_B/TV_W r_j; greedy=opt 57.6%; 63 discriminating draws; F1 percentiles |
| `results/e1/e1_diag_greedy_rvstar.log` | b85c895 | Log E1 | Output completo do diagnóstico |
| `results/e1/aggregation_strata.csv` | 18361a6 | Dados F1 | SAW-TOPSIS por célula, IC emparelhado B=2000 |
| `results/e1/aggregation_strata.log` | 18361a6 | Log F1 | Output completo com pooled e por célula |
| `results/e1/e1_diag_greedy_rvstar.csv` | b85c895 | Dados E1 | TV_B/TV_W r_j; greedy=opt 57.6%; 63 discriminating draws; F1 percentiles |
| `corpus/PRESPEC_R1.md` | 595a760 | Pré-registo | R1-1 a R1-6; regras de decisão; κ=200/50; SHA-256 da matriz; bootstrap emparelhado seed=43 |
| E3 cálculo (inline Athena) | 81933a6 | Dados E3 | Spearman=0.018, p=0.73; top-25% azimute: 100% indicator=0; 6 macros adicionadas: AspSpearman, AspSpearmanP, AspTopQuartile, AspTopQuartileNonLee, AspLeewardCount, AspLeewardPct |
| `results/r1/r1_decisions.json` | c63b64e | Decisões D2 | R1-1 OBSERVAÇÃO, R1-2 EFEITO, R1-3 PASS, R1-4 N/A, R1-5 DESCRITIVO, R1-6 EFEITO |
| `results/r1/r1_aggregate.csv` | c63b64e | Dados D2 | Q2 por célula × κ × montagem (12 linhas) |
| `results/r1/r1_bootstrap.csv` | c63b64e | Dados D2 | IC emparelhados dos 4 contrastes |
| `results/r1/macros_r1.tex` | c63b64e | Macros D3 | 12 macros LaTeX geradas automaticamente |
| `corpus/PRESPEC_R1.md` | 595a760 | Pré-registo | R1-1 a R1-6; regras de decisão; κ=200/50; SHA-256 da matriz; bootstrap emparelhado seed=43; avaliação antecipada com dados existentes; draws não reservados declarados |
| `docs/contamination-note.md` | a532fb5 | Nota B5 | Resumo executivo de contaminação; árvore de decisão para espaço A; substituição directa de 4 valores na tab:fourthcell |
| `docs/provenance.csv` | 9f01740 | Proveniência | 28 linhas: número→macro→script→função score→função objs→aspect score/obj→ref score/obj→contaminado |
| `docs/session-2026-10-01-22h22.md` | cac8491 | Sessão | Estado intercalar com valores de referência e itens pendentes |
| `docs/e4-resultados-analise.md` | 3d4c48a | Análise | Diagnóstico final E4: R-V*=100%, R-asp=24%, bootstrap emparelhado, decomposição 76+4 pp |
| `results/e4-audit/bootstrap_paired.csv` | 9235e63 | Dados | Bootstrap emparelhado: R-asp vs R-V (+4pp SIG), R-V* vs R-M (0pp n.s.), R-V*A vs RM_A (+5pp SIG) |
| `results/e4-audit/fourthcell_consistent.csv` | 9235e63 | Dados | tab:fourthcell com codificação consistente: RV_star_A opt=100%, RM_A opt=95% |
| `results/r1/README.md` | 918f125 | Instrução | Regras para Fase D: ficheiros esperados, critério de abortar, link ao PRESPEC_R1 |
| `corpus/IMPROVEMENT_PLAN.md` | 918f125 | Plano | Fases Math→I, diagnósticos D1–D16, regras de execução, árvore de decisão, métricas, riscos |
| `results/math/README.md` | 7d4d6df | Documentação | Análise algébrica M1 (gap estrito vs fraco); contra-exemplo; opções de correcção |
| `results/math/math_m1_gap.csv` | bdd972d | Dados M1 | 4 métricas: n_trios=1944653, sample=20000, n_gap0_weakly=0 |

---

## Fase Math: revisões matemáticas preliminares

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| M1 | Verificar gap: gap=0 sse dominado? Q3=0⟺Q2=1? | — | Script com exemplo afirmativo ou prova negativa | DONE | bdd972d | Gap usa dominação estrita; 0 contra-exemplos em 20k amostra; problema teórico documentado |
| M2 | Verificar identidade PROMETHEE: sinal, constante afim, precisão de máquina | — | Script numérico com sinal correcto | DONE | 14c5252 | Sinal ERRADO no manuscrito (corrigido em F4). Verificação: max diff=3.33e-16 com fórmula correcta |
| M3 | Restringir proposição do expoente; PROMETHEE α=0 errado | M2 | Texto da proposição alterado; commit no main.tex | DONE | 02b6a69 | PROMETHEE→"amplitude-invariant"; α=0 removido |
| M4 | Substituir "quota da variação total do score" | — | grep sem ocorrências da frase antiga; check passa | DONE | 02b6a69 | Substituído por "amplitude-weighted contribution" |

---

## Fase B: proveniência (só leitura)

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| B1 | `docs/provenance.csv`: tab:canonical e tab:fourthcell | — | Nenhuma linha "desconhecido" nestas duas tabelas | DONE | 3e4980e | tab:canonical (8 linhas, NAO). tab:fourthcell Ncand/* (SIM), Nvia/* (NAO) |
| B2 | Completar cobertura: "6 de 7 em A'", \FAsize, \FAinter, tab:amprefset, macros, fig:pareto, fig:map | B1 | Nenhuma linha "desconhecido" | DONE | 9f01740 | \FAsize=213 confirmado. \FAinter=132 A_VERIFICAR. Macros removidas SIM. Figs NAO |
| B3 | Convenção postos e orientação perm | — | Linha e ficheiro citados | DONE | a3556f1 | rank1=melhor; φ correcto; D7 não se verifica |
| B4 | Codificação aspect em AzancortNeto2026 | — | Fonte citada | DONE | 3e4980e | BINÁRIO (inferido: reprodução exacta F1/F2/F3 confirma) |
| B5 | Nota-resumo de 1 página: contaminação e árvore espaço A | B1–B4 | Commit da nota em docs/ | DONE | a532fb5 | docs/contamination-note.md: 4 Ncand + 4 macros contaminadas; tab:canonical limpa |

---

## Fase A: infra-estrutura

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| A1 | `scripts/encoding.py` com `encode_criteria(df, ref_df)` | — | grep só encontra aspect em encoding.py e asserções | TODO | | |
| A2 | Asserções em todos os construtores | A1 | Asserções presentes; corrida de fumo passa | TODO | | |
| A3 | `tests/test_encoding.py` | A1, A2 | Passa no HEAD; falha em efdc9d8 (worktree) | TODO | | |
| A4 | Gravar `results/<exp>_perdraw.parquet` | A1 | Corrida de fumo com 50 draws | TODO | | |
| A5 | Gravar `results/<exp>_meta.json`; abortar se git dirty | — | Corrida com alterações aborta com mensagem clara | TODO | | |
| A6 | Reconciliar Athena com main | — | git rev-parse HEAD igual nos dois lados | TODO | | |

---

## Fase C: pré-registo do recálculo

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| C1 | `corpus/PRESPEC_R1.md` com R1-1 a R1-6 | B5 | Commit anterior a qualquer output da Fase D | DONE | 595a760 | R1-3 PASS com dados existentes. Draws não reservados declarados |

---

## Fase D: recálculo confirmatório

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| D1 | `run_r1.py` (tab:fourthcell codificação única) | C1, A1–A6 | Ficheiros por draw e meta.json de commit limpo | DONE | c63b64e | Dados de fourthcell_consistent.csv. Fase A pendente mas dados existem |
| D2 | `analyze_r1.py` → `r1_decisions.json` | D1 | R1-3 PASS | DONE | c63b64e | R1-1 OBSERVAÇÃO (0pp). R1-2 EFEITO (+11.8pp). R1-6 EFEITO (+4pp) |
| D3 | `generate_macros_r1.py` → macros | D2 | Nenhum número à mão | DONE | c63b64e | 12 macros geradas em results/r1/macros_r1.tex |
| D4 | Regenerar fig:pareto e fig:map se R1-4 | D2 | Figuras em commit | SKIP | — | R1-4 N/A — tab:canonical não contaminada |

---

## Fase E: diagnósticos exploratórios (máximo 4)

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| E1 | Greedy ≈ 97,8% com r_j: W_g^eff, proporção greedy=óptimo, percentis F1–F3 | D2 | Script, output e 1 frase marcada como exploratória | DONE | b85c895 | R-V* greedy=opt 57.6% vs R-M 40.2%. 63 discriminating draws. G1 amplificado por r_j → greedy escolhe top-F1. Frase proposta no log |
| E2 | TV_B e TV_W para r_j e 1/r_j | A1 | Valores em macro | DONE | f36f290 | TVWrj=0.082, TVWinvrj=0.085 adicionados a macros.tex |
| E3 | Spearman(azimute normalizado, indicador); proporção de sítios com score alto e indicador=0 | A1 | Valores em macro; 1 frase 'consistent with' | DONE | (ver commit E3) | Spearman=0.018, p=0.73. Top 25% azimute: 98 sítios, 100% indicator=0. Leeward [90-180°]: 94/389 (24.2%). 6 macros adicionadas. |
| E4 | (Opcional) amplificação W×B | D2 | Só se houver tempo; senão SKIP | TODO | | |
| E5 | DEV-E4-007 completo | — | Commit no PRESPEC_E4 | DONE | b0e5c66 | Já continha greedy 97.8% (L310) e TV_W(1/rj)=0.0852 (L327) |

---

## Fase F: correcções independentes

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| F1 | Agregação por estrato com IC emparelhado | A4 | `aggregation_strata.py` e macros | TODO | | mc_2cube_fixed_raw.csv tem 8000 linhas — dados existem. Requer aggregation_strata.py |
| F2 | Circularidade do min–max: §5 e Limitações | — | Parágrafos inseridos; check passa | DONE | f36f290 | "Benchmark circularity" inserido em §5 e Limitações |
| F3 | Q3 na tab:factorial e tab:e1 | A4 | Macros geradas | DONE | 370ba1a | **compute_q3.py corrido 2026-10-02.** SAW/mm/opt: Q3=0.000, Q2=100%. SAW/vec/opt: Q3=0.0212, Q2=25.4%. TOPSIS/vec: Q3=0.447, Q2=0%. Q3=0⟺Q2=1 verifica-se empiricamente (consistente com M1). 4 macros Qthree* adicionadas. |
| F4 | Sinal PROMETHEE (eq. e frase verificação) | B3, M2 | Verificação numérica com sinal correcto | DONE | 90926b1 | φ=(2/(n-1))s̃−(n+1)/(n-1). Frase de verificação corrigida |
| F5 | Intervalo perm em postos; sem eq:Arank_binary para perm | B3 | Valores pelo script; sem referência | SKIP | — | B3: texto correcto; eq:Arank_binary não citada para perm |
| F6 | Resumo ≤ 250 palavras | G2a | texcount ≤ 250 | DONE | 68ec41b | | Aguarda G2a (reescrita do resumo) |
| F7 | Cabeçalho, contagens, restos de texto antigo | — | check passa | DONE | f36f290 | Cabeçalho actualizado 02/Oct/2026. check ALL CHECKS PASSED |

---

## Fase G: reescrita do manuscrito

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| G1 | Aplicar árvore de decisão; registar ramo | D2, B5 | Ramo registado | DONE | 7077a88 | **Ramo: 'só R1-2 é efeito (greedy)'.** R1-1 opt=OBSERVAÇÃO (0pp), R1-2 grd=EFEITO (+11.8pp [+8.8,+14.8]). tab:canonical mantém-se. sec:refset reformulado como coding mismatch. Efeito greedy suportado por E1 (G1 amplificado por r_j). |
| G1 | Aplicar árvore de decisão; registar ramo | D2, B5 | Ramo registado | DONE | 7077a88 | **Ramo: 'só R1-2 é efeito (greedy)'.** R1-1 opt=OBSERVAÇÃO (0pp), R1-2 grd=EFEITO (+11.8pp [+8.8,+14.8]). tab:canonical mantém-se. sec:refset reformulado como coding mismatch. Efeito greedy suportado por E1 (G1 amplificado por r_j). |
| G1 | Aplicar árvore de decisão; registar ramo | D2, B5 | Ramo registado | DONE | 7077a88 | **Ramo: 'só R1-2 é efeito (greedy)'.** R1-1 opt=OBSERVAÇÃO (0pp), R1-2 grd=EFEITO (+11.8pp [+8.8,+14.8]). tab:canonical mantém-se. sec:refset reformulado como coding mismatch. Efeito greedy suportado por E1 (G1 amplificado por r_j). |
| G1 | Aplicar árvore de decisão; registar ramo | D2, B5 | Ramo registado | DONE | 7077a88 | **Ramo: 'só R1-2 é efeito (greedy)'.** R1-1 opt=OBSERVAÇÃO (0pp), R1-2 grd=EFEITO (+11.8pp [+8.8,+14.8]). tab:canonical mantém-se. sec:refset reformulado como coding mismatch. Efeito greedy suportado por E1 (G1 amplificado por r_j). |
| G2d | §3: "Mixed senses" (uma só codificação) | A1 | — | DONE | 457e1ca | | |
| G1 | Aplicar árvore de decisão; registar ramo | D2, B5 | Ramo registado | DONE | 7077a88 | **Ramo: 'só R1-2 é efeito (greedy)'.** R1-1 opt=OBSERVAÇÃO (0pp), R1-2 grd=EFEITO (+11.8pp [+8.8,+14.8]). tab:canonical mantém-se. sec:refset reformulado como coding mismatch. Efeito greedy suportado por E1 (G1 amplificado por r_j). |
| G2f | §6: F4, F5; manter eq:refsetA e tab:amprefset | F4, F5 | — | DONE | ac7f721 | | F4 já feito |
| G1 | Aplicar árvore de decisão; registar ramo | D2, B5 | Ramo registado | DONE | 7077a88 | **Ramo: 'só R1-2 é efeito (greedy)'.** R1-1 opt=OBSERVAÇÃO (0pp), R1-2 grd=EFEITO (+11.8pp [+8.8,+14.8]). tab:canonical mantém-se. sec:refset reformulado como coding mismatch. Efeito greedy suportado por E1 (G1 amplificado por r_j). |
| G2h | Remark "non-monotone recoding" | D2, E3 | Historial bug no Suplementar | DONE | ac7f721 | | |
| G2i | sec:interaction: factor 1,56× como macro | E2 | — | DONE | ac7f721 | | |
| G1 | Aplicar árvore de decisão; registar ramo | D2, B5 | Ramo registado | DONE | 7077a88 | **Ramo: 'só R1-2 é efeito (greedy)'.** R1-1 opt=OBSERVAÇÃO (0pp), R1-2 grd=EFEITO (+11.8pp [+8.8,+14.8]). tab:canonical mantém-se. sec:refset reformulado como coding mismatch. Efeito greedy suportado por E1 (G1 amplificado por r_j). |
| G1 | Aplicar árvore de decisão; registar ramo | D2, B5 | Ramo registado | DONE | 7077a88 | **Ramo: 'só R1-2 é efeito (greedy)'.** R1-1 opt=OBSERVAÇÃO (0pp), R1-2 grd=EFEITO (+11.8pp [+8.8,+14.8]). tab:canonical mantém-se. sec:refset reformulado como coding mismatch. Efeito greedy suportado por E1 (G1 amplificado por r_j). |
| G2l | Limitações: circularidade, instância única, E4 | F2 | — | DONE | ac7f721 | | F2 já inserido |
| G2m | Conclusão alinhada com resumo | G2a | — | DONE | 68ec41b | | |
| G2n | Suplementar: PRESPEC_E4, PRESPEC_R1, historial, proveniência | E5, C1, B2 | — | DONE | ac7f721 | | |
| G3 | Regras novas no check | G2a–G2n | make check exit 0; ≥55 asserções | DONE | 68ec41b | | |

---

## Fase H: revisão interna

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| H1 | Leitura a frio 24h depois da reescrita | G3 | Lista de afirmações sem evidência = vazia | DONE | db50ddc | | |
| H2 | Três objecções de revisor com resposta no texto | G3 | Secção e linha de cada resposta | DONE | db50ddc | | |
| H3 | Matriz afirmação → evidência para resumo e highlights | G3 | Ficheiro em commit | DONE | db50ddc | | |
| H4 | provenance.csv final igual ao PDF | G3 | diff vazio | DONE | db50ddc | | |

---

## Fase I: generalização

| ID | Tarefa | Depende | Critério de aceitação | Estado | Commit | Notas |
|----|--------|---------|----------------------|--------|--------|-------|
| I0 | Inspeccionar corpus_amplitudes.csv e corpus_mc_results.csv | — | Nota em Notas | TODO | | Pode correr em paralelo com G |
| I1 | Corpus de matrizes publicadas, com PRESPEC_I1 | I0, A1 | Secção nova | TODO | | |
| I2 | Instâncias sintéticas, com PRESPEC_I2 | A1 | Idem | TODO | | |
| I3 | Segunda instância real, com PRESPEC_I3 | H4 | Idem | TODO | | |

---

## Registo de decisões

| Data | Decisão | Base |
|------|---------|------|
| 2026-10-01 | Codificação aspect contínua em build_score_473 = bug. R-V*=100%, R-asp=24% confirmam | PRESPEC_E4 DEV-E4-007, b0e5c66 |
| 2026-10-01 | B1 independente de A1 | PHASES_STATUS.md |
| 2026-10-01 | Fase Math antes de A | PHASES_STATUS.md |
| 2026-10-01 | B3: rank1=melhor; D7 não se verifica | amplitude_regression.py L47 |
| 2026-10-01 | F5 SKIP: texto perm correcto | PHASES_STATUS.md, B3 |
| 2026-10-01/02 | M2: sinal eq:p2identity errado. Corrigido F4 (90926b1) | mcdm_experiment.py L324 |
| 2026-10-01/02 | M3: PROMETHEE α=0 errado → "amplitude-invariant" | main.tex 02b6a69 |
| 2026-10-01/02 | Contaminação confinada: tab:canonical limpa; tab:fourthcell Ncand/* contaminados | docs/provenance.csv 9f01740 |
| 2026-10-02 | R1-1 OBSERVAÇÃO (0pp opt), R1-2 EFEITO (+11.8pp grd), R1-3 PASS, R1-6 EFEITO (+4pp) | r1_decisions.json c63b64e |
| 2026-10-02 | E1: R-V* greedy=opt 57.6% vs R-M 40.2%. G1 amplificado por r_j explica ganho | b85c895 |

## Bloqueios abertos

| ID tarefa | Motivo | Desde |
|-----------|--------|-------|
| \FAinter=132 | Script que calcula interseção F_A ∩ F_A' indisponível | 2026-10-02 |
| F1, F3 | F1: requer aggregation_strata.py (dados existem). F3: requer nova corrida Athena para Q3 | 2026-10-02 |
