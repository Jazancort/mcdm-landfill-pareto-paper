# Plano de melhorias — Artigo MCDM Fogo/Omega
**Versão:** 2.0 — 2026-10-01 (revisão após auditoria completa do manuscrito)
**Objetivo:** submissão defensável à Omega em 6 semanas.

---

## Estado actual verificado (não o que o plano anterior assumia)

| Item | Estado real |
|---|---|
| F8 circularity | Já está no texto: §5.4 (linha 1017) e §8.6 (linha 2594). Não falta escrever — falta consolidar e corrigir a justificação. |
| DEV-E4-007, commit hashes, PRESPEC no texto | 12 ocorrências confirmadas no texto principal (linhas 2086, 2161, 2165, 2210, 2257, 2659, 2761, 2763, 2767…). Visíveis a qualquer revisor. |
| C(473,3) no §2.5 | Erro confirmado: `\binom{\Ncand}{\kk}` = C(473,3). Correcto é C(389,3) = 9 735 114 (os \Ntrios do artigo). |
| Highlights > 85 caracteres | Segundo highlight confirma exceder o limite (>150 caracteres com os macros expandidos). |
| κ=50 | Mencionado no desenho (§5.1), mas os resultados para κ=50 não aparecem nas tabelas principais. |
| E6: Aj só no score ou também nos objectivos | Pendente de verificação — crítico para validade do experimento. |

---

## Semana 1 — Limpeza e erros factuais (prioridade máxima)

São problemas que um revisor apanha antes de chegar aos resultados. Custo por item: menos de 1 hora cada.

### A. Retirar artefactos de laboratório do texto principal

O manuscrito contém, no corpo do artigo, referências a DEV-E4-007, PRESPEC_E4.md, commit f6042f8, rules R1-1 to R1-6, "earlier version of our pipeline" e "withdrawn from the main text". Um revisor que nunca teve acesso a esse histórico lê isto como: "encontrámos um bug no nosso próprio código".

**O que fazer em cada ocorrência:**

- Linhas 2161-2166 e 2365-2383: substituir "DEV-E4-007" por "a pipeline inconsistency (see Supplementary Material)" e remover "withdrawn from the main text". Mover o detalhe técnico para o suplementar.
- Linha 2257: retirar o commit hash do texto principal. No suplementar é aceitável.
- Linhas 2761-2767: as regras R1-1 a R1-6 são internas. Substituir por "post hoc exploratory cells declared in the Supplementary Material before analysis".
- Linha 2659: DEV-E5-001 a DEV-E5-007 — idem, para o suplementar.

**O que manter:** o resultado substantivo (aspect coding inconsistency cria um artefacto de 80pp que desaparece com codificação consistente) é cientificamente relevante e deve ficar. O que sai é a linguagem de caderno de laboratório que expõe o processo interno.

### E. Erros factuais a corrigir

Verificados um a um contra o PDF:

| Local | Erro | Correcção |
|---|---|---|
| §2.5, linha 527 | `\binom{\Ncand}{\kk}` = C(473,3) | `\binom{\Nvia}{\kk}` = C(389,3) = \Ntrios |
| Theorem 1, "3−1 other sites" | Macro não expandido | Substituir por "two other sites" ou `$\kk-1$` |
| refs.bib | "Kadziski", "Sowiski" | "Kadziński", "Słowiński" |
| refs.bib | "@article{Kinay2019" | Verificar se o nome impresso no PDF está correcto |

Para a Fig. 4 (rácios vs pesos nominais) e para a Tabela 3 (codificação de aspect), identificar a linha exacta no texto e corrigir a descrição. São verificações de 5 minutos cada.

### G. Highlights: limite de 85 caracteres

O segundo highlight actual tem >150 caracteres. O quarto (between-group/within-group) não tem qualificador empírico.

**Versão dentro do limite:**

```
\item Effective weight scales with $w_jA_j$; min--max alone preserves
  elicited weights (Theorem~1)
\item Normalisation worth $+\NormGreedyContrast$~pp (greedy); aggregation
  $+\AggContrast$~pp pooled, sign depends on normalisation
\item Exact assembly gains $+\AsmMM$~pp under min--max; loses $-\AsmVec$~pp
  under vector (both significant)
\item Between-group distortion costs nothing on Fogo; within-group
  distortion accounts for most of the observed loss
\item Normalising over inadmissible sites costs up to 80~pp; effect is an
  artefact of non-monotone aspect coding, not an inherent property
```

Cada linha deve ser verificada com `wc -c` ou equivalente depois de expandir os macros com os valores actuais.

---

## Semana 1 (continuação) — Bloco 2 e Bloco 1

### Bloco 2 — Framing analítico vs empírico

Sem alterações face ao plano anterior. Auditar abstract, §1 e §8 para separar afirmações analíticas (Theorem 1, identidade de amplitude) de afirmações empíricas (+25.4pp, +35.8pp). Nas empíricas, adicionar "on this instance".

**Adicionalmente:** remover "55 studies" sem protocolo. A frase da linha 589 deve ou descrever o critério de inclusão (conjunto de candidatos ≥ 10, critérios espaciais, etc.) ou passar para um número mais conservador com citações directas.

