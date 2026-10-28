"""scripts/diag_e1_greedy_rvstar.py
E1 exploratory diagnostic: why does R-V* (X_adj_dm * r_j, aspect binary)
achieve greedy = 97.8% while R-M (X_adj_dm) achieves only 86.0%?

Measures:
1. W_g^eff for r_j pattern: effective group weights under amplitude r_j
2. TV_W(r_j) and TV_B(r_j): within- and between-group distortion
3. Proportion of draws where greedy == optimal (both R-V* and R-M)
4. For draws where R-V* greedy succeeds but R-M greedy fails:
   - percentiles of the greedy portfolio in F1, F2, F3 under R-V*
   - compare to the optimal portfolio
5. Foreclosure analysis: does R-V* greedy pick the same top site as optimal?

Exploratory, declared post hoc. Results reported as 'consistent with' not as evidence.
"""
import os, sys, time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

if "MCDM_DATA_DIR" not in os.environ:
    athena = "/home/julioazancort/scratch/mcdm"
    os.environ["MCDM_DATA_DIR"] = athena if os.path.exists(athena) else str(ROOT/"data")

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS,
    haversine_km, greedy_trio, MIN_DIST_KM,
    _build_decision_matrix,
)
from pareto_utils import build_pareto_utils

EPS     = 1e-9
N_DRAWS = 500
SEED    = 42
KAPPA   = 200
E1_SHA  = "bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487"

# ── Data ──────────────────────────────────────────────────────────────────────
import hashlib
df_all,_,_ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]]>0].copy()
N = len(df_via)
col_names = list(AHP_WEIGHTS.keys())
w_ahp = np.array(list(AHP_WEIGHTS.values()))
M = len(col_names)

wmat_path = ROOT / "results" / "e1" / "e1_weights_k200.npy"
assert hashlib.sha256(wmat_path.read_bytes()).hexdigest() == E1_SHA
w_matrix = np.load(wmat_path)

D = haversine_km(df_via["latitude (degrees)"].values, df_via["longitude (degrees)"].values)
valid = D >= MIN_DIST_KM

# ── Trios ─────────────────────────────────────────────────────────────────────
trios_list = [(i,j,k) for i in range(N) for j in range(i+1,N) if valid[i,j]
              for k in range(j+1,N) if valid[i,k] and valid[j,k]]
trios = np.array(trios_list, dtype=np.int32)
T0,T1,T2 = trios[:,0],trios[:,1],trios[:,2]
n = len(trios)
print(f"Trios: {n:,}", flush=True)

compute_objs, is_dominated, _ = build_pareto_utils(df_via, col_names, trios, eps=EPS)

# ── Matrices ──────────────────────────────────────────────────────────────────
X_raw, benefit = _build_decision_matrix(df_via)
X_adj = X_raw.copy()
for jj,b in enumerate(benefit):
    if not b: X_adj[:,jj] = 1.0 - X_raw[:,jj]

r_vec = np.array([
    (df_via[COL[c]].values.astype(float).max() - df_via[COL[c]].values.astype(float).min()) /
    max(df_imp[COL[c]].values.astype(float).max() - df_imp[COL[c]].values.astype(float).min(), 1e-12)
    for c in col_names
])

X_RVstar = X_adj * r_vec   # R-V* (aspect binary, amplitudes r_j)
X_RM     = X_adj           # R-M  (aspect binary, amplitudes 1)

# ── 1. W_g^eff under r_j ─────────────────────────────────────────────────────
GROUPS = {"G1":["perm","slope","roads"], "G2":["rivers","aspect","coast","protected","wells"], "G3":["urban","aero","cult"]}
print("\n=== 1. W_g^eff under r_j pattern ===")
for g, crits in GROUPS.items():
    W_g = sum(AHP_WEIGHTS[c] for c in crits)
    rbar_g = sum(AHP_WEIGHTS[c]*r_vec[col_names.index(c)] for c in crits) / W_g
    W_g_eff = W_g * rbar_g / sum(AHP_WEIGHTS[c]*r_vec[col_names.index(c)] for c in col_names)
    print(f"  {g}: W_g={W_g:.3f} -> W_g^eff={W_g_eff:.3f}  rbar_g={rbar_g:.4f}")
    for c in crits:
        j = col_names.index(c); A_j = r_vec[j] / rbar_g
        print(f"    {c:12s}: r_j={r_vec[j]:.4f}  A_j={A_j:.4f}")

