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
- [x] **1.14** Title page "ORCID(s):" field is empty → fill `\orcid{0009-0000-2754-8503}` or use cas-dc `[orcid=...]` syntax
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

- [ ] **3.01** §5.1 κ chronology: "κ=200 was fixed in the E1 pre-specification and **adopted for the factorial**" is impossible (E1 is a follow-up posterior to the factorial) → rewrite: "κ=200 was used in the factorial without a written pre-specification; E1 subsequently fixed κ=200 in its pre-specification for comparability"
- [ ] **3.02** §5.2: linked to 3.01 — TOST is pre-specified but κ of the factorial is not; add explicit statement: "The choice of κ for the factorial was not pre-specified; it is discussed in Section 5.1"
- [ ] **3.03** §8.6 (Limitations) F8 claim: "confirm that the result reflects score–objective alignment **rather than an intrinsic property** of min–max" — asymmetry (5.6 vs 43.2 pp) disproves pure alignment → rewrite: "alignment explains the diagonals, but the asymmetry (5.6 vs 43.2 pp off-diagonal) indicates that min–max scores are more robust to frontier misspecification than vector scores"
- [ ] **3.04** Intro, §6.9, §9: R advantage (1.36 pp) presented as result without "(below δ)" qualifier → add "(below the δ=2.5 pp margin)" in each occurrence
- [ ] **3.05** §7.8: E6 "85 of 88, p<0.001" reported without stating which criterion was pre-registered and what it showed → add: state the pre-registered criterion and its result before reporting DEV-E6-002 revision
- [ ] **3.06** §7.8 and §8.6: "order of magnitude" wrong — <3 pp vs 10.7 pp is 3–4×, not 10×; only against Fogo (35.8 pp) is ~12× → correct phrasing
- [ ] **3.07** §2.6: "Eiselt & Marianov (2014) were **the only prior study** to compute an exact Pareto frontier…" — but AzancortNeto2026 also did → add "apart from the source study (AzancortNeto2026)"
- [ ] **3.08** §4.1 "none enters F" missing scope: verified under nominal weights only, or across all 500 draws? → clarify "under the nominal weights $\wahp$"
- [ ] **3.09** §4.1 "imputation by midpoint is immaterial" too strong — midpoint doesn't change min–max extrema but does change vector norms → rewrite: "does not affect the min–max normalisation constants; its effect on vector norms is negligible given the three sites account for $3/\Ncand$ of the column"
- [ ] **3.10** Remark 7 calls the theorem a "sufficient" condition: the theorem is **necessary and sufficient** for efficiency over all instances; on one instance TV_W>0 is insufficient to guarantee loss → rewrite: "TV_W=0 is sufficient for efficiency; TV_W>0 is not sufficient to cause loss on every instance, as R-V* illustrates"
- [ ] **3.11** Intro: "within-group distortion **accounts for** 35.8 of the 43.2 pp" implies additivity → rewrite: "within-group distortion alone costs 35.8 pp, against 43.2 pp for the full distortion (the effects are not additive)"
- [ ] **3.12** §9: "distortions that **no** rank-agreement diagnostic reveals" — exaggeration → "that rank-agreement diagnostics **do not** reveal"
- [ ] **3.13** §9: "extending to TOPSIS and VIKOR **remains open**" — VIKOR is already characterised as affine-invariant → "extending the exact characterisation to TOPSIS (via α=2 analogy) remains open"
- [ ] **3.14** §8.6 "Regulatory grounding": "does not affect the relative comparison of methods" contradicts Table 8 → clarify: "the exclusion removes sites from the *selectable* set; it does not affect the normalisation reference set comparison in Table 8"
- [ ] **3.15** §8.6 "Scope of closed form": "Remark 3 extends the identity to **ordinal** families" — it does not → remove "ordinal" or clarify

---

## §4 — Analysis additions (computational)

- [ ] **4.01** **Table 5 at κ=50** — add κ=50 columns (Q₂ and SE) or a supplementary table; this is prerequisite for readers to verify the +20.4 pp aggregation result
- [ ] **4.02** **κ sweep plot** — run κ ∈ {25, 50, 100, 200, 400, 1000} on main contrasts; plot contrast vs κ; transforms κ-sensitivity from caveat to result (high priority)
- [ ] **4.03** §7.1 quantify membership: "Pareto membership improves" — add counts: e.g. "3 of 7 efficient in A; 6 of 7 in A′" (read from Table 3)
- [ ] **4.04** §4.2 eigenvector note — add: "AzancortNeto2026 describe the principal eigenvector; the released weights coincide with the column-normalised vector (max|Δ|=0.001) and differ from the eigenvector by at most 0.004 (perm), well below the Dirichlet SD (≈0.025)"
- [ ] **4.05** TOPSIS mechanism (post hoc, optional) — α=2 analogy implies effective-weight dispersion doubles in log scale; test TV(2)−TV(1) per draw as predictor of frontier miss in §7.3

