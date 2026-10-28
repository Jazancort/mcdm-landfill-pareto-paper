import sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import numpy as np
from wp4_synthetic import generate_criteria, make_coords, evaluate_instance, W_AHP, M, N_SITES, D_MIN_KM

rng = np.random.default_rng(42)
X = generate_criteria(N_SITES, M, p0=0.1, shape='normal', rng=rng)
coords = make_coords(N_SITES, rng)
t0 = time.time()
res = evaluate_instance(X, W_AHP, coords, D_MIN_KM, n_draws=20, kappa=50, seed=99)
dt = time.time() - t0
if res:
    print(f"OK in {dt:.1f}s -- N_SITES={N_SITES}")
    print(f"  minmax: Q2={res['minmax']['Q2']:.3f}  Q3={res['minmax']['Q3']:.4f}")
    print(f"  vector: Q2={res['vector']['Q2']:.3f}  Q3={res['vector']['Q3']:.4f}")
else:
    print("No admissible trios")
