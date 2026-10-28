# -*- coding: utf-8 -*-
"""fix_notation_504.py — replace plain A/A' for spaces with \\Aspace macro (5.04)"""
import re
from pathlib import Path

tex = Path("main.tex").read_text(encoding="utf-8")

replacements = [
    # space~$A$ -> space~$\Aspace$
    ("space~$A$", r"space~$\Aspace$"),
    # space~$A'$ -> space~$\Aspace'$
    ("space~$A'$", r"space~$\Aspace'$"),
    # $A$ and $A'$ -> $\Aspace$ and $\Aspace'$
    ("$A$ and $A'$", r"$\Aspace$ and $\Aspace'$"),
    # Q_2[A'] -> Q_2[\Aspace']
    ("Q_2[A']", r"Q_2[\Aspace']"),
    # in $A'$ (normalisation context at line 1000)
    ("sites not present in $A'$)", r"sites not present in $\Aspace'$)"),
]

count = 0
for old, new in replacements:
    n = tex.count(old)
    tex = tex.replace(old, new)
    print(f"  {old!r:50} -> {n} replacements")
    count += n

Path("main.tex").write_text(tex, encoding="utf-8")
print(f"\nTotal: {count} replacements")
