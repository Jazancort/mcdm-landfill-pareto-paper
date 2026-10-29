# DEV-SANT-E1-001: E1 cells evaluated against amplitude-specific frontier instead of mm-frontier

```
Status:      OPEN — corrective run not yet executed
Type:        Implementation error (post-PRESPEC, pre-data; undocumented)
Discovered:  2026-10-29 (after seeing all E1 cells at 100% in both branches)
Written:     2026-10-29
```

## What happened

Commit `67a71b8` (2026-10-28 07:36:33), message:
"fix(stage4): greedy/optimal selectors corrected; Q2 uses mm frontier for all 8 cells; E1 uses amplitude-specific frontier"

The commit explicitly set the E1 cells to use their own amplitude-specific Pareto frontier
for the Q2 and R computations, instead of the mm-frontier used in the Fogo E1 experiment.

Affected code in `run_santiago_mc.py` (CPU path):

```python
# WRONG (committed version)
F_e1_trios = compute_trio_objectives(F_e1_site, trios)  # E1-specific frontier
q2_opt = 0 if check_dominated_raw(F_e1_trios, F_e1_trios[tidx_opt]) else 1
```

Same pattern in GPU path (`compute_e1_cells_gpu`):

```python
# WRONG (committed version)
F_site_gpu, F_e1_trios_gpu = _f_trios_gpu(...)
q2_opt = 0 if _check_dom_gpu(F_e1_trios_gpu, F_e1_trios_gpu[tidx]) else 1
```

## Why this is wrong (PRESPEC evidence)

**PRESPEC_SANTIAGO.md lines 274–278 (literal):**

> "E1 cells M, B, W, V (definitions as Fogo §7.7, with Santiago's own rho_j and groups)."
>
> "**Frontier:** exact enumeration; dominance tolerance eps = 1e-9; `validate_core` checks pass
> (non-dominance and completeness) before any Q2."

One frontier is defined for all metrics. No E1-specific frontier is mentioned in
PRESPEC_SANTIAGO.md, PRESPEC_SANTIAGO_A5.md, A5a, A5b, or in any DEV file (grep confirmed).

"Definitions as Fogo §7.7" references the Fogo E1 experiment, which used mm-frontier.
Confirmed by `results/e1/e1_macros.tex` (auto-generated from Fogo data):

```
QtwoEoneWOpt = 64.2%   (against mm-frontier; not 100%)
QtwoEoneVOpt = 56.8%   (against mm-frontier; equal to QtwovecOptimal = 56.8%)
```

S3a predicts "E1-W optimal < 100% and E1-V optimal < 100%". Against amplitude-specific
frontier, the argmax is always on its own frontier (Theorem 1), so Q2_opt = 100% trivially.
This makes S3a non-falsifiable under the committed code; it is a real empirical prediction
only against the mm-frontier.

**The decision was not documented.** Commit `67a71b8` was made after `prespec-santiago-a5`
(tag, 2026-10-27) and before `stage4-launch-r3` (09:13, 2026-10-28), during pre-launch
code iteration. No DEV was filed. The phrase "amplitude-specific frontier" does not appear
in any PRESPEC or DEV file.

## Why this was not detected

- The K2 gate (E1-B optimal Q2 = 100%) PASSED. Under amplitude-specific frontier, K2 passes
  trivially for all cells by Theorem 1, not just E1-B. The PRESPEC intent is that K2 tests
  whether E1-B is on the mm-frontier (which it is, because TV_W = 0 means E1-B group
  objectives are a positive rescaling of mm group objectives — same Pareto set). Against
  amplitude-specific frontier, K2 is vacuous.
- The CPU/GPU equivalence validation (DEV-SANT-GPU-001) compared the 8 main cells only.
  E1 cells were not part of the A+B comparison.
- The error was discovered only after observing that all four E1 cells (M, B, W, V) showed
  Q2_opt = 100% in both branches, which is impossible under mm-frontier for E1-W and E1-V
  (Fogo: 64.2% and 56.8% respectively).

## Effect on sealed files

- `mc_ST_raw.csv` (SHA 123a5421) and `mc_SN_raw.csv` (SHA dbfa2f00): **not affected**.
  These contain the 8 factorial cells, which use mm-frontier correctly.
- `mc_ST_e1.csv` (SHA c074d3d0) and `mc_SN_e1.csv` (SHA 20b991c4): **affected**.
  Q2_opt = 100% for all E1 cells in both branches is an artefact of the wrong frontier.

K2 in the sealed log: PASSED vacuously (not a real test under the committed code).
The K2 pass does not validate Theorem 1 for Santiago in the sealed run.

Affected verdicts from `santiago_predictions.json`: S3a, S3b, S7a, S7b are invalid.
Unaffected: S0, S1, S2, S4, S5, K1, K3, K4, K5, K6.

## Correction

