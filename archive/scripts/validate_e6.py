# -*- coding: utf-8 -*-
"""validate_e6.py — E6-D validation script

Checks performed:
  1. Robustness: NaN, domain {0,1}, row count, instance count
  2. Completeness by key: cartesian product inst_id × draw × condition × assembly
  3. Regression invariant: M/B/C = 100% under optimal
  4. Primary estimand: loss_within = Q2[M]-Q2[W], CI
  5. Same-implementation reproducibility spot-check (NOT an independent audit):
     re-runs generation, objective, Pareto, and assembly for N=50_uniform_s10
     using the exact pipeline from run_e6_generator.py.
     Covers: condition M (q2=1 expected) and condition W (q2 may be <1).
"""
import pandas as pd, numpy as np, json, sys
from pathlib import Path
from itertools import product

ROOT  = Path(__file__).parent.parent
e6_dir = ROOT / "results" / "e6"

df    = pd.read_csv(e6_dir / "e6_raw_results.csv")
seeds = json.load(open(e6_dir / "e6_seeds.json"))

print("=== E6 VALIDATION ===")
print(f"Total rows: {len(df)}  (expected {45*5*2*200})")
print(f"Instances:  {df.inst_id.nunique()} / 45")
print(f"Conditions: {sorted(df.condition.unique())}")
print(f"Protocol hash: {seeds['protocol_hash']}")
print()

# ── 1. Robustness checks ────────────────────────────────────────────────────
print("ROBUSTNESS CHECKS:")
nan_q2    = df.q2.isna().sum()
non_bin   = (~df.q2.isin([0.0, 1.0])).sum()
row_ok    = len(df) == 45 * 5 * 2 * 200
inst_ok   = df.inst_id.nunique() == 45
print(f"  NaN in q2:       {nan_q2}  (expected 0)")
print(f"  Non-binary q2:   {non_bin}  (expected 0)")
print(f"  Row count:       {len(df)} == {45*5*2*200}? {row_ok}")
print(f"  Instance count:  {df.inst_id.nunique()} == 45? {inst_ok}")
if nan_q2 > 0 or non_bin > 0 or not row_ok or not inst_ok:
    print("  ROBUSTNESS FAILED")
    sys.exit(1)
print("  All robustness checks PASS")
print()

# ── 2. Completeness by key (cartesian product) ──────────────────────────────
print("COMPLETENESS BY KEY (inst_id × draw × condition × assembly):")
obs_keys = set(map(tuple, df[["inst_id","draw","condition","assembly"]].to_numpy()))
exp_keys = set(product(
    df.inst_id.unique(),
    range(seeds["N_DRAWS"]),
    ["B","C","M","V","W"],
    ["greedy","optimal"]
))
missing = exp_keys - obs_keys
extra   = obs_keys - exp_keys
dups    = df.duplicated(["inst_id","draw","condition","assembly"]).sum()
print(f"  Expected keys: {len(exp_keys)}")
print(f"  Observed keys: {len(obs_keys)}")
print(f"  Missing:  {len(missing)}")
print(f"  Extra:    {len(extra)}")
print(f"  Duplicate keys: {dups}")
if missing or extra or dups:
    print("  COMPLETENESS FAILED")
    sys.exit(1)
print("  Completeness PASS")
print()

# ── 3. Regression invariant: M/B/C = 100% ───────────────────────────────────
print("REGRESSION INVARIANT (M=B=C=100% under optimal):")
all_ok = True
for cond in ["M","B","C"]:
    sub   = df[(df.condition==cond) & (df.assembly=="optimal")]
    q2    = sub.groupby("inst_id")["q2"].mean()
    fails = q2[q2 < 1.0 - 1e-9]
    status = "OK" if len(fails)==0 else f"FAIL on {len(fails)} instances"
    print(f"  {cond}: {status}")
    if len(fails) > 0:
        all_ok = False

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
n_inst = len(delta)
se     = delta.std(ddof=1) / np.sqrt(n_inst)
ci_lo  = delta.mean() - 1.96*se
ci_hi  = delta.mean() + 1.96*se
print(f"  mean = {delta.mean():.2f} pp  SE = {se:.2f}  n = {n_inst} instances")
print(f"  95% CI = [{ci_lo:.1f}, {ci_hi:.1f}]")

print()
print("HIERARCHICAL CI (bootstrapped at instance level):")
for cond in ["W","V"]:
    sub = df[(df.condition==cond)&(df.assembly=="optimal")]
    inst_means = sub.groupby("inst_id")["q2"].mean()*100
    n   = len(inst_means)
    se  = inst_means.std(ddof=1)/np.sqrt(n)
    print(f"  {cond}: {inst_means.mean():.1f}% [{inst_means.mean()-1.96*se:.1f}, "
          f"{inst_means.mean()+1.96*se:.1f}] n={n} instances")

# ── 4. Same-implementation reproducibility spot-check ───────────────────────
# NOTE: this reruns the original pipeline functions from run_e6_generator.py.
# It is a same-implementation reproducibility check, not an independent
# Pareto audit: shared errors in compute_objectives or pareto_efficient_indices
# would not be detected. Covers two conditions (M and W) and verifies that
# n_pareto matches the CSV for the test instance.
print()
print("SAME-IMPLEMENTATION REPRODUCIBILITY SPOT-CHECK:")
print("  (reruns pipeline for N50_uniform_s10; not an independent Pareto audit)")

