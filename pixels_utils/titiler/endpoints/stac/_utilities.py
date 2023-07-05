import logging
from typing import Any, List, Tuple, Union

from geo_utils.vector import geojson_to_shapely, validate_geojson
from geopy.distance import distance
from numpy.typing import ArrayLike
from requests import get

# from pixels_utils.constants.sentinel2 import SCL
# from pixels_utils.mask import build_numexpr_scl_mask
from pixels_utils.titiler.endpoints.stac._constants import STAC_ENDPOINT

STAC_INFO_ENDPOINT = f"{STAC_ENDPOINT}/info"


# def generate_base_query(**kwargs) -> Dict[str, Any]:
#     """Generates a base query for the STAC Info endpoint."""
#     assert "url" in kwargs, '"url" must be passed as a keyword argument.'
#     logging.debug("Building query for: %s", kwargs["url"])
#     assets, expression = [kwargs.get(i, None) for i in ["assets", "expression"]]
#     kwargs["assets"] = [assets] if isinstance(assets, str) else assets
#     # asset_main = None if kwargs["assets"] is None else kwargs["assets"][0]
#     kwargs["height"], kwargs["width"] = (
#         to_pixel_dimensions(geojson=kwargs["feature"], gsd=kwargs["gsd"])
#         if not [x for x in (kwargs["feature"], kwargs["gsd"]) if x is None]
#         else [None, None]
#     )
#     # TODO: Delete kwargs["gsd"]?
#     return {k: v for k, v in kwargs.items() if v is not None}


def to_pixel_dimensions(geojson: Any, height: int, width: int, gsd: Union[int, float]) -> Tuple[int, int]:
    """Calculates pixel height and width for a ground sampling distance (in meters).

    Args:
        geojson (Any): geojson geometry.
        height (int): Desired height in pixels.
        width (int): Desired width in pixels.
        gsd (Union[int, float]): The desired ground sample distance in meters per pixel.

    Returns:
        Tuple(int, int): height, width pixel size for the tile.
    """
    bounds = geojson_to_shapely(validate_geojson(geojson)).bounds

    if height is None:
        p1 = (bounds[1], bounds[0])
        p2 = (bounds[3], bounds[0])
        height = abs(round(distance(p1, p2).meters / gsd))

    if width is None:
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
    """
    Validates that the assets passed to the Info endpoint are valid for the given STAC item.

    Args:
        assets (ArrayLike): Assets passed to the Info endpoint.
        asset_names (ArrayLike): Assets available for the STAC item.
        validate_individual_assets (bool, optional): Whether to validate each asset individually. Defaults to False.
        url (str, optional): The STAC item URL. Defaults to None.
        stac_info_endpoint (str, optional): The STAC Info endpoint URL. Defaults to STAC_INFO_ENDPOINT.

    Returns:
        List: Valid assets; if validate_individual_assets is True, this included only the valid assets.
    """
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
        assets_all = tuple([a for a in assets]) if assets else asset_names
        assets_available = []
        for asset in assets_all:
            if is_asset_available(item_url=item_url, asset=asset, stac_info_endpoint=stac_info_endpoint):
                logging.info('Item "%s" asset is AVAILABLE: "%s".', item, asset)
                assets_available.append(asset)
            else:
                logging.warning('Item "%s" asset is NOT AVAILABLE: "%s".', item, asset)
        return tuple(assets_available)
    return assets
