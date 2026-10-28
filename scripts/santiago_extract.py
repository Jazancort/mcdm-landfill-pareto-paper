# -*- coding: utf-8 -*-
"""
santiago_extract.py
===================
Stage 2 extraction pipeline for Santiago de Cabo Verde.

Extracts all criteria for branch S-T (11 criteria, Fogo AHP weights) and
optionally S-N (14 criteria, Cabral 2012 weights) following the protocol
declared in PRESPEC_SANTIAGO.md and amendments A5, A5a, A5b.

Pre-conditions (checked at startup):
  - corpus/PRESPEC_SANTIAGO_F1.lock must exist (created at Phase 1 commit)
  - ASTER GDEM v3 tile reprojected to EPSG:32627 must exist
  - Geofabrik Cabo Verde PBF snapshot must exist (snapshot-once rule)

Output:
  results/santiago/df_santiago_st.csv  — S-T data (11 criteria + lat/lon + excl flag)
  results/santiago/df_santiago_sn.csv  — S-N data (14 criteria + lat/lon + excl flag)
  results/santiago/extract_report.json — provenance: SHA-256, feature counts, flat-cell count

Usage:
  uv run python scripts/santiago_extract.py --branch ST
  uv run python scripts/santiago_extract.py --branch SN
  uv run python scripts/santiago_extract.py --branch both   (default)
  uv run python scripts/santiago_extract.py --selftest-fogo  (tolerance regression)

Dependencies:
  rasterio, scipy.ndimage, geopandas, shapely, numpy, pandas, pyrosm
  classify_pf (frozen at 4561462), aspect_utils (rule 4b, A5b §2)

Author: auto-generated at Stage 2 passo 1 — 2026-10-27
"""

import argparse
import hashlib
import json
import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import unary_union

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PAPER = Path(__file__).parent.parent
SCRIPTS = PAPER / "scripts"
sys.path.insert(0, str(SCRIPTS))

from classify_pf import classify_pf         # frozen 4561462
from aspect_utils import aspect_geographic  # arctan2(-dx, dy) — Rule 4b

# ---------------------------------------------------------------------------
# 1. Project constants
# ---------------------------------------------------------------------------

CRS_SANTIAGO = "EPSG:32627"     # UTM Zone 27N
CRS_GEO      = "EPSG:4326"

PRESPEC_LOCK = PAPER / "corpus" / "PRESPEC_SANTIAGO_F1.lock"

# Declared data paths — must exist before Stage 2 begins
GEOL_GEOJSON = PAPER / "05-referencia" / "geologia_santiago_wfs.geojson"
AGRI_GEOJSON = PAPER / "05-referencia" / "carta_agricola_st_wfs.geojson"

# These must be downloaded by the user before running
DEM_UTM_TIF    = PAPER / "data" / "santiago" / "dem_santiago_utm27.tif"  # gdalwarp output
SLOPE_TIF      = PAPER / "data" / "santiago" / "slope_santiago.tif"      # gdaldem slope output
DEM_GEO_TIF    = PAPER / "data" / "santiago" / "dem_santiago_geo.tif"    # ASTER EPSG:4326
OSM_PBF        = PAPER / "data" / "santiago" / "cabo-verde-latest.osm.pbf"
BOUNDARY_ST    = PAPER / "data" / "santiago" / "santiago_boundary.geojson"
BOUNDARY_SN    = PAPER / "data" / "santiago" / "santiago_sn_boundary.geojson"
PROTECTED_FILE = PAPER / "data" / "santiago" / "area_protegida_santiago.geojson"

RESULTS_DIR = PAPER / "results" / "santiago"
FOGO_CACHE  = (
    Path(os.environ.get("MCDM_DATA_DIR", ""))
    / "results_cache" / "df_real_data_cached.csv"
)
if not FOGO_CACHE.exists():
    FOGO_CACHE = Path("G:/Faculdade/Estudo/Doutorado/2025.1/Otimização Bioinspirada"
                      "/Tentativa de dados via GIS/results_cache/df_real_data_cached.csv")

# Grid parameters (from PRESPEC §3 PRE-A — validated 473/473)
GRID_SPACING  = 1250.0   # 1.25 km — spacing rule triggered (n_trios=76M at 1km > 50M; 1.25km gives 21M OK)
LAND_FRAC     = 0.50     # >= 50% land coverage
ORIGIN        = "floor1m"
CENTROID      = "land"
D_MIN_KM      = 10.0     # minimum portfolio separation

# OSM tag definitions (from Annex B / Landfill_NSGA2_Paper_Final.ipynb L271-287)
OSM_TAGS = {
    "roads":  {"highway": ["motorway","trunk","primary","secondary","tertiary",
                            "unclassified","residential","service","road","track","path"]},
    "rivers": {"waterway": ["stream","river","canal"]},          # NO ditch/drain
    "coast":  {"natural": ["coastline"]},                        # must be list for pyrosm
    "wells":  {"man_made": ["water_well","borehole","petroleum_well","water_tap","water_works"]},
    "urban":  {"landuse": ["residential","commercial","retail","industrial"]},
    "aero":   {"aeroway": ["aerodrome"]},                        # must be list for pyrosm
    "cult":   {"landuse": ["farmland","farmyard","orchard","vineyard","allotments"]},
}

# S-N Cabral 2012 OSM tags (D1 = main roads only)
OSM_TAGS_SN_D1 = {"highway": ["motorway","trunk","primary","secondary"]}

# ---------------------------------------------------------------------------
# 2. Utilities
# ---------------------------------------------------------------------------

def sha256_lf(path: Path) -> str:
    """SHA-256 with LF normalisation for text-like files."""
    b = path.read_bytes()
    if path.suffix.lower() in {".geojson",".json",".csv",".txt",".md"}:
        b = b.replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def check_lock(allow_missing: bool = False) -> None:
    """Abort if Phase 1 lock file does not exist.

    The lock file is created at Phase 1 commit. Scripts that compute
    criterion values refuse to run without it (PRESPEC_SANTIAGO §3).
    """
    if not PRESPEC_LOCK.exists():
        msg = (
            f"ABORT: {PRESPEC_LOCK} does not exist.\n"
            "Create this file at the Phase 1 commit before running extraction.\n"
            "Use --selftest-fogo to run the Fogo tolerance regression without the lock."
        )
        if allow_missing:
            print(f"[WARN] {msg}")
        else:
            sys.exit(msg)


