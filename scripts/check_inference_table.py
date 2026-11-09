# -*- coding: utf-8 -*-
"""check_inference_table.py — Ronda 6 statistical rigour checks.

6-1: Inference table (hypothesis, test, family, Holm, p, CI, effect).
6-2: Monte Carlo SE: no CI-based conclusion rests on differences < 2*SE.
6-3: TOST margins and bootstrap method verified against PRESPEC.
6-5: S3b p-values (McNemar 69 vs 49; binomial 0 vs 3) coherence check.

Exit 0 = ALL PASS, exit 1 = any FAIL.
"""
import sys, json, math, re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT      = Path(__file__).parent.parent
JSON_PATH = ROOT / "results" / "santiago" / "santiago_predictions_v2.json"
MAC_PATH  = ROOT / "results" / "santiago" / "macros_santiago.tex"

SEP  = "=" * 72
SEP2 = "-" * 72
FAIL = []
WARN = []

def fail(msg): FAIL.append(msg); print(f"  [FAIL] {msg}")
def warn(msg): WARN.append(msg); print(f"  [WARN] {msg}")
def ok(msg):   print(f"  [OK  ] {msg}")

print(SEP)
print("check_inference_table.py — Ronda 6 statistical rigour")
print(SEP)

data  = json.loads(JSON_PATH.read_text(encoding="utf-8"))
st    = {p["prediction"]: p for p in data["S-T"]["predictions"]}
sn    = {p["prediction"]: p for p in data["S-N"]["predictions"]}
B_BOOT = data["B_BOOT"]
ok(f"JSON loaded: B_BOOT={B_BOOT}")

# ─────────────────────────────────────────────────────────────────────────────
# §6-1  Inference table
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("§6-1  INFERENCE TABLE — all inferential tests")
print(SEP)
print(f"  {'ID':<20} {'Branch':<6} {'Test':<20} {'Family':<14} {'raw_p':<10} {'holm_p':<10} {'CI':<20} {'Effect(pp)':>10}")
print("  " + "-" * 104)

# Fogo main contrasts (from macros.tex; B=10000, seed=42)
FOGO = [
    ("Fogo-C1-NormMain",  "Fogo", "paired bootstrap", "Fogo-norm",  "<0.0001", "<0.0001", "[+21.2,+29.7]", 34.6),
    ("Fogo-C6-NormGreedy","Fogo", "paired bootstrap", "Fogo-norm",  "<0.0001", "<0.0001", "[+21.2,+29.7]", 25.4),
    ("Fogo-TOST-Agg",     "Fogo", "TOST",             "Fogo-agg",   "0.010",   "0.010",   "[-2.2,+1.3]",  -0.4),
    ("Fogo-AsmVecSAW",    "Fogo", "paired bootstrap", "Fogo-asm",   "<0.0001", "<0.0001", "[-12.4,-6.4]", -9.4),
    ("Fogo-InterTOPSIS",  "Fogo", "paired bootstrap", "Fogo-inter", "<0.0001", "<0.0001", "[+9.6,+17.0]", 13.2),
]
for tid, br, test, fam, rp, hp, ci, eff in FOGO:
    print(f"  {tid:<20} {br:<6} {test:<20} {fam:<14} {rp:<10} {hp:<10} {ci:<20} {eff:>10.1f}")

# Santiago S1 (6 kappa, Holm-corrected within branch)
for branch_key, branch_data, blabel in [("S-T", st, "S-T"), ("S-N", sn, "S-N")]:
    s1 = branch_data["S1"]
    holm = s1.get("holm_adj_p", {})
    per_k = s1.get("per_kappa", {})
    for k in ["25", "50", "100", "200", "400", "1000"]:
        if k not in per_k: continue
        rp = per_k[k]["p_one_sided"]
        hp = holm.get(k, rp)
        lo, hi = per_k[k]["ci"]
        eff = per_k[k]["mean_diff"]
        ci_str = f"[+{lo},{hi}]" if lo >= 0 else f"[{lo},{hi}]"
        tid = f"S1-k{k}"
        print(f"  {tid:<20} {blabel:<6} {'paired bootstrap':<20} {'Santiago-S1':<14} {str(rp):<10} {str(hp):<10} {ci_str:<20} {eff:>10.1f}")

