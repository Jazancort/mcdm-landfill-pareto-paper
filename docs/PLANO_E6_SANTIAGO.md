# Plano: E6 (mecanismo sintético) + Instância Santiago + Email Alkaradaghi

Criado: 2026-10-XX  
Status: rascunho para revisão — não executar até `corpus/PRESPEC_E6.md` e
`corpus/PRESPEC_SANTIAGO.md` estarem commitados no repositório

---

## Contexto e motivação

O artigo dispõe de três camadas de evidência para a decomposição TV_B/TV_W:

1. **Analítica** — Theorem 1 e Extension of Prop. 1: optimal assembly é eficiente
   se e só se TV_W = 0. Exacto, sem probabilidade.
2. **Empírica em Fogo** — E1, E4, F8: confirmação numa única instância. Magnitudes
   de 25–43 pp específicas desta geometria e distribuição de critérios.
3. **Sintética para generalização** — E5 (405 instâncias): impõe amplitudes em
   **score e objectivos em conjunto**, tornando optimal assembly eficiente por
   construção. **Não testa Theorem 1 nem o canal TV_W.**

O §8.6 do artigo declara explicitamente a limitação do E5:
> "E5 imposes amplitudes on score and objectives jointly, so optimal assembly is
> efficient by construction and the grid does not test Theorem 1."

**O E6 corrige exactamente esta falha**: impõe amplitudes só no score, mantém os
objectivos em min-max, e varia TV_B e TV_W de forma independente e controlada.

**A instância de Santiago** testa se as magnitudes (25 pp, 43 pp) são específicas
de Fogo ou se outros casos com diferentes estruturas de amplitude produzem perdas
comparáveis. É um segundo ponto empírico, não um experimento controlado.

---

## Parte 1 — PRESPEC_E6: mecanismo sintético (score-only amplitude manipulation)

### 1.1 Diferença crítica em relação ao E5

| Propriedade | E5 | E6 |
|---|---|---|
| Amplitudes no score | Sim | Sim |
| Amplitudes nos objectivos | Sim (mesmo factor s_W) | **Não** — objectivos fixos em min-max |
| Testa Theorem 1 | Não (Q2_opt=100% por construção) | Sim |
| Testa se TV_W governa optimal loss | Não | Sim |
| Testa se TV_B afecta optimal loss | Não | Sim (controlo) |

### 1.2 Design

**Instâncias de base**: Geometria de Fogo (fogo_trios.npy, d_min=10 km, k=3,
κ=200, N_adm=389) com colunas de critérios redrawadas de distribuições sintéticas.
Os trios já estão computados; só mudam as distribuições das colunas.

**Porquê usar a geometria de Fogo**: evita construir GIS novo; as restrições de
separação e de candidatos admissíveis são idênticas às do estudo principal, o que
torna os resultados directamente comparáveis.

**Famílias de distribuição marginal** (Factor 3):

| Família | Parâmetros | Propriedade |
|---|---|---|
| Lognormal | μ=0, σ=1 | Assimétrica positiva, sem zeros, similar a distâncias |
| Beta(1,3) | — | Assimétrica com massa no 0, similar a perm |
| Uniforme | — | Sem concentração, TV_W baixo esperado |

5 réplicas por família × 2 níveis de TV_B × 4 níveis de TV_W = 120 instâncias.

**Factores (3)**:

| Factor | Níveis | Notação |
|---|---|---|
| TV_W alvo (within-group) | 0, 0.10, 0.199 (Fogo), 0.30 | tw ∈ {0, L, F, H} |
| TV_B alvo (between-group) | 0, 0.249 (Fogo) | tb ∈ {0, F} |
| Família marginal | lognormal, beta(1,3), uniforme | fam |

**Total**: 4 × 2 × 3 × 5 réplicas = 120 instâncias. 5 células por instância.

### 1.3 Cinco células por instância

Como em E1, para cada instância (distribuição + réplica):

| Célula | Amplitudes A_j | TV_B | TV_W | Objectivos |
|---|---|---|---|---|
| M | A_j = 1 (min-max) | 0 | 0 | min-max |
| B | A_j = Ā_g (uniforme dentro do grupo) | tb | 0 | min-max |
| W | A_j controlado: between=0, within=tw | 0 | tw | min-max |
| V | A_j controlado: both=target | tb | tw | min-max |
| C | A_j = ρ_j natural da instância | empírico | empírico | min-max |

