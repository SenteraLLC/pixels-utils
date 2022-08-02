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
from pixels_utils.tests.data.load_data import (
    sample_geojson,
    sample_scene_url,
    sample_sceneid,
)

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
def GEOJSON_FIXTURE():
    return sample_geojson


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

    # if assets is None and expression == EXPRESSION_NDVI and gsd == None:
    #     return load_pickle(
    #         fname_pickle,
    #         join(dir_name, "ASSETS_None_EXPRESSION_NDVI_GSD_None"),
    #     )
    # elif assets == ASSETS_MSI and expression is None and gsd == None:
    #     return load_pickle(
    #         fname_pickle,
    #         join(dir_name, "ASSETS_MSI_EXPRESSION_None"),
    #     )
    # else:
    #     return None
