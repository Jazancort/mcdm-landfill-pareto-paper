# -*- coding: utf-8 -*-
"""
run_e6.py — PRESPEC_E6: Mechanism Generalisation (score-only amplitude manipulation)

Pre-specification: corpus/PRESPEC_E6.md (commit before this run)
Design reference: docs/PLANO_E6_SANTIAGO.md

DESIGN:
  120 instances: 4 marginal families × 30 replicates
  Families: lognormal, beta13, uniform, zero_inflated (π=0.90 zeros + LogN)
  Geometry: Fogo spatial structure (data/fogo_trios.npy, N=389, T=1,944,653)
  k = 3 (portfolio size, same as main study)

  7 cells per instance:
    M          : A_j = 1          (TV_B=0, TV_W=0)  — P1 assertion
    B          : Āg per group     (TV_B=0.249, TV_W=0) — P1 assertion
    W_inf_L    : inflate j*, TV_W=0.10
    W_inf_F    : inflate j*, TV_W=0.199             — P2 (Fogo level), P3, P4
    W_inf_H    : inflate j*, TV_W=0.30
    V_inf_F    : inflate + between, TV_B=0.249, TV_W≈0.199 — P3
    W_def_F    : deflate j*, TV_W=0.199             — P4

  Objectives: PER-DRAW weights w_d (same as E1, mc_unified).
  This guarantees P1 analytically (cell M/B = positive scalarisation of objectives).

  Parameters: N_draws=200, κ=200, seed_base=42, k=3

ASSERTIONS (before any analysis):
  P1: cells M and B must achieve Q2_optimal = 1.0 on ALL draws in ALL instances.

OUTPUT:
  results/e6/e6_instances_prespec.csv   — per-instance metadata + TV_W/TV_B actuals
  results/e6/e6_raw_prespec.csv         — per-(instance, cell, draw) Q2
  results/e6/e6_summary_prespec.csv     — aggregated Q2 per (family, cell)
  results/e6/e6_spearman_prespec.csv    — Spearman ρ per (family, replicate) for P2
  results/e6/e6_report_prespec.txt      — human-readable results + P1–P4 status

Idempotent: if e6_raw_prespec.csv is complete, regenerate summaries only.

Run on Athena:
  uv run python scripts/run_e6.py

Verify timing first with:
  uv run python scripts/run_e6.py --dry-run
"""

import os, sys, json, time, hashlib, argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import dirichlet as sp_dirichlet, spearmanr

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
OUT  = ROOT / "results" / "e6"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT / "scripts"))
from fogo_constants import W as W_AHP, OBJ_GROUPS, TV_W_VEC, TV_B_VEC
from e6_generate_amplitudes import build_amplitude_cells, tvw_sec64, tvb_sec64

# ── PROTOCOL CONSTANTS (frozen) ──────────────────────────────────────────────
N_SITES    = 389          # Fogo admissible sites (fixed spatial structure)
M_CRIT     = 11           # criteria
K          = 3            # portfolio size
N_DRAWS    = 200          # Dirichlet draws per instance
KAPPA      = 200          # Dirichlet concentration
SEED_BASE  = 42           # base seed; instance-specific seed = SEED_BASE + inst_idx
N_REP      = 30           # replicates per family
EPS        = 1e-9         # dominance tolerance

# Criterion orientation: G1 and G2 are cost (minimize), G3 is benefit (maximize)
# x_adj_j = 1 - n_j^mm for cost, n_j^mm for benefit
G1 = OBJ_GROUPS[0]   # [0,1,2]: perm, slope, roads (cost)
G2 = OBJ_GROUPS[1]   # [3,4,5,6,7]: rivers, aspect, coast, prot, wells (cost)
G3 = OBJ_GROUPS[2]   # [8,9,10]: urban, aero, cult (benefit)
COST_IDX   = G1 + G2  # benefit-adjusted: x_adj = 1-x
BENEFIT_IDX = G3       # benefit-adjusted: x_adj = x

W_G = np.array([W_AHP[g].sum() for g in OBJ_GROUPS])

