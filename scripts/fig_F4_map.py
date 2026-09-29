"""fig_F4_map.py -- Fogo Island map, IEEE-style.

Island outline from geologia_fogo.shp (dissolved to single exterior polygon),
grey dots = 389 admissible sites, blue diamonds = best-compromise {184,430,460},
dashed circles = d_min separation, settlements, north arrow, scale bar.
"""

import sys, os, csv, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig_utils import set_rcparams, savefig, COL1, C_TREATMENT, C_GRAY

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

set_rcparams()

here     = os.path.dirname(os.path.abspath(__file__))
SHP_PATH = (
    "G:\\Faculdade\\Estudo\\Doutorado\\2025.1\\Otimiza\u00e7\u00e3o Bioinspirada"
    "\\Tentativa de dados via GIS\\geologia_fogo.shp"
)

# ── Load site data ─────────────────────────────────────────────────────────
sites = []
with open(os.path.join(here, "results", "mcdm_rankings.csv")) as f:
    for r in csv.DictReader(f):
        sites.append({
            "idx": int(r[""]),
            "lat": float(r["latitude (degrees)"]),
            "lon": float(r["longitude (degrees)"]),
        })

lats = [s["lat"] for s in sites]
lons = [s["lon"] for s in sites]
bcs_target = {"184", "430", "460"}
bcs = [s for s in sites if str(s["idx"]) in bcs_target]
bcs_lat = [s["lat"] for s in bcs]
bcs_lon = [s["lon"] for s in bcs]

D_MIN_KM   = 10.0
lat_center = sum(lats) / len(lats)
lon_scale  = math.cos(math.radians(lat_center))
r_lat_deg  = D_MIN_KM / 111.0

# ── Load island shapefile ──────────────────────────────────────────────────
island_polys = None
try:
    import geopandas as gpd
    from shapely.ops import unary_union
    from shapely.geometry import Polygon
    gdf = gpd.read_file(SHP_PATH)
    gdf_ll = gdf.to_crs(epsg=4326)
    island_union = unary_union(gdf_ll.geometry)
    if island_union.geom_type == "MultiPolygon":
        exterior_polys = [Polygon(p.exterior) for p in island_union.geoms]
    else:
        exterior_polys = [Polygon(island_union.exterior)]
    island_polys = gpd.GeoDataFrame(geometry=exterior_polys, crs="EPSG:4326")
except Exception as e:
    import sys
    print(f"Could not load shapefile: {e}", file=sys.stderr)

# ── Figure ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(COL1 * 1.15, COL1 * 1.25))

# 1. Island outline
if island_polys is not None:
    island_polys.plot(ax=ax, facecolor="none", edgecolor="#555555",
                      linewidth=0.8, zorder=1)

# 2. All admissible sites (grey dots)
ax.scatter(lons, lats, s=5, color=C_GRAY, alpha=0.55,
           linewidths=0, zorder=2,
           label=f"Admissible sites ($n = 389$)")

# 3. d_min separation circles (dashed)
for lat_c, lon_c in zip(bcs_lat, bcs_lon):
    el = Ellipse((lon_c, lat_c),
                 width=2 * r_lat_deg / lon_scale,
                 height=2 * r_lat_deg,
                 fill=False, edgecolor=C_TREATMENT,
                 linestyle="--", linewidth=1.0, alpha=0.6, zorder=4)
    ax.add_patch(el)

# 4. Best-compromise portfolio
ax.scatter(bcs_lon, bcs_lat, s=90, color=C_TREATMENT,
           marker="D", zorder=5, linewidths=0.7, edgecolors="white",
           label=r"Best-compromise $\{184,\,430,\,460\}$")

# 5. Site labels
label_cfg = {
    "184": {"dx": -0.030, "dy":  0.000, "ha": "right", "va": "center"},
    "430": {"dx":  0.012, "dy":  0.006, "ha": "left",  "va": "bottom"},
    "460": {"dx":  0.012, "dy":  0.006, "ha": "left",  "va": "bottom"},
}
for s in bcs:
    cfg = label_cfg.get(str(s["idx"]),
                        {"dx": 0.010, "dy": 0.006, "ha": "left", "va": "bottom"})
    ax.text(s["lon"] + cfg["dx"], s["lat"] + cfg["dy"],
            f"#{s['idx']}", fontsize=9.5, color=C_TREATMENT,
            fontweight="bold", ha=cfg["ha"], va=cfg["va"], zorder=6)

# 6. Settlements
settlements = {
    "Sao Filipe":     (14.897, -24.496, "right"),
    "Mosteiros":      (15.039, -24.335, "right"),
    "Sta. Catarina":  (14.881, -24.284, "left"),
}
for name, (lat_s, lon_s, align) in settlements.items():
    ax.plot(lon_s, lat_s, "s", color="#333333", ms=4.5, zorder=7,
            markeredgewidth=0)
    dx_t = -0.005 if align == "right" else 0.005
    ax.text(lon_s + dx_t, lat_s + 0.005, name,
            fontsize=7.5, color="#333333", ha=align, va="bottom",
            style="italic", zorder=7)

# 7. North arrow (top-right corner)
ax.annotate("", xy=(0.96, 0.96), xytext=(0.96, 0.88),
            xycoords="axes fraction",
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2))
ax.text(0.96, 0.975, "N", transform=ax.transAxes,
        ha="center", va="bottom", fontsize=10, fontweight="bold")

# 8. Scale bar (5 km) — lower-right, outside island body
five_km_deg = 5.0 / (111.0 * lon_scale)
x_right = max(lons) + 0.19
y_sb    = min(lats) + 0.005
ax.plot([x_right - five_km_deg, x_right], [y_sb, y_sb],
        "-", color="black", lw=2, zorder=8, clip_on=False)
ax.plot([x_right - five_km_deg]*2, [y_sb - 0.002, y_sb + 0.002],
        "-", color="black", lw=1.5, zorder=8, clip_on=False)
ax.plot([x_right]*2, [y_sb - 0.002, y_sb + 0.002],
        "-", color="black", lw=1.5, zorder=8, clip_on=False)
ax.text(x_right - five_km_deg / 2, y_sb - 0.005, "5 km",
        ha="center", va="top", fontsize=8, color="black", clip_on=False)

# 9. d_min annotation — below scale bar, right-aligned, clear of island
ax.text(0.97, 0.03,
        fr"Dashed circles: $d_{{\min}} = {D_MIN_KM:.1f}$ km",
        transform=ax.transAxes, fontsize=8.5, color="#555555",
        ha="right", va="bottom", zorder=8)

# 10. Axes
ax.set_aspect(1 / lon_scale)
ax.set_xlim(min(lons) - 0.06, max(lons) + 0.29)
ax.set_ylim(min(lats) - 0.06, max(lats) + 0.05)
ax.tick_params(labelsize=8)
ax.set_xlabel("Longitude (\u00b0)", fontweight="bold")
ax.set_ylabel("Latitude (\u00b0)", fontweight="bold")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# 11. Legend
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13),
          ncol=1, frameon=False, fontsize=9)

plt.tight_layout(pad=0.5)
plt.subplots_adjust(bottom=0.20)
savefig(fig, "fig_F4_map")
