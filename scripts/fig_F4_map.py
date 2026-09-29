"""F4 — Map of Fogo Island candidate sites.

389 admissible sites as grey dots.
BCS portfolio {184, 430, 460} as blue diamonds with d_min=10km circles.
Single column (90 mm).

Note: no excluded-sites CSV available; map shows admissible set only.
If df_all_candidates.csv is later provided, add excluded sites in red x.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig_utils import set_rcparams, savefig, COL1, WONG
import csv, math
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle

set_rcparams()

here = os.path.dirname(os.path.abspath(__file__))

# ── Load admissible sites with lat/lon ───────────────────────────────────
sites = []
with open(os.path.join(here, "results", "mcdm_rankings.csv")) as f:
    for r in csv.DictReader(f):
        idx = int(r[""])   # original candidate index (0..472, with 84 gaps)
        lat = float(r["latitude (degrees)"])
        lon = float(r["longitude (degrees)"])
        sites.append({"idx": idx, "lat": lat, "lon": lon})

lats = [s["lat"] for s in sites]
lons = [s["lon"] for s in sites]

# ── BCS portfolio sites: look up by the original candidate index ─────────
# The '' column is the original 0-based index in the 473-candidate set.
# BCS sites {184, 430, 460} refer to these original indices.
bcs_target = {'184', '430', '460'}
bcs_sites = [s for s in sites if str(s["idx"]) in bcs_target]
print(f"BCS sites found: {[s['idx'] for s in bcs_sites]}")
if len(bcs_sites) != 3:
    raise ValueError(f"Expected 3 BCS sites, found {len(bcs_sites)}: {bcs_sites}")

bcs_lats = [s["lat"] for s in bcs_sites]
bcs_lons = [s["lon"] for s in bcs_sites]

# ── d_min circles in degrees (approx: 10km ≈ 0.090° lat at 15°N) ────────
# More precisely: 1° lat ≈ 111 km; 1° lon at lat 15° ≈ 107 km
# 10 km / 111 km = 0.090° lat  ≈  10/107 = 0.094° lon
# Use a circle approximation in lon units (cos correction)
D_MIN_KM   = 10.0
DEG_PER_KM = 1 / 111.0
lat_center = sum(lats) / len(lats)  # ≈ 14.9°N
lon_scale  = math.cos(math.radians(lat_center))
r_lat_deg  = D_MIN_KM * DEG_PER_KM

# ── Plot ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(COL1, COL1 * 1.15))

# All admissible sites
ax.scatter(lons, lats, s=4, color=WONG["gray"], alpha=0.5,
           linewidths=0, zorder=2, label=f"Admissible sites ($n=389$)")

# BCS portfolio
ax.scatter(bcs_lons, bcs_lats, s=40, color=WONG["blue"],
           marker="D", zorder=5, linewidths=0.6,
           edgecolors="white", label=r"Best-compromise $\{184,430,460\}$")

# d_min circles around each BCS site
for lat_c, lon_c in zip(bcs_lats, bcs_lons):
    # Draw an approximate circle using an ellipse (aspect ratio correction)
    from matplotlib.patches import Ellipse
    ellipse = Ellipse(
        (lon_c, lat_c),
        width  = 2 * r_lat_deg / lon_scale,   # in degrees lon
        height = 2 * r_lat_deg,                # in degrees lat
        fill=False, edgecolor=WONG["blue"],
        linestyle="--", linewidth=0.8, alpha=0.6, zorder=4
    )
    ax.add_patch(ellipse)

# Label BCS sites
for s, lon_c, lat_c in zip(bcs_sites, bcs_lons, bcs_lats):
    # Offset label to avoid overlap: 184 goes right, 430/460 go right
    ax.text(lon_c + 0.008, lat_c + 0.008, str(s["idx"]),
            fontsize=7, color=WONG["blue"], va="bottom", fontweight="bold")

ax.set_xlabel("Longitude (°)")
ax.set_ylabel("Latitude (°)")

# Equal aspect in geographic sense
ax.set_aspect(1 / lon_scale)

# Tight bounds with small padding
lon_pad = 0.05; lat_pad = 0.03
ax.set_ylim(min(lats) - lat_pad, max(lats) + lat_pad)

ax.legend(loc="upper left", fontsize=7, markerscale=1.4)

# Note placed inside map, bottom right, away from legend
ax.text(0.98, 0.04,
        fr"Dashed circles: $d_{{min}}={D_MIN_KM}$ km",
        transform=ax.transAxes, fontsize=6.5, color="#555555",
        ha="right", va="bottom")

# Extend xlim slightly to contain circles
lon_pad_right = 0.12   # circles of site 460 extend east
ax.set_xlim(min(lons) - lon_pad, max(lons) + lon_pad_right)

fig.tight_layout(pad=0.4)
savefig(fig, "fig_F4_map")
