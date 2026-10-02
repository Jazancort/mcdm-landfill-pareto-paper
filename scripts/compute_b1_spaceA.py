"""
compute_b1_spaceA.py  (B1/D1 — recalcular tab:fourthcell linhas 473/A e 389/A)
================================================================================
Propósito: recalcular as células 473/A e 389/A da tab:fourthcell com
aspect BINÁRIO nos objectivos do avaliador (fronteira A).

A corrida original usava aspect contínuo em build_score_473. As diagonais
A' foram corrigidas por run_fourthcell_consistent.py. As células com
fronteira A (avaliador sobre 473 sites) precisam ser verificadas com
aspect binário nos objectivos.

Design:
  Score: SAW min-max sobre df_via (389 sites) — idêntico ao original
  Objectivos: calculados com aspect BINÁRIO nos grupos F1/F2/F3
  Fronteira A: sobre os 473 candidatos (não apenas os 389 admissíveis)
    → 473 sites, k=3, d_min=10km, aspect binário nos objectivos

  Células:
    473/A: score=Ncand-normalisation (build_score_473 com aspect binário),
           evaluator=A (473 sites, aspect binário)
    389/A: score=Nvia-normalisation (standard SAW),
           evaluator=A (473 sites, aspect binário)

Parâmetros: N=500, kappa=200, seed=42.
Output: results/b1/b1_spaceA.csv
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import dirichlet as sp_dirichlet

ROOT = Path(__file__).parent.parent

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, haversine_km, MIN_DIST_KM,
    F1_CRIT, F2_CRIT, F3_CRIT, COL as COL_MAP, INV, COST, _norm,
    _build_decision_matrix
)
from pareto_utils import build_pareto_utils

t0 = time.time()
print("Loading data...", flush=True)
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)

# Space A: all 473 candidates
df_all_cands = df_imp.copy()
N_all = len(df_all_cands)

# Space A': 389 admissible
df_via = df_imp[df_imp[COL['protected']] > 0].copy()
N_via = len(df_via)
assert N_via == 389, f"Expected 389, got {N_via}"

col_names = list(AHP_WEIGHTS.keys())
w_ahp = np.array(list(AHP_WEIGHTS.values()))
print(f"  N_all={N_all}, N_via={N_via}  t={time.time()-t0:.1f}s", flush=True)

# ── Build trios over space A (473 sites, k=3, d_min=10km) ─────────────────
print("Building trios over space A (473 sites)...", flush=True)
D_all = haversine_km(df_all_cands['latitude (degrees)'].values,
                     df_all_cands['longitude (degrees)'].values)
valid_all = D_all >= MIN_DIST_KM
trios_A_list = [(i, j, k)
                for i in range(N_all) for j in range(i+1, N_all) if valid_all[i, j]
                for k in range(j+1, N_all) if valid_all[i, k] and valid_all[j, k]]
trios_A = np.array(trios_A_list, dtype=np.int32)
T0A, T1A, T2A = trios_A[:, 0], trios_A[:, 1], trios_A[:, 2]
n_trios_A = len(trios_A)
print(f"  Trios A: {n_trios_A:,}  t={time.time()-t0:.1f}s", flush=True)

# ── Build trios over space A' (389 admissible, same as main factorial) ──────
print("Building trios over space A'...", flush=True)
D_via = haversine_km(df_via['latitude (degrees)'].values,
                     df_via['longitude (degrees)'].values)
valid_via = D_via >= MIN_DIST_KM
trios_Ap_list = [(i, j, k)
                 for i in range(N_via) for j in range(i+1, N_via) if valid_via[i, j]
                 for k in range(j+1, N_via) if valid_via[i, k] and valid_via[j, k]]
trios_Ap = np.array(trios_Ap_list, dtype=np.int32)
n_trios_Ap = len(trios_Ap)
print(f"  Trios A': {n_trios_Ap:,}  t={time.time()-t0:.1f}s", flush=True)

# ── Pareto utilities for space A (473 sites, binary aspect in objectives) ───
# build_pareto_utils with df_all_cands uses binary aspect automatically
# (pareto_utils uses k=="aspect" → np.where encoding)
_, is_dominated_A, _ = build_pareto_utils(
    df_all_cands, col_names, trios_A, eps=1e-9
)
print(f"  Space A utilities ready  t={time.time()-t0:.1f}s", flush=True)

# ── Pareto utilities for space A' (389 admissible, binary aspect) ────────────
compute_objs_Ap, is_dominated_Ap, _ = build_pareto_utils(
    df_via, col_names, trios_Ap, eps=1e-9
)
print(f"  Space A' utilities ready  t={time.time()-t0:.1f}s", flush=True)

# ── Score matrices ─────────────────────────────────────────────────────────
# Score 473: SAW min-max normalised over 473 sites (but aspect BINARY)
# Use build_score_473 logic from mc_2cube_fixed but with binary aspect
def build_score_473_binary(w, df_via, df_imp, col_names):
    """SAW score using 473-site normalisation constants, binary aspect."""
    N_v = len(df_via)
    M = len(col_names)
    Xb = np.zeros((N_v, M), dtype=np.float64)
    for j, crit in enumerate(col_names):
        col = COL_MAP[crit]
        x_via = df_via[col].values.astype(float)
        x_all = df_imp[col].values.astype(float)
        if crit == "aspect":
            # Binary encoding (same as objectives)
            c_via = np.where((x_via >= 90) & (x_via <= 180), 0.0, 1.0)
            Xb[:, j] = c_via
        elif crit in COST:
            mn, mx = x_all.min(), x_all.max()
            rng = mx - mn if mx > mn else 1.0
            Xb[:, j] = (x_via - mn) / rng
        elif crit in INV:
            mn, mx = x_all.min(), x_all.max()
            rng = mx - mn if mx > mn else 1.0
            Xb[:, j] = 1.0 - (x_via - mn) / rng
        else:  # benefit
            mn, mx = x_all.min(), x_all.max()
            rng = mx - mn if mx > mn else 1.0
            Xb[:, j] = (x_via - mn) / rng
    return Xb @ w

# Score 389: standard SAW (binary aspect via _build_decision_matrix)
X_via_raw, benefit_flags = _build_decision_matrix(df_via)
X_adj_389 = X_via_raw.copy()
for j, b in enumerate(benefit_flags):
    if not b:
        X_adj_389[:, j] = 1.0 - X_via_raw[:, j]
def score_389(w): return X_adj_389 @ w

# ── Objective arrays over space A (for both 473/A and 389/A cells) ──────────
# compute_objs_A_fn: builds F1v, F2v, F3v over 473 sites with binary aspect
# We use build_pareto_utils which already uses binary aspect internally
# But we need F1v[T0A]+... for trios over A
# Re-use compute_objs_Ap but adapted for space A
_, _, _ = build_pareto_utils(df_all_cands, col_names, trios_A, eps=1e-9)
compute_objs_A, is_dominated_A_check, _ = build_pareto_utils(
    df_all_cands, col_names, trios_A, eps=1e-9
)
# is_dominated_A_check == is_dominated_A (same)

# ── Mapping: A' indices → A indices ─────────────────────────────────────────
# trios_A are indices into df_all_cands (0..472)
# trios_Ap are indices into df_via (0..388)
# We need: for a portfolio from score_473 or score_389 (indices 0..388 in df_via),
# find its position in trios_A (indices 0..472 in df_all_cands)
via_global = df_via.index.values    # global row indices of df_via in df_imp
all_global = df_all_cands.index.values  # global row indices of all 473
g2l_all = {g: l for l, g in enumerate(all_global)}  # global → local in A

def to_A_local(via_local_trio):
    """Convert 3 local df_via indices → 3 local df_all indices."""
    return [g2l_all[via_global[i]] for i in via_local_trio]

# ── Greedy assembly ──────────────────────────────────────────────────────────
def top_greedy(scores, valid):
    order = np.argsort(scores)[::-1]
    sel = []
    for idx in order:
        if all(valid[idx, s] for s in sel): sel.append(idx)
        if len(sel) == 3: break
    return sel if len(sel) == 3 else None

def top_opt_via(scores):
    T0, T1, T2 = trios_Ap[:, 0], trios_Ap[:, 1], trios_Ap[:, 2]
    ts = scores[T0] + scores[T1] + scores[T2]
    return list(trios_Ap[int(np.argmax(ts))])

# ── Monte Carlo ──────────────────────────────────────────────────────────────
N_DRAWS = 500; KAPPA = 200; SEED = 42
W_draws = sp_dirichlet.rvs(KAPPA * w_ahp, size=N_DRAWS,
                            random_state=np.random.default_rng(SEED))

cells = [
    ("473/A", "greedy"),
    ("473/A", "optimal"),
    ("389/A", "greedy"),
    ("389/A", "optimal"),
]

rows = []
for score_set, asm in cells:
    print(f"\n=== {score_set}/{asm} ===", flush=True)
    nd_cnt = 0; t_cell = time.time()

    for di, w in enumerate(W_draws):
        # Objectives: space A (473 sites, binary aspect)
        f1v, f2v, f3v = compute_objs_A(w)
        F1 = f1v[T0A] + f1v[T1A] + f1v[T2A]
        F2 = f2v[T0A] + f2v[T1A] + f2v[T2A]
        F3 = f3v[T0A] + f3v[T1A] + f3v[T2A]

        # Score
        if score_set == "473/A":
            sc_via = build_score_473_binary(w, df_via, df_imp, col_names)
        else:
            sc_via = score_389(w)

        # Assembly (over A' = 389 sites)
        if asm == "optimal":
            trio_via = top_opt_via(sc_via)
        else:
            trio_g = top_greedy(sc_via, valid_via)
            trio_via = trio_g if trio_g else None

        if trio_via is None:
            continue

        # Convert to A indices for is_dominated_A
        trio_A = to_A_local(trio_via)

        if not is_dominated_A(np.array(trio_A), F1, F2, F3):
            nd_cnt += 1

        if di % 50 == 0:
            eta = (time.time()-t_cell) / (di+1) * (N_DRAWS-di-1)
            print(f"  {di}/{N_DRAWS} Q2={nd_cnt/(di+1)*100:.1f}% eta={eta:.0f}s",
                  flush=True)

    Q2 = nd_cnt / N_DRAWS * 100
    SE = np.sqrt(Q2 * (100 - Q2) / N_DRAWS)
    print(f"  RESULT: Q2={Q2:.1f}% SE={SE:.2f}  t={time.time()-t_cell:.0f}s",
          flush=True)
    rows.append({
        "score_set": score_set, "assembly": asm,
        "Q2": round(Q2, 2), "SE": round(SE, 3),
        "n_trios_A": n_trios_A
    })

out = ROOT / "results" / "b1"
out.mkdir(exist_ok=True)
df = pd.DataFrame(rows)
df.to_csv(out / "b1_spaceA.csv", index=False)
print(f"\n=== B1 RESULTS ===\n{df.to_string(index=False)}")
print(f"\nTotal: {time.time()-t0:.1f}s")
