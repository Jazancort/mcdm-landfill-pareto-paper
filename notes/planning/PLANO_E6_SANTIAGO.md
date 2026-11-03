# Plano: E6 (mecanismo sintético) + Instância Santiago

> **SUPERSEDED — historical draft, not binding.**
> This document was a working draft written before PRESPEC_SANTIAGO.md was committed.
> It is retained for audit trail only.
> Authoritative protocol: PRESPEC_SANTIAGO.md (tag `prespec-santiago-f0-amend-final`)
> + Amendments A5 (tag `prespec-santiago-a5`), A5a (tag `prespec-santiago-a5a`),
> A5b (tag `prespec-santiago-a5b`).
>
> Known divergences from PRESPEC (do NOT follow this document):
> - DEM: this draft mentions Copernicus GLO-30; PRESPEC declares ASTER GDEM v3.
> - Wells: this draft says "omit from start"; PRESPEC uses contingency C-2 (omit only if OSM < 20 features).
> - Seed 42: this draft does not mention seeds; PRESPEC_A5b forbids seed 42 for Santiago.

Criado: 2026-10-XX  
Revisto: incorpora correcções de validação (sign error P2, P3 reformulada, P4 nova,
TV_W §6.4, family zero-inflated, 30 réplicas, regras Santiago)  
Status: rascunho final — commitar PRESPEC_E6.md antes de qualquer run

---

## Contexto e motivação

O artigo tem três camadas de evidência para a decomposição TV_B/TV_W:

1. **Analítica** — Theorem 1: optimal assembly é eficiente se e só se TV_W = 0. Exacto.
2. **Empírica em Fogo** — E1, E4, F8: quatro pontos numa única instância.
3. **Sintética** — E5 (405 instâncias): impõe amplitudes em score e objectivos
   em conjunto, tornando optimal assembly eficiente por construção. O manuscrito
   (§8.6) declara explicitamente que E5 "does not test Theorem 1".

**O E6 corrige a falha do E5**: impõe amplitudes só no score, objectivos em
min-max, e varia TV_B e TV_W de forma independente. É estruturalmente idêntico
ao E1, generalizado a instâncias sintéticas com distribuições controladas.

**Santiago** é evidência secundária: testa se as magnitudes de Fogo (25–43 pp)
se reproduzem noutra instância com estrutura de amplitude diferente.

---

## Parte 1 — E6: mecanismo sintético (score-only amplitude manipulation)

### 1.1 Diferença crítica E5 vs E6

| Propriedade | E5 | E6 |
|---|---|---|
| Amplitudes no score | Sim | Sim |
| Amplitudes nos objectivos | Sim (mesmo factor) | **Não** — min-max fixo |
| Testa Theorem 1 | Não — trivialmente verdadeiro | Sim |
| TV_W governa optimal loss? | Não testável | Testável (P2) |
| TV_B amplifica TV_W? | Não testável | Testável (P3) |
| Direcção importa? | Não testável | Testável (P4) |

### 1.2 Design

**Instâncias**: Fogo geometry (fogo_trios.npy, k=3, κ=200, d_min=10 km, N_adm=389)
com colunas de critérios redrawadas de distribuições sintéticas independentes.
Os trios e as restrições de separação são os de Fogo; só mudam as distribuições
das colunas.

**Razão de usar a geometria de Fogo**: os trios e as restrições de separação já
estão computados e são os mesmos do estudo principal. A geometria é instrumental;
o que muda são as amplitudes ρ_j geradas pelas novas distribuições.

**Famílias de distribuição** (4 famílias × 30 réplicas = 120 instâncias):

| Família | Especificação | Propriedade |
|---|---|---|
| Lognormal | LogN(μ=0, σ=1) | Assimétrica positiva, sem zeros |
| Beta(1,3) | — | Assimétrica, massa perto de 0, sem zeros exactos |
| Uniforme | U(0,1) | Sem concentração; TV_W esperado baixo |
| Zero-inflated | π=0.90 zeros + LogN(μ=0, σ=1) | Replica a estrutura extrema de perm |

