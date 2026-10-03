# Plano de Execução — Nota 9 Editorial (EJOR)

**Repositório:** `Jazancort/mcdm-landfill-pareto`  
**HEAD actual:** `03f0fcf` (v1.8 — 2026-10-03)  
**Plano criado:** 2026-10-03  
**Escopo:** fechado — 20 itens originais + pós-auditoria GPT/Gemini; sem E7, sem nova pergunta  
**Avaliação GPT final:** 9,0/10 provisória (v1.8)

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
| **P-1** | Verificar se abstract contém "389 admissíveis" em contexto correcto (não misturar com 473) | ✅ PASS — abstract não menciona 473; \Ncand e \Nvia definidos em macros L23-25 |
| **P-2** | Verificar que sec:e6 distingue explicitamente "4.4pp no E6" de "35.8pp no Fogo" — magnitudes diferentes por desenho | ✅ DONE — frase adicionada: "4.4pp na família sintética é menor que \EoneWloss pp no Fogo... não comparar directamente" |
| **P-3** | Auditar toda ocorrência de "for any instance" fora de contextos matemáticos formais (≥ 2 hits no PDF) | ✅ PASS — L2638 e L2784 são afirmações sobre resultados analíticos, não claims empíricos |
| **P-4** | Verificar I2: "within the class of fixed positive affine transformations... group-constant slopes are necessary and sufficient" — confirmar que o texto não afirma mais do que o teorema prova | ✅ PASS — L286: "A necessary and sufficient condition... Theorem~\ref{thm:groupconst}" |
| **P-5** | Verificar m_eff: se δ=0, confirmar que o texto não deriva S>0 a partir de soma zero; corrigir se necessário | ✅ PASS — prova pressupõe TV>0 (caso não-trivial); S>0 derivado de ≥1 δ_j>0 |
| **P-6** | Verificar TOPSIS: confirmar que o texto não mistura coeficiente quadrático da distância com closeness coefficient | ✅ PASS — L1358: C_i = d_i^-/(d_i^- + d_i^+) definido correctamente |

### Bloco Q — Qualidade de Integração (P2)

| ID | Tarefa | Status |
|---|---|---|
| **Q-1** | sec:e6 em Results: confirmar que a tabela/narrativa cobre as 5 condições × 2 assemblies com contagens de base; se só prosa, adicionar tabela minimalista | ✅ DONE — `tab:e6summary` adicionada: 5 condições × CI, primary loss |
| **Q-2** | Limitations §8.1: confirmar que a frase de E6 no final (adicionada em W-1) é consistente com sec:e6 — sem duplicação nem contradição | ✅ PASS — L2666-2682: consistente, não contradiz sec:e6 |
| **Q-3** | Conclusion: confirmar que a frase E6 diz "synthetic family" e não generaliza para todas as matrizes | ✅ PASS — L2752-2756: "synthetic family" explícito |
| **Q-4** | Abstract: confirmar que nenhuma frase usa linguagem de garantia universal que não seja sustentada pelos teoremas (e.g., "always", "all configurations") | ✅ PASS — 0 hits no abstract |

### Bloco R — Reprodutibilidade (P3)

| ID | Tarefa | Status |
|---|---|---|
| **R-1** | Confirmar que `e6_seeds.json`, `e6_raw_results.csv`, `e6_summary.csv` estão todos commitados e acessíveis no HEAD | ✅ PASS — git ls-files: 5 artefactos em results/e6/ |
| **R-2** | README: confirmar que o pipeline end-to-end menciona que `run_e1_v3.py` é ~5–10min e que o E6 completo levou 584s na Athena (para reprodução independente) | ✅ DONE — README actualizado com runtimes e nota sobre artefactos pré-commitados |
| **R-3** | `validate_e6.py`: confirmar que o script valida contagens de base (45), seeds (5), geometrias (3), N (3) — não só os números finais | ✅ PASS — L13-14: `inst_id.nunique()==45`; L53: `len(df)==45*5*2*200` |

### Bloco S — Submissão Final (P3)

