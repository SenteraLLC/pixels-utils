from datetime import date
from typing import Dict, Iterator, Tuple, Union

from geo_utils.general import ensure_valid_geojson
from pandas import DataFrame
from satsearch import Search  # type: ignore

# from .ui import y_choices, required_fields
from pixels_utils.constants.sentinel2 import (
    ELEMENT84_SEARCH_URL,
    SENTINEL_2_L2A_COLLECTION,
)

BoundingBox = Tuple[float, float, float, float]


def bbox_from_geojson(geojson: Dict) -> BoundingBox:
    # TODO: Check geojson keys: "geometry", "coordinates", etc.
    geojson = ensure_valid_geojson(geojson, keys=["coordinates", "type"])
    coords = geojson["coordinates"]
    lngs = [lng for lng in _walk_geom_coords(coords, lambda c: c[0])]
    lats = [lat for lat in _walk_geom_coords(coords, lambda c: c[1])]
    return (min(lngs), min(lats), max(lngs), max(lats))


def get_stac_scenes(
    bounding_box: BoundingBox,
    date_start: Union[date, str],
    date_end: Union[date, str],
    max_scene_cloud_cover_percent: int = 80,
):
    dates = str(date_start) + "/" + str(date_end)
    s = Search(
        url=ELEMENT84_SEARCH_URL,
        collections=[SENTINEL_2_L2A_COLLECTION],
        datetime=dates,
        bbox=bounding_box,
        query={"eo:cloud_cover": {"lt": max_scene_cloud_cover_percent}},
    )
    results_str = s.items().summary(
        params=[
            "id",
            "datetime",
            # "sentinel:product_id",
            "eo:cloud_cover",
        ]
    )
    summary = [line.split() for line in results_str.splitlines()]
    cols = summary[1]
    data = summary[2:]
    return DataFrame(data=data, columns=cols)
    # return list(result), list(result.properties("datetime")), list(result.properties("eo:cloud_cover"))


def _walk_geom_coords(coordinates, get_fn) -> Iterator[float]:
    for x in coordinates:
        if isinstance(x, float):
            yield get_fn(coordinates)
        elif isinstance(x, dict):
            yield from _walk_geom_coords(x["geometry"]["coordinates"], get_fn)
        else:
            yield from _walk_geom_coords(x, get_fn)
