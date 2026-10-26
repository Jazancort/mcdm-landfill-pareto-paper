# -*- coding: utf-8 -*-
"""
classify_pf.py
==============
Implements the P-F (permeability) classification rule for the Santiago geology layer,
following the rule declared in PRESPEC_SANTIAGO.md §4.3.

Rule (algorithm):
  1. Split the lit field by ";".
  2. Ignore clauses that are formation names or stratigraphic qualifiers
     (patterns starting with "Formação", "Fase … pós", "Complexo … do/de/da").
  3. The first remaining clause determines the class:
     - Baixa: clause begins with "Mantos", "derrames", or "escoadas" (lava flows)
     - não-Baixa/Média: clause begins with "Cones", "escórias", "piroclastos"
     - não-Baixa/Alta: clause begins with "Aluvio", "Dunas", "duna", sedimentary terms
       (calc, areia, marine sediments)
     - NC (no Fogo analog): anything else (intrusive, breccias, conglomerates, domes)
  4. Exception: PA (cod_form = 'PA') has lit = "Complexo eruptivo do Pico da Antónia…"
     with no primary lithological term. Classified as Baixa by analogy with PA1 (which
     explicitly lists "Mantos subaérios") and per Serralheiro (1976) / Cabral (2012, p.45).
  5. null cod_form: lit describes submarine hyaloclastites ("Mantos submarinos") → Baixa.

The function classify_pf(lit, cod_form) returns one of:
  'Baixa', 'Média', 'Alta', 'NC'

Test against T1 in PRESPEC_SANTIAGO.md:
  assert classify_pf(lit, cod_form) == expected_pf for all 27+1 rows of T1.
"""

import re

# Patterns that identify formation names / stratigraphic qualifiers to skip
_SKIP_PATTERNS = [
    re.compile(r'^\s*Forma\u00e7\u00e3o\s', re.IGNORECASE),          # "Formação …"
    re.compile(r'^\s*Fase\s+l\u00e1vica\s', re.IGNORECASE),          # "Fase lávica …"
    re.compile(r'^\s*Complexo\s+(?:eruptivo|filoniano)\s', re.IGNORECASE),  # "Complexo eruptivo/filoniano …"
]

# Primeira cláusula primária: prefixos → classe
_BAIXA_PREFIXES = ('mantos', 'derrames', 'escoadas')
_MEDIA_PREFIXES = ('cones', 'escórias', 'piroclastos', 'talus', 'brecha de talude',
                   'taludes', 'escorias', 'depósitos de vertente')
_ALTA_PREFIXES  = ('aluvio', 'aluviõ', 'dunas', 'duna', 'depósitos dunares',
                   'areia', 'areias', 'calcarenito', 'conglomerado marinho',
                   'conglomerados e calcarenitos', 'wave abrasion', 'marinho')


def _is_skip(clause: str) -> bool:
    c = clause.strip()
    return any(p.match(c) for p in _SKIP_PATTERNS)


def classify_pf(lit: str, cod_form: str = '') -> str:
    """
    Classify a Santiago geology polygon as 'Baixa', 'Média', 'Alta', or 'NC'.

    Parameters
    ----------
    lit : str
        The 'lit' field from the IDECV geologia_santiago layer.
    cod_form : str
        The cod_form code (used for the PA exception).

    Returns
    -------
    str : 'Baixa' | 'Média' | 'Alta' | 'NC'
    """
    # Exception: PA (no primary lit term, classified by PA1 analogy)
    if str(cod_form).strip().upper() == 'PA':
        return 'Baixa'

    if not lit:
        return 'NC'

    clauses = lit.split(';')
    for clause in clauses:
        c = clause.strip()
        if not c:
            continue
        if _is_skip(c):
            # Even if we skip the formation name, check any parenthetical content for primary terms
            m = re.search(r'\(([^)]+)\)', c)
            if m:
                paren = m.group(1).strip().lower()
                if any(paren.startswith(p) for p in _BAIXA_PREFIXES):
                    return 'Baixa'
                if any(paren.startswith(p) for p in _MEDIA_PREFIXES):
                    return 'Média'
                if any(paren.startswith(p) for p in _ALTA_PREFIXES):
                    return 'Alta'
            continue
        # Remove parenthetical rock-type qualifiers at the start and treat remainder
        # e.g. "(rochas traquito-fonolíticas)" → skip as it's a qualifier, not the main term
        c_lower = c.lower()
        # Remove leading parenthetical
        if c_lower.startswith('('):
            end = c_lower.find(')')
            if end != -1:
                c_lower = c_lower[end + 1:].strip()
                if not c_lower:
                    continue  # nothing left, try next clause

        if any(c_lower.startswith(p) for p in _BAIXA_PREFIXES):
            return 'Baixa'
        if any(c_lower.startswith(p) for p in _MEDIA_PREFIXES):
            return 'Média'
        if any(c_lower.startswith(p) for p in _ALTA_PREFIXES):
            return 'Alta'
        # First primary term is not lava, cone, or sediment → NC
        return 'NC'

    # No primary clause found
    return 'NC'


