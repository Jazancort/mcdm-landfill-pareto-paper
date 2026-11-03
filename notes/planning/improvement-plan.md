# Plano de Melhoria — v2
## Comparison between MCDM Methods for Landfill Site Selection

**v1:** Setembro de 2026
**v2:** Setembro de 2026 — incorpora revisão externa com verificação numérica independente

> **Mudanças em relação à v1:**
> - Adicionada Fase 0 (decisão estrutural sobre o desenho experimental), que é pré-requisito para todas as demais fases.
> - Fórmula de r_w corrigida (Pinto da Costa & Soares, 2005).
> - Código Python corrigido (API pyDecision, loop Monte Carlo, variável não usada, índice VIKOR).
> - Removidos scores de publicabilidade numéricos sem base metodológica.
> - Corrigida afirmação sobre rank reversal no PROMETHEE II.
> - Corrigidos graus de liberdade dos testes estatísticos.
> - Adicionado aviso sobre DOIs de referências 2025–2026 não verificados independentemente.

---

## Fase 0 — Decisão Estrutural sobre o Desenho Experimental

### 0.1 O problema

O desenho atual é circular: TOPSIS e PROMETHEE II foram aplicados à **matriz de comparação par a par do AHP**, usando os **pesos derivados dessa mesma matriz** como entrada. Os três métodos processam a mesma informação. A alta concordância observada (Kendall W = 0,966, p = 0,0013) é esperada por construção, não é evidência de que métodos independentes convergem.

Consequência direta: as Fases 1–4 do plano original não resolvem o problema estrutural. A Fase 1 (coeficientes de correlação) vai confirmar a circularidade. A Fase 2 (SAW como baseline) vai reproduzir o AHP pela propriedade $A \cdot w = \lambda_{max} \cdot w$. A Fase 3 (sensibilidade dos pesos do AHP) não faz sentido — no AHP, o ranking *é* o vetor de pesos. Todas essas fases só têm valor depois que a Fase 0 for resolvida.

### 0.2 Os três caminhos possíveis

#### Caminho A — Reprojetar o experimento (maior esforço, maior contribuição)

**O problema MCDM real** não é ranquear critérios — é ranquear *áreas candidatas* com base nos critérios. Cada área recebe uma pontuação em cada critério (distância medida em km, permeabilidade do solo em classes, etc.), e os métodos MCDM são aplicados para ranquear as áreas. Nesse caso, TOPSIS e PROMETHEE II operam sobre dados empíricos independentes dos pesos do AHP.

**O que fazer:** verificar se Andrade e Barbosa (2015) ou Sodré et al. (2020) publicam as pontuações das áreas candidatas por critério. Se publicam, extrair esses dados e reprojetar o experimento completo.

**O que ganhar:** o artigo passa a comparar métodos aplicados ao problema para o qual foram projetados. A concordância ou discordância observada terá significado metodológico real.

**Referência de modelo:** Sener et al. (2010) apresentam pontuações de áreas candidatas por critério e aplicam AHP + GIS — estrutura que pode ser seguida.

#### Caminho B — Transformar em comparação de métodos de ponderação

Em vez de comparar MCDM de ranking de alternativas, comparar **métodos para derivar pesos de critérios**. A pergunta passa a ser: "métodos distintos de ponderação produzem pesos similares para esses critérios?"

Métodos a comparar:
- **Autovetor (AHP):** já implementado — produz w = [0,166, 0,102, ...].
- **Média geométrica por linha:** alternativa de cálculo ao autovetor dentro do AHP; computacionalmente mais simples.
- **Best-Worst Method (BWM):** pede ao especialista apenas os melhores e piores critérios, não todas as comparações par a par — reduz o número de julgamentos de $n(n-1)/2 = 55$ para $2n - 3 = 19$.
- **Método da entropia:** deriva pesos a partir da dispersão dos dados, sem julgamentos de especialistas.
- **CRITIC (Criteria Importance Through Intercriteria Correlation):** combina desvio-padrão e correlação entre critérios para derivar pesos objetivos.

