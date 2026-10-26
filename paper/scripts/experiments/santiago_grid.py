#!/usr/bin/env python3
"""
santiago_grid.py — candidate grid + geometry-only trio count (PRESPEC_SANTIAGO §3).

Reads ONLY boundary geometry (and, in fogo-check mode, Fogo reference files).
Never reads any Santiago criterion layer.

Modes
  --selftest            verify the trio counter against brute-force enumeration
  --mode fogo-check     validate the declared grid rule on Fogo (PRE-A / contingency C-1)
  --mode santiago       build the S-T or S-N grid and apply the spacing rule (needs tag F0)

Conventions (confirmed from Landfill_NSGA2_Paper_Final.ipynb, the source of df_real_data_cached.csv):
  --origin   {bbox, floor1m, snap}
    bbox:    grid starts at exact bounding-box lower-left (xmin, ymin)
    floor1m: grid starts at floor(xmin), floor(ymin) — rounds to nearest metre (notebook convention)
    snap:    grid starts at floor(xmin/spacing)*spacing — rounds to nearest km
  --centroid {cell, land}
    cell:    candidate = midpoint of full 1 km × 1 km cell
    land:    candidate = centroid of land-covered intersection (notebook convention);
             includes a post-filter: candidates whose centroid is not within(island) are removed
"""
import argparse, datetime, hashlib, json, subprocess, sys
from itertools import combinations
from pathlib import Path

import numpy as np
import geopandas as gpd
from shapely.geometry import box

R_EARTH_KM = 6371.0                     # same constant as validate_core.py
PRESPEC_TAG = "prespec-santiago-f0"
FOGO_EXPECTED = {"n_cand": 473, "n_adm": 389, "n_trios": 1_944_653}

# ── provenance ────────────────────────────────────────────────────────────────
def sha256_lf(path):
    """SHA-256 over bytes; text formats normalised to LF (project convention)."""
    p = Path(path)
    if p.is_dir():                                   # e.g. shapefile folder: hash all members
        h = hashlib.sha256()
        for f in sorted(p.iterdir()):
            h.update(f.name.encode()); h.update(sha256_lf(f).encode())
        return h.hexdigest()
    b = p.read_bytes()
    if p.suffix.lower() in {".geojson", ".json", ".csv", ".txt", ".prj"}:
        b = b.replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()

def hash_vector_source(path):
    """Hash a vector file and, for shapefiles, its sidecar files."""
    p = Path(path)
    if p.suffix.lower() == ".shp":
        h = hashlib.sha256()
        for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
            f = p.with_suffix(ext)
            if f.exists():
                h.update(ext.encode()); h.update(sha256_lf(f).encode())
        return h.hexdigest()
    return sha256_lf(p)

def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.stdout.strip(), r.returncode

def git_state():
    commit, _ = git("rev-parse", "HEAD")
    describe, _ = git("describe", "--always", "--dirty", "--tags")
    status, _ = git("status", "--porcelain", "--untracked-files=no")
    return {"commit": commit, "describe": describe, "dirty": bool(status)}

def require_provenance(allow_dirty, need_tag):
    st = git_state()
    if st["dirty"] and not allow_dirty:
        sys.exit("ABORT: tracked files modified. Commit first (rule: nothing runs uncommitted).")
    if need_tag:
        tag, _ = git("tag", "-l", PRESPEC_TAG)
        if not tag:
            sys.exit(f"ABORT: tag '{PRESPEC_TAG}' not found. Santiago grid runs only after Phase 0.")
        _, rc = git("merge-base", "--is-ancestor", PRESPEC_TAG, "HEAD")
        if rc != 0:
            sys.exit(f"ABORT: HEAD does not descend from '{PRESPEC_TAG}'.")
    return st

# ── geometry ──────────────────────────────────────────────────────────────────
def load_region(path, crs, field=None, values=None):
    g = gpd.read_file(path)
    if g.crs is None:
        sys.exit(f"ABORT: {path} has no CRS.")
    if field:
        if field not in g.columns:
            sys.exit(f"ABORT: field '{field}' not in {list(g.columns)}")
        sel = g[g[field].isin(values)]
        missing = set(values) - set(sel[field])
        if missing:
            sys.exit(f"ABORT: region values not found in '{field}': {sorted(missing)}")
        g = sel
    g = g.to_crs(crs)
    geom = g.geometry.make_valid().union_all()
    return geom, len(g)

