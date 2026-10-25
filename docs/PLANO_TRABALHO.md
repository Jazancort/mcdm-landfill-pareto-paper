# Plano de Trabalho — Paper MCDM Landfill (Omega)

**Última actualização:** 2026-10-25 (correcção da data anterior: era 2026-10-28, data futura)
**HEAD actual:** 6e5af12 (actualizado de b1d715a)
**check_consistency:** exit 0, 26 casos
**Nota alvo:** 9/10

---

## Estado resumido das Fases

| Fase | Conteúdo | Estado |
|---|---|---|
| F475 | Revisão de f475928 | 3/6 completas, sub-items pendentes |
| A | 20 erros factuais | 19/20 (A1 pendente) |
| G | Build check + Figura 1 | 4/5 (G4/G5 pendentes) |
| B | Métrica de regret | 6/6 DONE |
| C | F8 matriz 2×2 | BUG ENCONTRADO — re-run Athena necessário |
| D | Correcções científicas | 6/6 DONE |
| E | Cortes estruturais | 10/10 DONE |
| F (Santiago) | Segunda instância | PRESPEC ainda não escrito |

---

## PRIORIDADE 0 — Contradição C4 (bloqueia o texto)

### C0-fix: Aspecto bug em compute_f8_mm_frontier.py

**Causa raiz confirmada** (commit f52987c, script `_diag_tv_bug.py`):

`C_score_vec[:, aspect]` era definido como `np.where(leeward, 0.0, 1.0)` — valores brutos {0,1} (amplitude=1,0) em vez de `C_vec_raw[:, j]` já L2-normalizado (amplitude=0,103). Aspecto inflacionado **9,7× na pontuação vec**.

**TV com o bug = 0,377** (não ≈ 0). O bug aumenta a distorção, não a anula.

| Critério | w_nom | w_eff canónico | w_eff bugado | delta |
|---|---|---|---|---|
| perm | 0,152 | 0,435 | 0,327 | +0,175 |
| aspect | 0,075 | 0,038 | **0,277** | **+0,202** |
| urban | 0,166 | 0,087 | 0,066 | −0,100 |
| outros | ... | ... | ... | negativos |
| **TV** | | | **0,377** | (canónico: 0,311) |

**Pólo do aspect:** `np.where(leeward, 0.0, 1.0)` → leeward=0 (neutro na score), windward=1 (penalizado em -w_asp=-0,075). A direcção é **acidentalmente correcta**, mas a amplitude é 9,7× acima do canónico.

**Explicação provisória do 99,8%:** o score bugado eleva o peso efectivo do aspect para 27,7% (2.º maior), seleccionando fortemente portfolios all-leeward. Estes portfolios têm F2 baixo (menos impacto ambiental) e aparecem non-dominated na fronteira mm com maior frequência do que os portfolios canónicos vec. O 99,8% reflete esta concentração acidental, não TV ≈ 0.

**H1** (fronteira mm errada) é menos provável: mm/mm/opt = 100% em ambas as corridas confirma que o teste de pertença funciona correctamente.

**Fix aplicado** (commit f52987c): `scoring.make_scorers()` substituiu a reimplementação. Assert rho_j a 1e-12. MCDM_DATA_DIR env var necessária na Athena.

**Run N=500 em curso na Athena** (tmux f8mm, `/tmp/f8mm_run.log`). C0-1 RUNNING.

---

### Critérios de aceitação da corrida (escritos antes de abrir o log)

Os draws, pesos e scorer são agora idênticos ao factorial. Output deve ser bit-for-bit igual.

| Verificação | Esperado exacto | Se falhar |
|---|---|---|
| Q2 mm/vec/opt | **284/500 = 56,8%** | Score ainda não é canónico |
| Q2 mm/vec/grd | **331/500 = 66,2%** | Idem |
| Q2 mm/mm/opt | 500/500 = 100,0% | Fronteira/Theorem 1 quebrado |
| Q2 mm/mm/grd | **430/500 = 86,0%** | Fronteira errada |
| SE mm/vec/opt | √(56,8×43,2/500) ≈ **2,22 pp** | Confirma contagem exacta |
| `\FEightVecMmOptQ` = `\QtwovecOptimal` | ambos 56,8% | Invariante: mesma célula, dois scripts |
| `\FEightVecMmGrdQ` = `\QtwovecGreedy` | ambos 66,2% | Idem |

