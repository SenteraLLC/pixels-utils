from datetime import date
from typing import Any, Dict, Union

from joblib import Memory  # type: ignore
from pandas import DataFrame, Series
from pystac_client import Client
from requests import get
from retry import retry

from pixels_utils.scenes._utils import bounds_from_geojson_or_geometry
from pixels_utils.stac_catalogs.earthsearch.v1 import EARTHSEARCH_URL, EarthSearchCollections

memory = Memory("/tmp/pixels-utils-cache/", bytes_limit=2**30, verbose=0)
memory.reduce_size()  # Pre-emptively reduce the cache on start-up (must be done manually)


def _earthsearch_version_from_stac_version(stac_catalog_url: str = EARTHSEARCH_URL):
    stac_version = stac_catalog_url.split("/")[-1]
    if stac_version == "v0":
        from pixels_utils.stac_catalogs.earthsearch.v0 import EarthSearchCollections

        return EarthSearchCollections
    elif stac_version == "v1":
        from pixels_utils.stac_catalogs.earthsearch.v1 import EarthSearchCollections

        return EarthSearchCollections
    else:
        raise ValueError(f"STAC version '{stac_version}' not supported by pixels-utils.")


def _validate_collections(collection: Union[str, EarthSearchCollections], stac_catalog_url: str = EARTHSEARCH_URL):
    # TODO: Make more robust if needing to support more STAC catalogs
    earthsearch_collections = _earthsearch_version_from_stac_version(stac_catalog_url)

    collection = collection.name if isinstance(collection, earthsearch_collections) else collection
    assert collection in [
        c.name for c in earthsearch_collections
    ], f"Collection '{collection}' not supported by pixels-utils."
    return collection


@memory.cache
@retry((RuntimeError, KeyError), tries=3, delay=2)
def get_stac_scenes(
    geometry: Any,
    date_start: Union[date, str],
    date_end: Union[date, str],
    intersects: None,
    stac_catalog_url: str = EARTHSEARCH_URL,
    collection: Union[str, EarthSearchCollections] = EarthSearchCollections.sentinel_2_l2a,
    query: Dict[str, Any] = {"eo:cloud_cover": {"lt": 80}},
) -> DataFrame:
    """
    Retrieves `scene_id`, `datetime`, and cloud cover for all available image tiles between `date_start` and `date_end`.

    See EarthSearch API documentation for more information:
    https://earth-search.aws.element84.com/v1/api.html#tag/Item-Search/operation/getItemSearch

    Args:
        geometry (Any): Geometry of search area; must be able to be parsed to a shapely object, and must be in the
        EPSG=4326 CRS. If a GeoJSON Feature or FeatureCollection is passed, all geometries will be combined into a
        single geometry to determine the bounding box.
        date_start (Union[date, str]): Earliest UTC date to seach for available images (inclusive).
        date_end (Union[date, str]): Latest UTC date to seach for available images (inclusive).
        intersects: The optional intersects parameter filters the result Items in the same was as bbox, only with a
        GeoJSON Geometry rather than a bbox. Not yet supported by pixels-utils.

        stac_catalog_url (str, optional): URL of the STAC catalog to search. Defaults to EARTHSEARCH_URL
        ("https://earth-search.aws.element84.com/v1").

        collection: Union[str, EarthSearchCollections], optional): STAC collection to search. Defaults to
        EarthSearchCollections.sentinel_2_l2a ("sentinel-2-l2a").

        query (Dict[str, Any], optional): Additional query parameters to pass to the STAC search API. Defaults to `{"eo:cloud_cover": {"lt": 80}}`, which filters out scenes with cloud cover greater than 80%.

    Returns:
        DataFrame: DataFrame with `scene_id`, `datetime`, and `eo:cloud_cover` for each scene within `bounding_box` and
        between the passed date parameters.
    """
    # TODO: Support "intersects"
    assert intersects is None, "Intersects not yet supported by pixels-utils."
    date_start = date_start.strftime("%Y-%m-%d") if isinstance(date_start, date) else date_start
    date_end = date_end.strftime("%Y-%m-%d") if isinstance(date_end, date) else date_end
    collection = _validate_collections(collection, stac_catalog_url)

    api = Client.open(url=stac_catalog_url)

    # TODO: Consider adding additional parameters to this function to allow for more control over the search
    s = api.search(
        method="POST",
        # max_items=None,
        # limit=limit,
        # ids=None,
        collections=[collection],
        bbox=bounds_from_geojson_or_geometry(geometry),
        # intersects=None,
        datetime=[date_start, date_end],
        # filter=None,
        # filter_lang=None,
        # sortby=sortby,
        # fields=None,
        query=query,
    )
    df = DataFrame(s.item_collection_as_dict()["features"])
    # Append `datetime` and `eo:cloud_cover` columns to main DataFrame
    df["datetime"] = df["properties"].apply(lambda properties: properties["datetime"])
    df["eo:cloud_cover"] = df["properties"].apply(lambda properties: properties["eo:cloud_cover"])
    df = df.sort_values(by="datetime", ascending=True, ignore_index=True)
    return df


def parse_nested_stac_data(df: DataFrame, column: str) -> DataFrame:
    """
    Parses nested STAC data from a DataFrame column into a new DataFrame.

    Args:
        df (DataFrame): DataFrame containing nested STAC data.
        column (str): Name of column containing nested STAC data.

    Returns:
        DataFrame: DataFrame with nested STAC data parsed into new columns.
    """
    assert column in df.columns, f"Column '{column}' not found in DataFrame"
    assert isinstance(df[column].iloc[0], dict), f"Column '{column}' must be a dict to parse nested data."
    return df[column].apply(lambda properties: Series(properties))


@memory.cache
@retry((RuntimeError, KeyError), tries=3, delay=2)
def request_asset_info(df: DataFrame) -> DataFrame:
    """
    Retrieves asset info for each scene in a DataFrame.

    Args:
        df (DataFrame): DataFrame containing STAC data.

    Returns:
        DataFrame: DataFrame with asset info for each scene.
    """
    assert "assets" in df.columns, "Column 'assets' not found in DataFrame; cannot retrieve asset info."
    assert (
        "stac_version" in df.columns
    ), "Column 'stac_version' not found in DataFrame; cannot retrieve determine structure of STAC data."

    def _request_asset_info(info_url: str) -> Series:
        r = get(url=info_url)
        return Series(r.json())

    def _get_stac_version(df: DataFrame) -> str:
        return df["stac_version"].iloc[0]

    stac_version = _get_stac_version(df)
    asset_info_str = "info" if stac_version == "1.0.0-beta.2" else "tileinfo_metadata"
    return df["assets"].apply(lambda assets: _request_asset_info(assets[asset_info_str]["href"]))