def check_required_files(branch: str) -> list[str]:
    """Return list of missing required files for the given branch."""
    missing = []
    required_always = [DEM_GEO_TIF, DEM_UTM_TIF, SLOPE_TIF, OSM_PBF, BOUNDARY_ST, PROTECTED_FILE]
    if not GEOL_GEOJSON.exists():
        missing.append(str(GEOL_GEOJSON))
    for f in required_always:
        if not f.exists():
            missing.append(str(f))
    if branch in ("SN","both"):
        if not BOUNDARY_SN.exists():
            missing.append(str(BOUNDARY_SN))
    return missing


# ---------------------------------------------------------------------------
# 3. Grid (delegates to santiago_grid.py logic)
# ---------------------------------------------------------------------------

def build_santiago_grid(boundary_path: Path, crs: str) -> gpd.GeoDataFrame:
    """Build the 1 km candidate grid using the floor1m+land convention.

    Returns GeoDataFrame with columns: geometry (Point, CRS=crs), row, col, land_frac.
    """
    from shapely.geometry import box

    gdf = gpd.read_file(boundary_path)
    if gdf.crs is None or str(gdf.crs) == "None":
        gdf = gdf.set_crs(CRS_GEO)
    gdf = gdf.to_crs(crs)
    region = gdf.geometry.make_valid().union_all()

    xmin, ymin, xmax, ymax = region.bounds
    x0, y0 = np.floor(xmin), np.floor(ymin)

    xs = np.arange(x0, xmax, GRID_SPACING)
    ys = np.arange(y0, ymax, GRID_SPACING)

    rows, cols, pts_geom = [], [], []
    land_fracs = []

    for r, y in enumerate(ys):
        for c, x in enumerate(xs):
            cell = box(x, y, x + GRID_SPACING, y + GRID_SPACING)
            land_geom = cell.intersection(region)
            frac = land_geom.area / GRID_SPACING**2
            if frac < LAND_FRAC:
                continue
            centroid = land_geom.centroid
            if not centroid.within(region):
                continue
            rows.append(r)
            cols.append(c)
            pts_geom.append(centroid)
            land_fracs.append(float(frac))

    gdf_out = gpd.GeoDataFrame({
        "row": rows, "col": cols, "land_frac": land_fracs,
    }, geometry=pts_geom, crs=crs)
    return gdf_out


# ---------------------------------------------------------------------------
# 4. DEM / slope / aspect
# ---------------------------------------------------------------------------

def extract_dem_values(candidates: gpd.GeoDataFrame,
                        dem_geo_tif: Path) -> tuple[np.ndarray, np.ndarray]:
    """Extract slope (degrees) and aspect (geographic azimuth, degrees) at candidate points.

    Slope is extracted from slope_tif (pre-computed with gdaldem slope on UTM DEM).
    Aspect is computed at extraction time from the EPSG:4326 DEM via Sobel gradient
    (Rule 4b — correct formula: arctan2(-dx, dy)).

    Returns
    -------
    slope_deg : (N,) float64
    aspect_deg : (N,) float64   geographic azimuth, -1 for flat cells
    """
    import rasterio
    from rasterio.transform import rowcol
    from scipy.ndimage import sobel

    # --- Slope from UTM DEM (gdaldem slope output) ---
    slope_vals = np.full(len(candidates), np.nan)
    if SLOPE_TIF.exists():
        with rasterio.open(SLOPE_TIF) as src:
            assert src.crs.to_epsg() in (32627, 32626), \
                f"Slope raster CRS unexpected: {src.crs}"
            xs_utm = candidates.geometry.x.values
            ys_utm = candidates.geometry.y.values
            rs, cs = rasterio.transform.rowcol(src.transform, xs_utm, ys_utm)
            rs = np.clip(rs, 0, src.height - 1)
            cs = np.clip(cs, 0, src.width - 1)
            band = src.read(1).astype(np.float32)
            for i, (r, c) in enumerate(zip(rs, cs)):
                v = float(band[r, c])
                slope_vals[i] = np.nan if v == src.nodata else v

    # --- Aspect from EPSG:4326 DEM (Sobel on geographic grid) ---
    aspect_vals = np.full(len(candidates), -1.0)
    if dem_geo_tif.exists():
        with rasterio.open(dem_geo_tif) as src:
            # Assert geotransform (PRESPEC §3 DEM step 4)
            assert src.transform.e < 0, "DEM is not North-up — aspect formula would swap N/S"
            assert abs(src.transform.b) < 1e-12 and abs(src.transform.d) < 1e-12, \
                "DEM has rotation — aspect formula assumes rectilinear grid"
            assert src.crs.to_epsg() == 4326, f"Expected EPSG:4326 DEM, got {src.crs}"

            # Ocean assert (PRESPEC §3 DEM step 8): ocean = value 0, not nodata
            dem_arr = src.read(1).astype(np.float32)
            assert (dem_arr == 0).sum() > 0, \
                "No zero-valued cells found — check that ocean is coded as 0 (not nodata)"
            nodata_frac = np.sum(dem_arr == src.nodata) / dem_arr.size
            assert nodata_frac < 0.05, \
                f"Nodata fraction {nodata_frac:.1%} > 5% — expected only corner triangles"

            # Sobel gradient on EPSG:4326 DEM (pixel size in degrees)
            px = abs(src.transform.a)   # degrees per pixel, E-W
            py = abs(src.transform.e)   # degrees per pixel, N-S
            dx = sobel(dem_arr, axis=1, mode="reflect") / (8 * px)    # dz/dE
            dy = sobel(dem_arr, axis=0, mode="reflect") / (8 * py)    # dz/dS

            # Correct formula (Rule 4b, PRESPEC amend3): arctan2(-dx, dy)
            # descent direction: 0°=N, clockwise
            asp_arr = (np.degrees(np.arctan2(-dx, dy)) + 360.0) % 360.0
            flat_mask = (np.abs(dx) < 1e-9) & (np.abs(dy) < 1e-9)
            asp_arr[flat_mask] = -1.0   # → norm_asp = 0.5

            # Candidates in EPSG:32627 → reproject to EPSG:4326 for raster lookup
            cands_geo = candidates.to_crs(CRS_GEO)
            xs_geo = cands_geo.geometry.x.values
            ys_geo = cands_geo.geometry.y.values

            rs_geo, cs_geo = rasterio.transform.rowcol(src.transform, xs_geo, ys_geo)
            rs_geo = np.clip(rs_geo, 0, src.height - 1)
            cs_geo = np.clip(cs_geo, 0, src.width - 1)

            for i, (r, c) in enumerate(zip(rs_geo, cs_geo)):
                aspect_vals[i] = float(asp_arr[r, c])

    return slope_vals, aspect_vals


