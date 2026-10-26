# -*- coding: utf-8 -*-
"""
WP4 GPU — Pareto front em GPU1 (RTX 4000 Ada, CUDA_VISIBLE_DEVICES=1)
"""
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "1"

import cupy as cp, numpy as np, time, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from wp4_synthetic import (
    generate_criteria, minmax_norm, vector_norm, tv_from_norm,
    W_AHP, M, GROUPS, run_unit_test, N_DRAWS, KAPPA,
    load_fogo_trios
)
import pandas as pd
from pathlib import Path
from itertools import product as iproduct
import argparse

sys.stdout.reconfigure(encoding='utf-8')

EPS = 1e-6

# ── Pareto GPU ──────────────────────────────────────────────────────────────

def pareto_front_gpu(F_np: np.ndarray) -> np.ndarray:
    """
    Correct Pareto filter on GPU1.
    F_np: (n, 3) float32 numpy — all objectives maximised.
    Returns boolean mask (numpy).
    Skyline maintained on CPU (~150-300 points); dominance check vectorised on GPU.
    """
    n = len(F_np)
    order = np.lexsort((-F_np[:, 2], -F_np[:, 1], -F_np[:, 0]))
    F_s_np = F_np[order].astype(np.float32)

    F_s = cp.asarray(F_s_np)
    nd = cp.ones(n, dtype=cp.bool_)

    sky_cpu = F_s_np[:1].copy()   # (1,3) numpy skyline
    sky = cp.asarray(sky_cpu)     # GPU copy

    batch = 100_000
    for start in range(1, n, batch):
        end = min(start + batch, n)
        Fi = F_s[start:end]  # (b, 3)

        # dominance: any skyline point dominates Fi[j]?
        dom = (
            (sky[:, cp.newaxis, :] >= Fi[cp.newaxis, :, :] - EPS).all(axis=2) &
            (sky[:, cp.newaxis, :] >  Fi[cp.newaxis, :, :] + EPS).any(axis=2)
        ).any(axis=0)  # (b,)
        nd[start:end] = ~dom

        # update skyline: add non-dominated, prune dominated-by-new
        new_np = cp.asnumpy(Fi[~dom])
        if len(new_np):
            sky_cpu = np.vstack([sky_cpu, new_np])
            # prune points in skyline dominated by any of the new points
            keep = np.ones(len(sky_cpu), dtype=bool)
            for npi in new_np:
                dominated = (
                    (npi >= sky_cpu - EPS).all(axis=1) &
                    (npi >  sky_cpu + EPS).any(axis=1)
                )
                keep &= ~dominated
            # always keep the new points themselves
            keep[len(sky_cpu) - len(new_np):] = True
            sky_cpu = sky_cpu[keep]
            sky = cp.asarray(sky_cpu)

    cp.cuda.Stream.null.synchronize()
    nd_np = cp.asnumpy(nd)
    result = np.zeros(n, dtype=bool)
    result[order] = nd_np
    return result


def unit_test_gpu():
    F = np.array([[10, 10, 1], [9, 1, 10], [8, 5, 5]], dtype=np.float32)
    nd = pareto_front_gpu(F)
    assert nd.all(), f"GPU unit test FAILED: {nd}"
    print("GPU UNIT TEST PASSED: P1,P2,P3 all non-dominated.")


# ── Evaluate instance (GPU) ──────────────────────────────────────────────────

