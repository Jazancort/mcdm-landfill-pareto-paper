# -*- coding: utf-8 -*-
"""
e6_generate_amplitudes.py — Amplitude vector construction for PRESPEC_E6.

Pre-specification: corpus/PRESPEC_E6.md (commit before first E6 run)

Implements:
  - TV_W and TV_B computation using the §6.4 formula from the manuscript
  - Calibration of within-group deviation δ_g via bisection
  - Construction of A_j vectors for the 7 cells:
      M            : A_j = 1               (TV_B=0, TV_W=0)
      B            : A_j = Āg per group    (TV_B=tb, TV_W=0)
      W_inf(L/F/H) : A_j^* inflated, rest 1 (TV_B=0, TV_W=tw)
      V_inf(F)     : inflate + between     (TV_B=tb, TV_W=tw)
      W_def(F)     : A_j^* deflated, rest 1 (TV_B=0, TV_W=tw_F)

TV_W formula (§6.4):
  TV_W = Σ_g W_g × TV_{W,g}
  TV_{W,g} = 0.5 × Σ_{j∈G_g} |w_j^eff/W_g^eff − w_j/W_g|
  where w_j^eff = w_j × A_j / Σ_k w_k × A_k

TV_B formula:
  TV_B = Σ_g |W_g^eff − W_g|
  where W_g^eff = Σ_{j∈G_g} w_j^eff = (W_g × Ā_g) / Σ_h W_h × Ā_h

Note on calibration:
  TV_W is calibrated using the AHP reference weights (not per-draw).
  Per-draw TV_W will differ slightly (Dirichlet κ=200 ≈ AHP).
  This is declared as a design choice: PRESPEC_E6.md §2.6.

Usage:
  from e6_generate_amplitudes import build_amplitude_cells
  cells = build_amplitude_cells(W_AHP, OBJ_GROUPS, W_G, tw=0.199, tb=0.249)
  # cells: dict mapping cell_name -> A_j vector (length M)
"""

import numpy as np

__all__ = [
    "tvw_sec64",
    "tvb_sec64",
    "calibrate_inflate",
    "calibrate_deflate",
    "build_amplitude_cells",
]


def tvw_sec64(w, A, groups, W_G=None, eps=1e-12):
    """
    TV_W under the §6.4 formula.

    Parameters
    ----------
    w      : (M,) reference weights (AHP or draw)
    A      : (M,) amplitude vector
    groups : list of lists of criterion indices per group
    W_G    : (G,) group weight sums; if None, computed from w
    eps    : numerical floor to prevent division by zero

    Returns
    -------
    float : TV_W value in [0, 1)
    """
    wA = w * A
    total = wA.sum()
    if total < eps:
        return 0.0

    w_eff = wA / total                              # effective weights (M,)

    if W_G is None:
        W_G = np.array([w[g].sum() for g in groups])

    W_G_eff = np.array([w_eff[g].sum() for g in groups])  # (G,)

    tv_w = 0.0
    for g_idx, g in enumerate(groups):
        W_g     = W_G[g_idx]
        W_g_eff = W_G_eff[g_idx]
        if W_g < eps or W_g_eff < eps:
            continue
        for j in g:
            tv_w += abs(w_eff[j] / W_g_eff - w[j] / W_g)

    return 0.5 * tv_w


def tvb_sec64(w, A, groups, W_G=None, eps=1e-12):
    """
    TV_B: between-group total variation.

    TV_B = Σ_g |W_g^eff − W_g|

    Parameters and returns same convention as tvw_sec64.
    """
    wA = w * A
    total = wA.sum()
    if total < eps:
        return 0.0

    w_eff = wA / total
    if W_G is None:
        W_G = np.array([w[g].sum() for g in groups])

    W_G_eff = np.array([w_eff[g].sum() for g in groups])
    return float(np.abs(W_G_eff - W_G).sum())


