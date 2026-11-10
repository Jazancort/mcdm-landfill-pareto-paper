# -*- coding: utf-8 -*-
"""check_refs.py — Ronda 9-1/9-2: verify refs.bib DOIs against Crossref.

For each entry with a DOI:
  - Resolve via api.crossref.org/works/<DOI>
  - Compare title (fuzzy), year, first author family name
  - Report MISMATCH / WARN / OK
  - Check retraction flag (Crossref update-to type=retraction)

Entries without DOI are listed separately.

Usage:
    uv run python scripts/check_refs.py

Output: results/refs_check.csv  (overwritten)
        prints structured report to stdout
"""

from __future__ import annotations
import re, sys, time, json, pathlib, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).parent.parent
BIB  = ROOT / "src" / "refs.bib"
OUT  = ROOT / "results" / "refs_check.csv"

# ─────────────────────────────────────────────────────────────────────────────
# §1  Parse refs.bib
# ─────────────────────────────────────────────────────────────────────────────

def _clean(s: str) -> str:
    """Strip LaTeX markup and normalise whitespace."""
    s = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', s)   # \cmd{x} → x
    s = re.sub(r'[{}\\]', '', s)
    return re.sub(r'\s+', ' ', s).strip()

def parse_bib(path: pathlib.Path) -> list[dict]:
    text  = path.read_text(encoding="utf-8")
    blocks = re.split(r'\n(?=@)', text)
    entries = []
    for block in blocks:
        m = re.match(r'@(\w+)\{([^,]+),', block)
        if not m:
            continue
        etype = m.group(1).lower()
        key   = m.group(2).strip()
        if etype in ("comment", "string", "preamble"):
            continue

        def field(name: str) -> str:
            pat = rf'\b{name}\s*=\s*[{{\"](.*?)[}}\"]'
            fm = re.search(pat, block, re.IGNORECASE | re.DOTALL)
            return _clean(fm.group(1)) if fm else ""

        # DOI: accept only lines with doi = {10....}
        doi_m = re.search(r'\bdoi\s*=\s*\{(10\.[^\s}]+)\}', block, re.IGNORECASE)
        doi   = doi_m.group(1).strip().rstrip(",") if doi_m else ""

        # author: first family name
        auth_m = re.search(r'\bauthor\s*=\s*\{(.*?)\}(?:\s*,|\s*\})', block,
                           re.IGNORECASE | re.DOTALL)
        author_raw = _clean(auth_m.group(1)) if auth_m else ""
        # "Family, Given and ..." → first token before comma or "and"
        first_author = re.split(r',|\band\b', author_raw)[0].strip()

        entries.append({
            "key":    key,
            "etype":  etype,
            "doi":    doi,
            "year":   field("year"),
            "title":  field("title")[:120],
            "author": first_author,
        })
    return entries

# ─────────────────────────────────────────────────────────────────────────────
# §2  Crossref lookup
# ─────────────────────────────────────────────────────────────────────────────

CROSSREF = "https://api.crossref.org/works/{doi}"
HEADERS  = {"User-Agent": "mcdm-landfill-check/1.0 (mailto:julioazancortneto@gmail.com)"}

def crossref_get(doi: str) -> dict | None:
    url = CROSSREF.format(doi=urllib.parse.quote(doi, safe="/.()"))
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())["message"]
    except Exception:
        return None

import urllib.parse  # noqa: E402 (needed above)

def _title_from_cr(msg: dict) -> str:
    titles = msg.get("title") or []
    return _clean(titles[0]) if titles else ""

def _year_from_cr(msg: dict) -> str:
    dp = (msg.get("published") or msg.get("published-print") or
          msg.get("published-online") or {}).get("date-parts", [[]])
    return str(dp[0][0]) if dp and dp[0] else ""

def _author_from_cr(msg: dict) -> str:
    authors = msg.get("author") or []
    if not authors:
        return ""
    return authors[0].get("family", "")

def _is_retracted(msg: dict) -> bool:
    for upd in msg.get("update-to", []):
        if upd.get("type", "").lower() == "retraction":
            return True
    return False

def title_sim(a: str, b: str) -> float:
    """Simple word-overlap Jaccard similarity (case-insensitive)."""
    wa = set(re.findall(r'\w+', a.lower()))
    wb = set(re.findall(r'\w+', b.lower()))
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)

# ─────────────────────────────────────────────────────────────────────────────
# §3  Main
# ─────────────────────────────────────────────────────────────────────────────

SEP  = "=" * 72
SEP2 = "-" * 72

