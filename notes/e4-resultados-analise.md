# E4 — Resultados e Análise (versão final, 2026-10-01T22:27)
**Commit do script final:** `efdc9d8` (run_e4.py v6)  
**Commit dos dados:** `7603722` (e4_results.csv)  
**Células exploratórias:** `a81db36` (run_e4_vstar.py), `2270cc4` (e4_vstar_results.csv)  
**PRESPEC:** commits `4716ab8`, `ece6544`, `bee5d24`, `e95caba`, `9eb4322`, `b0e5c66` (DEV-E4-007)

---

## 1. Desenho

O E4 testa se o mecanismo 2 (reference-set mismatch) se reduz a re-weighting dentro dos grupos no sentido do Teorema~thm:groupconst. Para isso, decompõe o score-473 em quatro células que isolam diferentes fontes de distorção.

**Instância:** Fogo, m=473 candidatos, m'=389 admissíveis, k=3, separação 10 km.  
**Estimand primário:** Q2[A'], kappa=200, N=500 draws (matriz de pesos e1_weights_k200.npy, SHA-256 `bea05275...`).  
**Avaliador:** fronteira A' (1 944 653 trios sobre 389 sítios admissíveis) — **binário** em todas as células.

| Célula | Amplitudes A_j | Base do score | Interpretação |
|--------|---------------|--------------|---------------|
| R-M    | 1             | X_adj_dm     | Controlo alinhado (= SAW/minmax sobre 389) |
| R-B    | rbar_g        | X_adj_dm × rbar_g | Group-constant: Teorema prevê 100% |
| R-W    | r_j/rbar_g    | X_adj_dm × r_j/rbar_g | Dentro-de-grupo apenas |
| R-V    | r_j (exact)   | Xadj473 (aspect **contínuo**) | Score-473 confundido — ver §4 |
| R-M'   | 1             | X_adj_dm     | Avaliador A' (não A — ver §4.4) |
| R-B'   | 1/rbar_g      | X_adj_dm / rbar_g | Group-constant inverso |
| R-W'   | rbar_g/r_j    | X_adj_dm × rbar_g/r_j | Dentro-de-grupo direcção inversa |
| R-V'   | 1/r_j         | X_adj_dm / r_j | Amplitudes inversas, avaliador A' |

**Nota técnica:** `X_adj_dm` usa aspect **binário** (c=1 se azimute ∈ [90°,180°], benefit=True). `Xadj473` usa aspect **contínuo** (min-max sobre graus). Todas as células excepto R-V usam aspect binário, idêntico ao avaliador. R-V tem codificação inconsistente — a comparação R-W vs R-V está confundida (ver §4).

---

## 2. Resultados completos

### kappa = 200 (estimand primário)

| Célula | Direcção | greedy Q2 | SE | **optimal Q2** | SE |
|--------|----------|-----------|----|----------------|----|
| R-M    | 473→A'   | 86.0%     | 1.55 | **100.0%** | 0.00 |
| R-B    | 473→A'   | 88.4%     | 1.43 | **100.0%** | 0.00 |
| R-W    | 473→A'   | 96.8%     | 0.79 | **100.0%** | 0.00 |
| R-V    | 473→A'   | 19.6%     | 1.78 | **20.0%**  | 1.79 |
| R-M'   | 389→A'   | 86.0%     | 1.55 | **100.0%** | 0.00 |
| R-B'   | 389→A'   | 87.2%     | 1.49 | **100.0%** | 0.00 |
| R-W'   | 389→A'   | 75.6%     | 1.92 | **86.2%**  | 1.54 |
| R-V'   | 389→A'   | 70.4%     | 2.04 | **88.4%**  | 1.43 |

**Nota:** a direcção das células com plica é 389→A' (avaliador A'), não 389→A como declarado no DEV-E4-002. Ver §4.4.

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
O Teorema thm:groupconst confirma-se: com amplitudes constantes dentro de cada grupo, a montagem exacta é Pareto-eficiente em todos os 500 draws. Asserção de regressão, não evidência nova.

### P_E4_2 (controlo de regressão): R-V reproduz tab:fourthcell dentro de 3 SE
**PASS (direcção directa).** R-V opt = 20.0%, ref = 20.0%, |diff| = 0.0 pp, 3 SE = 5.37 pp. Pipeline correcto para a célula 473/A'.

**FAIL (direcção inversa).** R-V' opt = 88.4%, ref tab:fourthcell 389/A = 95.0%, |diff| = 6.6 pp, 3 SE = 4.3 pp. A célula R-V' usa avaliador A' (não A) — é uma célula diferente da publicada. Ver §4.4.

### P_E4_3 (evidência primária): R-W loss ≥ 50% de R-V loss
**TESTÁVEL MAS NÃO INFORMATIVO tal como desenhado.**

R-W opt = 100.0% (loss = 0 pp), R-V opt = 20.0% (loss = 80 pp). O rácio observado = 0.00.

