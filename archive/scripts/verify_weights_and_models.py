# -*- coding: utf-8 -*-
"""
Verifica pesos do wp4_synthetic.py vs AHP_WEIGHTS do artigo.
Recalcula: SPARSE_ORDER correcto, grupos G1/G2/G3, m_eff de Fogo,
e os 4 modelos de regressão sobre as 16 células corrigidas.
"""
import numpy as np
import pandas as pd
from scipy import stats
from numpy.linalg import lstsq

# ------------------------------------------------------------------
# PESOS CORRECTOS (mcdm_experiment.py, Table 7 IEEE Access 2026)
# ------------------------------------------------------------------
# Ordem: perm, slope, roads, rivers, aspect, coast, protected, wells,
#        urban, aero, cult
W_CORRECT = np.array([
    0.152, 0.113, 0.030, 0.091,   # G1: perm, slope, roads, rivers
    0.075, 0.069, 0.066, 0.055,   # G2: aspect, coast, protected, wells
    0.166, 0.102, 0.081,           # G3: urban, aero, cult
], dtype=float)
assert abs(W_CORRECT.sum() - 1.0) < 1e-9, "pesos não somam 1"

# PESOS ERRADOS (wp4_synthetic.py)
W_WRONG = np.array([
    0.177, 0.107, 0.107, 0.059,
    0.059, 0.059, 0.069, 0.069,
    0.107, 0.107, 0.080,
], dtype=float)
W_WRONG /= W_WRONG.sum()

print("=== COMPARAÇÃO DE PESOS ===")
names = ['perm','slope','roads','rivers','aspect','coast','protected','wells','urban','aero','cult']
print(f"{'crit':>10} {'correcto':>10} {'errado':>10} {'diff':>8}")
for n, wc, we in zip(names, W_CORRECT, W_WRONG):
    print(f"  {n:>10} {wc:>10.4f} {we:>10.4f} {wc-we:>+8.4f}")
print()

# Impacto: SPARSE_ORDER correcto vs errado
order_correct = np.argsort(-W_CORRECT)
order_wrong   = np.argsort(-W_WRONG)
print("=== SPARSE_ORDER ===")
print(f"  Correcto:  {[names[i] for i in order_correct]}")
print(f"  Errado:    {[names[i] for i in order_wrong]}")
print(f"  1º esparso correcto: {names[order_correct[0]]} w={W_CORRECT[order_correct[0]]:.4f}")
print(f"  1º esparso errado:   {names[order_wrong[0]]} w={W_WRONG[order_wrong[0]]:.4f}")
print()

# ------------------------------------------------------------------
# m_eff de FOGO com pesos correctos
# ------------------------------------------------------------------
# delta_j = weff_j - w_j de Fogo (vector normalisation)
# weff_j = w_j * A_j / sum(w_k * A_k)
# Valores de A_j da tabela do artigo (vector normalisation, tab:amplitude)
# extraídos do patch_main.py: perm=0.583, slope=0.135, urban=0.107, aero=0.989...
# Mas usamos os valores do paper directamente:
# perm: rho=0.583, weff_norm=2.93*w = weff/w
FOGO_RATIOS = {
    'perm':      2.93,   # weff/w = 2.93 → weff = 2.93 * 0.152
    'slope':     0.68,
    'roads':     None,   # não reportado no paper
    'rivers':    None,
    'aspect':    None,
    'coast':     None,
    'protected': None,
    'wells':     None,
    'urban':     0.54,   # weff/w = 0.54 → weff = 0.54 * 0.166
    'aero':      1.11,
    'cult':      None,
}
# Usar os delta_j do artigo (patch_main.py):
# perm: weff = 0.286 (=2.93*0.152 → 0.445, but paper says +0.286)
# O paper reporta os delta_j = weff - w directamente na §8.6 / tab:amplitude
# Usar os valores de weff do script amplitude_regression.py
# Vec norm A_j values from tab:amplitude in paper:
# perm A=0.583, urban A=0.107, aero A=0.989 (from patch_main.py lines 45-53)
# Reconstrução: weff_j ∝ w_j * A_j^1
A_vec = {  # amplitudes sob vector normalisation — do artigo tab:amplitude
    'perm':      0.583,
    'slope':     0.135,
    'roads':     None,   # não na tabela, assumir ~0.3 (irrelevante para Fogo)
    'rivers':    None,
    'aspect':    0.995,
    'coast':     None,
    'protected': None,
    'wells':     None,
    'urban':     0.107,
    'aero':      0.989,
    'cult':      None,
}

