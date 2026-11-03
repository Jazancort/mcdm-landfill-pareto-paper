# Session Log — Artigo MCDM (Aterro Sanitário)
> **ARQUIVO HISTÓRICO — CONGELADO em 28/set/2026.**
> Não usar como referência para números, decisões ou status.
> Fonte de verdade: `estado-atual.md`
>
> O bloco "ESTADO ATUAL — FONTE DE VERDADE" abaixo está **superado** — foi o estado em 27/set/2026.

## Sessão de 27 de setembro de 2026

---

## ESTADO ATUAL — FONTE DE VERDADE (atualizado 27/set/2026)

Esta seção resume apenas decisões e fatos verificados diretamente. O histórico completo está nas seções abaixo.

### Dataset

| Item | Valor | Como verificado |
|------|-------|----------------|
| Dataset principal | `df_real_data_cached.csv` (473 linhas, 13 colunas em inglês, valores contínuos em metros/graus) | Leitura direta do CSV |
| Localização | `G:\...\Tentativa de dados via GIS\results_cache\df_real_data_cached.csv` | — |
| N candidatos (após filtro 50%) | 473 | `len(df)` |
| N áreas protegidas (dist==0) | 84 | `(df['dist_protected_area (m)'] == 0).sum()` |
| N viáveis para MCDM | 389 (= 473 − 84) | — |
| Pasta de resultados válida | `New code/results/results-2026-04-07_18-40-54/` | extremos conferem com artigo |
| Arquivos da raiz da pasta | INVÁLIDOS (versão 524) — ver seção "Separação de versões" | extremos divergem |

### Fronteira de Pareto

| Item | Valor | Como verificado |
|------|-------|----------------|
| Arquivo | `New code/results/.../exhaustive_search_pareto.csv` | — |
| N trios Pareto | 213 | `len(par)` |
| Cost_min | 0.019594 | script verify2_mcdm.py |
| Impact_min | 0.473199 | script verify2_mcdm.py |
| Safety_max | 0.688265 | script verify2_mcdm.py |
| Best Compromise Sites | {184, 430, 460} (índices 0-based em df) | coordenadas batem ao 6.º decimal |
| Soma dos objetivos do BCS | Cost=0.0811, Impact=0.5568, Safety=0.6170 | recalculado via per_site_objectives() |

### Normalização dos objetivos

**Usar min/max dos 473** (df_real_data_cached.csv) para calcular f₁, f₂, f₃ de qualquer área.
Normalização sobre os 389 viáveis NÃO reproduz o gabarito (discrepância f₃ = 8.5e-02).
Para TOPSIS/VIKOR/PROMETHEE II: cada método normaliza internamente sobre os 389 viáveis — isso é independente da normalização dos objetivos.

### Reprodutibilidade confirmada (script verify2_mcdm.py, 27/set/2026)

```
len(df)=473  len(par)=213
Cost_min=0.019594  Impact_min=0.473199  Safety_max=0.688265  (batem com Tabela 13)
Objetivos site 184: f1=0.041376  f2=0.166243  f3=0.237913  (bate com bcs.csv ao 4.º decimal)
Soma {184,430,460}: f1=0.0811  f2=0.5568  f3=0.6170  (bate com Tabela 12)
argmin S1 na fronteira: {184, 430, 460}  ← reproduz Tabela 14
argmin SAW na fronteira: {184, 430, 460}  ← coincide neste dataset; serve como teste de unidade
Trios Pareto com área protegida: 0
nsga2_pareto_front_results.csv (pasta nova): len=150, Safety_max=0.688265  ✓
```

### SAW vs S1 — decisão de 27/set/2026 (corrigindo erro anterior do log)

O SAW com pesos AHP individuais **NÃO é equivalente ao cenário S1**:
- SAW: score por área = soma ponderada onde critérios de custo/impacto entram com (1−c̃) e segurança com c̃. Isso equivale a pesos (1, 1, 1) nos objetivos normalizados f₁, f₂, f₃.
- S1: pesos (0.295, 0.356, 0.349) por cima dos objetivos já ponderados = double weighting.
- Neste dataset, argmin SAW = argmin S1 = {184, 430, 460} por coincidência numérica, não por equivalência formal.

### Pesos AHP — registro como inferência

Os pesos da Tabela 7 do IEEE Access (urban=0.166, perm=0.152, ...) são inferidos como normalização de colunas da matriz de Andrade & Barbosa (2015), arredondados para 3 casas decimais. Com arredondamento a soma dá 0.999; o IEEE usa rivers=0.091 em vez de 0.090 (normalização exata), provavelmente para fechar a soma em 1.000. Registrado como inferência — o artigo original de Andrade & Barbosa (2015) não foi acessado para confirmar.

### aspect == -1 — resultado definitivo

- No CSV bruto (524): 41 áreas têm aspect == -1 (terreno plano, DEM = 0; causa provável: células que caem no mar ou em bordas costeiras — hipótese, não verificada diretamente).
- No df_real_data_cached (473): 0 áreas com aspect == -1.
- Causa provável: o filtro de 50% de cobertura terrestre excluiu todas as 41.
- Impacto no experimento MCDM: nenhum.
- Bug latente no script: aspect == -1 receberia norm_asp=1 (pior nota) se chegasse ao código. Corrigido no mcdm_experiment.py (aspect==-1 → 0.5). Mencionar no README do repositório, não como limitação do artigo.

### NaN nos dados — tratamento obrigatório

3 sites têm NaN em uma coluna cada (descoberto 27/set/2026):
- Site 41: `dist_roads (m)` = NaN
- Site 385: `dist_urban_core (m)` = NaN
- Site 429: `dist_aerodrome (m)` = NaN

Tratamento: `impute_nan()` substitui NaN pelo ponto médio `(min+max)/2` dos 473, no valor bruto. Isso resulta em score normalizado = 0.5 para qualquer normalização min-max. O script original usava `_safe_norm(NaN) = 0.5` diretamente; o efeito é idêntico para os objetivos (f1,f2,f3), mas a imputação no valor bruto garante que TOPSIS, VIKOR e PROMETHEE também recebam dados consistentes. Com esse tratamento, todos os 213 trios reproduzem com diff < 1e-9.

---

### Especificação do mcdm_experiment.py (decisões de 27/set/2026)

| Item | Decisão |
|------|---------|
| Alternativas | 389 viáveis (`dist_protected_area (m) > 0`) |
| Pesos | Tabela 7 do IEEE Access (soma 1.000): urban=0.166, perm=0.152, slope=0.113, aero=0.102, rivers=0.091, cult=0.081, aspect=0.075, coast=0.069, protected=0.066, wells=0.055, roads=0.030. Inferência: normalização de colunas arredondada; com arredondamento a soma dá 0.999; rivers ajustado de 0.090 para 0.091 para fechar em 1.000. |
| Sentido dos critérios | Cost (min→bom): perm, slope, roads. Impact inverso (max dist→bom): rivers, coast, protected, wells. Impact binário: aspect (90–180 = leeward = 0, else = 1, aspect==-1→0.5). Safety (max dist→bom): urban, aero, cult. |
| NaN — tratamento | `impute_nan()`: substitui NaN pelo ponto médio (min+max)/2 dos 473, no valor bruto, antes de qualquer método. Isso dá score normalizado=0.5 para qualquer normalização min-max. Sites afetados: 41 (roads), 385 (urban), 429 (aero). Todos os 3 estão nos 389 viáveis. |
| Aspect = -1 | Tratado como 0.5 (neutro). Diverge do script IEEE que trataria como 1. Nenhum dos 473 tem aspect==-1, então não afeta resultados. |
| Métodos | SAW-389 (min-max sobre 389), SAW-473 (só para teste de unidade), TOPSIS (normalização vetorial sobre 389), VIKOR (v=0.5), PROMETHEE II (critério usual — P=1 se d>0, sem threshold) |
| Trio principal | Guloso: percorrer ranking decrescente de score, aceitar área a ≥10 km das já escolhidas |
| Trio de controle | Ótimo: maximizar soma de scores entre 1.944.653 trios viáveis. SAW e TOPSIS-MM: argmax vetorizado O(M). PROMETHEE: argmax de soma de φ. |
| Cálculo (f1,f2,f3) do trio | Normalização sobre os 473 |
| Avaliação contra Pareto | in_front (trio na fronteira exaustiva), dominated (tol=1e-9), gap=max(0, max_p min_m(t_m−p_m)) |
| Concordância entre rankings | WS, r_w, Jaccard top-10/top-20. WS satura com n=389 (WS≈0.91–0.99 para todos) — usar Jaccard como métrica principal. |

### Testes de unidade (todos PASSAM em mcdm_experiment.py)

1. `max_diff(recalc_213_trios) < 1e-9` — **PASSOU** (diff=2.22e-16)
2. `n_trios_viaveis_473 == 2_904_011` — **PASSOU** (publicado no IEEE; n_viaveis_389 = 1.944.653)
3. `argmin_SAW473(fronteira) == {184, 430, 460}` — **PASSOU** — usa `saw_scores(df_all)` do script
4. `argmin_S1(1.944.653 trios viáveis) não é dominado` — **PASSOU** — trio={184,430,460}

### Resultados do experimento (mcdm_experiment.py + diag2.py, 27/set/2026)

#### Derivação: PROMETHEE II (critério usual) = SAW sobre postos