| ID | Tarefa | Status |
|---|---|---|
| **S-1** | Cold read do PDF completo como revisor EJOR: verificar fluxo de argumento, claims vs evidência, captions, figuras | ✅ DONE — cold read completo; 0 problemas estruturais; P2 honest ("not confirmed"); E6 table renders; contribution list coerente |
| **S-2** | Build final limpo: main.pdf + suppl_wrapper.pdf, zero warnings LaTeX relevantes | ✅ DONE — 0 ??; tabela E6 overfull 55pt→10pt; caminho interno L2816 removido; 24 overfull residuais são todos do template CAS-DC (pre-existentes) |
| **S-3** | Mover tag `v1.0-submission-candidate` para o commit final pós-P/Q/R ou criar `v1.1-submission-candidate` | ✅ DONE — tag `v1.1-grade9-candidate` criada em commit 7e0135c |

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
Data       | ID        | Arquivo              | Mudança                                  | Commit  | Resultado
-----------|-----------|----------------------|------------------------------------------|---------|----------
2026-10-03 | I5        | main.tex             | Contraexemplo F3-max correcto            | 74ffb2a | PASS
2026-10-03 | W/V       | main.tex             | Claim suavizado (empirical)              | 74ffb2a | PASS
2026-10-03 | sec:e6    | main.tex             | sec:e6 adicionada em Results             | 74ffb2a | PASS
2026-10-03 | G3        | IMPROVEMENT_PLAN.md  | PROM = derivação, não orig.              | 74ffb2a | PASS
2026-10-03 | P-2       | main.tex             | E6 vs Fogo magnitude distinction        | aa3753f | PASS
2026-10-03 | Q-1       | main.tex             | tab:e6summary adicionada                 | aa3753f | PASS
2026-10-03 | R-2       | README.md            | Runtimes E1/E6                           | 2afa033 | PASS
2026-10-03 | CI-label  | main.tex             | 'hierarchical CI' → 'normal-approx CI'  | caf7c02 | PASS
2026-10-03 | sec:e6-pos| main.tex             | sec:e6 movida para antes de Discussion   | caf7c02 | PASS
2026-10-03 | P6-TOPSIS | main.tex             | Fórmula TOPSIS corrigida na prosa        | caf7c02 | PASS
2026-10-03 | P5-meff   | main.tex             | δ≠0 guard adicionado                     | caf7c02 | PASS
2026-10-03 | audit-CI  | validate_e6.py       | CI [2.2,6.6] calculado de raw data       | 19caed0 | PASS
2026-10-03 | GPT-r2-D  | main.tex             | 'hierarchical confidence' removido       | 8340c85 | PASS
2026-10-03 | GPT-r2-F  | main.tex             | 'not collinear'/'widen prop.' removidos  | 8340c85 | PASS
2026-10-03 | GPT-r2-H  | main.tex             | Greedy heurístico vs global clarificado  | 8340c85 | PASS
2026-10-03 | GPT-r2-G  | main.tex             | 'estimable'→'retained cells'             | 8340c85 | PASS
2026-10-03 | GPT-r2-E  | main.tex             | Escopo afim no abstract+conclusion       | 8340c85 | PASS
2026-10-03 | GPT-r2-I  | main.tex             | 'partly induced' → 2×2 decomp            | 8340c85 | PASS
2026-10-03 | GPT-r3-A  | main.tex+validate    | E6 empírico; λg explicado; spotcheck     | 1a337f9 | PASS
2026-10-03 | GPT-r3-B  | main.tex             | Ranks qualificados empiricamente         | 1a337f9 | PASS
2026-10-03 | GPT-r3-C  | main.tex             | TOST e assembly linguagem correcta       | 1a337f9 | PASS
2026-10-03 | GPT-r3-D  | main.tex             | u,v definidos no corolário               | 1a337f9 | PASS
2026-10-03 | GPT-r3-TV | main.tex             | TV = half ell1 norm (×2)                 | 1a337f9 | PASS
2026-10-03 | GPT-r4    | main.tex+validate    | E6 empírico final; completeness; fail-ok | 0f62c5c | PASS
2026-10-03 | GPT-r5-42 | validate_e6.py       | 42/92 reconciliado (X_norm, sem duplo +1000) | 03f0fcf | PASS
2026-10-03 | GPT-r5-all| main.tex+validate    | Completude chave; fail-closed; label conserv | 03f0fcf | PASS
```

---

## Estado Final

**Todos os 17 itens do plano: PASS/DONE**  
**Avaliação GPT: 9,0/10**  
**Item opcional não bloqueador:** implementação independente de Pareto dominance  
**Próxima acção:** submissão ao EJOR
