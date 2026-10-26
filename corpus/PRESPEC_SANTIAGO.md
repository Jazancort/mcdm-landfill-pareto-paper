# PRESPEC_SANTIAGO.md — Santiago de Cabo Verde Replication (Phase 0)

```
Status:       DRAFT — not yet committed
Immutability: starts at git tag `prespec-santiago-f0` (not at any specific commit)
Phase 0 hash: [HASH_F0]   (fill in TASKS.md after the tag is created)
Code hash:    94b5baf     (includes new R denominator from 5da02ab; scoring algorithm frozen at 022931e)
Written:      2026-10-26
```

Phase 0 is immutable from tag `prespec-santiago-f0`.
Phase 1 is appended in a separate commit; Phase 0 text is never edited afterwards.
Every departure from the design declared here is logged as DEV-S-### with date,
reason and expected direction of effect.

---

## 0. Inspection log (everything seen before this commit)

The following items were inspected before Phase 0 was committed.
"Inspected" means the schema and metadata were read; no criterion value,
normalised column, amplitude, distance, score, or Q2 was computed.

| Item | URL / path | Date accessed | SHA-256 (LF-normalised) | What was inspected | What was NOT computed |
|---|---|---|---|---|---|
| `geologia_santiago_wfs.geojson` | IDECV WFS `https://geoservicos-ingt.gov.cv/geoserver/carto_base/wfs`, layer `carto_base:geologia_santiago` | 2026-10-25 | `23158bc940efbf6f9e6f4be01c88e8ca332fe8a7bf14e185cc64eb48b4becd33` | schema; 976 polygons; polygon count per cod_form (no area, no distance); unique `lit` values (Annex A) | any area, distance, class share, amplitude, score |
| `carta_agricola_st_wfs.geojson` | IDECV WFS, layer `carto_base:carta_agricola_st` | 2026-10-25 | `b3b155c6db081eefe8288d2efea2337cacb30d5b1c126f54dce77524de568a47` | schema; 7 polygons; attribute `tipo_agric` | — |
| Cabral (2012) | hdl.handle.net/10362/8627 | 2026-10-25 | — (PDF, not a data file) | full text: AHP weights (Tab. 11–16, pp. 54–55), exclusion buffers (Tab. 18–26), hydrogeological units (pp. 44–46) and B1 matrix | — |
| Fogo source files | `Landfill_NSGA2_Paper_Final.ipynb`, cells §1.5 (`permeabili == 'Baixa'` filter; aspect rule `(90 - degrees(arctan2(dx, -dy)) + 360) % 360`; flat: `abs(dx)<1e-9 and abs(dy)<1e-9` → -1; centroid of land intersection) | 2026-10-25 | — | permeability filter; aspect formula; grid centroid convention | — |
| IDECV WFS GetCapabilities | `https://geoservicos-ingt.gov.cv/geoserver/ows?service=WFS&version=2.0.0&request=GetCapabilities` | 2026-10-25 | — (XML metadata) | 103 feature types; confirmed: `areas_especiais:zdti`, `areas_especiais:area_protegida`, `divisao_admin:concelho`, `divisao_admin:ilha`, `divisao_admin:cidade` | no geometry or attribute data downloaded |
| Gomes (2007) research summaries | Two independent research summaries of: Gomes, A.M. (2007), Hidrogeologia e recursos hídricos da ilha de Santiago, Universidade de Aveiro (RIA 10773/1316) | 2026-10-26 | — (secondary summaries; original page not verified due to SSL block) | units: Base = Complexo Eruptivo + Flamengos; Intermédia = PA + Assomada; Recente = MV + alluvium | no criterion values |
| Fogo boundary test runs | `scripts/santiago_grid.py --mode fogo-check` with 7 configurations (see §3 PRE-A table) | 2026-10-25–26 | SHA in `results/grid/fogo_*/grid_report.json` | boundary type, CRS, origin, centroid effect on N_cand/N_adm/n_trios; confirmed convention floor1m+land | no criterion values |
| `fogo_boundary.geojson` | IDECV WFS, layer `divisao_admin:ilha`, filtered to nom_ilha='FOGO'; saved to `05-referencia/fogo_boundary.geojson` | 2026-10-25 | `22680f5bcfdad0266eda35a889f78240f9d0187ec61b4cc6b99e31d976b00d17` | island polygon only; used in PRE-A grid validation | no criterion values |
| `Landfill_NSGA2_Paper_Final.ipynb` | `G:\Faculdade\Estudo\Doutorado\2025.1\Otimização Bioinspirada\Tentativa de dados via GIS\Landfill_NSGA2_Paper_Final.ipynb` | 2026-10-25 | `2e62392110c466127b77dcd43c83980f165bc5c300978e71aa9870936119b6f1` | script that generated `df_real_data_cached.csv` (the published 473-site dataset): CRS=EPSG:32626, MIN_LAND_COVERAGE=0.50, origin=`np.floor(xmin)` (integer bbox), centroid=cell midpoint, boundary=`geologia_fogo.shp`, OSM via `osmnx.features_from_point(..., dist=30000)`; criterion columns inspected (schema only) | no criterion values computed against Santiago |

No Santiago criterion value, normalised column, frontier, or Q2 has been computed before this commit.

---

## 1. Purpose and reporting commitment

Two independent branches, **both reported in the article regardless of outcome**:

**S-T (transfer):** the Fogo value model (11 criteria, Fogo AHP weights, 3 objectives) applied to
Santiago-wide data. The perm criterion uses the P-F rule (see §4.2). Question: do the Fogo mechanisms
and magnitudes depend on the spatial distribution of the Fogo data?

**S-N (native):** the Cabral (2012) value model (14 criteria, Cabral AHP weights, 4 objectives)
applied to the Southern Region (Praia, São Domingos, Ribeira Grande). Question: does the normalisation
mechanism appear under an independently elicited value model with a different set of criteria?

Neither branch is a real siting study. S-T weights are transferred by design. Results are reported as
an instance-dependence test (S-T) and a value-model generalisability test (S-N).

---

## 2. Instance-selection rule (declared before data extraction)

The study island is selected by three jointly necessary conditions, each verifiable from published
sources without examining criterion data:

(i)   a published AHP landfill-siting study (peer-reviewed article or examined dissertation)
      is available for the island;
(ii)  open-access digital geology at a resolution usable for distance computation is available;
(iii) the island area is between 300 km² and 1 000 km².

Santiago satisfies: (i) Cabral (2012), hdl.handle.net/10362/8627; (ii) IDECV WFS, confirmed
2026-10-25; (iii) approximately 991 km² total (S-N region: 395 km²).

Note: the instance-selection rule was finalised after Santiago was identified as a candidate
(based on the existence of Cabral 2012 and IDECV WFS). The rule is stated here to make the
selection transparent; it is not presented as a prospective criterion.

---

## 3. Common pipeline

**Code freeze and generalisation:** the scoring algorithm and analysis logic (scoring.py,
mc_unified.py, validate_core.py, compute_regret.py, run_e1.py) is frozen at commit 94b5baf
(includes new R denominator; core scoring algorithm frozen at 022931e).
The Santiago-specific extraction scripts (grid generation, OSM/DEM/WFS feature extraction) and
the generalised pipeline (supporting variable numbers of criteria and groups) do not yet exist.
They will be written and committed before Phase 1 begins. That commit hash must be recorded in
Phase 1 §9; no criterion value, distance, or normalised score may be computed before that commit.

**Mandatory regression test before Phase 1:** the generalised code, run with the Fogo
configuration (11 criteria, 3 groups, weights from `e1_weights_k200.npy`), must reproduce
the following four files bit-for-bit (SHA-256, LF-normalised):

| File | SHA-256 | Frozen at commit |
|---|---|---|
| `results/unified/mc_unified_raw.csv` | `b02df7277956c0112271065efbe201c2048ad4c92c2e6000794c659477e730f2` | `5fefa1a` |
| `results/regret/regret_perdraw.csv` | `0f8eb63d93bdde9d1f4827bf62c4d4941e189f52191a6cf721cd9e35bc401b77` | `9375147` |
| `results/e1/e1_diag_bootstrap.csv` | `32b536bf32516bb2458a8941929c5a85dba41bd54731a02cf3e4a947daf368aa` | `918f125` |
| `results/f8/f8_per_draw.csv` | `228d54ec91535fb4d85f723d7f6a196abfa9d76da4df546acfc08547b8e8850f` | `f2cc549` |

If any file does not match its expected SHA, Phase 1 does not start.

