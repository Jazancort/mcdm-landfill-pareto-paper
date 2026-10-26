# Estado Atual — Artigo MCDM (fonte de verdade)

**Última atualização:** 29/set/2026 (Round 19 — auditoria A/B/C/D; tabela robustez suspensa; Q1/Q2 a redefinir)
**Não citar session-log.md para números — usar apenas este arquivo.**

---

## 1. Dataset, espaços e fronteiras

### Contagens

| Item | Valor | Fonte |
|------|-------|-------|
| Candidatos totais | 473 | df_real_data_cached.csv |
| Excluídos (dist_protected=0) | 84 | verificado exatamente |
| Viáveis para MCDM | 389 | = 473 − 84 |
| Trios viáveis (389, k=3, d≥10 km) | 1.944.653 | contagem exata |
| NaN: roads(41), urban(385), aero(429) | 3 sites | imputados (min+max)/2 dos 473 |

### Dois espaços de objetivos

| Espaço | Referência da normalização | Fronteira Pareto | Uso |
|--------|---------------------------|-----------------|-----|
| **A** | 473 (todos os candidatos) | 213 trios | Reprodução direta do IEEE Access 2026 |
| **A′** | 389 (somente viáveis) | 181 trios (A∩A′=132) | Experimento fatorial (Round 11+) |

**Por que A′:** O min-max com os 84 inviáveis altera os limites [min,max] sem que esses sites possam ser selecionados. García-Cascales & Lamata (2012) [MCM 56:123–132] documentam um mecanismo análogo para o TOPSIS vetorial; para o min-max o princípio é o mesmo: alternativas irrelevantes (que não podem ser escolhidas) não deveriam alterar a escala de valor. **Evidência empírica:** apenas 132 trios em comum entre as fronteiras de 213 (A) e 181 (A′).

**Nota sobre invariância:** postos também dependem do conjunto (um novo candidato redistribui os postos). O vetorial divide pela norma calculada sobre os candidatos presentes. Nenhuma das três normalizações usuais é invariante a inclusão/exclusão de alternativas.

### Fórmula do gap_norm (espaço A, amplitudes 1.9M)

```
gap(t) = max(0, max_{t'∈ 1.9M trios} min(dc, di, ds))
  dc = (F1(t)−F1(t')) / range_A(F1)
  di = (F2(t)−F2(t')) / range_A(F2)
  ds = (F3(t')−F3(t)) / range_A(F3)
  Amplitudes (1.9M): F1=0.2600  F2=0.4548  F3=0.5583
  Pendência: tabela suplementar com gap(ideal–nadir) se referee pedir.
```

### Definição formal de Q1 e Q2 (Round 19 — especificação canônica)

Seja **w** o vetor de pesos, **s(·,w)** o score do método, **t(w)** o trio selecionado, **f(·,w,𝒳)** os objetivos de um site calculados com pesos **w** e normalização sobre o conjunto de referência **𝒳**, e **F(w,𝒳)** a fronteira Pareto de objetivos de trios.

```
Para um espaço de referência 𝒳 ∈ {A (473), A′ (389)}:

  Fronteira estática:  F_stat(𝒳) = F(w_ahp, 𝒳)   — calculada uma vez com w_ahp
  Fronteira dinâmica: F_dyn(w)   = F(w,     𝒳)   — recalculada para cada w_draw

  Q1[𝒳]: score sorteado com w_draw, dominância avaliada com fronteira ESTÁTICA e
          objetivos do trio calculados com w_ahp FIXO.
          nd_Q1 = is_nd( t(w_draw), f(·, w_ahp, 𝒳), F_stat(𝒳) )
          → trio varia; escala de avaliação fixa.

  Q2[𝒳]: score, objetivos do trio E fronteira todos calculados com w_draw.
          nd_Q2 = is_nd( t(w_draw), f(·, w_draw, 𝒳), F_dyn(w_draw) )
          → tudo consistente com os mesmos pesos sorteados.

  Garantia P1: SAW[𝒳] ótimo = 100% em Q2[𝒳] (consequência da escalarização linear).
               Não vale para Q1[𝒳].
```

**O que o mc_18cells implementa (auditado Round 19):**
- `nd_Q2Ap` = Q2[A'] coerente: `is_nd(t(w), f(·,w,A'), F_dyn(w))` ✅
- `nd_Q1Ap` = **híbrido**: `is_nd(t(w), f(·,w_ahp,A'), F_stat(A'))` — trio sorteado, objetivos e fronteira em w_ahp. É Q1 na definição acima para o par (trio, avaliador), mas o objetivo do trio usa a mesma escala mm independentemente da norma usada no score. SAW×vec com κ=200 produz Q1[A']=12.8% porque o trio vec sorteado ocasionalmente é nd quando avaliado em escala mm/w_ahp — não porque seja nd em sua própria escala.

**Consequência para a tabela de robustez ao avaliador:**
A coluna de referência deveria ser Q2 com avaliador diferente — não Q1. O desenho correto é:

```
  nd_Favaliador = is_nd( t(w_draw), f(·, w_draw, 𝒳_avaliador), F(w_draw, 𝒳_avaliador) )
