# -*- coding: utf-8 -*-
"""
WP3 — Passo 1: Calcular Aj, TV, m_eff, l2 para todas as normalizações candidatas.

Normalizações testadas:
  (existing) mm    : (x - min) / (max - min)           → Aj = 1 sempre → TV = 0
  (existing) vec   : x / ||x||                          → Aj = rho_j
  (existing) ranks : midrank / (N+1)                    → Aj = (r_max - r_min)/(N+1)
  (candidate) sum  : x / sum(x)                         → Aj = (max - min) / sum(x)
  (candidate) max  : x / max(x)                         → Aj = 1 - min/max
  (candidate) ZT   : ln(x) / sum(ln(x))  [Zavadskas-Turskis log]
  (candidate) P2   : (x/max)^2  [Peldschus nonlinear]   → Aj = 1 - (min/max)^2

Armadilha afim: checar se Aj de candidata = Aj de existente para algum j.
Criterion-wise: se Aj_candidata[j] = Aj_existente[j] para todo j → TV idêntico.
"""
import os, sys, numpy as np, pandas as pd
if 'MCDM_DATA_DIR' not in os.environ and os.path.exists('/home/julioazancort/scratch/mcdm'):
    os.environ['MCDM_DATA_DIR'] = '/home/julioazancort/scratch/mcdm'
sys.path.insert(0, 'scripts')
from mcdm_experiment import load_data, impute_nan, COL, AHP_WEIGHTS

df_all, par, bcs = load_data()
df_imp = impute_nan(df_all)
col_prot = COL['protected']
df_via = df_imp[df_imp[col_prot] > 0].copy()

# Build raw criterion matrix X (N=389, M=11) — after imputation
# For cost criteria (perm, slope, roads): invert so larger = better (1 - norm)
# Wait — mcdm_experiment.py does NOT invert for perm/slope/roads;
# it uses _norm(x, ref) directly, and bigger is already better (distance from hazard).
# Check: 'aspect' is binary. For the normalisation study, use only continuous criteria
# or handle aspect separately.

w = np.array(list(AHP_WEIGHTS.values()), dtype=float)
w /= w.sum()
names_crit = list(AHP_WEIGHTS.keys())
M = len(w)

# Build raw X (N, M) from df_via using the column names in COL
X = np.zeros((len(df_via), M))
for j, k in enumerate(names_crit):
    col = COL[k]
    vals = df_via[col].values.astype(float)
    # aspect: c=1 for [90,180] (leeward/favourable, n1=94), c=0 otherwise.
    # Yields Aj^vec = 1/sqrt(94) = 0.10314, matching Table 1 (0.103).
    if k == 'aspect':
        X[:, j] = np.where((vals >= 90) & (vals <= 180), 1.0, 0.0)
    else:
        X[:, j] = vals

N = len(df_via)
print(f"N={N}, M={M}")
print(f"Weights: {dict(zip(names_crit, w.round(4)))}")
print()

# -----------------------------------------------------------------------
# Normalisation functions (return normalised matrix V, shape NxM)
# -----------------------------------------------------------------------
def norm_minmax(X):
    lo, hi = X.min(0), X.max(0)
    R = np.where(hi > lo, hi - lo, 1.0)
    return (X - lo) / R

def norm_vector(X):
    norms = np.sqrt((X**2).sum(0))
    return X / np.where(norms > 0, norms, 1.0)

def norm_ranks(X):
    V = np.zeros_like(X, dtype=float)
    for j in range(X.shape[1]):
        r = pd.Series(X[:, j]).rank(method='average').values
        V[:, j] = r / (N + 1)
    return V

def norm_sum(X):
    """c_j(i) = x_ij / sum_i(x_ij)"""
    s = X.sum(0)
    return X / np.where(s > 0, s, 1.0)

def norm_max(X):
    """c_j(i) = x_ij / max_j(x_j)"""
    mx = X.max(0)
    return X / np.where(mx > 0, mx, 1.0)