### Bloco 1 — Consolidar F8 e corrigir a justificação

F8 existe em §5.4 e §8.6. A tarefa não é escrever de raiz.

**O que fazer:**

Fundir as duas ocorrências numa subsecção da Discussão. Cortar a repetição. No conteúdo, substituir o argumento "os objectivos existem em unidades físicas antes da normalização" pelo argumento de teoria de valor multiatributo:

Na MAVT, um peso só tem significado relativo ao intervalo definido para aquele critério (Keeney & Raiffa 1976; Belton & Stewart 2002; Choo et al. 1999). Min-max sobre o conjunto admissível é a escala de valor parcial linear local sob a qual os pesos AHP foram elicitados: é a escala em que "quanto vale uma unidade de F₁ versus uma unidade de F₂" tem a interpretação pretendida pelo analista. A escolha não é circular porque reflecte o modelo de preferência declarado; é uma limitação de âmbito porque generaliza só para configurações onde o mesmo modelo é adoptado.

Este argumento é mais forte do que o anterior porque está alinhado com §3.2 (que já diz que F é um espaço de valor parcial) e antecipa a crítica directamente.

**Verificar também:** SAW/vec/greedy = 100% contra fronteira vector. Provável explicação: com objectivos vector, perm domina o somatório pela mesma razão que na célula B (efeito quasi-lexicográfico). Confirmar com `diag_e1_greedy_rvstar.py` ou equivalente e acrescentar uma frase no texto.

---

## Semana 2 — Reanálise dos contrastes e literatura

### B. Contraste de agregação e TOST

**Problema 1:** o contraste agregado SAW−TOPSIS (+0.5pp) inclui SAW/mm/opt, que vale 100% por construção. O mesmo acontece com +8.1pp de assembly sob min-max (herda os +14.0 do SAW). O artigo já exclui essa célula do contraste de normalização; tem de ser coerente aqui.

**O que fazer:** recalcular os contrastes principais excluindo a célula construída. Reportar as duas versões numa nota de rodapé ou numa linha adicional da tabela: "excluding the SAW/mm/opt cell (fixed at 100% by Theorem 1): …pp".

**Problema 2:** o TOST declara equivalência sobre uma média de efeitos de sinal oposto (−8.4 a +4.4pp). Isto não é "ausência de efeito de agregação"; é uma interacção. A conclusão correcta é: "aggregation has no main effect; its effect depends on the normalisation". A frase "aggregation is worth 0.5pp" deve mudar em todo o texto.

**Problema 3:** "empirical ρ ≈ 0.5" na pré-especificação. Se foi calculado depois de ver os dados, retirar ou descrever o piloto de onde veio.

### C. Tensão interna: TV_W > 0 em R-V* não causa perda

R-V* tem amplitudes que variam dentro dos grupos (perm 0.482, slope 0.683, roads 1.0 em G1, segundo a Tabela 9) e ainda assim obtém 100% em assembly óptima. Isso não contradiz o Theorem 1, que é condicional (amplitudes constantes dentro do grupo garantem eficiência; não diz que variação dentro do grupo causa perda). Mas enfraquece o highlight "within-group distortion drives the loss" como afirmação geral.

**O que fazer:** calcular TV_W para R-V* (usando o mesmo script de amplitude). Colocar ao lado do valor da célula W na tabela de decomposição. Adicionar uma frase: "a non-zero TV_W is necessary but not sufficient for loss; the direction and structure of the distortion also matter, as illustrated by R-V*."

### D. Literatura em falta

A identidade $w_j^{\text{eff}} \propto w_j A_j$ está relacionada com a literatura de range sensitivity e swing weighting. Os trabalhos relevantes:

- von Nitzsch & Weber (1993): "The effect of attribute ranges on weights in multiattribute utility measurements"
- Fischer (1995): range frequency na elicitação de pesos
- Keeney & Raiffa (1976): peso só tem significado relativo ao intervalo

**O que fazer:** adicionar 2-3 citações no §2.2 ou no §6.1 (amplitude identity). O argumento passa a ser: "esta relação é conhecida qualitativamente (von Nitzsch & Weber, Fischer, Keeney & Raiffa); a contribuição deste trabalho é a forma fechada exacta para SAW, TOPSIS e PROMETHEE, e a medição da consequência em eficiência de Pareto."

Verificar os DOIs antes de inserir. von Nitzsch & Weber (1993) é ORSA Journal on Computing ou Management Science — confirmar.

### F. Q3 e κ=50

**Q3:** definida como medida secundária mas não reportada no texto principal. Se o artigo admite que falha em dominância fraca, ou substitui por indicador ε aditivo (Zitzler et al. 2003, simples de calcular), ou retira a definição e move para o suplementar.

**κ=50:** mencionado no desenho experimental mas os resultados não aparecem nas tabelas principais. Acrescentar uma linha de robustez ("results for κ=50 are qualitatively consistent; see Table S1") ou retirar κ=50 do texto se não for reportado.

### Bloco 4 — Pacote de reprodução público

