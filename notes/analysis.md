# Análise Crítica do Artigo — v2
## Comparison between Multi-Criteria Decision-Making Methods to support the determination of sites for the construction of a landfill

**Autor:** Julio L. Azancort Neto (UFPA, 2022)
**Versão analisada:** `Artigo Final - MCDM - Completo.docx` (Final v1, jun/2022)
**v1 desta análise:** Setembro de 2026
**v2 desta análise:** Setembro de 2026 — incorpora revisão externa com verificação numérica independente

> **Nota sobre a revisão:** os cálculos do artigo foram refeitos independentemente a partir da matriz de comparação par a par. Os rankings se confirmam. A revisão identificou um problema de desenho experimental que a v1 desta análise não havia detectado. Este documento incorpora e avalia cada ponto levantado.

---

## 1. Resumo do Artigo

O artigo compara três métodos MCDM — AHP, TOPSIS e PROMETHEE II — aplicados à classificação de onze critérios para seleção do melhor local de construção de um aterro sanitário. Os dados são extraídos de Andrade e Barbosa (2015), que analisaram a Ilha do Fogo, Cabo Verde. A implementação utiliza Python com a biblioteca `pyDecision`. Os métodos são comparados em termos de ranking de critérios, complexidade, laboriosidade, número máximo de critérios e frequência de uso na literatura.

**Contribuição declarada:** mostrar que nenhum método MCDM isolado é unanimemente válido; recomendar o uso simultâneo de múltiplos métodos.

---

## 2. O que é Bom

### 2.1 Escolha do problema
A localização de aterros sanitários é um problema real, relevante e com impacto direto na gestão ambiental urbana. O contexto de Belém/PA reforça a motivação local e conecta o trabalho a um problema concreto da região Amazônica.

### 2.2 Uso de Python e pyDecision
A implementação computacional via Python garante reprodutibilidade. Os cálculos foram verificados independentemente e os rankings se confirmam. Disponibilizar o código no GitHub é boa prática acadêmica.

### 2.3 Comparação de três métodos com fundamentos distintos
AHP (hierárquico, baseado em autovetores), TOPSIS (baseado em distância ao ideal) e PROMETHEE II (baseado em fluxos de preferência) representam paradigmas matematicamente diferentes. Mesmo aplicados ao mesmo input, produzem rankings distintos em algumas posições — o que demonstra que o paradigma do método importa. Isso é, em si, um resultado válido.

### 2.4 Tabela de parâmetros de comparação (Tabela 6)
A tabela que compara aplicabilidade, complexidade, laboriosidade, número de critérios, frequência e suporte a software é um elemento sintético útil.

### 2.5 Identificação de critérios-chave
A convergência dos três métodos em x1 (Núcleo Urbano) e x3 (Permeabilidade) como mais importantes, e em x4, x10, x8 como menos importantes, é um resultado prático utilizável.

### 2.6 Consistência da matriz AHP
λ_max = 11,853, CI = 0,085, CR = 0,057. A matriz está dentro do critério de aceitabilidade (CR < 0,10).

---

## 3. O Problema Principal: Desenho Experimental Circular

**Este é o problema mais sério do artigo e não havia sido detectado na v1 desta análise.**

### 3.1 Como o experimento está estruturado

TOPSIS e PROMETHEE II foram aplicados à **matriz de comparação par a par do AHP**, usando os **pesos derivados dessa mesma matriz** como pesos dos critérios. Isso significa que:

1. O AHP processa a matriz e produz o vetor de pesos w.
2. TOPSIS e PROMETHEE II recebem como input: (a) a própria matriz AHP como "decision matrix" e (b) o vetor w como pesos.
3. Os três métodos processam matematicamente a mesma informação.

### 3.2 Por que isso é um problema

A alta concordância entre os métodos é **esperada por construção**, não é evidência de que métodos diferentes convergem quando aplicados ao mesmo problema de forma independente.

Mais especificamente: pela propriedade do autovetor do AHP, $A \cdot w = \lambda_{max} \cdot w$. Isso significa que a soma ponderada das linhas da matriz retorna o próprio vetor de pesos multiplicado por $\lambda_{max}$. Qualquer método que compute uma soma ponderada das linhas da matriz de comparação — como SAW faz — vai reproduzir o ranking do AHP por definição.

### 3.3 O que a alta concordância realmente mostra

Os coeficientes calculados com os dados do artigo:

| Par | Spearman ρ | Kendall τ | r_w | WS (A→B) |
|---|---|---|---|---|
| AHP–TOPSIS | 0,936 | 0,818 | 0,921 | 0,873 |
| AHP–PROMETHEE II | 0,964 | 0,891 | 0,955 | 0,961 |
| TOPSIS–PROMETHEE II | 0,945 | 0,855 | 0,942 | 0,906 |
| **Kendall W** | **0,966** | χ²(10) = 28,97 | p = 0,0013 | — |