Porém a comparação R-W vs R-V está confundida: R-V usa Xadj473 com aspect **contínuo**, enquanto R-W usa X_adj_dm com aspect **binário**. A célula pré-registada pressupunha que R-V era afim de R-M; não é, porque aspect não é monotonamente relacionado entre as duas codificações. O P_E4_3 testou uma hipótese sobre o conjunto de referência mas a célula R-V mede maioritariamente um efeito de codificação. A substituição post hoc correcta é R-V*, que produz 100% — tornando o teste R-W vs R-V* trivialmente 0 pp vs 0 pp. O P_E4_3 é não informativo como desenhado.

### P_E4_4 (exploratória): assimetria fwd > rev em R-W
**FAIL (na direcção esperada).** R-W fwd = 100%, R-W' rev = 86.2%. A assimetria existe mas é inversa e refere-se ao avaliador A' em ambas as direcções — não ao contraste A vs A' publicado.

### P_E4_5 (exploratória): R-W fwd loss > E1-W loss (35.8 pp)
**FAIL.** R-W fwd = 100.0%. Não há perda para comparar.

**Versão reformulada de P_E4_5:** o padrão 1/r_j (R-V') custa 11.6 pp (kappa=200 optimal), enquanto o padrão r_j (R-V*) custa 0 pp. Com codificação consistente e o mesmo conjunto de referência, apenas a direcção da distorção muda o custo. TV_W do padrão 1/r_j ≈ TV_W(R-W) = 0.0815 (ver §4.6).

---

## 4. Diagnóstico

### 4.1 Causa da perda de 80 pp: codificação inconsistente de aspect

`Xadj473` (score R-V) trata `aspect` como contínuo: normaliza os azimutes em graus por min-max sobre 473 sítios. O avaliador (via `compute_objs_f64` em `pareto_utils.py`) trata `aspect` como binário: c=1 se azimute ∈ [90°, 180°] (sotavento indicator), c=0 caso contrário.

Estas transformações não são monotonamente relacionadas: um azimute de 350° tem valor alto no score contínuo (≈1.0) mas vale 0 no avaliador binário. O score maximiza sítios com azimute alto; o avaliador prefere sítios com azimute ∈ [90°,180°].

**Esta é uma inconsistência no pipeline** (build_score_473 vs _build_decision_matrix), não uma escolha metodológica do analista. O artigo deve apresentá-la assim.

**Os offsets b_j não são a causa.** Para portfolio de tamanho fixo k, score(T; b, A) = k·Σ_j w_j·b_j + Σ_{a∈T} Σ_j w_j·A_j·c̃_j(a). O primeiro termo é constante para todos os T de tamanho k, logo argmax(score) = argmax(score sem offset). Verificado algebricamente e numericamente (verify_e4_audit.py).

### 4.2 Decomposição confirmada pelas células post hoc (kappa=200, optimal)

| Contraste | Perda | Leitura |
|-----------|-------|---------|
| R-M → R-V* (só conjunto de referência, codificação consistente) | **0 pp** | Normalizar sobre 473 não custa nada sob montagem óptima |
| R-M → R-asp (só codificação, constantes de 389) | **76 pp** | A codificação explica praticamente tudo |
| R-asp → R-V (473 sítios em cima da codificação errada) | **4 pp** | Efeito residual; significância por confirmar com bootstrap emparelhado |

Sobre os 4 pp: a diferença não emparelhada é ≈1.5 SE. Não é possível afirmar significância ou não sem indicadores por draw (bootstrap emparelhado — ver §4.7).

### 4.3 R-V* greedy = 97.8% vs R-M greedy = 86.0%

Com codificação consistente (aspect binário), normalizar sobre os 473 sítios **melhora** a montagem greedy em ~12 pp. Este resultado contradiz a primeira recomendação prática actual do artigo ("normalise over the set of alternatives that can actually be chosen"). O efeito é consistente com kappa=50 (R-V* greedy = 97.6% vs R-M greedy = 96.0%; diferença menor porque kappa=50 já concentra pesos perto do AHP).

### 4.4 A direcção com plica usa avaliador A', não A

Verificado: R-M e R-M' têm médias idênticas draw-a-draw (86.0%/100.0%, kappa=200; 96.0%/100.0%, kappa=50). O DEV-E4-002 declarou que a direcção 389→A usaria a fronteira A (213 portfólios, objectivos sobre 473 sítios) — mas o pipeline não implementou isso. Todas as células usam avaliador A'.

R-V' = 88.4% ≠ 95.0% (tab:fourthcell row 389/A): |diff| = 6.6 > 3 SE = 4.3. **FAIL.** A comparação é entre células diferentes (A' vs A), não uma regressão.

Os valores R-V' = 88.4% e R-W' = 86.2% são um teste legítimo sobre o padrão 1/r_j contra o avaliador A'. Ver §4.6.

### 4.5 Assimetria por kappa

| kappa | R-V* opt (aspect binário) | R-V opt (aspect contínuo) | Perda de codificação |
|-------|--------------------------|--------------------------|---------------------|
| 200   | 100.0%                   | 20.0%                    | 80.0 pp             |
| 50    | 99.8%                    | 46.0%                    | 53.8 pp             |

