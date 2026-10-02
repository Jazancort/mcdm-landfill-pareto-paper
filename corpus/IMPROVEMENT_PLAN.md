# Plano de melhoria do manuscrito — do estado actual à submissão

**Registado em:** 2026-10-01T23:01 UTC-3  
**Estado do repositório ao registar:** commit `9235e63` (audit E4 final)  
**Caminho crítico:** A → B → C → D → G → H (~7–9 sessões até manuscrito submetível)

---

## 1. Diagnóstico

### 1.1 Sólido — não alterar

| Componente | Estado | Base |
|------------|--------|------|
| Identidade de amplitude w_j^eff ∝ w_j A_j | [verificado] | Álgebra directa |
| Teorema thm:groupconst (sse) | [verificado] | Prova iff revista; contra-exemplo fixa amplitudes com sítios extremos |
| Proposição 1 e célula de regressão = 100% | [verificado] | Reproduzida em factorial, E1 e E4 (R-M, R-B, R-B') |
| Factorial 2³ em A' | [verificado] | Usa X_adj_dm, aspect binário |
| E1 (M/B/W/V) | [verificado] | Mesma base; P1 confirmada, P2 e P3 falsificadas |
| Factorização TV / m_eff | [verificado] | Álgebra |
| Reprodutibilidade (macros, check, DEVs) | [verificado] | 45+ verificações passam |

### 1.2 Comprometido

| # | Problema | Gravidade | Estado |
|---|----------|-----------|--------|
| D1 | 80 pp da célula 473/A' vêm da codificação de aspect (contínua no score, binária no avaliador), não do conjunto de referência | Crítica | [verificado]: R-V*=100%, R-asp=24% |
| D2 | O espaço A (tab:canonical, 389/A=95%, \FAsize, \FAinter, reprodução {184,430,460}) pode usar a mesma codificação contínua | Crítica | [a verificar] |
| D3 | Cinco passagens do manuscrito afirmam "Mechanism 2", assimetria de 16× e "80 pp" | Crítica | [verificado] — já corrigidas em commit 9235e63 |
| D4 | Contraste de agregação +0,6 pp é média de estratos com sinais opostos: −8,4, +3,4, +2,8, +4,4. Sem célula fixa: −0,4 | Alta | [verificado] a partir de tab:factorial |
| D5 | Sinal da identidade PROMETHEE: derivação dá φ=−(n+1)/(n−1)+(2/(n−1))Σw_j r_j, contrário da eq. impressa. Pode ser convenção de postos | Média | álgebra [verificado]; convenção no código [a verificar] |
| D6 | Midrank de perm: se 350 zeros no topo → [0,003;0,550]; se na base → [0,450;0,997]. Amplitude = 0,547 em ambos os casos. Texto tem de corresponder à orientação implementada | Baixa | [a verificar] no código |
| D7 | Texto cita eq:Arank_binary para perm, que não é binário | Baixa | [verificado] |
| D8 | Circularidade: objectivos construídos em min–max, por isso "min–max ganha" mede proximidade ao modelo de valor, não superioridade absoluta. Texto não o diz | Alta | [verificado] |
| D9 | Q3 definido mas não reportado | Média | [verificado] |
| D10 | Pré-registo E4 alterado depois de vistos resultados (v1–v5) | Alta | [verificado] — documentado em DEV-E4-007 |
| D11 | Instância única | Alta | [verificado], tecto de nota |
| D12 | Resumo com ~280 palavras | Baixa | [a verificar] contagem exacta |

**Adicionado por revisão externa (2026-10-01):**

| # | Problema | Gravidade |
|---|----------|-----------|
| D13 | Definição de gap não satisfaz "gap=0 sse Pareto" — mínimo de melhorias = 0 quando um concorrente empata F2 e F3 mas melhora F1. Afecta Q3=0 ⟺ Q2=1 | Alta |
| D14 | Secção PROMETHEE precisa mais do que inverter o sinal: (a) verificar posto maior = melhor no código; (b) dividir por N+1 não destrói equivalência — a frase que atribui divergência empírica a essa divisão sozinha está errada; (c) a comparação "diferença à precisão de máquina" omite a constante afim | Média |
| D15 | "Proposição do expoente" excede o que demonstra para TOPSIS (w_j²A_j² ≠ vector de pesos efectivos do índice TOPSIS) e PROMETHEE (α=0 não pode significar w_j^0). Restringir a SAW; apresentar as outras como propriedades distintas com alcance explícito | Média |
| D16 | "Peso efectivo" = "quota da variação total do score" é enganador; amplitudes máximas por coluna não são quotas de variação observada | Baixa |

### 1.3 Causa de fundo

D1, D2, D3 e D10 têm a mesma origem: matrizes de score e de objectivos construídas em funções diferentes, com explicações adicionadas ao manuscrito antes de existirem números. As Fases A e B atacam estas duas causas.

D13, D14, D15 exigem uma **Fase Math preliminar** antes da Fase A: corrigir definições e provas para que o pipeline possa ser reproduzível sem reproduzir afirmações falsas.

---

## 2. Regras de execução (válidas para todas as fases)

1. **Rastreabilidade.** Cada número do manuscrito vem de uma macro; cada macro de um script em commit. Proibido escrever números à mão na prosa (excepto constantes de definição como 3 ou 10 km).
2. **Separar confirmatório de exploratório.** Uma análise só é confirmatória se a regra de decisão estiver em commit antes de a análise correr.
3. **Uma função por transformação.** A codificação, orientação e normalização de cada critério são feitas por uma única função, usada tanto pelo score como pelo avaliador.
4. **Resultados por draw.** Nenhum contraste é reportado sem IC bootstrap emparelhado.
5. **Explicação só depois do número.** O manuscrito só recebe uma explicação de mecanismo depois de existir uma medida que a sustente.
6. **Uma alteração estrutural por commit.** A mensagem indica o que muda no manuscrito e qual o script que o justifica.

---

## 3. Fases

### Fase Math (nova — preliminar a tudo)

**Objectivo:** corrigir definições e provas antes de refactorizar o código.

| Tarefa | Acção |
|--------|-------|
| D13: gap | Redefinir gap de forma que gap=0 sse dominado. Verificar Q3=0⟺Q2=1 por script antes de afirmar |
| D14: PROMETHEE | Verificar convenção de postos no código. Corrigir sinal ou declarar convenção. Verificar a comparação "à precisão de máquina" incluindo a constante afim |
| D15: proposição expoente | Restringir a SAW. Reformular TOPSIS e PROMETHEE como propriedades distintas com alcance explícito |
| D16: "quota da variação" | Substituir por "peso ponderado pela amplitude" |

Critério: as quatro definições/provas estão correctas antes de qualquer commit de código.

### Fase A — Infra-estrutura (após Fase Math, ~1 sessão)

**Objectivo:** tornar impossível que score e avaliador codifiquem um critério de forma diferente.

1. Criar `scripts/encoding.py` com função canónica `encode_criteria(df, ref_df)` — única fonte de verdade para codificação, orientação, min-max.
2. Todos os construtores de score e objectivos chamam `encode_criteria`. A única variação é `ref_df`.
3. Asserções em cada construtor: `assert set(np.unique(C[:,J_ASPECT])) <= {0.0,1.0}`.
4. Criar `tests/test_encoding.py` — falha no commit `efdc9d8`, passa com o código novo.
5. Scripts de Monte Carlo gravam `results/<exp>_perdraw.parquet` (kappa, draw, cell, assembly, in_frontier, gap).
6. Cada corrida grava `results/<exp>_meta.json` (git HEAD, git status, hash de pesos, Python, numpy, host).
7. Reconciliar Athena com main. A partir daqui, nenhuma corrida usa ficheiros copiados por SCP.

**Critério:** `grep -n "aspect" scripts/*.py` só encontra ocorrências em `encoding.py` e nas asserções. Teste passa no main e falha em `efdc9d8`. Corrida de fumo (50 draws) produz ficheiro por draw e metadados.

### Fase B — Auditoria de proveniência (~1 sessão, só leitura)

**Objectivo:** saber exactamente que números estão contaminados antes de recalcular.

Gerar `docs/provenance.csv` com colunas:

```
numero_no_artigo | macro/tabela | script | função_score | função_objs | aspect_score | aspect_obj | ref_score | ref_obj | contaminado?
```

Cobrir: tab:canonical (7 linhas), "6 de 7 não dominados em A'", reprodução {184,430,460}, \FAsize, \FAinter, quatro células de tab:fourthcell, tab:amprefset, fig:pareto, fig:map.

Verificar no código: convenção de ordenação por postos (D5); orientação de perm (D6); codificação de aspect no estudo-fonte AzancortNeto2026.

**Critério:** todas as tabelas e figuras com números têm uma linha. Nenhuma célula fica como "desconhecido".

### Fase C — Pré-registo do recálculo (~0,5 sessão)

**Objectivo:** fixar regras de decisão antes de ver os números novos.

Criar `corpus/PRESPEC_R1.md` com commit antes da Fase D:

| ID | Estimando | Regra de decisão |
|----|-----------|-----------------|
| R1-1 | Δ_ref,opt = Q2[473/A'] − Q2[389/A'], óptimo, κ=200 | Efeito se IC 95% exclui 0 e \|Δ\| ≥ 2,5 pp |
| R1-2 | O mesmo, montagem greedy | Mesma regra; sinal reportado tal como sair |
| R1-3 | Quatro células tab:fourthcell com codificação única | Regressão: diagonais = 100% óptimo. Falha → abortar Fase D |
| R1-4 | Se Fase B marca tab:canonical como contaminada: recalcular 7 linhas | Substituir na tabela |
| R1-5 | R-asp (codificação contínua) vs R-M | Descritivo; experiência post hoc deliberada |
| R1-6 | Resíduo R-V − R-asp | Mesma regra de R1-1; expectativa declarada: "não distinguível de zero" |

Declarar também: κ∈{50,200}, κ=200 primário; 500 draws de `e1_weights_k200.npy` (hash bea05275); 2000 réplicas bootstrap emparelhadas; semente fixa.

**Critério:** commit de PRESPEC_R1 com data anterior ao primeiro output da Fase D.

### Fase D — Recálculo confirmatório (~1–2 sessões)

1. Correr `run_r1.py` a partir de commit limpo, com metadados.
2. `analyze_r1.py`: Q2, Q3, SE, IC emparelhado, decisão automática → `results/r1/r1_decisions.json`.
3. `generate_macros.py`: regenerar macros a partir dos resultados.
4. Se R1-4 se aplicar: regenerar fig:pareto e fig:map com codificação única.

**Critério:** R1-3 passa; decisões saem do script, não de leitura humana.

### Fase E — Diagnósticos exploratórios (~1 sessão, após D)

| Pergunta | Medida | Onde entra |
|----------|--------|-----------|
| Porque é que greedy sobe para ~97,8% com amplitudes r_j? | W_g^eff para r_j; proporção de draws com greedy=óptimo | Suplementar |
| A direcção da distorção importa (r_j=0pp, 1/r_j=11,6pp)? | TV_B e TV_W para os dois padrões | Exploratório em §8 ou Limitações |
| Perda de R-asp deve-se à não-monotonia? | Spearman(azimute normalizado, indicador); proporção de sítios com valor alto e indicador=0 | Remark "consistent with" |
| Amplificação W×B do E1 (P2 falsificada) | Variar W_G1 com padrão interno fixo | Se houver tempo; candidata a segundo resultado teórico |

Actualizar DEV-E4-007: v1–v5 corridas e resultados vistos; outputs em `results/e4/`; P_E4_3 "falhado como especificado, pouco informativo"; P_E4_5 exploratório.

### Fase F — Correcções independentes (em paralelo com A–E, ~1 sessão)

| # | Correcção | Acção |
|---|-----------|-------|
| F1 | Agregação por estrato (D4) | Nova tabela SAW−TOPSIS por estrato + IC; contraste sem célula fixa; highlight: "no consistent effect: sign depends on cell" |
| F2 | Circularidade do min–max (D8) | Parágrafo em §5 e nas Limitações |
| F3 | Q3 (D9) | Coluna de Q3 em tab:factorial e tab:e1 |
| F4 | Sinal PROMETHEE (D5) | Declarar convenção ou corrigir sinal, conforme código (Fase B) |
| F5 | perm em postos (D6, D7) | Escrever intervalo conforme orientação implementada; deixar de citar eq:Arank_binary para perm |
| F6 | Resumo ≤250 palavras (D12) | Cortar frase dos 80 pp (Fase G) + condensar |
| F7 | Cabeçalho, contagem de proposições | Actualizar |

### Fase G — Reescrita do manuscrito (~2 sessões, após D, E, F)

**G1.** Decidir o destino do terceiro resultado com base em `r1_decisions.json` (árvore de decisão, §4).

**G2.** Mapa de reescrita:

| Secção | Acção |
|--------|-------|
| Resumo | Retirar "costs up to 80 pp". Se R1-1="efeito", substituir pelo número novo. Corrigir a frase da agregação (F1) |
| Highlights | Retirar ou substituir o 5.º. Reformular o 2.º (agregação) |
| Introdução | Reescrever "third finding"; contribuição (i) deixa de listar amplitude loss como efeito com custo |
| §3 Problema | Corrigir "Mixed senses": todas as matrizes usam a mesma codificação |
| §5 Desenho | Acrescentar circularidade (F2); conjunto de referência passa a factor secundário |
| §6 | Corrigir F4 e F5. Manter eq:refsetA e tab:amprefset |
| sec:refset | Reescrever: tab:fourthcell com valores consistentes; sai Mechanism 2 |
| Nova Remark | "A non-monotone recoding": R-asp 24%, mensagem "exact assembly amplifies any score–value-model mismatch". Historial do bug no Suplementar |
| sec:interaction | Manter, com o factor 1,56× dentro de G₁ como macro |
| §8.1 | Reescrever: um mecanismo com duas origens; sai factor 16 e sai "unexplained" |
| §8.5 Prática | Rec. 1: "report the reference set; both choices re-weight, direction is instance-dependent". Rec. 3 nova: "use one encoding function for score and value model" |
| Limitações | Acrescentar circularidade, instância única, carácter exploratório E4 |
| Conclusão | Retirar 80 pp e assimetria; alinhar com resumo |
| Suplementar | PRESPEC_E4 DEV-001..007, PRESPEC_R1, historial v1–v6, tabela de proveniência |

**G3.** Regras novas em `check_consistency.py`:
- Macros proibidas: `\MismatchRatioHi`, `\MismatchRatioLo`, `\MechOnePredAdmiss`, `\MechOneShare` (já adicionadas).
- Frases proibidas: "unexplained" a menos de 200 chars de "asymmetr", "Mechanism~2", "more severe mechanism", "re-weighting alone predicts", "equivalent to zero" (salvo F1).
- Nenhum número `\d+\.\d~pp` na prosa sem macro (regex, fora de tabelas).
- `tests/test_encoding.py` corre dentro do `make check`.
- Todas as macros usadas existem em `macros.tex`; todas as macros em `macros.tex` são usadas.

### Fase H — Revisão interna (~1 sessão, após G)

1. Leitura a frio do PDF inteiro 24h depois da reescrita; anotar afirmações sem número ou sem referência.
2. Simular três objecções de revisor EJOR/Omega (circularidade, instância única, agregação) e confirmar resposta no texto.
3. Matriz afirmação → evidência: cada frase do resumo e cada highlight aponta para tabela, macro ou teorema.
4. Tabela de proveniência final = estado do PDF.

### Fase I — Generalização (longo prazo)

| Opção | Custo | Ganho | Recomendação |
|-------|-------|-------|--------------|
| I1. Corpus de matrizes publicadas (já existe corpus_amplitudes.csv) | Médio | Responde a "joint distribution unknown" | Primeira escolha |
| I2. Instâncias sintéticas calibradas | Médio–alto | Testa Teorema fora do Fogo | Segunda escolha |
| I3. Segunda instância real | Alto (dados) | Maior ganho junto de revisores | Depois de I1 |

Cada opção: PRESPEC_I* próprio, mesmo pipeline (encoding.py), mesma gravação por draw.

---

## 4. Árvore de decisão para o terceiro resultado (aplicar após Fase D)

```
R1-3 (diagonais = 100% óptimo) falha?
├─ sim → ABORTAR; bug no pipeline novo; voltar à Fase A
└─ não → avaliar R1-1 (óptimo) e R1-2 (greedy)
     ├─ ambos "observação" (IC inclui 0 ou |Δ|<2,5pp)
     │    → retirar ref-set das contribuições;
     │      uma frase em sec:refset + Remark de recodificação;
     │      prática 1 = "reporte o conjunto usado"
     ├─ só R1-2 é "efeito" (greedy)
     │    → reportar como efeito do greedy, com direcção medida;
     │      explicação só se Fase E a sustentar
     └─ R1-1 é "efeito" (óptimo)
          → manter como resultado secundário com número novo;
            ligar ao Teorema via TV_W calculado (não por narrativa)

Fase B marcou espaço A como contaminado?
├─ sim, e AzancortNeto2026 usava aspect contínuo
│    → reprodução mantém-se, declarando a codificação;
│      análises comparativas passam a usar codificação única
└─ sim, e AzancortNeto2026 usava aspect binário
     → "reprodução exacta" estava errada; recalcular e corrigir frase

Contingência: se espaço A gerar > 2 correcções em cascata,
retirar do texto principal e manter só no Suplementar.
```

---

## 5. Métricas de sucesso

| Métrica | Alvo | Como se mede |
|---------|------|-------------|
| Números rastreáveis | 100% vêm de macros geradas por scripts | provenance.csv + regex no check |
| Codificação única | 0 transformações de aspect fora de encoding.py | grep + teste |
| Contrastes com IC emparelhado | 100% | analyze_*.py |
| Afirmações exploratórias marcadas | 100% | Revisão Fase H |
| Contradições internas | 0 | Leitura a frio + frases proibidas no check |
| make check | Exit 0, 55+ asserções | CI local |
| Compilação | 0 "Undefined", 0 "??", 0 "Repeated entry" | Log |
| Resumo | ≤ 250 palavras | texcount |
| Pré-registos | Commit de PRESPEC anterior ao primeiro output | git log vs meta.json |

---

## 6. Registo de riscos

| Risco | Sinal | Prevenção | Contingência |
|-------|-------|-----------|--------------|
| Explicações sem número no texto | Frase com "because" sem macro nem tabela | Regra 5 + Fase H | Reescrever como "consistent with" ou cortar |
| Bug de codificação noutro critério | Regressão diagonal < 100% | Alargar asserções a todos os critérios | Abortar Fase D; auditar coluna a coluna |
| Rever critérios de decisão depois de ver números | Commit PRESPEC posterior ao meta.json | Check de datas | Declarar como DEV; tratar como exploratório |
| Espaço A contaminado em cascata | >2 tabelas afectadas na Fase B | Árvore da §4 | Espaço A para o Suplementar |
| Divergência Athena vs repositório | git status não vazio no meta.json | Script aborta se houver alterações | Repetir a corrida |
| Agregação deixar de ser "equivalente" | F1 mostrar estrato significativo | Reformular honestamente | Mensagem principal mantém-se se +25,4 > todos os estratos |
| Âmbito a crescer | Fase E com >4 diagnósticos | Limitar a 4; resto = "future work" | Cortar |
| Fadiga em edições grandes do .tex | Diff >150 linhas num commit | Um commit por secção (Regra 6) | git revert da secção |

---

## 7. Cronograma e dependências

| Ordem | Fase | Depende de | Esforço |
|-------|------|-----------|---------|
| 0 | Math (D13–D16) | — | 0,5–1 sessão |
| 1 | A (infra-estrutura) + F2, F4, F5, F7 | Math | 1–1,5 sessões |
| 2 | B (proveniência) | A | 1 sessão |
| 3 | C (PRESPEC_R1) | B | 0,5 sessão |
| 4 | D (recálculo) + F1, F3 | C | 1–2 sessões |
| 5 | E (exploratório) | D | 1 sessão |
| 6 | G (reescrita) | D, E, F | 2 sessões |
| 7 | H (revisão interna) | G | 1 sessão |
| 8 | I (generalização) | H | Várias sessões |

**Total até submissão (sem I):** 7,5–10 sessões.  
**Nota esperada:** ~8,0 com A–H; 8,5–9,0 com I.

---

## 8. Primeiro passo concreto

1. Criar `scripts/encoding.py` e `tests/test_encoding.py` (Fase A, tarefas 1–3).
2. Na mesma sessão, gerar primeira versão de `docs/provenance.csv` para tab:canonical e tab:fourthcell (Fase B, parcial).
3. Commit de ambos **antes** de abrir o `main.tex`.

**Nota de ordem:** a revisão externa recomenda começar pela auditoria de proveniência (Fase B) antes da refactorização (Fase A), para não dificultar a reconstrução dos resultados antigos. A Fase Math (D13–D16) tem precedência sobre ambas.