Com o critério usual (P=1 se d>0, sem threshold) e sem empates, o fluxo líquido simplifica para uma soma ponderada dos postos. Com empates (e.g., aspect binário), vale usando postos médios. Consequências: PROMETHEE e SAW têm r_w=0.923 (maior concordância entre os quatro métodos). O guloso do PROMETHEE já encontra o ótimo — os dois coincidem no mesmo trio.

#### Taxa de base

91 sites únicos nos 213 trios Pareto (todos nos 389 viáveis). Taxa de base = 91/389 = 23.4%.
Top-10 aleatório esperado = 2.3 de 10. Top-20 = 4.7 de 20.

Frequência top-k (contexto: taxa de base 2.3 aleatório de 10):

| Método | top-10 | top-20 |
|--------|--------|--------|
| PROMETHEE | 10/10 (muito acima) | 13/20 |
| SAW | 8/10 | 14/20 |
| VIKOR | 7/10 | 16/20 |
| TOPSIS vetorial | 3/10 (abaixo do aleatório!) | 8/20 |

#### Pesos efetivos nas três normalizações

| Critério | w_nom | eff_minmax | eff_vetorial | eff_postos |
|---------|-------|-----------|------------|----------|
| perm | 0.152 | 0.152 | **0.549** | 0.135 |
| slope | 0.113 | 0.113 | 0.072 | 0.136 |
| urban | 0.166 | 0.166 | 0.120 | 0.292 |
| (outros) | — | = w_nom | distorcidos | estáveis |

Mecanismo: permeabilidade tem cauda longa (0–1100 m), norma vetorial dominada por outliers. Peso efetivo de 0.152 → 0.549. O TOPSIS vetorial efetivamente ranqueia por "longe de baixa permeabilidade", ignorando os outros critérios.

#### Tabela completa de trios — gap normalizado pela amplitude da fronteira

(Fronteira: f1_range=0.1793, f2_range=0.3433, f3_range=0.4538)

| Método | Variant | IDs | f₁ | f₂ | f₃ | in_front | dom | gap_norm |
|--------|---------|-----|------|------|------|---------|-----|---------|
| SAW | greedy | {184,279,320} | 0.1273 | 0.5963 | 0.6207 | False | Y | 0.0394 |
| SAW | optimal | {184,430,460} | 0.0811 | 0.5568 | 0.6170 | **True** | N | 0.0000 |
| TOPSIS-vn | greedy | {233,320,355} | 0.1113 | 0.5669 | 0.5358 | False | Y | 0.0605 |
| TOPSIS-vn | optimal | {227,233,345} | 0.0865 | 0.5955 | 0.5715 | False | Y | 0.0345 |
| TOPSIS-mm | greedy | {184,227,460} | 0.1104 | 0.6712 | 0.6883 | **True** | N | 0.0000 |
| TOPSIS-mm | optimal | {184,227,460} | 0.1104 | 0.6712 | 0.6883 | **True** | N | 0.0000 |
| VIKOR | greedy | {233,279,320} | 0.1190 | 0.5819 | 0.5879 | False | Y | 0.0642 |
| PROMETHEE | greedy | {51,233,345} | 0.0447 | 0.5900 | 0.4852 | **True** | N | 0.0000 |
| PROMETHEE | optimal | {51,233,345} | 0.0447 | 0.5900 | 0.4852 | **True** | N | 0.0000 |
| BCS_IEEE | ref | {184,430,460} | 0.0811 | 0.5568 | 0.6170 | **True** | N | 0.0000 |

**Conclusão central sustentada pelos dados:** com normalização min-max (SAW, PROMETHEE, TOPSIS-mm), os métodos encontram trios Pareto-ótimos. O TOPSIS vetorial não encontra o ótimo nem com enumeração (gap_norm=0.035). O mecanismo é a distorção de escala da permeabilidade. A afirmação "inteiramente" foi moderada para "principalmente" — resta verificar se há outros datasets onde a normalização vetorial não distorce assim.

#### Robustez à exclusão dos sites NaN

Retirando {41, 385, 429}: todos os trios greedy permanecem idênticos. Resultados robustos à imputação.

#### Concordância entre rankings (n=389)

| Par | r_w | WS(A→B) | WS(B→A) | Jac@10 | Jac@20 |
|-----|-----|---------|---------|--------|--------|
| SAW vs TOPSIS | 0.774 | 0.917 | 0.975 | 0.11 | 0.18 |
| SAW vs VIKOR | 0.762 | 0.994 | 0.996 | 0.54 | 0.54 |
| SAW vs PROMETHEE | 0.923 | 0.989 | 0.992 | 0.43 | 0.60 |
| TOPSIS vs VIKOR | 0.729 | 0.949 | 0.951 | 0.05 | 0.14 |
| TOPSIS vs PROMETHEE | 0.861 | 0.906 | 0.955 | 0.05 | 0.11 |
| VIKOR vs PROMETHEE | 0.752 | 0.993 | 0.992 | 0.33 | 0.48 |

WS satura com n=389. Usar Jaccard como métrica principal.

### Monte Carlo de pesos (monte_carlo.py v3, 27/set/2026 — CORRIGIDO)

**Bug da v1 (DESCARTADO):** v1 usava normalização 389 para scores mas avaliava dominância contra os 213 trios fixos (pesos AHP). Com pesos sorteados, o resultado era inconsistente. v3 usa dominância contra 1,944,653 trios com `compute_objectives(df_via, df_imp)` (normalização 473, pesos AHP fixos). Inclui variante ótima via argmax vetorizado. 4/4 PASS no teste de regressão.

**Definição v3:** dado um sorteio de pesos w, o trio selecionado pelo método é Pareto-ótimo no espaço A original (pesos AHP, normalização 473)?

Dirichlet(α·w_AHP), α ∈ {50, 200}, 500 sorteios, semente 42.

| Método | α | % não dom | med gap_norm | Jac@10 vs SAW |
|--------|---|-----------|-------------|---------------|
| SAW ótimo | 50 | 74.6% | 0.000 | 1.000 |
| SAW ótimo | 200 | **82.2%** | 0.000 | 1.000 |
| PROMETHEE greedy | 50 | 45.4% | 0.007 | 0.480 |
| PROMETHEE greedy | 200 | 54.6% | 0.000 | 0.446 |
| SAW greedy | 50 | 49.8% | 0.000 | 1.000 |
| SAW greedy | 200 | 42.2% | 0.024 | 1.000 |
| TOPSIS-MM greedy | 50 | 38.8% | 0.000 | 0.580 |
| TOPSIS-MM greedy | 200 | 32.2% | 0.000 | 0.616 |
| VIKOR greedy | 50 | 25.6% | 0.023 | 0.509 |
| VIKOR greedy | 200 | 29.6% | 0.023 | 0.526 |

**Interpretações moderadas:**
- SAW ótimo 82% com α=200 — consistente com P1 (linearidade no espaço A). Não é 100% porque normalização 389 dos scores diverge ligeiramente da normalização 473 dos objetivos quando os pesos mudam.
- PROMETHEE greedy 54% com α=200 — resultado empírico, **não estrutural**. P2 mostra que PROMETHEE é linear nos postos, não nos valores. P1 não se aplica diretamente.
- TOPSIS-VN não incluído nesta rodada (adicionar na próxima).

### Espaço de avaliação B v2 (space_b_v2.py, 27/set/2026 — REDEFINIDO E CORRIGIDO)

**B v1 descartado** (media de urban_norm era aditiva e media basicamente safety — circularidade com B3).

**B v2:**
- **B1** = f1(T) = soma f1 (custo aditivo — âncora comparável com espaço A)
- **B2** = max_i f2(i) = pior impacto ambiental (gargalo, não aditivo)
- **B3** = min_i f3(i) = gargalo de segurança (não aditivo)

P1 não se aplica a B2 e B3 — elimina a circularidade.

Algoritmo: `paretoset` (O(M log M), 0.08s). **VALIDADO PASS vs força bruta N=80 (14.327 trios).**

**Fronteira B v2:** 108 trios. A∩B = 33 trios.

| Label | B1_cost | B2_worst | B3_min_s | in_B |
|-------|---------|---------|---------|------|
| SAW greedy | 0.1273 | 0.2890 | 0.1570 | False |
| SAW optimal | 0.0811 | 0.2224 | 0.1542 | False |
| TOPSIS-VN greedy | 0.1113 | 0.2741 | 0.1570 | False |
| TOPSIS-VN optimal | 0.0865 | 0.2826 | 0.1409 | False |
| **TOPSIS-MM greedy** | 0.1104 | 0.2826 | **0.2249** | **True** |
| VIKOR greedy | 0.1190 | 0.2890 | 0.1570 | False |
| PROMETHEE greedy | 0.0447 | 0.2771 | 0.1392 | False |
| BCS_IEEE | 0.0811 | 0.2224 | 0.1542 | False |

TOPSIS-MM greedy é Pareto-ótimo em B porque tem B3=0.225 — gargalo de segurança máximo entre os canônicos. O trio {184,227,460} está no extremo de alta segurança. Não é vantagem metodológica — é posição na fronteira.

### Posição dos trios na fronteira A e importância dos critérios (diag_position.py)

Ideal A = (0.020, 0.473, 0.688). Nadir A = (0.199, 0.816, 0.234).
rS negativo significa que o trio supera o ideal em Safety da fronteira.

