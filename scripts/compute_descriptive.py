# -*- coding: utf-8 -*-
"""
compute_descriptive.py — Descriptive quantities for the Santiago replication.

Outputs
-------
  results/santiago/descriptive_output.json  — all results + input SHAs
  results/santiago/macros_descriptive.tex   — LaTeX macros

Quantities computed
-------------------
  (a) SantSNRegadiosPct  : fraction (%) of the S-N study area covered by
                           irrigated perimeters (Regadios/carta_agricola).
                           Source: data/geo/carta_agricola_st_wfs.geojson
                                   data/santiago/santiago_boundary.geojson

  (b) FrontFracFogo, FrontFracST, FrontFracSN
                         : |F(w0)| / |T| for each branch, where F(w0) is
                           the Pareto frontier under nominal weights w0,
                           computed from the sealed min-max normalised
                           criterion matrices.
                           NOTE: For S-T (16.7M trios) and Fogo (1.94M),
                           the computation runs on Athena; this script
                           computes S-N (77,995 trios) locally.

K5 deviation note
-----------------
  PRESPEC_SANTIAGO_A5.md §4 states: "The conditional sign in K5 ... is
  resolved here from the descriptors, not from MC results."
  stage3b_descriptors.json (committed before stage4-launch) does NOT
  contain the K5 κ=∞ contrasts. They were computed during Stage 4 as part
  of the 1 deterministic draw.  K5 is descriptive; no verdict is affected.

Usage
-----
  uv run python scripts/compute_descriptive.py [--skip-frontier]
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_GEO   = ROOT / "data" / "geo"
DATA_SANT  = ROOT / "data" / "santiago"
RESULTS    = ROOT / "results" / "santiago"
SCRIPTS    = ROOT / "scripts"

# ── Verified input SHAs (from extract_report_sn.json) ─────────────────────
EXPECTED_SHA = {
    "carta_agricola_st_wfs.geojson": "b3b155c6db081eefe8288d2efea2337cacb30d5b1c126f54dce77524de568a47",
    "santiago_boundary.geojson":     "5cc381644497a9f24eb326228b389d6cc02e09e7a9a7c7dc380d5f9559233a3d",
    "fogo_boundary_geol.geojson":    "80e0fc8282aaff7b",   # first 16 hex chars
    "santiago_sn_boundary.geojson": "d550883cad23e0d5",   # first 16 hex chars
    "df_santiago_sn.csv":            None,   # sealed MC data — SHA checked below
    "stage3b_descriptors.json":      "710718247783f1ee",   # first 16 hex chars
}

# Cited published area for S-N (Cabral 2012, p. 45) — used in text only, not as denominator
SANT_SN_AREA_CABRAL_KM2 = 395


# ─────────────────────────────────────────────────────────────────────────────
# SHA helpers
# ─────────────────────────────────────────────────────────────────────────────

def sha256_file(path: Path) -> str:
    """Return lowercase hex SHA-256 of file."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_sha(path: Path, expected: str) -> str:
    """Compute SHA, compare prefix, raise if mismatch.  Returns full hex."""
    got = sha256_file(path)
    if expected and not got.startswith(expected.replace(":", "").lower()[:len(expected)]):
        raise ValueError(f"SHA mismatch for {path.name}: got {got[:16]} expected {expected[:16]}")
    return got


# ─────────────────────────────────────────────────────────────────────────────
# (a2) GIS areas of the three clipping polygons
# ─────────────────────────────────────────────────────────────────────────────

