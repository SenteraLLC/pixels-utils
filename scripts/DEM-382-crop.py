# %% Imports
import logging
from os import getenv
from os.path import join
from pathlib import Path

from dotenv import load_dotenv
from numpy import float32
from utils.logging.tqdm import logging_init

from pixels_utils.rasterio_helper import save_image
from pixels_utils.scenes import parse_nested_stac_data, request_asset_info, search_stac_scenes
from pixels_utils.stac_catalogs.earthsearch.v1 import expression_from_collection
from pixels_utils.tests.data.load_data import sample_feature
from pixels_utils.titiler import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints.stac import Crop, CropPreValidation, QueryParamsCrop
from pixels_utils.titiler.endpoints.stac._crop_response_utils import parse_crop_response
from pixels_utils.titiler.mask.enum_classes import Sentinel2_SCL, Sentinel2_SCL_Group  # noqa

logging_init(
    level=logging.INFO,
    format_string="%(name)s - %(levelname)s - %(message)s",
    style="%",
)
c = load_dotenv()

# %% Settings
DATA_ID = 1
EARTHSEARCH_VER = "v1"  # "v0" or "v1"

temp_dir = getenv("TEMP_DIR")

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
scene_id = df_scenes.iloc[scene_idx]["id"]
url = EARTHSEARCH_SCENE_URL.format(collection=df_scenes.iloc[scene_idx]["collection"], id=scene_id)

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