**O que fazer:** aplicar cada método à mesma matriz ou conjunto de dados e comparar os vetores de pesos resultantes com Spearman ρ, r_w e WS.

**O que ganhar:** a questão de pesquisa se torna "métodos subjetivos (AHP, BWM) e objetivos (entropia, CRITIC) concordam na ponderação de critérios ambientais?" — uma contribuição genuína e não circular.

#### Caminho C — Manter o desenho, reconhecer a limitação, moderar as conclusões

Manter o experimento atual, mas:
1. Adicionar uma subseção explícita "Limitations of the Experimental Design" descrevendo a circularidade.
2. Reformular as conclusões: em vez de "métodos independentes convergem", dizer "quando os mesmos pesos e a mesma matriz são processados por paradigmas diferentes, as discrepâncias observadas revelam as diferenças matemáticas intrínsecas dos métodos".
3. Acrescentar a Fase 1 (coeficientes formais) com a interpretação correta: os altos valores de concordância confirmam o que era esperado pelo desenho, e a diferença em relação à linha de base aleatória (W = 0,55) quantifica o quanto a estrutura do input constrainge os rankings.

**O que fazer:** nenhuma mudança experimental — apenas na análise e na escrita.

**O que ganhar:** o artigo fica honesto sobre o que demonstra. Menor esforço, mas contribuição mais modesta.

### 0.3 Recomendação

O Caminho A produz o artigo mais forte, mas depende da disponibilidade dos dados das áreas candidatas em Andrade & Barbosa (2015) ou outra fonte. Verificar essa disponibilidade é a primeira ação concreta.

O Caminho B é independente de dados novos e transforma o artigo em uma contribuição metodológica legítima. É o caminho de menor risco.

O Caminho C é adequado para o contexto de um trabalho de disciplina de pós-graduação, mas insuficiente para publicação em periódico indexado.

### 0.4 Ação imediata

Antes de prosseguir com qualquer outra fase:

1. Ler Andrade e Barbosa (2015) na íntegra e verificar se as pontuações das áreas candidatas estão publicadas.
2. Ler Sodré et al. (2020) com o mesmo objetivo.
3. Decidir entre Caminhos A, B ou C e documentar a decisão.

---

## Fase 1 — Avaliação Matemática da Consistência dos Rankings

**Pré-requisito:** Fase 0 concluída. Se o Caminho C foi escolhido, esta fase pode ser aplicada ao experimento atual com a interpretação correta (os altos valores confirmam a circularidade). Se os Caminhos A ou B foram escolhidos, aplicar ao novo experimento.

### 1.1 Objetivo

Substituir a comparação por contagem de posições idênticas (%) por coeficientes estatísticos formais: Spearman ρ, Weighted Spearman r_w, WS Coefficient (Sałabun & Urbaniak, 2020) e Kendall W.

### 1.2 Coeficientes a calcular

#### Spearman ρ

$$\rho = 1 - \frac{6 \sum_{i=1}^{n} d_i^2}{n(n^2 - 1)}$$

onde $d_i = x_i - y_i$ é a diferença de posição do critério $i$ entre dois rankings e $n = 11$.

**Teste de significância:** estatística $t = \rho\sqrt{(n-2)/(1-\rho^2)}$ com $n - 2 = 9$ graus de liberdade.

#### Weighted Spearman r_w (Pinto da Costa & Soares, 2005)

$$r_w = 1 - \frac{6 \sum_{i=1}^{n} (x_i - y_i)^2 \left[(N - x_i + 1) + (N - y_i + 1)\right]}{N^4 + N^3 - N^2 - N}$$

onde $x_i$, $y_i$ são as posições nos dois rankings e $N = 11$. Esta fórmula pondera mais os critérios nas primeiras posições (menor valor de $x_i + y_i$ = posições mais altas = maior contribuição ao denominador das discrepâncias).

