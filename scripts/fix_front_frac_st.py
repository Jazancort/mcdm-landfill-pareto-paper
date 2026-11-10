# -*- coding: utf-8 -*-
"""fix_front_frac_st.py — Fix FrontFracST precision to 4 decimal places."""
import json
from pathlib import Path

ROOT    = Path(__file__).parent.parent
RESULTS = ROOT / "results" / "santiago"

d = json.loads((RESULTS / "descriptive_output.json").read_text(encoding="utf-8"))

front_size = d["frontier_st"]["front_size"]
n_trios    = d["frontier_st"]["n_trios"]
frac_pct   = round(front_size / n_trios * 100, 4)

print(f"front_size={front_size}, n_trios={n_trios:,}, frac_pct={frac_pct}")

d["frontier_st"]["fraction_pct"] = frac_pct
(RESULTS / "descriptive_output.json").write_text(
    json.dumps(d, indent=2), encoding="utf-8")
print("JSON updated")

macros_path = RESULTS / "macros_descriptive.tex"
lines = macros_path.read_text(encoding="utf-8").splitlines()
lines = [l for l in lines
         if "FrontFracST" not in l and "S-T frontier fraction: pending" not in l]
while lines and lines[-1].strip() == "":
    lines.pop()
lines += [
    "",
    f"\\newcommand{{\\FrontFracST}}{{{frac_pct}}}",
    f"% |F|={front_size}, |T|={n_trios}",
]
macros_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("Macro updated")
print(f"\n  => \\FrontFracST{{{frac_pct}}}")
