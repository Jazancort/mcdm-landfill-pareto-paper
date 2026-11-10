import pandas as pd, hashlib
from pathlib import Path
p = Path("scratch/mcdm-landfill-pareto-paper/results/santiago/sens_zdti_distrib.csv")
df = pd.read_csv(p)
sha = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
print(f"rows={len(df)}, SHA={sha}")
print(df.groupby(["kappa","cell"])["q2"].mean().unstack("cell").round(1).to_string())