---

## §5 — Notation conflicts

- [ ] **5.01** `δ` = equivalence margin AND `δⱼ` = deviation vector → rename margin to `Δ` throughout
- [ ] **5.02** `ρ` = vector amplitude AND `ρ` = Spearman correlation (§7.6) → rename Spearman to `rₛ`
- [ ] **5.03** `α` = TOPSIS exponent AND `α=0.05` significance level → rename exponent to `γ`
- [ ] **5.04** `A`/`𝒜` used inconsistently for space A and amplitude Aⱼ → always `𝒜`, `𝒜′` for spaces; `A_j` for amplitude
- [ ] **5.05** `S` = set of sites, S = ΣwⱼAⱼ, S = IEEE scalarisation, S in Prop.2 proof → resolve in §6.4
- [ ] **5.06** `R` = regret, `R_ℓ` = criterion range intervals, `R` = set in Thm.1 proof → rename range intervals to `Δ_ℓ` and the set to `U`
- [ ] **5.07** TV precision: 0.091 (3dp) vs 0.3113 (4dp) → choose 3dp throughout

---

## §6 — Structure and repetition

- [ ] **6.01** Pages 15–17 near-empty: §6.9 item 4 alone on a page, Fig.3 alone, Fig.4 alone → use `[t]` specifiers and reduce Fig.3 to single column; recover ~2 pages
- [ ] **6.02** "2.86×… 0.53 is difficult to defend" appears 3× (§8.3, §8.5, §9) → keep one, remove others
- [ ] **6.03** E6 results reported 3× (§7.8, §8.6, §9) → consolidate
- [ ] **6.04** "portfolios selected by exact optimisation… are better portfolios" in §7.3 and §7.4 → keep one
- [ ] **6.05** P1–P3 predictions announced twice in §7.7 → keep one announcement
- [ ] **6.06** §7.2 title "Confirmation of the amplitude lemma" contradicted by body ("not its foundation") → rename to "Empirical ordering by TV"
- [ ] **6.07** §7.3 title "The factorial design" duplicates §5.4 → rename to "Factorial results"
- [ ] **6.08** Remark 6 and Table 8 (coding inconsistency) buried in §7.5 (alignment section) → give own subsection
- [ ] **6.09** §7 opening "three parts" but has 8 subsections → fix count or restructure
- [ ] **6.10** Eq.(23) duplicates (15)–(16) → remove, add cross-reference
- [ ] **6.11** Highlight "by 25.4 pp; at both κ tested" grammatically broken → "Normalisation shifts greedy Pareto attainment by 25–29 pp at both κ tested"
- [ ] **6.12** Highlight "Pareto-safe" undefined jargon → define or replace with "Pareto-efficient under exact assembly"
- [ ] **6.13** Abstract ~260 words → verify Omega limit (Omega: 250 words max); trim if needed

---

## §7 — References

- [ ] **7.01** Eiselt: inconsistent initial ("H." vs "H.A.") causes wrong sort order → normalise to "H.A."
- [ ] **7.02** Martí et al. (2022) erratum note "10.1016/j.ejor.2025.12.002" — verify on Crossref; remove if not real
- [ ] **7.03** Andrade & Barbosa (2015) and Costa et al. (2020) missing DOI — Revista de Geografia (UFPE) assigns DOIs; look them up
- [ ] **7.04** Liesiö et al. (2021): confirm the paper says "cardinality-constrained with spatial interdependencies… largely unexplored"
- [ ] **7.05** §2.2 "Milani… confirmed this empirically" hangs from Kettani → "showed empirically that different norms produce different rankings"

---

## §8 — check_consistency.py new rules

- [ ] **8.01** Add rule: `pdftotext main.pdf - | grep -nE '\+\s?\+[0-9]'` — flags double positive sign
- [ ] **8.02** Add rule: `grep -nE 'shrinks?\s+to\s+zero|shrinking\s+to\s+zero'` in main.tex — flags banned phrase
- [ ] **8.03** Add rule: orphan bib entries (in .bbl but not in any `\cite` in main.tex) — flags Saaty and any others
- [ ] **8.04** Verify 35/35 still pass after all above changes

---

## §9 — Zenodo (last)

- [ ] **9.01** Confirm concept DOI: open zenodo.org record for 23676483 → click "Cite all versions" box → copy the DOI there (not the version DOI)
- [ ] **9.02** Update Code availability in main.tex with confirmed concept DOI + release v1.6
- [ ] **9.03** After all changes are committed, create release v1.6
- [ ] **9.04** Update README badge and CITATION.cff with confirmed concept DOI if different from 23676483

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

