# Estado actual — handoff para próxima sessão

**Ramo:** `writing-santiago` HEAD `90a4549`.

**§8 FECHADA.** Todos os três pontos pendentes da sessão anterior foram resolvidos no commit `90a4549`:
1. `\SantSNRegadiosPct` = 3.6% — denominador corrigido para o polígono dos três concelhos (387 km²; SHA `d550883c`); numerador = só Regadios (13.868 km²).
2. `tab:sant-dev` — 18 linhas cobrindo todos os DEV-SANT-* + Holm + DEV-FOGO-E1B-001; colunas Phase/Date/What/Qty seen/Verdict; E1-ABAR adicionado; K6 sem "K5(b) sign changes on S-T".
3. Fracções na fronteira: `\FrontFracFogo` = 0.0093% (181/1 944 653), `\FrontFracSN` = 1.91% (1 493/77 995); S5 com ressalva quantitativa. S-T fica para a Athena.

`make check` passa com 0 falhas. R10 (rerun no log) é artefacto de compilação.

**Próximo passo:** Bloco 2 — correcções ao texto do Fogo (§§1–7). Não depende de nada do Santiago.

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
- Bloco 0: CONCLUÍDO (ea86be2).
- Bloco 1: CONCLUÍDO (90a4549). `santiago.tex` + `supplementary.tex` com §8 completo,
  `tab:sant-dev` (18 linhas, todos DEV-SANT-*), parágrafo dos desvios reescrito,
  `\SantSNRegadiosPct`=3.6%, `\FrontFracFogo`=0.0093%, `\FrontFracSN`=1.91%.
  `make check` passa com 0 falhas.
- Bloco 2 (PENDENTE): correcções ao texto do Fogo (§§1–7). Ver Fase D para lista.

**Fase C — sensibilidades** (paralela, só descritivas):
SENS-AGR, S-N a 1,25 km, S5 com perm categórico, SENS-ZDTI-DISTRIB.
Correm com run_santiago_mc.py congelado, sem gates nem previsões novas.

**Fase D — limpeza antes da submissão (uma sessão):**
- Motor de compilação: decidido pdflatex, Makefile atualizado (root), fonte única
  paper/manuscript/main.tex, src/main.tex removido.
  **PENDENTE: escolher pdflatex como único motor (remover variantes `(xelatex variant)`
  do whitelist do check_consistency.py); corrigir linhas com overflow >1 pt em vez de
  as pôr no whitelist — 13.12 pt e 20.05 pt são visíveis no PDF.**
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
- **PENDENTE (Athena): clone limpo — `git clone && make paper && make check` ambos
  exit 0; confirmar que build_paper.py funciona em Linux.**
- **PENDENTE: FrontFracSN, FrontFracST, FrontFracFogo** (fracção de portefólios na
  fronteira com pesos nominais); scripts/compute_descriptive.py tem a lógica para
  S-N; S-T e Fogo precisam de correr na Athena (16.7M e 1.94M triplos).
  Quando existirem, trocar a ressalva qualitativa da S5 pela quantitativa.
- **PENDENTE: \SantSNRegadiosPct** (4.25%, scripts/compute_descriptive.py) usa
  convex hull dos candidatos como proxy da área S-N. Melhorar com polígono concavehull
  ou fronteiras municipais de Praia+SãoDomingos+RibeiraGrandeSantiago se disponíveis.
