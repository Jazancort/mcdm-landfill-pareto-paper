# -*- coding: utf-8 -*-
"""
WP4 — Synthetic instance grid, v4 (240 instances, ~16 min with 4 workers).

Key design:
  - OMP/MKL/OPENBLAS_NUM_THREADS=1 before numpy import
  - C matrix float32, trios int16 (N=389 << 32767)
  - Per-draw: dominance query O(n) vectorised + gap vectorised
    Uses w of the draw — satisfies wob = wfr coherence condition (§5.1)
    NO staircase per draw (that was the 262s bottleneck)
  - C @ Wg in batches of 20 draws (avoids (n,600,3) tensor thrash)
  - Full Pareto front only for nominal weights (for |F| reporting)
  - Unit tests removed from worker startup (run with --test)
  - Regression assert: argmax SAW ∈ F(w_draw) — O(n) dominance check

Usage
-----
    uv run python scripts/wp4_synthetic.py --test          # unit tests
    OMP_NUM_THREADS=1 ... uv run python scripts/wp4_synthetic.py --pilot
    for W in 0 1 2 3; do
      OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \\
      uv run python scripts/wp4_synthetic.py \\
          --calibrate --draws 200 --worker $W --total-workers 4 &
    done
"""

import os
os.environ.setdefault("OMP_NUM_THREADS",      "1")
os.environ.setdefault("MKL_NUM_THREADS",      "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS",  "1")

import sys, argparse, time
import numpy as np
import pandas as pd
from pathlib import Path
from itertools import product as iproduct

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent))
from pareto3d import pareto_front_3d, run_unit_tests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
W_AHP = np.array([
    0.177, 0.107, 0.107, 0.059,   # G1 siting
    0.059, 0.059, 0.069, 0.069,   # G2 impact
    0.107, 0.107, 0.080,           # G3 safety
], dtype=np.float32)
W_AHP /= W_AHP.sum()

M = len(W_AHP)
G1, G2, G3 = slice(0, 4), slice(4, 8), slice(8, 11)
GROUPS = [G1, G2, G3]

N_DRAWS   = 500
KAPPA     = 50
SEED_BASE = 20260929
EPS       = np.float32(1e-6)
BATCH     = 20   # draws per C @ Wg batch


# ---------------------------------------------------------------------------
# Normalisations
# ---------------------------------------------------------------------------
def minmax_norm(X):
    lo, hi = X.min(0), X.max(0)
    return ((X - lo) / np.where(hi > lo, hi - lo, 1.0)).astype(np.float32)

def vector_norm(X):
    norms = np.sqrt((X ** 2).sum(0))
    return (X / np.where(norms > 0, norms, 1.0)).astype(np.float32)

def tv_from_norm(V, w, alpha=1.0):
    A = V.max(0) - V.min(0)
    num = (w ** alpha) * (A ** alpha)
    s = num.sum()
    if s < 1e-30: return 0.0
    return 0.5 * float(np.abs(num / s - w).sum())


# ---------------------------------------------------------------------------
# Criterion generator
# ---------------------------------------------------------------------------
def generate_criteria(n, m, p0, shape, rng):
    X = np.zeros((n, m), dtype=np.float32)
    for j in range(m):
        nz = ~(rng.random(n) < p0)
        k = int(nz.sum())
        if k == 0: continue
        if shape == 'normal':
            v = rng.normal(0.5, 0.2, k).clip(1e-6, 1.0)
        elif shape == 'lognormal':
            v = rng.lognormal(-0.7, 0.6, k)
            lo, hi = v.min(), v.max()
            v = (v - lo) / (hi - lo + 1e-12)
        elif shape == 'bimodal':
            h = k // 2
            v = np.concatenate([rng.normal(0.2, 0.07, h).clip(0, 1),
                                 rng.normal(0.8, 0.07, k-h).clip(0, 1)])
            rng.shuffle(v)
        X[nz, j] = v.astype(np.float32)
    return X


# ---------------------------------------------------------------------------
# Fogo trio loader — int16 (N=389 << 32767)
# ---------------------------------------------------------------------------
def load_fogo_trios(data_dir):
    npy = data_dir / 'fogo_trios.npy'
    if not npy.exists():
        raise FileNotFoundError(f"fogo_trios.npy not found at {npy}")
    trios = np.load(npy).astype(np.int16)  # 11.1 MB vs 22.2 MB int32
    print(f"Loaded {len(trios):,} trios ({trios.nbytes/1e6:.1f} MB int16) from {npy}")
    return trios


