"""scripts/run_e4_vstar.py
Exploratory cells R-V* and R-asp, declared post hoc in DEV-E4-007.

R-V*: score = X_adj_dm * r_j  (aspect binary, same as evaluator)
      This is the correct PRESPEC cell V. If R-V* ≈ 100%, aspect coding explains
      the 80 pp. The only difference from R-V is: R-V uses Xadj473 (aspect continuous);
      R-V* uses X_adj_dm * r_j (aspect binary, same as _build_decision_matrix).

R-asp: score = X_adj_dm with aspect column replaced by Xadj473_aspect (continuous
       azimuth, 389-site constants). Isolates the aspect coding effect alone.
       Prediction: Q2 ≈ 24% (replicates v4 finding: R-M gave 24% with raw Xadj389).

Same matrix e1_weights_k200.npy (SHA-256 verified), N=500, kappa in {50, 200}.
"""
import hashlib, os, sys, time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT    = Path(__file__).parent.parent
RESULTS = ROOT / "results"
sys.path.insert(0, str(ROOT / "scripts"))

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS,
    haversine_km, greedy_trio, MIN_DIST_KM,
    _build_decision_matrix, COST as COST_SET,
)
from pareto_utils import build_pareto_utils

EPS       = 1e-9
N_DRAWS   = 500
SEED      = 42
KAPPA_PRI = 200
KAPPA_SEC = 50
E1_SHA256 = "bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487"

# ── Load data ──────────────────────────────────────────────────────────────────
if "MCDM_DATA_DIR" not in os.environ:
    athena = "/home/julioazancort/scratch/mcdm"
    os.environ["MCDM_DATA_DIR"] = athena if os.path.exists(athena) else str(ROOT/"data")

df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
viable_mask = df_imp[COL["protected"]] > 0
df_via = df_imp[viable_mask].copy()
assert len(df_imp) == 473; assert len(df_via) == 389

w_ahp     = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
N = len(df_via); M = len(col_names)

# ── Verify weight matrix ───────────────────────────────────────────────────────
wmat_path = RESULTS / "e1_weights_k200.npy"
sha = hashlib.sha256(wmat_path.read_bytes()).hexdigest()
assert sha == E1_SHA256, f"SHA-256 mismatch: {sha}"
w_matrix = np.load(wmat_path)
print(f"Weight matrix OK: {w_matrix.shape}  SHA-256 verified")

# ── Build score matrices ───────────────────────────────────────────────────────
# X_adj_dm: _build_decision_matrix (aspect binary: 1 if [90,180], else 0)
X_via_dm, _ = _build_decision_matrix(df_via)
X_adj_dm    = X_via_dm.copy()
for jj, b in enumerate(_build_decision_matrix(df_via)[1]):
    if not b: X_adj_dm[:, jj] = 1.0 - X_via_dm[:, jj]

# r_j = range_389 / range_473
r_vec = np.zeros(M)
for jj, crit in enumerate(col_names):
    x_via_raw = df_via[COL[crit]].values.astype(float)
    x_all_raw = df_imp[COL[crit]].values.astype(float)
    rng473 = x_all_raw.max() - x_all_raw.min() or 1.0
    rng389 = x_via_raw.max() - x_via_raw.min() or 1.0
    r_vec[jj] = rng389 / rng473

# Xadj473_aspect: aspect column as continuous (azimuth in degrees, 473-base)
J_ASPECT = col_names.index("aspect")
x_asp_all = df_imp[COL["aspect"]].values.astype(float)
x_asp_via = df_via[COL["aspect"]].values.astype(float)
mn473_asp = x_asp_all.min(); rng473_asp = x_asp_all.max() - mn473_asp or 1.0
xb473_asp = (x_asp_via - mn473_asp) / rng473_asp  # continuous, 473-base, [0,1]
# aspect is benefit=True in _build_decision_matrix => no flip needed
Xadj473_asp = xb473_asp   # already benefit-adjusted (higher = better in score)