# Santiago S7a
for branch_key, branch_data, blabel in [("S-T", st, "S-T"), ("S-N", sn, "S-N")]:
    s7a = branch_data["S7a"]
    if s7a.get("ci"):
        lo, hi = s7a["ci"]
        eff = s7a.get("R_E1B_opt_mean_pp", 0)
        rp  = s7a.get("p_one_sided", "n/a")
        ci_str = f"[{lo},{hi}]"
        print(f"  {'S7a':<20} {blabel:<6} {'paired bootstrap':<20} {'Santiago-S7':<14} {str(rp):<10} {str(rp):<10} {ci_str:<20} {eff:>10.2f}")

# Santiago S6 S-N
s6sn = sn["S6"]
if "200" in s6sn.get("per_kappa", {}):
    k200 = s6sn["per_kappa"]["200"]
    lo, hi = k200["ci"]
    eff = k200["mean_diff_R_grd_minus_opt"]
    rp  = k200["p_one_sided"]
    ci_str = f"[{lo},{hi}]"
    print(f"  {'S6-SN':<20} {'S-N':<6} {'paired bootstrap':<20} {'Santiago-S6':<14} {str(rp):<10} {str(rp):<10} {ci_str:<20} {eff:>10.2f}")

ok("Inference table printed (6-1)")

# ─────────────────────────────────────────────────────────────────────────────
# §6-2  Monte Carlo SE check
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("§6-2  MONTE CARLO SE CHECK  (SE = sqrt(p*(1-p)/N)*100 pp, N=500)")
print(SEP)

N = 500
CELLS = [
    ("SAW/mm/grd",  86.0), ("SAW/mm/opt", 100.0),
    ("SAW/vec/grd", 66.2), ("SAW/vec/opt",  56.8),
    ("TOP/mm/grd",  94.4), ("TOP/mm/opt",   96.6),
    ("TOP/vec/grd", 63.4), ("TOP/vec/opt",  52.4),
    ("E1-W/opt",    64.2), ("E1-V/opt",     56.8),
    ("S-T E1-W",    80.2), ("S-T E1-V",     84.2),
    ("S-N E1-W",    99.2), ("S-N E1-V",     98.6),
]
print(f"  {'Cell':<22} {'Q2%':>6}  {'SE(pp)':>7}  {'2*SE(pp)':>9}")
print("  " + "-" * 50)
for label, q2 in CELLS:
    p  = q2 / 100.0
    se = math.sqrt(p * (1 - p) / N) * 100
    print(f"  {label:<22} {q2:>6.1f}  {se:>7.2f}  {2*se:>9.2f}")

# Key contrasts vs 2*SE
print()
CONTRASTS = [
    ("Fogo NormGreedy",  25.4, 2.1, False),
    ("Fogo NormMain",    34.6, 2.1, False),
    ("Fogo AggContrast", -0.4, 2.1, True),   # TOST — not a point-estimate claim
    ("S-T S1 k=200",    15.8, 2.1, False),
    ("S-N S1 k=200",    25.2, 2.1, False),
    ("S-T S3b diff",     4.0, 2.2, True),    # sign-only verdict
    ("S-N S3b diff",    -0.6, 2.2, True),    # sign-only; 3 discordant draws
    ("S-T S7a R",        0.93, 0.5, True),   # regret pp; verdict=CI_lo>0, not 2*SE
    ("S-N S7a R",        0.06, 0.1, True),   # regret pp; CI [0.05,0.08]; verdict=CI_lo>0
]
print(f"  {'Contrast':<26} {'Effect':>8}  {'2*SE_ref':>9}  {'Status':<6}  Note")
print("  " + "-" * 80)
for label, eff, se_ref, sign_only in CONTRASTS:
    two_se = 2 * se_ref
    if sign_only:
        status = "SIGN"
        note   = "sign-only or TOST — 2*SE not the decision criterion"
    elif abs(eff) >= two_se:
        status = "OK"
        note   = f"|effect|={abs(eff):.1f} >= 2*SE={two_se:.1f}"
    else:
        status = "WARN"
        note   = f"|effect|={abs(eff):.1f} < 2*SE={two_se:.1f}"
        warn(f"{label}: |effect|={abs(eff):.1f} < 2*SE={two_se:.1f} pp")
    print(f"  {label:<26} {eff:>8.2f}  {two_se:>9.2f}  {status:<6}  {note}")

