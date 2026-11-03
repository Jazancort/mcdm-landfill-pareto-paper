# DEV-SANT-A5-001 — Clarification of A5 exclusion zones (carta_agricola_st)
Date: 2026-10-28
Type: pre-data clarification (class selection within declared source)
Branch: S-N only (S-T uses a different source; see §S-T note below)

## Commit provenance

This file was first committed in ebf7dfe (2026-10-28T00:10:27-03:00 = 03:10 UTC),
simultaneously with df_santiago_sn.csv (first S-N extraction at 1.25 km, N_cand=249).
Stage 3b descriptors (stage3b_descriptors.json) were first committed in 00b1424,
one minute later (2026-10-28T00:11:47-03:00 = 03:11 UTC).

This file therefore predates stage3b_descriptors.json. It does NOT predate
df_santiago_sn.csv (simultaneous commit). The 80 second interval confirms commit
order but does not demonstrate causal order of computations.

The stronger argument for "this decision predates the analysis" is a content
argument: the DEV was forced by the observation that N_adm = 0 under all-type
exclusion (checked at the time of extraction, before any descriptor was computed).
There was no choice among alternative exclusion sets that could have been
guided by results, because no result existed — the only observation was degeneracy.
The decision to use Regadios only is anchored in Cabral (2012), not in any
data-driven consideration of the descriptors.

## Problem

PRESPEC_SANTIAGO §5.2 declares A5 as:
"Agriculture: distance to agricultural protection zones, benefit; inside zones
 → excluded. Source: IDECV carta_agricola_st."

The carta_agricola_st layer classifies the ENTIRE Santiago island into 7 agricultural
land use types. Using all types as exclusion zones would eliminate almost all S-N
candidate sites (N_cand=249 at the initial 1.25 km extraction; N_adm=0 under all-type
exclusion), making the S-N branch degenerate. At the corrected 1.0 km spacing
(DEV-SANT-SPACING-001, commit b82e264), N_cand=387.

## Coverage of each tipo_agric (island-wide areas)

Areas below are island-wide totals (sum ≈ 1005 km², which exceeds the island area
of ≈991 km² by ≈14 km² due to overlapping polygon boundaries; this excess needs
verification to confirm it does not affect exclusion logic). Percentages are
fractions of the S-N region area.

| tipo_agric | Área na ilha (aprox.) | % da região S-N |
|---|---|---|
| Pastagens áridas, de baixa altitude | 429.5 km² | 74.0% |
| Afloramentos Rochosos | 112.5 km² | 9.8% |
| Pastagens Sub-húmidas, de altitude | 136.9 km² | 7.0% |
| Sequeiro Sub-húmido | 157.3 km² | 5.2% |
| Regadios | 51.7 km² | 3.6% |
| Sequeiro Húmido | 109.0 km² | 0.5% |
| Sequeiro Semiárido | 8.2 km² | 0.0% |

"Pastagens áridas" (arid pastures, 74%) and "Afloramentos Rochosos" (rocky outcrops,
9.8%) are not "agricultural protection zones" in any regulatory sense.

## Decision: Regadios only

The PRESPEC named carta_agricola_st as the source but did not specify which classes
constitute "agricultural protection zones". The ambiguity is resolved by the source
from which the criterion was taken: Cabral (2012) explicitly defines A5 exclusion
from "áreas de regadio" (irrigated perimeters). Using only "Regadios" operationalises
this definition faithfully.

## Buffer threshold: PRESPEC is explicit — 0 m (inside polygon only)

PRESPEC_SANTIAGO §5.2 states the exclusion as "inside zones → excluded", and
PRESPEC_SANTIAGO §5.3 documents this explicitly as "A5 agriculture inside zone (dist=0)".
The code implements: dist_A5 == 0 (eq criterion) → excluded, i.e., sites inside
any Regadios polygon are excluded; all others are admissible.

This is NOT a deviation from the PRESPEC. The PRESPEC chose not to adopt the 500 m
buffer that Cabral (2012, p. 63) applies around Regadios ("Áreas de Regadio (buffer
de proteção de 500 m)"). The comparison between 0 m and 500 m exclusion is a
pre-declared sensitivity (SENS-AGR-BUF below).

Operationalisation:
  dist_A5_agriculture = distance from candidate site to nearest Regadios polygon
  Exclusion: dist_A5_agriculture == 0 (inside polygon)
  Benefit criterion: dist_A5_agriculture > 0 (farther = better)

## Justification from source

Cabral (2012) hdl.handle.net/10362/8627, p. 63: "Áreas de Regadio (buffer de
proteção de 500 m)".

