import sys
sys.path.insert(0, '/home/julioazancort/scratch/mcdm/scripts')
from mcdm_experiment import load_data
df, p, b = load_data()
print("OK:", len(df), "sites,", len(p), "trios Pareto")
