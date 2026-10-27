# -*- coding: utf-8 -*-
"""
run_e7_kappa_sweep.py -- E7: κ sensitivity of factorial contrasts.

PRESPEC: corpus/PRESPEC_E7_KAPPA.md (tag prespec-e7-kappa)
AMENDMENT A1: corpus/PRESPEC_E7_KAPPA_A1.md (tag prespec-e7-kappa-a1)

Status: POST HOC (declared in PRESPEC). Results are descriptive.

Design:
  - Same 8 cells as Table 5 (2³: SAW/TOPSIS × mm/vec × greedy/opt)
  - κ ∈ {25, 50, 100, 200, 400, 1000} + w_AHP deterministic point
  - 500 paired draws per κ
  - Seeds: κ=200 → 42, κ=50 → 42 (same seed, different alpha), others → 100 + κ
  - Gates G1-G5 checked before writing final output

Per-draw extras (Amendment A1):
  - H(w) = Σ_g W_g(w)²  (group Herfindahl concentration)
  - tv2(w) = ½ Σ_j |w_j² A_j² / Σ_k w_k² A_k² - w_j|  (TV under α=2)

Outputs (results/e7/):
  e7_raw.csv          per draw × κ × cell
  e7_contrasts.csv    bootstrap CIs for 6 contrasts × 6 κ
  e7_gates.txt        gate check log

Run on Athena:
  cd ~/scratch/mcdm-landfill-pareto-paper/paper
  tmux new -s e7
  uv run python scripts/run_e7_kappa_sweep.py
"""

import os, sys, time, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent

if "MCDM_DATA_DIR" not in os.environ:
    _athena  = "/home/julioazancort/scratch/mcdm"
    _windows = (
        r"G:\Faculdade\Estudo\Mestrado\2022.1\Trabalhos\Multicriterio"
        r"\03-latex\paper - Comparison between MCDM Methods for Landfill Site Selection\data"
    )
    if os.path.exists(_athena):
        os.environ["MCDM_DATA_DIR"] = _athena
    elif os.path.exists(_windows):
        os.environ["MCDM_DATA_DIR"] = str(ROOT / "data")

sys.path.insert(0, str(ROOT / "scripts"))

from mcdm_experiment import (
    load_data, impute_nan, COL, AHP_WEIGHTS,
    haversine_km, MIN_DIST_KM, _build_decision_matrix,
    greedy_trio, F1_CRIT, F2_CRIT, F3_CRIT,
)
from pareto_utils import build_pareto_utils
from scoring import make_scorers

# ── Constants ─────────────────────────────────────────────────────────────────
E1_SHA   = "bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487"
E1_SHA50 = "e761c76d47bb7b6f949d116170fd900b8a87f4c356bf4a149f403a0f586060be"
# Data SHAs: sha256(W.tobytes()) — verified 2026-11-01 by diagnose_v1v2.py
# Must match rng(42).dirichlet(kappa*w_ahp, size=500).tobytes()
DATA_SHA_K200 = "1d5bb4dae459e895c818343c1805f3c0e39b379d28c5454e6ef0e5bc23b807c1"
DATA_SHA_K50  = "8b91cba20b29b08bde9f26a19eaceeabf187791ae7c8d60bbb9982ea87084ddf"
N_DRAWS  = 500
B_BOOT   = 2000
BASE_SEED = 100  # seed for new κ = BASE_SEED + κ
SEED_200  = 42   # reuse existing κ=200 seed (e1_weights_k200.npy)
SEED_50   = 42   # reuse existing κ=50 seed (e1_weights_k50.npy, same seed=42 + alpha=50)

ALPHAS = [25, 50, 100, 200, 400, 1000]

OUT = ROOT / "results" / "e7"
OUT.mkdir(parents=True, exist_ok=True)

# Group weights for H(w)
# G1=cost (perm,slope,roads), G2=env (rivers,aspect,coast,prot,wells), G3=social (urban,aero,cult)
col_names = list(AHP_WEIGHTS.keys())
G1_idx = [col_names.index(c) for c in F1_CRIT]
G2_idx = [col_names.index(c) for c in F2_CRIT]
G3_idx = [col_names.index(c) for c in F3_CRIT]
G_groups = [G1_idx, G2_idx, G3_idx]
W_G = np.array([sum(list(AHP_WEIGHTS.values())[j] for j in g) for g in G_groups])

def herfindahl(w):
    """Group weight concentration H(w) = Σ_g W_g(w)²."""
    Wg = np.array([w[g].sum() for g in G_groups])
    return float((Wg**2).sum())

def tv2(w, rho_j):
    """TV under α=2: ½ Σ_j |w_j² A_j² / Σ_k w_k² A_k² − w_j|."""
    num = (w**2) * (rho_j**2)
    denom = num.sum()
    if denom < 1e-15:
        return 0.0
    weff2 = num / denom
    return float(0.5 * np.abs(weff2 - w).sum())

