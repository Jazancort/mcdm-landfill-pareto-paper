# Plano de Trabalho — Paper MCDM Landfill (Omega)

**Última actualização:** 2026-10-28  
**HEAD actual:** b1d715a  
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

**Problema:** A célula "score vec vs fronteira mm" reporta Q2=99,8% e 99,6%. A Tabela 5 (factorial) dá 56,8% e 66,2% para as mesmas células. A contradição implica que o texto com "assimetria de 28×" (C4) está errado.

**Causa raiz confirmada:** `C_score_vec[:, aspect]` era definido como valores brutos {0,1} (amplitude=1,0) em vez do vetor L2-normalizado de `C_vec_raw[:, j]` (amplitude=0,103). Critério aspect inflacionado 9,7× na pontuação vec.

**Fix aplicado localmente** (commit pendente): substituída a reimplementação do score vec por `scoring.make_scorers()`, o mesmo que usam todos os outros scripts. Smoke test N=5 dá Q2≈60% (compatível com 56,8% esperado).

**Acções pendentes:**

- [x] **C0-fix APLICADO** (commit f52987c): `scoring.make_scorers()` substituiu a reimplementação bugada. rho_j assertion adicionada. MCDM_DATA_DIR env var necessária na Athena.
- [ ] **C0-1** RUNNING na Athena (tmux f8mm, `/tmp/f8mm_run.log`). Espera ~45 min.
- [ ] **C0-2..6** Após resultados da Athena.

**Skill/agent:** `research-coder` agent para Athena run, edição de main.tex directa depois.

**Protecção futura:** cada script de experiência deve importar `saw_sc` de `scoring.py` e fazer `assert np.allclose(saw_sc(w_ahp, 'vector'), ...)` contra o scorer canónico a 1e-12 antes de correr o Monte Carlo. Comentar no script com "ANTI-REIMPLEMENTAÇÃO: never reimplement saw_vec locally".

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

### PDF-2: §6.8 — Valores raw em vez de shift (A2, já tem macros)

**Estado:** macros `\TVvec{0.3113}`, `\DeltaLtwoshift{0.3101}`, `\DeltaLinfshift{0.2835}` existem.

- [ ] Verificar se `check_consistency.py` já guarda estes valores contra o PDF. (BAD_PHRASES já têm os raw: 0.3146, 0.3127, 0.2859.)
- [ ] Se §6.8 ainda tiver literais, substituir. **Provável que já esteja feito** (F475-4 cobriu).

---

### PDF-3: §5.4 — "≈1,0 pp in the other direction" deve ser 5,6 pp (A3)

**Estado:** `\FEightMMOptLoss{5.6}` existe. **Verificar se a linha 1131 de main.tex usa o macro correcto** — era onde o literal 5,6 estava hardcoded antes do F475.

- [ ] Rodar `grep -n "1\.0 pp in the other" main.tex` — se encontrar, substituir por `\FEightMMOptLoss pp`.

---

### PDF-4: §4.3 — aero na lista de critérios com mínimo 0 (A4)

**Estado:** provavelmente corrigido em F475-4 (item A4 do PLANO_REVISAO_9). **Verificar** que "perm, aspect, urban, cult, rivers" está em main.tex sem aero.

---

### PDF-5: §6.2 e eq.(20) — fórmulas na forma dos manuais (raw) contradizem eq.(9)

- [ ] **PDF-5** Localizar em main.tex a equação que define ρ_j na forma raw (`x_{ij}/||x_j||`). Substituir pela fórmula shift usada na implementação: `x̃_{ij}/||x̃_j||` com referência à eq.(9) e à nota do shift.

---

### PDF-6: §7.8 — "Seven cells yield 24,000 total draws" (A7)

**Estado:** corrigido em A7 (PLANO_REVISAO_9). `\EsixNdrawsTotal{168,000}` existe. **Verificar** no texto actual.

---

## PRIORIDADE 2 — Revisão f475928 (novos itens do segundo passe do revisor)

### R1: E1-V vs factorial SAW/vec/opt — draw-by-draw

**Problema:** §7.7 afirma "objectives, frontier, draws and feasible set are identical to the factorial (κ=200, 500 draws, space A′)". Se as sequências de draws forem diferentes, a frase é falsa. O F475-1 verificou 500/500 draws mas contra o F8, que é outra experiência.

**Teste a fazer localmente:**
```python
import pandas as pd
e1 = pd.read_csv("results/e1/e1_diag_bootstrap.csv")   # e1v_opt_nd por draw
fx = pd.read_csv("results/unified/mc_unified_raw.csv")  # ADAPT se necessário
fx = fx[(fx.agg=="SAW") & (fx.norm=="vector") & (fx.assembly=="optimal")].sort_values("draw")
print(len(e1), len(fx), (e1.e1v_opt_nd.values == fx.on_frontier.values).sum())
```

