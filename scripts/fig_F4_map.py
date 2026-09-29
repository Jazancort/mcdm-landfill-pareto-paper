"""F4 — Fogo Island map, Intervention Window style."""
import sys, os, csv, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig_utils import set_rcparams, savefig, COL1, C_TREATMENT, C_GRAY
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

set_rcparams()

here = os.path.dirname(os.path.abspath(__file__))

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

fig, ax = plt.subplots(figsize=(COL1 * 1.20, COL1 * 1.30))

# All admissible sites
ax.scatter(lons, lats, s=6, color=C_GRAY, alpha=0.50,
           linewidths=0, zorder=2,
           label=f"Admissible sites ($n=389$)")

# BCS portfolio
ax.scatter(bcs_lon, bcs_lat, s=80, color=C_TREATMENT,
           marker="D", zorder=5, linewidths=0.8,
           edgecolors="white",
           label=r"Best-compromise $\{184,\,430,\,460\}$")

# d_min ellipses
for lat_c, lon_c in zip(bcs_lat, bcs_lon):
    el = Ellipse((lon_c, lat_c),
                 width=2 * r_lat_deg / lon_scale,
                 height=2 * r_lat_deg,
                 fill=False, edgecolor=C_TREATMENT,
                 linestyle="--", linewidth=1.2, alpha=0.55, zorder=4)
    ax.add_patch(el)

# Labels for BCS sites
offsets = {"184": (0.008, -0.012), "430": (0.010, 0.008), "460": (0.010, 0.008)}
for s in bcs:
    dx, dy = offsets.get(str(s["idx"]), (0.008, 0.008))
    ax.text(s["lon"] + dx, s["lat"] + dy,
            str(s["idx"]), fontsize=11, color=C_TREATMENT,
            fontweight="bold", va="bottom")

ax.set_aspect(1 / lon_scale)
lon_pad = 0.05; lat_pad = 0.03
ax.set_xlim(min(lons) - lon_pad, max(lons) + 0.14)
ax.set_ylim(min(lats) - lat_pad, max(lats) + lat_pad)
ax.set_xlabel("Longitude (\u00b0)", fontweight="bold")
ax.set_ylabel("Latitude (\u00b0)", fontweight="bold")

ax.text(0.98, 0.03,
        fr"Dashed circles: $d_{{\min}}={D_MIN_KM}$ km",
        transform=ax.transAxes, fontsize=10, color="#555555",
        ha="right", va="bottom")

ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12),
          ncol=1, frameon=False)

plt.tight_layout(pad=0.5)
plt.subplots_adjust(bottom=0.20)
savefig(fig, "fig_F4_map")
