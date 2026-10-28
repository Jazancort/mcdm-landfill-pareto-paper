# DEV-SANT-ORDER-001 — Exploratory S-T extraction before Stage 1 confirmation
Date: 2026-10-28
Type: procedural deviation (pre-data; no results used)

Description:
  The S-T extraction (commit f07502a) was run before the Stage 1 regression
  was explicitly confirmed in the same session, and using Copernicus GLO-30
  instead of the declared ASTER GDEM v3 (PRESPEC_SANTIAGO §3).

  Stage 1 was committed at 3aa1143 BEFORE the extraction, so the git sequence
  is formally correct. However, the session did not verify Stage 1 completion
  before proceeding, and the DEM was a substitute.

Expected effect on analysis:
  None — this extraction is declared exploratory and will NOT be used in any
  analysis, amplitude computation, Monte Carlo, or prediction report.
  The official Stage 2 will be run after:
    (a) ASTER GDEM v3 tiles are downloaded and validated;
    (b) C-2 (wells) decision is committed;
    (c) |T| is checked and spacing rule applied if needed.

Affected files (exploratory, not canonical):
  results/santiago/df_santiago_st.csv   (f07502a) — exploratory, replaced by official run
  results/santiago/extract_report_st.json — same

Official Stage 2 will overwrite these files after ASTER validation.