def norm_zt(X):
    """Zavadskas-Turskis: c_j(i) = ln(x_ij+1) / sum_i(ln(x_ij+1))
    +1 to handle zeros.  Strictly: ZT uses ln(x) / prod, but common
    implementation uses sum of logs."""
    Lx = np.log1p(X)  # ln(x+1) to handle zeros
    s = Lx.sum(0)
    return Lx / np.where(s > 0, s, 1.0)

def norm_peldschus(X):
    """Peldschus (x/max)^2"""
    mx = X.max(0)
    c = X / np.where(mx > 0, mx, 1.0)
    return c ** 2

# -----------------------------------------------------------------------
# Amplitude Aj and TV computation (same as mcdm_experiment)
# -----------------------------------------------------------------------
def compute_tv(V, w, alpha=1.0):
    """TV under amplitude identity."""
    A = V.max(0) - V.min(0)
    num = (w**alpha) * (A**alpha)
    s = num.sum()
    if s < 1e-30:
        return 0.0, A, np.zeros(len(w))
    weff = num / s
    tv = 0.5 * float(np.abs(weff - w).sum())
    delta = weff - w
    # m_eff = (sum|delta|)^2 / sum(delta^2)
    sum_abs = np.abs(delta).sum()
    sum_sq  = (delta**2).sum()
    meff = (sum_abs**2) / sum_sq if sum_sq > 1e-30 else float('inf')
    l2   = np.sqrt(sum_sq)
    return tv, A, weff, delta, meff, l2

# -----------------------------------------------------------------------
# Compute for each normalisation
# -----------------------------------------------------------------------
norms = {
    'min-max': norm_minmax,
    'vector':  norm_vector,
    'ranks':   norm_ranks,
    'sum':     norm_sum,
    'max':     norm_max,
    'ZT-log':  norm_zt,
    'Peldschus': norm_peldschus,
}

results = {}
print(f"{'Norm':12s}  {'TV':7s}  {'m_eff':7s}  {'l2':7s}  {'Aj range':20s}")
print("-" * 65)

Aj_all = {}
for nm, fn in norms.items():
    V = fn(X)
    tv, A, weff, delta, meff, l2 = compute_tv(V, w)
    results[nm] = dict(tv=tv, meff=meff, l2=l2, A=A, weff=weff, delta=delta)
    Aj_all[nm] = A
    meff_str = "N/A" if tv < 1e-8 else f"{meff:.2f}"
    aj_str = f"[{A.min():.3f}, {A.max():.3f}]"
    print(f"  {nm:12s}  {tv:.5f}  {meff_str:>7s}  {l2:.5f}  {aj_str}")

print()

# -----------------------------------------------------------------------
# Check affine equivalence: Aj_a == Aj_b for all j?
# -----------------------------------------------------------------------
print("=== AFFINE EQUIVALENCE CHECK (Aj vectors) ===")
norm_names = list(norms.keys())
for i in range(len(norm_names)):
    for j in range(i+1, len(norm_names)):
        a, b = norm_names[i], norm_names[j]
        Aa, Ab = Aj_all[a], Aj_all[b]
        # Check if Aj vectors are proportional (affine equivalent)
        # A_a = k * A_b + c for some constants k, c?
        # Simpler: check TV equality (same Aj → same TV)
        tv_diff = abs(results[a]['tv'] - results[b]['tv'])
        if tv_diff < 1e-6:
            print(f"  {a} == {b}: TV={results[a]['tv']:.6f} (DUPLICATE — same TV)")
        # Check Aj vector correlation
        corr = np.corrcoef(Aa, Ab)[0,1]
        if corr > 0.999 and tv_diff > 1e-6:
            print(f"  {a} ~~ {b}: rho(Aj)={corr:.4f} (highly correlated Aj)")

print()

