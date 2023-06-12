# %% Imports
from datetime import datetime
from os.path import join as os_join
from pathlib import Path
from pickle import HIGHEST_PROTOCOL
from pickle import dump as pickle_dump

from pixels_utils.scenes import request_asset_info, search_stac_scenes
from pixels_utils.tests.data.load_data import (  # noqa
    sample_feature,
    sample_feature_collection,
    sample_geojson_multipolygon,
)

# %% Settings
DATA_ID = 1
OUTPUT_DIR = Path("/home/tyler/git/pixels-utils/pixels_utils/tests/data/scenes/")
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

with open(
    os_join(
        OUTPUT_DIR,
        f"earthsearch-{EARTHSEARCH_VER}",
        f"{COLLECTION_NAME.lower()}",
        f"CLOUD-{CLOUD_THRESH}_GEOM-{DATA_ID}_MONTH-{MONTH}.pickle",
    ),
    "wb",
) as handle:
    pickle_dump(df_scenes, handle, protocol=HIGHEST_PROTOCOL)

with open(
    os_join(
        OUTPUT_DIR,
        f"earthsearch-{EARTHSEARCH_VER}",
        f"{COLLECTION_NAME.lower()}",
        f"CLOUD-{CLOUD_THRESH}_GEOM-{DATA_ID}_MONTH-{MONTH}_asset-info.pickle",
    ),
    "wb",
) as handle:
    pickle_dump(df_asset_info, handle, protocol=HIGHEST_PROTOCOL)

# %%
