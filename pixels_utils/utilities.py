import logging
from typing import Dict, Iterable, Tuple, Union

from requests import get

from pixels_utils.constants.sentinel2 import SCL
from pixels_utils.constants.titiler import (
    ENDPOINT_INFO,
    NODATA_STR,
    PIXELS_URL,
    QUERY_ASSETS,
    QUERY_EXPRESSION,
    QUERY_URL,
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
    logging.info(f"assets: {assets}\nexpression: {expression}")
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
    mask_scl: Iterable[SCL] = None,
    whitelist: bool = True,
    nodata: Union[int, float] = None,
) -> Tuple[Dict, str]:
    """Creates the full query to be passed to GET or POST.

    Returns:
        Tuple[Dict, str]: _description_
    """
    assets, expression = _check_assets_expression(assets, expression)
    asset_main = _check_asset_main(assets)

    if assets is not None and mask_scl is not None:
        query = {
            QUERY_URL: scene_url,
            QUERY_ASSETS: build_numexpr_scl_mask(
                assets=assets,
                mask_scl=mask_scl,
                whitelist=whitelist,
                nodata=nodata,
            ),
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
                nodata=nodata,
            ),
        }
    elif expression is not None and mask_scl is None:
        query = {QUERY_URL: scene_url, QUERY_EXPRESSION: expression}
    return query, asset_main


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