A família zero-inflated é essencial: reproduz a estrutura que motivou o artigo
(90% de zeros em perm). As três primeiras não têm massa pontual em zero e podem
não gerar os TV_W extremos observados em Fogo.

**30 réplicas por família** (não 5): o que importa para generalização é o número
de instâncias, não de sorteios. Com 30 instâncias, cada família tem potência
estatística adequada para P2 (detecção de ρ_s ≠ 0 com ≥80% de instâncias).

**Factores (3)**:

| Factor | Níveis |
|---|---|
| TV_W alvo | tw ∈ {0, 0.10, 0.199, 0.30} |
| TV_B alvo | tb ∈ {0, 0.249} |
| Direcção | {inflate, deflate} para j* = argmax_{j∈G_g} w_j em cada grupo |

**7 células por instância**:

| Célula | TV_B | TV_W | Direcção | Previsão |
|---|---|---|---|---|
| M | 0 | 0 | — | P1: Q2_opt = 100% |
| B | 0.249 | 0 | — | P1: Q2_opt = 100% |
| W_inf(L) | 0 | 0.10 | inflate | P2 (nível baixo) |
| W_inf(F) | 0 | 0.199 | inflate | P2 (nível Fogo) |
| W_inf(H) | 0 | 0.30 | inflate | P2 (nível alto) |
| V_inf(F) | 0.249 | 0.199 | inflate | P3 (efeito TV_B) |
| W_def(F) | 0 | 0.199 | deflate | P4 (direcção) |

**Scope declarado**: E6 testa só optimal assembly. Greedy assembly não é testada:
colunas sintéticas independentes (sem autocorrelação espacial) confundem o efeito
de foreclosure; greedys de Fogo usam a correlação espacial real.

### 1.3 Definição de TV_W (§6.4 do artigo)

A formula do artigo (§6.4) é:

```
TV_W = sum_g W_g * TV_{W,g}
TV_{W,g} = 0.5 * sum_{j in G_g} |w_j^eff/W_g^eff - w_j/W_g|
```

onde w_j^eff = w_j * A_j / sum_k w_k * A_k.

Esta fórmula NÃO coincide com a fórmula do plano original "0.5 Σ_g Σ_j (w_j/W_g)|A_j/Ā_g − 1|".
Os níveis-alvo (0.10, 0.199, 0.30) têm de ser calibrados sobre a definição §6.4.

**Calibração**: para cada instância e nível tw, calcular δ_g por bissecção tal que
TV_W(A_j) = tw sob a fórmula §6.4. Verificar que A_j > 0 em todos os critérios
e A_{j*} ≤ 3.

### 1.4 Construção inflate / deflate

Em cada grupo G_g, identificar j* = argmax_{j∈G_g} w_j (maior peso dentro do grupo).

**Inflate (célula W_inf)**:
```
A_{j*} = 1 + delta_g    (delta_g > 0, calibrado para TV_W = tw)
A_{j≠j*} = 1
```

**Deflate (célula W_def)**:
```
A_{j*} = 1 - delta_g    (mesmo delta_g que inflate; TV_W idêntico)
A_{j≠j*} = 1
```

Restrição: verificar A_{j*} > 0 na célula deflate (pode falhar para tw=H e famílias
com ρ_{j*} pequeno; declarar como desvio se ocorrer).

**Célula B** (TV_W=0, TV_B=tb):
```
A_j = Abar_g para todo j in G_g
```
onde Abar_g são escalados por grupo para que TV_B = tb sob a fórmula §6.4.

**Score** (todas as células excecto M):
```
score(a) = sum_j w_j * A_j * n_j^mm(a)
```

**Objectivos** (todas as células):
```
F_g(a) = sum_{j in G_g} w_j * n_j^mm(a)    (sem factor A_j)
```

### 1.5 Quatro previsões pré-declaradas

**P1 — Assertion (Theorem 1 generalizado)**

Para TODAS as 120 instâncias × TODAS as famílias, células M e B:

