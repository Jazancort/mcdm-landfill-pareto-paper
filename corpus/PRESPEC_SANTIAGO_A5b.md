# PRESPEC_SANTIAGO — Amendment A5b: seed change declaration and independent streams

```
Status:     pre-registered before any Santiago criterion value, score, frontier or Q2 exists.
Parent:     PRESPEC_SANTIAGO_A5a.md, frozen at tag prespec-santiago-a5a
            (commit e23be284679c3eb3846e687361b42de8a174d8ec).
Written:    2026-10-27
```

## Motivation

A5a was labelled a "clarification" but it materially changed a registered parameter:
the parent document (PRESPEC_SANTIAGO §3) and A5 §1 both fixed κ = 200 with seed 42,
inherited from the Fogo E7 pipeline. A5a replaced seed 42 with seed 17 (κ = 200) and
prohibited seed 42 from Santiago entirely. That is an amendment to registered parameters,
not a clarification. This document corrects the label and records the change formally,
before any Santiago data are extracted or any script is run.

A5a also asserted that S-T and S-N "streams are independent" while using the same parent
seed per κ with different w0. Because `rng(s).dirichlet(κ·w0, 500)` shares the same
underlying uniform variates for both branches (only the Dirichlet transformation differs),
the draws are NOT statistically independent. This amendment corrects the independence
claim by adopting SeedSequence.spawn(2) per κ, which produces genuinely independent
child generators for S-T and S-N.

No Santiago data have been extracted, computed, or inspected as of this commit. The
corrections are to parameter declarations only.

---

## 1. Formal declaration of A5a as an amendment to prior registrations

The following parameter changes, introduced in A5a, are hereby declared as amendments:

| Parameter | Prior value (§3 parent + A5 §1) | New value (A5a, confirmed here) | Reason |
|---|---|---|---|
| κ=200 seed (S-T) | 42 (from `e1_weights_k200.npy`, E7 Fogo) | 17 (fresh draw) | seed 42 reserved for Fogo legacy |
| κ=50 seed (S-T) | 42 (from `e1_weights_k50.npy`, E7 Fogo) | 4 (fresh draw) | same |
| κ=200 seed (S-N) | 42 (parent §3: `rng(42).dirichlet(200·w0_Cabral, 500)`) | 17 (fresh, child of SeedSequence(17) below) | same; now fully independent from S-T |
| Independence claim | "independent stream" (different w0, same base RNG) | Genuinely independent via SeedSequence.spawn(2) | correct A5a error |

These changes are pre-data. No deviation (DEV-SANT-xxx) is required because no data
were produced under the prior convention.

**Scope restriction (added here):** the "no seed 42" rule applies EXCLUSIVELY to
Santiago pipeline scripts. Fogo legacy scripts (run_e1.py, run_e7_kappa_sweep.py,
mc_unified.py, etc.) continue to use seed 42 and the existing E7 weight files.
The assert in gen_santiago_seeds.py must not be imported by Fogo scripts.

---

## 2. Independent stream construction (supersedes A5a §1 seed specification)

For each κ in {25, 50, 100, 200, 400, 1000}:

```python
import numpy as np

PARENT_SEEDS = {25: 1, 50: 4, 100: 15, 200: 17, 400: 28, 1000: 30}

def get_branch_rngs(kappa: int):
    """Return (rng_ST, rng_SN) — genuinely independent generators.

    Both are children of SeedSequence(parent_seed), so they are derived from
    the declared parent rule and are reproducible. child[0] is S-T, child[1] is S-N.
    """
    parent_seed = PARENT_SEEDS[kappa]
    children = np.random.SeedSequence(parent_seed).spawn(2)
    return np.random.default_rng(children[0]), np.random.default_rng(children[1])

# Usage:
# rng_ST, rng_SN = get_branch_rngs(200)
# weights_ST = rng_ST.dirichlet(200 * w0_Fogo,   500)
# weights_SN = rng_SN.dirichlet(200 * w0_Cabral, 500)
```

The function `get_branch_rngs` is implemented in `scripts/gen_santiago_seeds.py`
(updated at this amendment). The first draw of each stream is fixed for verification.

---

## 3. Verification table (reproducibility fingerprints)

The first Dirichlet draw from each child stream, for a 3-component equal-weight prior
at concentration κ, is tabulated for verification. Any implementation that does not
reproduce these values exactly (to 4 decimal places) has a seed bug.

| κ | Parent seed | S-T first draw [0,1,2] | S-N first draw [0,1,2] |
|---|---|---|---|
| 25 | 1 | [0.3727, 0.3924, 0.2349] | [0.4461, 0.2156, 0.3383] |
| 50 | 4 | [0.3212, 0.3124, 0.3664] | [0.2960, 0.3610, 0.3430] |
| 100 | 15 | [0.2817, 0.3366, 0.3817] | [0.3063, 0.3359, 0.3578] |
| 200 | 17 | [0.3273, 0.3247, 0.3480] | [0.3285, 0.3471, 0.3245] |
| 400 | 28 | [0.3341, 0.3451, 0.3208] | [0.3141, 0.3168, 0.3691] |
| 1000 | 30 | [0.3424, 0.3353, 0.3223] | [0.3376, 0.3289, 0.3335] |

Script: `scripts/gen_santiago_seeds.py --verify`. Abort Stage 2 if any row fails.

---

## 4. Within-branch pairing (unchanged)

Within each branch and each κ, all 8 factorial cells and the E1 cells (at κ = 200 and
κ = ∞) share the same 500 draws. The within-branch pairing enables paired bootstrap
contrasts (B = 2000) and is not affected by this amendment.

---

## 5. Complete seed specification (this amendment supersedes A5 §1 and A5a §1)

| κ | Parent seed | S-T rng | S-N rng |
|---|---|---|---|
| 25 | 1 | `default_rng(SeedSequence(1).spawn(2)[0])` | `default_rng(SeedSequence(1).spawn(2)[1])` |
| 50 | 4 | `default_rng(SeedSequence(4).spawn(2)[0])` | `default_rng(SeedSequence(4).spawn(2)[1])` |
| 100 | 15 | `default_rng(SeedSequence(15).spawn(2)[0])` | `default_rng(SeedSequence(15).spawn(2)[1])` |
| 200 | 17 | `default_rng(SeedSequence(17).spawn(2)[0])` | `default_rng(SeedSequence(17).spawn(2)[1])` |
| 400 | 28 | `default_rng(SeedSequence(28).spawn(2)[0])` | `default_rng(SeedSequence(28).spawn(2)[1])` |
| 1000 | 30 | `default_rng(SeedSequence(30).spawn(2)[0])` | `default_rng(SeedSequence(30).spawn(2)[1])` |
| ∞ | — | w = w0_Fogo (deterministic) | w = w0_Cabral (deterministic) |

The `spawn(2)` call is deterministic: `SeedSequence(s).spawn(2)` always produces the
same pair of child SeedSequence objects for the same `s`.