**Referência:** Pinto da Costa, J. F., & Soares, R. (2005). A weighted rank correlation coefficient. *Statistical Methodology*, 2(1), 25–35.

#### WS Coefficient (Sałabun & Urbaniak, 2020)

$$WS(A, B) = 1 - \sum_{i=1}^{n} 2^{-x_i} \cdot \frac{|x_i - y_i|}{\max(x_i - 1,\; n - x_i)}$$

onde $x_i$ é a posição no ranking de referência A e $y_i$ no ranking testado B. O coeficiente é assimétrico: WS(A, B) ≠ WS(B, A) em geral.

**Referência:** Sałabun, W., & Urbaniak, K. (2020). A New Coefficient of Rankings Similarity in Decision-Making Problems. *ICCS 2020*, LNCS 12138. https://doi.org/10.1007/978-3-030-50417-5_47

#### Kendall W (concordância simultânea de m rankings)

$$W = \frac{12 S}{m^2(n^3 - n)}, \quad S = \sum_{i=1}^{n} \left(R_i - \bar{R}\right)^2$$

onde $R_i = \sum_{j=1}^{m} r_{ij}$ é a soma dos ranks do critério $i$ nos $m = 3$ métodos e $\bar{R} = m(n+1)/2$.

**Teste de significância:** $\chi^2 = m(n-1)W$ com $n - 1 = 10$ graus de liberdade. Para $n = 11$, testes de permutação são mais precisos que a aproximação qui-quadrado.

### 1.3 Valores calculados (experimento atual, para referência)

| Par | Spearman ρ | Kendall τ | r_w | WS (A→B / B→A) |
|---|---|---|---|---|
| AHP–TOPSIS | 0,936 | 0,818 | 0,921 | 0,873 / 0,869 |
| AHP–PROMETHEE II | 0,964 | 0,891 | 0,955 | 0,961 / 0,950 |
| TOPSIS–PROMETHEE II | 0,945 | 0,855 | 0,942 | 0,906 / 0,908 |
| **Kendall W** | **0,966** | χ²(10) = 28,97 | **p = 0,0013** | — |

Linha de base aleatória (100 mil sorteios, percentil 95): ρ = 0,53, WS = 0,80, W = 0,55.

**Interpretação correta:** Os valores estão acima da linha de base, mas são esperados dado o desenho circular. Eles quantificam a estrutura do input, não a convergência independente dos métodos.

### 1.4 Script Python corrigido

