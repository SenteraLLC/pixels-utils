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
from pixels_utils.titiler.endpoints.stac import QueryParamsStatistics, Statistics

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

# %% Set STAC Statistics defaults
url = EARTHSEARCH_SCENE_URL.format(collection=df_scenes.iloc[0]["collection"], id=df_scenes.iloc[0]["id"])
# scene_url = sample_scene_url(DATA_ID)
assets = None
expression = None
asset_as_band = None  # ?
asset_bidx = None  # ?
coord_crs = CRS.from_epsg(4326).to_string()  # Cannot be null
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

# %% Basic Statistics request
query_params = QueryParamsStatistics(
    url=url,
    feature=feature,
    assets=assets,  # ["nir"]
    expression="nir/red",  # "nir/red"
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


stats = Statistics(
    query_params=query_params,
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_scl=None,
    whitelist=True,
    validate_individual_assets=False,
)


# serialized_query_params = stats.serialized_query_params

# %% Pass both assets and expression to throw ValidationError
query_params = QueryParamsStatistics(
    url=url,
    feature=feature,
    assets=["nir"],  # it is not valid to pass both assets and expression
    expression="nir/red",
    gsd=20,
)

stats = Statistics(
    query_params=query_params,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_scl=None,
    whitelist=True,
    validate_individual_assets=True,
)

# %% Retrive NDVI expression via Expression classes (adapted from spyndex)

from pixels_utils.stac_catalogs.earthsearch.v1 import expression_from_collection, expressions_from_collection

# sentinel_2_l2a_indices = expressions_from_collection(collection=EarthSearchCollections.sentinel_2_l2a)
collection_indices = expressions_from_collection(collection=collection)
print(collection_indices.NDVI.assets)  # ['nir', 'red']
print(collection_indices.NDVI.expression)  # '(nir-red)/(nir+red)'
print(collection_indices.NDVI.bands)  # ['N', 'R']
print(collection_indices.NDVI.formula)  # (N-R)/(N+R)

collection_ndvi = expression_from_collection(collection=EarthSearchCollections.sentinel_2_l2a, spectral_index="NDVI")
print(collection_ndvi.assets)  # ['nir', 'red']
print(collection_ndvi.expression)  # '(nir-red)/(nir+red)'
print(collection_ndvi.bands)  # ['N', 'R']
print(collection_ndvi.formula)  # (N-R)/(N+R)


query_params = QueryParamsStatistics(
    url=url,
    feature=feature,
    expression=collection_indices.NDVI.expression,
    gsd=20,
)

stats = Statistics(
    query_params=query_params,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_scl=None,
    whitelist=True,
    validate_individual_assets=True,
)

# %% Override expression of Expression class
from spyndex import indices as spyndex_indices

from pixels_utils.stac_catalogs import Expression

ndvi = Expression(
    spyndex_object=spyndex_indices.NDVI,
    formula_override="custom_nir-custom_red/custom_nir+custom_red",
    assets_override=["custom_nir", "custom_red"],
)

# %% Extra
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
