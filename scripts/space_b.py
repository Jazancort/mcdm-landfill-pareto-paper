# -*- coding: utf-8 -*-
"""
space_b.py  —  Tarefa 4: Espaço de avaliação B (não aditivo)
Objetivos (todos para maximizar):
  B1 = min safety score entre os k locais  →  gargalo de segurança
  B2 = min distância entre pares (km)      →  dispersão mínima
  B3 = média urban_norm dos k locais       →  acesso a zonas urbanas

Fronteira exata via enumeração + algoritmo de Pareto 3D eficiente.
Avalia os trios canônicos dos métodos no espaço B.

Run:  uv run --with pandas --with numpy python scripts/space_b.py
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

from mcdm_experiment import (
    load_data, impute_nan, haversine_km,
    COL, AHP_WEIGHTS, MIN_DIST_KM,
)

# ─── load ─────────────────────────────────────────────────────────────────────
print("Carregando dados...")
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
via_global = df_via.index.values
N = len(df_via)

D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)

# ─── f3 por site (safety, normalizado sobre 473) ─────────────────────────────
def compute_f3_per_site(df_all_imp):
    sc = np.zeros(len(df_all_imp))
    cols = {"urban": COL["urban"], "aero": COL["aero"], "cult": COL["cult"]}
    ws   = {k: AHP_WEIGHTS[k] for k in cols}
    w_sum = sum(ws.values())
    for k, col in cols.items():
        v = df_all_imp[col].values.astype(float)
        mn, mx = np.nanmin(v), np.nanmax(v)
        n = (v - mn) / (mx - mn + 1e-12)
        n = np.nan_to_num(n, nan=0.5)
        sc += (ws[k] / w_sum) * n
    return sc

f3_473 = compute_f3_per_site(df_imp)
idx_in_473 = {gid: i for i, gid in enumerate(df_all.index)}
print(f"f3_per_site range: [{f3_473.min():.4f}, {f3_473.max():.4f}]")

# f3 nos 389 viáveis (índice local 0..388)
f3_via = np.array([f3_473[idx_in_473[int(gid)]] for gid in via_global])

# urban_norm nos 389 viáveis
ud_min = df_imp[COL["urban"]].min()
ud_max = df_imp[COL["urban"]].max()
urban_norm = (df_via[COL["urban"]].values - ud_min) / (ud_max - ud_min + 1e-12)

# ─── enumeração dos trios viáveis com objetivos B ────────────────────────────
print(f"Enumerando trios viáveis (N={N})...")
t0 = time.time()
valid = D_via >= MIN_DIST_KM  # (N, N) bool

B1_list, B2_list, B3_list = [], [], []
trio_ids = []

for i in range(N):
    for j in range(i + 1, N):
        if not valid[i, j]:
            continue
        for k in range(j + 1, N):
            if not valid[i, k] or not valid[j, k]:
                continue
            B1_list.append(min(f3_via[i], f3_via[j], f3_via[k]))
            B2_list.append(min(D_via[i, j], D_via[i, k], D_via[j, k]))
            B3_list.append((urban_norm[i] + urban_norm[j] + urban_norm[k]) / 3)
            trio_ids.append((i, j, k))

B1 = np.array(B1_list, dtype=np.float32)
B2 = np.array(B2_list, dtype=np.float32)
B3 = np.array(B3_list, dtype=np.float32)
M  = len(B1)
print(f"Trios viáveis: {M:,}  ({time.time()-t0:.1f}s)")

# ─── Pareto front 3D (maximizar B1, B2, B3) ─────────────────────────────────
# Algoritmo: sort por (-B1, -B2, -B3) lexicográfico.
# Ao varrer, manter lista de não-dominados vistos.
# Trio i é dominado se existe j anterior com B2[j]>=B2[i] e B3[j]>=B3[i]
# e (B2[j]>B2[i] ou B3[j]>B3[i])  [B1[j]>=B1[i] garantido pela ordem]
# Mantemos lista de candidatos reduzida: ao adicionar novo não-dominado,
# removemos da lista quem ele domina.
print("Calculando fronteira Pareto B...")
t0 = time.time()

order = np.lexsort((-B3, -B2, -B1))  # lex desc
B1s, B2s, B3s = B1[order], B2[order], B3[order]

non_dom = np.zeros(M, dtype=bool)
# cand_* = listas dos candidatos não-dominados até o ponto atual
cand_b2 = np.empty(0, dtype=np.float32)
cand_b3 = np.empty(0, dtype=np.float32)

REPORT = 400_000
for i in range(M):
    if i % REPORT == 0 and i > 0:
        print(f"  {i:,}/{M:,}  |cand|={len(cand_b2):,}  ({time.time()-t0:.0f}s)")
    b2i, b3i = B2s[i], B3s[i]

    if len(cand_b2):
        # Dominado se existe candidato com B2>=b2i e B3>=b3i e (B2>b2i ou B3>b3i)
        mask = (cand_b2 >= b2i) & (cand_b3 >= b3i) & ((cand_b2 > b2i) | (cand_b3 > b3i))
        if mask.any():
            continue  # dominado

    # Não dominado → adicionar
    non_dom[i] = True

    if len(cand_b2):
        # Remover candidatos que i domina: b2i>=B2[c] e b3i>=B3[c] e (b2i>B2[c] ou b3i>B3[c])
        keep = ~((b2i >= cand_b2) & (b3i >= cand_b3) & ((b2i > cand_b2) | (b3i > cand_b3)))
        cand_b2 = np.append(cand_b2[keep], b2i)
        cand_b3 = np.append(cand_b3[keep], b3i)
    else:
        cand_b2 = np.array([b2i], dtype=np.float32)
        cand_b3 = np.array([b3i], dtype=np.float32)

# Mapear de volta para ordem original
pareto_b = np.zeros(M, dtype=bool)
pareto_b[order] = non_dom
n_pb = pareto_b.sum()
print(f"Fronteira Pareto B: {n_pb:,} trios  ({time.time()-t0:.1f}s)")

# ─── estatísticas da fronteira B ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("Estatísticas — Fronteira Pareto B")
print(f"  n_pareto_B : {n_pb:,}")
print(f"  B1 range   : [{B1[pareto_b].min():.4f}, {B1[pareto_b].max():.4f}]")
print(f"  B2 range   : [{B2[pareto_b].min():.2f}, {B2[pareto_b].max():.2f}] km")
print(f"  B3 range   : [{B3[pareto_b].min():.4f}, {B3[pareto_b].max():.4f}]")

# Sites únicos na fronteira B
front_b_sites = set()
for idx in np.where(pareto_b)[0]:
    i, j, k = trio_ids[idx]
    front_b_sites.update([int(via_global[i]), int(via_global[j]), int(via_global[k])])
print(f"  Sites únicos: {len(front_b_sites)}")

# Sobreposição com fronteira A (213 trios)
front_a = set(frozenset([int(r.idx1), int(r.idx2), int(r.idx3)]) for _, r in par.iterrows())
front_b_set = set()
for idx in np.where(pareto_b)[0]:
    i, j, k = trio_ids[idx]
    front_b_set.add(frozenset([int(via_global[i]), int(via_global[j]), int(via_global[k])]))
overlap = len(front_a & front_b_set)
print(f"  Trios em A∩B: {overlap}  (A={len(front_a)}, B={n_pb})")

# ─── avaliação dos trios canônicos ───────────────────────────────────────────
print("\n" + "=" * 60)
print("Avaliação dos trios canônicos — Espaço B")
print(f"  {'Label':22s}  {'B1_min':>7}  {'B2_km':>7}  {'B3_urb':>7}  in_front_B")

global_to_local = {int(gid): li for li, gid in enumerate(via_global)}

CANONICAL = [
    ("SAW greedy",        (184, 279, 320)),
    ("SAW optimal",       (184, 430, 460)),
    ("TOPSIS-VN greedy",  (233, 320, 355)),
    ("TOPSIS-VN optimal", (227, 233, 345)),
    ("TOPSIS-MM greedy",  (184, 227, 460)),
    ("VIKOR greedy",      (233, 279, 320)),
    ("PROMETHEE greedy",  (51, 233, 345)),
    ("BCS_IEEE",          (184, 430, 460)),
]

results_b = []
for label, gids in CANONICAL:
    li = [global_to_local[g] for g in gids]
    b1 = min(f3_via[li[0]], f3_via[li[1]], f3_via[li[2]])
    b2 = min(D_via[li[0], li[1]], D_via[li[0], li[2]], D_via[li[1], li[2]])
    b3 = (urban_norm[li[0]] + urban_norm[li[1]] + urban_norm[li[2]]) / 3
    inf_b = frozenset(gids) in front_b_set
    print(f"  {label:22s}  {b1:7.4f}  {b2:7.2f}  {b3:7.4f}  {inf_b}")
    results_b.append({"label": label, "B1": b1, "B2_km": b2, "B3": b3, "in_front_B": inf_b})

# ─── salvar ─────────────────────────────────────────────────────────────────
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)
pd.DataFrame(results_b).to_csv(os.path.join(RESULTS_DIR, "space_b_canonical.csv"), index=False)

pb_rows = []
for idx in np.where(pareto_b)[0]:
    i, j, k = trio_ids[idx]
    pb_rows.append({"B1": float(B1[idx]), "B2": float(B2[idx]), "B3": float(B3[idx]),
                    "idx1": int(via_global[i]), "idx2": int(via_global[j]),
                    "idx3": int(via_global[k])})
pd.DataFrame(pb_rows).to_csv(os.path.join(RESULTS_DIR, "pareto_front_B.csv"), index=False)
print(f"\nResultados salvos em scripts/results/")