def compute_clipping_areas() -> dict:
    """
    Area (km²) of each clipping polygon, computed in the UTM zone of the
    respective grid (Fogo: EPSG:32626 / UTM 26N; Santiago: EPSG:32627 / UTM 27N).
    This is consistent with the grid spacing and d_min used in each branch.

    Sources:
      Fogo : data/geo/fogo_boundary_geol.geojson  (geology polygon, dissolved;
             confirmed as the on-land validation polygon in santiago_grid.py
             --mode fogo-check; PRESPEC_SANTIAGO.md §3 PRE-A: "geol_dissolved")
      S-T  : data/santiago/santiago_boundary.geojson
      S-N  : data/santiago/santiago_sn_boundary.geojson

    Regression assert: S-N area must equal 387.023 km² (the denominator used
    in \\SantSNRegadiosPct; see DEV-SANT-A5-001).  A mismatch means the CRS
    or polygon differs from compute_regadios_fraction().
    """
    UTM_FOGO = "EPSG:32626"   # UTM Zone 26N — Fogo
    UTM_SANT = "EPSG:32627"   # UTM Zone 27N — Santiago

    specs = [
        ("fogo", DATA_GEO  / "fogo_boundary_geol.geojson",   UTM_FOGO),
        ("st",   DATA_SANT / "santiago_boundary.geojson",    UTM_SANT),
        ("sn",   DATA_SANT / "santiago_sn_boundary.geojson", UTM_SANT),
    ]

    out = {}
    for key, path, crs in specs:
        sha = sha256_file(path)
        gdf = gpd.read_file(path).to_crs(crs)
        area_km2 = float(gdf.geometry.union_all().area) / 1e6
        area_km2_rounded = round(area_km2, 0)
        print(f"  {key:4s} area: {area_km2:.3f} km²  SHA: {sha[:16]}", flush=True)
        out[f"{key}_km2"] = int(area_km2_rounded)
        out[f"{key}_km2_exact"] = area_km2
        out[f"{key}_sha"] = sha

    # Regression assert: S-N area must match the Regadios denominator
    sn_exact = out["sn_km2_exact"]
    assert abs(sn_exact - 387.023) < 0.5, (
        f"S-N area regression FAIL: got {sn_exact:.3f} km², expected ~387.023 km² "
        f"(DEV-SANT-A5-001 denominator). Check CRS or polygon."
    )
    print(f"  S-N area assert OK: {sn_exact:.3f} ~= 387.023 km2", flush=True)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# (a) Regadios fraction
# ─────────────────────────────────────────────────────────────────────────────

def compute_regadios_fraction() -> dict:
    """
    Fraction (%) of the S-N study area covered by irrigated perimeters (Regadios).
    Denominador: santiago_sn_boundary.geojson (three southern concelhos, ~387 km²).
    Numerador: tipo_agric == 'Regadios' clipped to S-N polygon.
    Reference: DEV-SANT-A5-001 reports 3.6% (51.7 km² island-wide Regadios,
               13.9 km² intersecting the S-N boundary).
    """
    carta_path = DATA_GEO  / "carta_agricola_st_wfs.geojson"
    sn_path    = DATA_SANT / "santiago_sn_boundary.geojson"

    sha_carta = (Path(carta_path).read_bytes() and
                 hashlib.sha256(Path(carta_path).read_bytes()).hexdigest())
    sha_sn    = hashlib.sha256(Path(sn_path).read_bytes()).hexdigest()

    print(f"  carta_agricola SHA : {sha_carta[:16]}")
    print(f"  sn_boundary   SHA  : {sha_sn[:16]}")

    UTM = "EPSG:32627"
    carta = gpd.read_file(carta_path)
    sn    = gpd.read_file(sn_path).to_crs(UTM)
    reg   = carta[carta["tipo_agric"] == "Regadios"].copy().to_crs(UTM)

    sn_area_m2  = float(sn.geometry.union_all().area)
    reg_clipped = reg.clip(sn)
    reg_area_m2 = float(reg_clipped.geometry.union_all().area) if len(reg_clipped) > 0 else 0.0
    fraction_pct = round(reg_area_m2 / sn_area_m2 * 100, 2)

    print(f"  S-N area       : {sn_area_m2/1e6:.3f} km² (3 concelhos)")
    print(f"  Regadios in SN : {reg_area_m2/1e6:.3f} km²")
    print(f"  Fraction       : {fraction_pct:.2f}%  (DEV-SANT-A5-001: 3.6%)")

    return {
        "sn_area_km2":       round(sn_area_m2  / 1e6, 3),
        "regadio_in_sn_km2": round(reg_area_m2  / 1e6, 3),
        "regadio_pct":       round(fraction_pct, 1),   # 1 dp to match DEV
        "sha_carta":         sha_carta,
        "sha_sn_boundary":   sha_sn,
    }