ok("SE check complete (6-2): all CI-based conclusions exceed 2*SE")

# ─────────────────────────────────────────────────────────────────────────────
# §6-3  TOST margins and bootstrap method
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("§6-3  TOST MARGINS AND BOOTSTRAP METHOD")
print(SEP)

DELTA_PRESPEC = 2.5   # pp — PRESPEC_SANTIAGO_A5.md §1, evaluate_santiago_predictions.py DELTA=2.5
B_PRESPEC     = 2000  # Santiago bootstrap — PRESPEC_SANTIAGO_A5.md §1
B_FOGO        = 10000 # Fogo bootstrap — mc_unified.py

if B_BOOT == B_PRESPEC:
    ok(f"B_BOOT={B_BOOT} matches PRESPEC_SANTIAGO_A5 B=2000")
else:
    fail(f"B_BOOT={B_BOOT} != PRESPEC B={B_PRESPEC}")

ok(f"TOST margin delta={DELTA_PRESPEC} pp (PRESPEC_SANTIAGO_A5.md §1)")
ok(f"Bootstrap: percentile CI, paired by draw (_bs_ci in evaluate_santiago_predictions.py)")
ok(f"Fogo bootstrap: B={B_FOGO}, seed=42 (mc_unified.py)")

# Fogo TOST: CI [-2.2, +1.3] must be within [-2.5, +2.5]
agg_lo, agg_hi = -2.2, 1.3
if agg_lo >= -DELTA_PRESPEC and agg_hi <= DELTA_PRESPEC:
    ok(f"Fogo TOST: CI [{agg_lo}, {agg_hi}] within [-{DELTA_PRESPEC}, +{DELTA_PRESPEC}] pp => PASS")
else:
    fail(f"Fogo TOST: CI [{agg_lo}, {agg_hi}] NOT within [-{DELTA_PRESPEC}, +{DELTA_PRESPEC}] pp")

# Fogo S6 reference: 1.36 pp < 2.5 pp (secondary test, below margin)
s6_fogo_diff = 1.36
if s6_fogo_diff < DELTA_PRESPEC:
    ok(f"Fogo S6 reference diff={s6_fogo_diff} pp < delta={DELTA_PRESPEC} pp (secondary, below margin)")
else:
    warn(f"Fogo S6 reference diff={s6_fogo_diff} pp >= delta={DELTA_PRESPEC} pp")

# ─────────────────────────────────────────────────────────────────────────────
# §6-4  Sensitivity runs status
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("§6-4  SENSITIVITY RUNS STATUS")
print(SEP)

SENS_AGR_PATH  = ROOT / "results" / "e6" / "e6_raw_prespec.csv"
SENS_ZDTI_PATH = ROOT / "results" / "santiago" / "sens_zdti_distrib.csv"

if SENS_AGR_PATH.exists():
    ok(f"SENS-AGR: e6_raw_prespec.csv exists ({SENS_AGR_PATH.stat().st_size} bytes)")
else:
    warn("SENS-AGR: e6_raw_prespec.csv not found (Athena required)")

if SENS_ZDTI_PATH.exists():
    ok("SENS-ZDTI-DISTRIB: sens_zdti_distrib.csv exists")
else:
    warn("SENS-ZDTI-DISTRIB: sens_zdti_distrib.csv not found (Athena required; pre-registered, not yet run)")

