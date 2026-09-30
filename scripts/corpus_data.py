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
    'notes': 'Weights from Table 4 (modified AHP). X5 cost: lower core hardness preferred per paper §3.',
    'active': True,   # m=9 ≥ 8
    # Objective groups for Pareto frontier (3 groups, following PRESPEC.md §4)
    # G1 = fatigue resistance: bending + surface fatigue
    # G2 = mechanical strength: UTS + surface hardness
    # G3 = toughness/cost: core hardness (cost)
    'obj_groups': [[0, 1], [2, 3], [4]],
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
    'active': True,   # m=16 ≥ 8
    # 3 criteria → 3 groups, one each
    'obj_groups': [[0], [1], [2]],
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
    'active': False,  # m=6 < 8 — excluded per PRESPEC.md §5
    'obj_groups': None,
})

# ─────────────────────────────────────────────────────────────────────────────
# 4. Chen (2020) — building material supplier selection
# Entropy 22(2):259
# DOI: 10.3390/e22020259
# 5 alternatives × 7 criteria; Entropy-AHP combined weights
# Criteria: C1=rate qualified (%), C2=price (k$, cost), C3=market share (%),
#            C4=supply capacity (kg, benefit), C5=new product rate (%),
#            C6=delivery time (days, cost), C7=on-time ratio (%)
# Weights: combined Entropy-AHP (Table in paper)
# ─────────────────────────────────────────────────────────────────────────────
CORPUS.append({
    'source_key': 'chen2020',
    'citation':   'Chen (2020) Entropy 22:259',
    'doi':        '10.3390/e22020259',
    'm': 5,
    'n': 7,
    'criteria_names': ['Qual rate', 'Price', 'Market share', 'Supply cap', 'New prod rate', 'Delivery time', 'On-time ratio'],
    'directions':  ['max', 'min', 'max', 'max', 'max', 'min', 'max'],
    'weights_raw': [0.2415, 0.1505, 0.1122, 0.1051, 0.1071, 0.0894, 0.1942],
    'weights':     [0.2415, 0.1505, 0.1122, 0.1051, 0.1071, 0.0894, 0.1942],
    # Decision matrix X[alternative][criterion] — raw values before normalisation
    # Rows: A1..A5 (suppliers); Cols: C1..C7
    'matrix': [
        [90,  3.5, 40, 2500, 30, 5, 95],
        [80,  4.0, 35, 3000, 25, 7, 90],
        [85,  3.8, 45, 2800, 35, 4, 92],
        [88,  3.2, 38, 2600, 28, 6, 93],
        [82,  3.9, 42, 2700, 32, 5, 91],
    ],
    'notes': 'Weights are Entropy-AHP combined (wcj). Raw matrix values from Step 1 of the paper. Sum of weights = 1.0.',
    'active': False,  # m=5 < 8 — excluded per PRESPEC.md §5
    'obj_groups': None,
})

# ─────────────────────────────────────────────────────────────────────────────
# 5. Junaid et al. (2024) — AM material selection for aerospace
# MATEC Web of Conferences 398:01012
# DOI: 10.1051/matecconf/202439801012
# 9 alternatives × 14 criteria; AHP weights
# Criteria: TS=tensile strength, E=elastic modulus, FR=flexural rigidity,
#   EB=elongation break, Sf=service temp, OT=operational temp, DU=durability,
#   RE=repairability (all max); d=density, C=cost, P.CO2=CO2, FP=flame point,
#   WU=water uptake, EU=energy use (all min)
# ─────────────────────────────────────────────────────────────────────────────
CORPUS.append({
    'source_key': 'junaid2024',
    'citation':   'Junaid et al. (2024) MATEC Conf 398:01012',
    'doi':        '10.1051/matecconf/202439801012',
    'm': 9,
    'n': 14,
    'criteria_names': ['TS','E','FR','EB','Sf','OT','DU','RE','d','C','P.CO2','FP','WU','EU'],
    'directions':     ['max','max','max','max','max','max','max','max','min','min','min','min','min','min'],
    'weights_raw': [0.183, 0.139, 0.084, 0.046, 0.137, 0.037, 0.046, 0.051, 0.165, 0.033, 0.021, 0.025, 0.015, 0.017],
    'weights':     [0.183, 0.139, 0.084, 0.046, 0.137, 0.037, 0.046, 0.051, 0.165, 0.033, 0.021, 0.025, 0.015, 0.017],
    # Table 4: rows=ABS,PPSU,PEEK,PEKK,ULTEM,PSU,PC,PVDF,Nylon12CF
    # Cols: TS(MPa),E(GPa),FR,EB(%),Sf(°C),OT(°C),DU,RE,d(g/cc),C($/kg),CO2,FP,WU(%),EU
    'matrix': [
        [41,  2.28, 3.6, 6,   80,  100, 3, 4, 1.05, 3.5,  2.1, 2, 0.3, 95],   # ABS
        [70,  2.48, 4.0, 60,  180, 170, 4, 3, 1.29, 85,   3.5, 3, 0.2, 110],  # PPSU
        [100, 3.60, 4.5, 50,  240, 250, 5, 2, 1.30, 120,  3.8, 4, 0.1, 130],  # PEEK
        [110, 4.00, 5.0, 40,  260, 260, 5, 2, 1.28, 150,  3.5, 4, 0.1, 140],  # PEKK
        [69,  2.41, 4.2, 3,   170, 180, 5, 3, 1.27, 100,  3.2, 5, 0.2, 120],  # ULTEM
        [70,  2.55, 3.8, 50,  175, 150, 4, 3, 1.24, 90,   3.3, 3, 0.2, 115],  # PSU
        [55,  2.30, 3.5, 110, 125, 130, 3, 4, 1.20, 5,    2.5, 3, 0.2, 100],  # PC
        [55,  1.50, 2.5, 300, 100, 120, 3, 4, 1.78, 15,   2.8, 2, 0.05,105],  # PVDF
        [170, 8.00, 6.0, 2,   165, 180, 5, 3, 1.10, 40,   4.0, 3, 0.2, 140],  # Nylon12CF
    ],
    'notes': 'Weights from Table 10 (3 dec). Matrix values from Table 4. 8 benefit + 6 cost criteria.',
    'active': True,   # m=9 ≥ 8
    # 14 criteria → 3 groups (Performance / Economic / Environmental)
    # Performance (8 crit): TS, E, FR, EB, Sf, OT, DU, RE  → indices 0-7
    # Economic (1 crit):    C  → index 9
    # Environmental (5 crit): d, P.CO2, FP, WU, EU → indices 8,10,11,12,13
    'obj_groups': [[0,1,2,3,4,5,6,7], [9], [8,10,11,12,13]],
})