```
TV_W = 0  ⟹  Q2_optimal = 100%
```

P1 é uma assertion, não uma hipótese. Se falhar: bug na construção das amplitudes
ou objectivos não estão em min-max. Verificar antes de analisar P2–P4.

**P2 — Previsão ordinal primária**

Para cada instância × família, Q2_opt nas células W_inf é monotone não-crescente em tw.

Critério de confirmação:
- (a) ρ_s(TV_W, Q2_opt) < 0 em ≥ 80% das instâncias por família
- (b) Média(Q2_opt(tw=H)) < Média(Q2_opt(tw=0)) − 5 pp

Nota: ρ_s < 0 (negativo) porque Q2 diminui quando TV_W aumenta. O plano original
tinha ρ_s ≥ 0, o que é o sinal errado.

Falsificação: ρ_s ≥ 0 em > 20% das instâncias dentro de alguma família.

**P3 — Amplificação pelo TV_B (replica E1)**

Para cada instância × família, TV_W fixo = 0.199:

```
Q2_opt(V_inf) ≤ Q2_opt(W_inf)
```

Critério de confirmação: Q2_opt(V_inf) < Q2_opt(W_inf) em ≥ 70% das instâncias.

Fundamento: E1 encontrou W=64.2% vs V=56.8% (TV_B adicionou 7.4 pp de perda).
P3 testa se esta amplificação se generaliza. P3 NÃO prediz que TV_B não tem
efeito; prediz que TV_B agrava a perda.

Falsificação: Q2_opt(V_inf) > Q2_opt(W_inf) + 5 pp em > 30% das instâncias.

**P4 — Direcção da distorção (testa Remark rem:TVW)**

Para cada instância × família, TV_W fixo = 0.199, TV_B = 0:

```
Q2_opt(W_inf) < Q2_opt(W_def)
```

Critério de confirmação: Q2_opt(W_inf) < Q2_opt(W_def) em ≥ 70% das instâncias.

Fundamento: Remark rem:TVW declara que TV_W > 0 não é suficiente para perda sem
mais condições. P4 testa se inflar o critério de maior peso dentro do grupo é
mais custoso que deflacionar o mesmo critério ao mesmo TV_W. Previsão sem base
analítica — declarada antes de qualquer run.

Falsificação: Q2_opt(W_inf) > Q2_opt(W_def) em > 30% das instâncias.

### 1.6 Âmbito das previsões P2–P4

P2–P4 são empíricas. NÃO são consequências do Theorem 1. O teorema é existencial:
garante Q2_opt=100% se TV_W=0. Não implica monotonia, amplificação, nem assimetria.

Linguagem a usar no artigo se P2–P4 forem confirmadas: "on Fogo and across [N]
synthetic instances with four marginal families" — não "in general" nem remover
"on this instance" de forma absoluta.

### 1.7 Regras de decisão

| Condição | Consequência para o artigo |
|---|---|
| P1 falha em alguma instância | Bug — abortar |
| P1 confirma, P2 confirma | "on Fogo and in [N] synthetic instances" |
| P1 confirma, P2 falha | Manter "on this instance" |
| P3 confirma | "A amplificação do E1 generaliza-se a instâncias sintéticas" |
| P3 falha | Novo resultado: TV_B reduz perda nalgumas distribuições |
| P4 confirma | Resolve Remark rem:TVW: direcção importa |
| P4 falha | Remark rem:TVW permanece em aberto |

### 1.8 Output esperado

```
results/e6/e6_instances.csv
  colunas: family, replicate, cell, Q2_optimal, SE, TV_W_actual, TV_B_actual

results/e6/e6_summary.csv
  por (family, cell): mean(Q2_opt), SD, fraction_confirming

results/e6/e6_p2_spearman.csv
  por (family, replicate): rho_s
```

Figura: Q2_opt vs tw_level por família (4 painéis); scatter W_inf vs W_def (P4).

### 1.9 Passos de implementação

