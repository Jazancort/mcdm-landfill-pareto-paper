"""scripts/run_fourthcell_consistent.py  (v2 — fixed space A evaluator)
tab:fourthcell with consistent aspect encoding (binary in all four cells)
+ per-draw indicators for paired bootstrap.

Four cells, all with aspect binary (X_adj_dm base):
  RV_star_Aprime: score = X_adj_dm * r_j   vs evaluator A' (ref=389)
  RM_Aprime:      score = X_adj_dm          vs evaluator A' (ref=389)
  RV_star_A:      score = X_adj_dm * r_j   vs evaluator A  (ref=473)
  RM_A:           score = X_adj_dm          vs evaluator A  (ref=473)

Also R-asp and R-V for bootstrap contrasts:
  R_asp_Aprime:   score = X_adj_dm, aspect continuous (389-base) vs A'
  R_V_Aprime:     score = Xadj473 (aspect continuous, 473-base)  vs A'

Output: results/draws_fourthcell.npz, fourthcell_consistent.csv, bootstrap_paired.csv
Post hoc, declared in DEV-E4-007.
"""
import hashlib, os, sys, time
from pathlib import Path
import numpy as np, pandas as pd

ROOT    = Path(__file__).parent.parent
RESULTS = ROOT / "results"
sys.path.insert(0, str(ROOT / "scripts"))

if "MCDM_DATA_DIR" not in os.environ:
    athena = "/home/julioazancort/scratch/mcdm"
    os.environ["MCDM_DATA_DIR"] = athena if os.path.exists(athena) else str(ROOT/"data")

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS,
    haversine_km, greedy_trio, MIN_DIST_KM,
    _build_decision_matrix, INV, COST, F1_CRIT, F2_CRIT, F3_CRIT, _norm,
)
from pareto_utils import build_pareto_utils

EPS       = 1e-9
N_DRAWS   = 500
SEED      = 42
KAPPA     = 200
E1_SHA256 = "bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487"

# ── Data ──────────────────────────────────────────────────────────────────────
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]] > 0].copy()
assert len(df_imp) == 473 and len(df_via) == 389

w_ahp     = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
M = len(col_names); N = len(df_via)
J_ASPECT  = col_names.index("aspect")

wmat_path = RESULTS / "e1_weights_k200.npy"
assert hashlib.sha256(wmat_path.read_bytes()).hexdigest() == E1_SHA256, "SHA mismatch"
w_matrix = np.load(wmat_path)
print(f"Weight matrix OK {w_matrix.shape}")

# ── Matrices ──────────────────────────────────────────────────────────────────
X_raw, benefit = _build_decision_matrix(df_via)
X_adj_dm = X_raw.copy()
for jj, b in enumerate(benefit):
    if not b: X_adj_dm[:, jj] = 1.0 - X_raw[:, jj]

r_vec = np.array([
    (df_via[COL[c]].values.astype(float).max() - df_via[COL[c]].values.astype(float).min()) /
    max(df_imp[COL[c]].values.astype(float).max() - df_imp[COL[c]].values.astype(float).min(), 1e-12)
    for c in col_names
])

# Xadj473: continuous aspect (build_score_473 style)
Xb473 = np.zeros((N, M))
for jj, c in enumerate(col_names):
    x_v = df_via[COL[c]].values.astype(float)
    x_a = df_imp[COL[c]].values.astype(float)
    mn, mx = x_a.min(), x_a.max(); rng = mx - mn or 1.0
    Xb473[:, jj] = (x_v - mn) / rng
Xadj473 = Xb473.copy()
for jj, b in enumerate(benefit):
    if not b: Xadj473[:, jj] = 1.0 - Xb473[:, jj]

# R-asp: X_adj_dm with aspect replaced by continuous (389-base)
x_asp = df_via[COL["aspect"]].values.astype(float)
mn_asp = x_asp.min(); rng_asp = x_asp.max() - mn_asp or 1.0
X_rasp = X_adj_dm.copy()
X_rasp[:, J_ASPECT] = (x_asp - mn_asp) / rng_asp

# ── Trios ─────────────────────────────────────────────────────────────────────
D = haversine_km(df_via["latitude (degrees)"].values, df_via["longitude (degrees)"].values)
valid = D >= MIN_DIST_KM
trios_list = [(i,j,k) for i in range(N) for j in range(i+1,N) if valid[i,j]
              for k in range(j+1,N) if valid[i,k] and valid[j,k]]
