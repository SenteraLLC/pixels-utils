# %% Imports
import logging

from utils.logging.tqdm import logging_init

from pixels_utils.scenes import parse_nested_stac_data, request_asset_info, search_stac_scenes
from pixels_utils.stac_catalogs.earthsearch.v1 import expression_from_collection
from pixels_utils.tests.data.load_data import sample_feature
from pixels_utils.titiler import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints.stac import QueryParamsStatistics, Statistics, StatisticsPreValidation
from pixels_utils.titiler.mask.enum_classes import Sentinel2_SCL, Sentinel2_SCL_Group

logging_init(
    level=logging.INFO,
    format_string="%(name)s - %(levelname)s - %(message)s",
    style="%",
)

# %% Settings
DATA_ID = 1
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

# %% Set STAC Statistics defaults
# Choosing a scene with low cloud cover
scene_idx = 4
print(f"Scene {scene_idx} has {df_properties.iloc[scene_idx]['eo:cloud_cover']:.2f}% cloud cover")
url = EARTHSEARCH_SCENE_URL.format(
    collection=df_scenes.iloc[scene_idx]["collection"], id=df_scenes.iloc[scene_idx]["id"]
)
# scene_url = sample_scene_url(DATA_ID)
assets = None
expression = None
asset_as_band = True  # If you don't use `asset_as_band=True` option, band indexes must be passed within the expression (e.g., "(nir_b1-red_b1)/(nir_b1+red_b1)")
asset_bidx = None  # ?
coord_crs = None  # CRS.from_epsg(4326).to_string()
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

# %% Perform StatisticsPreValidation (maybe run once before running Statistics for a number of geometries or date ranges)
collection_ndvi = expression_from_collection(collection=EarthSearchCollections.sentinel_2_l2a, spectral_index="NDVI")

query_params = QueryParamsStatistics(
    url=url,
    feature=feature,
    assets=assets,  # ["nir"]
    expression=collection_ndvi.expression,  # "(nir-red)/(nir+red)"
    asset_as_band=asset_as_band,
    asset_bidx=asset_bidx,
    coord_crs=coord_crs,
    max_size=max_size,
    height=height,
    width=width,
    gsd=gsd,  # 20
    nodata=nodata,
    unscale=unscale,
    resampling=resampling,  # "nearest"
    categorical=categorical,
    c=c,
    p=p,
    histogram_bins=histogram_bins,
    histogram_range=histogram_range,
)

stats_preval = StatisticsPreValidation(query_params, titiler_endpoint=TITILER_ENDPOINT)
# Raises an AssertionError if any of the assets are not available for the query_params
# If you get a message "StatisticsPreValidation passed: all required assets are available.", you can proceed to Statistics

# %% Now actually request Statistics - for only arable pixels (whitelist=True)!
stats_arable = Statistics(
    query_params=query_params,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    clear_cache=False,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=Sentinel2_SCL_Group.ARABLE,
    mask_asset="scl",
    whitelist=True,
)

json_arable = stats_arable.response.json()

# %% And compare to statistics where all CLOUD pixels are masked, keeping only those with a mask over non-cloud pixels
# (by changing the mask_enum and whitelist arg)
stats_nonarable = Statistics(
    query_params=query_params,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    clear_cache=False,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=Sentinel2_SCL_Group.CLOUDS,
    mask_asset="scl",
    whitelist=False,
)

json_nonarable = stats_nonarable.response.json()

# %% And finally, get statistics without a mask
stats_all = Statistics(
    query_params=query_params,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    clear_cache=False,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=None,
    mask_asset=None,
    whitelist=None,
)

json_all = stats_all.response.json()

# %% Print results
for json_ in [json_arable, json_nonarable, json_all]:
    expression = list(json_["properties"]["statistics"].keys())[0]
    mean = json_["properties"]["statistics"][expression]["mean"]
    count = json_["properties"]["statistics"][expression]["count"]
    print(f"Expression: {expression}")
    print(f"Pixel count: {count}")
    print(f"Mean NDVI: {mean:.2f}\n")

# %% Get the count for each class in the Sentinel2_SCL enum

query_params = QueryParamsStatistics(url=url, feature=feature, expression="scl", asset_as_band=asset_as_band, nodata=-1)

for scl in Sentinel2_SCL:
    print(scl)
    stats_class = Statistics(
        query_params=query_params,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
        titiler_endpoint=TITILER_ENDPOINT,
        mask_enum=[scl],
        mask_asset="scl",
        whitelist=True,
    )
    json_class = stats_class.response.json()
    expression = list(json_class["properties"]["statistics"].keys())[0]
    min = json_class["properties"]["statistics"][expression]["min"]
    max = json_class["properties"]["statistics"][expression]["max"]
    count = json_class["properties"]["statistics"][expression]["count"]
    print(f"Class: {scl}")
    print(f"Pixel min: {min}")
    print(f"Pixel max: {max}")
    print(f"Pixel count: {count}\n")

# %%