**Construção controlada das amplitudes**:

Para uma instância sintética com amplitudes naturais ρ_j (da normalização vector):

```
# Definição: TV_W = 0.5 * sum_g sum_{j in G_g} (w_j/W_g) * |A_j/Ā_g - 1|
# onde Ā_g = weighted mean of A_j within group g

# Célula B (TV_B=tb, TV_W=0):
#   A_j^B = Ā_g, onde os Ā_g são escalados para que TV_B = tb
#   TV_B = 0.5 * sum_g W_g * |Ā_g - 1|   (group-level deviation from 1)

# Célula W (TV_B=0, TV_W=tw):
#   A_j^W = 1 + s_W * (ρ_j - Ā_g) / σ_atual
#   onde σ_atual = TV_W_natural da instância e s_W escolhido para atingir tw
#   Constrangimento: weighted mean A_j^W within G_g = 1 para todo g (TV_B=0)

# Célula V (TV_B=tb, TV_W=tw):
#   A_j^V = Ā_g^B + s_W * (ρ_j - Ā_g) / σ_atual
```

O score de um sítio a na célula W: `sum_j w_j * A_j^W * n_j^mm(a)`, onde n_j^mm
é min-max calculado sobre a instância sintética.

**Importante**: A_j^W é aplicado apenas ao score. Os objectivos são
`F_g(a) = sum_{j in G_g} w_j * n_j^mm(a)` — sem factor A_j. Esta é a distinção
central em relação ao E5.

### 1.4 Três previsões pré-declaradas

**P1 — Assertion dura (Theorem 1 generalizado)**

Para TODAS as 120 instâncias × TODAS as famílias, nas células M e B:

```
TV_W = 0  ⟹  Q2_optimal = 100%
```

P1 é uma assertion, não uma hipótese. Se falhar em qualquer instância, há um bug
na construção das amplitudes ou os objectivos não estão em min-max. Verificar P1
antes de analisar P2 e P3.

**P2 — Previsão ordinal primária**

Para cada instância, Q2_optimal na célula W é monotone não-crescente em TV_W:

```
Q2_opt(tw=0) ≥ Q2_opt(tw=L) ≥ Q2_opt(tw=F) ≥ Q2_opt(tw=H)
```

Critério de confirmação: Spearman ρ ≥ 0 em ≥ 80% das instâncias por família.

Falsificação: ρ < 0 em > 20% das instâncias dentro de alguma família.

**P3 — Isolamento do canal TV_W**

Para cada par de células com mesmo TV_W mas diferente TV_B (W vs V ao nível tw):

```
|Q2_opt(tb=0, tw) - Q2_opt(tb=F, tw)| < 10 pp
```

para ≥ 90% das instâncias. Confirma que TV_B não governa a perda em optimal assembly.
Falsificação: diferença > 10 pp em > 10% das instâncias.

### 1.5 Regras de decisão

| Condição | Consequência para o artigo |
|---|---|
| P1 falha em alguma instância | Bug — abortar, diagnosticar |
| P1 confirma, P2 confirma | Remover "on this instance" das frases sobre TV_W |
| P1 confirma, P2 falha | Manter qualificação; TV_W é observação empírica de Fogo |
| P3 confirma | Remover "on this instance" das frases sobre TV_B |
| P3 falha | TV_B tem efeito em optimal — investigar; novo resultado |

### 1.6 Output esperado

```
results/e6/e6_instances.csv
  colunas: family, replicate, tw_level, tb_level, cell, Q2_greedy, Q2_optimal, SE

results/e6/e6_summary.csv
  por (family, tw_level): mean(Q2_opt), SD, fraction_monotone
```

Figura: Q2_optimal vs tw_level, 3 painéis (um por família), P1 marcado a tracejado
em y=100.

### 1.7 Passos de implementação

1. Commitar `corpus/PRESPEC_E6.md` (versão deste §1) antes de qualquer run
2. Escrever `scripts/e6_generate_synthetic.py` — gera colunas para 120 instâncias
3. Escrever `scripts/run_e6.py` — corre 5 células × N_draws=500 × κ=200
4. Enviar para Athena — tempo estimado: ~3h (120 × 500 draws × 5 células)
5. Verificar P1 antes de analisar P2 e P3
6. Criar figura e tabela de sumário para §7 ou Supplementary

