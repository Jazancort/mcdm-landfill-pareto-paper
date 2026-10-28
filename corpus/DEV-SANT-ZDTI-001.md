# DEV-SANT-ZDTI-001 — A2 (ZDTI): HTTP 500 on download; C-4 triggered
Date: 2026-10-27
Type: pre-data deviation (computed before any score, Q2 or frontier for Santiago)

## PRESPEC declaration (§5.4, §5.6)

PRESPEC_SANTIAGO §5.4 declares:

> "ZDTI layer confirmed present in IDECV GetCapabilities (areas_especiais:zdti,
>  2026-10-25). C-4 is NOT triggered. A2 uses this layer as declared.
>  Weight redistribution (C-4) does not apply."

PRESPEC_SANTIAGO §5.6 declares:

> "Weight of A2 is NOT redistributed (ZDTI present; C-4 not triggered)."

## What happened

The `areas_especiais:zdti` layer is present in the IDECV GetCapabilities response
(confirmed 2026-10-25). However, when attempting to download the layer content on
2026-10-27 via WFS GetFeature request, the server returned HTTP 500 (Internal Server
Error). Repeated attempts at different times returned the same error. No ZDTI data
could be obtained.

The PRESPEC declaration was based on the GetCapabilities response (layer exists in
catalog). The actual download failure was only discovered at Phase 1 extraction time
(2026-10-27), after the PRESPEC was committed and locked.

## Second attempt (2026-10-28 UTC)

Two WFS GetFeature requests were sent at different times:

**Attempt 1 (2026-10-29, endpoint 1):**
URL: `https://geoservicos-ingt.gov.cv/geoserver/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=areas_especiais:zdti&outputFormat=application/json`
Response: HTTP 500 / OperationProcessingFailed
Error body: "Schema 'zdti' does not exist."

**Attempt 2 (2026-10-29, endpoint 2):**
URL: `https://geoservicos-ingt.gov.cv/geoserver/areas_especiais/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=areas_especiais:zdti&outputFormat=application/json`
Response: HTTP 500 / OperationProcessingFailed
Error body: "Schema 'zdti' does not exist."

**GetCapabilities (2026-10-29):**
`areas_especiais:zdti` is still listed as a valid feature type in the WFS capabilities.

**Diagnosis:** The layer exists in GeoServer's layer configuration but the underlying
database schema/table `zdti` does not exist in the PostGIS database. This is a
permanent server-side misconfiguration, not a transient HTTP error. The layer will
continue to return HTTP 500 on every GetFeature request until the DBA creates the
database table.

**Conclusion:** C-4 is permanently triggered for this criterion. The ZDTI data is
not recoverable via this service. Email to IDECV/INGT would be the only recourse,
but this is outside the timeline of the current study. The DEV-SANT-ZDTI-001
justification stands.

C-4 applied per PRESPEC_SANTIAGO §10 contingency rule:

> "C-4: ZDTI absent from IDECV: omit A2, redistribute weight, no Fogo control."

The HTTP 500 response makes the layer effectively absent for extraction purposes,
even though it appears in the catalog. The spirit of C-4 (layer unavailable for
extraction) applies.

## Consequence: weight redistribution

Cabral (2012) assigns the following leaf weights to the 14 S-N criteria:

| Criterion | Original w₀ | C-4 w₀ (renorm) |
|-----------|------------|-----------------|
| A1 — Built-up area    | 0.0383 | 0.0397 |
| A2 — ZDTI             | 0.0383 | **omitted** |
| A3 — Coastline        | 0.0260 | 0.0270 |
| A4 — Cultural heritage| 0.0383 | 0.0397 |
| A5 — Agriculture      | 0.0157 | 0.0163 |
| A6 — Airport          | 0.0313 | 0.0324 |
| A7 — Protected areas  | 0.0260 | 0.0270 |
| B1 — Hydrogeological  | 0.2020 | 0.2096 |
| B2 — Water points     | 0.1010 | 0.1048 |
| B3 — Streams          | 0.1010 | 0.1048 |
| C1 — Slope            | 0.0731 | 0.0759 |
| C2 — Aspect           | 0.0244 | 0.0253 |
| D1 — Roads            | 0.0945 | 0.0981 |
| D2 — MSW centre       | 0.1921 | 0.1993 |

Redistribution formula: w_j_new = w_j_old / (1 − w_A2_old) for j ≠ A2.
Original A2 weight from Cabral (2012) Tab. 14/16: 0.0383 (rounded).
Denominator: 1 − 0.0383 = 0.9617.
Sum of renormalized 13 weights: 1.0000 (verified).

Note: the exact original Cabral weights may differ by ≤0.001 from the values above
(rounding in Tab. 14). The renormalized w₀ above are the values used in extraction
and Stage 4 Monte Carlo. Any discrepancy is below the Dirichlet SD at κ=25 (~0.04).

## Group weights after C-4

Groups follow PRESPEC_SANTIAGO §5.6 (A, B, C, D) after A2 removal:

| Group | Criteria | W_g (C-4) |
|-------|----------|-----------|
| A     | A1, A3, A4, A5, A6, A7 | 0.1821 |
| B     | B1, B2, B3             | 0.4192 |
| C     | C1, C2                 | 0.1012 |
| D     | D1, D2                 | 0.2974 |

Original W_A (14 criteria, A2 included) = 0.1821 + 0.0383 = 0.2204.
After C-4: W_A = 0.1821 (A2 weight absorbed proportionally across all groups).

## Fogo control

Per C-4 declaration: "no Fogo control". No equivalent ZDTI criterion exists in
the S-T or Fogo models. This deviation has no Fogo control experiment.

## Expected direction of effect

A2 (distance from ZDTI special tourism zones) penalises sites near tourism areas.
Omitting A2 removes this penalty from the S-N model. Sites near ZDTI zones that
would otherwise be excluded (A2 < 500 m buffer) are not excluded in the actual run.

Direction on Q2: indeterminate. Removing A2 changes the criterion mix and the
relative weights of remaining criteria; the effect on Pareto attainment depends
on the spatial distribution of ZDTI zones relative to the S-N admissible sites.

## Source reference

Cabral, V. F. S. (2012). Localização de Aterros Sanitários na Ilha de Santiago usando
SIG e Análise Multi-Critério. MSc dissertation. Universidade Nova de Lisboa.
hdl.handle.net/10362/8627. AHP weights: Table 14 (leaf) and Table 16 (final).
