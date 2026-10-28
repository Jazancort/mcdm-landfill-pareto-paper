"""gen_santiago_seeds.py — canonical seed table for Santiago kappa grid.

Seed rule (declared in PRESPEC_SANTIAGO_A5a, superseded by A5b):
  kappa in {25, 50, 100, 200, 400, 1000} -> parent seeds {1, 4, 15, 17, 28, 30}
  Each kappa spawns two INDEPENDENT child generators via SeedSequence.spawn(2):
    child[0] -> S-T (Fogo AHP weights)
    child[1] -> S-N (Cabral weights)

SCOPE: this module applies ONLY to Santiago pipeline scripts.
Fogo legacy scripts (run_e1.py, run_e7_kappa_sweep.py, mc_unified.py, etc.)
continue to use seed 42 and the E7 weight files. The assert below must NOT be
imported by Fogo scripts.

Seed 42 is NEVER used in Santiago (reserved for Fogo legacy runs only).

Usage
-----
    uv run python scripts/gen_santiago_seeds.py          # print table
    uv run python scripts/gen_santiago_seeds.py --verify # verify fingerprints

Import:
    from scripts.gen_santiago_seeds import get_branch_rngs, get_seed, KAPPA_VALUES
"""

import sys

# ---------------------------------------------------------------------------
# Canonical mapping — do not modify without a new amendment + tag
# ---------------------------------------------------------------------------

KAPPA_VALUES = [25, 50, 100, 200, 400, 1000]
SEED_VALUES  = [ 1,  4,  15,  17,  28,   30]

SEEDS: dict[int, int] = dict(zip(KAPPA_VALUES, SEED_VALUES))
"""Maps each stochastic kappa to its canonical PARENT seed."""

FORBIDDEN_SEED = 42
"""Seed 42 is reserved for Fogo legacy runs only. Never use for Santiago."""

# Verification fingerprints (A5b §3): first Dirichlet draw from each child stream,
# equal-weight 3-component prior at concentration kappa.
FINGERPRINTS = {
    25:   {"ST": [0.3727, 0.3924, 0.2349], "SN": [0.4461, 0.2156, 0.3383]},
    50:   {"ST": [0.3212, 0.3124, 0.3664], "SN": [0.2960, 0.3610, 0.3430]},
    100:  {"ST": [0.2817, 0.3366, 0.3817], "SN": [0.3063, 0.3359, 0.3578]},
    200:  {"ST": [0.3273, 0.3247, 0.3480], "SN": [0.3285, 0.3471, 0.3245]},
    400:  {"ST": [0.3341, 0.3451, 0.3208], "SN": [0.3141, 0.3168, 0.3691]},
    1000: {"ST": [0.3424, 0.3353, 0.3223], "SN": [0.3376, 0.3289, 0.3335]},
}


def get_seed(kappa: int) -> int:
    """Return the canonical PARENT seed for a given kappa value.

    @param kappa - concentration parameter; must be in KAPPA_VALUES.
    @returns canonical parent seed integer.
    @raises ValueError if kappa is not registered.
    """
    if kappa not in SEEDS:
        raise ValueError(
            f"kappa={kappa} is not in the registered grid {KAPPA_VALUES}. "
            "Add a new amendment before using a different kappa."
        )
    seed = SEEDS[kappa]
    assert seed != FORBIDDEN_SEED, (
        f"BUG: seed {seed} equals the forbidden Fogo seed 42."
    )
    return seed


