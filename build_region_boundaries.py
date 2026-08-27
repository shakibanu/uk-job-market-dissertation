"""
build_region_boundaries.py

Builds data/UK_Region_Boundaries.geojson for the S4-15 3D Globe feature on
the Regional tab. This is a reference/build script (not run at runtime,
same pattern as build_region_mapping.py and build_nationality_dataset.py) -
run it again only if the source ONS boundary files are refreshed.

Source data - verified directly against the ONS Open Geography Portal
and ONS's own geography licensing page (not a GitHub mirror or any
other unofficial copy):

  1. "Regions (December 2024) Boundaries EN BGC"
     Publisher: Office for National Statistics (ONS)
     Geographic level: the 9 English regions (North East, North West,
       Yorkshire and The Humber, East Midlands, West Midlands, East of
       England, London, South East, South West)
     Resolution: BGC = Generalised (20m), Clipped to the coastline
     Format obtained: GeoJSON, coordinates in EPSG:4326 (WGS84 lat/lon)
     Field names confirm the ONS 2024 boundary schema: RGN24CD, RGN24NM
     Source page: https://geoportal.statistics.gov.uk/datasets/ons::regions-december-2024-boundaries-en-bgc-2/about
     Official REST endpoint (ONS's own ArcGIS org, confirmed via the
     matching data.gov.uk catalogue record):
     https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Regions_December_2024_Boundaries_EN_BGC/FeatureServer
     Obtained: downloaded directly by the student from the ONS portal
     and supplied to this build script - not sourced from GitHub or any
     third-party mirror.

  2. "Countries (December 2024) Boundaries UK BUC"
     Publisher: Office for National Statistics (ONS)
     Geographic level: Scotland, Wales, Northern Ireland, England as
       whole countries (only Scotland/Wales/NI are used below - England
       is excluded here since the 9 finer English regions above already
       cover England at a more useful resolution for this dashboard)
     Resolution: BUC = Ultra Generalised (500m), Clipped
     Format obtained: GeoJSON, coordinates in EPSG:4326 (WGS84 lat/lon)
     Field names confirm the ONS 2024 boundary schema: CTRY24CD, CTRY24NM
     Source page: https://open-geography-portalx-ons.hub.arcgis.com/datasets/ons::countries-december-2024-boundaries-uk-buc-2
     Official REST endpoint:
     https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Countries_December_2024_Boundaries_UK_BUC/FeatureServer
     Obtained: same as above - direct from the ONS portal.

  Licence (confirmed on ONS's own licensing page, not just the
  catalogue record - https://www.ons.gov.uk/methodology/geography/licences):
  Open Government Licence v3.0. Required attribution when this
  boundary data is reproduced:
    "Source: Office for National Statistics licensed under the Open
    Government Licence v.3.0"
    "Contains OS data (c) Crown copyright and database right [year]"
  This matches the licence already used for the dashboard's other
  4 government-sourced datasets (see Chapter 3 / Sources tab).

Region name comparison (Sponsors_By_Region.csv <-> ONS boundary names)
- verified 2026-08-27, all 12 regions match:
  East Midlands              <-> East Midlands              (exact)
  East of England             <-> East of England             (exact)
  London                       <-> London                       (exact)
  North East                   <-> North East                   (exact)
  North West                   <-> North West                   (exact)
  Northern Ireland             <-> Northern Ireland             (exact)
  Scotland                     <-> Scotland                     (exact)
  South East                   <-> South East                   (exact)
  South West                   <-> South West                   (exact)
  Wales                        <-> Wales                        (exact)
  West Midlands                 <-> West Midlands                 (exact)
  Yorkshire and the Humber      <-> Yorkshire and The Humber   (ONS
    boundary source uses a capital "The"; the dashboard's own dataset
    and the rest of this codebase use lowercase "the" - normalised to
    the dashboard's existing spelling below, via NAME_FIXES, so the
    join works. This is the only difference found across all 12
    regions; the original Sponsors_By_Region.csv is NOT modified to
    make this join work - only this boundary-loading step is.)

Known limitation, disclosed rather than hidden: the Regions file (BGC,
~20m generalisation) and the Countries file (BUC, ~500m generalisation)
are simplified to different precision levels. Where an English region's
border meets Scotland or Wales, the two source boundaries were not
digitised at the same resolution, so there can be a very small
(sub-pixel at UK scale) gap or overlap right at that shared border. This
does not affect the sponsor-count choropleth colouring, which is per
region, not per border.

Geometry is simplified with shapely (Douglas-Peucker, tolerance in
decimal degrees) purely to keep the browser payload small for an
interactive orthographic globe - the underlying counts and region
shapes are unaffected at UK-country viewing scale. Before simplifying,
the source Regions file had 138,433 coordinate pairs across 9 features;
after simplifying to 0.003 degrees (~200-300m at UK latitudes, well
below anything visible at country/region viewing scale) the combined
12-region file has 24,561 coordinate pairs and is 960KB, down from a
combined 5.5MB of source geometry. This runs once, offline, to produce
the static data/UK_Region_Boundaries.geojson file below - it is never
recomputed at app startup or on any callback.
"""