trios = np.array(trios_list, dtype=np.int32)
assert len(trios) == 1_944_653
T0, T1, T2 = trios[:,0], trios[:,1], trios[:,2]
print(f"Trios: {len(trios):,}")

# ── Evaluator A' (ref=389) via pareto_utils ────────────────────────────────────
compute_Aprime, is_dom_Aprime, _ = build_pareto_utils(df_via, col_names, trios, eps=EPS)

# ── Evaluator A (ref=473): build a pareto_utils-compatible evaluator ──────────
# Strategy: patch pareto_utils by building our own compute_objs_f64 with ref=df_imp
# and a custom is_dominated that uses the same sorted-idx + self-exclusion pattern.
# We do this by directly implementing the same logic as pareto_utils but with
# ref = df_imp for all criteria except aspect (which stays binary).

def build_compute_A():
    """Build compute_objs for space A (ref=473). Binary aspect, same as pareto_utils."""
    inv_set  = set(INV)
    cost_set = set(COST)
    f1_set   = set(F1_CRIT); f2_set = set(F2_CRIT)

    def compute_A(w):
        f1v = np.zeros(N, dtype=np.float64)
        f2v = np.zeros(N, dtype=np.float64)
        f3v = np.zeros(N, dtype=np.float64)
        for j, k in enumerate(col_names):
            x   = df_via[COL[k]].values.astype(np.float64)
            ref = df_imp[COL[k]].values.astype(np.float64)   # ref=473
            if k == "aspect":
                c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
            elif k in inv_set:  c = 1.0 - _norm(x, ref)
            elif k in cost_set: c = _norm(x, ref)
            else:               c = _norm(x, ref)
            c = c * float(w[j])
            if k in f1_set:   f1v += c
            elif k in f2_set: f2v += c
            else:             f3v += c
        return f1v, f2v, f3v

    # is_dominated for space A: same trio-level dominance check
    # F1, F2, F3 are aggregated trio arrays (shape = n_trios) computed externally.
    # trio arg is the selected trio (3-element array of site indices).
    # Build trio-index lookup once.
    trio_lookup = {}
    for idx in range(len(trios)):
        key = (int(trios[idx,0]), int(trios[idx,1]), int(trios[idx,2]))
        trio_lookup[key] = idx

    def is_dom_A(trio_arr, F1, F2, F3):
        i, j, k = int(trio_arr[0]), int(trio_arr[1]), int(trio_arr[2])
        key = tuple(sorted((i,j,k)))
        t_idx = trio_lookup.get(key, -1)
        if t_idx < 0:  # fallback (shouldn't happen)
            ft1=float(F1.max()); ft2=float(F2.max()); ft3=float(F3.min())
        else:
            ft1=float(F1[t_idx]); ft2=float(F2[t_idx]); ft3=float(F3[t_idx])
        mask = np.ones(len(F1), bool)
        if t_idx >= 0: mask[t_idx] = False
        F1m, F2m, F3m = F1[mask], F2[mask], F3[mask]
        weak = (F1m<=ft1+EPS)&(F2m<=ft2+EPS)&(F3m>=ft3-EPS)
        strc = (F1m<ft1-EPS)|(F2m<ft2-EPS)|(F3m>ft3+EPS)
        return bool((weak&strc).any())

    return compute_A, is_dom_A

compute_A, is_dom_A = build_compute_A()

# ── Score cells ───────────────────────────────────────────────────────────────
cells = [
    ("RV_star_Aprime", X_adj_dm * r_vec, compute_Aprime, is_dom_Aprime),
    ("RM_Aprime",      X_adj_dm,          compute_Aprime, is_dom_Aprime),
    ("RV_star_A",      X_adj_dm * r_vec, compute_A,      is_dom_A),
    ("RM_A",           X_adj_dm,          compute_A,      is_dom_A),
    ("R_asp_Aprime",   X_rasp,            compute_Aprime, is_dom_Aprime),
    ("R_V_Aprime",     Xadj473,           compute_Aprime, is_dom_Aprime),
]

# ── Monte Carlo ───────────────────────────────────────────────────────────────
draws_grd = {n: np.zeros(N_DRAWS, dtype=np.int8) for n,*_ in cells}
draws_opt = {n: np.zeros(N_DRAWS, dtype=np.int8) for n,*_ in cells}
records = []

