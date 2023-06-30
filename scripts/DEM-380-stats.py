# %% Imports
import logging
from datetime import datetime
from os.path import join as os_join
from pathlib import Path

from dateutil.relativedelta import relativedelta
from pyproj.crs import CRS
from utils.logging.tqdm import logging_init

from pixels_utils.scenes import parse_nested_stac_data, request_asset_info, search_stac_scenes
from pixels_utils.tests.data.load_data import sample_feature, sample_scene_url
from pixels_utils.titiler import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints.stac import Statistics

logging_init(
    level=logging.INFO,
    format_string="%(name)s - %(levelname)s - %(message)s",
    style="%",
)

# %% Settings
DATA_ID = 1
OUTPUT_DIR = Path("/mnt/c/Users/Tyler/Downloads")
EARTHSEARCH_VER = "v1"  # "v0" or "v1"

feature = sample_feature(DATA_ID)
date_start = "2022-06-01"  # planting date
date_end = "2022-06-30"
# date_end = (datetime.strptime(date_start, "%Y-%m-%d") + relativedelta(months=6)).date()

if EARTHSEARCH_VER == "v0":
    from pixels_utils.stac_catalogs.earthsearch.v0 import EARTHSEARCH_SCENE_URL, EARTHSEARCH_URL, EarthSearchCollections

    stac_catalog_url = EARTHSEARCH_URL
    collection = EarthSearchCollections.sentinel_s2_l2a_cogs
elif EARTHSEARCH_VER == "v1":
    from pixels_utils.stac_catalogs.earthsearch.v1 import EARTHSEARCH_SCENE_URL, EARTHSEARCH_URL, EarthSearchCollections

    stac_catalog_url = EARTHSEARCH_URL
    collection = EarthSearchCollections.sentinel_2_l2a
# %% Run

df_scenes = search_stac_scenes(
    geometry=feature,  # Can be feature, feature_dict, feature_multipolygon, shapely, etc. from above
    date_start=date_start,
    date_end=date_end,
    stac_catalog_url=stac_catalog_url,
    collection=collection,
    query={"eo:cloud_cover": {"lt": 80}},
    simplify_to_bbox=True,
)

df_properties = parse_nested_stac_data(df=df_scenes, column="properties")
df_assets = parse_nested_stac_data(df=df_scenes, column="assets")
df_asset_info = request_asset_info(df=df_scenes)

# %% STAC Statistics
url = EARTHSEARCH_SCENE_URL.format(collection=df_scenes.iloc[0]["collection"], id=df_scenes.iloc[0]["id"])
# scene_url = sample_scene_url(DATA_ID)
assets = None
assets = ["nir"]
expression = None
asset_as_band = True  # ?
asset_bidx = None  # ?
coord_crs = CRS.from_epsg(4326)
max_size = None
height = None
width = None
gsd = 20
nodata = None
unscale = None
resampling = "nearest"
categorical = False
c = None
p = None
histogram_bins = None
histogram_range = None


stats = Statistics(
    url=url,
    feature=feature,
    assets=assets,
    expression=expression,
    asset_as_band=asset_as_band,
    asset_bidx=asset_bidx,
    coord_crs=coord_crs,
    max_size=max_size,
    height=height,
    width=width,
    gsd=gsd,
    nodata=nodata,
    unscale=unscale,
    resampling=resampling,
    categorical=categorical,
    c=c,
    p=p,
    histogram_bins=histogram_bins,
    histogram_range=histogram_range,
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_scl=None,
    whitelist=True,
    validate_individual_assets=True
)


# %% Extra
    url=url,
    # assets=assets,
    assets=None,
    titiler_endpoint=TITILER_ENDPOINT,
    validate_individual_assets=True,
)


date_start = "2022-02-01"  # planting date
date_end = (datetime.strptime(date_start, "%Y-%m-%d") + relativedelta(months=6)).date()


df_stats = statistics(
    date_start,
    date_end,
    feature=feature,
    collection=collection,
    assets=assets,
    expression=expression,
    mask_scl=mask_scl,
    whitelist=whitelist,
    nodata=nodata,
    gsd=gsd,
    resampling=resampling,
    categorical=categorical,
    c=c,
    histogram_bins=histogram_bins,
)
df_stats.to_csv(os_join(OUTPUT_DIR, "pixels-titiler-test2.csv"), index=False)