Note: the author's name in the repository metadata is "Adilson Vaz Cabral" with
title "Análise multicritério em Sistema de Informação Geográfica para localização
de aterros sanitários. O caso da região sul da Ilha de Santiago, Cabo Verde." This
does not match the DEV-SANT-ZDTI-001 citation ("Cabral, V. F. S., Localização de
Aterros Sanitários…"). The correct author name and title need to be confirmed
against the dissertation PDF before submission and updated in refs.bib.

Page 63 and Table 18 citations have not been independently verified against the
PDF (access to hdl.handle.net/10362/8627 is not automated). Confirm before submission.

## Applicability to S-T branch

This deviation applies to the S-N branch only. S-T uses criterion "cult" (dist_cultivation
in metres), sourced from OSM cultivation polygons following the original Fogo methodology,
not from carta_agricola_st. No class-selection ambiguity exists for S-T. The S-T N_adm of
601 (out of 650 candidates) is consistent with this criterion functioning normally.

## Pre-declared sensitivity runs (mandatory)

All SENS runs use the canonical seeds from gen_santiago_seeds.py
(SeedSequence.spawn(2) per κ, parent seeds [1,4,15,17,28,30]) — the same as the
S-N main run. This ensures common random numbers (CRN) for the Dirichlet weight
draws, enabling direct comparison. The bootstrap in bootstrap_contrast() uses
numpy's global RNG (not the branch-specific RNG), so CRN applies to weight draws
only, not to bootstrap resampling.

Sealed reference: before any SENS run begins, a tag `stage4-results-sealed` is
created at the commit that introduces mc_SN_raw.csv and mc_SN_e1.csv from the
main Stage 4 run. SHA-256 hashes of those two files are included in the tag message.
No SENS run starts before this tag exists.

Testability: SENS changes the admissible set A' and hence TV_B. S3b and S7b
testability conditions are evaluated only on the main branch (principal run).
At S-N TV_B=0.057 (main), a SENS that reduces TV_B below 0.05 does not
reclassify the main result. Results from SENS are reported descriptively only.

### SENS-AGR-1 — R + Sequeiro Húmido

Repeat Stage 4 S-N with A5 exclusion set = {Regadios, Sequeiro Húmido}.
Rationale: SH has higher agricultural value than SSh (rain-fed humid > rain-fed sub-humid)
and is the next candidate for protection after Regadios.
Expected: N_adm decreases (SH covers ≈0.5% of S-N area).

### SENS-AGR-2 — R + Sequeiro Húmido + Sequeiro Sub-húmido

Repeat Stage 4 S-N with A5 exclusion set = {Regadios, Sequeiro Húmido, Sequeiro Sub-húmido}.
Expected: N_adm decreases further (SSh adds ≈5.2% of S-N area).

### SENS-AGR-BUF — 0 m vs 500 m buffer for each exclusion set

Repeat each of Main, SENS-AGR-1, SENS-AGR-2 with a 500 m exclusion buffer around
the exclusion polygons (in addition to inside-polygon exclusion). This operationalises
the Cabral (2012, p. 63) specification and bounds the effect of the 0 m choice.
Expected: N_adm decreases at each level (more sites excluded near polygon edges).
Total additional runs: 3 (one per exclusion set at 500 m buffer).

All five extra runs (SENS-AGR-1, SENS-AGR-2, SENS-AGR-BUF×3) are mandatory.
They require separate S-N extractions (df_santiago_sn_sensAGR*.csv) with the
modified exclusion criterion.

## Per-step criterion definition for SENS-AGR

For each SENS-AGR run, the A5 criterion is re-operationalised as follows:

**Main (R only):**
- Exclusion polygons: union of all Regadios polygons in carta_agricola_st
- Exclusion threshold: dist(candidate, exclusion_union) == 0 (inside polygon)
- A5 benefit value: dist(candidate, exclusion_union) in metres [same polygons]

**SENS-AGR-1 (R + SH):**
- Exclusion polygons: union of {Regadios, Sequeiro Húmido} polygons
- Exclusion threshold: dist == 0
- A5 benefit value: dist(candidate, new_exclusion_union) in metres
- Normalisation: recalculated over the new admissible set A'_{AGR-1}

**SENS-AGR-2 (R + SH + SSh):**
- Exclusion polygons: union of {Regadios, Sequeiro Húmido, Sequeiro Sub-húmido}
- Exclusion threshold: dist == 0
- A5 benefit value: dist(candidate, new_exclusion_union) in metres
- Normalisation: recalculated over the new admissible set A'_{AGR-2}

**SENS-AGR-BUF (×3, one per exclusion set):**
- Same exclusion polygon sets as Main / SENS-AGR-1 / SENS-AGR-2
- Exclusion threshold: dist < 500 m (Cabral 2012 buffer specification)
- A5 benefit value: dist(candidate, exclusion_union) in metres
  (the distance is measured to the polygon itself, not to the 500 m buffer boundary)
- Normalisation: recalculated over the new admissible set

In all cases: the dist_A5 column is the Euclidean distance in metres from the
candidate centroid to the nearest point on the exclusion polygon union (shapely
distance, 0 for interior points per compute_dist_to_polygons convention).
