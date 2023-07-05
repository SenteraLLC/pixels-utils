# %% Imports
import logging

from spyndex import indices as spyndex_indices
from utils.logging.tqdm import logging_init

from pixels_utils.scenes import parse_nested_stac_data, request_asset_info, search_stac_scenes
from pixels_utils.stac_catalogs import Expression
from pixels_utils.stac_catalogs.earthsearch.v1 import expression_from_collection, expressions_from_collection
from pixels_utils.tests.data.load_data import sample_feature
from pixels_utils.titiler import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints.stac import QueryParamsStatistics, Statistics, StatisticsPreValidation

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
url = EARTHSEARCH_SCENE_URL.format(collection=df_scenes.iloc[0]["collection"], id=df_scenes.iloc[0]["id"])
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

StatisticsPreValidation(query_params, titiler_endpoint=TITILER_ENDPOINT)
# Raises an AssertionError if any of the assets are not available for the query_params
# If you get a message "StatisticsPreValidation passed: all required assets are available.", you can proceed to Statistics

# %% Now actually request Statistics
stats = Statistics(
    query_params=query_params,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
)
stats.response.url
stats.response.json()


# %% Explore the Expression class to retrive NDVI expression (adapted from spyndex)

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

# Explore some of the different indexes available for the Sentinel-2 L2A collection
collection_indices.__dict__


# %% Get stats for MTVI2 (Modified Triangular Vegetation Index 2)
query_params = QueryParamsStatistics(
    url=url,
    feature=feature,
    asset_as_band=True,
    expression=collection_indices.MTVI2.expression,
    gsd=20,
)

stats = Statistics(
    query_params=query_params,
    titiler_endpoint=TITILER_ENDPOINT,
)
stats.response.json()


# %% Pass both assets and expression to throw ValidationError
query_params = QueryParamsStatistics(
    url=url,
    feature=feature,
    asset_as_band=True,
    assets=["nir"],  # it is not valid to pass both assets and expression
    expression=expression_from_collection(
        collection=EarthSearchCollections.sentinel_2_l2a, spectral_index="NDVI"
    ).expression,
    gsd=20,
)

stats = Statistics(
    query_params=query_params,
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
)
# ValidationError: {'_schema': ['Both "assets" and "expression" were passed, but only one is allowed.']}

# %% Override expression of Expression class (when spyndex doesn't perfectly match the needed expression)
ndre = Expression(
    spyndex_object=spyndex_indices.NDREI,
    expression_override="(nir-rededge1)/(nir+rededge1)",
    assets_override=["nir", "rededge1"],
)

query_params = QueryParamsStatistics(
    url=url,
    feature=feature,
    asset_as_band=True,
    expression=ndre.expression,
    gsd=20,
)

stats = Statistics(
    query_params=query_params,
    titiler_endpoint=TITILER_ENDPOINT,
)
stats.response.json()

# %% Play around with any of the Statistics QueryParams  (Testing TBD)
# https://developmentseed.org/titiler/endpoints/stac/#statistics

query_params = QueryParamsStatistics(
    url=url,  # required
    feature=feature,
    assets=assets,
    expression=collection_ndvi.expression,  # "(nir-red)/(nir+red)"
    asset_as_band=True,  # Be sure to pass this as True (otherwise expression should be of the form "(nir_b1-red_b1)/(nir_b1+red_b1)")
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

stats = Statistics(
    query_params=query_params,
    titiler_endpoint=TITILER_ENDPOINT,
)
stats.response.json()
