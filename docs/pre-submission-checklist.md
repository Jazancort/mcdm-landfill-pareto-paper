# Pre-submission Checklist — Revisão externa 2026-10-02

Fonte: revisão às cegas por GPT-4o/Opus antes de enviar a revisores externos.
Documento criado antes de qualquer corrida ou correcção.

---

## 1. Bloqueadores de compilação

| ID | Problema | Onde | Causa | Estado |
|----|---------|------|-------|--------|
| A7 | `check_consistency.py` não lê o PDF — `??` invisíveis ao check | check_consistency.py | Verifica .log mas não o PDF | TODO |
| COMP | Compilar xelatex×3+bibtex; confirmar `??`=0 no PDF via pdftotext | main.pdf | Sequência incompleta | TODO |
| COMP-EQ | Equações (17) e Cor.2 saem da coluna | p.9 e p.12 | Display demasiado largo | TODO |
| COMP-TAB | Coluna "95% CI" da Tab.6 sobrepõe texto | p.17 | Tabela larga 1 coluna | TODO |
| COMP-MACRO | "with 500 = 500 draws" | §5.2(iii) | `\ndraws` junto de número manual | TODO |

---

## 2. Problemas científicos

### 2.1 — Direcção da assimetria invertida (§7.5 e §8.1)
**Problema:** texto diz "deflação custa mais". Dados dizem o contrário:
- r_j ≤ 1 deflaciona perm → custa 0 pp
- 1/r_j ≈ 2.07× inflaciona perm → custa 11.6 pp

**Correcção:** inverter afirmação. P_E4_5 previa deflação custosa → falsificada → reportar.
**Exageros a cortar:**
- "the direction of distortion, not its magnitude, determines the cost" → duas células post hoc, 1 instância
- "is genuine" → demasiado forte
**Proposta:** "in two post hoc cells with nearly equal TV_W, inflating perm cost 11.6 pp and deflating it cost nothing; we do not test whether direction generalises."
**Estado:** TODO

---

### 2.2 — PROMETHEE: N+1 não quebra identidade afim (§6.5, §6.6, §8.4, contribuição v)
**Problema:** N+1 é constante comum a todos os critérios → TV invariante a escalas comuns (eq.15) → não pode quebrar identidade afim. "the exact identity no longer holds for the implemented score" é **falsa**. Verificação empírica logo a seguir dá 6.7×10⁻¹⁶ (confirma que é verdade).
**Causa real da deflação de perm (0.616):** empates nos midranks. Amplitude de φ_perm ≈ 213.5/388 dos outros critérios.
**Prop.2 "w_eff = w_j for any normalisation" é falsa:** PROMETHEE é invariante à normalização mas herda contracção por empates.
**§8.4 e contribuição (v)** têm de ser reescritas: não é o N+1 que causa o efeito, são os empates.
**Estado:** TODO

---

### 2.3 — Tabela 9 mistura proveniências (§7.5)
**Problema:**
- Linha 473/A′ mostra 97.8/100.0 (=R-V*), mas texto diz "drops from 100% to 20%"
- "off-diagonal cells confirm coding mismatch dominates" — tabela já não tem células com codificação inconsistente
- Linhas 473/A (84.6/100) e 389/A (58.8/95.0) são da corrida antiga; codificação de aspect no avaliador A não verificada
**Acção necessária:** B1 → D1 — recalcular tabela com codificação única
**Estado:** TODO (depende B1→D1)

---

### 2.4 — Post hoc vs confirmatório inconsistente (§7.5 e Conclusão)
**Problema:**
- §7.5: "post hoc cell R-V*"
- Conclusão: "The pre-registered confirmatory test found... +11.8 pp"
**Correcção:** R-V* é exploratório (declarado post hoc em DEV-E4-007). O confirmatorio é R1-2 (PRESPEC_R1). Texto tem de ser consistente.
**IC [0,0]:** "not significant (0 pp, 95% CI [0, 0])" → reformular para "identical (100% in both cells, zero variance across draws)"
**Estado:** TODO

