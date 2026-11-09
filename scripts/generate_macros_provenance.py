# -*- coding: utf-8 -*-
"""generate_macros_provenance.py — Build results/macros_provenance.csv.

For each \\newcommand{\\MacroName}{value} found in any macros*.tex file,
records: macro name, value, source .tex file, generator script (from
the file header comment), and SHA-256 of the source .tex file.

The make check step (via run_checks.py) calls check_macros_provenance.py
which verifies that every macro used in the manuscript has an entry here.

Usage:
    uv run python scripts/generate_macros_provenance.py

Output: results/macros_provenance.csv  (overwritten)
"""
import sys
import re
import csv
import hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
OUT  = ROOT / "results" / "macros_provenance.csv"

# ─────────────────────────────────────────────────────────────────────────────
# §1  Macro source files (in input order)
# ─────────────────────────────────────────────────────────────────────────────

MACRO_FILES = [
    ROOT / "macros" / "macros_structural.tex",
    ROOT / "macros" / "macros_amplitudes.tex",
    ROOT / "macros" / "macros.tex",
    ROOT / "macros" / "macros_raw_sens.tex",
    ROOT / "macros" / "macros_e6.tex",
    ROOT / "macros" / "macros_f8.tex",
    ROOT / "macros" / "macros_e7.tex",
    ROOT / "macros" / "macros_kappa_inf.tex",
    ROOT / "results" / "regret" / "regret_macros.tex",
    ROOT / "results" / "santiago" / "macros_santiago.tex",
    ROOT / "results" / "santiago" / "macros_descriptive.tex",
    ROOT / "results" / "e1" / "e1_macros.tex",
]

# ─────────────────────────────────────────────────────────────────────────────
# §2  Extract generator script from file header
# ─────────────────────────────────────────────────────────────────────────────

_GENERATOR_RE = re.compile(
    r'%\s*AUTO-GENERATED\s+by\s+(scripts/\S+\.py)',
    re.IGNORECASE
)

def extract_generator(text):
    m = _GENERATOR_RE.search(text[:500])
    return m.group(1) if m else "manually maintained"

# ─────────────────────────────────────────────────────────────────────────────
# §3  Extract macros from a .tex file
# ─────────────────────────────────────────────────────────────────────────────

_NEWCMD_RE = re.compile(
    r'\\(?:re)?newcommand\{\\([A-Za-z0-9]+)\}(?:\[\d+\])?\{([^}]*)\}'
    r'|\\providecommand\{\\([A-Za-z0-9]+)\}(?:\[\d+\])?\{([^}]*)\}'
)

def extract_macros(path):
    if not path.exists():
        print(f"  [WARN] not found: {path}", flush=True)
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    generator = extract_generator(text)
    rel_path = str(path.relative_to(ROOT)).replace("\\", "/")
    macros = []
    for m in _NEWCMD_RE.finditer(text):
        # Handle both \newcommand and \providecommand patterns
        name = m.group(1) or m.group(3)
        value = (m.group(2) or m.group(4) or "").strip()
        if name:
            macros.append({
                "macro": name,
                "value": value,
                "source_tex": rel_path,
                "generator": generator,
                "sha256_16": sha,
            })
    return macros

# ─────────────────────────────────────────────────────────────────────────────
# §4  Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    all_macros = []
    seen = set()
    for path in MACRO_FILES:
        macros = extract_macros(path)
        for m in macros:
            if m["macro"] not in seen:
                seen.add(m["macro"])
                all_macros.append(m)
            # else: later \renewcommand overrides earlier; keep first definition
            # (the override is noted in macros.tex comments)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["macro", "value", "source_tex", "generator", "sha256_16"]
        )
        writer.writeheader()
        writer.writerows(all_macros)

    print(f"Wrote {len(all_macros)} macros to {OUT}", flush=True)

if __name__ == "__main__":
    main()
