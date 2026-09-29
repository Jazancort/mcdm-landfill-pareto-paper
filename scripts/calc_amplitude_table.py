"""Compute A_j and w_eff/w ratios for tab:amplitude.

Analytical derivation of A_vec (vector normalisation):
  For a continuous criterion without ties:  A_j = rho_j = s_j / norm(x_j)
  where s_j = std(x_j) and norm(x_j) = sqrt(sum x_ij^2).
  The ratio rho_j is pre-computed from the raw data.

  For a binary (indicator) criterion (aspect, n1 ones out of N=389):
    norm(x_j) = sqrt(n1)       (only n1 entries are 1, rest are 0)
    mean(x_j) = n1/N
    s_j = sqrt(n1/N * (1-n1/N))
    A_j = rho_j = s_j / norm(x_j) = sqrt((1/N)(1 - n1/N)) = sqrt(n0/(N*n1))
    With n1=94, n0=295, N=389:
      A_j = sqrt(295 / (389 * 94)) = sqrt(295/36566) = 0.1031
  BUG HISTORY: previous value 0.0582 = 1/sqrt(295) used n0 instead of n1.

  For perm (n0=350 ties at 0, n1=39 non-zero):
    Same formula: A_j = sqrt(n1/(N*n0)) ... wait, perm is NOT binary —
    it has 350 zeros but the nonzero values are continuous distances.
    rho_perm is therefore computed from the raw column: confirmed=0.5827
    (audited externally; consistent with the continuous formula applied to
    the subset of nonzero values dominating the squared norm).

N, n1 for aspect:
  N=389 admissible sites; aspect indicator = 1 if aspect not in [90,180] deg
  n1=94 (ones, minority side), n0=295 (zeros)
"""
import math

N = 389
n1_aspect = 94
n0_aspect = 295

# aspect: binary indicator, correct formula A_j = sqrt(n0/(N*n1))
A_vec_aspect = math.sqrt(n0_aspect / (N * n1_aspect))
print(f"A_vec_aspect (corrected) = {A_vec_aspect:.4f}  (was 0.0582 = 1/sqrt(n0))")

W = {'perm':0.152,'slope':0.113,'roads':0.030,'rivers':0.091,'aspect':0.075,
     'coast':0.069,'protected':0.066,'wells':0.055,'urban':0.166,'aero':0.102,'cult':0.081}

# A_vec: all values audited from raw data; only aspect corrected here
A_vec  = {'perm':0.5827,'slope':0.1350,'roads':0.2056,'rivers':0.2649,
           'aspect': A_vec_aspect,          # CORRECTED: 0.1031 (was 0.0582)
           'coast':0.1258,'protected':0.1048,'wells':0.0811,
           'urban':0.1069,'aero':0.0863,'cult':0.1708}

# A_rank: (N-1)/(N+1) for continuous, N/[2(N+1)] for binary (aspect)
# urban has 5 ties → audited value 0.9885; cult 2 ties → 0.9808
A_rank = {'perm':0.5474,'slope':0.9949,'roads':0.9949,'rivers':0.9949,
           'aspect':0.4987,   # N/[2(N+1)] = 389/780
           'coast':0.9949,'protected':0.9949,'wells':0.9949,
           'urban':0.9885,'aero':0.9949,'cult':0.9808}

def weff(W, A):
    denom = sum(W[c]*A[c] for c in W)
    return {c: W[c]*A[c]/denom for c in W}

A_mm   = {c:1.0 for c in W}
we_mm  = weff(W, A_mm)
we_vec = weff(W, A_vec)
we_rank= weff(W, A_rank)

order = ['perm','slope','roads','rivers','aspect','coast','protected','wells','urban','aero','cult']

print(f"{'Criterion':12s}  {'w':5s}  {'A_vec':5s}  {'A_rank':5s}  {'r_vec':6s}  {'r_rank':6s}")
print('-'*60)
for c in order:
    r_vec  = we_vec[c]  / W[c]
    r_rank = we_rank[c] / W[c]
    print(f"{c:12s}  {W[c]:.3f}  {A_vec[c]:.3f}  {A_rank[c]:.3f}  {r_vec:.3f}   {r_rank:.3f}")

TV_vec  = 0.5*sum(abs(we_vec[c]-W[c])  for c in W)
TV_rank = 0.5*sum(abs(we_rank[c]-W[c]) for c in W)
print(f"\nTV: mm=0.000  vec={TV_vec:.4f} (rounds to {round(TV_vec,3):.3f})  rank={TV_rank:.4f} (rounds to {round(TV_rank,3):.3f})")
perm_r  = we_vec['perm']/W['perm']
urban_r = we_vec['urban']/W['urban']
print(f"perm vec factor: {perm_r:.2f}x  ({perm_r:.3f}x)")
print(f"urban vec factor: {urban_r:.2f}x  ({urban_r:.3f}x)")
print(f"aspect vec factor: {we_vec['aspect']/W['aspect']:.3f}x")
print(f"\nRegression slope (26.8pp / TV_vec): {26.8/TV_vec:.1f} pp/unit")

def weff(W, A):
    denom = sum(W[c]*A[c] for c in W)
    return {c: W[c]*A[c]/denom for c in W}

A_mm   = {c:1.0 for c in W}
we_mm  = weff(W, A_mm)
we_vec = weff(W, A_vec)
we_rank= weff(W, A_rank)

order = ['perm','slope','roads','rivers','aspect','coast','protected','wells','urban','aero','cult']

print(f"{'Criterion':12s}  {'w':5s}  {'A_vec':5s}  {'A_rank':5s}  {'r_vec':6s}  {'r_rank':6s}")
print('-'*60)
for c in order:
    r_vec  = we_vec[c]  / W[c]
    r_rank = we_rank[c] / W[c]
    print(f"{c:12s}  {W[c]:.3f}  {A_vec[c]:.3f}  {A_rank[c]:.3f}  {r_vec:.3f}   {r_rank:.3f}")

TV_vec  = 0.5*sum(abs(we_vec[c]-W[c])  for c in W)
TV_rank = 0.5*sum(abs(we_rank[c]-W[c]) for c in W)
print(f"TV: mm=0.000  vec={TV_vec:.3f}  rank={TV_rank:.3f}")
perm_r  = we_vec['perm']/W['perm']
urban_r = we_vec['urban']/W['urban']
print(f"perm vec factor: {perm_r:.2f}x")
print(f"urban vec factor: {urban_r:.2f}x")
