# -*- coding: utf-8 -*-
"""
aspect_utils.py
================
Single source of truth for the geographic-azimuth transformation.

The CSV column 'slope_aspect (degrees)' stores the NOTEBOOK convention:
    theta_nb = (270 - theta_geo) % 360

where theta_geo is the geographic descent azimuth (0°=N, clockwise),
computed via arctan2(-dx, dy) on the Sobel gradient.

The correct geographic azimuth is:
    theta_geo = (270 - theta_nb) % 360

This transformation is validated by the cone test (scripts/_verify_amend3.py):
    mean cosine = 0.805 (geographic) vs -0.102 (notebook), n=389 admissible sites.
    Max circular |Δ| between DEM-recomputed and this transformation = 0.000107° < 1e-4°.

Usage
-----
Import this function wherever continuous aspect values are needed:
    from aspect_utils import aspect_geographic

NEVER read df[COL["aspect"]] directly and normalize without applying this function.
The check_consistency.py BAD_PHRASES list will flag any direct reads of
slope_aspect outside this module.
"""

import numpy as np
from pathlib import Path


MAX_CIRCULAR_DELTA_DEG = 2e-4   # validated oracle threshold: 1.07e-4 actual


def aspect_geographic(values_notebook: np.ndarray) -> np.ndarray:
    """Convert notebook-convention aspect values to geographic azimuth.

    The CSV column 'slope_aspect (degrees)' stores (270 - theta_geo) % 360.
    This function inverts that transformation.

    Parameters
    ----------
    values_notebook : np.ndarray
        Raw aspect values from df[COL["aspect"]], shape (N,), in degrees.

    Returns
    -------
    np.ndarray
        Geographic azimuth (0°=N, clockwise), shape (N,), in degrees [0, 360).

    Notes
    -----
    The binary SE-facing indicator b_asp = (90° <= theta_geo <= 180°) is
    invariant under this transformation, because the reflection axis 135°
    is the midpoint of [90°, 180°].  The 94 SE-facing sites are unchanged.
    """
    theta_nb = np.asarray(values_notebook, dtype=np.float64)
    return (270.0 - theta_nb) % 360.0


def normalize_continuous_aspect(df_via, df_imp, col_aspect: str) -> np.ndarray:
    """Return min-max normalized geographic azimuth for the 389 viable sites,
    using the 473-site range (for R-V style cells).

    Parameters
    ----------
    df_via : DataFrame  (n=389 admissible sites)
    df_imp : DataFrame  (n=473 all sites, reference range)
    col_aspect : str    column name for aspect in the dataframes

    Returns
    -------
    np.ndarray of shape (389,), values in [0, 1]
    """
    via_nb = df_via[col_aspect].values.astype(np.float64)
    imp_nb = df_imp[col_aspect].values.astype(np.float64)
    via_geo = aspect_geographic(via_nb)
    imp_geo = aspect_geographic(imp_nb)
    mn = imp_geo.min()
    rng = imp_geo.max() - mn or 1.0
    return (via_geo - mn) / rng


def normalize_continuous_aspect_389(df_via, col_aspect: str) -> np.ndarray:
    """Return min-max normalized geographic azimuth for the 389 viable sites,
    using the 389-site range (for R-asp style cells).

    Parameters
    ----------
    df_via : DataFrame  (n=389 admissible sites)
    col_aspect : str    column name for aspect in the dataframes

    Returns
    -------
    np.ndarray of shape (389,), values in [0, 1]
    """
    via_nb = df_via[col_aspect].values.astype(np.float64)
    via_geo = aspect_geographic(via_nb)
    mn = via_geo.min()
    rng = via_geo.max() - mn or 1.0
    return (via_geo - mn) / rng
