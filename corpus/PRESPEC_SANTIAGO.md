# PRESPEC_SANTIAGO.md — Santiago de Cabo Verde Replication (Phase 0)

```
Status:       DRAFT — not yet committed
Immutability: starts at git tag `prespec-santiago-f0` (not at any specific commit)
Phase 0 hash: [HASH_F0]   (fill in TASKS.md after the tag is created)
Code hash:    022931e     (scoring algorithm frozen)
Written:      2026-10-xx
```

Phase 0 is immutable from commit [HASH_F0].
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
| Cabral (2012) | hdl.handle.net/10362/8627 | 2026-10-xx | — (PDF, not a data file) | full text: AHP weights (Tab. 11–16, pp. 54–55), exclusion buffers (Tab. 18–26), hydrogeological units (pp. 45–46) and B1 matrix | — |
| Fogo source files | NSGA-II Zenodo 17704387, script L257 (`permeabili == 'Baixa'`) and L428 (aspect rule `np.where(90<=asp<=180, 0,1)`) | 2026-10-xx | — | permeability classes; aspect binary rule | — |

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
mc_unified.py, validate_core.py, compute_regret.py, run_e1.py) is frozen at commit 022931e.
The Santiago-specific extraction scripts (grid generation, OSM/DEM/WFS feature extraction) and
the generalised pipeline (supporting variable numbers of criteria and groups) do not yet exist.
They will be written and committed before Phase 1 begins. That commit hash must be recorded in
Phase 1 §9; no criterion value, distance, or normalised score may be computed before that commit.

**Mandatory regression test before Phase 1:** the generalised code, run with the Fogo
configuration (11 criteria, 3 groups, weights from `e1_weights_k200.npy`), must reproduce
results/unified/mc_unified_raw.csv bit-for-bit. SHA-256 of that file is registered at commit
022931e. If the regression fails, Phase 1 does not start.

**Pre-MC assertion:** `max|local_score - make_scorers(w)| < 1e-12` on 20 random weight vectors
drawn with `seed=99`. Abort if any assert fails.

**Lock file:** scripts that compute scores or Q2 for Santiago refuse to run unless
`corpus/PRESPEC_SANTIAGO_F1.lock` exists. This file is created only at Phase 1 commit.

**Grid:** 1 km × 1 km cells; cells with less than 50% land coverage discarded; candidate = centroid.

Boundary source:
- S-T: Santiago island boundary from [SOURCE — to fill before commit: IDECV layer or OSM coastline,
  version/date].
- S-N: Southern Region boundary (Praia, São Domingos, Ribeira Grande) from [SOURCE].

**CRS:** EPSG:32627 (WGS 84 / UTM Zone 27N, central meridian 21°W) for all spatial distance
computations. Santiago (approximately 23.4°–23.8°W) lies within UTM Zone 27, whereas Fogo
(approximately 24.0°–24.4°W) lies within UTM Zone 26 (EPSG:32626). Using EPSG:32626 for Santiago
would introduce a scale error of approximately 0.06% (about 6 m per 10 km), negligible for 1 km
grid cells but incorrect. The IDECV GeoJSON data is in EPSG:4826 (WGS 84 / Cape Verde National,
a Lambert projection) and must be reprojected to EPSG:32627 before distance computation.
Distances between candidates: great-circle (haversine), same as Fogo.

Fogo grid validation (REQUIRED before commit):
- Run `scripts/_verify_fogo_grid.py` with the Fogo island boundary and the declared rule
  (1 km × 1 km, ≥ 50% land coverage). Record N_Fogo.
- If N_Fogo = 473: the declared rule reproduces the published dataset. No deviation.
- If N_Fogo ≠ 473: record as DEV-S-001: "declared rule gives N = [N_Fogo]; published
  dataset has 473; difference unexplained. Declared rule applied to Santiago."
  The unexplained difference between 473 (published paper) and 524 (original NSGA-II repo)
  most likely results from different island boundary shapefiles.

**Trio enumeration:** n_trios computed from geometry only (trace formula: tr(A³)/6, where A is the
binary adjacency matrix of valid pairs) BEFORE any criterion is extracted. Note: for N ≈ 800–900
candidates and 20% admissible, n_trios may reach 80–120 million without distance filtering.
Limit: 50 000 000 trios. If exceeded, increase spacing by 0.25 km until below limit; if spacing
reaches 5 km, the branch is abandoned and reported.