# R-V*: X_adj_dm * r_j  (aspect binary, amplitudes r_j)
X_Vstar = X_adj_dm * r_vec

# R-asp: X_adj_dm but aspect column replaced with continuous azimuth (389-base)
X_adj_asp = X_adj_dm.copy()
# 389-base continuous aspect: (x_via - min_via) / range_via
mn389_asp = x_asp_via.min(); rng389_asp = x_asp_via.max() - mn389_asp or 1.0
xb389_asp = (x_asp_via - mn389_asp) / rng389_asp
X_adj_asp[:, J_ASPECT] = xb389_asp

print(f"R-V*  aspect col: binary (X_adj_dm * r_j).  r_aspect={r_vec[J_ASPECT]:.4f}")
print(f"R-asp aspect col: continuous raw, 389-base.")
print()

# ── Trios ──────────────────────────────────────────────────────────────────────
D = haversine_km(df_via["latitude (degrees)"].values, df_via["longitude (degrees)"].values)
valid = D >= MIN_DIST_KM
trios_list = []
for i in range(N):
    for j in range(i+1, N):
        if not valid[i, j]: continue
        for k in range(j+1, N):
            if valid[i, k] and valid[j, k]: trios_list.append((i, j, k))
trios = np.array(trios_list, dtype=np.int32)
assert len(trios) == 1_944_653
T0, T1, T2 = trios[:,0], trios[:,1], trios[:,2]
print(f"Trios: {len(trios):,}")

compute_objs, is_dominated, _ = build_pareto_utils(df_via, col_names, trios, eps=EPS)

# ── Monte Carlo ────────────────────────────────────────────────────────────────
print("\nMonte Carlo:")
records = []
for kappa in [KAPPA_PRI, KAPPA_SEC]:
    if kappa == KAPPA_PRI:
        w_draws = w_matrix
    else:
        rng = np.random.default_rng(SEED)
        _ = rng.dirichlet(KAPPA_PRI * w_ahp, size=N_DRAWS)
        w_draws = rng.dirichlet(kappa * w_ahp, size=N_DRAWS)

    for cell_name, X_cell in [("R-V*", X_Vstar), ("R-asp", X_adj_asp)]:
        nd_g = 0; nd_o = 0; t0 = time.time()
        for draw_idx in range(N_DRAWS):
            w = w_draws[draw_idx]
            sc = (X_cell * w).sum(1)
            f1v, f2v, f3v = compute_objs(w)
            F1 = f1v[T0]+f1v[T1]+f1v[T2]
            F2 = f2v[T0]+f2v[T1]+f2v[T2]
            F3 = f3v[T0]+f3v[T1]+f3v[T2]
            idx_g = greedy_trio(sc, D)
            nd_g += int(not is_dominated(idx_g, F1, F2, F3))
            st = sc[T0]+sc[T1]+sc[T2]
            idx_o = np.array([T0[st.argmax()], T1[st.argmax()], T2[st.argmax()]])
            nd_o += int(not is_dominated(idx_o, F1, F2, F3))
        Q2g = nd_g/N_DRAWS*100; Q2o = nd_o/N_DRAWS*100
        SEg = (Q2g*(100-Q2g)/N_DRAWS)**.5; SEo = (Q2o*(100-Q2o)/N_DRAWS)**.5
        print(f"  kappa={kappa} {cell_name:6s}: grd={Q2g:.1f}% opt={Q2o:.1f}%  ({time.time()-t0:.1f}s)")
        records.append({"kappa": kappa, "cell": cell_name,
                        "Q2_greedy": round(Q2g,2), "SE_greedy": round(SEg,3),
                        "Q2_optimal": round(Q2o,2), "SE_optimal": round(SEo,3),
                        "n_draws": N_DRAWS})

out = RESULTS / "e4_vstar_results.csv"
pd.DataFrame(records).to_csv(out, index=False)
print(f"\nSaved: {out}")
print(f"Commit: {os.popen('git rev-parse HEAD').read().strip()}")
