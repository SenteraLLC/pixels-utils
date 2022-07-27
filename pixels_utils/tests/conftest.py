from json import load
from os import chdir
from os.path import abspath, join
from pathlib import Path
from typing import Dict, Optional

import pytest

from pixels_utils.tests.data import sample_aoi, sceneid

DATA_DIR = join(abspath(Path(__file__).resolve().parents[0]), "fixtures")
# chdir(DATA_DIR)


def get_fixture(file_name: str, directory: Optional[str] = DATA_DIR):
    """Read json from the fixtures directory."""
    with open(join(directory, file_name)) as f:
        return load(f)


@pytest.fixture
def sceneid_fixture():
    return sceneid


@pytest.fixture
def geojson_fixture():
    return sample_aoi