Critério "≈" não é aceitável. Qualquer desvio indica um bug remanescente.

**Acções C0-2 a C0-6** (só executar após passagem de TODOS os critérios acima):

- [x] **C0-1** CONCLUÍDA (ebb74c9). Resultados: mm/mm/opt=100%, mm/mm/grd=86%, mm/vec/opt=**56,8%** (284/500, exacto), mm/vec/grd=**66,2%**. Todos os critérios de aceitação passados. H1 descartada.
- [x] **C0-2** CONCLUÍDA: macros_f8.tex regenerado na Athena, scp para local. `\FEightMmVecOptQ{56.8}`, `\FEightMmVecGrdQ{66.2}`.
- [x] **C0-3** CONCLUÍDA: §7.4 actualizada — "assimetria de 28×" removida; nova assimetria 7,7× (vec scoring mais vulnerável); causalidade invertida corrigida.
- [x] **C0-4** CONCLUÍDA: BAD_PHRASES adicionados para "= 28$ times", "rarely misses", "VecMMOptLoss/FEightMmVecOptLoss = 28".
- [x] **C0-5** CONCLUÍDA: invariante `\FEightMmVecOptQ == \QtwovecOptimal` (56,8%) e `\FEightMmVecGrdQ == \QtwovecGreedy` (66,2%) em check_consistency. Secção "C0 invariant" aparece no log.
- [x] **C0-6** CONCLUÍDO: commit ebb74c9 + push.

**Auditoria anti-reimplementação** (junto com C0-6):
- [ ] Correr `test_no_local_scorers.py` (ver §6).
- [ ] Scripts que calculam algo próximo: assert `max|score_local - make_scorers(...)| < 1e-12` em 20 pesos aleatórios. Tolerância explícita, nunca `np.allclose`.
- [ ] SAW/mm/opt no regret: confirmar R=0 exactamente em 500/500 draws.

**Skill/agent:** `research-coder` agent para Athena run; edição de main.tex directa depois.

---

## PRIORIDADE 1 — Erros factuais no PDF (visíveis ao revisor)

### PDF-1: Figura 1 (A1)

**Problema:** A Figura 1 (diagrama de 6 etapas, p. 7) tem valores errados:
- Etapa 3: "perm: 2,88×" → deve ser `\PermInflation` = 2,86×
- Key finding: "Normalisation: +25,4 pp (greedy; +34,6 pp full 2³)" → o contraste 34,6 pp com o factorial completo não é mais reportado assim
- Key finding: "Assembly: −1,1 pp on average (+8,1 pp under min–max, −10,2 pp under vector)" → §7.4 diz expressamente que não reporta a média; +8,1 também não aparece no texto
- Key finding: "Aggregation: +0,5 pp, equivalent to zero (TOST…)" → D3 retirou o TOST dos destaques; o texto diz −0,4 pp
- Etapa 2: "Dirichlet, κ ∈ [50, 200]" → factorial usa κ = 200

**Solução:** refazer Figura 1 em TikZ dentro do LaTeX com macros. Assim nunca mais fica desactualizada.

- [ ] **A1-1** Identificar a figura: é o diagrama de workflow (fig_F4_map.pdf ou fig_workflow?). Verificar qual `fig_*.py` gera e qual variável LaTeX inclui.
- [ ] **A1-2** Criar nova figura em TikZ com macros `\PermInflation`, `\NormGreedyContrast`, `\AggContrast`, etc.
- [ ] **A1-3** Adicionar ao Makefile target `figures` e ao `build_check`.
- [ ] **A1-4** Fechar A20 (Code availability) logo depois.

**Skill/agent:** `academic-figures` skill para o TikZ; edição directa.

