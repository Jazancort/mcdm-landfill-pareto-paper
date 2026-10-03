# Plano de Execução — Nota 9 Editorial (EJOR)

**Repositório:** `Jazancort/mcdm-landfill-pareto`  
**HEAD actual:** `74ffb2a` (2026-10-03)  
**Plano criado:** 2026-10-03  
**Escopo:** fechado — 20 itens originais + pós-auditoria GPT/Gemini; sem E7, sem nova pergunta

---

## Estado de Partida (pós-sessão 2026-10-03)

| Check | Status | Evidência |
|---|---|---|
| `check_consistency.py` | ✅ 0 failures | commit 74ffb2a |
| `validate_e6.py` | ✅ PASSED | commit 9cb1537 |
| `verify_macros_permanent.py` | ✅ ALL PASSED | hash ea5dfe07 |
| `test_promethee_identity.py` | ✅ PASSED | — |
| `test_gap_counterexample.py` | ✅ PASSED | — |
| Abstract ≤ 250 palavras | ✅ 231 palavras | — |
| 0 `??` no PDF | ✅ confirmado | pdftotext |
| E6 em Methods/Results (`sec:e6`) | ✅ adicionado | commit 74ffb2a |
| I5 contraexemplo consistente com F3-max | ✅ corrigido | commit 74ffb2a |
| W/V claim suavizado (não "alone accounts") | ✅ corrigido | commit 74ffb2a |
| PROM classificado como derivação/corolário | ✅ corrigido | commit 74ffb2a |
| Supplementary 14pp, 0 `??` | ✅ — | pdftotext |
| Tag `v1.0-submission-candidate` | ✅ pushed | GitHub |

---

## Mapa Claim → Evidência (auditoria P0)

| Claim no manuscrito | Fonte | Artefato | Status |
|---|---|---|---|
| 45 instâncias E6 | protocolo `run_e6_generator.py` | `e6_seeds.json` hash 08db40bd | ✅ VERIFIED |
| M=B=C=100% | analítico (Prop 1) | `validate_e6.py` | ✅ VERIFIED |
| W/V=95.6% [93.4, 97.8] | hierárquico bootstrap | `e6_summary.csv` | ✅ VERIFIED |
| loss\_within=4.4pp CI [2.2, 6.6] | média bases, bootstrap hierárquico | `e6_raw_results.csv` | ✅ VERIFIED |
| TOST p=0.003, CI[-0.86,+1.96] | `tost_25pp.py`, n=500 | `PHASES_STATUS.md` | ✅ VERIFIED |
| E1: within=35.8pp, vector=43.2pp | `verify_macros_permanent.py` | macros.tex hash ea5dfe07 | ✅ VERIFIED |
| \Ncand=473, \Nvia=389 | macros.tex L23-25 | `check_consistency.py` | ✅ VERIFIED |
| PROM ≡ SAW midrank exacto 6.7×10⁻¹⁶ | `test_promethee_identity.py` | commit 171d789 | ✅ VERIFIED |
| gap=0 ≠ Pareto: t=(1,1,0), u=(0,1,0), v=(2,2,1) | `test_gap_counterexample.py` | commit 74ffb2a | ✅ VERIFIED |

---

## Itens Pendentes para Nota 9

Os 20 itens originais estão todos marcados `[x]` no `IMPROVEMENT_PLAN.md`.  
O que segue são os **itens adicionais** identificados na pós-auditoria GPT/Gemini.

### Bloco P — Precisão e Claims (P0/P1)

| ID | Tarefa | Status |
|---|---|---|
| **P-1** | Verificar se abstract contém "389 admissíveis" em contexto correcto (não misturar com 473) | [ ] |
| **P-2** | Verificar que sec:e6 distingue explicitamente "4.4pp no E6" de "35.8pp no Fogo" — magnitudes diferentes por desenho | [ ] |
| **P-3** | Auditar toda ocorrência de "for any instance" fora de contextos matemáticos formais (≥ 2 hits no PDF) | [ ] |
| **P-4** | Verificar I2: formulação "within the class of fixed positive affine transformations... group-constant slopes are necessary and sufficient" — confirmar que o texto não afirma mais do que o teorema prova | [ ] |
| **P-5** | Verificar m_eff: se δ=0, confirmar que o texto não deriva S>0 a partir de soma zero; corrigir se necessário | [ ] |
| **P-6** | Verificar TOPSIS: confirmar que o texto não mistura coeficiente quadrático da distância com closeness coefficient | [ ] |

### Bloco Q — Qualidade de Integração (P2)

| ID | Tarefa | Status |
|---|---|---|
| **Q-1** | sec:e6 em Results: confirmar que a tabela/narrativa cobre as 5 condições × 2 assemblies com contagens de base; se só prosa, adicionar tabela minimalista | [ ] |
| **Q-2** | Limitations §8.1: confirmar que a frase de E6 no final (adicionada em W-1) é consistente com sec:e6 — sem duplicação nem contradição | [ ] |
| **Q-3** | Conclusion: confirmar que a frase E6 diz "synthetic family" e não generaliza para todas as matrizes | [ ] |
| **Q-4** | Abstract: confirmar que nenhuma frase usa linguagem de garantia universal que não seja sustentada pelos teoremas (e.g., "always", "all configurations") | [ ] |

