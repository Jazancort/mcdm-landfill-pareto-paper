# Makefile for normalisation paper
# Windows-compatible (uses uv run python and xelatex)
#
# IMPORTANT: Compile in C:\build\paper (not G:) to avoid Google Drive sync
# truncating the .bbl file between bibtex and xelatex calls.
#
# Usage:
#   make macros   - regenerate macros.tex from CSV results
#   make check    - run consistency checks (exit 1 if any fail)
#   make paper    - compile in C:\build\paper (xelatex + bibtex + 2x xelatex)
#   make all      - macros + check + paper
#   make clean    - remove auxiliary LaTeX files (does NOT delete main.bbl)

PYTHON   = uv run python
XELATEX  = xelatex -interaction=nonstopmode
BUILDDIR = C:\build\paper
SRCDIR   = $(CURDIR)

.PHONY: macros check paper all clean

all: macros check paper

macros:
	$(PYTHON) scripts/generate_macros.py

check: macros
	$(PYTHON) scripts/check_tab_amplitude.py
	$(PYTHON) scripts/generate_macros_r1.py
	$(PYTHON) scripts/check_consistency.py

paper:
	if not exist "$(BUILDDIR)" mkdir "$(BUILDDIR)"
	xcopy /E /Y /Q "$(SRCDIR)\*" "$(BUILDDIR)\" >nul 2>&1
	cd "$(BUILDDIR)\src" && set "TEXINPUTS=.;..\template;;" && $(XELATEX) main.tex
	cd "$(BUILDDIR)\src" && set "BSTINPUTS=.;..\template;;" && bibtex main
	cd "$(BUILDDIR)\src" && set "TEXINPUTS=.;..\template;;" && $(XELATEX) suppl_wrapper.tex
	cd "$(BUILDDIR)\src" && set "TEXINPUTS=.;..\template;;" && $(XELATEX) main.tex
	cd "$(BUILDDIR)\src" && set "TEXINPUTS=.;..\template;;" && $(XELATEX) main.tex
	copy /Y "$(BUILDDIR)\src\main.bbl" "$(SRCDIR)\src\main.bbl"
	copy /Y "$(BUILDDIR)\src\main.pdf" "$(SRCDIR)\src\main.pdf"
	copy /Y "$(BUILDDIR)\src\suppl_wrapper.aux" "$(SRCDIR)\src\suppl_wrapper.aux"
	copy /Y "$(BUILDDIR)\src\suppl_wrapper.pdf" "$(SRCDIR)\src\suppl_wrapper.pdf"

clean:
	del /Q *.aux *.log *.out *.toc *.blg *.fls *.fdb_latexmk 2>nul || true
	@rem NOTE: main.bbl is NOT deleted — bibtex must run to regenerate it.
