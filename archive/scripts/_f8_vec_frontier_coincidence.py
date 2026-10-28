# -*- coding: utf-8 -*-
"""
_f8_vec_frontier_coincidence.py
================================
Two tasks in one script:

  Task 1 — Vec frontier (under AHP weights):
    size, non-dominance, completeness, epsilon sweep.

  Task 2 — Coincidence (vec/vec and vec/mm):
    Using the SAME saw_vec_aligned and compute_objs_vec_direct as
    compute_f8_circularity.py. Records portfolio indices per draw.
    Controls: Q2 values must match f8_per_draw.csv exactly.

Controls required before numbers become valid (§1.3 of the review):
  C1. Optimal portfolio index == index in f8_per_draw.csv: 500/500
  C2. Q2 greedy vec/vec recalculated == 100.0%
  C3. Q2 greedy vec/mm recalculated == 72.4% (±0.5%)
  C4. Q2 optimal vec/mm == 94.4% (±0.5%)
  C5. vec/mm on_frontier divergence == 112 draws

Run:
    uv run python scripts/_f8_vec_frontier_coincidence.py

Output:
    results/f8/f8_vec_frontier.csv  — frontier trios under AHP weights
    results/f8/f8_coincidence_v2.csv — per-draw portfolio indices + coincidence flags
"""
import sys, os, time, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import dirichlet as sp_dirichlet
from paretoset import paretoset

ROOT = Path(__file__).parent.parent
t0 = time.time()

# ── Load infrastructure from compute_f8_circularity.py ─────────────────────
# We re-use the same data loading and utility functions to guarantee consistency.
from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS, haversine_km, MIN_DIST_KM,
    _build_decision_matrix, F1_CRIT, F2_CRIT, F3_CRIT,
    INV as INV_SET, COST as COST_SET, _norm as _mm_norm
)

print("Loading data...", flush=True)
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL['protected']] > 0].copy()
N = len(df_via)
assert N == 389
col_names = list(AHP_WEIGHTS.keys())
w_ahp = np.array(list(AHP_WEIGHTS.values()))

print("Loading trios...", flush=True)
trios = np.load(ROOT / 'data' / 'fogo_trios.npy')
assert len(trios) == 1944653
T0, T1, T2 = trios[:, 0], trios[:, 1], trios[:, 2]
valid_mask = {(int(a), int(b)): True for a, b, _ in trios}
valid_mask.update({(int(b), int(a)): True for a, b, _ in trios})

# Distance matrix for greedy
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
valid = D_via >= MIN_DIST_KM

print(f"Data ready  t={time.time()-t0:.1f}s", flush=True)

# ── Build score matrices (same as compute_f8_circularity.py) ────────────────
X_raw, benefit_flags = _build_decision_matrix(df_via)
X_adj_mm = X_raw.copy()
for j, b in enumerate(benefit_flags):
    if not b:
        X_adj_mm[:, j] = 1.0 - X_raw[:, j]

L2_via = np.maximum(np.sqrt((X_raw**2).sum(0)), 1e-12)

f1_set = set(F1_CRIT)
f2_set = set(F2_CRIT)

# C_vec_raw (same as compute_f8_circularity.py)
C_vec_raw = np.zeros((N, len(col_names)), dtype=np.float64)
for j, k in enumerate(col_names):
    x = df_via[COL[k]].values.astype(np.float64)
    if k == "aspect":
        c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
    else:
        c = _mm_norm(x, x)
    L2_c = max(np.sqrt((c**2).sum()), 1e-12)
    C_vec_raw[:, j] = c / L2_c

# C_score_vec and sign_obj (same as compute_f8_circularity.py)
sign_obj = np.array([-1.0 if k in (f1_set | f2_set) else 1.0 for k in col_names])
C_score_vec = np.zeros((N, len(col_names)), dtype=np.float64)
for j, k in enumerate(col_names):
    if k == "aspect":
        C_score_vec[:, j] = np.where(
            (df_via[COL[k]].values.astype(float) >= 90) &
            (df_via[COL[k]].values.astype(float) <= 180), 0.0, 1.0)
    elif k in INV_SET:
        C_score_vec[:, j] = 1.0 - C_vec_raw[:, j]
    else:
        C_score_vec[:, j] = C_vec_raw[:, j]

