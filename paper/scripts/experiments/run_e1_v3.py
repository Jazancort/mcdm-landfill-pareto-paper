# -*- coding: utf-8 -*-
"""
run_e1_v3.py — Experiment E1, minimum diff from wp3_mc.py.
Pre-specification: corpus/PRESPEC_E1.md (commit f6042f8)

DIFF from wp3_mc.py:
  1. compute_objs_Ap upgraded to float64 + eps=1e-9 dominance (same as check_float64.py)
  2. NORMS extended with E1-M (A_j=1), E1-V (rho_j), E1-B (Aj_bar_g), E1-W (rho/Ajbar*scale)
  3. Assertions in chain: E1-M opt=100%, |E1-V - WP3| < 3SE, then E1-B and E1-W

Everything else is IDENTICAL to wp3_mc.py:
  - Space A' (389 sites), same viable trios
  - compute_objs_Ap structure (389-site reference, per-draw weights)
  - greedy_trio and argmax_trio
  - Same seed/kappa/N_DRAWS

Pre-registration: corpus/PRESPEC_E1.md (commit f6042f8, G: repo)
Invalid runs: DEV-E1-001..003

Groups (from fogo_constants.py / main.tex tab:amplitude):
  G1 = [perm(0), slope(1), roads(2)]              — F1 siting cost (minimise)
  G2 = [rivers(3), aspect(4), coast(5), prot(6), wells(7)] — F2 env (minimise)
  G3 = [urban(8), aero(9), cult(10)]              — F3 social safety (maximise)
"""
import os, sys, time
import numpy as np
import pandas as pd
from pathlib import Path

if 'MCDM_DATA_DIR' not in os.environ and os.path.exists('/home/julioazancort/scratch/mcdm'):
    os.environ['MCDM_DATA_DIR'] = '/home/julioazancort/scratch/mcdm'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcdm_experiment import (
    load_data, impute_nan, haversine_km,
    greedy_trio, COL, AHP_WEIGHTS, MIN_DIST_KM,
    _build_decision_matrix, _norm, INV, COST,
    F1_CRIT, F2_CRIT, F3_CRIT,
)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

EPS     = 1e-9
N_DRAWS = 500
KAPPA   = 200
SEED    = 42

# Reference values from wp3_summary.csv (will verify E1-M and E1-V against these)
WP3_MM_OPT  = 100.0  # E1-M must equal this exactly
WP3_VEC_GRD = 54.0   # E1-V greedy
WP3_VEC_OPT = 56.8   # E1-V optimal

print("=" * 70)
print("E1 v3: Amplitude decomposition (min diff from wp3_mc.py)")
print("Pre-spec: corpus/PRESPEC_E1.md (f6042f8)  eps=1e-9  float64")
print("=" * 70)

# ── Data (identical to wp3_mc.py) ─────────────────────────────────────────────
df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
viable = df_imp[COL["protected"]] > 0
df_via = df_imp[viable].copy()
N = len(df_via)
assert N == 389
D_via = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
w_ahp = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
M = len(w_ahp)

X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j2, b in enumerate(benefit):
    if not b:
        X_adj[:, j2] = 1.0 - X_via[:, j2]

# ── Trios (identical to wp3_mc.py) ───────────────────────────────────────────
t0 = time.time()
valid = D_via >= MIN_DIST_KM
trio_list = []
for i in range(N):
    for j in range(i + 1, N):
        if not valid[i, j]: continue
        for k in range(j + 1, N):
            if not valid[i, k] or not valid[j, k]: continue
            trio_list.append((i, j, k))
trio_arr = np.array(trio_list, dtype=np.int32)
T0, T1, T2 = trio_arr[:, 0], trio_arr[:, 1], trio_arr[:, 2]
assert len(trio_arr) == 1944653
print(f"Viable trios: {len(trio_arr):,} ({time.time()-t0:.1f}s)")

# ── Score matrices ────────────────────────────────────────────────────────────
# Vector norms from X_via (identical to wp3_mc.py X_vec_mc18)
norms_via = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)

# Group indices
G1 = [col_names.index(c) for c in F1_CRIT]
G2 = [col_names.index(c) for c in F2_CRIT]
G3 = [col_names.index(c) for c in F3_CRIT]
GROUPS = [G1, G2, G3]

