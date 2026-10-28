# results/math/ — Fase Math: verificações matemáticas preliminares

Esta pasta contém os outputs das verificações algébricas e numéricas
da Fase Math do plano de melhoria (`corpus/IMPROVEMENT_PLAN.md`).

## M1 — Definição de gap e Q3=0 ⟺ Q2=1

**Script:** inline na Athena (sessão tmux `gap_m1`)  
**Output:** `math_m1_gap.log`  
**Data:** 2026-10-01T23:13 UTC-3

### Definição actual (main.tex eq:gap, linha 687)

```
gap(t) = max_{t'∈T} min( (F1(t)-F1(t'))/R1, (F2(t)-F2(t'))/R2, (F3(t')-F3(t))/R3 )^+
```

O artigo afirma: "gap(t)=0 iff t∈F" (linha 693) e "Q3=0 iff Q2=1" (linha 907).

### Análise algébrica (verificado antes do script)

**gap(t)>0 → t estritamente dominado:** CORRECTO.  
O máximo é positivo sse existe t' tal que os três termos são simultaneamente positivos,
ou seja, t' é estritamente melhor em F1, F2 E F3 ao mesmo tempo — dominação estrita.

**gap(t)=0 → t não dominado: FALSO.**  
Contra-exemplo: t' domina t fracamente — melhora F1 e F3, empata F2:

| | F1 (custo, ↓) | F2 (impacto, ↓) | F3 (segurança, ↑) |
|--|--|--|--|
| t  | 0.5 | 0.4 | 0.6 |
| t' | 0.3 | 0.4 | 0.7 |

- F1(t)-F1(t') = 0.2 > 0 ✓
- F2(t)-F2(t') = 0.0 = 0 ← **bloqueia o mínimo**
- F3(t')-F3(t) = 0.1 > 0 ✓

min(0.2, 0.0, 0.1) = 0 → gap(t)=0, mas t' domina t (Pareto fraco).

**Implicação:** a definição de gap mede dominação **estrita**, não dominação de Pareto
(que é fraca: pelo menos tão bom em tudo, estritamente melhor em pelo menos um).
A afirmação "gap=0 iff t∈F" está errada quando a fronteira de Pareto inclui
portfólios que só são dominados fracamente.

**Q3=0 iff Q2=1:** igualmente não se sustenta pela mesma razão.

### Verificação numérica (a completar)

O script `gap_m1` conta, para os dados reais do Fogo, quantos trios têm gap=0
mas são fracamente dominados. Resultado em `math_m1_gap.log`.

### Opções de correcção

1. **Redefinir gap com dominação fraca:**
   ```
   gap_w(t) = max_{t'≠t} min( max(0, F1(t)-F1(t')), max(0, F2(t)-F2(t')), max(0, F3(t')-F3(t)) )
   ```
   Mas max-min de valores não-negativos ainda pode ser 0 quando um empata.

2. **Usar uma formulação standard:** distância à fronteira de Pareto em norma infinita,
   ou somar os excessos em cada objectivo sobre o melhor disponível:
   ```
   gap_alt(t) = max_{ℓ} [ excess_ℓ(t) / R_ℓ ]
   where excess_1 = max(0, F1(t) - min_{t'∈F} F1(t'))
   ```
   Mas requer conhecer F, que é o que queremos testar.

3. **Adoptar a formulação do ideal-nadiral** já mencionada no Suplementar.

4. **Declarar explicitamente** que gap mede dominação estrita, redefinir Q3 de forma
   consistente, e verificar que Q3=0 iff "sem dominador estrito" (não iff Pareto-eficiente).
   Neste caso, Q2 e Q3 medem coisas ligeiramente diferentes: Q2 usa a fronteira de
   Pareto (com dominação fraca), Q3 usa gap (com dominação estrita).

### Decisão necessária (registar em PHASES_STATUS.md M1)

Qual das quatro opções seguir? A decisão afecta:
- A definição de Q3 em §2 e no Suplementar
- A frase "Q3=0 iff Q2=1" (linha 907)
- O valor de gap reportado em tab:canonical (linha 1692–1696)
- O gap=0.028 mencionado para o portfólio greedy {184,279,320} (linha 2063)
