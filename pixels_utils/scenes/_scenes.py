import logging
from datetime import date, datetime
from typing import Any, Dict, Union

from geo_utils.vector import geojson_to_shapely, shapely_to_geojson_geometry
from geojson.feature import Feature
from joblib import Memory  # type: ignore
from pandas import DataFrame, Series
from pystac_client import Client
from rasterio.enums import Resampling
from requests import get
from requests.exceptions import ConnectionError as RequestsConnectionError
from retry import retry
from tqdm import tqdm

from pixels_utils.scenes._utils import _validate_collections, _validate_geometry
from pixels_utils.stac_catalogs.earthsearch import EARTHSEARCH_ASSET_INFO_KEY
from pixels_utils.stac_catalogs.earthsearch.v1 import (
    EARTHSEARCH_SCENE_URL,
    EARTHSEARCH_URL,
    EarthSearchCollections,
    Expression,
)
from pixels_utils.titiler import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints.stac._statistics import QueryParamsStatistics, Statistics
from pixels_utils.titiler.mask.enum_classes import Sentinel2_SCL_Group

memory = Memory("/tmp/pixels-utils-cache/", bytes_limit=2**30, verbose=0)
memory.reduce_size()  # Pre-emptively reduce the cache on start-up (must be done manually)


@memory.cache
@retry((RequestsConnectionError, KeyError, RuntimeError), tries=3, delay=2)
def search_stac_scenes(
    geometry: Any,
    date_start: Union[date, str],
    date_end: Union[date, str],
    stac_catalog_url: str = EARTHSEARCH_URL,
    collection: Union[str, EarthSearchCollections] = EarthSearchCollections.sentinel_2_l2a,
    query: Dict[str, Any] = {"eo:cloud_cover": {"lt": 80}},
    simplify_to_bbox: bool = False,
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

        stac_catalog_url (str, optional): URL of the STAC catalog to search. Defaults to EARTHSEARCH_URL
        ("https://earth-search.aws.element84.com/v1").

        collection: Union[str, EarthSearchCollections], optional): STAC collection to search. Defaults to
        EarthSearchCollections.sentinel_2_l2a ("sentinel-2-l2a").

        query (Dict[str, Any], optional): Additional query parameters to pass to the STAC search API. Defaults to
        `{"eo:cloud_cover": {"lt": 80}}`, which filters out scenes with cloud cover greater than 80%.

        simplify_to_bbox (bool, optional): Whether geometry should be simplified to the bounding box (True) or not; if
        True, uses `bbox` argument of `api.search()`; if False, uses `intersects` argument of `api.search()`. Defaults
        to False.

    Returns:
        DataFrame: DataFrame with `scene_id`, `datetime`, and `eo:cloud_cover` for each scene that intersects `geometry`
        and date parameters.
    """
    date_start = date_start.strftime("%Y-%m-%d") if isinstance(date_start, date) else date_start
    date_end = date_end.strftime("%Y-%m-%d") if isinstance(date_end, date) else date_end
    _validate_geometry(geometry)
    collection = _validate_collections(collection, stac_catalog_url)
    bbox = geojson_to_shapely(geometry).bounds if simplify_to_bbox is True else None
    intersects = shapely_to_geojson_geometry(geojson_to_shapely(geometry)) if simplify_to_bbox is False else None

    api = Client.open(url=stac_catalog_url)

    # TODO: Consider adding additional parameters to this function to provide more control over the search
    s = api.search(
        method="POST",
        # max_items=None,
        # limit=limit,
        # ids=None,
        collections=[collection],
        bbox=bbox,
        intersects=intersects,
        datetime=[date_start, date_end],
        # filter=None,
        # filter_lang=None,
        # sortby=sortby,
        # fields=None,
        query=query,
    )
    df = DataFrame(s.item_collection_as_dict()["features"])
    logging.info("search_stac_scenes found %s scenes", len(df))
    if len(df) == 0:
        return df
    if "properties" not in df.columns:
        logging.warning('"properties" key is not present in "%s" collection and cannot be parsed.', collection)
    else:
        prop_keys = [k for k in df.iloc[0]["properties"]]
        if "datetime" not in prop_keys:
            logging.warning(
                '"datetime" key is not present in "properties" of "%s" collection and cannot be added to dataframe.',
                collection,
            )
        else:
            df["datetime"] = df["properties"].apply(lambda properties: properties["datetime"])
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
    # TODO: Option to output in either wide or long format?
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
    return df["assets"].apply(
        lambda assets: _request_asset_info(assets[EARTHSEARCH_ASSET_INFO_KEY[stac_version]]["href"])
    )


def filter_scenes_with_all_nodata(
    df_scenes: DataFrame,
    feature: Feature,
    expression_obj: Expression,
    gsd: Union[float, int] = 10,
    nodata: Union[float, int] = -999,
) -> list:
    """
    Finds the index of all scenes without any valid pixels across the extent of the field group geometry.

    Note:
        The Titiler/sentera.pixels endpoint has a nuance that if all pixels within a spatial query are NODATA, then
        the Statistics endpoint returns statistics values equivalent to the NODATA value set. This function finds
        the index of all scenes where this is the case so they can be removed from the list of scenes to process.

    Args:
        df_scenes (DataFrame): Initial list of scenes to process.

    Returns:
        list: Index values of df_scenes that can safely be removed because they do not have any valid pixels.
    """
    df_scene_properties = parse_nested_stac_data(df=df_scenes, column="properties")

    ind_nodata = []
    for ind in tqdm(
        list(df_scenes.index),
        desc="Filtering out scenes where clouds are covering the plot area",
    ):
        scene = df_scenes.loc[ind]
        properties = df_scene_properties.loc[ind]
        date = datetime.strptime(properties["datetime"].split("T")[0], "%Y-%m-%d")
        # if date > datetime(2023, 5, 30):
        #     break

        scene_url = EARTHSEARCH_SCENE_URL.format(collection=EarthSearchCollections.sentinel_2_l2a.name, id=scene["id"])

        query_params = QueryParamsStatistics(
            url=scene_url,
            feature=feature,
            expression=expression_obj.expression,
            asset_as_band=True,
            coord_crs=None,
            gsd=gsd,
            nodata=nodata,
            resampling=Resampling.nearest.name,
        )

        stats_arable_wlist = Statistics(
            query_params=query_params,
            clear_cache=False,
            titiler_endpoint=TITILER_ENDPOINT,
            mask_enum=Sentinel2_SCL_Group.ARABLE,
            mask_asset="scl",
            whitelist=True,
        )

        expression_ = list(stats_arable_wlist.response.json()["properties"]["statistics"].keys())[0]
        stats = stats_arable_wlist.response.json()["properties"]["statistics"][expression_]
        # if stats["mean"] == nodata:
        if stats["min"] == nodata:
            # Indicates at least one pixel from statistics query is set to NODATA (i.e., masked)
            logging.debug(
                "%s: No valid pixels available",
                date.date(),
            )
            ind_nodata += [ind]

        else:
            logging.debug(
                "%s: %s valid pixels (Mean NDVI = %s)",
                date.date(),
                stats["count"],
                round(stats["mean"], 2),
            )
    return ind_nodata
