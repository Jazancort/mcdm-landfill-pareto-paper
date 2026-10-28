"""F5 — A_j^rank for binary criterion, Intervention Window style."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig_utils import set_rcparams, savefig, COL1, WONG, C_TREATMENT, C_BASELINE
import numpy as np
import matplotlib.pyplot as plt

set_rcparams()

N = 389
n1_vals = np.arange(1, N)
A_binary = np.full_like(n1_vals, N / (2 * (N + 1)), dtype=float)
A_cont   = (N - 1) / (N + 1)

fig, ax = plt.subplots(figsize=(COL1 * 1.2, COL1 * 0.95))

# Shaded gap
ax.fill_between([1, N-1], [A_binary[0]]*2, [A_cont]*2,
                color=C_TREATMENT, alpha=0.08)

# Continuous reference
ax.axhline(A_cont, color=C_TREATMENT, lw=2.0, ls="--",
           label=f"Continuous, no ties: (N-1)/(N+1)={A_cont:.3f}")

# Binary line
ax.plot(n1_vals, A_binary, color=C_BASELINE, lw=2.0,
        label=f"Binary: N/[2(N+1)]={A_binary[0]:.3f}")

# Marker at aspect
n1_aspect = 94
ax.scatter([n1_aspect], [A_binary[0]], color=C_BASELINE,
           s=60, zorder=5, linewidths=0)
ax.annotate(r"$n_1=94$ (aspect)",
            xy=(n1_aspect, A_binary[0]),
            xytext=(n1_aspect + 40, A_binary[0] - 0.07),
            fontsize=11, color=C_BASELINE,
            arrowprops=dict(arrowstyle="-", color=C_BASELINE, lw=1.0))

# Gap annotation
mid = N // 2
ax.annotate("", xy=(mid, A_cont), xytext=(mid, A_binary[0]),
            arrowprops=dict(arrowstyle="<->", color="#555555", lw=1.0))
ax.text(mid + 12, (A_cont + A_binary[0]) / 2,
        fr"$\Delta={A_cont - A_binary[0]:.3f}$",
        fontsize=11, color="#555555", va="center")

ax.set_xlabel(r"$n_1$ (number of ones in binary criterion)", fontweight="bold")
ax.set_ylabel(r"$A_j^{\rm rank}$", fontweight="bold")
ax.set_xlim(0, N)
ax.set_ylim(0.35, 1.05)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14),
          ncol=1, frameon=False)

plt.tight_layout(pad=0.5)
plt.subplots_adjust(bottom=0.22)
savefig(fig, "fig_F5_binary_amplitude")
