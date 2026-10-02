"""scripts/run_fourthcell_consistent.py
tab:fourthcell with consistent aspect encoding (binary in all four cells)
+ per-draw indicators for paired bootstrap.

Four cells, all with aspect binary (X_adj_dm base):
  RV_star_Aprime: score = X_adj_dm * r_j   vs  evaluator A' (= R-V* already run)
  RM_Aprime:      score = X_adj_dm          vs  evaluator A' (= R-M already run)
  RV_star_A:      score = X_adj_dm * r_j   vs  evaluator A  (ref=473, new)
  RM_A:           score = X_adj_dm          vs  evaluator A  (ref=473, new)

R-asp and R-V (continuous aspect) also recorded for bootstrap:
  R-asp:  score = X_adj_dm with continuous aspect, 389-base
  R-V:    score = Xadj473 (aspect continuous, 473-base)  — original published cell

Output: results/draws_fourthcell.npz
  draws[cell_name] = shape (N_DRAWS,) boolean array (1=non-dominated, 0=dominated)
  for each of: greedy and optimal assembly

Also outputs: results/fourthcell_consistent.csv (summary statistics)

Post hoc, declared in DEV-E4-007 (commit b0e5c66). Run 2026-10-01.
"""
import hashlib, os, sys, time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT    = Path(__file__).parent.parent
RESULTS = ROOT / "results"
sys.path.insert(0, str(ROOT / "scripts"))

if "MCDM_DATA_DIR" not in os.environ:
    athena = "/home/julioazancort/scratch/mcdm"
    os.environ["MCDM_DATA_DIR"] = athena if os.path.exists(athena) else str(ROOT/"data")

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS,
    haversine_km, greedy_trio, MIN_DIST_KM,
    _build_decision_matrix, INV, COST,
    F1_CRIT, F2_CRIT, F3_CRIT, _norm,
)
from pareto_utils import build_pareto_utils

EPS       = 1e-9
N_DRAWS   = 500
SEED      = 42
KAPPA     = 200
E1_SHA256 = "bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487"

# ── Data ───────────────────────────────────────────────────────────────────────
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]] > 0].copy()
assert len(df_imp) == 473 and len(df_via) == 389

w_ahp     = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
M = len(col_names); N = len(df_via)
J_ASPECT = col_names.index("aspect")

# Verify weight matrix
wmat_path = RESULTS / "e1_weights_k200.npy"
sha = hashlib.sha256(wmat_path.read_bytes()).hexdigest()
assert sha == E1_SHA256, f"SHA mismatch: {sha}"
w_matrix = np.load(wmat_path)
print(f"Weight matrix OK {w_matrix.shape}")

# ── Matrices ───────────────────────────────────────────────────────────────────
X_raw, benefit = _build_decision_matrix(df_via)
X_adj_dm = X_raw.copy()
for jj, b in enumerate(benefit):
    if not b: X_adj_dm[:, jj] = 1.0 - X_raw[:, jj]

# r_j = range_389 / range_473
r_vec = np.array([
    (df_via[COL[c]].max() - df_via[COL[c]].min()) /
    max(df_imp[COL[c]].max() - df_imp[COL[c]].min(), 1e-12)
    for c in col_names
])

# Xadj473: build_score_473 style (aspect continuous)
Xb473 = np.zeros((N, M))
for jj, c in enumerate(col_names):
    x_via = df_via[COL[c]].values.astype(float)
    x_all = df_imp[COL[c]].values.astype(float)
    mn, mx = x_all.min(), x_all.max(); rng = mx - mn or 1.0
    Xb473[:, jj] = (x_via - mn) / rng
Xadj473 = Xb473.copy()
for jj, b in enumerate(benefit):
    if not b: Xadj473[:, jj] = 1.0 - Xb473[:, jj]

# R-asp: X_adj_dm with aspect replaced by continuous (389-base)
x_asp_via = df_via[COL["aspect"]].values.astype(float)
mn389_asp = x_asp_via.min(); rng389_asp = x_asp_via.max() - mn389_asp or 1.0
X_rasp = X_adj_dm.copy()
X_rasp[:, J_ASPECT] = (x_asp_via - mn389_asp) / rng389_asp

