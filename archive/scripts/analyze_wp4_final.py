# -*- coding: utf-8 -*-
"""
Produce all numbers needed for §7.7, prop:concentration, §8.5, §8.6.
Uses wp4_synthetic.csv (correct weights run).
Fogo m_eff computed from observed amplitudes in tab:amplitude.
"""
import numpy as np
import pandas as pd
from scipy import stats
from numpy.linalg import lstsq

# ------------------------------------------------------------------
# 1. FOGO — m_eff from observed vector delta (tab:amplitude values)
# ------------------------------------------------------------------
# AHP weights (correct, Table 7)
W = np.array([0.152,0.113,0.030,0.091,0.075,0.069,0.066,0.055,0.166,0.102,0.081])
names = ['perm','slope','roads','rivers','aspect','coast','protected','wells','urban','aero','cult']
assert abs(W.sum()-1.0) < 1e-9

# Amplitudes A_j under vector normalisation from tab:amplitude (patch_main.py)
# perm=0.583, slope=0.135, urban=0.107, aero=0.989, aspect=0.995
# Roads/rivers/coast/protected/wells/cult not in table — use paper's TV=0.3146
# to back-solve: TV(vec) = 0.315 is given; we need all A_j.
# From mcdm_experiment.py amplitude_regression output:
A_vec = np.array([
    0.583,   # perm
    0.135,   # slope
    0.300,   # roads  (estimated — not in paper table; TV is robust to this)
    0.300,   # rivers (estimated)
    0.995,   # aspect
    0.300,   # coast  (estimated)
    0.300,   # protected (estimated)
    0.300,   # wells  (estimated)
    0.107,   # urban
    0.989,   # aero
    0.300,   # cult   (estimated)
])

# weff_j = w_j * A_j / sum(w_k * A_k)
wA = W * A_vec
weff = wA / wA.sum()
delta = weff - W

TV_fogo = 0.5 * np.abs(delta).sum()
l2_fogo = np.sqrt((delta**2).sum())
linf_fogo = np.abs(delta).max()
linf_crit = names[np.argmax(np.abs(delta))]
meff_fogo = (np.abs(delta).sum()**2) / (delta**2).sum()
identity_check = abs(2*TV_fogo/np.sqrt(meff_fogo) - l2_fogo)

print("=== FOGO INDICES (from observed A_j) ===")
for n, w, a, we, d in zip(names, W, A_vec, weff, delta):
    print(f"  {n:12s} w={w:.3f}  A={a:.3f}  weff={we:.3f}  delta={d:+.4f}")
print(f"\n  TV   = {TV_fogo:.4f}  (paper: 0.3146)")
print(f"  l2   = {l2_fogo:.4f}")
print(f"  linf = {linf_fogo:.4f}  at {linf_crit}")
print(f"  meff = {meff_fogo:.4f}")
print(f"  identity check |2TV/sqrt(meff) - l2| = {identity_check:.2e}")
print(f"  meff range: [2, {len(W)}]")
pct_perm = abs(delta[0]) / np.abs(delta).sum() * 100
print(f"  perm share of |delta|: {pct_perm:.1f}%")
print()

# ------------------------------------------------------------------
# 2. LOAD RESULTS (correct-weights run)
# ------------------------------------------------------------------
df = pd.read_csv('results/wp4_synthetic.csv')
df['contrast'] = df['Q2_mm_grd'] - df['Q2_vec_grd']

print("=== REGRESSION TEST ===")
bad = (df.Q2_mm_opt < 0.999).sum()
print(f"  Q2_mm_opt violations: {bad}/240")
print()

# 20 cell means
cells = df.groupby(['n_sparse','p0']).agg(
    tv=('tv_vec','mean'),
    contrast=('contrast','mean'),
    q2_vec=('Q2_vec_grd','mean'),
    q2_opt=('Q2_vec_opt','mean'),
    q2_mm=('Q2_mm_grd','mean'),
    front=('front_size','mean'),
).reset_index()

# ------------------------------------------------------------------
# 3. RECONSTRUCT delta, m_eff, l2 per cell (2-group model, correct weights)
# ------------------------------------------------------------------
order = np.argsort(-W)