**Parâmetros fixos**: N=500, κ=200, seed=42 (mesmo que E1), k=3, fogo_trios.npy.

---

## Parte 2 — PRESPEC_SANTIAGO: segunda instância real

### 2.1 Propósito e limite

Testar se as magnitudes de loss (25–43 pp) são específicas de Fogo ou se se
reproduzem com outra estrutura de amplitude no mesmo modelo de critérios.

**O que Santiago pode fazer**: segundo ponto empírico com distribuições de critérios
independentes de Fogo. Se TV_W(Santiago) for menor (esperado sem os 350 zeros de
perm), Q2_opt será maior — confirmando que as magnitudes dependem do caso.

**O que Santiago não pode fazer**: substituir o E6 para testar o mecanismo. É um
segundo ponto empírico, não um experimento controlado.

### 2.2 Critérios de inclusão (pré-declarados)

Uma segunda instância entra no artigo se e só se, antes de qualquer run de Q2:

1. Todos os dados brutos provêm de fontes públicas com DOI ou URL estável.
2. Os pesos AHP são os de Fogo, ou renormalizados se algum critério for omitido
   (ver §2.4).
3. N_adm ≥ 100 sítios admissíveis após exclusões.
4. `corpus/PRESPEC_SANTIAGO.md` está commitado com TV_W calculado dos dados brutos
   e as previsões P_S1–P_S4 escritas.

### 2.3 Ilha escolhida

Santiago (Cabo Verde): área ~991 km², maior ilha do arquipélago, maior
diversidade de dados OSM. Alternativa: Santo Antão (~779 km², potencialmente
menos dados OSM urbanos).

A escolha de Santiago é feita antes de qualquer extracção de dados, não com base
nos resultados.

### 2.4 Fontes de dados por critério

| Critério | Fonte | Resolução | Proxy |
|---|---|---|---|
| perm | SoilGrids v2 (ISRIC) — clay content | 250 m | Sim. Distribuição provavelmente menos extrema que Fogo. |
| slope | Copernicus DEM GLO-30 | 30 m | Não (derivado directo). |
| roads | OpenStreetMap (GeoFabrik Africa) | — | Não. Verificar completude. |
| rivers | OpenStreetMap + SRTM drainage | — | Parcial. Verificar ≥20 features. |
| aspect | Copernicus DEM GLO-30 (binário: azimuth ∈ [90°,180°]) | 30 m | Não. Mesma definição de Fogo. |
| coast | OpenStreetMap coastline | — | Não. |
| protected | WDPA (Protected Planet, versão actual) | — | Não. Verificar cobertura CV. |
| wells | a confirmar (ver §2.4a) | — | A determinar. |
| urban | OpenStreetMap building footprints | — | Não. |
| aero | OSM + dados oficiais | — | Aeródromo de Santiago (IATA: RAI). |
| cult | ESA WorldCover 2021 v200 (classes 40+10) | 10 m | Parcial (proxy agrícola). |

#### 2.4a Política para wells (pré-declarada)

1. Verificar OSM `natural=spring` + `man_made=water_well` em Santiago.
2. Se n_features < 20: dados insuficientes.
3. Se insuficiente: omitir wells; renormalizar os 10 pesos AHP restantes
   proporcionalmente para soma = 1.0 (wells tem w=0.055 em Fogo).
4. Declarar a omissão em `corpus/PRESPEC_SANTIAGO.md` antes de correr Q2.

### 2.5 Grelha de candidatos (pré-declarada)

Decidir antes de extrair qualquer critério:

- Grelha regular com espaçamento **2 km** dentro dos limites terrestres de Santiago
  (BBOX aproximada: -25.35, 14.85, -23.45, 15.40), dando ~500–800 candidatos brutos.
- Exclusões: dist_protected=0, dist_rivers < 500 m, dist_coast < 2000 m.
- Separação mínima no portfolio: 10 km (mesma de Fogo).
- Se N_adm < 100 após exclusões: alargar espaçamento para 3 km e declarar desvio.

O espaçamento 2 km é escolhido agora, não após ver os dados.

### 2.6 Pesos AHP