# ── 2. TV_B and TV_W for r_j ─────────────────────────────────────────────────
def tv_decomp(amp_fn):
    total_amp = sum(AHP_WEIGHTS[c]*amp_fn(c) for c in col_names)
    tvb = tvw = 0.0
    for g, crits in GROUPS.items():
        W_g = sum(AHP_WEIGHTS[c] for c in crits)
        rbar_g = sum(AHP_WEIGHTS[c]*amp_fn(c) for c in crits) / W_g
        A_g_eff = W_g * rbar_g / total_amp
        tvb += 0.5 * abs(A_g_eff - W_g)
        tvw += W_g * 0.5 * sum((AHP_WEIGHTS[c]/W_g)*abs(amp_fn(c)/rbar_g - 1) for c in crits)
    return tvb, tvw

tvb_rj, tvw_rj = tv_decomp(lambda c: r_vec[col_names.index(c)])
print(f"\n=== 2. TV decomposition for r_j ===")
print(f"  TV_B(r_j) = {tvb_rj:.4f}")
print(f"  TV_W(r_j) = {tvw_rj:.4f}")

# ── 3. Proportion greedy == optimal ──────────────────────────────────────────
print("\n=== 3. Proportion greedy == optimal ===")
grd_eq_opt_rvstar = 0; grd_eq_opt_rm = 0
grd_nd_rvstar = 0; opt_nd_rvstar = 0
grd_nd_rm = 0; opt_nd_rm = 0
# Store per-draw results for analysis
rv_grd_nd = np.zeros(N_DRAWS, dtype=bool)
rv_opt_nd = np.zeros(N_DRAWS, dtype=bool)
rm_grd_nd = np.zeros(N_DRAWS, dtype=bool)
rm_opt_nd = np.zeros(N_DRAWS, dtype=bool)
greedy_matches = []  # draws where RV* greedy ND but RM greedy dominated

t0 = time.time()
for d in range(N_DRAWS):
    w = w_matrix[d]
    f1v,f2v,f3v = compute_objs(w)
    F1=f1v[T0]+f1v[T1]+f1v[T2]; F2=f2v[T0]+f2v[T1]+f2v[T2]; F3=f3v[T0]+f3v[T1]+f3v[T2]

    # R-V*
    sc_rv = (X_RVstar * w).sum(1)
    grd_rv = greedy_trio(sc_rv, D)
    st_rv  = sc_rv[T0]+sc_rv[T1]+sc_rv[T2]
    best_rv = np.argmax(st_rv)
    opt_rv = np.array([T0[best_rv], T1[best_rv], T2[best_rv]])
    rv_grd_nd[d] = not is_dominated(grd_rv, F1, F2, F3)
    rv_opt_nd[d] = not is_dominated(opt_rv, F1, F2, F3)
    if tuple(sorted(grd_rv)) == tuple(sorted(opt_rv)):
        grd_eq_opt_rvstar += 1

    # R-M
    sc_rm = (X_RM * w).sum(1)
    grd_rm = greedy_trio(sc_rm, D)
    st_rm  = sc_rm[T0]+sc_rm[T1]+sc_rm[T2]
    best_rm = np.argmax(st_rm)
    opt_rm = np.array([T0[best_rm], T1[best_rm], T2[best_rm]])
    rm_grd_nd[d] = not is_dominated(grd_rm, F1, F2, F3)
    rm_opt_nd[d] = not is_dominated(opt_rm, F1, F2, F3)
    if tuple(sorted(grd_rm)) == tuple(sorted(opt_rm)):
        grd_eq_opt_rm += 1

    # Track draws where RV* greedy ND but RM greedy dominated
    if rv_grd_nd[d] and not rm_grd_nd[d]:
        greedy_matches.append(d)

    if d % 100 == 0:
        print(f"  {d/N_DRAWS*100:.0f}%  {time.time()-t0:.0f}s", flush=True)