# ── T1 from PRESPEC_SANTIAGO.md (27 named cod_forms + null) ──────────────────
# Format: (cod_form, lit_excerpt, expected_pf)
T1 = [
    ('A',    'Formação da Assomada; Mantos e Piroclastos (Pliocénico)',                'Baixa'),
    ('A1',   'Formação da Assomada; Mantos e Piroclastos subaérios (basanitos)',       'Baixa'),
    ('B',    'Brechas intravulcânicas (Ante-Miocénico médio)',                        'NC'),
    ('CA',   'Complexo filoniano de base; basanitos, limburgitos',                    'NC'),
    ('CB',   'Formação dos Flamengos (Mantos, piroclastos, chaminés)',                 'Baixa'),
    ('CBm',  'Formação dos Orgãos; Depósitos conglomeráticos-brechoídes terrestres',   'NC'),
    ('MV',   'Formação do Monte das Vacas; Cones de piroclastos, escórias e pequenos derrames', 'Média'),
    ('PA',   'Complexo eruptivo do Pico da Antónia (Pliocénico-Miocénico)',           'Baixa'),  # exception
    ('PA1',  'Complexo eruptivo do Pico da Antónia; Mantos subaérios, piroclastos',   'Baixa'),
    ('a',    'Aluviões antigas e modernas (Quaternário)',                              'Alta'),
    ('a dv', 'Aluviões antigas e modernas depósitos de vertente (Quaternário)',        'Alta'),
    ('a e',  'Aluviões e eluviões (Quaternário)',                                      'Alta'),
    ('c',    'Conglomerados e calcarenitos marinhos fossilíferos (Quaternário)',       'Alta'),
    ('calc', 'Calcarenitos marinhos, fossilíferos (Pliocénico-Miocénico)',             'Alta'),
    ('cb',   'Rochas granulares (carbonatitos); Complexo eruptivo interno',            'NC'),
    ('chb',  'Filões e chaminés piroclastos; Complexo eruptivo interno',               'NC'),
    ('chy',  'Filões e chaminés piroclastos; Complexo eruptivo interno',               'NC'),
    ('chφ',  'Filões e chaminés; Complexo eruptivo interno',                           'NC'),
    ('cong', 'Conglomerados e facies terrestres (Pliocénico-Miocénico)',               'NC'),
    ('d',    'Dunas (Quaternário)',                                                    'Alta'),
    ('de',   'Duna, eluviões (Quaternário)',                                           'Alta'),
    ('dv',   'Depósitos de vertente (Quaternário)',                                    'Média'),
    ('dφ',   'Domas e chaminés (fonólitos e traquitos); Fonólitos e traquitos',        'NC'),
    ('γ',    'Rochas granulares (gabros feldspatóidicos); Complexo eruptivo interno',  'NC'),
    ('λρ',   'Formação dos Flamengos; Mantos, piroclastos, chaminés (Miocénico médio)','Baixa'),
    ('λρ1',  'Formação dos Flamengos; Mantos, piroclastos, chaminés e hialoclastitos', 'Baixa'),
    ('φ',    'Fase lávica pós Formação dos Orgãos (rochas traquito-fonolíticas); Mantos; Piroclastos', 'Baixa'),
    ('null', 'Mantos submarinos, inferiores e superiores (hialoclastitos); Piroclastos; Tufo Brechas', 'Baixa'),
]


def run_tests():
    """Assert classify_pf matches T1 for all 28 rows."""
    failures = []
    for cod_form, lit, expected in T1:
        got = classify_pf(lit, cod_form)
        if got != expected:
            failures.append(f"  FAIL cod_form={cod_form!r}: got={got!r} expected={expected!r}  lit={lit[:60]!r}")
        else:
            print(f"  OK   cod_form={cod_form!r}: {got}")
    if failures:
        print()
        for f in failures:
            print(f)
        raise AssertionError(f"{len(failures)} T1 mismatches in classify_pf")
    print(f"\nAll {len(T1)} T1 rows pass.")


if __name__ == '__main__':
    run_tests()