Usar os pesos originais de Fogo (Tabela 2 do artigo) sem recalibração.
Renormalizar apenas se wells for omitido (ver §2.4a).

Justificação: o objectivo é manter o modelo de valor e variar só a distribuição
dos critérios. Recalibrar para Santiago criaria uma instância diferente que não
isola o efeito da distribuição.

### 2.7 Previsões ordinais (a commitar antes de qualquer run de Q2)

Estas previsões são escritas aqui como rascunho. Serão commitadas com os valores
concretos de TV_W e TV_B calculados dos dados brutos, antes de correr Q2.

**P_S1 — Regressão (assertion)**

SAW/mm/optimal = 100% em Santiago. Falha = bug.

**P_S2 — Previsão de magnitude (primária)**

Se TV_W(Santiago/vec) < TV_W(Fogo/vec) = 0.199, então:

```
Q2_opt(SAW/vec/Santiago) > Q2_opt(SAW/vec/Fogo) = 56.8%
```

Previsão base: sem concentração extrema como perm, TV_W ∈ (0.05, 0.15) e
Q2_opt ∈ (65, 90)%.

Falsificação: TV_W(Santiago) > 0.15 e Q2_opt < 56.8% (Santiago mais concentrado
que Fogo e loss superior — contraditório com E1).

**P_S3 — Padrão B/W/V**

Se m_eff(Santiago) < 5 (distorção concentrada num critério), a ordenação
B > W > V em optimal assembly deve manter-se.

Se m_eff(Santiago) ≥ 8 (distorção difusa), espera-se B ≈ V em optimal assembly.

**P_S4 — Direcção da distorção**

O critério com maior amplitude ρ_j em Santiago (análogo a perm em Fogo) é o que
governa TV_W. Identificar esse critério dos dados brutos e declarar em
`corpus/PRESPEC_SANTIAGO.md` antes de correr Q2.

### 2.8 Critérios de validade pós-extracção

Verificar antes de qualquer Monte Carlo (não informados por Q2):

1. N_adm ≥ 100
2. Todos os critérios com variância > 0
3. TV(vec, Santiago) > 0.05 (há distorção mensurável)
4. Nenhum critério com > 90% dos candidatos no mesmo valor

Se algum falhar: declarar como desvio em `PRESPEC_SANTIAGO.md` e decidir se
proceder antes de correr Q2.

### 2.9 Pipeline GIS (passos técnicos)

```
1. Copernicus GLO-30 BBOX: -25.35 14.85 -23.45 15.40
   → gdal_translate + gdaldem slope / gdaldem aspect

2. GeoFabrik Africa (Cabo Verde) → roads, rivers, coast, urban, aero, wells
   → distâncias por gdal_proximity ou scipy.ndimage

3. SoilGrids v2 REST API (clay_content_0-5cm_mean) → perm proxy

4. ESA WorldCover 2021 (tile: S15W024) → cult

5. WDPA geopackage → protected (intersecção)

6. Grelha regular 2 km → 500–800 pontos brutos
   → aplicar exclusões → df_via_santiago.csv

7. Verificar critérios de validade pós-extracção

8. Commitar PRESPEC_SANTIAGO.md com TV_W dos dados brutos + previsões P_S1–P_S4

9. Adaptar mc_unified.py para Santiago (substituir dados de entrada)

10. Correr na Athena (~30 min)

11. Verificar P_S1–P_S4
```

### 2.10 Riscos e mitigações

| Risco | Prob. | Mitigação |
|---|---|---|
| Wells indisponível | Alta | Política de omissão já declarada (§2.4a) |
| OSM rivers incompleto em Santiago | Média | Verificar n_features ≥ 20; proxy SRTM drainage |
| SoilGrids não representa perm | Média | Declarar como proxy; afecta magnitudes mas não mecanismo |
| N_adm < 100 com espaçamento 2 km | Baixa | Alargar para 3 km e declarar desvio |
| TV_W(Santiago) ≈ TV_W(Fogo) | Baixa | Reportar: magnitudes robustas; igualmente interessante |
| TV_W(Santiago) < 0.05 | Média | Reportar: perda residual em instância sem concentração; confirma dependência do caso |

---

## Parte 3 — Email corrigido a Alkaradaghi et al.

### 3.1 Contexto e o que pedir