def evaluate_instance_gpu(fogo_trios: np.ndarray, X_raw: np.ndarray,
                           w_ahp: np.ndarray, n_draws: int, kappa: float,
                           seed: int) -> dict:
    rng = np.random.default_rng(seed)
    results = {}

    for norm_name, norm_fn in [('minmax', minmax_norm), ('vector', vector_norm)]:
        V = norm_fn(X_raw)
        tv1 = tv_from_norm(V, w_ahp, alpha=1.0)
        tv2 = tv_from_norm(V, w_ahp, alpha=2.0)

        # Pre-compute Pareto front once with nominal weights (GPU)
        t0 = time.time()
        site_obj = np.stack([V[:, g] @ w_ahp[g] for g in GROUPS], axis=1)
        trio_obj_np = site_obj[fogo_trios].sum(axis=1).astype(np.float32)
        is_nd = pareto_front_gpu(trio_obj_np)
        front_nom = trio_obj_np[is_nd]
        R = trio_obj_np.max(axis=0) - trio_obj_np.min(axis=0)
        R = np.where(R > 0, R, 1.0)
        t_front = time.time() - t0

        # MC draws (O(n) each — no Pareto computation)
        q2_list, q3_list = [], []
        for _ in range(n_draws):
            w = rng.dirichlet(kappa * w_ahp)
            w /= w.sum()
            scores = V @ w
            trio_scores = scores[fogo_trios].sum(axis=1)
            best_idx = int(trio_scores.argmax())
            q2_list.append(float(is_nd[best_idx]))
            f_best = trio_obj_np[best_idx]
            diffs = (front_nom - f_best[np.newaxis, :]) / R[np.newaxis, :]
            q3_list.append(float(max(0.0, diffs.min(axis=1).max())))

        results[norm_name] = {
            'tv1': tv1, 'tv2': tv2,
            'front_size': int(is_nd.sum()),
            't_front': round(t_front, 1),
            'Q2': float(np.mean(q2_list)),
            'Q3': float(np.mean(q3_list)),
            'Q2_se': float(np.std(q2_list) / np.sqrt(n_draws)),
            'Q3_se': float(np.std(q3_list) / np.sqrt(n_draws)),
        }
    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--calibrate', action='store_true')
    parser.add_argument('--draws', type=int, default=N_DRAWS)
    parser.add_argument('--worker', type=int, default=0)
    parser.add_argument('--total-workers', type=int, default=1)
    parser.add_argument('--pilot', action='store_true')
    args = parser.parse_args()

    print(f"GPU: {cp.cuda.Device(0).use()}")
    run_unit_test()
    unit_test_gpu()

    data_dir = Path(__file__).parent.parent / 'data'
    out_dir  = Path(__file__).parent.parent / 'results'
    out_dir.mkdir(exist_ok=True)

    fogo_trios = load_fogo_trios(data_dir)
    N_FOGO = int(fogo_trios.max()) + 1
    print(f"N_FOGO={N_FOGO}, n_trios={len(fogo_trios):,}")

    p0_levels = np.linspace(0, 0.95, 20) if args.calibrate else np.linspace(0, 0.50, 11)
    shapes = ['normal', 'lognormal', 'bimodal']
    n_reps = 4
    n_draws = args.draws

    all_jobs = list(iproduct(p0_levels, shapes, range(n_reps)))
    my_jobs  = [j for i, j in enumerate(all_jobs) if i % args.total_workers == args.worker]
    suffix   = f'_gpu_w{args.worker}' if args.total_workers > 1 else '_gpu'

    if args.pilot:
        my_jobs = [(0.0,'normal',0),(0.25,'lognormal',0),(0.50,'bimodal',0)]
        print(f"\n=== PILOT (GPU1): {len(my_jobs)} instances, draws={n_draws} ===")

    print(f"Worker {args.worker}/{args.total_workers}: {len(my_jobs)} instances")

    rows = []
    for done, (p0, shape, rep) in enumerate(my_jobs, 1):
        seed = 20260929 + int(round(p0*1000))*10000 + shapes.index(shape)*100 + rep
        rng_inst = np.random.default_rng(seed)
        X = generate_criteria(N_FOGO, M, p0, shape, rng_inst)

        t0 = time.time()
        res = evaluate_instance_gpu(fogo_trios, X, W_AHP, n_draws, KAPPA, seed+1)
        dt = time.time() - t0

        for norm_name, vals in res.items():
            rows.append({'p0': round(p0,3), 'shape': shape, 'rep': rep,
                         'norm': norm_name, **vals})

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
    if args.pilot:
        print("\n=== Summary ===")
        print(df.groupby('norm')[['Q2','Q3','tv1']].mean().round(4).to_string())
    print(f"\nCONCLUÍDO worker={args.worker}")


if __name__ == '__main__':
    main()