---

### PDF-2: §6.8 — Valores raw (A2)

**FEITO** (F475-4, commit 36e7f37): macros `\TVvec`, `\DeltaLtwoshift`, `\DeltaLinfshift` existem e são usados. BAD_PHRASES em check_consistency.py guardam os valores raw 0.3146/0.3127/0.2859. Exit 0 confirma ausência.

### PDF-3: §5.4 — "≈1,0 pp in the other direction" (A3)

**FEITO** (F475-4): `\FEightMMOptLoss{5.6}` existe. Verificado por grep em check_consistency.py (exit 0).

### PDF-4: §4.3 — aero na lista min=0 (A4)

**FEITO** (F475-4): "perm, aspect, urban, cult, rivers" no texto, sem aero. BAD_PHRASE `\texttt{aero} and \texttt{rivers}` guarda.

### PDF-5: §6.2 e eq.(20) — fórmulas raw vs shift

- [ ] **PDF-5** Localizar a equação ou parágrafo em §6.2 que define ρ_j na forma raw (`x_{ij}/||x_j||`). Substituir pela fórmula shift `x̃_{ij}/||x̃_j||` ou acrescentar nota explicando a equivalência. Verificar com check_consistency.

### PDF-6: §7.8 — "24,000 total draws" (A7)

**FEITO** (F475-6/A7): `\EsixNdrawsTotal{168,000}` existe. BAD_PHRASE guarda o literal. Exit 0 confirma.

---

## PRIORIDADE 2 — Revisão f475928 (novos itens do segundo passe do revisor)

### R1: E1-V vs factorial SAW/vec/opt — draw-by-draw

**VERIFICADO** (2026-10-28): 500/500 draws idênticos.
`e1_diag_bootstrap.csv (e1v_opt_nd) == mc_unified_raw.csv (SAW/vector/optimal/nd_Q2Ap)` — match perfeito.
Frase §7.7 "draws identical to the factorial" está correcta. TASKS.md actualizado de "via agregados" para "verificado draw a draw".

---

### R2: Bootstrap B=10.000 vs B=2.000 inconsistência

**Decisão:** Opção B — declarar B=10.000 no E1. O `\nbootEone{10,000}` já existe.

- [ ] **R2-1** Adicionar frase na legenda da Tabela 6: "E1 intervals use $B=\nbootEone$ replicates."
- [ ] **R2-2** Verificar que §7.7 usa `\nbootEone`, não o literal.
- [ ] **R2-3** Adicionar MUST_FAIL para `[3.8; 11.0]` no check_consistency.py — intervalo que não corresponde a nenhuma configuração.

---

### R2: Bootstrap B=10.000 vs B=2.000 inconsistência

**Decisão:** Opção B — declarar B=10.000 no E1. O `\nbootEone{10,000}` já existe.

- [ ] **R2-1** Adicionar frase na legenda da Tabela 6: "E1 intervals use $B=\nbootEone$ replicates."
- [ ] **R2-2** Verificar que §7.7 usa `\nbootEone`, não o literal.
- [ ] **R2-3** Adicionar MUST_FAIL para `[3.8; 11.0]` no check_consistency.py — intervalo que não corresponde a nenhuma configuração.

---

### R3: SHA hashes independentes do sistema operativo

**Estado:** F475-3 já fez o `.gitattributes` e verificou os 4 SHAs canónicos.  
**Pendente:**

- [ ] **R3-1** Documentar no README.md: "Os hashes SHA-256 nos scripts são calculados sobre bytes LF. Normalização: `b.replace(b'\r\n', b'\n')`."
- [ ] **R3-2** Actualizar os scripts de verificação que calculam SHA para usar normalização LF antes de comparar.

---

### R4: "12%" e "all others" — completar a substituição (F475-4 pendente)

**Problema:** F475-4 substituiu "all others gain 12%" → "seven fully continuous criteria gain ≈\RnkContinuousGainPct%", mas o revisor nota que:
- Urban fica em 1,115 (não 1,12)
- Cult fica em 1,105 (não 1,12)
- A Tabela 2 já mostra 1,11 para urban e cult

