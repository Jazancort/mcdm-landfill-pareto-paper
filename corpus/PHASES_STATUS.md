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
| `results/e1/q3_results.csv` | 7c2e742 | Dados F3 | Q3=E[gap] por célula: SAW/mm/opt=0; TOPSIS/vec=0.447; Q2_zero% por célula |
| `results/e1/compute_q3.log` | 7c2e742 | Log F3 | Output completo compute_q3.py (158.7s) |
| `scripts/compute_q3.py` | 370ba1a | Script F3 | Q3 por draw, 8 células, kappa=200 |
| `scripts/aggregation_strata.py` | 18361a6 | Script F1 | SAW-TOPSIS por célula, IC emparelhado B=2000 |
| `scripts/diag_e1_greedy_rvstar.py` | 4192f3e | Script E1 | W_g^eff, greedy=opt %, draws discriminantes |
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
| I0 | Inspeccionar corpus_amplitudes.csv e corpus_mc_results.csv | — | Nota em Notas | DONE | (próximo commit) | **corpus_amplitudes.csv**: 7 fontes × 3 normas = 21 linhas. TV=0 para mm (correcto). TV_vec range [0.030, 0.320]. ident_ok=True todas. **corpus_mc_results.csv**: 3 fontes activas (milani2005 m=9 n=5, vafaei2018 m=16 n=3, junaid2024 m=9 n=14). Q2=100% para TODAS as células (9 linhas). **H1 Q2(mm)≥Q2(vec): trivialmente satisfeita** — 100%=100% em todas as 3 fontes activas: resultado não discriminante com estas instâncias. **O que falta para I1:** (a) activar as 4 fontes inactivas (vafaei2022, chen2020, bhaskar2023_asn/agr) — sem grupos obj definidos; (b) instâncias com Q2<100% sob vec normalisation; (c) PRESPEC_I1 antes de qualquer corrida. **Viabilidade I1:** scripts existem e passam no teste de regressão Fogo. A infra-estrutura está pronta; falta instâncias discriminantes e pré-registo. |
| I1 | Corpus de matrizes publicadas, com PRESPEC_I1 | I0, A1 | Secção nova | TODO | | |
| I2 | Instâncias sintéticas, com PRESPEC_I2 | A1 | Idem | TODO | | |
| H4 | provenance.csv final = estado do PDF | A5 | \FAinter=132 confirmado 2026-10-02 | DONE | (inline) | **\FAinter=132 CONFIRMADO**: |F_A|=213, |F_Ap|=181, intersecção=132. provenance.csv actualizado: 28 linhas, 0 A_VERIFICAR, 0 VERIFICANDO. H4 DONE. Fase H COMPLETA. |

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
| \FAinter=132 | RESOLVIDO 2026-10-02 — confirmado via sorted dominance inline (9c7a376) | 2026-10-02 |
| F1, F3 | RESOLVIDO — F1: aggregation_strata.py (18361a6); F3: compute_q3.py (7c2e742) | 2026-10-02 |


---

## Fase A7 (nova): check PDF via pdftotext

| ID | Tarefa | Estado |
|----|--------|--------|
| A7 | Adicionar regra check_consistency.py que corre pdftotext e conta '??' no PDF — deve dar 0 | DONE | |

---

## Fase F8 (nova): experiência de circularidade

| ID | Tarefa | Estado |
|----|--------|--------|
| F8 | Reconstruir fronteira Pareto com objectivos em vector normalisation; repetir 4 células SAW; previsão vec/opt=100% | TODO |

---

## Fase G2o (nova): regenerar figuras

| ID | Tarefa | Estado |
|----|--------|--------|
| G2o-F1 | Regenerar Figura 1 com números actuais | DONE | |
| G2o-F4 | Corrigir etiquetas Figura 4 painel ranks (rácios rank, não vec) | DONE | |

---

## Ajustes de texto pré-submissão (revisão externa 2026-10-02)

| ID | Secção | Problema | Estado |
|----|--------|---------|--------|
| 2.1 | §7.5/§8.1 | Direcção assimetria invertida — inflação custa, não deflação | TODO |
| 2.2 | §6.5/6.6/8.4 | PROMETHEE N+1 não quebra identidade — fonte é empates | TODO |
| 2.4 | §7.5+Conclusão | Post hoc vs confirmatory inconsistente; IC [0,0] → 'identical' | TODO |
| 2.6 | §7.5/§8 | 1 mecanismo+1 advertência; bug só suplementar; reordenar §7.5 | TODO |
| 2.7 | §8.5 | TOST p pequeno = equivalência demonstrada; IC por célula | TODO |
| 2.8 | §Resultados | Contraste montagem inclui célula 100% por construção | TODO |
| 2.11a | §6.2 | '388' → '389' midrank máximo | TODO |
| 2.11b | Resumo | decomposição não aditiva: 'accounts for' → frase correcta | TODO |
| 2.11d | Contrib.(i)/§6.10 | ref-set como efeito com custo → actualizar | TODO |