1. Commitar `corpus/PRESPEC_E6.md` antes de qualquer run
2. Escrever `scripts/e6_generate_amplitudes.py` — constrói A_j para 7 células
3. Escrever `scripts/run_e6.py` — corre 7 células × N=200 draws × 120 instâncias
4. Verificar timing com 1 instância antes de submeter job completo na Athena
5. Verificar P1 antes de analisar P2–P4
6. Criar figura e tabela de sumário

**Parâmetros**: N=200 draws, κ=200, seed=42, k=3, fogo_trios.npy.

---

## Parte 2 — Santiago: segunda instância real

### 2.1 Propósito e limite

Santiago testa se as magnitudes de perda (25–43 pp) são específicas de Fogo ou
se ocorrem com outra estrutura de amplitude no mesmo modelo de critérios.

Se o E6 existir, Santiago responde a uma pergunta diferente e mais restrita:
"as magnitudes empíricas de Fogo são atípicas relativamente a outras instâncias
do mesmo domínio?" É uma pergunta útil, mas secundária.

Melhor localização no artigo: tabela compacta Fogo/Santiago na §7.7, com detalhes
no suplementar. Não justifica uma secção nova.

### 2.2 Critérios de inclusão (pré-declarados)

A instância entra no artigo se e só se, antes de qualquer run de Q2:

1. Todos os dados brutos são de fontes públicas com DOI ou URL estável.
2. Os pesos AHP são os de Fogo, ou renormalizados se algum critério for omitido
   (ver §2.6b), com a transferência declarada explicitamente.
3. N_adm ≥ 100 após exclusões.
4. `corpus/PRESPEC_SANTIAGO.md` está commitado com TV_W calculado dos dados brutos
   e as previsões P_S1–P_S4 escritas.

### 2.3 Ilha escolhida

Santiago (Cabo Verde) — área ~991 km². Escolha feita antes de qualquer extracção
de dados; não é baseada nos resultados.

### 2.4 Fontes de dados por critério

| Critério | Fonte | Resolução | Proxy |
|---|---|---|---|
| **perm** | ver §2.4a | — | Condicionado |
| slope | Copernicus DEM GLO-30 | 30 m | Não |
| roads | OpenStreetMap (GeoFabrik Africa, Cabo Verde) | — | Não |
| rivers | OpenStreetMap + SRTM drainage | — | Verificar ≥20 features |
| aspect | DEM GLO-30; binário: azimuth ∈ [90°,180°] | 30 m | Não (mesma definição de Fogo) |
| coast | OSM coastline | — | Não |
| protected | WDPA (versão e data de acesso a declarar) | — | Não |
| wells | ver §2.4b | — | Condicionado |
| urban | OSM building footprints | — | Não |
| aero | OSM + dados oficiais (aeródromo RAI) | — | Não |
| cult | ESA WorldCover 2021 v200, **classe 40 apenas** | 10 m | Parcial |

Nota cult: classe 40 = cropland. A classe 10 é tree cover — não usar.

#### 2.4a Política para perm (pré-declarada)

Em Fogo, perm é uma **distância** a uma zona de permeabilidade desfavorável
(medida em metros, máximo 532 m, 350 zeros). Usar clay fraction do SoilGrids
(variável contínua sem zeros) é um critério diferente: muda a natureza do
critério que gerou o efeito principal. Não é uma substituição directa.

Prioridade:
1. Tentar reconstruir a distância à zona de permeabilidade desfavorável para
   Santiago, a partir de: (a) geologia pública do INGRH ou do Serviço de
   Recursos Naturais de Cabo Verde; (b) limiar de textura do SoilGrids como
   proxy de zone boundary.
2. Se impossível: usar clay fraction como proxy, declarando explicitamente que
   perm(Santiago) é um critério diferente de perm(Fogo) e que a comparação
   directa das magnitudes é limitada.
3. Em qualquer caso: não usar sem declaração prévia no PRESPEC.

#### 2.4b Política para wells (pré-declarada)

Omitir desde o início e renormalizar os 10 pesos AHP restantes para soma = 1,
com w_wells = 0.055 redistribuído proporcionalmente. Razão: dados de wells em
OSM para Santiago são muito provavelmente < 20 features fiáveis.

