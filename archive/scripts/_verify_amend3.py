# -*- coding: utf-8 -*-
"""
_verify_amend3.py
=================
Verifies four items needed before amend3:

A. Cone test: does aspect_correct align with azimuth from peak to site?
   (independent oracle — no GDAL needed, uses only elevation_utm.tif and lat/lon)

B. Boundary counts: sites with aspect exactly at 90° or 180°.

C. compute_edges check: is the slope raster's border valid?
   If yes → -compute_edges was likely used in Fogo.
   If border is nodata → -compute_edges was NOT used (consistent with declared default).

D. geotransform assert: does DEM have transform.e < 0 (North-up) and no rotation?
"""

import sys, csv, numpy as np
from pathlib import Path
from scipy.ndimage import sobel

DEM_PATH   = Path(r"G:\Faculdade\Estudo\Doutorado\2025.1\Otimização Bioinspirada"
                  r"\Tentativa de dados via GIS\elevation_utm.tif")
SLOPE_PATH = Path(r"G:\Faculdade\Estudo\Doutorado\2025.1\Otimização Bioinspirada"
                  r"\Tentativa de dados via GIS\declive_gdal_graus.tif")
CSV_PATH   = Path(r"G:\Faculdade\Estudo\Doutorado\2025.1\Otimização Bioinspirada"
                  r"\Tentativa de dados via GIS\results_cache\df_real_data_cached.csv")

try:
    import rasterio
except ImportError:
    print("ERROR: rasterio not available"); sys.exit(1)

# ── Load CSV ──────────────────────────────────────────────────────────────────
rows = []
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)
admissible = [r for r in rows if float(r['dist_protected_area (m)']) > 0]
print(f"Admissible sites (N_adm): {len(admissible)}")

lat_sites = np.array([float(r['latitude (degrees)'])  for r in admissible])
lon_sites = np.array([float(r['longitude (degrees)']) for r in admissible])
asp_pub   = np.array([float(r['slope_aspect (degrees)']) for r in admissible])

# ── D. Geotransform assert ────────────────────────────────────────────────────
print("\n=== D. Geotransform assert ===")
with rasterio.open(DEM_PATH) as src:
    tf = src.transform
    print(f"  transform: {tf}")
    print(f"  transform.a (E pixel, must be >0): {tf.a:.6f}")
    print(f"  transform.e (N pixel, must be <0): {tf.e:.6f}")
    print(f"  transform.b (must be 0): {tf.b:.6f}")
    print(f"  transform.d (must be 0): {tf.d:.6f}")
    north_up = tf.e < 0
    no_rot   = abs(tf.b) < 1e-12 and abs(tf.d) < 1e-12
    print(f"  North-up (e<0): {'OK' if north_up else 'FAIL'}")
    print(f"  No rotation (b=d=0): {'OK' if no_rot else 'FAIL'}")

# ── A. Cone test ──────────────────────────────────────────────────────────────
print("\n=== A. Cone test (independent oracle for aspect formula) ===")
with rasterio.open(DEM_PATH) as src:
    dem = src.read(1, masked=True)
    dem_float = dem.astype(np.float32)
    pixel_e = src.transform.a
    pixel_n = abs(src.transform.e)

    # Find peak: row/col of maximum elevation
    r_peak, c_peak = np.unravel_index(np.ma.argmax(dem), dem.shape)
    lon_peak, lat_peak = src.xy(r_peak, c_peak)   # xy() returns (x,y) = (lon,lat) for EPSG:4326
    elev_peak = dem[r_peak, c_peak]
    print(f"  Peak: lat={lat_peak:.5f}  lon={lon_peak:.5f}  elevation={elev_peak:.0f}m")

    # Compute azimuth from peak to each admissible site
    # b = azimuth peak → site = arctan2(delta_lon, delta_lat) % 360
    # (arctan2(East, North) = geographic bearing)
    delta_lon = lon_sites - lon_peak
    delta_lat = lat_sites - lat_peak
    b_peak_to_site = (np.degrees(np.arctan2(delta_lon, delta_lat)) + 360) % 360

    # Recompute both formulas at admissible sites
    dx = sobel(dem_float, axis=1, mode='reflect') / (8 * pixel_e)
    dy = sobel(dem_float, axis=0, mode='reflect') / (8 * pixel_n)
    asp_correct_raster  = (np.degrees(np.arctan2(-dx, dy)) + 360.0) % 360.0
    asp_notebook_raster = (90.0 - np.degrees(np.arctan2(dx, -dy)) + 360.0) % 360.0
    flat = (np.abs(dx) < 1e-9) & (np.abs(dy) < 1e-9)
    asp_correct_raster[flat]  = -1.0
    asp_notebook_raster[flat] = -1.0

    asp_correct_sites  = np.zeros(len(admissible))
    asp_notebook_sites = np.zeros(len(admissible))
    for i, (x, y) in enumerate(zip(lon_sites, lat_sites)):
        ri, ci = src.index(x, y)
        ri = min(max(ri, 0), dem.shape[0]-1)
        ci = min(max(ci, 0), dem.shape[1]-1)
        asp_correct_sites[i]  = asp_correct_raster[ri, ci]
        asp_notebook_sites[i] = asp_notebook_raster[ri, ci]

# Exclude flat sites and the summit cell itself
valid = (asp_correct_sites >= 0) & (asp_notebook_sites >= 0)
print(f"  Non-flat sites: {valid.sum()} of {len(admissible)}")