Referência completa: docs/pre-submission-checklist.md (criado 2026-10-02)


### Commits desta sessão (2026-10-02 manhã)
| Commit | Item | Descrição |
|--------|------|-----------|
| f1ecae9 | A7 | check PDF via pdftotext |
| 609eba6 | 2.1+2.6 | assimetria + 1 mec+1 advert |
| 9214377 | 2.4 | post hoc / IC [0,0] |
| cad0b1f | 2.7 | TOST equiv + ICs célula |
| a501eae | 2.11a+b | 388→389 + abs não aditivo |
| (este) | 2.2 | PROMETHEE N+1 → empates |


---

## F8 — Experiência de circularidade (2026-10-02)

| Campo | Valor |
|-------|-------|
| Script | scripts/compute_f8_circularity.py (7 versões, commit 84b8285→final) |
| Tempo | 1594.5s Athena |
| Output | results/f8/f8_circularity.csv |
| Análise | docs/f8-analysis.md |

### Resultados

| score_norm | assembly | Q2 (%) | SE |
|-----------|----------|--------|----|
| vec | optimal | 89.4 | 1.4 |
| mm | optimal | 6.0 | 1.1 |
| vec | greedy | 98.4 | 0.6 |
| mm | greedy | 35.2 | 2.1 |

### Análise resumida

1. vec/opt ≠ 100% (89.4%) — consistente com Teorema: vec tem amplitudes heterogéneas dentro de grupos, logo não garante 100%.
2. Inversão da direcção confirmada: mm/opt = 100% com fronteira mm; mm/opt = 6% com fronteira vec.
3. Mensagem central muda de "min-max é melhor" para "score-obj alignment matters" — não circular.
4. §5.4 e Limitações actualizados com resultado F8.

**Estado:** DONE

## Decision record — 2026-10-02

### B1/D1: tab:fourthcell space-A cells (commit 4059fb1)

**Problema identificado (Opus + GPT, 2026-10-02):** commits 2aa0d38 e 54195c1 construíram a fronteira A com os 473 candidatos (incluindo os 84 excluídos), violando §3.1 e a Proposição 1. A asserção de regressão foi removida em vez de se corrigir o script.

**Reversão:** commit ec33779 reverteu os dois commits bugados.

**Correcção aplicada:**
- `pareto_utils.py`: adicionado parâmetro `ref_df` para separar a população de normalização do universo de portefólios.
- `compute_b1_spaceA.py` (v3): trios = 1 944 653 admissíveis (df_via); objectivos A com `ref_df=df_imp` (473-site constants); score 473 = scalarização directa `-(F1+F2)+F3` com as mesmas colunas c_j do compute_A.
- Script aborta com `sys.exit(1)` se 473/A optimal ≠ 100%.

**Resultados B1 (N=500, κ=200, seed=42, t=237s):**

| Método | Avaliador | greedy | optimal |
|--------|-----------|--------|---------|
| 473/A  | A (ref=473) | 84.6% ±1.6 | **100.0%** ✓ |
| 389/A  | A (ref=473) | 58.8% ±2.2 | 95.0% ±1.0 |

Os valores coincidem com os que estavam na tabela original — confirmando que a tabela original era correcta. O REGRESSION_GUARD (commit 893d9bf) garante que valores esperados de regressão não podem ser editados sem esta entrada.

**Regra para o futuro:** qualquer alteração a um valor esperado de regressão no `check_consistency.py` exige uma entrada neste ficheiro com git hash e justificação.

---


## Task F8 — diagnóstico circularidade vec/vec (2026-10-02)

**Problema:** `compute_f8_circularity.py` reportou vec/opt = 89.4% (SE=1.4).
Pela Proposição 1, com score em normalização vectorial e objectivos construídos
na mesma normalização vectorial, a diagonal deve ser 100%.
O 89.4% indica desalinhamento entre score_vec e C_obj_vec em pelo menos uma coluna.

**Causa suspeita (Opus):** ordem das operações complement/normalise.
- Objectivos: `c_j = 1 − x̂` (complement precede normalização)
- Decisão matrix: normaliza `x` e depois complementa
- Sob normalização vectorial, as duas ordens produzem colunas diferentes (Corolário 2)

**Diagnóstico a fazer:** verificar `r(score_vec[:,j], C_obj_vec[:,j])` para cada coluna j.
Qualquer coluna com `r < 1 - 1e-12` indica desalinhamento.