| Label | rCost | rImpact | rSafety | Região |
|-------|-------|---------|---------|--------|
| SAW greedy | 0.601 | 0.359 | −0.149 | extremo alta segurança |
| SAW optimal | 0.343 | 0.244 | −0.157 | extremo alta segurança |
| TOPSIS-MM greedy | 0.506 | 0.577 | 0.000 | extremo alta segurança |
| VIKOR greedy | 0.554 | 0.317 | −0.221 | extremo alta segurança |
| **PROMETHEE greedy** | **0.140** | 0.340 | **−0.447** | **extremo baixo custo** |

Importância w_j × std(r_j) normalizado:
- urban: 0.197 (maior)
- aspect: 0.148 (2º)
- perm: 0.059 (menor — apesar de w_nom=0.152, baixíssima variância nos 389 viáveis)
- urban/perm ratio: 3.33× nesta métrica

### Decisão editorial: experimento de 2022 vs novo experimento (27/set/2026)

O artigo original (2022) ranqueava os 11 critérios de Andrade & Barbosa (2015) usando AHP, TOPSIS e PROMETHEE II — não áreas candidatas. O novo experimento ranqueia 389 áreas candidatas reais e avalia os trios resultantes contra a fronteira de Pareto exaustiva do IEEE Access (2026).

**Decisão:** o experimento de 2022 (ranqueamento de critérios) vira um parágrafo de contexto histórico na Introdução ou Materiais. Não entra nos Resultados. O artigo novo é sobre o experimento de localização de aterros.

**Pendências antes de reescrever o artigo:**
1. ~~Monte Carlo (Dirichlet sobre pesos)~~ — feito (v3), resultados válidos
2. ~~Espaço B~~ — feito (v2), validado
3. Verificar Brito (2020) para "40 thousand tons"
4. Obter PDF de Andrade & Barbosa (2015) para confirmar nome e pesos

### Nome de Andrade — NÃO CONFIRMADO

O nome "Alex Jaison Barbosa Andrade" aparece em algumas seções do log mas não foi verificado em nenhum documento primário. Remover de qualquer texto do artigo até confirmar.

---


| Método | α | % não dominado | mediana gap_norm | Jaccard@10 vs SAW |
|--------|---|--------------|----------------|------------------|
| PROMETHEE greedy | 50 | **100%** | 0.000 | 0.115 |
| PROMETHEE greedy | 200 | **100%** | 0.000 | 0.116 |
| SAW greedy | 50 | 74.6% | 0.000 | 1.000 |
| SAW greedy | 200 | 97.4% | 0.000 | 1.000 |
| TOPSIS-MM greedy | 50 | 54.4% | 0.000 | 0.263 |
| TOPSIS-MM greedy | 200 | 68.2% | 0.000 | 0.247 |
| VIKOR greedy | 50 | 34.0% | 0.030 | 0.237 |
| VIKOR greedy | 200 | 46.4% | 0.030 | 0.227 |
| TOPSIS-VN greedy | 50 | 7.4% | 0.060 | 0.145 |
| TOPSIS-VN greedy | 200 | **0.6%** | 0.060 | 0.092 |

**⚠️ DADOS DESATUALIZADOS — Monte Carlo v1 com bug. Ver versão corrigida acima (monte_carlo.py v3). Os números abaixo são INVÁLIDOS.**

**Interpretações verificadas:**
- PROMETHEE greedy = 100% não dominado em qualquer vetor de pesos plausível. Não é sorte do vetor AHP — é estrutural (P2: PROMETHEE = SAW sobre postos; postos são mais robustos a outliers do que valores brutos).
- TOPSIS-VN dominado em 99.4% dos sorteios com α=200. O mecanismo P3 (distorção de pesos efetivos pela permeabilidade) é robusto a variações de pesos.
- TOPSIS-MM melhor que VN (54% vs 7% com α=50), mas ainda sem garantia do greedy. P4 em ação.
- α=200 (pesos próximos ao AHP) produz resultados mais extremos que α=50 (pesos dispersos): SAW 97% vs 75%, TOPSIS-VN 0.6% vs 7.4%.

**Manchete sustentada:** "Normalização importa mais que método — e importa em qualquer vetor de pesos plausível, não apenas no vetor AHP original."

### Espaço de avaliação B (space_b.py, 27/set/2026)

Três objetivos não aditivos (todos para maximizar):
- **B1** = min safety score entre os k locais (gargalo do pior site)
- **B2** = menor distância entre pares (km) — dispersão mínima do trio
- **B3** = média urban_norm dos 3 sites — acesso ambiental médio

Fronteira exata B: **51 trios** (vs 213 no espaço A). Algoritmo Kung 3D via sweep de candidatos — 19 segundos total.

**Estatísticas da fronteira B:**
- B1 range: [0.131, 0.644]
- B2 range: [10.76, 21.98] km
- B3 range: [0.182, 0.701]
- Sites únicos: 53 (vs 91 no espaço A)
- Trios em A∩B: apenas **4** de 213+51

#### Avaliação dos trios canônicos no Espaço B

| Label | B1_min | B2_km | B3_urb | in_front_B |
|-------|--------|-------|--------|------------|
| SAW greedy | 0.4498 | 10.24 | 0.5582 | False |
| SAW optimal | 0.4419 | 10.69 | 0.5243 | False |
| TOPSIS-VN greedy | 0.4498 | 10.09 | 0.4050 | False |
| TOPSIS-VN optimal | 0.4038 | 10.33 | 0.5046 | False |
| **TOPSIS-MM greedy** | **0.6443** | **10.76** | **0.6917** | **True** |
| VIKOR greedy | 0.4498 | 10.24 | 0.5017 | False |
| PROMETHEE greedy | 0.3988 | 10.73 | 0.4454 | False |
| BCS_IEEE | 0.4419 | 10.69 | 0.5243 | False |

**Inversão de conclusão no espaço B:**

No espaço A (aditivo): PROMETHEE greedy = 100% Pareto-ótimo, SAW optimal = sempre Pareto-ótimo por P1, TOPSIS-VN = pior.

No espaço B (não aditivo): **TOPSIS-MM greedy** é o único método canônico Pareto-ótimo. PROMETHEE greedy não está na fronteira B. SAW optimal também não.

**Interpretação crítica:**
- No espaço B, o gargalo (B1 = min safety) privilegia trios com o pior site mais seguro. O trio TOPSIS-MM {184,227,460} tem B1=0.644 — o site 184 tem a safety mais alta do dataset.
- P1 não se aplica em B (objetivos não aditivos), confirmando a necessidade do espaço B para eliminar a circularidade.
- A conclusão "normalização importa mais que método" **se mantém** em B no sentido de que TOPSIS-MM (min-max) supera TOPSIS-VN em ambos os espaços. Mas a *ordem* dos outros métodos inverte.
- Este resultado é publicável: mostra que a vantagem de métodos lineares no espaço A é estrutural (P1), e no espaço B a hierarquia muda completamente.

**Sobreposição A∩B = 4 trios**: fronteiras A e B avaliam estruturas radicalmente diferentes do problema. Não são substituíveis.

Salvo em `scripts/results/pareto_front_B.csv` e `space_b_canonical.csv`.

---

### Decisão editorial: experimento de 2022 vs novo experimento (27/set/2026)

O artigo original (2022) ranqueava os 11 critérios de Andrade & Barbosa (2015) usando AHP, TOPSIS e PROMETHEE II — não áreas candidatas. O novo experimento ranqueia 389 áreas candidatas reais e avalia os trios resultantes contra a fronteira de Pareto exaustiva do IEEE Access (2026).

**Decisão:** o experimento de 2022 (ranqueamento de critérios) vira um parágrafo de contexto histórico na Introdução ou Materiais. Não entra nos Resultados. O artigo novo é sobre o experimento de localização de aterros.

**Justificativa:**
1. O ranqueamento de critérios não produz uma conclusão generalizável — qualquer método linear vai convergir quando aplicado à mesma matriz AHP.
2. O novo experimento tem uma pergunta de pesquisa verificável: métodos MCDM identificam áreas Pareto-ótimas? A resposta depende da normalização, não do método em si.
3. O título sugerido captura a contribuição: "Normalization matters more than method: benchmarking MCDM rankings against an exact Pareto front for multi-site landfill selection."

**Estrutura sugerida:**
- Introdução: lacuna (MCDM raramente validado contra fronteira exata)
- Materiais e Métodos: 389 áreas; pesos AHP; 4 métodos com tabela de normalizações; derivação PROMETHEE=SAW sobre postos; formação de trios; avaliação (in_front, dom, gap_norm); concordância (Jaccard)
- Resultados: tabela de trios; pesos efetivos; frequência top-k; concordância
- Discussão: normalização pesa mais que família do método; limitação por construção (avaliação aditiva favorece lineares); papel do guloso
- Conclusão

**Pendências antes de reescrever o artigo:**
1. Análise de sensibilidade Monte Carlo (Dirichlet sobre pesos, 500 sorteios)
2. Verificar Brito (2020) para "40 thousand tons"
3. Obter PDF de Andrade & Barbosa (2015) para confirmar nome e pesos

### Nome de Andrade — NÃO CONFIRMADO

O nome "Alex Jaison Barbosa Andrade" aparece em algumas seções do log mas não foi verificado em nenhum documento primário. Registrar como não confirmado até ter acesso ao PDF de Andrade & Barbosa (2015). Remover de qualquer texto do artigo.

---

## Histórico das Sessões