# ---------------------------------------------------------------------------
# C matrix  (n_trios, M)  float32, 81.6 MB — built once per normalisation
# ---------------------------------------------------------------------------
def build_C(V_f32, trios_i16):
    """C[t, j] = sum_{i in t} V[i, j].  float32 output."""
    i0, i1, i2 = trios_i16[:, 0].astype(np.int32), \
                  trios_i16[:, 1].astype(np.int32), \
                  trios_i16[:, 2].astype(np.int32)
    return (V_f32[i0] + V_f32[i1] + V_f32[i2])  # (n_trios, M) float32


# ---------------------------------------------------------------------------
# Weight-group matrix  (M, 3)
# ---------------------------------------------------------------------------
def build_Wg(w_f32):
    Wg = np.zeros((M, 3), dtype=np.float32)
    for ell, g in enumerate(GROUPS):
        Wg[g, ell] = w_f32[g]
    return Wg


# ---------------------------------------------------------------------------
# Vectorised dominance query:  is F[best] dominated by any row of F?
# chunk-wise to avoid (n,n,3) allocation
# ---------------------------------------------------------------------------
def is_dominated_vec(F_f32, best_idx):
    """True if F[best_idx] is dominated by some other row.  O(n) vectorised."""
    p = F_f32[best_idx]
    n = len(F_f32)
    chunk = 100_000
    for s in range(0, n, chunk):
        e = min(s + chunk, n)
        Fj = F_f32[s:e]
        dom = ((Fj >= p - EPS).all(1) & (Fj > p + EPS).any(1))
        if s <= best_idx < e:
            dom[best_idx - s] = False
        if dom.any():
            return True
    return False


def gap_vec(F_f32, best_idx, R_f32):
    """Scale-free gap of F[best_idx] against its dominators.  O(n)."""
    p = F_f32[best_idx]
    n = len(F_f32)
    chunk = 100_000
    best_gap = np.float32(0.0)
    for s in range(0, n, chunk):
        e = min(s + chunk, n)
        Fj = F_f32[s:e]
        dom = ((Fj >= p - EPS).all(1) & (Fj > p + EPS).any(1))
        if s <= best_idx < e:
            dom[best_idx - s] = False
        if dom.any():
            diffs = (Fj[dom] - p) / R_f32
            best_gap = max(best_gap, float(diffs.min(1).max()))
    return float(best_gap)


