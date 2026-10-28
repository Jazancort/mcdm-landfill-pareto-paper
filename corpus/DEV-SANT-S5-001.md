# DEV-SANT-S5-001 — S5 condition: criterion classification (categorical vs continuous)
Date: 2026-10-28
Type: pre-data classification decision (S5 testability requires this classification
      before any Q2 or Pareto result is seen)

## Background

PRESPEC_SANTIAGO §6 defines the S5 testability condition:

> "max_{j ∈ non-binary, non-categorical} point-mass share
>  (fraction of A' at modal value) < 0.5.
>  Binary criteria (aspect in S-T; B1 in S-N after normalisation)
>  and categorical criteria are excluded from this condition."

The PRESPEC names two exclusion classes (binary and categorical) but defines "binary"
only by example (aspect and B1) and does not define "categorical" explicitly.
This DEV fixes the definition and classifies every criterion in both branches.

## Definition of "categorical" for this study

A criterion is categorical if and only if the values in A' (the admissible set)
form a finite set derived from a discrete classification code or rubric — i.e.,
the values are codes or scores assigned from a lookup table rather than continuous
measurements. Distinct values ≤ 10 is a necessary (not sufficient) condition.
A continuous measurement that happens to cluster at a few values due to data
properties (e.g., many zeros) is NOT categorical.

Binary is a special case of categorical with exactly 2 values after any transformation.

## S-T: criterion classification

S-T uses 10 criteria (C-2 wells omit, renorm from Fogo AHP 11 criteria).
Source: Fogo methodology (published main article).

| Criterion | Raw source | Distinct values in A' | Classification | S5 included |
|---|---|---|---|---|
| perm | dist to Baixa geology polygons (m) | many (continuous) | Continuous | YES |
| slope | DEM slope (degrees) | many (continuous) | Continuous | YES |
| roads | dist to OSM roads (m) | many (continuous) | Continuous | YES |
| rivers | dist to OSM rivers (m) | many (continuous) | Continuous | YES |
| aspect | binary leeward indicator (0/1/0.5) | 3 (0, 0.5, 1) | Binary | NO (PRESPEC explicit) |
| coast | dist to coastline (m) | many (continuous) | Continuous | YES |
| protected | dist to protected area polygons (m) | many (continuous) | Continuous | YES |
| urban | dist to urban core polygons (m) | many (continuous) | Continuous | YES |
| aero | dist to aerodrome polygon (m) | many (continuous) | Continuous | YES |
| cult | dist to OSM cultivation polygons (m) | many (continuous) | Continuous | YES |

Perm justification: perm is a DISTANCE in metres to the nearest low-permeability
(Baixa) polygon. Sites inside Baixa have dist=0; sites outside have positive continuous
values. The high point mass at dist=0 (perm pm=0.617 in S-T) reflects data
(many sites touching or inside Baixa outcrops), NOT a discrete coding system.
A distance is a continuous measurement even when clustered. Perm is NOT categorical.

Consequence for S5 in S-T: perm is the criterion with the highest point mass
(0.617 > 0.5), so S5 condition is NOT met → S5 is NOT testable in S-T.

Alternative classification (sensitivity): if perm were classified as categorical
(because many sites share distance=0), perm would be excluded from the S5 check.
The next highest pm in S-T is [to be filled from Stage 3b output — see compute_stage3b.py
S5 summary]. If that pm < 0.5, S5 WOULD be testable under the alternative.
Report both classifications; the primary classification (perm = continuous) is fixed here.

## S-N: criterion classification

S-N uses 13 criteria (C-4 A2 omit, renorm from Cabral 2012 weights).

| Criterion | Raw source | Distinct values in A' | Classification | S5 included |
|---|---|---|---|---|
| A1 | dist to built-up area polygons (m) | many (continuous) | Continuous | YES |
| A3 | dist to coastline (m) | many (continuous) | Continuous | YES |
| A4 | dist to cultural heritage polygon (m) | many (continuous) | Continuous | YES |
| A5 | dist to Regadios polygons (m) | many (continuous) | Continuous | YES |
| A6 | dist to aerodrome polygon (m) | many (continuous) | Continuous | YES |
| A7 | dist to protected area polygons (m) | many (continuous) | Continuous | YES |
| B1 | hydrogeological score from geological class | 2–4 distinct values | Categorical | NO (PRESPEC explicit) |
| B2 | dist to water points (m) | many (continuous) | Continuous | YES |
| B3 | dist to stream network (m) | many (continuous) | Continuous | YES |
| C1 | DEM slope (degrees) | many (continuous) | Continuous | YES |
| C2 | aspect continuous v(θ) ∈ [0,1] | many (continuous) | Continuous | YES |
| D1 | dist to main roads (m) | many (continuous) | Continuous | YES |
| D2 | dist to Praia MSW centroid (m) | many (continuous) | Continuous | YES |

B1 justification: B1_score is derived from hydrogeological class codes (geological
map classification: each polygon gets a code NC/CA/CB/... mapped to a score in a
lookup table). The score takes a small number of distinct values (≤ 4 in A') derived
from discrete classification codes, not from continuous measurement. B1 IS categorical.

Distinction perm (S-T) vs B1 (S-N): perm uses the DISTANCE to a geological polygon
(continuous); B1 uses a SCORE ASSIGNED FROM the geological class (categorical). These
are structurally different even though both derive from geological maps.

Consequence for S5 in S-N: B1 is excluded. The maximum point mass of the remaining
12 continuous criteria is 0.016 (C1 slope, from Stage 3b output) < 0.5.
S5 IS testable in S-N.

## Consistency with the Fogo branch

In Fogo, perm (dist to Baixa) was included in the S5 condition with point mass 0.90
(350/389 sites inside Baixa → dist=0). S5 was not testable for Fogo.
This DEV maintains the same perm classification for S-T (continuous distance → included).
No inconsistency with the Fogo treatment.

## Summary of S5 testability

| Branch | perm/B1 classification | max pm_continuous | S5 testable |
|---|---|---|---|
| Fogo (reference) | perm = continuous (included) | 0.90 (perm) | NO |
| S-T | perm = continuous (included) | 0.617 (perm) | NO |
| S-N | B1 = categorical (excluded) | 0.016 (C1) | YES |