# Usar amplitude_regression.py ou calcular delta_j via §8.6
# O paper diz TV=0.315 e delta(perm)=+0.286 (2.93x → weff=0.445, delta=+0.293?)
# Inconsistência possível — calcular directamente do TV e dos ratios disponíveis

# Fogo: TV_vec=0.315 confirmado no artigo
# Usar o modelo de dois grupos para Fogo:
# G_sparse = {perm} com w_sparse = 0.152 (1 critério esparso mais pesado)
# S = 0.152, D = 0.848, TV = 0.315
# r = D*(S+TV) / [S*(D-TV)]
S = W_CORRECT[0]   # perm
D = 1 - S
TV_FOGO = 0.315
r_fogo = D*(S + TV_FOGO) / (S*(D - TV_FOGO))
print("=== MODELO DE DOIS GRUPOS PARA FOGO (perm como único esparso) ===")
print(f"  S={S:.4f}  D={D:.4f}  TV={TV_FOGO:.4f}")
print(f"  r_fogo = {r_fogo:.4f}")
print()

# Delta_j para Fogo via dois grupos
denom = r_fogo*S + D
delta_sparse = W_CORRECT[0] * D*(r_fogo-1) / denom    # perm
delta_dense  = W_CORRECT[1:] * S*(1-r_fogo) / denom   # todos os outros

delta_fogo = np.zeros(11)
delta_fogo[0] = delta_sparse
delta_fogo[1:] = delta_dense

TV_reconstructed = 0.5 * np.abs(delta_fogo).sum()
print(f"  TV reconstruído = {TV_reconstructed:.6f}  (alvo: 0.315000)")
print(f"  Erro: {abs(TV_reconstructed - TV_FOGO):.2e}")
print()

# m_eff de Fogo
sum_abs_delta = np.abs(delta_fogo).sum()   # = 2*TV
sum_sq_delta  = (delta_fogo**2).sum()
m_eff_fogo = (sum_abs_delta**2) / sum_sq_delta
l2_fogo    = np.sqrt(sum_sq_delta)
print(f"=== INDICES DE FOGO (com pesos correctos) ===")
print(f"  TV  = {TV_FOGO:.4f}  (= 0.5 * sum|delta|)")
print(f"  l2  = {l2_fogo:.4f}  (= sqrt(sum delta^2))")
print(f"  m_eff = {m_eff_fogo:.4f}")
print(f"  Verificação: 2*TV/sqrt(m_eff) = {2*TV_FOGO/np.sqrt(m_eff_fogo):.6f}  == l2 = {l2_fogo:.6f}")
print(f"  Erro identidade: {abs(2*TV_FOGO/np.sqrt(m_eff_fogo) - l2_fogo):.2e}")
print()

# ------------------------------------------------------------------
# Reconstrução delta por célula (20 células) com pesos CORRECTOS
# ------------------------------------------------------------------
df = pd.read_csv('results/wp4_synthetic.csv')
df['contrast'] = df['Q2_mm_grd'] - df['Q2_vec_grd']
cells = df.groupby(['n_sparse','p0']).agg(
    tv=('tv_vec','mean'), contrast=('contrast','mean')
).reset_index()

# SPARSE_ORDER com pesos correctos
order_c = np.argsort(-W_CORRECT)

def reconstruct_delta(n_sp, tv_val):
    """Reconstruir delta_j via modelo dois grupos."""
    if n_sp == 0 or tv_val < 1e-8:
        return np.zeros(11)
    S_c = W_CORRECT[order_c[:n_sp]].sum()
    D_c = 1 - S_c
    if D_c <= tv_val:   # evitar divisão por zero
        return np.zeros(11)
    r_c = D_c*(S_c + tv_val) / (S_c*(D_c - tv_val))
    denom_c = r_c*S_c + D_c
    delta = np.zeros(11)
    for idx in order_c[:n_sp]:
        delta[idx] = W_CORRECT[idx] * D_c*(r_c-1) / denom_c
    for idx in order_c[n_sp:]:
        delta[idx] = W_CORRECT[idx] * S_c*(1-r_c) / denom_c
    return delta

# Verificar que TV é preservado
print("=== VERIFICAÇÃO IDENTIDADE ℓ²=2TV/√m_eff (20 células) ===")
l2_vals = []
meff_vals = []
tv_check_errors = []
identity_errors = []