Minimum n_trios: if n_trios < 10 000 (can occur in S-N with 10 km separation), the branch is
reported as degenerate. Decrease spacing by 0.25 km until n_trios ≥ 10 000 and n_trios ≤ limit.

**Normalisation constants:** over the admissible set A' (candidates with zero exclusion
distance excluded). Missing values imputed to range midpoint (same as Fogo).

**Monte Carlo:** w ~ Dirichlet(κ · w_AHP), κ = 200, 500 draws, seed 42. S-T uses the Fogo
weight draws (same random stream, same draws per seed). S-N uses w ~ Dirichlet(κ · w_Cabral),
κ = 200, 500 draws, seed 42 (independent stream, separate call, same seed for reproducibility).

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
| slope | slope (degrees) | **COST**: min degrees = best. | `gdaldem slope`, units = degrees, DEM = Copernicus GLO-30 [version, date] | Copernicus GLO-30 |
| aspect | binary: 0 if azimuth ∈ [90°, 180°] (leeward), 1 otherwise; flat cells (NaN) = 0.5 (from Fogo `impact_function`, L428) | Special (binary, leeward coded as 0 in objectives, as 1 in SAW score). | Rule inherited from Andrade (2015); not a physical claim. | Copernicus GLO-30 |
| roads | dist_roads (m), query: Annex B L275–277 | **COST**: min distance = best. (`COST = {'roads', ...}`) | OSM elements downloaded for the whole island boundary (Option A: no radius limit); distance computed in EPSG:32627. Note on Fogo: Fogo script uses `dist=30000` (30 km radius per query), which covered Fogo (≈13 km radius). Santiago (≈55 km N–S) requires Option A to avoid NaN for candidates far from sparse features. | OSM snapshot [date — Phase 1] |
| rivers | dist_streams (m), query: Annex B L274 | **INV**: max distance = best. (`INV = {'rivers', ...}`) | OSM, Option A. Tags: waterway=[stream, river, canal] (Annex B L274; no ditch/drain in Fogo original). | OSM snapshot [date — Phase 1] |
| coast | dist_coastline (m), query: Annex B L282 | **INV**: max distance = best. | OSM, Option A. | OSM snapshot [date — Phase 1] |
| protected | dist_protected_area (m) | **INV**: max distance = best; = 0 inside → exclusion. | Source TBD: IDECV protected area layer if available; else WDPA [version]. Same rule as Fogo (`area_protegida.shp`, island-wide shapefile). | [to fill before commit] |
| wells | dist_wells (m), query: Annex B L278–280 | **INV**: max distance = best. (`INV = {'wells', ...}`) | OSM, Option A. C-2 applies if < 20 features on Santiago. | OSM snapshot [date — Phase 1] |
| urban | dist_urban_core (m), query: Annex B L272 | **BENEFIT**: max distance = best. | OSM, Option A. | OSM snapshot [date — Phase 1] |
| aero | dist_aerodrome (m), query: Annex B L273 | **BENEFIT**: max distance = best. Note: only features within Santiago island; aerodrome on Maio island excluded. | OSM, Option A. | OSM snapshot [date — Phase 1] |
| cult | dist_cultivation (m), query: Annex B L280–282 | **BENEFIT**: max distance = best. | OSM `landuse=farmland/farmyard/orchard/vineyard/allotments`, Option A. C-7 contingency: if OSM returns fewer than 50 agricultural polygons on Santiago → use WorldCover 2021 class 40 (Cropland), declared as C-7. In S-N: use `carta_agricola_st` (IDECV, SHA as §0) as primary; if OSM is used instead, declared as C-8. | OSM snapshot [date — Phase 1] |

### 4.3 Permeability rule P-F (main) and P-C (sensitivity)

**Important:** for the S-T distance criterion, ONLY whether a polygon is classified as Baixa
matters. The subclasses within non-Baixa (Média, Alta, "não-Baixa", "sem análogo") are all
equivalent: they are not included in the Baixa zone set and the candidate's perm distance is
the minimum distance to any Baixa polygon. If a cod_form has no direct Fogo analog, its default
classification is "not Baixa" (NC), and it does not enter the low-permeability zone set unless
a sensitivity run states otherwise.