### Bloco R — Reprodutibilidade (P3)

| ID | Tarefa | Status |
|---|---|---|
| **R-1** | Confirmar que `e6_seeds.json`, `e6_raw_results.csv`, `e6_summary.csv` estão todos commitados e acessíveis no HEAD | [ ] |
| **R-2** | README: confirmar que o pipeline end-to-end menciona que `run_e1_v3.py` é ~5–10min e que o E6 completo levou 584s na Athena (para reprodução independente) | [ ] |
| **R-3** | `validate_e6.py`: confirmar que o script valida contagens de base (45), seeds (5), geometrias (3), N (3) — não só os números finais | [ ] |

### Bloco S — Submissão Final (P3)

| ID | Tarefa | Status |
|---|---|---|
| **S-1** | Cold read do PDF completo como revisor EJOR: verificar fluxo de argumento, claims vs evidência, captions, figuras | [ ] |
| **S-2** | Build final limpo: main.pdf + suppl_wrapper.pdf, zero warnings LaTeX relevantes | [ ] |
| **S-3** | Mover tag `v1.0-submission-candidate` para o commit final pós-P/Q/R ou criar `v1.1-submission-candidate` | [ ] |

---

## Cronograma Recomendado

| Sessão | Duração | Foco | Saída mensurável |
|---|---|---|---|
| S1 | 1h | P-1 a P-4: auditar claims e abstract | Cada item marcado PASS ou BLOCKED com linha exacta |
| S2 | 1h | P-5, P-6, Q-1: m_eff, TOPSIS, tabela E6 | Texto corrigido ou confirmado; tabela adicionada se ausente |
| S3 | 1h | Q-2 a Q-4: Limitations, Conclusion, Abstract | Frases auditadas; nenhuma garante mais do que os teoremas |
| S4 | 1h | R-1 a R-3: artefatos, README, validate_e6 | Todos os artefatos acessíveis; README completo |
| S5 | 2h | S-1: cold read completo | Lista de correcções; nenhuma nova por perfeccionismo |
| S6 | 1h | S-2, S-3: build final + tag | PDF limpo, tag pushed |

**Total: ~7h de sessões focadas.** Computação pesada (re-run E6 completo) não é necessária se os artefatos já existem.

---

## Critérios de Nota 9 (EJOR)

Cada critério é **verificável** — não é aspiracional.

| Critério EJOR | Como verificar | Gate |
|---|---|---|
| **Contribuição clara** | Tabela i–v distingue original/derivação/aplicação | IMPROVEMENT_PLAN.md G-3 ✅ |
| **Teoria correcta** | Todos os teoremas têm escopo explícito; nenhuma frase promete mais | P-1 a P-6 |
| **Evidência empírica rastreável** | E6 auditado: sementes, protocolo, CSV, hash | Mapa claim→evidência ✅ |
| **Estatística pareada** | Bootstrap hierárquico com unidade = base; TOST documentado | PHASES_STATUS ✅ |
| **Integração manuscrito** | E6 em Methods+Results+Limitations+Conclusion; sem contradicção | Q-1 a Q-4 |
| **Reprodutibilidade** | Terceiro consegue repetir sem "eu lembro" | R-1 a R-3 |
| **Honestidade científica** | Claims fracos estreitados; nenhum resultado escondido | W/V claim ✅; P-2 |
| **PDF limpo** | 0 `??`, 0 ref quebradas, captions autocontidas | S-2 |

---

## Regras de Operação

1. **Uma tarefa activa por vez.** Fechar antes de abrir a próxima.
2. **BLOCKED ≠ falha.** Se um item não pode ser resolvido, marcar BLOCKED com motivo e estreitar o claim correspondente no manuscrito.
3. **Não criar item 21.** Se surgir novo problema, verifica se cabe num item existente (P/Q/R/S). Se não, registar como DEFERRED.
4. **Hash ≠ auditoria.** O commit prova que o artefato existe; a auditoria verifica que o número no texto coincide com o artefato.
5. **Nota 9 é editorial.** O plano maximiza a probabilidade; não garante o resultado.

---

## Log de Execução

```
Data       | ID   | Arquivo              | Mudança                        | Commit  | Resultado
-----------|------|----------------------|-------------------------------|---------|----------
2026-10-03 | I5   | main.tex             | Contraexemplo F3-max correcto  | 74ffb2a | PASS
2026-10-03 | W/V  | main.tex             | Claim suavizado (empirical)    | 74ffb2a | PASS
2026-10-03 | sec  | main.tex             | sec:e6 adicionada              | 74ffb2a | PASS
2026-10-03 | G3   | IMPROVEMENT_PLAN.md  | PROM = derivação, não orig.    | 74ffb2a | PASS
```

---

## Próxima Acção

**Executar S1:** verificar P-1 a P-4 (abstract 473/389, sec:e6 magnitudes E6 vs Fogo, "for any instance", I2 escopo do teorema). Cada item recebe PASS ou BLOCKED com localização exacta no TeX.
