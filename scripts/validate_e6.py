# -*- coding: utf-8 -*-
"""validate_e6.py — E6-D validation script"""
import pandas as pd, numpy as np, json, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
e6_dir = ROOT / "results" / "e6"

df = pd.read_csv(e6_dir / "e6_raw_results.csv")
seeds = json.load(open(e6_dir / "e6_seeds.json"))

print("=== E6 VALIDATION ===")
print(f"Total rows: {len(df)}  (expected {45*5*2*200})")
print(f"Instances:  {df.inst_id.nunique()} / 45")
print(f"Conditions: {sorted(df.condition.unique())}")
print(f"Protocol hash: {seeds['protocol_hash']}")
print()

# Robustness checks (NaN, domain, completeness)
print("ROBUSTNESS CHECKS:")
nan_q2 = df.q2.isna().sum()
print(f"  NaN in q2:       {nan_q2}  (expected 0)")
non_binary = (~df.q2.isin([0.0, 1.0])).sum()
print(f"  Non-binary q2:   {non_binary}  (expected 0)")
expected_rows = 45 * 5 * 2 * 200
row_ok = len(df) == expected_rows
print(f"  Row count:       {len(df)} == {expected_rows}? {row_ok}")
inst_ok = df.inst_id.nunique() == 45
print(f"  Instance count:  {df.inst_id.nunique()} == 45? {inst_ok}")
if nan_q2 > 0 or non_binary > 0 or not row_ok or not inst_ok:
    print("  ROBUSTNESS FAILED — see above")
    sys.exit(1)
print("  All robustness checks PASS")
print()

# Regression invariant
print("REGRESSION INVARIANT (M=B=C=100% under optimal):")
all_ok = True
for cond in ["M","B","C"]:
    sub = df[(df.condition==cond) & (df.assembly=="optimal")]
    q2 = sub.groupby("inst_id")["q2"].mean()
    fails = q2[q2 < 1.0 - 1e-9]
    status = "OK" if len(fails)==0 else f"FAIL on {len(fails)} instances"
    print(f"  {cond}: {status}")
    if len(fails) > 0: all_ok = False

print()
print("PRIMARY ESTIMAND:")
m_opt = df[(df.condition=="M")&(df.assembly=="optimal")]["q2"].mean()*100
w_opt = df[(df.condition=="W")&(df.assembly=="optimal")]["q2"].mean()*100
v_opt = df[(df.condition=="V")&(df.assembly=="optimal")]["q2"].mean()*100
print(f"  Q2[M,opt] = {m_opt:.1f}%")
print(f"  Q2[W,opt] = {w_opt:.1f}%  (within-group distortion)")
print(f"  Q2[V,opt] = {v_opt:.1f}%  (full vector amplitudes)")
print(f"  Loss within (M-W) = {m_opt-w_opt:.1f} pp")
print(f"  V-W = {v_opt-w_opt:.1f} pp")

print()
print("PRIMARY LOSS CI (paired per-instance, normal SEM):")
m_inst = df[(df.condition=="M")&(df.assembly=="optimal")].groupby("inst_id")["q2"].mean()*100
w_inst = df[(df.condition=="W")&(df.assembly=="optimal")].groupby("inst_id")["q2"].mean()*100
delta  = m_inst - w_inst
n      = len(delta)
se     = delta.std(ddof=1) / np.sqrt(n)
ci_lo  = delta.mean() - 1.96*se
ci_hi  = delta.mean() + 1.96*se
print(f"  mean = {delta.mean():.2f} pp  SE = {se:.2f}  n = {n} instances")
print(f"  95% CI = [{ci_lo:.1f}, {ci_hi:.1f}]")

print()
print("HIERARCHICAL CI (bootstrapped at instance level):")
for cond in ["W","V"]:
    sub = df[(df.condition==cond)&(df.assembly=="optimal")]
    inst_means = sub.groupby("inst_id")["q2"].mean()*100
    n = len(inst_means)
    se = inst_means.std(ddof=1)/np.sqrt(n)
    ci_lo = inst_means.mean() - 1.96*se
    ci_hi = inst_means.mean() + 1.96*se
    print(f"  {cond}: {inst_means.mean():.1f}% [{ci_lo:.1f}, {ci_hi:.1f}] n={n} instances")

print()
print("INDEPENDENT SPOT-CHECK (recomputes Pareto from objectives for one instance):")
try:
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "scripts"))
    from run_e6_generator import (
        generate_sites, generate_criteria,
        find_feasible_trios, compute_objectives,
        pareto_efficient_indices, saw_score, assemble_optimal,
        minmax_norm, W_CRIT_BASE, KAPPA
    )
    # Use first instance: N=50, geometry=uniform, spatial_seed=10
    _N, _geom, _sid = 50, "uniform", 10
    _crit_seed = _sid + 1000
    _inst_id = f"N{_N}_{_geom}_s{_sid}"
    # Re-generate from scratch
    _lat, _lon = generate_sites(_N, _geom, _sid)
    _X_raw = generate_criteria(_N, _crit_seed)
    _X     = minmax_norm(_X_raw)
    _trios = find_feasible_trios(_lat, _lon, seeds["DMIN_KM"])
    _F     = compute_objectives(_X_raw, _trios)
    _par   = pareto_efficient_indices(_F)
    _par_trios = set(map(tuple, _trios[list(_par)].tolist()))
    # Use draw 0 (first draw from the protocol RNG)
    _rng   = np.random.default_rng(seeds["SEED_DRAWS"])
    _draws = _rng.dirichlet(seeds["KAPPA"] * W_CRIT_BASE, size=1)
    _w     = _draws[0]
    _rho   = np.std(_X_raw, axis=0, ddof=1); _rho[_rho < 1e-10] = 1.0
    _s     = saw_score(_X, _w, "M", _rho)
    _sel   = assemble_optimal(_s, _trios)
    _q2_live = 1.0 if tuple(_sel) in _par_trios else 0.0
    _row   = df[(df.inst_id==_inst_id) & (df.condition=="M") &
                (df.assembly=="optimal") & (df.draw==0)]
    _q2_csv = float(_row.q2.values[0]) if len(_row) > 0 else float("nan")
    print(f"  Instance: {_inst_id}, draw 0, condition M, optimal assembly")
    print(f"  Pareto set size (recomputed from objectives): {len(_par_trios)}")
    print(f"  q2 recomputed live: {_q2_live}")
    print(f"  q2 in CSV:          {_q2_csv}")
    _spot_ok = abs(_q2_live - _q2_csv) < 1e-9
    print(f"  Match: {_spot_ok}")
    if not _spot_ok:
        print("  SPOT-CHECK FAILED — live recomputation disagrees with CSV")
        all_ok = False
    else:
        print("  SPOT-CHECK PASSED — independent Pareto recomputation agrees with CSV")
except Exception as e:
    print(f"  SPOT-CHECK SKIPPED (error): {e}")

print()
if all_ok and len(df) == 45*5*2*200 and df.inst_id.nunique() == 45:
    print("VALIDATION PASSED")
    sys.exit(0)
else:
    print("VALIDATION FAILED")
    sys.exit(1)
