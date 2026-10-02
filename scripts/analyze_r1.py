"""scripts/analyze_r1.py
Fase D: formaliza os outputs r1/ a partir dos dados já existentes.

Lê:
  results/e4-audit/fourthcell_consistent.csv  (Q2 por célula × kappa × montagem)
  results/e4-audit/bootstrap_paired.csv       (IC emparelhados dos contrastes)

Aplica as regras R1-1 a R1-6 do PRESPEC_R1.md (corpus/PRESPEC_R1.md).

Produz:
  results/r1/r1_aggregate.csv     — Q2, SE por célula × kappa × montagem
  results/r1/r1_decisions.json    — decisão automática por contraste
  results/r1/r1_bootstrap.csv     — IC emparelhados (cópia filtrada)
  results/r1/r1_meta.json         — timestamp, commit, hash dos pesos

Regras de decisão (PRESPEC_R1.md §1):
  Efeito   : IC 95% exclui 0 E |Δ| >= THRESHOLD_PP
  Observação: caso contrário
  ABORTAR   : R1-3 falha (alguma diagonal < 100%)

THRESHOLD_PP = 2.5  (declarado no PRESPEC_R1.md)
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

ROOT    = Path(__file__).parent.parent
R1_DIR  = ROOT / "results" / "r1"
AUDIT   = ROOT / "results" / "e4-audit"
E1_NPY  = ROOT / "results" / "e1" / "e1_weights_k200.npy"
E1_SHA  = "bea05275e85bc6ddbd754c88c0a05c90a568374ff76eacfc8b522750a4aef487"

THRESHOLD_PP = 2.5   # PRESPEC_R1.md §1 rule
KAPPA_PRIMARY = 200

# ── Load inputs ────────────────────────────────────────────────────────────────
fc = pd.read_csv(AUDIT / "fourthcell_consistent.csv")
boot = pd.read_csv(AUDIT / "bootstrap_paired.csv")

print("=== Fase D: analyze_r1.py ===")
print(f"fourthcell_consistent.csv: {len(fc)} rows")
print(f"bootstrap_paired.csv:      {len(boot)} rows")
print()

# ── Pivot fourthcell data ─────────────────────────────────────────────────────
# Columns: cell, kappa, n_draws, Q2_greedy, SE_greedy, Q2_optimal, SE_optimal
def q(cell, kappa, assembly):
    row = fc[(fc.cell == cell) & (fc.kappa == kappa)]
    if len(row) == 0:
        return None, None
    col = f"Q2_{assembly}"
    se_col = f"SE_{assembly}"
    return float(row[col].iloc[0]), float(row[se_col].iloc[0])

# ── R1-3: diagonal check (ABORTAR if any < 100%) ──────────────────────────────
diagonals = {
    "RV_star_Aprime": ("Ncand/A' with consistent coding", "optimal"),
    "RM_Aprime":      ("Nvia/A' control",                "optimal"),
    "RV_star_A":      ("Ncand/A with consistent coding",  "optimal"),
}
print("=== R1-3: diagonal check ===")
r13_pass = True
for cell, (label, asm) in diagonals.items():
    val, se = q(cell, KAPPA_PRIMARY, asm)
    status = "PASS" if val is not None and val >= 99.9 else "FAIL"
    if status == "FAIL":
        r13_pass = False
    print(f"  {cell:20s} opt={val}%  {status}  ({label})")

if not r13_pass:
    print("\nR1-3 FAILED. ABORTING Fase D. Return to Fase A.")
    sys.exit(2)
print("  R1-3: PASS\n")

# ── R1-1 and R1-2: Δ_ref ─────────────────────────────────────────────────────
print("=== R1-1 (optimal) and R1-2 (greedy): Δ_ref = RV_star_Aprime − RM_Aprime ===")

def get_bootstrap(keyword, side):
    """Find bootstrap row by keyword in pair label, side: 'opt' or 'grd'"""
    row = boot[boot.pair.str.contains(keyword, regex=False, na=False)]
    if len(row) == 0:
        return None, None, None
    r = row.iloc[0]
    diff = float(r[f"diff_{side}_pp"])
    lo   = float(r[f"ci_lo_{side}"])
    hi   = float(r[f"ci_hi_{side}"])
    return diff, lo, hi

def decide(diff_pp, lo, hi, rule_id):
    if diff_pp is None:
        return "UNKNOWN", "missing data"
    excludes_zero = (lo > 0) or (hi < 0)
    large_enough  = abs(diff_pp) >= THRESHOLD_PP
    if excludes_zero and large_enough:
        return "EFEITO", f"Δ={diff_pp:+.1f}pp  IC=[{lo:+.1f},{hi:+.1f}]  both criteria met"
    else:
        reason = []
        if not excludes_zero: reason.append("IC includes 0")
        if not large_enough:  reason.append(f"|Δ|={abs(diff_pp):.1f}<{THRESHOLD_PP}")
        return "OBSERVAÇÃO", f"Δ={diff_pp:+.1f}pp  IC=[{lo:+.1f},{hi:+.1f}]  {'; '.join(reason)}"

# R1-1: optimal
diff_opt, lo_opt, hi_opt = get_bootstrap("R-V* vs R-M", "opt")
dec_r11, reason_r11 = decide(diff_opt, lo_opt, hi_opt, "R1-1")
print(f"  R1-1 (opt): {dec_r11}  —  {reason_r11}")

# R1-2: greedy
diff_grd, lo_grd, hi_grd = get_bootstrap("R-V* vs R-M", "grd")
dec_r12, reason_r12 = decide(diff_grd, lo_grd, hi_grd, "R1-2")
print(f"  R1-2 (grd): {dec_r12}  —  {reason_r12}")
print()

# ── R1-4: tab:canonical ───────────────────────────────────────────────────────
print("=== R1-4: tab:canonical ===")
print("  N/A — Fase B marcou tab:canonical como NÃO contaminada (contamination-note.md §2)")
print("  tab:canonical mantém-se sem recálculo.")
dec_r14 = "N/A"
print()

# ── R1-5: R-asp (descritivo) ─────────────────────────────────────────────────
print("=== R1-5: R-asp descritivo ===")
rasp_opt, rasp_se = q("R_asp_Aprime", KAPPA_PRIMARY, "optimal")
rasp_grd, _      = q("R_asp_Aprime", KAPPA_PRIMARY, "greedy")
print(f"  R-asp opt={rasp_opt}%  grd={rasp_grd}%  (codificação contínua, post hoc, não-confirmatório)")
dec_r15 = f"DESCRITIVO: R-asp opt={rasp_opt}% grd={rasp_grd}%"
print()

# ── R1-6: resíduo R-V − R-asp ────────────────────────────────────────────────
print("=== R1-6: resíduo R-V − R-asp (efeito do conjunto de referência) ===")
row6 = boot[boot.pair.str.contains("R-asp vs R-V", regex=False)]
if len(row6) > 0:
    r6 = row6.iloc[0]
    diff6_opt = float(r6.diff_opt_pp)
    lo6_opt   = float(r6.ci_lo_opt)
    hi6_opt   = float(r6.ci_hi_opt)
    sig6_opt  = str(r6.sig_opt)
    diff6_grd = float(r6.diff_grd_pp)
    dec_r16, reason_r16 = decide(diff6_opt, lo6_opt, hi6_opt, "R1-6")
    print(f"  R1-6 (opt): {dec_r16}  —  {reason_r16}")
    print(f"  R1-6 (grd): Δ={diff6_grd:+.1f}pp  sig={sig6_opt}")
else:
    dec_r16 = "UNKNOWN"; reason_r16 = "missing data"
    diff6_opt = diff6_grd = lo6_opt = hi6_opt = None
    print("  R1-6: missing data")
print()

# ── Build decisions dict ──────────────────────────────────────────────────────
decisions = {
    "prespec_commit": "595a760",
    "analyze_r1_commit": subprocess.getoutput("git rev-parse HEAD").strip(),
    "kappa_primary": KAPPA_PRIMARY,
    "threshold_pp": THRESHOLD_PP,
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "R1-3": {
        "label": "Diagonal cells = 100% optimal",
        "decision": "PASS",
        "evidence": {c: q(c, KAPPA_PRIMARY, "optimal")[0] for c in diagonals}
    },
    "R1-1": {
        "label": "Δ_ref optimal (Ncand/A' − Nvia/A')",
        "decision": dec_r11,
        "delta_pp": diff_opt,
        "ci_lo": lo_opt,
        "ci_hi": hi_opt,
        "reason": reason_r11
    },
    "R1-2": {
        "label": "Δ_ref greedy",
        "decision": dec_r12,
        "delta_pp": diff_grd,
        "ci_lo": lo_grd,
        "ci_hi": hi_grd,
        "reason": reason_r12
    },
    "R1-4": {
        "label": "Recalculate tab:canonical",
        "decision": "N/A",
        "reason": "tab:canonical not contaminated (contamination-note.md §2)"
    },
    "R1-5": {
        "label": "R-asp descriptive",
        "decision": dec_r15,
        "R_asp_opt": rasp_opt,
        "R_asp_grd": rasp_grd
    },
    "R1-6": {
        "label": "Residual R-V − R-asp (reference-set effect)",
        "decision": dec_r16 if len(row6) > 0 else "UNKNOWN",
        "delta_pp": diff6_opt if len(row6) > 0 else None,
        "ci_lo": lo6_opt if len(row6) > 0 else None,
        "ci_hi": hi6_opt if len(row6) > 0 else None,
        "reason": reason_r16 if len(row6) > 0 else "missing data"
    },
}

# ── Build aggregate CSV ───────────────────────────────────────────────────────
agg_rows = []
for kappa in [200, 50]:
    for cell in ["RV_star_Aprime","RM_Aprime","RV_star_A","RM_A","R_asp_Aprime","R_V_Aprime"]:
        for asm in ["greedy","optimal"]:
            val, se = q(cell, kappa, asm)
            if val is not None:
                agg_rows.append({"cell":cell,"kappa":kappa,"assembly":asm,
                                  "Q2":val,"SE":se})
agg_df = pd.DataFrame(agg_rows)

# ── Save ──────────────────────────────────────────────────────────────────────
R1_DIR.mkdir(exist_ok=True)

agg_df.to_csv(R1_DIR/"r1_aggregate.csv", index=False)
boot.to_csv(R1_DIR/"r1_bootstrap.csv", index=False)

with open(R1_DIR/"r1_decisions.json","w") as f:
    json.dump(decisions, f, indent=2, default=str)

# meta
sha_npy = hashlib.sha256(E1_NPY.read_bytes()).hexdigest() if E1_NPY.exists() else "FILE_NOT_FOUND"
meta = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "git_head": subprocess.getoutput("git rev-parse HEAD").strip(),
    "git_status_clean": subprocess.getoutput("git status --porcelain").strip() == "",
    "e1_weights_sha256": sha_npy,
    "e1_weights_sha256_expected": E1_SHA,
    "e1_weights_match": sha_npy == E1_SHA,
    "python": sys.version,
    "source": "existing data from fourthcell_consistent.csv + bootstrap_paired.csv",
    "prespec_commit": "595a760",
}
with open(R1_DIR/"r1_meta.json","w") as f:
    json.dump(meta, f, indent=2)

print(f"Saved to {R1_DIR}/")
print(f"  r1_aggregate.csv  ({len(agg_df)} rows)")
print(f"  r1_bootstrap.csv  ({len(boot)} rows)")
print(f"  r1_decisions.json")
print(f"  r1_meta.json  (git_status_clean={meta['git_status_clean']})")
print()
print("=== Decision summary ===")
for rid in ["R1-3","R1-1","R1-2","R1-4","R1-5","R1-6"]:
    d = decisions[rid]
    print(f"  {rid}: {d['decision']}")
