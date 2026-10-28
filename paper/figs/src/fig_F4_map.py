"""fig_F4_map.py -- Fogo Island map, IEEE-style full-page.

Uses geologia_fogo.shp with ALL internal polygons (not dissolved) to render
the detailed river/ravine network exactly as in the IEEE reference figure.
No lat/lon axis labels -- island fills the plot area.
"""

import sys, os, csv, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig_utils import set_rcparams, savefig, COL1, C_TREATMENT, C_GRAY

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches

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

# ── Load island shapefile (ALL polygons — keeps internal river lines) ──────
island_gdf = None
try:
    import geopandas as gpd
    gdf = gpd.read_file(SHP_PATH)
    island_gdf = gdf.to_crs(epsg=4326)
except Exception as e:
    import sys as _sys
    print(f"Could not load shapefile: {e}", file=_sys.stderr)

# ── Figure — double-column width, tall ────────────────────────────────────
# Elsevier double column = 190 mm. COL1 ≈ 88 mm, so 2*COL1 ≈ 176 mm ≈ 6.9 in
FIG_W = COL1 * 2.2   # full double-column width (Elsevier ~190 mm)
FIG_H = FIG_W * 0.85  # slightly less tall — island + margins

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))

# 1. Island geology (all polygons — gives internal river/ravine detail)
if island_gdf is not None:
    island_gdf.plot(ax=ax, facecolor="none", edgecolor="#666666",
                    linewidth=0.5, zorder=1)
    # Also draw a thicker outer boundary by dissolving only for the outline
    from shapely.ops import unary_union
    from shapely.geometry import Polygon
    import geopandas as gpd2
    outer = unary_union(island_gdf.geometry)
    if outer.geom_type == "MultiPolygon":
        ext_polys = [Polygon(p.exterior) for p in outer.geoms]
    else:
        ext_polys = [Polygon(outer.exterior)]
    outer_gdf = gpd2.GeoDataFrame(geometry=ext_polys, crs="EPSG:4326")
    outer_gdf.plot(ax=ax, facecolor="none", edgecolor="#333333",
                   linewidth=1.2, zorder=2)

# 2. All admissible sites (grey dots)
ax.scatter(lons, lats, s=8, color=C_GRAY, alpha=0.55,
           linewidths=0, zorder=3,
           label=f"Admissible sites ($n = 389$)")

# 3. d_min separation circles (dashed)
for lat_c, lon_c in zip(bcs_lat, bcs_lon):
    el = Ellipse((lon_c, lat_c),
                 width=2 * r_lat_deg / lon_scale,
                 height=2 * r_lat_deg,
                 fill=False, edgecolor=C_TREATMENT,
                 linestyle="--", linewidth=1.2, alpha=0.6, zorder=4)
    ax.add_patch(el)

# 4. Best-compromise portfolio
ax.scatter(bcs_lon, bcs_lat, s=160, color=C_TREATMENT,
           marker="D", zorder=5, linewidths=0.8, edgecolors="white",
           label=r"Best-compromise $\{184,\,430,\,460\}$")

# 5. Site labels — positioned clear of diamond, matching IEEE style
label_cfg = {
    "184": {"x": bcs[next(i for i,b in enumerate(bcs) if b["idx"]==184)]["lon"] - 0.04,
            "y": bcs[next(i for i,b in enumerate(bcs) if b["idx"]==184)]["lat"] + 0.012,
            "ha": "right"},
    "430": {"x": bcs[next(i for i,b in enumerate(bcs) if b["idx"]==430)]["lon"] + 0.015,
            "y": bcs[next(i for i,b in enumerate(bcs) if b["idx"]==430)]["lat"] + 0.008,
            "ha": "left"},
    "460": {"x": bcs[next(i for i,b in enumerate(bcs) if b["idx"]==460)]["lon"] + 0.015,
            "y": bcs[next(i for i,b in enumerate(bcs) if b["idx"]==460)]["lat"] + 0.008,
            "ha": "left"},
}
for s in bcs:
    cfg = label_cfg.get(str(s["idx"]))
    if cfg:
        ax.text(cfg["x"], cfg["y"], f"#{s['idx']}",
                fontsize=11, color=C_TREATMENT, fontweight="bold",
                ha=cfg["ha"], va="bottom", zorder=6)

# 6. Settlements
settlements = {
    "S\u00e3o Filipe":    (14.897, -24.496, "right"),
    "Mosteiros":         (15.039, -24.335, "left"),
    "Sta. Catarina":     (14.881, -24.284, "left"),
}
for name, (lat_s, lon_s, align) in settlements.items():
    ax.plot(lon_s, lat_s, "s", color="#222222", ms=5.5, zorder=7,
            markeredgewidth=0)
    dx_t = -0.007 if align == "right" else 0.007
    ax.text(lon_s + dx_t, lat_s + 0.006, name,
            fontsize=9, color="#222222", ha=align, va="bottom",
            style="italic", zorder=7)

# 7. North arrow (top-right, outside island)
ax.annotate("", xy=(0.965, 0.97), xytext=(0.965, 0.90),
            xycoords="axes fraction",
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.5))
ax.text(0.965, 0.975, "N", transform=ax.transAxes,
        ha="center", va="bottom", fontsize=12, fontweight="bold")

# 8. Scale bar (5 km) — lower right, inside xlim
five_km_deg = 5.0 / (111.0 * lon_scale)
x_sb = max(lons) + 0.14
y_sb = min(lats) + 0.010
ax.plot([x_sb - five_km_deg, x_sb], [y_sb, y_sb],
        "-", color="black", lw=2.5, zorder=8)
ax.plot([x_sb - five_km_deg]*2, [y_sb - 0.003, y_sb + 0.003],
        "-", color="black", lw=1.5, zorder=8)
ax.plot([x_sb]*2, [y_sb - 0.003, y_sb + 0.003],
        "-", color="black", lw=1.5, zorder=8)
ax.text(x_sb - five_km_deg / 2, y_sb + 0.006, "5 km",
        ha="center", va="bottom", fontsize=9, color="black")

# 9. d_min note — below scale bar
ax.text(x_sb, y_sb - 0.012,
        fr"Dashed: $d_{{\min}}={D_MIN_KM:.0f}$ km",
        fontsize=9, color="#555555", ha="right", va="top")

# 10. Axes: remove everything (IEEE style — no lat/lon labels or ticks)
ax.set_aspect(1 / lon_scale)
ax.set_xlim(min(lons) - 0.06, max(lons) + 0.22)
ax.set_ylim(min(lats) - 0.09, max(lats) + 0.05)  # more bottom margin for scale/note
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlabel("")
ax.set_ylabel("")
for spine in ax.spines.values():
    spine.set_visible(False)

# 11. Legend — top-left corner inside plot (IEEE style with box)
legend_elements = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor=C_GRAY,
           markersize=7, label=f"Admissible sites ($n = 389$)"),
    Line2D([0], [0], marker="D", color="w", markerfacecolor=C_TREATMENT,
           markersize=9, label=r"Best-compromise $\{184,\,430,\,460\}$"),
    Line2D([0], [0], linestyle="--", color=C_TREATMENT, lw=1.2,
           label=fr"Separation circles ($d_{{\min}} = {D_MIN_KM:.0f}$ km)"),
    Line2D([0], [0], marker="s", color="w", markerfacecolor="#222222",
           markersize=7, label="Settlements"),
]
ax.legend(handles=legend_elements,
          loc="upper left", fontsize=9,
          frameon=True, framealpha=0.9,
          edgecolor="#cccccc", fancybox=False)

plt.tight_layout(pad=0.3)
savefig(fig, "fig_F4_map")