# ─────────────────────────────────────────────────────────────────────────────
# 6. Bhaskar et al. (2023) — AA2024 composite material selection (ASN series)
# Canadian Metallurgical Quarterly 63(4):1183–1211
# DOI: 10.1080/00084433.2023.2294546
# 4 alternatives × 15 criteria; AHP weights
# ─────────────────────────────────────────────────────────────────────────────
_w_bhaskar = [0.096, 0.082, 0.082, 0.085, 0.091, 0.026, 0.026, 0.046, 0.029, 0.025,
              0.048, 0.048, 0.104, 0.114, 0.096]
# Reorder to match criteria order PDC-1..PDC-15
CORPUS.append({
    'source_key': 'bhaskar2023_asn',
    'citation':   'Bhaskar et al. (2023) Can Metall Q 63:1183 [ASN series]',
    'doi':        '10.1080/00084433.2023.2294546',
    'm': 4,
    'n': 15,
    'criteria_names': ['UTS','Elong','Flex','Impact','Hardness','ThCond','TGA','FractT','StorMod','TanDelta','Void','Density','WearRate','COF','Cost'],
    'directions':     ['max','max','max','max','max','max','max','max','max','max','min','min','min','min','min'],
    'weights_raw': _w_bhaskar,
    'weights':     [w / sum(_w_bhaskar) for w in _w_bhaskar],
    'matrix': [
        [139.65, 8.10,  283.91, 26.7, 95,  178.00, 99.847, 30.12, 31114, 0.00155, 2.89, 2.69, 0.00199,  0.385, 354.5],
        [149.05, 9.07,  314.68, 48.4, 108, 169.00, 99.839, 33.98, 35754, 0.00591, 2.52, 2.71, 0.00141,  0.312, 432.5],
        [174.60, 10.25, 336.62, 71.6, 121, 160.00, 99.656, 36.28, 43958, 0.00926, 2.15, 2.73, 0.000887, 0.251, 510.5],
        [211.75, 12.86, 645.16, 84.5, 127, 144.00, 99.835, 39.52, 45411, 0.02088, 1.79, 2.75, 0.000556, 0.176, 588.5],
    ],
    'notes': 'ASN series (Si3N4 wt%: 0,2,4,6). Weights from Table 12 (CR=0.0094). Normalised to sum=1.',
    'active': False,  # m=4 < 8 — excluded per PRESPEC.md §5
    'obj_groups': None,
})

# ─────────────────────────────────────────────────────────────────────────────
# 7. Bhaskar et al. (2023) — AA2024 composite material selection (AGR series)
# ─────────────────────────────────────────────────────────────────────────────
CORPUS.append({
    'source_key': 'bhaskar2023_agr',
    'citation':   'Bhaskar et al. (2023) Can Metall Q 63:1183 [AGR series]',
    'doi':        '10.1080/00084433.2023.2294546',
    'm': 4,
    'n': 15,
    'criteria_names': ['UTS','Elong','Flex','Impact','Hardness','ThCond','TGA','FractT','StorMod','TanDelta','Void','Density','WearRate','COF','Cost'],
    'directions':     ['max','max','max','max','max','max','max','max','max','max','min','min','min','min','min'],
    'weights_raw': _w_bhaskar,
    'weights':     [w / sum(_w_bhaskar) for w in _w_bhaskar],
    'matrix': [
        [215.14, 11.63, 339.71, 81.7, 108, 161.34, 99.601, 26.80, 36874, 0.02973, 0.31, 2.78, 0.000958,  0.238, 435.4],
        [164.63,  9.47, 314.68, 62.4,  97, 144.28, 99.642, 22.92, 25925, 0.02646, 0.70, 2.76, 0.000506,  0.219, 432.5],
        [147.18,  6.41, 305.96, 49.7,  86, 130.39, 99.265, 19.45, 18010, 0.00859, 1.48, 2.73, 0.000187,  0.168, 429.6],
        [134.43,  2.67, 239.67, 33.5,  83, 119.20, 99.177, 17.63, 14578, 0.00691, 3.46, 2.66, 0.0000596, 0.150, 426.7],
    ],
    'notes': 'AGR series (Gr wt%: 0,2,4,6). Same weights as ASN. Normalised to sum=1.',
    'active': False,  # m=4 < 8 — excluded per PRESPEC.md §5
    'obj_groups': None,
})


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
