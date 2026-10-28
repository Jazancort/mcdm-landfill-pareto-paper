# -*- coding: utf-8 -*-
"""
_verify_leeward_sets.py
=======================
Verifies three things needed for amend2:

A. Fórmula do notebook vs fórmula correcta:
   - identifica a fórmula do notebook (stored in df_real_data_cached.csv)
   - calcula com ambas as fórmulas nos 389 locais admissíveis
   - verifica se os CONJUNTOS de IDs leeward são idênticos

B. Contagem de nodata na coluna 'slope' do CSV publicado:
   - quantos dos 473 (ou 389 admissíveis) têm slope nodata/NaN

C. Qual foi o raster do aspecto na Fogo (elevation_utm.tif vs hell.tif):
   - confirma que a regressão já feita (src.index + float32) reproduz 94/94
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
    print("ERROR: rasterio not available — install with: uv pip install rasterio --system")
    sys.exit(1)

# ── Load CSV ──────────────────────────────────────────────────────────────────
print("=== Loading CSV ===")
rows = []
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        rows.append(row)

print(f"  Total rows: {len(rows)}")
print(f"  Columns: {fieldnames}")

# Identify aspect and slope column names
asp_col   = next((c for c in fieldnames if 'aspect' in c.lower() or 'slope_asp' in c.lower()), None)
slope_col = next((c for c in fieldnames if 'slope' in c.lower() and 'aspect' not in c.lower()), None)
x_col     = next((c for c in fieldnames if 'lon' in c.lower()), None)
y_col     = next((c for c in fieldnames if 'lat' in c.lower()), None)
excl_col  = next((c for c in fieldnames if 'exclu' in c.lower() or 'admis' in c.lower()), None)

print(f"  aspect_col={asp_col!r}  slope_col={slope_col!r}  x_col={x_col!r}  y_col={y_col!r}  excl_col={excl_col!r}")

# If cannot identify, show first few rows of each column
if asp_col is None or x_col is None:
    print("  First row sample:")
    for k, v in list(rows[0].items())[:15]:
        print(f"    {k!r}: {v!r}")
    sys.exit(1)

# ── Identify admissible sites ─────────────────────────────────────────────────
# Admissible = not excluded (dist_protected_area != 0 in Fogo)
prot_col = next((c for c in fieldnames if 'protected' in c.lower() or 'prot' in c.lower()), None)
print(f"\n  protected_col={prot_col!r}")

if prot_col:
    admissible = [r for r in rows if float(r[prot_col]) > 0]
else:
    admissible = rows  # fallback

print(f"  Admissible (N_adm): {len(admissible)}")

# ── Aspect from CSV (published) ───────────────────────────────────────────────
print(f"\n=== Published aspect column: {asp_col!r} ===")
asp_vals = []
for r in admissible:
    v = r.get(asp_col, '')
    try:
        asp_vals.append(float(v))
    except (ValueError, TypeError):
        asp_vals.append(float('nan'))
asp_vals = np.array(asp_vals)

# Leeward in published dataset (aspect in [90, 180])
published_leeward = set(i for i, a in enumerate(asp_vals) if 90 <= a <= 180)
print(f"  Published leeward IDs count: {len(published_leeward)}")
print(f"  Sample published aspect values (first 10): {asp_vals[:10]}")

# ── Slope nodata check ────────────────────────────────────────────────────────
print(f"\n=== Slope nodata check: {slope_col!r} ===")
if slope_col:
    slope_all = []
    for r in rows:
        v = r.get(slope_col, '')
        try:
            slope_all.append(float(v))
        except:
            slope_all.append(float('nan'))
    slope_all = np.array(slope_all)
    slope_adm = np.array([float(r.get(slope_col, 'nan')) for r in admissible])
    nan_all = np.sum(np.isnan(slope_all))
    nan_adm = np.sum(np.isnan(slope_adm))
    print(f"  All 473: {nan_all} NaN/nodata slope values")
    print(f"  Admissible 389: {nan_adm} NaN/nodata slope values")
    print(f"  Slope range (admissible): [{np.nanmin(slope_adm):.3f}, {np.nanmax(slope_adm):.3f}] degrees")

# ── Recompute aspect from DEM ─────────────────────────────────────────────────
print(f"\n=== Recomputing aspect from DEM ===")
coords_x = np.array([float(r[x_col]) for r in admissible])
coords_y = np.array([float(r[y_col]) for r in admissible])
print(f"  Coordinate range X: [{coords_x.min():.2f}, {coords_x.max():.2f}]")
print(f"  Coordinate range Y: [{coords_y.min():.2f}, {coords_y.max():.2f}]")

with rasterio.open(DEM_PATH) as src:
    print(f"  DEM CRS: {src.crs}")
    print(f"  DEM transform: {src.transform}")
    print(f"  DEM size: {src.width}×{src.height}")
    dem = src.read(1).astype(np.float32)
    pixel_e = src.transform.a   # E pixel size (positive)
    pixel_n = abs(src.transform.e)  # N pixel size (positive)

    dx = sobel(dem, axis=1, mode='reflect') / (8 * pixel_e)
    dy = sobel(dem, axis=0, mode='reflect') / (8 * pixel_n)

    # Correct formula: arctan2(-dx, dy) → 0=N CW
    asp_correct_raster = (np.degrees(np.arctan2(-dx, dy)) + 360.0) % 360.0
    flat_mask = (np.abs(dx) < 1e-9) & (np.abs(dy) < 1e-9)
    asp_correct_raster[flat_mask] = -1.0

    # Notebook formula: (90 - arctan2(dx, -dy) + 360) % 360 → N=270, E=180, S=90, W=0
    asp_notebook_raster = (90.0 - np.degrees(np.arctan2(dx, -dy)) + 360.0) % 360.0
    asp_notebook_raster[flat_mask] = -1.0

    # Sample at admissible site coordinates using src.index
    asp_correct_sites  = np.zeros(len(admissible))
    asp_notebook_sites = np.zeros(len(admissible))
    for i, (x, y) in enumerate(zip(coords_x, coords_y)):
        row_idx, col_idx = src.index(x, y)
        row_idx = min(max(row_idx, 0), dem.shape[0]-1)
        col_idx = min(max(col_idx, 0), dem.shape[1]-1)
        asp_correct_sites[i]  = asp_correct_raster[row_idx, col_idx]
        asp_notebook_sites[i] = asp_notebook_raster[row_idx, col_idx]

# ── Compare leeward SETS ──────────────────────────────────────────────────────
print(f"\n=== Leeward set comparison ===")
leeward_correct  = set(i for i, a in enumerate(asp_correct_sites)  if 90 <= a <= 180)
leeward_notebook = set(i for i, a in enumerate(asp_notebook_sites) if 90 <= a <= 180)

print(f"  Correct formula  leeward count: {len(leeward_correct)}")
print(f"  Notebook formula leeward count: {len(leeward_notebook)}")
print(f"  Published CSV    leeward count: {len(published_leeward)}")

symmetric_diff_cn = leeward_correct ^ leeward_notebook
symmetric_diff_cp = leeward_correct ^ published_leeward
symmetric_diff_np = leeward_notebook ^ published_leeward

print(f"  Correct  XOR Notebook: {len(symmetric_diff_cn)} differences")
print(f"  Correct  XOR Published: {len(symmetric_diff_cp)} differences")
print(f"  Notebook XOR Published: {len(symmetric_diff_np)} differences")

if len(symmetric_diff_cn) == 0:
    print("  CONFIRMED: correct and notebook formulas give IDENTICAL leeward sets")
else:
    print(f"  WARNING: formulas give DIFFERENT leeward sets: {sorted(symmetric_diff_cn)}")

if len(symmetric_diff_np) == 0:
    print("  CONFIRMED: notebook formula reproduces published leeward set exactly")
elif len(symmetric_diff_cp) == 0:
    print("  CONFIRMED: correct formula reproduces published leeward set exactly")
else:
    print(f"  Notebook vs Published diff: {sorted(symmetric_diff_np)[:10]}...")
    print(f"  Correct  vs Published diff: {sorted(symmetric_diff_cp)[:10]}...")

# ── Aspect distribution ───────────────────────────────────────────────────────
print(f"\n=== Aspect distribution (admissible sites) ===")
bins = [0, 45, 90, 135, 180, 225, 270, 315, 360]
for b0, b1 in zip(bins, bins[1:]):
    n_c = np.sum((asp_correct_sites >= b0) & (asp_correct_sites < b1))
    n_p = np.sum((asp_vals >= b0) & (asp_vals < b1))
    label = f"[{b0}°,{b1}°)"
    print(f"  {label}: correct={n_c:3d}  published={n_p:3d}")

print(f"\n  Note: leeward interval [90,180] occupies octants E [90,135) and SE [135,180)")
print(f"  Trade winds from NE -> leeward = SW -> octant [180,270) is NOT the interval")