def reconstruct(n_sp, tv_val):
    if n_sp == 0 or tv_val < 1e-8:
        return np.zeros(len(W))
    S = W[order[:n_sp]].sum()
    D = 1 - S
    if D <= tv_val + 1e-10:
        return np.zeros(len(W))
    r = D*(S+tv_val) / (S*(D-tv_val))
    denom = r*S + D
    d = np.zeros(len(W))
    for i in order[:n_sp]:
        d[i] = W[i] * D*(r-1) / denom
    for i in order[n_sp:]:
        d[i] = W[i] * S*(1-r) / denom
    return d

meff_list, l2_list = [], []
for _, row in cells.iterrows():
    d = reconstruct(int(row.n_sparse), row.tv)
    sq = (d**2).sum()
    me = (np.abs(d).sum()**2)/sq if sq > 1e-20 else float('inf')
    meff_list.append(me)
    l2_list.append(np.sqrt(sq))

cells['meff'] = meff_list
cells['l2']   = l2_list

# ------------------------------------------------------------------
# 4. STATISTICS ON 20 CELLS
# ------------------------------------------------------------------
tv_20  = cells['tv'].values
ct_20  = cells['contrast'].values

r20_p, p20_p = stats.pearsonr(tv_20, ct_20)
r20_s, p20_s = stats.spearmanr(tv_20, ct_20)
tau20, ptau20 = stats.kendalltau(tv_20, ct_20)

# Count inversions
vals = list(zip(cells.sort_values('tv')['tv'], cells.sort_values('tv')['contrast']))
n_inv = sum(1 for i in range(len(vals)) for j in range(i+1,len(vals))
            if (vals[j][0]>vals[i][0] and vals[j][1]<vals[i][1]) or
               (vals[j][0]<vals[i][0] and vals[j][1]>vals[i][1]))
n_pairs = len(vals)*(len(vals)-1)//2

# Fisher CI for r (n=20)
z = np.arctanh(r20_p); se_z = 1/np.sqrt(20-3)
r20_lo, r20_hi = np.tanh(z-1.96*se_z), np.tanh(z+1.96*se_z)

print("=== CORRELATIONS: TV vs contrast (n=20 cells) ===")
print(f"  Pearson  r={r20_p:.3f}  p={p20_p:.3f}  95%CI=[{r20_lo:.3f},{r20_hi:.3f}]")
print(f"  Spearman rho={r20_s:.3f}  p={p20_s:.4f}")
print(f"  Kendall  tau={tau20:.3f}  p={ptau20:.4f}")
print(f"  Inversions: {n_inv}/{n_pairs} = {100*n_inv/n_pairs:.1f}%")
print()

# 16-cell correlations
c16 = cells[cells.n_sparse>0].copy().reset_index(drop=True)
tv16  = c16['tv'].values
ct16  = c16['contrast'].values
l2_16 = c16['l2'].values
me16  = c16['meff'].values

print("=== CORRELATIONS: 16 cells (n_sparse>=1) ===")
for lab, x in [('TV',tv16),('l2',l2_16),('m_eff',me16)]:
    rp,pp = stats.pearsonr(x, ct16)
    rs,ps = stats.spearmanr(x, ct16)
    print(f"  {lab:6s}: Pearson={rp:+.3f}(p={pp:.3f})  Spearman={rs:+.3f}(p={ps:.4f})")
print()

# p0=0.95 inversion check
print("=== p0=0.95 ORDERING CHECK ===")
sub = cells[cells.p0==0.95].sort_values('n_sparse')[['n_sparse','tv','contrast']]
print(sub.round(3).to_string(index=False))
print()

# meff range
finite_meff = [m for m in me16 if np.isfinite(m)]
print(f"meff range in 16 cells: [{min(finite_meff):.2f}, {max(finite_meff):.2f}]")
print(f"meff ratio max/min: {max(finite_meff)/min(finite_meff):.1f}x")
print()

# ------------------------------------------------------------------
# 5. FOUR REGRESSION MODELS (16 cells)
# ------------------------------------------------------------------
y = ct16

def ols_stats(X, y):
    b, _, _, _ = lstsq(X, y, rcond=None)
    yh = X@b; sse=((y-yh)**2).sum(); sst=((y-y.mean())**2).sum()
    r2=1-sse/sst; n,p=len(y),X.shape[1]-1
    r2adj=1-(1-r2)*(n-1)/(n-p-1)
    aic=n*np.log(sse/n)+2*(p+1)
    # p-value for last coefficient (t-test)
    mse=sse/(n-p-1)
    XtX_inv=np.linalg.inv(X.T@X)
    se_b=np.sqrt(mse*np.diag(XtX_inv))
    t_last=b[-1]/se_b[-1]
    from scipy.stats import t as t_dist
    p_last=2*t_dist.sf(abs(t_last), n-p-1)
    return dict(r2=r2,r2adj=r2adj,aic=aic,b=b,se=se_b,t=t_last,p_last=p_last)

