import logging
from typing import Any, Dict, Iterable, List, Tuple, Union

from geo_utils.validate import ensure_valid_geometry, get_all_geojson_geometries
from geopy.distance import distance
from numpy.typing import ArrayLike
from requests import get
from shapely.geometry import shape

from pixels_utils.constants.sentinel2 import SCL
from pixels_utils.constants.titiler import (
    ENDPOINT_INFO,
    NODATA_STR,
    PIXELS_URL,
    QUERY_ASSETS,
    QUERY_C,
    QUERY_CATEGORICAL,
    QUERY_COLOR_FORMULA,
    QUERY_COLORMAP,
    QUERY_COLORMAP_NAME,
    QUERY_EXPRESSION,
    QUERY_HEIGHT,
    QUERY_HISTOGRAM_BINS,
    QUERY_HISTOGRAM_RANGE,
    QUERY_NODATA,
    QUERY_P,
    QUERY_RESAMPLING,
    QUERY_RESCALE,
    QUERY_RETURN_MASK,
    QUERY_UNSCALE,
    QUERY_URL,
    QUERY_WIDTH,
)
from pixels_utils.mask import build_numexpr_scl_mask


def _check_assets_expression(assets: Iterable[str] = None, expression: str = None) -> Tuple[Iterable[str], str]:
    assets = [assets] if isinstance(assets, str) else assets
    if assets is None and expression is None:  # Neither are set
        raise ValueError("Either <assets> or <expression> must be passed.")
    if assets is not None and expression is not None:  # Both are set
        raise ValueError("Both <assets> and <expression> are set, but only one is allowed.")
    logging.debug("assets: %s", assets)
    logging.debug("expression: %s", expression)
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
    categorical: bool = False,
    c: List[Union[float, int]] = None,
    p: List[int] = None,
    histogram_bins: str = None,
    histogram_range: ArrayLike = None,
    unscale: Union[bool, None] = None,
    rescale: ArrayLike = None,
    color_formula: Union[str, None] = None,
    colormap: Union[Dict, None] = None,
    colormap_name: Union[str, None] = None,
    return_mask: Union[bool, None] = None,
) -> Tuple[Dict, str]:
    """Creates the full query to be passed to GET or POST.

    Returns:
        Tuple[Dict, str]: _description_
    """
    logging.debug("Building query for: %s", scene_url)
    assets, expression = _check_assets_expression(assets, expression)
    asset_main = _check_asset_main(assets)
    # geojson = ensure_valid_geometry(geojson, keys=["coordinates", "type"])
    height, width = to_pixel_dimensions(geojson, gsd)
    query = {QUERY_URL: scene_url}

    if assets is not None and mask_scl is not None:
        logging.warning("`assets` do not accept numexpr functions, so `mask_scl` will be ignored.")
        query.update({QUERY_ASSETS: assets})
        # query.update(
        #     {
        #         QUERY_ASSETS: build_numexpr_scl_mask(
        #             assets=assets,
        #             mask_scl=mask_scl,
        #             whitelist=whitelist,
        #             mask_value=nodata,
        #         )
        #     }
        # )
    elif assets is not None and mask_scl is None:
        query.update({QUERY_ASSETS: assets})

    if expression is not None and mask_scl is not None:
        query.update(
            {
                QUERY_EXPRESSION: build_numexpr_scl_mask(
                    expression=expression,
                    mask_scl=mask_scl,
                    whitelist=whitelist,
                    mask_value=nodata,
                )
            }
        )
    elif expression is not None and mask_scl is None:
        query.update({QUERY_EXPRESSION: expression})

    query.update(
        {
            QUERY_NODATA: nodata,
            QUERY_HEIGHT: height,
            QUERY_WIDTH: width,
            QUERY_RESAMPLING: resampling,
            QUERY_CATEGORICAL: str(categorical).lower(),
            QUERY_C: c,
            QUERY_P: p,
            QUERY_HISTOGRAM_BINS: histogram_bins,
            QUERY_HISTOGRAM_RANGE: histogram_range,
            QUERY_UNSCALE: unscale,
            QUERY_RESCALE: rescale,
            QUERY_COLOR_FORMULA: color_formula,
            QUERY_COLORMAP: colormap,
            QUERY_COLORMAP_NAME: colormap_name,
            QUERY_RETURN_MASK: return_mask,
        }
    )
    query_drop_null = {k: v for k, v in query.items() if v is not None}
    return query_drop_null, asset_main

    # if assets is not None and mask_scl is not None:
    #     query = {
    #         QUERY_URL: scene_url,
    #         QUERY_ASSETS: build_numexpr_scl_mask(
    #             assets=assets,
    #             mask_scl=mask_scl,
    #             whitelist=whitelist,
    #             mask_value=nodata,
    #         ),
    #         QUERY_NODATA: nodata,
    #         QUERY_HEIGHT: height,
    #         QUERY_WIDTH: width,
    #         QUERY_RESAMPLING: resampling,
    #         QUERY_CATEGORICAL: str(categorical).lower(),
    #         QUERY_C: c,
    #         QUERY_HISTOGRAM_BINS: histogram_bins,
    #     }
    # elif assets is not None and mask_scl is None:
    #     query = {
    #         QUERY_URL: scene_url,
    #         QUERY_ASSETS: assets,
    #         QUERY_NODATA: nodata,
    #         QUERY_HEIGHT: height,
    #         QUERY_WIDTH: width,
    #         QUERY_RESAMPLING: resampling,
    #         QUERY_CATEGORICAL: str(categorical).lower(),
    #         QUERY_C: c,
    #         QUERY_HISTOGRAM_BINS: histogram_bins,
    #     }

    # if expression is not None and mask_scl is not None:
    #     query = {
    #         QUERY_URL: scene_url,
    #         QUERY_EXPRESSION: build_numexpr_scl_mask(
    #             expression=expression,
    #             mask_scl=mask_scl,
    #             whitelist=whitelist,
    #             mask_value=nodata,
    #         ),
    #         QUERY_NODATA: nodata,
    #         QUERY_HEIGHT: height,
    #         QUERY_WIDTH: width,
    #         QUERY_RESAMPLING: resampling,
    #         QUERY_CATEGORICAL: str(categorical).lower(),
    #         QUERY_C: c,
    #         QUERY_HISTOGRAM_BINS: histogram_bins,
    #     }
    #     query = {
    #         QUERY_URL: scene_url,
    #         QUERY_EXPRESSION: build_numexpr_scl_mask(
    #             expression=expression,
    #             mask_scl=mask_scl,
    #             whitelist=whitelist,
    #             nodata=nodata,
    #         ),
    #         QUERY_NODATA: nodata,
    #     }
    # elif expression is not None and mask_scl is None:
    #     query = {
    #         QUERY_URL: scene_url,
    #         QUERY_EXPRESSION: expression,
    #         QUERY_NODATA: nodata,
    #         QUERY_HEIGHT: height,
    #         QUERY_WIDTH: width,
    #         QUERY_RESAMPLING: resampling,
    #         QUERY_CATEGORICAL: str(categorical).lower(),
    #         QUERY_C: c,
    #         QUERY_HISTOGRAM_BINS: histogram_bins,
    #     }


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
    query, asset_main = get_assets_expression_query(scene_url, assets=assets, expression=expression)
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
    geometry = ensure_valid_geometry(next(get_all_geojson_geometries(geojson)))
    bounds = shape(geometry).bounds  # tuple of left, bottom, right, top coordinates
    # ).bounds  # tuple of left, bottom, right, top coordinates

    p1 = (bounds[1], bounds[0])
    p2 = (bounds[3], bounds[0])
    height = abs(round(distance(p1, p2).meters / gsd))

    p3 = (bounds[1], bounds[0])
    p4 = (bounds[1], bounds[2])
    width = abs(round(distance(p3, p4).meters / gsd))
    return height, width


# def find_geometry_from_geojson(geojson: Any) -> Dict:
#     """One might think a geojson is a geojson, but it isn't always as simple as that.
#     This function returns the "lowest-level" geojson from any geometry object, feature.

#     Raises ValueError if there are more than one geometry.

#     Args:
#         geojson: _description_

#     Returns:
#         Dict: geometry expressed as a dictionary.
#     """
#     if "geometry" in geojson.keys():
#         geometry = geojson["geometry"]
#     elif "features" in geojson.keys():
#         feat_n = len(geojson["features"])
#         if feat_n > 1:
#             raise ValueError(
#                 "<geojson> contains {feat_n} geometries. Please pass a GeoJSON that "
#                 "contains one (and only one) geometry."
#             )
#         geometry = geojson["features"][0]["geometry"]
#     else:
#         raise ValueError("Could not determine a geometry from <geojson>.")
#     return geometry
