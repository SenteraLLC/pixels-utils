from datetime import date
from typing import Any, Union

from joblib import Memory  # type: ignore
from pandas import DataFrame, Series
from pystac_client import Client
from requests import get
from retry import retry

from pixels_utils.constants.stac_v1 import ELEMENT84_SEARCH_URL, EarthSearchCollections
from pixels_utils.scenes._utils import bounds_from_geojson_or_geometry

memory = Memory("/tmp/pixels-utils-cache/", bytes_limit=2**30, verbose=0)
memory.reduce_size()  # Pre-emptively reduce the cache on start-up (must be done manually)


def _validate_collections(collection: Union[str, EarthSearchCollections]):
    collection = collection.name if isinstance(collection, EarthSearchCollections) else collection
    assert collection in [
        c.name for c in EarthSearchCollections
    ], f"Collection '{collection}' not supported by pixels-utils."
    return collection


@memory.cache
@retry((RuntimeError, KeyError), tries=3, delay=2)
def get_stac_scenes(
    geometry: Any,
    date_start: Union[date, str],
    date_end: Union[date, str],
    max_scene_cloud_cover_percent: int = 80,
    stac_catalog_url: str = ELEMENT84_SEARCH_URL,
    collection: Union[str, EarthSearchCollections] = EarthSearchCollections.sentinel_2_l2a,
    max_items: int = None,
) -> DataFrame:
    """
    Retrieves `scene_id`, `datetime`, and cloud cover for all available image tiles between `date_start` and `date_end`.

    Args:
        geometry (Any): Geometry of search area; must be able to be parsed to a shapely object, and must be in the EPSG=4326 CRS. If a GeoJSON Feature or FeatureCollection is passed, all geometries will be combined into a single geometry to determine the bounding box.
        date_start (Union[date, str]): Earliest UTC date to seach for available images (inclusive).
        date_end (Union[date, str]): Latest UTC date to seach for available images (inclusive).
        max_scene_cloud_cover_percent (int, optional): Maximum percent cloud cover allowed in the scene. Scene cloud
        cover greater than this value will be dropped from the returned DataFrame. Defaults to 80.
        stac_catalog_url (str, optional): URL of the STAC catalog to search. Defaults to
        "https://earth-search.aws.element84.com/v0".

    Returns:
        DataFrame: DataFrame with `scene_id`, `datetime`, and `eo:cloud_cover` for each scene within `bounding_box` and
        betweent the passed date parameters.
    """
    date_start = date_start.strftime("%Y-%m-%d") if isinstance(date_start, date) else date_start
    date_end = date_end.strftime("%Y-%m-%d") if isinstance(date_end, date) else date_end
    collection = _validate_collections(collection)

    api = Client.open(url=stac_catalog_url)

    s = api.search(
        max_items=max_items,
        collections=[collection],
        bbox=bounds_from_geojson_or_geometry(geometry),
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


@memory.cache
@retry((RuntimeError, KeyError), tries=3, delay=2)
def request_asset_info(df: DataFrame) -> DataFrame:
    assert "assets" in df.columns, "Column 'assets' not found in DataFrame; cannot retrieve asset info."

    def _request_asset_info(info_url: str) -> Series:
        r = get(url=info_url)
        return Series(r.json())

    return df["assets"].apply(lambda assets: _request_asset_info(assets["info"]["href"]))