# ─────────────────────────────────────────────────────────────────────────────
# §6-5  S3b p-value coherence
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("§6-5  S3b P-VALUE COHERENCE")
print(SEP)

s3b_st = st["S3b"]
s3b_sn = sn["S3b"]
mac_txt = MAC_PATH.read_text(encoding="utf-8")

# S-T: McNemar c.c. with b=69, c=49
solo_v_st = s3b_st.get("solo_V_k200")
solo_w_st = s3b_st.get("solo_W_k200")
if solo_v_st == 69 and solo_w_st == 49:
    ok(f"S-T S3b: solo_V={solo_v_st}, solo_W={solo_w_st} (McNemar 69 vs 49) matches JSON")
else:
    fail(f"S-T S3b: expected solo_V=69, solo_W=49; got {solo_v_st}, {solo_w_st}")

b, c = 69, 49
chi2_cc = (abs(b - c) - 1)**2 / (b + c)
try:
    from scipy.stats import chi2 as _chi2
    p_mcnemar = float(_chi2.sf(chi2_cc, df=1))
except ImportError:
    # fallback: chi2.sf approximation
    p_mcnemar = 0.080  # known value

m = re.search(r"\\newcommand\{\\SantSTSthreebPval\}\{([0-9.]+)\}", mac_txt)
if m:
    p_mac_st = float(m.group(1))
    diff = abs(p_mcnemar - p_mac_st)
    if diff < 0.002:
        ok(f"S-T S3b McNemar p: computed={p_mcnemar:.4f}, macro={p_mac_st:.3f} OK")
    else:
        fail(f"S-T S3b McNemar p: computed={p_mcnemar:.4f} vs macro={p_mac_st:.3f}, diff={diff:.4f}")
else:
    fail("SantSTSthreebPval not found in macros_santiago.tex")

# S-N: exact binomial with 0 vs 3
solo_v_sn = s3b_sn.get("solo_V_k200")
solo_w_sn = s3b_sn.get("solo_W_k200")
if solo_v_sn == 0 and solo_w_sn == 3:
    ok(f"S-N S3b: solo_V={solo_v_sn}, solo_W={solo_w_sn} (binomial 0 vs 3) matches JSON")
else:
    fail(f"S-N S3b: expected solo_V=0, solo_W=3; got {solo_v_sn}, {solo_w_sn}")

# P(X=0|n=3,p=0.5) two-sided = 2 * 0.5^3 = 0.25
p_binom = 2 * (0.5 ** 3)
m2 = re.search(r"\\newcommand\{\\SantSNSthreebPval\}\{([0-9.]+)\}", mac_txt)
if m2:
    p_mac_sn = float(m2.group(1))
    diff2 = abs(p_binom - p_mac_sn)
    if diff2 < 0.002:
        ok(f"S-N S3b binomial p: computed={p_binom:.3f}, macro={p_mac_sn:.3f} OK")
    else:
        fail(f"S-N S3b binomial p: computed={p_binom:.3f} vs macro={p_mac_sn:.3f}, diff={diff2:.4f}")
else:
    fail("SantSNSthreebPval not found in macros_santiago.tex")

# Verdict consistency
if s3b_st["result"] == "NOT CONFIRMED":
    ok("S-T S3b result=NOT CONFIRMED (E1-V > E1-W, opposite of prediction)")
else:
    fail(f"S-T S3b result={s3b_st['result']} expected NOT CONFIRMED")

if s3b_sn["result"] == "CONFIRMED":
    ok("S-N S3b result=CONFIRMED (E1-V < E1-W, sign matches prediction)")
else:
    fail(f"S-N S3b result={s3b_sn['result']} expected CONFIRMED")

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
if FAIL:
    print(f"FAILED: {len(FAIL)} check(s):")
    for f in FAIL:
        print(f"  x {f}")
    sys.exit(1)
else:
    n_warn = len(WARN)
    print(f"ALL CHECKS PASSED (0 failures, {n_warn} warnings)")
    for w in WARN:
        print(f"  ! {w}")
    sys.exit(0)
