# -*- coding: utf-8 -*-
"""
scoring.py  --  Shared SAW and TOPSIS scoring functions.

Single source of truth for saw_sc and topsis_sc.
All scripts that need per-draw portfolio selection must import from here.

Source: functions are canonical versions from mc_2cube_fixed.py.
Any change here must be reflected in mc_2cube_fixed.py and vice versa.

Usage:
    from scoring import make_scorers
    saw_sc, topsis_sc = make_scorers(X_via, X_adj, norms_via, benefit)

    sc = saw_sc(w, norm='minmax')   # or 'vector'
    sc = topsis_sc(w, norm='minmax')
"""
import numpy as np


def make_scorers(X_via, X_adj, norms_via, benefit):
    """
    Build scoring closures over the pre-computed matrices.

    Parameters
    ----------
    X_via     : (N, M) float64  -- raw decision matrix (not benefit-adjusted)
    X_adj     : (N, M) float64  -- benefit-adjusted (cost cols flipped to 1-x)
    norms_via : (M,) float64    -- column norms of X_via (not X_adj)
    benefit   : (M,) bool       -- True = benefit criterion

    Returns
    -------
    saw_sc, topsis_sc : callables (w, norm) -> (N,) scores
    """

    def saw_sc(w, norm="minmax"):
        """
        SAW score per site.

        min-max: weighted sum of benefit-adjusted values.
        vector : weighted sum of benefit-adjusted values divided by column norms
                 of the RAW matrix (consistent with wp3_mc_fixed).
        """
        if norm == "minmax":
            return (X_adj * w).sum(1)
        else:
            return ((X_adj / norms_via) * w).sum(1)

    def topsis_sc(w, norm="minmax"):
        """
        TOPSIS score per site.

        min-max: uses raw X_via directly.
        vector : uses X_via / norms_via (raw, NOT benefit-adjusted).

        PIS for benefit criteria = max; for cost = min.
        NIS for benefit criteria = min; for cost = max.
        Score = d_NIS / (d_PIS + d_NIS); higher = better.
        """
        Xb  = X_via if norm == "minmax" else X_via / norms_via
        V   = Xb * w
        PIS = np.where(benefit, V.max(0), V.min(0))
        NIS = np.where(benefit, V.min(0), V.max(0))
        dp  = np.sqrt(((V - PIS)**2).sum(1))
        dn  = np.sqrt(((V - NIS)**2).sum(1))
        return np.where(dp + dn == 0, 0.5, dn / (dp + dn))

    return saw_sc, topsis_sc