Linha de base aleatória (100 mil sorteios de rankings de 11 itens, percentil 95): ρ = 0,53, WS = 0,80, W = 0,55.

Os valores estão muito acima da linha de base. Mas isso confirma a circularidade do desenho, não a robustez metodológica. A concordância seria esperada mesmo que os métodos fossem matematicamente idênticos.

### 3.4 O que o experimento ainda demonstra, corretamente

Apesar da circularidade, o experimento demonstra legitimamente:
- Que os três métodos, **mesmo com o mesmo input**, produzem rankings não idênticos (a taxa de posições idênticas não é 100%).
- Que as discrepâncias existentes (x9 em 7º vs. 6º, x11 em 6º vs. 7º) são devidas às diferenças de paradigma matemático entre os métodos.
- Que as propriedades operacionais dos métodos (complexidade, laboriosidade, suporte a software) diferem e podem guiar a escolha em contextos práticos.

A contribuição do artigo não é nula — ela é mais modesta do que declarada.

---

## 4. Erros Factuais no Artigo

### 4.1 "40 thousand tons per day" para Belém e RM
**Erro quase certamente.** São Paulo, a maior cidade do Brasil, gera ~20 mil toneladas/dia. Belém e região metropolitana gerarem o dobro é implausível. O dado de Brito et al. (2020) é provavelmente 40 mil toneladas/mês ou toneladas/ano. **Verificar na fonte antes de corrigir.**

### 4.2 7 ou 9 critérios?
O texto da Seção 3.2 afirma que "more than seven criteria lead to an increase in inconsistency" (citando Saaty & Ozdemir, 2003). A Tabela 6 registra "A threshold of nine (9) is recommended". São valores diferentes e inconsistentes. Saaty & Ozdemir (2003) discutem 7±2, ou seja, o limite razoável é entre 5 e 9. O artigo deve apresentar o valor correto de forma consistente.

### 4.3 "Raises doubts about the use of AHP" não se sustenta
O artigo afirma que o resultado desigual do AHP em comparação com TOPSIS "raises doubts about the use of the AHP method when there are more than nine criteria to be analyzed". Porém, o experimento usa exatamente 11 critérios e o CR calculado é 0,057 — bem dentro do limite aceitável de 0,10. Não há evidência de inconsistência neste experimento específico. A conclusão é uma generalização não sustentada pelos dados.

### 4.4 Complexidade "Low" para o AHP é contraditória
O texto descreve o AHP como exigindo compreensão de autovalores e autovetores, o que não é "baixa complexidade" por qualquer padrão razoável. Além disso, a Equação 2 apresentada no artigo é a aproximação por média das colunas normalizadas — uma heurística computacionalmente simples, não o cálculo do autovetor. O artigo deve ou (a) apresentar o autovetor como o método correto e reconhecer a complexidade, ou (b) apresentar a aproximação claramente como aproximação.

### 4.5 Fonte incorreta na Tabela 1
A Tabela 1 (pairwise comparison matrix) atribui a fonte a Costa et al. (2020), mas os dados são de Andrade e Barbosa (2015). Costa (2020) apenas reusa os critérios. A fonte correta é Andrade e Barbosa (2015).

### 4.6 x₄ e x₁₀ como "menos importantes": interpretação problemática
Área Protegida (x₄) e Poços/Furos (x₁₀) são tipicamente tratados na literatura como **restrições de exclusão** — áreas onde a construção de aterro é proibida, independentemente de outros critérios. Chamá-los de "menos importantes" pode ser lido como "não é tão importante estar longe de áreas protegidas", o que é uma interpretação potencialmente problemática. O artigo deve discutir a diferença entre critérios de classificação e restrições absolutas.

---

## 5. Erros Técnicos Nesta Análise (v1) — Corrigidos

### 5.1 Fórmula de r_w (Weighted Spearman)
A v1 apresentou a fórmula de rw com uma autocorreção no meio do texto, o que é um erro de edição grave. Além disso, a "versão corrigida" apresentada na v1 é outra fórmula incorreta que produziria valores de 0,993–0,996 para todos os pares, tornando o coeficiente inútil para distinguir concordâncias.

**A fórmula correta** é de Pinto da Costa & Soares (2005):

$$r_w = 1 - \frac{6 \sum_{i=1}^{n} (x_i - y_i)^2 \left[(N - x_i + 1) + (N - y_i + 1)\right]}{N^4 + N^3 - N^2 - N}$$

onde $x_i$ e $y_i$ são as posições do critério $i$ nos rankings comparados e $N = 11$.

Com esta fórmula, os valores calculados são: AHP–TOPSIS = 0,921, AHP–PROMETHEE = 0,955, TOPSIS–PROMETHEE = 0,942.

**Referência:** Pinto da Costa, J. F., & Soares, R. (2005). A weighted rank correlation coefficient. *Statistical Methodology*, 2(1), 25–35.

