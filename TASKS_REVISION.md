# Revision Task List — Reviewer Pass 2

Generated from full PDF audit. Order: §1+§2 (mechanical) → §3 (claims) → §4 (analysis) → §5–7 (notation/structure/refs) → §8 (checker) → §9 (Zenodo).

---

## §1 — Visible errors in PDF (mechanical)

- [x] **1.01** `+ +20.4` / `++20.4` double sign — find `+\` before macro in abstract, intro, Tab.6, §8.5 and fix
- [x] **1.02** §4.1 "Horn algorithm (gdaldem **slope**)" → `gdaldem **aspect**`
- [x] **1.03** §intro p.2 and §8.5 "shrinking/shrink to zero at κ=50" → "not distinguishable from zero at κ=50" (match abstract)
- [x] **1.04** §2.3 "set-dependence effect (Remark 6 and Table 8)" → Remark 7
- [x] **1.05** §8.3 "(Remark 6, cell R-V*)" → Remark 7, Table 8
- [x] **1.06** §3.2 group description "(Table 2)" → Table 1
- [x] **1.07** §5.2 "choice of κ is discussed in Section 5" (circular) → Section 5.1 (sec:design)
- [x] **1.08** §7.5 diagonal cells attributed to "Theorem 1" but Table 7 caption says "Proposition 1" → uniform to Proposition 1
- [x] **1.09** §8.4 "perm's amplitude to 0.616×" — 0.616 is the effective-weight factor; amplitude is **0.547** → fix value
- [x] **1.10** Remark 5 "every other criterion spans [0.003, 0.997]" false for aspect (0.499), urban (0.989), cult (0.981) → "every tie-free continuous criterion"
- [x] **1.11** Contrib. (ii) "frontier attainment reversing sign" — clarify it is the *assembly effect* that reverses sign, not frontier attainment per se
- [x] **1.12** §6.6 Eq.(21) uses `n`; rest of paper uses `N`. Also missing explicit assumption `Σwⱼ=1` → rename to `N`, add hypothesis
- [x] **1.13** §6.7 derivation uses raw `x` while Eq.(22) uses `x̃` → replace `x` with `x̃`
- [ ] **1.14** Title page "ORCID(s):" field is empty → fill `\orcid{0009-0000-2754-8503}` or use cas-dc `[orcid=...]` syntax — **BLOCKED: 0009-0000-2754-8503 fails InvenioRDM check-digit validation; copy correct ORCID from orcid.org/profile and update main.tex line 104, CITATION.cff line 24, and add to .zenodo.json creators[0]**
- [x] **1.15** Saaty 1990 and 2008 in bib but not cited in text (orphans) → add `\citep{Saaty1990,Saaty2008}` in §4.2 for RI=1.51 and CR<0.10 threshold

---

## §2 — κ qualification incomplete (mechanical)

- [x] **$2** Intro p.2 "TOPSIS gains +2.2 pp" — add "(at κ=200)"
- [x] **$2** Intro p.2 "Adding integer programming… improved… under min–max and reduced it under vector" — add "(at κ=200)"
- [x] **$2** Contrib. (ii) "normalisation dominates the choice of aggregation operator" — add "(at both κ tested; at κ=50 aggregation rises to +20.4 pp)"
- [x] **$2** Figure 1 "Key findings" box: "Aggregation: −0.4 pp, below δ-margin" and "1.36 pp" need "(κ=200)" labels
- [x] **$2** §7.3 aggregation paragraph — currently mentions only κ=200 result; add the κ=50 reversal (+20.4 pp SIG), which is the most important finding of that section
- [x] **$2** §8.3 "a loss of 43.2 pp under optimal assembly" — add "(κ=200)"
- [x] **$2** §9 paragraph 2: "equivalent to zero", "+25.4 pp", "lost 9.4/11.0 pp" — all without κ → add "(κ=200)" to each
- [x] **$2** §9 "Two consequences": "under vector normalisation it performs worse than reading the ranking top-down" — add "(at κ=200)"
- [x] **$2** Abstract and Intro: "these effects [SAW and TOPSIS] are not distinguishable from zero at κ=50" — Table 6 reports the *pooled mean*; write "the **mean** effect is not distinguishable from zero" or add per-method rows

---

## §3 — Claims reviewers will challenge (editorial)

- [x] **3.01** §5.1 κ chronology: "κ=200 was fixed in the E1 pre-specification and **adopted for the factorial**" is impossible (E1 is a follow-up posterior to the factorial) → rewrite: "κ=200 was used in the factorial without a written pre-specification; E1 subsequently fixed κ=200 in its pre-specification for comparability"
- [x] **3.02** §5.2: linked to 3.01 — TOST is pre-specified but κ of the factorial is not; add explicit statement: "The choice of κ for the factorial was not pre-specified; it is discussed in Section 5.1"
- [x] **3.03** §8.6 (Limitations) F8 claim: "confirm that the result reflects score–objective alignment **rather than an intrinsic property** of min–max" — asymmetry (5.6 vs 43.2 pp) disproves pure alignment → rewrite: "alignment explains the diagonals, but the asymmetry (5.6 vs 43.2 pp off-diagonal) indicates that min–max scores are more robust to frontier misspecification than vector scores"
- [x] **3.04** Intro, §6.9, §9: R advantage (1.36 pp) presented as result without "(below δ)" qualifier → add "(below the δ=2.5 pp margin)" in each occurrence
- [x] **3.05** §7.8: E6 "85 of 88, p<0.001" reported without stating which criterion was pre-registered and what it showed → add: state the pre-registered criterion and its result before reporting DEV-E6-002 revision
- [x] **3.06** §7.8 and §8.6: "order of magnitude" wrong — <3 pp vs 10.7 pp is 3–4×, not 10×; only against Fogo (35.8 pp) is ~12× → correct phrasing
- [x] **3.07** §2.6: "Eiselt & Marianov (2014) were **the only prior study** to compute an exact Pareto frontier…" — but AzancortNeto2026 also did → add "apart from the source study (AzancortNeto2026)"
- [x] **3.08** §4.1 "none enters F" missing scope: verified under nominal weights only, or across all 500 draws? → clarify "under the nominal weights $\wahp$"
- [x] **3.09** §4.1 "imputation by midpoint is immaterial" too strong — midpoint doesn't change min–max extrema but does change vector norms → rewrite: "does not affect the min–max normalisation constants; its effect on vector norms is negligible given the three sites account for $3/\Ncand$ of the column"
- [x] **3.10** Remark 7 calls the theorem a "sufficient" condition: the theorem is **necessary and sufficient** for efficiency over all instances; on one instance TV_W>0 is insufficient to guarantee loss → rewrite: "TV_W=0 is sufficient for efficiency; TV_W>0 is not sufficient to cause loss on every instance, as R-V* illustrates"
- [x] **3.11** Intro: "within-group distortion **accounts for** 35.8 of the 43.2 pp" implies additivity → rewrite: "within-group distortion alone costs 35.8 pp, against 43.2 pp for the full distortion (the effects are not additive)"
- [x] **3.12** §9: "distortions that **no** rank-agreement diagnostic reveals" — exaggeration → "that rank-agreement diagnostics **do not** reveal"
- [x] **3.13** §9: "extending to TOPSIS and VIKOR **remains open**" — VIKOR is already characterised as affine-invariant → "extending the exact characterisation to TOPSIS (via α=2 analogy) remains open"
- [x] **3.14** §8.6 "Regulatory grounding": "does not affect the relative comparison of methods" contradicts Table 8 → clarify: "the exclusion removes sites from the *selectable* set; it does not affect the normalisation reference set comparison in Table 8"
- [x] **3.15** §8.6 "Scope of closed form": "Remark 3 extends the identity to **ordinal** families" — it does not → remove "ordinal" or clarify

---

## §4 — Analysis additions (computational)

- [x] **4.01** **Table 5 at κ=50** — κ=50 columns (Q₂ and SE) added to Table 5 in main.tex (2026-10-30); macro provenance: mc_2cube_fixed_raw.csv (seed=42, correct) [DONE]
- [ ] **4.02** **κ sweep plot** — run κ ∈ {25, 50, 100, 200, 400, 1000} on main contrasts; plot contrast vs κ; transforms κ-sensitivity from caveat to result (high priority)
- [ ] **4.06** κ interpretation (new, B1): add SD(wᵢ) table to §7.x or caption; if expert weights available compute κ̂ = w₀(1−w₀)/Var(w) − 1 to locate the empirical regime on the reversal curve
- [x] **4.07** Reversal mechanism (new, B2): per-draw regression of SAW−TOPSIS contrast on N_eff = 1/Σwᵢ²; script: scripts/analyze_neff_regression.py; results: results/e7/neff_regression.json; paragraph added to sec:kappa after "reversal comes from both sides"; macros added to macros_e7.tex; commit 74896a2 [DONE: pooled r=−0.23, p<0.001, n=3000; crossover N_eff*≈9.2 ≈ AHP N_eff=9.3]
- [x] **4.08** Re-run official gate code on Athena with assert len > 0 active; 22/22 PASS in e7_official_run.log (Athena RTX 4000 Ada, 997s); bracket-notation fix for DataFrame.agg() method shadowing column access on pandas 3.x; commits 87aa84a + af3700a [DONE]
- [x] **4.03** §7.1 quantify membership: "Pareto membership improves" — add counts: e.g. "3 of 7 efficient in A; 6 of 7 in A′" (read from Table 3)
- [x] **4.04** §4.2 eigenvector note — add: "AzancortNeto2026 describe the principal eigenvector; the released weights coincide with the column-normalised vector (max|Δ|=0.001) and differ from the eigenvector by at most 0.004 (perm), well below the Dirichlet SD (≈0.025)"
- [ ] **4.05** TOPSIS mechanism (post hoc, optional) — α=2 analogy implies effective-weight dispersion doubles in log scale; test TV(2)−TV(1) per draw as predictor of frontier miss in §7.3

---

## §5 — Notation conflicts

- [ ] **5.01** `δ` = equivalence margin AND `δⱼ` = deviation vector → rename margin to `Δ` throughout
- [x] **5.02** `ρ` = vector amplitude AND `ρ` = Spearman correlation (§7.6) → rename Spearman to `rₛ`
- [ ] **5.03** `α` = TOPSIS exponent AND `α=0.05` significance level → rename exponent to `γ`
- [ ] **5.04** `A`/`𝒜` used inconsistently for space A and amplitude Aⱼ → always `𝒜`, `𝒜′` for spaces; `A_j` for amplitude
- [ ] **5.05** `S` = set of sites, S = ΣwⱼAⱼ, S = IEEE scalarisation, S in Prop.2 proof → resolve in §6.4
- [ ] **5.06** `R` = regret, `R_ℓ` = criterion range intervals, `R` = set in Thm.1 proof → rename range intervals to `Δ_ℓ` and the set to `U`
- [x] **5.07** TV precision: 0.091 (3dp) vs 0.3113 (4dp) → choose 3dp throughout (display conflict fixed in lines where 0.091 and \TVvec appear together)

---

## §6 — Structure and repetition

- [ ] **6.01** Pages 15–17 near-empty: §6.9 item 4 alone on a page, Fig.3 alone, Fig.4 alone → use `[t]` specifiers and reduce Fig.3 to single column; recover ~2 pages
- [x] **6.02** "2.86×… 0.53 is difficult to defend" appears 3× → §8.3 keeps full argument (with \PermInflation× and \UrbanRatioVec); §8.5 reduced to "the case for preferring min-max is developed in Section~\ref{sec:normliterature}"; §9 reduced to "see Section~\ref{sec:normliterature}" [DONE]
- [x] **6.03** E6 results reported 3× → §7.8 keeps full results; §8.6 reduced to cross-reference with interpretation ("losses vary substantially across marginal families"); §9 reduced to "supports the directional prediction" [DONE]
- [x] **6.04** "portfolios selected by exact optimisation… are better portfolios" in §7.3 and §7.4 → second occurrence (§7.4) removed [DONE]
- [x] **6.05** P1–P3 predictions announced twice in §7.7 → removed duplicate "predictions were committed to the repository before the first run (Supplementary Material)" from the introductory paragraph; single explicit list at "Three predictions were committed..." remains [DONE]
- [x] **6.06** §7.2 title "Confirmation of the amplitude lemma" contradicted by body ("not its foundation") → rename to "Empirical ordering by TV"
- [x] **6.07** §7.3 title "The factorial design" duplicates §5.4 → rename to "Factorial results"
- [ ] **6.08** Remark 6 and Table 8 (coding inconsistency) buried in §7.5 (alignment section) → give own subsection — VERIFY: sec:coding exists; check grep for residual "Remark 6" references
- [ ] **6.09** §7 opening "three parts" — verify text no longer says "three parts"; now reads "three follow-up experiments" (accurate) — CHECK then mark done
- [x] **6.10** Eq.(23) = eq:weff_vec removed; replaced by inline formula "$w_j^{eff} = w_j\rho_j/\sum_k w_k\rho_k$" with cross-reference to eq:weff; no dangling \eqref{eq:weff_vec} references remain [DONE]
- [ ] **6.11** Practical recommendations paragraph — add to §8 or §9 (bloco 3 from 2026-11-01 review): report normalisation scheme; characterise weight uncertainty before choosing aggregation; validate aspect encoding; report effective weights with elicited weights
- [x] **6.11** Highlight "by 25.4 pp; at both κ tested" grammatically broken → "Normalisation shifts greedy Pareto attainment by 25–29 pp at both κ tested"
- [x] **6.12** Highlight "Pareto-safe" undefined jargon → define or replace with "Pareto-efficient under exact assembly"
- [x] **6.13** Abstract ~260 words → verify Omega limit (Omega: 250 words max); trim if needed (trimmed to ~245 words by script count)

---

## §7 — References

- [x] **7.01** Eiselt: inconsistent initial ("H." vs "H.A.") causes wrong sort order → normalise to "H.A."
- [x] **7.02** Martí et al. (2022) erratum note "10.1016/j.ejor.2025.12.002" — verify on Crossref; remove if not real (note removed — unverifiable without internet)
- [ ] **7.03** Andrade & Barbosa (2015) and Costa et al. (2020) missing DOI — Revista de Geografia (UFPE) assigns DOIs; look them up (requires manual verification)
- [ ] **7.04** Liesiö et al. (2021): confirm the paper says "cardinality-constrained with spatial interdependencies… largely unexplored" (requires manual verification of source paper)
- [x] **7.05** §2.2 "Milani… confirmed this empirically" hangs from Kettani → "showed empirically that different norms produce different rankings"

---

## §8 — check_consistency.py new rules

- [x] **8.01** Add rule: `pdftotext main.pdf - | grep -nE '\+\s?\+[0-9]'` — flags double positive sign (BAD_PHRASE added: "+\AggContrastKfifty")
- [x] **8.02** Add rule: `grep -nE 'shrinks?\s+to\s+zero|shrinking\s+to\s+zero'` in main.tex — flags banned phrase (added to BAD_PHRASES + MUST_FAIL)
- [x] **8.03** Add rule: orphan bib entries (in .bbl but not in any `\cite` in main.tex) — flags Saaty and any others (WARN rule added; 47 orphan entries in refs.bib — review before submission)
- [x] **8.04** Verify 35/35 still pass after all above changes (38/38 PASS with 3 new regression cases)

---

## §9 — Zenodo (last)

- [x] **9.01** Confirm concept DOI: 10.5281/zenodo.23676428 confirmed [DONE]
- [x] **9.02** Code availability in main.tex updated with concept DOI + version DOI 10.5281/zenodo.23688817 (v1.7) [DONE]
- [x] **9.03** Release v1.7 created on GitHub (tag + GitHub Release); Zenodo deposit 23688817 published [DONE]
- [x] **9.04** README badge and CITATION.cff updated to v1.7; concept DOI 10.5281/zenodo.23676428 [DONE]

---

## Priority order for execution

```
Round 1 (this session, ~2h):  §1 all + §2 all + §3.01/02/03/04/07/08/09/11/12/13
Round 2 (next session, ~1h):  §3.05/06/10/14/15 + §4.03/04 + §5 + §7
Round 3 (after computation):  §4.01 (κ=50 table) + §4.02 (κ sweep) + §4.05 (TOPSIS mech)
Round 4 (polish):             §6 + §8 new rules + §9 Zenodo
```

---

*Last updated: 2026-10-29. check_consistency.py: 35/35 PASS before this list.*


## Stage 1 regression criteria (committed before run — 2026-10-27)

### Primary criterion (blocking)
All macros from Table 5, Table 6, E1 and F8 reproduce to the published value.
All 22 E7 gates pass (`check_e7_gates.py` exit 0).

### Secondary criterion (informative, non-blocking)
SHA-256 of the four reference files:
- `results/unified/mc_unified_raw.csv`: b02df7277956c0112271065efbe201c2048ad4c92c2e6000794c659477e730f2
- `results/regret/regret_perdraw.csv`:  0f8eb63d93bdde9d1f4827bf62c4d4941e189f52191a6cf721cd9e35bc401b77
- `results/e1/e1_diag_bootstrap.csv`:  32b536bf32516bb2458a8941929c5a85dba41bd54731a02cf3e4a947daf368aa
- `results/f8/f8_per_draw.csv`:         228d54ec91535fb4d85f723d7f6a196abfa9d76da4df546acfc08547b8e8850f

If SHA differs: report numeric max|diff| per column and library versions (pip freeze + Python version).
SHA mismatch alone does NOT block Stage 2.

### Environment
- Run code at commit 94b5baf via `git worktree add ../stage1_worktree 94b5baf`
- Do NOT modify the worktree code
- Record pip freeze and Python version in `results/stage1/stage1_env.txt`

## Git reconciliation audit (2026-10-27)

Performed before Santiago Stage 1.
Old origin/main: 19db852 (v1.6)
Merge-base (local main / old origin/main): 265a242a
Restored tree: e23be28 (flat structure, Santiago PRESPEC A5+A5a+A5b)
Current origin/main: ef12e7c (= e23be28 tree, b2fadc2 as parent)

### Verification: ef12e7c descends from 19db852
CONFIRMED: git merge-base --is-ancestor 19db852 ef12e7c returns 0.

### What origin/main had since merge-base that was NOT in local (265a242a → 19db852)
- .zenodo.json: new file (v1.6, ORCID 0009-0000-2754-8503 — OUTDATED, superseded by local v1.8 with correct ORCID 0000-0003-2866-5445)
- CITATION.cff: new file (v1.6, same ORCID issue — superseded)
- paper/manuscript/main.tex: v1.6 content — superseded by local main.tex at root (v1.8)
- paper/docs/prespec/PRESPEC_SANTIAGO.md: v1.6 snapshot — superseded by corpus/PRESPEC_SANTIAGO.md (A5+A5a+A5b)

### Content verdict
No content was lost. All v1.6 material was superseded by v1.8 local changes
with corrections (ORCID, v1.8 version bump, PRESPEC amendments, Santiago A5/A5a/A5b).
The v1.6 remote had outdated ORCID and version; the local had the correct values.
