# DEV-SANT-K5-001 — K5 definição errada no script de avaliação
Date: 2026-11-03 (registado depois do código, como declarado abaixo)
Type: implementation error in evaluation script — incorrect metric labelled as K5
Affects: evaluate_santiago_predictions.py S4/K5 output; JSON field K5_per_kappa
Correction: commit after aa9c87c

## Nota de registo pós-código

Este DEV foi escrito depois da correcção. A causa: a K5 foi tratada como descritiva, o
código usava a métrica errada mas não afectava nenhum veredicto, e a detecção aconteceu
na revisão da avaliação (antes da corrida). A regra "DEV antes do código" não foi
seguida. Exceção aceite: a correcção não altera dados selados, não altera predicções, e
o código corrigido é mais simples do que o anterior.

---

## Definição antiga (incorrecta, commits até aa9c87c)

`analyze_k5_greedy(branch_key)` calculava, por κ e por célula, a **fracção de sorteios
em que o greedy seleccionou o mesmo trio que o óptimo**:

```
agree_per_cell[cell] / N_DRAWS   (same-trio fraction)
```

Esta métrica não está em nenhum ponto da PRESPEC. Estava a calcular o "efeito de
montagem" no sentido de "o greedy chega ao mesmo resultado?", mas a PRESPEC define K5
como uma comparação de Q2, não de trios.

## Definição correcta (PRESPEC_SANTIAGO_A5.md linhas 90–100)

K5 tem duas partes:

**K5(a) — vector-assembly effect:**

```
K5(a)_κ = Q2(SAW, vec, opt)_κ − Q2(SAW, vec, grd)_κ   [pp]
```

Verifica se o sinal de K5(a) em κ=1000 é igual ao sinal em κ=∞.
Fogo E7: K5(a)≈−12 pp (negativo = greedy > optimal em Q2_vec).

**K5(b) — pooled SAW–TOPSIS aggregation contrast:**

```
K5(b)_κ = _agg_pooled3(κ) = mean(SAW3) − mean(TOPSIS3)   [pp]
```

Idêntico ao K6 mas na função de verificação de sinal (κ=1000 vs κ=∞).
Fogo E7: K5(b)≈−6 pp.

Ambos são **puramente descritivos**: nenhum CI, nenhum critério de confirmação.

## Origem do "+96,8"

O valor "+96,8 pp" que aparece no DEV-SANT-GPU-001 e no resumo de sessão é o **K5(a)
para S-N em κ=1000**, calculado pelo `run_santiago_mc.py` durante o Stage 4:

```
K5(a)_SN_k1000 = Q2(SAW,vec,opt) − Q2(SAW,vec,grd)
               = 100.00% − 3.20%
               = +96.80 pp
```

Confirmado do CSV selado `mc_SN_raw.csv` (SHA 357904c0…):

| κ | Q2_vec_opt | Q2_vec_grd | K5(a) |
|--|--|--|--|
| 25 | 99.80% | 85.60% | +14.20 pp |
| 50 | 99.60% | 73.40% | +26.20 pp |
| 100 | 99.60% | 51.00% | +48.60 pp |
| 200 | 98.60% | 34.20% | +64.40 pp |
| 400 | 99.80% | 14.80% | +85.00 pp |
| 1000 | 100.00% | 3.20% | +96.80 pp |
| ∞ | 100.00% | 0.00% | +100.00 pp |

O **script de avaliação** (evaluate_santiago_predictions.py) estava a calcular K5
como fracção de trios iguais (wrong metric). O **MC run** (run_santiago_mc.py) nunca
calculou K5 directamente; os valores acima vêm do CSV selado por simples diferença de
médias.

## S-T: valores K5(a) e o caso zero

S-T K5(a) a partir do CSV selado `mc_ST_raw.csv`:

| κ | Q2_vec_opt | Q2_vec_grd | K5(a) |
|--|--|--|--|
| 25 | 85.00% | 84.80% | +0.20 pp |
| 50 | 83.40% | 82.80% | +0.60 pp |
| 100 | 77.00% | 77.00% | +0.00 pp |
| 200 | 84.20% | 84.20% | +0.00 pp |
| 400 | 87.20% | 87.20% | +0.00 pp |
| 1000 | 94.40% | 94.40% | +0.00 pp |
| ∞ | 100.00% | 100.00% | +0.00 pp |

Para S-T: K5(a) = 0 em κ≥100, incluindo κ=1000 e κ=∞.

**Regra de sinal com zero — A5 não especifica:**
A PRESPEC A5 diz "checks whether these signs replicate" mas não define o que fazer
quando K5(a) = 0. Não há critério de empate documentado.

**Comportamento do código:**
O código usa `_sign(x)` que retorna 0 para x=0. O campo
`K5a_same_sign_1000_inf` = `None` quando `sign(K5a_inf)=0`.
JSON output: `"K5a_same_sign_1000_inf": null`.
Texto: "efeito nulo (K5a = 0 em κ=1000 e κ=∞)".

## K5(b): herança da correcção do DEV-SANT-K6-001

K5(b) usa a mesma fórmula de 3 células do K6 (DEV-SANT-K6-001: mm_opt excluído por
Proposição 1). O código usa `_agg_pooled3(grp)` já corrigido. Para κ=∞, usa os macros
de `macros_kappa_inf.tex` (SHA 9c086c02).

## Impacto

Nenhum veredicto (S0–S7b) depende do K5. K5 é puramente descritivo.
O campo `K5_per_kappa` no JSON de saída era incorrecto (fracção de trios iguais).
Após a correcção é `K5a_assembly_per_kappa` (Q2 difference em pp).

O campo antigo `K5_per_kappa` **não aparece em nenhum ficheiro selado** (a avaliação
completa ainda não correu). Não há propagação de erro para resultados existentes.