# TV_W targets for the 4 non-trivial cells
TW_L = 0.10
TW_F = TV_W_VEC   # 0.199 (Fogo reference)
TW_H = 0.30
TB   = TV_B_VEC   # 0.249 (Fogo reference)

# Cell order for reporting
CELL_NAMES = ['M', 'B', 'W_inf_L', 'W_inf_F', 'W_inf_H', 'V_inf_F', 'W_def_F']

# Marginal distribution families
FAMILIES = ['lognormal', 'beta13', 'uniform', 'zero_inflated']


# ── LOAD SPATIAL STRUCTURE ────────────────────────────────────────────────────
print("Loading Fogo trios...", flush=True)
trios_path = DATA / "fogo_trios.npy"
assert trios_path.exists(), f"Missing: {trios_path}"
trios = np.load(trios_path)                           # (T, 3) int32
T0, T1, T2 = trios[:, 0], trios[:, 1], trios[:, 2]
T = len(trios)
print(f"  Trios: {T:,}  Sites: {N_SITES}", flush=True)
assert T == 1944653, f"Expected 1,944,653 trios, got {T}"


# ── COLUMN GENERATOR ─────────────────────────────────────────────────────────
def generate_columns(family, seed, N=N_SITES, M=M_CRIT):
    """
    Generate raw criterion matrix X_raw (N × M) from the specified family.
    All columns are drawn i.i.d. from the family distribution.

    Parameters
    ----------
    family : str  one of 'lognormal', 'beta13', 'uniform', 'zero_inflated'
    seed   : int  per-instance seed
    """
    rng = np.random.default_rng(seed)
    if family == 'lognormal':
        X = rng.lognormal(mean=0.0, sigma=1.0, size=(N, M))
    elif family == 'beta13':
        X = rng.beta(a=1.0, b=3.0, size=(N, M))
    elif family == 'uniform':
        X = rng.uniform(low=0.0, high=1.0, size=(N, M))
    elif family == 'zero_inflated':
        # π=0.90 zeros + LogN(μ=0, σ=1) for the non-zero fraction
        X = rng.lognormal(mean=0.0, sigma=1.0, size=(N, M))
        zero_mask = rng.uniform(size=(N, M)) < 0.90
        X[zero_mask] = 0.0
    else:
        raise ValueError(f"Unknown family: {family}")
    return X.astype(np.float64)


# ── MIN-MAX NORMALISATION ─────────────────────────────────────────────────────
def minmax_norm(X_raw):
    """Normalise each column to [0, 1]. Constant columns → 0.5."""
    lo = X_raw.min(axis=0)
    hi = X_raw.max(axis=0)
    rng = hi - lo
    rng_safe = np.where(rng < 1e-12, 1.0, rng)
    X_mm = (X_raw - lo) / rng_safe
    X_mm[:, rng < 1e-12] = 0.5  # constant column → centre
    return X_mm


# ── BENEFIT-ADJUSTED MATRIX ───────────────────────────────────────────────────
def benefit_adjust(X_mm):
    """
    x_adj_j = 1 - x_j^mm  for cost criteria (G1, G2)
    x_adj_j = x_j^mm      for benefit criteria (G3)
    Returns x_adj (N × M) where HIGHER = BETTER for all criteria.
    """
    X_adj = X_mm.copy()
    for j in COST_IDX:
        X_adj[:, j] = 1.0 - X_mm[:, j]
    return X_adj


# ── PER-DRAW OBJECTIVES ───────────────────────────────────────────────────────
def compute_f1f2f3(X_adj, w_d):
    """
    Per-site objectives using draw weights w_d.

    Convention (matches pareto_utils.py is_dominated):
      F1_site: G1 contribution, MINIMIZE (dominator has F1 ≤ query)
      F2_site: G2 contribution, MINIMIZE
      F3_site: G3 contribution, MAXIMIZE (dominator has F3 ≥ query)

    For is_dominated to work correctly, F1 and F2 must be oriented so that
    LOWER = BETTER (minimize objective). With x_adj (higher=better for all),
    a group cost objective should have LOWER f = BETTER.

    We therefore define:
      F1_site[a] = -sum_{j in G1} w_d[j] * X_adj[a, j]  (negative → LOWER = better G1)
      F2_site[a] = -sum_{j in G2} w_d[j] * X_adj[a, j]  (same)
      F3_site[a] = +sum_{j in G3} w_d[j] * X_adj[a, j]  (positive → higher = better G3)

    This is identical to run_e1_v3.py and mc_unified.py conventions.
    """
    f1 = -(X_adj[:, G1] * w_d[G1]).sum(axis=1)
    f2 = -(X_adj[:, G2] * w_d[G2]).sum(axis=1)
    f3 =  (X_adj[:, G3] * w_d[G3]).sum(axis=1)
    return f1, f2, f3


