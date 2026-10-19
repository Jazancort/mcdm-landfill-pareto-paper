# Plano de melhorias — Artigo MCDM Fogo/Omega
**Versão:** 1.0 — 2026-10-01
**Objetivo:** levar o artigo da versão actual (~8.0) a uma submissão defensável à Omega (~8.5), sem recomeçar do zero e sem desperdiçar trabalho já feito.

---

## Contexto

O artigo tem uma base teórica sólida: a identidade de amplitude e os dois teoremas (Proposição 1 e Proposição groupconst) são resultados analíticos gerais que não dependem de Fogo. O que está incompleto é a separação entre o que o artigo *prova* e o que o artigo *observa*, e a ausência de evidência empírica em mais de uma instância real.

Um revisor da Omega vai fazer duas perguntas difíceis:

1. A fronteira de Pareto usa min-max: isso não favorece sistematicamente min-max na avaliação?
2. Os efeitos que vocês reportam são específicos de Fogo ou aparecem noutros contextos?

O plano responde às duas antes da submissão.

---

## Estado actual dos experimentos

| Experimento | Estado | O que produziu |
|---|---|---|
| E1 — intervenção em amplitudes | Completo, pré-registado | Decomposição between/within: B=100%, W=64.2%, V=56.8% |
| E4 — ref-set com coding consistente | Completo | R-V*=100%, R-asp=24%; 80pp era artefacto de coding |
| F8 — circularidade do benchmark | Script feito, fora do texto | Vec-opt=100%, MM-opt=94.4% com fronteira vector |
| E6 — 45 instâncias × 5 condições | A correr na Athena | Aguardando resultados |
| Instâncias externas reais | Não iniciado | — |

O pipeline está correcto (pareto_utils.py, float64, eps=1e-9), o pré-registo existe e o histórico git está documentado. O que falta está no texto e na evidência externa.

---

## Bloco 1 — Circularidade do benchmark
**Prioridade:** 1 | **Esforço:** 1 dia | **Experimento necessário:** nenhum (F8 já existe)

### O problema

A fronteira de Pareto é construída com objectivos min-max e pesos AHP. Quando SAW/min-max/optimal atinge 100%, parte disso é Proposição 1 (analítico) e parte é que o benchmark usa os mesmos objectivos. Se a fronteira fosse construída com objectivos vector, SAW/vector/optimal subiria para 100% e SAW/min-max/optimal desceria para 94.4%.

Um revisor vai levantar isto. O F8 já calculou exatamente essa sensibilidade.

### O que fazer

Escrever uma subsecção "Benchmark circularity and robustness" (~150 palavras) na Discussão com três pontos:

Primeiro: a fronteira usa min-max porque os objectivos físicos (custo de implantação, impacto ambiental, segurança social) existem em unidades substantivas antes de qualquer normalização. Não é uma escolha metodológica arbitrária.

Segundo: a robustez foi verificada reconstruindo a fronteira com objectivos vector. Os quatro valores de F8:

| Fronteira usada | SAW/mm/opt | SAW/mm/grd | SAW/vec/opt | SAW/vec/grd |
|---|:---:|:---:|:---:|:---:|
| Min-max (principal) | 100.0% | 86.0% | 56.8% | 66.2% |
| Vector (sensibilidade) | 94.4% | 72.4% | 100.0% | 100.0% |

Terceiro: o ordenamento das normalizações se inverte no sentido previsto pela Proposição 1, confirmando que o resultado é estrutural e não artefacto do benchmark.

### Resultado esperado

Uma subsecção de discussão que transforma a limitação mais óbvia numa verificação de robustez. O revisor que levantar a questão encontra a resposta no texto.

---

## Bloco 2 — Framing analítico vs empírico
**Prioridade:** 2 | **Esforço:** meio dia | **Experimento necessário:** nenhum

### O problema

O abstract, a introdução e a conclusão misturam afirmações que valem para qualquer instância com afirmações que valem apenas para Fogo. Isso dá a um revisor argumentos fáceis para pedir mais instâncias antes de considerar a publicação.

### Separação correcta

**Afirmações analíticas** (valem dentro do escopo definido, independente de Fogo):
- A identidade $w_j^{\text{eff}} \propto w_j A_j$ é exacta para SAW.
- Proposição 1: SAW/min-max/optimal atinge 100% para qualquer conjunto de candidatos.
- Proposição groupconst: amplitudes constantes dentro do grupo garantem a fronteira.
- A equivalência PROMETHEE-Borda é exacta para a função de preferência usual.

**Afirmações empíricas** (específicas de Fogo, generalizáveis com evidência adicional):
- O ganho de normalização é +25.4pp em greedy.
- A decomposição between/within dá 35.8pp vs 43.2pp.
- O efeito de assembly é −10.2pp sob vector.
- Vector normalisation multiplica o peso de perm por 2.88.

### O que fazer

Auditar abstract, §1 e §8 linha a linha. Em cada afirmação empírica, adicionar "on this instance" ou "in our data". Nas afirmações analíticas, remover qualificadores desnecessários como "we find" ou "our results show".