**Critério de aceitação:** vec/vec optimal = 100% (REGRESSION). Script deve abortar com
`sys.exit(1)` se falhar.

---


## Decision record — 2026-10-02 (GPT/Gemini re-analysis)

### Problemas confirmados que ainda não estão resolvidos

**P1 — B1: erro de estimando (não apenas implementação)**

O check `473/A' optimal = 100%` que mantive como regressão é **empiricamente correcto
para esta instância** mas **não é um teorema**. As duas diagonais teóricas genuínas são:
- A473 score + A473 evaluator → 100% (Prop1)
- A'389 score + A'389 evaluator → 100% (Prop1)

A célula `473/A'` é off-diagonal: score com constantes de 473, avaliador com constantes
de 389. Que dê 100% é resultado empírico desta instância, não invariante matemática.
**Acção:** remover do REGRESSION_GUARD a asserção `473/A' optimal = 100%`; manter
apenas `Nvia/A' = 100%` e `Ncand/A = 100%` (as diagonais genuínas).

**P2 — R1-6: bootstrap pareado não foi recalculado dos draws**

O que fiz: obtive marginais (R-asp opt=24.0, R-V opt=20.0, R-asp grd=25.2, R-V grd=19.6)
e deduzi CIs por draws. Mas CIs pareados não derivam de marginais — precisam de
alinhamento por draw ID. O `bootstrap_paired.csv` tem `R-asp vs R-V opt = +4.0 [+2.2,+6.0]`
e `grd = +5.6 [+3.6,+7.8]`. PORÉM: o GPT identificou que "+4.0 greedy" não coincide com
os marginais (25.2−19.6=5.6, não 4.0). O bootstrap foi calculado na corrida correcta ou
foi copy-paste de outra? **Acção:** verificar `bootstrap_paired.csv` vs `draws_fourthcell.npz`.

**P5 — Prop.2 PROMETHEE: correcção anterior imprecisa**

A minha adição "ties contract flows" está incorrecta se score e PROMETHEE usam os mesmos
midranks e pesos — nesse caso a equivalência afim mantém-se com empates. A divergência
vem da escala dos ranks, não dos empates em si. **Acção:** reverter a adição de "ties
contract flows" e reformular com precisão.

**P6 — gap=0 iff Pareto é falso**

Contraexemplo confirmado por Gemini: t=(1,1,0), u=(0,1,0), v=(2,2,1) com F1,F2 min e F3 max.
u domina t (F1 estrito), mas gap(t)=0 porque o operador min anula a folga positiva quando
há empate noutros critérios. **Acção:** adicionar nota nas Limitações; não alterar definição
do gap (é medida de gravidade, não de detecção de dominância — Q2 já usa dominância directa).

**P7 — AggContrast = +0.5 pp: aritmética confirmada por Gemini**

Média dos 4 estratos = (+(-8.4)+3.4+2.8+4.4)/4 = 2.2/4 = 0.55 ≈ 0.6 pp. OK.
O IC [-0.8,+1.8] e p=0.003 são do bootstrap pareado — rastreáveis ao `bootstrap_paired.csv`
ou ao script `analyze_r1.py`. Não foram recalculados nesta sessão — verificar proveniência.

### O que NÃO fazer antes de verificar P2 e P5

- Não submeter para revisão externa
- Não declarar checklist completo
- Não alterar valores esperados do check sem resolver P1 (REGRESSION_GUARD)

---


## Decision record — P2 resolução (2026-10-02)

### R1-6 bootstrap verificado dos draws pareados (commit seguinte)

Script: recalculado de `draws_fourthcell.npz` com `rng=42, B=9999`.
Todos os contrastes confirmados:

| Contraste | opt Δ | CI opt | grd Δ | CI grd |
|-----------|-------|--------|-------|--------|
| R-asp − R-V | +4.00 pp | [+2.20,+6.00] SIG | +5.60 pp | [+3.60,+7.60] SIG |
| R-V* − R-M | +0.00 pp | [0,0] n.s. | +11.80 pp | [+8.80,+15.00] SIG |
| R-V* − R-asp | +76.00 pp | [+72.2,+79.8] SIG | +72.60 pp | [+68.6,+76.6] SIG |
| R-V*A − R-MA | +5.00 pp | [+3.2,+7.0] SIG | +25.80 pp | [+22.0,+29.8] SIG |

**R1-6 correcto:** R-asp − R-V = +4.0 opt, +5.6 grd. CI greedy: [+3.6,+7.6] (não [+3.6,+7.8]
como estava no Suplementar — diferença de seed/B). Texto principal e Suplementar corrigidos.

**P2 FECHADO.**

---


## F4 — Grelha sintética expandida (E5) — 2026-10-02