# ── Trios ─────────────────────────────────────────────────────────────────────
D = haversine_km(df_via["latitude (degrees)"].values, df_via["longitude (degrees)"].values)
valid = D >= MIN_DIST_KM
trios_list = [(i,j,k) for i in range(N) for j in range(i+1,N) if valid[i,j]
              for k in range(j+1,N) if valid[i,k] and valid[j,k]]
trios = np.array(trios_list, dtype=np.int32)
assert len(trios) == 1_944_653
T0, T1, T2 = trios[:,0], trios[:,1], trios[:,2]
print(f"Trios: {len(trios):,}")

# ── Evaluator A' (ref=389) ────────────────────────────────────────────────────
compute_Aprime, is_dom_Aprime, _ = build_pareto_utils(df_via, col_names, trios, eps=EPS)

# ── Evaluator A (ref=473) — manual, same binary aspect as pareto_utils ────────
def build_compute_A_ref473():
    """Objectives for space A: same binary aspect, ref=473 (df_imp)."""
    def compute(w):
        f1v = np.zeros(N); f2v = np.zeros(N); f3v = np.zeros(N)
        for j, k in enumerate(col_names):
            x   = df_via[COL[k]].values.astype(float)
            ref = df_imp[COL[k]].values.astype(float)
            if k == "aspect":
                c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
            elif k in INV:   c = 1.0 - _norm(x, ref)
            elif k in COST:  c = _norm(x, ref)
            else:            c = _norm(x, ref)
            c = c * w[j]
            if k in F1_CRIT:   f1v += c
            elif k in F2_CRIT: f2v += c
            else:              f3v += c
        return f1v, f2v, f3v

    # Build sorted-trio lookup for self-exclusion (same as pareto_utils)
    from pareto_utils import build_pareto_utils as _bpu
    # We need is_dominated for space A — reuse pareto_utils with a mock
    # but with ref=473. pareto_utils hardcodes ref=df_via, so we build
    # is_dom manually using the same dominance logic.
    trio_lookup = {(int(trios[i,0]),int(trios[i,1]),int(trios[i,2])): i
                   for i in range(len(trios))}

    def is_dominated_A(trio, f1v, f2v, f3v, F1, F2, F3):
        i, j, k = int(trio[0]), int(trio[1]), int(trio[2])
        key = tuple(sorted((i,j,k)))
        idx = trio_lookup.get(key, -1)
        ft1 = float(f1v[i]+f1v[j]+f1v[k])
        ft2 = float(f2v[i]+f2v[j]+f2v[k])
        ft3 = float(f3v[i]+f3v[j]+f3v[k])
        if idx < 0:
            weak = (F1<=ft1+EPS)&(F2<=ft2+EPS)&(F3>=ft3-EPS)
            strc = (F1<ft1-EPS)|(F2<ft2-EPS)|(F3>ft3+EPS)
            return bool((weak&strc).any())
        mask = np.ones(len(F1), bool); mask[idx] = False
        F1m, F2m, F3m = F1[mask], F2[mask], F3[mask]
        weak = (F1m<=ft1+EPS)&(F2m<=ft2+EPS)&(F3m>=ft3-EPS)
        strc = (F1m<ft1-EPS)|(F2m<ft2-EPS)|(F3m>ft3+EPS)
        return bool((weak&strc).any())

    return compute, is_dominated_A

compute_A, is_dom_A = build_compute_A_ref473()

# ── Score matrices (cells) ────────────────────────────────────────────────────
cells = {
    "RV_star_Aprime": (X_adj_dm * r_vec,  compute_Aprime, is_dom_Aprime),
    "RM_Aprime":      (X_adj_dm,           compute_Aprime, is_dom_Aprime),
    "RV_star_A":      (X_adj_dm * r_vec,  compute_A,      is_dom_A),
    "RM_A":           (X_adj_dm,           compute_A,      is_dom_A),
    "R_asp_Aprime":   (X_rasp,             compute_Aprime, is_dom_Aprime),
    "R_V_Aprime":     (Xadj473,            compute_Aprime, is_dom_Aprime),
}

