# %% Imports
import logging

from utils.logging.tqdm import logging_init

from pixels_utils.scenes import parse_nested_stac_data, request_asset_info, search_stac_scenes
from pixels_utils.stac_catalogs.earthsearch.v1 import expression_from_collection
from pixels_utils.tests.data.load_data import sample_feature
from pixels_utils.titiler import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints.stac import Crop, CropPreValidation, QueryParamsCrop
from pixels_utils.titiler.mask.enum_classes import Sentinel2_SCL, Sentinel2_SCL_Group  # noqa

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

# %% Set STAC Crop defaults
# Choosing a scene with low cloud cover
scene_idx = 2
print(f"Scene {scene_idx} has {df_properties.iloc[scene_idx]['eo:cloud_cover']:.2f}% cloud cover")
url = EARTHSEARCH_SCENE_URL.format(
    collection=df_scenes.iloc[scene_idx]["collection"], id=df_scenes.iloc[scene_idx]["id"]
)

height = None
width = None
gsd = None
format_ = ".tif"
assets = None
expression = None
asset_as_band = True  # If you don't use `asset_as_band=True` option, band indexes must be passed within the expression (e.g., "(nir_b1-red_b1)/(nir_b1+red_b1)")
asset_bidx = None  # ?
coord_crs = None
max_size = None
nodata = None
unscale = None
resampling = None
rescale = None
color_formula = None
colormap = None
colormap_name = None
return_mask = None
algorithm = None
algorithm_params = None

# %% Perform CropPreValidation (maybe run once before running Statistics for a number of geometries or date ranges)
collection_ndvi = expression_from_collection(collection=EarthSearchCollections.sentinel_2_l2a, spectral_index="NDVI")

query_params = QueryParamsCrop(
    url=url,
    feature=feature,
    height=height,
    width=width,
    gsd=gsd,
    format_=format_,
    assets=assets,  # ["nir"]
    expression=collection_ndvi.expression,  # "(nir-red)/(nir+red)"
    asset_as_band=asset_as_band,
    asset_bidx=asset_bidx,
    coord_crs=coord_crs,
    max_size=max_size,
    nodata=nodata,
    unscale=unscale,
    resampling=resampling,  # "nearest"
    rescale=rescale,
    color_formula=color_formula,
    colormap=colormap,
    colormap_name=colormap_name,
    return_mask=return_mask,
    algorithm=algorithm,
    algorithm_params=algorithm_params,
)

crop_preval = CropPreValidation(query_params, titiler_endpoint=TITILER_ENDPOINT)
# Raises an AssertionError if any of the assets are not available for the query_params
# If you get a message "StatisticsPreValidation passed: all required assets are available.", you can proceed to Statistics

# %% Now actually request Statistics - for only arable pixels (whitelist=True)!
crop_arable_wlist = Crop(
    query_params=query_params,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=Sentinel2_SCL_Group.ARABLE,
    mask_asset="scl",
    whitelist=True,
)

json_arable_wlist = crop_arable_wlist.response.json()