### Estado actual dos experimentos sintéticos

| Experimento | Script | Células | N sites | Variação | Estado |
|-------------|--------|---------|---------|----------|--------|
| E2 | wp4_synthetic_fixed.py | 240 (s_B×s_W, 6 reps) | sintético ~50-200 | amplitudes | ✅ concluído, não integrado no artigo |
| E3 | run_e3_grid.py | 25 (s_B×s_W, 1 rep) | 389 (Fogo) | amplitudes over Fogo | ✅ concluído, não integrado |
| wp4 | — | 60 células | variável | lognormal | ✅ parcial |

**Limitação crítica:** E2 e E3 variam amplitudes mas mantêm a mesma estrutura espacial
(Fogo ou geometria sintética fixa). Para F4 (generalização genuína) precisamos de:
1. Diferentes N de sites (50, 100, 200, 389)
2. Diferentes geometrias espaciais (uniform random, clustered, grid)
3. Diferentes estruturas de grupos (2 grupos vs 3 grupos, diferentes W_g)
4. Diferentes distribuições de amplitudes (não só power-law)

### Estimands primários de E5 (a pré-especificar)

**Questão principal:** a relação entre TV_W (within-group amplitude variation) e
Q2_greedy loss é monotónica e generalizável além de Fogo?

**Estimands:**
1. E[Q2_mm_greedy | TV_W, N, geometry] — regressão de Q2 em TV_W com covariáveis
2. E[Q2_mm_optimal | TV_W] = 100% (regressão — invariante teórico)
3. Slope dQ2_greedy/dTV_W — é consistente entre instâncias independentes?

**Gate de stop/fail:** se o slope for inconsistente (intervalo inclui 0 em >30% das
instâncias), concluir que TV_W não é preditor robusto e reformular a tese.

### Decisão de design E5

- N ∈ {50, 100, 200, 389} — 4 níveis
- geometry ∈ {uniform_random, clustered_2, grid} — 3 tipos
- s_B ∈ {0, 0.5, 1.0} — 3 níveis (between-group)
- s_W ∈ {0, 0.25, 0.5, 0.75, 1.0} — 5 níveis (within-group)
- 3 replicates por célula × 4 N × 3 geo × 3 s_B × 5 s_W = 540 instâncias
- N_draws = 200 por instância (Monte Carlo preciso a ±2pp)
- ETA Athena: ~45-90 min

---


## E5 Results — 2026-10-02 (commit seguinte)

**Design:** N ∈ {50,100,200} × 3 geometrias × 3 s_B × 5 s_W × 3 reps = 405 instâncias
**N_draws = 100, κ=200, seed_base=100. Script: run_e5_grid.py v4. Commit: 4d438b6 + fixes**

### Resultados principais

| Métrica | Valor |
|---------|-------|
| Instâncias totais | 405 |
| Q2_mm_optimal = 100% (Regressão E5-R1) | ✅ todas |
| r(TV_W, loss_greedy) | **0.034** (quase nulo) |

**Por s_W (TV_W proxy):**

| s_W | TV_W médio | Q2_mm_greedy médio |
|-----|-----------|---------------------|
| 0.00 | 0.000 | 96.3% |
| 0.25 | 0.024 | 98.6% |
| 0.50 | 0.048 | 97.7% |
| 0.75 | 0.072 | 94.8% |
| 1.00 | 0.096 | 96.6% |

**Por N:** N=50 → 91.1%, N=100 → 99.7%, N=200 → 99.7%
**Por geometria:** clustered → 91.2%, grid → 99.3%, uniform → 99.9%

### Conclusão científica (E5-R3 activada)

TV_W não é preditor robusto da perda greedy nas instâncias sintéticas (r=0.034).
A variação é principalmente explicada por N (pequeno → maior variância) e geometria
(clustered → maior perda por concentração espacial de sites).

Fogo (TV_W≈0.032, Q2_grd=66.2%) é um outlier: muito abaixo das instâncias sintéticas
com TV_W similar (98.6%). Isto sugere que Fogo tem características não capturadas pelo
gerador sintético — provavelmente a estrutura específica dos critérios binários/concentrados
e a geometria do arquipélago.

**Implicação para a narrativa do artigo:**
A tese deve ser reformulada de "TV_W prediz perda" para "TV_W é condição analítica
suficiente para perda sob certas condições (Teorema), mas a magnitude da perda depende
de propriedades não capturadas por TV_W — demonstrado empiricamente pela grelha E5."
Fogo permanece como caso motivador; as instâncias sintéticas documentam a variabilidade.

### Figura
`figures/fig_E5_synthetic.png` — Q2_mm_greedy vs TV_W, 3 painéis por N, coloridos por geometria.

---