A frase correcta é "the seven fully continuous criteria gain ≈12%" (não "all others"). Verificar se o macro `\RnkContinuousGainPct` só se aplica aos sete critérios contínuos sem empates, não aos 11.

- [ ] **R4-1** Confirmar quais 7 critérios o macro captura (slope, roads, rivers, coast, protected, wells, aero?).
- [ ] **R4-2** Verificar que urban e cult **não** são incluídos na frase dos 12%.
- [ ] **R4-3** Se necessário, adicionar nota ou segundo macro `\UrbanRnkGain{1.11}` / `\CultRnkGain{1.11}`.

---

### R5: F475-5 — audit_hardcoded.py modo inverso (bidirecional)

**Problema:** depois de substituir um literal por macro, confirmar que o macro ficou no sítio certo. "Um macro certo no sítio errado passa em todos os checks que tens hoje."

- [ ] **R5-1** `git show f475928 -- main.tex` — extrair as linhas das substituições 1,77×/0,53×/0,51× e confirmar o contexto actual.
- [ ] **R5-2** Implementar `audit_hardcoded.py --reverse`: para cada macro em macros*.tex, listar todas as ocorrências em main.tex com 2 linhas de contexto, e verificar que a grandeza da frase bate com o significado do macro.

**Skill/agent:** `diagnose` skill para o R5-1; edição directa para R5-2.

---

## PRIORIDADE 3 — Build check (G4)

- [ ] **G4-1** Adicionar `check_tab_amplitude.py` ao Makefile target `check`:
  ```makefile
  check: check_consistency check_tab_amplitude check_hardcoded
  ```
- [ ] **G4-2** Adicionar `generate_macros_r1.py` ao target `macros`.
- [ ] **G4-3** Confirmar que `build_check.py` invoca todos os check_* scripts.
- [ ] **G20** Code availability (A20/G5): atualizar depois de A1 fechado.

---

## PRIORIDADE 4 — Santiago + Instâncias adicionais

> **Ressalva:** os dados abaixo vêm de resumos de pesquisa, não de textos completos. Pesos, critérios e camadas têm de ser confirmados nos documentos originais com DOI antes de entrarem no PRESPEC.

---

### Descoberta sobre o pipeline de Fogo (pré-requisito para Santiago)

**Repositório de origem:** GitHub `NSGA2-GIS-Landfill-Optimization-Cape-Verde`, dados no Zenodo 17704387 (CC-BY-4.0).

| Item | Resultado |
|---|---|
| Como os candidatos foram gerados | Grelha 1 km × 1 km, recortada pela ilha, só células com ≥50% de terra. Candidatos = centróides. É esta a regra a replicar. |
| 524 vs 473 discrepância | `criteria_data_for_optimization_524-3.csv` tem 524 sítios; Zenodo e artigo falam em 473. Há um passo de triagem não documentado. Resolver antes de replicar a grelha. |
| Origem do perm | Camada geológica com permeabilidade calculada (`geologia_com_permeabilidade_calculada.shp`). Não é SoilGrids. A regra litologia→permeabilidade vem de Andrade & Barbosa (2015) ou do script. |
| Origem dos wells | OSM, consulta automática, igual a roads/rivers/urban/aero/cult/coast. |
| Pipeline automático | O código regenera grelha, filtro de terra e consultas OSM quando os CSV não existem. Pode correr sobre Santiago directamente. |

**Consequências para o plano:**
- Omitir os wells de Santiago não se justifica: em Fogo também vieram do OSM. Omitir cria confundimento entre conjunto de critérios e ilha.
- O perm de Santiago é o mesmo critério de Fogo se usar a mesma regra geológica (não SoilGrids).

- [ ] **PRE-1** Resolver a diferença 524/473: ler o script de grelha e identificar o passo que vai de 524 para 473. Documentar no PRESPEC e verificar se há implicações para o próprio artigo de Fogo.
- [ ] **PRE-2** Extrair a regra litologia→permeabilidade de Andrade & Barbosa (2015) ou do script que criou `geologia_com_permeabilidade_calculada.shp`. Fixar no PRESPEC antes de abrir a camada de Santiago.

