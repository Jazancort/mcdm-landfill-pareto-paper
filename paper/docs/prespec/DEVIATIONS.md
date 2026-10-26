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


## DEV-002: m≥8 exclusion criterion added post-result

**Date:** 2026-09-30
**When added:** After observing Q2=0% for junaid2024 and Q2=100% for all cells,
  which prompted investigation that identified the root causes as a combination
  of orientation bugs and insufficient alternative space.
**Deviation:** §5 (m≥8 minimum) was not in PRESPEC v1. It was written after
  examining Q2 results and is therefore not prospectively declared.
**Structural justification (independent of results):** C(m,3) < 56 for m<8;
  without coupling constraints, the frontier covers a large fraction of the
  trio space, making Q2 nearly deterministically 100% regardless of normalisation.
  The criterion would have been declared prospectively had this been analysed
  in advance.
**Impact on corpus:** excludes bhaskar2023_asn (m=4), bhaskar2023_agr (m=4),
  chen2020 (m=5), vafaei2022 (m=6) from Q2 analysis. All remain in the
  amplitude table.

## DEV-003: Scope decision added post-result

**Date:** 2026-09-30
**When added:** After observing Q2=100% in all 9 Monte Carlo cells (3 instances ×
  3 normalisations).
**Deviation:** §6 scope decision ("corpus=amplitude table; Q2 via WS2") was
  written after seeing the results it cites. It is not prospectively declared.
**Structural justification:** The conclusion that Q2 is uninformative without
  coupling constraints follows from Proposition 1 and its Extension (one-criterion
  groups, affine normalisations). These theorems hold independently of the
  observed 100%. The scope decision would have been reached by prior analysis.
**Impact:** H1 and H2 are withdrawn (DEV-004). The corpus Q2 table is retained
  as a regression test but not reported as evidence for the ordering claim.

## DEV-004: H1 and H2 formally withdrawn

**Date:** 2026-09-30
**Deviation:** PRESPEC v1 §5 declared H1 (Q2(mm)≥Q2(vec) per instance) and
  H2 (Spearman ρ>0 across instances). Both are withdrawn.
**Reason:**
  H1: Without coupling constraints, Q2=1 by Proposition 1 (matched cells) and
  by the Extension (affine normalisations with multi-criterion groups). The
  ordering Q2(mm)≥Q2(vec) cannot be falsified in this design — it holds as
  an algebraic consequence, not as an empirical finding.
  H2: With Q2≈100% in all cells, the efficiency loss Loss=Q2(mm)-Q2(vec) is
  indistinguishable from 0 at N=3500. Spearman ρ is undefined on a constant.
**Status:** The ordering claim (H1) is tested via the A_j(t) path in WS2,
  which has coupling constraints and discriminating frontier base rates.
  H2 is replaced by the WS2 regression of Q2 loss on TV_W(t).

## DEV-005: vafaei2018 grouping corrected from 1-criterion groups

**Date:** 2026-09-30
**Original grouping:** [[0], [1], [2]] — one criterion per group.
**Corrected grouping:** [[0, 1], [2]] — illumination+reachability (benefit)
  as G1; land texture (cost) as G2.
**Reason:** One-criterion groups are degenerate for any affine normalisation
  (Extension of Proposition 1): the SAW score is a positive scalarisation of
  the group objectives, so Q2=1 by theorem for vector normalisation regardless
  of weights. Reporting this as a finding would be a tautology. The corrected
  grouping follows the natural semantic split in the source article (operational
  factors vs. terrain texture).
**Impact:** TV_W now defined for vafaei2018; Q2 cell for vector norm no longer
  trivially 100% by the affine argument (though still likely ~100% due to
  frontier base rate = 1.8% with m=16, n=3).