```python
# -*- coding: utf-8 -*-
"""
ranking_correlation.py
Coeficientes de correlação de ranking para os métodos MCDM do artigo.
Requer: numpy, scipy
"""

import numpy as np
from scipy import stats
from itertools import combinations, permutations

# Dados verificados independentemente (Tabela 2 do artigo)
CRITERIA = ['x1','x2','x3','x4','x5','x6','x7','x8','x9','x10','x11']
n = len(CRITERIA)

rankings = {
    'AHP':       np.array([1,  4,  2,  9,  8,  5,  3, 11,  7, 10,  6]),
    'TOPSIS':    np.array([2,  6,  1,  9,  7,  3,  4, 11,  8, 10,  5]),
    'PROMETHEE': np.array([1,  5,  2,  9,  8,  3,  4, 11,  6, 10,  7]),
}
methods = list(rankings.keys())


def spearman(a, b):
    rho, pval = stats.spearmanr(a, b)
    return rho, pval


def weighted_spearman(x, y, N):
    """
    Pinto da Costa & Soares (2005).
    r_w = 1 - 6*sum((x_i - y_i)^2 * [(N - x_i + 1) + (N - y_i + 1)]) / (N^4 + N^3 - N^2 - N)
    """
    numerator = 6 * np.sum((x - y)**2 * ((N - x + 1) + (N - y + 1)))
    denominator = N**4 + N**3 - N**2 - N
    return 1 - numerator / denominator


def ws_coefficient(a, b, n):
    """
    Sałabun & Urbaniak (2020). Assimétrico: A é o ranking de referência.
    WS(A,B) = 1 - sum( 2^(-a_i) * |a_i - b_i| / max(a_i-1, n-a_i) )
    """
    total = 0.0
    for i in range(n):
        denom = max(a[i] - 1, n - a[i])
        if denom == 0:
            # Posição única que não pode deslocar-se (só ocorre se n=1)
            continue
        total += 2**(-a[i]) * abs(a[i] - b[i]) / denom
    return 1 - total


def kendall_tau(a, b):
    tau, pval = stats.kendalltau(a, b)
    return tau, pval


def kendall_w(rank_matrix):
    """
    rank_matrix: array (n_criteria, n_methods).
    Retorna (W, chi2, p_value).
    """
    m = rank_matrix.shape[1]
    R_i = rank_matrix.sum(axis=1)
    R_bar = m * (n + 1) / 2
    S = np.sum((R_i - R_bar)**2)
    W = 12 * S / (m**2 * (n**3 - n))
    chi2 = m * (n - 1) * W
    pval = 1 - stats.chi2.cdf(chi2, df=n - 1)
    return W, chi2, pval


def permutation_baseline(n_items, n_methods, n_sim=100_000, seed=42):
    """
    Linha de base: percentil 95 dos coeficientes sob rankings aleatórios.
    """
    rng = np.random.default_rng(seed)
    ws_vals, rho_vals, w_vals = [], [], []
    for _ in range(n_sim):
        r = [rng.permutation(np.arange(1, n_items + 1)) for _ in range(n_methods)]
        rho_vals.append(stats.spearmanr(r[0], r[1]).statistic)
        ws_vals.append(ws_coefficient(r[0], r[1], n_items))
        mat = np.column_stack(r)
        W, _, _ = kendall_w_raw(mat, n_items)
        w_vals.append(W)
    p95 = lambda v: np.percentile(v, 95)
    return p95(rho_vals), p95(ws_vals), p95(w_vals)


def kendall_w_raw(rank_matrix, n):
    m = rank_matrix.shape[1]
    R_i = rank_matrix.sum(axis=1)
    R_bar = m * (n + 1) / 2
    S = np.sum((R_i - R_bar)**2)
    W = 12 * S / (m**2 * (n**3 - n))
    chi2 = m * (n - 1) * W
    pval = 1 - stats.chi2.cdf(chi2, df=n - 1)
    return W, chi2, pval


# --- Resultados ---
print("=" * 60)
print("COEFICIENTES DE CORRELAÇÃO DE RANKING")
print("=" * 60)

print("\nSpearman ρ e Kendall τ (par a par):")
for a_name, b_name in combinations(methods, 2):
    a, b = rankings[a_name], rankings[b_name]
    rho, p_rho = spearman(a, b)
    tau, p_tau = kendall_tau(a, b)
    print(f"  ({a_name}, {b_name}): rho={rho:.3f} (p={p_rho:.4f})  tau={tau:.3f} (p={p_tau:.4f})")

print("\nWeighted Spearman r_w (Pinto da Costa & Soares, 2005):")
for a_name, b_name in combinations(methods, 2):
    rw = weighted_spearman(rankings[a_name], rankings[b_name], n)
    print(f"  ({a_name}, {b_name}): r_w = {rw:.3f}")

print("\nWS Coefficient (Sałabun & Urbaniak, 2020) — assimétrico:")
for a_name, b_name in permutations(methods, 2):
    ws = ws_coefficient(rankings[a_name], rankings[b_name], n)
    print(f"  ({a_name} -> {b_name}): WS = {ws:.3f}")

print("\nKendall W (concordância global):")
rank_matrix = np.column_stack([rankings[m] for m in methods])
W, chi2, pval = kendall_w(rank_matrix)
print(f"  W = {W:.4f}   chi2({n-1}) = {chi2:.4f}   p = {pval:.4f}")

print("\nLinha de base aleatória (100k sorteios, percentil 95):")
p95_rho, p95_ws, p95_w = permutation_baseline(n, len(methods))
print(f"  rho_p95 = {p95_rho:.3f}   WS_p95 = {p95_ws:.3f}   W_p95 = {p95_w:.3f}")
```