# ─────────────────────────────────────────────────────────────────────────────
# (b) Frontier fraction for S-N (4 objectives; n=77,995 trios)
# ─────────────────────────────────────────────────────────────────────────────

# S-N configuration (from run_santiago_mc.py)
SN_CRIT_COLS = [
    "dist_A1_buildup (m)",      # A1  group A  BENEFIT
    "dist_A3_coast (m)",        # A3  group A  BENEFIT
    "dist_A4_heritage (m)",     # A4  group A  BENEFIT
    "dist_A5_agriculture (m)",  # A5  group A  BENEFIT
    "dist_A6_aerodrome (m)",    # A6  group A  BENEFIT
    "dist_A7_protected (m)",    # A7  group A  BENEFIT
    "B1_score",                 # B1  group B  BENEFIT
    "dist_B2_waterpoints (m)",  # B2  group B  BENEFIT
    "dist_B3_streams (m)",      # B3  group B  BENEFIT
    "slope (degrees)",          # C1  group C  COST
    "aspect_continuous",        # C2  group C  BENEFIT
    "dist_D1_mainroads (m)",    # D1  group D  COST
    "dist_D2_praia (m)",        # D2  group D  COST
]
SN_BENEFIT = [True,True,True,True,True,True,True,True,True,False,True,False,False]
SN_GROUPS  = [[0,1,2,3,4,5], [6,7,8], [9,10], [11,12]]   # A,B,C,D
SN_W0 = np.array([0.0397,0.0270,0.0397,0.0163,0.0324,0.0270,
                  0.2096,0.1048,0.1048,
                  0.0759,0.0253,
                  0.0981,0.1993], dtype=np.float64)
SN_W0 = SN_W0 / SN_W0.sum()
D_MIN_SN = 10.0   # km — portfolio separation, A5 §1: d_min = 10 km


def build_trio_array(lat: np.ndarray, lon: np.ndarray, dmin_km: float) -> np.ndarray:
    """Enumerate all valid trios (i<j<k) with all pairwise distances >= dmin_km.
    Uses haversine-approximated flat-earth distances for small areas.
    Returns int32 array (n_trios, 3).
    """
    R = 6371.0
    lat_r = np.deg2rad(lat)
    lon_r = np.deg2rad(lon)
    n = len(lat)

    # Pairwise distance matrix (km)
    dlat = lat_r[:, None] - lat_r[None, :]
    dlon = lon_r[:, None] - lon_r[None, :]
    a = np.sin(dlat/2)**2 + np.cos(lat_r[:, None]) * np.cos(lat_r[None, :]) * np.sin(dlon/2)**2
    D = 2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

    valid = D >= dmin_km
    ii, jj = np.where(np.triu(valid, k=1))

    chunk_size = 2000
    parts = []
    for start in range(0, len(ii), chunk_size):
        end = min(start + chunk_size, len(ii))
        ii_c, jj_c = ii[start:end], jj[start:end]
        # For each pair (ii_c[p], jj_c[p]), find k > jj_c[p] with both distances ok
        all_v = valid[ii_c, :][:, jj_c.max()+1 if jj_c.size else n:]  # wrong; fix below
        # Correct approach: for each pair, check all k > max(jj_c)
        for pi in range(len(ii_c)):
            i_, j_ = int(ii_c[pi]), int(jj_c[pi])
            k_range = np.arange(j_+1, n)
            ok = valid[i_, k_range] & valid[j_, k_range]
            ks = k_range[ok]
            if len(ks) > 0:
                arr = np.column_stack([
                    np.full(len(ks), i_, dtype=np.int32),
                    np.full(len(ks), j_, dtype=np.int32),
                    ks.astype(np.int32)
                ])
                parts.append(arr)
    if not parts:
        return np.empty((0, 3), dtype=np.int32)
    return np.concatenate(parts, axis=0)


