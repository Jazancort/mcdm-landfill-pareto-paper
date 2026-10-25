# PRESPEC_SANTIAGO.md — Santiago de Cabo Verde Replication (Phase 0)

```
Status:       DRAFT — not yet committed
Phase 0 hash: [HASH_F0]   (fill at commit)
Code hash:    022931e     (frozen; all scores via scoring.make_scorers())
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
| `geologia_santiago_wfs.geojson` | IDECV WFS `https://geoservicos-ingt.gov.cv/geoserver/carto_base/wfs`, layer `carto_base:geologia_santiago` | 2026-10-25 | `23158bc940efbf6f9e6f4be01c88e8ca332fe8a7bf14e185cc64eb48b4becd33` | schema; 976 polygons; 28 unique `cod_form` values (1 null, 27 named); unique `lit` values mapped in Annex A | any area, distance, class share, amplitude, score |
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

(i)   a published peer-reviewed AHP landfill-siting study is available for the island;
(ii)  open-access digital geology at a resolution usable for distance computation is available;
(iii) the island area is between 300 km² and 1 000 km².

Santiago satisfies: (i) Cabral (2012), hdl.handle.net/10362/8627; (ii) IDECV WFS, confirmed
2026-10-25; (iii) approximately 991 km² total (S-N region: 395 km²).

Note on area bounds: Fogo ≈ 476 km² falls in [300, 1000]. Santiago (991 km²) is above Fogo but
within the declared bound. The bound was chosen to keep exact Pareto enumeration tractable; at
1 km grid spacing the number of trios grows as approximately (N_adm choose 3) / 6 which for
N_adm ≈ 700 is of order 10^7, within the 50 million trio limit (§3).

---

## 3. Common pipeline

**Code freeze:** the scoring and analysis code (mc_unified.py, compute_f8_mm_frontier.py,
run_e1.py, compute_regret.py, scoring.py, validate_core.py) is frozen at commit 022931e.
The Santiago-specific extraction scripts (grid generation, OSM/DEM/WFS feature extraction)
do not yet exist; they will be written and committed in a dedicated commit before Phase 1 begins.
That commit hash must be recorded in Phase 1 §9; no criterion value, distance, or normalised
score may be computed before that commit. All scores computed via `scoring.make_scorers()`.
Pre-Monte Carlo assertion: `max|local_score - make_scorers(w)| < 1e-12` on 20 random weight
vectors drawn with `seed=99` (different from Monte Carlo seed). Abort if any assert fails.

**Lock file:** scripts that compute scores or Q2 for Santiago refuse to run unless
`corpus/PRESPEC_SANTIAGO_F1.lock` exists. This file is created only at Phase 1 commit.

**Grid:** 1 km × 1 km cells; cells with less than 50% land coverage discarded; candidate = centroid.

Boundary source:
- S-T: Santiago island boundary from [SOURCE — to fill before commit: IDECV layer or OSM coastline,
  version/date].
- S-N: Southern Region boundary (Praia, São Domingos, Ribeira Grande) from [SOURCE].

CRS: EPSG:4826 (West Cape Verde, UTM Zone 26N) for all spatial operations, reproduced from the
IDECV data. Distances between candidates: great-circle (haversine).

Fogo grid validation (REQUIRED before commit):
- Run `scripts/_verify_fogo_grid.py` with the Fogo island boundary and the declared rule
  (1 km × 1 km, ≥ 50% land coverage). Record N_Fogo.
- If N_Fogo = 473: the declared rule reproduces the published dataset. No deviation.
- If N_Fogo ≠ 473: record as DEV-S-001: "declared rule gives N = [N_Fogo]; published
  dataset has 473; difference unexplained. Declared rule applied to Santiago."
  The unexplained difference between 473 (published paper) and 524 (original NSGA-II repo)
  most likely results from different island boundary shapefiles.

**Trio enumeration:** n_trios computed from geometry only (count of valid pairs × (N_adm-2) / 3,
or exact trace formula) BEFORE any criterion is extracted. Limit: 50 000 000 trios. If exceeded,
increase spacing by 0.25 km until below limit; if spacing reaches 5 km and n_trios still exceeds
limit, the branch is abandoned and reported as such.