for _, row in cells.iterrows():
    d = reconstruct_delta(int(row['n_sparse']), row['tv'])
    tv_rec = 0.5*np.abs(d).sum()
    tv_check_errors.append(abs(tv_rec - row['tv']))
    sum_sq = (d**2).sum()
    meff = (np.abs(d).sum()**2) / sum_sq if sum_sq > 0 else float('inf')
    l2  = np.sqrt(sum_sq)
    l2_pred = 2*row['tv']/np.sqrt(meff) if meff < float('inf') else 0.0
    identity_errors.append(abs(l2 - l2_pred))
    l2_vals.append(l2)
    meff_vals.append(meff)

cells['l2']   = l2_vals
cells['meff'] = meff_vals
print(f"  Max erro TV reconstruído: {max(tv_check_errors):.2e}")
print(f"  Max erro identidade ℓ²=2TV/√m_eff: {max(identity_errors):.2e}")
print()

# ------------------------------------------------------------------
# 4 modelos de regressão (16 células, n_sparse>=1)
# ------------------------------------------------------------------
c16 = cells[cells['n_sparse']>0].copy().reset_index(drop=True)
y = c16['contrast'].values
tv_c = c16['tv'].values
l2_c = c16['l2'].values
me_c = c16['meff'].values

def ols(X, y):
    b, _, _, _ = lstsq(X, y, rcond=None)
    yhat = X@b
    ss_res = ((y-yhat)**2).sum()
    ss_tot = ((y-y.mean())**2).sum()
    r2 = 1-ss_res/ss_tot
    n, p = len(y), X.shape[1]-1
    r2adj = 1-(1-r2)*(n-1)/(n-p-1)
    # AIC (OLS, sigma²=ss_res/n)
    sigma2 = ss_res/n
    aic = n*np.log(sigma2) + 2*(p+1)
    return dict(r2=r2, r2adj=r2adj, aic=aic, b=b)

models = {
    'TV only':      np.column_stack([np.ones(16), tv_c]),
    'l2 only':      np.column_stack([np.ones(16), l2_c]),
    'TV + m_eff':   np.column_stack([np.ones(16), tv_c, me_c]),
    'l2 + TV':      np.column_stack([np.ones(16), l2_c, tv_c]),
}

print("=== 4 MODELOS DE REGRESSÃO (16 células, n_sparse>=1) ===")
print(f"  {'Modelo':20s} {'R²':>6} {'R²adj':>6} {'AIC':>8}  coefs")
for name, X in models.items():
    res = ols(X, y)
    print(f"  {name:20s} {res['r2']:6.3f} {res['r2adj']:6.3f} {res['aic']:8.2f}  {np.round(res['b'],4)}")
print()

# Correlações
print("=== CORRELAÇÕES (16 células) ===")
for label, col in [('TV', tv_c), ('l2', l2_c), ('m_eff', me_c)]:
    r_p, p_p = stats.pearsonr(col, y)
    r_s, p_s = stats.spearmanr(col, y)
    print(f"  {label:8s}: Pearson={r_p:+.3f}(p={p_p:.2e})  Spearman={r_s:+.3f}(p={p_s:.2e})")
print()

# Predicção para Fogo
print("=== PREDIÇÃO PARA FOGO ===")
for name, X_all in models.items():
    res = ols(X_all, y)
    # construir vetor para Fogo
    if name == 'TV only':
        x_fogo = np.array([1.0, TV_FOGO])
    elif name == 'l2 only':
        x_fogo = np.array([1.0, l2_fogo])
    elif name == 'TV + m_eff':
        x_fogo = np.array([1.0, TV_FOGO, m_eff_fogo])
    else:  # l2 + TV
        x_fogo = np.array([1.0, l2_fogo, TV_FOGO])
    pred = float(x_fogo @ res['b'])
    # IC aproximado via bootstrap
    rng = np.random.default_rng(42)
    preds_boot = []
    for _ in range(5000):
        idx = rng.integers(0, 16, 16)
        try:
            b_b, _, _, _ = lstsq(X_all[idx], y[idx], rcond=None)
            preds_boot.append(float(x_fogo @ b_b))
        except: pass
    lo, hi = np.percentile(preds_boot, [2.5, 97.5])
    err = pred - 0.299   # observado em Fogo = 29.9 pp
    print(f"  {name:20s}: pred={pred:.3f} ({pred*100:.1f}pp)  "
          f"CI=[{lo*100:.1f},{hi*100:.1f}]pp  err vs 29.9pp={err*100:+.1f}pp")
print()
print(f"  Observado Fogo: 29.9 pp (Q2_mm_grd - Q2_vec_grd)")
print(f"  Fogo m_eff = {m_eff_fogo:.4f}  l2 = {l2_fogo:.4f}  TV = {TV_FOGO:.4f}")