# ── IS_DOMINATED (optimised, no array copies) ────────────────────────────────
def is_dominated_fast(F1, F2, F3, idx):
    """
    Check if trio[idx] is dominated in (F1 min, F2 min, F3 max) space.
    Vectorised NumPy, no array copies. O(T) time and memory.
    """
    f1t, f2t, f3t = F1[idx], F2[idx], F3[idx]
    dom = (
        (F1 <= f1t + EPS) & (F2 <= f2t + EPS) & (F3 >= f3t - EPS) &
        ((F1 < f1t - EPS) | (F2 < f2t - EPS) | (F3 > f3t + EPS))
    )
    dom[idx] = False          # exclude the trio itself
    return bool(dom.any())


# ── SCORE COMPUTATION ─────────────────────────────────────────────────────────
def compute_score(X_adj, w_d, A_j):
    """
    SAW score: score[a] = sum_j w_d[j] * A_j[j] * X_adj[a, j]
    Returns (N,) float64.
    """
    return (X_adj * (w_d * A_j)).sum(axis=1)


def argmax_trio(score):
    """Return the feasible trio that maximises the sum of site scores."""
    trio_scores = score[T0] + score[T1] + score[T2]
    idx = int(trio_scores.argmax())
    return idx


# ── MAIN EXPERIMENT LOOP ──────────────────────────────────────────────────────
def run_experiment(dry_run=False):
    raw_path = OUT / "e6_raw_prespec.csv"

    # Build instance list (120 instances)
    instances = []
    for fam in FAMILIES:
        for rep in range(N_REP):
            inst_idx = len(instances)
            seed = SEED_BASE + inst_idx
            instances.append({
                'inst_id': f"{fam}_r{rep:02d}",
                'family': fam,
                'replicate': rep,
                'seed': seed,
            })

    N_INST = len(instances)
    assert N_INST == 120, f"Expected 120 instances, got {N_INST}"
    print(f"\n[INSTANCES] {N_INST} = {len(FAMILIES)} families × {N_REP} replicates")

    if dry_run:
        print("\n[DRY RUN] Timing 1 instance × 200 draws × 7 cells...")
        _dry_run_timing(instances[0])
        return

    # Idempotency check
    expected_rows = N_INST * len(CELL_NAMES) * N_DRAWS
    if raw_path.exists():
        df_exist = pd.read_csv(raw_path)
        if len(df_exist) == expected_rows:
            print(f"[SKIP] {raw_path} complete ({len(df_exist)} rows). Regenerating summaries.")
            generate_summaries(df_exist, instances)
            return
        print(f"[WARN] {raw_path} exists but incomplete ({len(df_exist)}/{expected_rows}). Rerunning.")

    # Shared Dirichlet draws: one weight matrix per draw, shared across instances
    # (instance-specific seeds come from column generation, not weight draws)
    rng_w = np.random.default_rng(SEED_BASE)
    alpha = W_AHP * KAPPA            # Dirichlet concentration centered at W_AHP
    W_DRAWS = sp_dirichlet.rvs(alpha, size=N_DRAWS, random_state=rng_w)
    print(f"[DRAWS] {N_DRAWS} Dirichlet draws, κ={KAPPA}, seed={SEED_BASE}")

    records = []
    inst_meta = []

    t0_total = time.time()

    for inst_idx, inst in enumerate(instances):
        fam   = inst['family']
        rep   = inst['replicate']
        inst_id = inst['inst_id']
        seed  = inst['seed']
        t_inst = time.time()

        # ── Generate synthetic columns ────────────────────────────────────────
        X_raw  = generate_columns(fam, seed)
        X_mm   = minmax_norm(X_raw)
        X_adj  = benefit_adjust(X_mm)

        # ── Build amplitude cells for this instance ───────────────────────────
        cells, tv_report, amp_warnings = build_amplitude_cells(
            w_ref=W_AHP, groups=OBJ_GROUPS, W_G=W_G,
            tw_L=TW_L, tw_F=TW_F, tw_H=TW_H, tb=TB,
        )

        inst_row = {**inst, 'n_trios': T}
        for cell_name in CELL_NAMES:
            inst_row[f'tv_w_{cell_name}'] = tv_report[cell_name]['tv_w']
            inst_row[f'tv_b_{cell_name}'] = tv_report[cell_name]['tv_b']
        if amp_warnings:
            inst_row['warnings'] = ' | '.join(amp_warnings)
        inst_meta.append(inst_row)

        # ── Per-draw loop ─────────────────────────────────────────────────────
        for d in range(N_DRAWS):
            w_d = W_DRAWS[d]

            # Per-draw trio objectives (fast NumPy indexing)
            f1s, f2s, f3s = compute_f1f2f3(X_adj, w_d)
            F1 = f1s[T0] + f1s[T1] + f1s[T2]
            F2 = f2s[T0] + f2s[T1] + f2s[T2]
            F3 = f3s[T0] + f3s[T1] + f3s[T2]

            for cell_name in CELL_NAMES:
                A_j     = cells[cell_name]
                score   = compute_score(X_adj, w_d, A_j)
                best_idx = argmax_trio(score)
                dominated = is_dominated_fast(F1, F2, F3, best_idx)
                q2 = 0 if dominated else 1

                records.append({
                    'inst_id': inst_id,
                    'family': fam,
                    'replicate': rep,
                    'draw': d,
                    'cell': cell_name,
                    'q2': q2,
                })

        elapsed = time.time() - t_inst
        n_done  = inst_idx + 1
        eta     = (time.time() - t0_total) / n_done * (N_INST - n_done)
        print(f"  [{n_done:3d}/{N_INST}] {inst_id}  {elapsed:4.1f}s  ETA {eta/60:.0f}min",
              flush=True)

    # ── Save raw results ──────────────────────────────────────────────────────
    df_raw = pd.DataFrame(records)
    df_raw.to_csv(raw_path, index=False)
    print(f"\n[SAVED] {raw_path}  ({len(df_raw)} rows)")

    df_meta = pd.DataFrame(inst_meta)
    df_meta.to_csv(OUT / "e6_instances_prespec.csv", index=False)
    print(f"[SAVED] {OUT/'e6_instances_prespec.csv'}")

    # ── P1 assertion ──────────────────────────────────────────────────────────
    print("\n[P1 ASSERTION] Cells M and B must have Q2_optimal = 1.0 on ALL draws.")
    p1_ok = True
    for cell_name in ('M', 'B'):
        sub = df_raw[df_raw['cell'] == cell_name]
        failures = sub[sub['q2'] < 1]
        if len(failures) > 0:
            print(f"  FAIL: {cell_name}: {len(failures)} draws with Q2=0  ← P1 VIOLATED")
            p1_ok = False
        else:
            print(f"  OK:   {cell_name}: 100% on all {len(sub)} draw-instance combinations")
    if not p1_ok:
        print("\nABORTING: P1 assertion violated. Check amplitude construction pipeline.")
        sys.exit(1)
    print("[P1 PASSED] All M and B draws are Pareto-efficient.")

    generate_summaries(df_raw, instances)