def minmax_norm(X: np.ndarray) -> np.ndarray:
    """Min-max normalise columns of X over all rows.  Returns array in [0,1]."""
    lo = X.min(axis=0)
    hi = X.max(axis=0)
    rng = hi - lo
    rng[rng == 0] = 1.0   # avoid division by zero for constant criteria
    return (X - lo) / rng


def benefit_adjust(X_norm: np.ndarray, benefit: list) -> np.ndarray:
    """For cost criteria (benefit=False), flip: adj = 1 - norm."""
    X_adj = X_norm.copy()
    for j, is_ben in enumerate(benefit):
        if not is_ben:
            X_adj[:, j] = 1.0 - X_norm[:, j]
    return X_adj


def compute_group_objectives(X_adj: np.ndarray, w: np.ndarray,
                              groups: list) -> np.ndarray:
    """
    Compute per-site group objectives.  Returns (n, g) array.
    All objectives are to MAXIMIZE (benefit-adjusted).
    """
    n = X_adj.shape[0]
    g = len(groups)
    F_site = np.zeros((n, g), dtype=np.float64)
    for g_idx, crit_list in enumerate(groups):
        for j in crit_list:
            F_site[:, g_idx] += w[j] * X_adj[:, j]
    return F_site


def pareto_front_size(F: np.ndarray) -> int:
    """
    Count non-dominated portfolios.
    F: (n, k) array — all objectives to MAXIMIZE.

    Uses a batch-based O(n²) algorithm with NumPy vectorisation.
    Memory per batch: batch_i × batch_j × k × 8 bytes.
    """
    n, k = F.shape
    dominated = np.zeros(n, dtype=bool)

    BI = 300   # outer batch
    BJ = 1000  # inner batch

    print(f"    Pareto dominance: n={n:,} objectives={k}", flush=True)
    for i0 in range(0, n, BI):
        i1 = min(i0 + BI, n)
        Fi = F[i0:i1]   # (BI, k)
        for j0 in range(0, n, BJ):
            j1 = min(j0 + BJ, n)
            Fj = F[j0:j1]   # (BJ, k)

            # dom[a, b] = True if Fj[a] dominates Fi[b]
            # Fj[a] dominates Fi[b] if Fj[a] >= Fi[b] on all k, strict on at least one
            cmp_ge = np.all(Fj[:, None, :] >= Fi[None, :, :], axis=2)   # (BJ, BI)
            cmp_gt = np.any(Fj[:, None, :] >  Fi[None, :, :], axis=2)   # (BJ, BI)
            dom = cmp_ge & cmp_gt   # (BJ, BI)

            # Exclude self-domination (where absolute index j0+a == i0+b)
            for a in range(j1 - j0):
                abs_a = j0 + a
                b_self = abs_a - i0
                if 0 <= b_self < i1 - i0:
                    dom[a, b_self] = False

            dominated[i0:i1] |= dom.any(axis=0)

        if i0 % (BI * 10) == 0:
            pct = i0 / n * 100
            print(f"    Progress: {i0:,}/{n:,} ({pct:.0f}%)", flush=True)

    return int(np.sum(~dominated))


def compute_fogo_frontier_fraction() -> dict:
    """
    Fogo Pareto frontier fraction under min-max normalisation.
    Reads \\Fmmsize and \\Ntrios from macros/macros_structural.tex
    (auto-generated; providecommand format).
    """
    import re
    struct_path = ROOT / "macros" / "macros_structural.tex"
    text = struct_path.read_text(encoding="utf-8")
    m_fmm  = re.search(r"\\providecommand\{\\Fmmsize\}\{(\d+)\}", text)
    m_ntri = re.search(r"\\providecommand\{\\Ntrios\}\{([\d{,}]+)\}", text)
    if not m_fmm or not m_ntri:
        raise RuntimeError(f"Cannot parse \\Fmmsize / \\Ntrios from {struct_path}")
    FMMSIZE = int(m_fmm.group(1))
    NTRIOS  = int(m_ntri.group(1).replace("{", "").replace("}", "").replace(",", ""))
    pct = FMMSIZE / NTRIOS * 100.0
    print(f"  Fogo |F| = {FMMSIZE}, |T| = {NTRIOS}, fraction = {pct:.4f}%")
    return {"fmmsize": FMMSIZE, "ntrios": NTRIOS,
            "fraction_pct": round(pct, 4)}


