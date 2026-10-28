# -*- coding: utf-8 -*-
import sys; sys.path.insert(0, 'scripts')
import numpy as np
from fogo_constants import W as W_AHP, OBJ_GROUPS, TV_W_VEC, TV_B_VEC
from e6_generate_amplitudes import build_amplitude_cells

W_G = np.array([W_AHP[g].sum() for g in OBJ_GROUPS])

targets = [('prespec (rho_raw)', 0.1986), ('sensit (rho_shift)', 0.1954)]
for label, tw_F in targets:
    cells, tv_report, warnings = build_amplitude_cells(
        w_ref=W_AHP, groups=OBJ_GROUPS, W_G=W_G,
        tw_L=0.10, tw_F=tw_F, tw_H=0.30, tb=TV_B_VEC
    )
    print("Target TW_F = %.4f (%s):" % (tw_F, label))
    for cell in ['W_inf_F', 'V_inf_F', 'W_def_F', 'W_inf_L', 'W_inf_H', 'M', 'B']:
        tvs = tv_report[cell]
        print("  %-12s: tv_w=%.6f  tv_b=%.6f" % (cell, tvs['tv_w'], tvs['tv_b']))
    if warnings:
        for w in warnings:
            print("  WARNING: %s" % w)
    print()

print("Diferenca tvw_achieved entre as duas corridas:")
_, tvr1, _ = build_amplitude_cells(W_AHP, OBJ_GROUPS, W_G,
                                    tw_F=0.1986, tw_L=0.10, tw_H=0.30, tb=TV_B_VEC)
_, tvr2, _ = build_amplitude_cells(W_AHP, OBJ_GROUPS, W_G,
                                    tw_F=0.1954, tw_L=0.10, tw_H=0.30, tb=TV_B_VEC)
for cell in ['W_inf_F', 'V_inf_F', 'W_def_F']:
    d = tvr1[cell]['tv_w'] - tvr2[cell]['tv_w']
    print("  %-12s: prespec=%.6f  sensit=%.6f  delta=%+.6f" % (
        cell, tvr1[cell]['tv_w'], tvr2[cell]['tv_w'], d))