If N_adm < 100: decrease spacing by 0.25 km while n_trios stays below limit; if impossible with
spacing ≥ 0.5 km, the branch is abandoned.

**Normalisation constants:** over the admissible set A' (candidates with zero exclusion
distance excluded). Missing values imputed to range midpoint (same as Fogo).

**Monte Carlo:** w ~ Dirichlet(κ · w_AHP), κ = 200, 500 draws, seed 42. S-T uses the Fogo
weight draws (same random stream, same draws per seed).

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

| Criterion | Raw variable | Rule | Source |
|---|---|---|---|
| perm | distance to P-F Baixa polygons (m) | **Rule P-F** (see §4.3 and Annex A): polygons of cod_form classified as Baixa in column P-F of T1. Benefit (larger distance = better). | IDECV `geologia_santiago`, SHA as §0 |
| slope | gdaldem slope (degrees), cost | Copernicus GLO-30 [version, date] |
| aspect | binary: 1 if azimuth ∈ [90°, 180°] (leeward), 0 otherwise; flat cells = 0.5 (as Fogo script). Benefit. | Copernicus GLO-30; rule inherited from Andrade (2015); not a physical claim |
| roads | distance to OSM highway=* (national roads), cost | OSM snapshot [date]; Overpass query in Annex B |
| rivers | distance to OSM waterway=*, cost | OSM; Annex B |
| coast | distance to coastline, cost | OSM coastline; Annex B |
| urban | distance to OSM place=city/town/village or landuse=residential, benefit | OSM; Annex B |
| aero | distance to OSM aeroway=aerodrome or helipad, benefit | OSM; Annex B |
| cult | distance to OSM leisure=park or historic=* or amenity=*, benefit | OSM; Annex B |
| protected | distance to WDPA protected areas; = 0 inside. Benefit. | WDPA [version]; or IDECV protected area layer if available |
| wells | distance to OSM amenity=drinking_water or man_made=water_well, cost | OSM; Annex B. If OSM returns fewer than 20 features on Santiago → C-2: use INGRH inventory if available; if unavailable → omit, redistribute weight proportionally, run Fogo-without-wells control (§8) |

### 4.3 Permeability rule P-F (main) and P-C (sensitivity)

Two permeability rules are declared:

**P-F (main rule for S-T):** classifies cod_form by lithology following the Fogo convention
(Andrade 2015, script L257): compact lava flows and intrusive rocks = Baixa. The classification
is made from the legend text (attribute `lit`) only, without examining the spatial distribution of
polygons. Mapping in Annex A, column P-F.

**P-C (sensitivity rule for S-T):** classifies cod_form by hydrogeological unit following Gomes
(2007) as interpreted in Cabral (2012, pp. 44–46): Base unit = Baixa; Intermédia = Média;
Recente = Alta. Mapping in Annex A, column P-C.

Key divergence: under P-F, the Pico da Antónia formation (PA, PA1) is classified as Baixa (it
consists of basaltic lava flows). Under P-C, PA/PA1 is classified as Intermédia (it is the main
Santiago aquifer, Gomes 2007). PA is likely the most areally extensive formation on the island.
This divergence will produce substantially different zero fractions and distance distributions
between P-F and P-C; the sensitivity run will quantify this.

