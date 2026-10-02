"""scripts/aggregation_strata.py
F1: SAW − TOPSIS contrast by stratum (norm × assembly cell),
with paired bootstrap CI, from mc_2cube_fixed_raw.csv.

mc_2cube_fixed_raw.csv columns: alpha, draw, agg, norm, mont, nd_Q2Ap
  agg  : saw | topsis
  norm : minmax | vector | ranks
  mont : greedy | optimal
  alpha: 50 | 200

Outputs:
  results/e1/aggregation_strata.csv   — contrast by cell with 95% CI
  results/e1/aggregation_strata.log   — summary for the paper
"""
import numpy as np
import pandas as pd
from pathlib import Path

ROOT   = Path(__file__).parent.parent
RAW    = ROOT / "results" / "fourthcell" / "mc_2cube_fixed_raw.csv"
OUT    = ROOT / "results" / "e1"

KAPPA = 200
B     = 2000
SEED  = 42
rng   = np.random.default_rng(SEED)

df = pd.read_csv(RAW)
df = df[df.alpha == KAPPA].copy()

# Each draw × norm × mont → SAW value and TOPSIS value
# Pivot so each row is (draw, norm, mont) with saw and topsis Q2
pivot = df.pivot_table(index=["draw","norm","mont"], columns="agg", values="nd_Q2Ap").reset_index()
pivot.columns.name = None
pivot = pivot.rename(columns={"saw":"saw","topsis":"topsis"})

# Contrast per cell: SAW − TOPSIS (positive = SAW better)
pivot["contrast"] = pivot["saw"] - pivot["topsis"]

cells = []
for (norm, mont), g in pivot.groupby(["norm","mont"]):
    c = g["contrast"].values
    diff = c.mean() * 100  # pp
    # Paired bootstrap CI
    boots = [rng.choice(c, size=len(c), replace=True).mean()*100 for _ in range(B)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    sig = "SIG" if (lo > 0 or hi < 0) else "n.s."
    cells.append({"norm":norm, "mont":mont, "diff_pp":round(diff,1),
                  "ci_lo":round(lo,1), "ci_hi":round(hi,1), "sig":sig,
                  "n_draws":len(c)})

results = pd.DataFrame(cells).sort_values(["mont","norm"])

# Overall (all cells pooled)
all_c = pivot["contrast"].values
overall = all_c.mean()*100
boots_all = [rng.choice(all_c,len(all_c),replace=True).mean()*100 for _ in range(B)]
lo_all, hi_all = np.percentile(boots_all, [2.5, 97.5])
sig_all = "SIG" if (lo_all > 0 or hi_all < 0) else "n.s."

# Without minmax/optimal cell (cell that drives the effect)
no_mmopt = pivot[~((pivot.norm=="minmax")&(pivot.mont=="optimal"))]["contrast"].values
diff_no = no_mmopt.mean()*100
boots_no = [rng.choice(no_mmopt,len(no_mmopt),replace=True).mean()*100 for _ in range(B)]
lo_no, hi_no = np.percentile(boots_no, [2.5, 97.5])
sig_no = "SIG" if (lo_no > 0 or hi_no < 0) else "n.s."

OUT.mkdir(exist_ok=True)
results.to_csv(OUT/"aggregation_strata.csv", index=False)

log = []
log.append("=== F1: SAW − TOPSIS contrast by cell (kappa=200, paired bootstrap B=2000) ===\n")
log.append(results.to_string(index=False))
log.append(f"\n\nOverall pooled: {overall:+.1f} pp  CI=[{lo_all:+.1f},{hi_all:+.1f}]  {sig_all}")
log.append(f"Without minmax/optimal: {diff_no:+.1f} pp  CI=[{lo_no:+.1f},{hi_no:+.1f}]  {sig_no}")
log.append(f"\nFor the paper: AggContrast={overall:.1f}  AggLo={lo_all:.1f}  AggHi={hi_all:.1f}")
txt = "\n".join(log)
print(txt)
(OUT/"aggregation_strata.log").write_text(txt, encoding="utf-8")
print(f"\nSaved to {OUT}/aggregation_strata.csv and .log")
