# -*- coding: utf-8 -*-
"""
diagnose_v1v2.py  --  DEV-E7-001 extended diagnosis (V1 + V2)

V1: trio-comparison at BOTH k=50 AND k=200
    mc_2cube saw_old (X_via/norms) vs scoring.py saw_new (X_adj/norms)
    Expected:
      k=200 → 0/500   (concentrated weights → same portfolio despite orientation error)
      k=50  → ~498/500 (dispersed weights → orientation error changes portfolio)

V2: Proposition 1 test (decisive, theory-based)
    Build F_vec(w) = Pareto frontier using vector-normalised objectives
      G1_vec(P,w) = Σ_{j∈G1} w_j * Σ_{a∈P} (X_adj[a,j]/norms[j])
      G2_vec, G3_vec analogous
    Scorer correct (scoring.py) optimal SAW/vec MUST land in F_vec(w): 500/500
    Scorer wrong   (mc_2cube)   optimal SAW/vec need not land in F_vec(w)
    Expected:
      scoring.py: 500/500 at both κ (algebraic guarantee — see note below)
      mc_2cube:   500/500 at k=200 (same portfolio as scoring.py), <500/500 at k=50

Note on Proposition 1:
    scoring.py optimal = argmax Σ_j w_j*(X_adj[a,j]/norms[j]) over trios
                       = argmax G1_vec(P,w) + G2_vec(P,w) + G3_vec(P,w)
    This is a positive linear scalarisation of (G1_vec, G2_vec, G3_vec).
    Any optimal solution to a linear scalarisation is (weakly) Pareto optimal.
    Since all group weights W_g = Σ_{j∈Gg} w_j are strictly positive,
    the optimal is STRICTLY Pareto optimal → guaranteed in F_vec(w).

Also prints:
    - Full data SHAs (for hardcoding in run_e7_kappa_sweep.py)
    - Summary table for DEV-E7-001 conclusion
"""
import os, sys, hashlib, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

if "MCDM_DATA_DIR" not in os.environ:
    for candidate in [
        "/home/julioazancort/scratch/mcdm",
        str(ROOT / "data"),
    ]:
        if os.path.exists(candidate):
            os.environ["MCDM_DATA_DIR"] = candidate
            break

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS,
    haversine_km, MIN_DIST_KM, _build_decision_matrix,
    greedy_trio, F1_CRIT, F2_CRIT, F3_CRIT,
)
from scoring import make_scorers

EPS = 1e-9

# ── Data setup ─────────────────────────────────────────────────────────────────
print("Loading data...", flush=True)
df_all, _, _ = load_data()
df_imp  = impute_nan(df_all)
df_via  = df_imp[df_imp[COL["protected"]] > 0].copy()
N       = len(df_via)
assert N == 389, f"Expected 389 admissible sites, got {N}"

w_ahp     = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)
col_names = list(AHP_WEIGHTS.keys())
D         = haversine_km(df_via["latitude (degrees)"].values,
                         df_via["longitude (degrees)"].values)
valid     = D >= MIN_DIST_KM
trios     = np.array(
    [(i, j, k)
     for i in range(N) for j in range(i+1, N) if valid[i, j]
     for k in range(j+1, N) if valid[i, k] and valid[j, k]],
    dtype=np.int32,
)
T0, T1, T2  = trios[:, 0], trios[:, 1], trios[:, 2]
trio_lookup = {(int(T0[i]),int(T1[i]),int(T2[i])): i for i in range(len(trios))}
print(f"Sites: {N}  Trios: {len(trios):,}", flush=True)

X_via, benefit = _build_decision_matrix(df_via)
X_adj          = X_via.copy()
for j, b in enumerate(benefit):
    if not b: X_adj[:, j] = 1.0 - X_via[:, j]
norms_via = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)
saw_new, topsis_new = make_scorers(X_via, X_adj, norms_via, benefit)

# Group indices (for V2 vector objectives)
G1_idx = np.array([col_names.index(c) for c in F1_CRIT], dtype=int)
G2_idx = np.array([col_names.index(c) for c in F2_CRIT], dtype=int)
G3_idx = np.array([col_names.index(c) for c in F3_CRIT], dtype=int)

# Pre-compute normalised values (constant across draws)
xnorm_adj = X_adj / norms_via  # (N, M)  used for V2 objectives

# mc_2cube scorer (inline, as in mc_2cube_and_4thcell.py)
def saw_old(w, norm="minmax"):
    if norm == "minmax":
        return (X_adj * w).sum(1)
    else:
        return ((X_via / norms_via) * w).sum(1)  # orientation bug: X_via not X_adj

def argmax_trio_fn(sc):
    st = sc[T0] + sc[T1] + sc[T2]
    return tuple(map(int, trios[int(st.argmax())]))


# ── Load weight matrices ───────────────────────────────────────────────────────
print("\n" + "="*60, flush=True)
print("DRAW MATRICES: SHA verification")
print("="*60, flush=True)

SEED = 42