A note on the P-F/P-C divergence will be added to the Limitations section of the paper.

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
default score declared in T1 (which may be 1.000, 0.472, or 0). A sensitivity run is triggered
for each NC cod_form with area share in A' > 2%, using the alternative score noted in T1. These
sensitivity runs are pre-declared and do not constitute deviations.

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
| S3 | E1-W optimal < 100%, E1-V optimal < 100%, \|E1-W - E1-V\| < 5 pp (point estimate) | TV_W(vec) ≥ 0.05 | E1 protocol: both TV components matter |
| S4 | SAW minus TOPSIS per cell: no sign predicted | — | Descriptive |
| S5 | Q2(SAW, vec, opt) in branch b > 56.8% (Fogo result) | max_{j} point-mass share < 0.5 on A' | Risky: predicts weaker mechanism under smoother distributions (E6 reasoning) |
| S6 | mean R(SAW, vec, opt) > 0, 95% CI excludes 0 | TV(vec) ≥ 0.05 | Regret consistent with Q2 loss |

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
- P-C sensitivity (not a deviation): run S-T with P-C rule after S-T main (P-F rule) results
  are sealed. No Fogo control.

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
- C-7: NC cod_form area share > 2% in A': trigger sensitivity run with alternative score (one step up or down; see T1 column for each case).