**Artigo:** Comparison between Multi-Criteria Decision-Making Methods to support the determination of sites for the construction of a landfill
**Autor:** Julio L. Azancort Neto (UFPA, 2022)
**Diretório do projeto:** `G:\Faculdade\Estudo\Mestrado\2022.1\Trabalhos\Multicriterio\`
**Pasta de trabalho:** `03-latex\paper - Comparison between MCDM Methods for Landfill Site Selection\`

---

## Artigos em 05-referencia — Seus Artigos Publicados (usar como contexto e referências)

Todos os artigos são seus e usam os dados de Andrade & Barbosa (2015) como base. Formam uma linha de pesquisa coerente sobre aterro sanitário na Ilha do Fogo + aplicações de IA/otimização em resíduos sólidos.

### 1. Costa et al. (2020) — `dorlivete,+e6939109013.pdf`
**Título:** As dimensões das Modelagens Matemática e Computacional prescrevidas à Gestão Ambiental
**Revista:** Research, Society and Development, v.9, n.10, e6939109013, 2020
**DOI:** 10.33448/rsd-v9i10.9013
**O que faz:** Aplica o Método de Cramer e o Método dos Pontos Interiores (Prime-dual / MATLAB) à matriz de comparação de Andrade & Barbosa (2015). Encontra a Solução Convencional e a Solução Ótima para os pesos dos critérios. Você é coautor (10%).
**Relevância para o artigo MCDM:** É o paper "pai" — foi o primeiro a processar matematicamente a matriz de Andrade & Barbosa. Deve ser citado no artigo como trabalho predecessor.
**BibTeX key:** `Costa2020` (já no .bib do artigo)

### 2. Azancort Neto et al. (2021) — `dorlivete,+e212101018841 (1).pdf`
**Título:** Artificial Intelligence implemented to recognize patterns of sustainable areas by evaluating the database of socioenvironmental safety restrictions
**Revista:** Research, Society and Development, v.10, n.10, e212101018841, 2021
**DOI:** 10.33448/rsd-v10i10.18841
**O que faz:** Usa Árvore de Decisão (RapidMiner) sobre cenários gerados a partir da matriz de Andrade & Barbosa (2015), criando novos cenários via média aritmética, média geométrica e desvio padrão. Accurácias de até 100% na classificação de aptidão (HIGH/MEDIUM/LOW). Você é primeiro autor.
**Relevância para o artigo MCDM:** É o paper "irmão" — mesmo dataset, abordagem diferente (IA vs MCDM). Já citado no artigo como `Azancort2021`.
**BibTeX key:** `Azancort2021` (já no .bib do artigo)

### 3. Azancort Neto et al. (2026) — `Landfill_Site_Allocation_Multi-Objective_Optimization_With_NSGA-II...pdf`
**Título:** Landfill Site Allocation Multi-Objective Optimization With NSGA-II: A Case Study on Fogo Island, Cape Verde
**Revista:** IEEE Access, v.14, 2026
**DOI:** 10.1109/ACCESS.2026.3697915
**O que faz:** Aplica GIS + NSGA-II para selecionar k=3 locais ótimos para aterro na Ilha do Fogo, com 3 objetivos conflitantes (custo, impacto ambiental, segurança social). Validado por Exhaustive Search — captura 99,50% do hipervolume do Pareto front real. Usa a matriz de pairwise comparison de Andrade & Barbosa como base para os pesos AHP. Você é primeiro autor.
**Relevância para o artigo MCDM:** É o paper mais recente e mais forte da série. Otimizou a localização de k=3 aterros simultaneamente (não ranqueou áreas individualmente). Fornece a matriz de decisão (473 candidatos × 11 critérios) e a fronteira exaustiva de 213 trios Pareto. Esses dados permitem que o artigo MCDM aplique SAW, TOPSIS, VIKOR e PROMETHEE II e compare os trios resultantes com a fronteira.
**Dados disponíveis:** Repositório GitHub: https://github.com/Jazancort/NSGA2-GIS-Landfill-Optimization-Cape-Verde | Zenodo: https://zenodo.org/records/17704387
**BibTeX key:** `AzancortNeto2026` — **NOVA REFERÊNCIA, adicionar ao .bib**

### 4. Azancort Neto et al. (2024) — `29423-421-23864-1-10-20240711 (1).pdf`
**Título:** Advanced Single-View Image-Based Framework for Volume Estimation in Urban Solid Waste Management
**Evento:** WCAMA 2024 (Workshop de Computação Aplicada a Gestão do Meio Ambiente e Recursos Naturais)
**O que faz:** Metodologia de estimativa de volume de resíduos sólidos em sacolas plásticas usando segmentação de instâncias (Mask R-CNN) + estimativa de profundidade monocular + point cloud. MAPE de 15,92% (single) e 11,49% (multiple). Você é primeiro autor.
**Relevância para o artigo MCDM:** Linha de pesquisa paralela (CV/IA para resíduos), não cita Andrade & Barbosa diretamente. Pouco relevante para o artigo MCDM — mencionar apenas no contexto geral.
**BibTeX key:** `AzancortNeto2024volume` — **NOVA REFERÊNCIA, adicionar ao .bib se necessário**

### 5. Azancort Neto et al. (2024b) — `29433-421-23874-1-10-20240711 (1).pdf`
**Título:** WasteInsight: Conjunto de Dados para Detecção e Estimativa de Volume de Resíduos Sólidos Urbanos
**Evento:** WCAMA 2024
**O que faz:** Apresenta o dataset "WasteInsight" com 447 imagens de sacolas de lixo em ambientes residenciais, disponível no Mendeley Data (DOI: 10.17632/p8n7nbxyw3.1). Você é primeiro autor.
**Relevância para o artigo MCDM:** Mínima — dataset para detecção por imagem, não relacionado aos métodos MCDM.
**BibTeX key:** `AzancortNeto2024dataset` — **NOVA REFERÊNCIA, adicionar ao .bib se necessário**

---

### Implicações para o Artigo MCDM

O paper do IEEE Access (2026) muda o contexto do artigo MCDM de forma importante:

1. **O artigo MCDM é complementar ao IEEE Access 2026**: o MCDM (2022) compara métodos de ponderação de critérios usando os dados de Andrade & Barbosa; o IEEE Access (2026) aplica esses pesos na otimização multiobjetivo real de localização. São trabalhos de períodos diferentes (2022 e 2026) que convergem para a mesma linha de pesquisa. A versão revisada do MCDM usa os dados do IEEE como validação externa.

2. **O IEEE Access 2026 fornece o dataset e a fronteira de Pareto**: ele otimizou a localização de k=3 aterros simultaneamente (não ranqueou áreas individualmente). O que ele fornece é a matriz de decisão (473 candidatos × 11 critérios) e a fronteira exaustiva de 213 trios. Esses dados permitem que o artigo MCDM aplique SAW, TOPSIS, VIKOR e PROMETHEE II individualmente e compare os trios resultantes com a fronteira.

3. **Sequência da linha de pesquisa:**
   - Andrade & Barbosa (2015) → define critérios e pesos por AHP + GIS
   - Costa et al. (2020) → otimização matemática da matriz de critérios (Cramer + Pontos Interiores)
   - Azancort Neto et al. (2021) → Árvore de Decisão sobre os cenários
   - **Artigo MCDM (2022)** → comparação de AHP, TOPSIS, PROMETHEE II nos critérios
   - Azancort Neto et al. (2026, IEEE Access) → NSGA-II para localização de aterro com múltiplos objetivos

4. **Correção do erro da tonelagem**: o texto do artigo MCDM cita "40 thousand tons per day" para Belém/RMB. Essa estatística vem de Brito (2020) — verificar o valor original no PDF. A dissertação de Sousa (2022) refere "cerca de 2 mil toneladas de lixo por dia" para Belém/RMB, o que é mais plausível. O IEEE Access 2026 não cita essa estatística. A correção no main.tex foi para "per month" com % TODO até confirmar Brito (2020).

---

## Artefatos Gerados Nesta Sessão

| Arquivo | Descrição |
|---|---|
| `03-latex/paper - .../main.tex` | Artigo completo reformatado para Elsevier CAS double-column (cas-dc) |
| `03-latex/paper - .../refs.bib` | 42 entradas BibTeX de todas as referências do artigo completo |
| `03-latex/paper - .../analysis.md` | Análise crítica do artigo v2 (com correções da revisão externa) |
| `03-latex/paper - .../improvement-plan.md` | Plano de melhoria v2 com Fase 0 e todos os erros corrigidos |
| `03-latex/paper - .../session-log.md` | Este arquivo |

**Arquivos de classe copiados para `03-latex/paper - .../`:**
- `cas-dc.cls`, `cas-common.sty`, `cas-model2-names.bst`

**Estrutura de pastas reorganizada:**
```
Multicriterio/
├── 01-tarefas/       ← pptx/pdf de tarefas e apresentações
├── 02-artigo/        ← versões .docx/.pdf do artigo
├── 03-latex/         ← projeto LaTeX + código Python
│   ├── paper - Comparison between MCDM Methods.../
│   ├── MCDM-final-paper/   (repositório git)
│   ├── MCDM-final-paper-Final/
│   └── algorithm/
├── 04-template/      ← els-cas-templates.zip + pasta extraída
└── 05-referencia/    ← artigos externos de referência
```

---

## Decisão sobre Versão do Artigo

O arquivo mais completo é **`Final v1/Artigo Final - MCDM - Completo.docx`** (jun/2022), não o "Final Final" (jul/2022):
- Tem as equações explícitas das seções AHP (Eq.1–2), TOPSIS (Eq.3–7) e PROMETHEE II (Eq.8–12)
- Tem a Tabela 3 separada com os 11 critérios e suas descrições
- Tem 8 referências a mais (Sener 2010, Pinheiro 2019, Erbas 2018, Liu 2014, Papathanasiou 2018, Srdjevic 2004, Yazdani 2015, Ho 2010)
- Tem uma conclusão mais desenvolvida

O "Final Final" é mais recente por data mas tem conteúdo mais enxuto — provavelmente uma versão resumida para entrega.

---

## Análise Crítica — Resumo dos Pontos Principais

### Problema Central (detectado via revisão externa com verificação numérica independente)

**O desenho experimental é circular.** TOPSIS e PROMETHEE II foram aplicados à matriz de comparação par a par do AHP, usando os pesos derivados dessa mesma matriz. Os três métodos processam a mesma informação. A alta concordância observada é esperada por construção, não é evidência de convergência metodológica independente.

Consequência direta:
- SAW como baseline vai reproduzir o AHP pela propriedade $A \cdot w = \lambda_{max} \cdot w$
- Análise de sensibilidade dos pesos do AHP não faz sentido no desenho atual
- Os coeficientes de correlação (Fase 1) confirmam circularidade, não robustez

### Coeficientes Calculados (verificados independentemente)

| Par | Spearman ρ | Kendall τ | r_w | WS (A→B / B→A) |
|---|---|---|---|---|
| AHP–TOPSIS | 0,936 | 0,818 | 0,921 | 0,873 / 0,869 |
| AHP–PROMETHEE II | 0,964 | 0,891 | 0,955 | 0,961 / 0,950 |
| TOPSIS–PROMETHEE II | 0,945 | 0,855 | 0,942 | 0,906 / 0,908 |
| **Kendall W** | **0,966** | χ²(10)=28,97 | **p=0,0013** | — |

Linha de base aleatória (100k sorteios, percentil 95): ρ=0,53, WS=0,80, W=0,55.

### Verificação Numérica do Artigo

| Item | Resultado |
|---|---|
| λ_max / CI / CR | 11,853 / 0,085 / 0,057 (consistente, CR < 0,10) |
| Pesos AHP | Calculados por aproximação (média das colunas normalizadas, Eq.2), não autovetor exato. Soma = 0,996. Rankings idênticos. |
| TOPSIS | Reproduzido. x₁=0,7352 truncado para 0,73 em vez de arredondado (0,74). |
| PROMETHEE II | Reproduzido, diferenças ~0,002 por normalização dos pesos. |
| % posições idênticas (Tabela 5) | Todos corretos. |

### Erros Factuais no Artigo

1. **"40 thousand tons per day"** para Belém/RM — quase certamente errado (São Paulo gera ~20k t/dia). Provavelmente t/mês ou t/ano. Verificar em Brito (2020).
2. **7 vs. 9 critérios** — texto diz 7, Tabela 6 diz 9. Inconsistente. Saaty & Ozdemir (2003) falam em 7±2.
3. **"Raises doubts about AHP"** — CR=0,057 não sustenta esta afirmação para este experimento específico.
4. **Complexidade "Low" para AHP** — contradiz a descrição no texto (autovalores, autovetores). Mudar para "Medium".
5. **Fonte Tabela 1** — atribuída a Costa (2020), deveria ser Andrade & Barbosa (2015).
6. **x₄ e x₁₀ como "menos importantes"** — Área Protegida e Poços são tipicamente restrições de exclusão, não critérios de classificação. Requer discussão adicional.

### Erros no Plano de Melhoria v1 (corrigidos na v2)

- Fórmula de r_w estava errada com autocorreção no meio do texto. Corrigida com Pinto da Costa & Soares (2005).
- "Sałabun et al. (2020) — JÁ NO ARTIGO" era parcialmente incorreto: o artigo cita Sałabun Symmetry (2020) mas não aplica os coeficientes nem cita Sałabun & Urbaniak ICCS (2020).
- Graus de liberdade errados (n vs n-2 para Spearman, n-1 para χ²).
- Rank reversal no PROMETHEE II — a afirmação de maior estabilidade estava incorreta (Mareschal et al. 2008).
- Código com `pass` no Monte Carlo, `diff` não usado em `perturb_weights`, API pyDecision incorreta para VIKOR e PROMETHEE.
- Scores de publicabilidade numéricos sem base — removidos.
- DOIs de referências 2025–2026 não verificados independentemente — sinalizados com aviso.

---

## Fase 0 — Achados da Busca de Datasets

### Andrade & Barbosa (2015)

- **Localizado:** Revista de Geografia UFPE, v.32 n.2 (2015), ID 229156
- **URL:** https://periodicos.ufpe.br/revistas/revistageografia/article/view/229156
- **Status:** PDF bloqueado por autenticação do portal UFPE
- **O que sabemos:** O artigo usa AHP + SIG para ranquear **áreas candidatas** na Ilha do Fogo, Cabo Verde — é o problema correto para o Caminho A
- **O que precisamos:** Acesso ao PDF para extrair a decision matrix (pontuações das áreas por critério)
- **Como resolver:** login UFPE, cópia física do artigo, ou contato com o autor de Andrade & Barbosa (2015) — nome não confirmado.

### Sodré et al. (2020) — via Sousa (2022) UFPA

**Dataset completo disponível em acesso aberto.**

A dissertação de TCC de Tiago Marinho Pedroso Sousa (UFPA, 2022) analisa 7 áreas candidatas do CONCISSS (Consórcio de Castanhal/PA) usando a metodologia de Sodré et al. (2020): NBR 13.896 + matriz de ponderação de Krebs/Monteiro.

**Referência:**
> Sousa, T. M. P. (2022). *Avaliação do meio físico como ferramenta para a seleção adequada de área para instalação de aterro sanitário municipal: estudo de caso do CONCISSS, região nordeste do Estado do Pará.* TCC, UFPA.
> URI: https://bdm.ufpa.br/jspui/handle/prefix/7320
> PDF: https://bdm.ufpa.br/server/api/core/bitstreams/99621725-e5ef-4515-ab7f-c696515bab84/content

---

## Dataset — Sousa (2022) ⚠️ DADOS NÃO VERIFICADOS

> **ATENÇÃO:** Os dados abaixo foram transcritos por OCR/leitura do PDF do TCC. Uma revisão
> independente detectou **divergência numérica** entre a Tabela 30 e a Tabela 31 do mesmo TCC.
> Os dados **não devem ser usados em código ou experimentos sem verificação manual no PDF original.**
>
> **Divergência detectada (setembro/2026):**
> A soma ponderada calculada a partir da Tabela 30 transcrita difere da Tabela 31 para 6 das 7 áreas:
>
> | Área | Soma calculada (Tabela 30) | Tabela 31 original | Diferença |
> |------|---------------------------|-------------------|-----------|
> | 1    | 74                        | 85                | −11       |
> | 2    | 66                        | 73                | −7        |
> | 3    | 61                        | 68                | −7        |
> | 4    | 66                        | 58,5              | +7,5      |
> | 5    | 60                        | 65                | −5        |
> | 6    | 64                        | 59                | +5        |
> | 7    | 64                        | 63                | +1        |
>
> A pontuação 85 para a Área 1 só seria consistente se ela atendesse 100% em todos os 14 critérios,
> o que contradiz a Tabela 30 (50% em condutividade, sistemas viários, infraestrutura e acesso).
>
> **Causas possíveis:** erro de OCR, uso de escala diferente de pontuação (o valor 58,5 sugere
> que pode haver níveis além de 0/50/100%), ou inconsistência no próprio TCC.
>
> **Ação necessária:** verificar manualmente no PDF original em
> https://bdm.ufpa.br/server/api/core/bitstreams/99621725-e5ef-4515-ab7f-c696515bab84/content
>
> **Nota adicional:** Sousa (2022) é um TCC de graduação em Geologia, não uma dissertação de mestrado.
> Mesmo com dados corretos, apresenta limitações estruturais para o artigo:
> - 9 dos 14 critérios têm valor idêntico em todas as 7 áreas → não discriminam alternativas → divisão por zero em VIKOR
> - Valores em apenas 3 níveis (0, 0.5, 1) → muitos empates → coeficientes de concordância pouco informativos
> - Pesos não derivados de AHP (são pesos ordinais da NBR 13.896) → AHP como método de ranqueamento inaplicável
> - SAW com esses pesos reproduz o método original (Krebs/Monteiro) → não serve como baseline independente

### Critérios, Pesos e Hierarquia (Tabela 29 de Sousa 2022)

| Critério | Prioridade | Peso |
|---|---|---|
| Distância mínima dos cursos d'água | 1 | 10 |
| Distância mínima dos núcleos populacionais | 1 | 10 |
| Distância de aeroportos | 1 | 10 |
| Condutividade hidráulica do solo | 1 | 10 |
| Área de Proteção Permanente (APP) | 1 | 10 |
| Distância satisfatória dos sistemas viários | 2 | 6 |
| Distância dos centros de coleta | 2 | 6 |
| Baixo investimento com infraestrutura | 3 | 4 |
| Vida útil mínima | 3 | 4 |
| Textura do solo (material de cobertura) | 3 | 4 |
| Declividade | 4 | 3 |
| Conteúdo mineralógico | 4 | 3 |
| Uso do solo | 4 | 3 |
| Acesso a veículos pesados | 5 | 2 |

**Peso máximo total:** 85 pontos

### Decision Matrix — % de Atendimento por Área e Critério (Tabela 30 de Sousa 2022)

```
Critério                      | Peso | A1   | A2   | A3   | A4   | A5   | A6   | A7
------------------------------|------|------|------|------|------|------|------|------
Dist. cursos d'água           |  10  | 100% | 100% | 100% | 100% | 100% | 100% | 100%
Dist. núcleos populacionais   |  10  | 100% |  50% |  50% | 100% |  50% |  50% |  50%
Dist. aeroportos              |  10  | 100% | 100% | 100% | 100% | 100% | 100% | 100%
Condutividade hidráulica      |  10  |  50% |  50% |   0% |   0% |   0% |  50% |  50%
APP                           |  10  | 100% | 100% | 100% | 100% | 100% | 100% | 100%
Dist. sistemas viários        |   6  |  50% |  50% |  50% |  50% | 100% |  50% |  50%
Dist. centros de coleta       |   6  | 100% |  50% |  50% |  50% |  50% |  50% |  50%
Infraestrutura (investimento)  |   4  |  50% |  50% |  50% |  50% |  50% |  50% |  50%
Vida útil mínima              |   4  | 100% | 100% | 100% | 100% |   0% |  50% |  50%
Textura do solo               |   4  | 100% | 100% | 100% | 100% | 100% | 100% | 100%
Declividade                   |   3  | 100% | 100% | 100% | 100% | 100% | 100% | 100%
Conteúdo mineralógico         |   3  | 100% | 100% | 100% | 100% | 100% | 100% | 100%
Uso do solo                   |   3  | 100% | 100% | 100% | 100% | 100% | 100% | 100%
Acesso a veículos pesados     |   2  |  50% |  50% |  50% |  50% |  50% |  50% |  50%
```

> Nota: 100% = atendimento total, 50% = atendimento parcial, 0% = não atendido.
> Área 3, 4 e 5 têm critério eliminatório (condutividade = 0%).

### Pontuações Finais (Tabela 31 de Sousa 2022)

| Área | Pontuação bruta | % | Classificação |
|---|---|---|---|
| Área 1 | 85 | 100% | Favorável |
| Área 2 | 73 | 86% | Favorável |
| Área 3 | 68 | 80% | Medianamente Favorável* |
| Área 4 | 58,5 | 69% | Desfavorável |
| Área 5 | 65 | 76% | Desfavorável |
| Área 6 | 59 | 69% | Medianamente Favorável |
| Área 7 | 63 | 74% | Medianamente Favorável |

> *Área 3 tem critério eliminatório (condutividade = 0) — classificada desfavorável apesar do % ≥ 80%.
> Critério: favorável ≥ 80% sem eliminatório; medianamente favorável 60–80% sem eliminatório; desfavorável < 60% ou com eliminatório.

### Decision Matrix em Formato Python (pronto para uso)

```python
import numpy as np