def get_branch_rngs(kappa: int):
    """Return (rng_ST, rng_SN) -- genuinely independent child generators.

    Both children are derived from SeedSequence(parent_seed), so they are
    reproducible. child[0] is S-T, child[1] is S-N. The streams are
    statistically independent (different internal states from spawn(2)).

    @param kappa - concentration parameter; must be in KAPPA_VALUES.
    @returns tuple (rng_ST, rng_SN) of numpy.random.Generator instances.

    Usage:
        rng_ST, rng_SN = get_branch_rngs(200)
        weights_ST = rng_ST.dirichlet(200 * w0_Fogo,   500)
        weights_SN = rng_SN.dirichlet(200 * w0_Cabral, 500)
    """
    try:
        import numpy as np
    except ImportError:
        raise ImportError("numpy is required to use get_branch_rngs")
    parent_seed = get_seed(kappa)
    children = np.random.SeedSequence(parent_seed).spawn(2)
    return np.random.default_rng(children[0]), np.random.default_rng(children[1])


def verify_no_forbidden_seeds() -> None:
    """Assert that seed 42 does not appear in SEEDS. Call at import time."""
    for k, s in SEEDS.items():
        if s == FORBIDDEN_SEED:
            raise RuntimeError(
                f"FORBIDDEN: kappa={k} maps to seed {FORBIDDEN_SEED} (Fogo legacy seed). "
                "Santiago must never use seed 42."
            )


verify_no_forbidden_seeds()


# ---------------------------------------------------------------------------
# Fingerprint verification
# ---------------------------------------------------------------------------

def verify_fingerprints() -> bool:
    """Verify that each branch RNG reproduces the tabulated first draw.

    @returns True if all fingerprints match, raises AssertionError otherwise.
    """
    import numpy as np
    all_ok = True
    for k in KAPPA_VALUES:
        rng_st, rng_sn = get_branch_rngs(k)
        st_draw = rng_st.dirichlet([k] * 3, 1)[0].round(4).tolist()
        sn_draw = rng_sn.dirichlet([k] * 3, 1)[0].round(4).tolist()
        fp = FINGERPRINTS[k]
        st_ok = all(abs(a - b) < 5e-4 for a, b in zip(st_draw, fp["ST"]))
        sn_ok = all(abs(a - b) < 5e-4 for a, b in zip(sn_draw, fp["SN"]))
        status = "PASS" if (st_ok and sn_ok) else "FAIL"
        if not (st_ok and sn_ok):
            all_ok = False
        print(f"  k={k:4d}  S-T {status}  {st_draw}  (expected {fp['ST']})")
        print(f"  {'':4s}  S-N {status}  {sn_draw}  (expected {fp['SN']})")
    return all_ok


# ---------------------------------------------------------------------------
# Human-readable table (stdout when run directly)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if "--verify" in sys.argv:
        print("Verifying Santiago seed fingerprints (PRESPEC_SANTIAGO_A5b §3)...")
        ok = verify_fingerprints()
        print()
        if ok:
            print("ALL FINGERPRINTS PASS")
        else:
            print("FINGERPRINT FAILURES DETECTED -- abort Stage 2")
            sys.exit(1)
        sys.exit(0)

    print("Santiago kappa-grid seed table (A5b: SeedSequence.spawn(2))")
    print("=" * 60)
    print(f"{'kappa':>8}  {'parent seed':>11}  {'stream S-T':<30}  {'stream S-N'}")
    print("-" * 60)
    for k, s in SEEDS.items():
        st = f"default_rng(SeedSequence({s}).spawn(2)[0])"
        sn = f"default_rng(SeedSequence({s}).spawn(2)[1])"
        print(f"{k:>8}  {s:>11}  {st:<38}  {sn}")
    print(f"{'inf':>8}  {'—':>11}  {'w = w0_Fogo (deterministic)':<38}  w = w0_Cabral (deterministic)")
    print()
    print(f"FORBIDDEN seed: {FORBIDDEN_SEED} (Fogo legacy -- Santiago ONLY rule)")
    print()
    print("SCOPE: this module is for Santiago scripts ONLY.")
    print("Fogo legacy scripts (E1-E7) continue to use seed 42.")
    print()
    print("Source: PRESPEC_SANTIAGO_A5b.md, tag prespec-santiago-a5b")
    print("Rule:   parent seeds 01 04 15 17 28 30 (user-declared 2026-10-27)")