def build_grid(region, crs, spacing, origin, centroid, land_frac):
    xmin, ymin, xmax, ymax = region.bounds
    if origin == "bbox":
        x0, y0 = xmin, ymin
    elif origin == "floor1m":
        # Source notebook convention: np.floor(xmin) — rounds to nearest metre.
        # Different from snap (which rounds to nearest spacing multiple).
        x0, y0 = np.floor(xmin), np.floor(ymin)
    else:  # snap
        x0, y0 = np.floor(xmin / spacing) * spacing, np.floor(ymin / spacing) * spacing
    xs = np.arange(x0, xmax, spacing)
    ys = np.arange(y0, ymax, spacing)
    rows, cols, cells = [], [], []
    for r, y in enumerate(ys):
        for c, x in enumerate(xs):
            rows.append(r); cols.append(c); cells.append(box(x, y, x + spacing, y + spacing))
    cells = gpd.GeoSeries(cells, crs=crs)
    land = cells.intersection(region)
    frac = (land.area / spacing**2).to_numpy()
    keep = frac >= land_frac
    near_threshold = int(np.sum(np.abs(frac - land_frac) < 1e-6))   # ambiguity flag

    if centroid == "cell":
        pts_geom = cells[keep].centroid
    else:  # "land" — centroid of the land intersection (source notebook convention)
        pts_geom = land[keep].centroid
        # Second filter: centroid must be within island (source notebook Method 2)
        within_island = pts_geom.within(region)
        keep_idx = within_island[within_island].index
        pts_geom = pts_geom.loc[keep_idx]
        frac_keep = frac[keep]
        frac_keep = frac_keep[within_island.values]
        # Rebuild rows/cols for kept cells
        rows_arr = np.array(rows)[keep][within_island.values]
        cols_arr = np.array(cols)[keep][within_island.values]
        pts_geom = pts_geom.reset_index(drop=True)
    
    if centroid == "cell":
        frac_keep = frac[keep]
        rows_arr = np.array(rows)[keep]
        cols_arr = np.array(cols)[keep]
        pts_geom = pts_geom.reset_index(drop=True)

    ll = pts_geom.to_crs(4326)
    cand = gpd.GeoDataFrame({
        "cand_id": np.arange(int(len(pts_geom))),
        "row": rows_arr, "col": cols_arr,
        "land_frac": frac_keep,
        "x": pts_geom.x.to_numpy(), "y": pts_geom.y.to_numpy(),
        "lon": ll.x.to_numpy(), "lat": ll.y.to_numpy(),
    }, geometry=pts_geom, crs=crs)
    return cand, {"n_cells_total": int(len(cells)), "n_near_threshold": near_threshold}

def haversine_matrix(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    dlat = la[:, None] - la[None, :]
    dlon = lo[:, None] - lo[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(la)[:, None] * np.cos(la)[None, :] * np.sin(dlon / 2) ** 2
    return 2 * R_EARTH_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))

