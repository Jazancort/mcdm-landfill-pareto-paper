# DEV-SANT-A5-001 — Clarification of A5 exclusion zones (carta_agricola_st)
Date: 2026-10-28
Type: pre-data clarification (no Q2/R/portfolio computed before this record)

## Problem

PRESPEC_SANTIAGO §5.2 declares A5 as:
"Agriculture: distance to agricultural protection zones, benefit; inside zones → excluded.
 Source: IDECV carta_agricola_st."

The carta_agricola_st layer classifies the ENTIRE Santiago island into 7 agricultural
land use types. Using all types as exclusion zones eliminates all 249 S-N candidate
sites (N_adm=0), making the S-N branch degenerate.

## Coverage of each tipo_agric in S-N region

| tipo_agric | S-N area | S-N coverage |
|---|---|---|
| Pastagens áridas, de baixa altitude | 429.5 km2 | 74.0% |
| Afloramentos Rochosos | 112.5 km2 | 9.8% |
| Pastagens Sub-húmidas, de altitude | 136.9 km2 | 7.0% |
| Sequeiro Sub-húmido | 157.3 km2 | 5.2% |
| Regadios | 51.7 km2 | 3.6% |
| Sequeiro Húmido | 109.0 km2 | 0.5% |
| Sequeiro Semiárido | 8.2 km2 | 0.0% |

"Pastagens áridas" (arid pastures, 74%) and "Afloramentos Rochosos" (rocky outcrops,
9.8%) are clearly not "agricultural protection zones" in any regulatory sense.

## Decision

The PRESPEC intent was "agricultural protection zones" — specific areas with active
irrigated or legally protected agriculture. The only tipo that clearly meets this
definition is "Regadios" (irrigated perimeters).

Correction: A5 exclusion applies ONLY to tipo_agric = "Regadios".
All other tipos remain as A5 distance criterion (farther = better = benefit).

Expected direction of effect: N_adm increases from 0 to a viable number.
The amplitude of A5 will decrease (fewer exclusions, but most of the S-N area
is now available). The effect on TV_W is unknown but expected to be small (Regadios
cover only 3.6% of the S-N area).

This deviation was triggered by data inspection BEFORE any descriptor computation,
and does not constitute a post-hoc adjustment to analysis results.

## Justification from Cabral (2012)

Cabral (2012, p. 63 and Tab. 18) defines A5 ("Usos do Solo") as exclusion from
"áreas de regadio" (irrigated perimeters). The operational definition in the
thesis is specifically irrigated agriculture, not all agricultural land use.
The carta_agricola_st layer includes pastagens (pastures), afloramentos rochosos
(rocky outcrops), and sequeiro (rain-fed dryland farming), which are not covered
by the Cabral definition of A5. Using only "Regadios" operationalises the
declared exclusion criterion faithfully.

Source: Cabral (2012) hdl.handle.net/10362/8627, p. 63:
"Áreas de Regadio (buffer de proteção de 500 m)".

## Pre-declared sensitivity SENS-A5

To bound the effect of this interpretation, a sensitivity run is pre-declared
here before any Stage 4 result is seen:

**SENS-A5**: repeat Stage 4 S-N with A5 exclusion applied to:
  tipo_agric IN {"Regadios", "Sequeiro Sub-húmido"}

Rationale: "Sequeiro Sub-húmido" (5.2% of S-N area) is the next most
plausible regulatory protection category after Regadios. Including it
increases the exclusion area slightly; sites in this zone are removed
from A'.

Expected direction: N_adm decreases moderately; TV and descriptor values
may shift; S1/S2 tests remain unchanged in structure.

This sensitivity is run AFTER Stage 4 main results are sealed, and reported
descriptively without a separate prediction block. It does not constitute a
new prediction and cannot be used to select among conflicting Stage 4 outcomes.
