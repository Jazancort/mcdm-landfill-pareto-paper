# DEVIATIONS.md — Deviations from PRESPEC.md protocol

This file records any deviation from the pre-specified protocol in PRESPEC.md.

## DEV-001: Vafaei2022 — weights normalised

**Entry:** vafaei2022
**Date:** 2026-09-30
**Deviation:** The published weights [0.03, 0.10, 0.30, 0.15, 0.15] sum to 0.73,
not 1.0. This likely indicates a 6th criterion whose weight is not printed in
the table (possible typographic omission or the paper only reports 5 of 6).
**Action:** Weights normalised to sum=1 by dividing by 0.73.
**Impact:** TV and m_eff computed on the normalised weights. Results flagged as
PENDING until the original Chakraborty & Yeh (2007/2009) source is verified.
**Justification:** Normalisation preserves relative weights; the mechanism is
scale-free with respect to w_j → c*w_j, c>0.
