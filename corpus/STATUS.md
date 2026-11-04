# Estado actual — handoff para próxima sessão

**Ramo:** `writing-santiago` HEAD `180ee60` (4 commits acima de `origin/main` ea86be2).
PR aberto em: https://github.com/Jazancort/mcdm-landfill-pareto-paper/pull/new/writing-santiago

**Bloco 1 pronto para revisão.** `santiago.tex` com §8 completo; compilação 33 páginas, bibtex funcional (0 citações indefinidas), 0 marcadores ativos.

**Próximo passo:** Julio revê `paper/manuscript/santiago.tex` e legenda do `fig:kappa`. Depois abrir PR e fazer merge para main.

**Avaliação do Santiago fechada (v2, commit d02a324, tag predictions-eval-v2).**
Bloco 0 completo: 219 macros em `macros_santiago.tex` (SHA verificado, 5 ficheiros),
K6 CIs descritivos calculados (`santiago_k6_ci.py`, percentile bootstrap B=2000,
SeedSequence(20261104)), figura `fig_kappa_santiago.pdf` com três curvas e bandas de IC
(Wong palette, fig_utils), `\input` no preâmbulo sem colisões. Motor: pdflatex (0
indefinidos, 31 páginas, exit 1 não-fatal — ver Fase D).

---

## O que está fechado

- Commit da avaliação: `d02a324` (eval-v2-rewrite)
- Tag: `predictions-eval-v2` aponta para `e9850ba` (registo dos resultados)
- JSON selado: `results/santiago/santiago_predictions_v2.json`
  SHA-256: `1fbc412b8ace6bdbd07d74f890f1460a2acdc268ce45ed59fc2a7900e520cf80`
- Errata S6 S-T: "efeito ausente (trios idênticos 500/500)", p não se aplica
- 28 REG OK, todos os gates PASS dentro da avaliação

## Tabela de resultados (v2, κ=200)

| Previsão | S-T | S-N |
|---|---|---|
| S0 | Confirmada (500/500; R=0) | Confirmada |
| S1 mm > vec | Confirmada: +15,8 [12,6; 19,0] | Confirmada: +25,2 [21,0; 29,2] |
| S2 opt < grd | Efeito ausente (0 contra 0) | Sinal oposto: −64,4 [−68,6; −60,0] (4 contra 326) |
| S3a | Confirmada (W 80,2; V 84,2) | Confirmada (W 99,2; V 98,6) |
| S3b V < W | Não confirmada: +4,0 (69 contra 49; p=0,080 McNemar) | Confirmada: −0,6 (0 contra 3; p=0,25 binomial) |
| S4 | Descritiva | Descritiva |
| S5 | Não testável (perm 0,617) | Confirmada: 98,6% |
| S6 R_grd > R_opt | Efeito ausente (trios idênticos 500/500) | Confirmada: Δ 13,44 [12,96; 13,93] |
| S7a R(E1-B) > 0 | Confirmada: 0,93 [0,84; 1,02]; 35,6% zeros (Fogo: 35,4%) | Confirmada: 0,06 [0,05; 0,08]; 79,6% zeros |
| S7b E1-B < E1-W | Confirmada: Δ [1,71; 2,18] | Confirmada: Δ [0,25; 0,38] |
| K5 (descritivo) | Sinal nulo em (a) e (b) | Mesmo sinal: (a) +96,8/+100; (b) −36,5/−33,3 |

## Três mensagens principais

1. **S2 e S6 juntas.** No S-N, Q2 e R concordam: o óptimo é melhor nas duas métricas.
   No S-T, a questão não se põe — o greedy encontra o trio óptimo em todos os
   sorteios a partir de κ=200.

2. **S7a.** No S-T, fracção de zeros (35,6%) ≈ Fogo (35,4%). No S-N, confirmada
   formalmente mas efeito de 0,06 pp sem importância prática. Dizer no texto.

3. **S3b.** Os dois ramos dão sentidos opostos.

## Protocolo em vigor

Só levanto um problema se mudar um veredicto. Tudo o resto vai para a lista da Fase D.

## Fases restantes

**Fase B — escrita:**
- Bloco 0: CONCLUÍDO (ea86be2). 219 macros em `macros_santiago.tex` (K1–K4 com
  ficheiro:linha A5, K6 por κ com CIs, Tabela A do stage3b), `verify_macros_permanent.py
  --santiago` difere 219 linhas contra temp. K6 CIs: `santiago_k6_ci.json` (SHA
  88fc473c…), percentile bootstrap B=2000. Figura `fig_kappa_santiago.pdf`: 3 curvas
  (Fogo, S-T, S-N), bandas de IC, Wong palette, fig_utils.
- Bloco 1: PRONTO PARA REVISÃO (180ee60, ramo writing-santiago). `santiago.tex`:
  §8.1 Tabela A (9 linhas); §8.2 Tabela B (16 previsões S0–S7b K1–K6 com coluna
  Fogo com valores reais para S5/S6/S7a/S7b e §\ref para os restantes); texto
  S2+S6/S7a/S3b/K5+K6; figura option A (fig_kappa_santiago.pdf).
  Citações: bibtex funcional (0 indefinidas). Marcadores: 0 ativos.
  Fonte única: paper/manuscript/main.tex (src/main.tex removido). Makefile
  atualizado para pdflatex + paper/manuscript/ como fonte.
  Pendente: aprovação das tabelas; suppl_wrapper microtype fix (Fase D).
- Depois: §7 (abstract com Santiago), highlights, §9 Discussion, §10 Conclusion.

**Fase C — sensibilidades** (paralela, só descritivas):
SENS-AGR, S-N a 1,25 km, S5 com perm categórico, SENS-ZDTI-DISTRIB.
Correm com run_santiago_mc.py congelado, sem gates nem previsões novas.

**Fase D — limpeza antes da submissão (uma sessão):**
- Motor de compilação: decidido pdflatex, Makefile atualizado (root), fonte única
  paper/manuscript/main.tex, src/main.tex removido.
- suppl_wrapper microtype: `pdfTeX error: auto expansion is only possible with
  scalable fonts` — fix: `\usepackage[protrusion=true,expansion=false]{microtype}`
  em suppl_wrapper.tex. Até lá, tab:orient_conv e tab:e7grid ficam indefinidas (3
  referências, pré-existentes).
- thumbnails/: copiar `thumbnails/cas-email.jpeg` do template CAS-DC para o repo;
  a sua ausência faz pdflatex sair com exit 1 em vez de exit 0.
- Referências por resolver: após compilar `suppl_wrapper.tex` primeiro, confirmar
  `grep -cE 'Reference .* undefined' main.log` devolve 0.
- Frase do E7: "as pre-registered (PRESPEC E7 §6)" → "as specified in
  PRESPEC_E7_KAPPA.md" (§7 classifica E7 como exploratório; "pre-registered" é
  reservado para Santiago e E1).
- merge para main (já feito); errata 28% → 35,4% no CHANGELOG do Zenodo
- run_e1.py marcado como INVALID; remover cópia duplicada run_e1_v3.py
- repor asserts A2/A3 com valores actuais
- refs.bib com year = {2012}
- *, w0 na assinatura
- corrigir texto do DEV-GPU-001
- lista de erratas acumuladas até lá