def saw_vec_aligned(w):
    """SAW score aligned with vec objectives: -(F1+F2)+F3."""
    return (C_score_vec * (w * sign_obj)).sum(axis=1)

def saw_mm(w):
    return X_adj_mm @ w

# Vec objectives (same as compute_f8_circularity.py)
def compute_objs_vec(w):
    f1v = np.zeros(N, dtype=np.float64)
    f2v = np.zeros(N, dtype=np.float64)
    f3v = np.zeros(N, dtype=np.float64)
    for j, k in enumerate(col_names):
        wj = float(w[j])
        if k == "aspect":
            c = np.where((df_via[COL[k]].values.astype(float) >= 90) &
                         (df_via[COL[k]].values.astype(float) <= 180), 0.0, 1.0)
        elif k in INV_SET:
            c = 1.0 - C_vec_raw[:, j]
        else:
            c = C_vec_raw[:, j]
        c = c * wj
        if k in f1_set:   f1v += c
        elif k in f2_set: f2v += c
        else:             f3v += c
    return f1v, f2v, f3v

EPS_VEC = 1e-9

def is_dominated_vec(f1t, f2t, f3t, F1, F2, F3):
    """Check if a specific point is dominated."""
    weak  = (F1 <= f1t+EPS_VEC) & (F2 <= f2t+EPS_VEC) & (F3 >= f3t-EPS_VEC)
    strict= (F1 <  f1t-EPS_VEC) | (F2 <  f2t-EPS_VEC) | (F3 >  f3t+EPS_VEC)
    return bool((weak & strict).any())

def top_opt(scores):
    return trios[int(np.argmax(scores[T0] + scores[T1] + scores[T2]))]

def top_greedy(scores):
    order = np.argsort(scores)[::-1]
    sel = []
    for idx in order:
        if all(valid[idx, s] for s in sel):
            sel.append(idx)
        if len(sel) == 3:
            break
    if len(sel) < 3:
        return None
    sf = frozenset(sel)
    for t in trios:
        if frozenset(t) == sf:
            return t
    return None

print(f"Scoring matrices ready  t={time.time()-t0:.1f}s", flush=True)

# ══════════════════════════════════════════════════════════════════════════════
# TASK 1 — Vec Pareto frontier (under AHP weights)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TASK 1 — Vec Pareto frontier (AHP weights)")
print("="*60)

# Compute vec objectives under AHP weights
f1, f2, f3 = compute_objs_vec(w_ahp)
F1_trio = f1[T0] + f1[T1] + f1[T2]
F2_trio = f2[T0] + f2[T1] + f2[T2]
F3_trio = f3[T0] + f3[T1] + f3[T2]

# Find Pareto-efficient trios using paretoset
# Orientation: F1 min, F2 min, F3 max → negate F3 for paretoset (assumes all min)
objectives_mat = np.column_stack([F1_trio, F2_trio, -F3_trio])
t_front = time.time()
on_front = paretoset(objectives_mat, sense=["min", "min", "min"])
n_front = int(on_front.sum())
print(f"  Frontier size |F_vec|: {n_front}  t={time.time()-t_front:.1f}s", flush=True)

# Save frontier trios
front_idx = np.where(on_front)[0]
df_front = pd.DataFrame({
    'trio_idx': front_idx,
    's0': trios[front_idx, 0],
    's1': trios[front_idx, 1],
    's2': trios[front_idx, 2],
    'F1': F1_trio[front_idx],
    'F2': F2_trio[front_idx],
    'F3': F3_trio[front_idx],
})
out_front = ROOT / 'results' / 'f8' / 'f8_vec_frontier.csv'
df_front.to_csv(out_front, index=False)
print(f"  Saved: {out_front}")