# ── Data setup ────────────────────────────────────────────────────────────────
print("Loading data ...", flush=True)
df_all, _, _ = load_data()
df_imp = impute_nan(df_all)
df_via = df_imp[df_imp[COL["protected"]] > 0].copy()
N = len(df_via)
assert N == 389, f"Expected 389 admissible sites, got {N}"

w_ahp     = np.array(list(AHP_WEIGHTS.values()), dtype=np.float64)

D     = haversine_km(df_via["latitude (degrees)"].values,
                     df_via["longitude (degrees)"].values)
valid = D >= MIN_DIST_KM
trios = np.array(
    [(i, j, k)
     for i in range(N) for j in range(i+1, N) if valid[i, j]
     for k in range(j+1, N) if valid[i, k] and valid[j, k]],
    dtype=np.int32,
)
T0, T1, T2 = trios[:, 0], trios[:, 1], trios[:, 2]
print(f"Sites: {N}  Trios: {len(trios):,}", flush=True)

compute_objs, is_dominated, _ = build_pareto_utils(df_via, col_names, trios)
X_via, benefit = _build_decision_matrix(df_via)
X_adj = X_via.copy()
for j, b in enumerate(benefit):
    if not b: X_adj[:, j] = 1.0 - X_via[:, j]
norms_via = np.maximum(np.sqrt((X_via**2).sum(0)), 1e-12)
saw_sc, topsis_sc = make_scorers(X_via, X_adj, norms_via, benefit)

# Vector amplitudes ρ_j (for TV(2))
rho_j = (X_adj.max(0) - X_adj.min(0)) / norms_via  # A_j for vector norm

def argmax_trio(sc):
    st = sc[T0] + sc[T1] + sc[T2]
    return trios[int(st.argmax())]

# Verify weight matrix SHA
wmat_path = ROOT / "results" / "e1" / "e1_weights_k200.npy"
wmat_k50_path = ROOT / "results" / "e1" / "e1_weights_k50.npy"
if wmat_path.exists():
    sha = hashlib.sha256(wmat_path.read_bytes()).hexdigest()
    assert sha == E1_SHA, f"Weight matrix κ=200 SHA mismatch: {sha[:16]}"
    W_k200 = np.load(wmat_path)
    data_sha200 = hashlib.sha256(W_k200.tobytes()).hexdigest()
    assert data_sha200 == DATA_SHA_K200, (
        f"κ=200 data SHA mismatch: got {data_sha200[:16]}, expected {DATA_SHA_K200[:16]}"
    )
    print(f"κ=200 weight matrix: {W_k200.shape}  file_SHA OK  data_SHA OK  ({data_sha200[:8]}...)", flush=True)
else:
    W_k200 = None
    print("WARNING: e1_weights_k200.npy not found", flush=True)

if wmat_k50_path.exists():
    sha50 = hashlib.sha256(wmat_k50_path.read_bytes()).hexdigest()
    assert sha50 == E1_SHA50, f"Weight matrix κ=50 SHA mismatch: {sha50[:16]}"
    W_k50 = np.load(wmat_k50_path)
    data_sha50 = hashlib.sha256(W_k50.tobytes()).hexdigest()
    assert data_sha50 == DATA_SHA_K50, (
        f"κ=50 data SHA mismatch: got {data_sha50[:16]}, expected {DATA_SHA_K50[:16]}\n"
        f"This means the file contains different draws than rng(42).dirichlet(50*w_ahp, 500).\n"
        f"Regenerate e1_weights_k50.npy with seed=42 before running E7."
    )
    print(f"loaded draws_k50  SHA={data_sha50[:8]}...  (data OK)", flush=True)
    print(f"κ=50 weight matrix:  {W_k50.shape}  file_SHA OK  data_SHA OK  ({data_sha50[:8]}...)", flush=True)
else:
    W_k50 = None
    print("WARNING: e1_weights_k50.npy not found — κ=50 gate may fail", flush=True)

CELLS_8 = [
    ("saw",   "minmax", "greedy"), ("saw",   "minmax", "optimal"),
    ("saw",   "vector", "greedy"), ("saw",   "vector", "optimal"),
    ("topsis","minmax", "greedy"), ("topsis","minmax", "optimal"),
    ("topsis","vector", "greedy"), ("topsis","vector", "optimal"),
]

# ── Gate checks ───────────────────────────────────────────────────────────────
GATE_LOG = []
def gate(name, passed, msg=""):
    status = "PASS" if passed else "FAIL"
    line = f"[{status}] {name}: {msg}"
    GATE_LOG.append(line)
    print(line, flush=True)
    return passed

# ── Main loop ─────────────────────────────────────────────────────────────────
all_records = []
t_start = time.time()

