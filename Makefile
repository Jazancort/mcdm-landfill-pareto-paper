# Makefile for normalisation paper
# Windows-compatible (uses uv run python and xelatex)
# Usage:
#   make macros   — regenerate macros.tex from CSV results
#   make check    — run consistency checks (exit 1 if any fail)
#   make paper    — compile main.tex with xelatex (2 passes)
#   make all      — macros + check + paper (NEXT)
#   make clean    — remove auxiliary LaTeX files

PYTHON   = uv run python
XELATEX  = xelatex -interaction=nonstopmode

.PHONY: macros check paper all clean

all: macros check paper

macros:
	$(PYTHON) scripts/generate_macros.py

check: macros
	$(PYTHON) scripts/check_consistency.py

paper:
	$(XELATEX) main.tex
	$(XELATEX) main.tex

clean:
	del /Q *.aux *.log *.out *.toc *.bbl *.blg *.fls *.fdb_latexmk 2>nul || true