# Critérios (14) e pesos (Tabela 29 de Sousa 2022, via NBR 13.896)
CRITERIA = [
    'Dist_agua',       # w=10
    'Dist_nucleos',    # w=10
    'Dist_aeroporto',  # w=10
    'Condutividade',   # w=10
    'APP',             # w=10
    'Dist_viarios',    # w=6
    'Dist_coleta',     # w=6
    'Infraestrutura',  # w=4
    'Vida_util',       # w=4
    'Textura',         # w=4
    'Declividade',     # w=3
    'Mineralogia',     # w=3
    'Uso_solo',        # w=3
    'Acesso',          # w=2
]

WEIGHTS_RAW = np.array([10, 10, 10, 10, 10, 6, 6, 4, 4, 4, 3, 3, 3, 2], dtype=float)
WEIGHTS = WEIGHTS_RAW / WEIGHTS_RAW.sum()  # normalizar

# Decision matrix: linhas = áreas (7), colunas = critérios (14)
# Valores = % de atendimento convertido para escala 0–1
# (100% = 1.0, 50% = 0.5, 0% = 0.0)
DECISION_MATRIX = np.array([
    # A1     A2     A3     A4     A5     A6     A7
    [1.0,   1.0,   1.0,   1.0,   1.0,   1.0,   1.0],  # Dist_agua
    [1.0,   0.5,   0.5,   1.0,   0.5,   0.5,   0.5],  # Dist_nucleos
    [1.0,   1.0,   1.0,   1.0,   1.0,   1.0,   1.0],  # Dist_aeroporto
    [0.5,   0.5,   0.0,   0.0,   0.0,   0.5,   0.5],  # Condutividade
    [1.0,   1.0,   1.0,   1.0,   1.0,   1.0,   1.0],  # APP
    [0.5,   0.5,   0.5,   0.5,   1.0,   0.5,   0.5],  # Dist_viarios
    [1.0,   0.5,   0.5,   0.5,   0.5,   0.5,   0.5],  # Dist_coleta
    [0.5,   0.5,   0.5,   0.5,   0.5,   0.5,   0.5],  # Infraestrutura
    [1.0,   1.0,   1.0,   1.0,   0.0,   0.5,   0.5],  # Vida_util
    [1.0,   1.0,   1.0,   1.0,   1.0,   1.0,   1.0],  # Textura
    [1.0,   1.0,   1.0,   1.0,   1.0,   1.0,   1.0],  # Declividade
    [1.0,   1.0,   1.0,   1.0,   1.0,   1.0,   1.0],  # Mineralogia
    [1.0,   1.0,   1.0,   1.0,   1.0,   1.0,   1.0],  # Uso_solo
    [0.5,   0.5,   0.5,   0.5,   0.5,   0.5,   0.5],  # Acesso
], dtype=float).T  # transposta: shape (7, 14)

