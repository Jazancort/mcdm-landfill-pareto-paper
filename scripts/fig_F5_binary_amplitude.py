"""F5 — A_j^rank for binary criterion as a function of n1.

Message: A_j = N/[2(N+1)] is constant in n1 (horizontal line).
         Contrast with (N-1)/(N+1) for continuous criteria.
         Point at n1=94 (aspect) shows the paper's dataset.
Single column (90 mm), purely analytical — no data from Fogo.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig_utils import set_rcparams, savefig, COL1, WONG
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

set_rcparams()

N = 389   # admissible sites

n1_vals = np.arange(1, N)  # 1 .. 388

# Binary criterion: A_j = N / [2(N+1)], independent of n1
A_binary  = np.full_like(n1_vals, N / (2 * (N + 1)), dtype=float)

# Continuous criterion without ties: A_j = (N-1)/(N+1), also independent
# (shown as horizontal reference)
A_cont = (N - 1) / (N + 1)

fig, ax = plt.subplots(figsize=(COL1, COL1 * 0.72))

# Continuous reference (dashed)
ax.axhline(A_cont, color=WONG["blue"], lw=1.2, ls="--",
           label=fr"Continuous, no ties: $(N-1)/(N+1)={A_cont:.3f}$")

# Binary A_j (solid)
ax.plot(n1_vals, A_binary, color=WONG["vermil"], lw=1.4,
        label=fr"Binary: $N/[2(N+1)]={A_binary[0]:.3f}$")

# Point for aspect (n1 = 94)
n1_aspect = 94
ax.scatter([n1_aspect], [A_binary[0]], color=WONG["vermil"],
           s=40, zorder=5)
ax.annotate(r"$n_1 = 94$ (aspect)",
            xy=(n1_aspect, A_binary[0]),
            xytext=(n1_aspect + 30, A_binary[0] - 0.06),
            fontsize=7.5,
            arrowprops=dict(arrowstyle="-", color="#555555", lw=0.8),
            color=WONG["vermil"])

# Shade the gap
ax.fill_between([1, N-1],
                [A_binary[0]] * 2,
                [A_cont] * 2,
                color=WONG["blue"], alpha=0.07)

ax.annotate("", xy=(N//2, A_cont), xytext=(N//2, A_binary[0]),
            arrowprops=dict(arrowstyle="<->", color="#555555", lw=0.8))
ax.text(N//2 + 8, (A_cont + A_binary[0]) / 2,
        fr"$\Delta = {A_cont - A_binary[0]:.3f}$",
        fontsize=7, color="#555555", va="center")

ax.set_xlabel(r"$n_1$ (number of ones in binary criterion)")
ax.set_ylabel(r"$A_j^{\rm rank}$")
ax.set_xlim(0, N)
ax.set_ylim(0.35, 1.05)
ax.legend(loc="center right", fontsize=7.5)

fig.tight_layout(pad=0.4)
savefig(fig, "fig_F5_binary_amplitude")
