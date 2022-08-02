from json import load
from os import chdir
from os.path import abspath
from pathlib import Path

from pixels_utils.constants.sentinel2 import (
    ELEMENT84_L2A_SCENE_URL,
    SENTINEL_2_L2A_COLLECTION,
)

chdir(abspath(Path(__file__).resolve().parents[0]))


def sample_sceneid(data_id=1):
    if data_id == 1:
        return "S2B_10TGS_20220419_0_L2A"
    elif data_id == 2:
        pass
        # return "S2B_10TGS_20220419_0_L2A"
    else:
        raise ValueError(f'<id> "{data_id}" not a valid scene_url')


def sample_scene_url(data_id=1):
    return ELEMENT84_L2A_SCENE_URL.format(
        collection=SENTINEL_2_L2A_COLLECTION, sceneid=sample_sceneid(data_id=1)
    )


def sample_geojson(data_id=1):
    name = f"aoi_{data_id}"
    with open(f"{name}.geojson") as f:
        geojson = load(f)
    return geojson
