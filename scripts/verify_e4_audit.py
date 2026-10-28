import pandas as pd, numpy as np

# ── Tarefa 1: prova algébrica dos offsets ────────────────────────────────────
print("=== Tarefa 1: offsets b_j (algébrica) ===")
print("Para portfolio de tamanho k fixo:")
print("  score(T) = k * C  +  score_sem_offset(T)")
print("  C = sum_j w_j * b_j  (constante por portfolio)")
print("  Logo argmax(score) = argmax(score_sem_offset). QED.")
print("  Greedy: score(site a) += sum_j w_j * b_j  (mesma constante p/ todos os sítios)")
print("  Logo mesma ordenação greedy.")
print("CONCLUSÃO: os offsets b_j não mudam nenhuma escolha. A causa dos 80 pp é outra.")
print()

# ── Tarefa 2: R-M vs R-M' draw-a-draw ────────────────────────────────────────
print("=== Tarefa 2: R-M vs R-M' draw-a-draw ===")
df = pd.read_csv("results/e4_results.csv")
rm  = df[(df["kappa"]==200) & (df["direction"]=="fwd") & (df["cell"]=="R-M")]
rmp = df[(df["kappa"]==200) & (df["direction"]=="rev") & (df["cell"]=="R-M'")]
print(f"R-M   greedy={rm['Q2_greedy'].values[0]}  optimal={rm['Q2_optimal'].values[0]}")
print(f"R-M'  greedy={rmp['Q2_greedy'].values[0]}  optimal={rmp['Q2_optimal'].values[0]}")
identical = (rm['Q2_greedy'].values[0] == rmp['Q2_greedy'].values[0] and
             rm['Q2_optimal'].values[0] == rmp['Q2_optimal'].values[0])
print(f"Médias idênticas: {identical}")
print("=> R-M e R-M' usam X_adj_dm com o mesmo avaliador A'.")
print("=> A 'direcção rev' NÃO usa a fronteira A (213 portfolios). Usa A'.")
print()

# ── Tarefa 4: R-V' vs tab:fourthcell ─────────────────────────────────────────
print("=== Tarefa 4: R-V' vs tab:fourthcell (389/A optimal = 95.0%) ===")
rvp = df[(df["kappa"]==200) & (df["direction"]=="rev") & (df["cell"]=="R-V'")]
q2  = rvp["Q2_optimal"].values[0]
se  = rvp["SE_optimal"].values[0]
ref = 95.0
diff = abs(q2 - ref)
threshold = 3 * max(se, 0.01)
verdict = "FAIL" if diff > threshold else "PASS"
print(f"R-V' kappa=200 opt = {q2}%  SE={se:.2f}")
print(f"Tab:fourthcell 389/A opt = {ref}%")
print(f"|diff| = {diff:.1f} pp   3 SE = {threshold:.2f} pp   => {verdict}")
print()

# ── Assimetria kappa=50 ────────────────────────────────────────────────────────
print("=== Assimetria kappa=50 vs kappa=200 ===")
for k in [50, 200]:
    rw  = df[(df["kappa"]==k) & (df["direction"]=="fwd") & (df["cell"]=="R-W")]
    rwp = df[(df["kappa"]==k) & (df["direction"]=="rev") & (df["cell"]=="R-W'")]
    rv  = df[(df["kappa"]==k) & (df["direction"]=="fwd") & (df["cell"]=="R-V")]
    rvp2 = df[(df["kappa"]==k) & (df["direction"]=="rev") & (df["cell"]=="R-V'")]
    asym_rw = (100 - rwp["Q2_optimal"].values[0]) - (100 - rw["Q2_optimal"].values[0])
    asym_rv = (100 - rvp2["Q2_optimal"].values[0]) - (100 - rv["Q2_optimal"].values[0])
    print(f"kappa={k}: R-W fwd loss={(100-rw['Q2_optimal'].values[0]):.1f}  R-W' rev loss={(100-rwp['Q2_optimal'].values[0]):.1f}  asym={asym_rw:.1f} pp")
    print(f"kappa={k}: R-V fwd loss={(100-rv['Q2_optimal'].values[0]):.1f}  R-V' rev loss={(100-rvp2['Q2_optimal'].values[0]):.1f}  asym={asym_rv:.1f} pp")
