# -*- coding: utf-8 -*-
"""audit_e6_group_constancy.py
For each draw and each E6 condition (M, B, C), compute
ratio_j = w_sc,j * A_j / W_CRIT_j for every criterion j.
Check if the ratio is constant within each group (3/5/3).
If yes, the analytic guarantee of Theorem~thm:groupconst applies.
If no, the 100% result is empirical, not analytic.
"""
import numpy as np
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent

# --- Reproduce E6 setup from run_e6_generator.py ---
W_G = np.array([0.295, 0.356, 0.349])
GROUPS = [list(range(0, 3)), list(range(3, 8)), list(range(8, 11))]
M_CRIT = 11

W_CRIT_BASE = np.concatenate([
    np.full(len(g), W_G[gi] / len(g))
    for gi, g in enumerate(GROUPS)
])
W_CRIT_BASE = W_CRIT_BASE / W_CRIT_BASE.sum()

# Amplitudes by condition (from run_e6_generator.py)
# M: A_j = 1 (aligned control)
# B: A_j = A_g (group amplitude, same for all j in group)
# C: A_j = 1/rho_j (compensation)
# W: A_j = within-group amplitude from vector norm
# V: A_j = full vector amplitude

# For M and B: amplitudes are constant within groups by construction
# For C: w_j' = w_j/rho_j => score proportional to sum w_j' * n_j = sum (w_j/rho_j) * A_j * c_j
#   ratio_j = w_sc,j * A_j / W_CRIT_j = (w_draw_j / rho_j) * A_j / W_CRIT_j
#   For C, w_sc,j = w_draw_j / rho_j and A_j = rho_j => ratio_j = w_draw_j / W_CRIT_j
# So constancy depends on whether w_draw_j / W_CRIT_j is constant within group.

# Load seeds to get the RNG setup
seeds = json.load(open(ROOT / "results" / "e6" / "e6_seeds.json"))
KAPPA = 200
N_DRAWS = 200
RNG_SEED = 9999

# Generate draws for ONE instance (same as in run_e6_generator.py)
rng = np.random.default_rng(RNG_SEED)
draws = rng.dirichlet(KAPPA * W_CRIT_BASE, size=N_DRAWS)  # (N_DRAWS, M_CRIT)

print("=" * 60)
print("AUDIT: within-group constancy of w_sc,j * A_j / W_CRIT_j")
print("=" * 60)
print(f"\nW_CRIT_BASE: {np.round(W_CRIT_BASE, 4)}")
print(f"Groups: {GROUPS}")

for cond_name, get_A in [
    ("M", lambda draw, rho: np.ones(M_CRIT)),
    ("B", lambda draw, rho: np.concatenate([
        np.full(len(g), draw[g].sum() / W_CRIT_BASE[g].sum())
        for g in GROUPS
    ])),
    ("C", lambda draw, rho: rho),  # w_sc = draw/rho, A = rho => ratio = draw/W_CRIT
]:
    print(f"\n--- Condition {cond_name} ---")
    # For M and B: ratio = draw * A / W_CRIT
    # For C: ratio = (draw/rho) * rho / W_CRIT = draw / W_CRIT

    # Use a dummy rho = ones for M/B, actual rho for C
    # rho doesn't matter for M/B since we compute draw*A/W_CRIT

    # Sample a few draws to check constancy
    violations = 0
    max_cv = 0.0

    for draw in draws[:50]:  # check first 50 draws
        if cond_name == "M":
            A = np.ones(M_CRIT)
            w_sc = draw
        elif cond_name == "B":
            # group amplitude: A_j = sum(draw_g)/sum(W_CRIT_g)
            A = np.concatenate([
                np.full(len(g), draw[g].sum() / W_CRIT_BASE[g].sum())
                for g in GROUPS
            ])
            w_sc = draw
        elif cond_name == "C":
            # w_sc,j = draw_j / rho_j, A_j = rho_j
            # we need rho — but rho = A_vector from this instance
            # For the audit we use rho=1 to show the ratio reduces to draw/W_CRIT
            A = np.ones(M_CRIT)  # A_j = rho_j cancels w/ w_sc,j = draw_j/rho_j
            w_sc = draw  # effectively draw_j/rho_j * rho_j = draw_j

        ratio = (w_sc * A) / W_CRIT_BASE

        for g_idx, g in enumerate(GROUPS):
            r_g = ratio[g]
            cv = r_g.std() / r_g.mean() if r_g.mean() > 0 else 0
            max_cv = max(max_cv, cv)
            if cv > 1e-9:
                violations += 1

    print(f"  Violations (CV>0) in 50 draws × 3 groups: {violations}")
    print(f"  Max within-group CV of ratio: {max_cv:.2e}")
    if violations == 0:
        print(f"  RESULT: ratio is exactly constant within groups => ANALYTIC guarantee applies")
    else:
        print(f"  RESULT: ratio varies within groups => empirical observation only")

print("\n--- Summary ---")
print("M: A_j=1, w_sc=draw => ratio_j = draw_j/W_CRIT_j")
print("  Constant within group IFF draw_j proportional to W_CRIT_j within each group.")
print("  Dirichlet(kappa*W_CRIT_BASE) draws ARE proportional in expectation,")
print("  but NOT exactly per-draw. So M is empirical (not analytic) per draw.")
print()
print("B: A_j=A_g (group constant), w_sc=draw => ratio_j=draw_j*A_g/W_CRIT_j")
print("  A_g=sum(draw_g)/sum(W_CRIT_g). So ratio_j = draw_j*sum(draw_g)/(W_CRIT_j*sum(W_CRIT_g))")
print("  Constant within group IFF draw_j/W_CRIT_j is constant within group => same as M.")
print()
print("C: w_sc,j=draw_j/rho_j, A_j=rho_j => ratio_j=draw_j/W_CRIT_j => same as M.")
print()
print("CONCLUSION: For Dirichlet draws, the ratio is NOT exactly constant per draw.")
print("The 100% result for M/B/C is empirical, not a universal analytic guarantee.")
print("It IS analytically guaranteed at the EXPECTED draw E[w]=W_CRIT,")
print("and empirically holds for all 45x200 draws due to the near-proportionality")
print("of Dirichlet(kappa=200) draws with kappa large enough.")
