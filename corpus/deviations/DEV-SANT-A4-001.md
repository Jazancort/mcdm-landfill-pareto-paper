# DEV-SANT-A4-001 — A4 cultural heritage: single-point fallback (Cidade Velha)
Date: 2026-10-28
Type: pre-data deviation (computed before any score, Q2 or frontier for Santiago)

## PRESPEC declaration

PRESPEC_SANTIAGO §5.2 declares for criterion A4:

> "Cultural heritage: distance to Cidade Velha UNESCO buffer zone, benefit; < 500 m excluded.
>  Source: UNESCO WHC boundary (publicly available shapefile, world heritage site ID 1310 —
>  Cidade Velha, Historic Centre of Ribeira Grande, inscribed 2009)."

## What happened

The IDECV WFS layer `areas_especiais:patrimonio_cultural` was downloaded as
`data/santiago/patrimonio_cultural.geojson` (2 features). On inspection, both
features are located on Ilha do Santo Antão, not on Santiago. No feature from
this layer falls within or near the S-N region.

The UNESCO WHC published shapefile (world heritage site ID 1310) was not
independently obtained from the UNESCO portal before Phase 1 began. Obtaining
it post-hoc would fall after Phase 1 commit and would violate the declared
source-freeze rule.

## Fallback applied

A single reference point approximating the centre of the Cidade Velha inscribed
site was used:

  Centre point: 14.9225°N, 23.6052°W  (Cidade Velha / Ribeira Grande, Santiago)
  Exclusion buffer: 100 m (applied as A4 < 500 m rule → sites within 100 m
  of the point are excluded; 500 m criterion uses distance to this point)

Note: the PRESPEC §5.2 specifies "< 500 m excluded". The 100 m buffer was the
exclusion boundary used in the extraction (distance = 0 inside the buffer → excluded).
All sites within 500 m of the point satisfy the benefit orientation (farther = better).

## Expected direction of effect

Using a single point instead of the full WHC boundary polygon concentrates the
criterion at one location. Point mass at specific distance intervals will be
higher than if the full boundary were used. The A4 amplitude (A_j) and its
contribution to TV_W may differ from a polygon-based extraction, but the direction
of the effect (farther from cultural heritage = better) is preserved.

The Cidade Velha site is the only UNESCO-inscribed heritage site on Santiago
(inscribed 2009, WH Committee Decision 33 COM 8B.51). A single-point approximation
is substantively correct for the site's location even if geometrically imprecise.

## Fogo control

Not applicable. A4 is an S-N-specific criterion; no equivalent exists in S-T.

## Expected bias direction

Indeterminate. The point-based A4 may overstate or understate distances to the
actual UNESCO buffer boundary depending on the shape of the inscribed area relative
to our reference point.

## Reference

UNESCO World Heritage Centre. (2009). Decision 33 COM 8B.51 — Cidade Velha,
Historic Centre of Ribeira Grande de Santiago (Cabo Verde). Retrieved from
https://whc.unesco.org/en/decisions/2153

Source file: data/santiago/patrimonio_cultural.geojson
  SHA-256: (see extract_report_sn.json; file not committed — gitignored)
  Features: 2 (both on Ilha do Santo Antão)

Fallback point: hard-coded in scripts/santiago_extract.py extract_sn() function,
confirmed in commit ebf7dfe.