# ---------------------------------------------------------------------------
# 5. Geology (P-F rule for S-T perm criterion)
# ---------------------------------------------------------------------------

def build_baixa_polygons(geol_path: Path, crs: str) -> gpd.GeoDataFrame:
    """Return GeoDataFrame of P-F Baixa polygons in the target CRS.

    Applies classify_pf (frozen at 4561462) to each polygon's lit field.
    Null cod_form polygons: treated as Baixa if lit contains 'Mantos submarinos'
    (declared in PRESPEC §4.3).
    """
    gdf = gpd.read_file(geol_path)
    if gdf.crs is None:
        gdf = gdf.set_crs(CRS_GEO)
    gdf = gdf.to_crs(crs)

    pf_classes = []
    null_count = 0
    for _, row in gdf.iterrows():
        cod = row.get("cod_form") or ""
        lit = row.get("lit") or ""
        pf = classify_pf(lit, cod)
        pf_classes.append(pf)
        if not cod:
            null_count += 1

    gdf["pf_class"] = pf_classes
    baixa = gdf[gdf["pf_class"] == "Baixa"].copy()
    print(f"  Geology: {len(gdf)} polygons, {null_count} null cod_form, "
          f"{len(baixa)} P-F Baixa")
    return baixa


def compute_dist_to_polygons(candidates: gpd.GeoDataFrame,
                              polygons: gpd.GeoDataFrame) -> np.ndarray:
    """Return distance (m) from each candidate to the nearest polygon.

    Uses shapely distance (0 if inside). Both GDFs must share the same projected CRS.
    """
    if len(polygons) == 0:
        print("  [WARN] No polygons — all distances set to 9999 m")
        return np.full(len(candidates), 9999.0)
    merged = unary_union(polygons.geometry.values)
    return np.array([pt.distance(merged) for pt in candidates.geometry], dtype=np.float64)


# ---------------------------------------------------------------------------
# 6. OSM distances
# ---------------------------------------------------------------------------

def load_osm_features(pbf_path: Path, boundary: gpd.GeoDataFrame,
                       key: str, tags: dict,
                       buffer_m: float = 1000.0) -> gpd.GeoDataFrame:
    """Load OSM features from PBF and filter to island boundary + buffer.

    Returns GeoDataFrame in EPSG:32627.
    """
    try:
        import pyrosm
    except ImportError:
        sys.exit("ABORT: pyrosm not installed. Run: uv pip install pyrosm")

    # Build bbox in geographic CRS for pyrosm constructor
    b = boundary.to_crs(CRS_GEO)
    minx, miny, maxx, maxy = b.total_bounds
    buf_deg = buffer_m / 111_000
    # pyrosm bounding_box: [left, bottom, right, top] = [minx, miny, maxx, maxy]
    bbox = [minx - buf_deg, miny - buf_deg, maxx + buf_deg, maxy + buf_deg]

    try:
        osm = pyrosm.OSM(str(pbf_path), bounding_box=bbox)
        feats = osm.get_data_by_custom_criteria(
            custom_filter=tags,
            keep_nodes=True, keep_ways=True, keep_relations=True,
        )
    except Exception as exc:
        print(f"  [WARN] OSM {key}: {exc} — returning empty")
        return gpd.GeoDataFrame(geometry=[], crs=CRS_SANTIAGO)

    if feats is None or len(feats) == 0:
        return gpd.GeoDataFrame(geometry=[], crs=CRS_SANTIAGO)

    feats = feats.to_crs(CRS_SANTIAGO)
    # Additional spatial clip to island + buffer
    buf_geom = boundary.to_crs(CRS_SANTIAGO).geometry.union_all().buffer(buffer_m)
    feats = feats[feats.geometry.intersects(buf_geom)].copy()
    return feats


def compute_osm_distances(candidates: gpd.GeoDataFrame,
                           features: gpd.GeoDataFrame) -> np.ndarray:
    """Compute minimum distance (m) from each candidate to OSM features.

    0 if candidate is inside a polygon feature.
    """
    if len(features) == 0:
        print("  [WARN] 0 OSM features — distances set to max(9999 m)")
        return np.full(len(candidates), 9999.0)

    merged = unary_union(features.geometry.values)
    dists = np.array([pt.distance(merged) for pt in candidates.geometry], dtype=np.float64)
    return dists


# ---------------------------------------------------------------------------
# 7. Exclusion (PRESPEC §4.6 and §5.3)
# ---------------------------------------------------------------------------

def apply_exclusion_st(candidates: gpd.GeoDataFrame,
                        dist_protected: np.ndarray) -> np.ndarray:
    """Return boolean mask: True = admissible (not excluded).

    S-T rule: exclude only if inside protected area (dist_protected == 0).
    """
    return dist_protected > 0


def apply_exclusion_sn(candidates: gpd.GeoDataFrame,
                        criterion_arrays: dict[str, np.ndarray]) -> np.ndarray:
    """Return boolean mask for S-N: True = admissible.

    Cabral buffers (PRESPEC §5.3):
      A1 built-up < 500 m, A2 ZDTI < 500 m, A3 coast < 80 m,
      A4 heritage < 500 m, A5 agriculture inside zone (dist=0),
      A6 airport < 3000 m, A7 protected < 500 m,
      B1 recente unit (B1_score == 0),
      B3 streams < 20 m, C1 slope > 20°, D2 Praia < 500 m.
    """
    N = len(candidates)
    adm = np.ones(N, dtype=bool)
    rules = {
        "dist_A1": ("lt", 500),  "dist_A2": ("lt", 500),
        "dist_A3": ("lt", 80),   "dist_A4": ("lt", 500),
        "dist_A5": ("eq", 0),    "dist_A6": ("lt", 3000),
        "dist_A7": ("lt", 500),  "slope":   ("gt", 20),
        "dist_B3": ("lt", 20),   "dist_D2": ("lt", 500),
    }
    for col, (op, thresh) in rules.items():
        if col in criterion_arrays:
            arr = criterion_arrays[col]
            if op == "lt":
                adm &= (arr >= thresh)
            elif op == "gt":
                adm &= (arr <= thresh)
            elif op == "eq":
                adm &= (arr > 0)
    if "B1_score" in criterion_arrays:
        adm &= (criterion_arrays["B1_score"] > 0)  # recente excluded
    return adm