AREAS = ['Área 1', 'Área 2', 'Área 3', 'Área 4', 'Área 5', 'Área 6', 'Área 7']

# Pontuações de referência (Tabela 31 de Sousa 2022 — verificação)
SCORES_SOUSA = np.array([85, 73, 68, 58.5, 65, 59, 63])
RANKING_SOUSA = [1, 2, 3, 6, 4, 7, 5]  # (menor rank = melhor área)
```

---

## Decisões Tomadas Nesta Sessão

### Estrutura do LaTeX

- Template escolhido: **cas-dc** (double column) — adequado para periódicos Elsevier como Waste Management, Environmental Earth Sciences, Sustainability
- Citações: estilo `authoryear` com `natbib`
- Tabelas: `booktabs` + `multirow`; pairwise matrix e results table em `table*` (largura dupla)
- Equações: todas numeradas com labels, cobertas nas seções AHP (2), TOPSIS (5) e PROMETHEE II (5)

### Reorganização de Pastas

Estrutura anterior (bagunçada): arquivos soltos na raiz + pastas "Final", "Final v1", "Final Final" com duplicatas.
Estrutura atual: 5 pastas numeradas com propósito claro.

### Estratégia de Dataset — DECISÃO DE SETEMBRO/2026

#### Dataset principal: IEEE Access 2026 (Ilha do Fogo)

**Decisão:** o dataset primário para o experimento MCDM é o do próprio paper IEEE Access (Azancort Neto et al., 2026), não o de Sousa (2022).

**Dados verificados diretamente** (pasta: `G:\Faculdade\Estudo\Doutorado\2025.1\Otimização Bioinspirada\Tentativa de dados via GIS\`):

| Arquivo | Linhas | Colunas | Observação |
|---------|--------|---------|------------|
| `dados_criterios_para_otimizacao_524-3.csv` | 525 (=524+header) | 13 colunas em PT | CSV bruto, antes do filtro de 50% de cobertura terrestre |
| `results_cache/df_real_data_cached.csv` | 474 (=473+header) | 13 colunas em EN | CSV após filtro de 50% — este é o que o script usa |
| `New code/results/.../exhaustive_search_pareto.csv` | 214 (=213+header) | Cost, Impact, Neg_Safety, Safety, idx1, idx2, idx3 | IDs 0-based no df_real_data_cached.csv |
| `New code/results/.../best_compromise_sites.csv` | 4 (=3+header) | site_id, lat, lon, cost, impact, safety, municipality | Objetivos individuais por site |

**Colunas do CSV bruto** (português → inglês mapeado):
- `declive (graus)` → `slope (degrees)`
- `exposicao_vertentes (graus)` → `slope_aspect (degrees)` ← **confirma correção: "Slope aspect (exposure)", não "Exhibition/Strands"**
- `dist_ribeiras (m)` → `dist_streams (m)` → renomeado para `Rivers` ← **confirma: "Rivers", não "Streams"**
- `dist_orla_maritima (m)` → `dist_coastline (m)` ← **confirma: "Coastline", não "Seafront"**

**Contagem correta de candidatos:**
- 524 = grade bruta (antes de qualquer filtro)
- 473 = após filtro de 50% de cobertura terrestre (este é o N do artigo)
- 84 = bloqueados por área protegida (penalizados via geometria, NÃO removidos)
- 389 = viáveis para o experimento MCDM (473 − 84)

**Para identificar os 84 bloqueados:** `df['dist_protected_area (m)'] == 0` (verificado: dá exatamente 84).

**Best Compromise Sites verificados** (site IDs 0-based no df_real_data_cached):
| ID | Lat | Lon | Cost | Impact | Safety | Município |
|----|-----|-----|------|--------|--------|-----------|
| 184 | 14.818 | −24.399 | 0.0414 | 0.1662 | 0.2379 | Mosteiros |
| 430 | 14.852 | −24.306 | 0.0193 | 0.1682 | 0.1542 | Mosteiros |
| 460 | 14.951 | −24.295 | 0.0204 | 0.2224 | 0.2249 | Santa Catarina |

**Objetivos como soma** (validation_metrics.json): cost=0.0811, impact=0.5568, safety=0.6170

**Validação (HV):** NSGA-II best=0.021842, Exhaustive=0.021952, gap=0.50%, capture=99.50%, speedup=4.0×, n_pareto=213

---

#### Dataset secundário: Sousa (2022) — Castanhal/PA

Usar apenas na Fase 4 (generalização), após verificação manual dos dados no PDF original e remoção dos 9 critérios iguais em todas as áreas. **Ver seção "Dataset Sousa (2022) — dados não verificados" acima.**

---

### Pendências e Decisões de Setembro/2026

#### Item 2 da revisão: Problemas confirmados na resposta anterior

**"Repositório confirmado" era inexato:**
- O agente apenas leu o README e o script. Os CSVs não haviam sido abertos.
- Agora **verificados diretamente** nos arquivos locais (ver tabela acima).
- A conta `524 − 84 = 440` estava errada. A conta correta é `473 − 84 = 389`.

**Nome errado no README do repositório:** o campo "Impact: 0.102" rotula o peso do Aeródromo. O peso de Impact (f₂) não é 0.102 — é a **soma** dos pesos dos critérios de impacto ambiental. Não copiar esse rótulo.

#### Item 3 da revisão: O que o PDF revela — decisões confirmadas

1. **Pesos AHP:** os pesos na Tabela 7 do IEEE Access (e no script) são normalização de colunas, não autovetor exato. Diferenças: urban=0.166 (autovetor=0.167), perm=0.152 (autovetor=0.156). Descrever no artigo MCDM o método que foi realmente usado (normalização de colunas), não afirmar que é autovetor.

2. **Correções de terminologia no main.tex (aplicadas):**
   - `x_5`: `Seafront` → `Coastline` ✓
   - `x_6`: `Streams` → `Rivers` ✓
   - `x_9`: `Exhibition/Strands` → `Slope aspect (exposure)` ✓

3. **SAW não é equivalente ao S1 (correção):** o SAW com pesos AHP individuais usa pesos (1,1,1) nos objetivos normalizados, enquanto S1 usa (0.295, 0.356, 0.349) — são matematicamente diferentes. Neste dataset, argmin SAW = argmin S1 = {184,430,460} por coincidência numérica. SAW representa a WLC compensatória que o IEEE Access critica; medir quanto TOPSIS e PROMETHEE II se afastam dela e da fronteira de Pareto é a contribuição nova.

4. **Double weighting na Eq. 20 do IEEE Access:** os pesos são usados duas vezes — uma nos critérios (dentro de f₁, f₂, f₃) e outra nos objetivos (no ranking S(x)). Não replicar essa estrutura no artigo MCDM sem justificativa.

#### Item 4 da revisão: Problemas de desenho do experimento MCDM — DECISÕES

**Problema principal:** MCDM ranqueia sites individuais; fronteira de Pareto tem trios (k=3).

**Solução adotada:**
1. Ranquear os 389 sites viáveis individualmente por SAW, TOPSIS, VIKOR, PROMETHEE II.
2. Para cada método, construir o melhor trio viável (greedy: site mais bem ranqueado + próximo mais bem ranqueado a ≥10 km + próximo seguinte a ≥10 km dos dois).
3. Calcular (f₁, f₂, f₃) do trio como soma dos objetivos individuais.
4. Verificar dominância contra os 213 trios do `exhaustive_search_pareto.csv`.
5. Medir distância euclidiana normalizada ao trio de Pareto mais próximo.

**Métrica complementar:** frequência com que as top-k áreas de cada método aparecem nos 213 trios de Pareto. Pergunta: "Qual método identifica mais áreas que fazem parte de configurações ótimas?"

**CSV a usar:** `df_real_data_cached.csv` (473 linhas, valores contínuos em metros/graus). NÃO usar `_standardized.csv` (notas ordinais 1-3 — gera empates).

**Excluir 84 protegidas:** identificar por `df['dist_protected_area (m)'] == 0` (verificado: dá exatamente 84).

**AHP no novo desenho:** fornece apenas pesos. NÃO ranqueia 389 alternativas (exigiria comparações par a par impossíveis). Métodos comparados: SAW, TOPSIS, VIKOR, PROMETHEE II.

**Título do artigo muda:** de "Comparison between Multi-Criteria Decision-Making Methods to support the determination of sites" para algo que inclua a validação contra a fronteira de Pareto.

#### Item 5 da revisão: Inconsistências no IEEE Access a não replicar

1. **Valores do BCS na Conclusão:** a Conclusão cita "96,8% de redução no custo" e "131% de melhora na segurança". Esses valores são das soluções extremas (0.0196 e 0.6883), não do BCS. O BCS tem cost=0.0811 e safety=0.6170. Não reproduzir esses números no artigo MCDM.

2. **Descrição de convergência contraditória:** o paper diz "converged to the true mathematical optima" (Seção III-D) e também "99.50%... rather than full equivalence" (Seção III-D). A segunda afirmação é correta e mais precisa.

3. **Aspect criterion definido de três formas:** "leeward 90°–180° (SE)", "SW prioritized" e "North/Northwest faces penalized". Escolher uma definição consistente no artigo MCDM.

4. **Site #184 como Mosteiros "southern coastal zone":** Mosteiros fica no NORDESTE da ilha, não no sul. A atribuição de município pode estar correta (o script usa distância geodésica ao centroide do município), mas a descrição "southern coastal zone" é imprecisa geograficamente.

5. **Escala dos objetivos:** o artigo afirma objetivos em [0,1], mas como são somas de 3 sites, o máximo é ~3× o valor por área. A hipótese de que a média aleatória do impacto excede 1 (o que indicaria inclusão de áreas protegidas penalizadas no baseline) não foi verificada diretamente — requer teste específico no random_baseline do script. Não afirmar [0,1] para as somas.

---

### Separação de versões — ATENÇÃO (verificado em 2026-09-27)

A pasta local `G:\...\Tentativa de dados via GIS\` contém **dois conjuntos de resultados** de versões diferentes do experimento. Não misturar.

#### Versão INVÁLIDA — baseada nos 524 candidatos (raiz da pasta)

Estes arquivos foram gerados antes do filtro de 50% de cobertura terrestre. O índice máximo (514) não existe entre os 473, e os extremos de Pareto não batem com os do artigo publicado.

| Arquivo | Por que é inválido |
|---------|-------------------|
| `nsga2_pareto_front_results.csv` | Safety_max=0.7265 ≠ 0.6883 publicado |
| `exhaustive_search_best_solutions.csv` | Tem índice 514, que não existe nos 473 |
| `pareto_front_complete_analysis.csv` | Gerado com o Pareto da versão 524 |
| `pareto_solutions_corrected.csv` | Idem |
| `pareto_solutions.csv` | Idem |
| `pareto_solutions_with_ws.csv` | Idem |
| `resultado/results-22-47-59/` | Contém `validation_metrics.json` antigo (hv_best desconhecido — não verificar) |
| `resultado/results-22-43-13/` | Sem conteúdo útil (pasta vazia parcial) |

**Regra:** nunca ler esses arquivos para gerar número do artigo.

#### Versão VÁLIDA — baseada nos 473 candidatos (New code/results/)

Pasta canônica: `New code/results/results-2026-04-07_18-40-54/`

| Arquivo | Conteúdo | Verificado |
|---------|----------|-----------|
| `exhaustive_search_pareto.csv` | 213 trios Pareto, colunas: Cost, Impact, Neg_Safety, Safety, idx1, idx2, idx3 | ✓ (214 linhas = 213+header; Cost_min=0.0196, Impact_min=0.4732, Safety_max=0.6883) |
| `best_compromise_sites.csv` | Sites {184, 430, 460} com lat/lon e objetivos individuais | ✓ (IDs 0-based, coordenadas batem com df) |
| `validation_metrics.json` | HV: NSGA-II=0.021842, Exhaustive=0.021952, gap=0.50%, n_pareto=213 | ✓ |
| `nsga2_pareto_front_results.csv` | Front do NSGA-II (150 soluções) | ✓ (Safety_max=0.6883) |
| `decision_making_metrics.json` | Métricas de Pareto e diversidade | Não lido ainda |

**`df_real_data_cached.csv`** (em `results_cache/`) é o CSV de trabalho principal: 473 linhas, 13 colunas em inglês, valores contínuos em metros/graus, IDs 0-based. É este o arquivo a usar no `mcdm_experiment.py`.

#### Resultados do bloco de verificação (seção 5 da revisão)

Rodado em 2026-09-27 via `uv run --with pandas`:

```
len(df)=473  len(par)=213
Cost_min  = 0.019594  ✓  (esperado 0.0196)
Impact_min= 0.473199  ✓  (esperado 0.4732)
Safety_max= 0.688265  ✓  (esperado 0.6883)