---

### 2.5 — +11.8 pp no resumo e highlights sem diagnóstico
**Problema:** resultado post hoc, 1 instância, E1 (diagnóstico greedy) ainda por fazer. Contradiz §8.3 ("min–max on the admissible set is preferable") e 1ª recomendação prática.
**Decisão a tomar:** fazer E1 antes de enviar, OU tirar do resumo/highlights e deixar só em §7.5 como observação exploratória.
**Estado:** DECIDIR

---

### 2.6 — Dois mecanismos vs um mecanismo + advertência (§7.5, §8, Remark 3)
**Problemas:**
- §8 abertura: "two routes to implicit re-weighting, which share one structure (Theorem)"
- Remark 3: "Theorem does not apply to non-monotone recoding"
→ Incompatíveis: se o Teorema não se aplica, não é uma via de re-ponderação.
- §7.5 título "the same mechanism at a higher cost" e abertura "far more costly" → falso com codificação consistente (custo = 0)
- Bug aparece 2× (§7.5 + Remark 3) → manter só no Suplementar
- §7.5 ordem de parágrafos errada: "For completeness, we recall the reference-set amplitude ratio" intercalado no meio

**Estrutura correcta:** 1 mecanismo (re-ponderação, coberto pelo Teorema) + 1 advertência (recodificação não monótona está fora do Teorema e montagem exacta amplifica-a).
**Estado:** TODO

---

### 2.7 — TOST interpretado ao contrário (§Resultados e §8.5)
**Problema:** "not significant in the pooled analysis (TOST p = 0.003)" — p pequeno de TOST significa equivalência demonstrada, não ausência de efeito.
**§8.5:** "sign cell-dependent from −8.4 to +4.4 pp by TOST" → sem significado; TOST não se aplica a um range de estimativas.
**Falta:** IC da célula −8.4. Se excluir −2.5, a agregação tem efeito relevante nessa célula → "least consequential" precisa de qualificação.
**Acção F1:** tabela por estrato com ICs emparelhados (já existe aggregation_strata.csv — é reportar os ICs no texto).
**Estado:** TODO

---

### 2.8 — Contraste de montagem inclui célula fixada por construção
**Problema:** +8.1 pp dentro de min-max = média de +14.0 (SAW, com célula 100% por construção) e +2.2 (TOPSIS). Célula foi excluída do headline de normalização mas não deste.
**Correcção:** reportar também TOPSIS isolado (+2.2) ou assinalar a assimetria de tratamento.
**Estado:** TODO

---

### 2.9 — Circularidade: headlines ignoram o §5.4
**Problema:** §5.4 admite benchmark min-max. Resumo apresenta "+25.4 pp" e §8.3 recomenda min-max sem qualificação.
**Experiência F8 (nova, recomendada):**
- Reconstruir fronteira com objectivos em vector normalisation
- Repetir 4 células SAW
- Previsão: vector/optimal = 100%, min-max perde
- Se confirmado: mensagem "normalização do score deve coincidir com a do modelo de valor" → não circular
**Estado:** TODO (F8 — nova)

---

### 2.10 — Teorema 1: quantificador vai ser questionado
**Problema:** condição (i) "every set of sites and every feasible family" — necessidade quase trivial porque família {T, T′} é escolhida à medida.
**Revisor vai perguntar:** mantém-se para famílias geradas por r-separação sobre um conjunto de sítios?
**Saídas:**
- Remark explícita: quantificador é sobre famílias arbitrárias (inclui r-separação)
- Ou construção em que T = argmax sobre todos os trios viáveis
**Estado:** TODO (menor, mas vale uma Remark)

---

### 2.11 — Menores

