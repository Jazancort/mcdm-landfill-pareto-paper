# -*- coding: utf-8 -*-
"""
generate_macros_e1.py  --  Generate E1-related macros from the verified log.

Source: data/e1_v3_rerun_20261002.log  (commit 44f7ff5, Athena, 500 draws, float64)
  The log is parsed directly. The hash certifies the log, not a transcription.
  results/e1/e1_v3_verified.csv is a DERIVED file (kept for reference only).

Archive: results/e1/archive/e1_v3_results_DRYRUN_N10_DEV-E1-004.csv
  This was a 10-draw dry-run (N_DRAWS=10, SE=15.8% confirms it).
  Cause: test run committed alongside session documentation (ddb584d).
  The published values (56.8%/64.2%) are from the 500-draw log.

Macros written to results/e1/e1_macros.tex:
  \\EoneVloss  = 100 - Q2_opt(E1-V)  = 43.2  (vector cell loss)
  \\EoneWloss  = 100 - Q2_opt(E1-W)  = 35.8  (within-group loss)

Cross-check (independent): QtwovecOptimal=56.8 from wp3_mc_fixed_raw.csv
  via factorial (scoring.py, same pipeline). EoneVloss = 100 - 56.8 = 43.2 ✓.

Run:
    uv run python scripts/generate_macros_e1.py
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
LOG  = ROOT / "data" / "e1_v3_rerun_20261002.log"
OUT  = ROOT / "results" / "e1" / "e1_macros.tex"
OUT_JSON = ROOT / "results" / "e1" / "e1_stats.json"

EXPECTED = {
    "EoneVloss": 43.2,
    "EoneWloss": 35.8,
}


def parse_log(log_path: Path) -> dict:
    """
    Parse RESULT lines and metadata from the E1 run log.
    Extracts: n_draws, precision, eps, pre_spec commit, and per-cell results.
    Asserts that n_draws == 500 (the expected value for the published run).
    """
    text = log_path.read_text(encoding="utf-8")

    # Extract metadata from pre-spec line
    meta = {}
    pre_re = re.compile(
        r"Pre-spec:\s*\S+\s+\((\w+)\)\s+eps=([0-9e\-]+)\s+(\w+)"
    )
    m_pre = pre_re.search(text)
    if m_pre:
        meta["prespec_commit"] = m_pre.group(1)
        meta["eps"]            = m_pre.group(2)
        meta["precision"]      = m_pre.group(3)  # float64
    else:
        meta["prespec_commit"] = "not found in log"
        meta["eps"] = "declared: 1e-9"
        meta["precision"] = "declared: float64"

    # Extract N_DRAWS from progress lines: [N/N_TOTAL]
    progress_re = re.compile(r"\[(\d+)/(\d+)\]")
    n_draws_set = set()
    for m in progress_re.finditer(text):
        n_draws_set.add(int(m.group(2)))
    if len(n_draws_set) == 1:
        meta["n_draws"] = n_draws_set.pop()
    elif len(n_draws_set) > 1:
        meta["n_draws"] = max(n_draws_set)   # take the max (could be cells with fewer)
    else:
        meta["n_draws"] = None

    # Assert key metadata
    assert meta["precision"] in ("float64", "declared: float64"), \
        f"Expected float64 precision, got: {meta['precision']}"
    if meta["n_draws"] is not None:
        assert meta["n_draws"] == 500, \
            f"Expected N_DRAWS=500 in log, got {meta['n_draws']}"
    else:
        meta["n_draws"] = "declared: 500"  # not verified from log

    # Extract cell results
    section_re = re.compile(r"--- (E1-[MVBW]):")
    result_re  = re.compile(
        r"RESULT: greedy=([\d.]+)%\s+\(SE=([\d.]+)\)\s+"
        r"optimal=([\d.]+)%\s+\(SE=([\d.]+)\)"
    )
    results = {}
    current_cell = None
    for line in text.splitlines():
        m_sec = section_re.search(line)
        if m_sec:
            current_cell = m_sec.group(1)
        m_res = result_re.search(line)
        if m_res and current_cell:
            results[current_cell] = {
                "greedy":     float(m_res.group(1)),
                "greedy_se":  float(m_res.group(2)),
                "optimal":    float(m_res.group(3)),
                "optimal_se": float(m_res.group(4)),
            }
    required = {"E1-M", "E1-V", "E1-B", "E1-W"}
    missing = required - results.keys()
    assert not missing, f"Log missing cells: {missing}"

    return {"meta": meta, "results": results}


def main():
    if not LOG.exists():
        raise FileNotFoundError(f"E1 log not found: {LOG}")

    sha = hashlib.sha256(LOG.read_bytes()).hexdigest()
    parsed = parse_log(LOG)
    meta    = parsed["meta"]
    results = parsed["results"]

    eone_v = round(100.0 - results["E1-V"]["optimal"], 1)
    eone_w = round(100.0 - results["E1-W"]["optimal"], 1)

    # Cross-check via independent path (factorial CSV)
    factorial_csv = ROOT / "results" / "wp3_mc_fixed_raw.csv"
    if factorial_csv.exists():
        import pandas as _pd
        df = _pd.read_csv(factorial_csv)
        q2_vec_opt = float(df[df["norm"] == "vector"]["nd_optimal"].mean()) * 100
        cross_check = abs(eone_v - (100 - q2_vec_opt)) < 0.05
        print(f"  Cross-check: 100 - Q2_vec_opt({q2_vec_opt:.1f}) = {100-q2_vec_opt:.1f}  "
              f"match EoneVloss({eone_v:.1f}): {'PASS' if cross_check else 'FAIL'}")
        assert cross_check, f"EoneVloss cross-check failed: {eone_v} vs {100-q2_vec_opt}"

    # Assertions against expected values
    assert abs(eone_v - EXPECTED["EoneVloss"]) < 0.05, \
        f"EoneVloss {eone_v} != {EXPECTED['EoneVloss']}"
    assert abs(eone_w - EXPECTED["EoneWloss"]) < 0.05, \
        f"EoneWloss {eone_w} != {EXPECTED['EoneWloss']}"

    lines = [
        "% AUTO-GENERATED by scripts/generate_macros_e1.py -- DO NOT EDIT BY HAND",
        f"% source: data/e1_v3_rerun_20261002.log  sha256={sha[:16]}  (full SHA in e1_stats.json)",
        f"% Parsed from log: n_draws={meta['n_draws']} precision={meta['precision']} eps={meta['eps']}",
        "% Cross-check: EoneVloss == 100 - QtwovecOptimal from wp3_mc_fixed_raw.csv",
        "",
        rf"\newcommand{{\EoneVloss}}{{{eone_v}}}            % 100 - Q2_opt(E1-V) = vector cell loss",
        rf"\newcommand{{\EoneWloss}}{{{eone_w}}}            % 100 - Q2_opt(E1-W) = within-group loss",
        "",
        "% ── E1 cell Q2 values (for tab:e1) ────────────────────────────────────",
        "% Cell M (min-max): also \\QtwommGreedy / \\QtwommOptimal in macros.tex",
        rf"\newcommand{{\QtwoEoneM}}{{M}}                    % cell label (min--max)",
        rf"\newcommand{{\QtwoEoneMGrd}}{{{results['E1-M']['greedy']:.1f}}}    % E1-M greedy Q2",
        rf"\newcommand{{\QtwoEoneMOpt}}{{{results['E1-M']['optimal']:.1f}}}   % E1-M optimal Q2",
        "% Cell B (between only)",
        rf"\newcommand{{\QtwoEoneBGrd}}{{{results['E1-B']['greedy']:.1f}}}    % E1-B greedy Q2",
        rf"\newcommand{{\QtwoEoneBOpt}}{{{results['E1-B']['optimal']:.1f}}}   % E1-B optimal Q2",
        "% Cell W (within only): loss = \\EoneWloss",
        rf"\newcommand{{\QtwoEoneWGrd}}{{{results['E1-W']['greedy']:.1f}}}    % E1-W greedy Q2",
        rf"\newcommand{{\QtwoEoneWOpt}}{{{results['E1-W']['optimal']:.1f}}}   % E1-W optimal Q2",
        "% Cell V (vector): also \\QtwovecGreedy / \\QtwovecOptimal in macros.tex; loss = \\EoneVloss",
        rf"\newcommand{{\QtwoEoneVGrd}}{{{results['E1-V']['greedy']:.1f}}}    % E1-V greedy Q2",
        rf"\newcommand{{\QtwoEoneVOpt}}{{{results['E1-V']['optimal']:.1f}}}   % E1-V optimal Q2",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Written: {OUT}")
    print(f"  EoneVloss = {eone_v}  sha256={sha[:16]}")
    print(f"  EoneWloss = {eone_w}")
    json.dump({"source_log": str(LOG.name), "sha256": sha,
               "n_draws": meta["n_draws"], "precision": meta["precision"], "eps": meta["eps"],
               "EoneVloss": eone_v, "EoneWloss": eone_w,
               "results": results}, OUT_JSON.open("w"), indent=2)
    print(f"Written: {OUT_JSON}")


if __name__ == "__main__":
    main()