Declarar a omissão e os pesos corrigidos no PRESPEC antes de qualquer run.

### 2.5 Grelha de candidatos (pré-declarada)

Espaçamento: **mesmo de Fogo** (verificar no estudo de origem; ~1 km). Com 1 km
em Santiago (~991 km²) o número de candidatos brutos é ~900. Verificar se a
enumeração de trios C(N_adm, 3) com d_min=10 km é viável na Athena antes de
submeter o job.

Regra de afastamento entre sítios seleccionados: 10 km (mesma de Fogo).

Se N_adm < 100 após exclusões: alargar o espaçamento e declarar como desvio
no PRESPEC antes de qualquer run.

### 2.6 Regras de exclusão (mesmas de Fogo)

A única exclusão de Fogo é `dist_protected = 0` (dentro de área protegida).
Usar exactamente as mesmas regras em Santiago. Não acrescentar distâncias de
buffer a rivers ou coast.

Fundamento: as regras de exclusão determinam quais candidatos entram em df_via,
que é a distribuição que queremos medir. Acrescentar regras altera as
distribuições dos critérios — exactamente o que se quer isolar entre as ilhas.

### 2.7 Pesos AHP (transferência declarada)

Usar os pesos de Fogo (Tabela 2) sem recalibração, excepto se wells for omitido
(§2.4b). Declarar no PRESPEC e no texto: "os pesos são transferidos de Fogo para
isolar o efeito da distribuição dos critérios; a instância de Santiago não é um
estudo de decisão real mas uma transferência de instância para testar as magnitudes
de loss sob um modelo de valor fixo."

Esta declaração é necessária porque o artigo, na §5.4 e nas Limitações, critica
exactamente a insensibilidade dos pesos AHP aos intervalos dos critérios.
A transferência deve ser apresentada como um instrumento de comparação controlada,
não como uma afirmação sobre as preferências de qualquer decisor real.

### 2.8 Previsões ordinais (a commitar com TV_W dos dados brutos)

Estas previsões são rascunho. Os valores concretos de TV_W e TV_B são calculados
dos dados brutos e commitados antes de qualquer run de Q2.

**P_S1 — Regressão (assertion)**

SAW/mm/optimal = 100% em Santiago. Falha = bug.

**P_S2 — Posição relativa ao E6 (primária)**

Depois de correr o E6, calcular o intervalo de Q2_opt observado para TV_W ≈
TV_W(Santiago) e na família mais próxima da distribuição de Santiago.

Previsão: Q2_opt(SAW/vec/Santiago) cai dentro do intervalo [min, max] do E6
para o mesmo TV_W e família correspondente.

Nota: a versão original de P_S2 previa a loss a partir da magnitude de TV_W.
Isso contradiz a Remark rem:TVW do artigo, que diz que TV_W sozinho não determina
a perda. A formulação correcta é posicionar Santiago no espaço do E6.

**P_S3 — Padrão B/W/V**

Se m_eff(Santiago) < 5 (distorção concentrada): Q2_opt segue ordenação B > W > V
(replica E1).

Se m_eff(Santiago) ≥ 8 (distorção difusa): Q2_opt(B) ≈ Q2_opt(V) (without
concentration, TV_B has little additive effect).

**P_S4 — Critério dominante**

O critério que governa TV_W(Santiago) é o que tem maior variação de
w_j^eff/W_g^eff dentro do seu grupo — não necessariamente o de maior ρ_j.
Identificar e declarar esse critério a partir dos dados brutos antes de correr Q2.

### 2.9 Critérios de validade pós-extracção

Verificar antes de qualquer Monte Carlo (informados pelos dados, não por Q2):

1. N_adm ≥ 100
2. Todos os critérios com variância > 0 em df_via
3. TV(vec, Santiago) > 0.05 (há distorção mensurável)