# Non-dominance check within frontier
F1f, F2f, F3f = F1_trio[front_idx], F2_trio[front_idx], F3_trio[front_idx]
obj_front = np.column_stack([F1f, F2f, -F3f])
re_front  = paretoset(obj_front, sense=["min","min","min"])
n_dom_in  = int((~re_front).sum())
print(f"  Non-dominance within F_vec: {n_dom_in} exceptions (expected 0)")

# Completeness: for each non-frontier trio, some frontier member dominates it
print("  Completeness check (vectorised)...", flush=True)
t_comp = time.time()
EPS_SWEEP = [0, 1e-9, 1e-7, 1e-5]
for eps in EPS_SWEEP:
    escaped = 0
    for i in range(len(F1_trio)):
        if on_front[i]:
            continue
        # Check if any frontier trio dominates trio i
        dominated = (
            (F1f <= F1_trio[i] + eps) &
            (F2f <= F2_trio[i] + eps) &
            (F3f >= F3_trio[i] - eps) &
            ((F1f < F1_trio[i] - eps) | (F2f < F2_trio[i] - eps) | (F3f > F3_trio[i] + eps))
        )
        if not dominated.any():
            escaped += 1
            if escaped <= 3:
                print(f"    escaped trio {i}: F1={F1_trio[i]:.6f} F2={F2_trio[i]:.6f} F3={F3_trio[i]:.6f}")
    print(f"  Completeness eps={eps:.0e}: {escaped} escaped (expected 0)")
    if eps == 0:
        completeness_strict = escaped
print(f"  Completeness t={time.time()-t_comp:.1f}s", flush=True)

# ══════════════════════════════════════════════════════════════════════════════
# TASK 2 — Coincidence computation (CORRECT scoring)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TASK 2 — Coincidence (500 draws, correct saw_vec_aligned)")
print("="*60)

N_DRAWS = 500; KAPPA = 200; SEED = 42
W_draws = sp_dirichlet.rvs(KAPPA * w_ahp, size=N_DRAWS,
                            random_state=np.random.default_rng(SEED))

# Load reference f8_per_draw.csv
f8_ref = pd.read_csv(ROOT / 'results' / 'f8' / 'f8_per_draw.csv')
ref_vv_opt = f8_ref[(f8_ref.score_norm=='vec') & (f8_ref.assembly=='optimal')].sort_values('draw')['on_frontier'].values
ref_vv_grd = f8_ref[(f8_ref.score_norm=='vec') & (f8_ref.assembly=='greedy')].sort_values('draw')['on_frontier'].values
ref_vm_opt = f8_ref[(f8_ref.score_norm=='mm')  & (f8_ref.assembly=='optimal')].sort_values('draw')['on_frontier'].values
ref_vm_grd = f8_ref[(f8_ref.score_norm=='mm')  & (f8_ref.assembly=='greedy')].sort_values('draw')['on_frontier'].values

records = []
t_mc = time.time()
print(f"  Running {N_DRAWS} draws × 4 cells...", flush=True)

vv_opt_q2 = 0; vv_grd_q2 = 0; vm_opt_q2 = 0; vm_grd_q2 = 0