def load_or_generate(path, kappa, seed):
    rng_ref = np.random.default_rng(seed)
    W_ref   = rng_ref.dirichlet(kappa * w_ahp, size=500)
    sha_ref = hashlib.sha256(W_ref.tobytes()).hexdigest()
    if path.exists():
        W_file     = np.load(path)
        sha_file   = hashlib.sha256(W_file.tobytes()).hexdigest()
        file_bytes = hashlib.sha256(path.read_bytes()).hexdigest()
        match      = (sha_file == sha_ref)
        src        = f"file ({path.name})"
        W_use      = W_file
    else:
        sha_file = "(file not found)"
        match    = False
        src      = "regenerated (seed=42)"
        W_use    = W_ref
    print(f"k={kappa}  data_sha_ref (rng42):  {sha_ref}")
    print(f"k={kappa}  data_sha_file:          {sha_file if path.exists() else 'N/A'}")
    print(f"k={kappa}  source: {src}  match: {'OK' if match else 'MISMATCH'}")
    return W_use, sha_ref

W200, sha_ref200 = load_or_generate(
    ROOT / "results" / "e1" / "e1_weights_k200.npy", 200, SEED)
W50,  sha_ref50  = load_or_generate(
    ROOT / "results" / "e1" / "e1_weights_k50.npy",   50, SEED)
print(flush=True)
print(">>> Hardcode these in run_e7_kappa_sweep.py (DATA_SHA_K200, DATA_SHA_K50)")
print(f"DATA_SHA_K200 = \"{sha_ref200}\"")
print(f"DATA_SHA_K50  = \"{sha_ref50}\"")


# ── V1: per-draw trio comparison mc_2cube vs scoring.py ─────────────────────
def v1_compare(W, kappa):
    """Count SAW/vec trios that differ between saw_old and saw_new."""
    n_diff_greedy = 0
    n_diff_opt    = 0
    for w in W:
        sc_old = saw_old(w, "vector")
        sc_new = saw_new(w, "vector")
        t_old_g = tuple(map(int, greedy_trio(sc_old, D)))
        t_new_g = tuple(map(int, greedy_trio(sc_new, D)))
        t_old_o = argmax_trio_fn(sc_old)
        t_new_o = argmax_trio_fn(sc_new)
        if t_old_g != t_new_g: n_diff_greedy += 1
        if t_old_o != t_new_o: n_diff_opt    += 1
    print(f"k={kappa}  SAW/vec greedy:  {n_diff_greedy}/{len(W)} trios differ", flush=True)
    print(f"k={kappa}  SAW/vec optimal: {n_diff_opt}/{len(W)} trios differ", flush=True)
    return n_diff_greedy, n_diff_opt


print("\n" + "="*60, flush=True)
print("V1: Trio comparison mc_2cube saw_old vs scoring.py saw_new")
print("="*60, flush=True)
print(f"Running {2 * len(W200)} scorings × 2 cells (greedy+opt)...", flush=True)
t0 = time.time()
g200, o200 = v1_compare(W200, 200)
g50,  o50  = v1_compare(W50,  50)
print(f"Done in {time.time()-t0:.0f}s", flush=True)

print()
if g200 == 0 and o200 == 0:
    print("V1 k=200: 0/500 differ — orientation error does NOT change portfolio at k=200")
    print("  (concentrated weights → rankings stable despite X_via vs X_adj)")
else:
    print(f"V1 k=200: {max(g200,o200)}/500 differ — UNEXPECTED (orientation error affects k=200 too)")
    print("  STOP: the orientation-bug hypothesis is INCONSISTENT with k=200 data.")
    print("  Report to user before any macro changes.")

if g50 > 0 or o50 > 0:
    print(f"V1 k=50:  {max(g50,o50)}/500 differ — orientation error changes portfolio at k=50")
    print("  (dispersed weights amplify orientation error)")
else:
    print("V1 k=50:  0/500 differ — UNEXPECTED (no portfolio change at k=50?)")


# ── V2: Proposition 1 test ─────────────────────────────────────────────────
def compute_vec_objs(w):
    """
    Per-trio vector-normalised objectives.
    All three groups are benefit-type (higher = better).
    G1_vec(P) = Σ_{j∈G1} w_j * Σ_{a∈P} (X_adj[a,j]/norms[j])
    """
    g1 = (xnorm_adj[:, G1_idx] * w[G1_idx]).sum(1)   # (N,)
    g2 = (xnorm_adj[:, G2_idx] * w[G2_idx]).sum(1)
    g3 = (xnorm_adj[:, G3_idx] * w[G3_idx]).sum(1)
    G1 = g1[T0] + g1[T1] + g1[T2]                     # (n_trios,)
    G2 = g2[T0] + g2[T1] + g2[T2]
    G3 = g3[T0] + g3[T1] + g3[T2]
    return G1, G2, G3


