# DEV-SANT-K5-001 — K5 definição errada no script de avaliação
Date: 2026-11-03 (registado depois do código, como declarado abaixo)
Type: implementation error in evaluation script — incorrect metric labelled as K5
Affects: evaluate_santiago_predictions.py S4 K5 output; JSON field K5_per_kappa
Correction: commit after b8db186

## Nota de registo pós-código

Este DEV foi escrito depois da correcção. A causa: a K5 foi tratada como
puramente descritiva (sem critério de confirmação, como diz a A5), o código
usava a métrica errada, e a detecção aconteceu na revisão antes da corrida.
A regra "DEV antes do código" não foi seguida. Exceção aceite: a correcção
não altera dados selados nem predicções testáveis; o código corrigido é
consistente com a definição pré-registada.

---

## Definição correcta: citação da A5 palavra por palavra

**Ficheiro:** `corpus/prespec/PRESPEC_SANTIAGO_A5.md`

```
PRESPEC_SANTIAGO_A5.md:91: **K5 — Descriptive check of the high-κ reading (descriptive)**
PRESPEC_SANTIAGO_A5.md:92: At κ = 1000 and κ = ∞ report:
PRESPEC_SANTIAGO_A5.md:93: (a) whether the vector-assembly effect (Q2(SAW, vec, opt) − Q2(SAW, vec, grd)) has the
PRESPEC_SANTIAGO_A5.md:94:     same sign in both cases;
PRESPEC_SANTIAGO_A5.md:95: (b) whether the pooled SAW–TOPSIS aggregation contrast (informative cells) has the same
PRESPEC_SANTIAGO_A5.md:96:     sign in both cases.
PRESPEC_SANTIAGO_A5.md:99: whether these signs replicate in Santiago without predicting the magnitudes.
PRESPEC_SANTIAGO_A5.md:100: K5 is purely descriptive; no CI test, no confirmation criterion.
PRESPEC_SANTIAGO_A5.md:115: K5 and K6 are descriptive (no adjustment).
PRESPEC_SANTIAGO_A5.md:138: The conditional sign in K5 (sign(assembly effect at κ = 1000) vs sign at κ = ∞)
PRESPEC_SANTIAGO_A5.md:138: is resolved here from the descriptors, not from MC results.
```

K5 tem veredicto descritivo: o script de avaliação deve reportar "mesmo sinal" ou
"sinal diferente" para K5(a) e K5(b) separadamente. "No CI test, no confirmation
criterion" significa que não há teste formal, não que não há output. A A5 define
explicitamente o que reportar: o resultado do sign check.

## Definição antiga (incorrecta, commits até b8db186)

`analyze_k5_greedy(branch_key)` calculava, por κ e por célula, a **fracção de sorteios
em que o greedy seleccionou o mesmo trio que o óptimo** (same-trio fraction). Esta
métrica não está em nenhum ponto da PRESPEC e não coincide com K5(a) nem K5(b).

## Definição correcta (implementada)

**K5(a):**
```
K5(a)_κ = Q2(SAW, vec, opt)_κ − Q2(SAW, vec, grd)_κ   [pp]
```

**K5(b):**
```
K5(b)_κ = _agg_pooled3(κ) = mean(SAW3) − mean(TOPSIS3)   [pp]
```
Idêntico ao K6 mas usado na função de verificação de sinal entre κ=1000 e κ=∞.

## Origem do "+96,8"

O valor "+96,8 pp" é o **K5(a) para S-N em κ=1000**, calculado do CSV selado
`mc_SN_raw.csv` (SHA 357904c0…):

```
K5(a)_SN_k1000 = Q2(SAW,vec,opt) − Q2(SAW,vec,grd)
               = 100.00% − 3.20%
               = +96.80 pp
```

O run_santiago_mc.py nunca calculou K5 directamente; os valores vêm do CSV selado
por simples diferença de médias. O script de avaliação estava a calcular uma métrica
diferente (fracção de trios iguais).

## Tabela K5(a) dos CSVs selados

| κ | S-T K5(a) | S-N K5(a) |
|--|--|--|
| 25 | +0.20 pp | +14.20 pp |
| 50 | +0.60 pp | +26.20 pp |
| 100 | +0.00 pp | +48.60 pp |
| 200 | +0.00 pp | +64.40 pp |
| 400 | +0.00 pp | +85.00 pp |
| 1000 | +0.00 pp | +96.80 pp |
| ∞ | +0.00 pp | +100.00 pp |

## Regra de zeros (decidida depois dos dados) — [POST-DATA]

A A5 não especifica o que reportar quando K5 = 0. A linha 100 diz "no confirmation
criterion" mas não define o comportamento para empates.

Os valores do S-T estavam no log selado (Stage 4 MC) quando esta regra foi escolhida.
Isto é uma decisão pós-dados.

**Regra adoptada (declarada aqui):**

O código devolve `None` (= "indeterminado") se **qualquer um** dos dois lados for 0
(não só o κ=∞). Fórmula no código:

```python
k5a_same_sign = (
    (k5a_sign_1000 == k5a_sign_inf)
    if (k5a_sign_1000 != 0 and k5a_sign_inf != 0)
    else None
)
```

**Duas leituras reportadas:**

| Leitura | S-T K5(a) | S-N K5(a) | S-T K5(b) | S-N K5(b) |
|--|--|--|--|--|
| Principal (indeterminado = nulo) | `null` (0 dos dois lados) | TRUE (+96,8 e +100) | `null` (K6[1000]=+24,1; K6[inf]=0) | TRUE (ambos negativos) |
| Conservadora (zero ≠ mesmo sinal) | "não confirmado" | "confirmado" | "não confirmado" | "confirmado" |

A leitura principal usa `None` sempre que qualquer lado for 0. A leitura conservadora
trata zero como sinal oposto (não confirmado).

## K5(b): herança da correcção DEV-SANT-K6-001

K5(b) usa a mesma fórmula de 3 células do K6 (DEV-SANT-K6-001: mm_opt excluído por
Proposição 1). O código usa `_agg_pooled3(grp)` já corrigido.

## Sobre a linha 138 da A5

"The conditional sign in K5...is resolved here from the descriptors, not from MC results."

Esta linha refere-se ao Stage 3. O K5(a) final usa Q2 do CSV selado (Stage 4 MC),
não dos descritores do Stage 3. Isto é uma divergência em relação à A5 linha 138.
A divergência é aceitável: os descritores de Stage 3 (TV, m_eff) não permitem
calcular Q2(SAW,vec,opt) nem Q2(SAW,vec,grd); só o MC fornece esses valores.

## Impacto

Nenhum veredicto (S0–S7b) depende do K5. K5 é puramente descritivo (sem ajuste
por multiplidade, sem critério de confirmação).