Alkaradaghi et al. (2019), *Sustainability* 11(17), 4530 — "Landfill Site Selection
Using GIS and Multi Criteria Decision-Making".

O artigo reporta apenas 7 sítios candidatos finais (resultado do overlay GIS).
Com 7 candidatos e k=3, há C(7,3)=35 portfólios — insuficiente para o modelo
deste artigo (requer ≥ 100 sítios admissíveis com fronteira de Pareto computável).

O email só tem sentido se pedir as **camadas raster dos critérios antes do overlay**,
que permitiriam construir uma grelha de candidatos com o mesmo pipeline de Fogo.

Prioridade: mais baixa que E6 e Santiago. Enviar em paralelo. Resposta improvável
em menos de 4 semanas.

### 3.2 Rascunho do email

```
Subject: Data request — GIS raster layers for your Sustainability 2019 landfill paper

Dear Dr. Alkaradaghi (and co-authors),

I am writing regarding your 2019 article "Landfill Site Selection Using GIS and
Multi Criteria Decision-Making" published in Sustainability (volume 11, issue 17,
article 4530). Our group found this paper valuable as a reference for spatial
landfill siting methodology.

We are developing a methodology that measures Pareto efficiency loss in
multi-criteria portfolio selection problems, and we would like to apply it to an
independent published instance. Your Halabja study is a strong candidate: it uses
an explicit AHP weight structure, spatial separation constraints, and covers a
region with distinct criterion distributions from our primary case study
(Fogo Island, Cabo Verde).

To apply our methodology, we would need the original GIS raster layers for each
evaluation criterion (slope, aspect, distance to roads, rivers, settlements,
protected areas, and any others used in your study) at the resolution used in
the analysis, before the overlay classification step. The seven final candidate
sites in the article are not sufficient because our analysis requires a regular
grid of candidate points with numerical criterion scores for all grid positions,
not just the selected sites.

All data would be used exclusively for academic research. We would provide full
attribution to your study in any publication and would be pleased to share a
preprint of our work with you.

If the raster layers are not available, any guidance on where the source data can
be obtained (for example, specific Iraqi government datasets, meteorological
organization data, or other public sources you used) would also be appreciated.

Thank you for your time and consideration.

Yours sincerely,
[Nome, afiliação]
```

---

## Sequência recomendada de execução

```
Agora (antes de qualquer run):
  1. Rever este documento e responder às decisões em aberto (§4)
  2. Commitar este ficheiro: docs/PLANO_E6_SANTIAGO.md
  3. Criar corpus/PRESPEC_E6.md (versão formal das previsões de §1)
  4. Enviar email a Alkaradaghi (paralelo, não bloqueia nada)

Semana 1:
  5. Implementar scripts/e6_generate_synthetic.py + scripts/run_e6.py
  6. Correr E6 na Athena (~3h) e verificar P1 antes de P2/P3
  7. Iniciar extracção de dados de Santiago

Semana 2:
  8. Commitar corpus/PRESPEC_SANTIAGO.md (com TV_W dos dados brutos + P_S1–P_S4)
  9. Correr Monte Carlo em Santiago (~30 min)
  10. Integrar E6 e Santiago no artigo

Critério de paragem satisfatória: E6 confirma P1+P2 e Santiago confirma P_S2.
Juntos substituem a limitação
"External confirmation on other published instances was not obtained"
por uma secção de resultados positiva.
```

---

## Decisões em aberto (responder antes de começar)

1. **Grelha de Santiago**: espaçamento 2 km (proposta) ou 3 km? Decidir antes de
   qualquer extracção de dados.

2. **Proxy de perm em Santiago**: clay fraction do SoilGrids (proposta) ou tentar
   obter dados de geologia/permeabilidade do INGRH primeiro?

3. **Wells em Santiago**: tentar primeiro, ou omitir desde o início e renormalizar?

4. **Réplicas no E6**: 5 réplicas × 3 famílias = 15 instâncias base × 8 células de
   factor = 120 runs. Suficiente ou 10 réplicas (240 runs)?

5. **Posição no artigo do E6**: nova subsecção em §7 como "Experiment E6:
   mechanism generalisation" ou no Supplementary ao lado do E5?

6. **Posição no artigo de Santiago**: tabela comparativa Fogo/Santiago em §7.7 ou
   nova subsecção na Discussão?
