# TASKS — Plano de melhorias artigo MCDM Fogo/Omega
Criado: 2026-10-01 | Sequência: Bloco 4 → 1 → 3 → 2 → submissão

---

## Bloco 4 — Framing analítico vs empírico (Semana 1 — meio dia)

- [ ] **4.1** Abstract: adicionar "on this instance" em cada afirmação empírica (25.4pp, 35.8pp, 43.2pp, −10.2pp)
- [ ] **4.2** Intro §1: separar frases analíticas ("exact assembly is guaranteed…") das empíricas ("in our data, normalisation is worth…")
- [ ] **4.3** Conclusão §8: auditar parágrafo a parágrafo — analítico vs empírico. Remover qualificadores das frases analíticas (não precisam de "in our data").

---

## Bloco 1 — Circularidade do benchmark F8 (Semana 1 — 1 dia)

- [ ] **1.1** Ler compute_f8_circularity.py e confirmar os 4 valores: `FEightVecOptQ=100.0`, `FEightMMOptQ=94.4`, `FEightVecGrdQ=100.0`, `FEightMMGrdQ=72.4`
- [ ] **1.2** Escrever subsecção `\subsection{Benchmark circularity and robustness}` (~150 palavras) na Discussão com:
  - Justificação de por que min-max para os objectivos não é uma escolha circular (os objectivos físicos existem antes da normalização)
  - Tabela ou frase com os 4 valores F8
  - Frase final: "the ranking of normalisations is preserved under the alternative frontier, consistent with Proposition 1"
- [ ] **1.3** Adicionar macros F8 ao main.tex preamble (ou confirmar que já estão em macros.tex)
- [ ] **1.4** Compilar e verificar que a subsecção não cria overfull ou referências quebradas

---

## Bloco 3 — Pacote de reprodução público (Semana 2 — 2-3 dias)

- [x] **3.1** Criar repositório GitHub público `mcdm-landfill-pareto-replication` — https://github.com/Jazancort/mcdm-landfill-pareto-replication (2026-10-19)
- [x] **3.2** Incluir no repo:
  - `scripts/run_e1_v3.py` (experimento E1 principal)
  - `scripts/generate_macros.py` (gera macros_auto.tex)
  - `scripts/verify_macros_permanent.py` (ALL CHECKS PASSED — hash 813030ffd9520c2d)
  - `corpus/PRESPEC_E1.md`
  - `data/e1_v3_rerun_20261002.log`
  - `results/fourthcell/mc_2cube_fixed_raw.csv`
  - `README.md` com 3 passos: clone → uv pip install → verify
- [ ] **3.3** Testar que `uv run python scripts/run_e1_v3.py` reproduz os resultados do artigo a partir de um clone limpo (requer MCDM_DATA_DIR com dados GIS)
- [x] **3.4** Tag `v1.0` no GitHub → **AGUARDA**: ativar webhook Zenodo em zenodo.org → DOI automático
- [x] **3.5** Seção "Code availability" adicionada ao main.tex (linha ~2887): `\url{https://github.com/...}` + placeholder `ZENODO-DOI-AQUI` para substituir após webhook
- [ ] **3.6** Após Zenodo: substituir `ZENODO-DOI-AQUI` em main.tex pelo DOI real; recompilar 4-pass

---

## Bloco 2 — Generalização: instâncias externas (Semanas 3-5 — 1-2 semanas)

### 2A — Identificar instâncias (Semana 3)

- [ ] **2.1** Confirmar se Fathalizadeh et al. (2020) publicam coordenadas + critérios + pesos: buscar no PDF/suplementar
- [ ] **2.2** Confirmar se Yal & Akgün (2014) publicam coordenadas + critérios + pesos: buscar no PDF/suplementar
- [ ] **2.3** Confirmar se Siddiqui et al. (1996) têm dados reprodutíveis
- [ ] **2.4** Para cada instância encontrada: verificar se tem ≥ 10 candidatos e ≥ 3 critérios (fronteira exacta computável)
- [ ] **2.5** Se nenhuma das 3 tiver dados suficientes, identificar 1-2 alternativas na revisão de Rezaeisabzevar2020

### 2B — Implementar e correr (Semana 4)

- [ ] **2.6** Escrever `scripts/run_external_instances.py` usando pareto_utils.py
  - Entrada: coordenadas, critérios, pesos em CSV
  - Saída: TV, Q2_greedy, Q2_optimal para cada combinação método × normalização
- [ ] **2.7** Correr para cada instância confirmada na Athena
- [ ] **2.8** Asserção de regressão: SAW/mm/optimal = 100% em cada instância (Proposição 1)

### 2C — Integrar no artigo (Semana 5)

- [ ] **2.9** Criar tabela de generalização: Fogo + instâncias externas × {TV, Q2_greedy, Q2_optimal}
- [ ] **2.10** Escrever parágrafo na Discussão: "On two independent instances from the siting literature, the ordering of normalisations by Q2 is consistent with the prediction of the amplitude identity…"
- [ ] **2.11** Adicionar na Limitações: as instâncias externas são pequenas (≤ 50 candidatos); o efeito de magnitude pode depender do tamanho do conjunto

---

## Bloco E6 — Generalização sintética (paralelo às Semanas 3-4)

- [ ] **E6.1** Aguardar conclusão do E6 na Athena (45 instâncias × 5 condições M/B/W/C/V)
- [ ] **E6.2** Verificar P1 (Proposição 1): 100% em M e B em todas as 45 instâncias
- [ ] **E6.3** Verificar que a decomposição between/within se mantém em instâncias com diferentes amplitudes
- [ ] **E6.4** Criar tab:e6 ou figura de dispersão TV vs Q2_optimal (45 instâncias)
- [ ] **E6.5** Integrar na secção de resultados como "external validity: synthetic instances"

---

## Semana 6 — Revisão final e submissão

- [ ] **Sub.1** Executar `make check` (xelatex ×4 + bibtex): 0 erros, 0 citações indefinidas
- [ ] **Sub.2** Verificar contagem de palavras do abstract: 150–250 palavras
- [ ] **Sub.3** Correr `scripts/verify_macros_permanent.py` — confirmar hash esperado
- [ ] **Sub.4** Verificar todas as tabelas contra CSV: nenhum número escrito à mão sem assert
- [ ] **Sub.5** Confirmar que o DOI do pacote de reprodução está no artigo
- [ ] **Sub.6** Confirmar que não há `\MechOnePredAdmiss`, `\MismatchRatioHi` ou outras macros removidas no texto (check_consistency.py)
- [ ] **Sub.7** Submeter à Omega via Editorial Manager

---

## Dependências

```
4.1-4.3 (independentes, fazer primeiro)
    ↓
1.1-1.4 (requer F8 verificado)
    ↓
3.1-3.6 (requer macros estáveis)
    ↓
2.1-2.5 → 2.6-2.8 → 2.9-2.11
              ↑
           E6.1-E6.5 (paralelo)
                    ↓
               Sub.1-Sub.7
```

---

## Estado actual dos experimentos

| Experimento | Estado | Resultado chave |
|---|---|---|
| E1 (intervenção amplitudes) | Completo | B=100%, W=64.2%, V=56.8% |
| E3 (grid power-law) | Completo (Q2_opt=100% todas) | Bug: score e obj usam Aj |
| E4 (ref-set decomposição) | Completo | R-V*=100%, R-asp=24% |
| E6 (45 instâncias ×5 cond.) | A correr | — |
| F8 (circularidade benchmark) | Script feito, não no texto | Vec-opt=100%, MM-opt=94.4% |
| Instâncias externas reais | Por iniciar | — |
