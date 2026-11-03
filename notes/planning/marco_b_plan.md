# Marco B: o plano para chegar a 9

**Pré-requisito:** Marco A fechado (merge Athena, DEV-E1, make check sem SKIP, frase simetria, tab:canonical).

---

## O que falta para um 9 na Omega

1. **Um teorema de caracterização** ("se e só se"), não apenas condição suficiente.
2. **Uma previsão pré-registada que se confirmou.** O E1 começa. O E3 e o E4 completam.
3. **Uma resposta à objecção "um só caso".**

---

## B1. Teorema de caracterização (prop:groupconst → thm:groupconst)

Retorno mais alto. Hoje: amplitudes constantes dentro do grupo **chegam** para a assembly óptima ficar na fronteira. A recíproca também se prova com dois portfólios. Resultado: assembly exacta é Pareto-consistente em **todas** as instâncias **se e só se** a normalização respeita a partição dos objectivos.

### Bloco LaTeX

```latex
\begin{theorem}[When exact assembly survives normalisation]
\label{thm:groupconst}
Fix weights $w>0$ and a score whose normalised columns are strictly
increasing affine functions of the oriented min--max partial values,
$n_j=b_j+A_j\,\tilde c_j$ with $A_j>0$, and let the objectives
\eqref{eq:F1}--\eqref{eq:F3} be built on min--max with the same
weights. The following are equivalent.
\begin{enumerate}[label=(\roman*),nosep]
  \item For every set of sites and every feasible family $\Tset$ of
    portfolios of size $\kk$,
    $T^{*}=\argmax_{T\in\Tset}\sum_{a\in T}s(a)$ belongs to $\Fset(w)$.
  \item The amplitudes are constant within each objective group:
    $A_j=\bar A_g$ for all $j\in G_g$, $g=1,2,3$.
\end{enumerate}
\end{theorem}

\begin{proof}
(ii)$\Rightarrow$(i).
Summing $s$ over a portfolio of fixed size gives
$\sum_{a\in T}s(a)=C-\bar A_1F_1(T)-\bar A_2F_2(T)+\bar A_3F_3(T)$
with $C$ independent of $T$, a strictly positive scalarisation of the
three objectives in their own senses; the argument of
Proposition~\ref{prop:p1:stmt} applies.

(i)$\Rightarrow$(ii).
Suppose $j,k\in G_g$ with $A_j<A_k$.
Take two sites $a,a'$ that coincide on every criterion except $j$ and
$k$, with oriented differences
$w_j[\tilde c_j(a')-\tilde c_j(a)]=x$ and
$w_k[\tilde c_k(a')-\tilde c_k(a)]=y$, where $y=-\eta<0$ and
$x=\tfrac{\eta}{2}\,(1+A_k/A_j)$, with $\eta>0$ small enough to keep all
partial values in $[0,1]$.
Then $x+y=\tfrac{\eta}{2}(A_k/A_j-1)>0$, so the portfolio $T'$ that
contains $a'$ improves objective $g$ over the portfolio $T$ that
contains $a$ instead, and leaves the other two objectives unchanged:
$T'$ dominates $T$.
Yet $A_jx+A_ky=\tfrac{\eta}{2}(A_j-A_k)<0$, so $T$ has the strictly
higher score.
On the feasible family $\Tset=\{T,T'\}$ exact assembly returns the
dominated portfolio, contradicting (i).
\end{proof}
```

Parágrafo de âmbito (logo a seguir):

```latex
The theorem treats the affine score map as given.
For data-dependent normalisations such as vector normalisation the
amplitudes are themselves computed on the instance, so (i)
$\Rightarrow$ (ii) should be read as: whenever a normalisation produces
amplitudes that vary within a group, there exist configurations of
sites under which exact assembly selects a dominated portfolio.
Section~\ref{sec:e1} shows that Fogo is such a configuration.
```

### O que o agente tem de fazer

1. Trocar `prop:groupconst` por `thm:groupconst` em **todas** as referências.
2. Acrescentar `\newtheorem{theorem}{Theorem}` no preâmbulo.
3. Actualizar o resumo: "We characterise **exactly** when exact assembly survives normalisation: **if and only if** amplitudes are constant within each objective group."
4. Actualizar contribuição (iv): "A **necessary and sufficient** condition…"
5. Retirar "we have not established the converse" da Conclusão e das Limitações.
6. **Pesquisa bibliográfica obrigatória** antes de submeter: escalarização por soma ponderada com reescalamento de objectivos (Marler & Arora 2004, 2010), invariância de Pareto sob transformações afins por objectivo. Cite e diga o que acrescenta.

---

## B2. Fechar o E3 sem reescrever o pré-registo

A corrida já tem os Q₂. Só o preditor TV_W^eff estava errado (dupla ponderação).

**Correcção:** usar a definição do PRESPEC: Σ_g W_g^eff · TV_W,g, com TV_W,g sobre as quotas dentro do grupo.

**Asserções independentes:** (0,1) → 0.199; (1,1) → 0.234. Vectores de amplitude nos cantos iguais aos do E1 até 1e-12.

**DEV-E3-001:** os valores dos cantos no PRESPEC (0.0641 e 0.0723) vinham da função com o bug. A definição escrita mantém-se.

**Avaliação das cinco previsões:**
- P_E3_2, P_E3_3, P_E3_4: não dependem do preditor — avaliar de imediato.
- P_E3_1, P_E3_5: avaliar com o preditor corrigido; reportar também o resultado com o preditor errado (transparência).

**Figura nova para o texto principal:** mapa de calor da perda em óptima sobre (s_B, s_W), com os quatro cantos do E1 marcados. Torna o teorema visível.