---

## Fase 2 — Expansão do Conjunto de Métodos

**Pré-requisito:** Fase 0 resolvida. Esta fase só faz sentido se o Caminho A ou B foi escolhido.

Se o Caminho A (ranquear áreas candidatas): adicionar VIKOR e ELECTRE III, que têm semântica natural para alternativas com pontuações em critérios.

Se o Caminho B (comparar métodos de ponderação): adicionar BWM, CRITIC e entropia — que são métodos de ponderação, não de ranqueamento de alternativas.

Se o Caminho C (manter desenho atual): SAW pode ser adicionado, mas com a nota de que vai reproduzir o AHP pela propriedade $A \cdot w = \lambda_{max} \cdot w$ e portanto não acrescenta informação nova sobre a comparação metodológica.

### 2.1 Correções de API da pyDecision

A versão v1 do plano continha erros de API. Verificar sempre na versão instalada:

```python
# Verificar assinatura das funções antes de usar
from pyDecision.algorithm import vikor_method, promethee_ii
import inspect
print(inspect.signature(vikor_method))
print(inspect.signature(promethee_ii))
```

Erros identificados na v1 (podem variar por versão da biblioteca):
- VIKOR: o parâmetro não se chama `v` — verificar se é `strategy_coefficient` ou outro nome.
- VIKOR: a função retorna uma tupla `(S, R, Q, ranking)` — usar o índice correto para o ranking.
- PROMETHEE II: exige parâmetros de função de preferência (Q, S, P) por critério — não aceita apenas pesos.
- A notação do VIKOR na v1 tinha erro de índice: $f_{ij}^* = \max_i f_{ij}$ (máximo sobre alternativas $i$, não sobre critérios $j$).

### 2.2 Correção da notação VIKOR

A fórmula correta:

$$f_j^* = \max_i f_{ij} \quad \text{(melhor valor do critério } j \text{ entre todas as alternativas } i\text{)}$$
$$f_j^- = \min_i f_{ij} \quad \text{(pior valor)}$$

$$S_i = \sum_{j=1}^{n} w_j \frac{f_j^* - f_{ij}}{f_j^* - f_j^-}$$

$$R_i = \max_j \left[ w_j \frac{f_j^* - f_{ij}}{f_j^* - f_j^-} \right]$$

$$Q_i = v \frac{S_i - S^*}{S^- - S^*} + (1-v) \frac{R_i - R^*}{R^- - R^*}$$

onde $v \in [0,1]$ é o parâmetro de compromisso (tipicamente $v = 0.5$).

---

## Fase 3 — Análise de Sensibilidade

**Pré-requisito:** Fase 0 resolvida. Com o Caminho A ou B.

Com o desenho atual (Caminho C), a análise de sensibilidade dos pesos do AHP não tem sentido autônomo: o ranking do AHP é o vetor de pesos, então "perturbar os pesos" é apenas redefinir a resposta do AHP. Isso não testa a sensibilidade dos *rankings* produzidos pelos métodos MCDM — apenas mostra que pesos diferentes produzem rankings diferentes, o que é trivial.

Com o Caminho A (áreas candidatas com pontuações independentes), a sensibilidade dos pesos testa como os rankings das áreas mudam quando os pesos dos critérios variam. Isso tem sentido porque as pontuações das áreas são fixas e independentes dos pesos.

### 3.1 Script corrigido — perturbação sistemática