for di, w in enumerate(W_draws):
    # Vec objectives for this draw
    f1v, f2v, f3v = compute_objs_vec(w)
    F1 = f1v[T0] + f1v[T1] + f1v[T2]
    F2 = f2v[T0] + f2v[T1] + f2v[T2]
    F3 = f3v[T0] + f3v[T1] + f3v[T2]

    # Portfolios
    vv_opt = top_opt(saw_vec_aligned(w))
    vv_grd = top_greedy(saw_vec_aligned(w))
    vm_opt = top_opt(saw_mm(w))
    vm_grd = top_greedy(saw_mm(w))

    # Q2 (on frontier)
    def on_f(trio):
        if trio is None: return 0
        f1t = float(f1v[trio[0]] + f1v[trio[1]] + f1v[trio[2]])
        f2t = float(f2v[trio[0]] + f2v[trio[1]] + f2v[trio[2]])
        f3t = float(f3v[trio[0]] + f3v[trio[1]] + f3v[trio[2]])
        return 0 if is_dominated_vec(f1t, f2t, f3t, F1, F2, F3) else 1

    q2_vv_opt = on_f(vv_opt)
    q2_vv_grd = on_f(vv_grd)
    q2_vm_opt = on_f(vm_opt)
    q2_vm_grd = on_f(vm_grd)

    vv_opt_q2 += q2_vv_opt; vv_grd_q2 += q2_vv_grd
    vm_opt_q2 += q2_vm_opt; vm_grd_q2 += q2_vm_grd

    # Coincidence (frozenset for robustness)
    vv_same = (vv_opt is not None and vv_grd is not None and
               frozenset(vv_opt) == frozenset(vv_grd))
    vm_same = (vm_opt is not None and vm_grd is not None and
               frozenset(vm_opt) == frozenset(vm_grd))

    records.append({
        'draw': di,
        'vv_opt': str(sorted(frozenset(vv_opt))) if vv_opt is not None else 'None',
        'vv_grd': str(sorted(frozenset(vv_grd))) if vv_grd is not None else 'None',
        'vm_opt': str(sorted(frozenset(vm_opt))) if vm_opt is not None else 'None',
        'vm_grd': str(sorted(frozenset(vm_grd))) if vm_grd is not None else 'None',
        'q2_vv_opt': q2_vv_opt, 'q2_vv_grd': q2_vv_grd,
        'q2_vm_opt': q2_vm_opt, 'q2_vm_grd': q2_vm_grd,
        'vv_same': int(vv_same), 'vm_same': int(vm_same),
    })

    if (di + 1) % 50 == 0:
        elapsed = time.time() - t_mc
        eta = elapsed / (di + 1) * (N_DRAWS - di - 1)
        print(f"  [{di+1}/{N_DRAWS}]  "
              f"vv_q2={vv_grd_q2/(di+1)*100:.1f}%/{vv_opt_q2/(di+1)*100:.1f}%  "
              f"vm_q2={vm_grd_q2/(di+1)*100:.1f}%/{vm_opt_q2/(di+1)*100:.1f}%  "
              f"eta={eta:.0f}s", flush=True)

df_coinc = pd.DataFrame(records)

# ── Controls ─────────────────────────────────────────────────────────────────
print("\n" + "-"*40)
print("CONTROLS (§1.3):")

# C2/C3/C4: Q2 values match log
q2_vv_opt_pct = vv_opt_q2 / N_DRAWS * 100
q2_vv_grd_pct = vv_grd_q2 / N_DRAWS * 100
q2_vm_opt_pct = vm_opt_q2 / N_DRAWS * 100
q2_vm_grd_pct = vm_grd_q2 / N_DRAWS * 100

print(f"  C2 vec/vec/grd Q2 = {q2_vv_grd_pct:.1f}% (expected 100.0): "
      f"{'PASS' if abs(q2_vv_grd_pct - 100.0) < 0.1 else 'FAIL'}")
print(f"  C3 vec/mm/grd  Q2 = {q2_vm_grd_pct:.1f}% (expected 72.4): "
      f"{'PASS' if abs(q2_vm_grd_pct - 72.4) < 0.5 else 'FAIL'}")
print(f"  C4 vec/mm/opt  Q2 = {q2_vm_opt_pct:.1f}% (expected 94.4): "
      f"{'PASS' if abs(q2_vm_opt_pct - 94.4) < 0.5 else 'FAIL'}")
print(f"  vec/vec/opt Q2 = {q2_vv_opt_pct:.1f}% (expected 100.0): "
      f"{'PASS' if abs(q2_vv_opt_pct - 100.0) < 0.1 else 'FAIL'}")