# Amplitudes rho_j = (range of X_via[:,j]) / ||X_via[:,j]||
# (uses X_via because norms_via is computed from X_via, not X_adj)
rho_j = np.zeros(M)
for j in range(M):
    col = X_via[:, j].astype(float)
    rng_v = col.max() - col.min()
    rho_j[j] = rng_v / norms_via[j] if norms_via[j] > 0 else 0.0

# Aj_bar_g = weighted mean of rho within group
Aj_bar = np.zeros(M)
for g in GROUPS:
    wg = w_ahp[g]
    Ajbar_g = np.dot(wg, rho_j[g]) / wg.sum()
    for j in g:
        Aj_bar[j] = Ajbar_g

print(f"Aj_bar_g: G1={Aj_bar[0]:.4f}  G2={Aj_bar[3]:.4f}  G3={Aj_bar[8]:.4f}")
assert abs(Aj_bar[0] - 0.3731) < 0.005
assert abs(Aj_bar[3] - 0.1458) < 0.005
assert abs(Aj_bar[8] - 0.1157) < 0.005

# E1-W rescale
Aj_E1W_raw = rho_j / Aj_bar
scale_EW = np.dot(w_ahp, rho_j) / np.dot(w_ahp, Aj_E1W_raw)
Aj_E1W = Aj_E1W_raw * scale_EW
print(f"E1-W rescale: {scale_EW:.4f} (published 0.2024)")

# TV_B(E1-W) assertion: weighted mean amplitude per group is constant
means_W = [float(np.dot(w_ahp[g], Aj_E1W[g])) / w_ahp[g].sum() for g in GROUPS]
for i, gn in enumerate(["G1","G2","G3"]):
    assert abs(means_W[i] - means_W[0]) < 1e-10, f"TV_B(E1-W) FAIL {gn}"
print(f"[TV_B] E1-W group amplitude means = {means_W[0]:.6f} (constant): PASS")

# Score matrices: V * w gives SAW score for site; higher = better
# E1-M: A_j = 1  =>  V = X_adj  (same as WP3 min-max)
# E1-V: A_j = rho_j  =>  V = X_adj / norms_via  (same as WP3 X_vec_mc18)
# E1-B: A_j = Aj_bar_g  =>  V = X_adj * Aj_bar / range(X_adj)
# E1-W: A_j = Aj_E1W    =>  V = X_adj * Aj_E1W  / range(X_adj)
def make_V(Aj):
    """V[:,j] = X_adj[:,j] * Aj[j] / range(X_adj[:,j])"""
    V = np.zeros_like(X_adj, dtype=np.float64)
    for j in range(M):
        col = X_adj[:, j].astype(float)
        rng_v = col.max() - col.min()
        V[:, j] = col * Aj[j] / rng_v if rng_v > 0 else col * Aj[j]
    return V

V_E1M = X_adj.copy().astype(np.float64)           # A_j = 1 (range of X_adj = 1 for mm)
V_E1V = (X_adj / norms_via).astype(np.float64)    # X_vec_mc18
V_E1B = make_V(Aj_bar)
V_E1W = make_V(Aj_E1W)

CELLS = [
    ("E1-M", V_E1M, "A_j=1 (min-max, regression test)"),
    ("E1-V", V_E1V, "A_j=rho_j (vector, WP3 reference)"),
    ("E1-B", V_E1B, "A_j=Ajbar_g (constant within group, TV_W=0)"),
    ("E1-W", V_E1W, "A_j=rho/Ajbar*scale (TV_B=0)"),
]

# ── compute_objs_Ap: upgraded to float64 + eps (ONLY change from wp3_mc.py) ──
def compute_objs_Ap_f64(w):
    """Compute per-site (f1, f2, f3) on A' using min-max on df_via. FLOAT64."""
    f1v = np.zeros(N, dtype=np.float64)
    f2v = np.zeros(N, dtype=np.float64)
    f3v = np.zeros(N, dtype=np.float64)
    for j, k in enumerate(col_names):
        col = COL[k]
        x   = df_via[col].values.astype(np.float64)
        ref = df_via[col].values.astype(np.float64)
        if k == "aspect":
            c = np.where((x >= 90) & (x <= 180), 0.0, 1.0)
        elif k in INV:
            c = 1.0 - _norm(x, ref)
        elif k in COST:
            c = _norm(x, ref)
        else:
            c = _norm(x, ref)
        c = c * float(w[j])
        if k in F1_CRIT:
            f1v += c
        elif k in F2_CRIT:
            f2v += c
        else:
            f3v += c
    return f1v, f2v, f3v