### 5.2 "Sałabun et al. (2020) — JÁ NO ARTIGO"
A nota na v1 dizia que Sałabun et al. (2020) *Symmetry* já estava no artigo. Isso é parcialmente correto: o artigo **cita** Sałabun et al. (2020) *Symmetry* 12:1549 na comparação de métodos. Mas não cita e não aplica os coeficientes de benchmarking descritos nesse artigo. E **não cita** Sałabun & Urbaniak (2020) *ICCS*, que introduz o WS coefficient. A distinção importa.

### 5.3 Graus de liberdade
A v1 mencionou "n = 11 graus de liberdade" incorretamente. Os valores corretos:
- Teste t para Spearman ρ: n − 2 = 9 graus de liberdade.
- Qui-quadrado para Kendall W: n − 1 = 10 graus de liberdade (confirmado: χ²(10) = 28,97).
- Para n = 11 critérios, testes de permutação são preferíveis a aproximações assintóticas.

### 5.4 Rank reversal no PROMETHEE II
A v1 afirmou que PROMETHEE II é "mais estável" ao rank reversal. Isso está errado. PROMETHEE II também é suscetível a inversões de ranking quando alternativas são adicionadas ou removidas. Mareschal et al. (2008) documentam isso. A afirmação foi removida.

### 5.5 Scores de publicabilidade numéricos
Os valores "35/100", "55/100", "70/100", "80/100" não têm metodologia definida. São estimativas qualitativas, não métricas. Foram removidos desta versão.

### 5.6 DOIs de referências 2025–2026
Os DOIs de Güler (2026), Rekkal et al. (2026), ElMarkaby & Elyamany (2026), Putro et al. (2025) e Lassey (2025) foram obtidos via Crossref mas não foram verificados independentemente. Devem ser conferidos antes de qualquer uso em submissão.

---

## 6. Lacunas Identificadas (mantidas, com correções)

### 6.1 Lacuna estrutural: o desenho experimental não compara métodos independentes
Esta é agora a lacuna principal. As demais lacunas técnicas (coeficientes formais, sensibilidade) só fazem sentido depois que o desenho for resolvido. Ver Fase 0 no plano de melhoria.

### 6.2 Avaliação matemática da consistência entre rankings
Mesmo com o desenho atual, a Tabela 5 (posições idênticas) deve ser substituída pelos coeficientes formais calculados. Os valores verificados independentemente estão na Seção 3.2 acima.

### 6.3 Ausência de análise de sensibilidade com sentido
No desenho atual, a "sensibilidade dos pesos" no AHP é circular: mudar os pesos é mudar a resposta do AHP por definição. A análise de sensibilidade só faz sentido após a Fase 0.

### 6.4 Apenas três métodos
Com o desenho atual, adicionar VIKOR e SAW acrescenta pouco: SAW vai reproduzir o AHP pela propriedade do autovetor. Esta expansão só tem valor após a Fase 0.

---

## 7. Avaliação da Publicabilidade

| Dimensão | Avaliação |
|---|---|
| Problema abordado | Relevante e bem motivado |
| Revisão de literatura | Adequada para o nível do trabalho |
| Metodologia declarada | Tecnicamente correta, mas o desenho experimental tem problema estrutural |
| Validade das conclusões | Limitada pela circularidade do desenho |
| Erros factuais | Três a quatro erros verificados (tonelagem, critérios, fonte da tabela) |
| Escrita e organização | Clara e bem estruturada |

O artigo na versão atual não seria aceito em periódico indexado. O problema não é a execução técnica — os cálculos estão corretos — mas o que o experimento pode e não pode concluir. A corrreção principal é reconhecer a circularidade como limitação e reformular as conclusões; ou reprojetar o experimento (Fase 0).

---

## 8. Referências desta Análise

- Pinto da Costa, J. F., & Soares, R. (2005). A weighted rank correlation coefficient. *Statistical Methodology*, 2(1), 25–35.
- Mareschal, B., De Smet, Y., & Nemery, P. (2008). Rank reversal in the PROMETHEE II method: some new results. In *2008 IEEE International Conference on Industrial Engineering and Engineering Management*, pp. 959–963. https://doi.org/10.1109/IEEM.2008.4737980
- Sałabun, W., & Urbaniak, K. (2020). A New Coefficient of Rankings Similarity in Decision-Making Problems. In *ICCS 2020*, LNCS 12138, pp. 632–645. https://doi.org/10.1007/978-3-030-50417-5_47
- Sałabun, W., Wątróbski, J., & Shekhovtsov, A. (2020). Are MCDA methods benchmarkable? *Symmetry*, 12(9), 1549. https://doi.org/10.3390/sym12091549
- Saaty, T. L., & Ozdemir, M. S. (2003). Why the magic number seven plus or minus two. *Mathematical and Computer Modelling*, 38(3–4), 233–244.