pct_eq_rv = grd_eq_opt_rvstar/N_DRAWS*100
pct_eq_rm = grd_eq_opt_rm/N_DRAWS*100
print(f"\n  R-V* greedy ND: {rv_grd_nd.mean()*100:.1f}%  opt ND: {rv_opt_nd.mean()*100:.1f}%")
print(f"  R-M  greedy ND: {rm_grd_nd.mean()*100:.1f}%  opt ND: {rm_opt_nd.mean()*100:.1f}%")
print(f"  R-V* greedy == optimal: {pct_eq_rv:.1f}% of draws")
print(f"  R-M  greedy == optimal: {pct_eq_rm:.1f}% of draws")
print(f"  Draws where R-V* greedy ND but R-M greedy dominated: {len(greedy_matches)}")

# ── 4. Objective percentiles in discriminating draws ──────────────────────────
if len(greedy_matches) > 0:
    print(f"\n=== 4. Objective analysis for {len(greedy_matches)} discriminating draws ===")
    # Use nominal weights as proxy
    w_nom = w_ahp
    f1v,f2v,f3v = compute_objs(w_nom)
    F1_nom=f1v[T0]+f1v[T1]+f1v[T2]; F2_nom=f2v[T0]+f2v[T1]+f2v[T2]; F3_nom=f3v[T0]+f3v[T1]+f3v[T2]
    # Percentile of median greedy portfolio
    sc_rv_nom = (X_RVstar * w_nom).sum(1)
    sc_rm_nom = (X_RM * w_nom).sum(1)
    grd_rv_nom = greedy_trio(sc_rv_nom, D)
    grd_rm_nom = greedy_trio(sc_rm_nom, D)
    t_rv = tuple(sorted(grd_rv_nom))
    t_rm = tuple(sorted(grd_rm_nom))
    # F1 percentile (lower=better)
    f1_rv = sum(f1v[s] for s in grd_rv_nom); f1_rm = sum(f1v[s] for s in grd_rm_nom)
    pct_f1_rv = (F1_nom < f1_rv + EPS).mean()*100  # % of trios with worse (higher) F1
    pct_f1_rm = (F1_nom < f1_rm + EPS).mean()*100
    f3_rv = sum(f3v[s] for s in grd_rv_nom); f3_rm = sum(f3v[s] for s in grd_rm_nom)
    pct_f3_rv = (F3_nom > f3_rv - EPS).mean()*100  # % with worse (lower) F3
    pct_f3_rm = (F3_nom > f3_rm - EPS).mean()*100
    print(f"  Nominal weights greedy:")
    print(f"    R-V* sites={sorted(grd_rv_nom)}  F1={f1_rv:.4f} (better than {pct_f1_rv:.0f}% of trios)  F3={f3_rv:.4f} (better than {pct_f3_rv:.0f}%)")
    print(f"    R-M  sites={sorted(grd_rm_nom)}  F1={f1_rm:.4f} (better than {pct_f1_rm:.0f}% of trios)  F3={f3_rm:.4f} (better than {pct_f3_rm:.0f}%)")

# ── Save ──────────────────────────────────────────────────────────────────────
out = ROOT / "results" / "e1"
out.mkdir(exist_ok=True)
pd.DataFrame({
    "metric": [
        "tv_b_rj","tv_w_rj",
        "rvstar_greedy_nd_pct","rvstar_opt_nd_pct","rvstar_greedy_eq_opt_pct",
        "rm_greedy_nd_pct","rm_opt_nd_pct","rm_greedy_eq_opt_pct",
        "n_discriminating_draws"
    ],
    "value": [
        tvb_rj, tvw_rj,
        rv_grd_nd.mean()*100, rv_opt_nd.mean()*100, pct_eq_rv,
        rm_grd_nd.mean()*100, rm_opt_nd.mean()*100, pct_eq_rm,
        len(greedy_matches)
    ]
}).to_csv(out/"e1_diag_greedy_rvstar.csv", index=False)
print(f"\nSaved: {out}/e1_diag_greedy_rvstar.csv")
print(f"Total time: {time.time()-t0:.1f}s")