---

### Regra de selecção das instâncias (escrever antes de tudo)

Para afastar a crítica de ter escolhido as ilhas a dedo:

> "Ilhas com um estudo de localização de aterros por AHP publicado, geologia digital aberta e área entre 300 e 1000 km²."

Santiago (~991 km²) e Lemnos (~477 km²) cumprem. Maurícia (Ramjeawon & Beerachee 2008) fica de fora por ter só 4 candidatos, insuficientes para portfolio com separação mínima. Regra declarada; instâncias decorrem dela.

---

### Santiago — Fontes confirmadas

**perm:**
- Plano A (principal): Carta Geológica de Santiago (Serralheiro et al. 1977, 1:100 000), vectorizada pelo INGT. Acesso via IDECV (`idecv.gov.cv`), camada `carto_base:geologia_santiago`, WMS/WFS. Se WFS bloqueado: `ingt@ingt.gov.cv`.
- Plano B (sensibilidade): SoilGrids 250m.
- Três unidades hidrogeológicas conhecidas: complexo eruptivo interno (quase impermeável), aquífero principal (pillow lavas/basaltos), cones piroclásticos (muito permeável). Confirmar transmissividade na literatura INGRH.

**wells:**
- Primário: OSM, mesma consulta de Fogo.
- Sensibilidade 1: Inventário de furos e poços do INGRH por concelho.
- Sensibilidade 2: USGS Heilweil et al. (2009), *Hydrogeology Journal*, DOI 10.1007/s10040-009-0434-2. Coordenadas nas tabelas suplementares. Por verificar.
- Regra PRESPEC: "se OSM tiver ≥ X poços, usa OSM; caso contrário, INGRH como desvio declarado."

**Pesos — dois ramos:**

| Ramo | Fonte | Estado |
|---|---|---|
| S-T (transferidos) | Pesos de Fogo (AHP, Andrade 2015) | Imediato; isola efeito da distribuição dos dados |
| S-L (locais) | Cabral (2012/2013), dissertação FCSH/Universidade Nova de Lisboa: AHP para aterro na região sul de Santiago. Cobre hidrografia, uso do solo, solos, acessibilidade e declive. | **Por verificar:** extrair tabela de pesos do texto original; confirmar mapeamento para os 11 critérios |
| (referência adicional) | Tavares, Zsigraiová & Semiao (2011), *Waste Management* 31(9-10), DOI 10.1016/j.wasman.2011.04.013. AHP para incineradora em Santiago: socioeconómico 48%, técnico 41%, ambiental 11%. | Outro tipo de infra-estrutura; útil só se Cabral falhar |

O ramo S-L responde à objecção "os pesos de Fogo são específicos de Fogo". Se o mapeamento entre os critérios de Cabral e os 11 for forçado, S-L cai e fica só S-T — decidir ao ler a tabela original.

---

### Lemnos — Terceira instância (opcional, alto esforço)

**Estudo de base:** Kontos, Komilis & Halvadakis (2005), *Waste Management* 25(8), 818–832. DOI: 10.1016/j.wasman.2005.04.002.

**Por que é um bom candidato:**
- Área ≈ 477 km² (Fogo: 476 km²). Mesmo tamanho, enumeração exacta continua viável.
- Pesos AHP publicados para aterro, com SAW. Mesmo modelo de valor.
- Critérios sobreponíveis a Fogo: permeabilidade, águas superficiais, ecossistemas sensíveis, áreas urbanas, património cultural, uso do solo, morfologia, orientação face ao vento (≈ aspect).
- Dados europeus abertos: Copernicus DEM GLO-30 (declive/aspect), CORINE/ESA WorldCover (uso do solo), Natura 2000/WDPA (áreas protegidas), OSM (estradas/etc.), mapas geológicos IGME/HSGME.