A assimetria entre direcções (R-V' vs R-V) com codificação consistente:

| kappa | R-V* opt (r_j, 0 pp perda) | R-V' opt (1/r_j, A') | Assimetria |
|-------|---------------------------|---------------------|-----------|
| 200   | 100.0%                    | 88.4%               | −11.6 pp  |
| 50    | 99.8%                     | 96.8%               | −3.0 pp   |

### 4.6 R-V' como teste genuíno do Teorema (P_E4_5 reformulado)

Com codificação consistente, o contraste r_j (R-V*, 0 pp) vs 1/r_j (R-V', 11.6 pp) é evidência genuína sobre o efeito da direcção da distorção: mesmo TV_W, amplitude diferente da distorção entre os dois padrões. Calcular TV_W(padrão 1/r_j) com tvw_e4.py — esperado ≈ TV_W(R-W) = 0.0815 (mesma magnitude, sinal oposto).

### 4.7 Indicadores por draw — pendente

O e4_results.csv e o e4_vstar_results.csv contêm apenas médias. Para:
- confirmar R-M = R-M' draw-a-draw (actualmente apenas médias confirmadas)
- bootstrap emparelhado R-asp vs R-V (4 pp: significativo ou não)
- bootstrap emparelhado R-V* vs R-M greedy (12 pp greedy: significativo ou não)

É necessário modificar run_e4.py e run_e4_vstar.py para gravar indicadores por draw. Ver item 6 da lista de tarefas.

---

## 5. Historial de bugs no pipeline

| Versão | Bug | Sintoma |
|--------|-----|---------|
| v1 (ca50ce2) | Score usava X_adj escalado por A_j (389-base) | Todos fwd = 100% incluindo R-V |
| v2/v3 (d1bb682) | Construção afim com aspect binário vs contínuo | R-M = 24% |
| v4 (73cd65f) | Xadj389 raw para todas as células | R-M = 24% (aspect contínuo, 389-base) |
| v5 (f4d94d0) | Interpolação Xadj473 + (A_j-r_j)*X_adj_dm | R-M = 24% persistiu |
| v6 (efdc9d8) | X_adj_dm*A_j para B/W/M, Xadj473 para R-V | R-M=100%, R-V=20%: correcto para o controlo |

As versões v1 a v5 foram corridas e os resultados foram vistos antes de v6. Documentado explicitamente no DEV-E4-007 (commit b0e5c66).

---

## 6. Auditoria de codificação de aspect por script/espaço (2026-10-01T22:22)

| Script/Função | aspect coding | Usado em |
|---------------|---------------|----------|
| `pareto_utils.py` L107 — `compute_objs_f64` | **BINÁRIO** c=[90,180]=0 | Avaliador A' em todos os scripts |
| `run_473A_389A.py` L90 — `build_objs_ref` | **BINÁRIO** c=[90,180]=0 | Avaliador A (ref=473 e ref=389) |
| `mcdm_experiment.py` L166 — `compute_objectives` | **BINÁRIO** c=[90,180]=0 | Reprodução estudo-fonte |
| `mcdm_experiment.py` L132 — `_build_decision_matrix` | **BINÁRIO** c=[90,180]=1, benefit=True | Score SAW/minmax (factorial, E1, run_e4) |
| `mc_2cube_fixed.py` L113 — `build_score_473` | **CONTÍNUO** (x_via-mn)/rng | Score 473 (tab:fourthcell, R-V) |

**Conclusão:** o espaço A não tem inconsistência no avaliador. A tab:canonical, FAsize, FAinter e a reprodução {184,430,460} estão correctos. A inconsistência está confinada a `build_score_473` e afecta apenas as células da tab:fourthcell que usam este score.

A célula 473/A = 100% na tab:fourthcell é coincidência: os sítios com azimute alto (próximos de 360°) têm score alto no score contínuo E são classificados como não-sotavento pelo avaliador binário. Não é porque o avaliador A seja contínuo — é binário (pareto_utils L107, run_473A_389A L90).

---

## 7. Ficheiros produzidos

| Ficheiro | Commit | Descrição |
|----------|--------|-----------|
| `scripts/run_e4.py` | `efdc9d8` | Script final (v6) |
| `scripts/run_e4_vstar.py` | `a81db36` | Células post hoc R-V* e R-asp |
| `scripts/analyze_e4.py` | `ca50ce2` | Análise das previsões |
| `scripts/tvw_e4.py` | `d4e970b` | Cálculo de TV_W(R-W) |
| `scripts/verify_e4_audit.py` | `b0e5c66` | Verificações algébricas |
| `results/e4_results.csv` | `7603722` | 16 linhas (8 células × 2 kappas) |
| `results/e4_vstar_results.csv` | `2270cc4` | 8 linhas (R-V* e R-asp × 2 kappas) |
| `results/e1_weights_k200.npy` | `f607d27` | Matriz de pesos (SHA-256 bea05275) |
| `corpus/PRESPEC_E4.md` | `b0e5c66` | DEV-E4-001..007 |
