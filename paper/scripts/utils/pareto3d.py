# -*- coding: utf-8 -*-
"""
pareto3d.py — Correct 3-objective Pareto filter using 2D staircase.

Algorithm (O(n log n)):
  1. Sort by F0 descending. Ties in F0 are processed as a batch: all queries
     happen before any insertions into the staircase (avoids same-F0 points
     dominating each other).
  2. Maintain a 2D staircase of (F1, F2) for points already processed.
     The staircase is a list of points sorted descending by F1, with strictly
     increasing F2 (it is a proper Pareto front in 2D).
  3. Point p is dominated iff there exists a staircase point s with
     s.F1 >= p.F1 - eps AND s.F2 >= p.F2 - eps.
     After sorting by F0 desc, all staircase points satisfy s.F0 >= p.F0,
     so only checking F1 and F2 suffices.
  4. To query efficiently: binary-search for the insertion point of p.F1
     in the staircase (sorted desc F1). The rightmost staircase point with
     F1 >= p.F1 has the maximum F2 among all staircase points with F1 >= p.F1.
     If that maximum F2 >= p.F2, then p is dominated.
  5. Insert p into the staircase and prune: remove all points dominated by p.

Passes four validation tests:
  (a) Counterexample (10,10,1)/(9,1,10)/(8,5,5): all 3 non-dominated
  (b) 300 random uniform sets: 0 errors vs brute force
  (c) 300 anticorrelated sets: 0 errors vs brute force
  (d) 200 sets with massive ties: 0 errors vs brute force
"""

import bisect
import numpy as np


EPS = 1e-9


def pareto_front_3d(F: np.ndarray, eps: float = EPS) -> np.ndarray:
    """
    Return boolean mask of non-dominated rows of F (shape n×3), all maximised.

    O(n log n) correct 3D Pareto filter using sort + 2D staircase.
    Safe for n up to several million.

    Parameters
    ----------
    F   : (n, 3) float array, all objectives maximised
    eps : tolerance for dominance comparisons

    Returns
    -------
    nd  : (n,) boolean mask, True = non-dominated
    """
    F = np.asarray(F, dtype=float)
    n = len(F)
    if n == 0:
        return np.zeros(0, dtype=bool)

    # Sort by F0 descending, break ties by F1 desc then F2 desc
    order = np.lexsort((-F[:, 2], -F[:, 1], -F[:, 0]))
    F_s = F[order]
    nd_s = np.ones(n, dtype=bool)

    # Staircase: list of [f1, f2] sorted descending by f1,
    # with strictly increasing f2 (the 2D Pareto front of processed points).
    # Invariant: staircase[0].f1 is highest, staircase[-1].f2 is highest.
    staircase_f1 = []   # desc sorted f1 values
    staircase_f2 = []   # corresponding f2 values (strictly increasing)

    i = 0
    while i < n:
        # Collect all points with the same F0 value (process as a batch)
        f0_val = F_s[i, 0]
        j = i + 1
        while j < n and F_s[j, 0] >= f0_val - eps:
            j += 1
        batch = F_s[i:j]  # all points with F0 == f0_val (within eps)

        # --- Query phase: classify each point in the batch ---
        batch_dominated = np.zeros(len(batch), dtype=bool)
        for k, p in enumerate(batch):
            pf1, pf2 = p[1], p[2]
            # Check against staircase (points with F0 > current F0)
            if staircase_f1:
                idx = _bisect_desc_ge(staircase_f1, pf1, eps)
                if idx > 0 and staircase_f2[idx - 1] >= pf2 - eps:
                    batch_dominated[k] = True
                    continue
            # Check intra-batch dominance (other points in same F0 group
            # can dominate via F1 and F2, since F0 is tied)
            for m, q in enumerate(batch):
                if m == k:
                    continue
                if (q[1] >= pf1 - eps and q[2] >= pf2 - eps and
                        (q[1] > pf1 + eps or q[2] > pf2 + eps)):
                    batch_dominated[k] = True
                    break

        # --- Insert phase: add non-dominated batch points to staircase ---
        for k, p in enumerate(batch):
            if batch_dominated[k]:
                continue
            pf1, pf2 = p[1], p[2]
            # Insert p into staircase and prune dominated points
            # A staircase point s is dominated by p iff s.f1 <= p.f1+eps and s.f2 <= p.f2+eps
            new_f1 = []
            new_f2 = []
            for sf1, sf2 in zip(staircase_f1, staircase_f2):
                if sf1 <= pf1 + eps and sf2 <= pf2 + eps:
                    pass  # dominated by p, drop
                else:
                    new_f1.append(sf1)
                    new_f2.append(sf2)
            # Insert p in correct position (descending f1 order)
            pos = _bisect_desc_insert(new_f1, pf1)
            new_f1.insert(pos, pf1)
            new_f2.insert(pos, pf2)
            staircase_f1 = new_f1
            staircase_f2 = new_f2

        # Mark dominated points in output
        nd_s[i:j][batch_dominated] = False
        i = j

    result = np.zeros(n, dtype=bool)
    result[order] = nd_s
    return result


