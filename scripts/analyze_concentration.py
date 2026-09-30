# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
from scipy import stats

w_ahp = np.array([0.177,0.107,0.107,0.059,0.059,0.059,0.069,0.069,0.107,0.107,0.080])
w_ahp /= w_ahp.sum()
sparse_order = np.argsort(-w_ahp)

def hhi(n_sp):
    if n_sp == 0: return 0.0
    ws = w_ahp[sparse_order[:n_sp]]
    ws_norm = ws / ws.sum()
    return float((ws_norm**2).sum())

print("=== INDICES DE CONCENTRACAO POR N_SPARSE ===")
header = f"{'n_sp':>5} {'w_sparse':>10} {'w_max':>8} {'HHI':>8} {'w_max/w_sp':>12}"
print(header)
for ns in range(5):
    if ns == 0:
        w_sp = 1.0; w_max = 0.0; h = 0.0; ratio = 0.0
    else:
        ws = w_ahp[sparse_order[:ns]]
        w_sp = float(ws.sum())
        w_max = float(ws.max())
        h = hhi(ns)
        ratio = w_max / w_sp
    row = f"{ns:>5} {w_sp:>10.4f} {w_max:>8.4f} {h:>8.4f} {ratio:>12.4f}"
    print(row)
print()

df = pd.read_csv('results/wp4_synthetic.csv')
df['contrast'] = df['Q2_mm_grd'] - df['Q2_vec_grd']
cells = df.groupby(['n_sparse','p0']).agg(
    tv=('tv_vec','mean'), contrast=('contrast','mean')
).reset_index()

def w_sparse(n):
    if n == 0: return 1.0
    return float(w_ahp[sparse_order[:n]].sum())
def w_max_fn(n):
    if n == 0: return 0.0
    return float(w_ahp[sparse_order[:n]].max())

cells['w_sp']      = cells['n_sparse'].apply(w_sparse)
cells['conc_rev']  = cells['tv'] / cells['w_sp']
cells['hhi_val']   = cells['n_sparse'].apply(hhi)
cells['conc_hhi']  = cells['tv'] * cells['hhi_val']
cells['w_max']     = cells['n_sparse'].apply(w_max_fn)
cells['linf_l1']   = np.where(cells['n_sparse']>0, cells['w_max']/cells['w_sp'], 0.0)
cells['conc_linf'] = cells['tv'] * cells['linf_l1']

print("=== CORRELACOES (20 celulas) ===")
for label, col in [
    ('TV sozinho', 'tv'),
    ('TV / w_sparse (revisor)', 'conc_rev'),
    ('TV * HHI', 'conc_hhi'),
    ('TV * (w_max/w_sparse)', 'conc_linf'),
]:
    r_p, p_p = stats.pearsonr(cells[col], cells['contrast'])
    r_s, p_s = stats.spearmanr(cells[col], cells['contrast'])
    print(f"  {label:32s}: Pearson={r_p:.3f}(p={p_p:.2e})  Spearman={r_s:.3f}(p={p_s:.2e})")
print()

print("=== CORRELACOES (16 celulas, n_sparse>=1) ===")
c16 = cells[cells['n_sparse']>0].copy()
for label, col in [
    ('TV sozinho', 'tv'),
    ('TV / w_sparse (revisor)', 'conc_rev'),
    ('TV * HHI', 'conc_hhi'),
    ('TV * (w_max/w_sparse)', 'conc_linf'),
]:
    r_p, p_p = stats.pearsonr(c16[col], c16['contrast'])
    r_s, p_s = stats.spearmanr(c16[col], c16['contrast'])
    print(f"  {label:32s}: Pearson={r_p:.3f}(p={p_p:.2e})  Spearman={r_s:.3f}(p={p_s:.2e})")
print()

# Regressao TV + concentracao (TV/w_sparse) nas 16 celulas
from numpy.linalg import lstsq
X = np.column_stack([np.ones(16), c16['tv'].values, c16['conc_rev'].values])
y = c16['contrast'].values
b, _, _, _ = lstsq(X, y, rcond=None)
yhat = X @ b
ss_res = ((y-yhat)**2).sum(); ss_tot = ((y-y.mean())**2).sum()
r2 = 1 - ss_res/ss_tot
r2adj = 1 - (1-r2)*15/13
print(f"Regressao TV + conc_rev (16 celulas): R2={r2:.3f}  R2adj={r2adj:.3f}  coefs={np.round(b,4)}")

# Regressao conc_rev sozinho nas 16 celulas
X1 = np.column_stack([np.ones(16), c16['conc_rev'].values])
b1, _, _, _ = lstsq(X1, y, rcond=None)
yhat1 = X1 @ b1
ss_res1 = ((y-yhat1)**2).sum()
r2_1 = 1 - ss_res1/ss_tot
r2adj_1 = 1 - (1-r2_1)*15/14
print(f"Regressao conc_rev sozinho (16 cel):   R2={r2_1:.3f}  R2adj={r2adj_1:.3f}  coefs={np.round(b1,4)}")
