# -*- coding: utf-8 -*-
"""
test_unit.py
============
Unit tests for mcdm_experiment.py.
Imports all functions from the main script — does NOT re-implement them.

Run:
    uv run --with pandas --with numpy python scripts/test_unit.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd

from mcdm_experiment import (
    load_data, impute_nan, compute_objectives,
    haversine_km, saw_scores, topsis_scores, vikor_scores, promethee2_scores,
    count_viable_trios, optimal_trio_enumerate, greedy_trio,
    pareto_dominates, epsilon_additive,
    run_unit_tests,
    CACHE_CSV, PARETO_CSV, BCS_CSV, COL, AHP_WEIGHTS, MIN_DIST_KM,
)


def main():
    print("=" * 55)
    print("test_unit.py  —  importing from mcdm_experiment.py")
    print("=" * 55)

    # Load and prepare
    df_all, par, bcs = load_data()
    df_imp = impute_nan(df_all)
    viable_mask = df_imp[COL["protected"]] > 0
    df_via = df_imp[viable_mask].copy()
    via_global = df_via.index.values
    objs_473 = compute_objectives(df_imp, df_imp)
    D_via = haversine_km(
        df_via["latitude (degrees)"].values,
        df_via["longitude (degrees)"].values,
    )

    # SAW on all 473 (for unit test 3)
    sc_saw473 = saw_scores(df_imp)

    # Run the centralised unit test suite
    results = run_unit_tests(
        df_all=df_imp,
        par=par,
        df_viable=df_via,
        D_via=D_via,
        scores_saw473=sc_saw473,
        via_global=via_global,
        objs_473=objs_473,
        saw389_fn=saw_scores,
        topsis_fn=topsis_scores,
    )

    all_pass = True
    for name, passed, detail in results:
        tag = "PASS" if passed else "FAIL"
        print(f"[{tag}] {name}: {detail}")
        all_pass &= passed

    print()
    if all_pass:
        print("All unit tests PASSED.")
        sys.exit(0)
    else:
        print("Some unit tests FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