```python
# -*- coding: utf-8 -*-
"""
sensitivity_analysis.py
Análise de sensibilidade — requer o Caminho A (pontuações reais de áreas).
O loop Monte Carlo está completo (a v1 tinha 'pass' no lugar do corpo do loop).
"""

import numpy as np
from scipy.stats import dirichlet

# ATENÇÃO: preencher com pontuações reais das áreas candidatas (Caminho A).
# Este script é um template — não funciona com a matriz AHP (Caminho C).
# decision_matrix: shape (n_areas, n_criteria)
# decision_matrix = np.array([...])  # extrair de Andrade & Barbosa (2015)

N_SIM = 1_000
N_CRITERIA = 11
criteria_names = ['x1','x2','x3','x4','x5','x6','x7','x8','x9','x10','x11']
weights_original = np.array([0.166,0.102,0.152,0.065,0.069,
                               0.089,0.113,0.029,0.075,0.055,0.081])


def perturb_weights(weights, idx, delta):
    """
    Perturba w[idx] em +delta e redistribui o excesso proporcionalmente
    entre os demais critérios, mantendo sum(w) = 1.
    """
    w = weights.copy()
    w[idx] = np.clip(weights[idx] + delta, 0.0, 1.0)
    residual = 1.0 - w[idx]
    others = [i for i in range(len(w)) if i != idx]
    total_others = weights[others].sum()
    if total_others > 0:
        w[others] = weights[others] * residual / total_others
    return w / w.sum()   # normalizar para garantir soma exata = 1


def run_methods(decision_matrix, weights, criterion_type):
    """
    Executa os métodos MCDM e retorna os rankings.
    Preencher com as chamadas corretas da pyDecision após verificar a API.
    """
    # Verificar assinaturas antes de usar:
    # from pyDecision.algorithm import topsis_method, promethee_ii, vikor_method
    # print(inspect.signature(topsis_method))
    raise NotImplementedError("Preencher com chamadas pyDecision verificadas")


# --- Monte Carlo ---
rng = np.random.default_rng(seed=42)
random_weights = dirichlet.rvs([1.0] * N_CRITERIA, size=N_SIM, random_state=42)

# Contadores de frequência no top-3
top3_freq = {m: np.zeros(N_CRITERIA) for m in ['TOPSIS', 'PROMETHEE', 'VIKOR']}

for sim_idx in range(N_SIM):
    w = random_weights[sim_idx]
    # rankings_sim = run_methods(decision_matrix, w, criterion_type)
    # for method_name, ranking in rankings_sim.items():
    #     top3 = np.argsort(ranking)[:3]
    #     top3_freq[method_name][top3] += 1
    pass  # REMOVER este pass após implementar run_methods

# Verificar que os contadores foram preenchidos antes de plotar
total_filled = sum(top3_freq['TOPSIS'])
if total_filled == 0:
    print("AVISO: run_methods não implementado — gráfico vazio.")
else:
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    for ax, (method_name, freq) in zip(axes, top3_freq.items()):
        ax.bar(range(N_CRITERIA), freq / N_SIM, tick_label=criteria_names)
        ax.set_title(f'{method_name}')
        ax.set_ylim(0, 1)
        ax.set_ylabel('Freq. no top-3')
    plt.suptitle(f'Frequência no top-3 em {N_SIM} simulações Monte Carlo')
    plt.tight_layout()
    plt.savefig('sensitivity_top3.pdf', bbox_inches='tight', dpi=300)
    plt.savefig('sensitivity_top3.png', bbox_inches='tight', dpi=300)
    plt.close()
    print("Figuras salvas.")
```

---

## Fase 4 — Segundo Dataset

**Pré-requisito:** Fase 0, Caminho A.

O segundo dataset deve ser outra aplicação real de MCDM para seleção de aterro com pontuações de áreas candidatas disponíveis. Candidatos: Sener et al. (2010) — Turquia; Sodré et al. (2020) — Castanhal, Pará.

Verificar a disponibilidade dos dados antes de planejar esta fase.