# %% 1. Single asset, no geojson, default GSD
query_params_1 = QueryParamsCrop(
    url=url,
    feature=None,
    height=None,
    width=None,
    gsd=None,
    format_=".tif",
    assets=["nir"],  # ["nir"]
    expression=None,  # collection_ndvi.expression = "(nir-red)/(nir+red)"
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

# %% 1a. Request Crop data - no mask
crop_1a = Crop(
    query_params=query_params_1,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=None,
)

r = crop_1a.response
print(f"Response status code: {r.status_code}")
print(f"Response size: {len(r.content)} bytes")

# %% 2. Single asset as expression (to enable masking), no geojson, default GSD
query_params_2 = QueryParamsCrop(
    url=url, feature=None, gsd=None, format_=".tif", assets=None, expression="nir", asset_as_band=asset_as_band
)

# %% 2a. Request Crop data - no mask
crop_2a = Crop(
    query_params=query_params_2,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=None,
)

r = crop_2a.response
print(f"Response status code: {r.status_code}")
print(f"Response size: {len(r.content)} bytes")
# %% 2b. Request Crop data - for arable pixels only
crop_2b = Crop(
    query_params=query_params_2,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=Sentinel2_SCL_Group.ARABLE,
    mask_asset="scl",
    whitelist=True,
)

r = crop_2b.response
print(f"Response status code: {r.status_code}")
print(f"Response size: {len(r.content)} bytes")
# %% 3. NDVI, Crop by geojson, default GSD
collection_ndvi = expression_from_collection(collection=EarthSearchCollections.sentinel_2_l2a, spectral_index="NDVI")

query_params_3 = QueryParamsCrop(
    url=url,
    feature=feature,
    gsd=None,
    format_=".tif",
    assets=None,
    expression=collection_ndvi.expression,
    asset_as_band=asset_as_band,
)

crop_preval = CropPreValidation(query_params_3, titiler_endpoint=TITILER_ENDPOINT)

# %% 3a. Request Crop data - no mask
crop_3a = Crop(
    query_params=query_params_3,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=None,
)

r = crop_3a.response
print(f"Response status code: {r.status_code}")
print(f"Response size: {len(r.content)} bytes")
# %% 3b. Request Crop data - for arable pixels only
crop_3b = Crop(
    query_params=query_params_3,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=Sentinel2_SCL_Group.ARABLE,
    mask_asset="scl",
    whitelist=True,
)

r = crop_3b.response
print(f"Response status code: {r.status_code}")
print(f"Response size: {len(r.content)} bytes")
# %% 4. NDVI, Crop by geojson, 10 m GSD
collection_ndvi = expression_from_collection(collection=EarthSearchCollections.sentinel_2_l2a, spectral_index="NDVI")

query_params_4 = QueryParamsCrop(
    url=url,
    feature=feature,
    gsd=10,
    format_=".tif",
    assets=None,
    expression=collection_ndvi.expression,
    asset_as_band=asset_as_band,
)

crop_preval = CropPreValidation(query_params_4, titiler_endpoint=TITILER_ENDPOINT)

# %% 4a. Request Crop data - no mask
crop_4a = Crop(
    query_params=query_params_4,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=None,
)

r = crop_4a.response
print(f"Response status code: {r.status_code}")
print(f"Response size: {len(r.content)} bytes")
# %% 4b. Request Crop data - for arable pixels only
crop_4b = Crop(
    query_params=query_params_4,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=Sentinel2_SCL_Group.ARABLE,
    mask_asset="scl",
    whitelist=True,
)

r = crop_4b.response
print(f"Response status code: {r.status_code}")
print(f"Response size: {len(r.content)} bytes")

# %% 5. NDVI, Crop by geojson, 100 m GSD, jpg
collection_ndvi = expression_from_collection(collection=EarthSearchCollections.sentinel_2_l2a, spectral_index="NDVI")

query_params_5 = QueryParamsCrop(
    url=url,
    feature=feature,
    gsd=100,
    format_=".jpg",
    assets=None,
    expression=collection_ndvi.expression,
    asset_as_band=asset_as_band,
)

crop_preval = CropPreValidation(query_params_5, titiler_endpoint=TITILER_ENDPOINT)

# %% 5a. Request Crop data - no mask
crop_5a = Crop(
    query_params=query_params_5,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=None,
)

r = crop_5a.response
print(f"Response status code: {r.status_code}")
print(f"Response size: {len(r.content)} bytes")
# %% 5b. Request Crop data - for arable pixels only
crop_5b = Crop(
    query_params=query_params_5,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=Sentinel2_SCL_Group.ARABLE,
    mask_asset="scl",
    whitelist=True,
)

r = crop_5b.response
print(f"Response status code: {r.status_code}")
print(f"Response size: {len(r.content)} bytes")

# %% 6. Now format the raw response data into geotiff: https://developmentseed.org/titiler/output_format/
# NDVI, Crop by geojson, 10 m GSD, tif
collection_ndvi = expression_from_collection(collection=EarthSearchCollections.sentinel_2_l2a, spectral_index="NDVI")

format_ = ".tif"
query_params_6 = QueryParamsCrop(
    url=url,
    feature=feature,
    gsd=10,
    format_=format_,
    assets=None,
    expression=collection_ndvi.expression,
    asset_as_band=asset_as_band,
)

crop_preval = CropPreValidation(query_params_6, titiler_endpoint=TITILER_ENDPOINT)

# %% 6a. Request Crop data and save as geotiff
crop_6a = Crop(
    query_params=query_params_6,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=None,
)

r = crop_6a.response
print(f"Response status code: {r.status_code}")
print(f"Response size: {len(r.content)} bytes")

data_mask, profile_mask, tags = parse_crop_response(
    r=r,
    **{"dtype": float32, "band_names": [collection_ndvi.short_name], "band_description": [collection_ndvi.short_name]},
)

save_image(
    array=data_mask,
    profile=profile_mask,
    fname_out=Path(join(temp_dir, f"ndvi-{scene_id}.tif")),
    driver="Gtiff",
    interleave=None,
    keep_xml=False,
)


# %% Change the fomrat from tif to numpy and make new request
format_ = ".npy"
query_params_6.format_ = format_

crop_preval = CropPreValidation(query_params_6, titiler_endpoint=TITILER_ENDPOINT)

# %% 6b. Request Crop data and save as numpy
crop_6b = Crop(
    query_params=query_params_6,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    clear_cache=True,
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=Sentinel2_SCL_Group.ARABLE,
    mask_asset="scl",
    whitelist=False,
)

r = crop_6b.response
print(f"Response status code: {r.status_code}")
print(f"Response size: {len(r.content)} bytes")

data_mask, profile_mask, tags = parse_crop_response(
    r=r,
    **{"dtype": float32, "band_names": [collection_ndvi.short_name], "band_description": [collection_ndvi.short_name]},
)

save_image(
    array=data_mask,
    profile=profile_mask,
    fname_out=Path(join(temp_dir, f"ndvi-{scene_id}{format_}")),
    driver="Gtiff",
    interleave=None,
    keep_xml=False,
)

# %%
