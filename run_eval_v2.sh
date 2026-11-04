#!/bin/bash
set -e
cd ~/scratch/mcdm-landfill-pareto-paper
MCDM_DATA_DIR=/home/julioazancort/scratch/mcdm CUDA_VISIBLE_DEVICES=0 \
  .venv/bin/python3 -u scripts/evaluate_santiago_predictions.py \
  2>&1 | tee results/santiago/eval_v2_full_20261104.log
echo "EVAL_DONE_exit=${PIPESTATUS[0]}" >> results/santiago/eval_v2_full_20261104.log