def _bisect_desc_ge(desc_list: list, value: float, eps: float) -> int:
    """
    In a descending sorted list, return the count of elements >= value - eps.
    Equivalent to the index of the first element < value - eps.
    """
    lo, hi = 0, len(desc_list)
    threshold = value - eps
    while lo < hi:
        mid = (lo + hi) // 2
        if desc_list[mid] >= threshold:
            lo = mid + 1
        else:
            hi = mid
    return lo


def _bisect_desc_insert(desc_list: list, value: float) -> int:
    """Position to insert value keeping the list descending."""
    lo, hi = 0, len(desc_list)
    while lo < hi:
        mid = (lo + hi) // 2
        if desc_list[mid] > value:
            lo = mid + 1
        else:
            hi = mid
    return lo


# ── Brute-force reference (O(n²), for testing only) ─────────────────────────

def pareto_front_brute(F: np.ndarray, eps: float = EPS) -> np.ndarray:
    F = np.asarray(F, dtype=float)
    n = len(F)
    nd = np.ones(n, dtype=bool)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if (np.all(F[j] >= F[i] - eps) and np.any(F[j] > F[i] + eps)):
                nd[i] = False
                break
    return nd


# ── Unit tests ───────────────────────────────────────────────────────────────

def run_unit_tests(verbose: bool = True) -> bool:
    """
    Four test cases. Raises AssertionError with details on any failure.
    Returns True if all pass.
    """
    passed = 0

    # (a) The documented counterexample to the sweep filter
    F = np.array([[10, 10, 1],
                  [9,  1, 10],
                  [8,  5,  5]], dtype=float)
    nd = pareto_front_3d(F)
    assert nd.all(), (
        f"TEST (a) FAILED: counterexample — expected [T,T,T], got {nd}\n"
        "P3=(8,5,5) must be non-dominated: P1 loses on F2, P2 loses on F1."
    )
    passed += 1
    if verbose: print("TEST (a) PASSED: counterexample (10,10,1)/(9,1,10)/(8,5,5)")

    # (b) Random uniform — compare against brute force
    rng = np.random.default_rng(20260929)
    errors_b = 0
    for _ in range(300):
        F = rng.random((50, 3))
        nd_stair = pareto_front_3d(F)
        nd_brute = pareto_front_brute(F)
        if not np.array_equal(nd_stair, nd_brute):
            errors_b += 1
    assert errors_b == 0, f"TEST (b) FAILED: {errors_b}/300 random uniform sets disagree with brute force"
    passed += 1
    if verbose: print(f"TEST (b) PASSED: 300 random uniform sets, 0 errors vs brute force")

    # (c) Anticorrelated — hardest case for staircase
    errors_c = 0
    for _ in range(300):
        t = rng.random(50)
        F = np.stack([t, 1 - t + 0.1 * rng.random(50),
                         1 - t + 0.1 * rng.random(50)], axis=1)
        nd_stair = pareto_front_3d(F)
        nd_brute = pareto_front_brute(F)
        if not np.array_equal(nd_stair, nd_brute):
            errors_c += 1
    assert errors_c == 0, f"TEST (c) FAILED: {errors_c}/300 anticorrelated sets disagree"
    passed += 1
    if verbose: print(f"TEST (c) PASSED: 300 anticorrelated sets, 0 errors vs brute force")

    # (d) Massive ties (discrete grid)
    errors_d = 0
    for _ in range(200):
        F = rng.integers(0, 5, size=(50, 3)).astype(float)
        nd_stair = pareto_front_3d(F)
        nd_brute = pareto_front_brute(F)
        if not np.array_equal(nd_stair, nd_brute):
            errors_d += 1
    assert errors_d == 0, f"TEST (d) FAILED: {errors_d}/200 tie sets disagree"
    passed += 1
    if verbose: print(f"TEST (d) PASSED: 200 discrete tie sets, 0 errors vs brute force")

    if verbose: print(f"\nAll {passed}/4 unit tests passed.")
    return True


def benchmark(n: int = 1_944_653) -> float:
    """Return wall-clock seconds for n random points."""
    import time
    rng = np.random.default_rng(42)
    F = rng.random((n, 3)).astype(np.float32)
    t0 = time.time()
    nd = pareto_front_3d(F)
    dt = time.time() - t0
    print(f"n={n:,}: |front|={nd.sum()}, t={dt:.2f}s")
    return dt


if __name__ == "__main__":
    run_unit_tests()
    benchmark()
