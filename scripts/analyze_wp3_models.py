# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from scipy import stats

# Results from wp3_summary.csv
data = [
    ("min-max", 0.0000, 82.9),
    ("Peldschus", 0.0023, 86.6),
    ("max", 0.0033, 83.2),
    ("ranks", 0.0911, 77.1),
    ("vector", 0.3113, 55.4),
    ("sum", 0.5669, 73.1),
]
df = pd.DataFrame(data, columns=["norm", "TV", "Q2"])

def run_ols(sub_norms, name):
    sub = df[df.norm.isin(sub_norms)].sort_values("TV")
    x = sub.TV.values
    y = sub.Q2.values
    n = len(x)
    df_resid = n - 2
    res = stats.linregress(x, y)
    y_pred = res.intercept + res.slope * x
    residuals = y - y_pred
    s_err = np.sqrt((residuals**2).sum() / df_resid) if df_resid > 0 else 0.0
    sxx = ((x - x.mean())**2).sum()
    se_slope = s_err / np.sqrt(sxx) if sxx > 0 else 0.0
    print("=" * 60)
    print("Model: %s (n=%d, df=%d)" % (name, n, df_resid))
    print("Levels:   ", list(sub.norm))
    print("TV:       ", [round(v, 4) for v in x])
    print("Q2:       ", [round(v, 1) for v in y])
    print("Slope:     %+.2f pp/unit TV" % res.slope)
    print("SE(slope):  %.2f pp" % se_slope)
    print("R^2:        %.4f" % (res.rvalue**2))
    print("Intercept:  %.2f%%" % res.intercept)
    if df_resid > 0:
        print("p-value:    %.4e" % res.pvalue)

run_ols(["min-max", "ranks", "vector"], "1. Original 3 levels (Table 3)")
run_ols(["min-max", "max", "ranks", "vector"], "2. Four monotonic levels (mm, max, ranks, vector)")
run_ols(["min-max", "Peldschus", "max", "ranks", "vector"], "3. Five levels (with Peldschus, without sum)")
run_ols(["min-max", "max", "ranks", "vector", "sum"], "4. Five levels (with sum)")
run_ols(["min-max", "Peldschus", "max", "ranks", "vector", "sum"], "5. All six levels")