spot_ok = False
try:
    sys.path.insert(0, str(ROOT / "scripts"))
    from run_e6_generator import (
        generate_sites, generate_criteria,
        find_feasible_trios, compute_objectives,
        pareto_efficient_indices, saw_score, assemble_optimal,
        minmax_norm, W_CRIT_BASE, KAPPA
    )
    _N, _geom, _sid = 50, "uniform", 10
    _inst_id = f"N{_N}_{_geom}_s{_sid}"

    # Reproduce exactly as main(): generate_criteria(N, sp_seed)
    # Function internally uses rng(sp_seed + 1000) = rng(1010)
    _lat, _lon = generate_sites(_N, _geom, _sid)
    _X_raw = generate_criteria(_N, _sid)   # NOT _sid+1000
    _X     = minmax_norm(_X_raw)           # main() uses X_norm for objectives
    _trios = find_feasible_trios(_lat, _lon, seeds["DMIN_KM"])
    _F     = compute_objectives(_X, _trios)  # use X_norm, same as main()
    _par   = pareto_efficient_indices(_F)
    _par_trios = set(map(tuple, _trios[list(_par)].tolist()))

    # Verify n_pareto matches CSV
    _csv_npar = int(df[(df.inst_id==_inst_id) & (df.draw==0) &
                       (df.condition=="M") & (df.assembly=="optimal")
                       ]["n_pareto"].values[0])
    _npar_match = len(_par) == _csv_npar
    print(f"  n_pareto recomputed: {len(_par)}  CSV: {_csv_npar}  match: {_npar_match}")
    if not _npar_match:
        raise RuntimeError(f"n_pareto mismatch: {len(_par)} != {_csv_npar}")

    # Draw 0 from protocol RNG
    _rng   = np.random.default_rng(seeds["SEED_DRAWS"])
    _draws = _rng.dirichlet(seeds["KAPPA"] * W_CRIT_BASE, size=1)
    _w     = _draws[0]
    _rho   = _X.max(axis=0) - _X.min(axis=0); _rho[_rho < 1e-10] = 1e-10

    results = []
    for _cond in ["M", "W"]:
        _s   = saw_score(_X, _w, _cond, _rho)
        _sel = assemble_optimal(_s, _trios)
        _q2_live = 1.0 if tuple(_sel) in _par_trios else 0.0
        _row = df[(df.inst_id==_inst_id) & (df.condition==_cond) &
                  (df.assembly=="optimal") & (df.draw==0)]
        _q2_csv = float(_row.q2.values[0]) if len(_row) > 0 else float("nan")
        _ok = abs(_q2_live - _q2_csv) < 1e-9
        results.append(_ok)
        print(f"  cond={_cond}: q2_live={_q2_live}  q2_csv={_q2_csv}  match={_ok}")

    # Also confirm at least one W/V draw has q2=0 in the full dataset
    w_zeros = (df[(df.condition=="W")&(df.assembly=="optimal")].q2 == 0.0).sum()
    print(f"  W condition q2=0 cases in full CSV: {w_zeros} (expected > 0)")
    if w_zeros == 0:
        print("  WARNING: no q2=0 cases found for condition W — unexpected")

    spot_ok = all(results) and _npar_match

except Exception as e:
    print(f"  SPOT-CHECK FAILED (error): {e}")
    spot_ok = False

if not spot_ok:
    all_ok = False

# ── 5. Independent Pareto audit (brute-force, no import from generator) ─────
print()
print("INDEPENDENT PARETO AUDIT (brute-force O(n^2), no import from run_e6_generator):")
ind_audit_ok = False
try:
    import importlib.util
    _audit_path = ROOT / "scripts" / "audit_pareto_independent.py"
    _spec = importlib.util.spec_from_file_location("_indep_audit", _audit_path)
    _mod  = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)

    _test_cases = [
        (50, "uniform",   10),
        (50, "clustered", 10),
        (50, "grid",      10),
    ]
    _all_match = True
    for _N, _geom, _sid in _test_cases:
        _inst_id = f"N{_N}_{_geom}_s{_sid}"
        _lat, _lon, _X = _mod.regenerate_instance(_N, _geom, _sid)
        _trios = _mod.ind_feasible_trios(_lat, _lon, _mod.DMIN_KM)
        _F     = _mod.ind_objectives(_X, _trios, _mod.GROUPS, _mod.W_G)
        _par   = _mod.ind_pareto_brute(_F)
        _row   = df[(df.inst_id==_inst_id)&(df.draw==0)&
                    (df.condition=="M")&(df.assembly=="optimal")]
        _n_csv = int(_row.n_pareto.values[0]) if len(_row)>0 else -1
        _m     = len(_par) == _n_csv
        print(f"  {_inst_id:22s}  n_pareto_brute={len(_par)}  csv={_n_csv}  match={_m}")
        if not _m:
            _all_match = False
    ind_audit_ok = _all_match
    if ind_audit_ok:
        print("  INDEPENDENT AUDIT PASSED")
    else:
        print("  INDEPENDENT AUDIT FAILED")
        all_ok = False
except Exception as _e:
    print(f"  INDEPENDENT AUDIT SKIPPED (error): {_e}")
    ind_audit_ok = False
    all_ok = False

print()
if all_ok:
    print("VALIDATION PASSED")
    sys.exit(0)
else:
    print("VALIDATION FAILED")
    sys.exit(1)