The correct code checks the E1 portfolio's mm-group objectives against the mm-frontier.
`F_mm_trios` and `F_mm_site` are already available per draw in both CPU and GPU paths
(used for the 8 main cells). The correction:

1. Select the E1-optimal portfolio using the E1 score (unchanged).
2. Evaluate that portfolio's mm-group objectives (A_j = 1) against F_mm_trios.

CPU path fix:

```python
# CORRECT
tidx_opt = optimal_selector(sc_opt, trios)
trio_opt = trios[tidx_opt]
f_mm_opt = (F_mm_site[trio_opt[0]] +
            F_mm_site[trio_opt[1]] +
            F_mm_site[trio_opt[2]])
q2_opt = 0 if check_dominated_raw(F_mm_trios, f_mm_opt) else 1

trio_grd = greedy_selector(sc_opt, data["D"])
f_mm_grd = (F_mm_site[trio_grd[0]] +
            F_mm_site[trio_grd[1]] +
            F_mm_site[trio_grd[2]])
q2_grd = 0 if check_dominated_raw(F_mm_trios, f_mm_grd) else 1
```

GPU path: select trio using E1 GPU score; then look up that trio's mm-objectives
from `F_mm_site_gpu` (already computed in the GPU path) and check against the
mm Pareto frontier.

## Acceptance criteria for the corrective run

Santiago proceeds only if all three gates pass in sequence:

**Gate 1 — Fogo regression (exact to half the last decimal place):**
Apply corrected code to Fogo data with Fogo E1 weights (e1_weights_k200.npy,
SHA bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487).

Required results (from e1_macros.tex):

| Cell | Q2_opt |
|------|--------|
| E1-M | 100.0% |
| E1-B | 100.0% |
| E1-W | 64.2%  |
| E1-V | 56.8%  |

E1-V must equal QtwovecOptimal (56.8%) exactly, since E1-V uses A_j = rho_j
(same as vec normalization).

**Gate 2 — Internal consistency (Santiago, exact):**

- E1-M opt = 100.0% (mm normalization, by Proposition 1).
- E1-B opt = 100.0% (Proposition 1: TV_W = 0; this is now a real check).
- E1-V opt at kappa=200 must equal SAW_vec_opt from the sealed mc_ST_raw.csv / mc_SN_raw.csv
  draw-for-draw.

**Gate 3 — Main cells SHA preserved:**
Full Stage 4 run with corrected code. mc_ST_raw.csv and mc_SN_raw.csv must have
the same SHA-256 as the sealed files (SHA 123a5421 and dbfa2f00 respectively).
This proves the correction does not affect the 8 main cells.

## Reporting

Both runs are reported in the manuscript.

The sealed run: "The initial Stage 4 run (tag stage4-results-sealed) contained an
implementation error in the E1 cell computation (DEV-SANT-E1-001): E1 portfolios were
evaluated against an amplitude-specific Pareto frontier rather than the mm-frontier
used in the Fogo E1 experiment. Under this error, all four E1 cells reported Q2_opt = 100%
trivially (Theorem 1). Results for S3a, S3b, S7a, S7b from the sealed run are invalid.
The corrective run (tag stage4-e1fix-sealed) is the primary result for these predictions."

The 8 main cells and K1–K6 are unchanged and are cited from the original sealed run.

## Tags

- `stage4-results-sealed`: original run (E1 values invalid for S3a, S3b, S7a, S7b)
- `stage4-e1fix-sealed`: corrective run (to be created after gates pass)

## Expected direction (declared before corrective run)

Based on Fogo analogy. Not predictions; direction only.

- E1-W opt: expected below 100% (Fogo: 64.2% at kappa=200)
- E1-V opt: expected below 100% (Fogo: 56.8% at kappa=200)
- E1-V opt < E1-W opt: expected (Fogo: 56.8% < 64.2%)
- S3a: expected to confirm
- S3b: expected to confirm

No magnitude predictions are made for Santiago.

---

## Adenda 2026-10-29: segundo bug — fórmula de Ā_g em get_e1_amplitudes

### O que foi encontrado

Depois de a stage4-e1fix-sealed ser criada, o gate do Fogo revelou que
`get_e1_amplitudes` usa os pesos do sorteio w para calcular Ā_g (média
dentro do grupo), enquanto o oracle (run_e1_v3.py, log 44f7ff5) usa os
pesos fixos w₀.

Sequência dos gates:

| Gate | Resultado | Causa |
|------|-----------|-------|
| v1 (gate_e1_fogo.py) | FAIL — E1-W = 100% | rho_j = np.std(X_mm) ≈ uniforme → E1-W ≡ E1-M |
| v2 (gate_e1_fogo_v2.py) | FAIL — E1-W = 63,6% | Ā_g com pesos do sorteio |
| v3 (gate_e1_fogo_v3.py) | PASS — 100/100/64,2/56,8 | Ā_g com pesos fixos w₀ |

