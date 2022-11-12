import logging
from typing import Any, Iterable, List, Union

from geo_utils.validate import ensure_valid_featurecollection
from geo_utils.world import round_dec_degrees
from joblib import Memory  # type: ignore
from requests import get, post
from shapely.geometry import shape

from pixels_utils.constants.sentinel2 import SCL
from pixels_utils.constants.titiler import (
    ENDPOINT_CROP,
    ENDPOINT_STATISTICS,
    PIXELS_URL,
    URL_PIXELS_CROP,
    URL_PIXELS_CROP_GEOJSON,
)
from pixels_utils.constants.types import STAC_crop, STAC_statistics
from pixels_utils.utilities import (  # find_geometry_from_geojson,
    get_assets_expression_query,
    get_nodata,
    to_pixel_dimensions,
)

memory = Memory("/tmp/pixels-utils-cache/", bytes_limit=2**30, verbose=0)
memory.reduce_size()  # Pre-emptively reduce the cache on start-up (must be done manually)


@memory.cache
def statistics_response(
    scene_url: str,
    assets: Iterable[str] = None,
    expression: str = None,
    geojson: Any = None,
    mask_scl: Iterable[SCL] = None,
    whitelist: bool = True,
    nodata: Union[int, float] = None,
    gsd: Union[int, float] = 20,
    resampling: str = "nearest",
    categorical: bool = False,
    c: List[Union[float, int]] = None,
    histogram_bins: str = None,
    clear_cache=False,
) -> STAC_statistics:
    """Return asset's statistics for a GeoJSON.

    See: https://developmentseed.org/titiler/endpoints/stac/#statistics

    Args:
        scene_url: STAC item URL.
        assets: Asset names. If both <assets> and <expression> are set to None, will
        return all available assets. Default is None.
        expression: Rio-tiler's math expression with asset names (e.g.,
        "(B08-B04)/(B08+B04)"). Ignored when <assets> is set to a non-null value.
        Default is None.
        geojson: _description_. Defaults to None.
        mask_scl: _description_. Defaults to None.
        whitelist: _description_. Defaults to True.
        nodata: _description_. Defaults to None.
        gsd: _description_. Defaults to 20.
        resampling: _description_. Defaults to "nearest".
    """
    geojson_fc = ensure_valid_featurecollection(geojson, create_new=False)
    nodata = get_nodata(scene_url, assets=assets, expression=expression) if nodata is None else nodata

    query, _ = get_assets_expression_query(
        scene_url,
        assets=assets,
        expression=expression,
        geojson=geojson_fc,
        mask_scl=mask_scl,
        whitelist=whitelist,
        nodata=nodata,
        gsd=gsd,
        resampling=resampling,
        categorical=categorical,
        c=c,
        histogram_bins=histogram_bins,
    )
    if clear_cache is True:
        headers = {"Cache-Control": "no-cache", "Pragma": "no-cache"}
    else:
        headers = {}

    if geojson_fc is not None:
        logging.debug(
            'POST request to "%s" with the following args:\nparams: %s\njson: %s\nheaders: %s',
            PIXELS_URL.format(endpoint=ENDPOINT_STATISTICS),
            query,
            geojson_fc,
            headers,
        )
        return post(
            PIXELS_URL.format(endpoint=ENDPOINT_STATISTICS),
            params=query,
            json=geojson_fc,
            headers=headers,
        )
    else:
        logging.debug(
            'GET request to "%s" with the following args:\nparams: %s\nheaders: %s',
            PIXELS_URL.format(endpoint=ENDPOINT_STATISTICS),
            query,
            headers,
        )
        return get(
            PIXELS_URL.format(endpoint=ENDPOINT_STATISTICS),
            params=query,
            headers=headers,
        )


@memory.cache
def crop_response(
    scene_url: str,
    assets: Iterable[str] = None,
    expression: str = None,
    geojson: Any = None,
    mask_scl: Iterable[SCL] = None,
    whitelist: bool = True,
    nodata: Union[int, float] = None,
    gsd: Union[int, float] = 20,
    resampling: str = "nearest",
    format_stac: str = ".tif",
) -> STAC_crop:
    """

    See: https://developmentseed.org/titiler/endpoints/stac/#crop-part

    Args:
        scene_url: STAC item URL.

        assets: Asset names. If both <assets> and <expression> are set to None, will
            return all available assets. Default is None.

        expression: Rio-tiler's math expression with asset names (e.g.,
            "(B08-B04)/(B08+B04)"). Ignored when <assets> is set to a non-null value.
            Default is None.

        geojson: _description_. Defaults to None.
        mask_scl: _description_. Defaults to None.
        whitelist: _description_. Defaults to True.
        nodata: _description_. Defaults to None.
        gsd: _description_. Defaults to 20.
        resampling: _description_. Defaults to "nearest".
        format_stac: _description_. Defaults to ".tif".
    """
    geojson_fc = ensure_valid_featurecollection(geojson, create_new=False)
    nodata = get_nodata(scene_url, assets=assets, expression=expression) if nodata is None else nodata
    query, _ = get_assets_expression_query(
        scene_url,
        assets=assets,
        expression=expression,
        geojson=geojson_fc,
        mask_scl=mask_scl,
        whitelist=whitelist,
        nodata=nodata,
        gsd=gsd,
        resampling=resampling,
    )
    query = {k: v for k, v in query.items() if k not in ["height", "width"]}

    height, width = to_pixel_dimensions(geojson_fc, gsd)
    # minx, miny, maxx, maxy = shape(find_geometry_from_geojson(geojson)).bounds

    if geojson_fc is not None:
        r = post(
            URL_PIXELS_CROP_GEOJSON.format(
                pixels_endpoint=PIXELS_URL.format(endpoint=ENDPOINT_CROP),
                width=width,
                height=height,
                format=format_stac,
            ),
            params=query,
            json=geojson_fc,
        )
    else:
        minx, miny, maxx, maxy = shape(geojson_fc).bounds
        r = get(
            URL_PIXELS_CROP.format(
                pixels_endpoint=PIXELS_URL.format(endpoint=ENDPOINT_CROP),
                minx=round_dec_degrees(minx, n_decimal_places=6),
                miny=round_dec_degrees(miny, n_decimal_places=6),
                maxx=round_dec_degrees(maxx, n_decimal_places=6),
                maxy=round_dec_degrees(maxy, n_decimal_places=6),
                width=width,
                height=height,
                format=format_stac,
            ),
            params=query,
        )
    return STAC_crop(r)
