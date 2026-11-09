"""
check_tab_amplitude.py  --  Verify tab:amplitude values against amplitudes.json
================================================================================
Reads the A_vec column from tab:amplitude in main.tex and compares each value
against amplitudes.json["rho_j"] at 3 decimal places.

Also checks TV_vec bottom row.

Exit code 0 = all match. Exit code 1 = at least one mismatch.
"""

import json, re, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

AMP_JSON = ROOT / "results" / "amplitudes" / "amplitudes.json"
MAIN_TEX = ROOT / "paper" / "manuscript" / "main.tex"

# ── Load amplitudes.json ───────────────────────────────────────────────────
with open(AMP_JSON) as f:
    amp = json.load(f)

rho_j = amp["rho_j"]  # dict: crit -> float
tv_vec = amp["TV_vec"]

print(f"amplitudes.json: TV_vec={tv_vec:.3f}")
print()

# ── Parse tab:amplitude from main.tex ─────────────────────────────────────
tex = MAIN_TEX.read_text(encoding="utf-8")

# Find the table rows between \label{tab:amplitude} and \end{table*}
# Each data row: \textit{name} & group & w_j & A_mm & A_vec & A_rank & ...
# We match: \textit{CRIT} & ... & A_vec_val & A_rank_val ...
TABLE_START = r"\label{tab:amplitude}"
TABLE_END   = r"\end{table*}"

start = tex.find(TABLE_START)
end   = tex.find(TABLE_END, start)
assert start != -1 and end != -1, "tab:amplitude not found in main.tex"
table_block = tex[start:end]

# Match rows: \textit{name} & group & w_j & A_mm & A_vec & A_rank & weff_vec & weff_rank
ROW_PATTERN = re.compile(
    r"\\textit\{(\w+)\}\s*&\s*\$[^$]+\$\s*&\s*([\d.]+)\s*"  # name & group & w_j
    r"&\s*([\d.]+)\s*"  # A_mm
    r"&\s*([\d.]+)\s*"  # A_vec
    r"&\s*([\d.]+)\s*",  # A_rank
    re.DOTALL
)

# Also match TV row: $\mathrm{TV}$ & & & TV_mm & TV_vec & TV_rank
# TV_vec may be a literal number or a macro like $\TVvec$
TV_PATTERN = re.compile(
    r"\\mathrm\{TV\}.*?&\s*&\s*&\s*([\d.]+)\s*&\s*(\$?\\?[\w{}$]+)\s*&\s*([\d.]+)",
    re.DOTALL
)

print("=== Checking A_vec column ===")
failures = []
rows_found = 0
for m in ROW_PATTERN.finditer(table_block):
    crit    = m.group(1)
    a_vec   = float(m.group(4))  # A_vec from table

    if crit not in rho_j:
        print(f"  SKIP {crit}: not in rho_j dict")
        continue

    expected = round(rho_j[crit], 3)
    actual   = round(a_vec, 3)
    ok = abs(expected - actual) < 0.0005

    rows_found += 1
    status = "OK  " if ok else "FAIL"
    print(f"  [{status}] {crit:10}: table={actual:.3f}  json={expected:.3f}  "
          f"diff={abs(expected-actual):.4f}")

    if not ok:
        failures.append(f"{crit}: table={actual:.3f} vs json={expected:.3f}")

print()
print(f"  Rows checked: {rows_found}/11")

# TV row
print()
print("=== Checking TV_vec ===")
tv_m = TV_PATTERN.search(table_block)
tv_verified = False
if tv_m:
    tv_cell = tv_m.group(2).strip()
    # tv_cell may be a literal float or a macro like $\TVvec$
    import re as _re
    lit_m = _re.match(r'^[\d.]+$', tv_cell)
    if lit_m:
        tv_table = float(tv_cell)
    else:
        # extract macro name and resolve from macros_amplitudes.tex
        mac_name_m = _re.search(r'\\(\w+)', tv_cell)
        if mac_name_m:
            mac_name = mac_name_m.group(1)
            mac_tex_path = ROOT / "macros" / "macros_amplitudes.tex"
            if mac_tex_path.exists():
                mac_tex = mac_tex_path.read_text(encoding="utf-8")
                mac_val_m = _re.search(rf'\\(?:re)?newcommand\{{\\{mac_name}\}}\{{([\d.]+)\}}', mac_tex)
                tv_table = float(mac_val_m.group(1)) if mac_val_m else None
            else:
                tv_table = None
        else:
            tv_table = None
    if tv_table is not None:
        expected_tv = round(tv_vec, 3)
        ok = abs(tv_table - expected_tv) < 0.0005
        status = "OK  " if ok else "FAIL"
        print(f"  [{status}] TV_vec: table={tv_table:.3f}  json={expected_tv:.3f}  (cell={tv_cell!r})")
        if not ok:
            failures.append(f"TV_vec: table={tv_table:.3f} vs json={expected_tv:.3f}")
        else:
            tv_verified = True
    else:
        failures.append(f"TV_vec: could not resolve cell value {tv_cell!r}")
        print(f"  [FAIL] TV_vec: could not resolve cell value {tv_cell!r}")
else:
    failures.append("TV row not found in tab:amplitude")
    print("  [FAIL] TV row not found in tab:amplitude")

print()
if failures:
    print(f"FAILED: {len(failures)} mismatches:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    tv_suffix = " + TV_vec" if tv_verified else ""
    print(f"ALL OK: tab:amplitude matches amplitudes.json at 3dp ({rows_found} values{tv_suffix})")
