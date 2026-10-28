# Santiago Data Download Instructions

Run these steps BEFORE santiago_extract.py --selftest-fogo or any extraction.

## 1. Santiago island boundary (S-T)
Source: IDECV WFS divisao_admin:ilha, nom_ilha='SANTIAGO'

`python
import requests, json
WFS = "https://geoservicos-ingt.gov.cv/geoserver/divisao_admin/wfs"
params = {
    "service": "WFS", "version": "2.0.0", "request": "GetFeature",
    "typeName": "divisao_admin:ilha",
    "outputFormat": "application/json",
    "CQL_FILTER": "nom_ilha='SANTIAGO'"
}
r = requests.get(WFS, params=params, timeout=60, verify=False)
with open("data/santiago/santiago_boundary.geojson", "w") as f:
    json.dump(r.json(), f)
`

## 2. Southern Region boundary (S-N)
Source: IDECV WFS divisao_admin:concelho, concelhos: Praia, Sao Domingos, Ribeira Grande de Santiago

`python
cql = "concelho IN ('Praia','Sao Domingos','Ribeira Grande de Santiago')"
# adjust if exact names differ
`

## 3. Protected areas
Source: IDECV WFS areas_especiais:area_protegida

`python
WFS = "https://geoservicos-ingt.gov.cv/geoserver/areas_especiais/wfs"
params = {"service":"WFS","version":"2.0.0","request":"GetFeature",
          "typeName":"areas_especiais:area_protegida","outputFormat":"application/json"}
`

## 4. ASTER GDEM v3
Source: https://earthdata.nasa.gov/ (requires free NASA Earthdata account)
Tiles needed: ASTGTMV003_N14W025, ASTGTMV003_N15W025

After download:
`ash
# Keep geographic (EPSG:4326) version:
cp ASTGTMV003_N15W025_dem.tif data/santiago/dem_santiago_geo.tif
# Reproject to UTM 27N:
gdalwarp -r bilinear -tr 30 30 -t_srs EPSG:32627 data/santiago/dem_santiago_geo.tif data/santiago/dem_santiago_utm27.tif
# Compute slope on UTM:
gdaldem slope data/santiago/dem_santiago_utm27.tif data/santiago/slope_santiago.tif
`

## 5. Geofabrik OSM PBF
Source: https://download.geofabrik.de/africa/cabo-verde-latest.osm.pbf
Direct download (~30-50 MB):
`ash
wget https://download.geofabrik.de/africa/cabo-verde-latest.osm.pbf -O data/santiago/cabo-verde-latest.osm.pbf
`
Or via Python:
`python
import requests
url = "https://download.geofabrik.de/africa/cabo-verde-latest.osm.pbf"
with requests.get(url, stream=True) as r:
    with open("data/santiago/cabo-verde-latest.osm.pbf", "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
`
Record the download date and SHA-256 for PRESPEC_SANTIAGO Phase 1 §9.
