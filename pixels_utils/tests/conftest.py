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


def get_fixture(file_name: str, directory: Optional[str] = DATA_DIR):
    """Read json from the fixtures directory."""
    with open(join(directory, file_name)) as f:
        return load(f)


def get_fixture_pickle(file_name: str, directory: Optional[str] = DATA_DIR):
    """Read json from the fixtures directory."""
    with open(join(directory, file_name), "rb") as f:
        return pickle.load(f)


@pytest.fixture
def sceneid_aoi1_fixture():
    return sceneid


@pytest.fixture
def scene_url_aoi1_fixture():
    return ELEMENT84_L2A_SCENE_URL.format(
        collection=SENTINEL_2_L2A_COLLECTION, sceneid=sceneid_aoi1_fixture
    )


@pytest.fixture
def geojson_aoi1_fixture():
    return sample_aoi


def mock_get_stac_statistics_geo_None_scl_mask_None(
    # scene_url=scene_url_aoi1_fixture,
    assets=None,
    expression=None,
):
    fname_pickle = f"geo_None_scl_mask_None.pickle"
    dir_name = join(DATA_DIR, "statistics")
    if assets is None and expression == EXPRESSION_NDVI:
        return get_fixture_pickle(
            fname_pickle,
            join(dir_name, "ASSETS_None_EXPRESSION_NDVI"),
        )
    elif assets == ASSETS_MSI and expression is None:
        return get_fixture_pickle(
            fname_pickle,
            join(dir_name, "ASSETS_MSI_EXPRESSION_None"),
        )

    # elif assets == ASSETS_MSI and expression == EXPRESSION_NDVI:
    #     return get_fixture_pickle(
    #         fname_pickle,
    #         join(dir_name, "ASSETS_MSI_EXPRESSION_NDVI"),
    #     )
    else:
        return None


@pytest.fixture
def mock_get_stac_statistics_geo_None_scl_mask_None_fixture():
    return mock_get_stac_statistics_geo_None_scl_mask_None