**Por verificar:**
- [ ] Confirmar se o artigo publica os pesos e as regras de exclusão em tabela.
- [ ] Confirmar se a geologia de Lemnos pode ser reconstruída com resolução suficiente.
- [ ] Identificar os critérios de Kontos sem equivalente nos 11 (visibilidade, património) e decidir regra de omissão.

**Dois ramos de pesos:** L-T (transferidos de Fogo) e L-K (locais Kontos 2005).

**Recomendação:** preparar Lemnos só se Santiago correr bem e houver tempo. Duas instâncias reais bem construídas valem mais do que três com dados frágeis.

---

### V1: Cabral 2012 (não 2013)

**Metadados confirmados:**
- Título: *Análise multicritério em SIG para localização de aterros sanitários. O caso da região sul da Ilha de Santiago, Cabo Verde*
- Autor: Adilson Vaz Cabral
- Ano: **2012** (não 2013)
- Grau: Mestrado em Gestão do Território, especialização em Detecção Remota e SIG, FCSH, Universidade Nova de Lisboa
- Handle: http://hdl.handle.net/10362/8627
- **Acesso bloqueado** (protecção anti-robô do repositório RUN). PDF deve ser descarregado manualmente em http://hdl.handle.net/10362/8627

**ATENÇÃO:** os pesos "66,7%, 62,5%, ..." que circularam antes vieram de um resumo de pesquisa e não estão confirmados. Não entram no PRESPEC até extracção do texto original.

- [ ] **V1-1** Descarregar PDF de http://hdl.handle.net/10362/8627 e carregar na conversa para extracção.
- [ ] **V1-2** Extrair: matriz AHP e pesos (com número de página), razão de consistência, critérios de exclusão (buffers em metros), fontes de cada camada, área exacta de estudo (só região sul).
- [ ] **V1-3** Avaliar viabilidade do mapeamento dos critérios de Cabral para os 11 do artigo.

### V2: Kontos et al. 2005 (Lemnos)

**Dado parcial confirmado** (por verificar no texto completo):

| Classe permeabilidade | Condição K | Nota |
|---|---|---|
| Alta | K ≥ 10⁻⁵ m/s | 2 |
| Água salobra | — | 5 |
| Média-baixa | 10⁻⁵ > K > 10⁻⁷ m/s | 8 |
| Baixa | K ≤ 10⁻⁷ m/s | 10 |

**Diferença importante para o artigo:** esta é uma escala de classes (0–10), não uma distância à zona de baixa permeabilidade como o perm de Fogo. Se Lemnos avançar, decidir qual das duas formas usar para a compatibilidade de critérios.

- [ ] **V2-1** Confirmar se o artigo publica os pesos AHP e as regras de exclusão (buffers) em tabela.
- [ ] **V2-2** Confirmar se os critérios sem equivalente nos 11 (visibilidade, património cultural) têm regra de omissão.
- [ ] **V2-3** Decidir critério perm: escala de classes de Kontos ou distância à baixa permeabilidade (Fogo).

### V3: IDECV WFS de Santiago

- WFS testado (`https://geoservicos-ingt.gov.cv/geoserver/carto_base/wfs`): servidor responde com página Tomcat por defeito. Pode ser bloqueio só a acessos automáticos.
- [ ] **V3-1** Testar no QGIS: Camada → Adicionar camada WFS → esse URL → procurar `geologia_santiago`.
- [ ] **V3-2** Se WFS bloqueado, pedir a camada a `ingt@ingt.gov.cv`.

---

### Decisões confirmadas

| Item | Decisão |
|---|---|
| S-D1: papel do Santiago | Replicação completa factorial + E1. §7.10, protocolo idêntico ao Fogo. "Confirmar" → "Testar". |
| S-D2: previsões base | S0–S6 + S-L aceites. Ver tabela acima. |
| Wells | Não omitir. OSM principal; INGRH como sensibilidade se necessário. |
| perm principal | Geologia IDECV (mesma abordagem de Fogo), não SoilGrids. |

---

### PRESPEC — Fase 0 (commitar ANTES de extrair qualquer dado)