# ---------------------------------------------------------------------------
# Instance evaluator — O(n) per draw, wob = wfr
# ---------------------------------------------------------------------------
def evaluate_instance(fogo_trios, X_raw, w_ahp, n_draws, kappa, seed):
    rng = np.random.default_rng(seed)
    results = {}
    w_f32 = w_ahp.astype(np.float32)

    for norm_name, norm_fn in [('minmax', minmax_norm), ('vector', vector_norm)]:
        V = norm_fn(X_raw)                  # (N, M) float32
        tv1 = tv_from_norm(V, w_f32, 1.0)
        tv2 = tv_from_norm(V, w_f32, 2.0)

        # Pre-compute C once (no allocations inside draw loop)
        C = build_C(V, fogo_trios)          # (n_trios, M) float32, 81.6 MB

        # Nominal objectives + full Pareto front (once, for |F| and regression)
        Wg_nom = build_Wg(w_f32)
        F_nom  = (C @ Wg_nom).astype(np.float32)  # (n_trios, 3)
        is_nd_nom = pareto_front_3d(F_nom.astype(float))
        front_size = int(is_nd_nom.sum())
        R_nom = (F_nom.max(0) - F_nom.min(0)).astype(np.float32)
        R_nom = np.where(R_nom > 0, R_nom, np.float32(1.0))

        # Regression assert (nominal, cheap)
        saw_nom = (C @ w_f32)
        best_nom = int(saw_nom.argmax())
        assert is_nd_nom[best_nom], (
            f"REGRESSION [{norm_name}] nominal: tv1={tv1:.4f}, |F|={front_size}"
        )

        # Monte Carlo — per-draw, using w of that draw (wob = wfr coherence)
        # SAW optimal: Q2=1 by prop:p1 (regression test for correctness)
        # Q3 measures how far suboptimal draws fall from the frontier
        q2_list, q3_list = [], []
        W_draws = rng.dirichlet(kappa * w_f32.astype(float), size=n_draws).astype(np.float32)
        W_draws /= W_draws.sum(1, keepdims=True)

        trios_i32 = fogo_trios.astype(np.int32)

        for b_start in range(0, n_draws, BATCH):
            b_end = min(b_start + BATCH, n_draws)
            W_batch = W_draws[b_start:b_end]
            SAW_batch = (C @ W_batch.T)  # (n_trios, b)

            for k in range(b_end - b_start):
                w_k = W_batch[k]
                Wg_k = build_Wg(w_k)
                F_k  = (C @ Wg_k).astype(np.float32)
                best_idx = int(SAW_batch[:, k].argmax())

                R_k = (F_k.max(0) - F_k.min(0)).astype(np.float32)
                R_k = np.where(R_k > 0, R_k, np.float32(1.0))

                dominated = is_dominated_vec(F_k, best_idx)
                q2_list.append(float(not dominated))
                q3_list.append(gap_vec(F_k, best_idx, R_k) if dominated else 0.0)

        results[norm_name] = {
            'tv1': tv1, 'tv2': tv2,
            'front_size': front_size,
            'Q2':    float(np.mean(q2_list)),
            'Q3':    float(np.mean(q3_list)),
            'Q2_se': float(np.std(q2_list) / np.sqrt(n_draws)),
            'Q3_se': float(np.std(q3_list) / np.sqrt(n_draws)),
        }
        del C  # free 81.6 MB before next normalisation

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test',         action='store_true')
    parser.add_argument('--pilot',        action='store_true')
    parser.add_argument('--calibrate',    action='store_true')
    parser.add_argument('--draws',        type=int, default=N_DRAWS)
    parser.add_argument('--worker',       type=int, default=0)
    parser.add_argument('--total-workers',type=int, default=1)
    args = parser.parse_args()

    if args.test:
        run_unit_tests(verbose=True)
        print("All unit tests passed.")
        return

    print(f"BLAS: OMP={os.environ.get('OMP_NUM_THREADS')} "
          f"MKL={os.environ.get('MKL_NUM_THREADS')} "
          f"OPENBLAS={os.environ.get('OPENBLAS_NUM_THREADS')}")

    data_dir = Path(__file__).parent.parent / 'data'
    out_dir  = Path(__file__).parent.parent / 'results'
    out_dir.mkdir(exist_ok=True)

    fogo_trios = load_fogo_trios(data_dir)
    N_FOGO = int(fogo_trios.astype(np.int32).max()) + 1
    print(f"N_FOGO={N_FOGO}, n_trios={len(fogo_trios):,}")

    p0_levels = np.linspace(0, 0.95, 20) if args.calibrate else np.linspace(0, 0.50, 11)
    shapes    = ['normal', 'lognormal', 'bimodal']
    n_reps    = 4
    n_draws   = args.draws

    all_jobs = list(iproduct(p0_levels, shapes, range(n_reps)))
    worker, n_workers = args.worker, args.total_workers
    my_jobs  = [j for i, j in enumerate(all_jobs) if i % n_workers == worker]
    suffix   = f'_w{worker}' if n_workers > 1 else ''

    if args.pilot:
        my_jobs = [(0.0,'normal',0),(0.25,'lognormal',0),(0.50,'bimodal',0),(0.90,'normal',0)]
        print(f"\n=== PILOT: {len(my_jobs)} instances, draws={n_draws} ===")

    print(f"Worker {worker}/{n_workers}: {len(my_jobs)} instances, draws={n_draws}")

    rows = []
    for done, (p0, shape, rep) in enumerate(my_jobs, 1):
        seed = SEED_BASE + int(round(p0 * 1000)) * 10000 + shapes.index(shape) * 100 + rep
        rng_inst = np.random.default_rng(seed)
        X = generate_criteria(N_FOGO, M, p0, shape, rng_inst)
        t0 = time.time()
        res = evaluate_instance(fogo_trios, X, W_AHP, n_draws, KAPPA, seed + 1)
        dt = time.time() - t0

        for nm, vals in res.items():
            rows.append({'p0': round(p0,3), 'shape': shape, 'rep': rep,
                         'norm': nm, **vals})

        pct = 100*done/len(my_jobs)
        print(f"[{done}/{len(my_jobs)}] {pct:.1f}% p0={p0:.2f} {shape} rep{rep} {dt:.0f}s | "
              f"mm tv1={res['minmax']['tv1']:.3f} Q2={res['minmax']['Q2']:.3f} "
              f"|F|={res['minmax']['front_size']} | "
              f"vec tv1={res['vector']['tv1']:.3f} Q2={res['vector']['Q2']:.3f} "
              f"|F|={res['vector']['front_size']}")
        sys.stdout.flush()

    df = pd.DataFrame(rows)
    csv_out = out_dir / f'wp4_synthetic{suffix}.csv'
    df.to_csv(csv_out, index=False)
    print(f"\nSaved {len(df)} rows to {csv_out}")

    if n_workers == 1 or args.pilot:
        print("\n=== Summary by norm ===")
        print(df.groupby('norm')[['Q2','Q3','tv1']].mean().round(4).to_string())
        print("\n=== Q2 and tv1 by (p0, norm) ===")
        print(df.groupby(['p0','norm'])[['Q2','tv1']].mean().unstack('norm').round(3).to_string())

    print(f"\nCONCLUÍDO worker={worker}")


if __name__ == '__main__':
    main()
