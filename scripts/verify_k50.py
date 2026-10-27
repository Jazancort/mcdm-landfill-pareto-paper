import numpy as np, hashlib
from pathlib import Path
ROOT = Path(__file__).parent.parent
p = ROOT / "results" / "e1" / "e1_weights_k50.npy"
d = p.read_bytes()
sha = hashlib.sha256(d).hexdigest()
W = np.load(p)
print(f"SHA256: {sha}")
print(f"Shape: {W.shape}")
print(f"W[0,:3]: {W[0,:3]}")
print(f"W[0].sum(): {W[0].sum():.8f}")