def count_trios(D, dmin):
    """Number of 3-cliques of the graph D >= dmin: trace(A^3)/6 (exact in float64 for N < 2e5)."""
    A = (D >= dmin).astype(np.float64)
    np.fill_diagonal(A, 0.0)
    t = float(np.einsum("ij,ji->", A @ A, A))
    n = int(round(t / 6.0))
    assert abs(t / 6.0 - n) < 1e-6, "non-integer trio count"
    n_pairs = int(A.sum() // 2)
    near = int(np.sum(np.abs(D[np.triu_indices_from(D, 1)] - dmin) < 1e-6))
    return n, n_pairs, near

# ── modes ─────────────────────────────────────────────────────────────────────
def selftest():
    rng = np.random.default_rng(0)
    for trial in range(5):
        n = 40
        lat = 15.0 + rng.uniform(0, 0.3, n); lon = -24.4 + rng.uniform(0, 0.3, n)
        D = haversine_matrix(lat, lon)
        fast, _, _ = count_trios(D, 10.0)
        brute = sum(1 for i, j, k in combinations(range(n), 3)
                    if D[i, j] >= 10 and D[i, k] >= 10 and D[j, k] >= 10)
        assert fast == brute, (trial, fast, brute)
    print("SELFTEST: trio counter == brute force on 5 random instances. PASS")

def write_outputs(out, cand, D, report, force):
    out = Path(out)
    if out.exists() and any(out.iterdir()) and not force:
        sys.exit(f"ABORT: {out} not empty; use another --out or --force (validated artefacts are never overwritten).")
    out.mkdir(parents=True, exist_ok=True)
    cand.drop(columns="geometry").to_csv(out / "candidates.csv", index=False, lineterminator="\n")
    np.save(out / "D_km.npy", D)
    report["outputs"] = {f: sha256_lf(out / f) for f in ("candidates.csv", "D_km.npy")}
    (out / "grid_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                                          encoding="utf-8")
    print(f"Outputs written to {out}")

def fogo_check(a, base):
    region, n_feat = load_region(a.boundary, a.crs)
    cand, gmeta = build_grid(region, a.crs, a.spacing, a.origin, a.centroid, a.land_frac)
    D = haversine_matrix(cand.lat.to_numpy(), cand.lon.to_numpy())
    rep = {**base, "mode": "fogo-check", "boundary_features": n_feat, **gmeta,
           "n_cand": int(len(cand)), "expected": FOGO_EXPECTED}

    if a.reference_csv:                                    # match published candidates
        import pandas as pd
        df = pd.read_csv(a.reference_csv)
        rp = gpd.GeoSeries(gpd.points_from_xy(df[a.ref_lon], df[a.ref_lat]), crs=4326).to_crs(a.crs)
        cx, cy = cand.x.to_numpy(), cand.y.to_numpy()
        dist = np.hypot(rp.x.to_numpy()[:, None] - cx[None, :], rp.y.to_numpy()[:, None] - cy[None, :])
        nearest = dist.min(axis=1)
        rep["reference"] = {
            "n_ref": int(len(df)),
            "ref_matched_within_tol": int(np.sum(nearest <= a.match_tol_m)),
            "match_tol_m": a.match_tol_m,
            "nearest_dist_m_quantiles": np.quantile(nearest, [0, .5, .95, 1]).round(3).tolist(),
            "cand_matched_by_ref": int(np.sum(dist.min(axis=0) <= a.match_tol_m)),
        }
        # Diagnostic: are unmatched candidates all coastal (land_frac < 1)?
        mism = dist.min(axis=0) > a.match_tol_m
        if mism.any():
            rep["reference"]["mismatch_land_frac_quantiles"] = (
                np.quantile(cand.land_frac.to_numpy()[mism], [0, .5, 1]).round(4).tolist()
            )
            rep["reference"]["mismatch_all_coastal"] = bool(
                (cand.land_frac.to_numpy()[mism] < 1.0).all()
            )
        else:
            rep["reference"]["mismatch_land_frac_quantiles"] = []
            rep["reference"]["mismatch_all_coastal"] = True  # no mismatches = vacuously true
        rep["reference_csv_sha256"] = sha256_lf(a.reference_csv)

    if a.exclude:                                          # Fogo exclusion: centroid inside protected
        prot, _ = load_region(a.exclude, a.crs)
        inside = cand.geometry.intersects(prot).to_numpy()
        adm = ~inside
        Dadm = D[np.ix_(adm, adm)]
        n_tr, n_pairs, near = count_trios(Dadm, a.dmin)
        rep.update({"n_excl": int(inside.sum()), "n_adm": int(adm.sum()),
                    "n_trios_adm": n_tr, "n_pairs_adm": n_pairs, "pairs_near_dmin": near,
                    "exclude_sha256": hash_vector_source(a.exclude)})

    rep["verdict"] = {
        "n_cand_matches_473": rep["n_cand"] == FOGO_EXPECTED["n_cand"],
        "n_adm_matches_389": rep.get("n_adm") == FOGO_EXPECTED["n_adm"] if a.exclude else None,
        "n_trios_matches": rep.get("n_trios_adm") == FOGO_EXPECTED["n_trios"] if a.exclude else None,
    }
    print(json.dumps(rep["verdict"], indent=2), "\nN_cand =", rep["n_cand"])
    if not rep["verdict"]["n_cand_matches_473"]:
        print("→ Record contingency C-1 in the PRESPEC (declared rule applied to Santiago unchanged).")
    write_outputs(a.out, cand, D, rep, a.force)

def santiago(a, base):
    region, n_feat = load_region(a.boundary, a.crs, a.region_field, a.region_values)
    spacing, tried, decision = a.spacing, [], None
    while True:
        cand, gmeta = build_grid(region, a.crs, spacing, a.origin, a.centroid, a.land_frac)
        D = haversine_matrix(cand.lat.to_numpy(), cand.lon.to_numpy())
        n_tr, n_pairs, near = count_trios(D, a.dmin)
        tried.append({"spacing_m": spacing, "n_cand": int(len(cand)), "n_trios_cand": n_tr,
                      "n_pairs": n_pairs, "pairs_near_dmin": near, **gmeta})
        print(f"spacing {spacing:.0f} m: N_cand={len(cand)}  n_trios(N_cand)={n_tr:,}")
        # Phase 1: increase spacing if over limit
        if n_tr > a.trio_limit:
            spacing += a.step
            if spacing > a.max_spacing:
                decision = "abandon_trio_limit"
                break
            continue
        # Phase 2: decrease spacing if under minimum
        if n_tr < a.trio_min:
            spacing -= a.step
            if spacing < a.min_spacing:
                decision = "abandon_trio_min"
                break
            continue
        break  # n_trios in [trio_min, trio_limit]: accept

    final = tried[-1]
    if decision is None:
        if final["n_cand"] < 100:
            decision = "flag_ncand_below_100"
        else:
            decision = "ok"

    rep = {**base, "mode": "santiago", "branch": a.branch, "boundary_features": n_feat,
           "region_field": a.region_field, "region_values": a.region_values,
           "spacing_trials": tried, "final_spacing_m": final["spacing_m"],
           "n_cand": final["n_cand"], "n_trios_cand_upper_bound": final["n_trios_cand"],
           "decision": decision,
           "note": "n_trios is computed on N_cand (before exclusions): an upper bound on n_trios(A')."}
    print("DECISION:", decision)
    write_outputs(a.out, cand, D, rep, a.force)

# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--mode", choices=["fogo-check", "santiago"])
    p.add_argument("--branch", choices=["ST", "SN"])
    p.add_argument("--boundary")
    p.add_argument("--region-field"); p.add_argument("--region-values", nargs="+")
    p.add_argument("--crs", type=int, help="projected EPSG (Fogo 32626, Santiago 32627)")
    p.add_argument("--origin", choices=["bbox", "floor1m", "snap"])
    p.add_argument("--centroid", choices=["cell", "land"])
    p.add_argument("--spacing", type=float, default=1000.0)
    p.add_argument("--land-frac", type=float, default=0.5)
    p.add_argument("--dmin", type=float, default=10.0, help="km")
    p.add_argument("--trio-limit", type=int, default=50_000_000)
    p.add_argument("--trio-min", type=int, default=10_000)
    p.add_argument("--step", type=float, default=250.0)
    p.add_argument("--max-spacing", type=float, default=5000.0)
    p.add_argument("--min-spacing", type=float, default=500.0,
                   help="minimum spacing in m when decreasing for trio_min (default 500)")
    p.add_argument("--reference-csv"); p.add_argument("--ref-lat", default="latitude (degrees)")
    p.add_argument("--ref-lon", default="longitude (degrees)")
    p.add_argument("--match-tol-m", type=float, default=1.0)
    p.add_argument("--exclude", help="fogo-check only: protected-area polygons")
    p.add_argument("--out"); p.add_argument("--force", action="store_true")
    p.add_argument("--allow-dirty", action="store_true", help="fogo-check only; recorded in report")
    a = p.parse_args()

    if a.selftest:
        selftest(); return
    for req in ("mode", "boundary", "crs", "origin", "centroid", "out"):
        if getattr(a, req) is None:
            sys.exit(f"ABORT: --{req.replace('_', '-')} is required (conventions must be explicit).")
    if a.mode == "santiago":
        if a.branch is None: sys.exit("ABORT: --branch required in santiago mode.")
        if a.branch == "SN" and not (a.region_field and a.region_values):
            sys.exit("ABORT: S-N needs --region-field and --region-values (the three concelhos).")
        if a.allow_dirty: sys.exit("ABORT: --allow-dirty is not permitted in santiago mode.")
        if a.exclude: sys.exit("ABORT: exclusions are applied in Phase 1, not here.")

    st = require_provenance(a.allow_dirty, need_tag=(a.mode == "santiago"))
    import datetime as _dt
    base = {
        "script": "santiago_grid.py",
        "timestamp_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "git": st, "boundary": str(a.boundary), "boundary_sha256": hash_vector_source(a.boundary),
        "params": {k: getattr(a, k) for k in ("crs", "origin", "centroid", "spacing", "land_frac",
                                              "dmin", "trio_limit", "trio_min", "step", "max_spacing")},
        "distance": "haversine on WGS84 lat/lon of projected centroids, R = 6371.0 km",
        "threshold_rules": "keep cell iff land_frac >= land_frac; pair feasible iff D >= dmin (no epsilon)",
    }
    fogo_check(a, base) if a.mode == "fogo-check" else santiago(a, base)

if __name__ == "__main__":
    main()
