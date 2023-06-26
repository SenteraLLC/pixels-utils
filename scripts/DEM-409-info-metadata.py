# %% Imports
import logging

from utils.logging.tqdm import logging_init

from pixels_utils.scenes import parse_nested_stac_data, search_stac_scenes
from pixels_utils.stac_metadata import STACMetaData
from pixels_utils.tests.data.load_data import sample_feature
from pixels_utils.titiler import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints.stac import Info

logging_init(
    level=logging.INFO,
    # format_string="{name} - {levelname}: {message}",
    style="%",
)
# %% Settings
DATA_ID = 1
EARTHSEARCH_VER = "v1"  # "v0" or "v1"

geojson = sample_feature(DATA_ID)
date_start = "2022-06-01"  # planting date
date_end = "2022-06-30"

if EARTHSEARCH_VER == "v0":
    from pixels_utils.stac_catalogs.earthsearch.v0 import (
        EARTHSEARCH_COLLECTION_URL,
        EARTHSEARCH_SCENE_URL,
        EARTHSEARCH_URL,
        EarthSearchCollections,
    )

    collection = EarthSearchCollections.sentinel_s2_l2a_cogs

elif EARTHSEARCH_VER == "v1":
    from pixels_utils.stac_catalogs.earthsearch.v1 import (
        EARTHSEARCH_COLLECTION_URL,
        EARTHSEARCH_SCENE_URL,
        EARTHSEARCH_URL,
        EarthSearchCollections,
    )

    collection = EarthSearchCollections.sentinel_2_l2a
    # collection = EarthSearchCollections.landsat_c2_l2
    # collection = EarthSearchCollections.sentinel_2_l1c

stac_catalog_url = EARTHSEARCH_URL
stac_collection_url = EARTHSEARCH_COLLECTION_URL.format(collection=collection.name)
stac_metadata = STACMetaData(collection_url=stac_collection_url)
# %% Get a list of scenes that match the spatiotemporal query

df_scenes = search_stac_scenes(
    geometry=geojson,
    date_start=date_start,
    date_end=date_end,
    stac_catalog_url=stac_catalog_url,
    collection=collection,
    # query={"eo:cloud_cover": {"lt": 80}},
    simplify_to_bbox=True,
)

df_properties = parse_nested_stac_data(df=df_scenes, column="properties")
df_assets = parse_nested_stac_data(df=df_scenes, column="assets")

# %% Choose a scene, and use Info to retrieve the metadata for that particular scene

i = 1  # Choose from 0 to n (len of df_scenes)
url = EARTHSEARCH_SCENE_URL.format(collection=df_scenes.iloc[i]["collection"], id=df_scenes.iloc[i]["id"])

# The following will filter the assets to only those we're interested in getting info for
if EARTHSEARCH_VER == "v0":
    assets = tuple(
        [
            stac_metadata.AssetNames["B01"].name,
            stac_metadata.AssetNames["B02"].name,
            stac_metadata.AssetNames["B03"].name,
            stac_metadata.AssetNames["B04"].name,
            stac_metadata.AssetNames["B05"].name,
            stac_metadata.AssetNames["B06"].name,
            stac_metadata.AssetNames["B07"].name,
            stac_metadata.AssetNames["B08"].name,
            stac_metadata.AssetNames["B8A"].name,
            stac_metadata.AssetNames["B09"].name,
            stac_metadata.AssetNames["SCL"].name,
            stac_metadata.AssetNames["visual"].name,
            "some_invalid_asset",
        ]
    )
elif EARTHSEARCH_VER == "v1":
    if collection.equals("sentinel-2-l2a"):
        assets = tuple(
            [
                stac_metadata.AssetNames["blue"].name,
                stac_metadata.AssetNames["green"].name,
                stac_metadata.AssetNames["red"].name,
                stac_metadata.AssetNames["rededge1"].name,
                stac_metadata.AssetNames["rededge2"].name,
                stac_metadata.AssetNames["rededge3"].name,
                stac_metadata.AssetNames["nir"].name,
                stac_metadata.AssetNames["nir08"].name,
                stac_metadata.AssetNames["nir09"].name,
                stac_metadata.AssetNames["scl"].name,
                stac_metadata.AssetNames["visual"].name,
                "some_invalid_asset",
            ]
        )
    elif collection.equals("landsat-c2-l2"):
        assets = tuple(
            [
                stac_metadata.AssetNames["blue"].name,
                stac_metadata.AssetNames["green"].name,
                stac_metadata.AssetNames["red"].name,
                stac_metadata.AssetNames["nir08"].name,
                stac_metadata.AssetNames["swir16"].name,
                stac_metadata.AssetNames["swir22"].name,
            ]
        )
    elif collection.equals("sentinel-2-l1c"):
        assets = tuple(
            [
                stac_metadata.AssetNames["blue"].name,
                stac_metadata.AssetNames["green"].name,
                stac_metadata.AssetNames["red"].name,
                # stac_metadata.AssetNames["rededge1"].name,
                # stac_metadata.AssetNames["rededge2"].name,
                # stac_metadata.AssetNames["rededge3"].name,
                # stac_metadata.AssetNames["nir"].name,
                # stac_metadata.AssetNames["nir08"].name,
                # stac_metadata.AssetNames["nir09"].name,
                # stac_metadata.AssetNames["swir16"].name,
            ]
        )


