# Makefile for normalisation paper
# Cross-platform: Linux / macOS / Windows (tested with mingw32-make on Windows)
#
# Usage:
#   make macros     — regenerate macros from data sources (SHA-verified)
#   make check      — run consistency and Santiago macro checks (exit 0 = all pass)
#   make paper      — compile PDF via scripts/build_paper.py + latexmk
#   make all        — macros + check + paper
#   make reproduce  — verify inputs + macros + check + paper (full pipeline)
#   make clean      — remove build/ directory
#
# Requirements: uv, latexmk (any TeX distribution), Python >= 3.10
# Set MCDM_DATA_DIR to the path of the non-versioned GIS data directory.

PYTHON   = uv run python
BUILD    = build/paper
MSRC     = paper/manuscript

.PHONY: all macros check paper markers reproduce clean

all: macros check paper

macros:
	$(PYTHON) scripts/make_santiago_macros.py

check: macros
	$(PYTHON) -X utf8 scripts/run_checks.py

markers:
	$(PYTHON) -c "import subprocess,sys; r=subprocess.run(['python','-c',\"import re,pathlib; files=list(pathlib.Path('paper/manuscript').glob('*.tex')); matches=[f'{f.name}:{i+1}: {l.rstrip()}' for f in files for i,l in enumerate(f.read_text('utf-8',errors='replace').splitlines()) if re.search(r'\\\\[[A-Z-]+\\\\]|TODO|XXX',l) and not l.lstrip().startswith('%')]; [print(m) for m in matches]; sys.exit(1 if matches else 0)\"],capture_output=False); sys.exit(r.returncode)"

paper:
	$(PYTHON) scripts/build_paper.py --build-dir $(BUILD) --src-dir $(MSRC)

reproduce:
	$(PYTHON) -X utf8 scripts/check_inputs.py
	$(PYTHON) scripts/make_santiago_macros.py
	$(PYTHON) -X utf8 scripts/run_checks.py
	$(PYTHON) scripts/build_paper.py --build-dir $(BUILD) --src-dir $(MSRC)

clean:
	$(PYTHON) -c "import shutil; shutil.rmtree('$(BUILD)', ignore_errors=True)"
