# %% Imports
from datetime import datetime
from pathlib import Path

from dateutil.relativedelta import relativedelta
from geo_utils.validate import ensure_valid_featurecollection, get_all_geojson_geometries

from pixels_utils.constants.sentinel2 import ELEMENT84_SEARCH_URL_V0
from pixels_utils.scenes import bbox_from_geometry, get_stac_scenes, parse_nested_stac_data, request_asset_info
from pixels_utils.tests.data.load_data import sample_geojson

# %% Settings
DATA_ID = 1
OUTPUT_DIR = Path("/mnt/c/Users/Tyler/Downloads")

geojson = sample_geojson(DATA_ID)
geojson_fc = ensure_valid_featurecollection(geojson, create_new=True)
date_start = "2022-02-01"  # planting date
date_end = "2022-08-01"
date_end = (datetime.strptime(date_start, "%Y-%m-%d") + relativedelta(months=6)).date()

# %% Run
df_scenes = get_stac_scenes(
    bounding_box=bbox_from_geometry(next(get_all_geojson_geometries(geojson_fc))),
    date_start=date_start,
    date_end=date_end,
    max_scene_cloud_cover_percent=80,
    stac_catalog_url=ELEMENT84_SEARCH_URL_V0,
)

df_properties = parse_nested_stac_data(df=df_scenes, column="properties")
df_asset_info = request_asset_info(df=df_scenes)