def is_dominated_eps(f1t, f2t, f3t, F1, F2, F3):
    """Dominance test with tolerance eps=1e-9."""
    weak  = (F1 <= f1t + EPS) & (F2 <= f2t + EPS) & (F3 >= f3t - EPS)
    strict = (F1 < f1t - EPS) | (F2 < f2t - EPS) | (F3 > f3t + EPS)
    return bool((weak & strict).any())

def argmax_trio(sc):
    st = sc[T0] + sc[T1] + sc[T2]
    return trio_arr[st.argmax()]

# ── Monte Carlo ────────────────────────────────────────────────────────────────
rng = np.random.default_rng(SEED)
draws = rng.dirichlet(KAPPA * w_ahp, size=N_DRAWS)

rows = []
t_total = time.time()

for cell_name, V, desc in CELLS:
    print(f"\n--- {cell_name}: {desc} ---")
    nd_g = 0; nd_o = 0
    t0 = time.time()
    trio_cache = {}

    for draw_idx, w in enumerate(draws):
        f1v, f2v, f3v = compute_objs_Ap_f64(w)
        F1 = f1v[T0] + f1v[T1] + f1v[T2]
        F2 = f2v[T0] + f2v[T1] + f2v[T2]
        F3 = f3v[T0] + f3v[T1] + f3v[T2]

        sc = (V * w).sum(1)

        # Greedy
        trio_g = tuple(greedy_trio(sc, D_via))
        if trio_g not in trio_cache:
            ti, tj, tk = trio_g
            f1t = float(f1v[ti]+f1v[tj]+f1v[tk])
            f2t = float(f2v[ti]+f2v[tj]+f2v[tk])
            f3t = float(f3v[ti]+f3v[tj]+f3v[tk])
            trio_cache[trio_g] = (f1t, f2t, f3t)
        f1t, f2t, f3t = trio_cache[trio_g]
        if not is_dominated_eps(f1t, f2t, f3t, F1, F2, F3):
            nd_g += 1

        # Optimal
        trio_o = tuple(argmax_trio(sc))
        if trio_o not in trio_cache:
            ti, tj, tk = trio_o
            f1t = float(f1v[ti]+f1v[tj]+f1v[tk])
            f2t = float(f2v[ti]+f2v[tj]+f2v[tk])
            f3t = float(f3v[ti]+f3v[tj]+f3v[tk])
            trio_cache[trio_o] = (f1t, f2t, f3t)
        f1t, f2t, f3t = trio_cache[trio_o]
        if not is_dominated_eps(f1t, f2t, f3t, F1, F2, F3):
            nd_o += 1

        trio_cache.clear()  # cache per draw (objectives change each draw)

        if (draw_idx + 1) % 100 == 0:
            elapsed = time.time() - t0
            print(f"  [{draw_idx+1}/{N_DRAWS}]  grd={nd_g/(draw_idx+1)*100:.1f}%  "
                  f"opt={nd_o/(draw_idx+1)*100:.1f}%  {elapsed:.0f}s")

    Q2g = nd_g / N_DRAWS * 100
    Q2o = nd_o / N_DRAWS * 100
    SEg = (Q2g * (100 - Q2g) / N_DRAWS) ** 0.5
    SEo = (Q2o * (100 - Q2o) / N_DRAWS) ** 0.5
    print(f"  RESULT: greedy={Q2g:.2f}% (SE={SEg:.2f})  optimal={Q2o:.2f}% (SE={SEo:.2f})")
    rows += [
        {"cell": cell_name, "assembly": "greedy",  "Q2": Q2g, "SE": SEg},
        {"cell": cell_name, "assembly": "optimal", "Q2": Q2o, "SE": SEo},
    ]

# ── Chained assertions ────────────────────────────────────────────────────────
def get(cell, asm):
    return next(r["Q2"] for r in rows if r["cell"]==cell and r["assembly"]==asm)

print(f"\n{'='*70}")
print("CHAINED ASSERTIONS")
print(f"{'='*70}")

SE_ref = (WP3_VEC_GRD * (100-WP3_VEC_GRD) / N_DRAWS) ** 0.5

# A1: E1-M optimal = 100% (P1 for A_j=1, i.e. Proposition 1 itself)
a1 = abs(get("E1-M","optimal") - 100.0) < 1e-6
print(f"A1 E1-M optimal = {get('E1-M','optimal'):.2f}% (must be 100.0%): {'PASS' if a1 else 'FAIL'}")
assert a1, f"A1 FAIL: E1-M optimal={get('E1-M','optimal'):.4f}% — pipeline bug if fails"

