# E4 — Resultados e Análise
**Data da corrida:** 2026-10-01, 20:25–21:50 UTC-3  
**Commit do script final:** `efdc9d8` (run_e4.py v6)  
**Commit dos dados:** `7603722` (e4_results.csv)  
**PRESPEC:** commits `4716ab8`, `ece6544`, `bee5d24`, `e95caba`, `9eb4322` (todos antes de qualquer corrida)

---

## 1. Desenho

O E4 testa se o mecanismo 2 (referência-set mismatch) se reduz a re-weighting dentro dos grupos no sentido do Teorema~thm:groupconst. Para isso, decompõe o score-473 em quatro células que isolam diferentes fontes de distorção.

**Instância:** Fogo, m=473 candidatos, m'=389 admissíveis, k=3, separação 10 km.  
**Estimand primário:** Q2[A'], kappa=200, N=500 draws (matriz de pesos e1_weights_k200.npy, SHA-256 `bea05275...`).  
**Avaliador:** fronteira A' (1 944 653 trios sobre 389 sítios admissíveis).

| Célula | Amplitudes A_j | Base do score | Interpretação |
|--------|---------------|--------------|---------------|
| R-M    | 1             | X_adj_dm     | Controlo alinhado (= SAW/minmax sobre 389) |
| R-B    | rbar_g        | X_adj_dm × rbar_g | Group-constant: Teorema prevê 100% |
| R-W    | r_j/rbar_g    | X_adj_dm × r_j/rbar_g | Dentro-de-grupo apenas |
| R-V    | r_j (exact)   | Xadj473      | Score-473 publicado; regressão tab:fourthcell |
| R-M'   | 1             | X_adj_dm     | Controlo alinhado (direcção 389→A) |
| R-B'   | 1/rbar_g      | X_adj_dm / rbar_g | Group-constant inverso |
| R-W'   | rbar_g/r_j    | X_adj_dm × rbar_g/r_j | Dentro-de-grupo direcção inversa |
| R-V'   | 1/r_j         | X_adj_dm / r_j | Score-389 publicado; regressão tab:fourthcell |

**Nota técnica:** `X_adj_dm` é a matriz de decisão de `_build_decision_matrix(df_via)`, que usa tratamento binário para `aspect`. `Xadj473` é `(x_via - min_all)/range_all` — o mesmo que `build_score_473` no mc_2cube_fixed.py. As duas diferem para a coluna `aspect` (binária vs contínua), o que torna as células R-B e R-W não directamente comparáveis à R-V como interpolação afim. R-V é a célula de regressão; R-B, R-W, R-M são definidas em relação ao SAW/minmax (R-M).

---

## 2. Resultados completos

### kappa = 200 (estimand primário)

| Célula | Direcção | greedy Q2 | SE | **optimal Q2** | SE |
|--------|----------|-----------|----|----------------|----|
| R-M    | 473→A'   | 86.0%     | 1.55 | **100.0%** | 0.00 |
| R-B    | 473→A'   | 88.4%     | 1.43 | **100.0%** | 0.00 |
| R-W    | 473→A'   | 96.8%     | 0.79 | **100.0%** | 0.00 |
| R-V    | 473→A'   | 19.6%     | 1.78 | **20.0%**  | 1.79 |
| R-M'   | 389→A    | 86.0%     | 1.55 | **100.0%** | 0.00 |
| R-B'   | 389→A    | 87.2%     | 1.49 | **100.0%** | 0.00 |
| R-W'   | 389→A    | 75.6%     | 1.92 | **86.2%**  | 1.54 |
| R-V'   | 389→A    | 70.4%     | 2.04 | **88.4%**  | 1.43 |

### kappa = 50 (secundário)

| Célula | greedy Q2 | **optimal Q2** | SE |
|--------|-----------|----------------|----|
| R-M    | 96.0%     | **100.0%** | 0.00 |
| R-B    | 95.2%     | **100.0%** | 0.00 |
| R-W    | 96.4%     | **99.4%**  | 0.35 |
| R-V    | 46.0%     | **46.0%**  | 2.23 |
| R-M'   | 96.0%     | **100.0%** | 0.00 |
| R-B'   | 96.0%     | **100.0%** | 0.00 |
| R-W'   | 89.2%     | **95.6%**  | 0.92 |
| R-V'   | 87.8%     | **96.8%**  | 0.79 |

---

## 3. Avaliação das previsões (kappa=200, optimal assembly)

### P_E4_1 (asserção de regressão): R-B = 100% e R-B' = 100% em todos os draws
**PASS.** R-B opt = 100.0% (SE = 0.00), R-B' opt = 100.0% (SE = 0.00).  
O Teorema thm:groupconst confirma-se: com amplitudes constantes dentro de cada grupo, a montagem exacta é Pareto-eficiente em todos os 500 draws.  
**Nota:** isto é uma asserção de regressão, não evidência. O mesmo resultado é esperado por construção (rem:definitional).

### P_E4_2 (controlo de regressão): R-V reproduz tab:fourthcell dentro de 3 SE
**PASS.** R-V opt = 20.0%, ref = 20.0%, |diff| = 0.0 pp, 3 SE = 5.37 pp.  
Pipeline correcto. A célula R-V é idêntica à célula 473/A' da tab:fourthcell.

### P_E4_3 (evidência primária): R-W loss ≥ 50% de R-V loss
**FAIL.** R-W opt = 100.0%, loss_RW = 0.0 pp, loss_RV = 80.0 pp. Rácio = 0.00.  
Dentro-de-grupo sozinho (R-W = X_adj_dm × r_j/rbar_g) não causa qualquer perda.

### P_E4_4 (exploratória): assimetria fwd > rev em R-W
**FAIL (na direcção esperada).** R-W fwd = 100% (perda 0 pp), R-W' rev = 86.2% (perda 13.8 pp).  
A assimetria existe mas é **inversa**: é a direcção reversa (389→A) que perde, não a directa.

### P_E4_5 (exploratória): R-W fwd loss > E1-W loss (35.8 pp)
**FAIL.** R-W fwd = 100.0%. Não há perda para comparar.

---

## 4. Diagnóstico: o que o E4 descobriu

### 4.1 Cause da perda de 80 pp na célula 473/A' — diagnóstico inicial ERRADO

O relatório original (§4.1) atribuiu a perda aos offsets absolutos `b_j = (min_via - min_473)/range_473`. Esta explicação está **matematicamente errada**.

Para um portfolio de tamanho fixo k, o score SAW com offsets é:

```
score(T; w, b, A) = k · Σ_j w_j·b_j  +  Σ_{a∈T} Σ_j w_j·A_j·c̃_j(a)
```

O primeiro termo é a mesma constante para **todos** os portfolios T de tamanho k. Logo argmax(score) = argmax(score sem offset). O mesmo argumento aplica-se ao greedy: cada sítio recebe o mesmo incremento `Σ_j w_j·b_j`, que não muda a ordenação.

**Os offsets b_j não mudam nenhuma escolha, em nenhuma montagem.**

O §4.2 do relatório original ("portfólios que incluem sítios abaixo do mínimo admissível") também era falso: o A3 confirmou que todos os trios são indexados sobre os 389 sítios admissíveis.

### 4.2 Causa provável: codificação inconsistente de `aspect`

`Xadj473` (usado em R-V) trata `aspect` como contínuo: normaliza os azimutes em graus por min-max. O avaliador (via `compute_objs_f64` → `_build_decision_matrix`) trata `aspect` como binário: `c = 1` se azimute ∈ [90°, 180°] (sotavento), `c = 0` caso contrário. Estas são transformações não monotonamente relacionadas: um azimute de 350° tem valor alto no score (próximo de max/range_all) mas vale 0 no avaliador.

A evidência directa veio da v4 do pipeline: com `Xadj389` (constantes de 389, aspect contínuo), R-M = **24%** em vez de 100%. Sem alterar o conjunto de referência — apenas mudando a codificação de `aspect` — a perda é de ~76 pp, praticamente os 80 pp da célula publicada.

**Hipótese:** a perda de 80 pp na célula 473/A' é explicada pela codificação inconsistente de `aspect` entre o score e o avaliador, não pelo conjunto de referência. O E4 não testou esta hipótese porque a célula R-V usa `Xadj473` (aspect contínuo) enquanto todas as outras células usam `X_adj_dm` (aspect binário).

### 4.3 Células exploratórias necessárias (post hoc, declaradas no DEV-E4-007)

Para separar os dois efeitos:

| Célula | Score | Predição se hipótese correcta |
|--------|-------|-------------------------------|
| R-V* | `X_adj_dm × r_j` (aspect binário, constantes 473) | ≈ 100% — sem perda de codificação |
| R-asp | `X_adj_dm` com coluna aspect trocada pela contínua, constantes 389 | ≈ 24% — codificação sozinha |

Se R-V* ≈ 100%: os 80 pp são todos de codificação. O "Mechanism 2" desaparece como efeito de referência.  
Se R-V* << 100%: o conjunto de referência tem efeito próprio adicional à codificação.

### 4.4 A direcção inversa não é a que foi declarada no PRESPEC

Verificado: R-M e R-M' têm médias idênticas draw-a-draw (86.0%/100.0%, kappa=200 e 96.0%/100.0%, kappa=50). Isto confirma que **ambas as direcções usam o avaliador A'** (fronteira sobre 389 sítios). O DEV-E4-002 declarou que a direcção 389→A usaria a fronteira A (213 portfolios, objectivos sobre 473 sítios) — mas o pipeline não implementou isso. As células com plica são uma segunda cópia da direcção directa com amplitudes invertidas, não o espelho contra a fronteira A.

Consequências:
- R-V' = 88.4% ≠ 95.0% (tab:fourthcell row 3): **FAIL** (|diff|=6.6 > 3 SE=4.3).
- P_E4_4 e a "assimetria inversa" referem-se a um desenho diferente do pré-registado.
- R-W' = 86.2% não é evidência sobre a assimetria publicada de 80 vs 5 pp.

### 4.5 Assimetria por kappa (corrigida)

| kappa | R-V fwd loss | R-V' rev loss | Assimetria (rev−fwd) |
|-------|-------------|---------------|----------------------|
| 200   | 80.0 pp     | 11.6 pp       | −68.4 pp             |
| 50    | 54.0 pp     | 3.2 pp        | −50.8 pp             |

A assimetria é **menor** com kappa=50 (50.8 pp) do que com kappa=200 (68.4 pp). O relatório original tinha este sinal invertido — corrigido aqui.

---

## 5. Historial de bugs no pipeline

| Versão | Bug | Sintoma | Correcção |
|--------|-----|---------|-----------|
| v1 (commit `ca50ce2`) | Score fwd usava `X_adj` (389-base), escalado por `A_j` | Todos fwd = 100% incluindo R-V | Usar `Xadj473` para R-V |
| v2/v3 (`d1bb682`) | Construção `b_j + A_j * X_adj` usava `_build_decision_matrix` para aspect (binário vs contínuo) | Diferença máxima 1.0 na coluna aspect | Identificado mas não corrigido aqui |
| v4 (`73cd65f`) | Usava `Xadj389` raw em vez de `X_adj_dm`; R-M = 24% (não 100%) | R-M ≠ SAW/minmax | Usar `X_adj_dm` para base |
| v5 (`f4d94d0`) | `Xadj473 + (A_j-r_j)*X_adj_dm`: R-M = 24% persistiu | A interpolação não funciona quando aspect difere | Abandonada |
| v6 (`efdc9d8`) | `X_adj_dm * A_j` para todas excepto R-V = `Xadj473` | R-M = 100%, R-V = 20%: correcto | **Versão final** |

**Nota sobre DEV-E4-006:** o bug e as iterações estão documentados no PRESPEC_E4.md antes da corrida final.

---

## 6. Próximos passos

### Imediato (antes de integrar E4 no artigo)
1. **DEV-E4-007:** declarar R-V* e R-asp como exploratórias post hoc; declarar v1-v5 como corridas com resultados vistos; corrigir P_E4_3 como "não avaliável tal como desenhado" por inconsistência na codificação de `aspect`.
2. **Correr R-V* e R-asp** na Athena (mesma matriz de pesos, kappa ∈ {50, 200}).
3. **Confirmar o pipeline das células com plica:** o code mostra que R-M' = R-M, logo o avaliador é A' em ambas as direcções. O DEV-E4-002 declarou fronteira A — isso nunca foi implementado.
4. **Não reverter sec:refset ainda:** o enquadramento antigo ("same normalisation… voided") também não está provado. Aguardar R-V* antes de reescrever.

### Médio prazo (após R-V* e R-asp)
5. **Se R-V* ≈ 100%:** os 80 pp são de codificação. Reescrever sec:refset, §8.1, resumo, highlights, recomendação prática. Adicionar tab:e4 com codificação como variável.
6. **Se R-V* << 100%:** o conjunto de referência tem efeito próprio. Identificar a causa analiticamente antes de escrever.
7. **Segunda instância (Marco B4).**
8. **Script de análise completo** com bootstrap emparelhado e ICs.

### Interpretação para o artigo (rascunho)
> "Experiment 4 tests whether the 80-pp loss under reference-set mismatch can be attributed to within-group re-weighting. Cells R-B and R-B' confirm the theorem (P_E4_1, both 100%). Cell R-W, which isolates within-group amplitude variation while using 389-site normalisation constants, reaches 100% (P_E4_3 not confirmed). The 80-pp loss is therefore not caused by within-group amplitude variation; it arises from the change in absolute minima between the 389 and 473 candidate sets (offsets b_j), which shifts the argmax of trios independently of group structure. The asymmetry between directions (R-W' = 86.2% vs R-W = 100%) remains unexplained by the theorem and motivates further analysis."

---

## 7. Ficheiros produzidos

| Ficheiro | Commit | Descrição |
|----------|--------|-----------|
| `scripts/run_e4.py` | `efdc9d8` | Script final (v6) |
| `scripts/analyze_e4.py` | `ca50ce2` | Análise das previsões |
| `scripts/check_feasible_e4.py` | `f607d27` | Verificação de factibilidade |
| `scripts/tvw_e4.py` | `d4e970b` | Cálculo de TV_W(R-W) |
| `results/e4_results.csv` | `7603722` | CSV completo das 16 células |
| `results/e1_weights_k200.npy` | `f607d27` | Matriz de pesos (SHA-256 `bea05275`) |
| `corpus/PRESPEC_E4.md` | `9eb4322` | Pré-registo com DEV-E4-001..006 |
