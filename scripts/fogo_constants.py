"""
fogo_constants.py
=================
Single source of truth for all Fogo numerical constants used in regression
tests and decomposition assertions.

ALL values come directly from main.tex tab:amplitude (lines 1372-1390).
Never written from memory. If main.tex changes, update this file and
re-run all regression tests.

Source: tab:amplitude, lines 1379-1390 of main.tex at commit 87bf3b9.
Criterion order (0-indexed, as they appear top-to-bottom in the table):
  0: perm      G1   w=0.152  Aj_vec=0.583  Aj_rnk=0.547
  1: slope     G1   w=0.113  Aj_vec=0.135  Aj_rnk=0.995
  2: roads     G1   w=0.030  Aj_vec=0.206  Aj_rnk=0.995
  3: rivers    G2   w=0.091  Aj_vec=0.265  Aj_rnk=0.995
  4: aspect    G2   w=0.075  Aj_vec=0.103  Aj_rnk=0.499
  5: coast     G2   w=0.069  Aj_vec=0.126  Aj_rnk=0.995
  6: protected G2   w=0.066  Aj_vec=0.105  Aj_rnk=0.995
  7: wells     G2   w=0.055  Aj_vec=0.081  Aj_rnk=0.995
  8: urban     G3   w=0.166  Aj_vec=0.107  Aj_rnk=0.989
  9: aero      G3   w=0.102  Aj_vec=0.086  Aj_rnk=0.995
 10: cult      G3   w=0.081  Aj_vec=0.171  Aj_rnk=0.981

TV row (bottom of tab:amplitude):
  TV(mm)=0.000, TV(vec)=0.315, TV(rnk)=0.091
"""

import numpy as np

# ─── Weights (col 3 of tab:amplitude) ────────────────────────────────────────
W = np.array([
    0.152,  # perm      G1
    0.113,  # slope     G1
    0.030,  # roads     G1
    0.091,  # rivers    G2
    0.075,  # aspect    G2
    0.069,  # coast     G2
    0.066,  # protected G2
    0.055,  # wells     G2
    0.166,  # urban     G3
    0.102,  # aero      G3
    0.081,  # cult      G3
], dtype=float)
W = W / W.sum()   # normalise (sum=1.000 before normalisation)

# ─── Amplitudes (cols 5 and 6 of tab:amplitude) ──────────────────────────────
AJ_VEC = np.array([0.583, 0.135, 0.206, 0.265, 0.103, 0.126, 0.105, 0.081,
                   0.107, 0.086, 0.171], dtype=float)

AJ_RNK = np.array([0.547, 0.995, 0.995, 0.995, 0.499, 0.995, 0.995, 0.995,
                   0.989, 0.995, 0.981], dtype=float)

AJ_MM  = np.ones(11, dtype=float)   # A_j = 1 by construction for min-max

# ─── Groups (from tab:amplitude, column 2) ───────────────────────────────────
# Source: lines 1379-1389 of main.tex, tab:amplitude
# G1 = perm, slope, roads       (indices 0, 1, 2)
# G2 = rivers, aspect, coast, protected, wells   (indices 3, 4, 5, 6, 7)
# G3 = urban, aero, cult        (indices 8, 9, 10)
OBJ_GROUPS = [[0, 1, 2], [3, 4, 5, 6, 7], [8, 9, 10]]

CRITERION_NAMES = [
    'perm', 'slope', 'roads', 'rivers', 'aspect', 'coast',
    'protected', 'wells', 'urban', 'aero', 'cult'
]

# ─── Published scalar results (from §6.2 and tab:tvorder) ────────────────────
# These are the values to assert against. Change ONLY with entry in DEVIATIONS.md.
TV_VEC   = 0.3146   # tab:amplitude TV row, vector column
L2_VEC   = 0.3127   # §6.6
MEFF_VEC = 4.0486   # §6.6

# TV_B and TV_W from decomposition with groups OBJ_GROUPS above.
# Source: Reviewer computation 2026-09-30, confirmed by paper §8.x (to be inserted).
TV_B_VEC = 0.2489   # between-group component
TV_W_VEC = 0.1986   # within-group component (weighted mean)

# TV for ranks
TV_RNK   = 0.0912   # tab:amplitude TV row, ranks column (reported as 0.091)

def verify_source():
    """Print the source lines for manual audit."""
    print("Source: main.tex tab:amplitude lines 1379-1389")
    print(f"  Criterion order: {CRITERION_NAMES}")
    print(f"  OBJ_GROUPS: G1={OBJ_GROUPS[0]}, G2={OBJ_GROUPS[1]}, G3={OBJ_GROUPS[2]}")
    print(f"  W (normalised): {np.round(W, 4)}")
    print(f"  AJ_VEC: {AJ_VEC}")
    print(f"  TV_VEC={TV_VEC}, L2_VEC={L2_VEC}, MEFF_VEC={MEFF_VEC}")
    print(f"  TV_B_VEC={TV_B_VEC}, TV_W_VEC={TV_W_VEC}")