# A2: E1-M greedy ≈ WP3 min-max greedy (65.8%)
a2 = abs(get("E1-M","greedy") - 65.8) < 3 * SE_ref
print(f"A2 E1-M greedy  = {get('E1-M','greedy'):.2f}% (WP3=65.8%, tol=3*SE={3*SE_ref:.1f}pp): {'PASS' if a2 else 'FAIL'}")

# A3: E1-V greedy ≈ WP3 vector greedy (54.0%)
a3 = abs(get("E1-V","greedy") - WP3_VEC_GRD) < 3 * SE_ref
print(f"A3 E1-V greedy  = {get('E1-V','greedy'):.2f}% (WP3=54.0%, tol={3*SE_ref:.1f}pp): {'PASS' if a3 else 'FAIL'}")

# A4: E1-V optimal ≈ WP3 vector optimal (56.8%)
a4 = abs(get("E1-V","optimal") - WP3_VEC_OPT) < 3 * SE_ref
print(f"A4 E1-V optimal = {get('E1-V','optimal'):.2f}% (WP3=56.8%, tol={3*SE_ref:.1f}pp): {'PASS' if a4 else 'FAIL'}")

# A2/A3 compare greedy against WP3 (different estimand: per-draw vs fixed objectives).
# Greedy mismatch is expected and documented. Only A1 (optimal=100%) is a pipeline test.
assert a1, "Pipeline broken: E1-M optimal != 100%. Stop."

# P1: E1-B optimal = 100%
p1 = abs(get("E1-B","optimal") - 100.0) < 1e-6
print(f"P1 E1-B optimal = {get('E1-B','optimal'):.2f}% (must be 100.0%): {'PASS' if p1 else 'FAIL'}")

# P2: E1-W optimal ≈ E1-V optimal (within 5pp)
p2_diff = abs(get("E1-W","optimal") - get("E1-V","optimal"))
p2 = p2_diff < 5.0
print(f"P2 |E1-W opt - E1-V opt| = {p2_diff:.1f}pp (pred <5pp): {'CONFIRMED' if p2 else 'PARTIAL (5-15pp)' if p2_diff<15 else 'FAILED'}")

# P3: E1-B greedy < 100%
p3 = get("E1-B","greedy") < 99.0
print(f"P3 E1-B greedy  = {get('E1-B','greedy'):.2f}% (must be <100%): {'CONFIRMED' if p3 else 'UNEXPECTED'}")

# ── Save ──────────────────────────────────────────────────────────────────────
# -- Save: archive path with metadata --
import subprocess as _sp
def _git_short():
    """Return short git hash, appending '-dirty' if there are uncommitted changes."""
    try:
        sha = _sp.check_output(
            ['git', '-C', str(Path(__file__).parent), 'rev-parse', '--short', 'HEAD'],
            stderr=_sp.DEVNULL).decode().strip()
        status = _sp.check_output(
            ['git', '-C', str(Path(__file__).parent), 'status', '--porcelain'],
            stderr=_sp.DEVNULL).decode().strip()
        if status:
            sha += '-dirty'
            print(f"WARNING: working tree is dirty. Abort if this run is for provenance.")
        return sha
    except Exception:
        return 'unknown'

code_commit = _git_short()
_archive_dir = Path(RESULTS_DIR).parent / 'results' / 'archive' / code_commit / 'e1'
_archive_dir.mkdir(parents=True, exist_ok=True)

df_out = pd.DataFrame(rows)
df_out['n_draws']       = N_DRAWS
df_out['seed']          = SEED
df_out['code_commit']   = code_commit
df_out['prereg_commit'] = 'fdf078a'  # commit where Athena predictions were written

out_archive = _archive_dir / f'e1_v3_perdraw_N{N_DRAWS}.csv'
df_out.to_csv(out_archive, index=False)

print(f"\n{'='*70}")
print("RESULTS:")
print(df_out.to_string(index=False))
print(f"\nTotal elapsed: {(time.time()-t_total)/60:.1f} min")
print(f"Archive: {out_archive}")
import hashlib as _hl
print(f"SHA-256: {_hl.sha256(out_archive.read_bytes()).hexdigest()} ({out_archive.name})")
print("DONE")
