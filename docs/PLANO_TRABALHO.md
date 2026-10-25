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

- [x] **C0-fix APLICADO** (commit f52987c): `scoring.make_scorers()` substituiu a reimplementação bugada.
- [ ] **C0-1** RUNNING na Athena (tmux f8mm, `/tmp/f8mm_run.log`). Espera ~45 min.
- [ ] **C0-2** `MCDM_DATA_DIR=.../scripts uv run python scripts/generate_macros_f8.py` na Athena; scp macros_f8.tex para local.
- [ ] **C0-3** Actualizar §7.4: substituir "assimetria de 28×", "0,2 pp" e "99,8%" pelos correctos. Nova assimetria: óptima mm→vec = 5,6 pp, vec→mm = 43,2 pp; greedy mm→vec = 27,6 pp, vec→mm = 33,8 pp.
- [ ] **C0-4** Remover 99,8%/99,6%/0,2 pp/28× de main.tex, suplemento, highlights e comentários de macros. Adicionar ao BAD_PHRASES.
- [ ] **C0-5** Adicionar invariante ao check_consistency: `\FEightVecMmOptQ == \QtwovecOptimal` (56,8%) e `\FEightVecMmGrdQ == \QtwovecGreedy` (66,2%).
- [ ] **C0-6** Commitar + push.

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

## PRIORIDADE 4 — Santiago (segunda instância, obrigatória para 9/10)

### Decisões necessárias (responder antes de escrever o PRESPEC)

**Decisão S-D1:** Qual o papel do Santiago no artigo?
- Papel decidido: replicação completa do factorial + E1 (protocolo idêntico ao Fogo). "Confirmar" substituído por "Testar" em todas as previsões.
- Posição no artigo: §7.10, paralelo ao §7.9 (E1).

**Decisão S-D2:** Previsões S0–S6 como base — aceites. Ramo S-L (pesos locais Cabral 2013) adicionado.

| ID | Previsão | Tipo |
|---|---|---|
| S0 | SAW/mm/opt=100% e E1-B=100% | regressão (não evidência) |
| S1 | Q2(mm)−Q2(vec)>0 em greedy, IC exclui 0, se TV(vec)>0,05 | replicação destaque |
| S2 | óptima−greedy<0 para SAW/vec, se TV_W>0,05 | replicação inversão |
| S3 | E1-W<100% e E1-V<100%; \|W−V\|<5 pp | protocolo E1 |
| S4 | Agregação: sem previsão de sinal; reportar por célula | declarado descritivo |
| S5 | Se nenhum critério tiver fracção zeros≥0,5: Q2(SAW/vec/opt,Santiago)>56,8% | previsão arriscada ligada ao E6 |
| S6 | R(vec,opt)>R(mm,opt) em SAW | regret |
| S-L | Com pesos locais (Cabral 2013): reportar TV e Q2; sem previsão de sinal vs S-T | ramo de sensibilidade |

### PRESPEC — Fase 0 (commitar ANTES de extrair qualquer dado)

- [ ] **S-F0-1** Definir fontes, versões e datas de acesso para cada critério:
  - **perm** — Plano A: carta geológica de Santiago (IDECV/INGT, `carto_base:geologia_santiago`), mesma regra litologia→permeabilidade de Fogo (`geologia_com_permeabilidade_calculada.shp`). Plano B: SoilGrids 250m, só como sensibilidade.
  - **wells** — OSM, mesma consulta de Fogo. Renormalização e controlo "Fogo sem wells" só se a regra falhar.
  - **rivers** — DEM, limiar de acumulação de fluxo **fixado aqui** antes de extrair dados.
  - **aspect** — leeward definido como [90°, 180°] (convenção herdada de Fogo, não afirmação física sobre os alísios de Santiago — **declarar explicitamente**).
- [ ] **S-F0-2** Grelha: 1 km × 1 km com ≥50% de terra (regra do repositório de Fogo). Resolver a diferença 524/473 entre ficheiros do GitHub e o artigo antes de definir a grelha.
- [ ] **S-F0-3** Regra de selecção do espaçamento: mesmo de Fogo; aumentar 0,25 km até n_trios < limite fixado agora. Medir só com geometria (sem critérios): `n_trios = int(np.trace(Av @ Av @ Av)) // 6`.
- [ ] **S-F0-4** Pesos: ramo S-T = transferidos de Fogo; ramo S-L = pesos locais Cabral 2013 (a confirmar na tabela original, região sul de Santiago). Renormalizar se algum critério for ausente.
- [ ] **S-F0-5** Commitar o código de análise (freeze do commit hash do scoring).
- [ ] **S-F0-6** Escrever previsões S0–S6 como regras condicionais em função de (TV_B, TV_W, m_eff, fracção de zeros). Cada previsão tem: regra de decisão + frase para o artigo + cenário de falha.
- [ ] **S-F0-7** Definir critérios de validade: instância inválida se < X sítios admissíveis ou n_trios < Y.
- [ ] **S-F0-8** Frases para cada resultado possível (aprovação, falha, inconclusivo).
- [ ] **S-F0-9** Instância opcional: Lemnos (Kontos et al. 2005) como terceira candidata — decidir inclusão aqui.
- [ ] **S-F0-10** Dois controlos em Fogo: (a) Fogo sem wells (pesos renormalizados); (b) Fogo com o mesmo substituto do perm. Declarar que servem para isolar o efeito da instância vs o conjunto de critérios.
- [ ] **S-F0-COMMIT** `git commit -m "feat: PRESPEC_SANTIAGO.md Fase 0"` — **IMUTÁVEL após push**.

### PRESPEC — Fase 1 (após extracção, antes de qualquer score)

- [ ] **S-F1-1** Hash dos dados extraídos.
- [ ] **S-F1-2** Calcular amplitudes, TV, TV_B, TV_W, m_eff e fracção de zeros por critério.
- [ ] **S-F1-3** Verificar critérios de validade da Fase 0.
- [ ] **S-F1-4** Resolver previsões condicionais (S5 especialmente: verificar fracção de zeros).
- [ ] **S-F1-COMMIT** `git commit -m "feat: PRESPEC_SANTIAGO.md Fase 1 — post-extraction"` — **IMUTÁVEL**.

### Pipeline Santiago (após PRESPEC Fase 1)

- [ ] **S-P1** `santiago_constants.py` equivalente ao `fogo_constants.py`.
- [ ] **S-P2** Fronteira, amplitudes e factorial (scripts da Athena, mesma estrutura).
- [ ] **S-P3** E1 equivalente (TV_W prediction test).
- [ ] **S-P4** Regret R para as 8 células.
- [ ] **S-P5** Dois controlos em Fogo (sem wells, com substituto perm).
- [ ] **S-P6** Reportar como §7.10 com protocolo análogo ao §7.9 (E1).
- [ ] **S-P7** Actualizar frase de generalização na §8 e Conclusão.

**Guardrail no código:** os scripts que calculam scores, portfolios ou Q2 para Santiago devem recusar correr se o commit da Fase 1 não existir. Implementar como `assert (ROOT / "PRESPEC_SANTIAGO_F1.lock").exists()`.

**Skill/agent:** `doc-coauthoring` para o PRESPEC; `research-coder` agent para o pipeline Athena; `feature-dev` skill para a integração no paper.

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