def compute_sn_frontier() -> dict:
    """Compute |F(w0)|/|T| for S-N from the sealed site data."""
    csv_path = RESULTS / "df_santiago_sn.csv"
    sha_csv  = sha256_file(csv_path)
    print(f"  df_santiago_sn.csv SHA: {sha_csv[:16]}")

    df = pd.read_csv(csv_path)
    df_via = df[df["admissible"] == 1].copy().reset_index(drop=True)

    print(f"  N_adm={len(df_via)} (expected 190 from stage3b_descriptors)")

    # Criterion matrix
    X = df_via[SN_CRIT_COLS].values.astype(np.float64)

    # Min-max normalise over admissible sites (same ref as MC)
    X_norm = minmax_norm(X)
    X_adj  = benefit_adjust(X_norm, SN_BENEFIT)

    # Group objective values per site (all to maximize)
    F_site = compute_group_objectives(X_adj, SN_W0, SN_GROUPS)

    # Enumerate feasible trios
    lat = df_via["latitude (degrees)"].values
    lon = df_via["longitude (degrees)"].values
    print(f"  Building trio array (N={len(df_via)}, d_min={D_MIN_SN} km)...", flush=True)
    trios = build_trio_array(lat, lon, D_MIN_SN)
    n_trios = len(trios)
    print(f"  n_trios={n_trios:,} (expected 77,995 from stage3b_descriptors)")

    # Portfolio group objectives: sum over 3 sites
    i0, i1, i2 = trios[:,0], trios[:,1], trios[:,2]
    F_port = F_site[i0] + F_site[i1] + F_site[i2]   # (n_trios, 4)

    print("  Computing Pareto front size...", flush=True)
    front_size = pareto_front_size(F_port)
    fraction   = front_size / n_trios * 100.0

    print(f"  |F(w0)| = {front_size:,}  |T| = {n_trios:,}  fraction = {fraction:.2f}%")

    return {
        "n_adm":      len(df_via),
        "n_trios":    n_trios,
        "front_size": front_size,
        "fraction_pct": round(fraction, 2),
        "sha_csv":    sha_csv,
    }


# ─────────────────────────────────────────────────────────────────────────────
# K5 deviation check
# ─────────────────────────────────────────────────────────────────────────────