Nota: o critério original "nenhum critério com > 90% dos candidatos no mesmo valor"
foi retirado: em Fogo, perm tem exactamente 350/389 = 90% de zeros, e esta
concentração é o ponto de entrada do artigo. O critério eliminaria a estrutura
que se quer testar.

### 2.10 Pipeline GIS (passos técnicos)

```
1. Confirmar espaçamento de Fogo no estudo de origem (provavelmente ~1 km)
2. Copernicus GLO-30 BBOX: -25.35, 14.85, -23.45, 15.40
   → gdaldem slope, gdaldem aspect (binário: azimuth ∈ [90°, 180°])
3. GeoFabrik (Cabo Verde) → roads, rivers, coast, urban, aero
   → verificar rivers: n_features ≥ 20 antes de usar
4. WDPA → protected (declarar versão e data)
5. Tentativa perm: geologia INGRH/serviços públicos → distância à zona desfavorável
   Fallback: SoilGrids clay_content_0-5cm_mean (declarar como proxy diferente)
6. ESA WorldCover 2021 v200, tile S15W024, classe 40 apenas → cult
7. Wells: omitir (§2.4b); renormalizar pesos
8. Grelha ~1 km dentro dos limites terrestres → 800-1000 candidatos brutos
   → aplicar exclusão dist_protected = 0 → df_via_santiago.csv
9. Verificar critérios de validade pós-extracção
10. Commitar PRESPEC_SANTIAGO.md com TV_W dos dados brutos + P_S1–P_S4
11. Verificar enumeração de trios C(N_adm, 3) com d_min=10 km (pode ser maior que Fogo)
12. Correr mc_unified adaptado na Athena
```

### 2.11 Riscos

| Risco | Prob. | Mitigação |
|---|---|---|
| Geologia perm indisponível | Alta | Fallback SoilGrids com declaração de proxy diferente |
| Rivers OSM incompleto | Média | Proxy SRTM drainage; verificar n_features |
| Enumeração de trios inviável (N_adm grande) | Média | Amostrar trios em vez de enumerar; declarar desvio |
| N_adm < 100 | Baixa | Alargar espaçamento, declarar desvio |
| TV_W(Santiago) < 0.05 | Média | Reportar: caso sem concentração produz loss residual; resultado esperado |
| WDPA cobertura incompleta em Cabo Verde | Média | Usar WDPA + verificar com legislação local; declarar limitação |

---

## Sequência de execução

```
Agora:
  1. Rever este documento e confirmar decisões respondidas abaixo
  2. Commitar corpus/PRESPEC_E6.md (versão formal das previsões de §1)

Semana 1:
  3. Implementar e6_generate_amplitudes.py + run_e6.py
  4. Verificar timing com 1 instância antes de enviar job completo
  5. Correr E6 na Athena (~4h estimado, a verificar)
  6. Verificar P1 antes de analisar P2–P4
  7. Iniciar pipeline GIS Santiago (confirmação do espaçamento de Fogo)

Semana 2:
  8. Commitar PRESPEC_SANTIAGO.md com TV_W dos dados brutos
  9. Correr Monte Carlo em Santiago
  10. Integrar E6 e Santiago no artigo

Pré-condição obrigatória: fechar os itens A1–A6 do processo de revisão antes
de E6 e Santiago. A1 pode alterar as amplitudes de referência usadas no E6.
```

---

## Decisões respondidas

| Questão | Resposta |
|---|---|
| Espaçamento da grelha Santiago | Mesmo de Fogo (~1 km); confirmar no estudo de origem |
| Proxy perm Santiago | Tentar primeiro reconstruir distância; clay fraction como último recurso com declaração |
| Wells Santiago | Omitir desde o início; renormalizar 10 pesos proporcionalmente |
| Réplicas E6 | 30 por família × 4 famílias = 120 instâncias; 200 sorteios |
| Posição E6 no artigo | Subsecção curta em §7 (não suplementar): é evidência sobre o mecanismo principal |
| Posição Santiago no artigo | Tabela compacta Fogo/Santiago em §7.7; detalhes no suplementar |
| Email Alkaradaghi | Não enviar |