def calibrate_inflate(w_ref, groups, W_G, tw, max_iter=60, tol=1e-7):
    """
    Find A_inflate such that TV_W(w_ref, A_inflate) = tw and TV_B = 0.

    Construction (guarantees TV_B = 0 exactly):
    - j*_g = argmax_{j in G_g} w_ref[j]
    - A_{j*_g} = 1 + Delta_g, A_{j != j*_g} = 1
    - Delta_g chosen so all groups have the same weighted mean amplitude:
        Abar_g = (sum_{j in G_g} w_ref[j] * A_j) / W_G[g]
               = 1 + w_ref[j*_g] * Delta_g / W_G[g]
      Setting Abar_g = Abar (same for all g) gives: Delta_g = (Abar-1) * W_G[g] / w_ref[j*_g]
    - Abar is calibrated via bisection to achieve TV_W = tw.
    - TV_B = 0 exactly because Abar_g is constant across groups.

    Returns
    -------
    A_inflate  : (M,) amplitude vector with TV_B = 0 and TV_W = tw
    tv_w_actual : float
    """
    M = len(w_ref)
    jstar_global = [g[int(np.argmax(w_ref[g]))] for g in groups]  # global index of j*_g

    def build_A(Abar):
        """Abar = target within-group mean amplitude (> 1 for inflate)."""
        A = np.ones(M)
        for g_idx, g in enumerate(groups):
            j_global = jstar_global[g_idx]
            Delta_g = (Abar - 1.0) * W_G[g_idx] / w_ref[j_global]
            A[j_global] = 1.0 + Delta_g
        return A

    def tv_w_for_Abar(Abar):
        return tvw_sec64(w_ref, build_A(Abar), groups, W_G)

    if tw < tol:
        return np.ones(M), 0.0

    # Find upper bracket
    Abar_hi = 1.1
    while tv_w_for_Abar(Abar_hi) < tw:
        Abar_hi = 1.0 + (Abar_hi - 1.0) * 2.0
        if Abar_hi > 50:
            A = build_A(Abar_hi)
            return A, tvw_sec64(w_ref, A, groups, W_G)

    # Bisection on Abar in (1, Abar_hi)
    Abar_lo = 1.0
    for _ in range(max_iter):
        Abar_mid = 0.5 * (Abar_lo + Abar_hi)
        tv_mid = tv_w_for_Abar(Abar_mid)
        if abs(tv_mid - tw) < tol:
            break
        if tv_mid < tw:
            Abar_lo = Abar_mid
        else:
            Abar_hi = Abar_mid

    A = build_A(0.5 * (Abar_lo + Abar_hi))
    return A, tvw_sec64(w_ref, A, groups, W_G)


def calibrate_deflate(w_ref, groups, W_G, tw, max_iter=60, tol=1e-7):
    """
    Find A_deflate such that TV_W(w_ref, A_deflate) = tw and TV_B = 0.

    Symmetric to calibrate_inflate: A_{j*_g} = 1 - Delta_g (Delta_g > 0).
    Delta_g = (1 - Abar) * W_G[g] / w_ref[j*_g], where Abar in (0, 1).

    Constraint: A_{j*_g} > 0 means Delta_g < 1 means Abar > 1 - W_G[g]/w_ref[j*_g].

    Returns
    -------
    A_deflate  : (M,) amplitude vector
    tv_w_actual : float
    feasible   : bool  False if maximum feasible TV_W < tw
    """
    M = len(w_ref)
    jstar_global = [g[int(np.argmax(w_ref[g]))] for g in groups]

    def build_A(Abar):
        """Abar = target within-group mean amplitude (< 1 for deflate)."""
        A = np.ones(M)
        for g_idx, g in enumerate(groups):
            j_global = jstar_global[g_idx]
            Delta_g = (1.0 - Abar) * W_G[g_idx] / w_ref[j_global]
            A[j_global] = max(0.0, 1.0 - Delta_g)
        return A

    def tv_w_for_Abar(Abar):
        return tvw_sec64(w_ref, build_A(Abar), groups, W_G)

    if tw < tol:
        return np.ones(M), 0.0, True

    # Minimum feasible Abar: A_{j*_g} = 0 → Abar_min_g = 1 - W_G[g]/w_ref[j*_g]
    Abar_floor = max(
        1.0 - W_G[g_idx] / w_ref[jstar_global[g_idx]]
        for g_idx in range(len(groups))
    )
    Abar_floor = max(Abar_floor, 0.0)

    tv_at_floor = tv_w_for_Abar(Abar_floor)
    if tv_at_floor < tw - tol:
        A = build_A(Abar_floor)
        return A, tv_w_for_Abar(Abar_floor), False

    # Bisection on Abar in (Abar_floor, 1)
    Abar_lo, Abar_hi = Abar_floor, 1.0
    for _ in range(max_iter):
        Abar_mid = 0.5 * (Abar_lo + Abar_hi)
        tv_mid = tv_w_for_Abar(Abar_mid)
        if abs(tv_mid - tw) < tol:
            break
        if tv_mid < tw:
            Abar_hi = Abar_mid
        else:
            Abar_lo = Abar_mid

    A = build_A(0.5 * (Abar_lo + Abar_hi))
    return A, tvw_sec64(w_ref, A, groups, W_G), True


