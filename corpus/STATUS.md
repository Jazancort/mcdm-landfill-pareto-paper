# Estado actual — handoff para próxima sessão

**Ramo:** `eval-v2-rewrite` (este ficheiro está aqui, não em main).
Ao abrir a próxima sessão: `git switch eval-v2-rewrite`.

**Avaliação do Santiago fechada (v2, commit d02a324, tag predictions-eval-v2).**
Escrita, Bloco 0: gerar o macros_santiago.tex a partir do santiago_predictions_v2.json,
verificando o SHA (1fbc412b…), e juntá-lo ao verify_macros_permanent.py. O p da S3b é
calculado no gerador a partir das contagens. A seguir, a figura do κ com três curvas
(Fogo, S-T e S-N). Antes do Bloco 1, extrair do JSON os veredictos K1–K4 e K6. Depois,
Bloco 1: secção do Santiago.

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
- Bloco 0: gerar macros_santiago.tex a partir do JSON (SHA 1fbc412b); juntar ao
  verify_macros_permanent.py; calcular p da S3b no gerador a partir das contagens.
- Bloco 0b: figura do κ com três curvas (Fogo, S-T e S-N).
- Bloco 0c: extrair K1–K4 e K6 do JSON antes de escrever.
- Bloco 1: secção do Santiago.
- Depois: §7, abstract, highlights, §9.

**Fase C — sensibilidades** (paralela, só descritivas):
SENS-AGR, S-N a 1,25 km, S5 com perm categórico, SENS-ZDTI-DISTRIB.
Correm com run_santiago_mc.py congelado, sem gates nem previsões novas.

**Fase D — limpeza antes da submissão (uma sessão):**
- merge para main
- errata 28% → 35,4% no CHANGELOG do Zenodo (versões afectadas)
- run_e1.py marcado como INVALID; remover cópia duplicada run_e1_v3.py
- repor asserts A2/A3 com valores actuais
- refs.bib com year = {2012}
- *, w0 na assinatura
- corrigir texto do DEV-GPU-001
- lista de erratas acumuladas até lá