**P-F (main rule for S-T):** classifies cod_form by lithology following the Fogo convention
(`landfill_nsga2_optimization.py` L257, `permeabili == 'Baixa'`). Three values:
- Baixa: formations with "Mantos" (compact lava flows/sheets) in `lit` — direct Fogo analog.
- não-Baixa: formations with direct Fogo analog to a non-Baixa class (Média = cinder cones,
  talus; Alta = ash, alluvium, dunas).
- sem análogo em Fogo: intrusive rocks (CA, γ), carbonatites (cb), dykes/necks (chb, chy, chφ),
  breccias (B), conglomerates (CBm, cong), composite codes (CB where CBm component is involved).
  Default = NC (not included in Baixa zones). Sensitivity: classify each as Baixa; run only if
  their combined area share in A' > 2%.

Note on aspect: in the Fogo impact function (L428), flat cells (NaN aspect) receive
`norm_asp = 0.5`. The rule `0 if [90,180], 0.5 if flat, 1 otherwise` is reproduced exactly.

**P-C (sensitivity rule for S-T and B1 mapping for S-N):** classifies cod_form by
hydrogeological unit following Serralheiro (1976) as interpreted in Cabral (2012, pp. 44–46).
Mapping in Annex A, column P-C.

Key divergence: under P-F, PA/PA1 is Baixa (basaltic lava flows). Under P-C, PA/PA1 is
Intermédia (main Santiago aquifer, Gomes 2007). PA is likely the most areally extensive
formation. A note on this divergence will appear in the Limitations section.

### 4.4 Rivers rule

OSM waterway=* as primary. If OSM returns fewer than 20 waterway features on Santiago: use DEM
flow accumulation ≥ 1 km² (same algorithm as Fogo) → C-3.

### 4.5 Weights and groups

Fogo AHP weights (Table 2 of main article, fogo_constants.py). Groups G1–G3, objectives F1–F3,
orientations as §5 of main article.

### 4.6 Exclusion

Distance to protected areas = 0 only (same as Fogo).

---

## 5. Branch S-N

### 5.1 Area

Southern Region of Santiago: concelhos of Praia, São Domingos, and Ribeira Grande de Santiago.
Area approximately 395 km² (Cabral 2012). Boundary: [SOURCE — to fill before commit].

### 5.2 Criteria

Raw variables are extracted for the S-N region. Cabral buffers (§5.3) define exclusions;
normalisation over A' is the experimental factor.

| Id | Criterion | Raw variable / orientation | Exclusion | Source |
|---|---|---|---|---|
| A1 | Built-up | distance to OSM building=* or place=*, benefit | < 500 m | OSM |
| A2 | ZDTI | distance to ZDTI zones, benefit | < 500 m | IDECV if layer present (check GetCapabilities); else omit → C-4 (§5.4) |
| A3 | Coast | distance to coastline, benefit | < 80 m | OSM coastline |
| A4 | Cultural heritage | distance to Cidade Velha UNESCO buffer zone, benefit | < 500 m | UNESCO WHC boundary (public shapefile) |
| A5 | Agriculture | distance to agricultural protection zones, benefit | inside zones | IDECV `carta_agricola_st`, SHA as §0 |
| A6 | Airport | distance to Praia International Airport (OSM aeroway=aerodrome), benefit | < 3 000 m | OSM |
| A7 | Protected areas | distance to WDPA polygons, benefit | < 500 m | WDPA [version] |
| B1 | Hydrogeological unit | categorical score (see §5.5); orientation benefit | recente unit → exclusion (score = 0) | IDECV `geologia_santiago`, mapping Annex A column P-C |
| B2 | Water points | distance to OSM amenity=drinking_water or man_made=water_well, benefit | < 400 m | OSM; if < 20 features → INGRH inventory → C-5 |
| B3 | Streams | distance to OSM waterway=*, benefit | < 20 m | OSM; if < 20 features → DEM flow acc. ≥ 1 km² → C-6 |
| C1 | Slope | gdaldem slope (degrees), cost | > 20° excluded | Copernicus GLO-30 |
| C2 | Aspect | v(θ) = (1 − cos(θ − 22.5°)) / 2, benefit; flat cells (undefined aspect) = 0.5 | — | Copernicus GLO-30 |
| D1 | Main roads | distance to OSM highway=primary or highway=secondary (national network), cost | < 50 m | OSM; Annex B for exact tag rule |
| D2 | MSW centre | distance to Praia urban limit (OSM or IDECV), cost | < 500 m | [source to fill] |

