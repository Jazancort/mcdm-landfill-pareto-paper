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

### 4.1 Cause da perda de 80 pp na célula 473/A'

O E4 isola o efeito. R-W usa as constantes dos **389 sítios** (através de `X_adj_dm × r_j/rbar_g`) com amplitudes que variam dentro dos grupos — e não perde nada. R-V usa as constantes dos **473 sítios** (`Xadj473`) — e perde 80 pp.

**Conclusão:** a perda de 80 pp vem dos **offsets absolutos** `b_j = (min_via - min_473)/range_473`, não da variação das amplitudes `r_j` dentro dos grupos. Quando o score usa `min_473` (que pode ser menor que `min_via`), o ranking de trios muda para portfólios que incluem sítios cujos valores ficam abaixo do mínimo admissível — portfólios que a fronteira A' não reconhece como óptimos.

### 4.2 Implicação para o enquadramento teórico

O Teorema thm:groupconst aplica-se à situação **R-B vs R-M**: se as amplitudes forem constantes dentro dos grupos, a montagem exacta é Pareto-eficiente. Isso está confirmado (P_E4_1).

Mas a perda de 80 pp na célula publicada 473/A' (R-V) não é um caso do teorema porque:
1. O score-473 não é afim do score-389 com amplitudes `r_j` **quando os mínimos diferem** (`min_473 ≠ min_via`). A relação é `n^{473}(a) = b_j + r_j * n^{389}(a)` apenas se `b_j = 0` (o que é aproximadamente verdade, mas não exactamente — especialmente para `aspect`).
2. A variação dentro dos grupos (`r_j ≠ rbar_g`) não é o mecanismo que causa a perda. São os offsets `b_j` que mudam o argmax dos trios.

**Formulação correcta para o artigo:** a célula 473/A' perde porque o score optimiza sobre os 473 sítios e depois restringe à fronteira dos 389 — os mínimos são diferentes, por isso o argmax de trio no espaço dos 389 não é o mesmo que no espaço dos 473. Isso é um problema de **conjunto de referência diferente para o avaliador e para o score**, não de re-weighting dentro dos grupos.

### 4.3 A reformulação da sessão (B1/B2) precisa de revisão

Nesta sessão reescrevemos `sec:refset` com a afirmação:
> "Mismatch is therefore a special case of the re-weighting covered by Theorem~\ref{thm:groupconst}: the guarantee fails because r_j varies within objective groups."

O E4 **falsifica** esta afirmação empiricamente (P_E4_3 FAIL). R-W tem r_j variando dentro dos grupos mas chega a 100%. A perda vem dos offsets, não da variação de r_j. O texto do `sec:refset` e do `§8.1` introduzidos na sessão de hoje precisa de ser revertido ou reescrito antes de submeter.

### 4.4 O que está correcto e pode ficar

- **P_E4_1 (teorema):** confirmado. Amplitudes group-constant => 100%. Isto não é afectado pelo E4.
- **Assimetria reversa (R-W' = 86.2%):** a direcção 389→A, com dentro-de-grupo apenas, perde 13.8 pp. A assimetria existe, mas ao contrário do esperado.
- **R-V' = 88.4% vs R-V = 20%:** a assimetria de 80 vs 12 pp (kappa=200) é um resultado empírico robusto, mas a sua explicação não é o TV_W nem o teorema — é a diferença de offsets entre as duas direcções.

### 4.5 Comparação com kappa=50

A kappa=50 (pesos mais dispersos), R-V opt = 46% e R-V' opt = 96.8%. A assimetria persiste (|diff| = 50 pp) e é maior do que a kappa=200 (|diff| = 68 pp → 46 vs 88 para fwd/rev). R-W fwd kappa=50 = 99.4% (quase 100%), confirmando que dentro-de-grupo não causa perda robusta.

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
1. **Reverter `sec:refset` e `§8.1`** para uma formulação que não afirme que mismatch é re-weighting dentro dos grupos (empiricamente falsificado).
2. **Reformular a explicação da assimetria:** os offsets `b_j` como causa da perda, não `r_j`. Verificar analiticamente se isso é consistente com a TV ≈ 0.107.
3. **Calcular TV dos offsets:** `TV_b = sum_j w_j * |b_j * range_all/range_via - 1|` ou equivalente.

### Médio prazo
4. **Segunda instância (Marco B4):** correr E4 numa segunda ilha para verificar se o resultado generaliza.
5. **Script de análise do E4:** expandir `analyze_e4.py` com bootstrap emparelhado, intervalos de confiança, e comparação com tab:fourthcell.
6. **Tabela no artigo:** tab:e4 com as 8 células (kappa=200), análise das previsões.

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