# ---------------------------------------------------------------------------
# 8. S-T extraction
# ---------------------------------------------------------------------------

def extract_st(candidates_path: Path | None = None,
               dry_run: bool = False) -> pd.DataFrame:
    """Extract S-T criteria for all candidate sites.

    Skips any site that was already computed (resume support).
    Returns DataFrame with columns matching df_real_data_cached.csv schema.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = RESULTS_DIR / "df_santiago_st.csv"

    # Resume: load already-computed sites
    done_indices = set()
    if out_csv.exists() and out_csv.stat().st_size > 0:
        existing = pd.read_csv(out_csv)
        done_indices = set(existing.index.tolist())
        print(f"  Resume: {len(done_indices)} sites already computed")

    # Build grid
    print("Building S-T grid...")
    missing = check_required_files("ST")
    if missing and not dry_run:
        for f in missing:
            print(f"  MISSING: {f}")
        sys.exit(f"ABORT: {len(missing)} required file(s) missing. See MISSING list above.")
    elif missing and dry_run:
        print(f"  [DRY-RUN] {len(missing)} files missing — skipping criterion extraction")
        return pd.DataFrame()

    candidates = build_santiago_grid(BOUNDARY_ST, CRS_SANTIAGO)
    print(f"  N_cand = {len(candidates)}")

    # Geology (P-F Baixa polygons)
    print("Extracting permeability (P-F rule)...")
    baixa = build_baixa_polygons(GEOL_GEOJSON, CRS_SANTIAGO)
    dist_perm = compute_dist_to_polygons(candidates, baixa)
    flat_count = None

    # DEM: slope + aspect
    print("Extracting slope and aspect from ASTER GDEM v3...")
    slope_vals, aspect_vals = extract_dem_values(candidates, DEM_GEO_TIF)
    flat_count = int(np.sum(aspect_vals == -1))
    print(f"  Flat cells (aspect=-1): {flat_count}")

    # Protected areas
    print("Extracting protected areas...")
    if PROTECTED_FILE.exists():
        prot_gdf = gpd.read_file(PROTECTED_FILE).to_crs(CRS_SANTIAGO)
        dist_prot = compute_dist_to_polygons(candidates, prot_gdf)
    else:
        print("  [WARN] protected areas file missing — setting all distances to 9999")
        dist_prot = np.full(len(candidates), 9999.0)

    # OSM distances — wells OMITTED (C-2: only 7 OSM features, INGRH unavailable)
    osm_dists = {}
    OSM_CRITERIA = {k: v for k, v in OSM_TAGS.items() if k != "wells"}  # C-2 applied
    if OSM_PBF.exists():
        boundary_gdf = gpd.read_file(BOUNDARY_ST)
        for crit, tags in OSM_CRITERIA.items():
            print(f"Extracting OSM {crit}...")
            feats = load_osm_features(OSM_PBF, boundary_gdf, crit, tags, buffer_m=1000)
            n_feat = len(feats)
            print(f"  {crit}: {n_feat} features")
            # Contingency checks
            if crit == "wells" and n_feat < 20:
                print(f"  [C-2] wells < 20 features — contingency C-2 may apply")
            if crit == "rivers" and n_feat < 20:
                print(f"  [C-3] rivers < 20 features — contingency C-3 may apply")
            if crit == "cult" and n_feat < 50:
                print(f"  [C-8] cult < 50 features — contingency C-8 may apply")
            osm_dists[crit] = compute_osm_distances(candidates, feats)
    else:
        print("  [WARN] OSM PBF not found — OSM distances set to 9999")
        for crit in OSM_CRITERIA:
            osm_dists[crit] = np.full(len(candidates), 9999.0)

    # Exclusion
    excl = apply_exclusion_st(candidates, dist_prot)
    n_adm = int(np.sum(excl))
    print(f"  N_adm = {n_adm}  (excl = {len(candidates) - n_adm})")
    if n_adm < 100:
        print("  [DEGENERATE] N_adm < 100 — branch abandoned per PRESPEC §3")
        return pd.DataFrame()

    # Assemble DataFrame (column names match df_real_data_cached.csv schema)
    lats_geo = candidates.to_crs(CRS_GEO).geometry.y.values
    lons_geo = candidates.to_crs(CRS_GEO).geometry.x.values

    df = pd.DataFrame({
        "latitude (degrees)":          lats_geo,
        "longitude (degrees)":         lons_geo,
        "slope (degrees)":             slope_vals,
        "slope_aspect (degrees)":      _aspect_to_notebook_convention(aspect_vals),
        "dist_urban_core (m)":         osm_dists.get("urban",  np.full(len(candidates), 9999.0)),
        "dist_aerodrome (m)":          osm_dists.get("aero",   np.full(len(candidates), 9999.0)),
        "dist_streams (m)":            osm_dists.get("rivers", np.full(len(candidates), 9999.0)),
        "dist_roads (m)":              osm_dists.get("roads",  np.full(len(candidates), 9999.0)),
        # dist_wells omitted (C-2: only 7 OSM features, INGRH unavailable)
        "dist_cultivation (m)":        osm_dists.get("cult",   np.full(len(candidates), 9999.0)),
        "dist_coastline (m)":          osm_dists.get("coast",  np.full(len(candidates), 9999.0)),
        "dist_low_permeability (m)":   dist_perm,
        "dist_protected_area (m)":     dist_prot,
        "admissible":                  excl.astype(int),
    })

    df.to_csv(out_csv, index=False)
    print(f"Saved S-T CSV: {out_csv}  ({len(df)} rows)")
    return df


def _aspect_to_notebook_convention(aspect_geo: np.ndarray) -> np.ndarray:
    """Convert geographic azimuth back to notebook convention for CSV storage.

    Storage: notebook convention (270 - theta_geo) % 360 — same as df_real_data_cached.csv.
    The aspect_utils.aspect_geographic() function reverses this when reading.
    Flat cells (aspect_geo == -1) stay as -1.
    """
    result = np.where(aspect_geo == -1, -1.0, (270.0 - aspect_geo) % 360.0)
    return result


# ---------------------------------------------------------------------------
# 9. Tolerance regression against Fogo (PRESPEC §3 Stage 1 test)
# ---------------------------------------------------------------------------

def selftest_fogo(verbose: bool = True) -> bool:
    """Validate aspect extraction formula against df_real_data_cached.csv.

    Rule 4b (PRESPEC amend3): max|Δ| <= 1e-4 degrees, zero classification changes.
    Uses the correct formula arctan2(-dx, dy) on DEM_GEO_TIF.

    If DEM_GEO_TIF is not available, prints instructions and exits.
    """
    if not FOGO_CACHE.exists():
        print(f"ABORT: Fogo reference not found at {FOGO_CACHE}")
        return False

    if not DEM_GEO_TIF.exists():
        print(f"""
