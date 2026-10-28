# -*- coding: utf-8 -*-
"""
test_aspect_formula.py
======================
Unit test: synthetic cardinal-direction planes verify that:
  aspect_correct(descent-North) = 0°
  aspect_correct(descent-East)  = 90°
  aspect_correct(descent-South) = 180°
  aspect_correct(descent-West)  = 270°

And that the binary leeward indicator [90°, 180°] is IDENTICAL for both
the correct formula (arctan2(-dx, dy)) and the notebook formula
(90 - arctan2(dx, -dy) + 360) % 360.
"""

import numpy as np
from scipy.ndimage import sobel

PIXEL_DEG = 0.000278   # ASTER GDEM pixel size in degrees (equatorial)


def _aspect_correct(dem, pixel_deg=PIXEL_DEG):
    """Santiago formula: descent azimuth 0=N clockwise. arctan2(-dx, dy)."""
    f = dem.astype(np.float32)
    dx = sobel(f, axis=1, mode='reflect') / (8 * pixel_deg)   # dz/dEast
    dy = sobel(f, axis=0, mode='reflect') / (8 * pixel_deg)   # dz/dSouth (row++)
    a = (np.degrees(np.arctan2(-dx, dy)) + 360.0) % 360.0
    flat = (np.abs(dx) < 1e-9) & (np.abs(dy) < 1e-9)
    a[flat] = -1.0
    return a


def _aspect_notebook(dem, pixel_deg=PIXEL_DEG):
    """Fogo notebook formula: (270deg - correct) mod 360.  N->270, E->180, S->90, W->0."""
    f = dem.astype(np.float32)
    dx = sobel(f, axis=1, mode='reflect') / (8 * pixel_deg)
    dy = sobel(f, axis=0, mode='reflect') / (8 * pixel_deg)
    a = (90.0 - np.degrees(np.arctan2(dx, -dy)) + 360.0) % 360.0
    flat = (np.abs(dx) < 1e-9) & (np.abs(dy) < 1e-9)
    a[flat] = -1.0
    return a


# 5x5 synthetic planes — "descent toward X" = elevation decreases going X
# In rasterio: row 0 = North, row index increases going South.
#              col 0 = West,  col index increases going East.
# "descent toward N": low elevation at N (row 0), high at S (row 4)
#   => elevation increases with row => tile arange(1,6) top-to-bottom
# "descent toward S": high elevation at N (row 0=5), low at S (row 4=1)
#   => elevation decreases with row => tile arange(5,0,-1) top-to-bottom
# Same logic for E/W along columns.
planes = {
    'N': np.tile(np.arange(1, 6, dtype=np.float32), (5, 1)).T,        # row: 1,2,3,4,5 (high S, descends N)
    'S': np.tile(np.arange(5, 0, -1, dtype=np.float32), (5, 1)).T,    # row: 5,4,3,2,1 (high N, descends S)
    'E': np.tile(np.arange(5, 0, -1, dtype=np.float32), (5, 1)),      # col: 5,4,3,2,1 (high W, descends E)
    'W': np.tile(np.arange(1, 6, dtype=np.float32), (5, 1)),           # col: 1,2,3,4,5 (high E, descends W)
}

# Expected correct-formula azimuths (descent direction, 0=N CW)
EXPECTED_CORRECT  = {'N': 0.0,   'E': 90.0,  'S': 180.0, 'W': 270.0}
# Expected notebook-formula azimuths (= (270 - correct) mod 360)
EXPECTED_NOTEBOOK = {'N': 270.0, 'E': 180.0, 'S': 90.0,  'W': 0.0}
# Expected leeward binary: only East-facing [90,180] is leeward
EXPECTED_LEEWARD  = {'N': False, 'E': True, 'S': True, 'W': False}


def run_tests():
    """Run all synthetic plane checks. Returns list of failure messages."""
    failures = []
    print("=== Aspect formula synthetic test (centre pixel [2,2]) ===")
    for d, dem in planes.items():
        ac = _aspect_correct(dem)[2, 2]
        an = _aspect_notebook(dem)[2, 2]
        ok_c = abs(ac - EXPECTED_CORRECT[d]) < 1.0
        ok_n = abs(an - EXPECTED_NOTEBOOK[d]) < 1.0
        leeward_c = 90 <= ac <= 180
        leeward_n = 90 <= an <= 180
        ok_inv = (leeward_c == leeward_n == EXPECTED_LEEWARD[d])
        status = "OK  " if (ok_c and ok_n and ok_inv) else "FAIL"
        note = "" if (ok_c and ok_n and ok_inv) else " <-- FAIL"
        print(
            f"  [{status}] descent->{d}: "
            f"correct={ac:.1f}deg (exp {EXPECTED_CORRECT[d]:.0f}), "
            f"notebook={an:.1f}deg (exp {EXPECTED_NOTEBOOK[d]:.0f}), "
            f"leeward: correct={leeward_c} notebook={leeward_n} "
            f"(exp {EXPECTED_LEEWARD[d]}){note}"
        )
        if not ok_c:
            failures.append(f"correct formula descent->{d}: got {ac:.1f}, expected {EXPECTED_CORRECT[d]:.0f}")
        if not ok_n:
            failures.append(f"notebook formula descent->{d}: got {an:.1f}, expected {EXPECTED_NOTEBOOK[d]:.0f}")
        if not ok_inv:
            failures.append(
                f"leeward invariance descent->{d}: correct={leeward_c}, notebook={leeward_n}, "
                f"expected_both={EXPECTED_LEEWARD[d]}"
            )
    return failures


if __name__ == '__main__':
    import sys
    fails = run_tests()
    print()
    if fails:
        for f in fails:
            print(f"  FAIL: {f}")
        sys.exit(1)
    print("ALL PASS")
