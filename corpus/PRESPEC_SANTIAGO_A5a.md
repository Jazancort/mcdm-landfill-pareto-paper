# PRESPEC_SANTIAGO — Amendment A5a: seed table clarification

```
Status:     pre-registered before any Santiago criterion value, score, frontier or Q2 exists.
Parent:     PRESPEC_SANTIAGO_A5.md, frozen at tag prespec-santiago-a5
            (commit fa2f9a2eff6f102b74af53902047f029b9d1f71f).
Written:    2026-10-27
```

Motivation: PRESPEC_SANTIAGO_A5.md cited the E7/Fogo seed-42 convention for κ = 200 and
κ = 50. The project rule is that seed 42 is NEVER used for Santiago (reserved for Fogo
legacy runs only). This amendment supersedes the seed specification in A5 §1 and records
the canonical seed table before any Santiago data are extracted or any script is run.

A5a also corrects the A5 statement "the κ = 200 draws are those of the parent pipeline
(seed 42)": the Santiago κ = 200 draws use seed 17, generated fresh. No E7 weight file
from Fogo is reused for Santiago.

All other content of A5 remains in force.

---

## 1. Canonical seed table

Seed rule: `01 04 15 17 28 30` mapped to κ ∈ {25, 50, 100, 200, 400, 1000}.
Source: user declaration 2026-10-27. Implemented in `scripts/gen_santiago_seeds.py`.

**Seed 42 is forbidden for any Santiago computation.** It is reserved for Fogo legacy
runs (E1–E7) and must not appear in any Santiago pipeline script or configuration file.

| κ | Seed | S-T draw command | S-N draw command |
|---|---|---|---|
| 25 | 1 | `rng(1).dirichlet(25·w0_Fogo, 500)` | `rng(1).dirichlet(25·w0_Cabral, 500)` |
| 50 | 4 | `rng(4).dirichlet(50·w0_Fogo, 500)` | `rng(4).dirichlet(50·w0_Cabral, 500)` |
| 100 | 15 | `rng(15).dirichlet(100·w0_Fogo, 500)` | `rng(15).dirichlet(100·w0_Cabral, 500)` |
| 200 | 17 | `rng(17).dirichlet(200·w0_Fogo, 500)` | `rng(17).dirichlet(200·w0_Cabral, 500)` |
| 400 | 28 | `rng(28).dirichlet(400·w0_Fogo, 500)` | `rng(28).dirichlet(400·w0_Cabral, 500)` |
| 1000 | 30 | `rng(30).dirichlet(1000·w0_Fogo, 500)` | `rng(30).dirichlet(1000·w0_Cabral, 500)` |
| ∞ | — | w = w0_Fogo (deterministic) | w = w0_Cabral (deterministic) |

`rng(s)` = `numpy.random.default_rng(s)`.

**Independence note.** S-T and S-N use the same seed per κ but different concentration
vectors (w0_Fogo vs w0_Cabral). Because `rng(s).dirichlet(α·w0, 500)` is a deterministic
function of the seed AND the parameter vector, and w0_Fogo ≠ w0_Cabral, the two draw
matrices are different — but the underlying uniform samples are the same, so they are
not statistically independent at the RNG level. This co-dependence is acceptable for
descriptive within-κ contrasts; it would be a concern only if cross-branch correlation
were modelled explicitly. If strict RNG-level independence is required in a future
revision, additional seeds must be requested from the author and recorded in a new
amendment before any data are processed. The current S-T/S-N correlation structure
is weaker than the within-draw pairing used in bootstrap contrasts (B = 2000).

---

## 2. Verification gate (Stage 1, before any Santiago data)

Before Stage 2 begins, the pipeline script must:

```python
from scripts.gen_santiago_seeds import get_seed, FORBIDDEN_SEED, KAPPA_VALUES
import numpy as np

# Verify seed table at import time (asserts no forbidden seeds)
# Then spot-check: seed 42 must not appear
assert FORBIDDEN_SEED not in [get_seed(k) for k in KAPPA_VALUES], \
    "ABORT: seed 42 found in Santiago seed table"

# Verify deterministic reproducibility: same seed → same first draw
for k in KAPPA_VALUES:
    s = get_seed(k)
    d1 = np.random.default_rng(s).dirichlet([k]*3, 1)
    d2 = np.random.default_rng(s).dirichlet([k]*3, 1)
    assert np.allclose(d1, d2), f"RNG not deterministic for κ={k}, seed={s}"

print("Seed verification PASS: no forbidden seeds, deterministic RNG confirmed")
```

If this gate fails, abort Stage 2 and log as DEV-SANT-xxx.

---

## 3. Superseded text in A5

The following passages in PRESPEC_SANTIAGO_A5.md §1 are superseded by this amendment:

- "the κ = 200 draws are those of the parent pipeline (seed 42)." → **replaced by seed 17.**
- "S-T reuses `e1_weights_k50.npy` (seed 42; ...)" → **replaced by seed 4 (fresh draw).**
- "seed convention identical to PRESPEC_E7_KAPPA_A2 [cite section]" → **superseded by the table above. E7/Fogo weight files are NOT reused for Santiago.**

No other content of A5 is affected.

---

## 4. Deviation from A5

The change from the E7/Fogo seed convention to the rule `01 04 15 17 28 30` is logged
here as a pre-data clarification, not a deviation (no data were processed under the old
convention). If any script had already generated Santiago weight draws using seed 42 before
this amendment, that would constitute DEV-SANT-001; as of this commit, no such script exists.