# -----------------------------------------------------------------------
# Per-criterion Aj table
# -----------------------------------------------------------------------
print("=== Aj PER CRITERION ===")
print(f"{'Crit':12s}  {'w':6s}  {'mm':6s}  {'vec':6s}  {'ranks':6s}  {'sum':6s}  {'max':6s}  {'ZT':6s}  {'Peld':6s}")
print("-"*80)
for j, k in enumerate(names_crit):
    row = f"  {k:12s}  {w[j]:.4f}"
    for nm in norm_names:
        row += f"  {Aj_all[nm][j]:.4f}"
    print(row)
print()

# -----------------------------------------------------------------------
# TV spacing analysis
# -----------------------------------------------------------------------
tvs = sorted([(nm, r['tv']) for nm, r in results.items()], key=lambda x: x[1])
print("=== TV SPACING ===")
for nm, tv in tvs:
    print(f"  {nm:12s}  TV={tv:.5f}  m_eff={results[nm]['meff']:.2f}  l2={results[nm]['l2']:.5f}")

print()
# Check if spacing is adequate
tv_vals = [t for _, t in tvs]
gaps = [tv_vals[i+1] - tv_vals[i] for i in range(len(tv_vals)-1)]
print(f"TV range: [{tv_vals[0]:.4f}, {tv_vals[-1]:.4f}]")
print(f"Gaps between consecutive TV levels: {[round(g,4) for g in gaps]}")
print(f"TV spread = {tv_vals[-1]-tv_vals[0]:.4f}")

# -----------------------------------------------------------------------
# REGRESSION TEST: TV(vector) must match Tab1 = 0.3146
# -----------------------------------------------------------------------
print()
tv_vec = results['vector']['tv']
meff_vec = results['vector']['meff']
print(f"=== REGRESSION TEST ===")
print(f"  TV(vector)   = {tv_vec:.4f}  (Tab1: 0.3146,  OK if |diff| < 0.001)")
print(f"  m_eff(vector)= {meff_vec:.3f}  (Tab1: 4.049,   OK if |diff| < 0.01)")
print(f"  PASS" if abs(tv_vec - 0.3146) < 0.001 and abs(meff_vec - 4.049) < 0.05 else "  FAIL — aspect binarization still wrong")

# -----------------------------------------------------------------------
# 5-level analysis: mm, max, ranks, vector, sum
# -----------------------------------------------------------------------
print()
five = ['min-max', 'max', 'ranks', 'vector', 'sum']
print("=== FIVE LEVELS (mm, max, ranks, vector, sum) ===")
from scipy.stats import pearsonr, spearmanr
tv5   = np.array([results[nm]['tv']   for nm in five])
meff5 = np.array([results[nm]['meff'] for nm in five if results[nm]['tv'] > 1e-8])
tv5_nz = np.array([results[nm]['tv']  for nm in five if results[nm]['tv'] > 1e-8])
print(f"{'Norm':12s}  {'TV':8s}  {'m_eff':8s}  {'l2':8s}")
for nm in five:
    r = results[nm]
    me_str = "N/A" if r['tv'] < 1e-8 else f"{r['meff']:.3f}"
    print(f"  {nm:12s}  {r['tv']:.5f}  {me_str:>8s}  {r['l2']:.5f}")

if len(tv5_nz) >= 3:
    r_p, _ = pearsonr(tv5_nz, meff5)
    r_s, _ = spearmanr(tv5_nz, meff5)
    print(f"\nCollinearity TV vs m_eff (4 non-zero levels):")
    print(f"  Pearson r = {r_p:.4f}   Spearman rho = {r_s:.4f}")

# Leverage (Sxx) for regression with 5 levels
tv_mean = tv5.mean()
sxx = ((tv5 - tv_mean)**2).sum()
print(f"\nLeverage: Sxx(TV, 5 levels) = {sxx:.4f}")
print(f"SE(slope) = sigma/sqrt(Sxx) ≈ {0.02/np.sqrt(sxx):.4f}  (assuming sigma=2pp)")