O resultado é um artigo que não promete mais do que pode entregar. O teorema vale sempre; a magnitude de 25.4pp vale para Fogo.

---

## Bloco 3 — Generalização empírica
**Prioridade:** 3 | **Esforço:** 1-2 semanas | **Experimento necessário:** sim

### O problema

Um único conjunto de dados reais não estabelece a generalização dos efeitos empíricos. O E6 com 45 instâncias sintéticas cobre a variação paramétrica, mas não substitui instâncias reais com distribuições de critérios independentes.

### O que o E6 já cobre

Quando terminar, o E6 vai mostrar que: (a) a Proposição 1 vale em todas as 45 instâncias, (b) a decomposição between/within se mantém quando as amplitudes variam sistematicamente. Isso é evidência forte para os teoremas.

### O que o E6 não cobre

A magnitude dos efeitos em instâncias com geometria espacial diferente, frequência de empates diferente e distribuição de critérios diferente.

### O que fazer

Identificar 2 instâncias publicadas na literatura de siting com coordenadas, critérios e pesos disponíveis. Candidatos com mais probabilidade de ter dados reprodutíveis:

- Fathalizadeh et al. (2020): siting em contexto iraniano, publicado em Waste Management.
- Yal & Akgün (2014): siting na Turquia, publicado em Waste Management.
- Siddiqui et al. (1996): caso clássico dos EUA com múltiplos critérios.

Para cada instância confirmada: correr o pipeline existente (pareto_utils.py sem modificações), calcular TV, Q2_greedy, Q2_optimal e verificar a asserção de regressão SAW/mm/optimal=100%.

Reportar numa tabela de 3-4 linhas (Fogo + instâncias externas) com TV e Q2. O objectivo não é reproduzir os 25.4pp, mas verificar que o ordenamento das normalizações é consistente com a amplitude identity.

Se nenhuma das 3 instâncias tiver dados suficientes, limitar explicitamente as conclusões empíricas a Fogo e reportar o E6 como evidência de robustez paramétrica.

---

## Bloco 4 — Pacote de reprodução público
**Prioridade:** 4 | **Esforço:** 2-3 dias | **Experimento necessário:** nenhum

### O que falta

O código existe e está testado. Falta um repositório público com DOI permanente que permita a um revisor verificar os resultados centrais a partir de um clone limpo.

### O que fazer

Criar o repositório `mcdm-landfill-pareto-replication` no GitHub com:

- `scripts/run_e1_v3.py`: reproduz E1 (experimento central pré-registado).
- `scripts/generate_macros.py`: reproduz as macros do artigo a partir dos CSV.
- `scripts/verify_macros_permanent.py`: verifica o hash esperado dos resultados.
- `corpus/PRESPEC_E1.md`: pré-especificação com timestamp de commit.
- `README.md`: três passos — clone, `uv run python scripts/run_e1_v3.py`, verificar hash.

Tag v1.0 + Zenodo para DOI permanente. Adicionar no artigo: "Code and data available at `doi.org/10.5281/zenodo.XXXXXXX`".

---

## Sequência de execução

```
Semana 1
  Bloco 2 (framing) — meio dia
  Bloco 1 (F8, escrever subsecção) — 1 dia

Semana 2
  Bloco 4 (repositório público, Zenodo) — 2-3 dias

Semanas 3-4
  Bloco 3 — identificar instâncias externas
  Bloco 3 — implementar run_external_instances.py e correr
  E6 — aguardar resultados e verificar

Semana 5
  Bloco 3 — integrar resultados no artigo
  E6 — integrar na secção de resultados

Semana 6
  Revisão final: make check, verify_macros_permanent, contagem de palavras
  Submissão à Omega via Editorial Manager
```

---

## O que não fazer

Não reconstruir a fronteira de Pareto com outro modelo de valor só para responder à questão de circularidade. O F8 já responde, e uma fronteira alternativa sem justificativa substantiva cria mais problemas do que resolve.

Não acrescentar mais simulações sintéticas com o mesmo gerador do E6. O que falta é variação real na geometria e na distribuição dos critérios, que instâncias reais fornecem de forma mais convincente.

Não limitar as conclusões ao "caso único" antes de tentar o Bloco 3. Esse movimento defensivo baixa o artigo sem necessidade, se houver 2 instâncias externas disponíveis na literatura.

Não expandir os teoremas para TOPSIS ou VIKOR sem demonstração. O escopo aditivo está correcto e bem delimitado.

---

## Critério de submissão

O artigo está pronto para submissão quando:

1. Nenhuma afirmação empírica no abstract ou na conclusão estiver sem o qualificador "on this instance" ou equivalente.
2. A subsecção F8 existir na Discussão com os 4 valores verificados.
3. O DOI do pacote de reprodução estiver no artigo.
4. `verify_macros_permanent.py` passar sem erro.
5. `xelatex ×4 + bibtex`: 0 erros, 0 citações indefinidas.
6. Pelo menos 2 instâncias externas reais reportadas, ou uma limitação explícita com justificativa caso os dados não estejam disponíveis.
