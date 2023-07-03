import logging
from typing import Any, Dict, Iterable, List, Tuple, Union

from geo_utils.vector import geojson_to_shapely, validate_geojson
from geopy.distance import distance
from numpy.typing import ArrayLike
from requests import get

from pixels_utils.constants.sentinel2 import SCL
from pixels_utils.mask import build_numexpr_scl_mask
from pixels_utils.titiler.endpoints.stac._constants import STAC_ENDPOINT
from pixels_utils.titiler.endpoints.stac.titiler import (
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

STAC_INFO_ENDPOINT = f"{STAC_ENDPOINT}/info"


# def _check_assets_expression(assets: Iterable[str] = None, expression: str = None) -> Tuple[Iterable[str], str]:
#     assets = [assets] if isinstance(assets, str) else assets
#     if assets is None and expression is None:  # Neither are set
#         raise ValueError('Either "assets" or "expression" must be passed (both are null).')
#     if assets is not None and expression is not None:  # Both are set
#         raise ValueError('Both "assets" and "expression" are set, but only one is allowed.')
#     logging.debug("assets: %s", assets)
#     logging.debug("expression: %s", expression)
#     return assets, expression


# def _check_asset_main(assets: Iterable[str] = None) -> str:
#     """Determines the "main" asset from an iterable."""
#     if assets is not None:
#         asset_main = assets if isinstance(assets, str) else assets[0]
#     else:
#         asset_main = None
#     return asset_main


def generate_base_query(**kwargs) -> Dict[str, Any]:
    assert "url" in kwargs, '"url" must be passed as a keyword argument.'
    logging.debug("Building query for: %s", kwargs["url"])
    assets, expression = [kwargs.get(i, None) for i in ["assets", "expression"]]
    kwargs["assets"] = [assets] if isinstance(assets, str) else assets
    # asset_main = None if kwargs["assets"] is None else kwargs["assets"][0]
    kwargs["height"], kwargs["width"] = (
        to_pixel_dimensions(geojson=kwargs["feature"], gsd=kwargs["gsd"])
        if not [x for x in (kwargs["feature"], kwargs["gsd"]) if x is None]
        else [None, None]
    )
    # TODO: Delete kwargs["gsd"]?
    return {k: v for k, v in kwargs.items() if v is not None}


# def get_assets_expression_query_full(
#     scene_url: str,
#     assets: Iterable[str] = None,
#     expression: str = None,
#     geojson: Any = None,
#     mask_scl: Iterable[SCL] = None,
#     whitelist: bool = True,
#     nodata: Union[int, float] = None,
#     gsd: Union[int, float] = None,
#     resampling: str = "nearest",
#     categorical: bool = False,
#     c: List[Union[float, int]] = None,
#     p: List[int] = None,
#     histogram_bins: str = None,
#     histogram_range: ArrayLike = None,
#     unscale: Union[bool, None] = None,
#     rescale: ArrayLike = None,
#     color_formula: Union[str, None] = None,
#     colormap: Union[Dict, None] = None,
#     colormap_name: Union[str, None] = None,
#     return_mask: Union[bool, None] = None,
# ) -> Tuple[Dict, str]:
#     """Creates the full query to be passed to GET or POST.

#     Returns:
#         Tuple[Dict, str]: _description_
#     """
#     logging.debug("Building query for: %s", scene_url)
#     assets, expression = _check_assets_expression(assets, expression)
#     asset_main = _check_asset_main(assets)
#     # geojson = ensure_valid_geometry(geojson, keys=["coordinates", "type"])
#     height, width = to_pixel_dimensions(geojson, gsd)
#     query = {QUERY_URL: scene_url}

#     if assets is not None and mask_scl is not None:
#         logging.info("`assets` do not accept numexpr functions, so `mask_scl` will be ignored.")
#         query.update({QUERY_ASSETS: assets})
#         # query.update(
#         #     {
#         #         QUERY_ASSETS: build_numexpr_scl_mask(
#         #             assets=assets,
#         #             mask_scl=mask_scl,
#         #             whitelist=whitelist,
#         #             mask_value=nodata,
#         #         )
#         #     }
#         # )
#     elif assets is not None and mask_scl is None:
#         query.update({QUERY_ASSETS: assets})

#     if expression is not None and mask_scl is not None:
#         query.update(
#             {
#                 QUERY_EXPRESSION: build_numexpr_scl_mask(
#                     expression=expression,
#                     mask_scl=mask_scl,
#                     whitelist=whitelist,
#                     mask_value=nodata,
#                 )
#             }
#         )
#     elif expression is not None and mask_scl is None:
#         query.update({QUERY_EXPRESSION: expression})

#     query.update(
#         {
#             QUERY_NODATA: nodata,
#             QUERY_HEIGHT: height,
#             QUERY_WIDTH: width,
#             QUERY_RESAMPLING: resampling,
#             QUERY_CATEGORICAL: str(categorical).lower(),
#             QUERY_C: c,
#             QUERY_P: p,
#             QUERY_HISTOGRAM_BINS: histogram_bins,
#             QUERY_HISTOGRAM_RANGE: histogram_range,
#             QUERY_UNSCALE: unscale,
#             QUERY_RESCALE: rescale,
#             QUERY_COLOR_FORMULA: color_formula,
#             QUERY_COLORMAP: colormap,
#             QUERY_COLORMAP_NAME: colormap_name,
#             QUERY_RETURN_MASK: return_mask,
#         }
#     )
#     query_drop_null = {k: v for k, v in query.items() if v is not None}
#     return query_drop_null, asset_main


def to_pixel_dimensions(geojson: Any, gsd: Union[int, float]) -> Tuple[int, int]:
    """Calculates pixel height and width for a ground sampling distance (in meters).

    Args:
        geojson: geojson geometry.
        gsd: The desired ground sample distance in meters per pixel.

    Returns:
        Tuple(int, int): height, width pixel size for the tile.
    """
    # if geojson is None or gsd is None:
    #     return None, None
    # if gsd <= 0:
    #     raise ValueError(f"<gsd> of {gsd} is invalid (must be greater than 0.0).")
    bounds = geojson_to_shapely(validate_geojson(geojson)).bounds

    p1 = (bounds[1], bounds[0])
    p2 = (bounds[3], bounds[0])
    height = abs(round(distance(p1, p2).meters / gsd))

    p3 = (bounds[1], bounds[0])
    p4 = (bounds[1], bounds[2])
    width = abs(round(distance(p3, p4).meters / gsd))
    return height, width


# TODO: Can we do a general check on the passed assets by looping through them for the collection?
def is_asset_available(item_url: str, asset: str, stac_info_endpoint: str = STAC_INFO_ENDPOINT) -> bool:
    query = {
        "url": item_url,
        "assets": (asset,),
    }
    if (
        get(
            stac_info_endpoint,
            params=query,
        ).status_code
        == 200
    ):
        return True
    else:
        return False


def validate_assets(
    assets: ArrayLike,
    asset_names: ArrayLike,
    validate_individual_assets: bool = False,
    url: str = None,
    stac_info_endpoint: str = STAC_INFO_ENDPOINT,
) -> List:
    # TODO: Consider maintaining a list of available assets for each collection, and checking against that list; see
    # https://sentera.atlassian.net/wiki/spaces/GML/pages/3357278209/EarthSearch+Collection+Availability
    if (assets is not None) and (set(assets) != set(asset_names)):
        invalid_assets = list(set(assets) - set(asset_names))
        logging.warning(
            "Some assets passed to the Info endpoint are invalid. Invalid assets are being removed from the assets "
            "property and include: %s",
            invalid_assets,
        )
        assets = asset_names
    if assets is None:
        logging.warning(
            "`assets=None`; although Titiler defaults to all available assets, availability of assets within a "
            "catalog are not guaranteed. It is recommended to explicitly pass desired assets. See availability of "
            "assets for different Collections in this Confluence page: "
            "https://sentera.atlassian.net/wiki/spaces/GML/pages/3357278209/EarthSearch+Collection+Availability."
        )

    if validate_individual_assets:
        item_url = url
        item = item_url.split("/")[-1]
        # TODO: Do we want to remove unavailable assets, or just issue warnings to let user know which are unavailable?
        assets = tuple([a for a in assets]) if assets else asset_names
        for asset in assets:
            if is_asset_available(item_url=item_url, asset=asset, stac_info_endpoint=stac_info_endpoint):
                logging.info('Item "%s" asset is AVAILABLE: "%s".', item, asset)
            else:
                logging.warning('Item "%s" asset is NOT AVAILABLE: "%s".', item, asset)
    return assets
