# Makefile for normalisation paper
# Windows-compatible (uses uv run python and pdflatex)
#
SHELL = cmd.exe
#
# Single source of truth: paper/manuscript/main.tex
# src/main.tex is DEPRECATED (removed 2026-11-04, writing-santiago branch).
#
# IMPORTANT: Compile in C:\build\paper (not G:) to avoid Google Drive sync
# truncating the .bbl file between bibtex and pdflatex calls.
#
# Note on xelatex: MiKTeX 26.5 xelatex crashes on 2nd pass with FATAL
# fwrite EINVAL (C4P.h:531) due to STIX font file handle conflict on Windows.
# pdflatex works correctly (0 undefined cross-references, same page count).
#
# Usage:
#   make macros   - regenerate macros.tex from CSV results
#   make check    - run consistency checks (exit 1 if any fail)
#   make paper    - compile in C:\build\paper (pdflatex + bibtex + 2x pdflatex)
#   make markers  - fail if [PLACEHOLDER] or TODO markers remain in .tex sources
#   make all      - macros + check + markers + paper
#   make clean    - remove auxiliary LaTeX files (does NOT delete main.bbl)

PYTHON    = uv run python
PDFLATEX  = pdflatex -interaction=nonstopmode
BUILDDIR  = C:\build\paper
SRCDIR    = $(CURDIR)
MSRC      = $(SRCDIR)\paper\manuscript

.PHONY: macros check paper markers all clean

all: macros check markers paper

macros:
	$(PYTHON) scripts/generate_macros.py
	$(PYTHON) scripts/make_santiago_macros.py

check: macros
	$(PYTHON) scripts/check_tab_amplitude.py
	$(PYTHON) scripts/generate_macros_r1.py
	$(PYTHON) scripts/check_consistency.py
	$(PYTHON) scripts/verify_macros_permanent.py --santiago

markers:
	@$(PYTHON) -c "import subprocess, sys; r=subprocess.run(['powershell','-Command','Select-String -Path paper\\\\manuscript\\\\*.tex -Pattern \"\\\\[[A-Z-]+\\\\]|TODO|XXX\" | ForEach-Object { \\\"$$($$.Filename):$$($$.LineNumber): $$($$.Line)\\\" }'],capture_output=True,text=True,cwd=r'$(SRCDIR)'); out=r.stdout.strip(); sys.exit(1 if out else 0) if (print('MARKERS FOUND:\\n'+out) if out else print('markers: OK')) else None"

paper:
	if not exist "$(BUILDDIR)" mkdir "$(BUILDDIR)"
	xcopy /E /Y /Q "$(MSRC)\*"     "$(BUILDDIR)\"     >nul 2>&1
	xcopy /E /Y /Q "$(SRCDIR)\results\*" "$(BUILDDIR)\results\" >nul 2>&1
	xcopy /E /Y /Q "$(SRCDIR)\figures\*" "$(BUILDDIR)\figures\" >nul 2>&1
	copy /Y "$(SRCDIR)\macros\macros_e7.tex"       "$(BUILDDIR)\macros_e7.tex"       >nul
	copy /Y "$(SRCDIR)\macros\macros_kappa_inf.tex" "$(BUILDDIR)\macros_kappa_inf.tex" >nul
	-cd /d "$(BUILDDIR)" && $(PDFLATEX) main.tex
	-cd /d "$(BUILDDIR)" && bibtex main
	-cd /d "$(BUILDDIR)" && $(PDFLATEX) suppl_wrapper.tex
	-cd /d "$(BUILDDIR)" && $(PDFLATEX) main.tex
	-cd /d "$(BUILDDIR)" && $(PDFLATEX) main.tex
	copy /Y "$(BUILDDIR)\main.bbl" "$(MSRC)\main.bbl"
	copy /Y "$(BUILDDIR)\main.pdf" "$(MSRC)\main.pdf"
	copy /Y "$(BUILDDIR)\suppl_wrapper.aux" "$(MSRC)\suppl_wrapper.aux"
	copy /Y "$(BUILDDIR)\suppl_wrapper.pdf" "$(MSRC)\suppl_wrapper.pdf"

clean:
	del /Q "$(MSRC)\*.aux" "$(MSRC)\*.log" "$(MSRC)\*.out" "$(MSRC)\*.toc" "$(MSRC)\*.blg" "$(MSRC)\*.fls" "$(MSRC)\*.fdb_latexmk" 2>nul || true
	@rem NOTE: main.bbl is NOT deleted — bibtex must run to regenerate it.
