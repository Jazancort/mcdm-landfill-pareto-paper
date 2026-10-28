# -*- coding: utf-8 -*-
"""_diag_tv_bug.py -- compute TV for canonical vs buggy score."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pathlib import Path
from mcdm_experiment import AHP_WEIGHTS

ROOT = Path(__file__).parent.parent
col_names = list(AHP_WEIGHTS.keys())
w_nom = np.array(list(AHP_WEIGHTS.values()))

rho_can = json.loads((ROOT/"results/amplitudes/amplitudes.json").read_text())["rho_j"]
amp_can = np.array([rho_can[k] for k in col_names])

asp_idx = col_names.index("aspect")
amp_bug = amp_can.copy()
amp_bug[asp_idx] = 1.0  # BUG: raw {0,1}, not L2-normalised

S_can = (w_nom * amp_can).sum()
S_bug = (w_nom * amp_bug).sum()
w_eff_can = w_nom * amp_can / S_can
w_eff_bug = w_nom * amp_bug / S_bug

tv_can = 0.5 * np.abs(w_eff_can - w_nom).sum()
tv_bug = 0.5 * np.abs(w_eff_bug - w_nom).sum()

print(f"TV_canonical = {tv_can:.4f}  (paper: ~0.311)")
print(f"TV_bug       = {tv_bug:.4f}  (reviewer calculated ~0.38)")
print()
print(f"{'crit':12s}  {'w_nom':>6s}  {'w_eff_can':>9s}  {'w_eff_bug':>9s}  {'delta_bug':>9s}")
for j, k in enumerate(col_names):
    print(f"  {k:12s}  {w_nom[j]:.3f}   {w_eff_can[j]:.3f}      {w_eff_bug[j]:.3f}      {w_eff_bug[j]-w_nom[j]:+.3f}")
print()
perm_idx = col_names.index("perm")
print(f"aspect amp: bug={amp_bug[asp_idx]:.3f} vs can={amp_can[asp_idx]:.4f} ({1.0/amp_can[asp_idx]:.1f}x)")
print(f"perm   amp: bug={amp_bug[perm_idx]:.4f} vs can={amp_can[perm_idx]:.4f} (unchanged)")
print()
print("Pole inversion for aspect in buggy score:")
print("  leeward (good sites) -> c_asp=0 -> contribution=-w_asp*0=0")
print("  windward (bad sites) -> c_asp=1 -> contribution=-w_asp*1=-0.075")
print("  Net effect: score PENALIZES windward, NEUTRAL on leeward.")
print("  Direction is accidentally correct (penalizing windward is right)")
print("  but amplitude is 9.7x too large.")
