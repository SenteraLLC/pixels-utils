from json import load
from os import chdir
from os.path import abspath
from pathlib import Path

chdir(abspath(Path(__file__).resolve().parents[0]))

sceneid = "S2B_10TGS_20220419_0_L2A"


def sample_aoi(name="aoi"):
    with open(f"./fixtures/{name}.geojson") as f:
        geojson = load(f)
    return geojson