# Cone test: cosine similarity between aspect and azimuth-from-peak
# A cone gives aspect ≈ azimuth from peak → high positive cosine
cos_correct  = np.mean(np.cos(np.radians(asp_correct_sites[valid]  - b_peak_to_site[valid])))
cos_notebook = np.mean(np.cos(np.radians(asp_notebook_sites[valid] - b_peak_to_site[valid])))
cos_pub      = np.mean(np.cos(np.radians(asp_pub[valid]            - b_peak_to_site[valid])))

print(f"\n  Cosine similarity (correct  formula, azimuth from peak): {cos_correct:.4f}")
print(f"  Cosine similarity (notebook formula, azimuth from peak): {cos_notebook:.4f}")
print(f"  Cosine similarity (published CSV,     azimuth from peak): {cos_pub:.4f}")
print()
print(f"  Interpretation:")
print(f"    > +0.5 → formula aligns with geographic descent direction (correct)")
print(f"    ≈  0.0 → formula is ~90° off (wrong convention)")
print(f"    < −0.5 → formula inverted")

# Also check: does the correct formula match the published CSV?
cos_corr_vs_pub = np.mean(np.cos(np.radians(asp_correct_sites[valid] - asp_pub[valid])))
cos_note_vs_pub = np.mean(np.cos(np.radians(asp_notebook_sites[valid] - asp_pub[valid])))
print(f"\n  Correct  vs Published: cosine = {cos_corr_vs_pub:.4f}")
print(f"  Notebook vs Published: cosine = {cos_note_vs_pub:.4f}")
print(f"  (Notebook should be ~1.0, Correct should be ~cos(avg diff))")

# Show average angular difference
avg_diff_cn = np.mean(np.abs(((asp_correct_sites[valid] - asp_notebook_sites[valid] + 180) % 360) - 180))
print(f"\n  Mean |correct - notebook| (angular): {avg_diff_cn:.1f}°  (expected 90° for reflection)")

# ── B. Boundary counts ────────────────────────────────────────────────────────
print("\n=== B. Boundary counts (aspect exactly at 90° or 180°) ===")
n_exactly_90  = np.sum(asp_pub == 90.0)
n_exactly_180 = np.sum(asp_pub == 180.0)
n_correct_90  = np.sum(asp_correct_sites == 90.0)
n_correct_180 = np.sum(asp_correct_sites == 180.0)
n_flat_zero   = np.sum(asp_correct_sites == 0.0)

print(f"  Published  at 90°:  {n_exactly_90} sites")
print(f"  Published  at 180°: {n_exactly_180} sites")
print(f"  Correct    at 90°:  {n_correct_90} sites")
print(f"  Correct    at 180°: {n_correct_180} sites")
print(f"  Correct    at 0° (flat cells giving 0°): {n_flat_zero} sites")

n_leeward_half_open_pub = np.sum((asp_pub > 90) & (asp_pub < 180))
n_leeward_closed_pub    = np.sum((asp_pub >= 90) & (asp_pub <= 180))
print(f"\n  Published leeward (90, 180) half-open: {n_leeward_half_open_pub}")
print(f"  Published leeward [90, 180] closed:    {n_leeward_closed_pub}  (← should be 94)")
print(f"  The closed interval adds {n_leeward_closed_pub - n_leeward_half_open_pub} boundary sites")

# ── C. compute_edges check ────────────────────────────────────────────────────
print("\n=== C. compute_edges check (slope raster border) ===")
with rasterio.open(SLOPE_PATH) as src_s:
    print(f"  Slope CRS: {src_s.crs}  size: {src_s.width}×{src_s.height}")
    slope = src_s.read(1, masked=True)
    nodata_val = src_s.nodata
    print(f"  Slope nodata value: {nodata_val}")

    # Count nodata cells in first/last 3 rows and columns (border)
    border_top    = slope[:3, :]
    border_bottom = slope[-3:, :]
    border_left   = slope[:, :3]
    border_right  = slope[:, -3:]

    def count_nodata(arr):
        if hasattr(arr, 'mask'):
            return int(np.sum(arr.mask))
        if nodata_val is not None:
            return int(np.sum(arr.data == nodata_val))
        return 0

    nd_top    = count_nodata(border_top)
    nd_bottom = count_nodata(border_bottom)
    nd_left   = count_nodata(border_left)
    nd_right  = count_nodata(border_right)
    nd_total  = count_nodata(slope)
    valid_total = int(np.sum(~slope.mask)) if hasattr(slope, 'mask') else slope.size

    print(f"  Nodata in border top 3 rows:    {nd_top}")
    print(f"  Nodata in border bottom 3 rows: {nd_bottom}")
    print(f"  Nodata in border left 3 cols:   {nd_left}")
    print(f"  Nodata in border right 3 cols:  {nd_right}")
    print(f"  Total nodata:  {nd_total}")
    print(f"  Total valid:   {valid_total}")

    if nd_top == 0 and nd_bottom == 0 and nd_left == 0 and nd_right == 0:
        print(f"  INFERENCE: all border cells valid → consistent with -compute_edges (or DEM larger than island)")
    else:
        print(f"  INFERENCE: border nodata present → consistent with NO -compute_edges (default Horn)")

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n=== SUMMARY ===")
print(f"D. Geotransform: North-up={'OK' if north_up else 'FAIL'}  No-rotation={'OK' if no_rot else 'FAIL'}")
print(f"A. Cone test: correct={cos_correct:.4f}  notebook={cos_notebook:.4f}  published={cos_pub:.4f}")
print(f"B. Boundary: published at 90°={n_exactly_90}  at 180°={n_exactly_180}  → closed adds {n_leeward_closed_pub - n_leeward_half_open_pub}")
print(f"C. Slope border nodata: top={nd_top} bottom={nd_bottom} left={nd_left} right={nd_right}")
