"""gen_santiago_seeds.py — canonical seed table for Santiago κ grid.

Seed rule (declared in PRESPEC_SANTIAGO_A5a, tag prespec-santiago-a5a):
  κ ∈ {25, 50, 100, 200, 400, 1000} → seeds {1, 4, 15, 17, 28, 30}
  Seed 42 is NEVER used in Santiago (reserved for Fogo legacy runs only).

Both S-T (w0 = Fogo AHP) and S-N (w0 = Cabral) use the same seed per κ;
the streams are statistically independent because w0_Fogo ≠ w0_Cabral, so
rng(seed).dirichlet(κ·w0_Fogo, 500) and rng(seed).dirichlet(κ·w0_Cabral, 500)
produce different draws. If strict RNG-level independence is required in
a future revision, additional seeds must be requested and recorded in a new
amendment before any data are processed.

κ = ∞ is deterministic (w = w0 directly); no seed is needed.

Usage
-----
    uv run python scripts/gen_santiago_seeds.py

Output
------
Prints the seed table to stdout. Import SEEDS or get_seed() for use in
pipeline scripts.
"""

# ---------------------------------------------------------------------------
# Canonical mapping — do not modify without a new amendment + tag
# ---------------------------------------------------------------------------

KAPPA_VALUES = [25, 50, 100, 200, 400, 1000]
SEED_VALUES  = [ 1,  4,  15,  17,  28,   30]

SEEDS: dict[int, int] = dict(zip(KAPPA_VALUES, SEED_VALUES))
"""Maps each stochastic κ to its canonical seed."""

FORBIDDEN_SEED = 42
"""Seed 42 is reserved for Fogo legacy runs only. Never use for Santiago."""


def get_seed(kappa: int) -> int:
    """Return the canonical seed for a given κ value.

    @param kappa - concentration parameter; must be in KAPPA_VALUES.
    @returns canonical seed integer.
    @raises ValueError if kappa is not registered or seed 42 would be used.
    """
    if kappa not in SEEDS:
        raise ValueError(
            f"κ={kappa} is not in the registered grid {KAPPA_VALUES}. "
            "Add a new amendment before using a different κ."
        )
    seed = SEEDS[kappa]
    assert seed != FORBIDDEN_SEED, (
        f"BUG: seed {seed} equals the forbidden Fogo seed 42."
    )
    return seed


def verify_no_forbidden_seeds() -> None:
    """Assert that seed 42 does not appear in SEEDS. Call at import time."""
    for k, s in SEEDS.items():
        if s == FORBIDDEN_SEED:
            raise RuntimeError(
                f"FORBIDDEN: κ={k} maps to seed {FORBIDDEN_SEED} (Fogo legacy seed). "
                "Santiago must never use seed 42."
            )


verify_no_forbidden_seeds()


# ---------------------------------------------------------------------------
# Human-readable table (stdout when run directly)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print("Santiago kappa-grid seed table")
    print("=" * 50)
    print(f"{'kappa':>8}  {'seed':>6}  {'stream note'}")
    print("-" * 50)
    for k, s in SEEDS.items():
        note = "S-T: rng(seed).dirichlet(k*w0_Fogo, 500)"
        print(f"{k:>8}  {s:>6}  {note}")
        note = "S-N: rng(seed).dirichlet(k*w0_Cabral, 500)"
        print(f"{'':>8}  {'':>6}  {note}")
        print()
    print(f"  kappa=inf  -> deterministic (w = w0); no seed")
    print()
    print(f"FORBIDDEN seed: {FORBIDDEN_SEED} (Fogo legacy -- never use for Santiago)")
    print()
    print("Source: PRESPEC_SANTIAGO_A5a.md, tag prespec-santiago-a5a")
    print("Rule:   01 04 15 17 28 30  (user-declared, 2026-10-27)")