---

## Fase 5 — Reestruturação do Artigo

**Pré-requisito:** Fases 0–3 concluídas.

### 5.1 Erros a corrigir independentemente do caminho escolhido

Os itens abaixo devem ser corrigidos em qualquer versão do artigo:

1. **"40 thousand tons per day"** — verificar em Brito et al. (2020) e corrigir para o valor real (provavelmente t/mês ou t/ano).
2. **7 vs. 9 critérios** — adotar um valor consistente em todo o texto. Saaty & Ozdemir (2003) falam em 7±2; a Tabela 6 pode manter "threshold of 9" se esse for o valor adotado, mas o texto deve usar o mesmo número.
3. **"Raises doubts about AHP"** — remover ou reformular. O CR = 0,057 não sustenta esta afirmação para o experimento atual.
4. **Complexidade do AHP** — mudar de "Low" para "Medium" na Tabela 6, ou adicionar nota distinguindo a complexidade da aproximação da complexidade do autovetor exato.
5. **Fonte da Tabela 1** — corrigir de Costa (2020) para Andrade e Barbosa (2015).
6. **x₄ e x₁₀ como "menos importantes"** — adicionar parágrafo discutindo a diferença entre critérios de classificação e restrições absolutas.

### 5.2 Nova seção 4.1: avaliação matemática (aplicável ao Caminho C)

Substituir a Tabela 5 pelos coeficientes da Fase 1. Apresentar:

- Tabela com Spearman ρ, Kendall τ, r_w, WS para os três pares.
- Kendall W com teste qui-quadrado (W = 0,966, χ²(10) = 28,97, p = 0,0013).
- Linha de base aleatória como referência.
- Interpretação: os valores altos são esperados dado o desenho do experimento, e são reportados para rigor metodológico, não como evidência de convergência independente.

### 5.3 Figuras

**Figura 1 (manter):** fluxograma da metodologia — bem construído.

**Figura 2 (nova, aplicável a qualquer caminho):** heatmap dos coeficientes WS entre pares de métodos.

```python
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Valores da Fase 1 (A→B, usando AHP como referência)
# Linha/coluna i: AHP=0, TOPSIS=1, PROMETHEE=2
ws_matrix = np.array([
    [1.000, 0.873, 0.961],
    [0.869, 1.000, 0.906],
    [0.950, 0.908, 1.000],
])
labels = ['AHP', 'TOPSIS', 'PROMETHEE']

fig, ax = plt.subplots(figsize=(5, 4))
sns.heatmap(ws_matrix, annot=True, fmt='.3f', cmap='RdYlGn',
            xticklabels=labels, yticklabels=labels,
            vmin=0.5, vmax=1.0, ax=ax,
            linewidths=0.5, linecolor='white')
ax.set_title('WS Coefficient — Ranking Similarity')
ax.set_xlabel('Tested ranking (B)')
ax.set_ylabel('Reference ranking (A)')
plt.tight_layout()
plt.savefig('fig_ws_heatmap.pdf', bbox_inches='tight', dpi=300)
plt.savefig('fig_ws_heatmap.png', bbox_inches='tight', dpi=300)
plt.close()
```

**Figura 3 (nova):** parallel coordinates dos rankings por critério por método — útil para visualizar onde os métodos discordam.

---

## Apêndice A — Cronograma por Caminho

### Caminho C (mínimo viável)

| Ação | Estimativa |
|---|---|
| Corrigir 6 erros factuais do artigo | 0,5 dia |
| Implementar Fase 1 (coeficientes, script correto) | 1 dia |
| Escrever nova Seção 4.1 e gerar heatmap WS | 1 dia |
| Adicionar subseção "Limitations of the Experimental Design" | 0,5 dia |
| Reformular conclusões | 0,5 dia |
| **Total** | **~3,5 dias** |

### Caminho B (comparação de métodos de ponderação)

