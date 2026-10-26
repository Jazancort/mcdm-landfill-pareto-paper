# DEPRECATED: replaced by santiago_grid.py --mode fogo-check
# Original used EPSG:4826 (Cape Verde Lambert) -> gives N=475, not 473.
# Corrected to EPSG:32626 before deprecation; documented in PRESPEC §3 PRE-A table.
# Kept for audit trail only. Do not use.

# -*- coding: utf-8 -*-
"""
_verify_fogo_grid.py
====================
Pre-commit validation for PRESPEC_SANTIAGO.md §3 (grid rule).

Tests whether the declared grid rule (1 km × 1 km, ≥ 50% land coverage)
applied to the Fogo island boundary reproduces the published candidate count
of 473. If not, records the discrepancy as DEV-S-001.

REQUIRES:
  - A GeoJSON or shapefile of the Fogo island boundary.
    Place at: 05-referencia/fogo_boundary.geojson
    Source: IDECV WFS carto_base:limites_ilha or OSM coastline + land polygon.
    CRS: EPSG:4326 (WGS84) or EPSG:4826 (UTM Zone 26N).

  - geopandas, shapely, numpy (install: uv pip install geopandas shapely numpy)

OUTPUTS:
  Prints N_Fogo and comparison with 473.
  If N_Fogo != 473: prints DEV-S-001 message to include in PRESPEC.

USAGE:
  uv run python scripts/_verify_fogo_grid.py
"""

import sys
import pathlib
import numpy as np

BOUNDARY_PATH = pathlib.Path(__file__).parent.parent / "05-referencia" / "fogo_boundary.geojson"
GRID_SIZE_KM = 1.0
MIN_LAND_COVERAGE = 0.50
PUBLISHED_N = 473

def main():
    if not BOUNDARY_PATH.exists():
        print(f"ERROR: boundary file not found: {BOUNDARY_PATH}")
        print("Download Fogo island boundary and place it at the path above.")
        print("Possible sources:")
        print("  IDECV WFS: https://geoservicos-ingt.gov.cv/geoserver/carto_base/wfs")
        print("  Layer: carto_base:limites_ilha (filter: ilha='Fogo')")
        print("  Or: OSM coastline polygon for Fogo")
        sys.exit(1)

    try:
        import geopandas as gpd
        from shapely.geometry import box, Point
    except ImportError:
        print("ERROR: geopandas and shapely are required.")
        print("Install: uv pip install geopandas shapely")
        sys.exit(1)

    print(f"Loading boundary from: {BOUNDARY_PATH}")
    boundary = gpd.read_file(BOUNDARY_PATH)
    print(f"  CRS: {boundary.crs}, features: {len(boundary)}")

    # CRS must match mcdm_experiment.py: EPSG:32626 (WGS 84 / UTM Zone 26N)
    # for Fogo (approximately 24.0-24.4 W), as declared in PRESPEC_SANTIAGO §3.
    # Using EPSG:4826 (Cape Verde Lambert) gives 475, not 473.
    boundary_proj = boundary.to_crs("EPSG:32626")
    print(f"  Reprojected to EPSG:32626 (UTM Zone 26N, per PRESPEC §3)")

    island = boundary_proj.geometry.union_all()
    grid_m = GRID_SIZE_KM * 1000.0
    cell_area = grid_m ** 2

    minx, miny, maxx, maxy = island.bounds
    xs = np.arange(minx, maxx, grid_m)
    ys = np.arange(miny, maxy, grid_m)

    print(f"Grid extent: {len(xs)} x {len(ys)} = {len(xs)*len(ys)} cells before filtering")

    candidates = []
    for x in xs:
        for y in ys:
            cell = box(x, y, x + grid_m, y + grid_m)
            inter = island.intersection(cell)
            if inter.is_empty:
                continue
            coverage = inter.area / cell_area
            if coverage >= MIN_LAND_COVERAGE:
                cx = x + grid_m / 2
                cy = y + grid_m / 2
                candidates.append((cx, cy))

    N_fogo = len(candidates)
    print(f"\nN_Fogo (grid rule: {GRID_SIZE_KM} km, coverage >= {MIN_LAND_COVERAGE:.0%}): {N_fogo}")
    print(f"Published N (paper):   {PUBLISHED_N}")

    if N_fogo == PUBLISHED_N:
        print("\nPASS: declared rule reproduces published dataset exactly.")
        print("No DEV-S-001 needed.")
    else:
        diff = N_fogo - PUBLISHED_N
        print(f"\nMISMATCH: difference = {diff:+d}")
        print("\nDEV-S-001 message to add to PRESPEC_SANTIAGO.md §3:")
        print(f'  "Declared rule (1 km, ≥50% land coverage) applied to Fogo island boundary')
        print(f'   [{BOUNDARY_PATH.name}] gives N = {N_fogo}; published dataset (Andrade 2015)')
        print(f'   has {PUBLISHED_N}. Difference unexplained; most likely due to a different')
        print(f'   island boundary shapefile used in the original pipeline. The declared rule')
        print(f'   is applied to Santiago unchanged."')

if __name__ == "__main__":
    main()