**Leituras esperadas:**
- P_E3_2 e P_E3_4 confirmadas: o teorema tem uma curva dose-resposta pré-registada.
- P_E3_3 confirmada: a interacção do E1 passa de um ponto a um efeito replicado.
- Se falharem: reportar tal como sai. O teorema não depende do E3.

---

## B3. E4: o mesmo teorema numa segunda situação

A célula 473/A′ é um score afim nos objectivos com `A_j = range_389(j) / range_473(j)` (tab:amprefset). O teorema aplica-se directamente.

**Consequência forte:** a perda de 80 pp ("Mecanismo 2") deve desaparecer com group-constant amplitudes. Se confirmar: dois "mecanismos" passam a ser um teorema. Se não confirmar: Mecanismo 2 fica bem caracterizado como distinto.

**Verificação prévia:** confirmar no `mc_2cube_fixed.py` que a selecção na célula 473 se faz só entre os 389 sítios admissíveis. Se incluir inadmissíveis, o score deixa de ser afim nos objectivos de A′.

### PRESPEC_E4.md (texto completo)

```markdown
# PRESPEC_E4 — Reference-set mismatch as within-group re-weighting

## Design
Score: SAW, constants over 473 sites, selection over the 389 admissible.
Evaluator: objectives and frontier over A' (389), per draw, pareto_utils,
eps=1e-9, kappa=200, N=1000, seed declared.
Let r_j = range_389(j)/range_473(j) (tab:amprefset). Four cells:
  R-M: A_j = 1                (aligned control; = 389/A')
  R-B: A_j = rbar_g           (w-weighted mean of r_j within group g)
  R-W: A_j ∝ r_j / rbar_g     (group totals equalised)
  R-V: A_j = r_j              (= the published 473/A' cell)
The mirror direction (389 score vs A evaluator) is run with 1/r_j,
same four cells.

## Predictions
P_E4_1 (theorem): R-B optimal Q2 = 100% on every draw, both directions.
        Hard assertion; failure = bug or theorem false.
P_E4_2: R-V optimal reproduces tab:fourthcell (20.0% and 95.0%) within 3 SE.
P_E4_3: R-W optimal loss >= 50% of R-V optimal loss, in the 473→A' direction.
P_E4_4 (exploratory, declared): the 80 vs 5 pp asymmetry persists in R-W.
Unit of analysis: cell, paired bootstrap by draw (2000 replicates).
Inherited: the asymmetry was unexplained by TV, TV_B and TV_W (marco A).
```

---

## B4. Responder à objecção "um só caso"

Por ordem de força:

1. **Uma segunda ilha de Cabo Verde** (Santiago ou Santo Antão): mesmo pipeline SIG, dados abertos (SRTM, OSM, áreas protegidas), mesmos critérios/grupos/pesos AHP. Correr só a 4ª célula, E1 e E4 com asserções de regressão. **Pré-registar antes de calcular a fronteira.** Fecha a objecção.
2. **Uma instância publicada** com coordenadas e tabela de critérios, que permita enumerar os trios.
3. **Mínimo aceitável:** tabela de amplitudes do corpus (TV, TV_B, TV_W em ≥ 7 matrizes publicadas, com grupos das hierarquias originais). Mostra que a distorção dentro dos grupos é comum. Barato mas não substitui 1 ou 2.

---

## B5. Reescrever à volta de uma única tese

**Tese:** A normalização custa eficiência de Pareto exactamente na medida em que distorce os pesos **dentro** dos grupos de objectivos. A assembly exacta amplifica essa distorção; a escolha do operador de agregação vem depois.

**Estrutura:**
1. O teorema (B1)
2. O factorial (normalização domina, assembly sem efeito médio, agregação ≡ 0)
3. E1 e E3 (decomposição e dose-resposta)
4. E4 (conjunto de referência explicado pelo mesmo teorema)
5. Segunda instância

**Para o Suplementar:** PROMETHEE–Borda, expoente para TOPSIS/VIKOR, ordem das operações, detalhes de ranks, grelha sintética antiga.

**Cortar 20–25%:** 23 → ~18 páginas.

**Título proposto:** "When does exact assembly survive normalisation? A characterisation for multi-criteria portfolio selection, with evidence from landfill siting"

**Código e dados:** Zenodo com DOI; `make all` reproduz todas as tabelas a partir dos dados brutos.

---

## Ordem, esforço e nota

| Passo | Esforço | Nota depois |
|-------|---------|-------------|
| Fechar Marco A | ~1 dia | 8.0–8.5 |
| B1: teorema + revisão biblio + texto | 1–2 dias | ~8.7 |
| B2: E3 corrigido + figura | 1 dia (sem nova corrida) | ~8.8 |
| B3: E4 pré-registado + corrida | 2–3 dias | ~9.0 se P_E4_1 confirmar |
| B4: segunda ilha | 1–3 semanas | 9.0 robusto |
| B5: reescrita | 3–4 dias | consolida tudo |

**Caminho mais rápido para 9:** B1 + B3.
- B1 não depende de nenhuma corrida.
- B3 é barato e tem previsão nítida derivada do próprio teorema.
- Com os dois confirmados: caracterização + duas confirmações pré-registadas em situações diferentes.
- B4 (segunda ilha) impede que um revisor exigente traga de volta para 8.5.

---

## Primeira entrega do Marco B (o que o agente entrega na próxima ronda)

1. `git diff main.tex` com o teorema (B1).
2. Commit do `corpus/PRESPEC_E4.md`, com hash e hora, **antes de qualquer corrida**.
3. A linha do `mc_2cube_fixed.py` que define o conjunto de selecção da célula 473.
