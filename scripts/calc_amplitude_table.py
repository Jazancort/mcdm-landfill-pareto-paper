"""Compute A_j and w_eff/w ratios for tab:amplitude."""
W = {'perm':0.152,'slope':0.113,'roads':0.030,'rivers':0.091,'aspect':0.075,
     'coast':0.069,'protected':0.066,'wells':0.055,'urban':0.166,'aero':0.102,'cult':0.081}

A_vec  = {'perm':0.5827,'slope':0.1350,'roads':0.2056,'rivers':0.2649,'aspect':0.0582,
           'coast':0.1258,'protected':0.1048,'wells':0.0811,'urban':0.1069,'aero':0.0863,'cult':0.1708}
A_rank = {'perm':0.5474,'slope':0.9949,'roads':0.9949,'rivers':0.9949,'aspect':0.4987,
           'coast':0.9949,'protected':0.9949,'wells':0.9949,'urban':0.9885,'aero':0.9949,'cult':0.9808}

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
