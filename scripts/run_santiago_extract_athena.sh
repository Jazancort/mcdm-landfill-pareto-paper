#!/bin/bash
# run_santiago_extract_athena.sh
# Stage 2 extraction of Santiago criteria on Athena.
# Usage: bash scripts/run_santiago_extract_athena.sh [ST|SN|both]
# Depends: data/santiago/*.tif, data/santiago/*.pbf, data/santiago/*.geojson

set -euo pipefail
BRANCH=${1:-ST}

cd ~/scratch/mcdm-landfill-pareto-paper

echo "=== Santiago Stage 2 extraction — branch $BRANCH ==="
echo "$(date)"

# Verify environment
python -c "import rasterio, pyrosm, geopandas, scipy; print('deps OK')"

# Run extraction
PYTHONIOENCODING=utf-8 uv run python scripts/santiago_extract.py \
    --branch "$BRANCH" 2>&1 | tee "results/santiago/extract_${BRANCH}.log"

echo ""
echo "=== DONE $(date) ==="
echo "Check results/santiago/df_santiago_st.csv"
