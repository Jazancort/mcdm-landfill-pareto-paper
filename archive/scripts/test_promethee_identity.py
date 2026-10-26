"""
test_promethee_identity.py
--------------------------
Verify: PROMETHEE II (usual preference) == affine transform of rank-weighted SAW
for arbitrary (heterogeneous) tie patterns.

The identity is:
    phi(a) = 2/(n-1) * sum_j w_j r_j(a) - (n+1)/(n-1)
where r_j(a) is the ORIENTED midrank of alternative a on criterion j
(ascending for cost criteria after sign flip, so higher rank = better).

With ties: midranks are averages of the positions that would be occupied.
This holds for ANY tie pattern across criteria.

exit 0 = PASS, exit 1 = FAIL
"""
import sys
import numpy as np

TOL = 1e-10

def midrank(values):
    """Oriented midranks: higher value → higher rank (1..n)."""
    n = len(values)
    ranks = np.zeros(n)
    for i, v in enumerate(values):
        # rank = 1 + number of values strictly below v + 0.5 * number of ties
        below = sum(1 for u in values if u < v)
        equal = sum(1 for u in values if u == v)
        ranks[i] = below + 0.5 * (equal - 1) + 1.0
    return ranks

def promethee_II_usual(P, w):
    """
    P: (n x m) matrix, P[i,j] = score of alternative i on criterion j.
       Higher is better on all criteria.
    w: (m,) weight vector, sum to 1.
    Returns: phi vector (n,)
    """
    n, m = P.shape
    phi = np.zeros(n)
    for i in range(n):
        for k in range(n):
            if i == k:
                continue
            # usual preference: P(a,b) = 1 if a > b, 0 otherwise (per criterion)
            pref = sum(w[j] for j in range(m) if P[i, j] > P[k, j])
            phi[i] += pref - sum(w[j] for j in range(m) if P[k, j] > P[i, j])
    return phi / (n - 1)

def saw_midrank(P, w):
    """
    SAW using oriented midranks.
    Returns: score vector (n,)
    """
    n, m = P.shape
    R = np.column_stack([midrank(P[:, j]) for j in range(m)])
    return R @ w

def check_affine_equiv(P, w, label):
    """Test that PROMETHEE II == affine(saw_midrank) up to TOL."""
    phi  = promethee_II_usual(P, w)
    saw  = saw_midrank(P, w)
    n    = len(phi)
    # Fit affine: phi = a * saw + b  (least squares, should be exact)
    A    = np.column_stack([saw, np.ones(n)])
    coef, residuals, *_ = np.linalg.lstsq(A, phi, rcond=None)
    phi_hat = A @ coef
    max_err = np.max(np.abs(phi - phi_hat))
    ok = max_err < TOL
    print(f"  [{label}] affine_a={coef[0]:.6f}  affine_b={coef[1]:.6f}  max_err={max_err:.2e}  {'OK' if ok else 'FAIL'}")
    # Also verify ranking order is preserved (affine with positive slope)
    assert coef[0] > 0, f"Non-positive affine slope: {coef[0]}"
    return ok

PASS = True

print("=== PROMETHEE II / SAW midrank affine identity ===\n")

# Case 1: no ties, 3 alternatives, 2 criteria
w1 = np.array([0.6, 0.4])
P1 = np.array([[3.0, 1.0], [2.0, 3.0], [1.0, 2.0]])
PASS &= check_affine_equiv(P1, w1, "no ties 3x2")

# Case 2: uniform ties (all equal on criterion 1)
P2 = np.array([[2.0, 1.0], [2.0, 3.0], [2.0, 2.0]])
PASS &= check_affine_equiv(P2, w1, "uniform tie on j=0")

# Case 3: heterogeneous ties (different patterns per criterion)
P3 = np.array([
    [3.0, 1.0, 2.0],
    [3.0, 2.0, 2.0],   # tie with row 0 on j=0, tie with row 0 on j=2
    [1.0, 3.0, 1.0],
    [2.0, 1.0, 3.0],
])
w3 = np.array([0.4, 0.35, 0.25])
PASS &= check_affine_equiv(P3, w3, "heterogeneous ties 4x3")

# Case 4: binary criterion (many ties of both values)
np.random.seed(42)
n4 = 8
P4 = np.column_stack([
    np.random.choice([0.0, 1.0], n4),   # binary — many ties
    np.random.permutation(n4).astype(float),  # no ties
    np.random.choice([1.0, 2.0, 3.0], n4),    # 3 values, ties
])
w4 = np.array([0.5, 0.3, 0.2])
PASS &= check_affine_equiv(P4, w4, "binary col + heterogeneous 8x3")

# Case 5: all tied on all criteria (degenerate — phi=0, saw=const; skip ratio check)
P5 = np.ones((4, 2))
w5 = np.array([0.5, 0.5])
phi5  = promethee_II_usual(P5, w5)
saw5  = saw_midrank(P5, w5)
ok5   = np.max(np.abs(phi5)) < TOL
print(f"  [all tied degenerate] phi_max={np.max(np.abs(phi5)):.2e}  {'OK' if ok5 else 'FAIL'}")
PASS &= ok5

print()
if PASS:
    print("ALL TESTS PASSED — PROMETHEE II and SAW midrank are affinely equivalent")
    print("including under heterogeneous tie patterns.")
    sys.exit(0)
else:
    print("FAIL — identity broken")
    sys.exit(1)