def build_amplitude_cells(w_ref, groups, W_G,
                          tw_L=0.10, tw_F=0.199, tw_H=0.30, tb=0.249,
                          tol=1e-7):
    """
    Build A_j vectors for all 7 cells of PRESPEC_E6.

    Parameters
    ----------
    w_ref  : (M,) AHP reference weights
    groups : list of lists, criterion indices per objective group
    W_G    : (G,) group weight sums
    tw_L/F/H : TV_W targets (low / Fogo / high)
    tb     : TV_B target for cells B and V_inf(F)
    tol    : bisection tolerance

    Returns
    -------
    cells : dict with keys
        'M'          : A_j for cell M
        'B'          : A_j for cell B
        'W_inf_L'    : A_j for W_inf(tw=L)
        'W_inf_F'    : A_j for W_inf(tw=F)
        'W_inf_H'    : A_j for W_inf(tw=H)
        'V_inf_F'    : A_j for V_inf(tw=F, tb)
        'W_def_F'    : A_j for W_def(tw=F)

    tv_report : dict with measured (TV_W, TV_B) per cell
    warnings  : list of str for any calibration warnings
    """
    M = len(w_ref)
    cells = {}
    tv_report = {}
    warnings = []

    # ── Cell M (A_j = 1) ────────────────────────────────────────────────────
    cells['M'] = np.ones(M)
    tv_report['M'] = {'tv_w': 0.0, 'tv_b': 0.0}

    # ── Cell B (A_j = Āg, TV_W=0, TV_B=tb) ──────────────────────────────────
    # Find Āg values such that TV_B = tb using bisection on a scale factor s:
    #   Āg(s) = 1 + s * (target_g - 1)  where target_g encodes group-level deviation
    # For simplicity: inflate G1 and G3, deflate G2 (or vice versa) to achieve tb.
    # Simple approach: set Āg = 1 + r_g for each group, where r_g is chosen to match tb.
    # We use a one-parameter family: Āg = exp(s * sign_g) for signs = [+1, -1, +1].
    def build_B(s, signs=None):
        """A_j = Āg = exp(s * sign_g) for each group."""
        if signs is None:
            signs = np.array([1.0, -1.0, 1.0])  # G1 and G3 inflated, G2 deflated
        A = np.ones(M)
        for g_idx, g in enumerate(groups):
            Abar_g = np.exp(s * signs[g_idx])
            for j in g:
                A[j] = Abar_g
        return A

    def tvb_for_s(s):
        return tvb_sec64(w_ref, build_B(s), groups, W_G)

    if abs(tb) < tol:
        cells['B'] = np.ones(M)
        tv_report['B'] = {'tv_w': 0.0, 'tv_b': 0.0}
    else:
        # Bisect on s
        s_hi = 0.1
        while tvb_for_s(s_hi) < tb:
            s_hi *= 2.0
            if s_hi > 50:
                warnings.append(f"B cell: cannot reach TV_B={tb}; using max s={s_hi}")
                break
        s_lo = 0.0
        for _ in range(60):
            s_mid = 0.5 * (s_lo + s_hi)
            if abs(tvb_for_s(s_mid) - tb) < tol:
                break
            if tvb_for_s(s_mid) < tb:
                s_lo = s_mid
            else:
                s_hi = s_mid
        A_B = build_B(0.5 * (s_lo + s_hi))
        cells['B'] = A_B
        tv_report['B'] = {
            'tv_w': tvw_sec64(w_ref, A_B, groups, W_G),
            'tv_b': tvb_sec64(w_ref, A_B, groups, W_G),
        }
        if abs(tv_report['B']['tv_w']) > 1e-4:
            warnings.append(f"B cell: TV_W={tv_report['B']['tv_w']:.4f} != 0 (expected 0)")

    # ── Inflate cells ────────────────────────────────────────────────────────
    for cell_name, tw in [('W_inf_L', tw_L), ('W_inf_F', tw_F), ('W_inf_H', tw_H)]:
        A, tv_w_actual = calibrate_inflate(w_ref, groups, W_G, tw, tol=tol)
        cells[cell_name] = A
        tv_report[cell_name] = {
            'tv_w': tv_w_actual,
            'tv_b': tvb_sec64(w_ref, A, groups, W_G),
        }
        if abs(tv_w_actual - tw) > 0.005:
            warnings.append(
                f"{cell_name}: calibrated TV_W={tv_w_actual:.4f}, target={tw:.4f}"
            )
        A_max = A.max()
        if A_max > 3.0:
            warnings.append(
                f"{cell_name}: max amplitude A_j={A_max:.2f} > 3.0 (DEV-E6-002)"
            )

    # ── V_inf(F): between + within inflate ───────────────────────────────────
    # Combine B and W_inf(F): multiply element-wise, then re-normalise TV to (tb, tw_F)
    # Approach: Āg * inflate_factor_j
    A_W = cells['W_inf_F']
    A_B = cells['B']
    # V = Āg * (1 + delta_j_within), calibrated to (tv_b=tb, tv_w=tw_F) simultaneously.
    # Approximation: A_V = A_B * A_W (product of the two components).
    # The actual (TV_B, TV_W) may differ; we report them as actuals.
    A_V = A_B * A_W
    cells['V_inf_F'] = A_V
    tv_report['V_inf_F'] = {
        'tv_w': tvw_sec64(w_ref, A_V, groups, W_G),
        'tv_b': tvb_sec64(w_ref, A_V, groups, W_G),
    }
    if abs(tv_report['V_inf_F']['tv_w'] - tw_F) > 0.02:
        warnings.append(
            f"V_inf_F: TV_W={tv_report['V_inf_F']['tv_w']:.4f} != {tw_F:.4f}"
        )

    # ── W_def(F): deflate ────────────────────────────────────────────────────
    A_def, tv_w_def, feasible = calibrate_deflate(w_ref, groups, W_G, tw_F, tol=tol)
    cells['W_def_F'] = A_def
    tv_report['W_def_F'] = {
        'tv_w': tv_w_def,
        'tv_b': tvb_sec64(w_ref, A_def, groups, W_G),
    }
    if not feasible:
        warnings.append(
            f"W_def_F: tw={tw_F} not achievable without negative amplitudes (DEV-E6-001); "
            f"using max feasible TV_W={tv_w_def:.4f}"
        )
    if abs(tv_w_def - tw_F) > 0.005 and feasible:
        warnings.append(
            f"W_def_F: calibrated TV_W={tv_w_def:.4f}, target={tw_F:.4f}"
        )

    return cells, tv_report, warnings


