"""Compute E1-B, E1-W, E1-V amplitudes from fogo_constants.py."""
import sys; sys.path.insert(0, 'scripts')
import numpy as np
from fogo_constants import W, AJ_VEC, OBJ_GROUPS, CRITERION_NAMES, TV_B_VEC, TV_W_VEC
from corpus_amplitudes import compute_TV_meff, compute_TV_between_within

print("Groups (source: fogo_constants.py -> main.tex tab:amplitude):")
for g_idx, g in enumerate(OBJ_GROUPS):
    print(f"  G{g_idx+1} = {[CRITERION_NAMES[j] for j in g]} indices={g}")

# Aj_bar_g: weighted mean rho_j within each group
Aj_bar = np.zeros(len(W))
print("\nAj_bar_g (weighted mean within group):")
for g_idx, g in enumerate(OBJ_GROUPS):
    wg = W[g]; Ajg = AJ_VEC[g]
    Ajbar_g = float(np.dot(wg, Ajg) / wg.sum())
    for j in g:
        Aj_bar[j] = Ajbar_g
    print(f"  G{g_idx+1}: Aj_bar={Ajbar_g:.6f}  W_g={wg.sum():.4f}  criteria={[CRITERION_NAMES[j] for j in g]}")

# E1-B: Aj = Aj_bar_g (constant within group)
Aj_E1B = Aj_bar.copy()
res_B  = compute_TV_meff(W, Aj_E1B)
bw_B   = compute_TV_between_within(W, Aj_E1B, OBJ_GROUPS)
print(f"\nE1-B (Aj=Aj_bar_g):")
print(f"  Aj = {np.round(Aj_E1B,4)}")
print(f"  TV={res_B['TV']:.6f}  TV_B={bw_B['TV_B']:.6f}  TV_W={bw_B['TV_W']:.2e}")
print(f"  TV_W < 1e-10: {abs(bw_B['TV_W']) < 1e-10}  (by algebra, must be exactly 0)")

# E1-W: rho_j / Aj_bar_g (equalise group means, preserve within-group ratios)
Aj_E1W_raw = AJ_VEC / Aj_bar
# Rescale so mean_w(Aj_E1W) = mean_w(AJ_VEC) (comparable overall scale)
scale = np.dot(W, AJ_VEC) / np.dot(W, Aj_E1W_raw)
Aj_E1W = Aj_E1W_raw * scale
res_W  = compute_TV_meff(W, Aj_E1W)
bw_W   = compute_TV_between_within(W, Aj_E1W, OBJ_GROUPS)
print(f"\nE1-W (Aj=rho_j/Aj_bar_g, rescaled by {scale:.4f}):")
print(f"  Aj = {np.round(Aj_E1W,4)}")
print(f"  TV={res_W['TV']:.4f}  TV_B={bw_W['TV_B']:.6f}  TV_W={bw_W['TV_W']:.4f}")
print(f"  TV_B < 0.001: {abs(bw_W['TV_B']) < 0.001}")

# E1-V: rho_j (vector normalisation)
res_V  = compute_TV_meff(W, AJ_VEC)
bw_V   = compute_TV_between_within(W, AJ_VEC, OBJ_GROUPS)
print(f"\nE1-V (Aj=rho_j, vector, published):")
print(f"  Aj = {AJ_VEC}")
print(f"  TV={res_V['TV']:.4f}  TV_B={bw_V['TV_B']:.4f}  TV_W={bw_V['TV_W']:.4f}")
print(f"  published: TV_B={TV_B_VEC}, TV_W={TV_W_VEC}")

# Summary table
print("\n=== Summary (inputs to PRESPEC_E1.md) ===")
print(f"  Cell   TV      TV_B    TV_W")
print(f"  E1-B   {res_B['TV']:.4f}  {bw_B['TV_B']:.4f}  {bw_B['TV_W']:.2e}  (TV_W=0 by algebra)")
print(f"  E1-W   {res_W['TV']:.4f}  {bw_W['TV_B']:.4f}  {bw_W['TV_W']:.4f}")
print(f"  E1-V   {res_V['TV']:.4f}  {bw_V['TV_B']:.4f}  {bw_V['TV_W']:.4f}")
