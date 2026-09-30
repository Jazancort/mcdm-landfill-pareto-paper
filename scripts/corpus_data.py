"""
corpus_data.py
==============
Decision matrices from published MCDM literature.
Each entry is a dict with:
  source_key : str  — unique ID used in corpus tables
  citation   : str  — short citation
  doi        : str
  m          : int  — number of alternatives
  n          : int  — number of criteria
  directions : list[str]  — 'max'/'min' for each criterion
  weights    : list[float]  — w_j (must sum to 1.0; normalised if needed)
  weights_raw: list[float]  — original w_j as published (may not sum to 1)
  matrix     : list[list[float]]  — X[i][j], row=alternative, col=criterion
  notes      : str
"""

import numpy as np

CORPUS = []

# ─────────────────────────────────────────────────────────────────────────────
# 1. Milani et al. (2005) — gear material selection
# Structural and Multidisciplinary Optimization 29:312–318
# DOI: 10.1007/s00158-004-0473-1
# Table 2 (raw data) + Table 4 (weights w_j = modified AHP+entropy)
# 9 alternatives × 5 criteria
# Criteria: X1=bending fatigue limit, X2=surface fatigue limit,
#            X3=UTS, X4=surface hardness, X5=core hardness
# Directions: X1–X4 benefit (higher is better); X5 cost (lower core hardness
#             prevents early fracture — lower is preferred, see paper §3)
# Weights from Table 4: w_j = [0.426, 0.292, 0.172, 0.102, 0.005] (AHP)
# Note: entropy weights also given as w'_j = [0.246, 0.225, 0.266, 0.237, 0.023]
# We use the combined modified weights w_j (AHP) as they represent elicited priors
# Raw data: averages of ranges given in Table 2
# ─────────────────────────────────────────────────────────────────────────────
CORPUS.append({
    'source_key': 'milani2005',
    'citation':   'Milani et al. (2005) Struct Multidisc Optim 29:312',
    'doi':        '10.1007/s00158-004-0473-1',
    'm': 9,
    'n': 5,
    'criteria_names': ['Bending fatigue', 'Surface fatigue', 'UTS', 'Surface hardness', 'Core hardness'],
    'directions': ['max', 'max', 'max', 'max', 'min'],
    'weights_raw': [0.426, 0.292, 0.172, 0.102, 0.005],
    'weights':     [0.426, 0.292, 0.172, 0.102, 0.005],  # already sum to ~1
    # Table 2: rows = A1..A9, cols = [bend_fat, surf_fat, UTS, surf_hard, core_hard]
    # Ranges averaged; surface/core hardness converted to midpoint HB or HV
    'matrix': [
        # A1: Cast iron DIN1691:       bend=100, surf=330,  UTS=380,  surf_h=200,  core_h=200
        [100,   330,   380,   200,   200],
        # A2: Ductile iron DIN1692:    bend=360, surf=460,  UTS=880,  surf_h=220,  core_h=220
        [360,   460,   880,   220,   220],
        # A3: S.G. iron DIN1692:       bend=340, surf=550,  UTS=845,  surf_h=240,  core_h=240],  midpoints
        [340,   550,   845,   240,   240],
        # A4: Cast alloy:              bend=435, surf=630,  UTS=845,  surf_h=270,  core_h=270
        [435,   630,   845,   270,   270],
        # A5: Through-hardened alloy:  bend=540, surf=670,  UTS=1190, surf_h=270,  core_h=270
        [540,   670,  1190,   270,   270],
        # A6: Surface-hardened alloy:  bend=680, surf=1160, UTS=1580, surf_h=585,  core_h=240
        [680,  1160,  1580,   585,   240],
        # A7: Carburised steels:       bend=920, surf=1500, UTS=2300, surf_h=700,  core_h=315
        [920,  1500,  2300,   700,   315],
        # A8: Nitrided steels:         bend=760, surf=1250, UTS=1250, surf_h=750,  core_h=315
        [760,  1250,  1250,   750,   315],
        # A9: Through-hardened carbon: bend=430, surf=500,  UTS=635,  surf_h=185,  core_h=185
        [430,   500,   635,   185,   185],
    ],
    'notes': 'Table 2 ranges averaged for single-point values. Weights from Table 4 (modified AHP). X5 cost: lower core hardness preferred per paper §3.',
})