if __name__ == "__main__":
    """Self-test: reproduce E1 amplitudes (TV_W=0.199, TV_B=0.249) as a check."""
    from fogo_constants import W, OBJ_GROUPS, W as W_AHP, TV_W_VEC, TV_B_VEC

    W_G = np.array([W[g].sum() for g in OBJ_GROUPS])

    cells, tv_report, warnings = build_amplitude_cells(
        w_ref=W_AHP,
        groups=OBJ_GROUPS,
        W_G=W_G,
        tw_L=0.10,
        tw_F=TV_W_VEC,
        tw_H=0.30,
        tb=TV_B_VEC,
    )

    print("=" * 55)
    print("E6 amplitude cells — self-test")
    print("=" * 55)
    print(f"Reference: TV_W(Fogo)={TV_W_VEC:.4f}, TV_B(Fogo)={TV_B_VEC:.4f}")
    print()
    for name, tvs in tv_report.items():
        print(f"  {name:12s}: TV_W={tvs['tv_w']:.4f}  TV_B={tvs['tv_b']:.4f}")
    print()
    if warnings:
        print("Warnings:")
        for w_str in warnings:
            print(f"  {w_str}")
    else:
        print("No warnings.")
    print()
    print("Cell M:", cells['M'])
    print("Cell W_inf_F A_j:", np.round(cells['W_inf_F'], 4))
    print("Cell W_def_F A_j:", np.round(cells['W_def_F'], 4))

    # Verify P1 conditions: M and B should have TV_W ≈ 0
    for cell_name in ('M', 'B'):
        tv_w = tv_report[cell_name]['tv_w']
        assert tv_w < 0.01, f"P1 pre-condition failed: {cell_name} TV_W={tv_w:.4f}"
    print("P1 pre-conditions OK: M and B have TV_W ~ 0.")
