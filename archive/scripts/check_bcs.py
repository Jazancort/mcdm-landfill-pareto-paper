import csv, math

lat_col = 'latitude (degrees)'
lon_col = 'longitude (degrees)'

rows = list(csv.DictReader(open('scripts/results/mcdm_rankings.csv')))
idx_map = {r['']: r for r in rows}

targets = ['184', '430', '460']
coords = {}
for t in targets:
    if t in idx_map:
        r = idx_map[t]
        coords[t] = (float(r[lat_col]), float(r[lon_col]))
        print(f"idx={t}  lat={coords[t][0]:.5f}  lon={coords[t][1]:.5f}")
    else:
        print(f"idx={t}  NOT FOUND")

# Haversine distance
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

print()
for i, a in enumerate(targets):
    for b in targets[i+1:]:
        if a in coords and b in coords:
            d = haversine(*coords[a], *coords[b])
            print(f"dist({a},{b}) = {d:.2f} km")

# Also check mcdm_trios.csv for BCS confirmation
print()
rows_t = list(csv.DictReader(open('scripts/results/mcdm_trios.csv')))
print('mcdm_trios cols:', list(rows_t[0].keys()))
for r in rows_t[:5]:
    print(' ', r)