def main() -> int:
    offline = "--offline" in sys.argv
    entries = parse_bib(BIB)
    with_doi    = [e for e in entries if e["doi"]]
    without_doi = [e for e in entries if not e["doi"]]

    if offline:
        print(SEP)
        print("§9-1  CHECK_REFS — offline mode (DOI list only, no network)")
        print(SEP)
        print(f"  Total entries : {len(entries)}")
        print(f"  With DOI      : {len(with_doi)}")
        print(f"  Without DOI   : {len(without_doi)}")
        print()
        print("  Entries WITHOUT DOI:")
        for e in without_doi:
            print(f"    {e['key']} ({e['year']}): {e['title'][:70]}")
        print()
        print("[OK] offline — run 'uv run python scripts/check_refs.py' for full check")
        return 0

    print(SEP)
    print("§9-1/9-2  CHECK_REFS — Crossref verification + retraction check")
    print(SEP)
    print(f"  Total bib entries : {len(entries)}")
    print(f"  With DOI          : {len(with_doi)}")
    print(f"  Without DOI       : {len(without_doi)}")
    print()

    # ── 9-1: entries without DOI ─────────────────────────────────────────────
    print(SEP2)
    print("§9-1a  ENTRIES WITHOUT DOI")
    print(SEP2)
    for e in without_doi:
        print(f"  NO-DOI  {e['key']} ({e['year']}): {e['title'][:70]}")
    print()

    # ── 9-1/9-2: resolve DOIs ────────────────────────────────────────────────
    print(SEP2)
    print("§9-1b  DOI RESOLUTION (Crossref) + §9-2 RETRACTION CHECK")
    print(SEP2)

    rows = []
    fails = 0
    retracted = []

    for e in with_doi:
        doi = e["doi"]
        msg = crossref_get(doi)
        time.sleep(0.35)   # polite rate-limit

        if msg is None:
            status = "NOT_FOUND"
            cr_title = cr_year = cr_author = ""
            sim = 0.0
            retract = False
        else:
            cr_title  = _title_from_cr(msg)
            cr_year   = _year_from_cr(msg)
            cr_author = _author_from_cr(msg)
            retract   = _is_retracted(msg)
            sim       = title_sim(e["title"], cr_title)

            if sim >= 0.55:
                status = "OK"
            elif sim >= 0.30:
                status = "WARN"
            else:
                status = "MISMATCH"

        if status in ("MISMATCH", "NOT_FOUND"):
            fails += 1
        if retract:
            retracted.append(e["key"])

        rows.append({
            "key": e["key"], "doi": doi, "bib_year": e["year"],
            "cr_year": cr_year, "bib_title": e["title"][:80],
            "cr_title": cr_title[:80], "bib_author": e["author"],
            "cr_author": cr_author, "sim": round(sim, 3),
            "status": status, "retracted": retract,
        })

        icon = "✓" if status == "OK" else ("?" if status == "WARN" else "✗")
        ret_flag = " [RETRACTED]" if retract else ""
        print(f"  {icon} {e['key']} ({e['year']}) sim={sim:.2f} {status}{ret_flag}")
        if status != "OK":
            print(f"      bib : {e['title'][:70]}")
            print(f"      cr  : {cr_title[:70]}")
            if e["year"] and cr_year and e["year"] != cr_year:
                print(f"      year: bib={e['year']} cr={cr_year}")
            if e["author"] and cr_author and e["author"].lower() not in cr_author.lower():
                print(f"      auth: bib={e['author']} cr={cr_author}")

    # ── Summary ──────────────────────────────────────────────────────────────
    ok_n    = sum(1 for r in rows if r["status"] == "OK")
    warn_n  = sum(1 for r in rows if r["status"] == "WARN")
    miss_n  = sum(1 for r in rows if r["status"] == "MISMATCH")
    nf_n    = sum(1 for r in rows if r["status"] == "NOT_FOUND")

    print()
    print(SEP)
    print("SUMMARY")
    print(SEP)
    print(f"  OK        : {ok_n}")
    print(f"  WARN      : {warn_n}  (title similarity 0.30–0.54; review manually)")
    print(f"  MISMATCH  : {miss_n}  (title similarity < 0.30)")
    print(f"  NOT_FOUND : {nf_n}  (DOI did not resolve)")
    print(f"  RETRACTED : {len(retracted)}")
    if retracted:
        for k in retracted:
            print(f"    [RETRACTED] {k}")
    print()

    # ── Write CSV ─────────────────────────────────────────────────────────────
    OUT.parent.mkdir(parents=True, exist_ok=True)
    import csv
    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        w.writeheader()
        w.writerows(rows)
    print(f"  Wrote: {OUT}", flush=True)

    # ── Exit code ─────────────────────────────────────────────────────────────
    if fails > 0 or retracted:
        print(f"\n[FAIL] {fails} MISMATCH/NOT_FOUND + {len(retracted)} RETRACTED")
        return 1
    if warn_n > 0:
        print(f"\n[WARN] {warn_n} entries need manual review (WARN)")
    else:
        print("\n[OK] All DOIs verified — no mismatches, no retractions")
    return 0

if __name__ == "__main__":
    sys.exit(main())
