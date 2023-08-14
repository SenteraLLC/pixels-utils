import pickle
from json import load
from os.path import abspath
from os.path import join as os_join
from pathlib import Path
from typing import Optional

import pytest

from pixels_utils.tests.data.load_data import sample_feature, sample_scene_url, sample_sceneid

# from pixels_utils.constants.sentinel2 import (  # ELEMENT84_L2A_SCENE_URL,; SENTINEL_2_L2A_COLLECTION,
#     ASSETS_MSI,
#     EXPRESSION_NDVI,
# )

DATA_DIR = os_join(abspath(Path(__file__).resolve().parents[0]), "data")
# chdir(DATA_DIR)


def load_file(file_name: str, directory: Optional[str] = DATA_DIR):
    """Read json from the data directory."""
    with open(os_join(directory, file_name)) as f:
        return load(f)


def load_pickle(file_name: str, directory: Optional[str] = DATA_DIR):
    """Read json from the data directory."""
    with open(os_join(directory, file_name), "rb") as f:
        return pickle.load(f)


@pytest.fixture(autouse=True, scope="class")
def SCENEID_FIXTURE():
    return sample_sceneid


@pytest.fixture(autouse=True, scope="class")
def SCENE_URL_FIXTURE():
    return sample_scene_url


@pytest.fixture(autouse=True, scope="class")
def FEATURE_FIXTURE():
    return sample_feature


@pytest.fixture(autouse=True, scope="function")
def mock_scenes_earthsearch_v1():
    def f(fname_pickle="CLOUD_80-GEOM_1-MONTH_6.pickle"):
        COLLECTION_DIR = Path(os_join(DATA_DIR, "scenes", "earthsearch_v1", "sentinel-2-l2a"))
        return load_pickle(fname_pickle, COLLECTION_DIR)

    return f


@pytest.fixture(autouse=True, scope="function")
def mock_scene_asset_info_earthsearch_v1():
    def f(fname_pickle="CLOUD_80-GEOM_1-MONTH_6-asset_info.pickle"):
        COLLECTION_DIR = Path(os_join(DATA_DIR, "scenes", "earthsearch_v1", "sentinel-2-l2a"))
        return load_pickle(fname_pickle, COLLECTION_DIR)

    return f


@pytest.fixture(autouse=True, scope="function")
def mock_statistics_earthsearch_v1():
    # def mock_statistics_earthsearch_v1(data_id: int, name: str):

    def f(data_id=1, name="stats_all"):
        # def f(fname_pickle=fname_pickle):
        fname_pickle = f"GEOM_{data_id}-SCENE_{sample_sceneid(data_id).upper()}-{name.upper()}.pickle"
        COLLECTION_DIR = Path(os_join(DATA_DIR, "statistics", "earthsearch_v1", "sentinel-2-l2a", "expression_ndvi"))
        return load_pickle(fname_pickle, COLLECTION_DIR)

    return f
