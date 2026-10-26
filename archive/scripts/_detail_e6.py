# -*- coding: utf-8 -*-
import sys, pandas as pd
sys.path.insert(0, 'scripts')
from pathlib import Path

ROOT = Path('.')
prin = pd.read_csv(ROOT / 'results/e6/e6_raw_prespec.csv')
sens = pd.read_csv(ROOT / 'results/e6/sensit/e6_raw_sensit_tvwF01954.csv')
merge_cols = ['family', 'inst_id', 'draw']

print("Diferencas por celula:")
for cell in ['M','B','W_inf_L','W_inf_F','W_inf_H','V_inf_F','W_def_F']:
    p_c = prin[prin['cell'] == cell]
    s_c = sens[sens['cell'] == cell]
    m = p_c[merge_cols + ['q2']].merge(s_c[merge_cols + ['q2']], on=merge_cols, suffixes=('_p','_s'))
    n_diff = int((m.q2_p != m.q2_s).sum())
    print(f"  {cell:12s}: {n_diff}/{len(m)} draws diferentes")

print()
from e6_stats import compute_all_stats
FAMILIES = ['lognormal','beta13','uniform','zero_inflated']
Sp = compute_all_stats(prin, FAMILIES)
Ss = compute_all_stats(sens, FAMILIES)
p4p = Sp['All']['P4']
p4s = Ss['All']['P4']
print("P4 principal: Defl=%d Infl=%d NonTied=%d Tied=%d  p=%.6f" % (
    p4p['Defl'],p4p['Infl'],p4p['NonTied'],p4p['Tied'],p4p['P']))
print("P4 sensit   : Defl=%d Infl=%d NonTied=%d Tied=%d  p=%.6f" % (
    p4s['Defl'],p4s['Infl'],p4s['NonTied'],p4s['Tied'],p4s['P']))

principal_sig = p4p['P'] < 0.05
sensit_sig    = p4s['P'] < 0.05
print("Principal p4 < 0.05: %s (p=%.4f)" % ("SIM" if principal_sig else "NAO", p4p['P']))
print("Sensit    p4 < 0.05: %s (p=%.4f)" % ("SIM" if sensit_sig   else "NAO", p4s['P']))

if principal_sig != sensit_sig:
    print("ATENCAO: Veredicto P4 muda entre principal e sensibilidade!")
    print("  Principal: borderline nao conclusivo (p=0.053)")
    print("  Sensit   : significativo a 0.05 (p=0.048)")
    print("  O pre-registered test (inflate<deflate) continua a falhar em ambas.")
    print("  Mas o post-hoc (deflate>inflate) muda de nao-significativo para significativo.")
else:
    print("P4 veredicto estavel (mesmo lado de 0.05 nas duas corridas).")

print()
p3p = Sp['All']['P3']
p3s = Ss['All']['P3']
print("P3 principal: PreregN=%d InfStrict=%d InfDenom=%d p=%.6f" % (
    p3p['PreregN'],p3p['InfStrict'],p3p['InfDenom'],p3p['P']))
print("P3 sensit   : PreregN=%d InfStrict=%d InfDenom=%d p=%.6f" % (
    p3s['PreregN'],p3s['InfStrict'],p3s['InfDenom'],p3s['P']))
print("Diferenca PreregN: +%d" % (p3s['PreregN'] - p3p['PreregN']))
