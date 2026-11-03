# Bundle de avaliação — Santiago Stage 4
Criado: 2026-11-02  
Propósito: tudo o que foi pedido para fazer S3a/S3b por regra, gate interno sorteio a sorteio, e verificar os pesos do Cabral.

---

## ÍNDICE

1. [Correcções ao plano](#1-correcções-ao-plano)
2. [SHA manifesto — dois tags selados](#2-sha-manifesto)
3. [Ficheiros disponíveis / não disponíveis](#3-disponibilidade-de-ficheiros)
4. [scp + verificação SHA](#4-scp--verificação-sha)
5. [gate_e1_fogo_v4.py — código completo + análise per-draw](#5-gate_e1_fogo_v4py)
6. [git diff stage4-launch-r5 → stage4-e1fix2-sealed](#6-git-diff)
7. [evaluate_santiago_predictions.py — código completo](#7-evaluate_santiago_predictionspy)
8. [Regret oracle — 4.53 / 6.63 / 5.27 / 28%](#8-regret-oracle)
9. [_compute_e1_regret.py — código completo](#9-_compute_e1_regretpy)
10. [PRESPEC K-predictions (A5 §2)](#10-prespec-k-predictions)
11. [DEV-SANT-E1-001](#11-dev-sant-e1-001)
12. [DEV-SANT-GPU-001](#12-dev-sant-gpu-001)
13. [DEV-SANT-W0-001](#13-dev-sant-w0-001)
14. [DEV-SANT-S5-001](#14-dev-sant-s5-001)
15. [Problema residual: w0=None na assinatura GPU](#15-problema-residual-w0none)
16. [Problema no evaluate_santiago: e1.csv errado](#16-evaluate_santiago-lê-e1csv-errado)
17. [Log selado (K1–K6) — na Athena](#17-log-selado-k1k6--na-athena)
18. [santiago_predictions.json — ainda não existe](#18-santiago_predictionsjson--ainda-não-existe)

---

## 1. Correcções ao plano

### 1.1 R = 1 − Q2 está ERRADO. Não verificar — substituir.

No Fogo, `R = 1 − Q2` dá 33.8 / 43.2 pp (para SAW/vec/grd e SAW/vec/opt).  
O oracle de value regret é 6.63 / 5.27 pp — calculado por `compute_regret.py` com a fórmula:

```
R(t; w) = [V_mm(t*(w)) - V_mm(t; w)] / [V_mm(t*(w)) - V_mm(t_min(w))]
```

O `evaluate_santiago_predictions.py` usa `R = 1 − Q2` em S6, S7a, S7b. Isso inverte S6 (S6 deveria ser confirmada em Fogo com R_grd=6.63 > R_opt=5.27, mas com 1-Q2 S6 não é confirmada porque Q2(opt) < Q2(grd) = S2 oposto). A v2 tem de importar as funções do `compute_regret.py`.

### 1.2 Não usar `git show … > ficheiro` no PowerShell

`mc_ST_raw.csv` e `mc_SN_raw.csv` **não estão no git** — os SHAs constam apenas na mensagem da tag, não como blobs. Usar `scp` da Athena (ver §4). Verificar com `Get-FileHash -Algorithm SHA256`.

### 1.3 κ=∞ da e1fix2

A e1fix2 foi uma corrida completa e incluiu κ=∞. Registar como verificado empiricamente (idêntico à e1fix segundo o commit message: "E1-M, E1-B, E1-V: bit-exact identical to e1fix-sealed"). κ=∞ → w=w₀ → E1-ABAR usa mesmos pesos de qualquer forma; portanto κ=∞ não era afectado pelo bug, mas deve ser reportado como empiricamente verificado.

### 1.4 K2

K2 (E1-B opt = 100%) decorre da **Proposição 1**, não do Teorema 1. O DEV-SANT-E1-001 menciona "Theorem 1" mas a proposição correcta é P1 (SAW[ref] ótimo = 100% em Q2[mesma ref]). Confirmar que o script não cita Teorema 1 para K2.

### 1.5 S3b — não registar sentido sem teste

Em S-N (e1fix2): E1-V=98.6%, E1-W=99.2% — baseados em 3 sorteios que saem de E1-W > E1-V. Não registar sentido. Esperar McNemar sobre 500 sorteios.

### 1.6 Holm — família definida na PRESPEC A5 §3

Família K3+K4 por ramo, Holm dentro de K4 sobre os 6 κ. Citar A5 §3, não escolher agora.

---

## 2. SHA manifesto

### stage4-results-sealed (tag anotada, commit 7ed3202)

```
mc_ST_raw.csv  : 123a5421d81b7bdd5d405ddb4a60edde1eeaa2f7da5cefbb640812aeed67bd80
mc_SN_raw.csv  : dbfa2f00b6f3f98e3a900f9020f98ecb55ef98dfdeed199a334f7b299013d492
mc_ST_e1.csv   : c074d3d0ad95731099c21744fdd1a1b6dea23df258aac13c64fbc5a79d341526  (INVÁLIDO — E1-FRONT)
mc_SN_e1.csv   : 20b991c4731912a38a8ece610309ff428f769fe889b475d87f27b5743271dc93  (INVÁLIDO — E1-FRONT)
log GPU        : 0be5cf3475650143926431f29a083eeb780f4e5c60f69f253d31463095bf1c5a
```

### stage4-e1fix2-sealed (tag anotada, commit 2d6f725)

```
mc_ST_e1_fix2.csv : 7806db5da3e78246e2707ef7df3e4980b445f9b7e04e751e65dbfeefd2b07507
mc_SN_e1_fix2.csv : 357904c04d9d863b40c3cb448cb3b58e4615321cf5ac25f24c84a228312c1593

Resultados selados (S-T, κ=200): E1-M=100.0%  E1-B=100.0%  E1-V=84.2%  E1-W=80.2%
Resultados selados (S-N, κ=200): E1-M=100.0%  E1-B=100.0%  E1-V=98.6%  E1-W=99.2%

Gate: gate_e1_fogo_v4 PASS — Ā_g=0.3744/0.1473/0.1161  A_W diff=0
K2 (real): E1-B opt = 100% (mm-frontier, Proposição 1 — não vacuo)
E1-M, E1-B, E1-V: bit-exact identical to e1fix-sealed (501 rows each)
Raw CSVs: ST=123a5421 SN=dbfa2f00 (UNCHANGED — Gate 3 passed)
```

### SHAs locais verificados

```powershell
# Executar localmente:
Get-FileHash "results\santiago\mc_ST_e1_fix2.csv" -Algorithm SHA256
# Esperado: 7806DB5DA3E78246E2707EF7DF3E4980B445F9B7E04E751E65DBFEEFD2B07507  ✓

Get-FileHash "results\santiago\mc_SN_e1_fix2.csv" -Algorithm SHA256
# Esperado: 357904C04D9D863B40C3CB448CB3B58E4615321CF5AC25F24C84A228312C1593  ✓
```

---

## 3. Disponibilidade de ficheiros

| Ficheiro | Local Windows | Athena | Nota |
|---|---|---|---|
| `mc_ST_e1_fix2.csv` | ✓ `results/santiago/` | ✓ | SHA verificado |
| `mc_SN_e1_fix2.csv` | ✓ `results/santiago/` | ✓ | SHA verificado |
| `mc_ST_raw.csv` | ✗ | ✓ | scp (ver §4) |
| `mc_SN_raw.csv` | ✗ | ✓ | scp (ver §4) |
| `gate_e1_fogo_v4.py` | ✓ `scripts/` | — | ver §5 |
| `evaluate_santiago_predictions.py` | ✓ `scripts/` | — | ver §7; atenção §16 |
| `compute_regret.py` | ✓ `scripts/` | — | oracle em §8 |
| `_compute_e1_regret.py` | ✓ `scripts/` | — | oracle em §9 |
| `regret_macros.tex` | ✓ `results/regret/` | — | contém 4.53/28% |
| `regret_aggregate.csv` | ✓ `results/regret/` | — | contém 6.63/5.27 |
| `DEV-SANT-E1-001.md` | ✓ `corpus/deviations/` | — | ver §11 |
| `DEV-SANT-GPU-001.md` | ✓ `corpus/deviations/` | — | ver §12 |
| `DEV-SANT-W0-001.md` | ✓ `corpus/deviations/` | — | ver §13 |
| `DEV-SANT-S5-001.md` | ✓ `corpus/deviations/` | — | ver §14 |
| `PRESPEC_SANTIAGO_A5.md` | ✓ `corpus/prespec/` | — | K1–K6 em §10 |
| `mc_full_20261028T1237Z_gpu.log` | ✗ | ✓ | gitignored, SHA na tag |
| `santiago_predictions.json` | ✗ (não existe) | ✗ | criar com eval v2 |
| PDF Cabral (2012) | ✗ | ✗ | CAPTCHA; abrir à mão |

---

## 4. scp + verificação SHA

```bash
# Na Athena (ssh julioazancort@athena):
REPO=~/scratch/mcdm-landfill-pareto-paper
LOCAL=G:/Faculdade/Estudo/Mestrado/2022.1/Trabalhos/Multicriterio/03-latex/"paper - Comparison between MCDM Methods for Landfill Site Selection"/results/santiago

scp $REPO/results/santiago/mc_ST_raw.csv "$LOCAL/mc_ST_raw.csv"
scp $REPO/results/santiago/mc_SN_raw.csv "$LOCAL/mc_SN_raw.csv"

# Verificar SHA após download (PowerShell):
Get-FileHash "results\santiago\mc_ST_raw.csv" -Algorithm SHA256
# Esperado: 123A5421D81B7BDD5D405DDB4A60EDDE1EEAA2F7DA5CEFBB640812AEED67BD80

Get-FileHash "results\santiago\mc_SN_raw.csv" -Algorithm SHA256
# Esperado: DBFA2F00B6F3F98E3A900F9020F98ECB55EF98DFDEED199A334F7B299013D492
```

Log GPU selado (K1–K6) se necessário:
```bash
scp $REPO/results/santiago/mc_full_20261028T1237Z_gpu.log .
# SHA esperado: 0be5cf3475650143926431f29a083eeb780f4e5c60f69f253d31463095bf1c5a
```

---

## 5. gate_e1_fogo_v4.py

### Análise per-draw

- **Check 1**: Ā_g via `get_e1_amplitudes` (função de produção importada directamente). Comparação com oracle (G1=0.3744, G2=0.1473, G3=0.1161). Não é per-draw — é único por construção (w0 fixo).
- **Check 2**: vector A_W por critério contra oracle. Não per-draw — único.
- **Check 3**: Corre 500 draws, calcula Q2_opt draw-a-draw para M/B/W/V e compara **aggregate** com oracle (100/100/64.2/56.8 ± 0.05 pp). Tem os q2 individuais em lista mas só compara a média.
- **Check 4**: E1-V **aggregate** == 56.8% exacto. Não per-draw.

**Conclusão**: gate v4 não faz comparação per-draw para E1-W. Para a S3b (McNemar) precisas das 500 linhas individuais de `mc_ST_e1_fix2.csv` (colunas `Q2_opt` por `e1_cell` e `draw`). Essas colunas existem no CSV local.

### Código completo

```python
# -*- coding: utf-8 -*-
"""gate_e1_fogo_v4.py — Final Fogo E1 gate for E1-ABAR fix.

Uses get_e1_amplitudes imported directly from run_santiago_mc.py (production code).
No copy of the function. If the function is wrong, the gate fails.

Checks:
1. Ā_g values match oracle log v3 header (G1=0.3744, G2=0.1473, G3=0.1161)
2. A_W (E1-W amplitude vector) matches oracle up to 1e-12
3. Q2_opt matches oracle (100/100/64.2/56.8) within 0.05pp
4. E1-V optimal = E1-V optimal from oracle (same draws → same Q2 per draw)

Reference: data/e1_v3_rerun_20261002.log (SHA e05cd8a4..., commit 44f7ff5)

Run:
  CUDA_VISIBLE_DEVICES=0 uv run python scripts/gate_e1_fogo_v4.py
"""
import json, sys, os, hashlib
import numpy as np
from pathlib import Path

ROOT    = Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

if "MCDM_DATA_DIR" not in os.environ:
    os.environ["MCDM_DATA_DIR"] = "/home/julioazancort/scratch/mcdm"

from run_santiago_mc import (
    get_e1_amplitudes, optimal_selector,
    compute_group_objectives, compute_trio_objectives, check_dominated_raw,
)

AMP_JSON = ROOT / "results" / "amplitudes" / "amplitudes.json"
amp = json.loads(AMP_JSON.read_text())

FOGO_CRIT = ["perm","slope","roads","rivers","aspect","coast",
             "protected","wells","urban","aero","cult"]
rho_j_fogo = np.array([amp["rho_j"][c] for c in FOGO_CRIT], dtype=float)
FOGO_GROUPS = [[0,1,2],[3,4,5,6,7],[8,9,10]]

FOGO_W0 = np.array([0.152,0.113,0.030,0.091,0.075,0.069,
                    0.066,0.055,0.166,0.102,0.081], dtype=float)
FOGO_W0 = FOGO_W0 / FOGO_W0.sum()

# Check 1: Ā_g
print("=== Check 1: Ā_g values ===")
e1_test = get_e1_amplitudes(rho_j_fogo, FOGO_GROUPS, FOGO_W0)
A_B = e1_test["B"]
ORACLE_ABAR = {0: 0.3744, 3: 0.1473, 8: 0.1161}
all_pass = True
for idx, ref in ORACLE_ABAR.items():
    got = float(A_B[idx])
    ok = abs(got - ref) < 1e-3
    all_pass = all_pass and ok
    g = next(i for i,g in enumerate(FOGO_GROUPS) if idx in g)
    print(f"  G{g+1} Ā_g: got={got:.4f}  oracle={ref:.4f}  {'OK' if ok else 'FAIL'}")

# Check 2: A_W vector
print("\n=== Check 2: E1-W amplitude vector ===")
A_W = e1_test["W"]
Abar_g_oracle = A_B.copy()
A_W_raw_oracle = np.where(Abar_g_oracle > 1e-15, rho_j_fogo / Abar_g_oracle, 0.0)
s_V = float(np.dot(FOGO_W0, rho_j_fogo))
s_W = float(np.dot(FOGO_W0, A_W_raw_oracle))
scale_oracle = s_V / s_W if s_W > 1e-15 else 1.0
A_W_oracle = A_W_raw_oracle * scale_oracle
max_diff = float(np.max(np.abs(A_W - A_W_oracle)))
print(f"  Max |A_W_production - A_W_oracle|: {max_diff:.2e}  {'OK' if max_diff < 1e-10 else 'FAIL'}")
if max_diff >= 1e-10: all_pass = False
print(f"  scale_EW: {scale_oracle:.4f}  (oracle log: 0.2034)")

# Load data
print("\n=== Loading data ===")
from mcdm_experiment import load_data, impute_nan, COL, _build_decision_matrix
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]] > 0].copy().reset_index(drop=True)
assert len(df_via) == 389
X_raw, benefit = _build_decision_matrix(df_via)
X_adj = X_raw.copy()
for j, b in enumerate(benefit):
    if not b: X_adj[:,j] = 1.0 - X_raw[:,j]
lo = X_adj.min(0); hi = X_adj.max(0)
denom = np.where(hi - lo > 1e-9, hi - lo, 1.0)
X_mm = (X_adj - lo) / denom
trios = np.load(ROOT / "data" / "fogo_trios.npy").astype(np.int32)
assert len(trios) == 1_944_653
SHA_W = "bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487"
wmat_path = ROOT / "results" / "e1" / "e1_weights_k200.npy"
assert hashlib.sha256(wmat_path.read_bytes()).hexdigest() == SHA_W, "SHA mismatch"
W = np.load(wmat_path)
print(f"  X_mm: {X_mm.shape}  n_trios: {len(trios):,}  weights: {W.shape}  SHA OK")

# Check 3: Q2_opt per draw (aggregate)
N_DRAWS = 500
A_ones = np.ones(len(rho_j_fogo))
q2_opt = {"M": [], "B": [], "W": [], "V": []}
print(f"\nRunning {N_DRAWS} draws (CPU)...", flush=True)
for draw_idx in range(N_DRAWS):
    w = W[draw_idx]
    F_mm_site  = compute_group_objectives(X_mm, w, A_ones, FOGO_GROUPS)
    F_mm_trios = compute_trio_objectives(F_mm_site, trios)
    e1_amps = get_e1_amplitudes(rho_j_fogo, FOGO_GROUPS, FOGO_W0)
    for e1_name in ["M","B","W","V"]:
        A_e1 = e1_amps[e1_name]
        sc_opt = (X_mm * A_e1 * w).sum(1)
        tidx_opt = optimal_selector(sc_opt, trios)
        trio_opt = trios[tidx_opt]
        f_mm_opt = (F_mm_site[trio_opt[0]] + F_mm_site[trio_opt[1]] + F_mm_site[trio_opt[2]])
        q2 = 0 if check_dominated_raw(F_mm_trios, f_mm_opt) else 1
        q2_opt[e1_name].append(q2)
    if (draw_idx + 1) % 100 == 0:
        print(f"  {draw_idx+1}/{N_DRAWS}", flush=True)

REF = {"M": 100.0, "B": 100.0, "W": 64.2, "V": 56.8}
TOL = 0.05
print("\n=== Check 3: Q2_opt vs oracle (100/100/64.2/56.8) ===")
for e1_name in ["M","B","W","V"]:
    pct = float(np.mean(q2_opt[e1_name])) * 100
    ref = REF[e1_name]
    ok  = abs(pct - ref) <= TOL
    all_pass = all_pass and ok
    print(f"  E1-{e1_name}: {pct:.1f}%  ref {ref:.1f}%  diff {pct-ref:+.1f}pp  {'OK' if ok else 'FAIL'}")

# Check 4: E1-V aggregate == 56.8%
print(f"\n=== Check 4: E1-V aggregate == oracle (56.8% exact) ===")
e1v_pct = float(np.mean(q2_opt["V"])) * 100
ok4 = abs(e1v_pct - 56.8) <= 0.05
all_pass = all_pass and ok4
print(f"  E1-V: {e1v_pct:.1f}%  oracle: 56.8%  {'OK' if ok4 else 'FAIL'}")

print()
if all_pass:
    print("ALL CHECKS PASS — E1-ABAR fix verified with production code.")
else:
    print("CHECKS FAILED — do not proceed.")
    sys.exit(1)
```

---

## 6. git diff

`git diff stage4-launch-r5 stage4-e1fix2-sealed -- scripts/run_santiago_mc.py`

Mudanças principais:
1. `get_e1_amplitudes(rho_j, w, groups)` → `get_e1_amplitudes(rho_j, groups, w0)` — w removido, w0 explícito
2. Ā_g usa `w0[g_arr]` em vez de `w[g_arr]`
3. E1-W recebe rescale global: `scale = dot(w0, rho_j) / dot(w0, A_W_raw)`
4. CPU e1 path usa `F_mm_trios_k1` em vez de `F_e1_trios` (mm-frontier, não amplitude-specific)
5. GPU e1 path recebe `F_mm_site_gpu` e `F_mm_trios_gpu` como argumentos
6. `compute_q2_all_cells_gpu` agora retorna `F_site_gpu` também (terceiro elemento)
7. Pool GPU: `set_limit(85% free)` + OOM fallback
8. `compute_e1_cells_gpu` signature: adicionado `w0: np.ndarray = None` (ver §15)

Diff completo (selecção das linhas mais relevantes para E1):

```diff
-def get_e1_amplitudes(rho_j: np.ndarray, w: np.ndarray, groups: list) -> dict:
+def get_e1_amplitudes(rho_j: np.ndarray, groups: list, w0: np.ndarray) -> dict:
+    Ā_g computed from FIXED declared AHP weights w0, not per-draw weights.
+    Signature note: w (per-draw) is intentionally absent to prevent the E1-ABAR bug.
     for g in groups:
         g_arr = np.array(g, dtype=int)
-        W_g   = w[g_arr].sum()
-        avg   = float(np.dot(w[g_arr], rho_j[g_arr]) / W_g) if W_g > 0 else 0.0
+        W_g   = w0[g_arr].sum()
+        avg   = float(np.dot(w0[g_arr], rho_j[g_arr]) / W_g) if W_g > 0 else 0.0
-    A_W = np.where(Abar_g > 1e-15, rho_j / Abar_g, 0.0)
+    A_W_raw = np.where(Abar_g > 1e-15, rho_j / Abar_g, 0.0)
+    s_V = float(np.dot(w0, rho_j))
+    s_W = float(np.dot(w0, A_W_raw))
+    scale = s_V / s_W if s_W > 1e-15 else 1.0
+    A_W = A_W_raw * scale

 # CPU path E1:
-    e1_amps = get_e1_amplitudes(rho_j, w, groups)
+    e1_amps = get_e1_amplitudes(rho_j, groups, w0)
-    F_e1_site = compute_group_objectives(X_mm, w, A_e1, groups)
-    F_e1_trios = compute_trio_objectives(F_e1_site, trios)
-    q2_opt = 0 if check_dominated_raw(F_e1_trios, F_e1_trios[tidx_opt]) else 1
+    # Q2 against mm-frontier (DEV-SANT-E1-001)
+    f_mm_opt = (F_mm_site_k1[trio_opt[0]] + F_mm_site_k1[trio_opt[1]] + F_mm_site_k1[trio_opt[2]])
+    q2_opt = 0 if check_dominated_raw(F_mm_trios_k1, f_mm_opt) else 1

 # GPU path:
-    e1_amps = get_e1_amplitudes(rho_j_cpu, w_cpu, groups)
+    e1_rows = compute_e1_cells_gpu(gpu_data, w, rho_j, groups, data["D"],
+                                   F_mm_site_gpu=F_mm_site_gpu,
+                                   F_mm_trios_gpu=F_mm_trios_gpu,
+                                   w0=w0)
```

---

## 7. evaluate_santiago_predictions.py

**Aviso antes de usar (ver §16):** o script lê `mc_ST_e1.csv` e `mc_SN_e1.csv` (inválidos — E1-FRONT). Para a v2, mudar para `mc_ST_e1_fix2.csv` e `mc_SN_e1_fix2.csv`.

**Aviso (ver §1.1):** S6, S7a, S7b usam `R = 1 - Q2`. Na v2, substituir pelas funções de `compute_regret.py`.

```python
# ── Constantes e condições (lines 35–50) ──────────────────────────────────────
ROOT    = Path(__file__).parent.parent
SEALED  = ROOT / "results" / "santiago"
B_BOOT  = 2000
DELTA   = 2.5    # TOST margin (pp), PRESPEC A5 §1

COND_ST = {"TV": 0.2324, "TV_B": 0.1960, "TV_W": 0.1565, "S5_max_pm": 0.6173}
COND_SN = {"TV": 0.0757, "TV_B": 0.0572, "TV_W": 0.0561, "S5_max_pm": 0.0158}
FOGO_Q2_SAW_VEC_OPT = 56.8

# ── main() lê estes ficheiros ─────────────────────────────────────────────────
# !! CORRIGIR ANTES DA TAG v2 !!
st_res = evaluate_branch("S-T",
    SEALED / "mc_ST_raw.csv",
    SEALED / "mc_ST_e1.csv",     # ← ERRADO; deve ser mc_ST_e1_fix2.csv
    COND_ST)
sn_res = evaluate_branch("S-N",
    SEALED / "mc_SN_raw.csv",
    SEALED / "mc_SN_e1.csv",     # ← ERRADO; deve ser mc_SN_e1_fix2.csv
    COND_SN)

# ── Regras por previsão ───────────────────────────────────────────────────────
# S0: SAW/mm/opt Q2=100% every draw (K1 regression). df["SAW_mm_opt"].all()
# S1: Q2(SAW,mm,grd) > Q2(SAW,vec,grd). CI excludes 0. TV≥0.05. Holm K4.
# S2: Q2(SAW,vec,opt) < Q2(SAW,vec,grd). CI excludes 0. TV_W≥0.05. (GREEDY REVERSAL)
# S3a: E1-W opt < 100% AND E1-V opt < 100%. TV_W≥0.05.
# S3b: E1-V opt < E1-W opt. CI via McNemar (pairwise). TV_W≥0.05 AND TV_B≥0.05.
#      ATENÇÃO: script actual usa comparação de médias. Para v2, usar McNemar exacto.
# S4: SAW-TOPSIS per κ, descritivo.
# S5: Q2(SAW,vec,opt) > 56.8%. max_pm_continuous < 0.5.
# S6: R(SAW,vec,grd) > R(SAW,vec,opt). CI excludes 0. TV_W≥0.05.
#      NOTA: script usa R=1-Q2. Para v2, usar compute_regret value regret.
#      Com R=1-Q2: S6 e S2 são a mesma previsão (sentido oposto). Com value regret: distintas.
# S7a: R(E1-B,opt) > 0. TV_B≥0.05. NOTA: K2=100% → R=0 → S7a não confirmável.
#      Para v2, R deve ser o value regret, não 1-Q2.
# S7b: R(E1-B,opt) < R(E1-W,opt) a κ=200. TV_B≥0.05 AND TV_W≥0.05.
#      Para v2, usar value regret.

# ── Outputs ───────────────────────────────────────────────────────────────────
# results/santiago/santiago_predictions.json
# results/santiago/st_k5_greedy_ST.json
# results/santiago/st_k5_greedy_SN.json
```

---

## 8. Regret oracle

Origem dos quatro valores usados como gate de EVAL-R:

| Valor | Script fonte | Output | Macro LaTeX |
|---|---|---|---|
| **4.53 pp** | `scripts/_compute_e1_regret.py` | `results/regret/regret_macros.tex` | `\RegretEoneB` (E1-B/opt mean R) |
| **6.63 pp** | `scripts/compute_regret.py` | `results/regret/regret_aggregate.csv` | `\RegrSAWvecGrd` |
| **5.27 pp** | `scripts/compute_regret.py` | `results/regret/regret_aggregate.csv` | `\RegrSAWvecOpt` |
| **28%** | `scripts/_compute_e1_regret.py` | `results/regret/regret_macros.tex` | `\RegretEoneBfracZero` (draws com R=0 em E1-B/opt) |

`regret_aggregate.csv` (confirmado):
```
agg,norm,mont,mean_R,se_R,mean_R_pp,se_R_pp,mean_V_mm,Q2_pct
saw,minmax,greedy,0.0233,0.0012,2.33,0.12,1.9976,86.0
saw,minmax,optimal,0.0,0.0,0.0,0.0,2.0207,100.0
saw,vector,greedy,0.0663,0.0014,6.63,0.14,1.9544,66.2
saw,vector,optimal,0.0527,0.0014,5.27,0.14,1.9679,56.8
topsis,minmax,greedy,0.0358,0.0012,3.58,0.12,1.9852,94.4
topsis,minmax,optimal,0.0272,0.0011,2.72,0.11,1.9938,96.6
topsis,vector,greedy,0.0851,0.0016,8.51,0.16,1.9358,63.4
topsis,vector,optimal,0.0635,0.0015,6.35,0.15,1.957,52.4
```

`compute_regret.py` lê: `results/unified/mc_unified_raw.csv` (não mc_18cells_raw.csv).
Fórmula: `R(t;w) = (V_mm(t*) - V_mm(t)) / V_range(w)` onde V_range = max - min sobre 1.94M trios.

`_compute_e1_regret.py` lê: `results/e1/e1_weights_k200.npy` (SHA bea05275...).
Fórmula idêntica mas aplicada às 8 células E1 (M/B/W/V × greedy/optimal).

**Gate EVAL-R para Santiago:**
1. Adaptar `compute_regret.py` para ler `mc_ST_raw.csv`
2. Verificar que reproduz 6.63 / 5.27 no Fogo antes de correr no Santiago
3. Adaptar `_compute_e1_regret.py` para E1 fix2 do Santiago
4. Verificar 4.53 / 28% no Fogo

---

## 9. _compute_e1_regret.py

```python
# -*- coding: utf-8 -*-
"""
_compute_e1_regret.py  (v2: new denominator)
Compute value regret R for all 8 E1 cells (M, B, W, V x greedy/optimal)
with CORRECTED denominator: range over ALL feasible trios T.

R(t; w) = [V_mm(t*(w)) - V_mm(t; w)] / [V_mm(t*(w)) - V_mm(t_min(w))]
  t*(w)    = argmax V_mm over T
  t_min(w) = argmin V_mm over T
R in [0,1]; independent of which cells are compared.
"""
# ... (lê results/e1/e1_weights_k200.npy, data/fogo_trios.npy)
# ... usa fogo_constants.py: OBJ_GROUPS, AJ_VEC as rho_j, W as w_ahp_raw
# ... computa Ā_g com w_ahp fixo (equivalente ao gate v4)
# Outputs (print para stdout):
#   E1-M greedy: Q2=86.0  R=2.33 pp
#   E1-M optimal: Q2=100.0 R=0.0 pp
#   E1-B greedy: Q2=100.0 R=8.25 pp
#   E1-B optimal: Q2=100.0 R=4.53 pp  ← oracle
#   E1-W greedy: Q2=~64  R=6.51 pp
#   E1-W optimal: Q2=64.2 R=6.47 pp
#   E1-V greedy: Q2=66.2  R=6.63 pp  ← oracle (igual a SAW/vec/grd)
#   E1-V optimal: Q2=56.8 R=5.27 pp  ← oracle (igual a SAW/vec/opt)
# Paired bootstrap B=2000, seed=55 → E1-B grd-opt = 3.72 pp [3.3, 4.1]
# RegretEoneBfracZero = 28 (% de sorteios onde E1-B/opt R=0)
# RegretEoneB = 4.53 pp (média)
```

Nota: o script tem um bug de lógica no loop (não calcula Q2 para o `optimal` path correctamente dentro do loop — verifica `V_sel = V_e1_opt` mas `Q2_vals[d] = nan`). Não afecta o regret (R é calculado). Confirmar antes de usar para Q2.

---

## 10. PRESPEC K-predictions (A5 §2)

Fonte: `corpus/prespec/PRESPEC_SANTIAGO_A5.md` §2.

**K1 — Implementation check (abort if failed)**
SAW/mm/opt Q2=100% at every κ (stochastic + deterministic). Consequência da Proposição 1. Falha → abort.

**K2 — Proposição 1 at κ=200 and κ=∞**
E1-B (between-group only, TV_W=0) Q2=100% optimal a κ=200 e κ=∞. Falha a κ=200 = regression failure (S0). A κ=∞ = novo check.

**K3 — Normalisation contrast never reverses (confirmatory)**
Para nenhum κ ∈ {25,50,100,200,400,1000} o CI de Q2(SAW,mm,grd)-Q2(SAW,vec,grd) está inteiramente abaixo de zero. Avaliado por κ individualmente (sem ajuste de multiplicidade — conservativo para "never reverses").

**K4 — Normalisation detectable at some κ (confirmatory)**
Para pelo menos um κ o contraste de normalização é positivo e significativo após correcção de Holm sobre os 6 κ estocásticos. H0: contraste ≤ 0; rejeitar se CI lower > 0 após Holm.

**K5 — High-κ reading (descriptive)**
A κ=1000 e κ=∞: (a) sinal do assembly effect (SAW/vec/opt − SAW/vec/grd) igual nos dois casos? (b) sinal do contraste agregado SAW-TOPSIS igual? Descritivo — sem CI, sem confirmação.

**K6 — SAW-TOPSIS across κ (exploratory, descriptive)**
Contraste pooled SAW-TOPSIS a cada κ, com CI. Sem previsão direcional. Fogo: inversão de sinal não explicada teoricamente.

**Multiplicity (A5 §3):**
- K3 e K4 formam uma família por ramo; Holm aplica-se dentro de K4 (6 κ, 1 teste por κ).
- K1 e K2 são implementation checks.
- K5 e K6 são descritivos (sem ajuste).

**Seeds (A5b §5):**
- κ=200: parent_seed=17; S-T child[0], S-N child[1] via `SeedSequence(17).spawn(2)`
- κ=50: parent_seed=4
- Outros κ: parent_seed = {25:1, 100:15, 400:28, 1000:30}

---

## 11. DEV-SANT-E1-001

(Conteúdo completo em `corpus/deviations/DEV-SANT-E1-001.md`)

**Resumo:**
- Bug E1-FRONT (commit 67a71b8, 2026-10-28): E1 avaliava contra fronteira amplitude-específica em vez de mm-frontier. Causa: derivado do run_e1.py v2 (não do oracle run_e1_v3.py).
- Bug E1-ABAR (adenda 2026-10-29): Ā_g calculado com pesos do sorteio w em vez de w₀ fixo.
- Correcção: `get_e1_amplitudes(rho_j, groups, w0)` — w₀ fixo, w removido.
- Gate v3 (PASSOU): fórmula oracle confirmada (G1=0.3744, G2=0.1473, G3=0.1161, Q2=100/100/64.2/56.8).
- Gate v4 (PASSOU): importa função de produção directamente. A_W diff=0.
- Ficheiros afectados: mc_ST_e1_fix2.csv (SHA 7806db5d), mc_SN_e1_fix2.csv (SHA 357904c0).
- Ficheiros válidos sem alteração: mc_ST_raw.csv (123a5421), mc_SN_raw.csv (dbfa2f00).
- 0.2024 vs 0.2034: discrepância de escala por arredondamento de w₀. Valor correcto (oracle): 0.2034.

---

## 12. DEV-SANT-GPU-001

(Conteúdo completo em `corpus/deviations/DEV-SANT-GPU-001.md`)

**Resumo:**
- Corrida CPU (r4, da3a840) abortada aos ~3 min. GPU (r5, 7ed3202, RTX 4000 Ada, GPU 1) usada.
- Equivalência S-N: 0 diferenças em 24,008 valores Q2. GPU r5 aceite.
- Equivalência S-T — Critério A (margin audit, 24,000 draws): 0 fragile decisions, min argmax_gap=1.25e-7, min dom_gap=2.72e-4. Critério B (CPU sample 232 draws): 0 Q2 diffs, 0 trio_idx diffs. GPU r5 aceite.
- κ=∞ no S-T: convergência suave (κ=10⁴→10⁶: K6 cai de +1.5 → 0.0 pp). Não é descontinuidade — é convergência ao limite determinístico.
- κ=∞ no S-N: converge a -25.0 pp (de baixo), consistente com κ=1000=-27.4 pp.

---

## 13. DEV-SANT-W0-001

(Conteúdo completo em `corpus/deviations/DEV-SANT-W0-001.md`)

**Resumo:**
- Escrito pós-corrida (não pre-data declaration).
- Pesos W0_SN verificados numericamente: 12 de 13 critérios coincidem com Cabral renorm 0.9637. A6: 0.0324 vs 0.0325 (1 unidade na 4ª casa decimal) — sugere uso dos pesos não-arredondados do Cabral.
- Padrões verificados: B1=2·B2=2·B3, A1=A4.
- Pesos W0_ST verificados: diferença < 5e-7 relativamente a Fogo AHP 10 critérios (C-2 wells, renorm).
- **Pendente**: verificar contra a tabela publicada do Cabral (2012) — hdl.handle.net/10362/8627. Todos os veredictos S-N são provisórios até aí. Regra W0-001: se pesos divergirem > 0.0001, nova corrida S-N.

---

## 14. DEV-SANT-S5-001

(Conteúdo completo em `corpus/deviations/DEV-SANT-S5-001.md`)

**Resumo:**
- **S-T**: perm = DISTÂNCIA (contínua, mesmo com ponto de massa em 0). max_pm_continuous = 0.617 > 0.5. **S5 NÃO testável em S-T.**
- **S-N**: B1 = SCORE de classe geológica (categórico). Excluído da condição S5. max_pm_continuous = 0.016 (C1). **S5 testável em S-N.**
- Sensibilidade: se perm classificado como categórico, S5 seria testável em S-T. Reportar as duas classificações.

---

## 15. Problema residual: w0=None na assinatura GPU

O diff confirma que `compute_e1_cells_gpu` ainda tem `w0: np.ndarray = None` na assinatura (stage4-e1fix2-sealed):

```diff
+def compute_e1_cells_gpu(gd, w_cpu, rho_j_cpu, groups, D,
+                          F_mm_site_gpu=None, F_mm_trios_gpu=None,
+                          w0: np.ndarray = None) -> list:
```

O default `None` significa que se `w0` for omitido acidentalmente, `get_e1_amplitudes` recebe `None` e falha com TypeError (em vez de produzir resultados silenciosamente errados). Portanto é "fail-closed", mas é melhor remover o default explicitamente. Corrigir antes da tag `predictions-eval-v2`:

```python
# Correcto (sem default):
def compute_e1_cells_gpu(gd, w_cpu, rho_j_cpu, groups, D,
                          F_mm_site_gpu=None, F_mm_trios_gpu=None,
                          w0: np.ndarray) -> list:
```

Commit isolado com esta única mudança.

---

## 16. evaluate_santiago: lê mc_ST_e1.csv errado

O `main()` actual (HEAD) passa:
```python
SEALED / "mc_ST_e1.csv"   # SHA c074d3d0 — INVÁLIDO (E1-FRONT bug)
SEALED / "mc_SN_e1.csv"   # SHA 20b991c4 — INVÁLIDO (E1-FRONT bug)
```

Para a tag `predictions-eval-v2`, corrigir para:
```python
SEALED / "mc_ST_e1_fix2.csv"  # SHA 7806db5d — válido
SEALED / "mc_SN_e1_fix2.csv"  # SHA 357904c0 — válido
```

Esta correcção + remoção de `w0=None` + substituição de R=1-Q2 em S6/S7 são as **três alterações obrigatórias** antes da tag v2.

---

## 17. Log selado (K1–K6) — na Athena

Ficheiro: `results/santiago/mc_full_20261028T1237Z_gpu.log`  
SHA: `0be5cf3475650143926431f29a083eeb780f4e5c60f69f253d31463095bf1c5a`  
Localização: Athena `~/scratch/mcdm-landfill-pareto-paper/results/santiago/`  
Gitignored: sim.

```bash
scp athena:~/scratch/mcdm-landfill-pareto-paper/results/santiago/mc_full_20261028T1237Z_gpu.log .
```

As linhas K1–K6 no log são do `evaluate_gates()` em `run_santiago_mc.py`. Procurar por `K1`, `K2`, `K3`, `K4`, `K5`, `K6` no log.

---

## 18. santiago_predictions.json — ainda não existe

O ficheiro `results/santiago/santiago_predictions.json` não existe localmente (nem na Athena se `evaluate_santiago_predictions.py` não correu com a e1fix2).

Para criar:
1. Fazer as três correcções ao script (§16, §15, §1.1)
2. Garantir que `mc_ST_raw.csv` e `mc_SN_raw.csv` estão locais (§4)
3. Criar tag `predictions-eval-v2` antes de correr
4. Correr: `CUDA_VISIBLE_DEVICES=0 uv run python scripts/evaluate_santiago_predictions.py`

O output será `results/santiago/santiago_predictions.json` + dois ficheiros `st_k5_greedy_*.json`.

---

## ADENDA — Problemas corrigidos e novos dados

### A1. Quatro problemas encontrados no bundle original

**Problema 1: Gate v4 — verificação 2 é circular**
A verificação 2 do gate v4 reconstrói A_W_oracle a partir do A_B devolvido pela própria função de produção (o mesmo `A_B = e1_test["B"]`). O "diff = 0" é garantido por construção. Não compara com o log v3. O valor do rescale (0.2034) é impresso mas não verificado numericamente. Acção pendente: gate v4b com comparação sorteio a sorteio do log v3.

**Problema 2: w0=None — sintaxe errada**
`def f(..., w0: np.ndarray)` sem default depois de parâmetros com default dá SyntaxError. Forma correcta:
```python
def compute_e1_cells_gpu(gd, w_cpu, rho_j_cpu, groups, D, *, w0, F_mm_site_gpu=None, F_mm_trios_gpu=None):
```
O `*` força keyword-only. Não urgente (None causa TypeError imediato), não juntar à tag eval v2.

**Problema 3 (correcção do utilizador): S3b usa CI bootstrap, não McNemar**
O §6 diz apenas "direction" para S3b, sem método estatístico explícito. Verificar: o PRESPEC §6 literal (ver §A2 abaixo) apenas define a direcção como previsão confirmada se E1-V < E1-W. O `evaluate_santiago_predictions.py` usa comparação de médias. O McNemar é adicional (informativo). Regra: S3b = E1-V_mean < E1-W_mean (ponto) com CI da diferença emparelhada (bootstrap B=2000).

**Problema 4: EVAL-R — não adaptar compute_regret.py**
O value regret precisa do V_mm do trio seleccionado por sorteio. mc_*_raw.csv provavelmente só tem Q2. Recalcular na GPU importando as funções sem as alterar. As três verificações embutidas (ver §8 do bundle) permanecem.

---

### A2. PRESPEC §6 — texto literal

```markdown
## 6. Predictions

For each branch b ∈ {S-T, S-N}. Conditions are resolved in Phase 1 after data extraction,
before any score or Q2 is computed.

| Id | Prediction | Condition | Type |
|---|---|---|---|
| S0 | SAW/mm/opt Q2 = 100% and R = 0 on every draw; E1-B optimal Q2 = 100% | — | Regression (failure = bug; abort before any Q2) |
| S1 | Q2(SAW, mm, greedy) > Q2(SAW, vec, greedy), 95% CI excludes 0 | TV(vec) ≥ 0.05 | Replication of Fogo main finding |
| S2 | Q2(SAW, vec, opt) < Q2(SAW, vec, grd), 95% CI excludes 0 | TV_W(vec) ≥ 0.05 | Replication of Fogo greedy reversal |
| S3a | E1-W optimal < 100% and E1-V optimal < 100% | TV_W(vec) ≥ 0.05 | E1 protocol: both TV components matter |
| S3b | E1-V optimal < E1-W optimal (direction observed in Fogo and E6) | TV_W(vec) ≥ 0.05 **and** TV_B(vec) ≥ 0.05 | E1 direction replication. V differs from W by the between-group distortion; both conditions needed to ensure the directional claim is not vacuous. |
| S4 | SAW minus TOPSIS per cell: no sign predicted | — | Descriptive |
| S5 | Q2(SAW, vec, opt) in branch b > 56.8% (Fogo result) | max_{j ∈ non-binary, non-categorical} point-mass share < 0.5 | Risky |
| S6 | R(SAW, vec, grd) > R(SAW, vec, opt), 95% CI excludes 0. Fogo reference: R(vec,grd)=6.63 pp, R(vec,opt)=5.27 pp, difference=1.36 pp. | TV_W(vec) ≥ 0.05 | Opposite direction to S2 (Q2–R discordance) |
| S7a | R(E1-B, optimal) > 0, 95% CI excludes 0. Fogo reference: 4.53 pp mean. | TV_B(vec) ≥ 0.05 | Low risk |
| S7b | R(E1-B, optimal) < R(E1-W, optimal) — Fogo ordering (4.53 pp < 6.47 pp). | TV_B(vec) ≥ 0.05 and TV_W(vec) ≥ 0.05 | Risky |

Multiple testing note: S1, S2, S3a, S3b, S5, S6, S7a, S7b (8 tested predictions) × 2 branches
= up to 16 tests. Each reported individually without multiplicity correction.
```

---

### A3. Formato e conteúdo dos CSV E1 (locais)

**Ficheiro:** `results/santiago/mc_ST_e1_fix2.csv` (2005 linhas = 1 header + 2004 dados)  
**Colunas:** `draw, kappa, e1_cell, Q2_opt, Q2_grd`

Estrutura:
- κ=200: draws 0–499 × 4 células (M, B, W, V) = 2000 linhas
- κ=∞: draw 0 × 4 células = 4 linhas

**Linhas κ=∞:**

| Branch | κ | M opt/grd | B opt/grd | W opt/grd | V opt/grd |
|--------|---|-----------|-----------|-----------|-----------|
| S-T | ∞ | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 |
| S-N | ∞ | 1 / 0 | 1 / 0 | 1 / 0 | 1 / 0 |

S-T κ=∞: greedy e optimal são ambos Pareto-eficientes (consistente com K5: "greedy = optimal em 100% dos sorteios para κ≥100 em S-T"). S-N κ=∞: optimal é sempre eficiente (K2 verificado empiricamente), greedy nunca é eficiente.

**Resultados selados κ=200 (do commit stage4-e1fix2-sealed):**

| Branch | E1-M | E1-B | E1-V | E1-W |
|--------|------|------|------|------|
| S-T | 100.0% | 100.0% | 84.2% | 80.2% |
| S-N | 100.0% | 100.0% | 98.6% | 99.2% |

---

### A4. S3a e S3b — veredictos provisórios (sem bootstrap)

**S3a:** E1-W opt < 100% AND E1-V opt < 100%

| Branch | TV_W | Testável | E1-W opt | E1-V opt | Veredicto |
|--------|------|----------|----------|----------|-----------|
| S-T | 0.1565 ≥ 0.05 ✓ | Sim | 80.2% < 100% ✓ | 84.2% < 100% ✓ | **CONFIRMED** |
| S-N | 0.0561 ≥ 0.05 ✓ | Sim | 99.2% < 100% ✓ | 98.6% < 100% ✓ | **CONFIRMED** |

**S3b:** E1-V opt < E1-W opt

| Branch | TV_W | TV_B | Testável | E1-V opt | E1-W opt | Diferença | Veredicto |
|--------|------|------|----------|----------|----------|-----------|-----------|
| S-T | 0.1565 ✓ | 0.1960 ✓ | Sim | 84.2% | 80.2% | +4.0 pp (V > W) | **NOT CONFIRMED** (sentido oposto ao Fogo) |
| S-N | 0.0561 ✓ | 0.0572 ✓ | Sim | 98.6% | 99.2% | −0.6 pp (V < W) | Aguarda CI bootstrap (diferença = 3 sorteios) |

Nota S-N: com apenas 3 sorteios de diferença (493 vs 496 / 500), o CI bootstrapped provavelmente inclui 0. Não registar como confirmada antes do bootstrap.

---

### A5. W0-001 commit (antes do PDF)

Commit `fb455f6` (2026-11-02):
- Threshold: ≤ 0.0001 (ambíguo, A6 no limite) → ≤ 0.001 (A6 = 0.0001, dentro do limite)
- Escala: explicitado que a comparação é em pesos renormalizados (sum=1)
- Retractada a hipótese de "pesos não arredondados" (contradita pela soma bruta = 0.9999)
- Activation rule: se PDF mostra |w_Cabral_renorm - w_code| > 0.001, re-run S-N

---

### A6. Ficheiros ainda em falta

| Ficheiro | Estado | Como obter |
|---|---|---|
| mc_ST_raw.csv | ✗ local | scp da Athena (SHA 123a5421d...) |
| mc_SN_raw.csv | ✗ local | scp da Athena (SHA dbfa2f00b...) |
| mc_full_20261028T1237Z_gpu.log | ✗ local | scp da Athena (SHA 0be5cf347...) |
| PDF Cabral (2012) | ✗ | Abrir à mão: hdl.handle.net/10362/8627 |
| santiago_predictions.json | ✗ (não existe) | Criar com eval v2 depois do scp |