- [ ] **S-F0-1** Declarar regra de selecção das instâncias (ver acima).
- [ ] **S-F0-2** Definir fontes, versões e datas de acesso para cada critério (perm IDECV, wells OSM, rivers DEM com limiar fixado aqui, aspect [90°,180°] como convenção herdada).
- [ ] **S-F0-3** Grelha: 1 km × 1 km, ≥50% terra (regra de Fogo, após resolução da diferença 524/473). Contar trios só com geometria antes de extrair critérios.
- [ ] **S-F0-4** Pesos: dois ramos S-T e S-L. Mapeamento dos critérios de Cabral declarado aqui; critérios sem correspondência com regra de redistribuição.
- [ ] **S-F0-5** Regra de contagem mínima de wells do OSM.
- [ ] **S-F0-6** Commitar o código de análise (freeze do commit hash do scoring).
- [ ] **S-F0-7** Escrever previsões S0–S6 como regras condicionais em função de (TV_B, TV_W, m_eff, fracção de zeros). Cada previsão: regra + frase para artigo + cenário de falha.
- [ ] **S-F0-8** Dois controlos em Fogo: (a) Fogo sem wells, pesos renormalizados; (b) Fogo com o substituto do perm de Santiago. Isolam efeito da instância vs critérios.
- [ ] **S-F0-9** Declarar que resultados serão reportados seja qual for a direcção.
- [ ] **S-F0-COMMIT** — **IMUTÁVEL após push**.

### PRESPEC — Fase 1 (após extracção, antes de qualquer score)

- [ ] **S-F1-1** Hash dos dados; amplitudes, TV, TV_B, TV_W, m_eff, fracção de zeros.
- [ ] **S-F1-2** Verificar critérios de validade e resolver previsões condicionais (S5 especialmente).
- [ ] **S-F1-COMMIT** — **IMUTÁVEL após push**.

### Pipeline Santiago (após Fase 1)

- [ ] **S-P1** `santiago_constants.py` equivalente ao `fogo_constants.py`.
- [ ] **S-P2** Fronteira, amplitudes e factorial (scripts da Athena, mesma estrutura).
- [ ] **S-P3** E1 equivalente (TV_W prediction test).
- [ ] **S-P4** Regret R para as 8 células.
- [ ] **S-P5** Dois controlos em Fogo (ver S-F0-8).
- [ ] **S-P6** Reportar como §7.10 com protocolo análogo ao §7.9 (E1).
- [ ] **S-P7** Actualizar frase de generalização na §8 e Conclusão.

**Guardrail:** scripts de score Santiago recusam correr sem `PRESPEC_SANTIAGO_F1.lock`.

**Skill/agent:** `doc-coauthoring` para o PRESPEC; `research-coder` agent para o pipeline Athena; `feature-dev` skill para integração no paper.

---

## Ordem de execução recomendada

```
Imediato (esta sessão):
  C0-1   → rodar compute_f8_mm_frontier.py N=500 na Athena
  R1-1   → testar draws E1-V vs factorial por draw (local, ~5 min)
  PDF-3  → verificar §5.4 "1.0 pp" vs "\FEightMMOptLoss"

Próxima sessão (após resultados da Athena):
  C0-2..6  → actualizar macros, texto C4/§7.4, check_consistency
  R2       → decidir opção A ou B, implementar macro CI
  R4       → verificar "7 criteria" vs urban/cult
  A1       → Figura 1 em TikZ

Depois (semana seguinte):
  R3       → README + scripts SHA
  R5       → audit_hardcoded.py reverse
  G4       → Makefile check targets
  PDF-2,5  → §6.8 e eq.(20) verificação
  S-D1,D2  → decisões Santiago
  S-F0     → PRESPEC Fase 0

Quando PDF actualizado:
  Enviar ao revisor para nova avaliação
  S-F1..P  → pipeline Santiago (Athena)
```

---

## PRIORIDADE 6 — Teste anti-reimplementação do scorer