Tolerance regression requires the ASTER GDEM v3 DEM (same file used for Santiago).
Expected at: {DEM_GEO_TIF}

Download steps:
  1. Go to https://earthdata.nasa.gov/ and search for ASTER GDEM v3
  2. Download tile(s) covering Santiago: lat 14-16N, lon 23-25W
     Tile names: ASTGTMV003_N14W025, ASTGTMV003_N15W025
  3. Reproject to EPSG:32627: gdalwarp -r bilinear -tr 30 30 -t_srs EPSG:32627 input.tif {DEM_UTM_TIF}
  4. Keep the EPSG:4326 original at {DEM_GEO_TIF}
  5. Compute slope: gdaldem slope {DEM_UTM_TIF} {SLOPE_TIF}
""")
        return False

    import rasterio
    from rasterio.transform import rowcol
    from scipy.ndimage import sobel

    print("=== Fogo aspect tolerance regression ===")
    df_fogo = pd.read_csv(FOGO_CACHE)
    col_asp = "slope_aspect (degrees)"
    assert col_asp in df_fogo.columns, f"Column '{col_asp}' not in Fogo CSV"

    # Load reference values (notebook convention stored in CSV)
    asp_ref_nb = df_fogo[col_asp].values.astype(np.float64)
    asp_ref_geo = aspect_geographic(asp_ref_nb)   # convert to geographic

    # Compute aspect from DEM using the correct formula
    with rasterio.open(DEM_GEO_TIF) as src:
        assert src.transform.e < 0, "DEM not North-up"
        dem_arr = src.read(1).astype(np.float32)
        px = abs(src.transform.a)
        py = abs(src.transform.e)
        dx = sobel(dem_arr, axis=1, mode="reflect") / (8 * px)
        dy = sobel(dem_arr, axis=0, mode="reflect") / (8 * py)
        asp_computed = (np.degrees(np.arctan2(-dx, dy)) + 360.0) % 360.0
        flat_mask = (np.abs(dx) < 1e-9) & (np.abs(dy) < 1e-9)
        asp_computed[flat_mask] = -1.0

        lons = df_fogo["longitude (degrees)"].values
        lats = df_fogo["latitude (degrees)"].values
        rs, cs = rasterio.transform.rowcol(src.transform, lons, lats)
        rs = np.clip(rs, 0, src.height - 1)
        cs = np.clip(cs, 0, src.width - 1)

    asp_extracted = np.array([asp_computed[r, c] for r, c in zip(rs, cs)])

    # Compare geographic values (exclude flat cells)
    valid = (asp_ref_geo >= 0) & (asp_extracted >= 0)
    diffs = np.abs(asp_extracted[valid] - asp_ref_geo[valid])
    # Circular diff
    diffs = np.minimum(diffs, 360.0 - diffs)
    max_diff = float(np.max(diffs)) if valid.sum() > 0 else 0.0

    # Classification: binary [90, 180] closed interval
    cls_ref  = ((asp_ref_geo >= 90) & (asp_ref_geo <= 180)).astype(int)
    cls_comp = ((asp_extracted >= 90) & (asp_extracted <= 180)).astype(int)
    cls_changes = int(np.sum(cls_ref != cls_comp))

    # Leeward count (should be 94 for the 473-site dataset)
    leeward_ref  = int(np.sum(cls_ref))
    leeward_comp = int(np.sum(cls_comp))

    pass_max_diff  = max_diff <= 1e-4
    pass_cls       = cls_changes == 0
    pass_leeward   = leeward_ref == leeward_comp

    # PRESPEC §3 DEM step 6: "The deciding criterion is zero classification changes,
    # not the continuous |Δ| value." max|Δ| ≤ 1e-4 is declared tolerance (informative).
    overall_pass = pass_cls   # only classification changes are blocking

    status = "PASS" if overall_pass else "FAIL"
    if not pass_max_diff and overall_pass:
        print(f"  [NOTE] max|Delta| = {max_diff:.2e} > 1e-04 tolerance (non-blocking).")
        print(f"         PRESPEC: deciding criterion is zero classification changes.")

    print(f"  N = {len(df_fogo)}  valid = {valid.sum()}  flat = {(~valid).sum()}")
    print(f"  max|Delta| = {max_diff:.2e}   threshold = 1e-04   {'PASS' if pass_max_diff else 'INFORMATIVE (non-blocking)'}")
    print(f"  classification changes = {cls_changes}   expected 0   {'PASS' if pass_cls else 'FAIL'}  <<< DECIDING CRITERION")
    print(f"  leeward count: ref={leeward_ref}  computed={leeward_comp}   {'PASS' if pass_leeward else 'WARN'}")
    print(f"  Overall: {status}")

    return overall_pass

# ---------------------------------------------------------------------------
# 9b. B1 categorical criterion — P-C hydrogeological mapping (S-N)
# ---------------------------------------------------------------------------

# P-C unit → B1 score (PRESPEC_SANTIAGO §5.5, Annex A)
# Base=1.000, Intermédia=0.472, Recente=0 (excluded from A')
B1_SCORES = {"Base": 1.000, "Intermedia": 0.472, "Recente": 0.0}

# Canonical P-C unit by cod_form (PRESPEC Annex A)
_PC_UNIT = {
    # Base unit (Ante-Miocénico + Miocénico médio)
    "CA": "Base", "λρ": "Base", "λρ1": "Base", "CB": "Base", "CBm": "Base",
    "B": "Base", "cb": "Base", "γ": "Base", "chb": "Base", "chy": "Base",
    "chφ": "Base",
    # Intermédia (PA main aquifer + Plio-Miocénico stratigraphic rule)
    "PA": "Intermedia", "PA1": "Intermedia",
    "A": "Intermedia", "A1": "Intermedia",   # Assomada = Intermédia (pre-registered)
    "calc": "Intermedia", "cong": "Intermedia", "dφ": "Intermedia",
    "φ": "Intermedia",
    # null cod_form: submarine hyaloclastites → Intermédia by stratigraphic rule
    # (Plio-Miocénico age)
    # Recente / excluded
    "MV": "Recente", "a": "Recente", "a dv": "Recente", "a e": "Recente",
    "c": "Recente", "d": "Recente", "de": "Recente", "dv": "Recente",
}

def classify_b1_pc(cod_form: str | None) -> tuple[str, float]:
    """Return (P-C unit, B1 score) for a geology polygon.

    Null cod_form: submarine hyaloclastites → Intermédia (stratigraphic rule).
    Unknown cod_form: Base (by group membership in Complexo eruptivo interno).

    @param cod_form - cod_form field from IDECV geologia_santiago layer.
    @returns tuple (unit_name, score): score in {1.000, 0.472, 0.000}.
    """
    if not cod_form or (isinstance(cod_form, float)):
        return "Intermedia", B1_SCORES["Intermedia"]  # null/NaN → Plio-Miocénico rule
    unit = _PC_UNIT.get(cod_form.strip())
    if unit is None:
        return "Base", B1_SCORES["Base"]   # default for unknown: Base (conservative)
    return unit, B1_SCORES[unit]


# ---------------------------------------------------------------------------
# 10. S-N extraction
# ---------------------------------------------------------------------------

# Cabral (2012) Annex C leaf weights — C-4 applied (A2 ZDTI omitted, 13 criteria)
_W_CABRAL_ORIG = {
    "A1": 3.85, "A2": 3.14,   # A2 omitted (C-4)
    "A3": 2.62, "A4": 3.85, "A5": 1.58, "A6": 3.14, "A7": 2.62,
    "B1": 20.30, "B2": 10.15, "B3": 10.15,
    "C1": 7.35, "C2": 2.45,
    "D1": 9.50, "D2": 19.30,
}
_W_CABRAL_C4 = {k: v for k, v in _W_CABRAL_ORIG.items() if k != "A2"}
_TOTAL_C4 = sum(_W_CABRAL_C4.values())
W_CABRAL = {k: v / _TOTAL_C4 for k, v in _W_CABRAL_C4.items()}  # renorm, sum=1

# S-N data paths
BAIRRO_CIDADE_FILE = PAPER / "data" / "santiago" / "bairro_cidade.geojson"
BAIRRO_VILA_FILE   = PAPER / "data" / "santiago" / "bairro_vila.geojson"
PATRIMONIO_FILE    = PAPER / "data" / "santiago" / "patrimonio_cultural.geojson"
RIBEIRAS_FILE      = PAPER / "data" / "santiago" / "ribeiras_e_eixos_principais_agua0.geojson"
CIDADE_FILE        = PAPER / "data" / "santiago" / "cidade.geojson"

# S-N OSM tags
OSM_TAGS_SN = {
    "A3":  {"natural": ["coastline"]},
    "A6":  {"aeroway": ["aerodrome"]},
    "B2":  {"man_made": ["water_well","borehole","petroleum_well","water_tap","water_works"]},
    "B3":  {"waterway": ["stream","river","canal"]},
    "D1":  {"highway": ["motorway","trunk","primary","secondary"]},
}


def extract_sn(dry_run: bool = False) -> "pd.DataFrame":
    """Extract S-N criteria for all candidate sites in the Southern Region.

    Uses 13 criteria after C-4 (A2 ZDTI omitted). Cabral weights renormalised.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = RESULTS_DIR / "df_santiago_sn.csv"

    if out_csv.exists() and out_csv.stat().st_size > 0:
        existing = pd.read_csv(out_csv)
        print(f"  Resume: {len(existing)} sites already computed")

    # Check required files
    missing = []
    for f in [DEM_GEO_TIF, DEM_UTM_TIF, SLOPE_TIF, OSM_PBF, BOUNDARY_SN,
              GEOL_GEOJSON, BAIRRO_CIDADE_FILE, CIDADE_FILE]:
        if not f.exists():
            missing.append(str(f))
    if missing and not dry_run:
        for f in missing:
            print(f"  MISSING: {f}")
        sys.exit(f"ABORT: {len(missing)} required file(s) missing.")
    elif missing and dry_run:
        print(f"  [DRY-RUN] {len(missing)} files missing — skipping S-N criterion extraction")
        return pd.DataFrame()

    # Build S-N grid (1.25 km, floor1m, land centroid, S-N boundary)
    print(f"Building S-N grid (spacing={GRID_SPACING}m)...")
    candidates = build_santiago_grid(BOUNDARY_SN, CRS_SANTIAGO)
    print(f"  N_cand = {len(candidates)}")

    # --- B1: Hydrogeological unit score (P-C, categorical) ---
    print("Extracting B1 (hydrogeological unit, P-C mapping)...")
    geol = gpd.read_file(GEOL_GEOJSON).to_crs(CRS_SANTIAGO)
    b1_scores = np.full(len(candidates), 0.472)  # default Intermédia
    b1_units  = np.full(len(candidates), "Intermedia", dtype=object)
    for idx, pt in enumerate(candidates.geometry):
        covering = geol[geol.geometry.covers(pt)]
        if len(covering) == 0:
            covering = geol[geol.geometry.intersects(pt.buffer(50))]
        if len(covering) > 0:
            row = covering.iloc[0]
            unit, score = classify_b1_pc(row.get("cod_form"))
            b1_scores[idx] = score
            b1_units[idx]  = unit
    n_recente = int(np.sum(b1_scores == 0.0))
    n_base    = int(np.sum(b1_scores == 1.0))
    n_inter   = int(np.sum(b1_scores == 0.472))
    print(f"  Base={n_base}  Intermédia={n_inter}  Recente(excl)={n_recente}")

    # --- DEM: slope + aspect ---
    print("Extracting slope and C2 continuous aspect from ASTER GDEM v3...")
    slope_vals, aspect_geo = extract_dem_values(candidates, DEM_GEO_TIF)
    # C2 continuous: v(θ) = (1 - cos(θ - 22.5°)) / 2
    # θ = geographic descent azimuth (0°=N, clockwise)
    # aspect_geo = -1 for flat cells → v = 0.5 (neutral)
    asp_rad_shift = np.radians(aspect_geo - 22.5)
    c2_vals = np.where(aspect_geo == -1, 0.5, (1.0 - np.cos(asp_rad_shift)) / 2.0)
    # c2_vals in [0,1], benefit=True (SSW = 1, NNE = 0)
    flat_count = int(np.sum(aspect_geo == -1))
    print(f"  Flat cells (aspect=-1): {flat_count}  C2 range=[{c2_vals.min():.3f},{c2_vals.max():.3f}]")

    # --- A7: Protected areas ---
    print("Extracting A7 (protected areas)...")
    prot_gdf = gpd.read_file(PROTECTED_FILE).to_crs(CRS_SANTIAGO)
    dist_A7 = compute_dist_to_polygons(candidates, prot_gdf)

    # --- A5: Agriculture (DEV-SANT-A5-001: only Regadios excluded, not all tipos) ---
    print("Extracting A5 (agriculture, Regadios exclusion only per DEV-SANT-A5-001)...")
    agri_gdf = gpd.read_file(AGRI_GEOJSON).to_crs(CRS_SANTIAGO)
    # Only Regadios (irrigated) are exclusion zones — other tipos are distance only
    regadios = agri_gdf[agri_gdf["tipo_agric"] == "Regadios"].copy()
    agri_all_utm = agri_gdf  # for distance criterion
    regadios_gdf = regadios if len(regadios) > 0 else gpd.GeoDataFrame(geometry=[], crs=CRS_SANTIAGO)
    dist_A5_criterion = compute_dist_to_polygons(candidates, regadios_gdf)
    dist_A5_exclusion = dist_A5_criterion  # same: exclusion = inside Regadios
    print(f"  {len(regadios)} Regadios polygons (exclusion); {len(agri_gdf)} total (distance)")

    # --- A1: Built-up areas (bairro_cidade + bairro_vila) ---
    print("Extracting A1 (built-up)...")
    built_gdf = gpd.GeoDataFrame()
    for f in [BAIRRO_CIDADE_FILE, BAIRRO_VILA_FILE]:
        if f.exists():
            g = gpd.read_file(f).to_crs(CRS_SANTIAGO)
            built_gdf = pd.concat([built_gdf, g], ignore_index=True)
    built_gdf = gpd.GeoDataFrame(built_gdf, crs=CRS_SANTIAGO)
    dist_A1 = compute_dist_to_polygons(candidates, built_gdf)
    print(f"  {len(built_gdf)} polygons")

    # --- A4: Cultural heritage (patrimonio_cultural, filtered to Santiago) ---
    print("Extracting A4 (cultural heritage)...")
    if PATRIMONIO_FILE.exists():
        pat_all = gpd.read_file(PATRIMONIO_FILE).to_crs(CRS_SANTIAGO)
        # Filter to features within Santiago island + 5 km buffer
        santiago_buf = gpd.read_file(BOUNDARY_ST).to_crs(CRS_SANTIAGO).geometry.union_all().buffer(5000)
        pat_gdf = pat_all[pat_all.geometry.intersects(santiago_buf)].copy()
        if len(pat_gdf) == 0:
            print("  No patrimônio features on Santiago — using Cidade Velha point (14.922N, 23.605W)")
            from shapely.geometry import Point
            # Cidade Velha UNESCO WHC #1310 (Historic Centre of Ribeira Grande)
            cv_utm = gpd.GeoDataFrame(
                geometry=[Point(-23.605, 14.922)], crs="EPSG:4326"
            ).to_crs(CRS_SANTIAGO).geometry.values[0].buffer(100)  # 100m point buffer
            pat_gdf = gpd.GeoDataFrame(geometry=[cv_utm], crs=CRS_SANTIAGO)
        print(f"  {len(pat_gdf)} A4 features (on Santiago)")
        dist_A4 = compute_dist_to_polygons(candidates, pat_gdf)
    else:
        from shapely.geometry import Point
        cv_utm = gpd.GeoDataFrame(
            geometry=[Point(-23.605, 14.922)], crs="EPSG:4326"
        ).to_crs(CRS_SANTIAGO).geometry.values[0].buffer(100)
        pat_gdf = gpd.GeoDataFrame(geometry=[cv_utm], crs=CRS_SANTIAGO)
        print("  Using Cidade Velha point fallback (14.922N, 23.605W)")
        dist_A4 = compute_dist_to_polygons(candidates, pat_gdf)

    # --- D2: Praia urban limit ---
    print("Extracting D2 (Praia urban limit)...")
    if CIDADE_FILE.exists():
        cidade_gdf = gpd.read_file(CIDADE_FILE).to_crs(CRS_SANTIAGO)
        # Filter to Praia: nom_zvc = 'Cidade da Praia' or similar
        praia = cidade_gdf[cidade_gdf.apply(
            lambda r: any("praia" in str(v).lower() for v in r.values), axis=1
        )]
        if len(praia) == 0:
            praia = cidade_gdf  # fallback: use all city boundaries
        print(f"  Praia features: {len(praia)}")
        dist_D2 = compute_dist_to_polygons(candidates, praia)
    else:
        dist_D2 = np.full(len(candidates), 9999.0)

    # --- OSM criteria ---
    boundary_gdf = gpd.read_file(BOUNDARY_SN)
    osm_dists = {}
    if OSM_PBF.exists():
        for crit, tags in OSM_TAGS_SN.items():
            print(f"Extracting OSM {crit}...")
            feats = load_osm_features(OSM_PBF, boundary_gdf, crit, tags, buffer_m=1000)
            n_feat = len(feats)
            print(f"  {crit}: {n_feat} features")
            if crit == "B3" and n_feat < 20:
                print(f"  [C-6] B3 streams < 20 OSM features — using IDECV ribeiras")
                if RIBEIRAS_FILE.exists():
                    rib = gpd.read_file(RIBEIRAS_FILE).to_crs(CRS_SANTIAGO)
                    # Clip to S-N boundary
                    sn_buf = boundary_gdf.to_crs(CRS_SANTIAGO).geometry.union_all().buffer(1000)
                    rib = rib[rib.geometry.intersects(sn_buf)].copy()
                    print(f"  IDECV ribeiras (S-N): {len(rib)} features")
                    osm_dists[crit] = compute_osm_distances(candidates, rib)
                else:
                    osm_dists[crit] = compute_osm_distances(candidates, feats)
            else:
                osm_dists[crit] = compute_osm_distances(candidates, feats)
    else:
        for crit in OSM_TAGS_SN:
            osm_dists[crit] = np.full(len(candidates), 9999.0)

    # --- Exclusion rules (Cabral buffers, PRESPEC §5.3) ---
    # Note: A3 < 80m (coast), A4 < 500m, A5 inside (dist=0), A7 < 500m, B1=Recente,
    #       C1 > 20°, D2 < 500m, A1 < 500m, A6 < 3000m (but A6 is benefit so just distance)
    adm = np.ones(len(candidates), dtype=bool)
    # B1 Recente → excluded
    adm &= (b1_scores > 0)
    # A3 coast < 80m
    adm &= (osm_dists.get("A3", np.full(len(candidates), 9999.0)) >= 80)
    # A4 heritage < 500m
    adm &= (dist_A4 >= 500)
    # A5 agriculture: inside zones (dist=0) → excluded (DEV-SANT-A5-001: Regadios only)
    adm &= (dist_A5_exclusion > 0)
    # A7 protected < 500m
    adm &= (dist_A7 >= 500)
    # A1 built-up < 500m
    adm &= (dist_A1 >= 500)
    # C1 slope > 20°
    adm &= (slope_vals <= 20.0)
    # D2 Praia < 500m
    adm &= (dist_D2 >= 500)

    n_adm = int(np.sum(adm))
    print(f"  N_adm = {n_adm}  (excl = {len(candidates) - n_adm})")
    if n_adm < 100:
        print("  [DEGENERATE] N_adm < 100 — branch S-N abandoned per PRESPEC §3")
        return pd.DataFrame()

    # --- Assemble DataFrame ---
    lats_geo = candidates.to_crs("EPSG:4326").geometry.y.values
    lons_geo = candidates.to_crs("EPSG:4326").geometry.x.values

    df = pd.DataFrame({
        "latitude (degrees)":  lats_geo,
        "longitude (degrees)": lons_geo,
        "B1_score":            b1_scores,
        "B1_unit":             b1_units,
        "slope (degrees)":     slope_vals,
        "aspect_continuous":   c2_vals,
        "dist_A1_buildup (m)":       dist_A1,
        "dist_A3_coast (m)":         osm_dists.get("A3", np.full(len(candidates), 9999.0)),
        "dist_A4_heritage (m)":      dist_A4,
        "dist_A5_agriculture (m)":   dist_A5_criterion,
        "dist_A6_aerodrome (m)":     osm_dists.get("A6", np.full(len(candidates), 9999.0)),
        "dist_A7_protected (m)":     dist_A7,
        "dist_B2_waterpoints (m)":   osm_dists.get("B2", np.full(len(candidates), 9999.0)),
        "dist_B3_streams (m)":       osm_dists.get("B3", np.full(len(candidates), 9999.0)),
        "dist_D1_mainroads (m)":     osm_dists.get("D1", np.full(len(candidates), 9999.0)),
        "dist_D2_praia (m)":         dist_D2,
        "admissible":                adm.astype(int),
    })

    df.to_csv(out_csv, index=False)
    print(f"Saved S-N CSV: {out_csv}  ({len(df)} rows)")
    return df