# ─────────────────────────────────────────────────────────────────────────────
# 2. Vafaei et al. (2018) — autonomous drone landing site selection
# Int. J. Information and Decision Sciences 10(1):19–38
# DOI: 10.1504/IJIDS.2018.090667
# Table 2: 16 alternatives × 3 criteria
# Criteria: C1=illumination (benefit), C2=reachability (benefit),
#            C3=land texture (cost)
# Weights: equal (1/3 each)
# ─────────────────────────────────────────────────────────────────────────────
CORPUS.append({
    'source_key': 'vafaei2018',
    'citation':   'Vafaei et al. (2018) IJIDS 10:19',
    'doi':        '10.1504/IJIDS.2018.090667',
    'm': 16,
    'n': 3,
    'criteria_names': ['Illumination', 'Reachability', 'Land texture'],
    'directions': ['max', 'max', 'min'],
    'weights_raw': [1/3, 1/3, 1/3],
    'weights':     [1/3, 1/3, 1/3],
    'matrix': [
        [138.6090, 0.3349,  6.4543],
        [154.7214, 0.3395, 11.4244],
        [158.3081, 0.3441, 11.4244],
        [157.3082, 0.3487,  6.8542],
        [144.5976, 0.3301, 11.2616],
        [138.5982, 0.3346, 11.2616],
        [131.5989, 0.3391, 11.1988],
        [132.5988, 0.3437, 11.1988],
        [144.5976, 0.3252, 11.2616],
        [138.5982, 0.3297, 11.2616],
        [132.5988, 0.3342, 11.1988],
        [135.9513, 0.3387,  6.8974],
        [119.7141, 0.3204, 11.2616],
        [112.7148, 0.3248, 11.1988],
        [112.7148, 0.3292, 11.1988],
        [128.9520, 0.3337,  6.8974],
    ],
    'notes': 'Equal weights (1/3 each) — elicited via equal judgment. TV under vector will be small given equal magnitudes. Useful for TV≈0 anchor in corpus.',
})

# ─────────────────────────────────────────────────────────────────────────────
# 3. Vafaei et al. (2022) — SAW normalisation assessment
# Procedia Computer Science (CENTERIS 2022) 196:544–551
# DOI: 10.1016/j.procs.2022.01.156
# Uses matrix from Chakraborty & Yeh [11] in Table 2
# 6 alternatives × 5 criteria (C1..C5 — C6 weight missing; raw sum=0.73)
# DEVIATION: weights sum to 0.73 as published; normalised to sum=1 here.
# See corpus/DEVIATIONS.md.
# Criteria: C1=? (max), C2=? (min), C3=? (max), C4=? (max), C5=? (max)
# Published weights: [0.03, 0.10, 0.30, 0.15, 0.15]; sum=0.73
# ─────────────────────────────────────────────────────────────────────────────
_w_raw_v22 = [0.03, 0.10, 0.30, 0.15, 0.15]
_w_sum_v22 = sum(_w_raw_v22)  # 0.73
_w_norm_v22 = [w / _w_sum_v22 for w in _w_raw_v22]

CORPUS.append({
    'source_key': 'vafaei2022',
    'citation':   'Vafaei et al. (2022) Procedia CS 196:544 [matrix from Chakraborty & Yeh]',
    'doi':        '10.1016/j.procs.2022.01.156',
    'm': 6,
    'n': 5,
    'criteria_names': ['C1', 'C2', 'C3', 'C4', 'C5'],
    'directions': ['max', 'min', 'max', 'max', 'max'],
    'weights_raw': _w_raw_v22,
    'weights':     _w_norm_v22,  # normalised; raw sum=0.73, see DEVIATIONS.md
    'matrix': [
        [690, 3.1,  9,  7,  4],
        [590, 3.9,  7,  6, 10],
        [600, 3.6,  8,  8,  7],
        [620, 3.8,  7, 10,  6],
        [700, 2.8, 10,  4,  6],
        [650, 4.0,  6,  9,  8],
    ],
    'notes': 'Weights sum to 0.73 as published — possible missing 6th criterion. Normalised to 1. Flag as PENDING verification of original Chakraborty & Yeh source.',
})

# ─────────────────────────────────────────────────────────────────────────────
# Placeholders for pending matrices (to be added after PDF download)
# ─────────────────────────────────────────────────────────────────────────────
# chen2020    — Chen (2020) Entropy 22:259; DOI 10.3390/e22020259
#               Building material supplier selection; AHP+entropy weights
#               URL for manual download: https://www.mdpi.com/1099-4300/22/2/259
#
# junaid2024  — Junaid et al. (2024) MATEC Conf 398:01012
#               DOI 10.1051/matecconf/202439801012
#               9 polymer AM materials for aerospace; AHP weights
#               URL: https://www.matec-conferences.org/articles/matecconf/pdf/2024/20/matecconf_icmsem2024_01012.pdf
#
# To add: place PDF in corpus/pdfs/, extract matrix, append entry above.


def get_matrix(source_key):
    for entry in CORPUS:
        if entry['source_key'] == source_key:
            return entry
    raise KeyError(f"Matrix '{source_key}' not found in corpus.")


def list_corpus():
    print(f"{'ID':<30} {'m':>4} {'n':>4}  {'doi'}")
    print("-" * 70)
    for e in CORPUS:
        print(f"{e['source_key']:<30} {e['m']:>4} {e['n']:>4}  {e['doi']}")


if __name__ == '__main__':
    list_corpus()
    print(f"\nTotal: {len(CORPUS)} matrices confirmed")