Quarto episódio do mesmo padrão (Q3 float32, F8 v2 injection, coincidência dos 210, aspecto na C1). A guarda `anti-X_adj_vec` não apanha re-implementações com nomes diferentes.

```python
# tests/test_no_local_scorers.py
import re, pathlib
SUSPECT = re.compile(
    r"def\s+(saw|topsis|vikor|score)\w*\s*\("
    r"|linalg\.norm\("
    r"|np\.where\(.*90.*180"
)
for p in pathlib.Path("scripts").rglob("*.py"):
    if "deprecated" in p.parts or p.name in ("scoring.py", "_diag_tv_bug.py"): continue
    src = re.sub(r"#.*", "", p.read_text(encoding="utf-8", errors="ignore"))
    hits = SUSPECT.findall(src)
    assert not hits, f"{p}: possível reimplementação do scorer {hits}"
```

Para scripts que legitimamente calculam algo parecido (compute_regret.py, raw_sensitivity):

```python
# Antes do Monte Carlo, em cada script
_w_test = np.random.default_rng(0).dirichlet(np.ones(11), size=20)
for _w in _w_test:
    _local = my_scorer(_w)
    _canon = saw_sc_fn(_w, norm='vector')
    assert np.max(np.abs(_local - _canon)) < 1e-12, "scorer diverge do canónico"
```

Tolerância explícita `1e-12`, nunca `np.allclose` (rtol=1e-5 é exactamente o tipo de folga que deixou passar bugs antes).

- [ ] **T1** Criar `tests/test_no_local_scorers.py` e adicionar ao Makefile `check`.
- [ ] **T2** Adicionar assert a 1e-12 no início de `compute_regret.py`.
- [ ] **T3** SAW/mm/opt no regret: confirmar R=0 exactamente em 500/500 draws (assert no script).

---

1. Nenhum script corre na Athena sem estar commitado.
2. Cada substituição de literal por macro: verificar contexto com `audit_hardcoded.py`.
3. check_consistency.py exit 0 antes de qualquer commit que toca main.tex.
4. PRESPEC_SANTIAGO não pode ser alterado após commit.
5. Scripts de score Santiago importam `scoring.make_scorers()` e fazem assert a 1e-12. Nunca reimplementar saw_vec localmente.

---

## Comandos Athena rápidos

```bash
# Acessar
ssh athena-isaci

# Correr F8 mm frontier (Ponto 0)
cd ~/scratch/mcdm-landfill-pareto
git pull
tmux new -s f8mm
uv run python scripts/compute_f8_mm_frontier.py
# Depois: scp resultados para local

# Monitorar
tmux attach -t f8mm
# Ctrl+B, D para desligar sem matar
```

---

## Log de descobertas desta sessão

### 2026-10-28 — Diagnóstico do C4 (aspecto bug)

**Encontrado:** `compute_f8_mm_frontier.py` linha ~95: `C_score_vec[:, j] = np.where((x >= 90) & (x <= 180), 0.0, 1.0)` define aspect com valores brutos {0,1} (amplitude=1,0) em vez de usar `C_vec_raw[:, j]` que está L2-normalizado (amplitude=0,103). Inflação de 9,7× no peso efectivo do aspect.

**Consequência:** TV do score vec na C1 cai para quase 0 (aspect domina e está mal escalado), portfolios vec da C1 são completamente diferentes dos do factorial (484/500 mismatches), Q2 sobe artificialmente para 99,8%.

**Fix:** substituir a reimplementação local do score vec por `scoring.make_scorers()`. Assert rho_j contra amplitudes.json adicionado como guarda.

**Protecção futura:** regra anti-reimplementação no código — qualquer script que precise de `saw_vec` importa de `scoring.py` e não define a função localmente.

**Quarto episódio do mesmo padrão:** Q3 (float32), F8 v2 (injection bug), coincidência dos 210, e agora aspecto na C1. Padrão: bug não é detectado pela guarda anti-X_adj_vec porque usa um nome diferente. Solução definitiva: assert a 1e-12 antes de qualquer MC.
