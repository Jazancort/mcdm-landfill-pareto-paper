# DEV-SANT-A5-001 — Clarification of A5 exclusion zones (carta_agricola_st)
Date: 2026-10-28
Type: pre-data clarification (no Q2/R/portfolio computed before this record)
Branch: S-N only (S-T uses a different source; see §S-T below)
Commit provenance: present in commit bc41fd5 (stage4-prelaunch); Stage 3b
  descriptors first computed under compute_stage3b.py at a later date.

## Problem

PRESPEC_SANTIAGO §5.2 declares A5 as:
"Agriculture: distance to agricultural protection zones, benefit; inside zones
 → excluded. Source: IDECV carta_agricola_st."

The carta_agricola_st layer classifies the ENTIRE Santiago island into 7 agricultural
land use types. Using all types as exclusion zones eliminates all 387 S-N candidate
sites (N_adm=0), making the S-N branch degenerate.

## Coverage of each tipo_agric (island-wide areas)

The table below shows the area of each tipo_agric on the island as a whole and
the corresponding proportion of the S-N region. Areas sum to ≈1005 km² (the
excess over the island area of ≈991 km² is due to overlapping polygons at
polygon boundaries, estimated at ≈14 km²; needs verification to confirm no
double-counting that would affect exclusion logic).

| tipo_agric | Área na ilha (aprox.) | % da região S-N |
|---|---|---|
| Pastagens áridas, de baixa altitude | 429.5 km² | 74.0% |
| Afloramentos Rochosos | 112.5 km² | 9.8% |
| Pastagens Sub-húmidas, de altitude | 136.9 km² | 7.0% |
| Sequeiro Sub-húmido | 157.3 km² | 5.2% |
| Regadios | 51.7 km² | 3.6% |
| Sequeiro Húmido | 109.0 km² | 0.5% |
| Sequeiro Semiárido | 8.2 km² | 0.0% |

Note: percentages are fractions of the S-N region area, not of the island.
"Pastagens áridas" (arid pastures, 74%) and "Afloramentos Rochosos" (rocky outcrops,
9.8%) are not "agricultural protection zones" in any regulatory sense.

## Decision

The PRESPEC named carta_agricola_st as the source but did not specify which classes to
exclude. The ambiguity is resolved by the source from which the criterion was taken:
Cabral (2012, p. 63, Tab. 18) explicitly defines A5 exclusion from "áreas de regadio"
(irrigated perimeters). Using only "Regadios" operationalises this definition faithfully.

Operationalisation:
  A5 benefit criterion = distance from candidate site to nearest Regadios polygon
    (dist_A5_agriculture in metres; larger = better = benefit).
  Exclusion = sites within a Regadios polygon (dist_A5_agriculture = 0 m).

Expected direction of effect: N_adm increases from 0 to a viable number.
The amplitude of A5 will decrease (fewer exclusions, but most of the S-N area
is now available). The effect on TV_W is unknown but expected to be small
(Regadios cover only 3.6% of the S-N area).

## Distance threshold and buffer declaration

Cabral (2012, p. 63) specifies: "Áreas de Regadio (buffer de proteção de 500 m)".
This implies a 500 m exclusion buffer around Regadios polygons, not a simple
inside/outside test.

Verification required: inspect santiago_extract.py A5 exclusion logic to confirm
whether the distance threshold is 0 m (inside only) or 500 m (Cabral buffer).

If 0 m was applied (inside only), the deviation from Cabral's 500 m buffer must be
declared explicitly. Candidate statement (to be confirmed):
  DEV-SANT-A5B-BUFFER-001: A5 exclusion applied at distance threshold = 0 m
  (sites inside Regadios polygon only), not 500 m as specified by Cabral (2012).
  Expected direction: N_adm is higher than under 500 m buffer; A5 amplitude
  is lower (more sites available). SENS-A5b includes a 0m vs 500m comparison.

## Justification from source

Cabral (2012) hdl.handle.net/10362/8627, p. 63:
"Áreas de Regadio (buffer de proteção de 500 m)".

Note: citation at page 63 and Table 18 has not been independently verified against
the dissertation text. Confirm before submission that the quoted phrase and table
reference are literal and not paraphrased.

## Applicability to S-T branch

This deviation applies to the S-N branch only. S-T uses criterion "cult" (dist_cultivation
in metres), sourced from OSM cultivation polygons following the original Fogo methodology,
not from carta_agricola_st. No class-selection ambiguity exists for S-T. The S-T N_adm of
601 (out of 650 candidates) is consistent with this criterion functioning normally.

## Pre-declared sensitivity SENS-A5

To bound the effect of the Regadios-only interpretation, a sensitivity analysis is
pre-declared here before any Stage 4 result is seen.

The nested ladder below tests increasingly conservative exclusions in order of
agricultural value (Regadios > Sequeiro Húmido > Sequeiro Sub-húmido). Each step
includes all higher-value classes from prior steps.

### Ladder

| Run | A5 exclusion set | Expected N_adm direction |
|-----|-----------------|--------------------------|
| Main | R only | baseline (387 → N_adm base) |
| SENS-A5a | R + Sequeiro Húmido (SH) | N_adm decreases (adds 0.5% of S-N area) |
| SENS-A5b | R + SH + Sequeiro Sub-húmido (SSh) | N_adm decreases further (adds 5.2% of S-N area) |

Optional (if buffer question resolved): repeat each rung above with 0 m vs 500 m
exclusion buffer to disentangle the two choices. Report as SENS-A5a-buf, SENS-A5b-buf.

Rationale for ladder order: in agricultural value, Regadios (irrigated, highest)
> Sequeiro Húmido (rain-fed humid) > Sequeiro Sub-húmido (rain-fed sub-humid).
The ladder ascends from most obvious (Regadios) to more conservative interpretations
in value order. The original single-step SENS with SSh only (skipping SH) was
removed because SH has higher agricultural protection value than SSh and therefore
belongs earlier in the ladder.

### Execution rules

Seeds: the same canonical seeds as the S-N main run (SeedSequence.spawn(2) per κ,
parent seeds [1, 4, 15, 17, 28, 30] from gen_santiago_seeds.py). Common random
numbers permit direct comparison between main and SENS.

Sealed reference: before any SENS run begins, the commit hash of the main Stage 4
MC result commit (containing mc_SN_raw.csv, mc_SN_e1.csv) plus the SHA-256 of the
two S-N main output files will be recorded. No SENS run starts before this reference
is committed.

Testability: the SENS changes the admissible set A' and hence TV_B. The S3b and S7b
testability conditions (TV_B ≥ 0.05 and TV_W ≥ 0.05) are evaluated only on the main
branch. Testability does not transfer from SENS to main. At S-N TV_B = 0.057
(marginally above 0.05), a SENS that reduces TV_B below 0.05 would not reclassify
any prediction — the main result remains the reference.

This sensitivity is run AFTER Stage 4 main results are sealed, and reported
descriptively without a separate prediction block. It does not constitute a new
prediction and cannot be used to select among conflicting Stage 4 outcomes.

## Prior deviation record (order of events)

This DEV record was written on 2026-10-28, before any Stage 3b descriptor computation
for S-N. The Stage 3b script (compute_stage3b.py) was run and its outputs committed
at a later point. Both this file and compute_stage3b.py are present in commit bc41fd5
(stage4-prelaunch, 2026-10-28). No Q2, regret, Pareto portfolio, or MC result existed
before this record.