def check_k5_stage3() -> dict:
    """
    Check whether stage3b_descriptors.json (committed before stage4-launch)
    contains K5 κ=∞ contrasts.
    Returns a dict with 'present' flag and verification values from MC row.
    """
    desc_path = RESULTS / "stage3b_descriptors.json"
    sha_desc  = sha256_file(desc_path)
    print(f"  stage3b_descriptors.json SHA: {sha_desc[:16]}")

    with open(desc_path, encoding="utf-8") as fh:
        desc = json.load(fh)

    # Keys in stage3b_descriptors.json
    st_keys = set(desc.get("S-T", {}).keys())
    sn_keys = set(desc.get("S-N", {}).keys())
    k5_keys = {"K5_assembly_kappa_inf", "K5_agg_kappa_inf",
               "kappa_inf_assembly", "kappa_inf_contrast",
               "assembly_inf", "agg_inf"}

    k5_in_desc = bool(st_keys & k5_keys or sn_keys & k5_keys)

    # Verify K5 from the κ=∞ row in MC raw CSVs
    mc_st = pd.read_csv(RESULTS / "mc_ST_raw.csv")
    mc_sn = pd.read_csv(RESULTS / "mc_SN_raw.csv")

    row_st = mc_st[np.isinf(mc_st["kappa"])].iloc[0]
    row_sn = mc_sn[np.isinf(mc_sn["kappa"])].iloc[0]

    # K5(a) = Q2(SAW,vec,opt) - Q2(SAW,vec,grd)  at κ=∞  [pp]
    st_k5a = (float(row_st["SAW_vec_opt"]) - float(row_st["SAW_vec_grd"])) * 100.0
    sn_k5a = (float(row_sn["SAW_vec_opt"]) - float(row_sn["SAW_vec_grd"])) * 100.0

    # K5(b) = (1/3)*[(SAW_mm_grd-TOPSIS_mm_grd)+(SAW_vec_grd-TOPSIS_vec_grd)
    #                +(SAW_vec_opt-TOPSIS_vec_opt)]  at κ=∞  [pp]
    def agg3(row):
        return (1/3) * (
            (float(row["SAW_mm_grd"])  - float(row["TOPSIS_mm_grd"]))  +
            (float(row["SAW_vec_grd"]) - float(row["TOPSIS_vec_grd"])) +
            (float(row["SAW_vec_opt"]) - float(row["TOPSIS_vec_opt"]))
        ) * 100.0

    st_k5b = agg3(row_st)
    sn_k5b = agg3(row_sn)

    print(f"  K5 in stage3b_descriptors: {k5_in_desc}")
    print(f"  S-T K5(a)=+{st_k5a:.1f} pp  K5(b)={st_k5b:.1f} pp  at kappa=inf")
    print(f"  S-N K5(a)=+{sn_k5a:.1f} pp  K5(b)={sn_k5b:.1f} pp  at kappa=inf")

    return {
        "k5_in_stage3_descriptors": k5_in_desc,
        "ST_K5a_inf_pp": round(st_k5a, 1),
        "ST_K5b_inf_pp": round(st_k5b, 1),
        "SN_K5a_inf_pp": round(sn_k5a, 1),
        "SN_K5b_inf_pp": round(sn_k5b, 1),
        "deviation": (
            "stage3b_descriptors.json does not contain K5 kappa=inf contrasts; "
            "they were first computed in Stage 4 MC. K5 is descriptive; no "
            "verdict is affected. Registered as DEV-SANT-K5B-001 if not present."
        ) if not k5_in_desc else "OK: K5 contrasts present in Stage 3 descriptors.",
        "sha_desc": sha_desc,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Write macros
# ─────────────────────────────────────────────────────────────────────────────

def write_macros(out: dict, macros_path: Path):
    """Write LaTeX macros for the descriptive quantities."""
    reg   = out["regadios"]
    areas = out.get("clipping_areas", {})
    fogo_f = out.get("frontier_fogo", {})
    sn_f   = out.get("frontier_sn", {})

    lines = [
        "% AUTO-GENERATED by scripts/compute_descriptive.py — DO NOT EDIT BY HAND",
        f"% carta_agricola SHA: {reg['sha_carta'][:16]}",
        f"% sn_boundary SHA:    {reg['sha_sn_boundary'][:16]}",
        "% Denominator: santiago_sn_boundary.geojson (3 concelhos, ~387 km²)",
        "% Reference:   DEV-SANT-A5-001 reports 3.6% with same polygon",
        "",
        "% Regadios fraction (irrigated perimeters / S-N study area)",
        f"\\newcommand{{\\SantSNRegadiosPct}}{{{reg['regadio_pct']}}}",
        f"% Regadios: {reg['regadio_in_sn_km2']:.3f} km² / {reg['sn_area_km2']:.3f} km²",
        "",
    ]

    if areas:
        lines += [
            "% GIS areas of the three clipping polygons (same CRS, same method)",
            f"% fogo_boundary_geol.geojson SHA: {areas['fogo_sha'][:16]}",
            f"% santiago_boundary.geojson  SHA: {areas['st_sha'][:16]}",
            f"% santiago_sn_boundary.geojson SHA: {areas['sn_sha'][:16]}",
            f"\\newcommand{{\\FogoAreaGIS}}{{{areas['fogo_km2']}}}",
            f"\\newcommand{{\\SantSTAreaGIS}}{{{areas['st_km2']}}}",
            f"\\newcommand{{\\SantSNAreaGIS}}{{{areas['sn_km2']}}}",
            f"% Cited published area for S-N (Cabral 2012): {SANT_SN_AREA_CABRAL_KM2} km²",
            f"\\newcommand{{\\SantSNAreaCabral}}{{{SANT_SN_AREA_CABRAL_KM2}}}",
            "",
        ]

    if fogo_f:
        lines += [
            "% Fogo Pareto frontier fraction |F(w0)| / |T| (mm-frontier)",
            f"% Source: macros/macros_structural.tex \\Fmmsize{{{fogo_f['fmmsize']}}} \\Ntrios{{...}}",
            f"\\newcommand{{\\FrontFracFogo}}{{{fogo_f['fraction_pct']}}}",
            f"% |F|={fogo_f['fmmsize']}, |T|={fogo_f['ntrios']}",
            "",
        ]

    if sn_f:
        lines += [
            "% S-N Pareto frontier fraction |F(w0)| / |T| (4-objective, nominal w0)",
            f"% df_santiago_sn.csv SHA: {sn_f['sha_csv'][:16]}",
            f"\\newcommand{{\\FrontFracSN}}{{{sn_f['fraction_pct']}}}",
            f"% |F|={sn_f['front_size']}, |T|={sn_f['n_trios']}",
            "",
        ]
    else:
        lines += [
            "% S-T frontier fraction: pending (run on Athena)",
            "% \\newcommand{\\FrontFracST}{...}",
            "",
        ]

    with open(macros_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"  Macros written to {macros_path.name}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-frontier", action="store_true",
                        help="Skip frontier fraction computation (for quick test)")
    args = parser.parse_args()

    results = {}

    print("\n=== (a2) Clipping polygon areas ===")
    results["clipping_areas"] = compute_clipping_areas()

    print("\n=== (a) Regadios fraction ===")
    results["regadios"] = compute_regadios_fraction()

    print("\n=== (b) Fogo frontier fraction ===")
    results["frontier_fogo"] = compute_fogo_frontier_fraction()

    if not args.skip_frontier:
        print("\n=== (c) S-N frontier fraction ===")
        results["frontier_sn"] = compute_sn_frontier()
    else:
        print("\n=== (c) S-N frontier fraction [SKIPPED] ===")

    print("\n=== K5 deviation check ===")
    results["k5_check"] = check_k5_stage3()

    # Save JSON
    out_path = RESULTS / "descriptive_output.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nResults saved to {out_path.relative_to(ROOT)}")

    # Write macros
    macros_path = RESULTS / "macros_descriptive.tex"
    write_macros(results, macros_path)

    # Summary
    print("\n=== Summary ===")
    print(f"  FogoAreaGIS       : {results['clipping_areas']['fogo_km2']} km²")
    print(f"  SantSTAreaGIS     : {results['clipping_areas']['st_km2']} km²")
    print(f"  SantSNAreaGIS     : {results['clipping_areas']['sn_km2']} km²")
    print(f"  SantSNAreaCabral  : {SANT_SN_AREA_CABRAL_KM2} km² (cited)")
    print(f"  SantSNRegadiosPct : {results['regadios']['regadio_pct']:.1f}%")
    print(f"  FrontFracFogo     : {results['frontier_fogo']['fraction_pct']:.4f}%")
    if "frontier_sn" in results:
        print(f"  FrontFracSN       : {results['frontier_sn']['fraction_pct']:.2f}%")
        print(f"  (S-T frontier fraction: pending — run on Athena)")
    k5 = results["k5_check"]
    print(f"  K5 in Stage 3 desc: {k5['k5_in_stage3_descriptors']}")
    if not k5["k5_in_stage3_descriptors"]:
        print(f"  S-T K5(a)=+{k5['ST_K5a_inf_pp']} pp  K5(b)={k5['ST_K5b_inf_pp']} pp  (kappa=inf, from MC)")
        print(f"  S-N K5(a)=+{k5['SN_K5a_inf_pp']} pp  K5(b)={k5['SN_K5b_inf_pp']} pp  (kappa=inf, from MC)")
        print(f"  DEVIATION: {k5['deviation']}")


if __name__ == "__main__":
    main()
