from typing import Any, Iterable, Union

from joblib import Memory  # type: ignore
from requests import Response, get, post

from pixels_utils.constants.sentinel2 import SCL
from pixels_utils.constants.titiler import (
    ENDPOINT_CROP,
    ENDPOINT_STATISTICS,
    PIXELS_URL,
)
from pixels_utils.utilities import get_assets_expression_query, get_nodata

memory = Memory("/tmp/pixels-demo-cache/", bytes_limit=2**30, verbose=0)
memory.reduce_size()  # Pre-emptively reduce the cache on start-up (must be done manually)


@memory.cache
def statistics(
    scene_url: str,
    assets: Iterable[str] = None,
    expression: str = None,
    geojson: Any = None,
    mask_scl: Iterable[SCL] = None,
    whitelist: bool = True,
    nodata: Union[int, float] = None,
    gsd: Union[int, float] = 20,
    resampling: str = "nearest",
) -> Response:
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
    nodata = (
        get_nodata(scene_url, assets=assets, expression=expression)
        if nodata is None
        else nodata
    )

    query, _ = get_assets_expression_query(
        scene_url,
        assets=assets,
        expression=expression,
        geojson=geojson,
        mask_scl=mask_scl,
        whitelist=whitelist,
        nodata=nodata,
        gsd=gsd,
        resampling=resampling,
    )

    if geojson is not None:
        return post(
            PIXELS_URL.format(endpoint=ENDPOINT_STATISTICS),
            params=query,
            json=geojson,
        )
    else:
        return get(PIXELS_URL.format(endpoint=ENDPOINT_STATISTICS), params=query)


@memory.cache
def crop(
    scene_url: str,
    assets: Iterable[str] = None,
    expression: str = None,
    geojson: Any = None,
    mask_scl: Iterable[SCL] = None,
    whitelist: bool = True,
    nodata: Union[int, float] = None,
    gsd: Union[int, float] = 20,
    resampling: str = "nearest",
    format: str = ".tif",
) -> Response:
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
        format: _description_. Defaults to ".tif".
    """
    from shapely.geometry import shape

    from pixels_utils.utilities import find_geometry_from_geojson, to_pixel_dimensions

    PIXELS_CROP_URL = (
        "{pixels_endpoint}/{minx},{miny},{maxx},{maxy}/{width}x{height}/{format}"
    )
    PIXELS_CROP_URL = "{pixels_endpoint}"
    nodata = (
        get_nodata(scene_url, assets=assets, expression=expression)
        if nodata is None
        else nodata
    )
    height, width = to_pixel_dimensions(geojson, gsd)
    minx, miny, maxx, maxy = shape(find_geometry_from_geojson(geojson)).bounds

    query, _ = get_assets_expression_query(
        scene_url,
        assets=assets,
        expression=expression,
        geojson=geojson,
        mask_scl=mask_scl,
        whitelist=whitelist,
        nodata=nodata,
        gsd=gsd,
        resampling=resampling,
    )

    query = {k: v for k, v in query.items() if k not in ["height", "width"]}
    if geojson is not None:
        r = post(
            PIXELS_URL.format(endpoint=ENDPOINT_CROP),
            # PIXELS_CROP_URL.format(
            #     pixels_endpoint=PIXELS_URL.format(endpoint=ENDPOINT_CROP),
            #     minx=minx,
            #     miny=miny,
            #     maxx=maxx,
            #     maxy=maxy,
            #     width=width,
            #     height=height,
            #     format=format,
            # ),
            params=query,
            json=geojson,
        )
    else:
        r = get(PIXELS_URL.format(endpoint=ENDPOINT_CROP), params=query)
    return r.content
    # path = "/mnt/c/Users/Tyler/Downloads/test.png"

    # with open(path, 'wb') as f:
    #     f.write(r.content)


# r = post(
#     PIXELS_URL.format(endpoint=ENDPOINT_CROP),
#     # PIXELS_CROP_URL.format(
#     #     pixels_endpoint=PIXELS_URL.format(endpoint=ENDPOINT_CROP),
#     #     minx=minx,
#     #     miny=miny,
#     #     maxx=maxx,
#     #     maxy=maxy,
#     #     width=width,
#     #     height=height,
#     #     format=format,
#     # ),
#     params=query,
#     json=geojson,
# )