### 5.3 Exclusion zones (Cabral buffers)

Cells are excluded (removed from A') if they violate any buffer in §5.2. B1 recente (score = 0)
also serves as an exclusion. Slope > 20° serves as an exclusion for C1.

### 5.4 ZDTI rule

ZDTI (Zonas Demarcadas de Turismo Integrado) layers will be checked in the IDECV GetCapabilities
response. If present: use as A2. If absent: A2 is omitted, its weight (3.14% of total) is
redistributed proportionally to the remaining 6 Group A criteria. No manual digitisation from
PDF is performed. No Fogo control is triggered by ZDTI absence.

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

Cabral (2012) AHP leaf weights (Annex C). Weight of A2 redistributed if absent (§5.4).
Groups: A (criteria A1–A7 or A1–A6 without ZDTI), B (B1–B3), C (C1–C2), D (D1–D2).
All four group objectives F_A, F_B, F_C, F_D are maximised (4-dimensional frontier).
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
| S3b | E1-V optimal < E1-W optimal (direction observed in Fogo and E6) | TV_W(vec) ≥ 0.05 | E1 direction replication |
| S4 | SAW minus TOPSIS per cell: no sign predicted | — | Descriptive |
| S5 | Q2(SAW, vec, opt) in branch b > 56.8% (Fogo result) | max_{j ∈ non-binary} point-mass share (fraction of A' at modal value, continuous criteria only) < 0.5. Note: binary criteria (aspect in S-T; B1 in S-N after normalization) are excluded from this condition. In Fogo: perm point-mass = 350/389 = 0.90 → S5 would not have been tested; Santiago should have smoother distributions. | Risky: predicts weaker mechanism under smoother distributions (E6 reasoning) |
| S6 | R(SAW, vec, grd) > R(SAW, vec, opt), 95% CI excludes 0. Fogo reference: R(vec,grd)=77.15 pp, R(vec,opt)=61.19 pp, difference=15.96 pp [95% CI: 12.6, 19.5 pp]. | TV_W(vec) ≥ 0.05 | Greedy has more regret than optimal under vector scoring; consistent with Q2 reversal (S2) |

If a condition fails, the prediction is not tested and the cell is reported descriptively
(see Annex D for templates).

---

## 7. Validity criteria

Checked in Phase 1, before any score is computed:

1. N_adm ≥ 100
2. Variance > 0 for every criterion on A'
3. `validate_core` passes: frontier non-dominance and completeness
4. B1: every polygon in A' has a non-null P-C class. If > 5% of A' polygons are NC,
   report area share as limitation but do not abandon branch. Apply declared defaults from T1.

TV(vec) < 0.05 does not invalidate the branch; it causes S1, S2, S3, S5, S6 to be
reported as not-tested (not as failures).

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

1. SHA-256 of every spatial layer extracted (CRS, feature count, date)
2. N_cand, N_excl, N_adm; n_trios
3. Per criterion on A': amplitude ρ_j (vec, ranks), point-mass share (fraction of A'
   at poles), TV, TV_B, TV_W, m_eff
4. Resolution of every condition in §6 (TV(vec) ≥ 0.05? max point-mass share < 0.5?)
5. Validity checks of §7

---

## 10. Deviation policy

Any change after [HASH_F0] that modifies a prediction, threshold, criterion definition,
or weight in §3–§6 must be logged as DEV-S-NNN with date, reason, and expected direction
of effect. No prediction, threshold, or definition in §3–§6 may be changed after Phase 1
commit [HASH_F1].

Pre-declared contingency rules (not deviations; responses are fully specified here):
- C-1: Fogo grid count. If `_verify_fogo_grid.py` gives N ≠ 473: state the discrepancy; apply declared rule to Santiago unchanged (see §3).
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

All sensitivity runs are pre-declared here. They are all **descriptive**: predictions S0–S6
are evaluated only on the main analysis. Sensitivity results are reported in a supplementary
table. No sensitivity run can replace the main analysis.

| ID | Description | Scope | When runs |
|---|---|---|---|
| SENS-1 | S-T with P-C rule instead of P-F (perm criterion only) | S-T | Always; after main S-T results are sealed |
| SENS-2 | S-T with CA, γ, cb, dφ reclassified as Baixa (a single combined run, not formation-by-formation) | S-T | Always |
| SENS-3 | For each NC B1 cod_form (calc, cong, dφ, φ, null) with area share > 2% in A': reclassify to adjacent unit (one run per triggered formation) | S-N | If C-7 triggers; otherwise skip |
| SENS-4 | Contingency responses: C-2 (wells), C-8 (cult WorldCover), other C-x triggered | Both | If corresponding C-x triggers |
| SENS-5 (C-9) | Run Santiago extraction pipeline on Fogo with Option A (island-wide download) and a contemporaneous OSM snapshot; compare dist_* columns with df_real_data_cached.csv: Spearman correlation, fraction of sites with |diff| > 100 m, ρ_j(vec) actual vs published. Report in supplementary. | S-T only | Always |

SENS-2 justification: classifying all four "no Fogo analog" intrusive formations as Baixa in a
single run avoids creating four separate analyses. The result tells whether the Baixa boundary
changes qualitatively when these formations are included.

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
("Tufo Brechas"). These features are not in Serralheiro's (1976) terrestrial scheme; they are
excluded from T1 and flagged in the Phase 1 data quality report. Their combined area share in A'
is reported in Phase 1 §9. If > 2%, they receive P-F = NC and P-C = NC (default: Base = 1.000).

Note on T1 count: the PLANO_TRABALHO V3 note listed "24 unique formations" (a typo; the same
list contained 25 items). The T1 below has 27 named formations because: (a) the initial count
omitted cod_form "A" (Formação da Assomada without numeric suffix); (b) the IDECV layer uses
cod_form "CB" as a composite code combining two formations (Flamengos + Orgãos) that are also
separately encoded as λρ, λρ1, and CBm; this composite code is a data artefact but represents
real polygons that must be classified.

† Symbol in the B1 score column denotes an NC case with a declared default classification.
The default follows P-F class (Alta→Recente/excl., Média→Base, Baixa→Base or Intermédia as
noted per row). A sensitivity run is triggered for each NC cod_form whose area share in A' > 2%.

| cod_form | lit (IDECV, key terms) | grupo | P-F class | P-F source | P-C unit | B1 score | P-C source |
|---|---|---|---|---|---|---|---|
| A | Formação da Assomada; Mantos e Piroclastos (Pliocénico) | — | **Baixa** | "Mantos" (lava flows) per lit; lava = Baixa by P-F rule | **Intermédia** | 0.472 | By analogy with PA: Assomada = post-PA subaerial lavas; similar hydrological role. Not explicitly listed in Cabral (2012) pp. 44–46; assigned by stratigraphic position (Serralheiro 1976). |
| A1 | Formação da Assomada; Mantos e Piroclastos subaérios (basanitos, basanitóides, limburgiticos) (Pliocénico) | — | **Baixa** | "Mantos subaérios" (subaerial lava flows); lava = Baixa | **Intermédia** | 0.472 | As A; PA1-equivalent by stratigraphy |
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
| cong | Conglomerados e facies terrestres (Pliocénico-Miocénico) | — | **Média** | Terrestrial conglomerates; variable consolidation; not compact lava | **Intermédia** (†, stratigraphic rule) | 0.472† | Plio-Miocénico age → Intermédia by stratigraphic rule. Not explicitly listed in Cabral (2012). Sensitivity: Base (1.000). Run if cong area share in A' > 2%. |
| d | Dunas (Quaternário) | — | **Alta** | Sandy dunes; very high permeability | **Recente** | 0 (excl.) | Quaternary = Recente |
| de | Duna, eluviões (Quaternário) | — | **Alta** | Dunes + eluvial deposits | **Recente** | 0 (excl.) | As "d" |
| dv | Depósitos de vertente (Quaternário) | — | **Média** | Slope deposits; heterogeneous; more permeable than lavas | **Recente** | 0 (excl.) | Quaternary = Recente |
| dφ | Domas e chaminés (fonólitos e traquitos); Fonólitos e traquitos (Pliocénico-Miocénico) | Fonólitos e traquitos | **Baixa** | "Domas" (lava domes) = compact extrusive phonolite; by Fogo analogy compact lava flows = Baixa. NOTE: no explicit Fogo analog (Fogo has no phonolite); classified as Baixa by the "compact volcanic = Baixa" principle. Sensitivity: NC. | **Intermédia** (†, stratigraphic rule) | 0.472† | Plio-Miocénico age → Intermédia by stratigraphic rule. Not in Cabral (2012). Sensitivity: Base (1.000). |
| γ | Rochas granulares (gabros feldspatóidicos, piroxenitos alcalinos, sienitos feldspatóidicos); Complexo eruptivo interno, antigo (Ante-Miocénico médio) | Complexo eruptivo interno, antigo | **sem análogo em Fogo (default: NC)** | Granular intrusive rocks; no Fogo analog for intrusive rocks. Default NC. Sensitivity: Baixa. | **Base** | 1.000 | Cabral (2012) p.45: γ = gabros = Base unit |
| λρ | Formação dos Flamengos; Mantos, piroclastos, chaminés (Miocénico médio) | — | **Baixa** | "Mantos" (lava flows); the dominant component | **Base** | 1.000 | Cabral (2012) p.45: λρ = Formação dos Flamengos = Base unit |
| λρ1 | Formação dos Flamengos; Mantos, piroclastos, chaminés e hialoclastitos, submarinos (Miocénico médio) | — | **Baixa** | As λρ; submarine hyaloclastites = solidified lava glass, generally impermeable | **Base** | 1.000 | As λρ |
| φ | Fase lávica pós Formação dos Orgãos (rochas traquito-fonolíticas); Mantos; Piroclastos (Pliocénico-Miocénico) | Fonólitos e traquitos | **Baixa** | "Mantos" (lava flows component); compact phonolitic/trachytic lavas | **NC (default: Intermédia)** | 0.472† | Post-Orgãos, pre-PA stratigraphically. Default = Intermédia: by age position (between Base and Intermédia units) and because compact phonolite lavas are the main constituent of the PA aquifer. Sensitivity: Base (1.000). |
| null | Mantos submarinos, inferiores e superiores (hialoclastitos); Piroclastos; Tufo Brechas (Pliocénico-Miocénico) | — | **Baixa** | "Mantos submarinos (hialoclastitos)" = submarine hyaloclastites; direct analog with λρ1 ("Formação dos Flamengos Mantos, piroclastos, chaminés e hialoclastitos, submarinos") which is Baixa. | **NC (default: Intermédia)** | 0.472† | 136 features with null cod_form. Submarine lavas are age-correlative with Pico da Antónia (Plio-Miocénico); default Intermédia by stratigraphic rule. Sensitivity: Base (1.000). |

Summary for distance computation (S-T, P-F main rule):
- Baixa polygons (used in `dist_low_permeability`): λρ, λρ1, PA, PA1, A, A1, φ, dφ, CB, null
- sem análogo em Fogo (default NC, not in Baixa set): CA, γ, cb, chb, chy, chφ, B, CBm, cong
- não-Baixa Média: MV, dv
- não-Baixa Alta: a, a dv, a e, c, d, de, calc

Summary for B1 score (S-N, P-C) using stratigraphic rule for NC cases:
- Base (score = 1.000): CA, λρ, λρ1, CB, CBm, B, cb, γ, chb, chy, chφ [Ante-Miocénico + Miocénico médio from Cabral]
- Intermédia (score = 0.472): PA, PA1 [from Cabral]; A, A1, calc, cong, dφ, φ, null [†, stratigraphic rule: Plio-Miocénico → Intermédia]
- Recente / excluded (score = 0): MV, a, a dv, a e, c, d, de, dv
- Stratigraphic rule: Ante-Miocénico médio and Miocénico médio → Base; Plio-Miocénico → Intermédia; Quaternário and pyroclastic cones → Recente. Applied to all NC cases (not in Cabral 2012 pp. 44–46). Sensitivity for each NC case = adjacent unit (see individual rows). A, A1 have marker † because they are assigned Intermédia by this rule without explicit Cabral source.

---

## Annex B — OSM criterion definitions (verbatim from Fogo script)

Source: `landfill_nsga2_optimization.py` (NSGA-II pipeline, Zenodo 17704387), lines 271–287.
All criteria use `osmnx.features_from_point(lat, lon, tags, dist=30000)` to query features within
30 km of each candidate, then compute minimum Euclidean distance in EPSG:32626 (WGS 84 / UTM Zone 26N).

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

Note on Option A (island-wide download): instead of using the per-point `dist=30000` radius of
the Fogo script, Santiago uses a single island-wide OSM download (`ox.features_from_polygon(island_geom, tags)`)
and then computes nearest distance for all candidates. This avoids NaN values for candidates far
from sparse features (e.g., aerodrome is only in Praia; some candidates in Tarrafal are >45 km
away). The 3 NaN values in Fogo (sites 41, 385, 429) were likely caused by the 30 km radius.

Note on waterway tags: confirmed Fogo original (L274): only `['stream', 'river', 'canal']`.
No `ditch` or `drain`. Santiago uses the same tags under Option A.

OSM snapshot date for Santiago: [date — to fill at extraction time, before Phase 1 commit].
All criteria use the same OSM snapshot. The snapshot date is recorded in Phase 1 §9.

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
  100%, confirming that both TV components contribute to the mechanism."
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
  under S-[T/N], consistent with Fogo (15.96 pp [12.6, 19.5 pp])."
- Not confirmed: "The difference was [X] pp (95% CI: [[a], [b]] pp), inconsistent with Fogo."
- Not tested: "TV_W = [tw] < 0.05; S6 not tested."

### S5 (Q2 > Fogo 56.8%)
- Confirmed (Q2 > 56.8%, condition met): "SAW/vec/opt reached [Q2]% under S-[T/N],
  above the Fogo result (56.8%), consistent with the E6 prediction that smoother distributions
  reduce the mechanism's magnitude."
- Not confirmed (Q2 ≤ 56.8%, condition met): "SAW/vec/opt was [Q2]% under S-[T/N], at or
  below the Fogo result (56.8%). The E6 prediction was not confirmed."
- Not tested (condition not met, point-mass ≥ 0.5): "A point-mass share of [pm] ≥ 0.5
  was observed on criterion [j]; S5 condition not met. Q2 = [Q2]% reported descriptively."

### S1–S6: no-results template (branch abandoned)
- "Branch S-[T/N] was abandoned: [N_adm < 100 / n_trios > 50M or < 10000 / validity check failed].
  No Q2 results are reported for this branch."

### S2+S6 joint outcome (Q2–R discordance replication)
- Both confirmed (S2: greedy Q2 > optimal Q2; S6: greedy R > optimal R):
  "Under S-[T/N] with vector normalisation, exact assembly reached the frontier
  $\QtwovecOptimal$~pp less often than greedy assembly (S2) but achieved
  $\RegrDiffSAWvec$~pp less value regret (S6), replicating the Q2--R discordance
  observed in Fogo."
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

- [ ] Run `scripts/_verify_fogo_grid.py`: record N_Fogo, log C-1 if ≠ 473 (see §10)
- [ ] Note: do NOT choose between boundary sources based on which reproduces 473.
       Use the boundary that the original study was based on (from NSGA-II Zenodo repo); if not accessible, use IDECV island boundary and log the discrepancy as C-1.
- [ ] Complete Annex B: copy Overpass queries from Fogo script
- [ ] Complete Annex B: copy Overpass queries from Fogo script
- [ ] Fill `[HASH_F0]` (this commit's hash — fill after `git commit`, before push)
- [ ] Fill `[HASH_CODE]` = 022931e (already known; confirm unchanged)
- [ ] Fill boundary source and version for S-T and S-N
- [ ] Fill OSM snapshot date (for Phase 1; note that at Phase 0 no OSM data has been downloaded)
- [ ] Fill WDPA version
- [ ] Confirm ZDTI layer presence/absence in IDECV GetCapabilities
- [ ] Confirm D2 source (Praia urban limit)
- [ ] check_consistency.py exit 0 after adding any PRESPEC-related BAD_PHRASE