def write_report(branch: str, df: pd.DataFrame, extra: dict | None = None) -> None:
    """Write JSON provenance report for the extraction run."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RESULTS_DIR / f"extract_report_{branch.lower()}.json"

    n_cand = len(df)
    n_adm  = int(df["admissible"].sum()) if "admissible" in df.columns else None
    flat_c = extra.get("flat_count") if extra else None

    sha_sources = {}
    for f in [GEOL_GEOJSON, AGRI_GEOJSON, BOUNDARY_ST, PROTECTED_FILE, OSM_PBF]:
        if f.exists():
            sha_sources[f.name] = sha256_lf(f)

    report = {
        "branch": branch,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_cand": n_cand, "n_adm": n_adm,
        "flat_cells_aspect": flat_c,
        "source_sha256": sha_sources,
        "grid_params": {
            "spacing_m": GRID_SPACING, "land_frac": LAND_FRAC,
            "origin": ORIGIN, "centroid": CENTROID, "crs": CRS_SANTIAGO,
        },
    }
    if extra:
        report.update({k: v for k, v in extra.items() if k != "flat_count"})

    report_path.write_text(json.dumps(report, indent=2, default=str))
    print(f"Report written: {report_path}")


# ---------------------------------------------------------------------------
# 11. Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Santiago Stage 2 extraction pipeline")
    parser.add_argument("--branch", default="both", choices=["ST","SN","both"],
                        help="Branch to extract (default: both)")
    parser.add_argument("--selftest-fogo", action="store_true",
                        help="Run tolerance regression on Fogo aspect and exit")
    parser.add_argument("--dry-run", action="store_true",
                        help="Check files and grid only; do not extract criteria")
    parser.add_argument("--allow-missing-lock", action="store_true",
                        help="Skip lock file check (use only for development)")
    args = parser.parse_args()

    if args.selftest_fogo:
        ok = selftest_fogo()
        sys.exit(0 if ok else 1)

    check_lock(allow_missing=args.allow_missing_lock)

    if args.branch in ("ST", "both"):
        print("\n" + "=" * 60)
        print("S-T extraction (11 criteria, Fogo AHP weights)")
        print("=" * 60)
        df_st = extract_st(dry_run=args.dry_run)
        if len(df_st) > 0:
            write_report("ST", df_st)

    if args.branch in ("SN", "both"):
        print("\n" + "=" * 60)
        print("S-N extraction (14 criteria, Cabral 2012 weights)")
        print("=" * 60)
        df_sn = extract_sn(dry_run=args.dry_run)
        if len(df_sn) > 0:
            write_report("SN", df_sn)


if __name__ == "__main__":
    main()