# C1: Q2 values match f8_per_draw.csv
c1_vv_opt = (df_coinc['q2_vv_opt'].values == ref_vv_opt).all()
c1_vv_grd = (df_coinc['q2_vv_grd'].values == ref_vv_grd).all()
c1_vm_opt = (df_coinc['q2_vm_opt'].values == ref_vm_opt).all()
c1_vm_grd = (df_coinc['q2_vm_grd'].values == ref_vm_grd).all()
c1_pass = c1_vv_opt and c1_vv_grd and c1_vm_opt and c1_vm_grd
print(f"  C1 on_frontier matches f8_per_draw.csv: "
      f"vv_opt={c1_vv_opt} vv_grd={c1_vv_grd} vm_opt={c1_vm_opt} vm_grd={c1_vm_grd} "
      f"-> {'PASS' if c1_pass else 'FAIL'}")
if not c1_pass:
    for lbl, a, b in [('vv_opt', df_coinc['q2_vv_opt'].values, ref_vv_opt),
                      ('vv_grd', df_coinc['q2_vv_grd'].values, ref_vv_grd),
                      ('vm_opt', df_coinc['q2_vm_opt'].values, ref_vm_opt),
                      ('vm_grd', df_coinc['q2_vm_grd'].values, ref_vm_grd)]:
        diffs = np.where(a != b)[0]
        if len(diffs):
            print(f"    {lbl} differs at draws: {diffs[:10].tolist()}")

# C5: vec/mm divergence == 112
vv_div = int((df_coinc['q2_vv_opt'] != df_coinc['q2_vv_grd']).sum())
vm_div = int((df_coinc['q2_vm_opt'] != df_coinc['q2_vm_grd']).sum())
print(f"  C5 vec/mm on_frontier divergence = {vm_div} (expected 112): "
      f"{'PASS' if vm_div == 112 else 'FAIL'}")
print(f"     vec/vec divergence = {vv_div} (expected 0): "
      f"{'PASS' if vv_div == 0 else 'FAIL'}")

# ── Final counts ─────────────────────────────────────────────────────────────
vv_coinc = int(df_coinc['vv_same'].sum())
vm_coinc = int(df_coinc['vm_same'].sum())
print(f"\nCOINCIDENCE (same portfolio):")
print(f"  vec/vec greedy == optimal: {vv_coinc}/{N_DRAWS}")
print(f"  vec/mm  greedy == optimal: {vm_coinc}/{N_DRAWS}")

# ── Save ──────────────────────────────────────────────────────────────────────
out_coinc = ROOT / 'results' / 'f8' / 'f8_coincidence_v2.csv'
df_coinc.to_csv(out_coinc, index=False)
sha_coinc = hashlib.sha256(out_coinc.read_bytes()).hexdigest()
sha_front = hashlib.sha256(out_front.read_bytes()).hexdigest()

all_controls = (c1_pass and
                abs(q2_vv_grd_pct-100.0) < 0.1 and
                abs(q2_vm_grd_pct-72.4) < 0.5 and
                abs(q2_vm_opt_pct-94.4) < 0.5 and
                vm_div == 112 and vv_div == 0)

print(f"\n{'='*60}")
print("RESULTS SUMMARY")
print(f"{'='*60}")
print(f"Task 1 — Vec frontier:")
print(f"  |F_vec| (AHP weights) = {n_front}")
print(f"  Non-dominance within F_vec: {n_dom_in} exceptions")
print(f"  Completeness (strict): {completeness_strict} escaped")
print(f"  f8_vec_frontier.csv: {sha_front}")
print()
print(f"Task 2 — Coincidence:")
print(f"  Controls: {'ALL PASS' if all_controls else 'SOME FAIL — numbers NOT valid'}")
print(f"  vec/vec greedy == optimal: {vv_coinc}/{N_DRAWS}")
print(f"  vec/mm  greedy == optimal: {vm_coinc}/{N_DRAWS}")
print(f"  f8_coincidence_v2.csv: {sha_coinc}")
print()
print(f"Total elapsed: {(time.time()-t0)/60:.1f} min")
print("DONE")