Sem alterações de fundo, mas incluir o pipeline completo dos dados brutos à enumeração da fronteira, não só o E1. Confirmar a licença dos dados GIS do estudo original (Andrade & Barbosa, 2015) antes de publicar.

---

## Semanas 3-5 — Generalização empírica

### E6: verificação da validade do experimento

Antes de usar os resultados do E6, confirmar que `compute_objectives` usa uma normalização fixa (min-max sobre os 389 sítios) e não a normalização com Aj da instância. Se ambos usam o mesmo Aj, a assembly óptima é eficiente por construção (Theorem 1 trivial) e o E6 só caracteriza o greedy.

Se o E6 estiver correcto (score com Aj, objectivos fixos), os resultados são válidos para a generalização da decomposição between/within. Se não estiver, corrigir o script e re-correr antes de usar.

### Bloco 3 — Instâncias externas com previsões pré-especificadas

**Candidatos verificáveis na literatura:**

- Siddiqui et al. (1996): caso dos EUA, confirmar se a matriz de decisão está publicada.
- Yal & Akgün (2014): confirmar dados disponíveis.
- Fathalizadeh et al. (2020): confirmação pendente.

**Alternativa mais controlada:** construir uma segunda instância real com dados abertos para outra ilha de Cabo Verde (Santiago ou Santo Antão) usando OSM, SRTM e WDPA, com o mesmo protocolo de Fogo. Permite pré-especificar as previsões antes de correr, o que uma instância extraída da literatura raramente permite.

**Pré-especificação obrigatória:** antes de correr qualquer instância externa, commitar um PRESPEC_external.md com: (a) a instância, (b) a previsão para a ordenação das normalizações por Q2, (c) a asserção de regressão SAW/mm/optimal=100%. Uma instância sem previsões pré-especificadas não serve de evidência confirmatória.

**O que reportar:** numa tabela de 3-4 linhas (Fogo + instâncias externas): TV, Q2_greedy, Q2_optimal, ordenação das normalizações. O objectivo não é reproduzir 25.4pp — é verificar que o ordenamento é consistente com a amplitude identity.

---

## Semana 6 — Revisão final e submissão

### Critérios de submissão

O artigo está pronto quando todos estes passam:

1. Nenhum DEV-, commit hash, PRESPEC ou "earlier version" no texto principal.
2. C(473,3) corrigido para C(389,3) em todo o texto.
3. Highlights ≤ 85 caracteres cada (verificar com os macros expandidos).
4. Contraste de agregação e TOST reformulados como interacção, não como equivalência.
5. Subsecção F8 consolidada com justificação por MAVT em vez de "objectivos físicos".
6. `xelatex ×4 + bibtex`: 0 erros, 0 citações indefinidas.
7. `verify_macros_permanent.py` passa sem erro.
8. DOI do pacote de reprodução no artigo.
9. Pelo menos 2 instâncias externas com previsões pré-especificadas, ou limitação explícita com justificativa.

### Carta ao editor

Incluir um parágrafo sobre a relação com Azancort Neto et al. (2026, IEEE Access): mesmo conjunto de dados de Fogo, pergunta diferente. Antecipa preocupação de sobreposição antes que o editor a levante.

---

## Sequência completa

```
Semana 1
  A — retirar artefactos de laboratório do texto (1 dia)
  E — corrigir erros factuais: C(473→389), macro "3−1 sites", encoding refs (meio dia)
  G — highlights ≤ 85 caracteres (2 horas)
  Bloco 2 — framing analítico vs empírico, retirar "55 studies" sem protocolo (meio dia)
  Bloco 1 — consolidar F8, corrigir justificação para MAVT (1 dia)

Semana 2
  B — recalcular contrastes sem célula construída, reformular TOST como interacção (1 dia)
  C — calcular TV_W para R-V*, adicionar frase sobre condição necessária não suficiente (meio dia)
  D — inserir von Nitzsch & Weber, Fischer, Keeney & Raiffa (verificar DOIs) (meio dia)
  F — Q3: substituir por indicador ε ou retirar; κ=50: linha de robustez ou retirar (meio dia)
  Bloco 4 — repositório público, Zenodo, licença dos dados (2 dias)

Semanas 3-4
  E6 — verificar que compute_objectives usa normalização fixa; corrigir se necessário
  Bloco 3 — PRESPEC_external.md + commit; correr instâncias externas
  E6 — integrar resultados se válidos

Semana 5
  Bloco 3 — integrar instâncias externas no artigo

Semana 6
  Verificar os 9 critérios de submissão
  Carta ao editor
  Submissão à Omega
```

---

## O que não fazer

Não refazer a fronteira de Pareto com outro modelo de valor para responder à circularidade. A justificação por MAVT é suficiente e mais forte.

Não acrescentar mais simulações sintéticas com o mesmo gerador sem primeiro corrigir o E6.

Não limitar as conclusões ao "caso único" sem tentar as instâncias externas. O movimento defensivo baixa o artigo sem necessidade se houver dados disponíveis.

Não promover o Corolário 1 (TOPSIS) sem demonstração completa. O reviewer tem razão: uma "analogia" de α=2 não é um corolário. Despromover para Remark.
