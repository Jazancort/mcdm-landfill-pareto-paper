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

**Attempt 1 (2026-10-28 UTC, endpoint 1):**
URL: `https://geoservicos-ingt.gov.cv/geoserver/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=areas_especiais:zdti&outputFormat=application/json`
Response: HTTP 500 / OperationProcessingFailed
Error body: "Schema 'zdti' does not exist."
HTTP Date header: not captured.

**Attempt 2 (2026-10-28 UTC, endpoint 2):**
URL: `https://geoservicos-ingt.gov.cv/geoserver/areas_especiais/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=areas_especiais:zdti&outputFormat=application/json`
Response: HTTP 500 / OperationProcessingFailed
Error body: "Schema 'zdti' does not exist."
HTTP Date header: not captured.

**Correction note:** The dates in the attempt labels above were originally written as
"2026-10-29" due to a timezone/date error (UTC vs local time). Corrected to
"2026-10-28 UTC" in commit r2. Commit 7f1028d — which first documented these retry
attempts — was made at 2026-10-28T11:32:43Z UTC (= 2026-10-28T08:32:43 at UTC-3),
firmly on 2026-10-28 in both UTC and local time. The "2026-10-29" label was a simple
error, not a UTC vs. local ambiguity (UTC-3 could only produce day+1 UTC if the local
time were after 21:00, which the commit timestamp rules out). The server response body
and error code are unchanged. The HTTP Date header was not captured at the time of
the request.

**GetCapabilities (2026-10-28 UTC):**
`areas_especiais:zdti` is still listed as a valid feature type in the WFS capabilities.

**Diagnosis:** The layer exists in GeoServer's layer configuration but the underlying
database schema/table `zdti` does not exist in the PostGIS database. This is a
server-side misconfiguration that was persistent across all attempts between
2026-10-27 and 2026-10-28. The layer will return HTTP 500 on every GetFeature request
until the DBA creates the database table. Email to INGT/IDECV is the only recourse;
if data is received after the Stage 4 results are sealed, it enters the analysis only
as a post-hoc sensitivity (not as a replacement for the C-4 result).

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

Cabral (2012) assigns the following leaf weights to the 14 S-N criteria (Annex C,
PDF-verified 2026-11-02). A2 is the "Zona Demarcada de Interesse Turístico Integrado"
criterion. "Original w₀" values are back-calculated as C-4_code_value × 0.9686 and
confirmed against the PDF; they are presented to 4 d.p. with small rounding residuals.

| Criterion | Original w₀ (Annex C) | C-4 w₀ (renorm) |
|-----------|----------------------|-----------------|
| A1 — Built-up area    | 0.0385 | 0.0397 |
| A2 — ZDTI (Integrado) | 0.0314 | **omitted** |
| A3 — Coastline        | 0.0262 | 0.0270 |
| A4 — Cultural heritage| 0.0385 | 0.0397 |
| A5 — Agriculture      | 0.0158 | 0.0163 |
| A6 — Airport          | 0.0314 | 0.0324 |
| A7 — Protected areas  | 0.0262 | 0.0270 |
| B1 — Hydrogeological  | 0.2030 | 0.2096 |
| B2 — Water points     | 0.1015 | 0.1048 |
| B3 — Streams          | 0.1015 | 0.1048 |
| C1 — Slope            | 0.0735 | 0.0759 |
| C2 — Aspect           | 0.0245 | 0.0253 |
| D1 — Roads            | 0.0949 | 0.0981 |
| D2 — MSW centre       | 0.1930 | 0.1993 |

Note: A2 and A6 share the same AHP leaf weight (0.0314 = 3.14%). The 14 Annex C
values sum to ≈ 1.0000 (sum of 13 remaining: ≈ 0.9686; plus A2: 0.0314 = 1.0000).

