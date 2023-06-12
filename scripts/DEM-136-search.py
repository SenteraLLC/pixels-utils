# %% Imports
from datetime import datetime  # noqa
from json import load  # noqa
from pathlib import Path

from dateutil.relativedelta import relativedelta  # noqa
from geo_utils.vector import geojson_to_shapely, shapely_to_geojson_geometry  # noqa
from shapely.geometry import Point, Polygon

from pixels_utils.scenes import parse_nested_stac_data, request_asset_info, search_stac_scenes
from pixels_utils.tests.data.load_data import (  # noqa
    sample_feature,
    sample_feature_collection,
    sample_geojson_multipolygon,
)

# # %% Testing out geometry input types
# feature = sample_feature()
# _bounds_from_geojson_or_geometry(feature)

# feature_collection = sample_feature_collection()
# _bounds_from_geojson_or_geometry(feature_collection)  # Raises TypeError

# feature2 = feature_collection["features"][0]
# _bounds_from_geojson_or_geometry(feature2)

# # dict-type geojson
# feature_dict = load(open("/home/tyler/git/pixels-utils/pixels_utils/tests/data/aoi_1.geojson"))
# _bounds_from_geojson_or_geometry(feature_dict)

# geojson_multipolygon = sample_geojson_multipolygon()
# _bounds_from_geojson_or_geometry(geojson_multipolygon)

# shapely = geojson_to_shapely(geojson_multipolygon)
# _bounds_from_geojson_or_geometry(shapely)
# geojson_mp = shapely_to_geojson_geometry(shapely)


# %% Geojson vs Dict vs Shapely

geometry = Polygon((Point(6, 59), Point(-5, -2), Point(88, -46), Point(6, 59)))

# %% Settings
DATA_ID = 1
OUTPUT_DIR = Path("/mnt/c/Users/Tyler/Downloads")
EARTHSEARCH_VER = "v1"  # "v0" or "v1"

geojson = sample_feature(DATA_ID)
date_start = "2022-06-01"  # planting date
date_end = "2022-06-30"
# date_end = (datetime.strptime(date_start, "%Y-%m-%d") + relativedelta(months=6)).date()

if EARTHSEARCH_VER == "v0":
    from pixels_utils.stac_catalogs.earthsearch.v0 import EARTHSEARCH_URL, EarthSearchCollections

    stac_catalog_url = EARTHSEARCH_URL
    collection = EarthSearchCollections.sentinel_s2_l2a_cogs
elif EARTHSEARCH_VER == "v1":
    from pixels_utils.stac_catalogs.earthsearch.v1 import EARTHSEARCH_URL, EarthSearchCollections

    stac_catalog_url = EARTHSEARCH_URL
    collection = EarthSearchCollections.sentinel_2_l2a
# %% Run

df_scenes = search_stac_scenes(
    geometry=geojson,  # Can be feature, feature_dict, geojson_multipolygon, shapely, etc. from above
    date_start=date_start,
    date_end=date_end,
    intersects=None,
    stac_catalog_url=stac_catalog_url,
    collection=collection,
    query={"eo:cloud_cover": {"lt": 80}},
    simplify_to_bbox=True,
)

df_properties = parse_nested_stac_data(df=df_scenes, column="properties")
df_assets = parse_nested_stac_data(df=df_scenes, column="assets")
df_asset_info = request_asset_info(df=df_scenes)