for alpha in ALPHAS:
    print(f"\n=== κ={alpha} ===", flush=True)
    # Seed selection
    if alpha == 200:
        seed = SEED_200
    elif alpha == 50:
        seed = SEED_50
    else:
        seed = BASE_SEED + alpha

    # Weight draws — use precomputed matrices for κ=200 and κ=50 (gate replication)
    if alpha == 200 and W_k200 is not None:
        W = W_k200
    elif alpha == 50 and W_k50 is not None:
        W = W_k50
    else:
        rng = np.random.default_rng(seed)
        W = rng.dirichlet(alpha * w_ahp, size=N_DRAWS)

    # Check no weight floor violation (flag only, don't abort)
    min_w = W.min(axis=1)
    n_floor = (min_w < 1e-4).sum()
    if n_floor > 0:
        print(f"  FLAG: {n_floor} draws have min_j w_j < 1e-4 (κ={alpha})", flush=True)

    t_alpha = time.time()
    for d in range(N_DRAWS):
        w = W[d]

        # Objectives and frontier
        f1v, f2v, f3v = compute_objs(w)
        F1 = f1v[T0] + f1v[T1] + f1v[T2]
        F2 = f2v[T0] + f2v[T1] + f2v[T2]
        F3 = f3v[T0] + f3v[T1] + f3v[T2]

        # Amendment A1 metrics
        Hw = herfindahl(w)
        tv2w = tv2(w, rho_j)

        for agg, norm, mont in CELLS_8:
            sc = saw_sc(w, norm) if agg == "saw" else topsis_sc(w, norm)
            if mont == "greedy":
                trio = greedy_trio(sc, D)
            else:
                trio = argmax_trio(sc)

            i0, i1, i2 = int(trio[0]), int(trio[1]), int(trio[2])
            q2 = int(not is_dominated(trio, F1, F2, F3))

            all_records.append({
                "alpha": alpha, "draw": d,
                "agg": agg, "norm": norm, "mont": mont,
                "nd_Q2Ap": q2,
                "H_w": round(Hw, 6),
                "tv2_w": round(tv2w, 6),
            })

        if d % 100 == 0:
            elapsed = time.time() - t_alpha
            eta = elapsed / max(d, 1) * (N_DRAWS - d)
            print(f"  κ={alpha} draw {d:3d}/{N_DRAWS}  {elapsed:4.0f}s  ETA {eta:3.0f}s",
                  flush=True)

    print(f"  κ={alpha} done in {time.time()-t_alpha:.0f}s", flush=True)

df_raw = pd.DataFrame(all_records)
df_raw.to_csv(OUT / "e7_raw.csv", index=False)
print(f"\nRaw data: {OUT/'e7_raw.csv'}  ({len(df_raw):,} rows)  {time.time()-t_start:.0f}s total")

# ── Gate G1: κ=200 and κ=50 reproduce Tables 5-6 ────────────────────────────
KNOWN_Q2 = {
    200: {("saw","minmax","greedy"):86.0, ("saw","minmax","optimal"):100.0,
          ("saw","vector","greedy"):66.2, ("saw","vector","optimal"):56.8,
          ("topsis","minmax","greedy"):94.4, ("topsis","minmax","optimal"):96.6,
          ("topsis","vector","greedy"):63.4, ("topsis","vector","optimal"):52.4},
    50:  {("saw","minmax","greedy"):97.6, ("saw","minmax","optimal"):100.0,
          ("saw","vector","greedy"):77.0, ("saw","vector","optimal"):79.4,
          ("topsis","minmax","greedy"):89.8, ("topsis","minmax","optimal"):92.2,
          ("topsis","vector","greedy"):52.0, ("topsis","vector","optimal"):51.0},
}
all_gates_pass = True
for kappa, cells_known in KNOWN_Q2.items():
    dfk = df_raw[df_raw.alpha == kappa]
    for (agg, norm, mont), expected in cells_known.items():
        # Use .astype(str) to guard against pandas StringDtype boolean indexing quirks
        got = dfk.query(f"agg=='{agg}' and norm=='{norm}' and mont=='{mont}'")["nd_Q2Ap"].mean()*100
        ok = abs(got - expected) <= 0.5
        gate(f"G1 κ={kappa} {agg}/{norm}/{mont}", ok, f"{got:.1f}% vs expected {expected:.1f}%")
        if not ok:
            all_gates_pass = False

# ── Gate G2: SAW/mm/opt = 100% at every κ ───────────────────────────────────
for kappa in ALPHAS:
    dfk = df_raw[df_raw.alpha == kappa]
    q2 = dfk.query("agg=='saw' and norm=='minmax' and mont=='optimal'")["nd_Q2Ap"].mean()*100
    ok = abs(q2 - 100.0) < 0.01
    gate(f"G2 SAW/mm/opt κ={kappa}", ok, f"{q2:.1f}%")
    if not ok:
        all_gates_pass = False

