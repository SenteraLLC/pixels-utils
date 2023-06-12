import pickle
from datetime import datetime
from json import load
from os import chdir
from os.path import abspath
from os.path import join
from os.path import join as os_join
from pathlib import Path
from typing import Dict, Optional

import pytest

from pixels_utils.constants.sentinel2 import (  # ELEMENT84_L2A_SCENE_URL,; SENTINEL_2_L2A_COLLECTION,
    ASSETS_MSI,
    EXPRESSION_NDVI,
)
from pixels_utils.tests.data.load_data import sample_feature, sample_scene_url, sample_sceneid

DATA_DIR = join(abspath(Path(__file__).resolve().parents[0]), "data")
# chdir(DATA_DIR)


def load_file(file_name: str, directory: Optional[str] = DATA_DIR):
    """Read json from the data directory."""
    with open(join(directory, file_name)) as f:
        return load(f)


def load_pickle(file_name: str, directory: Optional[str] = DATA_DIR):
    """Read json from the data directory."""
    with open(join(directory, file_name), "rb") as f:
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
    def f(
        fname_pickle=f"CLOUD-80_GEOM-1_MONTH-6.pickle",
    ):
        dir_name = join(DATA_DIR, "scenes")
        return load_pickle(
            fname_pickle,
            join(
                dir_name,
                "earthsearch-v1",
                "sentinel-2-l2a",
            ),
        )

    return f


@pytest.fixture(autouse=True, scope="function")
def mock_scene_asset_info_earthsearch_v1():
    def f(
        fname_pickle=f"CLOUD-80_GEOM-1_MONTH-6_asset-info.pickle",
    ):
        dir_name = join(DATA_DIR, "scenes")
        return load_pickle(
            fname_pickle,
            join(
                dir_name,
                "earthsearch-v1",
                "sentinel-2-l2a",
            ),
        )

    return f


@pytest.fixture(autouse=True, scope="function")
def mock_endpoints_stac_statistics():
    def f(
        assets=None,
        expression=None,
        gsd=None,
        fname_pickle=f"geo_aoi1_scl_mask_None.pickle",
    ):
        dir_name = join(DATA_DIR, "statistics")
        assets_name = "MSI" if assets == ASSETS_MSI else "None"
        expression_name = "NDVI" if expression == EXPRESSION_NDVI else "None"
        folder = f"ASSETS_{assets_name}_EXPRESSION_{expression_name}_GSD_{gsd}"
        return load_pickle(
            fname_pickle,
            join(dir_name, folder),
        )

    return f
