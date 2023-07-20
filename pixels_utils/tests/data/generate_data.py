# %% Imports
from datetime import datetime
from os.path import join as os_join
from pathlib import Path
from pickle import HIGHEST_PROTOCOL
from pickle import dump as pickle_dump

from pixels_utils.scenes import request_asset_info, search_stac_scenes
from pixels_utils.stac_catalogs.earthsearch.v1 import (
    EARTHSEARCH_URL,
    EarthSearchCollections,
    expression_from_collection,
)
from pixels_utils.tests.data.load_data import sample_feature, sample_scene_url, sample_sceneid
from pixels_utils.titiler import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints.stac import QueryParamsStatistics, Statistics
from pixels_utils.titiler.mask.enum_classes import Sentinel2_SCL, Sentinel2_SCL_Group

# %% Settings
DATA_ID = 1
OUTPUT_DIR = Path("/home/tyler/git/pixels-utils/pixels_utils/tests/data/")
EARTHSEARCH_VER = "v1"  # "v0" or "v1"

geojson = sample_feature(DATA_ID)
date_start = "2022-06-01"  # planting date
date_end = "2022-06-30"

if EARTHSEARCH_VER == "v0":
    from pixels_utils.stac_catalogs.earthsearch.v0 import EARTHSEARCH_URL, EarthSearchCollections

    stac_catalog_url = EARTHSEARCH_URL
    collection = EarthSearchCollections.sentinel_s2_l2a_cogs
elif EARTHSEARCH_VER == "v1":
    from pixels_utils.stac_catalogs.earthsearch.v1 import EARTHSEARCH_URL, EarthSearchCollections

    stac_catalog_url = EARTHSEARCH_URL
    collection = EarthSearchCollections.sentinel_2_l2a

# %% Request data
df_scenes = search_stac_scenes(
    geometry=geojson,
    date_start=date_start,
    date_end=date_end,
    stac_catalog_url=stac_catalog_url,
    collection=collection,
    query={"eo:cloud_cover": {"lt": 80}},
    simplify_to_bbox=True,
)
df_asset_info = request_asset_info(df=df_scenes)

# %% Store to file
COLLECTION_NAME = collection.name.upper()
MONTH = datetime.strptime(date_start, "%Y-%m-%d").month
CLOUD_THRESH = 80

COLLECTION_DIR = Path(os_join(OUTPUT_DIR, "scenes", f"earthsearch_{EARTHSEARCH_VER}", f"{COLLECTION_NAME.lower()}"))
COLLECTION_DIR.mkdir(parents=True, exist_ok=True)


with open(
    os_join(
        COLLECTION_DIR,
        f"CLOUD_{CLOUD_THRESH}-GEOM_{DATA_ID}-MONTH_{MONTH}.pickle",
    ),
    "wb",
) as handle:
    pickle_dump(df_scenes, handle, protocol=HIGHEST_PROTOCOL)

with open(
    os_join(
        COLLECTION_DIR,
        f"CLOUD_{CLOUD_THRESH}-GEOM_{DATA_ID}-MONTH_{MONTH}-asset_info.pickle",
    ),
    "wb",
) as handle:
    pickle_dump(df_asset_info, handle, protocol=HIGHEST_PROTOCOL)

# %% Set STAC Statistics defaults
feature = sample_feature(DATA_ID)
collection_ndvi = expression_from_collection(collection=EarthSearchCollections.sentinel_2_l2a, spectral_index="NDVI")

url = sample_scene_url(DATA_ID)
assets = None
expression = collection_ndvi.expression
asset_as_band = True  # If you don't use `asset_as_band=True` option, band indexes must be passed within the expression (e.g., "(nir_b1-red_b1)/(nir_b1+red_b1)")
asset_bidx = None
coord_crs = None
max_size = None
height = None
width = None
gsd = None
nodata = None
unscale = None
resampling = None
categorical = None
c = None
p = None
histogram_bins = None
histogram_range = None

query_params = QueryParamsStatistics(
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
)

# stats_preval = StatisticsPreValidation(query_params, titiler_endpoint=TITILER_ENDPOINT)
# # Raises an AssertionError if any of the assets are not available for the query_params
# # If you get a message "StatisticsPreValidation passed: all required assets are available.", you can proceed to Statistics

# %% Request Statistics and pickle result
stats_all = Statistics(
    query_params=query_params,
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=None,
    mask_asset=None,
    whitelist=None,
)

stats_arable_wlist = Statistics(
    query_params=query_params,
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=Sentinel2_SCL_Group.ARABLE,
    mask_asset="scl",
    whitelist=True,
)

stats_arable_blist = Statistics(
    query_params=query_params,
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=Sentinel2_SCL_Group.CLOUDS,
    mask_asset="scl",
    whitelist=False,
)

stats_cloud_wlist = Statistics(
    query_params=query_params,
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=Sentinel2_SCL_Group.CLOUDS,
    mask_asset="scl",
    whitelist=True,
)

stats_nodata = Statistics(
    query_params=query_params,
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=[Sentinel2_SCL.NO_DATA],
    mask_asset="scl",
    whitelist=True,
)

# %% Store to file
COLLECTION_NAME = collection.name.upper()
EXPRESSION = collection_ndvi.short_name
SCENE_ID = sample_sceneid(DATA_ID)

EXPRESSION_DIR = Path(
    os_join(
        OUTPUT_DIR,
        "statistics",
        f"earthsearch_{EARTHSEARCH_VER}",
        f"{COLLECTION_NAME.lower()}",
        f"expression_{EXPRESSION.lower()}",
    )
)
EXPRESSION_DIR.mkdir(parents=True, exist_ok=True)


for stats, name in zip(
    [stats_all, stats_arable_wlist, stats_arable_blist, stats_cloud_wlist, stats_nodata],
    ["stats_all", "stats_arable_wlist", "stats_arable_blist", "stats_cloud_wlist", "stats_nodata"],
):
    with open(
        os_join(
            EXPRESSION_DIR,
            f"GEOM_{DATA_ID}-SCENE_{SCENE_ID.upper()}-{name.upper()}.pickle",
        ),
        "wb",
    ) as handle:
        pickle_dump(stats.response, handle, protocol=HIGHEST_PROTOCOL)

# %%