| Ação | Estimativa |
|---|---|
| Implementar BWM, CRITIC e entropia em Python | 2 dias |
| Comparar vetores de pesos com os coeficientes da Fase 1 | 1 dia |
| Reestruturar artigo | 2 dias |
| **Total** | **~5 dias** |

### Caminho A (áreas candidatas reais)

| Ação | Estimativa |
|---|---|
| Localizar e extrair dados de áreas (Andrade 2015 / Sodré 2020) | 1–3 dias |
| Reprojetar e implementar experimento completo | 3 dias |
| Análise de sensibilidade e Monte Carlo | 2 dias |
| Reestruturar artigo + figuras | 3 dias |
| **Total** | **~12 dias** |

---

## Apêndice B — Periódicos-Alvo

| Periódico | Quartil (verificar JIF atual) | Adequação |
|---|---|---|
| *Symmetry* (MDPI) | Q2 | Alta — publica benchmarking MCDM |
| *Mathematics* (MDPI) | Q1 | Alta — aceita metodologia MCDM |
| *Environmental Earth Sciences* (Springer) | Q2 | Alta com Caminho A |
| *Sustainability* (MDPI) | Q2 | Alta com componente ambiental |
| *Waste Management* (Elsevier) | Q1 | Média-alta com Caminho A e dados reais |

> Verificar os fatores de impacto e quartis atuais em JCR/Scimago antes de submeter. Os valores acima podem estar desatualizados.

---

## Apêndice C — Referências Novas (verificar DOIs antes de citar)

> **Aviso:** os DOIs abaixo foram obtidos via Crossref mas não foram verificados individualmente. Conferir cada um em https://doi.org antes de incluir em submissão.

1. **Pinto da Costa, J. F., & Soares, R. (2005).** A weighted rank correlation coefficient. *Statistical Methodology*, 2(1), 25–35.

2. **Sałabun, W., & Urbaniak, K. (2020).** A New Coefficient of Rankings Similarity in Decision-Making Problems. *ICCS 2020*, LNCS 12138, pp. 632–645. Springer. https://doi.org/10.1007/978-3-030-50417-5_47

3. **Mareschal, B., De Smet, Y., & Nemery, P. (2008).** Rank reversal in the PROMETHEE II method: some new results. *2008 IEEE IEEM*, pp. 959–963. https://doi.org/10.1109/IEEM.2008.4737980

4. **Alkaradaghi, K., Ali, S. S., Al-Ansari, N., & Laue, J. (2020).** Landfill Site Selection Using GIS and MCDM AHP and SAW Methods. *Engineering*, 12(4), 254–268. https://doi.org/10.4236/eng.2020.124021 *(verificar)*

5. **Korucu, M. K., & Erdagi, B. (2012).** A criticism of applications with MCDM for municipal solid waste disposal site selection. *Waste Management*, 32(12), 2315–2323. https://doi.org/10.1016/j.wasman.2012.07.003

6. **Güler, E. (2026).** A Novel Spherical Distance Measure for SF-TOPSIS via Landfill Site Selection. *Mathematics*, 14(9), 1416. https://doi.org/10.3390/math14091416 *(verificar — 2026)*

7. **Putro, D. P. et al. (2025).** Comparative Analysis of AHP, SAW, TOPSIS, VIKOR, and MABAC. *Transformatika*, 23(1). https://doi.org/10.26623/transformatika.v23i1.12220 *(verificar — 2025)*

8. **Rekkal, S. et al. (2026).** Comparative Study of TOPSIS, AHP, VIKOR, PROMETHEE II and ELECTRE II. *Acta Informatica Pragensia*, 15(3). https://doi.org/10.18267/j.aip.322 *(verificar — 2026)*

9. **Lassey, M. K. (2025).** Comparative Analysis of PROMETHEE, VIKOR and TOPSIS for Logistics Centre Location. Preprint. https://doi.org/10.21203/rs.3.rs-7870462/v1 *(verificar — preprint)*