**DEM:** ASTER GDEM v3 (doi: 10.5067/ASTER/ASTGTM.003) for slope and aspect in S-T and S-N
(confirmed in `Landfill_NSGA2_Paper_Final.ipynb` Markdown: "Raster extraction: Slope (°) and
Aspect (°) from ASTER GDEM v3"). This is the same product as Fogo, ensuring transfer coherence
for S-T.

DEM processing pipeline (confirmed from file inspection of Fogo working directory):
1. ASTER GDEM v3 tiles downloaded in EPSG:4326 (~0.000278°/pixel ≈ 30 m); local file:
   `elevation_utm.tif` (EPSG:4326 despite the name, 0.000278°/pixel).
2. DEM reprojected to UTM (Fogo: EPSG:32626; Santiago: EPSG:32627) at ~30 m pixel size
   using `gdalwarp` (resampling method: bilinear assumed; confirm at Santiago extraction);
   local file used for Fogo: `hell.tif` (EPSG:32626, 30.28 m/pixel).
3. Slope: `gdaldem slope <UTM_DEM> <slope_raster>` on the UTM raster (metres-per-metre
   gradient, output in degrees). Fogo output: `declive_gdal_graus.tif` (EPSG:32626, 30.28 m).
   Computation on UTM ensures correct metric slope without the scale parameter.
4. Aspect: Sobel gradient applied to the EPSG:4326 DEM (`elevation_utm.tif`) at extraction time.
   Exact formula from `Landfill_NSGA2_Paper_Final.ipynb`:
   ```python
   from scipy.ndimage import sobel
   dx = sobel(dem, axis=1, mode='reflect') / (8 * src.transform.a)    # E-W gradient
   dy = sobel(dem, axis=0, mode='reflect') / (8 * abs(src.transform.e)) # N-S gradient
   aspect = (90.0 - np.degrees(np.arctan2(dx, -dy)) + 360.0) % 360.0
   flat = (np.abs(dx) < 1e-9) & (np.abs(dy) < 1e-9)
   aspect[flat] = -1.0  # → norm_asp = 0.5
   ```
   Convention: 0° = North, clockwise. The -dy argument corrects for rasterio's row axis
   (increasing row = decreasing northing). For Fogo at ~15°N, 1°lon ≈ 107 km vs 1°lat ≈ 111 km
   (~3.7% anisotropy); the ratio dx/dy in arctan2 absorbs this without material effect on the
   binary [90°, 180°] classification.
5. Raster sampling at each candidate centroid: nearest-pixel (`rasterio.windows.Window(col, row, 1, 1)`)
   after projecting the WGS84 centroid to the raster CRS via `rasterio_transform`.
6. Flat cells: `|dx| < 1e-9 AND |dy| < 1e-9` → aspect = −1 → norm_asp = 0.5.
   Phase 1 must report the count of flat cells in A' (aspect = −1 before binarisation).

DEM URL and SHA-256 of the downloaded tile(s) recorded in Phase 1 §9.

**OSM download strategy:** Geofabrik PBF extract for Cabo Verde (not live Overpass queries).
The first Geofabrik download at Phase 1 extraction time is the definitive snapshot; re-downloading
is prohibited after Phase 1 begins. Distance to features computed with shapely (0 if point is
inside a polygon), in EPSG:32627. Buffer: island polygon + 1 km for S-T to ensure coastal
elements are captured; the three concelhos + 1 km for S-N (elements near the boundary are
included). In S-N, all OSM elements within the buffer are used regardless of which concelho they
fall in. Tags for each criterion: as declared in Annex B (from `Landfill_NSGA2_Paper_Final.ipynb`).

**Pre-MC assertion:** `max|local_score - make_scorers(w)| < 1e-12` on 20 random weight vectors
drawn with `seed=99`. Abort if any assert fails.

**Lock file:** scripts that compute scores or Q2 for Santiago refuse to run unless
`corpus/PRESPEC_SANTIAGO_F1.lock` exists. This file is created only at Phase 1 commit.

**Grid:** 1 km × 1 km cells; cells with less than 50% land coverage discarded; candidate = centroid of the land-covered portion of the cell (guaranteed to be on land).

Grid conventions (confirmed to coordinate level from `Landfill_NSGA2_Paper_Final.ipynb` and `scripts/santiago_grid.py`):
- `origin = floor1m`: `np.floor(xmin)`, `np.floor(ymin)` — rounds to nearest metre. Implemented as `--origin floor1m` in santiago_grid.py.
- `centroid = land`: centroid of the **land intersection** of the cell with the island polygon (source: `intersection.centroid`; comment in source: "Use centroid of the INTERSECTION. This guarantees the point is on land"). For interior cells (land_frac = 1) this equals the cell midpoint; for coastal cells (land_frac < 1) the point is pulled towards the land by 10–250 m.
- Post-filter: centroid must be `within` the island polygon (source notebook Method 2). Catches edge cases at complex coastlines.
- `land_frac = 0.5`: ≥ 50% land coverage required.
- CRS: `EPSG:32626` for Fogo; `EPSG:32627` for Santiago.

**PRE-A grid validation — all trials recorded (2026-10-25–26):**

| Trial | CRS | Origin | Centroid | Boundary | N_cand | N_adm | ref/473 | n_trios |
|---|---|---|---|---|---|---|---|---|
| NSGA-II original (`intersects` filter) | 4826 | floor | cell | geologia_fogo.shp | 524 | — | — | — |
| `_verify_fogo_grid.py` v1 (bug: 4826) | 4826 | bbox | cell | IDECV ilha | 475 | — | — | — |
| 4826 + snap | 4826 | snap | cell | IDECV ilha | 467 | — | — | — |
| 4826 + bbox (ref+excl) | 4826 | bbox | cell | IDECV ilha | 475 | — | — | — |
| 32626 + bbox + cell (ref+excl) | 32626 | bbox | cell | IDECV ilha | 473 | 389 | 421/473 | 1,974,552 |
| 32626 + bbox + cell + geol (ref+excl) | 32626 | bbox | cell | geol dissolved | 473 | 389 | 421/473 | 1,974,552 |
| **32626 + floor1m + land + geol (ref+excl)** | **32626** | **floor1m** | **land** | **geol dissolved** | **473** | **389** | **473/473 (0.0 m)** | **1,944,653** |

Reference dataset (`df_real_data_cached.csv`, SHA-256: `8c88b3654f06a3008241a113fdaaceec5888c1aa71b333cb91805dbc5e99fd15`): N_cand=473, N_adm=389, n_trios=1,944,653.
Source notebook: `Landfill_NSGA2_Paper_Final.ipynb` (SHA-256: `2e62392110c466127b77dcd43c83980f165bc5c300978e71aa9870936119b6f1`).

**PRE-A verdict: CONFIRMED.** All three published values reproduced exactly. 473/473 coordinates match at sub-micrometre precision. The rule is confirmed to coordinate level.

Trials 5–6 (centroid=cell) gave 421/473 position matches and n_trios +1.5% because the 52 coastal cells have land centroids 10–250 m from their cell midpoints. This is not a different rule; it is the correct rule incorrectly implemented.

Boundary source:
- S-T: Santiago island boundary from IDECV `divisao_admin:ilha`, filtered to nom_ilha='SANTIAGO'. CRS: EPSG:4326 → reprojected to EPSG:32627 for distance computations. Version: IDECV WFS as accessed 2026-10-25.
- S-N: Southern Region boundary from IDECV `divisao_admin:concelho`, filtered to concelhos: Praia, São Domingos, Ribeira Grande de Santiago. CRS: EPSG:4326 → reprojected to EPSG:32627.

**CRS:** EPSG:32627 (WGS 84 / UTM Zone 27N, central meridian 21°W) for all spatial distance
computations. Santiago lies within UTM Zone 27. Fogo used EPSG:32626 (UTM Zone 26N).
The IDECV and other source layers are served in their native CRS; at extraction time each layer
is reprojected to EPSG:32627 before distance computation. No single "native CRS" is assumed:
the actual CRS of each downloaded file is recorded in Phase 1 §9.

Fogo grid validation: COMPLETED (2026-10-25). See PRE-A table above. Use `scripts/santiago_grid.py --mode fogo-check` for any re-verification (replaces the now-deprecated `scripts/deprecated/_verify_fogo_grid.py`).

**Trio enumeration:** n_trios computed from geometry only (trace formula: tr(A³)/6, where A is the
binary adjacency matrix of valid pairs). This formula operates on N_cand (before exclusions) and
produces an upper bound on n_trios(A'), because exclusions can only remove trios. The trio limit
(50 000 000) applies to n_trios(N_cand).

Spacing algorithm (implemented in `scripts/santiago_grid.py`):
1. Start at initial spacing (default 1 000 m).
2. If n_trios(N_cand) > trio_limit: increase by 0.25 km steps until n_trios ≤ limit or spacing > 5 000 m. If 5 000 m is reached: branch abandoned.
3. If n_trios(N_cand) < trio_min (10 000): decrease by 0.25 km steps until n_trios ≥ trio_min or spacing < min_spacing (0.5 km). If 0.5 km is reached without meeting trio_min: branch abandoned.
4. Final spacing and n_trios recorded in Phase 1 §9.

Note: N_adm < 100 is checked in Phase 1 after exclusions; it is not enforced in the geometry-only stage (santiago_grid.py cannot know exclusions). If Phase 1 finds N_adm < 100: treat as degenerate (report and abandon).

**Rule for N_adm < 100:** if after exclusions N_adm < 100, report as degenerate. Decreasing spacing to add more candidates would require re-extracting criteria for new sites, which violates the freeze-before-compute rule. Report and abandon the branch.

**Monte Carlo:** w ~ Dirichlet(κ · w_AHP), κ = 200, 500 draws, seed 42. S-T uses the Fogo
weight draws (same random stream, same draws per seed). S-N uses w ~ Dirichlet(κ · w_Cabral),
κ = 200, 500 draws, seed 42 (independent stream). If C-2 triggers (wells absent): same draws,
weight of wells removed and remaining weights renormalised per draw.

**Cells computed:** SAW, TOPSIS × {min–max, vector} × {greedy, optimal}; SAW × ranks (as
Table 4 of main article); E1 cells M, B, W, V (definitions as Fogo §7.7, with Santiago's
own ρ_j and groups).

**Frontier:** exact enumeration; dominance tolerance ε = 1e-9; `validate_core` checks pass
(non-dominance and completeness) before any Q2.

**Metrics:** Q2 (primary), Q3, value regret R. Contrasts: paired bootstrap, B = 2000 replicates,
percentile 95% CI.

---

## 4. Branch S-T

### 4.1 Area

Whole island of Santiago.

### 4.2 Criteria — definitions

All raw variables identical to Fogo unless stated. Orientation same as Fogo (benefit = larger is
better for the site).

| Criterion | Raw variable | Orientation | Rule | Source |
|---|---|---|---|---|
| perm | distance to P-F Baixa polygons (m) | **COST**: site wants to be close to Baixa zones; min distance = best. (`mcdm_experiment.py` L101: `COST = {'perm', ...}`) | **Rule P-F** (see §4.3 and Annex A): polygons of cod_form classified as Baixa in column P-F of T1. | IDECV `geologia_santiago`, SHA as §0 |
| slope | slope (degrees) | **COST**: min degrees = best. | Pre-computed with `gdaldem slope` from ASTER GDEM v3 (same product as Fogo). Raster sampling: nearest-pixel (`rasterio.windows.Window(col, row, 1, 1)`) at the WGS84 centroid of each candidate, projected to the DEM CRS. | ASTER GDEM v3 (doi: 10.5067/ASTER/ASTGTM.003) |
| aspect | binary: 0 if azimuth ∈ [90°, 180°] (leeward), 1 otherwise; flat cells = 0.5 | Special (binary, leeward coded as 0 in objectives, as 1 in SAW score). Flat cells (Sobel magnitude < 1e-9) receive aspect = −1 → norm_asp = 0.5. Source: `Landfill_NSGA2_Paper_Final.ipynb` (`norm_asp = 0.5 # neutral for missing aspect`). Not L428 of the NSGA-II pipeline (that script produced the 524-site dataset, not the 473-site one). | Aspect computed at extraction time via Sobel gradient from ASTER GDEM v3 (not read from a pre-computed aspect raster). Rule: azimuth computed from Sobel dx/dy; flat cells detected by `abs(dx) < 1e-9 and abs(dy) < 1e-9`. | ASTER GDEM v3 |
| roads | dist_roads (m) | **COST**: min distance = best. | OSM `highway=[motorway, trunk, primary, secondary, tertiary, unclassified, residential, service, road, track, path]` (tags from Annex B). Downloaded from Geofabrik PBF (island-wide, Option A); distance = 0 if inside a road polygon, computed in EPSG:32627. | OSM snapshot [date — Phase 1] |
| rivers | dist_streams (m) | **INV**: max distance = best. | OSM `waterway=[stream, river, canal]` (tags from Annex B, no ditch/drain). Option A. | OSM snapshot [date — Phase 1] |
| coast | dist_coastline (m) | **INV**: max distance = best. | OSM `natural=coastline`. Option A. | OSM snapshot [date — Phase 1] |
| protected | dist_protected_area (m) | **INV**: max distance = best; = 0 inside → exclusion. | IDECV `areas_especiais:area_protegida` (confirmed present in GetCapabilities 2026-10-25); this replaces WDPA as primary source. If the IDECV layer has fewer than 5 polygons on Santiago → fall back to WDPA (latest release at Phase 1 time, version recorded in Phase 1 §9). Same rule as Fogo (`area_protegida.shp`, island-wide shapefile). | IDECV `areas_especiais:area_protegida` [date — Phase 1] |
| wells | dist_wells (m) | **INV**: max distance = best. | OSM `man_made=[water_well, borehole, petroleum_well, water_tap, water_works]` (tags from Annex B). Option A. C-2 applies if < 20 features on Santiago. | OSM snapshot [date — Phase 1] |
| urban | dist_urban_core (m) | **BENEFIT**: max distance = best. | OSM `landuse=[residential, commercial, retail, industrial]` (tags from Annex B). Option A. | OSM snapshot [date — Phase 1] |
| aero | dist_aerodrome (m) | **BENEFIT**: max distance = best. Note: only features within Santiago island boundary; aerodrome on Maio island excluded (filtered by island polygon). | OSM `aeroway=aerodrome`. Option A. | OSM snapshot [date — Phase 1] |
| cult | dist_cultivation (m) | **BENEFIT**: max distance = best. | OSM `landuse=[farmland, farmyard, orchard, vineyard, allotments]` (tags from Annex B). Option A. C-8 contingency for S-T: if OSM returns fewer than 50 agricultural polygons on Santiago → use WorldCover 2021 class 40 (Cropland). In S-N: use IDECV `carta_agricola_st` (SHA as §0) as primary source (confirmed downloaded; not a contingency). | OSM snapshot [date — Phase 1] |

### 4.3 Permeability rule P-F (main) and P-C (sensitivity)

**Important:** for the S-T distance criterion, ONLY whether a polygon is classified as Baixa
matters. The subclasses within non-Baixa (Média, Alta, "não-Baixa", "sem análogo") are all
equivalent: they are not included in the Baixa zone set and the candidate's perm distance is
the minimum distance to any Baixa polygon. If a cod_form has no direct Fogo analog, its default
classification is "not Baixa" (NC), and it does not enter the low-permeability zone set unless
a sensitivity run states otherwise.

**P-F (main rule for S-T):** classifies cod_form by lithology following the Fogo convention (filter: `permeabili == 'Baixa'` applied to `geologia_com_permeabilidade_calculada.shp` in `Landfill_NSGA2_Paper_Final.ipynb`). Criteria for Baixa in Santiago:

- **Baixa**: formations whose `lit` field begins with a term describing compact lava flows or sheets ("Mantos", "derrames", "escoadas"). Precedence rule: **the first lithological term in the lit field determines the class**. Formations that begin with non-lava terms (cones, breccias, ash) are not Baixa even if they contain a secondary lava component. This rule reproduces the Fogo dataset: e.g., MV begins with "Cones de piroclastos" → not Baixa despite having "pequenos derrames" later.

  Exception: PA (cod_form = 'PA'). The IDECV lit field for PA is "Complexo eruptivo do Pico da Antónia (Pliocénico-Miocénico)" — does not explicitly begin with "Mantos". PA is classified as Baixa for two reasons: (i) PA1 (a sub-code in the IDECV layer for the same formation) has lit = "Complexo eruptivo do Pico da Antónia; Mantos subaérios, piroclastos", confirming the lava flow character; (ii) Serralheiro (1976) and Cabral (2012, p. 45) describe the PA as an aquifer unit dominated by basaltic lava flows ("mantos basálticos"). PA and PA1 are treated identically.

- **não-Baixa**: formations with a direct Fogo analog to a non-Baixa class. Média = cinder/scoria cones, talus (MV — begins with "Cones de piroclastos"; dv). Alta = ash, alluvium, sediments (a, a dv, a e, c, d, de).

- **sem análogo em Fogo (NC)**: formations whose first term is not a lava flow and have no direct Fogo analog. Default = not included in the Baixa zone set. Includes: intrusive rocks (CA, γ), carbonatites (cb), dykes/necks (chb, chy, chφ), breccias (B, CBm), conglomerates (cong), and lava domes/necks (dφ — "Domas e chaminés" begin with domes, not flows; NC, not Baixa).

Note: the calc (calcarenites) and other sedimentary Alta formations are not Baixa; their first term is a sedimentary description, not a lava flow.

**SENS-2 (always, one run):** all NC formations reclassified as Baixa in a single combined run. NC formations: CA, γ, cb, dφ, chb, chy, chφ, B, CBm, cong. Run always (not contingent on area share).

Note on dφ: previously classified as Baixa by the "compact volcanic = Baixa" principle; corrected to NC because domes and necks are not lava flows by the precedence rule.

**P-C (sensitivity rule for S-T and B1 mapping for S-N):** classifies cod_form by hydrogeological unit following Serralheiro (1976) as interpreted in Cabral (2012, pp. 44–46).
Mapping in Annex A, column P-C.

Key divergence: under P-F, PA/PA1 is Baixa (basaltic lava flows). Under P-C, PA/PA1 is Intermédia (main Santiago aquifer, Gomes 2007). PA is likely the most areally extensive formation. A note on this divergence will appear in the Limitations section.

### 4.4 Rivers rule

OSM `waterway=[stream, river, canal]` as primary (same tags as Annex B; no ditch/drain). Option A (island-wide download). If OSM returns fewer than 20 waterway features on Santiago: use DEM flow accumulation (D8 algorithm, catchment area threshold ≥ 1 km²) from ASTER GDEM v3 → C-3.

### 4.5 Weights and groups

Fogo AHP weights (Table 2 of main article, fogo_constants.py). Groups G1–G3, objectives F1–F3,
orientations as §5 of main article.

### 4.6 Exclusion

Distance to protected areas = 0 only (same as Fogo).

---

## 5. Branch S-N

### 5.1 Area

Southern Region of Santiago: concelhos of Praia, São Domingos, and Ribeira Grande de Santiago.
Area approximately 395 km² (Cabral 2012). Boundary: IDECV `divisao_admin:concelho`, filtered to these three concelhos (confirmed present in GetCapabilities 2026-10-25). CRS: EPSG:4326 → reprojected to EPSG:32627. Rule for cells on the boundary between concelhos: cell is included if ≥ 50% of its area (as a 1 km × 1 km grid cell) falls within the 3-concelho region. Land centroid (same rule as S-T, from `Landfill_NSGA2_Paper_Final.ipynb`).

### 5.2 Criteria

Raw variables are extracted for the S-N region. Cabral buffers (§5.3) define exclusions;
normalisation over A' is the experimental factor.

| Id | Criterion | Raw variable / orientation | Exclusion | Source |
|---|---|---|---|---|
| A1 | Built-up | distance to built-up area polygons, benefit | < 500 m | Primary: IDECV `divisao_admin:bairro_cidade` + `divisao_admin:bairro_vila` (confirmed present 2026-10-25); these are neighbourhood-level polygons for cities and towns. Distance = 0 if inside any polygon → excluded. Fall back: OSM `landuse=[residential, commercial, retail, industrial]` if IDECV layer returns < 5 polygons on Santiago. |
| A2 | ZDTI | distance to ZDTI zones, benefit | < 500 m | IDECV `areas_especiais:zdti` (confirmed present in GetCapabilities 2026-10-25; C-4 NOT triggered). |
| A3 | Coast | distance to coastline, benefit | < 80 m | OSM `natural=coastline`. Option A. |
| A4 | Cultural heritage | distance to Cidade Velha UNESCO buffer zone, benefit | < 500 m | UNESCO WHC boundary (publicly available shapefile, world heritage site ID 1310 — Cidade Velha, Historic Centre of Ribeira Grande, inscribed 2009). Version at Phase 1 time; SHA recorded. |
| A5 | Agriculture | distance to agricultural protection zones, benefit | inside zones | IDECV `carta_agricola_st` (SHA as §0). Distance = 0 if inside any polygon → excluded. |
| A6 | Airport | distance to Praia International Airport, benefit | < 3 000 m | OSM `aeroway=aerodrome`. Option A. |
| A7 | Protected areas | distance to protected area polygons, benefit | < 500 m | IDECV `areas_especiais:area_protegida` (confirmed present 2026-10-25; same source as S-T). |
| B1 | Hydrogeological unit | categorical score (see §5.5); orientation benefit | recente unit → exclusion (score = 0) | IDECV `geologia_santiago`, mapping Annex A column P-C. |
| B2 | Water points | distance to water points, benefit | < 400 m | OSM `man_made=[water_well, borehole, petroleum_well, water_tap, water_works]` (same tags as Annex B wells criterion). Option A. If < 20 features → INGRH inventory → C-5. |
| B3 | Streams | distance to streams, benefit | < 20 m | OSM `waterway=[stream, river, canal]` (same tags as Annex B rivers criterion; no ditch/drain). Option A. If < 20 features → DEM flow acc. ≥ 1 km² (D8) → C-6. |
| C1 | Slope | gdaldem slope (degrees), cost | > 20° excluded | ASTER GDEM v3 (same product as S-T for consistency). Pre-computed with `gdaldem slope`. |
| C2 | Aspect | v(θ) = (1 − cos(θ − 22.5°)) / 2, benefit; flat cells (Sobel < 1e-9) = 0.5 | — | ASTER GDEM v3. Aspect computed via Sobel gradient at extraction time (same method as S-T). |
| D1 | Main roads | distance to main road network, cost | < 50 m | OSM `highway=[motorway, trunk, primary, secondary]` (national-level roads, subset of Annex B tags; restricted to match Cabral "principais vias de comunicação"). Option A. |
| D2 | MSW centre | distance to Praia urban limit, cost | < 500 m → excluded | IDECV `divisao_admin:cidade`, nom_zvc='Cidade da Praia' (confirmed present 2026-10-25). Distance measured to the polygon boundary (not to its centroid); dist = 0 if candidate is inside the polygon → excluded as per Cabral 500 m rule. |

### 5.3 Exclusion zones (Cabral buffers)

Cells are excluded (removed from A') if they violate any buffer in §5.2. B1 recente (score = 0)
also serves as an exclusion. Slope > 20° serves as an exclusion for C1.

### 5.4 ZDTI rule

ZDTI layer confirmed present in IDECV GetCapabilities (`areas_especiais:zdti`, 2026-10-25). C-4 is NOT triggered. A2 uses this layer as declared. Weight redistribution (C-4) does not apply.

### 5.5 B1 — hydrogeological unit scores

B1 is a single categorical criterion with three classes (Cabral 2012, Tab. 14, p. 55):
- Base unit: score = 1.000
- Intermédia unit: score = 27.8 / 58.9 = 0.472 (ratio of class proportions in the AHP matrix)
- Recente unit: score = 0 (excluded)

The class-to-cod_form mapping follows the P-C column of T1 (Annex A). NC cases receive the
default score declared in T1, which follows the stratigraphic rule for formations not listed
in Cabral (2012) pp. 44–46 (see T1 summary below). A sensitivity run is triggered for each
NC cod_form with area share in A' > 2%, using the alternative score noted in T1. These
sensitivity runs are pre-declared contingency C-7 and do not constitute deviations.

Note on B1 after normalisation: B1 raw values are base=1.000, intermédia=0.472, recente=0.
Under min-max normalisation over A', B1 becomes binary {0, 1} (min=0.472, max=1.000;
min-max(0.472)=0, min-max(1.000)=1). Under vector normalisation, ρ_j = 1/||c_j||₂ where
c_j counts base-unit sites in A'. B1 is structurally binary after any affine normalisation;
this is precisely the case Corollary 1 addresses. Coding: base=1 (benefit).

Note on B1 CI: Cabral (2012, Tab. 14) reports CI = CR = 0.000. The published matrix is not
exactly reciprocal; the actual CI ≈ 0.004 (see Annex C). The published pairwise ratios and the
resulting weights (13.3 / 27.8 / 58.9%) are used as given.

### 5.6 Weights and groups

Cabral (2012) AHP leaf weights (Annex C). Weight of A2 is NOT redistributed (ZDTI present; C-4 not triggered).
Groups: A (criteria A1–A7), B (B1–B3), C (C1–C2), D (D1–D2).
All four group objectives F_A, F_B, F_C, F_D are maximised. Each objective: F_g(t, w) = Σ_{j∈Gg} w_j c̃_j(t), where c̃_j(t) is the partial value score of site t on criterion j, oriented so that higher is better (cost criteria complemented: c̃_j = 1 − c_j for COST orientation), normalised over A'.
Theorem 1 and Proposition 1 hold for any criterion-to-group partition (proof unchanged).

### 5.7 Aspect C2 — operationalisation

Cabral (2012) does not publish numerical aspect intervals; Fig. 37 shows that NE/NNE aspects
receive the lowest scores. The function v(θ) = (1 − cos(θ − 22.5°)) / 2, where θ is the
topographic azimuth in degrees, assigns:
- v = 0.0 at θ = 22.5° (NNE, worst)
- v = 0.5 at θ = 112.5° (ESE) and θ = 292.5° (WNW)
- v = 1.0 at θ = 202.5° (SSW, best)

This is our operationalisation of "NE/NNE is worst", not a claim from Cabral.
A sentence to this effect will appear in the article.

Flat cells (DEM slope = 0, aspect undefined): v = 0.5 (neutral; same as the [90°, 180°]
convention for flat cells in the Fogo script).

---

## 6. Predictions

For each branch b ∈ {S-T, S-N}. Conditions are resolved in Phase 1 after data extraction,
before any score or Q2 is computed.

| Id | Prediction | Condition | Type |
|---|---|---|---|
| S0 | SAW/mm/opt Q2 = 100% and R = 0 on every draw; E1-B optimal Q2 = 100% | — | Regression (failure = bug; abort before any Q2) |
| S1 | Q2(SAW, mm, greedy) > Q2(SAW, vec, greedy), 95% CI excludes 0 | TV(vec) ≥ 0.05 | Replication of Fogo main finding |
| S2 | Q2(SAW, vec, opt) < Q2(SAW, vec, grd), 95% CI excludes 0 | TV_W(vec) ≥ 0.05 | Replication of Fogo greedy reversal |
| S3a | E1-W optimal < 100% and E1-V optimal < 100% | TV_W(vec) ≥ 0.05 | E1 protocol: both TV components matter |
| S3b | E1-V optimal < E1-W optimal (direction observed in Fogo and E6) | TV_W(vec) ≥ 0.05 **and** TV_B(vec) ≥ 0.05 | E1 direction replication. V differs from W by the between-group distortion; both conditions needed to ensure the directional claim is not vacuous. |
| S4 | SAW minus TOPSIS per cell: no sign predicted | — | Descriptive |
| S5 | Q2(SAW, vec, opt) in branch b > 56.8% (Fogo result) | max_{j ∈ non-binary, non-categorical} point-mass share (fraction of A' at modal value) < 0.5. Binary criteria (aspect in S-T; B1 in S-N after normalisation) and categorical criteria are excluded from this condition. In Fogo: perm point-mass = 350/389 = 0.90 → S5 would not have been tested on Fogo. Under P-F in S-T, PA (likely areally extensive) is Baixa, which may create a similar high point-mass for perm → S5 may not be testable in S-T either. S5 condition is resolved in Phase 1 after data extraction, not as a prior expectation. | Risky: predicts weaker mechanism under smoother distributions (E6 reasoning). Condition is likely not met in S-T under P-F. |
| S6 | R(SAW, vec, grd) > R(SAW, vec, opt), 95% CI excludes 0. Fogo reference (new denominator, min over all T): R(vec,grd)=6.63 pp, R(vec,opt)=5.27 pp, difference=1.36 pp [95% CI: 0.95, 1.74 pp]. Note: this difference is below the δ=2.5 pp margin pre-specified for Q2; in the PRESPEC it is treated as a secondary test. | TV_W(vec) ≥ 0.05 | Opposite direction to S2 (Q2–R discordance): S2 shows greedy beating optimal in Q2 (frontier); S6 shows optimal beating greedy in R (value). Effect is small (below δ). |
| S7a | R(E1-B, optimal) > 0, 95% CI excludes 0. Fogo reference: 4.53 pp mean (median 5.50 pp); 28% of draws R = 0. | TV_B(vec) ≥ 0.05 | Low risk: R ≥ 0 by construction; if any draws have R > 0 (which happens in 72% of Fogo draws), the mean CI will exclude 0. |
| S7b | R(E1-B, optimal) < R(E1-W, optimal) — ordering of Fogo (4.53 pp < 6.47 pp). | TV_B(vec) ≥ 0.05 and TV_W(vec) ≥ 0.05 | Risky: can fail if between-group distortion is large relative to within-group. |

**Multiple testing note:** S1, S2, S3a, S3b, S5, S6, S7a, S7b (8 tested predictions) × 2 branches = up to 16 tests; S0 is a regression check, S4 is descriptive. Each reported individually without multiplicity correction. Results read as a pattern, not independent tests.

If a condition fails, the prediction is not tested and the cell is reported descriptively
(see Annex D for templates).

---

## 7. Validity criteria

Checked in Phase 1, before any score is computed:

1. N_adm ≥ 100
2. Variance > 0 for every criterion on A'
3. `validate_core` passes: frontier non-dominance and completeness
4. B1: every site in A' is covered by a geology polygon with a non-null P-C class. If > 5% of sites in A' fall outside all geology polygons (no polygon covers their centroid), report area share as limitation but do not abandon branch. Apply the NC default (Base, score = 1.000) for uncovered sites.

TV(vec) < 0.05 does not invalidate the branch. Each prediction is tested if and only if its own stated condition in §6 is met.

---

## 8. Fogo controls

Triggered automatically if the corresponding Santiago deviation occurs:

- Wells absent from Santiago (C-2): run Fogo factorial without the wells criterion,
  renormalising the 10 remaining weights proportionally. Report Q2 change.
- P-C sensitivity (SENS-1, always): run S-T with P-C rule after S-T main (P-F rule) results
  are sealed. No Fogo control.
- C-9 (SENS-5, always): run the Santiago extraction pipeline on Fogo with Option A and a
  contemporaneous OSM snapshot. Compare with df_real_data_cached.csv column-by-column.
  Report Spearman correlation and fraction of sites with |diff| > 100 m per criterion.

---

## 9. Phase 1 content (one commit, before any score)

Phase 1 commit [HASH_F1] contains, and only contains:

1. SHA-256 of every spatial layer extracted (CRS, feature count, date, version)
2. N_cand, N_excl, N_adm; n_trios(N_cand) (upper bound) and n_trios(A') (exact)
3. Per criterion on A': amplitude ρ_j (vec, ranks), point-mass share (fraction of A' at modal value, continuous criteria only), TV, TV_B, TV_W, m_eff
4. Resolution of every condition in §6 (TV(vec) ≥ 0.05? TV_W ≥ 0.05? TV_B ≥ 0.05? max point-mass < 0.5?)
5. Validity checks of §7
6. Count of cells cut by the within-island filter (centroid=land; how many candidates removed by Method 2)
7. Count of flat cells in A' for the aspect criterion (Sobel magnitude < 1e-9)
8. OSM element counts per criterion (resolves C-2 through C-8)
9. Count of sites in A' that fall outside any geology polygon (B1 criterion); these receive the default NC score
10. SHA-256 of the extraction code commit and the Geofabrik PBF tile

---

## 10. Deviation policy

Any change after [HASH_F0] that modifies a prediction, threshold, criterion definition,
or weight in §3–§6 must be logged as DEV-S-NNN with date, reason, and expected direction
of effect. No prediction, threshold, or definition in §3–§6 may be changed after Phase 1
commit [HASH_F1].

Pre-declared contingency rules (not deviations; responses are fully specified here):
- C-1: Not triggered. PRE-A confirmed (2026-10-25–26): 473/473 coordinates at 0.0 m, N_adm=389, n_trios=1,944,653. Convention: 32626 + floor1m + land + geologia_fogo.shp.
- C-2: Wells OSM < 20 features (S-T and S-N): use INGRH inventory; if unavailable → omit + Fogo control.
- C-3: Rivers OSM < 20 features: use DEM flow accumulation ≥ 1 km².
- C-4: ZDTI absent from IDECV: omit A2, redistribute weight, no Fogo control.
- C-5: Water points OSM < 20 features, S-N: use INGRH; if unavailable → omit.
- C-6: Streams OSM < 20 features, S-N: use DEM flow accumulation.
- C-7: NC B1 cod_form (calc, cong, dφ, φ, null) area share > 2% in A' for S-N → trigger sensitivity run with adjacent unit.
- C-8: OSM agriculture < 50 polygons on Santiago → use WorldCover 2021 class 40 (Cropland) for S-T cult; for S-N use `carta_agricola_st` (IDECV, already downloaded, SHA as §0).

True deviations (DEV-S-###) are unplanned departures from §3–§6 that occur during Phase 1 or later.

---

## 11. Sensitivity runs and controls

All sensitivity runs are pre-declared here. They are all **descriptive**: predictions S0–S7b
are evaluated only on the main analysis. Sensitivity results are reported in a supplementary
table. No sensitivity run can replace the main analysis.

| ID | Description | Scope | When runs |
|---|---|---|---|
| SENS-1 | S-T with P-C rule instead of P-F (perm criterion only) | S-T | Always; after main S-T results are sealed |
| SENS-2 | S-T with all NC formations (CA, γ, cb, dφ, chb, chy, chφ, B, CBm, cong) reclassified as Baixa in a single combined run | S-T | Always |
| SENS-3 | For each NC B1 cod_form (calc, cong, dφ, φ, null) with area share > 2% in A': reclassify to adjacent unit (one run per triggered formation) | S-N | If C-7 triggers; otherwise skip |
| SENS-4 | Contingency responses: C-2 (wells), C-8 (cult WorldCover), other C-x triggered | Both | If corresponding C-x triggers |
| SENS-5 (C-9) | Run Santiago extraction pipeline on Fogo with Option A (island-wide download) using the **same Geofabrik PBF used for Santiago** (not a contemporaneous download); compare dist_* columns with df_real_data_cached.csv: Spearman correlation, fraction of sites with |diff| > 100 m, ρ_j(vec) actual vs published. Report in supplementary. | S-T only | Always |

SENS-2 justification: classifying all NC formations as Baixa in a
single run avoids creating multiple separate analyses. NC formations: CA, γ, cb, dφ, chb, chy,
chφ, B, CBm, cong. The result tells whether the Baixa boundary changes qualitatively when all
intrusive, dome, and uncommon formations are included. Run always (not contingent on area share).

SENS-5 (C-9) also tests whether the 3 NaN values in Fogo (sites 41, 385, 429) were caused by
the 30 km radius. Under Option A they should receive non-NaN values; if they do, the imputation
was not neutral and should be reported.

---

## Annex A — T1: cod_form → permeability classification

Each cod_form has two independent classifications:

**P-F** (Rule P-F, main rule for S-T): based on the `lit` legend text alone, following
the Fogo convention: compact lava flows = Baixa. Intrusive rocks, breccias, conglomerates
and formations without a direct Fogo analog default to NC (not included in the Baixa zone set).
Source: Andrade (2015) script rule; lit text in IDECV layer.

**P-C** (Rule P-C, sensitivity for S-T; and B1 mapping for S-N): based on the hydrogeological
unit following Serralheiro (1976) as interpreted in Cabral (2012, pp. 44–46) via Gomes (2007).
Source: Cabral (2012) pp. 44–46 text, cited as "Base unit", "Unidade Intermédia",
"Unidade Recente". Formations with grupo = "Complexo eruptivo interno, antigo" that are not
explicitly named in Cabral's text are assigned to Base by group membership; this is noted in
the "P-C source" column.

Data quality note: 1 entry in the IDECV layer has cod_form = null (136 features); lit text
describes submarine pillow lavas ("Mantos submarinos, inferiores e superiores") and tuff breccias
("Tufo Brechas"). These features have a dedicated row in T1 (see null row below). P-F = Baixa
(submarine hyaloclastites, direct analog of λρ1). P-C = NC (default: Intermédia, by the
Plio-Miocénico stratigraphic rule). Their combined area share in A' is reported in Phase 1 §9.

Note on T1 count: the PLANO_TRABALHO V3 note listed "24 unique formations" (a typo; the same
list contained 25 items). The T1 below has 27 named formations because: (a) the initial count
omitted cod_form "A" (Formação da Assomada without numeric suffix); (b) the IDECV layer uses
cod_form "CB" as a composite code combining two formations (Flamengos + Orgãos) that are also
separately encoded as λρ, λρ1, and CBm; this composite code is a data artefact but represents
real polygons that must be classified.

† Symbol in the B1 score column denotes an NC case with a declared default classification by the
stratigraphic rule. The default is Intermédia for Plio-Miocénico formations not listed in Cabral
(2012) pp. 44–46. A sensitivity run is triggered for each such cod_form whose area share in A' > 2%.

| cod_form | lit (IDECV, key terms) | grupo | P-F class | P-F source | P-C unit | B1 score | P-C source |
|---|---|---|---|---|---|---|---|
| A | Formação da Assomada; Mantos e Piroclastos (Pliocénico) | — | **Baixa** | "Mantos" (lava flows) per lit; lava = Baixa by P-F rule | **Intermédia** | 0.472 | Gomes (2007) places the Formação da Assomada in the Unidade Intermédia alongside PA (two independent research summaries agree). Source: Gomes, A.M. (2007), Hidrogeologia e recursos hídricos da ilha de Santiago (Cabo Verde), Universidade de Aveiro. **TO CONFIRM before tag:** verify page number in the original thesis (RIA handle 10773/1316). If confirmed: remove †. If Recente: update P-C to Recente (score = 0, excluded in S-N) and add sensitivity with Intermédia. |
| A1 | Formação da Assomada; Mantos e Piroclastos subaérios (basanitos, basanitóides, limburgiticos) (Pliocénico) | — | **Baixa** | "Mantos subaérios" (subaerial lava flows); lava = Baixa | **Intermédia** | 0.472 | As A; same source (Gomes 2007 pending page confirmation). |
| B | Brechas intravulcânicas (Ante-Miocénico médio) | Complexo eruptivo interno, antigo | **sem análogo em Fogo (default: NC)** | Intravulcanic breccias; Fogo NC class (agglomerates/breccias) is closest analog. Default NC. Sensitivity: Baixa. | **Base** | 1.000 | Cabral (2012) p.45: formations of "Complexo eruptivo interno, antigo" = Base; B listed in this group |
| CA | Complexo filoniano de base; basanitos, limburgitos, ancaratritos (Ante-Miocénico médio) | Complexo eruptivo interno, antigo | **sem análogo em Fogo (default: NC)** | Intrusive dyke complex; Fogo has no class for intrusive rocks (NC = carbonatites and agglomerates is closest). Default NC. Sensitivity: Baixa. | **Base** | 1.000 | Cabral (2012) p.45: CA = Complexo de Base |
| CB | Formação dos Flamengos (Mantos, piroclastos, chaminés) + Formação dos Orgãos (Depósitos conglomeráticos-brechoídes) — composite IDECV code (Miocénico médio) | — | **Baixa** | "Mantos" in Flamengos component = lava flows = Baixa (direct Fogo analog). The CBm component (conglomerate) has no Fogo analog but is dominated by the Flamengos lava component in this composite code. | **Base** | 1.000 | Flamengos = λρ = Base; Orgãos = CBm = Base; both components in Cabral (2012) p.45 |
| CBm | Formação dos Orgãos; Depósitos conglomeráticos-brechoídes terrestres (Miocénico médio) | — | **sem análogo em Fogo (default: NC)** | Terrestrial conglomerate-breccia; no Fogo analog (Fogo has no sedimentary conglomerates). Sensitivity: Baixa. | **Base** | 1.000 | Cabral (2012) p.45: CBm = Formação dos Orgãos = Base unit |
| MV | Formação do Monte das Vacas; Cones de piroclastos, escórias e pequenos derrames (Pliocénico) | — | **não-Baixa (Média)** | "Cones de piroclastos, escórias" = scoria cones; direct Fogo analog: cinder cones = Média (not Alta). | **Recente** | 0 (excl.) | Cabral (2012): Monte das Vacas = Recente unit |
| PA | Complexo eruptivo do Pico da Antónia (Pliocénico-Miocénico) | — | **Baixa** | "Complexo eruptivo" = basaltic lava flows; lava = Baixa by P-F rule. **KEY DIVERGENCE**: PA = main Santiago aquifer; P-F/P-C disagree here | **Intermédia** | 0.472 | Cabral (2012) p.45: PA = Pico da Antónia = main aquifer = Intermédia |
| PA1 | Complexo eruptivo do Pico da Antónia; Mantos subaérios, piroclastos (Pliocénico-Miocénico) | — | **Baixa** | "Mantos subaérios" = subaerial lava flows | **Intermédia** | 0.472 | As PA |
| a | Aluviões antigas e modernas (Quaternário) | — | **Alta** | Alluvial deposits; unconsolidated; high permeability | **Recente** | 0 (excl.) | Cabral (2012): alluvium = Recente unit |
| a dv | Aluviões antigas e modernas depósitos de vertente (Quaternário) | — | **Alta** | As "a"; plus slope deposits | **Recente** | 0 (excl.) | As "a" |
| a e | Aluviões e eluviões (Quaternário) | — | **Alta** | Alluvium + eluvial deposits | **Recente** | 0 (excl.) | As "a" |
| c | Conglomerados e calcarenitos marinhos fossilíferos (Quaternário) | — | **Alta** | Marine sediments; highly porous | **Recente** | 0 (excl.) | Quaternary marine deposits = Recente |
| calc | Calcarenitos marinhos, fossilíferos (Pliocénico-Miocénico) | — | **Alta** | Marine calcarenite; highly porous; no compact lava | **Intermédia** (†, stratigraphic rule) | 0.472† | Plio-Miocénico age → Intermédia by stratigraphic rule. Not in Cabral (2012) pp. 44–46. Sensitivity: Recente (0, excluded). Run if calc area share in A' > 2%. |
| cb | Rochas granulares (carbonatitos); Complexo eruptivo interno, antigo (Ante-Miocénico médio) | Complexo eruptivo interno, antigo | **sem análogo em Fogo (default: NC)** | Carbonatites = NC in Fogo (not a lava flow, not a sediment); no direct Fogo analog. Sensitivity: Baixa. | **Base** | 1.000 | Cabral (2012) p.45: formations of "Complexo eruptivo interno, antigo" = Base; cb in this group |
| chb | Filões e chaminés piroclastos; Complexo eruptivo interno, antigo (Miocénico médio) | Complexo eruptivo interno, antigo | **sem análogo em Fogo (default: NC)** | Pyroclastic dykes/necks; no direct Fogo analog. Sensitivity: Baixa. | **Base** | 1.000 | Part of "Complexo eruptivo interno, antigo" group = Base (Cabral 2012 p.45) |
| chy | Filões e chaminés piroclastos; Complexo eruptivo interno, antigo (Ante-Miocénico médio) | Complexo eruptivo interno, antigo | **sem análogo em Fogo (default: NC)** | As chb | **Base** | 1.000 | As chb |
| chφ | Filões e chaminés; Complexo eruptivo interno, antigo (Ante-Miocénico médio) | Complexo eruptivo interno, antigo | **sem análogo em Fogo (default: NC)** | Phonolitic dykes; no direct Fogo analog. Sensitivity: Baixa. | **Base** | 1.000 | As chb |
| cong | Conglomerados e facies terrestres (Pliocénico-Miocénico) | — | **sem análogo em Fogo (default: NC)** | Terrestrial conglomerates; no direct Fogo analog (Fogo has no sedimentary terrestrial conglomerates; class Média was wrong in earlier version). Default NC. SENS-2: Baixa. | **Intermédia** (†, stratigraphic rule) | 0.472† | Plio-Miocénico age → Intermédia by stratigraphic rule. Not explicitly listed in Cabral (2012). Sensitivity: Base (1.000). Run if cong area share in A' > 2%. |
| d | Dunas (Quaternário) | — | **Alta** | Sandy dunes; very high permeability | **Recente** | 0 (excl.) | Quaternary = Recente |
| de | Duna, eluviões (Quaternário) | — | **Alta** | Dunes + eluvial deposits | **Recente** | 0 (excl.) | As "d" |
| dv | Depósitos de vertente (Quaternário) | — | **Média** | Slope deposits; heterogeneous; more permeable than lavas | **Recente** | 0 (excl.) | Quaternary = Recente |
| dφ | Domas e chaminés (fonólitos e traquitos); Fonólitos e traquitos (Pliocénico-Miocénico) | Fonólitos e traquitos | **sem análogo em Fogo (default: NC)** | Lava domes and phonolitic necks; not a lava flow; no direct Fogo analog (Fogo has no phonolite domes). Default NC. SENS-2: Baixa. Correction from previous version which classified dφ as Baixa by the "compact volcanic = Baixa" principle; that principle is not in the P-F rule. | **Intermédia** (†, stratigraphic rule) | 0.472† | Plio-Miocénico age → Intermédia by stratigraphic rule. Not in Cabral (2012). Sensitivity: Base (1.000). |
| γ | Rochas granulares (gabros feldspatóidicos, piroxenitos alcalinos, sienitos feldspatóidicos); Complexo eruptivo interno, antigo (Ante-Miocénico médio) | Complexo eruptivo interno, antigo | **sem análogo em Fogo (default: NC)** | Granular intrusive rocks; no Fogo analog for intrusive rocks. Default NC. Sensitivity: Baixa. | **Base** | 1.000 | Cabral (2012) p.45: γ = gabros = Base unit |
| λρ | Formação dos Flamengos; Mantos, piroclastos, chaminés (Miocénico médio) | — | **Baixa** | "Mantos" (lava flows); the dominant component | **Base** | 1.000 | Cabral (2012) p.45: λρ = Formação dos Flamengos = Base unit |
| λρ1 | Formação dos Flamengos; Mantos, piroclastos, chaminés e hialoclastitos, submarinos (Miocénico médio) | — | **Baixa** | As λρ; submarine hyaloclastites = solidified lava glass, generally impermeable | **Base** | 1.000 | As λρ |
| φ | Fase lávica pós Formação dos Orgãos (rochas traquito-fonolíticas); Mantos; Piroclastos (Pliocénico-Miocénico) | Fonólitos e traquitos | **Baixa** | "Mantos" (lava flows component); compact phonolitic/trachytic lavas. "Mantos" is present in the lit field. | **NC (default: Intermédia)** | 0.472† | Post-Orgãos, pre-PA stratigraphically; assigned Intermédia by age position. Sensitivity: Base (1.000). |
| null | Mantos submarinos, inferiores e superiores (hialoclastitos); Piroclastos; Tufo Brechas (Pliocénico-Miocénico) | — | **Baixa** | "Mantos submarinos (hialoclastitos)" = submarine hyaloclastites; direct analog with λρ1 ("Formação dos Flamengos Mantos, piroclastos, chaminés e hialoclastitos, submarinos") which is Baixa. | **NC (default: Intermédia)** | 0.472† | 136 features with null cod_form. Submarine lavas are age-correlative with Pico da Antónia (Plio-Miocénico); default Intermédia by stratigraphic rule. Sensitivity: Base (1.000). |

Summary for distance computation (S-T, P-F main rule):
- Baixa polygons (used in `dist_low_permeability`): λρ, λρ1, PA, PA1, A, A1, φ, CB, null
- sem análogo em Fogo (default NC, not in Baixa set): CA, γ, cb, dφ, chb, chy, chφ, B, CBm, cong
- não-Baixa Média: MV, dv
- não-Baixa Alta: a, a dv, a e, c, d, de, calc
Note: within não-Baixa, only the distinction Baixa/não-Baixa matters for the S-T distance criterion. The subclasses (Média, Alta, NC) are informative but do not affect the distance computation.

Summary for B1 score (S-N, P-C) using stratigraphic rule for NC cases:
- Base (score = 1.000): CA, λρ, λρ1, CB, CBm, B, cb, γ, chb, chy, chφ [Ante-Miocénico + Miocénico médio from Cabral]
- Intermédia (score = 0.472): PA, PA1 [from Cabral]; A, A1, calc, cong, dφ, φ, null [†, stratigraphic rule: Plio-Miocénico → Intermédia]
- Recente / excluded (score = 0): MV, a, a dv, a e, c, d, de, dv
- Stratigraphic rule: Ante-Miocénico médio and Miocénico médio → Base; Plio-Miocénico → Intermédia; Quaternário and pyroclastic cones → Recente. Applied to all NC cases (not in Cabral 2012 pp. 44–46). Sensitivity for each NC case = adjacent unit (see individual rows). A, A1 have marker † because they are assigned Intermédia by this rule without explicit Cabral source.

---

## Annex B — OSM criterion definitions (confirmed from the source that generated df_real_data_cached.csv)

Source: `Landfill_NSGA2_Paper_Final.ipynb` (SHA-256: `2e62392110c466127b77dcd43c83980f165bc5c300978e71aa9870936119b6f1`). This is the script that wrote `results_cache/df_real_data_cached.csv` (confirmed by grep). The notebook uses `osmnx.features_from_point(..., dist=30000)` (live Overpass API) for Fogo. For **Santiago**, the same tag definitions are used but with a Geofabrik PBF extract (declared in §3 OSM snapshot rule). Distance computed with shapely: `geom.distance(point)` returns 0 if the point is inside a polygon, in the CRS of the geometry (EPSG:32627). Buffer: island polygon + 1 km for S-T; 3-concelho boundary + 1 km for S-N. All OSM elements within the buffer are used regardless of which sub-region they fall in.

The tag definitions below are from the source notebook and apply to both Fogo (with Overpass) and Santiago (with Geofabrik PBF; same tags, same distance logic).

```python
osm_criteria = {                                                   # L271–287
    'dist_urban_core':  {'tags': {'landuse': ['residential',       # L272
                                              'commercial',
                                              'retail',
                                              'industrial']}},
    'dist_aerodrome':   {'tags': {'aeroway': 'aerodrome'}},        # L273
    'dist_streams':     {'tags': {'waterway': ['stream',           # L274
                                               'river',
                                               'canal']}},
    'dist_roads':       {'tags': {'highway': ['motorway',          # L275–277
                                              'trunk',
                                              'primary',
                                              'secondary',
                                              'tertiary',
                                              'unclassified',
                                              'residential',
                                              'service',
                                              'road',
                                              'track',
                                              'path']}},
    'dist_wells':       {'tags': {'man_made': ['water_well',       # L278–280
                                               'borehole',
                                               'petroleum_well',
                                               'water_tap',
                                               'water_works']}},
    'dist_cultivation': {'tags': {'landuse': ['farmland',          # L280–282
                                              'farmyard',
                                              'orchard',
                                              'vineyard',
                                              'allotments']}},
    'dist_coastline':   {'tags': {'natural': 'coastline'}},        # L282
}
```

Note on cult (dist_cultivation): the criterion measures distance to OSM agricultural land use,
not to parks or historic sites. This is the definition used throughout Fogo.

Note on D1 (S-N main roads): use only `highway: ['motorway', 'trunk', 'primary', 'secondary']`
(national-level roads). The full Fogo roads query includes tertiary/residential/track/path which are
not equivalent to "principais vias de comunicação" in the Cabral study area.

Note on Option A: Santiago downloads all features from the Geofabrik PBF for the island + 1 km buffer; nearest distance for all candidates is computed in one pass. This replaces the per-point `dist=30000` Overpass query used in Fogo and avoids NaN values for candidates far from sparse features. The 3 NaN values in Fogo (sites 41, 385, 429) were probably caused by the 30 km radius (hypothesis tested by C-9).

Note on waterway tags: confirmed Fogo original (L274): only `['stream', 'river', 'canal']`.
No `ditch` or `drain`. Santiago uses the same tags under Option A.

OSM snapshot date for Santiago: [date — to fill at extraction time, before Phase 1 commit].
All criteria use the same OSM snapshot. The snapshot date is recorded in Phase 1 §9.

**OSM snapshot rule (snapshot-once):** the first Geofabrik Cabo Verde extract downloaded at Phase 1 extraction time is the definitive snapshot. Re-downloading is prohibited after Phase 1 begins. The extraction script must record the Geofabrik URL, the download date, and the SHA-256 of the PBF file. Any re-download would constitute a deviation (DEV-S-###).

**D2 source (Centro de RSU — Praia urban limit):** IDECV `divisao_admin:cidade`, filtered to nom_zvc='Cidade da Praia' (confirmed present in GetCapabilities 2026-10-25; feature count = 1 polygon). Distance computed to the polygon boundary (dist = 0 if candidate is inside the polygon → excluded under Cabral 500 m buffer). See §5.2 for the distance rule. If the polygon is absent at Phase 1: fall back to OSM `place=city` boundary for Praia.

**Area protegida source:** IDECV `areas_especiais:area_protegida` (confirmed present 2026-10-25). This layer replaces WDPA as primary source. The `area_protegida.shp` used in Fogo came from the same IDECV service (confirmed by CRS=EPSG:4826 and field names: ilha, categorias, designacao). If the IDECV layer covers fewer than 5 polygons on Santiago: fall back to WDPA (latest release at Phase 1 time, version recorded in Phase 1 §9).

---

## Annex C — Cabral (2012) weight tables

Source: Cabral (2012), hdl.handle.net/10362/8627, Tables 11–16 (pp. 54–55).

### Level 1 weights (4 groups)

| Group | Cabral weight (%) | Leaf weight sum check |
|---|---|---|
| A — Uso do solo | 20.8 | 3.85 + 3.14 + 2.62 + 3.85 + 1.58 + 3.14 + 2.62 = 20.8 ✓ |
| B — Hidrogeologia | 40.6 | 20.3 + 10.15 + 10.15 = 40.6 ✓ |
| C — Morfologia | 9.8 | 7.35 + 2.45 = 9.8 ✓ |
| D — Acessibilidade | 28.8 | 9.5 + 19.3 = 28.8 ✓ |

CI (level 1) = 0.047, CR = 0.052 (Cabral 2012, Tab. 11). Acceptable (< 0.1).

### Leaf weights

| Id | Criterion | Within-group weight | Final weight (%) |
|---|---|---|---|
| A1 | Áreas edificadas | 18.5% of A | 3.85 |
| A2 | ZDTI | 15.1% of A | 3.14 |
| A3 | Orla costeira | 12.6% of A | 2.62 |
| A4 | Património cultural | 18.5% of A | 3.85 |
| A5 | Áreas agrícolas | 7.6% of A | 1.58 |
| A6 | Aeroporto | 15.1% of A | 3.14 |
| A7 | Áreas protegidas | 12.6% of A | 2.62 |
| B1 | Unidades hidrogeológicas | 50% of B | 20.3 |
| B2 | Pontos de água | 25% of B | 10.15 |
| B3 | Ribeiras e eixos de drenagem | 25% of B | 10.15 |
| C1 | Declive | 75% of C | 7.35 |
| C2 | Orientação de vertentes | 25% of C | 2.45 |
| D1 | Principais vias de comunicação | 33% of D | 9.50 |
| D2 | Centro de RSU | 67% of D | 19.30 |

Note on B1 CI: Cabral (2012, Tab. 14) reports CI = CR = 0.000. The published pairwise matrix is
not exactly reciprocal (entry B1.2:B1.1 = 2 rather than the implied 3; see §3 of the dissertation).
The actual CI ≈ 0.004, which rounds to 0 at the published precision. The published weights
(13.3 / 27.8 / 58.9%) correspond to the geometric mean of the published non-reciprocal matrix.
These weights are used as-is; the discrepancy is noted for completeness.

---

## Annex D — Outcome sentence templates

For use in §7.10 of the article. Fill in actual values at reporting time.

### S0 (regression — must pass)
- Pass: "The SAW/mm/opt cell reached 100% on all 500 draws and R = 0 on all draws, confirming
  the scorer implementation."
- Fail: "S0 FAILED: [describe]. Analysis halted; results not reported."

### S1 (replication of mm > vec)
- Confirmed (condition met, CI excludes 0): "Under S-[T/N], SAW/mm/greedy exceeded SAW/vec/greedy
  by [X] pp (95% CI: [[a], [b]] pp), replicating the main Fogo finding."
- Not confirmed (condition met, CI includes 0): "Under S-[T/N], the mm advantage over vec was
  [X] pp (95% CI: [[a], [b]] pp), consistent with zero. TV = [tv]."
- Not tested (condition not met, TV < 0.05): "TV(vec) = [tv] < 0.05; S1 was not tested.
  All cells are reported descriptively."

### S2 (reversal under vector scoring)
- Confirmed: "The SAW/vec/greedy cell exceeded SAW/vec/opt by [X] pp (95% CI: [[a], [b]] pp)
  under S-[T/N], replicating the Fogo greedy reversal."
- Not confirmed: "The reversal was [X] pp (95% CI: [[a], [b]] pp), consistent with zero."
- Not tested: "TV_W = [tw] < 0.05; S2 not tested."

### S3a (E1-V and E1-W both < 100%)
- Both confirmed: "E1-V optimal was [V]% and E1-W optimal was [W]% under S-[T/N], both below
  100%, confirming that within-group distortion alone moves exact assembly off the frontier
  (cell W), and the full mechanism (cell V) also reduces frontier attainment."
- One or both not confirmed: "E1-[V/W] optimal reached [X]%. TV_W = [tw]."

### S3b (E1-V < E1-W)
- Confirmed: "E1-V optimal ([V]%) was below E1-W optimal ([W]%) by [X] pp, replicating the
  direction observed in Fogo and the E6 experiment."
- Not confirmed: "E1-V ([V]%) was at or above E1-W ([W]%), inconsistent with the Fogo direction."

### S4 (SAW vs TOPSIS: descriptive)
- "SAW and TOPSIS Q2 cells are reported in Table X. No sign was predicted; the comparison is
  descriptive."

### S5 (Q2 > Fogo 56.8%)
- Condition not met (max point-mass on continuous criteria ≥ 0.5): "Point-mass share exceeded
  0.5 on criterion [j] ([pm]). S5 condition not met. Q2 = [Q2]% reported descriptively."
- Confirmed (Q2 > 56.8%): "SAW/vec/opt reached [Q2]% under S-[T/N], above the Fogo result
  (56.8%), consistent with the E6 prediction."
- Not confirmed (Q2 ≤ 56.8%): "SAW/vec/opt was [Q2]% under S-[T/N], at or below Fogo (56.8%)."

### S6 (R(vec,grd) > R(vec,opt) — greedy has more regret)
- Confirmed: "R(SAW, vec, grd) exceeded R(SAW, vec, opt) by [X] pp (95% CI: [[a], [b]] pp)
  under S-[T/N], consistent with Fogo (1.36 pp [0.95, 1.74 pp]; below δ=2.5 pp)."
- Not confirmed: "The difference was [X] pp (95% CI: [[a], [b]] pp), inconsistent with Fogo."
- Not tested: "TV_W = [tw] < 0.05; S6 not tested."

### S7a (R(E1-B, opt) > 0 — positive value cost of between-group distortion)
- Confirmed: "R(E1-B, opt) was [X] pp (95% CI: [[a], [b]] pp) under S-[T/N], with the CI
  excluding zero, consistent with Fogo (4.53 pp mean, median 5.50 pp; 28% of draws R = 0). Low-risk prediction."
- Not confirmed: "R(E1-B, opt) was [X] pp (95% CI: [[a], [b]] pp), consistent with zero."
- Not tested: "TV_B(vec) = [tv] < 0.05; S7a not tested."

### S7b (R(E1-B, opt) < R(E1-W, opt) — Fogo ordering)
- Confirmed: "R(E1-B, opt) was [b] pp, below R(E1-W, opt) = [w] pp by [d] pp, replicating the Fogo ordering (4.53 < 6.47 pp)."
- Not confirmed: "R(E1-B, opt) = [b] pp ≥ R(E1-W, opt) = [w] pp; Fogo ordering not replicated."
- Not tested: "TV_B < 0.05 or TV_W < 0.05; S7b not tested."

### S0–S7: no-results template (branch abandoned)
- "Branch S-[T/N] was abandoned: [N_adm < 100 / n_trios > 50M or < 10000 / validity check failed].
  No Q2 results are reported for this branch."

### S2+S6 joint outcome (Q2–R discordance replication)
- Both confirmed (S2: greedy Q2 > optimal Q2; S6: greedy R > optimal R):
  "Under S-[T/N] with vector normalisation, exact assembly reached the frontier
  less often than greedy assembly (S2) but achieved less value regret (S6),
  replicating the Q2--R discordance observed in Fogo (Q2 diff: $\AsmVecSAW$~pp;
  R diff: $\RegrDiffSAWvec$~pp, below δ)."
- S2 confirmed, S6 not confirmed:
  "Frontier attainment replicated (S2 confirmed); the Q2--R discordance did not replicate
  (S6 not confirmed): exact assembly regret was [X] pp, [above/below] greedy [Y] pp."
- S2 not confirmed, S6 confirmed:
  "The greedy Q2 advantage did not replicate (S2 not confirmed); however, exact assembly
  achieved [X] pp less value regret (S6 confirmed)."
- Both not confirmed:
  "Neither the Q2 reversal (S2) nor the regret advantage (S6) replicated under S-[T/N]."

---

## Pre-commit checklist

- [x] Run `scripts/santiago_grid.py --mode fogo-check` (replaces deprecated `_verify_fogo_grid.py`): **CONFIRMED** 473/473 coordinates at 0.0 m, N_adm=389, n_trios=1,944,653. Convention: 32626+floor1m+land+geol_dissolved. All trials documented in §3 PRE-A table. (2026-10-25–26)
- [x] Note: did NOT choose between boundary sources based on which reproduces 473. Convention (floor1m+land) read from `Landfill_NSGA2_Paper_Final.ipynb` and confirmed by 473/473 coordinate match.
- [x] Complete Annex B: source confirmed as `Landfill_NSGA2_Paper_Final.ipynb` (SHA documented in §0). Queries identical to Zenodo script (same tags, same dist=30000). Source citation updated from L271-287 to notebook.
- [ ] Fill `[HASH_F0]` (this commit's hash — fill after `git commit`, before push)
- [x] Fill `[HASH_CODE]` = 94b5baf (includes new R denominator; scoring algorithm frozen at 022931e)
- [x] Fill boundary source and version for S-T: IDECV `divisao_admin:ilha`, nom_ilha='SANTIAGO', EPSG:32627
- [x] Fill boundary source and version for S-N: IDECV `divisao_admin:concelho`, 3 concelhos, EPSG:32627
- [x] OSM snapshot rule: snapshot-once (first Geofabrik download at Phase 1 is definitive; SHA recorded in Phase 1 §9; re-download prohibited). Buffer: island + 1 km for S-T, 3 concelhos + 1 km for S-N.
- [x] Area protegida source: IDECV `areas_especiais:area_protegida` (confirmed 2026-10-25; same service as Fogo; replaces WDPA). Fallback: WDPA latest at Phase 1.
- [x] Confirm ZDTI layer presence/absence: PRESENT (`areas_especiais:zdti`). C-4 NOT triggered. (2026-10-25)
- [x] D2 source confirmed: IDECV `divisao_admin:cidade`, nom_zvc='Cidade da Praia'; distance to polygon boundary (not centroid), dist=0 inside → excluded.
- [x] DEM: ASTER GDEM v3 (same as Fogo) confirmed from `Landfill_NSGA2_Paper_Final.ipynb`.
- [x] Raster sampling: nearest-pixel confirmed from notebook.
- [x] Aspect flat rule: Sobel < 1e-9 → norm_asp = 0.5 confirmed from notebook.
- [ ] Assomada (A/A1) P-C: two research summaries of Gomes (2007) confirm Intermédia; page number in original thesis not yet confirmed (RIA SSL blocked 2026-10-26). Before tag: verify in Gomes (2007) p. [X] or Pina (2009) and update T1 row A accordingly (remove note, add page citation, or change to Recente if source says so).
- [ ] Fill OSM snapshot date and DEM release version (at Phase 1 extraction time, before Phase 1 commit)
- [ ] Fogo boundary test with IDECV ilha + floor1m + land (see §4 of review; determines whether Santiago uses ilha boundary or geologia dissolved)
- [x] → **DONE (2026-10-26):** IDECV ilha + floor1m + land gives 473/473 at 0.0 m, N_adm=389, n_trios=1,944,653. Result is identical to geologia dissolved. The boundary type does not matter; Santiago uses IDECV ilha as declared.
- [ ] check_consistency.py exit 0 after adding any PRESPEC-related BAD_PHRASE
