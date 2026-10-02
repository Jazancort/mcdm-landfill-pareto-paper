"""
compute_b1_spaceA.py  —  B1/D1 corrected (v2)
==============================================
Recalculates tab:fourthcell rows 473/A and 389/A with the correct design:

  Trios:       the same 1,944,653 admissible trios (indices into df_via, 389 sites)
  Evaluator A: objectives normalised with ref_df=df_all (473-site constants),
               binary aspect, portfolios restricted to df_via sites
               → build_pareto_utils(df_via, ..., ref_df=df_all)
  Score 473:   SAW with 473-site normalisation constants (ref_df=df_all), binary aspect
  Score 389:   SAW with 389-site normalisation constants (ref_df=df_via), binary aspect

Proposition 1 requires:
  473/A optimal = 100%  (score and evaluator share ref_df=df_all, binary aspect)
  389/A optimal = measured  (score ref=df_via, evaluator ref=df_all → mixed)

The script aborts with sys.exit(1) if 473/A optimal deviates from 100%.
N=500, kappa=200, seed=42.
Output: results/b1/b1_spaceA.csv
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import dirichlet as sp_dirichlet

ROOT = Path(__file__).parent.parent
if "MCDM_DATA_DIR" not in os.environ:
    athena = "/home/julioazancort/scratch/mcdm"
    os.environ["MCDM_DATA_DIR"] = athena if os.path.exists(athena) else str(ROOT / "data")

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS,
    haversine_km, MIN_DIST_KM,
    _build_decision_matrix, INV, COST, _norm,
)
from pareto_utils import build_pareto_utils

t0 = time.time()
print("Loading data...", flush=True)
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
assert len(df_imp) == 473, f"Expected 473 candidates, got {len(df_imp)}"

df_via = df_imp[df_imp[COL['protected']] > 0].copy()
assert len(df_via) == 389, f"Expected 389 admissible sites, got {len(df_via)}"

col_names = list(AHP_WEIGHTS.keys())
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
N = len(df_via)
print(f"  df_all={len(df_imp)}, df_via={N}  t={time.time()-t0:.1f}s", flush=True)

# ── Trios: 1,944,653 admissible (indices into df_via, same as main factorial) ──
print("Building trios (df_via, 389 sites)...", flush=True)
D = haversine_km(df_via['latitude (degrees)'].values,
                 df_via['longitude (degrees)'].values)
valid = D >= MIN_DIST_KM
trios_list = [(i, j, k)
              for i in range(N) for j in range(i+1, N) if valid[i, j]
              for k in range(j+1, N) if valid[i, k] and valid[j, k]]
trios = np.array(trios_list, dtype=np.int32)
assert len(trios) == 1_944_653, f"Expected 1,944,653 trios, got {len(trios)}"
T0, T1, T2 = trios[:, 0], trios[:, 1], trios[:, 2]
print(f"  Trios: {len(trios):,}  t={time.time()-t0:.1f}s", flush=True)

# ── Evaluator A': ref_df=df_via (standard, same as main factorial) ─────────────
compute_Ap, is_dom_Ap, _ = build_pareto_utils(
    df_via, col_names, trios, ref_df=df_via
)
print(f"  Evaluator A' ready  t={time.time()-t0:.1f}s", flush=True)

# ── Evaluator A: ref_df=df_all (473-site normalisation constants) ───────────────
# Portfolios are still restricted to df_via sites (trios index into df_via).
# Only the normalisation min/max per column comes from df_all.
compute_A, is_dom_A, _ = build_pareto_utils(
    df_via, col_names, trios, ref_df=df_imp
)
print(f"  Evaluator A  ready  t={time.time()-t0:.1f}s", flush=True)

# ── Score matrices ──────────────────────────────────────────────────────────────
# Score 389: SAW with ref=df_via (standard, binary aspect via _build_decision_matrix)
X_raw, benefit = _build_decision_matrix(df_via)
X_adj_389 = X_raw.copy()
for j, b in enumerate(benefit):
    if not b:
        X_adj_389[:, j] = 1.0 - X_raw[:, j]

def score_389(w):
    return X_adj_389 @ w

# Score 473: SAW with ref=df_all (473-site normalisation), binary aspect
# Must use same encoding as evaluator A to satisfy Prop1 on the diagonal.
X_raw_473 = np.zeros((N, len(col_names)), dtype=np.float64)
for j, k in enumerate(col_names):
    x_via = df_via[COL[k]].values.astype(float)
    x_all = df_imp[COL[k]].values.astype(float)
    if k == "aspect":
        # Binary: leeward (90-180°) → 0 (favourable for cost), windward → 1
        c = np.where((x_via >= 90) & (x_via <= 180), 0.0, 1.0)
        X_raw_473[:, j] = c        # already "benefit" orientation for SAW
    elif k in COST:
        mn, mx = x_all.min(), x_all.max()
        X_raw_473[:, j] = (x_via - mn) / max(mx - mn, 1e-12)
    else:  # INV or BENEFIT
        mn, mx = x_all.min(), x_all.max()
        X_raw_473[:, j] = (x_via - mn) / max(mx - mn, 1e-12)

# Adjust orientation to benefit (higher = better for SAW score)
X_adj_473 = X_raw_473.copy()
_, benefit_flags = _build_decision_matrix(df_via)  # get orientation flags
for j, b in enumerate(benefit_flags):
    if k == "aspect":
        pass   # already handled above as benefit
    elif not b:
        X_adj_473[:, j] = 1.0 - X_raw_473[:, j]

def score_473(w):
    return X_adj_473 @ w

# ── Greedy assembly ─────────────────────────────────────────────────────────────
def top_greedy(sc):
    order = np.argsort(sc)[::-1]
    sel = []
    for idx in order:
        if all(valid[idx, s] for s in sel):
            sel.append(idx)
        if len(sel) == 3:
            break
    return tuple(sel) if len(sel) == 3 else None

def top_optimal(sc):
    ts = sc[T0] + sc[T1] + sc[T2]
    best = int(np.argmax(ts))
    return (int(T0[best]), int(T1[best]), int(T2[best]))

# ── Monte Carlo ─────────────────────────────────────────────────────────────────
N_DRAWS = 500; KAPPA = 200; SEED = 42
rng = np.random.default_rng(SEED)
W_draws = sp_dirichlet.rvs(KAPPA * w_ahp, size=N_DRAWS, random_state=rng)

cells = [
    ("473/A", "optimal",  score_473, compute_A,  is_dom_A),
    ("473/A", "greedy",   score_473, compute_A,  is_dom_A),
    ("389/A", "optimal",  score_389, compute_A,  is_dom_A),
    ("389/A", "greedy",   score_389, compute_A,  is_dom_A),
]

rows = []
for score_set, asm, score_fn, compute_fn, is_dom_fn in cells:
    print(f"\n=== {score_set}/{asm} ===", flush=True)
    nd = 0; t_cell = time.time()

    for di, w in enumerate(W_draws):
        # Objectives for evaluator (A or A')
        f1v, f2v, f3v = compute_fn(w)
        F1 = f1v[T0] + f1v[T1] + f1v[T2]
        F2 = f2v[T0] + f2v[T1] + f2v[T2]
        F3 = f3v[T0] + f3v[T1] + f3v[T2]

        # Score and assembly
        sc = score_fn(w)
        trio = top_optimal(sc) if asm == "optimal" else top_greedy(sc)
        if trio is None:
            continue

        if not is_dom_fn(trio, F1, F2, F3):
            nd += 1

        if di % 50 == 0:
            eta = (time.time() - t_cell) / (di + 1) * (N_DRAWS - di - 1)
            print(f"  {di}/{N_DRAWS}  Q2={nd/(di+1)*100:.1f}%  eta={eta:.0f}s",
                  flush=True)

    Q2 = nd / N_DRAWS * 100
    SE = np.sqrt(Q2 * (100 - Q2) / N_DRAWS)
    print(f"  RESULT: Q2={Q2:.1f}%  SE={SE:.2f}  t={time.time()-t_cell:.0f}s",
          flush=True)
    rows.append({"score_set": score_set, "assembly": asm,
                 "Q2": round(Q2, 2), "SE": round(SE, 3)})

print(f"\n=== B1 RESULTS ===")
df_out = pd.DataFrame(rows)
print(df_out.to_string(index=False))

# ── REGRESSION CHECK: 473/A optimal must = 100% (Proposition 1) ──────────────
val_473A_opt = df_out.loc[
    (df_out.score_set == "473/A") & (df_out.assembly == "optimal"), "Q2"
].iloc[0]

if abs(val_473A_opt - 100.0) > 0.5:
    print(f"\nREGRESSION FAIL: 473/A optimal = {val_473A_opt:.1f}% (expected 100%).")
    print("Score and evaluator A share the same ref_df=df_all and binary aspect.")
    print("A value < 100% means score/objective columns are misaligned. DO NOT commit.")
    sys.exit(1)
else:
    print(f"\nREGRESSION OK: 473/A optimal = {val_473A_opt:.1f}% ✓")

out = ROOT / "results" / "b1"
out.mkdir(exist_ok=True)
df_out.to_csv(out / "b1_spaceA.csv", index=False)
print(f"Saved: {out / 'b1_spaceA.csv'}")
print(f"Total: {time.time()-t0:.1f}s")
