# -*- coding: utf-8 -*-
"""build_paper.py -- cross-platform LaTeX build (Linux / macOS / Windows).

Usage:
    uv run python scripts/build_paper.py [--build-dir build/paper] [--src-dir paper/manuscript]

Requires latexmk and bibtex on PATH (installed with any TeX distribution).
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _cp(src: Path, dst: Path) -> None:
    """Copy file; create parent if needed."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))


def _cp_tree(src: Path, dst: Path) -> None:
    """Copy directory tree, handling read-only files on Windows."""
    if dst.exists():
        import stat as _stat
        def _rm_readonly(func, path, _):
            import os as _os
            _os.chmod(path, _stat.S_IWRITE)
            func(path)
        shutil.rmtree(str(dst), onerror=_rm_readonly)
    shutil.copytree(str(src), str(dst))


def _cp_tex_ascii(src: Path, dst: Path) -> None:
    """Copy .tex file replacing non-ASCII bytes with '-'.
    pdflatex without inputenc cannot process UTF-8 in the preamble.
    Macro values are always ASCII; only comments contain non-ASCII chars.
    """
    raw = src.read_bytes()
    ascii_bytes = bytes(b if b < 128 else ord('-') for b in raw)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(ascii_bytes)


def _cp_macros_tex(src: Path, dst: Path) -> None:
    """Copy macros.tex adjusting \\input paths for build/paper/ context.

    macros.tex uses:
      \\input{../results/e1/e1_macros}   -> \\input{results/e1/e1_macros}
      \\input{../macros/macros_structural} -> \\input{macros_structural}
    These paths work when compiled from paper/manuscript/ but not from
    build/paper/ (where ../results/ would point to build/results/ which
    does not exist). We adjust them to be relative to build/paper/.
    """
    raw = src.read_bytes()
    # Replace non-ASCII bytes with '-' first
    ascii_bytes = bytes(b if b < 128 else ord('-') for b in raw)
    # Adjust paths (all ASCII after substitution)
    text = ascii_bytes.decode('ascii')
    text = text.replace('\\input{../results/', '\\input{results/')
    text = text.replace('\\input{../macros/', '\\input{')
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(text.encode('ascii'))


def _run(args, cwd):
    r = subprocess.run(args, cwd=str(cwd))
    if r.returncode != 0:
        print(f"ERROR: {' '.join(str(a) for a in args)} returned {r.returncode}",
              file=sys.stderr)
        sys.exit(r.returncode)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build-dir", default="build/paper")
    p.add_argument("--src-dir",   default="paper/manuscript")
    args = p.parse_args()

    BUILD = ROOT / args.build_dir
    MSRC  = ROOT / args.src_dir

    print(f"Build dir : {BUILD}")
    print(f"Source dir: {MSRC}")

    # -- 1. Set up build directory -----------------------------------------------
    BUILD.mkdir(parents=True, exist_ok=True)

    # Copy all manuscript files (tex, cls, sty, bst, bib, thumbnails, ...)
    for item in MSRC.iterdir():
        dst = BUILD / item.name
        if item.is_dir():
            _cp_tree(item, dst)
        else:
            _cp(item, dst)

    # Copy figures directory
    _cp_tree(ROOT / "figures", BUILD / "figures")

    # Copy all .tex files from results/ recursively
    results_src = ROOT / "results"
    results_dst = BUILD / "results"
    for tex_file in results_src.rglob("*.tex"):
        rel = tex_file.relative_to(results_src)
        _cp_tex_ascii(tex_file, results_dst / rel)

    # Copy ALL macros/*.tex to build/paper/ (source of truth since Ronda 2a).
    # macros.tex needs path adjustment; others are copied with ASCII sanitisation.
    for f in (ROOT / "macros").glob("macros*.tex"):
        if f.name == "macros.tex":
            _cp_macros_tex(f, BUILD / f.name)
        else:
            _cp_tex_ascii(f, BUILD / f.name)

    # -- 2. Compile --------------------------------------------------------------
    pdflatex = ["pdflatex", "-halt-on-error", "-interaction=nonstopmode"]
    latexmk  = ["latexmk", "-pdf", "-halt-on-error", "-interaction=nonstopmode"]

    print("\n[1/4] pdflatex main.tex (pass 1 -- create main.aux) ...")
    _run(pdflatex + ["main.tex"], cwd=BUILD)

    print("[2/4] bibtex main ...")
    _run(["bibtex", "main"], cwd=BUILD)

    print("[3/4] compiling suppl_wrapper.tex (reads main.aux) ...")
    _run(pdflatex + ["suppl_wrapper.tex"], cwd=BUILD)
    _run(pdflatex + ["suppl_wrapper.tex"], cwd=BUILD)  # extra pass for outlines

    print("[4/4] latexmk main.tex (full run, reads suppl_wrapper.aux) ...")
    _run(latexmk + ["main.tex"], cwd=BUILD)

    # -- 3. Copy outputs back into source tree -----------------------------------
    for f in ["main.pdf", "main.bbl", "main.log",
              "suppl_wrapper.aux", "suppl_wrapper.pdf", "suppl_wrapper.log"]:
        _cp(BUILD / f, MSRC / f)

    print(f"\nDone.  PDF -> {MSRC / 'main.pdf'}")


if __name__ == "__main__":
    main()