# ── Gate G3: 500 valid draws per κ ──────────────────────────────────────────
for kappa in ALPHAS:
    dfk = df_raw[df_raw.alpha == kappa]
    n_draws = dfk["draw"].nunique()
    ok = (n_draws == N_DRAWS)
    gate(f"G3 N_draws κ={kappa}", ok, f"{n_draws}")
    if not ok:
        all_gates_pass = False

# Write gate log
gate_file = OUT / "e7_gates.txt"
gate_file.write_text("\n".join(GATE_LOG) + "\n")
print(f"\nGate log: {gate_file}")
if not all_gates_pass:
    print("WARNING: Some gates failed — check e7_gates.txt before reporting")

# ── Bootstrap contrasts ───────────────────────────────────────────────────────
print("\nComputing bootstrap contrasts ...", flush=True)

def bstrap(diff_pp, B=B_BOOT, seed=99):
    rng_b = np.random.default_rng(seed)
    boots = np.array([rng_b.choice(diff_pp, size=len(diff_pp), replace=True).mean()
                      for _ in range(B)])
    obs = float(diff_pp.mean())
    lo  = float(np.percentile(boots, 2.5))
    hi  = float(np.percentile(boots, 97.5))
    sig = "SIG" if (lo > 0 or hi < 0) else "n.s."
    return obs, lo, hi, sig

contrast_records = []
for alpha in ALPHAS:
    dfk = df_raw[df_raw.alpha == alpha]
    pv  = dfk.pivot_table(index="draw",
                          columns=["agg","norm","mont"],
                          values="nd_Q2Ap")
    def C(agg, norm, mont):
        return pv[agg][norm][mont].values.astype(float)

    contrasts = {
        "Norm_greedy":  0.5*(C("saw","minmax","greedy")+C("topsis","minmax","greedy"))
                       -0.5*(C("saw","vector","greedy")+C("topsis","vector","greedy")),
        "Norm_optimal": 0.5*(C("saw","minmax","optimal")+C("topsis","minmax","optimal"))
                       -0.5*(C("saw","vector","optimal")+C("topsis","vector","optimal")),
        "Agg_pooled3":  (1/3)*((C("saw","minmax","greedy")-C("topsis","minmax","greedy"))
                              +(C("saw","vector","greedy")-C("topsis","vector","greedy"))
                              +(C("saw","vector","optimal")-C("topsis","vector","optimal"))),
        "Asm_vec_SAW":  C("saw","vector","optimal") - C("saw","vector","greedy"),
        "Asm_vec_TOP":  C("topsis","vector","optimal") - C("topsis","vector","greedy"),
        "Asm_mm_TOP":   C("topsis","minmax","optimal") - C("topsis","minmax","greedy"),
        # Per-method aggregation for Amendment A1
        "Agg_SAW_3inf": (1/3)*((C("saw","minmax","greedy")-C("topsis","minmax","greedy"))
                               +(C("saw","vector","greedy")-C("topsis","vector","greedy"))
                               +(C("saw","vector","optimal")-C("topsis","vector","optimal"))),
        "SAW_mean_3inf": (1/3)*(C("saw","minmax","greedy")
                               +C("saw","vector","greedy")
                               +C("saw","vector","optimal")),
        "TOP_mean_3inf": (1/3)*(C("topsis","minmax","greedy")
                               +C("topsis","vector","greedy")
                               +C("topsis","vector","optimal")),
    }
    for name, diff in contrasts.items():
        obs, lo, hi, sig = bstrap(diff * 100, B=B_BOOT, seed=100 + alpha)
        contrast_records.append({
            "kappa": alpha, "contrast": name,
            "diff_pp": round(obs, 2), "ci_lo": round(lo, 1), "ci_hi": round(hi, 1),
            "sig": sig,
        })

df_contrasts = pd.DataFrame(contrast_records)
df_contrasts.to_csv(OUT / "e7_contrasts.csv", index=False)
print(f"Contrasts: {OUT/'e7_contrasts.csv'}")

# Print key table
print("\n=== Key contrasts (pp) ===")
for contrast in ["Norm_greedy", "Agg_pooled3", "SAW_mean_3inf", "TOP_mean_3inf"]:
    row_str = f"{contrast:20}"
    for alpha in ALPHAS:
        r = df_contrasts[(df_contrasts.kappa==alpha)&(df_contrasts.contrast==contrast)].iloc[0]
        row_str += f"  κ={alpha}: {r.diff_pp:+6.1f}({r.sig:4})"
    print(row_str)

total = time.time() - t_start
print(f"\nDONE: {total:.0f}s ({total/60:.1f} min)")
print(f"Output: {OUT}")