print("\nMonte Carlo:")
for name, X_cell, compute_objs, is_dominated in cells:
    t0 = time.time()
    for d in range(N_DRAWS):
        w = w_matrix[d]
        sc = (X_cell * w).sum(1)
        f1v, f2v, f3v = compute_objs(w)
        F1 = f1v[T0]+f1v[T1]+f1v[T2]
        F2 = f2v[T0]+f2v[T1]+f2v[T2]
        F3 = f3v[T0]+f3v[T1]+f3v[T2]
        # greedy
        idx_g = greedy_trio(sc, D)
        draws_grd[name][d] = int(not is_dominated(idx_g, F1, F2, F3))
        # optimal
        best = np.argmax(sc[T0]+sc[T1]+sc[T2])
        idx_o = np.array([T0[best], T1[best], T2[best]])
        draws_opt[name][d] = int(not is_dominated(idx_o, F1, F2, F3))

    Q2g = draws_grd[name].mean()*100; Q2o = draws_opt[name].mean()*100
    SEg = (Q2g*(100-Q2g)/N_DRAWS)**.5; SEo = (Q2o*(100-Q2o)/N_DRAWS)**.5
    print(f"  {name:20s}: grd={Q2g:.1f}% opt={Q2o:.1f}%  ({time.time()-t0:.1f}s)")
    records.append({"cell":name,"kappa":KAPPA,"n_draws":N_DRAWS,
                    "Q2_greedy":round(Q2g,2),"SE_greedy":round(SEg,3),
                    "Q2_optimal":round(Q2o,2),"SE_optimal":round(SEo,3)})

# ── Bootstrap paired tests ────────────────────────────────────────────────────
print("\nPaired bootstrap (B=4000):")
B = 4000
rng = np.random.default_rng(SEED + 1)
pairs = [
    ("R_asp_Aprime", "R_V_Aprime",     "R-asp vs R-V  (4pp residual ref-set: sig?)"),
    ("RV_star_Aprime","RM_Aprime",      "R-V* vs R-M   (ref-set effect consistent)"),
    ("RV_star_Aprime","R_asp_Aprime",  "R-V* vs R-asp (76pp coding effect)"),
    ("RV_star_A",     "RM_A",           "R-V*A vs R-MA (ref-set, evaluator A)"),
]
bootstrap_records = []
for a, b_name, label in pairs:
    diff_opt = draws_opt[a].mean() - draws_opt[b_name].mean()
    diff_grd = draws_grd[a].mean() - draws_grd[b_name].mean()
    boots_o = []; boots_g = []
    for _ in range(B):
        idx = rng.integers(0, N_DRAWS, N_DRAWS)
        boots_o.append(draws_opt[a][idx].mean() - draws_opt[b_name][idx].mean())
        boots_g.append(draws_grd[a][idx].mean() - draws_grd[b_name][idx].mean())
    lo_o, hi_o = np.percentile(boots_o, [2.5, 97.5])
    lo_g, hi_g = np.percentile(boots_g, [2.5, 97.5])
    sig_o = "SIG" if (lo_o > 0 or hi_o < 0) else "n.s."
    sig_g = "SIG" if (lo_g > 0 or hi_g < 0) else "n.s."
    print(f"  {label}")
    print(f"    opt: {diff_opt*100:+.1f}pp  [{lo_o*100:+.1f},{hi_o*100:+.1f}]  {sig_o}")
    print(f"    grd: {diff_grd*100:+.1f}pp  [{lo_g*100:+.1f},{hi_g*100:+.1f}]  {sig_g}")
    bootstrap_records.append({"pair":label,
        "diff_opt_pp":round(diff_opt*100,2),"ci_lo_opt":round(lo_o*100,2),"ci_hi_opt":round(hi_o*100,2),"sig_opt":sig_o,
        "diff_grd_pp":round(diff_grd*100,2),"ci_lo_grd":round(lo_g*100,2),"ci_hi_grd":round(hi_g*100,2),"sig_grd":sig_g,
    })

# ── Save ──────────────────────────────────────────────────────────────────────
np.savez(RESULTS/"draws_fourthcell.npz",
         **{f"grd_{k}": v for k,v in draws_grd.items()},
         **{f"opt_{k}": v for k,v in draws_opt.items()})
pd.DataFrame(records).to_csv(RESULTS/"fourthcell_consistent.csv", index=False)
pd.DataFrame(bootstrap_records).to_csv(RESULTS/"bootstrap_paired.csv", index=False)
print(f"\nSaved: draws_fourthcell.npz, fourthcell_consistent.csv, bootstrap_paired.csv")
print(f"Commit: {os.popen('git rev-parse HEAD').read().strip()}")