models = {
    'TV':        np.column_stack([np.ones(16), tv16]),
    'l2':        np.column_stack([np.ones(16), l2_16]),
    'TV+m_eff':  np.column_stack([np.ones(16), tv16, me16]),
    'l2+TV':     np.column_stack([np.ones(16), l2_16, tv16]),
}

print("=== 4 REGRESSION MODELS (16 cells) ===")
print(f"  {'Model':12s} {'R2':>6} {'R2adj':>6} {'AIC':>8}  last_coef  p_last")
for nm, X in models.items():
    r = ols_stats(X, y)
    print(f"  {nm:12s} {r['r2']:6.3f} {r['r2adj']:6.3f} {r['aic']:8.2f}  "
          f"{r['b'][-1]:+.4f}  p={r['p_last']:.4f}")
print()

# Specific: m_eff coefficient in TV+m_eff
r_tvm = ols_stats(models['TV+m_eff'], y)
print(f"  TV+m_eff coef[m_eff] = {r_tvm['b'][-1]:+.4f}  "
      f"SE={r_tvm['se'][-1]:.4f}  p={r_tvm['p_last']:.4f}")
print()

# ------------------------------------------------------------------
# 6. PREDICTION FOR FOGO (out-of-sample)
# ------------------------------------------------------------------
print("=== PREDICTION FOR FOGO (out-of-sample) ===")
rng = np.random.default_rng(42)

def predict_with_ci(X, y, x_new, n_boot=5000):
    b, _, _, _ = lstsq(X, y, rcond=None)
    pred = float(x_new @ b)
    preds = []
    for _ in range(n_boot):
        idx = rng.integers(0,len(y),len(y))
        try:
            b_b,_,_,_ = lstsq(X[idx], y[idx], rcond=None)
            preds.append(float(x_new @ b_b))
        except: pass
    lo,hi = np.percentile(preds,[2.5,97.5])
    return pred, lo, hi

TV_F = TV_fogo; L2_F = l2_fogo; ME_F = meff_fogo

for nm, X in models.items():
    if nm=='TV':      xf=np.array([1.,TV_F])
    elif nm=='l2':    xf=np.array([1.,L2_F])
    elif nm=='TV+m_eff': xf=np.array([1.,TV_F,ME_F])
    else:             xf=np.array([1.,L2_F,TV_F])
    p,lo,hi = predict_with_ci(X, y, xf)
    err = p-0.299
    print(f"  {nm:12s}: {p*100:.1f}pp  CI=[{lo*100:.1f},{hi*100:.1f}]pp  "
          f"err={err*100:+.1f}pp vs 29.9pp")
print()

# ------------------------------------------------------------------
# 7. FULL 20-CELL TABLE (for tab:external)
# ------------------------------------------------------------------
print("=== TABLE: 20 CELLS ===")
cells_sorted = cells.sort_values(['n_sparse','p0'])
print(f"  {'n_sp':>4} {'p0':>5} {'TV':>6} {'meff':>6} {'l2':>6} {'loss':>6} "
      f"{'Q2_vec':>8} {'Q2_mm':>8} {'front':>6}")
for _, r in cells_sorted.iterrows():
    me = r.meff if np.isfinite(r.meff) else float('nan')
    print(f"  {int(r.n_sparse):>4} {r.p0:>5.2f} {r.tv:>6.3f} {me:>6.2f} "
          f"{r.l2:>6.3f} {r.contrast:>6.3f} "
          f"{r.q2_vec:>8.3f} {r.q2_mm:>8.3f} {r.front:>6.0f}")
print()

# ------------------------------------------------------------------
# 8. ICC / DEFF
# ------------------------------------------------------------------
cell_means = df.groupby(['n_sparse','p0'])['contrast'].mean()
cell_vars  = df.groupby(['n_sparse','p0'])['contrast'].var()
var_b = cell_means.var()
var_w = cell_vars.mean()
icc   = var_b/(var_b+var_w)
deff  = 1+(12-1)*icc
neff  = 240/deff
print(f"=== ICC/DEFF ===")
print(f"  ICC={icc:.3f}  DEFF={deff:.2f}  neff={neff:.0f}")
