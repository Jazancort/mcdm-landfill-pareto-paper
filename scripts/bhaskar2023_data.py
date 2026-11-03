"""
Dados extraídos de:
Bhaskar, S., Kumar, M., & Patnaik, A. (2024).
Investigation for the optimum selection of hybrid AA2024 – ceramic particulate alloy
composite materials prepared through stir casting using the hybrid AHP-TOPSIS MCDM technique.
Canadian Metallurgical Quarterly, 63(4), 1183–1211.
DOI: 10.1080/00084433.2023.2294546
"""

bhaskar2023 = {
    # ─── Identificação ────────────────────────────────────────────────────────
    "doi": "10.1080/00084433.2023.2294546",
    "citation": (
        "Bhaskar, S., Kumar, M., & Patnaik, A. (2024). "
        "Investigation for the optimum selection of hybrid AA2024 – ceramic particulate "
        "alloy composite materials prepared through stir casting using the hybrid "
        "AHP-TOPSIS MCDM technique. "
        "Canadian Metallurgical Quarterly, 63(4), 1183–1211. "
        "https://doi.org/10.1080/00084433.2023.2294546"
    ),

    # ─── Dimensões do problema ────────────────────────────────────────────────
    # O paper apresenta DOIS problemas independentes de MCDM:
    #   ASN: AA2024 + SiC + Si3N4 + Gr (variando Si3N4: 0, 2, 4, 6 wt%)
    #   AGR: AA2024 + SiC + Si3N4 + Gr (variando Gr: 0, 2, 4, 6 wt%)
    # Ambos usam os mesmos 15 critérios (PDCs) e os mesmos pesos AHP.
    "m_asn": 4,   # alternativas: ASN-0, ASN-2, ASN-4, ASN-6
    "m_agr": 4,   # alternativas: AGR-0, AGR-2, AGR-4, AGR-6
    "n": 15,       # critérios (PDCs)

    # ─── Critérios (PDCs) ─────────────────────────────────────────────────────
    # Chave: código PDC | direction: "max" (higher-the-better) / "min" (lower-the-better)
    "criteria": {
        "PDC-1":  {"name": "Ultimate tensile strength (MPa)",         "direction": "max"},
        "PDC-2":  {"name": "Elongation (%)",                          "direction": "max"},
        "PDC-3":  {"name": "Flexural strength (MPa)",                 "direction": "max"},
        "PDC-4":  {"name": "Impact strength (J)",                     "direction": "max"},
        "PDC-5":  {"name": "Hardness (HV)",                           "direction": "max"},
        "PDC-6":  {"name": "Thermal conductivity (W/mK)",             "direction": "max"},
        "PDC-7":  {"name": "Material stability - TGA (%)",            "direction": "max"},
        "PDC-8":  {"name": "Fracture toughness - FT at 0.5 mm (MPa.m^0.5)","direction": "max"},
        "PDC-9":  {"name": "Storage modulus (MPa)",                   "direction": "max"},
        "PDC-10": {"name": "Tan delta (damping capacity)",                "direction": "max"},
        "PDC-11": {"name": "Void content (%)",                        "direction": "min"},
        "PDC-12": {"name": "Actual density (g/cc)",                   "direction": "min"},
        "PDC-13": {"name": "Specific wear rate (mm3/Nm)",             "direction": "min"},
        "PDC-14": {"name": "Coefficient of friction (COF)",           "direction": "min"},
        "PDC-15": {"name": "Cost (INR or relative)",                  "direction": "min"},
    },

    # ─── Pesos AHP (w_j) — Tabela 12 ─────────────────────────────────────────
    # Exatamente como publicados. Soma = 0.998 (arredondamento do paper).
    # Ordem decrescente: PDC-14 > PDC-13 > PDC-1 ≈ PDC-15 > PDC-5 > PDC-4 >
    #                    PDC-2 ≈ PDC-3 > PDC-11 ≈ PDC-12 > PDC-8 > PDC-9 >
    #                    PDC-6 ≈ PDC-7 > PDC-10
    "ahp_weights": {
        "PDC-1":  0.096,
        "PDC-2":  0.082,
        "PDC-3":  0.082,
        "PDC-4":  0.085,
        "PDC-5":  0.091,
        "PDC-6":  0.026,
        "PDC-7":  0.026,
        "PDC-8":  0.046,
        "PDC-9":  0.029,
        "PDC-10": 0.025,
        "PDC-11": 0.048,
        "PDC-12": 0.048,
        "PDC-13": 0.104,
        "PDC-14": 0.114,
        "PDC-15": 0.096,
    },
    "ahp_consistency": {
        "lambda_max": 15.0,   # ≈ 15 (paper: "maximum Eigen value λmax ≈ 15")
        "CI": 0.0150,
        "CR": 0.0094,         # < 0.10 → consistente
        "RI": 1.59,           # n=15, da Tabela 5
    },

    # ─── Matriz de Decisão: ASN alloy composites (Tabela 13) ─────────────────
    # Linhas: alternativas | Colunas: PDC-1 a PDC-15 (mesma ordem)
    "decision_matrix_asn": {
        "alternatives": ["ASN-0", "ASN-2", "ASN-4", "ASN-6"],
        "columns": [
            "PDC-1", "PDC-2", "PDC-3", "PDC-4", "PDC-5",
            "PDC-6", "PDC-7", "PDC-8", "PDC-9", "PDC-10",
            "PDC-11", "PDC-12", "PDC-13", "PDC-14", "PDC-15",
        ],
        "values": {
            # Alt     UTS      Elong   Flex     Impact  Hardness  TherCond  TGA       FT@0.5  StorMod   TanD       VoidC   ActDens  SWR        COF     Cost
            "ASN-0": [139.65,  8.10,   283.91,  26.7,   95,       178.00,   99.847,   30.12,  31114,    0.00155,   2.89,   2.69,    0.00199,   0.385,  354.5],
            "ASN-2": [149.05,  9.07,   314.68,  48.4,   108,      169.00,   99.839,   33.98,  35754,    0.00591,   2.52,   2.71,    0.00141,   0.312,  432.5],
            "ASN-4": [174.60,  10.25,  336.62,  71.6,   121,      160.00,   99.656,   36.28,  43958,    0.00926,   2.15,   2.73,    0.000887,  0.251,  510.5],
            "ASN-6": [211.75,  12.86,  645.16,  84.5,   127,      144.00,   99.835,   39.52,  45411,    0.02088,   1.79,   2.75,    0.000556,  0.176,  588.5],
        },
    },

    # ─── Matriz de Decisão: AGR alloy composites (Tabela 18) ─────────────────
    "decision_matrix_agr": {
        "alternatives": ["AGR-0", "AGR-2", "AGR-4", "AGR-6"],
        "columns": [
            "PDC-1", "PDC-2", "PDC-3", "PDC-4", "PDC-5",
            "PDC-6", "PDC-7", "PDC-8", "PDC-9", "PDC-10",
            "PDC-11", "PDC-12", "PDC-13", "PDC-14", "PDC-15",
        ],
        "values": {
            # Alt     UTS      Elong   Flex     Impact  Hardness  TherCond  TGA       FT@0.5  StorMod   TanD       VoidC   ActDens  SWR          COF     Cost
            "AGR-0": [215.14,  11.63,  339.71,  81.7,   108,      161.34,   99.601,   26.80,  36874,    0.02973,   0.31,   2.78,    0.000958,    0.238,  435.4],
            "AGR-2": [164.63,  9.47,   314.68,  62.4,   97,       144.28,   99.642,   22.92,  25925,    0.02646,   0.70,   2.76,    0.000506,    0.219,  432.5],
            "AGR-4": [147.18,  6.41,   305.96,  49.7,   86,       130.39,   99.265,   19.45,  18010,    0.00859,   1.48,   2.73,    0.000187,    0.168,  429.6],
            "AGR-6": [134.43,  2.67,   239.67,  33.5,   83,       119.20,   99.177,   17.63,  14578,    0.00691,   3.46,   2.66,    0.0000596,   0.150,  426.7],
        },
    },

    # ─── Ranking final (Tabelas 17 e 22) ─────────────────────────────────────
    "topsis_results_asn": {
        "ASN-0": {"D_plus": 0.0959, "D_minus": 0.0236, "CC": 0.1975, "rank": 4},
        "ASN-2": {"D_plus": 0.0668, "D_minus": 0.0360, "CC": 0.3498, "rank": 3},
        "ASN-4": {"D_plus": 0.0448, "D_minus": 0.0635, "CC": 0.5867, "rank": 2},
        "ASN-6": {"D_plus": 0.0236, "D_minus": 0.0959, "CC": 0.8025, "rank": 1},
    },
    "topsis_results_agr": {
        "AGR-0": {"D_plus": 0.0886, "D_minus": 0.0777, "CC": 0.4671, "rank": 4},
        "AGR-2": {"D_plus": 0.0531, "D_minus": 0.0711, "CC": 0.5725, "rank": 2},
        "AGR-4": {"D_plus": 0.0494, "D_minus": 0.0831, "CC": 0.6274, "rank": 1},
        "AGR-6": {"D_plus": 0.0777, "D_minus": 0.0886, "CC": 0.5329, "rank": 3},
    },
}


if __name__ == "__main__":
    import json

    # Verificações rápidas
    w = bhaskar2023["ahp_weights"]
    print(f"Soma dos pesos AHP: {sum(w.values()):.3f}  (paper: 0.998)")
    print(f"n critérios: {bhaskar2023['n']}")
    print(f"m alternativas ASN: {bhaskar2023['m_asn']}")
    print(f"m alternativas AGR: {bhaskar2023['m_agr']}")
    print()
    print("Pesos em ordem decrescente:")
    for k, v in sorted(w.items(), key=lambda x: -x[1]):
        name = bhaskar2023["criteria"][k]["name"]
        print(f"  {k}: {v:.3f}  — {name}")
    print()
    print("Matriz ASN (primeiros valores):")
    for alt, vals in bhaskar2023["decision_matrix_asn"]["values"].items():
        print(f"  {alt}: {vals}")
    print()
    print("Matriz AGR:")
    for alt, vals in bhaskar2023["decision_matrix_agr"]["values"].items():
        print(f"  {alt}: {vals}")
