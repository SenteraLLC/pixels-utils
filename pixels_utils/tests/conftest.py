import pickle
from json import load
from os import chdir
from os.path import abspath, join
from pathlib import Path
from typing import Dict, Optional

import pytest

from pixels_utils.constants.sentinel2 import (
    ASSETS_MSI,
    ELEMENT84_L2A_SCENE_URL,
    EXPRESSION_NDVI,
    SENTINEL_2_L2A_COLLECTION,
)
from pixels_utils.tests.data import sample_aoi, sceneid

DATA_DIR = join(abspath(Path(__file__).resolve().parents[0]), "fixtures")
# chdir(DATA_DIR)


def load_file(file_name: str, directory: Optional[str] = DATA_DIR):
    """Read json from the fixtures directory."""
    with open(join(directory, file_name)) as f:
        return load(f)


def load_pickle(file_name: str, directory: Optional[str] = DATA_DIR):
    """Read json from the fixtures directory."""
    with open(join(directory, file_name), "rb") as f:
        return pickle.load(f)


@pytest.fixture
def sceneid_aoi1_fixture():
    return sceneid


@pytest.fixture(autouse=True, scope="class")
def SCENE_URL_1():
    return ELEMENT84_L2A_SCENE_URL.format(
        collection=SENTINEL_2_L2A_COLLECTION, sceneid=sceneid
    )


@pytest.fixture(autouse=True, scope="class")
def GEOJSON_1():
    return sample_aoi


@pytest.fixture(autouse=True, scope="function")
def mock_endpoints_stac_statistics():
    def f(assets=None, expression=None, fname_pickle=f"geo_aoi1_scl_mask_None.pickle"):
        dir_name = join(DATA_DIR, "statistics")
        if assets is None and expression == EXPRESSION_NDVI:
            return load_pickle(
                fname_pickle,
                join(dir_name, "ASSETS_None_EXPRESSION_NDVI"),
            )
        elif assets == ASSETS_MSI and expression is None:
            return load_pickle(
                fname_pickle,
                join(dir_name, "ASSETS_MSI_EXPRESSION_None"),
            )
        else:
            return None

    return f
