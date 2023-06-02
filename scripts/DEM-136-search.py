# %% Imports
from datetime import datetime
from pathlib import Path

from dateutil.relativedelta import relativedelta
from shapely.geometry import Point, Polygon

from pixels_utils.constants.stac_v1 import ELEMENT84_SEARCH_URL, EarthSearchCollections
from pixels_utils.scenes._scenes import get_stac_scenes, parse_nested_stac_data, request_asset_info
from pixels_utils.tests.data.load_data import sample_geojson

# %% Geojson vs Dict vs Shapely

geometry = Polygon((Point(6, 59), Point(-5, -2), Point(88, -46), Point(6, 59)))

# %% Settings
DATA_ID = 1
OUTPUT_DIR = Path("/mnt/c/Users/Tyler/Downloads")

geojson = sample_geojson(DATA_ID)
# geojson_fc = ensure_valid_featurecollection(geojson, create_new=True)
date_start = "2022-02-01"  # planting date
date_end = "2022-04-01"
date_end = (datetime.strptime(date_start, "%Y-%m-%d") + relativedelta(months=6)).date()

# %% Run

df_scenes = get_stac_scenes(
    # geometry=Polygon((Point(6, 59), Point(-5, -2), Point(88, -46), Point(6, 59))),
    geometry=geojson,
    date_start=date_start,
    date_end=date_end,
    max_scene_cloud_cover_percent=80,
    stac_catalog_url=ELEMENT84_SEARCH_URL,
    collection=EarthSearchCollections.sentinel_2_l2a,
    max_items=None,
)

df_properties = parse_nested_stac_data(df=df_scenes, column="properties")
df_asset_info = request_asset_info(df=df_scenes)