# ── Monte Carlo ───────────────────────────────────────────────────────────────
draws_grd = {name: np.zeros(N_DRAWS, dtype=np.int8) for name in cells}
draws_opt = {name: np.zeros(N_DRAWS, dtype=np.int8) for name in cells}
records = []

print("\nMonte Carlo:")
for name, (X_cell, compute_objs, is_dominated) in cells.items():
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
        st = sc[T0]+sc[T1]+sc[T2]
        best = np.argmax(st)
        idx_o = np.array([T0[best], T1[best], T2[best]])
        draws_opt[name][d] = int(not is_dominated(idx_o, F1, F2, F3))

    Q2g = draws_grd[name].mean()*100; Q2o = draws_opt[name].mean()*100
    SEg = (Q2g*(100-Q2g)/N_DRAWS)**.5; SEo = (Q2o*(100-Q2o)/N_DRAWS)**.5
    print(f"  {name:20s}: grd={Q2g:.1f}% opt={Q2o:.1f}%  ({time.time()-t0:.1f}s)")
    records.append({"cell": name, "kappa": KAPPA, "n_draws": N_DRAWS,
                    "Q2_greedy": round(Q2g,2), "SE_greedy": round(SEg,3),
                    "Q2_optimal": round(Q2o,2), "SE_optimal": round(SEo,3)})

# ── Bootstrap paired tests ────────────────────────────────────────────────────
print("\nPaired bootstrap (B=4000):")
B = 4000
rng = np.random.default_rng(SEED + 1)
pairs = [
    ("R_asp_Aprime",  "R_V_Aprime",    "R-asp vs R-V (4 pp residual: significant?)"),
    ("RV_star_Aprime","RM_Aprime",      "R-V* vs R-M greedy: ref-set effect (12 pp greedy)"),
    ("RV_star_Aprime","R_asp_Aprime",   "R-V* vs R-asp optimal (76 pp coding)"),
]
bootstrap_records = []
for a, b_name, label in pairs:
    diff_obs_opt  = draws_opt[a].mean()  - draws_opt[b_name].mean()
    diff_obs_grd  = draws_grd[a].mean()  - draws_grd[b_name].mean()
    boots_opt = []
    boots_grd = []
    for _ in range(B):
        idx = rng.integers(0, N_DRAWS, size=N_DRAWS)
        boots_opt.append(draws_opt[a][idx].mean() - draws_opt[b_name][idx].mean())
        boots_grd.append(draws_grd[a][idx].mean() - draws_grd[b_name][idx].mean())
    lo_opt, hi_opt = np.percentile(boots_opt, [2.5, 97.5])
    lo_grd, hi_grd = np.percentile(boots_grd, [2.5, 97.5])
    print(f"  {label}")
    print(f"    opt: diff={diff_obs_opt*100:+.1f} pp  95%CI=[{lo_opt*100:+.1f}, {hi_opt*100:+.1f}]")
    print(f"    grd: diff={diff_obs_grd*100:+.1f} pp  95%CI=[{lo_grd*100:+.1f}, {hi_grd*100:+.1f}]")
    bootstrap_records.append({"pair": label,
        "diff_opt_pp": round(diff_obs_opt*100,2), "ci_lo_opt": round(lo_opt*100,2), "ci_hi_opt": round(hi_opt*100,2),
        "diff_grd_pp": round(diff_obs_grd*100,2), "ci_lo_grd": round(lo_grd*100,2), "ci_hi_grd": round(hi_grd*100,2),
    })

# ── Save ──────────────────────────────────────────────────────────────────────
np.savez(RESULTS/"draws_fourthcell.npz", **{f"grd_{k}": v for k,v in draws_grd.items()},
         **{f"opt_{k}": v for k,v in draws_opt.items()})
pd.DataFrame(records).to_csv(RESULTS/"fourthcell_consistent.csv", index=False)
pd.DataFrame(bootstrap_records).to_csv(RESULTS/"bootstrap_paired.csv", index=False)
print(f"\nSaved: draws_fourthcell.npz, fourthcell_consistent.csv, bootstrap_paired.csv")
print(f"Commit: {os.popen('git rev-parse HEAD').read().strip()}")
