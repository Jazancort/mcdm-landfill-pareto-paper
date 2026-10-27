# -*- coding: utf-8 -*-
import sys, numpy as np, json, re
sys.path.insert(0, 'scripts')
from pathlib import Path

ROOT = Path(__file__).parent.parent
amp = json.loads((ROOT / 'results/amplitudes/amplitudes.json').read_text())
from fogo_constants import W as w_ahp, CRITERION_NAMES

rho = np.array([amp['rho_j'][k] for k in CRITERION_NAMES])
w   = np.array([w_ahp[j] for j in range(len(CRITERION_NAMES))])
w   = w / w.sum()

w_eff      = w * rho
w_eff_norm = w_eff / w_eff.sum()

m_eff = 1.0 / float(np.sum(w_eff_norm**2))
perm_idx   = list(CRITERION_NAMES).index('perm')
perm_share = float(w_eff_norm[perm_idx] * 100)
TV = 0.5 * float(np.abs(w_eff_norm - w).sum())

# contribution to |TV| deviation from perm
tv_half     = np.abs(w_eff_norm - w)
tv_total    = float(tv_half.sum())
perm_tv_pct = float(tv_half[perm_idx] / tv_total * 100)

# Macros
mamp = (ROOT / 'macros_amplitudes.tex').read_text(encoding='utf-8')
meff_macro = re.search(r'meff\}\{([0-9.]+)', mamp)
sxx_macro  = re.search(r'SxxPctVecOpt\}\{([0-9]+)', mamp)

print("m_eff (shift, correcto): %.4f" % m_eff)
print("perm share of w_eff:     %.1f%%" % perm_share)
print("perm contrib to |TV|:    %.1f%%" % perm_tv_pct)
print("TV(vec/shift):           %.4f" % TV)
print()
print("macros_amplitudes.tex:")
print("  meff  = %s" % (meff_macro.group(1) if meff_macro else "NAO ENCONTRADO"))
print("  SxxPct= %s%%" % (sxx_macro.group(1) if sxx_macro else "NAO ENCONTRADO"))
print()
print("Texto main.tex diz:")
print("  m_eff = 4.05  ->  correcto seria %.2f" % m_eff)
print("  45.4%%         ->  perm share %.1f%%  ou  perm contrib TV %.1f%%" % (perm_share, perm_tv_pct))

# Verificar o que o macros_amplitudes tem para meff
main_tex = (ROOT / 'main.tex').read_text(encoding='utf-8')
meff_in_text = re.search(r'm_\{\\mathrm\{eff\}\}=(\d+\.\d+)', main_tex)
sxx_in_text  = re.search(r'45\.4', main_tex)
print()
print("Ocorrencias em main.tex:")
print("  m_eff= %s" % (meff_in_text.group(0) if meff_in_text else "NAO ENCONTRADO"))
print("  45.4%%: %s" % ("ENCONTRADO" if sxx_in_text else "NAO"))