def generate_summaries(df_raw, instances):
    """Generate aggregated summaries and Spearman report."""
    print("\n[SUMMARIES]")

    # ── Summary by (family, cell) ─────────────────────────────────────────────
    agg = (df_raw.groupby(['family', 'cell'])['q2']
           .agg(['mean', 'std', 'count']).reset_index())
    agg['q2_pct'] = agg['mean'] * 100
    agg['se_pct'] = agg['std'] / np.sqrt(agg['count']) * 100
    agg.to_csv(OUT / "e6_summary_prespec.csv", index=False)
    print(f"  Saved: {OUT/'e6_summary_prespec.csv'}")

    # ── Spearman ρ per (family, replicate) for P2 ─────────────────────────────
    # Test: ρ(TV_W_level, Q2_opt) across W_inf cells (L, F, H + M as level 0)
    tw_map = {'M': 0.0, 'W_inf_L': 0.10, 'W_inf_F': TW_F, 'W_inf_H': TW_H}
    p2_cells = ['M', 'W_inf_L', 'W_inf_F', 'W_inf_H']

    spearman_rows = []
    for fam in FAMILIES:
        for rep in range(N_REP):
            inst_id = f"{fam}_r{rep:02d}"
            sub = df_raw[(df_raw['inst_id'] == inst_id) &
                         (df_raw['cell'].isin(p2_cells))]
            if len(sub) == 0:
                continue
            inst_agg = sub.groupby('cell')['q2'].mean().reset_index()
            tv_levels = [tw_map[r] for r in inst_agg['cell']]
            q2_vals   = inst_agg['q2'].values
            if len(tv_levels) < 3:
                continue
            rho, pval = spearmanr(tv_levels, q2_vals)
            spearman_rows.append({
                'family': fam, 'replicate': rep, 'inst_id': inst_id,
                'rho_s': rho, 'pval': pval,
                'confirming_P2': int(rho < 0),
            })

    df_sp = pd.DataFrame(spearman_rows)
    df_sp.to_csv(OUT / "e6_spearman_prespec.csv", index=False)
    print(f"  Saved: {OUT/'e6_spearman_prespec.csv'}")

    # ── Report ────────────────────────────────────────────────────────────────
    lines = []
    lines.append("=" * 65)
    lines.append("E6 PRESPEC RESULTS REPORT")
    lines.append(f"PRESPEC: corpus/PRESPEC_E6.md")
    lines.append("=" * 65)
    lines.append("")
    lines.append("POOLED Q2 BY FAMILY AND CELL (optimal assembly):")
    lines.append("")

    for fam in FAMILIES:
        lines.append(f"  Family: {fam}")
        sub = agg[agg['family'] == fam][['cell', 'q2_pct', 'se_pct', 'count']]
        sub = sub.set_index('cell').reindex(CELL_NAMES)
        for cell_name in CELL_NAMES:
            row = sub.loc[cell_name] if cell_name in sub.index else None
            if row is not None and not row.isna().all():
                lines.append(
                    f"    {cell_name:12s}: {row['q2_pct']:5.1f}% ±{row['se_pct']:.1f} pp"
                )
        lines.append("")

    lines.append("")
    lines.append("P1 ASSERTION (M and B = 100%):")
    for cell_name in ('M', 'B'):
        sub = agg[agg['cell'] == cell_name]
        mean_q2 = sub['q2_pct'].mean() if len(sub) > 0 else float('nan')
        status = "OK" if abs(mean_q2 - 100) < 0.01 else "FAIL"
        lines.append(f"  {cell_name}: {mean_q2:.2f}%  [{status}]")

    lines.append("")
    lines.append("P2 SPEARMAN (ρ < 0 criterion for each family):")
    for fam in FAMILIES:
        sub = df_sp[df_sp['family'] == fam]
        n_confirming = sub['confirming_P2'].sum()
        n_total = len(sub)
        frac = n_confirming / n_total if n_total > 0 else float('nan')
        status = "OK" if frac >= 0.80 else "FAIL"
        rho_mean = sub['rho_s'].mean() if len(sub) > 0 else float('nan')
        lines.append(
            f"  {fam:16s}: {n_confirming}/{n_total} ({frac:.0%}) ρ<0  "
            f"mean_ρ={rho_mean:+.3f}  [{status}]"
        )

    lines.append("")
    lines.append("P3 CHECK (Q2_opt(V_inf_F) ≤ Q2_opt(W_inf_F) in ≥70% instances):")
    for fam in FAMILIES:
        sub_W = df_raw[(df_raw['family'] == fam) & (df_raw['cell'] == 'W_inf_F')]
        sub_V = df_raw[(df_raw['family'] == fam) & (df_raw['cell'] == 'V_inf_F')]
        if len(sub_W) == 0 or len(sub_V) == 0:
            continue
        w_mean = sub_W.groupby('replicate')['q2'].mean()
        v_mean = sub_V.groupby('replicate')['q2'].mean()
        common = w_mean.index.intersection(v_mean.index)
        n_conf = int((v_mean[common] <= w_mean[common] + EPS).sum())
        n_tot  = len(common)
        frac   = n_conf / n_tot if n_tot > 0 else float('nan')
        status = "OK" if frac >= 0.70 else "FAIL"
        lines.append(
            f"  {fam:16s}: {n_conf}/{n_tot} ({frac:.0%}) V≤W  [{status}]"
        )

    lines.append("")
    lines.append("P4 CHECK (Q2_opt(W_inf_F) < Q2_opt(W_def_F) in ≥70% instances):")
    for fam in FAMILIES:
        sub_inf = df_raw[(df_raw['family'] == fam) & (df_raw['cell'] == 'W_inf_F')]
        sub_def = df_raw[(df_raw['family'] == fam) & (df_raw['cell'] == 'W_def_F')]
        if len(sub_inf) == 0 or len(sub_def) == 0:
            continue
        inf_mean = sub_inf.groupby('replicate')['q2'].mean()
        def_mean = sub_def.groupby('replicate')['q2'].mean()
        common = inf_mean.index.intersection(def_mean.index)
        n_conf = int((inf_mean[common] < def_mean[common] - EPS).sum())
        n_tot  = len(common)
        frac   = n_conf / n_tot if n_tot > 0 else float('nan')
        status = "OK" if frac >= 0.70 else "FAIL"
        lines.append(
            f"  {fam:16s}: {n_conf}/{n_tot} ({frac:.0%}) inf<def  [{status}]"
        )

    report_text = "\n".join(lines)
    with open(OUT / "e6_report_prespec.txt", "w") as f:
        f.write(report_text)
    print(f"  Saved: {OUT/'e6_report_prespec.txt'}")
    print()
    print(report_text)