```

onde 𝒳_avaliador ∈ {A′_mm (389, mm), A′_vec (389, vec), A′_fixo (bounds convencionais)}.
Isso é recalcular a fronteira para CADA draw com a escala do avaliador — computacionalmente custoso (~3× o tempo do mc_18cells) mas conceitualmente limpo.

**Decisão de escopo:** a tabela de robustez requer redefinição e reexecução. Prosseguir com escrita de P1/P2/P3/P4 + Methods, que não dependem dessa tabela.

### Definição de Q1 e Q2 (versão anterior — SUBSTITUÍDA PELA ACIMA)

```
Q1[A]:  pesos sorteados no score do método; dominância em F(w_AHP, ref=473)
Q2[A]:  mesmos pesos sorteados no score E em F (ref=473)
Q1[A']: pesos sorteados no score; dominância em F(w_AHP, ref=389)
Q2[A']: mesmos pesos sorteados no score E em F (ref=389)

Garantia P1: SAW[ref] ótimo = 100% em Q2[mesma ref].
  SAW[473] ótimo em Q2[A]  = 100% ✓
  SAW[389] ótimo em Q2[A'] = 100% ✓
  SAW[389] em Q2[A]: NÃO tem garantia (referências diferentes).

Importante: os métodos no mc_18cells.py usam SEMPRE ref=389 para o score.
  Isso explica a diferença entre seção 4 (ref=473) e seção 10 (ref=389):
    TOPSIS-MM greedy: Q1[A] = 32.2% (seção 4) vs 24.8% (seção 10)
    SAW greedy:        Q1[A] = 67.0% (seção 4) vs 41.0% (seção 10)
  São métodos diferentes, não o mesmo método avaliado em dois espaços.
```

---

## 2. Pesos AHP e grupos de critérios

```
  f1 (custo,     minimizar): perm(0.152), slope(0.113), roads(0.030)
  f2 (impacto,   minimizar): rivers(0.091), aspect(0.075), coast(0.069),
                              protected(0.066), wells(0.055)
  f3 (segurança, maximizar): urban(0.166), aero(0.102), cult(0.081)
  CR = 0.056  (λ_max=11.8525, CI=0.08525, RI=1.51)
```

---

## 3. Experimento base — trios canônicos em A (pesos AHP, normalização 473)

**Nomenclatura:** SAW[473] = score com min-max sobre os 473. SAW[389] = min-max sobre os 389.
O trio {184,279,320} com gap_A=0.032 é o SAW[473] greedy em A. O SAW[389] greedy (caso base de A′) coincide numericamente com esse trio — confirmado.

| Método | Variante | IDs | f1_A | f2_A | f3_A | in_A | gap_A |
|--------|----------|-----|------|------|------|------|-------|
| SAW[473] greedy | greedy | {184,279,320} | 0.1273 | 0.5963 | 0.6207 | False | 0.032 |
| SAW[473] optimal | optimal | {184,430,460} | 0.0811 | 0.5568 | 0.6170 | True | 0.000 |
| TOPSIS-VN greedy | greedy | {233,320,355} | 0.1113 | 0.5669 | 0.5358 | False | 0.048 |
| TOPSIS-MM greedy | greedy | {184,227,460} | 0.1104 | 0.6712 | 0.6883 | True | 0.000 |
| VIKOR greedy | greedy | {233,279,320} | 0.1190 | 0.5819 | 0.5879 | False | 0.052 |
| PROMETHEE greedy | greedy | {51,233,345} | 0.0447 | 0.5900 | 0.4852 | True | 0.000 |
| BCS_IEEE | ref | {184,430,460} | 0.0811 | 0.5568 | 0.6170 | True | 0.000 |

**SAW clássico (sem inversão de custo):** o "SAW clássico" que aparece em seção 4 maximiza todos os critérios, inclusive os de custo. Não é um método MCDM válido para este problema — é artefato de uma implementação sem orientação dos critérios. Os 42–50% de %nd são artefato, não resultado substantivo.

---

## 4. MC Q2 v2 — espaço A, score com normalização 473 (monte_carlo_q2_v2.py)

**Válido:** `monte_carlo_q2_v2.py` (ref=473 nos scores E nos objetivos).
**Inválidos:** `monte_carlo_q2.py`, `mc_q1q2*.csv`.

### Regressão de sanidade (v2 = v3 para métodos comuns)

| Método | α=50 v3 | α=50 v2 | α=200 v3 | α=200 v2 |
|--------|---------|---------|---------|---------|
| PROMETHEE | 45.4% | 45.4% | 54.6% | 54.6% |
| TOPSIS-MM | 38.8% | 38.8% | 32.2% | 32.2% |
| VIKOR | 25.6% | 25.6% | 29.6% | 29.6% |

Identidade confirma lógica de fronteira idêntica entre scripts.

### Tabela MC Q2 v2 — Q1[A] e Q2[A], ref=473

| Método | Variante | α=50 Q1[A] | α=50 Q2[A] | α=200 Q1[A] | α=200 Q2[A] |
|--------|---------|-----------|-----------|-----------|-----------|
| SAW[473] optimal | optimal | 87% | **100%** | 97% | **100%** |
| SAW[473] greedy | greedy | 65% | 73% | 67% | 68% |
| PROMETHEE greedy | greedy | 45% | 56% | 55% | 60% |
| TOPSIS-MM greedy | greedy | 39% | 65% | 32% | 67% |
| VIKOR greedy | greedy | 26% | 49% | 30% | 47% |
| TOPSIS-VN greedy | greedy | 14% | 36% | 2% | 21% |

**Q2 e Q1 em A:** em A, Q2 ≥ Q1 em todos os métodos. Em A′ há inversões (ver seção 6).

---

## 5. Espaço A′ — trios canônicos (space_aprime.py)

**Fronteira A′:** 181 trios. A∩A′=132.

| Label | in_A | gap_A | in_A′ | gap_A′ |
|-------|------|-------|-------|--------|
| SAW[473] greedy | False | 0.032 | True | 0.000 |
| SAW[473] optimal | True | 0.000 | True | 0.000 |
| TOPSIS-VN greedy | False | 0.048 | True | 0.000 |
| TOPSIS-MM greedy | True | 0.000 | True | 0.000 |
| VIKOR greedy | False | 0.052 | True | 0.000 |
| PROMETHEE greedy | True | 0.000 | True | 0.000 |

A falha do TOPSIS-VN em A é parcialmente atribuível ao conjunto de referência da normalização, não apenas ao método.

---

## 6. MC Q1 e Q2 em A′ — mc_aprime_full.py (Round 11, ref=389 nos scores)

| Método | Variante | α=50 Q1[A'] | α=50 Q2[A'] | α=200 Q1[A'] | α=200 Q2[A'] |
|--------|---------|------------|------------|------------|------------|
| SAW_mm optimal | optimal | 84% | **100%** | 89% | **100%** |
| SAW_mm greedy | minmax | 73% | 73% | **70%** | **65%** |
| TOPSIS_mm greedy | minmax | 57% | 73% | 69% | 72% |
| TOPSIS_vn greedy | vector | 49% | 43% | 57% | 51% |

**Inversões Q2<Q1 em A′:**
- SAW_mm greedy α=200: Q1=70% vs Q2=65%
- TOPSIS_vn greedy: Q2<Q1 em ambos os α

TOPSIS-VN não é o único — é o mais extremo. Não usar "único".

---

## 7. Bug de sinal postos×TOPSIS/VIKOR (Round 13 — corrigido)

**Causa:** `X_ranks` vem de `X_adj` (custo já invertido), mas o código reaplicava `benefit` ao calcular PIS/NIS no TOPSIS/VIKOR, invertendo os critérios de custo uma segunda vez. Os scores ficavam parcialmente invertidos (não negativamente correlacionados — Spearman=+0.456 com a versão correta, não negativo).

**Evidência:** Spearman(SAW-ranks, TOPSIS-ranks_bugado)=0.456. Spearman(SAW-ranks, TOPSIS-ranks_corrigido)=0.907.

**Consequência:** as células bugadas preferiam sites caros e produziam trios dominados. Com a correção, passam de 0% para 22–47% em Q2[A′].

**Regressão bit-a-bit (Round 14):** células não-postos foram testadas contra mc_aprime_full.py.
- SAW×mm×greedy: 69.0% vs 64.6% (FAIL: 4.4 pp) — scripts diferentes (mc_18cells usa ref=389 no score; mc_aprime_full usava pipeline diferente). O 69.0% vem da mc_aprime_full; o canônico é 64.6% (mc_18cells_raw).
- SAW×mm×optimal: 100% (PASS)
- TOPSIS×mm×greedy: 72.9% vs 72.4% (PASS)
- TOPSIS×mm×optimal: 94.4% vs 96.6% (FAIL: 2.2 pp) — mesma causa. O 94.4% vem da mc_aprime_full; o canônico é 96.6% (mc_18cells_raw).

Estas diferenças são esperadas: os dois scripts calculam o score de forma ligeiramente diferente. Não são bugs — são implementações distintas. A versão mc_18cells.py é a canônica para o experimento fatorial.

**Q1[A]=Q1[A′] em SAW×ranks:** real. O trio SAW-ranks não muda com A vs A′ (postos não dependem da referência de normalização). Mas a fronteira de avaliação é diferente (213 vs 181 trios). 2998/3000 linhas idênticas. As 2 exceções são trios na fronteira de um espaço mas não do outro — documentar se aparecer em citação.

---

## 8. Pesos efetivos vetoriais — w_j × (max−min)/‖x_j‖ (Round 13)

Forma fechada: ρ_j = (max_j−min_j)/‖x_j‖ = R_j/σ_j / √(n(1+CV_j⁻²))

| Critério | w_nom | escala | ρ_j=(max−min)/‖x‖ | w_eff_norm | fator |
|---------|-------|--------|-----------------|-----------|-------|
| **perm** | 0.152 | contínua (m) | 0.583 | 0.436 | **2.865×** ↑ |
| rivers | 0.091 | contínua (m) | 0.265 | 0.119 | 1.302× |
| cult | 0.081 | contínua (m) | 0.171 | 0.068 | 0.839× |
| roads | 0.030 | contínua (m) | 0.206 | 0.030 | 1.012× |
| slope | 0.113 | contínua (°) | 0.139 | 0.077 | 0.682× |
| aspect | 0.075 | **binária** {0,1} | 0.103¹ | 0.038 | 0.507× |
| coast | 0.069 | contínua (m) | 0.131 | 0.044 | 0.645× |
| protected | 0.066 | contínua (m) | 0.105 | 0.034 | 0.516× |
| **urban** | 0.166 | contínua (m) | 0.107 | 0.087 | **0.525×** ↓ |
| aero | 0.102 | contínua (m) | 0.088 | 0.044 | 0.432× |
| wells | 0.055 | contínua (m) | 0.084 | 0.023 | 0.412× |

*Para critérios binários: ρ_j = 1/√n₁ onde n₁ = nº de sites com valor 1. Aspect: n₁=94, ρ=1/√94=0.1031. Todos os demais critérios são contínuos (distâncias em metros ou ângulos em graus) — ρ_j calculado sobre os dados brutos dos 389 sites viáveis.*

¹ aspect: X_via[:,aspect] é binário (0/1 após conversão de ângulo). c=1 se aspecto∉[90°,180°] (n₁=94 sites dos 389 viáveis), c=0 caso contrário (n₀=295). Forma fechada: ρ = 1/√n₁ = 1/√94 = 0.1031. **Origem do 0.0967 (Round 15 revisado, confirmado Round 16):** o valor 0.0967 = (max−min)/‖x_raw‖ sobre os ângulos brutos (não binarizados) dos 389 sites — confirmado por print direto: range=358.7, ‖x‖=3709.8, ρ=0.09668. Coincide com 1/√107, mas 107 não é n₁ de nenhum subconjunto real (df_via binarizado: n₁=94, ρ=0.1031; df_imp binarizado: n₁=115, ρ=0.0933). Valor correto para TOPSIS vetorial: **ρ_aspect = 0.1031**.

**Origem do 2.40× para rivers:** é w×std(rivers_vec)/w×std(rivers_mm) = 0.145/0.061 = 2.40, medindo a dispersão normalizada (std), não ρ_j. São métricas distintas. O ρ_j de rivers é apenas 1.31× — a distorção de peso via ρ é modesta.

**perm no top-10:** 90% dos 389 sites têm perm=0. Top-10 SAW-mm: todos perm=0. Top-10 SAW-vec: site 396 tem perm=532 (máximo) no topo — o perm inflado pelo vetorial seleciona um outlier (site 396) que fica fora do top-10 do min-max. Hipótese P3 para perm: "perm está concentrado em outliers fora do conjunto competitivo; o peso inflado seleciona sites dominados".

---

## 9. Análise das 12 células válidas — efeitos marginais (analyze_14cells.py, Round 13)

**Células excluídas:** ranks×topsis e ranks×vikor (bug de sinal Round 13); VIKOR×vector (duplicata por invariância afim). VIKOR×ranks não colapsa (R16 confirmado): scores distribuídos, {51,215,386} com pesos AHP fixos (ver seção 16 item 2 para Q2 MC).

**Médias por nível corretas (α=200, Q2[A′], 12 células):**

| Fator | Níveis | Amplitude |
|-------|--------|-----------|
| Normalização | mm=79.3%, ranks=76.5%, vec=53.5% | **25.8 pp** |
| Montagem | optimal=78.8%, greedy=61.7% | **17.0 pp** [15.5, 18.4] |
| Agregação | saw=71.4%, vikor=71.2%, topsis=68.0% | **3.4 pp** |

*Nota arredondamento (Montagem): diff real = 17.03 pp; 78.8−61.7 = 17.1 por arredondar médias primeiro. Usar 17.0 pp.*

**Notas:**
1. Efeito de normalização inclui ranks (76.5%) que só aparece com SAW — confundimento parcial.
2. Efeito de montagem inflado por SAW×mm×ótimo=100% (P1 garante). Excluindo P1, efeito de agregação dentro de minmax×greedy = **8.6 pp**.
3. Efeito de agregação de 3.4 pp está deprimido pelo desbalanceamento: TOPSIS tem 2/4 células vetoriais, VIKOR nenhuma. Amplitudes dentro de cada normalização divergem.

---

## 10. 2³ balanceado {SAW,TOPSIS}×{mm,vec}×{greedy,ótimo} (mc_18cells_raw, Round 14)

> **Nomenclatura (R0c):** neste documento α é o parâmetro de concentração de Dirichlet (α∈{50,200}) — **não** é distância de separação. A distância mínima entre sites é sempre `d_min=10 km` (MIN_DIST_KM=10 no código). Os scripts mc_robustez.py e mc_2x2_fronteiras.py precisam de assert `MIN_DIST_KM == 10` antes do loop — isso é parte do gate R1.

κ=200, Q2[A′], ref=389 nos scores. Dados de mc_18cells_raw.csv (bug de sinal corrigido). (κ = α = concentração Dirichlet; usando κ daqui em diante para evitar colisão com distância).

### Tabela

| Agg | Norm | Mont | Q1[A] | Q2[A] | Q1[A′] | Q2[A′] |
|-----|------|------|-------|-------|--------|--------|
| saw | minmax | greedy | 41.0% | 46.6% | 70.0% | 64.6% |
| saw | minmax | optimal | 87.4% | 95.0% | 89.4% | **100.0%** |
| saw | vector | greedy | 0.8% | 18.6% | 12.8% | 54.2% |
| saw | vector | optimal | 3.4% | 16.2% | 31.6% | 56.8% |
| topsis | minmax | greedy | 24.8% | 61.4% | 68.8% | 72.4% |
| topsis | minmax | optimal | 72.4% | 81.2% | 81.4% | 96.6% |
| topsis | vector | greedy | 0.0% | 14.2% | 56.8% | 50.6% |
| topsis | vector | optimal | 0.0% | 14.2% | 36.6% | 52.4% |

### Efeitos principais e interação norm×mont (bootstrap 2000, α=200, Q2[A′])

| Efeito | pp | IC 95% |
|--------|-----|--------|
| Normalização (mm−vec) | **+29.9** | [+27.1, +32.9] |
| Montagem (ótimo−greedy) | **+16.0** | [+14.1, +17.9] |
| Agregação (SAW−TOPSIS) | +0.9 | [−0.5, +2.3] |
| **Montagem DENTRO de mm** | **+29.8** | [+27.4, +32.2] |
| **Montagem DENTRO de vec** | **+2.2** | [−0.5, +4.9] |

### Interpretação da interação

A montagem (ótima vs gulosa) produz **+29.8 pp com min-max** e apenas **+2.2 pp com vetorial** (IC inclui 0). O efeito principal de montagem (+16.0 pp) é uma média ponderada dessas duas situações — ele mascara uma interação forte.

**Por que a montagem não ajuda com vetorial:** o score vetorial não está alinhado com o avaliador (que usa min-max). Otimizar um score desalinhado produz trios que maximizam o critério errado. A montagem ótima só garante Pareto-eficiência quando score e avaliador usam a mesma normalização.

**Circularidade do avaliador:** parte do efeito de normalização (mm > vec, +29.9 pp) reflete o fato de que o avaliador A′ também usa min-max. Esse artefato de alinhamento é quantificado pela quarta casa (seção 11), que mostra o custo do desalinhamento entre a referência do método e a do avaliador.

---

## 11. Quarta casa 2×2: ref método × avaliador (mc_4thcell_raw, Round 14)

2×2: ref método {473, 389} × avaliador {A, A′}. SAW×mm como representante. α=200. Todos os valores são Q2.

| ref método | avaliador | greedy Q2 | ótimo Q2 |
|-----------|-----------|-----------|----------|
| 473 | A | 68.4% | 100.0% |
| **473** | **A′** | **15.0%** | **20.0%** |
| 389 | A | 46.6% | 95.0% |
| **389** | **A′** | **64.6%** | **100.0%** |

**Padrão observado: cruzamento — cada referência vence no avaliador que usa a mesma referência.**
- ref=473 vence em A (avaliador 473): +68.4 vs +46.6 pp (+21.8 pp)
- ref=389 vence em A′ (avaliador 389): +64.6 vs +15.0 pp (+49.6 pp)

**O que os dados mostram:** o **desalinhamento** entre a referência do método e a do avaliador é caro. Quando o método usa os 473 (incluindo inviáveis) mas o avaliador usa os 389 (espaço de decisão real), o custo é 49.6 pp (greedy) e 80.0 pp (ótimo). O custo no sentido oposto é 21.8 pp (greedy) e 5.0 pp (ótimo).

**O que os dados não mostram sozinhos:** qual avaliador é o correto. Para o argumento normativo ("normalizar só sobre os viáveis"), é necessário justificar que A′ é o avaliador relevante — porque os 84 sites inviáveis (dist_protected=0) não podem ser escolhidos (García-Cascales & Lamata 2012). A quarta casa quantifica o custo do desalinhamento, não o prova a priori.

**Assimetria informativa:** o custo maior do lado ref=473 (49.6 pp vs 21.8 pp) é consistente com a hipótese de que incluir inviáveis distorce mais a escala do que excluí-los — mas essa assimetria também pode refletir a maior amplitude dos objetivos em A (mais candidatos).

Para TOPSIS×mm (α=200, quarta casa):
- greedy: Q1[A′]=42.2%, Q2[A′]=52.2% com ref=473 — substancialmente inferior a ref=389 (68.8%/72.4%)
- Efeito desalinhamento para TOPSIS: +26.6 pp Q1[A′] e +20.2 pp Q2[A′]

---

## 12. Proposições — status (Round 14)

| P | Enunciado | Status |
|---|-----------|--------|
| P1 | SAW[ref] ótimo é Pareto-ótimo em Q2[mesma ref] | Confirmada. Citar como resultado técnico, não contribuição. |
| P2 | PROMETHEE II (usual) = SAW sobre postos | **Identidade exata** (Round 19). Com midranks puros (sem normalização): $\phi(a) = \frac{n+1}{n-1} - \frac{2}{n-1}\sum_j w_j\,r_j(a)$, verificação numérica: $\max|\phi + \frac{2}{n-1}\text{SAWranks}| = 6.7\times10^{-16}$, Spearman=1.000000, divergências=0/389. Empates não quebram a identidade — se cancelam algebricamente. A divergência 367/389 do código vem de usar $r_j/(N+1)$ (midranks normalizados) em vez de $r_j$ puros: com 350 zeros em perm, o midrank máximo é ≈214.5 em vez de 389, comprimindo a amplitude para ~0.55× — mesmo mecanismo de ρ_j da P3, agindo sobre postos. Corolário: SAW-ranks com normalização por (N+1) **não** é idêntico ao PROMETHEE II quando há empates massivos. |
| P3 | No TOPSIS vetorial, perm é inflado 2.86× e urban reduzido 0.53× via ρ_j=(max−min)/‖x‖. perm seleciona outlier (site 396) fora do conjunto competitivo. Shapley(Jac@10): urban=0.309 e aspect=0.228 lideram diferença de **ordenação**. | Forma fechada verificada. ρ_aspect=0.1031 (n₁=94, binário: 1/√94). ρ_perm=0.583 (contínuo: cauda longa concentra norma). ρ_j=1/√n₁ aplica-se **apenas** a critérios binários. Tabela §8 tem coluna `escala`. Valores: perm=2.865×, urban=0.525×, aspect=0.507×. Shapley(Jac) mede diferença de **ordenação** — fenômeno distinto de ρ_j. |
| P4 | SAW[389] greedy dominado em Q2[A′] mesmo sendo não dominado em Q1[A′] (gap_Q1=0) | Confirmada: draw=302, α=200, gids={184,279,320}, gap_Q2=0.028, gap_Q1=0.000 |

---

## 13. Scripts — estado correto (Round 14)

```
VÁLIDOS:
  mcdm_experiment.py             ← MCDM_DATA_DIR + line_buffering
  monte_carlo_q2_v2.py           ← MC espaço A, ref=473
  mc_18cells.py                  ← 18 células, bug de sinal corrigido (Round 13)
  analyze_14cells.py             ← 12 células válidas (analisa mc_18cells_raw)
  mc_2cube_and_4thcell.py        ← 2³ + quarta casa (rodando Athena, Round 14)
  mc_aprime_full.py              ← 7 métodos em A′ (Round 11)
  shapley_norm.py                ← Shapley 2048 combos
  diag_r14.py                   ← aspect, perm top-10, bit-a-bit (Round 14)
  diag_p3.py                    ← pesos efetivos vetoriais (Round 13)
  rw_p2.py                      ← r_w Pinto da Costa 2005 (Round 17)
  vikor_ranks_q2.py             ← VIKOR×ranks Q2[A'] (Round 17)
  mc_2x2_fronteiras.py          ← F_vec (109) e F_fixo (184) (Round 17)
  mc_robustez.py                ← predicado misto (obsoleto para publicação) — manter para histórico
  mc_robustez_q1.py             ← predicado Q1 coerente (CANÔNICO, Round 18)
  assert_r1.py                  ← 5 asserts de regressão Gate R1 (Round 18)
  diag_mc_robustez.py           ← D1+D2+D3: diagnóstico predicado + bootstrap (Round 18)

RESULTADOS VÁLIDOS:
  results/mc_q2v2_summary.csv           ← espaço A, ref=473
  results/mc_18cells_raw.csv            ← 18 células corrigidas (CANÔNICO)
  results/mc_18cells_summary.csv        ← idem summary
  results/analysis_14cells.csv          ← 12 células
  results/mc_4thcell_raw.csv            ← quarta casa
  results/pareto_front_Aprime.csv       ← 181 trios, IDs globais
  results/rw_p2.csv                     ← r_w=0.9808, Jaccard top-3=1.000
  results/vikor_ranks_q2.csv            ← VIKOR×ranks pesos fixos
  results/mc_2x2_fvec.csv              ← F_vec 109 trios
  results/mc_2x2_ffixo.csv             ← F_fixo 184 trios (ex-fexog)
  results/mc_robustez_q1_raw.csv       ← colunas: nd_Fmm, nd_Fvec, nd_Ffixo (predicado Q1, CANÔNICO)
  results/mc_robustez_q1_summary.csv   ← tabela resumo por alpha/norm/mont
  results/bootstrap_q1_gaps.csv        ← IC bootstrap emparelhado Q1 coerente (PUBLICÁVEL)
  results/diag_q1_comparison.csv       ← comparação Q1_corrigido vs F_mm_robusto
  results/bootstrap_gaps.csv           ← bootstrap sobre mc_robustez_raw (predicado misto, obsoleto)
  results/mc_robustez_raw.csv          ← predicado misto (obsoleto para publicação)
  results/shapley_norm_results.csv
  results/p4_best_counterexample.json

INVÁLIDOS:
  monte_carlo_q2.py, mc_q1q2_summary.csv, mc_q1q2_raw.csv
  variance_decomp_fogo.csv
  results/mc_2x2_fexog.csv             ← substituído por mc_2x2_ffixo.csv
```

---

## 14. .bib — estado correto

- **GarciaCascales2012:** MCM 56(5-6):123-132, DOI 10.1016/j.mcm.2011.12.022. ✓ no refs.bib.
- Bouyssou (1992) — citar para P2.
- Marchant (1996/1998) — citar para P2.
- Mareschal, De Smet & Nemery (2008, IEEM) — não está no refs.bib.
- Pinto da Costa & Soares (2005) — não está no refs.bib.
- Brito (2020), Andrade & Barbosa (2015) — localizar PDF.

---

## 15. Manchete defensável — baseada em Q2[A'] (Round 19)

> **Nota:** §15 anterior com +75/+89 pp foi revertida — era artefato de gap com vec=0%. A manchete abaixo usa apenas Q2[A'] do mc_18cells_raw, que tem predicado coerente e canônico verificado.

"Na seleção de conjuntos de locais via MCDM, normalizar incluindo alternativas inviáveis desalinha o método em relação ao espaço de decisão relevante. Esse desalinhamento custa 50–80 pp de qualidade Pareto medida no espaço dos candidatos viáveis (quarta casa, SAW×mm, κ=200). Dentro do espaço viável (A′, ref=389), em Q2[A'] com κ=200: a normalização (mm vs vetorial) contribui com +29.9 pp [+27.1, +32.9]; a montagem (ótima vs gulosa) contribui com +29.8 pp dentro de mm e +2.2 pp (ns) dentro de vec; a agregação importa menos de 1 pp entre SAW e TOPSIS. A questão de quanto do efeito de normalização é circularidade do avaliador vs efeito intrínseco requer um avaliador exógeno com definição formal — pendente (ver §18 fila)."

**Números canônicos para §15 (todos de mc_18cells_raw.csv, Q2[A'], κ=200):**
- Norm: +29.9 pp [+27.1, +32.9]
- Montagem: +16.0 pp [+14.1, +17.9] (média); +29.8 pp dentro de mm; +2.2 pp (ns) dentro de vec
- Agregação: +0.9 pp (ns)
- Quarta casa: greedy 15.0%→64.6% (+49.6 pp), optimal 20.0%→100% (+80.0 pp)

---

## 16. Estado dos experimentos — lista única (Round 17, saneado)

> **ATENÇÃO:** esta é a única lista canônica de status. Seções anteriores de "próximos passos" foram colapsadas aqui. Cada item tem um carimbo de round.

| # | Experimento | Status | Round | Número canônico |
|---|-------------|--------|-------|-----------------|
| 1 | Discrepância ρ_aspect (0.1031 vs 0.0967) | ✅ CORRIGIDO | R15 | ρ=1/√94=0.1031 (binarizado, n₁=94); 0.0967 era ρ do ângulo bruto |
| 2 | VIKOR×ranks: colapsa? | ✅ NÃO colapsa | R16 | Com pesos fixos: greedy={215,386,51} dominado. MC: Q2=22.0%/34.8% (mc_18cells_raw) |
| 3 | ρ_perm na matriz TOPSIS-VN | ✅ CONFIRMADO | R16 | perm é **contínuo** (distância em m). ρ=0.583 decorre de max=532 com ‖x‖≈912: a cauda longa concentra a norma em poucos sites. A forma fechada ρ=1/√n₁ aplica-se apenas a critérios binários (ver aspect, n₁=94). |
| 4 | P2 — identidade PROMETHEE = SAW-ranks | ✅ EXATA | R19 | Identidade exata com midranks puros: $\max\|\phi + \frac{2}{n-1}\text{SAW}\| = 6.7\times10^{-16}$, Spearman=1.000, divergências=0/389. Empates se cancelam algebricamente. Divergência 367/389 no código anterior: usar $r/(N+1)$ em vez de $r$ comprime amplitude de perm para 0.55× (350 zeros). Corolário de P3: mesmo mecanismo ρ_j sobre postos. |
| 5 | r_w (Pinto da Costa 2005) | ✅ CALCULADO | R17 | r_w=0.9808 ≈ Spearman=0.9806. Divergência top-3=0 |
| 6 | F_vec (fronteira alternativa) | ✅ CALCULADO | R17 | 109 trios. `results/mc_2x2_fvec.csv` |
| 7 | F_fixo (fronteira alternativa, ex-F_exog) | ✅ CALCULADO | R17+R18 | 184 trios. `results/mc_2x2_ffixo.csv` (cópia de mc_2x2_fexog.csv, renomeado). Bounds **convencionais** — não regulatórios. slope=(0,20)° ≠ conversão de NBR 13.896 (jurisdição errada). |
| 8 | MC robustez 2×2+1 | ✅ VÁLIDO | R17+R18+A3 | Gate R1: 5/5 asserts. mc_robustez_q1.py com predicado Q1 coerente. Bootstrap Q1 emparelhado: todos os 12 gaps excluem zero. Ver tabela na §16 (subsecção "Tabela 2×2+1 REINTERPRETADA") e §15 para manchete calibrada. |
| 9 | .bib verificação | ✅ CONCLUÍDO | R17 | Kuo2017, Hwang1981, PintoDaCosta2005 adicionados. Yang2015, EiseltMarianov2014 confirmados |
| 10 | Espaço B MC | ❌ LIMITAÇÃO | — | Tratado como limitação do artigo |

### Resultados válidos (não afetados pelo bug R17)

**S1 — r_w:** Spearman=0.9806, r_w=0.9808, Jaccard top-3=1.000, top-10=0.818. `results/rw_p2.csv`.

**S2 — VIKOR×ranks (pesos AHP fixos):** trio={51,215,386} dominado em A′ para α=50 e α=200. Q2=0% com pesos fixos. Q2=22.0%/34.8% é a média MC do mc_18cells_raw (500 draws). `results/vikor_ranks_q2.csv`.

**S3 — Fronteiras F_vec e F_fixo:** calculadas na Athena em 28s. F_vec=109 trios, F_fixo=184 trios. `results/mc_2x2_fvec.csv`, `results/mc_2x2_ffixo.csv`.

### Tabela 2×2+1 — SUSPENSA (Round 19 — achados A/B/C/D)

> **NÃO PUBLICAR.** Três problemas estruturais identificados. Requer redefinição formal de Q1/Q2 antes de reexecução.

**Achado A (bloqueador):** com SAW×vec = 0.0% em κ=200, o gap mm−vec = nível absoluto de mm. O bootstrap do "contraste" colapsa em bootstrap de mm sozinho. O IC [+71.6, +79.2] não é IC de contraste — é IC de mm reetiquetado. §15 com +75 a +89 pp contradiz §10 com +29.9 pp para o mesmo contraste; o maior é artefato de subtrair zero.

**Achado B (fatal para independência dos avaliadores):** nd_Fvec == nd_Ffixo em 99.92% das 4.000 linhas, apesar de |F_vec ∩ F_fixo| = 29/119/168. A convergência não vem das fronteiras — vem do predicado com objetivos w_ahp fixos que domina a resposta independentemente de qual fronteira se usa. F_fixo não é um avaliador independente neste desenho: é uma réplica de F_vec.

**Achado C (lógica de publicação):** o gate falhou para F_mm (−12 a −58 pp vs §10). As colunas sem canônico de referência (F_vec, F_fixo) são as menos verificáveis, não as mais publicáveis. Ausência de teste ≠ evidência de correção.

**Achado D (raiz de tudo):** Q1[A'] não tem definição canônica consistente no código. mc_18cells e mc_robustez_q1 implementam coisas diferentes, ambas internamente misturadas. **Ação: escrever definição formal antes de qualquer reexecução.**

**O que está sólido (não afetado):**
- Q2[A'] do mc_18cells: pesos w_draw em (a) score, (b) objetivos trio, (c) fronteira — coerente. Todos os resultados da §10 baseados em Q2[A'] são válidos.
- P1 (100% Q2), P4 (contraexemplo Q2), interação norm×mont (+29.8 vs +2.2 pp em Q2).
- P2, P3 — não dependem de Q1/Q2.

**Próximo passo:** definição formal de Q1/Q2 (§1 do doc atualizar), auditoria mc_18cells contra essa definição, reexecução se necessário. Ver §18 fila de escrita.

## 18. Plano de escrita — estado atual (Round 19)

> Experimentos Q2 concluídos e válidos. Tabela de robustez suspensa — requer redefinição Q1/Q2 e reexecução. Próxima etapa: escrita R3 paralela à redefinição.

### Decisões pendentes

| Decisão | Status | Impacto |
|---------|--------|---------|
| **D1 — Venue-alvo** | ⬜ ABERTO | Define comprimento da Discussion. Decidir antes de Results/Discussion. |
| **D2 — Base legal para A′** | ⬜ ABERTO | Citar decreto/lei para os 84 inviáveis. Sem isso, A′ é escolha analítica. |
| **D3 — Tabela robustez** | ⬜ BLOQUEADO | Requer: definição formal Q2 com avaliador diferente; recalcular fronteira para cada draw com escala do avaliador; n≥5.000 draws se efeito < 5 pp. Não bloqueia P1–P4 + Methods. |

### O que pode escrever agora

| # | Tarefa | Estimativa |
|---|--------|-----------|
| R3a | `propositions.tex` P1/P2/P3/P4 | 2–3 h |
| R3b | Problem formulation (definição formal Q2, espaços A/A') | 1–2 h |
| R3c | Methods (dataset, critérios, métodos, normalização, r-sep, montagem, Q2) | 3–4 h |
| R3d | Literature Review | 4–5 h |
| R3e | Introduction | 3–4 h |

### O que espera D3

| # | Tarefa |
|---|--------|
| R3f | Results — tabela 2³ e quarta casa disponíveis; robustez aguarda D3 |
| R3g | Discussion — aguarda R3f + D1 + D2 |
| R3h | Abstract + Conclusion |

### Spec R3a — propositions.tex

- **P1:** consequência da escalarização linear. SAW[𝒳] ótimo é Pareto-ótimo em Q2[𝒳]. Verificação: 100% Q2[A'] mm×optimal κ=200. Não apresentar como contribuição nova.
- **P2:** corolário Bouyssou 1992 + Marchant 1996. Quando P_j discreta por posto, PROMETHEE II = SAW sobre postos = Borda. r_w=0.9808, Jaccard top-3=1.000. Divergência 367/389 sites: empates em perm (350 zeros).
- **P3:** ρ_j = (max−min)/‖x‖ (contínuo); ρ_j = 1/√n₁ (binário, aspect n₁=94). Tabela: perm=2.865×, urban=0.525×, aspect=0.507×. Shapley(Jac@10) mede ordenação — distinto de ρ_j.
- **P4:** contraexemplo em Q2 puro. draw=302, κ=200, {184,279,320}: não-dominado no escore greedy, dominado em Q2[A'] (gap_Q2=0.028). Reformular sem mencionar Q1 (suspensa).


**R3e — Results (após D1):**
- Tabela 2³: 8 células, efeitos em pp com IC bootstrap (seção 10)
- Quarta casa: tabela 2×2, cruzamento, custo de desalinhamento 50–80 pp (seção 11)
- Robustez ao avaliador: F_vec e F_fixo; usar §15 para manchete calibrada e bootstrap_q1_gaps.csv para números
- VIKOR×ranks: Q2=22.0%/34.8%, trio dominado com pesos fixos
- P4: contraexemplo numérico

**R3f — Discussion (após D2):**
- Posicionar contra portfólio MCDM sem restrição espacial (Vetschera, Mavrotas)
- A vs A′: García-Cascales 2012 como âncora; os 84 inviáveis precisam de base legal (D2)
- P2 como corolário, não contribuição nova
- Limitações: espaço B (ref=389 fixo) como limitação; empates perm na P2; F_fixo são bounds convencionais
- Lassey 2025 aqui, não na revisão