True deviations (DEV-S-###) are unplanned departures from §3–§6 that occur during Phase 1 or later.

---

## Annex A — T1: cod_form → permeability classification

Each cod_form has two independent classifications:

**P-F** (Rule P-F, main rule for S-T): based on the `lit` legend text alone, following
the Fogo convention — compact lava flows and intrusive rocks = Baixa. Source: Andrade (2015)
script rule; lit text in IDECV layer.

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
| B | Brechas intravulcânicas (Ante-Miocénico médio) | Complexo eruptivo interno, antigo | **NC** | Breccias = highly variable permeability; not a compact lava flow | **Base** | 1.000 | Cabral (2012) p.45: formations of "Complexo eruptivo interno, antigo" = Base; B listed in this group |
| CA | Complexo filoniano de base; basanitos, limburgitos, ancaratritos (Ante-Miocénico médio) | Complexo eruptivo interno, antigo | **Baixa** | Intrusive dyke complex; massive, compact; equivalent to Fogo undated intrusive lithologies | **Base** | 1.000 | Cabral (2012) p.45: CA = Complexo de Base |
| CB | Formação dos Flamengos (Mantos, piroclastos, chaminés) + Formação dos Orgãos (Depósitos conglomeráticos-brechoídes) — composite IDECV code (Miocénico médio) | — | **Baixa** | "Mantos" in Flamengos component = lava flows; dominant by lit text | **Base** | 1.000 | Flamengos = λρ = Base; Orgãos = CBm = Base; both components in Cabral (2012) p.45 |
| CBm | Formação dos Orgãos; Depósitos conglomeráticos-brechoídes terrestres (Miocénico médio) | — | **NC** | Conglomerate-breccia; semi-consolidated; not a compact lava flow | **Base** | 1.000 | Cabral (2012) p.45: CBm = Formação dos Orgãos = Base unit |
| MV | Formação do Monte das Vacas; Cones de piroclastos, escórias e pequenos derrames (Pliocénico) | — | **Alta** | "Cones de piroclastos, escórias" = scoria cones; highly permeable | **Recente** | 0 (excl.) | Cabral (2012): Monte das Vacas = Recente unit |
| PA | Complexo eruptivo do Pico da Antónia (Pliocénico-Miocénico) | — | **Baixa** | "Complexo eruptivo" = basaltic lava flows; lava = Baixa by P-F rule. **KEY DIVERGENCE**: PA = main Santiago aquifer; P-F/P-C disagree here | **Intermédia** | 0.472 | Cabral (2012) p.45: PA = Pico da Antónia = main aquifer = Intermédia |
| PA1 | Complexo eruptivo do Pico da Antónia; Mantos subaérios, piroclastos (Pliocénico-Miocénico) | — | **Baixa** | "Mantos subaérios" = subaerial lava flows | **Intermédia** | 0.472 | As PA |
| a | Aluviões antigas e modernas (Quaternário) | — | **Alta** | Alluvial deposits; unconsolidated; high permeability | **Recente** | 0 (excl.) | Cabral (2012): alluvium = Recente unit |
| a dv | Aluviões antigas e modernas depósitos de vertente (Quaternário) | — | **Alta** | As "a"; plus slope deposits | **Recente** | 0 (excl.) | As "a" |
| a e | Aluviões e eluviões (Quaternário) | — | **Alta** | Alluvium + eluvial deposits | **Recente** | 0 (excl.) | As "a" |
| c | Conglomerados e calcarenitos marinhos fossilíferos (Quaternário) | — | **Alta** | Marine sediments; highly porous | **Recente** | 0 (excl.) | Quaternary marine deposits = Recente |
| calc | Calcarenitos marinhos, fossilíferos (Pliocénico-Miocénico) | — | **Alta** | Marine calcarenite; highly porous; no compact lava | **NC (default: Recente)** | 0 (excl.)† | Not in Cabral (2012) pp. 44–46. Default = Recente (same rule as "c": marine calcarenite = high permeability = excluded). Sensitivity: Intermédia (0.472). Sensitivity run only if calc area share in A' > 2%. |
| cb | Rochas granulares (carbonatitos); Complexo eruptivo interno, antigo (Ante-Miocénico médio) | Complexo eruptivo interno, antigo | **Baixa** | Massive carbonatite intrusive rocks; compact; very low permeability | **Base** | 1.000 | Cabral (2012) p.45: formations of "Complexo eruptivo interno, antigo" = Base; cb in this group |
| chb | Filões e chaminés piroclastos; Complexo eruptivo interno, antigo (Miocénico médio) | Complexo eruptivo interno, antigo | **NC** | Pyroclastic dykes/necks; variable; not compact lavas | **Base** | 1.000 | Part of "Complexo eruptivo interno, antigo" group = Base (Cabral 2012 p.45) |
| chy | Filões e chaminés piroclastos; Complexo eruptivo interno, antigo (Ante-Miocénico médio) | Complexo eruptivo interno, antigo | **NC** | As chb | **Base** | 1.000 | As chb |
| chφ | Filões e chaminés; Complexo eruptivo interno, antigo (Ante-Miocénico médio) | Complexo eruptivo interno, antigo | **NC** | Phonolitic dykes; intrusive; variable | **Base** | 1.000 | As chb |
| cong | Conglomerados e facies terrestres (Pliocénico-Miocénico) | — | **Média** | Terrestrial conglomerates; variable consolidation; not compact lava | **NC (default: Base)** | 1.000† | Not explicitly listed in Cabral (2012). Default = Base by analogy with CBm (Formação dos Orgãos = Base), which also consists of terrestrial conglomerate-breccia. Sensitivity: Intermédia (0.472). Sensitivity run only if cong area share in A' > 2%. |
| d | Dunas (Quaternário) | — | **Alta** | Sandy dunes; very high permeability | **Recente** | 0 (excl.) | Quaternary = Recente |
| de | Duna, eluviões (Quaternário) | — | **Alta** | Dunes + eluvial deposits | **Recente** | 0 (excl.) | As "d" |
| dv | Depósitos de vertente (Quaternário) | — | **Média** | Slope deposits; heterogeneous; more permeable than lavas | **Recente** | 0 (excl.) | Quaternary = Recente |
| dφ | Domas e chaminés (fonólitos e traquitos); Fonólitos e traquitos (Pliocénico-Miocénico) | Fonólitos e traquitos | **Baixa** | Phonolite domes; massive compact intrusive; very low permeability | **NC (default: Base)** | 1.000† | Not in Cabral (2012). Default = Base: compact intrusive phonolite behaves like Base (same rule as cb = carbonatitos = Base). Sensitivity: Intermédia (0.472). |
| γ | Rochas granulares (gabros feldspatóidicos, piroxenitos alcalinos, sienitos feldspatóidicos); Complexo eruptivo interno, antigo (Ante-Miocénico médio) | Complexo eruptivo interno, antigo | **Baixa** | Granular intrusive; massive, compact; very low permeability | **Base** | 1.000 | Cabral (2012) p.45: γ = gabros = Base unit |
| λρ | Formação dos Flamengos; Mantos, piroclastos, chaminés (Miocénico médio) | — | **Baixa** | "Mantos" (lava flows); the dominant component | **Base** | 1.000 | Cabral (2012) p.45: λρ = Formação dos Flamengos = Base unit |
| λρ1 | Formação dos Flamengos; Mantos, piroclastos, chaminés e hialoclastitos, submarinos (Miocénico médio) | — | **Baixa** | As λρ; submarine hyaloclastites = solidified lava glass, generally impermeable | **Base** | 1.000 | As λρ |
| φ | Fase lávica pós Formação dos Orgãos (rochas traquito-fonolíticas); Mantos; Piroclastos (Pliocénico-Miocénico) | Fonólitos e traquitos | **Baixa** | "Mantos" (lava flows component); compact phonolitic/trachytic lavas | **NC (default: Intermédia)** | 0.472† | Post-Orgãos, pre-PA stratigraphically. Default = Intermédia: by age position (between Base and Intermédia units) and because compact phonolite lavas are the main constituent of the PA aquifer. Sensitivity: Base (1.000). |
| null | Mantos submarinos, inferiores e superiores (hialoclastitos); Piroclastos; Tufo Brechas (Pliocénico-Miocénico) | — | **NC** | Submarine pillow lavas + tuff breccias; not in Serralheiro (1976) terrestrial scheme | **NC (default: Base)** | 1.000† | 136 features with null cod_form. Submarine lavas are structurally compact → default Base by lithology analogy. Sensitivity: Intermédia (0.472). |

Summary for distance computation (S-T, P-F main rule):
- Baixa polygons (used in `dist_low_permeability`): CA, λρ, λρ1, CB, cb, γ, PA, PA1, A, A1, dφ, φ
- NC polygons (excluded from Baixa zones, get positive distance): B, CBm, chb, chy, chφ, null
- Média polygons: dv, cong
- Alta polygons: MV, a, a dv, a e, c, d, de, calc

Summary for B1 score (S-N, P-C):
- Base (score = 1.000): CA, λρ, λρ1, CB, CBm, B, cb, γ, chb, chy, chφ
- Intermédia (score = 0.472): PA, PA1, A, A1
- Recente / excluded (score = 0): MV, a, a dv, a e, c, d, de, dv
- NC with default Recente/excl. (score = 0†): calc
- NC with default Base (score = 1.000†): cong, dφ
- NC with default Intermédia (score = 0.472†): φ
- NC null (136 features, default Base, score = 1.000†): cod_form = null

---

## Annex B — Overpass query strings (Fogo)

**PENDING: copy exact query strings from the Fogo pipeline script before commit.**

The Fogo pipeline (NSGA-II, Zenodo 17704387, file `landfill_nsga2_optimization.py`) contains
the OSM Overpass API queries used to construct each distance criterion. Copy the exact query
strings for: roads, rivers, coast, urban, aero, cult, wells. Paste verbatim below, with line
numbers from the source script.

The same query strings will be used for Santiago (S-T and S-N), except D1 of S-N which uses
only national-level roads.

```
# roads   (script line XXX):
<paste here>

# rivers  (script line XXX):
<paste here>

# coast   (script line XXX):
<paste here>

# urban   (script line XXX):
<paste here>

# aero    (script line XXX):
<paste here>

# cult    (script line XXX):
<paste here>

# wells   (script line XXX):
<paste here>
```

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

### S5 (Q2 > Fogo 56.8%)
- Confirmed (Q2 > 56.8%, condition met): "SAW/vec/opt reached [Q2]% under S-[T/N],
  above the Fogo result (56.8%), consistent with the E6 prediction that smoother distributions
  reduce the mechanism's magnitude."
- Not confirmed (Q2 ≤ 56.8%, condition met): "SAW/vec/opt was [Q2]% under S-[T/N], at or
  below the Fogo result (56.8%). The E6 prediction was not confirmed."
- Not tested (condition not met, point-mass ≥ 0.5): "A point-mass share of [pm] ≥ 0.5
  was observed on criterion [j]; S5 condition not met. Q2 = [Q2]% reported descriptively."

### S1–S6: no-results template (branch abandoned)
- "Branch S-[T/N] was abandoned: [N_adm < 100 / n_trios > 50M / validity check failed].
  No Q2 results are reported for this branch."

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