| Sub-item | Problema | Acção | Estado |
|----------|---------|-------|--------|
| 2.11a | §6.2: "instead of 388" — midrank max com N=389 é 389, não 388 | Substituir 388→389 | TODO |
| 2.11b | Resumo: "accounts for 35.8 of the 43.2 pp" sugere decomposição aditiva (há interacção +7.4) | "within-group alone costs 35.8 pp; full distortion 43.2 pp" | TODO |
| 2.11c | Fig 4: etiquetas no painel de postos mostram rácios de normalização vectorial | Regenerar com rácios correctos | TODO |
| 2.11d | Contribuição (i) e §6.10 ponto 4: listam ref-set como efeito com custo | Actualizar para "custo 0 com codificação consistente" | TODO |

---

## 3. Figuras

| ID | Figura | Problema | Estado |
|----|--------|---------|--------|
| G2o-F1 | Figura 1 | Números antigos: "+29.9 pp", "Assembly +16.0 pp", "+0.9 pp (n.s.)", "18 cells (17 after…)" | TODO |
| G2o-F4 | Figura 4 | Etiquetas painel ranks mostram rácios vec em vez de rácios rank | TODO |

---

## 4. Ordem de execução recomendada

| Prioridade | Acção | ID | Athena? | Sessão |
|-----------|-------|-----|---------|--------|
| 1 | Compilação + A7 (check PDF) | A7, COMP | Não | 1 |
| 2 | Correcções de texto: 2.1, 2.4, 2.6, 2.7, 2.11a/b | — | Não | 1 |
| 3 | PROMETHEE: 2.2 (requer entender o mecanismo exacto) | — | Não | 1 |
| 4 | Montagem: 2.8 + IC célula −8.4 (F1 dados já existem) | F1 | Não | 1 |
| 5 | F8: experiência circularidade | F8 | Sim | 2 |
| 6 | Regenerar Fig1 e corrigir Fig4 | G2o | Não | 1-2 |
| 7 | B1→D1: recalcular Tabela 9 | B1/D1 | Sim | 2 |
| 8 | Decidir +11.8 (E1 ou tirar) | 2.5/E1 | Depends | 2 |
| 9 | Revisão externa: passagem 1 às cegas | H2 | Não | Após 1-5 |

---

## 5. Prompt de revisão (versão corrigida)

### Passagem 1 — às cegas

```
You are Reviewer 2 for the European Journal of Operational Research. Attached:
the manuscript, the Supplementary Material, and the pre-registration files.

Review the paper as you would a real submission. Structure:
1. SUMMARY: main claims, in your own words.
2. MAJOR ISSUES: for each, give (a) location (section/table/equation),
   (b) why it threatens a claim, (c) severity: fatal / major / minor,
   (d) the specific analysis or correction that would resolve it.
3. MATHEMATICAL CHECK: verify every proposition and the theorem line by line.
   State whether each proof is correct, whether the quantifiers make the
   result non-trivial, and whether the result is new relative to known
   scalarisation results (e.g. Geoffrion 1968).
4. INTERNAL CONSISTENCY: recompute every reported contrast from the tables;
   list every place where abstract, highlights, text, tables and figures disagree.
5. CLAIM-EVIDENCE MAP: for each sentence of the abstract, say which result
   supports it and whether that result is confirmatory or exploratory.
6. RECOMMENDATION with a one-paragraph justification.

Do not comment on formatting or citation style, and do not request a broader
literature review. Be specific; quote the text you criticise.
```

### Passagem 2 — dirigida (só depois da 1ª)

```
Now address specifically, if you have not already:
- Is the Pareto benchmark circular with respect to min-max normalisation,
  and what experiment would break the circularity?
- Does a single instance support each generalisation in the abstract and conclusion?
- Is the aggregation contrast (pooled vs per-cell) presented fairly, and is
  the TOST result interpreted correctly?
- Which results are post hoc, and are they presented as such everywhere?
```

---

## 6. Notas

- Usar dois modelos diferentes (GPT-4o + Claude Opus) e comparar as revisões
- Enviar: manuscript PDF + supplementary.pdf + PRESPEC_R1.md + PRESPEC_E4.md
- NÃO enviar lista de temas nem números — revisor deve encontrá-los
- NÃO enviar antes de completar prioridades 1–4 da tabela acima
