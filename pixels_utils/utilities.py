import logging
from typing import Any, Dict, Iterable, Tuple, Union

from geopy.distance import distance
from requests import get
from shapely.geometry import shape

from pixels_utils.constants.sentinel2 import SCL
from pixels_utils.constants.titiler import (
    ENDPOINT_INFO,
    NODATA_STR,
    PIXELS_URL,
    QUERY_ASSETS,
    QUERY_EXPRESSION,
    QUERY_HEIGHT,
    QUERY_NODATA,
    QUERY_RESAMPLING,
    QUERY_URL,
    QUERY_WIDTH,
)
from pixels_utils.mask import build_numexpr_scl_mask


def _check_assets_expression(
    assets: Iterable[str] = None, expression: str = None
) -> Tuple[Iterable[str], str]:
    if assets is None and expression is None:  # Neither are set
        raise ValueError("Either <assets> or <expression> must be passed.")
    if assets is not None and expression is not None:  # Both are set
        raise ValueError(
            "Both <assets> and <expression> are set, but only one is allowed."
        )
    logging.info("assets: %s\nexpression: %s", assets, expression)
    return assets, expression


def _check_asset_main(assets: Iterable[str] = None) -> str:
    """Determines the "main" asset from an iterable."""
    if assets is not None:
        asset_main = assets if isinstance(assets, str) else assets[0]
    else:
        asset_main = None
    return asset_main


def get_assets_expression_query(
    scene_url: str,
    assets: Iterable[str] = None,
    expression: str = None,
    geojson: Any = None,
    mask_scl: Iterable[SCL] = None,
    whitelist: bool = True,
    nodata: Union[int, float] = None,
    gsd: Union[int, float] = None,
    resampling: str = "nearest",
) -> Tuple[Dict, str]:
    """Creates the full query to be passed to GET or POST.

    Returns:
        Tuple[Dict, str]: _description_
    """
    assets, expression = _check_assets_expression(assets, expression)
    asset_main = _check_asset_main(assets)
    height, width = to_pixel_dimensions(geojson, gsd)

    if assets is not None and mask_scl is not None:
        query = {
            QUERY_URL: scene_url,
            QUERY_ASSETS: build_numexpr_scl_mask(
                assets=assets,
                mask_scl=mask_scl,
                whitelist=whitelist,
                mask_value=nodata,
            ),
            QUERY_NODATA: nodata,
            QUERY_HEIGHT: height,
            QUERY_WIDTH: width,
            QUERY_RESAMPLING: resampling,
        }
    elif assets is not None and mask_scl is None:
        query = {QUERY_URL: scene_url, QUERY_ASSETS: assets}

    if expression is not None and mask_scl is not None:
        query = {
            QUERY_URL: scene_url,
            QUERY_EXPRESSION: build_numexpr_scl_mask(
                expression=expression,
                mask_scl=mask_scl,
                whitelist=whitelist,
                mask_value=nodata,
            ),
            QUERY_NODATA: nodata,
            QUERY_HEIGHT: height,
            QUERY_WIDTH: width,
            QUERY_RESAMPLING: resampling,
        }
        # query = {
        #     QUERY_URL: scene_url,
        #     QUERY_EXPRESSION: build_numexpr_scl_mask(
        #         expression=expression,
        #         mask_scl=mask_scl,
        #         whitelist=whitelist,
        #         nodata=nodata,
        #     ),
        #     QUERY_NODATA: nodata,
        # }
    elif expression is not None and mask_scl is None:
        query = {
            QUERY_URL: scene_url,
            QUERY_EXPRESSION: expression,
            QUERY_NODATA: nodata,
            QUERY_HEIGHT: height,
            QUERY_WIDTH: width,
            QUERY_RESAMPLING: resampling,
        }
    query_drop_null = {k: v for k, v in query.items() if v is not None}
    return query_drop_null, asset_main


def get_nodata(
    scene_url: str,
    assets: Iterable[str] = None,
    expression: str = None,
) -> float:
    """Gets nodata value for a given <scene_url>.

    Args:
        scene_url: STAC item URL.
        assets: Asset names. If both <assets> and <expression> are set to None, will
        return all available assets. Default is None.
        expression: Rio-tiler's math expression with asset names (e.g.,
        "(B08-B04)/(B08+B04)"). Ignored when <assets> is set to a non-null value.
        Default is None.
    """
    query, asset_main = get_assets_expression_query(
        scene_url, assets=assets, expression=expression
    )
    r = get(PIXELS_URL.format(endpoint=ENDPOINT_INFO), params=query)
    asset_main = list(r.json().keys())[0] if asset_main is None else asset_main
    return float(r.json()[asset_main][NODATA_STR])


def to_pixel_dimensions(geojson: Any, gsd: Union[int, float]) -> Tuple[int, int]:
    """Calculates pixel height and width for a ground sampling distance (in meters).

    Args:
        geojson: geojson geometry.
        gsd: The desired ground sample distance in meters per pixel.

    Returns:
        Tuple(int, int): height, width pixel size for the tile.
    """
    if geojson is None or gsd is None:
        return None, None
    if gsd <= 0:
        raise ValueError(f"<gsd> of {gsd} is invalid (must be greater than 0.0).")
    bounds = shape(
        find_geometry_from_geojson(geojson)
    ).bounds  # tuple of left, bottom, right, top coordinates

    p1 = (bounds[1], bounds[0])
    p2 = (bounds[3], bounds[0])
    height = abs(round(distance(p1, p2).meters / gsd))

    p3 = (bounds[1], bounds[0])
    p4 = (bounds[1], bounds[2])
    width = abs(round(distance(p3, p4).meters / gsd))
    return height, width


def find_geometry_from_geojson(geojson: Any) -> Dict:
    """One might think a geojson is a geojson, but it isn't always as simple as that.
    This function returns the "lowest-level" geojson from any geometry object, feature.

    Raises ValueError if there are more than one geometry.

    Args:
        geojson: _description_

    Returns:
        Dict: geometry expressed as a dictionary.
    """
    if "geometry" in geojson.keys():
        geometry = geojson["geometry"]
    elif "features" in geojson.keys():
        feat_n = len(geojson["features"])
        if feat_n > 1:
            raise ValueError(
                "<geojson> contains {feat_n} geometries. Please pass a GeoJSON that "
                "contains one (and only one) geometry."
            )
        geometry = geojson["features"][0]["geometry"]
    else:
        raise ValueError("Could not determine a geometry from <geojson>.")
    return geometry