Redistribution formula: w_j_new = w_j_old / (Σ_{k≠A2} w_k_old) for j ≠ A2.
Original A2 weight from Cabral (2012) Annex C (PDF-verified): 0.0314.
The denominator for C-4 renormalization is 1.0000 − 0.0314 = 0.9686.
Using 0.9686 reproduces all 13 renormalized values in the "C-4 w₀" column above
within 0.0001 absolute difference (no exceptions). The weights in the "C-4 w₀"
column are copied directly from the code constant W0_SN in run_santiago_mc.py
(before the `/ sum` normalization step, sum = 0.9999), representing the actual
weights used in Stage 4.

**Redistribution scope (C-4):** The PRESPEC §10 contingency rule specifies
"redistribute weight" but does not define the redistribution scope. The code
redistributes A2's weight proportionally across all remaining 13 criteria (global
redistribution). This changes the group weights from the original Cabral values
(F_A=0.208, F_B=0.406, F_C=0.098, F_D=0.288) to (F_A=0.182, F_B=0.419,
F_C=0.101, F_D=0.297). An alternative consistent with AHP practice would redistribute
within Group A only (remaining 6 criteria: A1, A3, A4, A5, A6, A7), preserving the
Cabral group weights for B, C, D. This alternative is declared below as mandatory
pre-analysis sensitivity SENS-ZDTI-DISTRIB.

### SENS-ZDTI-DISTRIB — within-Group-A redistribution

**Pre-declared before any SENS computation (2026-11-02).**

Repeat Stage 4 S-N with C-4 weight redistribution confined to the 6 remaining Group A
criteria only (A1, A3, A4, A5, A6, A7). A2's weight (0.0314) is distributed
proportionally among these 6, preserving the original Cabral group weights for
B (0.406), C (0.098), D (0.288) and restoring F_A = 0.208.

This affects TV_B and potentially the testability of S3b in S-N (current TV_B = 0.057,
close to the 0.05 threshold). If any prediction verdict changes relative to the main
run, record in DEVIATIONS.md and consult PRESPEC §11.

w0 integrity: the startup log includes `assert abs(w0.sum() - 1) < 1e-6` for each
branch via log_startup_provenance(), confirming the normalized sum before use.

Sum of renormalized 13 weights (from code): 0.9999 before normalization → 1.0000
after `W0_SN / W0_SN.sum()`. Any residual is at the level of floating-point rounding.

## Group weights after C-4

Groups follow PRESPEC_SANTIAGO §5.6 (A, B, C, D) after A2 removal:

| Group | Criteria | W_g (C-4) |
|-------|----------|-----------|
| A     | A1, A3, A4, A5, A6, A7 | 0.1821 |
| B     | B1, B2, B3             | 0.4192 |
| C     | C1, C2                 | 0.1012 |
| D     | D1, D2                 | 0.2974 |

Original W_A (14 criteria, A2 included) = sum(A1+A2+A3+A4+A5+A6+A7)
  = 0.0385+0.0314+0.0262+0.0385+0.0158+0.0314+0.0262 = 0.2080 ≈ 0.208 (Cabral Tab. 11–16).
After C-4: W_A (renormalized 6 criteria, A2 removed) = (0.2080−0.0314)/0.9686 = 0.1824 ≈ 0.1821.

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

Cabral, Adilson Vaz (2012). *Análise Multicritério em Sistemas de Informação
Geográfica para a Localização de Aterros Sanitários. O caso da região Sul da
ilha de Santiago, Cabo Verde.* Dissertação de Mestrado, Faculdade de Ciências
Sociais e Humanas, Universidade Nova de Lisboa. hdl.handle.net/10362/8627.

AHP weights: Table 14 (leaf) and Table 16 (final); group percentages in Tab. 11–16
(pp. 54–55): Group A = 20.8%, B = 40.6%, C = 9.8%, D = 28.8%.

Note: the repository metadata at hdl.handle.net/10362/8627 uses "Sistema" (singular);
the correct title from the PDF is "Sistemas" (plural) as cited above.
Earlier DEV versions cited an incorrect author name and title (confirmed by PDF
2026-11-02). Added to refs.bib as @mastersthesis{Cabral2012}.
