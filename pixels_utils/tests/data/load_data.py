from json import load
from os import chdir
from os.path import abspath
from pathlib import Path

from geo_utils.validate import ensure_valid_featurecollection, ensure_valid_geometry

from pixels_utils.stac_catalogs.earthsearch.v0 import EARTHSEARCH_SCENE_URL, EARTHSEARCH_URL, EarthSearchCollections

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
    return EARTHSEARCH_SCENE_URL.format(collection=EARTHSEARCH_URL, sceneid=sample_sceneid(data_id=1))


def sample_featurecollection(data_id=1):
    name = f"aoi_{data_id}"
    with open(f"{name}.geojson") as f:
        geojson = ensure_valid_featurecollection(load(f), create_new=True)
    return geojson


def sample_geojson(data_id=1):
    name = f"aoi_{data_id}"
    with open(f"{name}.geojson") as f:
        geojson = load(f)
    return geojson


def sample_geometry(data_id=1):
    name = f"aoi_{data_id}"
    with open(f"{name}.geojson") as f:
        geometry = ensure_valid_geometry(load(f))
    return geometry