def is_dominated_maxmax(trio_tuple, G1, G2, G3):
    """
    Return True if trio is dominated in the max-max-max objective space.
    P' dominates P if G_i(P') >= G_i(P) for all i (at least one strict).
    """
    key = (min(trio_tuple), sorted(trio_tuple)[1], max(trio_tuple))
    idx = trio_lookup.get(key, -1)
    if idx < 0:
        # tuple may come unsorted from argmax_trio_fn
        s = tuple(sorted(trio_tuple))
        idx = trio_lookup.get(s, -1)
    if idx < 0:
        return False  # trio not in admissible set
    g1t, g2t, g3t = float(G1[idx]), float(G2[idx]), float(G3[idx])
    mask = np.ones(len(G1), dtype=bool)
    mask[idx] = False
    G1m, G2m, G3m = G1[mask], G2[mask], G3[mask]
    weak   = (G1m >= g1t - EPS) & (G2m >= g2t - EPS) & (G3m >= g3t - EPS)
    strict = (G1m >  g1t + EPS) | (G2m >  g2t + EPS) | (G3m >  g3t + EPS)
    return bool((weak & strict).any())


def v2_prop1(W, kappa):
    """
    For each draw w: check if optimal trio from saw_new and saw_old
    land in F_vec(w) (max-max-max Pareto frontier).
    scoring.py (saw_new): must be 500/500 (Proposition 1 guarantee).
    mc_2cube   (saw_old): may differ.
    """
    hits_new = 0
    hits_old = 0
    for w in W:
        G1, G2, G3 = compute_vec_objs(w)
        # scoring.py optimal
        sc_new   = saw_new(w, "vector")
        t_new    = argmax_trio_fn(sc_new)
        if not is_dominated_maxmax(t_new, G1, G2, G3):
            hits_new += 1
        # mc_2cube optimal
        sc_old   = saw_old(w, "vector")
        t_old    = argmax_trio_fn(sc_old)
        if not is_dominated_maxmax(t_old, G1, G2, G3):
            hits_old += 1
    n = len(W)
    print(f"k={kappa}  scoring.py optimal in F_vec: {hits_new}/{n}", flush=True)
    print(f"k={kappa}  mc_2cube  optimal in F_vec: {hits_old}/{n}", flush=True)
    return hits_new, hits_old


print("\n" + "="*60, flush=True)
print("V2: Proposition 1 — optimal SAW/vec in F_vec(w)?")
print("Expected: scoring.py → 500/500 both κ;  mc_2cube → <500 at k=50")
print("="*60, flush=True)
t0 = time.time()
new200, old200 = v2_prop1(W200, 200)
new50,  old50  = v2_prop1(W50,  50)
print(f"Done in {time.time()-t0:.0f}s", flush=True)

print()
print("--- V2 interpretation ---")
if new200 == 500 and new50 == 500:
    print("scoring.py: 500/500 at both κ — Proposition 1 holds. scorer is CORRECT.")
else:
    print(f"WARNING: scoring.py: k=200={new200}/500  k=50={new50}/500")
    print("Proposition 1 violated for scoring.py — check objective definition.")

if old200 == 500 and old50 < 500:
    print(f"mc_2cube:  500/500 at k=200 (same portfolio as scoring.py for concentrated weights)")
    print(f"           {old50}/500 at k=50 (orientation error changes portfolio for dispersed weights)")
    print("CONCLUSION: orientation bug in mc_2cube confirmed by Proposition 1.")
elif old200 == 500 and old50 == 500:
    print("mc_2cube: 500/500 at BOTH κ — unexpected. Either:")
    print("  (a) mc_2cube always picks the same portfolio as scoring.py, OR")
    print("  (b) The X_via/X_adj difference does not affect portfolio selection at all.")
    print("  In case (a), no macro correction is needed. Re-check V1 results.")
elif old200 < 500:
    print(f"mc_2cube: {old200}/500 at k=200 — orientation bug ALSO affects k=200.")
    print("INCONSISTENT with Gate G1 passing at k=200. Report to user before any changes.")


# ── Summary ────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("SUMMARY FOR DEV-E7-001")
print("="*60)
print(f"V1  k=200  SAW/vec  trios differ:  greedy={g200}  opt={o200}")
print(f"V1  k=50   SAW/vec  trios differ:  greedy={g50}   opt={o50}")
print(f"V2  k=200  scoring.py in F_vec:  {new200}/500   mc_2cube in F_vec:  {old200}/500")
print(f"V2  k=50   scoring.py in F_vec:  {new50}/500    mc_2cube in F_vec:  {old50}/500")
print()
if g200 == 0 and new200 == 500 and old200 == 500 and g50 > 400 and new50 == 500 and old50 < 500:
    print("ALL CHECKS CONSISTENT WITH ORIENTATION BUG HYPOTHESIS:")
    print("  mc_2cube uses X_via/norms (no orientation flip for cost criteria)")
    print("  scoring.py uses X_adj/norms (cost criteria flipped — §4.3 convention)")
    print("  At k=200: weights concentrated → same portfolio despite wrong orientation")
    print("  At k=50:  weights dispersed   → orientation error changes portfolio")
    print()
    print("NEXT STEP: re-run mc_unified at k=50 with scoring.py + e1_weights_k50.npy")
    print("  to get correct \\QtwovecGreedyKfifty and \\QtwovecOptimalKfifty")
else:
    print("NOT ALL CHECKS CONSISTENT — review individual results above before proceeding.")