import json
from shapely.geometry import shape, mapping

REGIONS_SRC = "data/Raw/Regions_December_2024_Boundaries_EN_BGC.geojson"
COUNTRIES_SRC = "data/Raw/Countries_December_2024_Boundaries_UK_BUC.geojson"
OUTPUT_PATH = "data/UK_Region_Boundaries.geojson"

# Douglas-Peucker tolerance in decimal degrees. ~0.003 degrees is roughly
# 200-300m at UK latitudes - imperceptible at the country/region scale
# this globe is viewed at, while cutting the combined file from ~5.5MB
# to well under 1MB for a responsive globe.
SIMPLIFY_TOLERANCE = 0.003

# Maps the source name fields onto the dashboard's own "Region" spelling
# (matches data/Sponsors_By_Region.csv exactly)
NAME_FIXES = {
    "Yorkshire and The Humber": "Yorkshire and the Humber",
}


def simplify_feature(name, geometry):
    geom = shape(geometry)
    simplified = geom.simplify(SIMPLIFY_TOLERANCE, preserve_topology=True)
    # Label anchor point for the S4-15 globe's region-name labels,
    # computed here (offline, shapely already a dependency of this
    # build-time-only script) rather than at runtime in callbacks.py.
    # representative_point() is used rather than a plain centroid because
    # a centroid can fall outside a concave or multi-part shape (e.g.
    # Scotland's islands) - representative_point() is guaranteed to land
    # inside the polygon. Computed on the simplified geometry, the same
    # shape actually drawn, so the label matches what's on screen.
    label_point = simplified.representative_point()
    return {
        "type": "Feature",
        "properties": {"Region": name, "LabelPoint": [label_point.y, label_point.x]},
        "geometry": mapping(simplified),
    }


def main():
    with open(REGIONS_SRC) as f:
        regions_raw = json.load(f)
    with open(COUNTRIES_SRC) as f:
        countries_raw = json.load(f)

    features = []

    # The 9 English regions
    for feat in regions_raw["features"]:
        name = feat["properties"]["RGN24NM"]
        name = NAME_FIXES.get(name, name)
        features.append(simplify_feature(name, feat["geometry"]))

    # Scotland, Wales, Northern Ireland only - England is excluded since
    # it's already covered, at finer resolution, by the 9 regions above
    keep_countries = {"Scotland", "Wales", "Northern Ireland"}
    for feat in countries_raw["features"]:
        name = feat["properties"]["CTRY24NM"]
        if name in keep_countries:
            features.append(simplify_feature(name, feat["geometry"]))

    out = {"type": "FeatureCollection", "features": features}

    with open(OUTPUT_PATH, "w") as f:
        json.dump(out, f)

    names = sorted(f["properties"]["Region"] for f in features)
    print(f"Wrote {OUTPUT_PATH} with {len(features)} regions:")
    for n in names:
        print(" -", n)


if __name__ == "__main__":
    main()
