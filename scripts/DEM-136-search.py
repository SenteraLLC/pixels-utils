# %% Imports
from datetime import datetime
from pathlib import Path

from dateutil.relativedelta import relativedelta
from shapely.geometry import Point, Polygon

from pixels_utils.scenes import parse_nested_stac_data, request_asset_info, search_stac_scenes
from pixels_utils.tests.data.load_data import sample_geojson

# %% Geojson vs Dict vs Shapely

geometry = Polygon((Point(6, 59), Point(-5, -2), Point(88, -46), Point(6, 59)))

# %% Settings
DATA_ID = 1
OUTPUT_DIR = Path("/mnt/c/Users/Tyler/Downloads")
STAC_VERSION = "v0"  # "v0" or "v1"

geojson = sample_geojson(DATA_ID)
# geojson_fc = ensure_valid_featurecollection(geojson, create_new=True)
date_start = "2022-02-01"  # planting date
date_end = "2022-04-01"
date_end = (datetime.strptime(date_start, "%Y-%m-%d") + relativedelta(months=6)).date()

if STAC_VERSION == "v0":
    from pixels_utils.stac_catalogs.earthsearch.v0 import EARTHSEARCH_URL, EarthSearchCollections

    stac_catalog_url = EARTHSEARCH_URL
    collection = EarthSearchCollections.sentinel_s2_l2a_cogs
elif STAC_VERSION == "v1":
    from pixels_utils.stac_catalogs.earthsearch.v1 import EARTHSEARCH_URL, EarthSearchCollections

    stac_catalog_url = EARTHSEARCH_URL
    collection = EarthSearchCollections.sentinel_2_l2a
# %% Run

df_scenes_v0 = search_stac_scenes(
    # geometry=Polygon((Point(6, 59), Point(-5, -2), Point(88, -46), Point(6, 59))),
    geometry=geojson,
    date_start=date_start,
    date_end=date_end,
    intersects=None,
    stac_catalog_url=stac_catalog_url,
    collection=collection,
    query={"eo:cloud_cover": {"lt": 1}},
)

df_properties = parse_nested_stac_data(df=df_scenes_v0, column="properties")
df_assets = parse_nested_stac_data(df=df_scenes_v0, column="assets")
df_asset_info = request_asset_info(df=df_scenes_v0)
