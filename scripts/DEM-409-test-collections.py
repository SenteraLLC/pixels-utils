# %% Setup
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


DATA_ID = 1
EARTHSEARCH_VER = "v1"  # "v0" or "v1"

geojson = sample_feature(DATA_ID)
date_start = "2022-01-01"  # planting date
date_end = "2022-06-30"

logging.info("Earthsearch version: %s", EARTHSEARCH_VER)
logging.info("Date range: %s - %s", date_start, date_end)


if EARTHSEARCH_VER == "v0":
    from pixels_utils.stac_catalogs.earthsearch.v0 import (
        EARTHSEARCH_COLLECTION_URL,
        EARTHSEARCH_SCENE_URL,
        EARTHSEARCH_URL,
        EarthSearchCollections,
    )

    # collection = EarthSearchCollections.sentinel_s2_l2a_cogs

elif EARTHSEARCH_VER == "v1":
    from pixels_utils.stac_catalogs.earthsearch.v1 import (
        EARTHSEARCH_COLLECTION_URL,
        EARTHSEARCH_SCENE_URL,
        EARTHSEARCH_URL,
        EarthSearchCollections,
    )

    # collection = EarthSearchCollections.sentinel_2_l2a
    # collection = EarthSearchCollections.landsat_c2_l2
    # collection = EarthSearchCollections.sentinel_2_l1c

# %%
collections = [EarthSearchCollections[m] for m in EarthSearchCollections.__members__]
# collection = EarthSearchCollections.sentinel_s2_l1c
for collection in collections:
    logging.info("======================================================")
    logging.info("Evaluating: %s", collection.name)
    stac_collection_url = EARTHSEARCH_COLLECTION_URL.format(collection=collection.name)
    logging.info("Collection URL: %s", stac_collection_url)
    stac_catalog_url = EARTHSEARCH_URL
    stac_collection_url = EARTHSEARCH_COLLECTION_URL.format(collection=collection.name)
    try:
        stac_metadata = STACMetaData(collection_url=stac_collection_url)
        if any((stac_metadata.asset_names, stac_metadata.asset_titles, stac_metadata.df_assets)) is None:
            logging.info("Loading STACMetadata: FAILED (One or more STACMetaData property is None)")
        else:
            logging.info("Loading STACMetadata: SUCCESS (%s assets available)", len(stac_metadata.df_assets))
    except Exception as e:
        logging.info("Loading STACMetadata: FAILED (%s)", e)  # noqa

    try:
        df_scenes = search_stac_scenes(
            geometry=geojson,
            date_start=date_start,
            date_end=date_end,
            stac_catalog_url=stac_catalog_url,
            collection=collection,
            # query={"eo:cloud_cover": {"lt": 80}},
            simplify_to_bbox=True,
        )
        logging.info("search_stac_scenes: SUCCESS (%s scenes available)", len(df_scenes))
    except Exception as e:
        logging.info("search_stac_scenes: FAILED (%s)", e)  # noqa
        continue

    if len(df_scenes) > 0 and "properties" in df_scenes.columns:
        try:
            df_properties = parse_nested_stac_data(df=df_scenes, column="properties")
            logging.info(
                "Parse STAC properties: SUCCESS (%s nested items across %s assets)",
                len([k for k in df_scenes.iloc[0]["properties"]]),
                len(df_scenes),
            )

        except Exception as e:
            logging.info("Parse STAC properties: FAILED (%s)", e)  # noqa
    else:
        logging.info('Parse STAC properties: N/A (no scenes available with "properties")')

    if len(df_scenes) > 0 and "assets" in df_scenes.columns:
        try:
            df_properties = parse_nested_stac_data(df=df_scenes, column="assets")
            logging.info(
                "Parse STAC assets: SUCCESS (%s nested items across %s assets)",
                len([k for k in df_scenes.iloc[0]["assets"]]),
                len(df_scenes),
            )

        except Exception as e:
            logging.info("Parse STAC assets: FAILED (%s)", e)  # noqa
    else:
        logging.info('Parse STAC assets: N/A (no scenes available with "assets")')

    if len(df_scenes) == 0:
        logging.info("Titiler STAC info endpoint: N/A")
        continue

    try:
        i = 0  # Choose from 0 to n (len of df_scenes)
        url = EARTHSEARCH_SCENE_URL.format(collection=df_scenes.iloc[i]["collection"], id=df_scenes.iloc[i]["id"])
        scene_info = Info(
            url=url,
            assets=None,
            titiler_endpoint=TITILER_ENDPOINT,
        )
        if scene_info.response.status_code == 200:
            logging.info("Titiler STAC info endpoint: SUCCCESS")
        else:
            logging.info(
                "Titiler STAC info endpoint: FAILED (%s: %s)",
                scene_info.response.status_code,
                scene_info.response.reason,
            )
    except Exception as e:
        logging.info("Titiler STAC info endpoint: FAILED (%s)", e)  # noqa
        continue

# %%
