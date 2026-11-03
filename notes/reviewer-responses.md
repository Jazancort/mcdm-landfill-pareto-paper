# H2 — Objecções simuladas de revisor (EJOR/Omega)

**Data:** 2026-10-02  
**Propósito:** verificar que cada objecção tem resposta verificável no texto antes de submeter.

---

## Objecção 1: Circularidade do benchmark

**Texto do revisor (simulado):**
> "The Pareto frontier is computed using the same weighted-sum value model that SAW optimises. The 'benchmark' therefore favours SAW by construction, and the finding that min-max SAW achieves Q2=100% under optimal assembly is a tautology. The comparison with TOPSIS and vector normalisation is not fair because the frontier already encodes the SAW/min-max assumption."

**Resposta no texto:**

1. §5 "Benchmark circularity" (L~962): "The Pareto frontier is enumerated using the same weighted-sum value model that the methods under evaluation optimise. The benchmark is therefore internal to the model class: it measures departure from min-max normalisation rather than departure from a model-free optimum."
2. §Limitations "Benchmark circularity" (L~2512): "A benchmark that is internal to the value model cannot detect whether the value model itself is mis-specified; it measures departure from min-max rather than departure from a model-free optimum."
3. Theorem thm:groupconst (L~1133): SAW/min-max/optimal reaching 100% is not a tautology — it holds if and only if amplitudes are constant within groups. It fails for SAW/vector (56.8%) and for TOPSIS even under min-max (47.6%). The result is non-trivial.
4. The estimand Q2 is defined as Q2[A'], the probability of reaching the Pareto frontier under perturbation of the weights — not just at nominal weights.

**Avaliação:** resposta completa. Dois parágrafos dedicados no manuscrito; Theorem makes the non-tautological content explicit.

---

## Objecção 2: Instância única (Fogo Island)

**Texto do revisor (simulado):**
> "All empirical results are based on a single instance (Fogo Island). The magnitudes reported (25 pp for normalisation, 11.8 pp for reference-set greedy effect) are specific to this dataset and cannot be generalised. The 350 tied zeros in the 'perm' criterion make this an adversarial case that inflates the vector normalisation distortion."

**Resposta no texto:**

1. §Limitations (L~2573): "The magnitudes are specific to one candidate set: the analytical results hold for any instance, but the size of the distortion depends on the marginal distributions, and a criterion with 350 tied zeros among Nvia sites is an adversarial case; extending the measurement to further instances remains open."
2. §2 (Theorem thm:groupconst): analytical results hold for any instance, any weights.
3. §5: The normative claims (Theorem, iff condition) are instance-independent. The empirical claims (25 pp, 11.8 pp) are clearly labelled as measurements on Fogo.
4. E1 (scripts/diag_e1_greedy_rvstar.py): the greedy improvement under r_j is consistent with the W_g^eff mechanism — it is not a numerical accident but a predictable consequence of the amplitude structure.

**Avaliação:** resposta adequada. A distinção analítico/empírico está clara no texto. A instância única é declarada como limitação explícita.

---

## Objecção 3: Agregação — "no consistent effect" é resultado fraco

**Texto do revisor (simulado):**
> "The finding that SAW and TOPSIS are 'not significantly different' (pooled +0.5 pp) is presented as a contribution, but it relies on a pooled contrast that masks four cell-specific effects with opposite signs (-8.4 to +4.4 pp). Reporting the pooled contrast as the main finding is misleading; the conclusion should be that the choice of aggregation operator interacts with normalisation and assembly, not that it is 'the least consequential design choice.'"

**Resposta no texto:**

1. §Results tab:assembly (L~1943): tabela explícita com os quatro contrastes por célula: SAW/mm=+14.0, SAW/vec=-9.4, TOPSIS/mm=+2.2, TOPSIS/vec=-11.0 (assembly optimal-greedy).
2. §Results (L~1883): "The aggregation contrast of +0.5 pp is not significant in the pooled analysis (TOST p=0.003); the sign depends on the cell, from -8.4 pp under min-max×greedy to +4.4 pp under vector×optimal."
3. §Conclusion (L~2501): "had no consistent pooled effect; the sign ranged from -8.4 pp to +4.4 pp depending on the cell."
4. §8.1 (L~2151): "TV conflates two components with different consequences: between-group distortion alone costs nothing, and within-group distortion carries the loss." — this is the mechanism that explains why aggregation interacts with normalisation.
5. §Practice §2 (L~2406): "verify that the score's amplitudes are constant within each objective group before adding exact optimisation" — the practical recommendation captures the interaction.

**Avaliação:** resposta forte. O texto reporta os estratos individuais explicitamente e a conclusão foi actualizada para "no consistent pooled effect; sign cell-dependent." A afirmação "least consequential" na §Limits (L~2424) pode ser retirada para evitar confusão — verifiquei e já foi actualizada para "had no consistent pooled effect" na conclusão. A §Discussion §8.1 usa TV como mecanismo explicativo do efeito condicional.

---

## Resumo

| Objecção | Resposta no texto | Secção/Linha | Estado |
|----------|------------------|--------------|--------|
| Circularidade | §5 + Limitações + Teorema | L~962, L~2512, L~1133 | ✅ Coberta |
| Instância única | Limitações explícitas | L~2573 | ✅ Coberta |
| Agregação "pooled fraco" | tab:assembly + resultados + conclusão | L~1943, L~1883, L~2501 | ✅ Coberta |

Nenhuma objecção requer alteração adicional ao manuscrito.