scene_info = Info(
    url=url,
    # assets=assets,
    assets=None,
    titiler_endpoint=TITILER_ENDPOINT,
)

# %% Check that invalid assets are removed from list:
scene_info.assets
scene_info.asset_metadata.assets

# %% Get info as a dataframe
df = scene_info.to_dataframe()

# %% Explore the asset_metadata (decendent of the STACMetaData class)
asset_metadata = scene_info.asset_metadata
asset_metadata.asset_names
asset_metadata.asset_titles
asset_metadata.AssetNames
asset_metadata.assets
df_assets = asset_metadata.df_assets
# Note that only the assets passed to Info() are included in the STACMetaDate
raster_bands = asset_metadata.parse_asset_bands(
    column_name="raster:bands", return_dataframe=False
)  # Should raise AssertionError for Earthsearch V0 ("raster:bands" is not a valid attribute in V0)
df_eo_bands = asset_metadata.parse_asset_bands(column_name="eo:bands", return_dataframe=True)

# %% Test the different Earthsearch V1 catalogs
from pixels_utils.stac_catalogs.earthsearch.v1 import (  # noqa
    EARTHSEARCH_COLLECTION_URL,
    EARTHSEARCH_SCENE_URL,
    EARTHSEARCH_URL,
    EarthSearchCollections,
)

DATA_ID = 1
EARTHSEARCH_VER = "v1"  # "v0" or "v1"

geojson = sample_feature(DATA_ID)
date_start = "2022-06-01"  # planting date
date_end = "2022-06-30"

for collection in EarthSearchCollections:
    logging.info("======================================================")
    logging.info("Evaluating: %s", collection.name)
    stac_collection_url = EARTHSEARCH_COLLECTION_URL.format(collection=collection.name)
    logging.info("Collection URL: %s", stac_collection_url)
    stac_metadata = STACMetaData(collection_url=stac_collection_url)
    if any((stac_metadata.asset_names, stac_metadata.asset_titles, stac_metadata.df_assets)) is None:
        logging.info("Loading STACMetaData for %s: FAILED", collection.name)
    else:
        logging.info("Loading STACMetaData for %s: SUCCESS", collection.name)

    df_scenes = search_stac_scenes(
        geometry=geojson,
        date_start=date_start,
        date_end=date_end,
        stac_catalog_url=EARTHSEARCH_URL,
        collection=collection,
        # query={"eo:cloud_cover": {"lt": 80}},
        simplify_to_bbox=True,
    )

    if len(df_scenes) > 0 and "properties" in df_scenes.columns:
        try:
            df_properties = parse_nested_stac_data(df=df_scenes, column="properties")
            logging.info('Parsing %s nested "properties": SUCCESS', len([k for k in df_scenes.iloc[0]["properties"]]))
        except:  # noqa
            logging.info('Parsing %s nested "properties": FAILED', len([k for k in df_scenes.iloc[0]["properties"]]))
    if len(df_scenes) > 0 and "assets" in df_scenes.columns:
        try:
            df_assets = parse_nested_stac_data(df=df_scenes, column="assets")
            logging.info('Parsing %s nested "assets": SUCCESS', len([k for k in df_scenes.iloc[0]["assets"]]))
        except:  # noqa
            logging.info('Parsing %s nested "assets": FAILED', len([k for k in df_scenes.iloc[0]["assets"]]))

    if not len(df_scenes) > 0:
        logging.info("Titiler STAC info endpoint: N/A")
    else:
        i = 0  # Choose from 0 to n (len of df_scenes)
        url = EARTHSEARCH_SCENE_URL.format(collection=df_scenes.iloc[i]["collection"], id=df_scenes.iloc[i]["id"])
        scene_info = Info(
            url=url,
            # assets=stac_metadata.assets,
            titiler_endpoint=TITILER_ENDPOINT,
        )
        if scene_info.response.status_code == 200:
            logging.info("Titiler STAC info endpoint: SUCCCESS")
        else:
            logging.info("Titiler STAC info endpoint: FAILED - %s", scene_info.response.reason)


# %%
