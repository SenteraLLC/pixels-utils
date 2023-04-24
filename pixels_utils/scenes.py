from datetime import date
from typing import Dict, Iterator, Tuple, Union

from geo_utils.validate import ensure_valid_geometry
from pandas import DataFrame
from retry import retry

# from satsearch import Search  # type: ignore
from pystac_client import Client

from pixels_utils.constants.sentinel2 import ELEMENT84_SEARCH_URL, SENTINEL_2_L2A_COLLECTION

BoundingBox = Tuple[float, float, float, float]


def bbox_from_geometry(geometry: Dict) -> BoundingBox:
    geometry = ensure_valid_geometry(geometry, keys=["coordinates", "type"])
    coords = geometry["coordinates"]
    lngs = [lng for lng in _walk_geom_coords(coords, lambda c: c[0])]
    lats = [lat for lat in _walk_geom_coords(coords, lambda c: c[1])]
    return (min(lngs), min(lats), max(lngs), max(lats))


@retry((RuntimeError, KeyError), tries=3, delay=2)
def get_stac_scenes(
    bounding_box: BoundingBox,
    date_start: Union[date, str],
    date_end: Union[date, str],
    max_scene_cloud_cover_percent: int = 80,
) -> DataFrame:
    """
    Retrieves `scene_id`, `datetime`, and cloud cover for all available image tiles
    between `date_start` and `date_end`.

    Args:
        bounding_box (BoundingBox): Geospatial bounding box of search area; must be
        EPSG=4326.
        date_start (Union[date, str]): Earliest UTC date to seach for available images
        (inclusive).
        date_end (Union[date, str]): Latest UTC date to seach for available images
        (inclusive).
        max_scene_cloud_cover_percent (int, optional): Maximum percent cloud cover
        allowed in the scene. Scene cloud cover greater than this value will be dropped
        from the returned DataFrame. Defaults to 80.

    Returns:
        DataFrame: DataFrame with `scene_id`, `datetime`, and `eo:cloud_cover` for each
        scene withing `bounding_box` and betweent the passed date parameters.
    """
    api = Client.open("https://earth-search.aws.element84.com/v0")

    s = api.search(
        max_items=None,
        collections=[SENTINEL_2_L2A_COLLECTION],
        bbox=bounding_box,
        datetime=[date_start, date_end],
        query={"eo:cloud_cover": {"lt": max_scene_cloud_cover_percent}},
    )

    ic = s.item_collection_as_dict()["features"]
    df = DataFrame(ic)
    df["datetime"] = df["properties"].map(lambda dct: dct["datetime"])
    df["eo:cloud_cover"] = df["properties"].map(lambda dct: dct["eo:cloud_cover"])
    df = df[["id", "datetime", "eo:cloud_cover"]].sort_values(by="datetime", ascending=True, ignore_index=True)
    return df


def _walk_geom_coords(coordinates, get_fn) -> Iterator[float]:
    for x in coordinates:
        if isinstance(x, float):
            yield get_fn(coordinates)
        elif isinstance(x, dict):
            yield from _walk_geom_coords(x["geometry"]["coordinates"], get_fn)
        else:
            yield from _walk_geom_coords(x, get_fn)
