import pandas as pd
import numpy as np

repo = r"G:\Faculdade\Estudo\Mestrado\2022.1\Trabalhos\Multicriterio\03-latex\paper - Comparison between MCDM Methods for Landfill Site Selection"
df = pd.read_csv(repo + r"\results\e4_results.csv")
print(df.to_string())
print()

k200 = df[df['kappa']==200].copy()

def get(direction, cell, col):
    row = k200[(k200['direction']==direction) & (k200['cell']==cell)]
    return row[col].values[0]

print("=== P_E4_1: R-B and R-B' optimal = 100% on every draw ===")
rb_fwd = get('fwd', 'R-B', 'Q2_optimal')
rb_rev = get('rev', "R-B'", 'Q2_optimal')
print(f"  R-B  opt = {rb_fwd}%  -> {'PASS' if rb_fwd==100.0 else 'FAIL'}")
print(f"  R-B' opt = {rb_rev}%  -> {'PASS' if rb_rev==100.0 else 'FAIL'}")

print()
print("=== P_E4_2: R-V reproduces tab:fourthcell within 3 SE ===")
rv_opt = get('fwd', 'R-V', 'Q2_optimal')
rv_se  = get('fwd', 'R-V', 'SE_optimal')
ref_473 = 20.0
diff = abs(rv_opt - ref_473)
thresh = 3 * max(rv_se, 0.01)
print(f"  R-V  fwd opt = {rv_opt}%  ref = {ref_473}%  |diff| = {diff:.1f}  3SE = {thresh:.2f}")
print(f"  -> {'PASS' if diff <= thresh else 'FAIL'}")

print()
print("=== P_E4_3: R-W loss >= 50% of R-V loss (fwd direction) ===")
rm_opt = get('fwd', 'R-M', 'Q2_optimal')
rw_opt = get('fwd', 'R-W', 'Q2_optimal')
rv_opt_fwd = get('fwd', 'R-V', 'Q2_optimal')
loss_rw = rm_opt - rw_opt
loss_rv = rm_opt - rv_opt_fwd
print(f"  R-M opt = {rm_opt}%  R-W opt = {rw_opt}%  loss_RW = {loss_rw:.1f} pp")
print(f"  R-V opt = {rv_opt_fwd}%  loss_RV = {loss_rv:.1f} pp")
if loss_rv > 0:
    ratio = loss_rw / loss_rv
    print(f"  R-W/R-V loss ratio = {ratio:.2f}  threshold = 0.50")
    print(f"  -> {'PASS' if ratio >= 0.5 else 'FAIL'}")
else:
    print("  R-V loss = 0 (R-V also 100%) -- P_E4_3 not applicable")

print()
print("=== P_E4_4: asymmetry fwd loss > rev loss in R-W ===")
rw_rev = get('rev', "R-W'", 'Q2_optimal')
loss_fwd = 100 - rw_opt
loss_rev = 100 - rw_rev
print(f"  R-W  fwd opt = {rw_opt}%  loss = {loss_fwd:.1f} pp")
print(f"  R-W' rev opt = {rw_rev}%  loss = {loss_rev:.1f} pp")
print(f"  fwd loss > rev loss: {loss_fwd > loss_rev}")

print()
print("=== P_E4_5: R-W fwd loss > E1-W loss (35.8 pp) ===")
loss_rw_pp = 100 - rw_opt
print(f"  R-W fwd opt = {rw_opt}%  loss = {loss_rw_pp:.1f} pp")
print(f"  E1-W loss = 35.8 pp (Q2=64.2%)")
print(f"  -> {'PASS' if loss_rw_pp > 35.8 else 'FAIL'}")
