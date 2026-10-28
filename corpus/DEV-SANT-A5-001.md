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