O gate v1 foi substituído incorrectamente antes de ser resolvido. A causa
real não era "convenção de direcção" mas sim o rho_j errado (np.std em
vez de 1/L2(mm_norm)). Esse erro foi corrigido no v2, que revelou o segundo
problema: Ā_g com pesos do sorteio.

### Confirmação da fórmula correcta

O log v3 (data/e1_v3_rerun_20261002.log, SHA e05cd8a4, commitado em 44f7ff5)
contém:

```
Aj_bar_g: G1=0.3744  G2=0.1473  G3=0.1161
E1-W rescale: 0.2034 (published 0.2024)
```

Estes são três valores fixos (não por sorteio). A aritmética confirma que
saem de FOGO_W0 (pesos AHP fixos):

  Ā_G1 = (0.152×0.5827 + 0.113×0.1388 + 0.030×0.2058) / 0.295 = 0.3744 ✓

O script que produziu o log v3 é run_e1_v3.py (path Windows G:\...) —
nunca commitado no repositório. O log foi commitado em 44f7ff5 a partir
de uma corrida que terminou em crash (assertions A2/A3 falham após os
resultados estarem completos). Os valores Q2 são válidos.

O discrepância "0.2034 vs 0.2024 (published)" deve-se a arredondamento dos
pesos AHP: FOGO_W0/FOGO_W0.sum() vs FOGO_W0 sem renormalização. O gate v3
usa FOGO_W0/FOGO_W0.sum() e reproduz 64.2% exactamente.

### Origem do oracle

A origin dos números 64.2%/56.8% é:
- script: run_e1_v3.py (Windows, não commitado)
- log commitado: data/e1_v3_rerun_20261002.log (44f7ff5, 2026-10-03)
- macros gerados por: scripts/generate_macros_e1.py

O run_e1.py no repositório nunca foi o script correcto. O commit 7fb70fc
(2026-09-30) documenta explicitamente "E1-W/E1-V optimal=100% (estimand
differs from WP3 56.8%)". O run_e1.py está actualmente quebrado (E1-B=81.8%
em vez de 100%) por razão independente do Bug 1 e deste Bug 2.

### Consequência para stage4-e1fix-sealed

Os ficheiros mc_ST_e1_fix.csv e mc_SN_e1_fix.csv (tag stage4-e1fix-sealed)
foram produzidos com Ā_g por sorteio. Os valores de E1-W são provisórios:

| | E1-W opt (por sorteio, e1fix-sealed) | E1-W opt (w₀ fixo, e1fix2) |
|---|---|---|
| S-T κ=200 | 80,0% | a calcular |
| S-N κ=200 | 99,2% | a calcular |

E1-M, E1-B e E1-V não são afectados (independentes de Ā_g).

O veredicto de S3a (E1-W < 100%) provavelmente mantém-se com a fórmula
correcta, mas não pode ser declarado antes da corrida com w₀ fixo.
A direcção de S3b (E1-V < E1-W) no S-T INVERTE-SE com os valores actuais
(84.2% vs 80.0%): com a fórmula correcta pode inverter novamente se E1-W
subir acima de E1-V. Este é o risco principal da correcção.

Tags afectadas: stage4-e1fix-sealed. Os raw CSVs principais permanecem
válidos (SHA 123a5421 e dbfa2f00 confirmados por Gate 3).

### Correcção

A correcção é: passar w₀ fixo (ST_W0 ou SN_W0) a get_e1_amplitudes em vez
de w (pesos do sorteio). Apenas o cálculo de Abar_g muda; o portfolio
continua a ser seleccionado com w (pesos do sorteio).

A correcção só avança depois de:
1. Confirmar a fórmula no §7.7 do manuscrito.
2. Verificar que o §7.7 não é ambíguo ou, se for, documentar a decisão.
3. Escrever o commit exclusivamente com a correcção (sem outros diffs).

### Verificação embutida para κ=∞

Em κ=∞, w = w₀ (determinístico). Portanto a fórmula antiga (pesos do
sorteio) e a nova (pesos fixos) são idênticas para κ=∞. A coluna κ=∞ dos
mc_*_e1_fix.csv é válida para E1-W e não precisa de nova corrida.

### Nota sobre o gate v1 e a explicação anterior

A explicação dada para o v1 ("convenção de direcção diferente") estava
errada. A causa real foi o rho_j = np.std(X_mm) ≈ uniforme, que colapsa
E1-W para E1-M. Este engano deveu-se a não ter verificado os valores de
rho_j antes de elaborar a explicação.

O gate v1 foi substituído por gates internos (gate_e1_internal.py) sem o
gate do Fogo ter passado. Isso foi incorrecto per os critérios de aceitação
do DEV. Os gates internos provaram que o código usa a mm-fronteira, mas
não validaram a fórmula de E1-W.

### Data

Descoberto 2026-10-29 ao analisar o output do gate v2 (E1-W = 63.6% ≠ 64.2%).
Escrito 2026-10-29, antes de qualquer alteração ao código.
