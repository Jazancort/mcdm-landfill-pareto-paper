#!/usr/bin/env bash
set -e
cd /home/julioazancort/scratch/mcdm-landfill-pareto

for w in 0 1 2 3; do
    tmux kill-session -t wp4_w${w} 2>/dev/null || true
    tmux new-session -d -s wp4_w${w} "cd /home/julioazancort/scratch/mcdm-landfill-pareto && OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 uv run python scripts/wp4_synthetic.py --draws 200 --worker ${w} --total-workers 4 2>&1 | tee results/wp4_w${w}.log; echo 'WORKER ${w} FINISHED'; read"
    echo "Started worker ${w} in tmux session wp4_w${w}"
done
