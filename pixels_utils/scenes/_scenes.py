from datetime import date
from typing import Dict, Iterator, Tuple, Union

from geo_utils.validate import ensure_valid_geometry
from pandas import DataFrame, Series
from pystac_client import Client
from requests import get
from retry import retry

from pixels_utils.constants.sentinel2 import ELEMENT84_SEARCH_URL_V0, SENTINEL_2_L2A_COLLECTION

BoundingBox = Tuple[float, float, float, float]


@retry((RuntimeError, KeyError), tries=3, delay=2)
def get_stac_scenes(
    bounding_box: BoundingBox,
    date_start: Union[date, str],
    date_end: Union[date, str],
    max_scene_cloud_cover_percent: int = 80,
    stac_catalog_url: str = ELEMENT84_SEARCH_URL_V0,
) -> DataFrame:
    """
    Retrieves `scene_id`, `datetime`, and cloud cover for all available image tiles between `date_start` and `date_end`.

    Args:
        bounding_box (BoundingBox): Geospatial bounding box of search area; must be EPSG=4326.
        date_start (Union[date, str]): Earliest UTC date to seach for available images (inclusive).
        date_end (Union[date, str]): Latest UTC date to seach for available images (inclusive).
        max_scene_cloud_cover_percent (int, optional): Maximum percent cloud cover allowed in the scene. Scene cloud
        cover greater than this value will be dropped from the returned DataFrame. Defaults to 80.
        stac_catalog_url (str, optional): URL of the STAC catalog to search. Defaults to
        "https://earth-search.aws.element84.com/v0".

    Returns:
        DataFrame: DataFrame with `scene_id`, `datetime`, and `eo:cloud_cover` for each scene withing `bounding_box` and
        betweent the passed date parameters.
    """
    assert stac_catalog_url in (ELEMENT84_SEARCH_URL_V0,), f"Unsupported STAC catalog URL: {stac_catalog_url}"
    date_start = date_start.strftime("%Y-%m-%d") if isinstance(date_start, date) else date_start
    date_end = date_end.strftime("%Y-%m-%d") if isinstance(date_end, date) else date_end

    api = Client.open(url=stac_catalog_url)

    s = api.search(
        max_items=None,
        collections=[SENTINEL_2_L2A_COLLECTION],
        bbox=bounding_box,
        datetime=[date_start, date_end],
        query={"eo:cloud_cover": {"lt": max_scene_cloud_cover_percent}},
    )
    df = DataFrame(s.item_collection_as_dict()["features"])
    # Append `datetime` and `eo:cloud_cover` columns to main DataFrame
    df["datetime"] = df["properties"].apply(lambda properties: properties["datetime"])
    df["eo:cloud_cover"] = df["properties"].apply(lambda properties: properties["eo:cloud_cover"])
    # df = df[["id", "datetime", "eo:cloud_cover"]].sort_values(by="datetime", ascending=True, ignore_index=True)
    df = df.sort_values(by="datetime", ascending=True, ignore_index=True)
    return df


def parse_nested_stac_data(df: DataFrame, column: str) -> DataFrame:
    assert column in df.columns, f"Column '{column}' not found in DataFrame"
    assert isinstance(df[column].iloc[0], dict), f"Column '{column}' must be a dict to parse nested data."
    return df[column].apply(lambda properties: Series(properties))


def request_asset_info(df: DataFrame) -> DataFrame:
    assert "assets" in df.columns, "Column 'assets' not found in DataFrame; cannot retrieve asset info."

    def _request_asset_info(info_url: str) -> Series:
        r = get(url=info_url)
        return Series(r.json())

    return df["assets"].apply(lambda assets: _request_asset_info(assets["info"]["href"]))


def bbox_from_geometry(geometry: Dict) -> BoundingBox:
    geometry = ensure_valid_geometry(geometry, keys=["coordinates", "type"])
    coords = geometry["coordinates"]
    lngs = [lng for lng in _walk_geom_coords(coords, lambda c: c[0])]
    lats = [lat for lat in _walk_geom_coords(coords, lambda c: c[1])]
    return (min(lngs), min(lats), max(lngs), max(lats))


def _walk_geom_coords(coordinates, get_fn) -> Iterator[float]:
    for x in coordinates:
        if isinstance(x, float):
            yield get_fn(coordinates)
        elif isinstance(x, dict):
            yield from _walk_geom_coords(x["geometry"]["coordinates"], get_fn)
        else:
            yield from _walk_geom_coords(x, get_fn)
