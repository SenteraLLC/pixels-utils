from json import load
from os import chdir
from os.path import abspath
from pathlib import Path

from geo_utils.vector import validate_geojson, validate_geojson_geometry

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


def sample_feature(data_id=1):
    name = f"aoi_{data_id}"
    with open(f"{name}.geojson") as f:
        geojson = validate_geojson(load(f))
    return geojson


def sample_feature_collection(data_id=1):
    name = f"aoi_{data_id}-feature-collection"
    with open(f"{name}.geojson") as f:
        geojson = validate_geojson(load(f))
    return geojson


def sample_geojson_multipolygon(data_id=1):
    name = f"aoi_{data_id}"
    with open(f"{name}.geojson") as f:
        geometry = validate_geojson_geometry(load(f)["geometry"])
    return geometry