Resultado esperado: 500/500 (coincidência perfeita confirma draws iguais, como a probabilidade de 2,5% para coincidência por acaso sugere).

- [ ] **R1-1** Correr o teste acima; registar resultado.
- [ ] **R1-2** Se 500/500: actualizar TASKS.md de "verificado via agregados" para "verificado draw a draw". Frase §7.7 fica correcta.
- [ ] **R1-3** Se < 500: mudar §7.7 para "draws from the same Dirichlet distribution (seed=42, κ=200)".

**Skill/agent:** edição directa; PowerShell local.

---

### R2: Bootstrap B=10.000 vs B=2.000 inconsistência

**Problema:** O IC [4,0; 11,0] do E1 foi calculado com B=10.000 (diag_e1b_greedy.py), mas §5.4 e Tabela 6 dizem "2.000-replicate bootstrap". Além disso, o intervalo [3,8; 11,0] mencionado numa versão anterior não corresponde a nenhuma configuração.

**Decisão necessária — escolher UMA:**
- Opção A: Uniformizar para B=2.000 → [3,8; 11,2]; usar o macro `\nboot{2,000}` existente.
- Opção B: Declarar B=10.000 no E1 → manter `\nbootEone{10,000}` e escrever "95% paired bootstrap CI, B=\nbootEone, replicates" especificamente no parágrafo E1.

- [ ] **R2-1** Decidir a opção.
- [ ] **R2-2** Implementar: gerar macro `\EoneWVgapCI` a partir do script correcto; verificar que §7.7 usa o macro, não o literal.
- [ ] **R2-3** Adicionar MUST_FAIL para `[3.8; 11.0]` no check_consistency.py (intervalo que não corresponde a nenhuma configuração).

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
- Opção A: "tabela compacta, evidência secundária" (cita o E6 para generalização)
- Opção B: replicação completa do factorial + E1 (mesmo protocolo que Fogo)
- Recomendação: Opção B, com o mesmo protocolo do E1. Mas substituir "Confirmar" por "Testar" em todas as previsões.

**Decisão S-D2:** Aceitar as previsões S0–S6 como base?

| ID | Previsão | Tipo |
|---|---|---|
| S0 | SAW/mm/opt=100% e E1-B=100% | regressão (não evidência) |
| S1 | Q2(mm)−Q2(vec)>0 em greedy, IC exclui 0, se TV(vec)>0,05 | replicação destaque |
| S2 | óptima−greedy<0 para SAW/vec, se TV_W>0,05 | replicação inversão |
| S3 | E1-W<100% e E1-V<100%; \|W−V\|<5 pp | protocolo E1 |
| S4 | Agregação: sem previsão de sinal; reportar por célula | declarado descritivo |
| S5 | Se nenhum critério de Santiago tiver fracção zeros≥0,5: Q2(SAW/vec/opt)>56,8% | previsão arriscada ligada ao E6 |
| S6 | R(vec,opt)>R(mm,opt) em SAW | regret |

### PRESPEC — Fase 0 (commitar ANTES de extrair qualquer dado)

- [ ] **S-F0-1** Definir fontes, versões e datas de acesso para cada critério.
- [ ] **S-F0-2** Definir regra da grelha e triagem inicial (replicar critérios de exclusão de AzancortNeto2026 + Andrade 2015).
- [ ] **S-F0-3** Definir cada critério — incluindo planos A e B para o perm (SoilGrids 250m vs proxy) e limiar de acumulação dos rivers (fixar agora).
- [ ] **S-F0-4** Fixar pesos: transferidos de Fogo com renormalização se wells ou perm for ausente.
- [ ] **S-F0-5** Commitar o código de análise (freeze do commit hash).
- [ ] **S-F0-6** Escrever previsões como regras condicionais em função de (TV_B, TV_W, m_eff, fracção de zeros).
- [ ] **S-F0-7** Definir critérios de validade e frases para cada resultado possível.
- [ ] **S-F0-8** Definir regra do espaçamento da grelha: mesmo de Fogo (1 km?), aumentando 0,25 km até n_trios < limite fixado aqui.
- [ ] **S-F0-9** Planear dois controlos em Fogo: Fogo sem wells (pesos renormalizados) e Fogo com o mesmo substituto do perm.
- [ ] **S-F0-10** Declarar convenção de aspect: [90°, 180°] é convenção herdada de Fogo, não afirmação física sobre os alísios de Santiago.
- [ ] **S-F0-COMMIT** `git commit -m "feat: PRESPEC_SANTIAGO.md Fase 0 — pre-extraction"` — **ESTE COMMIT NÃO PODE SER ALTERADO DEPOIS**.

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

## Regras de processo

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