df.loc[184] → lat=14.818041, lon=-24.398681  ↔  bcs[184] lat=14.818041, lon=-24.398681  ✓ (0-based)
df.loc[430] ✓  df.loc[460] ✓

dist_protected_area == 0: 84  ✓  (esperado ~84)

aspect == -1 nos 473: 0 ocorrências
aspect == -1 no bruto (524): 41 de 524 (7.8%)
→ Causa provável: células da grade que caem no mar ou em bordas, onde o DEM vale 0 (hipótese, não verificada diretamente).
→ O filtro de 50% de cobertura terrestre excluiu todas as 41 áreas planas.
→ O experimento MCDM não é afetado.
→ O min-max do IEEE Access foi calculado sobre os 473 (verificado: max perm = 1.104 m nos 473 vs 18.795 m nos 524). As 41 planas não afetaram os resultados publicados.
```

#### Lógica de aspect no script (linha 428, `landfill_nsga2_optimization.py`)

```python
norm_asp = 0   if (np.isfinite(asp) and 90 <= asp <= 180)   # leeward → baixo impacto
         = 0.5 if not np.isfinite(asp)                       # NaN/ausente
         = 1   else                                          # barlavento → alto impacto
```

`aspect == -1` é um número finito, portanto receberia `norm_asp=1` (pior nota).
Isso é um defeito latente do código — corrigir no mcdm_experiment.py e no README do repositório.
Não afetou os resultados publicados (as 41 planas foram excluídas antes do cálculo).

---

### Nova Pergunta de Pesquisa (surgiu com o IEEE Access 2026)

**"São as soluções MCDM consistentes com a fronteira de Pareto do NSGA-II?"**

Dado que o IEEE Access já calculou a fronteira de Pareto verdadeira (exhaustive search) para as 473 áreas candidatas:
- As áreas selecionadas pelo topo do TOPSIS, PROMETHEE II e VIKOR estão na fronteira de Pareto?
- Quantas das top-k soluções MCDM são Pareto-ótimas?
- Onde no espaço de objetivos (custo, impacto, segurança) se situam as soluções MCDM?

Esta pergunta é **original** (não aparece na literatura de comparação MCDM para aterros), **verificável** (fronteira de Pareto existe nos CSVs do repositório), e **liga os dois papers** de forma metodológica sólida.

---

### Cronologia — IMPORTANTE

O artigo MCDM (versão original: 2022) é **anterior** ao IEEE Access (publicado: 2026).
Posicionamento correto: o artigo MCDM e o IEEE Access são **complementares**, não sequenciais.
- Artigo MCDM: compara métodos de ranqueamento escalar (ponderação e agregação)
- IEEE Access: usa otimização multiobjetivo sem agregação a priori
- Relação: demonstram que ranqueamento e otimização chegam a conclusões convergentes (ou divergentes) — isso é a contribuição conjunta.

**Não escrever** "o artigo MCDM antecede e fundamenta o IEEE Access" — cronologicamente incorreto para um artigo de 2026/2027.

---

## Próximos Passos — Esta Semana (27/set/2026)

> **Histórico de sessões anteriores — manter para rastreabilidade, mas não usar como referência para números ou decisões. Ver a seção "Estado atual" no topo.**

### Decisão: artigo novo, experimento de 2022 fora do escopo

Registrado em 27/set/2026. O artigo atual (main.tex) será reescrito como um artigo novo, focado em benchmark de métodos MCDM contra a fronteira de Pareto exata. O experimento de 2022 (ranqueamento de critérios com AHP+TOPSIS+PROMETHEE aplicados às 11 variáveis) vira no máximo um parágrafo de contexto histórico na Introdução. Não entra nos Resultados.

Plano completo em `plano-a1.md` (criado em 27/set/2026).

### O que fazer esta semana

- [ ] **Busca sistemática** — Scopus + WoS com as strings do plano-a1.md §2. Confirma se a lacuna (ranking vs portfólio + fronteira exata + restrição espacial) existe sem sobreposição com Liesiö et al. (2007) e Mavrotas et al.
- [ ] **Escrever P1–P4** com provas e conferir cada uma nos números de Fogo (números no Estado Atual acima).
- [ ] **Monte Carlo de pesos** — Dirichlet(α·w_AHP), α ∈ {50, 200}, 500 sorteios, semente fixa. Reportar: % de sorteios em que cada variante não é dominada, mediana do gap_norm, Jaccard@10 vs SAW.
- [ ] Obter PDF de Andrade & Barbosa (2015) — confirmar nome e pesos.
- [ ] Verificar Brito (2020) — estatística de tonelagem (% TODO linha 141 main.tex).

### O que foi feito até aqui (rounds 1–7)

1. Dataset confirmado: 473 candidatos, 389 viáveis, 3 NaN, 84 excluídos por protected=0.
2. Fronteira reproduzida: 213 trios, diff < 1e-9.
3. 4 métodos implementados + TOPSIS-mm como variante.
4. Taxa de base calculada: 91/389 = 23.4%.
5. Pesos efetivos calculados: mecanismo do TOPSIS vetorial identificado (perm: 0.152→0.549).
6. TOPSIS-mm e PROMETHEE ótimo: ambos Pareto-ótimos.
7. Gap normalizado pela amplitude da fronteira: tabela completa.
8. Derivação PROMETHEE = SAW sobre postos: sustentada empiricamente (r_w=0.923, greedy=ótimo).
9. Decisão editorial registrada: artigo novo. Plano em plano-a1.md.

### Pendências técnicas menores

- Verificar Brito (2020) para tonelagem (% TODO main.tex linha 141)
- Obter PDF Andrade & Barbosa (2015) para confirmar pesos

---

## Histórico — Notas de Sessões Anteriores (desatualizado, não usar como referência)

| Referência | Uso |
|---|---|
| Sousa, T. M. P. (2022). UFPA TCC. URI: bdm.ufpa.br/jspui/handle/prefix/7320 | **Dataset secundário** (Fase 4, generalização — apenas após verificação manual) |
| Sałabun & Urbaniak (2020). ICCS 2020. DOI: 10.1007/978-3-030-50417-5_47 | WS Coefficient para benchmarking MCDM |
| Pinto da Costa & Soares (2005). Statistical Methodology, 2(1), 25–35. | Fórmula correta do r_w (Weighted Spearman) |
| Mareschal et al. (2008). IEEE IEEM. DOI: 10.1109/IEEM.2008.4737980 | Rank reversal no PROMETHEE II |
| Alkaradaghi et al. (2020). Engineering, 12(4). DOI: 10.4236/eng.2020.124021 | AHP + SAW para aterro (modelo para expansão) |
| Günay & Dere (2024). JARNAS, 10(2). DOI: 10.28979/jarnas.1416814 | Análise de sensibilidade em problema de aterro |
| Güler (2026). Mathematics, 14(9), 1416. DOI: 10.3390/math14091416* | SF-TOPSIS + Spearman para aterro sanitário |
| Rekkal et al. (2026). Acta Inf. Pragensia, 15(3). DOI: 10.18267/j.aip.322* | Comparação 5 métodos MCDM |
| Putro et al. (2025). Transformatika, 23(1). DOI: 10.26623/transformatika.v23i1.12220* | AHP+SAW+TOPSIS+VIKOR+MABAC com sensibilidade |
| Lassey (2025). Preprint. DOI: 10.21203/rs.3.rs-7870462/v1* | PROMETHEE vs VIKOR vs TOPSIS |

> *DOIs obtidos via Crossref mas não verificados individualmente. Confirmar antes de citar em submissão.

---

## Fórmulas de Referência Rápida

### Spearman ρ (n=11 critérios ou n=7 áreas)
$$\rho = 1 - \frac{6\sum d_i^2}{n(n^2-1)}, \quad t = \rho\sqrt{\frac{n-2}{1-\rho^2}} \sim t_{n-2}$$

### Weighted Spearman r_w (Pinto da Costa & Soares, 2005)
$$r_w = 1 - \frac{6\sum_{i=1}^{n}(x_i-y_i)^2[(N-x_i+1)+(N-y_i+1)]}{N^4+N^3-N^2-N}$$

### WS Coefficient (Sałabun & Urbaniak, 2020)
$$WS(A,B) = 1 - \sum_{i=1}^{n} 2^{-x_i} \cdot \frac{|x_i-y_i|}{\max(x_i-1,\,n-x_i)}$$
Assimétrico: A é o ranking de referência.

### Kendall W (concordância simultânea de m rankings)
$$W = \frac{12S}{m^2(n^3-n)}, \quad S=\sum\left(R_i-\bar{R}\right)^2, \quad \chi^2=m(n-1)W \sim \chi^2_{n-1}$$

### TOPSIS (closeness coefficient)
$$C_i = \frac{S_i^-}{S_i^++S_i^-}, \quad S_i^+ = \sqrt{\sum_j (v_{ij}-v_j^+)^2}$$

onde $v_{ij} = w_j \cdot r_{ij}$ já inclui o peso. A fórmula **não** tem $w_j$ dentro da raiz — o peso entra antes na matriz ponderada $V = W \cdot R$.

### VIKOR (compromise index)
$$Q_i = v\frac{S_i-S^*}{S^--S^*} + (1-v)\frac{R_i-R^*}{R^--R^*}, \quad v=0.5$$

### SAW (Simple Additive Weighting)
$$V_i = \sum_{j=1}^{n} w_j \cdot r_{ij}$$