def _dry_run_timing(inst):
    """Run one instance for timing estimate, then extrapolate."""
    fam  = inst['family']
    seed = inst['seed']
    print(f"  Instance: {inst['inst_id']}")

    rng_w  = np.random.default_rng(SEED_BASE)
    alpha  = W_AHP * KAPPA
    W_DRAWS = sp_dirichlet.rvs(alpha, size=N_DRAWS, random_state=rng_w)

    X_raw = generate_columns(fam, seed)
    X_mm  = minmax_norm(X_raw)
    X_adj = benefit_adjust(X_mm)
    cells, tv_report, _ = build_amplitude_cells(
        W_AHP, OBJ_GROUPS, W_G, tw_L=TW_L, tw_F=TW_F, tw_H=TW_H, tb=TB
    )

    t0 = time.time()
    for d in range(N_DRAWS):
        w_d = W_DRAWS[d]
        f1s, f2s, f3s = compute_f1f2f3(X_adj, w_d)
        F1 = f1s[T0] + f1s[T1] + f1s[T2]
        F2 = f2s[T0] + f2s[T1] + f2s[T2]
        F3 = f3s[T0] + f3s[T1] + f3s[T2]
        for cell_name in CELL_NAMES:
            A_j = cells[cell_name]
            score = compute_score(X_adj, w_d, A_j)
            best_idx = argmax_trio(score)
            _ = is_dominated_fast(F1, F2, F3, best_idx)

    t1 = time.time()
    inst_time = t1 - t0
    total_est = inst_time * 120
    print(f"\n  1 instance × {N_DRAWS} draws × {len(CELL_NAMES)} cells: {inst_time:.1f}s")
    print(f"  Extrapolation to 120 instances: {total_est:.0f}s = {total_est/60:.0f} min")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true',
                        help='Time 1 instance and extrapolate; do not run full experiment')
    args = parser.parse_args()
    run_experiment(dry_run=args.dry_run)
