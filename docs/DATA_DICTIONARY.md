# DATA_DICTIONARY.md — Fogo Island Landfill Site Selection Dataset

**Status:** Fase 0 — preencher antes da Fase 3 (pipeline de dados abertos)  
**Fonte primária:** Azancort Neto et al. (2026, IEEE Access), dataset no Zenodo  
**Ficheiro de dados:** `df_real_data_cached.csv`  
**SHA-256 (df_real_data_cached.csv):** `234f6e1c2697ea540ed0e0674018e6446e9255b25009167cbb0c19c51311722a`  
(verificado por `scripts/validate_core.py`, Gate 1, commit b1bae3c)  
**N candidatos brutos:** 473  
**N excluídos (dist_protected = 0):** 84  
**N admissíveis (A'):** 389  

---

## Regra de exclusão

Um candidato é excluído se `dist_protected_area (m) == 0` — o sítio está dentro de uma área protegida e não pode ser seleccionado. Todos os 84 sítios excluídos cumprem exactamente esta condição.

---

## Critérios — 11 variáveis

### Grupo G1 — Eficiência de localização (F1, minimizar)

#### perm — `dist_low_permeability (m)`

| Campo | Valor |
|---|---|
| Definição | Distância em metros do ponto candidato à zona de baixa permeabilidade (solo impermeável) mais próxima |
| Unidade | metros |
| Fonte | **[TODO — confirmar]** Mapa geológico de Cabo Verde / estudo de origem Andrade & Barbosa (2015)? |
| Processamento | **[TODO — confirmar]** Distância Euclidiana ou Haversine à feature de polígono de baixa permeabilidade |
| Resolução | **[TODO — confirmar]** |
| Direcção | COST: menor distância = melhor (queremos construir sobre solo impermeável) |
| Grupo | G1 |
| Peso AHP | 0.152 |
| Valor 0 | O sítio está sobre a zona de baixa permeabilidade |
| N zeros em A' | **350 de 389** (90.0%) — valor extremo, mais alto de todos os critérios |
| Máximo em A' | 532 m |
| Nota crítica | Os 350 zeros fazem ρ_j(vec) = 0.583, inflando o peso efectivo 2.88×. É o critério central de todo o artigo. A sua definição em Fogo **não pode** ser substituída por clay_fraction do SoilGrids sem declaração explícita de que é um critério diferente. |

#### slope — `slope (degrees)`

| Campo | Valor |
|---|---|
| Definição | Inclinação do terreno em graus no ponto candidato |
| Unidade | graus (°) |
| Fonte | DEM derivado de dados topográficos de Fogo |
| Processamento | Derivado com `gdaldem slope`, unidade graus |
| Resolução | **[TODO — confirmar]** |
| Direcção | COST: menor inclinação = melhor (terreno plano = mais seguro e estável) |
| Grupo | G1 |
| Peso AHP | 0.113 |
| Valor 0 | Terreno horizontal |
| N zeros em A' | **[TODO — verificar]** |

#### roads — `dist_roads (m)`

| Campo | Valor |
|---|---|
| Definição | Distância em metros à estrada mais próxima |
| Unidade | metros |
| Fonte | OpenStreetMap / rede viária oficial de Cabo Verde |
| Processamento | Distância Euclidiana à feature de linha mais próxima |
| Resolução | — |
| Direcção | COST: menor distância = melhor (maior acessibilidade) |
| Grupo | G1 |
| Peso AHP | 0.030 |
| Valor 0 | O sítio está sobre uma estrada |
| NaN | Sítio 41 — imputado com midpoint do intervalo dos 473 |

---

### Grupo G2 — Integridade ambiental (F2, minimizar)

#### rivers — `dist_streams (m)`

| Campo | Valor |
|---|---|
| Definição | Distância em metros à linha de água (ribeira) mais próxima |
| Unidade | metros |
| Fonte | OpenStreetMap / rede hídrica |
| Processamento | Distância Euclidiana à feature de linha mais próxima |
| Resolução | — |
| Direcção | INV: maior distância = melhor (evitar contaminação de recursos hídricos) |
| Grupo | G2 |
| Peso AHP | 0.091 |
| Valor 0 | O sítio está sobre uma linha de água |
| N zeros em A' | **[TODO — verificar]** |

#### aspect — `slope_aspect (degrees)`

| Campo | Valor |
|---|---|
| Definição | Orientação do terreno em graus (azimute geográfico, 0° = Norte, sentido horário). Convertido a binário: SE-facing ∈ [90°, 180°] (fechado nos extremos) = 1 (benéfico), restante = 0. |
| Unidade | graus (°) em bruto; binário {0,1} no scorer |
| Fonte | ASTER GDEM v3 (`elevation_utm.tif`, EPSG:4326, 0.000278°/pixel) |
| Processamento | Sobel gradient na resolução 4326 (fórmula geográfica): `arctan2(-dx, dy)`, graus, 0°=N sentido horário. Fórmula correcta validada pelo teste do cone: coseno médio azimute-pico 0.805. **Nota de convenção:** a coluna `slope_aspect (degrees)` do CSV publicado (SHA-256 234f6e1c…) armazena a convenção reflectida, θ_pub = (270° − θ) mod 360°, onde θ é o azimute geográfico. A coluna NÃO é um azimute geográfico standard. O indicador binário SE-facing é invariante sob esta reflexão (eixo 135° = centro do intervalo). |
| Binarização | `c = 1 if 90° ≤ θ ≤ 180° else 0` (intervalo fechado; 3 sítios têm aspecto exactamente nos extremos) |
| Resolução | 30 m (ASTER GDEM v3) |
| Direcção | BENEFIT no scorer (1 = SE-facing = bom); COST nos objectivos F2 (c=0 para SE-facing = menor impacto ambiental) |
| Grupo | G2 |
| Peso AHP | 0.075 |
| Valor 0 | Sítio não está virado a SE (fora do intervalo [90°,180°]) |
| n₁ (SE-facing) | **94 de 389** em A' |
| ρ_j (vec) | 1/√94 = 0.103 |
| Nota de justificação | Andrade & Barbosa (2015, p. 254): "Os ventos dominantes na área de estudo são ventos de nordeste e noroeste. Consequentemente, estas vertentes receberam a classificação de aptidão mínima." NE/NW-facing = aptidão mínima → o complemento (encostas SE/S, intervalo [90°,180°]) = aptidão máxima. O número exacto [90°,180°] não está no texto — deriva da implementação GIS. |
| Nota crítica | A coluna `slope_aspect` armazena a convenção reflectida. Qualquer análise contínua (e.g. R-asp) deve usar `θ_correct = (270 − θ_pub) % 360` ou recalcular directamente do DEM com `arctan2(-dx, dy)`. |

#### coast — `dist_coastline (m)`

| Campo | Valor |
|---|---|
| Definição | Distância em metros à linha de costa mais próxima |
| Unidade | metros |
| Fonte | OpenStreetMap coastline / carta náutica |
| Processamento | Distância Euclidiana à feature de linha de costa |
| Resolução | — |
| Direcção | INV: maior distância = melhor (risco de escoamento para o oceano) |
| Grupo | G2 |
| Peso AHP | 0.069 |
| Valor 0 | O sítio está na linha de costa |
| N zeros em A' | **[TODO — verificar]** |

#### protected — `dist_protected_area (m)`

| Campo | Valor |
|---|---|
| Definição | Distância em metros ao limite de área protegida mais próxima. Sítios DENTRO da área (valor 0) são excluídos. |
| Unidade | metros |
| Fonte | WDPA (Protected Planet) |
| Processamento | Distância Euclidiana ao polígono de área protegida mais próximo; 0 = dentro da área |
| Resolução | — |
| Direcção | INV: maior distância = melhor (respeitar zonas de protecção ambiental) |
| Grupo | G2 |
| Peso AHP | 0.066 |
| Valor 0 | **EXCLUSÃO** — sítio dentro de área protegida (84 candidatos excluídos) |
| N zeros em A' | 0 (todos os zeros foram excluídos; nenhum sítio admissível tem protected=0) |

#### wells — `dist_wells (m)`

| Campo | Valor |
|---|---|
| Definição | Distância em metros ao poço de água mais próximo |
| Unidade | metros |
| Fonte | **[TODO — confirmar]** dados de poços de Cabo Verde / INGRH |
| Processamento | Distância Euclidiana à feature de ponto mais próxima |
| Resolução | — |
| Direcção | INV: maior distância = melhor (evitar contaminação de fontes de água subterrânea) |
| Grupo | G2 |
| Peso AHP | 0.055 |
| Valor 0 | O sítio está sobre um poço |
| N zeros em A' | **[TODO — verificar]** |
| Nota para Santiago | Provavelmente indisponível em dados abertos. Política: omitir e renormalizar os 10 pesos restantes (declarar como desvio). |

---

### Grupo G3 — Segurança social (F3, maximizar)

#### urban — `dist_urban_core (m)`

| Campo | Valor |
|---|---|
| Definição | Distância em metros ao núcleo urbano mais próximo |
| Unidade | metros |
| Fonte | OpenStreetMap building footprints / dados de aglomeração urbana |
| Processamento | Distância Euclidiana à área urbana mais próxima |
| Resolução | — |
| Direcção | BENEFIT: maior distância = melhor (evitar impacto sobre populações) |
| Grupo | G3 |
| Peso AHP | 0.166 — o maior peso de todos |
| Valor 0 | O sítio está dentro da área urbana |
| NaN | Sítio 385 — imputado com midpoint do intervalo dos 473 |
| ρ_j (vec) | 0.107 — deflacionado 0.53× pelo peso nominal |

#### aero — `dist_aerodrome (m)`

| Campo | Valor |
|---|---|
| Definição | Distância em metros ao aeródromo mais próximo |
| Unidade | metros |
| Fonte | OpenStreetMap / dados oficiais de aviação |
| Processamento | Distância Euclidiana ao polígono ou ponto de aeródromo |
| Resolução | — |
| Direcção | BENEFIT: maior distância = melhor (restrições de altura e risco de colisão com aves) |
| Grupo | G3 |
| Peso AHP | 0.102 |
| Valor 0 | O sítio está no aeródromo |
| NaN | Sítio 429 — imputado com midpoint do intervalo dos 473 |

#### cult — `dist_cultivation (m)`

| Campo | Valor |
|---|---|
| Definição | Distância em metros à área de cultivo agrícola mais próxima |
| Unidade | metros |
| Fonte | **[TODO — confirmar]** dados de uso do solo de Cabo Verde |
| Processamento | Distância Euclidiana à feature de polígono de terra cultivada mais próxima |
| Resolução | — |
| Direcção | BENEFIT: maior distância = melhor (proteger solos agrícolas e evitar impacto nas culturas) |
| Grupo | G3 |
| Peso AHP | 0.081 |
| Valor 0 | O sítio está dentro de área cultivada |
| N zeros em A' | **[TODO — verificar]** |
| Nota para Santiago | Usar ESA WorldCover 2021, classe 40 (cropland) apenas. Não usar classe 10 (tree cover). |

---

## Imputação de valores em falta

| Sítio | Critério | Coluna | Valor imputado | Justificação |
|---|---|---|---|---|
| 41 | roads | `dist_roads (m)` | (min + max) / 2 dos 473 sítios | Falha provável na consulta OSM; valor neutro |
| 385 | urban | `dist_urban_core (m)` | (min + max) / 2 dos 473 sítios | Idem |
| 429 | aero | `dist_aerodrome (m)` | (min + max) / 2 dos 473 sítios | Idem |

---

## Pesos AHP e hierarquia (Tabela 2 do artigo)

| Critério | Grupo | Peso nominal | Fonte dos pesos |
|---|---|---|---|
| perm | G1 | 0.152 | Andrade & Barbosa (2015), matriz AHP coluna-normalizada |
| slope | G1 | 0.113 | Idem |
| roads | G1 | 0.030 | Idem |
| rivers | G2 | 0.091 | Idem (ajustado de 0.090 para fechar soma em 1.000) |
| aspect | G2 | 0.075 | Idem |
| coast | G2 | 0.069 | Idem |
| protected | G2 | 0.066 | Idem |
| wells | G2 | 0.055 | Idem |
| urban | G3 | 0.166 | Idem |
| aero | G3 | 0.102 | Idem |
| cult | G3 | 0.081 | Idem |
| **Total** | | **1.000** | CR = 0.056 |

Pesos de grupo: W_G1 = 0.295, W_G2 = 0.356, W_G3 = 0.349.

---

## Conversões binárias

#### aspect

Valor bruto (azimute em graus) → binário no scorer:
```python
c = np.where((x >= 90) & (x <= 180), 1.0, 0.0)
# leeward (sotavento): azimute in [90, 180] → c = 1 (benéfico para TOPSIS)
# nos objectivos F2: c = 0 para [90, 180] (menor impacto ambiental = melhor)
```

A convenção é: 0° = Norte, sentido horário (padrão `gdaldem aspect`). A binarização usa o azimute do vento dominante em Fogo (alísios de NE/E → sotavento = SE/S, ou seja azimute ∈ [90°, 180°]).

**Para Santiago:** verificar a direcção do vento dominante antes de aplicar a mesma convenção. Declarar no PRESPEC se a convenção mudar.

---

## TODO — Campos a confirmar antes da Fase 3

| Campo | Critério | Pergunta |
|---|---|---|
| Fonte | perm | É o mapa geológico de Cabo Verde? Qual publicação ou fonte digital? |
| Processamento | perm | Distância ao polígono de baixa permeabilidade? Qual é o limiar de permeabilidade usado? |
| Resolução do DEM | slope, aspect | Qual resolução foi usada? Copernicus 30m ou outro? |
| Fonte | cult | É o uso do solo do estudo de origem ou ESA WorldCover? |
| Fonte | wells | Qual é a base de dados de poços usada? INGRH? |
| N zeros | rivers, slope, roads, coast, wells, cult | Verificar contagens exactas em A' |
| Critério de exclusão | protected | Confirmar que 0 = dentro da área (não buffer de 0 m) |

Estes campos bloqueiam a Fase 3. Sem a definição exacta de perm, o pipeline aberto para Santiago não pode reproduzir o resultado de Fogo.

---

## Amplitudes sob normalização vector (Tabela 2 do artigo)

Calculadas sobre A' (389 sítios). **Sujeito a verificação na Fase 1.3** (discrepância de 6.7% em aspect).

| Critério | ρ_j (vec) | w_eff/w (vec) | Nota |
|---|---|---|---|
| perm | 0.583 | **2.88×** | 350 zeros comprimem a norma |
| slope | 0.135 | 0.67× | |
| roads | 0.206 | 1.02× | |
| rivers | 0.265 | 1.31× | |
| aspect | 0.103 | 0.51× | Binário, n₁=94: ρ=1/√94 |
| coast | 0.126 | 0.63× | |
| protected | 0.105 | 0.52× | |
| wells | 0.081 | 0.40× | |
| urban | 0.107 | **0.53×** | |
| aero | 0.086 | 0.43× | |
| cult | 0.171 | 0.85× | |
| TV(vec) | 0.315 | — | |
| TV_B | 0.249 | — | |
| TV_W | 0.199 | — | |
| m_eff | 4.05 | — | |
